#!/usr/bin/env python3
"""
End-to-End Recovery Plan Testing
Tests complete CRUD operations: Create, Read, Update, Delete
"""
import boto3
import requests
import json
import sys
import time

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

def test_1_create_recovery_plan(token):
    """
    Test 1: Create Recovery Plan with 3 waves
    - Wave 1: Web (WebServers, 2 servers)
    - Wave 2: App (AppServers, 2 servers)  
    - Wave 3: Database (DatabaseServers, 2 servers)
    """
    print("\n" + "=" * 60)
    print("TEST 1: CREATE RECOVERY PLAN")
    print("=" * 60)
    
    # Get Protection Groups first
    print("\n📋 Step 1: Fetching Protection Groups...")
    headers = {'Authorization': f'Bearer {token}'}
    pg_response = requests.get(f'{API_ENDPOINT}/protection-groups', headers=headers)
    
    if pg_response.status_code != 200:
        print(f"❌ Failed to get Protection Groups: {pg_response.status_code}")
        return None, False
    
    pgs = pg_response.json().get('groups', [])
    
    # Find our three PGs
    web_pg = next((pg for pg in pgs if pg['name'] == 'WebServers'), None)
    app_pg = next((pg for pg in pgs if pg['name'] == 'AppServers'), None)
    db_pg = next((pg for pg in pgs if pg['name'] == 'DatabaseServers'), None)
    
    if not all([web_pg, app_pg, db_pg]):
        print("❌ Missing required Protection Groups")
        print(f"   Found: {[pg['name'] for pg in pgs]}")
        return None, False
    
    print(f"✅ Found WebServers: {len(web_pg['sourceServerIds'])} servers")
    print(f"✅ Found AppServers: {len(app_pg['sourceServerIds'])} servers")
    print(f"✅ Found DatabaseServers: {len(db_pg['sourceServerIds'])} servers")
    
    # Create Recovery Plan
    print("\n📝 Step 2: Creating Recovery Plan...")
    create_payload = {
        "PlanName": "TEST",
        "Description": "Automated E2E test plan",
        "AccountId": "438465159935",
        "Region": "us-east-1",
        "Owner": "apitest",
        "RPO": "1h",
        "RTO": "30m",
        "Waves": [
            {
                "WaveId": "wave-0",
                "WaveName": "Web",
                "WaveDescription": "Web servers wave",
                "ExecutionOrder": 0,
                "ProtectionGroupId": web_pg['protectionGroupId'],
                "ServerIds": web_pg['sourceServerIds'],  # All 2 servers
                "ExecutionType": "sequential",
                "Dependencies": []
            },
            {
                "WaveId": "wave-1",
                "WaveName": "App",
                "WaveDescription": "Application servers wave",
                "ExecutionOrder": 1,
                "ProtectionGroupId": app_pg['protectionGroupId'],
                "ServerIds": app_pg['sourceServerIds'],  # All 2 servers
                "ExecutionType": "sequential",
                "Dependencies": [{"DependsOnWaveId": "wave-0"}]
            },
            {
                "WaveId": "wave-2",
                "WaveName": "Database",
                "WaveDescription": "Database servers wave",
                "ExecutionOrder": 2,
                "ProtectionGroupId": db_pg['protectionGroupId'],
                "ServerIds": db_pg['sourceServerIds'],  # All 2 servers
                "ExecutionType": "sequential",
                "Dependencies": [{"DependsOnWaveId": "wave-1"}]
            }
        ]
    }
    
    create_response = requests.post(
        f'{API_ENDPOINT}/recovery-plans',
        headers=headers,
        json=create_payload
    )
    
    if create_response.status_code not in [200, 201]:
        print(f"❌ Failed to create plan: {create_response.status_code}")
        print(f"   Response: {create_response.text}")
        return None, False
    
    plan = create_response.json()
    plan_id = plan.get('id') or plan.get('PlanId')
    
    print(f"✅ Created Recovery Plan: {plan_id}")
    print(f"   Name: TEST")
    print(f"   Waves: 3")
    print(f"   - Wave 0 (Web): {len(web_pg['sourceServerIds'])} servers")
    print(f"   - Wave 1 (App): {len(app_pg['sourceServerIds'])} servers")
    print(f"   - Wave 2 (Database): {len(db_pg['sourceServerIds'])} servers")
    
    # Store PGs for next test
    return {
        'plan_id': plan_id,
        'web_pg': web_pg,
        'app_pg': app_pg,
        'db_pg': db_pg
    }, True

