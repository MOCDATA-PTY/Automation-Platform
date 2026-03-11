"""Test sending TP1 to ethansevenster5@gmail.com via local dev server."""
import requests

s = requests.Session()

# 1. Get login page for CSRF
r = s.get('http://127.0.0.1:8000/login/')
csrf = s.cookies.get('csrftoken', '')
print(f"CSRF token: {csrf[:20]}...")

# 2. Login
r = s.post('http://127.0.0.1:8000/login/', data={
    'username': 'Ethan',
    'password': '4269875321',
    'csrfmiddlewaretoken': csrf,
}, headers={'Referer': 'http://127.0.0.1:8000/login/'}, allow_redirects=False)
print(f"Login response: {r.status_code} Location: {r.headers.get('Location', 'none')}")

# Follow redirect manually
if r.status_code in (301, 302):
    r = s.get('http://127.0.0.1:8000' + r.headers['Location'])
    print(f"After redirect: {r.status_code} {r.url}")

# 3. Send TP1 to test email
csrf = s.cookies.get('csrftoken', '')
r = s.post('http://127.0.0.1:8000/email-templates/send/', json={
    'touchpoint_number': 1,
    'recipients': ['ethansevenster5@gmail.com'],
}, headers={
    'X-CSRFToken': csrf,
    'Referer': 'http://127.0.0.1:8000/',
})
print(f"\nSend result: {r.status_code}")
print(r.text)
