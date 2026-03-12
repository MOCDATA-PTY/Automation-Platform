#!/usr/bin/env python3
"""
Test script to trigger touchpoint email sending and check if it works.
"""
import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automations.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

def test_email_send():
    print("🧪 Testing touchpoint email sending...")
    
    # Create test client
    client = Client()
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com', 'is_staff': True}
    )
    if created:
        user.set_password('testpass')
        user.save()
        print("✅ Created test user")
    
    # Login
    client.force_login(user)
    print("✅ Logged in test user")
    
    # Test payload for TP1
    payload = {
        'tp_num': 1,
        'test_mode': True  # Add test mode if available
    }
    
    print(f"📤 Sending POST to /useu-list/send-all/ with payload: {payload}")
    
    # Make the request
    response = client.post('/useu-list/send-all/', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    print(f"📬 Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Response: {data}")
        if 'job_id' in data:
            print(f"🎯 Job ID: {data['job_id']}")
            print("📊 Check the server logs for debug messages!")
            print("🔍 You should see: [DEBUG] Attempting Graph API email send to: ...")
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        if hasattr(response, 'content'):
            print(f"Error content: {response.content.decode()}")
        return False

if __name__ == '__main__':
    success = test_email_send()
    if success:
        print("\n🎉 Test completed successfully!")
        print("👀 Now check the server logs with:")
        print("   sudo journalctl -u gunicorn-automation.service -f")
    else:
        print("\n💥 Test failed!")