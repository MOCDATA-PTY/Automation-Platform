#!/usr/bin/env python3
"""
Run full touchpoint email campaign from terminal
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

from dashboard.models import USEUContact
from dashboard.views import send_all_touchpoint, _send_all_progress
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
import json
import threading
import time

class MockRequest:
    """Mock Django request object for terminal use"""
    def __init__(self, data, user=None):
        self.method = 'POST'
        self.body = json.dumps(data).encode('utf-8')
        self.user = user

def run_tp1_campaign():
    print("🚀 Starting TP1 Email Campaign from Terminal...")
    
    # Authenticate user
    print("🔐 Authenticating...")
    try:
        user = User.objects.get(username='Ethan')
        print("✅ User authenticated")
    except User.DoesNotExist:
        print("❌ User 'Ethan' not found")
        return
    
    # Check eligible contacts first
    eligible = USEUContact.objects.filter(
        status='Active', 
        tp1_sent_on=''
    ).exclude(email='').exclude(email__isnull=True).count()
    
    print(f"📊 Found {eligible:,} eligible contacts for TP1")
    
    if eligible == 0:
        print("❌ No eligible contacts found")
        return
    
    if eligible > 100:
        response = input(f"⚠️  This will send {eligible:,} emails. Continue? (y/N): ")
        if response.lower() != 'y':
            print("🛑 Campaign cancelled")
            return
    
    # Create mock request with authenticated user
    request_data = {'touchpoint_number': 1}
    mock_request = MockRequest(request_data, user=user)
    
    print("📧 Starting email campaign...")
    
    # Call the send function
    response = send_all_touchpoint(mock_request)
    
    if hasattr(response, 'content'):
        result = json.loads(response.content.decode())
    else:
        result = response
    
    if isinstance(result, dict) and result.get('ok'):
        job_id = result.get('job_id')
        total = result.get('total')
        print(f"✅ Campaign started successfully!")
        print(f"📊 Job ID: {job_id}")
        print(f"📊 Total emails: {total:,}")
        
        # Monitor progress
        print("\n📈 Monitoring progress (Ctrl+C to stop monitoring)...")
        print("   You can check debug logs to see actual sends:")
        print("   [BULK DEBUG] Sending to: contact@example.com")
        print("   [DEBUG] Attempting Graph API email send to: contact@example.com")
        
        try:
            while True:
                if job_id in _send_all_progress:
                    progress = _send_all_progress[job_id]
                    sent = progress.get('sent', 0)
                    failed = progress.get('failed', 0)
                    current = progress.get('current', '')
                    done = progress.get('done', False)
                    
                    print(f"\r📊 Progress: {sent:,} sent, {failed} failed", end="")
                    if current:
                        print(f" | Current: {current}", end="")
                    
                    if done:
                        print(f"\n✅ Campaign completed!")
                        print(f"📊 Final results: {sent:,} sent, {failed} failed")
                        break
                
                time.sleep(2)
        except KeyboardInterrupt:
            print(f"\n⏹️  Monitoring stopped (campaign continues in background)")
    else:
        print(f"❌ Campaign failed: {result}")

def run_custom_campaign():
    print("🎯 Custom Email Campaign")
    
    # Authenticate user
    print("🔐 Authenticating...")
    try:
        user = User.objects.get(username='Ethan')
        print("✅ User authenticated")
    except User.DoesNotExist:
        print("❌ User 'Ethan' not found")
        return
    
    while True:
        try:
            tp_num = int(input("Enter touchpoint number (1-10): "))
            if 1 <= tp_num <= 10:
                break
            else:
                print("Please enter a number between 1 and 10")
        except ValueError:
            print("Please enter a valid number")
    
    # Check eligible contacts
    tp_sent_field = f'tp{tp_num}_sent_on'
    filters = {'status': 'Active', tp_sent_field: ''}
    eligible = USEUContact.objects.filter(**filters).exclude(email='').exclude(email__isnull=True).count()
    
    print(f"📊 Found {eligible:,} eligible contacts for TP{tp_num}")
    
    if eligible == 0:
        print("❌ No eligible contacts found")
        return
    
    if eligible > 100:
        response = input(f"⚠️  This will send {eligible:,} emails. Continue? (y/N): ")
        if response.lower() != 'y':
            print("🛑 Campaign cancelled")
            return
    
    # Create mock request with authenticated user
    request_data = {'touchpoint_number': tp_num}
    mock_request = MockRequest(request_data, user=user)
    
    print(f"📧 Starting TP{tp_num} campaign...")
    
    # Call the send function
    response = send_all_touchpoint(mock_request)
    
    if hasattr(response, 'content'):
        result = json.loads(response.content.decode())
    else:
        result = response
    
    if isinstance(result, dict) and result.get('ok'):
        job_id = result.get('job_id')
        total = result.get('total')
        print(f"✅ TP{tp_num} campaign started successfully!")
        print(f"📊 Job ID: {job_id}")
        print(f"📊 Total emails: {total:,}")
        print("\n📈 Campaign running in background...")
    else:
        print(f"❌ Campaign failed: {result}")

def run_test_campaign():
    print("🧪 Send ONE test email to ethansevenster5@gmail.com")
    
    # Authenticate user
    print("🔐 Authenticating...")
    try:
        user = User.objects.get(username='Ethan')
        print("✅ User authenticated")
    except User.DoesNotExist:
        print("❌ User 'Ethan' not found")
        return
    
    while True:
        try:
            tp_num = int(input("Enter touchpoint number to test (1-10): "))
            if 1 <= tp_num <= 10:
                break
            else:
                print("Please enter a number between 1 and 10")
        except ValueError:
            print("Please enter a valid number")
    
    print(f"🧪 This will send ONE TP{tp_num} email to ethansevenster5@gmail.com")
    print("   (Same template and attachments as real campaign)")
    response = input("Continue? (y/N): ")
    if response.lower() != 'y':
        print("🛑 Test cancelled")
        return
    
    # Get a real contact for template data
    test_contact = USEUContact.objects.filter(status='Active').exclude(email='').first()
    if not test_contact:
        print("❌ No active contacts found for template data")
        return
    
    print(f"📧 Using template data from: {test_contact.org_name}")
    
    # Import the sending logic
    from dashboard.views import _get_graph_token, _graph_send_mail, GRAPH_MAILBOX
    from dashboard.models import TouchpointTemplate
    import base64
    import os
    from django.conf import settings as django_settings
    
    # Get template
    try:
        template = TouchpointTemplate.objects.get(touchpoint_number=tp_num)
        print(f"✅ Got TP{tp_num} template: {template.subject}")
    except TouchpointTemplate.DoesNotExist:
        print(f"❌ TP{tp_num} template not found")
        return
    
    # Get Graph token
    print("📡 Getting Graph API token...")
    token = _get_graph_token()
    if not token:
        print("❌ Failed to get Graph API token")
        return
    print("✅ Got Graph API token")
    
    # Build email with same logic as bulk campaign
    body_content = template.body_html if template.body_html else template.body
    content_type = 'HTML' if template.body_html else 'Text'
    
    # Variable substitution
    final_body = body_content
    final_body = final_body.replace('{{org_name}}', test_contact.org_name or '')
    final_body = final_body.replace('{{contact_name}}', test_contact.contact_name or '')
    final_body = final_body.replace('{{email}}', 'ethansevenster5@gmail.com')
    final_body = final_body.replace('{{phone}}', test_contact.phone or '')
    final_body = final_body.replace('{{touchpoint_number}}', str(tp_num))
    
    # Add signature handling (same as bulk)
    import re
    sig_inline = None
    if content_type == 'HTML':
        final_body = re.sub(
            r'https://drive\.google\.com/thumbnail\?id=[^"\'&]+(?:&amp;[^"\']*|&[^"\']*)*',
            r'cid:signature_waldo',
            final_body,
            flags=re.IGNORECASE
        )
        sig_path = os.path.join(django_settings.BASE_DIR, 'static', 'signature_waldo.png')
        if os.path.isfile(sig_path):
            with open(sig_path, 'rb') as sf:
                sig_inline = {
                    '@odata.type': '#microsoft.graph.fileAttachment',
                    'name': 'signature_waldo.png',
                    'contentType': 'image/png',
                    'contentBytes': base64.b64encode(sf.read()).decode('utf-8'),
                    'contentId': 'signature_waldo',
                    'isInline': True,
                }
    
    # Add template attachment (same as bulk)
    att_data = None
    if template.attachment:
        try:
            att_path = template.attachment.path
            with open(att_path, 'rb') as f:
                att_bytes = f.read()
            raw_name = os.path.basename(att_path)
            name_part, ext = os.path.splitext(raw_name)
            att_name = name_part.replace('_', ' ').replace('-', ' ')
            att_name = ' '.join(att_name.split()) + ext
            att_data = {
                '@odata.type': '#microsoft.graph.fileAttachment',
                'name': att_name,
                'contentBytes': base64.b64encode(att_bytes).decode('utf-8'),
            }
            print(f"📎 Attachment: {att_name}")
        except Exception as e:
            print(f"⚠️  Attachment error: {e}")
    
    subject = template.subject or f'TP{tp_num}'
    subject = subject.replace('{{org_name}}', test_contact.org_name or '')
    subject = subject.replace('{{contact_name}}', test_contact.contact_name or '')
    
    # Build payload (same structure as bulk)
    payload = {
        'message': {
            'subject': subject,
            'body': {'contentType': content_type, 'content': final_body},
            'from': {'emailAddress': {'name': 'Magnum Opus Consultants', 'address': GRAPH_MAILBOX}},
            'toRecipients': [{'emailAddress': {'address': 'ethansevenster5@gmail.com'}}],
        },
        'saveToSentItems': False,  # Try without saving first
    }
    
    # Add attachments
    att_list = []
    if att_data:
        att_list.append(att_data)
    if sig_inline:
        att_list.append(sig_inline)
    if att_list:
        payload['message']['attachments'] = att_list
    
    print(f"📧 Sending test email...")
    print(f"   📤 From: {GRAPH_MAILBOX}")
    print(f"   📬 To: ethansevenster5@gmail.com")
    print(f"   📝 Subject: {subject}")
    if att_list:
        print(f"   📎 Attachments: {len(att_list)}")
    
    # Send the email
    sent_ok, status_code = _graph_send_mail(token, payload)
    
    if sent_ok:
        print(f"✅ TEST EMAIL SENT SUCCESSFULLY! Status: {status_code}")
        print("📬 Check ethansevenster5@gmail.com inbox (and spam folder)")
        print("📤 Email should also appear in waldogaybba@moc-pty.com sent items")
        return True
    else:
        print(f"❌ TEST EMAIL FAILED! Status: {status_code}")
        if status_code == 403:
            print("🔍 Permission denied - check shared mailbox permissions")
        elif status_code == 401:
            print("🔍 Authentication failed - token expired")
        return False
if __name__ == "__main__":
    print("📧 Touchpoint Email Campaign Runner")
    print("=" * 40)
    print("1. Run TP1 Campaign (Full)")
    print("2. Custom Touchpoint Campaign")
    print("3. Send ONE test email to ethansevenster5@gmail.com")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == '1':
                run_tp1_campaign()
                break
            elif choice == '2':
                run_custom_campaign()
                break
            elif choice == '3':
                run_test_campaign()
                break
            elif choice == '4':
                print("👋 Goodbye!")
                break
            else:
                print("Please enter 1, 2, 3, or 4")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break