"""Send TP1 email with local signature image as inline CID attachment."""
import os, sys, django, base64, re
os.environ['DJANGO_SETTINGS_MODULE'] = 'automations.settings'
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from dashboard.views import _get_graph_token, GRAPH_MAILBOX
from dashboard.models import TouchpointTemplate
import requests as http_requests

token = _get_graph_token()
template = TouchpointTemplate.objects.get(touchpoint_number=1)
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

body_content = template.body_html

# Replace the Google Drive img src with cid:waldo_signature
body_content = re.sub(
    r'(<img\s+[^>]*?)src=["\']https://drive\.google\.com/thumbnail\?id=[^"\']+["\']',
    r'\1src="cid:waldo_signature"',
    body_content,
    flags=re.IGNORECASE
)
print('Replaced Google Drive URL with cid:waldo_signature')

# Read local signature image
sig_path = os.path.join(os.path.dirname(__file__), 'static', 'signature_waldo.png')
with open(sig_path, 'rb') as f:
    sig_bytes = f.read()
print(f'Signature image: {len(sig_bytes)} bytes')

payload = {
    'message': {
        'subject': template.subject or 'Magnum Opus Consultants - Introduction',
        'body': {'contentType': 'HTML', 'content': body_content},
        'toRecipients': [{'emailAddress': {'address': 'ethansevenster5@gmail.com'}}],
    },
    'saveToSentItems': 'true',
}

# Build attachments: inline signature + PDF
attachments = [
    {
        '@odata.type': '#microsoft.graph.fileAttachment',
        'name': 'signature.png',
        'contentBytes': base64.b64encode(sig_bytes).decode('utf-8'),
        'contentType': 'image/png',
        'contentId': 'waldo_signature',
        'isInline': True,
    }
]

if template.attachment:
    att_path = template.attachment.path
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
    print(f'Attached: {att_name}')

payload['message']['attachments'] = attachments

r = http_requests.post(
    f'https://graph.microsoft.com/v1.0/users/{GRAPH_MAILBOX}/sendMail',
    headers=headers, json=payload
)
print(f'Status: {r.status_code}')
if r.status_code == 202:
    print('SUCCESS! Email sent to ethansevenster5@gmail.com')
else:
    print(f'Error: {r.text[:500]}')
