#!/usr/bin/env python3
"""
Check Graph API token permissions and available mailboxes
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

from dashboard.views import _get_graph_token
import requests
import json

def check_token_permissions():
    print("🔍 Checking Graph API token and permissions...")
    
    # Get token
    token = _get_graph_token()
    if not token:
        print("❌ Failed to get Graph API token")
        return
    
    print("✅ Got Graph API token")
    headers = {'Authorization': f'Bearer {token}'}
    
    # Check current user profile
    print("\n👤 Checking current user profile...")
    try:
        r = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
        if r.status_code == 200:
            user = r.json()
            print(f"✅ Current user: {user.get('displayName')} ({user.get('userPrincipalName')})")
            print(f"   Email: {user.get('mail')}")
        else:
            print(f"❌ Failed to get user profile: {r.status_code}")
            print(f"Response: {r.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Check mailboxes we can access
    print("\n📫 Checking accessible mailboxes...")
    try:
        r = requests.get('https://graph.microsoft.com/v1.0/me/mailFolders', headers=headers)
        if r.status_code == 200:
            print("✅ Can access own mailbox")
        else:
            print(f"❌ Cannot access own mailbox: {r.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Try to access shared mailbox
    print(f"\n🔄 Testing access to shared mailbox: waldogaybba@moc-pty.com")
    try:
        r = requests.get('https://graph.microsoft.com/v1.0/users/waldogaybba@moc-pty.com/mailFolders', headers=headers)
        if r.status_code == 200:
            print("✅ Can access shared mailbox folders")
        else:
            print(f"❌ Cannot access shared mailbox folders: {r.status_code}")
            print(f"Response: {r.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test send permission from user's own account
    print(f"\n📧 Testing send permission from user's own account...")
    test_payload = {
        'message': {
            'subject': 'Test Permission Check',
            'body': {'contentType': 'Text', 'content': 'Testing send permissions'},
            'toRecipients': [{'emailAddress': {'address': 'ethansevenster5@gmail.com'}}],
        },
        'saveToSentItems': False  # Don't actually save it
    }
    
    try:
        # Try sending from user's own account (not shared mailbox)
        r = requests.post(
            'https://graph.microsoft.com/v1.0/me/sendMail',  # Send from 'me' not shared mailbox
            headers={**headers, 'Content-Type': 'application/json'},
            json=test_payload
        )
        if r.status_code == 202:
            print("✅ CAN send from user's own account!")
            print("💡 Suggestion: Change FROM address to ethan.sevenster@moc-pty.com")
        else:
            print(f"❌ Cannot send from user's own account: {r.status_code}")
            print(f"Response: {r.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test send permission from shared mailbox
    print(f"\n📧 Testing send permission from shared mailbox...")
    try:
        r = requests.post(
            'https://graph.microsoft.com/v1.0/users/waldogaybba@moc-pty.com/sendMail',
            headers={**headers, 'Content-Type': 'application/json'},
            json=test_payload
        )
        if r.status_code == 202:
            print("✅ CAN send from shared mailbox!")
        else:
            print(f"❌ Cannot send from shared mailbox: {r.status_code}")
            print(f"Response: {r.text}")
            if r.status_code == 403:
                print("🔍 403 = Permission denied. App needs 'Send As' permission for shared mailbox")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n📋 Summary:")
    print("- If user account works: Change GRAPH_MAILBOX to ethan.sevenster@moc-pty.com")
    print("- If shared mailbox needed: Add 'Send As' permission in Azure AD")
    print("- Check Exchange Online permissions for shared mailbox access")

if __name__ == "__main__":
    check_token_permissions()