import os, sys
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'automations.settings'
import django
django.setup()
from dashboard.models import TouchpointTemplate

t = TouchpointTemplate.objects.get(touchpoint_number=1)
print('=== SUBJECT ===')
print(t.subject)
print('=== BODY HTML (first 3000 chars) ===')
print((t.body_html or 'EMPTY')[:3000])
print('=== BODY PLAIN (first 1000 chars) ===')
print((t.body or 'EMPTY')[:1000])
print('=== SIGNATURE ===')
print((t.signature or 'EMPTY')[:1000])
print('=== ATTACHMENT ===')
print(t.attachment.name if t.attachment else 'NONE')
