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
    print("🧪 Test Campaign to ethansevenster5@gmail.com (same as full campaign)")
    
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
    
    print(f"🧪 This will run the full TP{tp_num} campaign but send only to ethansevenster5@gmail.com")
    print("   (Same logic, templates, attachments as real campaign)")
    response = input("Continue? (y/N): ")
    if response.lower() != 'y':
        print("🛑 Test cancelled")
        return
    
    # Set test mode temporarily - modify Django settings directly
    from django.conf import settings as django_settings
    
    # Store original value
    original_override = getattr(django_settings, 'TEST_EMAIL_OVERRIDE', None)
    
    # Set the test override
    django_settings.TEST_EMAIL_OVERRIDE = 'ethansevenster5@gmail.com'
    
    try:
        # Create mock request with authenticated user (same as real campaign)
        request_data = {'touchpoint_number': tp_num}
        mock_request = MockRequest(request_data, user=user)
        
        print(f"📧 Starting TP{tp_num} test campaign...")
        print(f"🔄 All emails will be redirected to: ethansevenster5@gmail.com")
        
        # Call the actual send function (same as real campaign)
        response = send_all_touchpoint(mock_request)
        
        if hasattr(response, 'content'):
            result = json.loads(response.content.decode())
        else:
            result = response
        
        if isinstance(result, dict) and result.get('ok'):
            job_id = result.get('job_id')
            total = result.get('total')
            print(f"✅ Test campaign started successfully!")
            print(f"📊 Job ID: {job_id}")
            print(f"📊 Emails redirected to: ethansevenster5@gmail.com")
            print("🔍 Debug logs will show the actual sending process")
            
            # Monitor progress briefly
            print("\n📈 Monitoring progress...")
            for i in range(10):  # Check for 20 seconds
                if job_id in _send_all_progress:
                    progress = _send_all_progress[job_id]
                    sent = progress.get('sent', 0)
                    failed = progress.get('failed', 0)
                    current = progress.get('current', '')
                    done = progress.get('done', False)
                    
                    print(f"\r📊 Progress: {sent} sent, {failed} failed", end="")
                    if current:
                        print(f" | Redirected to: ethansevenster5@gmail.com", end="")
                    
                    if done:
                        print(f"\n✅ Test campaign completed!")
                        print(f"📊 Final: {sent} emails sent to ethansevenster5@gmail.com")
                        break
                
                time.sleep(2)
            
            if not done:
                print(f"\n📊 Test campaign is running in background...")
            
        else:
            print(f"❌ Test campaign failed: {result}")
    
    finally:
        # Restore original setting
        if original_override is None:
            if hasattr(django_settings, 'TEST_EMAIL_OVERRIDE'):
                delattr(django_settings, 'TEST_EMAIL_OVERRIDE')
        else:
            django_settings.TEST_EMAIL_OVERRIDE = original_override
if __name__ == "__main__":
    print("📧 Touchpoint Email Campaign Runner")
    print("=" * 40)
    print("1. Run TP1 Campaign (Full)")
    print("2. Custom Touchpoint Campaign")
    print("3. Test Campaign to ethansevenster5@gmail.com (full campaign logic)")
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