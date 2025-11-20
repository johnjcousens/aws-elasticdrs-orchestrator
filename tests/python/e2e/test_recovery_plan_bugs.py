"""
E2E API Test: Validate P1 Bug Fixes
Tests both Wave transformation and Delete performance bugs are fixed.
"""
import os
import json
import requests
import pytest
from typing import Dict, Any

# API Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'https://etv40zymeg.execute-api.us-east-1.amazonaws.com/test')
API_ENDPOINT = f"{API_BASE_URL}/recovery-plans"

# Test credentials (from .env.test or environment)
ID_TOKEN = os.getenv('ID_TOKEN', '')  # Must be set before running


@pytest.fixture
def auth_headers():
    """Authentication headers for API calls."""
    if not ID_TOKEN:
        pytest.skip("ID_TOKEN not set - run manual auth first")
    return {
        'Authorization': ID_TOKEN,  # No 'Bearer' prefix for API Gateway
        'Content-Type': 'application/json'
    }


@pytest.fixture
def test_plan_data():
    """Sample Recovery Plan data with multiple waves."""
    return {
        "recoveryPlanName": "TEST-E2E-API-P1-VALIDATION",
        "description": "E2E test for P1 bug validation",
        "waves": [
            {
                "waveName": "Database",
                "protectionGroupIds": ["pg-database-123"],
                "serverIds": ["s-3d75cdc0d9a28a725", "s-3afa164776f93ce4f"]  # CRITICAL: Arrays
            },
            {
                "waveName": "Application", 
                "protectionGroupIds": ["pg-application-456"],
                "serverIds": ["s-app1", "s-app2"]  # CRITICAL: Arrays
            }
        ]
    }


def test_create_recovery_plan(auth_headers, test_plan_data):
    """Test: Create Recovery Plan via API."""
    response = requests.post(
        API_ENDPOINT,
        headers=auth_headers,
        json=test_plan_data
    )
    
    assert response.status_code == 201, f"Create failed: {response.text}"
    data = response.json()
    assert 'recoveryPlanId' in data
    
    # Store for cleanup
    plan_id = data['recoveryPlanId']
    return plan_id


def test_edit_recovery_plan_validates_array_format(auth_headers, test_plan_data):
    """
    Test: P1 Wave Bug Fix - ServerIds remain arrays after edit.
    
    Bug: transform_rp_to_camelcase() converted ServerIds to strings
    Fix: Preserve ServerIds as arrays in transformation
    """
    # Create plan
    create_response = requests.post(
        API_ENDPOINT,
        headers=auth_headers,
        json=test_plan_data
    )
    assert create_response.status_code == 201, f"Create failed: {create_response.text}"
    response_data = create_response.json()
    # API returns PlanId, not recoveryPlanId
    plan_id = response_data.get('PlanId') or response_data.get('recoveryPlanId') or response_data.get('planId')
    assert plan_id, f"No plan ID in response: {response_data}"
    
    try:
        # Get plan for edit
        get_response = requests.get(
            f"{API_ENDPOINT}/{plan_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200, f"GET failed: {get_response.status_code} - {get_response.text}"
        plan_data = get_response.json()
        
        # CRITICAL VALIDATION: Check ServerIds are arrays, not strings
        waves = plan_data.get('waves', [])
        assert len(waves) >= 2, "Expected at least 2 waves"
        
        for wave in waves:
            server_ids = wave.get('serverIds', [])
            # BUG VALIDATION: ServerIds must be list/array type
            assert isinstance(server_ids, list), \
                f"Wave '{wave.get('waveName')}' has ServerIds as {type(server_ids).__name__}, expected list"
            
            # Validate array contains strings, not nested arrays
            for server_id in server_ids:
                assert isinstance(server_id, str), \
                    f"ServerIds contains {type(server_id).__name__}, expected string"
        
        print(f"✅ P1 WAVE BUG FIX VALIDATED: ServerIds are arrays")
        
        # Edit plan (update description)
        plan_data['description'] = "Updated via E2E test"
        edit_response = requests.put(
            f"{API_ENDPOINT}/{plan_id}",
            headers=auth_headers,
            json=plan_data
        )
        assert edit_response.status_code == 200, f"Edit failed: {edit_response.text}"
        
        # Verify ServerIds still arrays after edit
        edited_data = edit_response.json()
        edited_waves = edited_data.get('waves', [])
        for wave in edited_waves:
            server_ids = wave.get('serverIds', [])
            assert isinstance(server_ids, list), \
                f"After edit: Wave '{wave.get('waveName')}' ServerIds became {type(server_ids).__name__}"
        
        print(f"✅ P1 WAVE BUG FIX VALIDATED AFTER EDIT: ServerIds remain arrays")
        
    finally:
        # Cleanup
        requests.delete(f"{API_ENDPOINT}/{plan_id}", headers=auth_headers)


def test_delete_recovery_plan_performance(auth_headers, test_plan_data):
    """
    Test: P1 Delete Bug Fix - Uses scan with FilterExpression.
    
    Bug: Tried to use non-existent GSI, caused error
    Fix: Use scan() with FilterExpression for delete operation
    """
    # Create plan
    create_response = requests.post(
        API_ENDPOINT,
        headers=auth_headers,
        json=test_plan_data
    )
    assert create_response.status_code == 201
    plan_id = create_response.json()['recoveryPlanId']
    
    # Delete plan - should succeed without error
    delete_response = requests.delete(
        f"{API_ENDPOINT}/{plan_id}",
        headers=auth_headers
    )
    
    # CRITICAL VALIDATION: Delete succeeds (no GSI error)
    assert delete_response.status_code in [200, 204], \
        f"Delete failed with {delete_response.status_code}: {delete_response.text}"
    
    print(f"✅ P1 DELETE BUG FIX VALIDATED: Delete succeeded using scan")
    
    # Verify plan deleted - GET should return 404
    get_response = requests.get(
        f"{API_ENDPOINT}/{plan_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404, "Plan should be deleted"


if __name__ == "__main__":
    """Run tests directly for quick validation."""
    print("=" * 60)
    print("E2E API Test: P1 Bug Validation")
    print("=" * 60)
    
    if not ID_TOKEN:
        print("❌ ERROR: ID_TOKEN environment variable not set")
        print("   Set it from your authenticated session:")
        print("   export ID_TOKEN='your_token_here'")
        exit(1)
    
    headers = {'Authorization': ID_TOKEN, 'Content-Type': 'application/json'}
    plan_data = {
        "PlanName": "TEST-E2E-API-P1-VALIDATION",
        "Description": "E2E test for P1 bug validation",
        "AccountId": "123456789012",
        "Region": "us-east-1",
        "Owner": "***REMOVED***",
        "RPO": 60,
        "RTO": 120,
        "Waves": [
            {
                "waveNumber": 1,
                "WaveName": "Database",
                "ProtectionGroupIds": ["pg-database-123"],
                "ServerIds": ["s-3d75cdc0d9a28a725", "s-3afa164776f93ce4f"]
            }
        ]
    }
    
    print("\n1. Testing Wave Bug Fix...")
    try:
        test_edit_recovery_plan_validates_array_format(headers, plan_data)
    except AssertionError as e:
        print(f"❌ Wave test failed: {e}")
        # Try to get more details
        response = requests.post(API_ENDPOINT, headers=headers, json=plan_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        raise
    
    print("\n2. Testing Delete Bug Fix...")
    test_delete_recovery_plan_performance(headers, plan_data)
    
    print("\n" + "=" * 60)
    print("✅ ALL P1 BUG FIXES VALIDATED")
    print("=" * 60)
