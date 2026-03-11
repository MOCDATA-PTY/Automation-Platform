"""Test sending an email from waldogaybba@moc-pty.com via Graph API Mail.Send"""
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
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Send a test email from the shared mailbox to itself
email_payload = {
    "message": {
        "subject": "Test Email from Automation Platform",
        "body": {
            "contentType": "Text",
            "content": "This is a test email sent via Microsoft Graph API from the Automation Platform."
        },
        "toRecipients": [
            {
                "emailAddress": {
                    "address": "ethansevenster5@gmail.com"
                }
            }
        ]
    },
    "saveToSentItems": "true"
}

r = requests.post(
    f'https://graph.microsoft.com/v1.0/users/{MAILBOX}/sendMail',
    headers=headers,
    json=email_payload
)

print(f"\nSend email status: {r.status_code}")
if r.status_code == 202:
    print("SUCCESS! Email sent from waldogaybba@moc-pty.com")
    print("Check the inbox for the test message.")
else:
    print(f"Error: {r.text[:500]}")
