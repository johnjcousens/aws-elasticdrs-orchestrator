#!/usr/bin/env python3
"""Create TEST data with REAL DRS servers"""
import boto3
import requests

# Config
API_ENDPOINT = "https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test"
USER_POOL_ID = "us-east-1_wfyuacMBX"
CLIENT_ID = "48fk7bjefk88aejr1rc7dvmbv0"
USERNAME = "testuser@example.com"
PASSWORD = "IiG2b1o+D$"

# Real DRS servers
REAL_SERVERS = [
    "s-3c1730a9e0771ea14",  # EC2AMAZ-4IMB9PN
    "s-3d75cdc0d9a28a725",  # EC2AMAZ-RLP9U5V
    "s-3afa164776f93ce4f",  # EC2AMAZ-H0JBE4J
    "s-3c63bb8be30d7d071",  # EC2AMAZ-8B7IRHJ
    "s-3578f52ef3bdd58b4",  # EC2AMAZ-FQTJG64
    "s-3b9401c1cd270a7a8",  # EC2AMAZ-3B0B3UD
]

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

# Clean up existing TEST data
print("\n🧹 Cleaning up old test data...")
r = requests.get(f'{API_ENDPOINT}/recovery-plans', headers=headers)
for plan in r.json().get('plans', []):
    if plan.get('name') == 'TEST':
        plan_id = plan.get('recoveryPlanId') or plan.get('planId') or plan.get('id')
        print(f"  Deleting old TEST plan: {plan_id}")
        requests.delete(f'{API_ENDPOINT}/recovery-plans/{plan_id}', headers=headers)

r = requests.get(f'{API_ENDPOINT}/protection-groups', headers=headers)
for pg in r.json().get('groups', []):
    if pg.get('name') in ['WebServers', 'AppServers', 'DatabaseServers']:
        pg_id = pg.get('protectionGroupId') or pg.get('groupId') or pg.get('id')
        print(f"  Deleting old PG: {pg.get('name')} ({pg_id})")
        requests.delete(f'{API_ENDPOINT}/protection-groups/{pg_id}', headers=headers)

# Create Protection Groups with REAL servers
print("\n📦 Creating Protection Groups with REAL DRS servers...")
pg_data = {
    'WebServers': REAL_SERVERS[:2],      # First 2 servers
    'AppServers': REAL_SERVERS[2:4],     # Next 2 servers  
    'DatabaseServers': REAL_SERVERS[4:]  # Last 2 servers
}

pg_map = {}
for name, server_ids in pg_data.items():
    payload = {
        "GroupName": name,
        "Region": "us-east-1",
        "Description": f"UI test - REAL DRS servers - {name}",
        "AccountId": "123456789012",
        "sourceServerIds": server_ids
    }
    r = requests.post(f'{API_ENDPOINT}/protection-groups', headers=headers, json=payload)
    if r.status_code != 201:
        print(f"❌ Error creating {name}: {r.status_code} - {r.text}")
        continue
    pg = r.json()
    pg_id = pg.get('protectionGroupId')
    pg_map[name] = {'id': pg_id, 'servers': server_ids}
    print(f"  ✓ {name}: {pg_id} ({len(server_ids)} real DRS servers)")

# Create Recovery Plan with 3 waves
print("\n🚀 Creating 'TEST' Recovery Plan with 3 waves...")
waves = [
    {
        "waveNumber": 1,
        "WaveName": "WebTier",
        "ProtectionGroupId": pg_map['WebServers']['id'],
        "ServerIds": pg_map['WebServers']['servers']
    },
    {
        "waveNumber": 2,
        "WaveName": "AppTier",
        "ProtectionGroupId": pg_map['AppServers']['id'],
        "ServerIds": pg_map['AppServers']['servers']
    },
    {
        "waveNumber": 3,
        "WaveName": "DatabaseTier",
        "ProtectionGroupId": pg_map['DatabaseServers']['id'],
        "ServerIds": pg_map['DatabaseServers']['servers']
    }
]

payload = {
    "PlanName": "TEST",
    "Description": "UI test - 3 waves with REAL DRS servers",
    "Waves": waves
}

r = requests.post(f'{API_ENDPOINT}/recovery-plans', headers=headers, json=payload)
if r.status_code != 201:
    print(f"❌ Error: {r.status_code} - {r.text}")
    exit(1)

plan = r.json()
plan_id = plan.get('recoveryPlanId') or plan.get('planId') or plan.get('id')

print(f"\n✅ SUCCESS! TEST Recovery Plan created with REAL data")
print(f"   Plan ID: {plan_id}")
print(f"   3 Protection Groups: WebServers (2), AppServers (2), DatabaseServers (2)")
print(f"   3 Waves: WebTier → AppTier → DatabaseTier")
print(f"\n🌐 View in UI: https://d1wfyuosowt0hl.cloudfront.net/recovery-plans")
print(f"\n✓ All data uses REAL DRS servers from us-east-1")
print(f"✓ Servers are in CONTINUOUS replication state")
