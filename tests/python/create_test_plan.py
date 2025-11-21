#!/usr/bin/env python3
"""
Create TEST Recovery Plan with actual Protection Groups for UI verification
"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.test')

API_URL = os.getenv('API_URL', 'https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test')
TOKEN = os.getenv('COGNITO_TOKEN')

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

print("🔍 Step 1: Getting Protection Groups...")
response = requests.get(f'{API_URL}/protection-groups', headers=headers)
response.raise_for_status()
pgs = response.json()

# Find target PGs
pg_map = {}
for pg in pgs:
    if pg['name'] in ['WebServers', 'AppServers', 'DatabaseServers']:
        pg_map[pg['name']] = pg['id']
        print(f"  ✓ {pg['name']}: {pg['id']}")

if len(pg_map) != 3:
    print(f"❌ Error: Need all 3 Protection Groups. Found: {list(pg_map.keys())}")
    exit(1)

print("\n🔍 Step 2: Getting servers from each Protection Group...")
waves_data = []

# Wave 1: Web - Select 2 servers from WebServers
response = requests.get(f'{API_URL}/protection-groups/{pg_map["WebServers"]}/servers', headers=headers)
response.raise_for_status()
web_servers = response.json()
selected_web = [s['serverId'] for s in web_servers[:2]]
print(f"  ✓ WebServers: Selected 2 of {len(web_servers)} servers")
print(f"    Server IDs: {selected_web}")

waves_data.append({
    "WaveName": "Web",
    "ProtectionGroupId": pg_map["WebServers"],
    "ServerIds": selected_web
})

# Wave 2: App - Select 2 of 4 servers from AppServers
response = requests.get(f'{API_URL}/protection-groups/{pg_map["AppServers"]}/servers', headers=headers)
response.raise_for_status()
app_servers = response.json()
selected_app = [s['serverId'] for s in app_servers[:2]]
print(f"  ✓ AppServers: Selected 2 of {len(app_servers)} servers")
print(f"    Server IDs: {selected_app}")

waves_data.append({
    "WaveName": "App",
    "ProtectionGroupId": pg_map["AppServers"],
    "ServerIds": selected_app
})

# Wave 3: Database - Select last 2 servers from DatabaseServers
response = requests.get(f'{API_URL}/protection-groups/{pg_map["DatabaseServers"]}/servers', headers=headers)
response.raise_for_status()
db_servers = response.json()
selected_db = [s['serverId'] for s in db_servers[-2:]] if len(db_servers) >= 2 else [s['serverId'] for s in db_servers]
print(f"  ✓ DatabaseServers: Selected last 2 of {len(db_servers)} servers")
print(f"    Server IDs: {selected_db}")

waves_data.append({
    "WaveName": "Database",
    "ProtectionGroupId": pg_map["DatabaseServers"],
    "ServerIds": selected_db
})

print("\n🚀 Step 3: Creating Recovery Plan 'TEST'...")
recovery_plan_data = {
    "PlanName": "TEST",
    "Description": "Test plan for UI verification - 3 waves with actual Protection Groups",
    "Waves": waves_data
}

print(f"\n📋 Recovery Plan Payload:")
print(json.dumps(recovery_plan_data, indent=2))

response = requests.post(
    f'{API_URL}/recovery-plans',
    headers=headers,
    json=recovery_plan_data
)

if response.status_code == 201:
    result = response.json()
    print(f"\n✅ SUCCESS! Recovery Plan created:")
    print(f"   Plan ID: {result.get('id', 'N/A')}")
    print(f"   Plan Name: {result.get('name', 'TEST')}")
    print(f"   Waves: {len(result.get('waves', []))}")
    print(f"\n🌐 Check UI at: https://d1wfyuosowt0hl.cloudfront.net/recovery-plans")
    print(f"\n✓ Plan left in system - NOT deleted - you can verify in UI")
else:
    print(f"\n❌ ERROR: Failed to create Recovery Plan")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    exit(1)
