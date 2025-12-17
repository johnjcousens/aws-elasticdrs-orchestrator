#!/usr/bin/env python3
"""
Test Multi-Account Logic Directly
Tests the multi-account functions without going through API Gateway authentication
"""

import json
import sys
import os
import boto3
from moto import mock_dynamodb, mock_sts

# Set up mock environment BEFORE importing
os.environ['PROTECTION_GROUPS_TABLE'] = 'protection-groups-test'
os.environ['RECOVERY_PLANS_TABLE'] = 'recovery-plans-test'
os.environ['EXECUTION_HISTORY_TABLE'] = 'execution-history-test'
os.environ['ACCOUNTS_TABLE'] = 'accounts-test'
os.environ['STEP_FUNCTIONS_ARN'] = 'arn:aws:states:us-east-1:123456789012:stateMachine:test'

# Add lambda directory to path
sys.path.insert(0, 'lambda')

# Import the Lambda functions
from index import (
    determine_target_account_context,
    get_cross_account_session,
    list_protection_groups,
    list_recovery_plans,
    create_protection_group,
    create_recovery_plan
)

@mock_dynamodb
@mock_sts
def test_multi_account_logic():
    """Test multi-account logic with mocked AWS services"""
    
    # Create mock DynamoDB tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Create Protection Groups table
    pg_table = dynamodb.create_table(
        TableName='protection-groups-test',
        KeySchema=[{'AttributeName': 'GroupId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'GroupId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create Recovery Plans table
    rp_table = dynamodb.create_table(
        TableName='recovery-plans-test',
        KeySchema=[{'AttributeName': 'PlanId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'PlanId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create Accounts table
    accounts_table = dynamodb.create_table(
        TableName='accounts-test',
        KeySchema=[{'AttributeName': 'AccountId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'AccountId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Wait for tables to be created
    pg_table.wait_until_exists()
    rp_table.wait_until_exists()
    accounts_table.wait_until_exists()
    
    print("=== Testing Multi-Account Logic ===")
    
    # Test 1: Create a cross-account protection group
    print("\n1. Creating cross-account protection group...")
    pg_data = {
        'GroupId': 'pg-cross-account-test',
        'GroupName': 'Cross Account Test Group',
        'Region': 'us-east-1',
        'AccountId': '999888777666',  # Different account
        'Servers': ['i-1234567890abcdef0'],
        'CreatedBy': 'test-user',
        'CreatedAt': '2024-01-01T00:00:00Z'
    }
    
    try:
        result = create_protection_group(pg_data)
        print(f"✅ Created protection group: {result}")
    except Exception as e:
        print(f"❌ Failed to create protection group: {e}")
    
    # Test 2: Create a recovery plan that uses the cross-account protection group
    print("\n2. Creating recovery plan with cross-account protection group...")
    rp_data = {
        'PlanId': 'rp-cross-account-test',
        'PlanName': 'Cross Account Recovery Plan',
        'Waves': [
            {
                'WaveNumber': 1,
                'ProtectionGroupId': 'pg-cross-account-test',
                'PauseBeforeWave': False
            }
        ],
        'CreatedBy': 'test-user',
        'CreatedAt': '2024-01-01T00:00:00Z'
    }
    
    try:
        result = create_recovery_plan(rp_data)
        print(f"✅ Created recovery plan: {result}")
    except Exception as e:
        print(f"❌ Failed to create recovery plan: {e}")
    
    # Test 3: Test target account determination
    print("\n3. Testing target account determination...")
    try:
        context = determine_target_account_context(rp_data)
        print(f"✅ Target account context: {json.dumps(context, indent=2)}")
        
        if context['AccountId'] == '999888777666':
            print("✅ Correctly identified cross-account target")
        else:
            print("❌ Failed to identify cross-account target")
            
    except Exception as e:
        print(f"❌ Failed to determine target account: {e}")
    
    # Test 4: Test cross-account session creation (will fail without real credentials)
    print("\n4. Testing cross-account session creation...")
    try:
        # Register a mock account first
        accounts_table.put_item(Item={
            'AccountId': '999888777666',
            'AccountName': 'Test Cross Account',
            'CrossAccountRoleArn': 'arn:aws:iam::999888777666:role/DRSOrchestrationCrossAccountRole',
            'Regions': ['us-east-1', 'us-west-2'],
            'RegisteredAt': '2024-01-01T00:00:00Z'
        })
        
        session = get_cross_account_session('999888777666')
        print(f"✅ Cross-account session created: {type(session)}")
    except Exception as e:
        print(f"⚠️  Cross-account session failed (expected in test): {e}")
    
    # Test 5: List protection groups (should show cross-account group)
    print("\n5. Testing protection groups listing...")
    try:
        groups = list_protection_groups()
        print(f"✅ Found {len(groups)} protection groups:")
        for group in groups:
            account_id = group.get('AccountId', 'current')
            print(f"  - {group['GroupId']}: {group['GroupName']} (Account: {account_id})")
    except Exception as e:
        print(f"❌ Failed to list protection groups: {e}")
    
    # Test 6: List recovery plans
    print("\n6. Testing recovery plans listing...")
    try:
        plans = list_recovery_plans()
        print(f"✅ Found {len(plans)} recovery plans:")
        for plan in plans:
            print(f"  - {plan['PlanId']}: {plan['PlanName']}")
            for wave in plan.get('Waves', []):
                pg_id = wave.get('ProtectionGroupId', 'N/A')
                print(f"    Wave {wave.get('WaveNumber', '?')}: PG {pg_id}")
    except Exception as e:
        print(f"❌ Failed to list recovery plans: {e}")

def test_account_context_edge_cases():
    """Test edge cases in account context determination"""
    print("\n=== Testing Account Context Edge Cases ===")
    
    # Test with empty recovery plan
    print("\n1. Testing empty recovery plan...")
    empty_plan = {'Waves': []}
    try:
        context = determine_target_account_context(empty_plan)
        print(f"✅ Empty plan context: {json.dumps(context, indent=2)}")
    except Exception as e:
        print(f"❌ Failed with empty plan: {e}")
    
    # Test with multiple waves, same account
    print("\n2. Testing multiple waves, same account...")
    multi_wave_plan = {
        'Waves': [
            {'WaveNumber': 1, 'ProtectionGroupId': 'pg-account-a'},
            {'WaveNumber': 2, 'ProtectionGroupId': 'pg-account-a-2'}
        ]
    }
    try:
        context = determine_target_account_context(multi_wave_plan)
        print(f"✅ Multi-wave same account context: {json.dumps(context, indent=2)}")
    except Exception as e:
        print(f"❌ Failed with multi-wave plan: {e}")
    
    # Test with mixed accounts (should fail)
    print("\n3. Testing mixed accounts (should fail)...")
    mixed_plan = {
        'Waves': [
            {'WaveNumber': 1, 'ProtectionGroupId': 'pg-account-a'},
            {'WaveNumber': 2, 'ProtectionGroupId': 'pg-account-b'}
        ]
    }
    try:
        context = determine_target_account_context(mixed_plan)
        print(f"❌ Mixed accounts should have failed: {json.dumps(context, indent=2)}")
    except Exception as e:
        print(f"✅ Correctly failed with mixed accounts: {e}")

if __name__ == '__main__':
    print("============================================================")
    print("Multi-Account Logic Direct Tests")
    print("============================================================")
    
    test_multi_account_logic()
    test_account_context_edge_cases()
    
    print("\n============================================================")
    print("Multi-Account Logic Tests Complete")
    print("============================================================")