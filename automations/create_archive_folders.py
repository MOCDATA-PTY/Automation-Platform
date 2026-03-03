#!/usr/bin/env python3
"""Create an Archive subfolder inside each PNL station folder on OneDrive."""
import os, sys, django, requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automations.settings')
django.setup()

from dashboard.onedrive_sync import get_access_token, GRAPH_API_ENDPOINT

STATION_FOLDERS = [
    '/Automation Platform/PPG Financial Analysis Report',
    '/Automation Platform/DOR Financial Analysis Report',
    '/Automation Platform/CON Financial Analysis Report',
    '/Automation Platform/ATL Financial Analysis Report',
    '/Automation Platform/HNL Financial Analysis Report',
    '/Automation Platform/JFK Financial Analysis Report',
    '/Automation Platform/CCC Financial Analysis Report',
    '/Automation Platform/CCD Financial Analysis Report',
    '/Automation Platform/FAX Financial Analysis Report',
    '/Automation Platform/IMP Financial Analysis Report',
    '/Automation Platform/HOU Financial Analysis Report',
    '/Automation Platform/ICS  Financial Analysis Report',
    '/Automation Platform/LAX Financial Analysis Report',
    '/Automation Platform/LCL Financial Analysis Report',
    '/Automation Platform/ORD Financial Analysis Report',
]

token = get_access_token()
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

for folder in STATION_FOLDERS:
    url = f"{GRAPH_API_ENDPOINT}/me/drive/root:{folder}:/children"
    resp = requests.post(url, headers=headers, json={"name": "Archive", "folder": {}, "@microsoft.graph.conflictBehavior": "fail"})
    station = folder.split('/')[-1]
    if resp.status_code == 201:
        print(f"  [CREATED]  {station}/Archive")
    elif resp.status_code == 409:
        print(f"  [EXISTS]   {station}/Archive")
    else:
        print(f"  [ERROR]    {station}/Archive  (HTTP {resp.status_code}: {resp.text[:80]})")
