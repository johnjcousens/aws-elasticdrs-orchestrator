"""
E2E API Test: Recovery Plan CRUD Operations

Tests the complete lifecycle of Recovery Plans via direct API calls:
1. Create 3 Protection Groups (WebServers, AppServers, DatabaseServers)
2. Create Recovery Plan with 3 waves
3. Edit plan by removing one server from each wave
4. Delete Recovery Plan
"""

import boto3
import requests
import json
import pytest
from typing import Dict, List

# Test Configuration
API_ENDPOINT = "https://yta7zbmsz1.execute-api.us-east-1.amazonaws.com/test"
USER_POOL_ID = "us-east-1_uCT6Sr0iO"
USER_POOL_CLIENT_ID = "1inhoq5alvu9p24dmqkdkc8jbj"
REGION = "us-east-1"
USERNAME = "testuser@example.com"
PASSWORD = "IiG2b1o+D$"


class CognitoAuthenticator:
    """Handles Cognito authentication"""
    
    def __init__(self):
        self.client = boto3.client('cognito-idp', region_name=REGION)
        self.id_token = None
        self.access_token = None
        
    def authenticate(self, username: str, password: str, client_id: str) -> Dict[str, str]:
        """Authenticate user and get tokens"""
        # Initiate auth
        auth_response = self.client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        self.id_token = auth_response['AuthenticationResult']['IdToken']
        self.access_token = auth_response['AuthenticationResult']['AccessToken']
        
        return {
            'Authorization': self.id_token,
            'Content-Type': 'application/json'
        }


