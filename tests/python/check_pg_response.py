#!/usr/bin/env python3
"""Check what Protection Groups API actually returns"""
import boto3
import requests
import json

API_ENDPOINT = "https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test"
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
headers = {'Authorization': f'Bearer {token}'}

print("\n📦 Fetching Protection Groups...")
r = requests.get(f'{API_ENDPOINT}/protection-groups', headers=headers)
print(f"\nStatus: {r.status_code}")
print(f"\nResponse JSON:")
print(json.dumps(r.json(), indent=2))
