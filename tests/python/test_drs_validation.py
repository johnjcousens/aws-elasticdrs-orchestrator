"""
Test DRS Server Validation

Verifies that the API now rejects fake server IDs and only accepts real DRS servers.
"""

import boto3
import requests
import json

# Test Configuration
API_ENDPOINT = "https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test"
USER_POOL_ID = "us-east-1_wfyuacMBX"
USER_POOL_CLIENT_ID = "48fk7bjefk88aejr1rc7dvmbv0"
REGION = "us-east-1"
USERNAME = "testuser@example.com"
PASSWORD = "IiG2b1o+D$"

# Authenticate
print("🔐 Authenticating...")
cognito = boto3.client('cognito-idp', region_name=REGION)
auth_response = cognito.initiate_auth(
    ClientId=USER_POOL_CLIENT_ID,
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={'USERNAME': USERNAME, 'PASSWORD': PASSWORD}
)
token = auth_response['AuthenticationResult']['IdToken']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("\n" + "="*70)
print("TEST 1: Verify FAKE Server IDs Are REJECTED")
print("="*70)

fake_payload = {
    "GroupName": "FakeGroup",
    "Region": "us-east-1",
    "Description": "Test with fake servers",
    "AccountId": "123456789012",
    "sourceServerIds": ["i-fakeid001", "i-fakeid002"]  # Fake EC2-style IDs
}

print(f"\n📤 Attempting to create PG with FAKE server IDs...")
print(f"   Server IDs: {fake_payload['sourceServerIds']}")

response = requests.post(
    f"{API_ENDPOINT}/protection-groups",
    headers=headers,
    json=fake_payload
)

print(f"\n📥 Response: {response.status_code}")
print(f"   Body: {response.text}")

if response.status_code == 400:
    print("\n✅ SUCCESS! Fake server IDs were REJECTED as expected")
else:
    print(f"\n❌ FAILED! Expected 400 error, got {response.status_code}")

print("\n" + "="*70)
print("TEST 2: Verify REAL Server IDs Are ACCEPTED")
print("="*70)

# Get real DRS servers
print("\n🔍 Getting real DRS servers...")
drs = boto3.client('drs', region_name='us-east-1')
servers_response = drs.describe_source_servers()
real_servers = [s['sourceServerID'] for s in servers_response.get('items', [])][:2]

print(f"   Found {len(real_servers)} servers: {real_servers}")

real_payload = {
    "GroupName": "RealGroup-Test",
    "Region": "us-east-1", 
    "Description": "Test with real DRS servers",
    "AccountId": "123456789012",
    "sourceServerIds": real_servers
}

print(f"\n📤 Attempting to create PG with REAL server IDs...")
response = requests.post(
    f"{API_ENDPOINT}/protection-groups",
    headers=headers,
    json=real_payload
)

print(f"\n📥 Response: {response.status_code}")
if response.status_code == 201:
    pg_data = response.json()
    pg_id = pg_data.get('protectionGroupId')
    print(f"   Created PG: {pg_id}")
    print("\n✅ SUCCESS! Real server IDs were ACCEPTED")
    
    # Clean up
    print(f"\n🧹 Cleaning up test PG...")
    requests.delete(f"{API_ENDPOINT}/protection-groups/{pg_id}", headers=headers)
else:
    print(f"   Body: {response.text}")
    print(f"\n❌ FAILED! Expected 201 created, got {response.status_code}")

print("\n" + "="*70)
print("VALIDATION TESTS COMPLETE")
print("="*70)
