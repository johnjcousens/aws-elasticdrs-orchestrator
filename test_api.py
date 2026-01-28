#!/usr/bin/env python3
import boto3
import json
import requests
import sys

# Get credentials
secrets = boto3.client('secretsmanager', region_name='us-east-1')
secret = json.loads(secrets.get_secret_value(
    SecretId='arn:aws:secretsmanager:us-east-1:438465159935:secret:drs-orchestration/test-user-credentials-vV4S44'
)['SecretString'])

# Authenticate with Cognito
client = boto3.client('cognito-idp', region_name='us-east-1')

response = client.admin_initiate_auth(
    UserPoolId=secret['userPoolId'],
    ClientId=secret['clientId'],
    AuthFlow='ADMIN_NO_SRP_AUTH',
    AuthParameters={
        'USERNAME': secret['username'],
        'PASSWORD': secret['password']
    }
)

id_token = response['AuthenticationResult']['IdToken']
print(f"✅ Authenticated successfully\n")

# Test Protection Groups API
api_endpoint = "https://q9hfc15oh1.execute-api.us-east-1.amazonaws.com/test"
headers = {
    'Authorization': id_token,
    'Content-Type': 'application/json'
}

print(f"📡 Testing GET /protection-groups")
response = requests.get(f"{api_endpoint}/protection-groups", headers=headers)
print(f"Status: {response.status_code}\n")

if response.status_code == 200:
    data = response.json()
    print(f"✅ Protection Groups Response:")
    for pg in data.get('protectionGroups', []):
        print(f"\n  📦 {pg.get('groupName')}")
        print(f"     ID: {pg.get('protectionGroupId')}")
        print(f"     sourceServerIds: {pg.get('sourceServerIds', [])}")
        print(f"     serverSelectionTags: {pg.get('serverSelectionTags', {})}")
else:
    print(f"❌ Error: {response.text}")
