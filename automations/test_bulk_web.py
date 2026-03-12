#!/usr/bin/env python3
"""
Test bulk email sending via HTTP POST to the web interface
"""
import requests
import json
import time

# Test credentials (replace with actual admin credentials)
LOGIN_URL = "http://127.0.0.1:8000/login/"
SEND_URL = "http://127.0.0.1:8000/useu-list/send-all/"

def test_bulk_email_via_web():
    print("🔧 Testing bulk email via web interface...")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # First, try to get the login page to get CSRF token
    print("📡 Getting login page...")
    try:
        login_page = session.get(LOGIN_URL, timeout=10)
        if login_page.status_code != 200:
            print(f"❌ Failed to get login page: {login_page.status_code}")
            return
        
        # Look for CSRF token in the response
        csrf_token = None
        if 'csrfmiddlewaretoken' in login_page.text:
            # Extract CSRF token from the form
            import re
            csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
        
        if not csrf_token:
            print("❌ Could not find CSRF token")
            return
            
        print(f"✅ Got CSRF token: {csrf_token[:10]}...")
        
    except requests.RequestException as e:
        print(f"❌ Error connecting to server: {e}")
        print("💡 Make sure Django development server is running:")
        print("   python manage.py runserver")
        return
    
    # Try to login (you may need to provide actual credentials)
    print("🔐 Attempting login...")
    login_data = {
        'username': 'admin',  # Replace with actual username
        'password': 'password',  # Replace with actual password
        'csrfmiddlewaretoken': csrf_token,
    }
    
    try:
        login_response = session.post(LOGIN_URL, data=login_data, timeout=10)
        if login_response.status_code == 200 and 'login' not in login_response.url.lower():
            print("✅ Login successful")
        else:
            print("❌ Login failed - you may need to update credentials in this script")
            print("💡 Or test manually by:")
            print("   1. Starting Django: python manage.py runserver")
            print("   2. Going to http://127.0.0.1:8000/useu-list/")
            print("   3. Clicking 'Send All TP1' button")
            return
            
    except requests.RequestException as e:
        print(f"❌ Login request failed: {e}")
        return
    
    # Now try to send emails
    print("📧 Triggering bulk email send...")
    send_data = {
        'touchpoint_number': 1  # Send TP1
    }
    
    try:
        send_response = session.post(
            SEND_URL, 
            data=json.dumps(send_data),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if send_response.status_code == 200:
            result = send_response.json()
            if result.get('ok'):
                print(f"✅ Bulk email triggered successfully!")
                print(f"📊 Job ID: {result.get('job_id')}")
                print(f"📊 Total contacts: {result.get('total')}")
                print("🔍 Debug logs should now show:")
                print("   [BULK DEBUG] Sending to: contact@example.com")
                print("   [DEBUG] Attempting Graph API email send to: contact@example.com")
                return True
            else:
                print(f"❌ Send request failed: {result.get('error')}")
        else:
            print(f"❌ HTTP error: {send_response.status_code}")
            print(f"Response: {send_response.text[:200]}...")
            
    except requests.RequestException as e:
        print(f"❌ Send request failed: {e}")
    
    return False

if __name__ == "__main__":
    print("🚀 Make sure Django is running first:")
    print("   cd automations && python manage.py runserver")
    print("")
    input("Press Enter when Django is running...")
    test_bulk_email_via_web()