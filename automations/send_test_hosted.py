"""Send TP1 email with server-hosted signature image URL."""
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

# Replace Google Drive URL with server-hosted image
body_content = re.sub(
    r'https://drive\.google\.com/thumbnail\?id=[^"\'&]+(?:&amp;[^"\']*|&[^"\']*)*',
    r'https://workspace.moc-pty.com/static/signature_waldo.png',
    body_content,
    flags=re.IGNORECASE
)

print(f'Body length: {len(body_content)}')
print(f'Has signature URL: {"signature_waldo.png" in body_content}')

payload = {
    'message': {
        'subject': template.subject or 'Magnum Opus Consultants - Introduction',
        'body': {'contentType': 'HTML', 'content': body_content},
        'toRecipients': [{'emailAddress': {'address': 'anthony.penzes@eclick.co.za'}}],
    },
    'saveToSentItems': 'true',
}

# Add PDF attachment if exists
if template.attachment:
    att_path = template.attachment.path
    with open(att_path, 'rb') as f:
        att_bytes = f.read()
    raw_name = os.path.basename(att_path)
    name_part, ext = os.path.splitext(raw_name)
    att_name = name_part.replace('_', ' ').replace('-', ' ')
    att_name = ' '.join(att_name.split()) + ext
    payload['message']['attachments'] = [{
        '@odata.type': '#microsoft.graph.fileAttachment',
        'name': att_name,
        'contentBytes': base64.b64encode(att_bytes).decode('utf-8'),
    }]
    print(f'Attached: {att_name}')

r = http_requests.post(
    f'https://graph.microsoft.com/v1.0/users/{GRAPH_MAILBOX}/sendMail',
    headers=headers, json=payload
)
print(f'Status: {r.status_code}')
if r.status_code == 202:
    print('SUCCESS! Email sent to ethansevenster5@gmail.com')
else:
    print(f'Error: {r.text[:500]}')
