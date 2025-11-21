#!/usr/bin/env python3
"""
Automated API test for Protection Groups selection fix
Tests that Protection Groups have SourceServerIds field populated
"""
import boto3
import requests
import json
import sys

# Config
USER_POOL_ID = 'us-east-1_S3wvMGaT0'
CLIENT_ID = '31jqv7bghmie564eehjpgqf2tr'
USERNAME = 'apitest@example.com'
PASSWORD = 'ApiTest123!'
API_ENDPOINT = 'https://19rzo4z35f.execute-api.us-east-1.amazonaws.com/test'

def get_auth_token():
    """Get Cognito ID token"""
    try:
        client = boto3.client('cognito-idp', region_name='us-east-1')
        response = client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': USERNAME,
                'PASSWORD': PASSWORD
            }
        )
        return response['AuthenticationResult']['IdToken']
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return None

def test_protection_groups_api():
    """Test that Protection Groups API returns SourceServerIds"""
    print("\n🧪 Testing Protection Groups API...")
    
    # Get token
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate")
        return False
    
    print("✅ Authenticated successfully")
    
    # Call API
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{API_ENDPOINT}/protection-groups', headers=headers)
    
    if response.status_code != 200:
        print(f"❌ API call failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    print(f"✅ API returned {response.status_code}")
    
    # Parse response
    data = response.json()
    pgs = data.get('groups', []) if isinstance(data, dict) else []
    
    if not pgs:
        print("❌ No Protection Groups returned")
        return False
    
    print(f"✅ Found {len(pgs)} Protection Groups")
    
    # Check each PG has SourceServerIds
    all_valid = True
    for pg in pgs:
        pg_name = pg.get('name') or pg.get('Name') or pg.get('GroupName', 'Unknown')
        source_servers = pg.get('SourceServerIds') or pg.get('sourceServerIds')
        
        if not source_servers:
            print(f"❌ {pg_name}: Missing SourceServerIds field")
            all_valid = False
        elif not isinstance(source_servers, list):
            print(f"❌ {pg_name}: SourceServerIds is not a list")
            all_valid = False
        elif len(source_servers) == 0:
            print(f"⚠️  {pg_name}: SourceServerIds is empty")
        else:
            print(f"✅ {pg_name}: Has {len(source_servers)} servers")
    
    return all_valid

if __name__ == '__main__':
    print("=" * 60)
    print("PROTECTION GROUPS API FIX VALIDATION")
    print("=" * 60)
    
    success = test_protection_groups_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED - Protection Groups API working correctly!")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED - Protection Groups API has issues")
        sys.exit(1)
