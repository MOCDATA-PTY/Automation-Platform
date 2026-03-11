"""Send fresh email and ask to check headers."""
import msal
import requests

CLIENT_ID = '43fbe5a9-6b5b-4c81-9067-7aff9ac3ed5a'
TENANT_ID = 'b1504b1d-d096-409a-a0f0-6cc546dde993'
CLIENT_SECRET = 'w6B8Q~W3ac9klXa8NkMDo4cPNyOsjEryVL5TwdhQ'
MAILBOX = 'waldogaybba@moc-pty.com'
TO_EMAIL = 'anthony.penzes@eclick.co.za'

app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=f'https://login.microsoftonline.com/{TENANT_ID}',
    client_credential=CLIENT_SECRET
)
result = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])
token = result['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

email = {
    "message": {
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
        "from": {
            "emailAddress": {"address": MAILBOX, "name": "Waldo Gaybba"}
        },
        "toRecipients": [
            {"emailAddress": {"address": TO_EMAIL, "name": "Ethan Sevenster"}}
        ]
    },
    "saveToSentItems": "true"
}

r = requests.post(
    f'https://graph.microsoft.com/v1.0/users/{MAILBOX}/sendMail',
    headers=headers, json=email
)
print(f"Status: {r.status_code} {'SUCCESS' if r.status_code == 202 else r.text[:300]}")
