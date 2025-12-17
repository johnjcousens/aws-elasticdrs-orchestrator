#!/usr/bin/env python3
"""
Debug Multi-Account Implementation
Tests the actual Lambda function multi-account logic with various scenarios
"""

import json
import sys
import os

# Set up mock environment BEFORE importing
os.environ['PROTECTION_GROUPS_TABLE'] = 'protection-groups-test'
os.environ['RECOVERY_PLANS_TABLE'] = 'recovery-plans-test'
os.environ['EXECUTION_HISTORY_TABLE'] = 'execution-history-test'
os.environ['ACCOUNTS_TABLE'] = 'accounts-test'
os.environ['STEP_FUNCTIONS_ARN'] = 'arn:aws:states:us-east-1:123456789012:stateMachine:test'

# Add lambda directory to path
sys.path.insert(0, 'lambda')

# Import the Lambda function
from index import lambda_handler

def test_protection_groups_cross_account():
    """Test protection groups endpoint with cross-account scenario"""
    print("=== Testing Protection Groups Cross-Account ===")
    
    event = {
        'httpMethod': 'GET',
        'path': '/protection-groups',
        'headers': {
            'Authorization': 'Bearer fake-token-for-testing'
        },
        'queryStringParameters': None,
        'body': None,
        'requestContext': {
            'accountId': '123456789012'
        }
    }
    
    try:
        response = lambda_handler(event, {})
        print(f"Status: {response['statusCode']}")
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            print(f"Found {len(body)} protection groups")
            for pg in body[:2]:  # Show first 2
                print(f"  - {pg.get('GroupId', 'N/A')}: {pg.get('GroupName', 'N/A')} (Account: {pg.get('AccountId', 'N/A')})")
        else:
            print(f"Error: {response['body']}")
    except Exception as e:
        print(f"Exception: {e}")

def test_recovery_plans_cross_account():
    """Test recovery plans endpoint with cross-account scenario"""
    print("\n=== Testing Recovery Plans Cross-Account ===")
    
    event = {
        'httpMethod': 'GET',
        'path': '/recovery-plans',
        'headers': {
            'Authorization': 'Bearer fake-token-for-testing'
        },
        'queryStringParameters': None,
        'body': None,
        'requestContext': {
            'accountId': '123456789012'
        }
    }
    
    try:
        response = lambda_handler(event, {})
        print(f"Status: {response['statusCode']}")
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            print(f"Found {len(body)} recovery plans")
            for rp in body[:2]:  # Show first 2
                print(f"  - {rp.get('PlanId', 'N/A')}: {rp.get('PlanName', 'N/A')}")
                waves = rp.get('Waves', [])
                print(f"    Waves: {len(waves)}")
                for i, wave in enumerate(waves[:2]):
                    pg_id = wave.get('ProtectionGroupId', 'N/A')
                    print(f"      Wave {i+1}: PG {pg_id}")
        else:
            print(f"Error: {response['body']}")
    except Exception as e:
        print(f"Exception: {e}")

def test_execution_start_cross_account():
    """Test starting execution with cross-account scenario"""
    print("\n=== Testing Execution Start Cross-Account ===")
    
    # Create a test recovery plan
    test_plan = {
        "PlanId": "rp-test-cross-account",
        "PlanName": "Test Cross Account Plan",
        "Waves": [
            {
                "WaveNumber": 1,
                "ProtectionGroupId": "pg-test-123",
                "PauseBeforeWave": False
            }
        ]
    }
    
    event = {
        'httpMethod': 'POST',
        'path': '/executions',
        'headers': {
            'Authorization': 'Bearer fake-token-for-testing',
            'Content-Type': 'application/json'
        },
        'queryStringParameters': None,
        'body': json.dumps({
            'RecoveryPlan': test_plan,
            'ExecutionType': 'DRILL',
            'InvocationSource': 'DEBUG_TEST'
        }),
        'requestContext': {
            'accountId': '123456789012'
        }
    }
    
    try:
        response = lambda_handler(event, {})
        print(f"Status: {response['statusCode']}")
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            print(f"Execution started: {body.get('ExecutionId', 'N/A')}")
            print(f"Target Account: {body.get('TargetAccount', 'N/A')}")
            print(f"Status: {body.get('Status', 'N/A')}")
        else:
            print(f"Error: {response['body']}")
    except Exception as e:
        print(f"Exception: {e}")

def test_account_registration():
    """Test account registration endpoint"""
    print("\n=== Testing Account Registration ===")
    
    event = {
        'httpMethod': 'POST',
        'path': '/accounts',
        'headers': {
            'Authorization': 'Bearer fake-token-for-testing',
            'Content-Type': 'application/json'
        },
        'queryStringParameters': None,
        'body': json.dumps({
            'AccountId': '999888777666',
            'AccountName': 'Test Cross Account',
            'CrossAccountRoleArn': 'arn:aws:iam::999888777666:role/DRSOrchestrationCrossAccountRole',
            'Regions': ['us-east-1', 'us-west-2']
        }),
        'requestContext': {
            'accountId': '123456789012'
        }
    }
    
    try:
        response = lambda_handler(event, {})
        print(f"Status: {response['statusCode']}")
        print(f"Response: {response['body']}")
    except Exception as e:
        print(f"Exception: {e}")

def test_accounts_list():
    """Test listing registered accounts"""
    print("\n=== Testing Accounts List ===")
    
    event = {
        'httpMethod': 'GET',
        'path': '/accounts',
        'headers': {
            'Authorization': 'Bearer fake-token-for-testing'
        },
        'queryStringParameters': None,
        'body': None,
        'requestContext': {
            'accountId': '123456789012'
        }
    }
    
    try:
        response = lambda_handler(event, {})
        print(f"Status: {response['statusCode']}")
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            print(f"Found {len(body)} registered accounts")
            for account in body:
                print(f"  - {account.get('AccountId', 'N/A')}: {account.get('AccountName', 'N/A')}")
                print(f"    Role: {account.get('CrossAccountRoleArn', 'N/A')}")
                print(f"    Regions: {account.get('Regions', [])}")
        else:
            print(f"Error: {response['body']}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == '__main__':
    print("============================================================")
    print("Multi-Account Implementation Debug Tests")
    print("============================================================")
    
    # Environment already set up above
    
    # Run tests
    test_accounts_list()
    test_account_registration()
    test_protection_groups_cross_account()
    test_recovery_plans_cross_account()
    test_execution_start_cross_account()
    
    print("\n============================================================")
    print("Debug Tests Complete")
    print("============================================================")