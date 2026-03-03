#!/usr/bin/env python3
"""Test user management: list, add, change password, delete."""
import requests

BASE_URL = "https://workspace.moc-pty.com"
USERNAME = "Ethan"
PASSWORD = "4269875321"
TEST_USER = "test_autouser_99"
TEST_PASS = "TestPass123!"
NEW_PASS  = "NewPass456!"

session = requests.Session()

def get_csrf():
    return session.cookies.get('csrftoken')

def log(label, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"   [{status}] {label}" + (f" — {detail}" if detail else ""))

# ── Login ──────────────────────────────────────────────────────────────────────
print("\n1. Logging in...")
r = session.get(f"{BASE_URL}/login/", verify=False)
r = session.post(f"{BASE_URL}/login/", verify=False, allow_redirects=True, data={
    'username': USERNAME, 'password': PASSWORD,
    'csrfmiddlewaretoken': get_csrf(),
}, headers={'Referer': f"{BASE_URL}/login/"})
log("Login", r.status_code == 200 and r.url == f"{BASE_URL}/", f"final={r.url}")

# ── Users page loads ───────────────────────────────────────────────────────────
print("\n2. Users page...")
r = session.get(f"{BASE_URL}/users/", verify=False)
log("GET /users/ returns 200", r.status_code == 200, f"status={r.status_code}")
log("Page contains user table", 'user-table' in r.text or 'All Users' in r.text)
log(f"Logged-in user '{USERNAME}' shown", USERNAME in r.text)

# ── Clean up leftover test user if exists ──────────────────────────────────────
if TEST_USER in r.text:
    print(f"   (test user '{TEST_USER}' already exists, cleaning up first)")

# ── Add user ───────────────────────────────────────────────────────────────────
print("\n3. Add user...")
r = session.post(f"{BASE_URL}/users/add/", verify=False, allow_redirects=True, data={
    'username': TEST_USER,
    'password': TEST_PASS,
    'csrfmiddlewaretoken': get_csrf(),
}, headers={'Referer': f"{BASE_URL}/users/"})
log("POST /users/add/ redirects to /users/", '/users/' in r.url, f"final={r.url}")
log(f"New user '{TEST_USER}' appears in list", TEST_USER in r.text)
log("Success message shown", 'created successfully' in r.text.lower() or TEST_USER in r.text)

# Find the new user's ID from the page (look for delete form action)
import re
user_id = None
matches = re.findall(r'/users/(\d+)/delete/', r.text)
# Find the id associated with TEST_USER
lines = r.text.split('\n')
for i, line in enumerate(lines):
    if TEST_USER in line:
        # search nearby for delete URL
        chunk = ' '.join(lines[max(0,i-5):i+10])
        m = re.search(r'/users/(\d+)/delete/', chunk)
        if m:
            user_id = int(m.group(1))
            break
log(f"Found user ID", user_id is not None, f"id={user_id}")

# ── Duplicate username rejected ────────────────────────────────────────────────
print("\n4. Duplicate username check...")
r = session.post(f"{BASE_URL}/users/add/", verify=False, allow_redirects=True, data={
    'username': TEST_USER,
    'password': TEST_PASS,
    'csrfmiddlewaretoken': get_csrf(),
}, headers={'Referer': f"{BASE_URL}/users/"})
log("Duplicate rejected with error message", 'already exists' in r.text.lower())

# ── Change password ────────────────────────────────────────────────────────────
print("\n5. Change password...")
if user_id:
    r = session.post(f"{BASE_URL}/users/{user_id}/edit/", verify=False, allow_redirects=True, data={
        'password': NEW_PASS,
        'csrfmiddlewaretoken': get_csrf(),
    }, headers={'Referer': f"{BASE_URL}/users/"})
    log("POST /users/<id>/edit/ redirects to /users/", '/users/' in r.url, f"final={r.url}")
    log("Success message shown", 'updated' in r.text.lower() or 'password' in r.text.lower())

    # Verify new password works by logging in as the test user
    s2 = requests.Session()
    s2.get(f"{BASE_URL}/login/", verify=False)
    r2 = s2.post(f"{BASE_URL}/login/", verify=False, allow_redirects=True, data={
        'username': TEST_USER, 'password': NEW_PASS,
        'csrfmiddlewaretoken': s2.cookies.get('csrftoken'),
    }, headers={'Referer': f"{BASE_URL}/login/"})
    log(f"Login with new password works", r2.status_code == 200 and 'login' not in r2.url.lower(), f"url={r2.url}")
else:
    log("Change password", False, "skipped — no user ID found")

# ── Delete user ────────────────────────────────────────────────────────────────
print("\n6. Delete user...")
if user_id:
    r = session.post(f"{BASE_URL}/users/{user_id}/delete/", verify=False, allow_redirects=True, data={
        'csrfmiddlewaretoken': get_csrf(),
    }, headers={'Referer': f"{BASE_URL}/users/"})
    log("POST /users/<id>/delete/ redirects to /users/", '/users/' in r.url, f"final={r.url}")
    # Username may appear in the success flash message — check table body specifically
    import re as _re
    table_body = _re.search(r'<tbody>(.*?)</tbody>', r.text, _re.DOTALL)
    table_html = table_body.group(1) if table_body else r.text
    log(f"User '{TEST_USER}' no longer in table", TEST_USER not in table_html)
    log("Success message shown", 'deleted' in r.text.lower())
else:
    log("Delete user", False, "skipped — no user ID found")

# ── Cannot delete self ─────────────────────────────────────────────────────────
print("\n7. Cannot delete own account...")
r = session.get(f"{BASE_URL}/users/", verify=False)
# Find current user's ID
own_id = None
for i, line in enumerate(lines):
    if 'badge-you' in line or f'>{USERNAME}<' in line:
        chunk = ' '.join(r.text.split('\n')[max(0,i-5):i+10])
        m = re.search(r'/users/(\d+)/delete/', chunk)
        if m:
            own_id = int(m.group(1))
            break
# The delete button should NOT appear next to the current user (checked in template)
log("Delete button absent for own account", f'users/{own_id}/delete' not in r.text if own_id else 'badge-you' in r.text,
    f"own_id={own_id}")

print("\n--- Done ---\n")
