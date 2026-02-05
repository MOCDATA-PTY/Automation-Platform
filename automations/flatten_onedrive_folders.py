"""
Flatten OneDrive folder structure - Move all Excel files to root folder
Removes year subfolders (2020, 2021, 2022, etc.) and puts all files in main folder
Standalone script - no Django required.
"""
import json
import os
import msal
import requests

# Config
CLIENT_ID = '43fbe5a9-6b5b-4c81-9067-7aff9ac3ed5a'
TENANT_ID = 'b1504b1d-d096-409a-a0f0-6cc546dde993'
CLIENT_SECRET = 'w6B8Q~W3ac9klXa8NkMDo4cPNyOsjEryVL5TwdhQ'
SCOPES = ['Files.Read.All', 'Files.ReadWrite.All']
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'onedrive_token.json')
GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
FOLDER_PATH = '/Automation Platform/Turn Over Automation Report'


def get_access_token():
    """Get a valid access token, refreshing if needed"""
    if not os.path.exists(TOKEN_FILE):
        print("Error: No token file found. Run auth.py first.")
        return None

    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)

    # Try refresh token first to get a fresh access token
    refresh_token = token_data.get('refresh_token')
    if refresh_token:
        app = msal.ConfidentialClientApplication(
            CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            client_credential=CLIENT_SECRET
        )
        result = app.acquire_token_by_refresh_token(refresh_token, scopes=SCOPES)
        if 'access_token' in result:
            # Save the new token
            with open(TOKEN_FILE, 'w') as f:
                json.dump(result, f, indent=2)
            return result['access_token']
        else:
            print(f"Token refresh failed: {result.get('error_description', 'unknown')}")

    # Fall back to saved access token
    return token_data.get('access_token')


def list_all_items_recursive(token, folder_path='/'):
    """List all items (files and folders) recursively"""
    headers = {'Authorization': f'Bearer {token}'}

    if folder_path == '/':
        url = f'{GRAPH_API_ENDPOINT}/me/drive/root/children'
    else:
        url = f'{GRAPH_API_ENDPOINT}/me/drive/root:{folder_path}:/children'

    items = []

    def list_folder(folder_url, current_path):
        response = requests.get(folder_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('value', []):
                item_name = item['name']
                item_path = f"{current_path}/{item_name}".replace('//', '/')

                if 'folder' in item:
                    items.append({
                        'type': 'folder',
                        'id': item['id'],
                        'name': item_name,
                        'path': item_path,
                        'parent_id': item.get('parentReference', {}).get('id')
                    })
                    list_folder(f"{GRAPH_API_ENDPOINT}/me/drive/items/{item['id']}/children", item_path)
                elif 'file' in item:
                    items.append({
                        'type': 'file',
                        'id': item['id'],
                        'name': item_name,
                        'path': item_path,
                        'parent_id': item.get('parentReference', {}).get('id'),
                        'parent_path': item.get('parentReference', {}).get('path', '')
                    })
        else:
            print(f"  Warning: Got {response.status_code} listing {current_path}")
            print(f"  {response.text[:200]}")

    list_folder(url, folder_path)
    return items


def get_root_folder_id(token, folder_path):
    """Get the ID of the root folder"""
    headers = {'Authorization': f'Bearer {token}'}

    if folder_path == '/':
        url = f'{GRAPH_API_ENDPOINT}/me/drive/root'
    else:
        url = f'{GRAPH_API_ENDPOINT}/me/drive/root:{folder_path}'

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['id']
    print(f"  Error getting folder: {response.status_code} {response.text[:200]}")
    return None


def move_file_to_root(token, file_id, file_name, root_folder_id):
    """Move a file to the root folder"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    url = f'{GRAPH_API_ENDPOINT}/me/drive/items/{file_id}'
    payload = {
        'parentReference': {'id': root_folder_id},
        'name': file_name
    }

    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code != 200:
        print(f" (error {response.status_code}: {response.text[:100]})", end='')
    return response.status_code == 200


def delete_empty_folder(token, folder_id):
    """Delete an empty folder"""
    headers = {'Authorization': f'Bearer {token}'}
    url = f'{GRAPH_API_ENDPOINT}/me/drive/items/{folder_id}'

    response = requests.delete(url, headers=headers)
    return response.status_code == 204


def main():
    folder_path = FOLDER_PATH

    print("=" * 80)
    print("OneDrive Folder Flattening Tool")
    print("=" * 80)
    print(f"Target folder: {folder_path}")
    print()
    print("This will move all Excel files from year subfolders into the root folder.")
    print()

    # Get token
    print("Getting access token...")
    token = get_access_token()
    if not token:
        print("Error: Could not get access token. Run auth.py first.")
        return

    print("Token OK")
    print()

    # Get root folder ID
    print("Getting root folder information...")
    root_folder_id = get_root_folder_id(token, folder_path)
    if not root_folder_id:
        print("Error: Could not get root folder ID")
        return

    print(f"Root folder ID: {root_folder_id}")
    print()

    # List all items
    print("Scanning OneDrive folder structure...")
    items = list_all_items_recursive(token, folder_path)

    # Separate files and folders
    files = [item for item in items if item['type'] == 'file']
    folders = [item for item in items if item['type'] == 'folder']

    # Filter Excel files in subfolders (parent_id != root_folder_id)
    excel_files = [f for f in files if f['name'].lower().endswith(('.xlsx', '.xls'))]
    files_to_move = [f for f in excel_files if f['parent_id'] != root_folder_id]

    print()
    print(f"Found {len(excel_files)} Excel files total")
    print(f"Found {len(files_to_move)} files in subfolders that need to be moved")
    print(f"Found {len(folders)} subfolders")
    print()

    if not files_to_move:
        print("All files are already in the root folder!")
        return

    # Show what will be moved
    print("Files to be moved:")
    print("-" * 80)
    for file in files_to_move:
        print(f"  {file['path']}  ->  {folder_path}/{file['name']}")
    print("-" * 80)
    print()

    # Ask for confirmation
    response = input("Proceed with moving these files? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Operation cancelled.")
        return

    print()
    print("Moving files...")
    print("-" * 80)

    moved_count = 0
    failed_count = 0

    for file in files_to_move:
        print(f"  {file['name']}... ", end='', flush=True)
        success = move_file_to_root(token, file['id'], file['name'], root_folder_id)
        if success:
            print("OK")
            moved_count += 1
        else:
            print("FAILED")
            failed_count += 1

    print("-" * 80)
    print(f"Moved: {moved_count} | Failed: {failed_count}")
    print()

    # Delete empty year folders
    if folders and moved_count > 0:
        print(f"Cleaning up {len(folders)} empty subfolders...")
        print("-" * 80)

        deleted_count = 0
        # Deepest first so children are deleted before parents
        folders_sorted = sorted(folders, key=lambda x: x['path'].count('/'), reverse=True)

        for folder in folders_sorted:
            print(f"  {folder['name']}... ", end='', flush=True)
            success = delete_empty_folder(token, folder['id'])
            if success:
                print("deleted")
                deleted_count += 1
            else:
                print("skipped (not empty)")

        print("-" * 80)
        print(f"Deleted: {deleted_count} folders")

    print()
    print("=" * 80)
    print("Done! All Excel files are now in:")
    print(f"  {folder_path}")
    print("=" * 80)
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
