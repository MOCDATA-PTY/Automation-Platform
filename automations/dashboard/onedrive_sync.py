"""OneDrive sync module for MOC Automations"""
import os
import json
import io
import re
from datetime import datetime
import msal
import requests
from django.conf import settings
from django.db import connection
from psycopg2.extras import execute_values
import openpyxl
import xlrd

# Microsoft Graph API endpoint
GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'

def get_msal_app():
    """Create MSAL application instance"""
    return msal.ConfidentialClientApplication(
        settings.ONEDRIVE_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{settings.ONEDRIVE_TENANT_ID}",
        client_credential=settings.ONEDRIVE_CLIENT_SECRET
    )

def get_access_token():
    """Get access token from saved file or return None"""
    token_file = settings.ONEDRIVE_TOKEN_FILE
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            token_data = json.load(f)
            return token_data.get('access_token')
    return None

def save_token(token_data):
    """Save token data to file"""
    with open(settings.ONEDRIVE_TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)

def get_auth_url():
    """Generate authorization URL for OAuth flow"""
    app = get_msal_app()
    auth_url = app.get_authorization_request_url(
        scopes=settings.ONEDRIVE_SCOPES,
        redirect_uri=settings.ONEDRIVE_REDIRECT_URI
    )
    return auth_url

def acquire_token_by_auth_code(code):
    """Exchange authorization code for access token"""
    app = get_msal_app()
    result = app.acquire_token_by_authorization_code(
        code,
        scopes=settings.ONEDRIVE_SCOPES,
        redirect_uri=settings.ONEDRIVE_REDIRECT_URI
    )
    if "access_token" in result:
        save_token(result)
        return result
    return None