def test_2_update_recovery_plan(token, test_data):
    """
    Test 2: Update Recovery Plan
    Remove one server from each wave
    """
    print("\n" + "=" * 60)
    print("TEST 2: UPDATE RECOVERY PLAN")
    print("=" * 60)
    
    plan_id = test_data['plan_id']
    web_pg = test_data['web_pg']
    app_pg = test_data['app_pg']
    db_pg = test_data['db_pg']
    
    print(f"\n📝 Updating plan {plan_id}...")
    print("   Removing 1 server from each wave")
    
    # Update with one server removed from each wave
    update_payload = {
        "PlanName": "TEST",
        "Description": "Updated - one server removed per wave",
        "Waves": [
            {
                "WaveId": "wave-0",
                "WaveName": "Web",
                "WaveDescription": "Web servers wave (1 server)",
                "ExecutionOrder": 0,
                "ProtectionGroupId": web_pg['protectionGroupId'],
                "ServerIds": [web_pg['sourceServerIds'][0]],  # Only first server
                "ExecutionType": "sequential",
                "Dependencies": []
            },
            {
                "WaveId": "wave-1",
                "WaveName": "App",
                "WaveDescription": "Application servers wave (1 server)",
                "ExecutionOrder": 1,
                "ProtectionGroupId": app_pg['protectionGroupId'],
                "ServerIds": [app_pg['sourceServerIds'][0]],  # Only first server
                "ExecutionType": "sequential",
                "Dependencies": [{"DependsOnWaveId": "wave-0"}]
            },
            {
                "WaveId": "wave-2",
                "WaveName": "Database",
                "WaveDescription": "Database servers wave (1 server)",
                "ExecutionOrder": 2,
                "ProtectionGroupId": db_pg['protectionGroupId'],
                "ServerIds": [db_pg['sourceServerIds'][0]],  # Only first server
                "ExecutionType": "sequential",
                "Dependencies": [{"DependsOnWaveId": "wave-1"}]
            }
        ]
    }
    
    headers = {'Authorization': f'Bearer {token}'}
    update_response = requests.put(
        f'{API_ENDPOINT}/recovery-plans/{plan_id}',
        headers=headers,
        json=update_payload
    )
    
    if update_response.status_code != 200:
        print(f"❌ Failed to update plan: {update_response.status_code}")
        print(f"   Response: {update_response.text}")
        return False
    
    print(f"✅ Updated Recovery Plan successfully")
    print(f"   - Wave 0 (Web): 1 server (removed 1)")
    print(f"   - Wave 1 (App): 1 server (removed 1)")
    print(f"   - Wave 2 (Database): 1 server (removed 1)")
    
    return True

def test_3_delete_recovery_plan(token, test_data):
    """
    Test 3: Delete Recovery Plan
    """
    print("\n" + "=" * 60)
    print("TEST 3: DELETE RECOVERY PLAN")
    print("=" * 60)
    
    plan_id = test_data['plan_id']
    
    print(f"\n🗑️  Deleting plan {plan_id}...")
    
    headers = {'Authorization': f'Bearer {token}'}
    delete_response = requests.delete(
        f'{API_ENDPOINT}/recovery-plans/{plan_id}',
        headers=headers
    )
    
    if delete_response.status_code not in [200, 204]:
        print(f"❌ Failed to delete plan: {delete_response.status_code}")
        print(f"   Response: {delete_response.text}")
        return False
    
    print(f"✅ Deleted Recovery Plan successfully")
    
    # Verify deletion
    print("\n🔍 Verifying deletion...")
    get_response = requests.get(
        f'{API_ENDPOINT}/recovery-plans/{plan_id}',
        headers=headers
    )
    
    if get_response.status_code == 404:
        print("✅ Plan confirmed deleted (404 Not Found)")
        return True
    else:
        print(f"⚠️  Plan still exists: {get_response.status_code}")
        return False

def main():
    print("=" * 60)
    print("RECOVERY PLAN E2E TEST SUITE")
    print("=" * 60)
    
    # Authenticate
    print("\n🔐 Authenticating...")
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        sys.exit(1)
    print("✅ Authenticated successfully")
    
    # Test 1: Create
    test_data, success = test_1_create_recovery_plan(token)
    if not success:
        print("\n❌ TEST 1 FAILED - Aborting remaining tests")
        sys.exit(1)
    
    # Wait and get fresh token for update
    time.sleep(1)
    print("\n🔐 Getting fresh token for Test 2...")
    token = get_auth_token()
    if not token:
        print("❌ Token refresh failed")
        sys.exit(1)
    
    # Test 2: Update
    success = test_2_update_recovery_plan(token, test_data)
    if not success:
        print("\n❌ TEST 2 FAILED")
        # Try to cleanup
        print("\n🧹 Attempting cleanup...")
        test_3_delete_recovery_plan(token, test_data)
        sys.exit(1)
    
    # Wait and get fresh token for delete
    time.sleep(1)
    print("\n🔐 Getting fresh token for Test 3...")
    token = get_auth_token()
    if not token:
        print("❌ Token refresh failed")
        sys.exit(1)
    
    # Test 3: Delete
    success = test_3_delete_recovery_plan(token, test_data)
    if not success:
        print("\n❌ TEST 3 FAILED")
        sys.exit(1)
    
    # Final Summary
    print("\n" + "=" * 60)
    print("✅ ALL E2E TESTS PASSED!")
    print("=" * 60)
    print("\nTest Results:")
    print("  ✅ Test 1: Create Recovery Plan with 3 waves")
    print("  ✅ Test 2: Update Recovery Plan (remove servers)")
    print("  ✅ Test 3: Delete Recovery Plan")
    print("\n" + "=" * 60)
    
    sys.exit(0)

if __name__ == '__main__':
    main()
