#!/usr/bin/env python3
"""
Simple email test without attachments to isolate the permission issue
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
import requests
import json

def test_simple_email():
    print("🧪 Simple email test (no attachments, minimal payload)")
    
    # Get Graph token
    print("📡 Getting Graph API token...")
    token = _get_graph_token()
    if not token:
        print("❌ Failed to get Graph API token")
        return
    print("✅ Got Graph API token")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Minimal payload without explicit from field
    print(f"\n📧 Test 1: Minimal payload (no from field)")
    payload1 = {
        'message': {
            'subject': 'Simple Test Email',
            'body': {'contentType': 'Text', 'content': 'This is a simple test email.'},
            'toRecipients': [{'emailAddress': {'address': 'ethansevenster5@gmail.com'}}],
        },
        'saveToSentItems': False,
    }
    
    try:
        r = requests.post(
            f'https://graph.microsoft.com/v1.0/users/{GRAPH_MAILBOX}/sendMail',
            headers=headers,
            json=payload1,
            timeout=30
        )
        print(f"Result: Status {r.status_code}")
        if r.status_code == 202:
            print("✅ SUCCESS! Simple email sent")
        else:
            print(f"❌ Failed: {r.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: With explicit from field
    print(f"\n📧 Test 2: With explicit from field")
    payload2 = {
        'message': {
            'subject': 'Test Email with From Field',
            'body': {'contentType': 'Text', 'content': 'This is a test email with explicit from field.'},
            'from': {'emailAddress': {'name': 'Magnum Opus Consultants', 'address': GRAPH_MAILBOX}},
            'toRecipients': [{'emailAddress': {'address': 'ethansevenster5@gmail.com'}}],
        },
        'saveToSentItems': False,
    }
    
    try:
        r = requests.post(
            f'https://graph.microsoft.com/v1.0/users/{GRAPH_MAILBOX}/sendMail',
            headers=headers,
            json=payload2,
            timeout=30
        )
        print(f"Result: Status {r.status_code}")
        if r.status_code == 202:
            print("✅ SUCCESS! Email with from field sent")
        else:
            print(f"❌ Failed: {r.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: With saveToSentItems true
    print(f"\n📧 Test 3: With saveToSentItems = true")
    payload3 = {
        'message': {
            'subject': 'Test Email Save to Sent',
            'body': {'contentType': 'Text', 'content': 'Testing save to sent items.'},
            'toRecipients': [{'emailAddress': {'address': 'ethansevenster5@gmail.com'}}],
        },
        'saveToSentItems': True,
    }
    
    try:
        r = requests.post(
            f'https://graph.microsoft.com/v1.0/users/{GRAPH_MAILBOX}/sendMail',
            headers=headers,
            json=payload3,
            timeout=30
        )
        print(f"Result: Status {r.status_code}")
        if r.status_code == 202:
            print("✅ SUCCESS! Email saved to sent items")
        else:
            print(f"❌ Failed: {r.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n📋 Summary:")
    print(f"   GRAPH_MAILBOX: {GRAPH_MAILBOX}")
    print(f"   Target: ethansevenster5@gmail.com")
    print(f"   Check your Gmail inbox for any successful test emails")

if __name__ == "__main__":
    test_simple_email()