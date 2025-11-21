#!/usr/bin/env python3
"""
Clean up ALL Protection Groups and Recovery Plans via API
"""
import boto3
import requests

# Test Configuration
API_ENDPOINT = "https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test"
USER_POOL_ID = "us-east-1_wfyuacMBX"
USER_POOL_CLIENT_ID = "48fk7bjefk88aejr1rc7dvmbv0"
REGION = "us-east-1"
USERNAME = "***REMOVED***"
PASSWORD = "IiG2b1o+D$"

print("🔐 Authenticating...")
client = boto3.client('cognito-idp', region_name=REGION)
response = client.initiate_auth(
    ClientId=USER_POOL_CLIENT_ID,
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={'USERNAME': USERNAME, 'PASSWORD': PASSWORD}
)
token = response['AuthenticationResult']['IdToken']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("\n🗑️  Deleting all Recovery Plans...")
r = requests.get(f'{API_ENDPOINT}/recovery-plans', headers=headers)
plans = r.json().get('plans', [])
print(f"Found {len(plans)} Recovery Plans")
for plan in plans:
    plan_id = plan.get('recoveryPlanId') or plan.get('PlanId')
    plan_name = plan.get('recoveryPlanName') or plan.get('PlanName', 'Unknown')
    if plan_id:
        print(f"  Deleting: {plan_name} ({plan_id})")
        requests.delete(f'{API_ENDPOINT}/recovery-plans/{plan_id}', headers=headers)

print("\n🗑️  Deleting all Protection Groups...")
r = requests.get(f'{API_ENDPOINT}/protection-groups', headers=headers)
groups = r.json().get('groups', [])
print(f"Found {len(groups)} Protection Groups")
for pg in groups:
    pg_id = pg['protectionGroupId']
    pg_name = pg['name']
    print(f"  Deleting: {pg_name} ({pg_id})")
    requests.delete(f'{API_ENDPOINT}/protection-groups/{pg_id}', headers=headers)

print("\n✅ All data cleaned up!")
print("\n📋 Ready for manual UI testing:")
print("   1. Navigate to: https://d1wfyuosowt0hl.cloudfront.net/recovery-plans")
print("   2. First create 3 Protection Groups:")
print("      - WebServers (2 DRS servers)")
print("      - AppServers (4 DRS servers)")  
print("      - DatabaseServers (2 DRS servers)")
print("   3. Then create TEST Recovery Plan with 3 waves as specified")
