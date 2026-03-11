"""Import US-EU contacts from CSV into database."""
import os, sys, csv, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'automations.settings'
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from dashboard.models import USEUContact

csv_path = os.path.join(os.path.dirname(__file__), 'US-EU List.csv.bak')

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    print('CSV columns:', reader.fieldnames)

    batch = []
    count = 0
    for row in reader:
        email_val = (row.get('Email') or '').strip()
        # Clean email: some have format "Name <email>" - extract just the email
        if '<' in email_val and '>' in email_val:
            email_val = email_val.split('<')[1].split('>')[0].strip()

        contact = USEUContact(
            org_name=(row.get('Org. Name') or '').strip(),
            default=(row.get('Default') or '').strip(),
            contact_name=(row.get('Contact Name') or '').strip(),
            attach=(row.get('Attach') or '').strip(),
            phone=str(row.get('Phone') or '').strip(),
            email=email_val,
            touchpoint_1=(row.get('Touchpoint 1') or '').strip(),
            tp1_sent_on=(row.get('TP1 Sent On') or '').strip(),
            touchpoint_2=(row.get('Touchpoint 2') or '').strip(),
            last_touch=(row.get('Last Touch Date') or '').strip(),
            journey_status=(row.get('Journey Status') or 'Active').strip(),
            status=(row.get('Journey Status') or 'Active').strip(),
            tp1_processing_id=(row.get('TP1ProcessingId') or '').strip(),
        )
        batch.append(contact)
        count += 1

        if len(batch) >= 1000:
            USEUContact.objects.bulk_create(batch)
            print(f'  Imported {count} contacts...')
            batch = []

    if batch:
        USEUContact.objects.bulk_create(batch)

    print(f'Done! Imported {count} contacts total.')
    print(f'DB count: {USEUContact.objects.count()}')
