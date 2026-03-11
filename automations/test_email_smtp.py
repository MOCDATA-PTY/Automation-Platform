"""Test email via SMTP with OAuth2 + try alternative approaches."""
import msal
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import time

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

# ── Method A: SMTP with OAuth2 ─────────────────────────────────────────────
print("=" * 60)
print("METHOD A: SMTP AUTH via smtp.office365.com with OAuth2")
print("=" * 60)
try:
    # Get SMTP token
    smtp_result = app.acquire_token_for_client(scopes=['https://outlook.office365.com/.default'])
    if 'access_token' in smtp_result:
        smtp_token = smtp_result['access_token']
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f'Waldo Gaybba <{MAILBOX}>'
        msg['To'] = TO_EMAIL
        msg['Subject'] = 'SMTP Test - Magnum Opus Consultants'
        
        text = "Hi Ethan,\n\nThis is a test via SMTP.\n\nBest,\nWaldo Gaybba\nMagnum Opus Consultants"
        html = """<html><body style="font-family:Arial,sans-serif;font-size:14px;">
<p>Hi Ethan,</p><p>This is a test via SMTP.</p>
<p>Best,<br><strong>Waldo Gaybba</strong><br>Magnum Opus Consultants</p>
</body></html>"""
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        # XOAUTH2 string
        auth_string = f'user={MAILBOX}\x01auth=Bearer {smtp_token}\x01\x01'
        
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.docmd('AUTH', 'XOAUTH2 ' + base64.b64encode(auth_string.encode()).decode())
        server.sendmail(MAILBOX, [TO_EMAIL], msg.as_string())
        server.quit()
        print("SUCCESS via SMTP!")
    else:
        print(f"SMTP token error: {smtp_result.get('error')}")
except Exception as e:
    print(f"SMTP failed: {e}")

time.sleep(2)

# ── Method B: List all users we can send as ─────────────────────────────────
print("\n" + "=" * 60)
print("METHOD B: Check what other mailboxes exist in the tenant")
print("=" * 60)

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Try to list users (needs User.Read.All but let's check)
r = requests.get(
    'https://graph.microsoft.com/v1.0/users?$select=displayName,mail,userPrincipalName&$top=20',
    headers=headers
)
if r.status_code == 200:
    users = r.json().get('value', [])
    print(f"Found {len(users)} users in tenant:")
    for u in users:
        print(f"  - {u.get('displayName', 'N/A')} | {u.get('mail', 'N/A')} | {u.get('userPrincipalName', 'N/A')}")
    
    # Try sending from the first user that isn't the shared mailbox
    for u in users:
        alt_mail = u.get('mail') or u.get('userPrincipalName', '')
        if alt_mail and alt_mail != MAILBOX and '@moc-pty.com' in alt_mail:
            print(f"\nTrying to send from: {alt_mail}")
            email_alt = {
                "message": {
                    "subject": f"Test from {u.get('displayName', alt_mail)}",
                    "body": {
                        "contentType": "HTML",
                        "content": f"""<html><body style="font-family:Arial,sans-serif;font-size:14px;">
<p>Hi Ethan,</p><p>Test email sent from {u.get('displayName', alt_mail)}.</p>
<p>Best regards,<br><strong>{u.get('displayName', '')}</strong><br>Magnum Opus Consultants</p>
</body></html>"""
                    },
                    "from": {
                        "emailAddress": {"address": alt_mail, "name": u.get('displayName', '')}
                    },
                    "toRecipients": [
                        {"emailAddress": {"address": TO_EMAIL}}
                    ]
                },
                "saveToSentItems": "true"
            }
            ra = requests.post(
                f'https://graph.microsoft.com/v1.0/users/{alt_mail}/sendMail',
                headers=headers, json=email_alt
            )
            print(f"  Status: {ra.status_code} {'SUCCESS' if ra.status_code == 202 else ra.text[:300]}")
            break
else:
    print(f"Cannot list users: {r.status_code} - {r.text[:300]}")

print("\n" + "=" * 60)
print("Check inbox AND spam:")
print("  A. Subject: 'SMTP Test - Magnum Opus Consultants'")
print("  B. Subject: 'Test from [user name]' (if another user was found)")
print("=" * 60)
