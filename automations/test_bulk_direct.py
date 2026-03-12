#!/usr/bin/env python3
"""
Direct test of bulk email sending - bypasses Django auth
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

from dashboard.views import _get_graph_token, _graph_send_mail, GRAPH_MAILBOX
from dashboard.models import USEUContact, TouchpointTemplate
import json
import base64
import datetime

def test_bulk_email_direct():
    print("🔧 Testing bulk email sending (direct)...")
    
    # Get a few test contacts
    print("👥 Finding test contacts...")
    contacts = list(USEUContact.objects.filter(
        status='Active', 
        tp1_sent_on=''
    ).exclude(email='').exclude(email__isnull=True)[:3])  # Only 3 for testing
    
    if not contacts:
        print("❌ No eligible contacts found for testing")
        return False
    
    print(f"✅ Found {len(contacts)} test contacts")
    for contact in contacts:
        print(f"   - {contact.email} ({contact.org_name})")
    
    # Get TP1 template
    print("📄 Getting TP1 template...")
    try:
        template = TouchpointTemplate.objects.get(touchpoint_number=1)
        print(f"✅ Got template: {template.subject}")
    except TouchpointTemplate.DoesNotExist:
        print("❌ TP1 template not found")
        return False
    
    # Get Graph token
    print("📡 Getting Graph API token...")
    token = _get_graph_token()
    if not token:
        print("❌ Failed to get Graph API token")
        return False
    print("✅ Got Graph API token")
    
    # Test sending to each contact
    print("📧 Testing email sends...")
    success_count = 0
    
    for i, contact in enumerate(contacts):
        email_addr = contact.email.strip()
        print(f"\n📧 [{i+1}/{len(contacts)}] Sending to: {email_addr}")
        
        # Build email payload (same as bulk logic)
        body_content = template.body_html if template.body_html else template.body
        content_type = 'HTML' if template.body_html else 'Text'
        
        # Variable substitution
        final_body = body_content
        final_body = final_body.replace('{{org_name}}', contact.org_name or '')
        final_body = final_body.replace('{{contact_name}}', contact.contact_name or '')
        final_body = final_body.replace('{{email}}', contact.email or '')
        final_body = final_body.replace('{{phone}}', contact.phone or '')
        final_body = final_body.replace('{{touchpoint_number}}', '1')
        
        subject = template.subject or ''
        subject = subject.replace('{{org_name}}', contact.org_name or '')
        subject = subject.replace('{{contact_name}}', contact.contact_name or '')
        
        # Build payload (exactly like bulk sending)
        payload = {
            'message': {
                'subject': subject,
                'body': {'contentType': content_type, 'content': final_body},
                'from': {'emailAddress': {'name': 'Magnum Opus Consultants', 'address': GRAPH_MAILBOX}},
                'toRecipients': [{'emailAddress': {'address': email_addr}}],
            },
            'saveToSentItems': True,  # Fixed boolean value
        }
        
        print(f"   📤 From: {GRAPH_MAILBOX}")
        print(f"   📬 To: {email_addr}")
        print(f"   📝 Subject: {subject}")
        
        # Send the email
        sent_ok, status_code = _graph_send_mail(token, payload)
        
        if sent_ok:
            print(f"   ✅ SUCCESS: Status {status_code}")
            success_count += 1
            
            # Update contact (same as bulk logic)
            now_str = datetime.datetime.now().strftime('%d/%m/%Y')
            contact.tp1_sent_on = now_str
            contact.last_touch = '1'
            contact.save(update_fields=['tp1_sent_on', 'last_touch'])
            print(f"   💾 Updated contact record")
        else:
            print(f"   ❌ FAILED: Status {status_code}")
            if status_code == 401:
                print("      🔍 Authentication failed")
            elif status_code == 403:
                print("      🔍 Permission denied - check shared mailbox permissions")
            elif status_code == 404:
                print("      🔍 Mailbox not found")
            elif status_code == 429:
                print("      🔍 Rate limited")
    
    print(f"\n📊 Results: {success_count}/{len(contacts)} emails sent successfully")
    
    if success_count > 0:
        print("✅ Bulk email system is working!")
        print("📬 Check the recipients' inboxes and shared mailbox sent items")
        print("💡 The 'Send All' button should now work correctly")
    else:
        print("❌ No emails were sent successfully")
        print("🔍 Check Graph API permissions and shared mailbox configuration")
    
    return success_count > 0

if __name__ == "__main__":
    test_bulk_email_direct()