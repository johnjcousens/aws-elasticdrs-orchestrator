#!/usr/bin/env python3
"""
E2E API Test for Protection Groups CRUD Operations
Tests POST, GET, PUT, DELETE methods and name uniqueness validation
"""
import boto3
import requests
import json
import sys
import time

# Config - UPDATE THESE AFTER DEPLOYMENT
USER_POOL_ID = 'us-east-1_jKbDOFre2'  # From stack outputs
CLIENT_ID = '79e5u9lflt3hvbuug78mg9okn3'      # From stack outputs
API_ENDPOINT = 'https://n122r4122g.execute-api.us-east-1.amazonaws.com/test'   # From stack outputs
USERNAME = '***REMOVED***'
PASSWORD = 'TestPass123!'

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

def test_create_protection_group(token):
    """Test POST /protection-groups"""
    print("\n🧪 Test 1: CREATE Protection Group (POST)")
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {
        'GroupName': f'test-pg-{int(time.time())}',
        'Description': 'Test protection group for CRUD operations',
        'Region': 'us-east-1',
        'AccountId': '123456789012',
        'Owner': '***REMOVED***',
        'sourceServerIds': ['s-1234567890abcdef0', 's-1234567890abcdef1']
    }
    
    response = requests.post(
        f'{API_ENDPOINT}/protection-groups',
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        pg = response.json()
        print(f"✅ CREATE successful: {pg['id']}")
        print(f"   Name: {pg['name']}")
        print(f"   Servers: {len(pg.get('sourceServerIds', []))}")
        return pg['id'], pg['name']
    else:
        print(f"❌ CREATE failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None, None

def test_get_protection_group(token, pg_id):
    """Test GET /protection-groups/{id}"""
    print(f"\n🧪 Test 2: GET Protection Group (GET /{pg_id})")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f'{API_ENDPOINT}/protection-groups/{pg_id}',
        headers=headers
    )
    
    if response.status_code == 200:
        pg = response.json()
        print(f"✅ GET successful")
        print(f"   Name: {pg['name']}")
        print(f"   Servers: {len(pg.get('sourceServerIds', []))}")
        return True
    else:
        print(f"❌ GET failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_update_protection_group(token, pg_id):
    """Test PUT /protection-groups/{id}"""
    print(f"\n🧪 Test 3: UPDATE Protection Group (PUT /{pg_id})")
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {
        'description': 'Updated description - testing PUT method',
        'sourceServerIds': ['s-1234567890abcdef0', 's-1234567890abcdef1', 's-1234567890abcdef2'],
        'tags': [
            {'key': 'Environment', 'value': 'Test'},
            {'key': 'Updated', 'value': 'True'}
        ]
    }
    
    response = requests.put(
        f'{API_ENDPOINT}/protection-groups/{pg_id}',
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        pg = response.json()
        print(f"✅ UPDATE successful")
        print(f"   Description: {pg['description']}")
        print(f"   Servers: {len(pg.get('sourceServerIds', []))} (added 1 server)")
        print(f"   Tags: {len(pg.get('tags', []))} (added 1 tag)")
        return True
    else:
        print(f"❌ UPDATE failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_delete_protection_group(token, pg_id):
    """Test DELETE /protection-groups/{id}"""
    print(f"\n🧪 Test 4: DELETE Protection Group (DELETE /{pg_id})")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.delete(
        f'{API_ENDPOINT}/protection-groups/{pg_id}',
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ DELETE successful")
        return True
    else:
        print(f"❌ DELETE failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_name_uniqueness(token, existing_name):
    """Test name uniqueness validation"""
    print(f"\n🧪 Test 5: Name Uniqueness Validation")
    print(f"   Attempting to create PG with existing name: {existing_name}")
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {
        'GroupName': existing_name,  # Use existing name - should fail
        'Description': 'This should fail due to duplicate name',
        'Region': 'us-east-1',
        'AccountId': '123456789012',
        'Owner': '***REMOVED***',
        'sourceServerIds': ['s-test123']
    }
    
    response = requests.post(
        f'{API_ENDPOINT}/protection-groups',
        headers=headers,
        json=data
    )
    
    if response.status_code == 400:
        error = response.json()
        if 'already exists' in error.get('error', '').lower():
            print(f"✅ Name uniqueness validation working")
            print(f"   Correctly rejected duplicate name")
            return True
        else:
            print(f"⚠️  Got 400 but unexpected error: {error.get('error')}")
            return False
    else:
        print(f"❌ Name uniqueness validation FAILED")
        print(f"   Should return 400, got: {response.status_code}")
        print(f"   Duplicate names allowed (BUG!)")
        return False

def main():
    """Run all CRUD tests"""
    print("=" * 60)
    print("Protection Groups CRUD E2E Test Suite")
    print("=" * 60)
    
    # Check config
    if 'UPDATE_ME' in [USER_POOL_ID, CLIENT_ID, API_ENDPOINT]:
        print("\n❌ ERROR: Update config variables at top of file")
        print("   Get values from: aws cloudformation describe-stacks")
        return False
    
    # Authenticate
    print("\n📝 Step 1: Authentication")
    token = get_auth_token()
    if not token:
        return False
    print("✅ Authenticated successfully")
    
    # Test CRUD operations
    results = []
    
    # CREATE
    pg_id, pg_name = test_create_protection_group(token)
    results.append(('CREATE', pg_id is not None))
    if not pg_id:
        print("\n❌ Cannot continue - CREATE failed")
        return False
    
    # GET
    results.append(('GET', test_get_protection_group(token, pg_id)))
    
    # UPDATE (PUT)
    results.append(('UPDATE', test_update_protection_group(token, pg_id)))
    
    # Name Uniqueness
    results.append(('UNIQUENESS', test_name_uniqueness(token, pg_name)))
    
    # DELETE
    results.append(('DELETE', test_delete_protection_group(token, pg_id)))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED")
        print("=" * 60)
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
