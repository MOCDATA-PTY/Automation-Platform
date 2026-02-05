"""
List OneDrive contents to find folder paths
"""
import json
import requests

TOKEN_FILE = 'onedrive_token.json'
GRAPH_API = 'https://graph.microsoft.com/v1.0'

def list_onedrive_contents(path='/', depth=0):
    """List files and folders in OneDrive recursively"""
    # Load token
    try:
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)
            token = token_data.get('access_token')
    except FileNotFoundError:
        print("Error: Token file not found. Run 'python3 auth.py' first.")
        return

    headers = {'Authorization': f'Bearer {token}'}

    # Get folder contents
    if path == '/':
        url = f'{GRAPH_API}/me/drive/root/children'
    else:
        url = f'{GRAPH_API}/me/drive/root:{path}:/children'

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        indent = "  " * depth

        for item in data.get('value', []):
            name = item['name']
            item_path = f"{path}/{name}".replace('//', '/')

            if 'folder' in item:
                # It's a folder
                print(f"{indent}[FOLDER] {name}")
                print(f"{indent}  Path: {item_path}")

                # Recursively list subfolder contents (limit depth to 3)
                if depth < 3:
                    list_onedrive_contents(item_path, depth + 1)
            else:
                # It's a file
                size = item.get('size', 0)
                size_mb = size / (1024 * 1024)
                print(f"{indent}[FILE] {name} ({size_mb:.2f} MB)")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Error: Token expired or invalid. Run 'python3 auth.py' again.")
        else:
            print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("OneDrive Contents")
    print("=" * 60)
    print()
    list_onedrive_contents()
    print()
    print("=" * 60)
    print("Use the folder paths above to update ONEDRIVE_FOLDER_PATH")
    print("in automations/settings.py")
    print("=" * 60)
