"""
Turnover Sync Simulation Test
Dry-run test - reads files from OneDrive, processes them, validates data.
Does NOT write to the database.
"""
import os, sys, django, re
sys.path.insert(0, os.path.dirname(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = 'automations.settings'
django.setup()

from django.conf import settings
from dashboard import onedrive_sync
import requests

GRAPH = 'https://graph.microsoft.com/v1.0'
PASS = '  [PASS]'
FAIL = '  [FAIL]'


def section(title):
    print(f'\n{"="*60}')
    print(f'  {title}')
    print(f'{"="*60}')


def check(label, condition, detail=''):
    status = PASS if condition else FAIL
    print(f'{status} {label}' + (f'  ({detail})' if detail else ''))
    return condition


# ── 1. TOKEN ────────────────────────────────────────────────
section('1. OneDrive Token')
token = onedrive_sync.get_access_token()
check('Token obtained', bool(token))

headers = {'Authorization': f'Bearer {token}'}

# ── 2. FOLDER ACCESS ────────────────────────────────────────
section('2. Folder Access')
folder = settings.ONEDRIVE_FOLDER_PATH
url = f'{GRAPH}/me/drive/root:{folder}:/children'
resp = requests.get(url, headers=headers)
check('Folder reachable', resp.status_code == 200, f'HTTP {resp.status_code}')
items = resp.json().get('value', [])
check('Folder has files', len(items) > 0, f'{len(items)} items found')

# ── 3. FILE DETECTION ───────────────────────────────────────
section('3. File Detection (what sync will process)')
archive_files = [f for f in items if 'file' in f and re.match(r'^20\d{2}_', f.get('name',''))]
active_files = [
    f for f in items
    if 'file' in f
    and f['name'].lower().endswith(('.xlsx', '.xls'))
    and not re.match(r'^20\d{2}_', f['name'])
]
print(f'  Archive files (skipped):  {len(archive_files)}')
print(f'  Active files (processed): {len(active_files)}')
for f in active_files:
    print(f'    -> {f["name"]}')
check('Active files found', len(active_files) > 0, 'No files will be synced if 0')

# ── 4. BRANCH DETECTION ─────────────────────────────────────
section('4. Branch Detection')
for f in active_files:
    branch_from_name = onedrive_sync.get_branch(f['name'])
    # Also test file-based detection by downloading and peeking
    content = onedrive_sync.download_file(f['id'])
    branch_from_file = None
    if content and not branch_from_name:
        import openpyxl, io
        content.seek(0)
        try:
            wb = openpyxl.load_workbook(content, data_only=True)
            branch_from_file = onedrive_sync.get_branch_from_file(wb.active)
            content.seek(0)
        except:
            pass
    detected = branch_from_name or branch_from_file
    source = 'filename' if branch_from_name else ('file contents' if branch_from_file else 'NOT FOUND')
    check(f'Branch detected for "{f["name"]}"', detected is not None, f'branch={detected} via {source}')
if not active_files:
    print('  (no active files to test)')

# ── 5. FILE PROCESSING ──────────────────────────────────────
section('5. File Processing (dry-run, no DB writes)')
total_rows = 0
errors = []
results = []

for f in active_files:
    name = f['name']
    content = onedrive_sync.download_file(f['id'])
    if not content:
        errors.append(f'Failed to download: {name}')
        continue

    rows = onedrive_sync.process_excel_file(content, name)

    # Get detected branch from the actual rows
    branch = rows[0][3] if rows else 'NOT DETECTED'

    # Validations
    has_rows       = len(rows) > 0
    correct_fields = all(len(r) == 6 for r in rows)
    has_debtor     = all(r[0] for r in rows)
    has_name       = all(r[1] for r in rows)
    has_date       = all(r[2] for r in rows)
    correct_branch = branch in onedrive_sync.KNOWN_BRANCHES
    has_value      = all(isinstance(r[4], (int, float)) for r in rows)

    missing_names  = sum(1 for r in rows if not r[1])
    dates          = sorted(set(r[2] for r in rows))

    results.append({
        'name': name, 'branch': branch, 'rows': len(rows),
        'missing_names': missing_names, 'dates': dates,
        'ok': has_rows and correct_fields and has_debtor and has_name and correct_branch
    })

    print(f'\n  File: {name}')
    check('  Has records',         has_rows,        f'{len(rows)} rows')
    check('  6-field tuples',      correct_fields,  'debtor,debtor_name,date,branch,value,report_date')
    check('  All have debtor',     has_debtor)
    check('  All have name',       has_name,        f'{missing_names} missing')
    check('  All have date',       has_date)
    check('  Branch correct',      correct_branch,  f'detected={branch}')
    check('  All values are float',has_value)
    if dates:
        print(f'       Date range: {dates[0]} to {dates[-1]}')
    total_rows += len(rows)

# ── 6. SUMMARY ──────────────────────────────────────────────
section('6. Summary')
print(f'  Active files found:  {len(active_files)}')
print(f'  Files processed:     {len(results)}')
print(f'  Total rows extracted:{total_rows}')
print(f'  Errors:              {len(errors)}')
for e in errors:
    print(f'    -> {e}')

all_ok = all(r['ok'] for r in results) and not errors
if all_ok and active_files:
    print('\n  SIMULATION PASSED - Safe to sync')
elif not active_files:
    print('\n  WARNING: No active files to process. Upload files without 20XX_ prefix.')
else:
    print('\n  SIMULATION FAILED - Fix issues above before syncing')

# ── 7. DB CURRENT STATE ─────────────────────────────────────
section('7. Current DB State (read-only)')
from django.db import connection
with connection.cursor() as cur:
    cur.execute('''
        SELECT branch, COUNT(*) as total,
               COUNT(debtor_name) as has_name,
               COUNT(*) - COUNT(debtor_name) as missing,
               MIN(date) as earliest, MAX(date) as latest
        FROM turnover_data GROUP BY branch ORDER BY branch
    ''')
    print(f'  {"Branch":<12} {"Total":<8} {"Has Name":<10} {"Missing":<10} {"Earliest":<12} {"Latest"}')
    print(f'  {"-"*65}')
    for r in cur.fetchall():
        flag = ' <-- NEEDS FIX' if r[3] > 0 else ''
        print(f'  {str(r[0]):<12} {str(r[1]):<8} {str(r[2]):<10} {str(r[3]):<10} {str(r[4]):<12} {str(r[5])}{flag}')