class RecoveryPlanAPITester:
    """Tests Recovery Plan CRUD operations via API"""
    
    def __init__(self, api_endpoint: str, headers: Dict[str, str]):
        self.api_endpoint = api_endpoint
        self.headers = headers
        self.created_pg_ids = []
        self.created_plan_id = None
        
    def create_protection_group(self, name: str, num_servers: int) -> str:
        """Create a Protection Group with mock servers"""
        # Generate mock server IDs
        server_ids = [f"i-{name.lower()}{i:03d}" for i in range(1, num_servers + 1)]
        
        payload = {
            "GroupName": name,
            "Region": REGION,
            "Description": f"Test Protection Group for {name}",
            "AccountId": "123456789012",  # Required by deployed API
            "sourceServerIds": server_ids
        }
        
        response = requests.post(
            f"{self.api_endpoint}/protection-groups",
            headers=self.headers,
            json=payload
        )
        
        assert response.status_code == 201, f"Failed to create PG {name}: {response.text}"
        
        pg_data = response.json()
        pg_id = pg_data.get('protectionGroupId') or pg_data.get('id') or pg_data.get('GroupId')
        assert pg_id, f"No ID in response: {pg_data}"
        self.created_pg_ids.append(pg_id)
        
        print(f"✅ Created Protection Group: {name} ({pg_id}) with {num_servers} servers")
        return pg_id
        
    def create_recovery_plan(self, plan_name: str, waves: List[Dict]) -> str:
        """Create a Recovery Plan with multiple waves
        
        Args:
            plan_name: Name of the recovery plan
            waves: List of wave configurations, each with:
                   - name: Wave name
                   - pg_id: Protection Group ID
                   - server_ids: List of server IDs to include
        """
        wave_configs = []
        
        for wave in waves:
            wave_config = {
                "waveNumber": wave.get('order', len(wave_configs) + 1),
                "name": wave['name'],
                "protectionGroupId": wave['pg_id'],
                "serverIds": wave['server_ids'],
                "launchOrder": wave.get('order', len(wave_configs) + 1)
            }
            wave_configs.append(wave_config)
        
        payload = {
            "PlanName": plan_name,
            "Description": f"Test recovery plan - {plan_name}",
            "AccountId": "123456789012",
            "Region": REGION,
            "Owner": USERNAME,
            "Waves": wave_configs
        }
        
        response = requests.post(
            f"{self.api_endpoint}/recovery-plans",
            headers=self.headers,
            json=payload
        )
        
        assert response.status_code == 201, f"Failed to create plan: {response.text}"
        
        plan_data = response.json()
        print(f"  DEBUG - API Response: {json.dumps(plan_data, indent=2)}")
        self.created_plan_id = plan_data.get('PlanId') or plan_data.get('id') or plan_data.get('planId')
        
        assert self.created_plan_id, f"No plan ID in response! Keys: {list(plan_data.keys())}"
        
        print(f"✅ Created Recovery Plan: {plan_name} ({self.created_plan_id}) with {len(waves)} waves")
        return self.created_plan_id
        
    def update_recovery_plan(self, plan_id: str, updated_waves: List[Dict]) -> Dict:
        """Update a Recovery Plan by modifying wave configurations"""
        payload = {
            "waves": updated_waves
        }
        
        response = requests.put(
            f"{self.api_endpoint}/recovery-plans/{plan_id}",
            headers=self.headers,
            json=payload
        )
        
        assert response.status_code == 200, f"Failed to update plan: {response.text}"
        
        print(f"✅ Updated Recovery Plan: {plan_id}")
        return response.json()
        
    def delete_recovery_plan(self, plan_id: str) -> None:
        """Delete a Recovery Plan"""
        response = requests.delete(
            f"{self.api_endpoint}/recovery-plans/{plan_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to delete plan: {response.text}"
        
        print(f"✅ Deleted Recovery Plan: {plan_id}")
        
    def cleanup_protection_groups(self) -> None:
        """Clean up created Protection Groups"""
        for pg_id in self.created_pg_ids:
            response = requests.delete(
                f"{self.api_endpoint}/protection-groups/{pg_id}",
                headers=self.headers
            )
            if response.status_code == 200:
                print(f"✅ Deleted Protection Group: {pg_id}")
            else:
                print(f"⚠️  Failed to delete Protection Group {pg_id}: {response.text}")


@pytest.fixture(scope="module")
def auth_headers():
    """Authenticate and get headers for API requests"""
    authenticator = CognitoAuthenticator()
    headers = authenticator.authenticate(USERNAME, PASSWORD, USER_POOL_CLIENT_ID)
    return headers


@pytest.fixture(scope="module")
def api_tester(auth_headers):
    """Create API tester instance"""
    tester = RecoveryPlanAPITester(API_ENDPOINT, auth_headers)
    yield tester
    # Cleanup after tests
    tester.cleanup_protection_groups()


def test_recovery_plan_full_lifecycle(api_tester):
    """
    Complete Recovery Plan Lifecycle Test:
    1. Create Recovery Plan with 3 waves
    2. Edit plan by removing one server from each wave
    3. Delete Recovery Plan
    """
    import time
    timestamp = int(time.time())
    
    # ========================================================================
    # PART 1: Create Recovery Plan with 3 Waves
    # ========================================================================
    print("\n" + "="*80)
    print("PART 1: Create Recovery Plan with 3 Waves")
    print("="*80)
    
    # Create Protection Groups
    web_pg_id = api_tester.create_protection_group(f"WebServers-{timestamp}", 2)
    app_pg_id = api_tester.create_protection_group(f"AppServers-{timestamp}", 2)
    db_pg_id = api_tester.create_protection_group(f"DatabaseServers-{timestamp}", 2)
    
    # Define waves with all servers from each PG
    waves = [
        {
            "name": "Web",
            "pg_id": web_pg_id,
            "server_ids": ["i-webservers001", "i-webservers002"],
            "order": 1
        },
        {
            "name": "App",
            "pg_id": app_pg_id,
            "server_ids": ["i-appservers001", "i-appservers002"],
            "order": 2
        },
        {
            "name": "Database",
            "pg_id": db_pg_id,
            "server_ids": ["i-databaseservers001", "i-databaseservers002"],
            "order": 3
        }
    ]
    
    # Create Recovery Plan
    plan_id = api_tester.create_recovery_plan(f"TEST-{timestamp}", waves)
    assert plan_id is not None, "Failed to create Recovery Plan"
    
    print(f"\n✅ PART 1 PASSED: Recovery Plan created")
    print(f"   Plan ID: {plan_id}")
    
    # ========================================================================
    # PART 2: Edit Plan - Remove One Server from Each Wave
    # ========================================================================
    print("\n" + "="*80)
    print("PART 2: Edit Plan - Remove One Server from Each Wave")
    print("="*80)
    
    # Updated waves with one server removed from each
    updated_waves = [
        {
            "waveName": "Web",
            "protectionGroupId": web_pg_id,
            "serverIds": ["i-webservers001"],  # Removed i-webservers002
            "launchOrder": 1
        },
        {
            "waveName": "App",
            "protectionGroupId": app_pg_id,
            "serverIds": ["i-appservers001"],  # Removed i-appservers002
            "launchOrder": 2
        },
        {
            "waveName": "Database",
            "protectionGroupId": db_pg_id,
            "serverIds": ["i-databaseservers001"],  # Removed i-databaseservers002
            "launchOrder": 3
        }
    ]
    
    # Update plan
    updated_plan = api_tester.update_recovery_plan(plan_id, updated_waves)
    
    print(f"\n✅ PART 2 PASSED: Recovery Plan updated")
    print(f"   Updated: Web (1 server), App (1 server), Database (1 server)")
    
    # ========================================================================
    # PART 3: Delete Recovery Plan
    # ========================================================================
    print("\n" + "="*80)
    print("PART 3: Delete Recovery Plan")
    print("="*80)
    
    # Delete plan
    api_tester.delete_recovery_plan(plan_id)
    
    print(f"\n✅ PART 3 PASSED: Recovery Plan deleted")
    print(f"   Deleted Plan ID: {plan_id}")
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED: Complete Recovery Plan Lifecycle")
    print("="*80)


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
