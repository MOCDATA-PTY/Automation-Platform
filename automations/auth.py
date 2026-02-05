"""
One-time OneDrive authentication script
Run this once to authenticate with OneDrive
Token will be saved and used by the dashboard for 24 months
"""
import json
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import msal

# OneDrive app credentials
CLIENT_ID = '43fbe5a9-6b5b-4c81-9067-7aff9ac3ed5a'
TENANT_ID = 'b1504b1d-d096-409a-a0f0-6cc546dde993'
CLIENT_SECRET = 'w6B8Q~W3ac9klXa8NkMDo4cPNyOsjEryVL5TwdhQ'
REDIRECT_URI = 'http://localhost:8000/onedrive/callback'
SCOPES = ['Files.Read.All', 'Files.ReadWrite.All']
TOKEN_FILE = 'onedrive_token.json'

# Global to capture auth code
auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback"""
    def do_GET(self):
        global auth_code

        # Parse the callback URL
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            auth_code = params['code'][0]

            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
                <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #054B70;">Authentication Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Error: No authorization code received</h1></body></html>')

    def log_message(self, format, *args):
        """Suppress server logs"""
        pass


def authenticate():
    """Run authentication flow"""
    print("=" * 60)
    print("MOC Automations - OneDrive Authentication")
    print("=" * 60)
    print()

    # Create MSAL app
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET
    )

    # Generate auth URL
    auth_url = app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    print("Step 1: Opening browser for authentication...")
    print()
    webbrowser.open(auth_url)

    print("Step 2: Waiting for authorization...")
    print("(If browser doesn't open, copy this URL manually:)")
    print(auth_url)
    print()

    # Start local server to capture callback
    server = HTTPServer(('localhost', 8000), CallbackHandler)
    server.timeout = 120  # 2 minute timeout

    # Wait for one request (the callback)
    server.handle_request()
    server.server_close()

    if not auth_code:
        print("Error: No authorization code received")
        print("Please try again")
        return False

    print()
    print("Step 3: Exchanging authorization code for token...")

    # Exchange code for token
    result = app.acquire_token_by_authorization_code(
        auth_code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    if "access_token" in result:
        # Save token to file
        with open(TOKEN_FILE, 'w') as f:
            json.dump(result, f, indent=2)

        print()
        print("=" * 60)
        print("SUCCESS! OneDrive authentication complete")
        print("=" * 60)
        print()
        print(f"Token saved to: {TOKEN_FILE}")
        print("This token will be valid for 24 months")
        print()
        print("You can now run your dashboard and it will automatically")
        print("use this token to sync from OneDrive.")
        print()
        return True
    else:
        print()
        print("Error: Failed to get access token")
        print(f"Error details: {result.get('error_description', 'Unknown error')}")
        return False


if __name__ == '__main__':
    try:
        success = authenticate()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nAuthentication cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        exit(1)
