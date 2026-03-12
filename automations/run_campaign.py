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
    print("🧪 Test Email Campaign (sends to ethansevenster5@gmail.com)")
    
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
    
    print(f"🧪 This will send 1 test TP{tp_num} email to ethansevenster5@gmail.com")
    response = input("Continue? (y/N): ")
    if response.lower() != 'y':
        print("🛑 Test cancelled")
        return
    
    # Get any contact for template data
    test_contact = USEUContact.objects.filter(status='Active').first()
    if not test_contact:
        print("❌ No contacts found for template data")
        return
    
    print(f"📧 Using contact data from: {test_contact.org_name} for template")
    
    # Import the direct sending logic
    from dashboard.views import _get_graph_token, _graph_send_mail, GRAPH_MAILBOX
    from dashboard.models import TouchpointTemplate
    import datetime
    
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
    
    # Build test email
    body_content = template.body_html if template.body_html else template.body
    content_type = 'HTML' if template.body_html else 'Text'
    
    # Variable substitution using test contact data
    final_body = body_content
    final_body = final_body.replace('{{org_name}}', test_contact.org_name or 'TEST COMPANY')
    final_body = final_body.replace('{{contact_name}}', test_contact.contact_name or 'TEST CONTACT')
    final_body = final_body.replace('{{email}}', 'ethansevenster5@gmail.com')
    final_body = final_body.replace('{{phone}}', test_contact.phone or 'TEST PHONE')
    final_body = final_body.replace('{{touchpoint_number}}', str(tp_num))
    
    # Add test notice to email
    if content_type == 'HTML':
        test_notice = '<div style="background:#ffeb3b;padding:10px;margin-bottom:20px;border:2px solid #f57f17;"><strong>🧪 TEST EMAIL</strong> - This is a test of TP' + str(tp_num) + ' sent from the terminal campaign runner.</div>'
        final_body = test_notice + final_body
    else:
        final_body = f"🧪 TEST EMAIL - This is a test of TP{tp_num} sent from the terminal campaign runner.\n\n" + final_body
    
    subject = template.subject or f'TP{tp_num} Test'
    subject = subject.replace('{{org_name}}', test_contact.org_name or 'TEST COMPANY')
    subject = subject.replace('{{contact_name}}', test_contact.contact_name or 'TEST CONTACT')
    subject = f"🧪 TEST - {subject}"
    
    # Build payload
    payload = {
        'message': {
            'subject': subject,
            'body': {'contentType': content_type, 'content': final_body},
            'from': {'emailAddress': {'name': 'Magnum Opus Consultants', 'address': GRAPH_MAILBOX}},
            'toRecipients': [{'emailAddress': {'address': 'ethansevenster5@gmail.com', 'name': 'Ethan Test'}}],
        },
        'saveToSentItems': True,
    }
    
    print(f"📧 Sending test email...")
    print(f"   📤 From: {GRAPH_MAILBOX}")
    print(f"   📬 To: ethansevenster5@gmail.com")
    print(f"   📝 Subject: {subject}")
    
    # Send the email
    sent_ok, status_code = _graph_send_mail(token, payload)
    
    if sent_ok:
        print(f"✅ TEST EMAIL SENT SUCCESSFULLY! Status: {status_code}")
        print("📬 Check ethansevenster5@gmail.com inbox (and spam folder)")
        print("📤 Email should also appear in waldogaybba@moc-pty.com sent items")
        return True
    else:
        print(f"❌ TEST EMAIL FAILED! Status: {status_code}")
        return False
if __name__ == "__main__":
    print("📧 Touchpoint Email Campaign Runner")
    print("=" * 40)
    print("1. Run TP1 Campaign (Full)")
    print("2. Custom Touchpoint Campaign")
    print("3. Test Email to ethansevenster5@gmail.com")
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