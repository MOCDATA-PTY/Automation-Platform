"""
Test OneDrive sync - grab turnover data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automations.settings')

import django
django.setup()

from dashboard.onedrive_sync import sync_turnover_data

if __name__ == '__main__':
    print("=" * 60)
    print("Testing OneDrive Turnover Data Sync")
    print("=" * 60)
    print()

    try:
        count = sync_turnover_data()
        print()
        print("=" * 60)
        print(f"SUCCESS! Synced {count} records to database")
        print("=" * 60)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
