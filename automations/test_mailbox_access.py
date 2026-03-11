"""Quick test: can our Azure app access waldogaybba@moc-pty.com mailbox?"""
import msal
import requests

CLIENT_ID = '43fbe5a9-6b5b-4c81-9067-7aff9ac3ed5a'
TENANT_ID = 'b1504b1d-d096-409a-a0f0-6cc546dde993'
CLIENT_SECRET = 'w6B8Q~W3ac9klXa8NkMDo4cPNyOsjEryVL5TwdhQ'
MAILBOX = 'waldogaybba@moc-pty.com'

app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=f'https://login.microsoftonline.com/{TENANT_ID}',
    client_credential=CLIENT_SECRET
)

result = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])

if 'access_token' not in result:
    print(f"Token error: {result.get('error')}: {result.get('error_description')}")
    exit(1)

print("Got access token successfully")
token = result['access_token']
headers = {'Authorization': f'Bearer {token}'}

# 1) Look up the user
r = requests.get(f'https://graph.microsoft.com/v1.0/users/{MAILBOX}', headers=headers)
print(f"\n--- User lookup: {r.status_code} ---")
if r.status_code == 200:
    d = r.json()
    print(f"  Display Name : {d.get('displayName', 'N/A')}")
    print(f"  Mail         : {d.get('mail', 'N/A')}")
    print(f"  UPN          : {d.get('userPrincipalName', 'N/A')}")
else:
    print(f"  Error: {r.text[:400]}")

# 2) Try reading inbox
r2 = requests.get(
    f'https://graph.microsoft.com/v1.0/users/{MAILBOX}/messages?$top=3&$select=subject,from,receivedDateTime',
    headers=headers
)
print(f"\n--- Inbox access: {r2.status_code} ---")
if r2.status_code == 200:
    msgs = r2.json().get('value', [])
    print(f"  Found {len(msgs)} recent messages:")
    for m in msgs:
        subj = m.get('subject', '(no subject)')
        frm = m.get('from', {}).get('emailAddress', {}).get('address', '')
        dt = m.get('receivedDateTime', '')
        print(f"    - {subj}  |  from: {frm}  |  {dt}")
else:
    print(f"  Error: {r2.text[:400]}")

# 3) Check sent items (proxy for Mail.Send permission)
r3 = requests.get(
    f'https://graph.microsoft.com/v1.0/users/{MAILBOX}/mailFolders/sentitems/messages?$top=1&$select=subject',
    headers=headers
)
print(f"\n--- Sent folder access: {r3.status_code} ---")
if r3.status_code == 200:
    print("  OK - Mail.Send should work for this mailbox")
else:
    print(f"  Error: {r3.text[:400]}")
