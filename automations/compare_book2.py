"""Compare Book1 2.xlsx with DB to find what needs updating."""
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'automations.settings'
django.setup()

import openpyxl
from dashboard.models import USEUContact

wb = openpyxl.load_workbook('Book1 2.xlsx', read_only=True)
ws = wb.active

def safe(val):
    if val is None:
        return ''
    s = str(val).strip().lstrip('\t')
    return s

# Gather spreadsheet data
xlsx_data = {}
has_tp1_sent = 0
blank_tp1_sent = 0
total = 0

for row in ws.iter_rows(min_row=2, values_only=True):
    total += 1
    email = safe(row[13] if len(row) > 13 else '').lower()
    org = safe(row[1] if len(row) > 1 else '')
    tp1 = safe(row[15] if len(row) > 15 else '')
    tp1_sent = safe(row[27] if len(row) > 27 else '')
    journey = safe(row[26] if len(row) > 26 else '')
    
    if tp1_sent:
        has_tp1_sent += 1
    else:
        blank_tp1_sent += 1
    
    key = email if email else org.lower()
    xlsx_data[key] = {
        'org_name': org,
        'email': safe(row[13] if len(row) > 13 else ''),
        'tp1': tp1,
        'tp1_sent': tp1_sent,
        'journey': journey,
        'tp2': safe(row[16] if len(row) > 16 else ''),
        'tp2_sent': safe(row[28] if len(row) > 28 else ''),
    }

wb.close()

print(f"=== SPREADSHEET ===")
print(f"Total rows: {total}")
print(f"Has TP1 Sent On: {has_tp1_sent}")
print(f"Blank TP1 Sent On: {blank_tp1_sent}")

# Check DB
db_blank_tp1_sent = USEUContact.objects.filter(tp1_sent_on='').count()
db_has_tp1_sent = USEUContact.objects.exclude(tp1_sent_on='').count()
print(f"\n=== DATABASE ===")
print(f"Total: {USEUContact.objects.count()}")
print(f"Has TP1 Sent On: {db_has_tp1_sent}")
print(f"Blank TP1 Sent On: {db_blank_tp1_sent}")

# Find matches: records in DB with blank tp1_sent_on that have a value in spreadsheet
db_blank = USEUContact.objects.filter(tp1_sent_on='')
can_update = 0
sample_updates = []
for contact in db_blank[:200]:
    key = contact.email.lower() if contact.email else contact.org_name.lower()
    if key in xlsx_data and xlsx_data[key]['tp1_sent']:
        can_update += 1
        if len(sample_updates) < 5:
            sample_updates.append({
                'org': contact.org_name,
                'email': contact.email,
                'db_tp1_sent': contact.tp1_sent_on,
                'xlsx_tp1_sent': xlsx_data[key]['tp1_sent'],
            })

print(f"\nSample matches (DB blank -> XLSX has value): {can_update} in first 200")
for s in sample_updates:
    print(f"  {s['org']} ({s['email']}): DB='{s['db_tp1_sent']}' -> XLSX='{s['xlsx_tp1_sent']}'")

# Also check: are there records where the spreadsheet has DIFFERENT touchpoint dates?
print("\n=== CHECKING FOR DIFFERENCES ===")
diffs = 0
diff_samples = []
for contact in USEUContact.objects.all()[:500]:
    key = contact.email.lower() if contact.email else contact.org_name.lower()
    if key in xlsx_data:
        xd = xlsx_data[key]
        changes = []
        if xd['tp1'] and xd['tp1'] != contact.touchpoint_1:
            changes.append(f"tp1: '{contact.touchpoint_1}' -> '{xd['tp1']}'")
        if xd['tp1_sent'] and xd['tp1_sent'] != contact.tp1_sent_on:
            changes.append(f"tp1_sent: '{contact.tp1_sent_on}' -> '{xd['tp1_sent']}'")
        if xd['journey'] and xd['journey'] != contact.journey_status:
            changes.append(f"journey: '{contact.journey_status}' -> '{xd['journey']}'")
        if changes:
            diffs += 1
            if len(diff_samples) < 10:
                diff_samples.append(f"{contact.org_name}: {'; '.join(changes)}")

print(f"Records with differences (first 500 checked): {diffs}")
for d in diff_samples:
    print(f"  {d}")
