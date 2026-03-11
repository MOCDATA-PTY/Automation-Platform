"""Test different email sending methods to avoid spam filters."""
import msal
import requests
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
if 'access_token' not in result:
    print(f"Token error: {result.get('error')}: {result.get('error_description')}")
    exit(1)

token = result['access_token']
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# ── Method 1: HTML email with proper structure ──────────────────────────────
print("=" * 60)
print("METHOD 1: Professional HTML email with display name")
print("=" * 60)

email1 = {
    "message": {
        "subject": "Invoice Follow-Up - Magnum Opus Consultants",
        "body": {
            "contentType": "HTML",
            "content": """<html>
<head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head>
<body style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
<p>Dear Customer,</p>
<p>I hope this email finds you well. This is a follow-up regarding your recent inquiry.</p>
<p>Please do not hesitate to reach out if you have any questions.</p>
<br>
<p>Kind regards,</p>
<p><strong>Waldo Gaybba</strong><br>
Magnum Opus Consultants (Pty) Ltd<br>
Email: waldogaybba@moc-pty.com</p>
</body>
</html>"""
        },
        "from": {
            "emailAddress": {
                "address": MAILBOX,
                "name": "Waldo Gaybba - Magnum Opus Consultants"
            }
        },
        "toRecipients": [
            {"emailAddress": {"address": TO_EMAIL, "name": "Ethan Sevenster"}}
        ],
        "replyTo": [
            {"emailAddress": {"address": MAILBOX, "name": "Waldo Gaybba"}}
        ]
    },
    "saveToSentItems": "true"
}

r1 = requests.post(
    f'https://graph.microsoft.com/v1.0/users/{MAILBOX}/sendMail',
    headers=headers, json=email1
)
print(f"Status: {r1.status_code} {'SUCCESS' if r1.status_code == 202 else r1.text[:300]}")

time.sleep(3)

# ── Method 2: Plain text, personal tone ─────────────────────────────────────
print("\n" + "=" * 60)
print("METHOD 2: Plain text personal email")
print("=" * 60)

email2 = {
    "message": {
        "subject": "Quick question about your account",
        "body": {
            "contentType": "Text",
            "content": "Hi Ethan,\n\nJust wanted to check in and see if you received my previous message.\n\nLet me know if you need any help.\n\nBest regards,\nWaldo Gaybba\nMagnum Opus Consultants\nwaldogaybba@moc-pty.com"
        },
        "from": {
            "emailAddress": {
                "address": MAILBOX,
                "name": "Waldo Gaybba"
            }
        },
        "toRecipients": [
            {"emailAddress": {"address": TO_EMAIL}}
        ]
    },
    "saveToSentItems": "true"
}

r2 = requests.post(
    f'https://graph.microsoft.com/v1.0/users/{MAILBOX}/sendMail',
    headers=headers, json=email2
)
print(f"Status: {r2.status_code} {'SUCCESS' if r2.status_code == 202 else r2.text[:300]}")

time.sleep(3)

# ── Method 3: MIME message with custom headers ──────────────────────────────
print("\n" + "=" * 60)
print("METHOD 3: Raw MIME with custom headers (List-Unsubscribe, etc.)")
print("=" * 60)

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

msg = MIMEMultipart('alternative')
msg['From'] = f'Waldo Gaybba <{MAILBOX}>'
msg['To'] = TO_EMAIL
msg['Subject'] = 'Meeting Follow-Up - Magnum Opus Consultants'
msg['Reply-To'] = MAILBOX
msg['X-Mailer'] = 'MOC-Automations/1.0'

text_part = MIMEText(
    "Hi Ethan,\n\nThank you for your time today. Looking forward to hearing from you.\n\nBest,\nWaldo Gaybba\nMagnum Opus Consultants",
    'plain'
)
html_part = MIMEText(
    """<html><body style="font-family: Arial, sans-serif; font-size: 14px;">
<p>Hi Ethan,</p>
<p>Thank you for your time today. Looking forward to hearing from you.</p>
<p>Best,<br><strong>Waldo Gaybba</strong><br>Magnum Opus Consultants</p>
</body></html>""",
    'html'
)
msg.attach(text_part)
msg.attach(html_part)

mime_content = base64.b64encode(msg.as_bytes()).decode('utf-8')

r3 = requests.post(
    f'https://graph.microsoft.com/v1.0/users/{MAILBOX}/sendMail',
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'text/plain'
    },
    data=mime_content
)
# MIME send uses a different endpoint - try the /messages approach
if r3.status_code != 202:
    # Try creating a draft then sending
    draft_headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    email3 = {
        "subject": "Meeting Follow-Up - Magnum Opus Consultants",
        "body": {
            "contentType": "HTML",
            "content": """<html><body style="font-family: Arial, sans-serif; font-size: 14px;">
<p>Hi Ethan,</p>
<p>Thank you for your time today. Looking forward to hearing from you.</p>
<p>Best,<br><strong>Waldo Gaybba</strong><br>Magnum Opus Consultants</p>
</body></html>"""
        },
        "from": {
            "emailAddress": {"address": MAILBOX, "name": "Waldo Gaybba"}
        },
        "toRecipients": [
            {"emailAddress": {"address": TO_EMAIL}}
        ],
        "importance": "normal",
        "inferenceClassification": "focused"
    }
    # Create draft
    rd = requests.post(
        f'https://graph.microsoft.com/v1.0/users/{MAILBOX}/messages',
        headers=draft_headers, json=email3
    )
    if rd.status_code == 201:
        msg_id = rd.json()['id']
        # Send the draft
        rs = requests.post(
            f'https://graph.microsoft.com/v1.0/users/{MAILBOX}/messages/{msg_id}/send',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f"Draft+Send Status: {rs.status_code} {'SUCCESS' if rs.status_code == 202 else rs.text[:300]}")
    else:
        print(f"Draft creation failed: {rd.status_code} {rd.text[:300]}")
else:
    print(f"Status: {r3.status_code} SUCCESS")

print("\n" + "=" * 60)
print("All methods sent. Check inbox AND spam for 3 emails.")
print("Subject lines to look for:")
print("  1. 'Invoice Follow-Up - Magnum Opus Consultants'")
print("  2. 'Quick question about your account'")
print("  3. 'Meeting Follow-Up - Magnum Opus Consultants'")
print("=" * 60)
