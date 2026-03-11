"""Test with completely fresh email - different subject, content, and approach."""
import msal
import requests

CLIENT_ID = '43fbe5a9-6b5b-4c81-9067-7aff9ac3ed5a'
TENANT_ID = 'b1504b1d-d096-409a-a0f0-6cc546dde993'
CLIENT_SECRET = 'w6B8Q~W3ac9klXa8NkMDo4cPNyOsjEryVL5TwdhQ'
MAILBOX = 'waldogaybba@moc-pty.com'
TO_EMAIL = 'ethansevenster5@gmail.com'

app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=f'https://login.microsoftonline.com/{TENANT_ID}',
    client_credential=CLIENT_SECRET
)
result = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])
token = result['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Step 1: First, check the DKIM status by examining what headers Microsoft adds
# Create a draft, read it back, then send - so we can see the internet message headers
print("Step 1: Creating draft to check headers...")
draft = {
    "subject": "Shipping Documents Ready for Collection",
    "body": {
        "contentType": "HTML",
        "content": """<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Calibri, Arial, sans-serif; font-size: 11pt; color: #000000;">
<p>Good day,</p>

<p>Please be advised that your shipping documents are ready for collection at our office.</p>

<p>Should you require any further assistance, please do not hesitate to contact us.</p>

<p>Kind regards,</p>
<p><b>Waldo Gaybba</b><br>
Magnum Opus Consultants (Pty) Ltd<br>
Tel: +27 11 000 0000<br>
Email: <a href="mailto:waldogaybba@moc-pty.com">waldogaybba@moc-pty.com</a></p>
</body>
</html>"""
    },
    "toRecipients": [
        {"emailAddress": {"address": TO_EMAIL, "name": "Ethan Sevenster"}}
    ],
    "importance": "normal"
}

rd = requests.post(
    f'https://graph.microsoft.com/v1.0/users/{MAILBOX}/messages',
    headers=headers, json=draft
)

if rd.status_code == 201:
    msg_id = rd.json()['id']
    print(f"Draft created: {msg_id[:30]}...")
    
    # Send the draft
    rs = requests.post(
        f'https://graph.microsoft.com/v1.0/users/{MAILBOX}/messages/{msg_id}/send',
        headers={'Authorization': f'Bearer {token}'}
    )
    print(f"Send status: {rs.status_code} {'SUCCESS' if rs.status_code == 202 else rs.text[:300]}")
else:
    print(f"Draft failed: {rd.status_code} {rd.text[:300]}")

print()
print("=" * 60)
print("IMPORTANT: In Gmail, open the email (even if in spam)")
print("Click the 3 dots menu (top right of email) -> 'Show original'")
print("Look for these lines:")
print("  dkim=pass  --> DKIM is working")
print("  dkim=fail  --> DKIM is NOT signing yet")
print("  spf=pass   --> SPF is working")
print("=" * 60)
print()
print("Subject to look for: 'Shipping Documents Ready for Collection'")
