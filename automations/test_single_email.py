#!/usr/bin/env python3
"""
Single Email Test - Send to ethansevenster5@gmail.com from shared mailbox
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

from dashboard.views import _get_graph_token, _graph_send_mail
import json

def test_single_email():
    print("🔧 Testing single email send...")
    
    # Get Graph API token
    print("📡 Getting Graph API token...")
    token = _get_graph_token()
    if not token:
        print("❌ Failed to get Graph API token!")
        return
    print("✅ Got Graph API token")
    
    # Create email payload
    email_payload = {
        "message": {
            "subject": "🔧 TEST EMAIL - Shared Mailbox Test",
            "body": {
                "contentType": "HTML",
                "content": """
                <html>
                <body>
                    <h2>🔧 Test Email from Shared Mailbox</h2>
                    <p>This is a test email sent from <strong>waldogaybba@moc-pty.com</strong> shared mailbox.</p>
                    <p>If you receive this, the email system is working!</p>
                    <p>Time: """ + str(datetime.datetime.now()) + """</p>
                </body>
                </html>
                """
            },
            "from": {
                "emailAddress": {
                    "address": "waldogaybba@moc-pty.com",
                    "name": "Magnum Opus Consultants"
                }
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": "ethansevenster5@gmail.com",
                        "name": "Ethan Test"
                    }
                }
            ]
        },
        "saveToSentItems": True
    }
    
    print("📧 Sending email to ethansevenster5@gmail.com...")
    print(f"📧 From shared mailbox: waldogaybba@moc-pty.com")
    
    # Send the email
    success, status_code = _graph_send_mail(token, email_payload)
    
    if success:
        print(f"✅ EMAIL SENT SUCCESSFULLY! Status: {status_code}")
        print("📬 Check ethansevenster5@gmail.com inbox (and spam folder)")
        print("📤 Email should also appear in waldogaybba@moc-pty.com sent items")
        print("\n🔍 Debug: Status 202 means Microsoft Graph accepted the email for delivery")
        print("🔍 If you don't receive it, check:")
        print("   - Spam/junk folder in Gmail")
        print("   - Sent items in waldogaybba@moc-pty.com")
        print("   - Email delivery delays (can take 1-5 minutes)")
    else:
        print(f"❌ EMAIL FAILED! Status code: {status_code}")
        
        # Try to get more debug info
        print("\n🔍 Debug info:")
        print(f"Token length: {len(token) if token else 'None'}")
        print(f"Recipient: ethansevenster5@gmail.com")
        print(f"Shared mailbox: waldogaybba@moc-pty.com")
        
        # Common error codes
        if status_code == 401:
            print("❌ Authentication failed - token expired or invalid")
        elif status_code == 403:
            print("❌ Permission denied - app may not have Send As permission for shared mailbox")
        elif status_code == 404:
            print("❌ Mailbox not found - check if waldogaybba@moc-pty.com exists")
        elif status_code == 429:
            print("❌ Rate limited - too many requests")
        elif status_code == 0:
            print("❌ Network error or timeout")
    
    return success

if __name__ == "__main__":
    import datetime
    test_single_email()