def list_files_in_folder(folder_path='/'):
    """List all files in OneDrive folder recursively"""
    token = get_access_token()
    if not token:
        return []

    headers = {'Authorization': f'Bearer {token}'}

    # Get folder by path
    if folder_path == '/':
        url = f'{GRAPH_API_ENDPOINT}/me/drive/root/children'
    else:
        url = f'{GRAPH_API_ENDPOINT}/me/drive/root:{folder_path}:/children'

    files = []

    def list_folder(folder_url):
        response = requests.get(folder_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('value', []):
                if 'folder' in item:
                    # Recurse into folders
                    list_folder(f"{GRAPH_API_ENDPOINT}/me/drive/items/{item['id']}/children")
                elif 'file' in item:
                    # Add file to list
                    files.append({
                        'id': item['id'],
                        'name': item['name'],
                        'path': item.get('parentReference', {}).get('path', ''),
                        'download_url': item.get('@microsoft.graph.downloadUrl')
                    })

    list_folder(url)
    return files

def download_file(file_id):
    """Download file from OneDrive by file ID"""
    token = get_access_token()
    if not token:
        return None

    headers = {'Authorization': f'Bearer {token}'}
    url = f'{GRAPH_API_ENDPOINT}/me/drive/items/{file_id}/content'

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return io.BytesIO(response.content)
    return None

def get_branch(filename):
    """Extract branch code from filename"""
    branches = ['ATL', 'HEC', 'HNL', 'HOU', 'ICS', 'IMP', 'JFK', 'LAX', 'LCL', 'ORD', 'PPG']
    filename_upper = filename.upper()

    # Check if filename starts with branch code
    for branch in branches:
        if filename_upper.startswith(branch):
            return branch

    # Check if filename contains branch code
    for branch in branches:
        if branch in filename_upper:
            return branch

    return None

def extract_report_date(ws):
    """Extract report date from row 11 (format: 'Printed by Name DD-MMM-YY HH:MM AM/PM')"""
    try:
        import re
        from datetime import datetime

        row11_text = str(ws.cell(row=11, column=2).value) if hasattr(ws, 'cell') else str(ws.row_values(10)[1])

        # Extract date pattern like "05-Jan-26 12:06 AM"
        date_match = re.search(r'(\d{2}-[A-Za-z]{3}-\d{2})\s+(\d{1,2}:\d{2}\s+[AP]M)', row11_text)
        if date_match:
            date_str = date_match.group(1)
            time_str = date_match.group(2)
            report_date = datetime.strptime(f"{date_str} {time_str}", "%d-%b-%y %I:%M %p")
            return report_date.strftime('%Y-%m-%d')
    except:
        pass
    return None

def process_excel_file(file_content, filename):
    """Process Excel file and return data rows with report date"""
    branch = get_branch(filename)
    if not branch:
        return []

    rows = []

    try:
        # Try openpyxl for .xlsx
        wb = openpyxl.load_workbook(file_content, data_only=True)
        ws = wb.active

        # Extract report date from row 11
        report_date = extract_report_date(ws)

        # Check if this is WIDE format (header row with month columns)
        # Row 13 should have: Debtor, Debtor Name, TOTAL, 202501, 202502, etc.
        header_row = [ws.cell(row=13, column=i).value for i in range(4, 20)]

        # Check if we have month columns (202501, 202502, etc.)
        month_columns = []
        for col_idx, val in enumerate(header_row, start=4):
            if isinstance(val, int) and 202000 <= val <= 209912:  # Valid YYYYMM
                month_columns.append((col_idx, val))

        if month_columns:
            # WIDE FORMAT: Pivot data from columns to rows
            print(f"  Processing WIDE format with {len(month_columns)} month columns")

            # Process data rows (starting from row 14)
            for row_idx in range(14, ws.max_row + 1):
                debtor = ws.cell(row=row_idx, column=4).value  # Column D = Debtor
                if not debtor:
                    continue

                debtor = str(debtor).strip()

                # Process each month column
                for col_idx, month_val in month_columns:
                    value = ws.cell(row=row_idx, column=col_idx).value

                    if value and isinstance(value, (int, float)) and value != 0:
                        # Convert month to date string
                        year = month_val // 100
                        month = month_val % 100
                        date_str = f"{year:04d}-{month:02d}-01"

                        rows.append((debtor, date_str, branch, value, report_date))

        else:
            # LONG FORMAT: Original processing (one row per value)
            print(f"  Processing LONG format")
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row and len(row) >= 4 and row[0]:
                    debtor = str(row[0]).strip() if row[0] else None
                    date_val = row[2] if len(row) > 2 else None
                    value = float(row[3]) if len(row) > 3 and row[3] else 0

                    if not debtor or not date_val:
                        continue

                    # Parse date
                    if isinstance(date_val, datetime):
                        date_str = date_val.strftime('%Y-%m-%d')
                    elif isinstance(date_val, (int, float)):
                        date_int = int(date_val)
                        year = date_int // 100
                        month = date_int % 100
                        date_str = f"{year:04d}-{month:02d}-01"
                    else:
                        try:
                            date_int = int(str(date_val).strip())
                            year = date_int // 100
                            month = date_int % 100
                            date_str = f"{year:04d}-{month:02d}-01"
                        except:
                            date_str = str(date_val) if date_val else None

                    if debtor and date_str and value != 0:
                        rows.append((debtor, date_str, branch, value, report_date))

    except Exception as e:
        print(f"  Error with openpyxl: {e}, trying xlrd...")
        # Try xlrd for .xls
        try:
            file_content.seek(0)
            wb = xlrd.open_workbook(file_contents=file_content.read())
            ws = wb.sheet_by_index(0)

            report_date = extract_report_date(ws)

            # Check for wide format
            header_row = ws.row_values(12)  # Row 13 (0-indexed as 12)
            month_columns = []
            for col_idx, val in enumerate(header_row[3:19], start=3):
                if isinstance(val, (int, float)) and 202000 <= val <= 209912:
                    month_columns.append((col_idx, int(val)))

            if month_columns:
                # WIDE FORMAT
                for row_idx in range(13, ws.nrows):  # Row 14+ (0-indexed as 13+)
                    row = ws.row_values(row_idx)
                    debtor = row[3] if len(row) > 3 else None
                    if not debtor:
                        continue

                    debtor = str(debtor).strip()

                    for col_idx, month_val in month_columns:
                        value = row[col_idx] if len(row) > col_idx else None
                        if value and isinstance(value, (int, float)) and value != 0:
                            year = month_val // 100
                            month = month_val % 100
                            date_str = f"{year:04d}-{month:02d}-01"
                            rows.append((debtor, date_str, branch, value, report_date))
            else:
                # LONG FORMAT
                for row_idx in range(1, ws.nrows):
                    row = ws.row_values(row_idx)
                    if row and len(row) >= 4 and row[0]:
                        debtor = str(row[0]).strip() if row[0] else None
                        date_val = row[2] if len(row) > 2 else None
                        value = float(row[3]) if len(row) > 3 and row[3] else 0

                        if not debtor or not date_val:
                            continue

                        if isinstance(date_val, (int, float)):
                            date_int = int(date_val)
                            year = date_int // 100
                            month = date_int % 100
                            date_str = f"{year:04d}-{month:02d}-01"
                        else:
                            try:
                                date_int = int(str(date_val).strip())
                                year = date_int // 100
                                month = date_int % 100
                                date_str = f"{year:04d}-{month:02d}-01"
                            except:
                                date_str = str(date_val)

                        if debtor and date_str and value != 0:
                            rows.append((debtor, date_str, branch, value, report_date))
        except Exception as e:
            print(f"  Error processing {filename}: {e}")
            return []

    return rows

def sync_turnover_data():
    """Sync turnover data from OneDrive to PostgreSQL"""
    folder_path = settings.ONEDRIVE_FOLDER_PATH
    files = list_files_in_folder(folder_path)

    # Filter Excel files, skip historical year archives (20XX_*.xlsx)
    excel_files = [
        f for f in files
        if f['name'].lower().endswith(('.xlsx', '.xls'))
        and not re.match(r'^20\d{2}_', f['name'])  # Skip 2020_ATL.xlsx, 2021_HNL.xlsx, etc.
    ]

    all_rows = []

    for file_info in excel_files:
        print(f"Processing {file_info['name']}...")
        file_content = download_file(file_info['id'])

        if file_content:
            rows = process_excel_file(file_content, file_info['name'])
            all_rows.extend(rows)
            print(f"  Extracted {len(rows)} records")

    # Upsert to database with report date tracking
    if all_rows:
        with connection.cursor() as cur:
            # New query that only updates if the new report is newer (or if no report_date exists)
            query = """
                INSERT INTO turnover_data (debtor, date, branch, value, report_date)
                VALUES %s
                ON CONFLICT (debtor, date, branch)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    report_date = EXCLUDED.report_date
                WHERE
                    turnover_data.report_date IS NULL
                    OR EXCLUDED.report_date IS NULL
                    OR EXCLUDED.report_date >= turnover_data.report_date
            """
            execute_values(cur, query, all_rows)
        print(f"\n✓ Total: {len(all_rows)} records processed")
    else:
        print(f"\n✓ No new files to sync")

    # Always save last sync time (even if no new records)
    last_sync = {'last_sync': datetime.now().isoformat()}
    with open(settings.LAST_SYNC_FILE, 'w') as f:
        json.dump(last_sync, f)

    return len(all_rows)
