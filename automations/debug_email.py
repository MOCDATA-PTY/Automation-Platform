#!/usr/bin/env python3
"""
Debug email with attachments - show exact payload and Graph API response
"""
import os
import sys
import django

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automations.settings')
django.setup()

from dashboard.views import _get_graph_token, GRAPH_MAILBOX
from dashboard.models import TouchpointTemplate, USEUContact
import requests
import json
import base64
import os as os_module

def debug_email_with_attachment():
    print("🔍 Debug email with attachment payload")
    
    # Get token
    token = _get_graph_token()
    if not token:
        print("❌ Failed to get Graph API token")
        return
    print("✅ Got Graph API token")
    
    # Get template
    try:
        template = TouchpointTemplate.objects.get(touchpoint_number=1)
        print(f"✅ Got TP1 template")
    except:
        print("❌ TP1 template not found")
        return
    
    # Get a contact for template data
    contact = USEUContact.objects.filter(status='Active').first()
    if not contact:
        print("❌ No active contacts found")
        return
    
    print(f"📧 Using contact: {contact.org_name}")
    
    # Build email body
    body_content = template.body_html if template.body_html else template.body
    content_type = 'HTML' if template.body_html else 'Text'
    
    final_body = body_content
    final_body = final_body.replace('{{org_name}}', contact.org_name or '')
    final_body = final_body.replace('{{contact_name}}', contact.contact_name or '')
    final_body = final_body.replace('{{email}}', 'ethansevenster5@gmail.com')
    final_body = final_body.replace('{{phone}}', contact.phone or '')
    final_body = final_body.replace('{{touchpoint_number}}', '1')
    
    subject = template.subject or 'TP1'
    
    # Load attachment
    print(f"\n📎 Processing attachment...")
    att_data = None
    if template.attachment:
        try:
            att_path = template.attachment.path
            att_size = os_module.path.getsize(att_path)
            print(f"   File size: {att_size:,} bytes ({att_size / 1024 / 1024:.2f} MB)")
            
            with open(att_path, 'rb') as f:
                att_bytes = f.read()
            
            print(f"   Read {len(att_bytes):,} bytes from file")
            
            # Encode to base64
            att_base64 = base64.b64encode(att_bytes).decode('utf-8')
            print(f"   Base64 encoded: {len(att_base64):,} characters")
            
            raw_name = os_module.path.basename(att_path)
            name_part, ext = os_module.splitext(raw_name)
            att_name = name_part.replace('_', ' ').replace('-', ' ')
            att_name = ' '.join(att_name.split()) + ext
            
            att_data = {
                '@odata.type': '#microsoft.graph.fileAttachment',
                'name': att_name,
                'contentBytes': att_base64,
            }
            print(f"   ✅ Attachment prepared: {att_name}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return
    
    # Build payload
    payload = {
        'message': {
            'subject': subject,
            'body': {'contentType': content_type, 'content': final_body[:100] + '...'},  # Truncate for display
            'from': {'emailAddress': {'name': 'Magnum Opus Consultants', 'address': GRAPH_MAILBOX}},
            'toRecipients': [{'emailAddress': {'address': 'ethansevenster5@gmail.com'}}],
        },
        'saveToSentItems': False,
    }
    
    if att_data:
        payload['message']['attachments'] = [att_data]
    
    # Show payload info
    print(f"\n📋 Payload structure:")
    print(f"   Subject: {subject}")
    print(f"   From: {GRAPH_MAILBOX}")
    print(f"   To: ethansevenster5@gmail.com")
    print(f"   Body type: {content_type}")
    print(f"   Body length: {len(final_body):,} chars")
    print(f"   Attachments: {'Yes' if att_data else 'No'}")
    
    # Estimate JSON size
    import json
    payload_json = json.dumps(payload)
    payload_size = len(payload_json)
    payload_size_mb = payload_size / 1024 / 1024
    print(f"   JSON payload size: {payload_size:,} bytes ({payload_size_mb:.2f} MB)")
    
    if payload_size_mb > 4:
        print(f"   ⚠️  WARNING: Payload > 4MB (Graph API limit)")
    
    # Send
    print(f"\n📧 Sending...")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        r = requests.post(
            f'https://graph.microsoft.com/v1.0/users/{GRAPH_MAILBOX}/sendMail',
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"\n📊 Response:")
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 202:
            print(f"   ✅ SUCCESS!")
        else:
            print(f"   ❌ FAILED!")
            print(f"   Response body: {r.text}")
            
            # Parse error
            try:
                error_json = r.json()
                if 'error' in error_json:
                    error = error_json['error']
                    print(f"\n   Error code: {error.get('code')}")
                    print(f"   Error message: {error.get('message')}")
                    if 'innerError' in error:
                        print(f"   Inner error: {error['innerError']}")
            except:
                pass
    
    except Exception as e:
        print(f"   ❌ Request error: {e}")

if __name__ == "__main__":
    debug_email_with_attachment()