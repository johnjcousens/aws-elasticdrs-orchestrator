#!/usr/bin/env python3
"""Create TEST plan - standalone script"""
import boto3
import requests

# Config from test file
API_ENDPOINT = "https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test"
USER_POOL_ID = "us-east-1_wfyuacMBX"
CLIENT_ID = "48fk7bjefk88aejr1rc7dvmbv0"
USERNAME = "***REMOVED***"
PASSWORD = "IiG2b1o+D$"

# Get auth token
print("🔐 Authenticating...")
cognito = boto3.client('cognito-idp', region_name='us-east-1')
response = cognito.initiate_auth(
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={'USERNAME': USERNAME, 'PASSWORD': PASSWORD},
    ClientId=CLIENT_ID
)
token = response['AuthenticationResult']['IdToken']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Get existing Protection Groups
print("\n📦 Getting existing Protection Groups...")
r = requests.get(f'{API_ENDPOINT}/protection-groups', headers=headers)
r.raise_for_status()
response_data = r.json()
print(f"DEBUG Full response: {response_data}")
all_pgs = response_data.get('groups', [])
print(f"DEBUG Groups: {all_pgs}")

# Use WebServers PG only
if not all_pgs:
    print("❌ No Protection Groups found!")
    exit(1)

web_pg = all_pgs[0]
pg_id = web_pg['protectionGroupId']
servers = web_pg['sourceServerIds']
print(f"  ✓ Using {web_pg['name']}: {pg_id} ({len(servers)} servers)")

# Single wave plan  
waves = [
    {"waveNumber": 1, "WaveName": "WebTier", "ProtectionGroupId": pg_id, "ServerIds": servers}
]

print("\n🚀 Creating 'TEST' Recovery Plan...")
payload = {"PlanName": "TEST", "Description": "UI test - 1 wave", "Waves": waves}
print(f"DEBUG Payload: {payload}")
r = requests.post(f'{API_ENDPOINT}/recovery-plans', headers=headers, json=payload)
if r.status_code != 201:
    print(f"❌ Error: {r.status_code} - {r.text}")
r.raise_for_status()
plan = r.json()
print(f"DEBUG Plan response: {plan}")

plan_id = plan.get('id') or plan.get('planId') or plan.get('recoveryPlanId')
print(f"\n✅ SUCCESS! Plan created")
print(f"   Plan ID: {plan_id}")
print(f"   Plan Name: {plan.get('name', plan.get('planName', 'TEST'))}")
print(f"\n🌐 View in UI: https://d1wfyuosowt0hl.cloudfront.net/recovery-plans")
print(f"\n✓ Plan 'TEST' is now in the system - NOT deleted")
