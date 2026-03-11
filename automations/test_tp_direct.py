"""Test sending TP1 with inline CID signature (no external URLs)."""
import os, sys
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'automations.settings'
import django
django.setup()

import re
import base64
import json
import msal
import requests as http_requests
from dashboard.models import TouchpointTemplate

# Get template
t = TouchpointTemplate.objects.get(touchpoint_number=1)
body_content = t.body_html
content_type = 'HTML'

# Replace Google Drive URL with CID reference (inline attachment)
body_content = re.sub(
    r'https://drive\.google\.com/thumbnail\?id=[^"\'&]+(?:&amp;[^"\']*|&[^"\']*)*',
    r'cid:signature_waldo',
    body_content,
    flags=re.IGNORECASE
)

print("=== CHECKING SIGNATURE ===")
if 'cid:signature_waldo' in body_content:
    print("[OK] Signature uses CID inline reference")
elif 'drive.google.com' in body_content:
    print("[FAIL] Google Drive URL still present!")
else:
    print("[?] No signature URL found at all")
print()

# Get Graph token
GRAPH_CLIENT_ID = '43fbe5a9-6b5b-4c81-9067-7aff9ac3ed5a'
GRAPH_TENANT_ID = 'b1504b1d-d096-409a-a0f0-6cc546dde993'
GRAPH_CLIENT_SECRET = 'w6B8Q~W3ac9klXa8NkMDo4cPNyOsjEryVL5TwdhQ'
GRAPH_MAILBOX = 'waldogaybba@moc-pty.com'

app = msal.ConfidentialClientApplication(
    GRAPH_CLIENT_ID,
    authority=f'https://login.microsoftonline.com/{GRAPH_TENANT_ID}',
    client_credential=GRAPH_CLIENT_SECRET,
)
result = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])
token = result.get('access_token')
if not token:
    print("FAILED to get token:", result)
    sys.exit(1)
print("[OK] Got Graph API token")

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Build attachments list
attachments = []

# Regular file attachment
if t.attachment:
    att_path = t.attachment.path
    with open(att_path, 'rb') as f:
        att_bytes = f.read()
    raw_name = os.path.basename(att_path)
    name_part, ext = os.path.splitext(raw_name)
    att_name = name_part.replace('_', ' ').replace('-', ' ')
    att_name = ' '.join(att_name.split()) + ext
    attachments.append({
        '@odata.type': '#microsoft.graph.fileAttachment',
        'name': att_name,
        'contentBytes': base64.b64encode(att_bytes).decode('utf-8'),
    })
    print(f"[OK] Attachment: {att_name} ({len(att_bytes)} bytes)")

# Inline signature image (CID attachment)
sig_path = os.path.join(os.path.dirname(__file__), 'static', 'signature_waldo.png')
if os.path.isfile(sig_path):
    with open(sig_path, 'rb') as sf:
        sig_bytes = sf.read()
    attachments.append({
        '@odata.type': '#microsoft.graph.fileAttachment',
        'name': 'signature_waldo.png',
        'contentType': 'image/png',
        'contentBytes': base64.b64encode(sig_bytes).decode('utf-8'),
        'contentId': 'signature_waldo',
        'isInline': True,
    })
    print(f"[OK] Inline signature: signature_waldo.png ({len(sig_bytes)} bytes)")
else:
    print(f"[WARN] Signature file not found: {sig_path}")

subject = t.subject or 'Introducing Magnum Opus Consultants'

payload = {
    'message': {
        'subject': subject,
        'body': {'contentType': content_type, 'content': body_content},
        'from': {'emailAddress': {'name': 'Magnum Opus Consultants', 'address': GRAPH_MAILBOX}},
        'toRecipients': [{'emailAddress': {'address': 'ethansevenster5@gmail.com'}}],
    },
    'saveToSentItems': 'true',
}
if attachments:
    payload['message']['attachments'] = attachments

print(f"\nSending to: ethansevenster5@gmail.com")
print(f"From: Magnum Opus Consultants <{GRAPH_MAILBOX}>")
print(f"Subject: {subject}")
print(f"Content type: {content_type}")
print(f"Body length: {len(body_content)} chars")
print(f"Attachments: {len(attachments)} (including inline signature)")

r = http_requests.post(
    f'https://graph.microsoft.com/v1.0/users/{GRAPH_MAILBOX}/sendMail',
    headers=headers, json=payload, timeout=30
)
print(f"\nResponse: {r.status_code}")
if r.status_code != 202:
    print(r.text)
else:
    print("[OK] Email sent successfully with inline signature!")
