#!/usr/bin/env python3
"""Test login and page access to find 500 errors."""
import requests

BASE_URL = "https://workspace.moc-pty.com"
USERNAME = "Ethan"
PASSWORD = "4269875321"

session = requests.Session()

# Step 1: GET login page to get CSRF token
print("1. Fetching login page...")
r = session.get(f"{BASE_URL}/login/", verify=False)
print(f"   Status: {r.status_code}")

csrf_token = session.cookies.get('csrftoken')
print(f"   CSRF token: {csrf_token}")

# Step 2: POST login
print("\n2. Logging in...")
r = session.post(f"{BASE_URL}/login/", data={
    'username': USERNAME,
    'password': PASSWORD,
    'csrfmiddlewaretoken': csrf_token,
}, headers={'Referer': f"{BASE_URL}/login/"}, verify=False, allow_redirects=True)
print(f"   Status: {r.status_code}")
print(f"   Final URL: {r.url}")

if r.status_code == 500:
    print("\n   *** 500 ERROR ON LOGIN ***")
    # Print the error text
    lines = r.text.split('\n')
    for line in lines:
        if any(k in line for k in ['Error', 'Exception', 'Traceback', 'line', 'File']):
            print(f"   {line.strip()}")

# Step 3: Test all main pages
pages = [
    ('Home', '/'),
    ('Sync Monitor', '/monitor/'),
    ('Turnover', '/turnover/'),
    ('PNL', '/pnl/'),
    ('ATL', '/atl/'),
    ('CCC', '/ccc/'),
    ('CCD', '/ccd/'),
    ('CON', '/con/'),
    ('DOR', '/dor/'),
    ('FAX', '/fax/'),
    ('HNL', '/hnl/'),
    ('HOU', '/hou/'),
    ('ICS', '/ics/'),
    ('IMP', '/imp/'),
    ('JFK', '/jfk/'),
    ('LAX', '/lax/'),
    ('LCL', '/lcl/'),
    ('ORD', '/ord/'),
    ('PPG', '/ppg/'),
    ('Creditor', '/creditor/'),
    ('PowerBI Embed API', '/powerbi/embed/?page=ppg'),
]

print("\n3. Testing pages...")
print(f"   {'Page':<25} {'Status'}")
print(f"   {'-'*25} {'-'*6}")
errors = []
for name, path in pages:
    r = session.get(f"{BASE_URL}{path}", verify=False, allow_redirects=True)
    status = r.status_code
    mark = "OK" if status == 200 else "!!"
    print(f"   {mark} {name:<24} {status}")
    if status >= 400:
        errors.append((name, path, status, r.text[:500]))

if errors:
    print("\n*** ERRORS FOUND ***")
    for name, path, status, text in errors:
        print(f"\n{name} ({path}) - HTTP {status}:")
        for line in text.split('\n'):
            if line.strip():
                print(f"  {line.strip()}")
        print()
else:
    print("\n   All pages OK")

# Step 4: Test Power BI embed save/load/clear
print("\n4. Testing Power BI embed API...")
TEST_PAGE = 'turnover'
TEST_URL = 'https://app.powerbi.com/reportEmbed?reportId=test-report-id-12345'

def get_csrf():
    return session.cookies.get('csrftoken')

# 4a: GET before save (should return empty)
r = session.get(f"{BASE_URL}/powerbi/embed/?page={TEST_PAGE}", verify=False)
data = r.json()
print(f"   GET before save:  status={r.status_code}  embed_url='{data.get('embed_url', '')}'")
assert r.status_code == 200, f"Expected 200, got {r.status_code}"
assert data.get('embed_url') == '' or data.get('embed_url') is not None, "Missing embed_url key"

# 4b: POST save a URL
r = session.post(
    f"{BASE_URL}/powerbi/embed/save/",
    headers={'Content-Type': 'application/json', 'X-CSRFToken': get_csrf(), 'Referer': BASE_URL},
    json={'page': TEST_PAGE, 'embed_url': TEST_URL},
    verify=False
)
print(f"   POST save:        status={r.status_code}  response={r.text[:80]}")
assert r.status_code == 200, f"Expected 200, got {r.status_code}"
assert r.json().get('status') == 'ok', f"Expected ok, got {r.json()}"

# 4c: GET after save (should return the URL)
r = session.get(f"{BASE_URL}/powerbi/embed/?page={TEST_PAGE}", verify=False)
data = r.json()
print(f"   GET after save:   status={r.status_code}  embed_url='{data.get('embed_url', '')[:60]}...'")
assert data.get('embed_url') == TEST_URL, f"URL mismatch: {data.get('embed_url')}"

# 4d: POST clear (empty URL)
r = session.post(
    f"{BASE_URL}/powerbi/embed/save/",
    headers={'Content-Type': 'application/json', 'X-CSRFToken': get_csrf(), 'Referer': BASE_URL},
    json={'page': TEST_PAGE, 'embed_url': ''},
    verify=False
)
print(f"   POST clear:       status={r.status_code}  response={r.text[:80]}")
assert r.json().get('status') == 'ok'

# 4e: GET after clear (should return empty)
r = session.get(f"{BASE_URL}/powerbi/embed/?page={TEST_PAGE}", verify=False)
data = r.json()
print(f"   GET after clear:  status={r.status_code}  embed_url='{data.get('embed_url', '')}'")
assert data.get('embed_url') == '', f"Expected empty, got {data.get('embed_url')}"

print("\n   Power BI embed API: PASS - save, retrieve, and clear all work correctly")
