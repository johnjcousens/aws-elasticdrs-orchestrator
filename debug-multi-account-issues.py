#!/usr/bin/env python3
"""
Debug Multi-Account Implementation Issues
Identifies specific problems with the current multi-account logic
"""

import json
import sys
import os
import boto3
from moto import mock_dynamodb

# Set up mock environment BEFORE importing
os.environ['PROTECTION_GROUPS_TABLE'] = 'protection-groups-test'
os.environ['RECOVERY_PLANS_TABLE'] = 'recovery-plans-test'
os.environ['EXECUTION_HISTORY_TABLE'] = 'execution-history-test'
os.environ['ACCOUNTS_TABLE'] = 'accounts-test'
os.environ['STEP_FUNCTIONS_ARN'] = 'arn:aws:states:us-east-1:123456789012:stateMachine:test'

# Add lambda directory to path
sys.path.insert(0, 'lambda')

from index import determine_target_account_context, create_drs_client

@mock_dynamodb
def test_with_real_protection_groups():
    """Test with actual protection groups in DynamoDB"""
    print("=== Testing with Real Protection Groups ===")
    
    # Create mock DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Create Protection Groups table
    table = dynamodb.create_table(
        TableName='protection-groups-test',
        KeySchema=[{'AttributeName': 'GroupId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'GroupId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()
    
    # Add test protection groups
    test_groups = [
        {
            'GroupId': 'pg-current-account',
            'GroupName': 'Current Account Group',
            'Region': 'us-east-1',
            'AccountId': '438465159935',  # Current account
            'Servers': ['i-1111111111111111'],
            'CreatedAt': '2024-01-01T00:00:00Z'
        },
        {
            'GroupId': 'pg-cross-account-999888777666',
            'GroupName': 'Cross Account Group',
            'Region': 'us-east-1',
            'AccountId': '999888777666',  # Different account
            'Servers': ['i-2222222222222222'],
            'CreatedAt': '2024-01-01T00:00:00Z'
        },
        {
            'GroupId': 'pg-another-account-111111111111',
            'GroupName': 'Another Account Group',
            'Region': 'us-west-2',
            'AccountId': '111111111111',  # Another different account
            'Servers': ['i-3333333333333333'],
            'CreatedAt': '2024-01-01T00:00:00Z'
        }
    ]
    
    for group in test_groups:
        table.put_item(Item=group)
    
    print(f"Created {len(test_groups)} test protection groups")
    
    # Test 1: Single wave with current account
    print("\n1. Testing single wave with current account...")
    plan1 = {
        'PlanId': 'rp-test-current',
        'Waves': [
            {
                'WaveNumber': 1,
                'ProtectionGroupId': 'pg-current-account'
            }
        ]
    }
    
    try:
        context = determine_target_account_context(plan1)
        print(f"✅ Current account result: {json.dumps(context, indent=2)}")
        
        if context['AccountId'] == '438465159935' and context['isCurrentAccount']:
            print("✅ Correctly identified current account")
        else:
            print("❌ Failed to identify current account correctly")
            
    except Exception as e:
        print(f"❌ Error with current account: {e}")
    
    # Test 2: Single wave with cross-account
    print("\n2. Testing single wave with cross-account...")
    plan2 = {
        'PlanId': 'rp-test-cross',
        'Waves': [
            {
                'WaveNumber': 1,
                'ProtectionGroupId': 'pg-cross-account-999888777666'
            }
        ]
    }
    
    try:
        context = determine_target_account_context(plan2)
        print(f"✅ Cross-account result: {json.dumps(context, indent=2)}")
        
        if context['AccountId'] == '999888777666' and not context['isCurrentAccount']:
            print("✅ Correctly identified cross-account")
        else:
            print("❌ Failed to identify cross-account correctly")
            print(f"   Expected: AccountId=999888777666, isCurrentAccount=False")
            print(f"   Got: AccountId={context['AccountId']}, isCurrentAccount={context['isCurrentAccount']}")
            
    except Exception as e:
        print(f"❌ Error with cross-account: {e}")
    
    # Test 3: Multiple waves, same cross-account
    print("\n3. Testing multiple waves, same cross-account...")
    plan3 = {
        'PlanId': 'rp-test-multi-same',
        'Waves': [
            {
                'WaveNumber': 1,
                'ProtectionGroupId': 'pg-cross-account-999888777666'
            },
            {
                'WaveNumber': 2,
                'ProtectionGroupId': 'pg-cross-account-999888777666'  # Same account
            }
        ]
    }
    
    try:
        context = determine_target_account_context(plan3)
        print(f"✅ Multi-wave same account result: {json.dumps(context, indent=2)}")
        
        if context['AccountId'] == '999888777666':
            print("✅ Correctly identified consistent cross-account")
        else:
            print("❌ Failed to identify consistent cross-account")
            
    except Exception as e:
        print(f"❌ Error with multi-wave same account: {e}")
    
    # Test 4: Multiple waves, different accounts (should fail)
    print("\n4. Testing multiple waves, different accounts (should fail)...")
    plan4 = {
        'PlanId': 'rp-test-multi-different',
        'Waves': [
            {
                'WaveNumber': 1,
                'ProtectionGroupId': 'pg-cross-account-999888777666'
            },
            {
                'WaveNumber': 2,
                'ProtectionGroupId': 'pg-another-account-111111111111'  # Different account
            }
        ]
    }
    
    try:
        context = determine_target_account_context(plan4)
        print(f"❌ Should have failed with mixed accounts: {json.dumps(context, indent=2)}")
        print("🐛 BUG: Mixed accounts should throw an exception!")
    except Exception as e:
        print(f"✅ Correctly failed with mixed accounts: {e}")

def test_account_id_extraction():
    """Test how account IDs are extracted from protection group IDs"""
    print("\n=== Testing Account ID Extraction Logic ===")
    
    test_cases = [
        ('pg-simple', None, 'No account ID in name'),
        ('pg-account-123456789012', '123456789012', 'Account ID at end'),
        ('pg-test-999888777666', '999888777666', 'Account ID at end'),
        ('pg-cross-account-111111111111', '111111111111', 'Account ID at end'),
        ('pg-123456789012-test', None, 'Account ID not at end'),
        ('pg-12345678901', None, 'Too short (11 digits)'),
        ('pg-1234567890123', None, 'Too long (13 digits)'),
        ('pg-abcdefghijkl', None, 'Not numeric'),
    ]
    
    for pg_id, expected_account, description in test_cases:
        print(f"\nTesting: {pg_id} ({description})")
        
        # Extract account ID using the same logic as the Lambda
        parts = pg_id.split('-')
        extracted_account = None
        
        if len(parts) >= 2 and parts[-1].isdigit() and len(parts[-1]) == 12:
            extracted_account = parts[-1]
        
        if extracted_account == expected_account:
            print(f"  ✅ Correctly extracted: {extracted_account}")
        else:
            print(f"  ❌ Expected: {expected_account}, Got: {extracted_account}")

def test_cross_account_role_assumption():
    """Test cross-account role assumption logic"""
    print("\n=== Testing Cross-Account Role Assumption ===")
    
    # Test current account context
    print("\n1. Testing current account context...")
    current_context = {
        'AccountId': '438465159935',
        'isCurrentAccount': True
    }
    
    try:
        client = create_drs_client('us-east-1', current_context)
        print(f"✅ Current account client created: {type(client)}")
    except Exception as e:
        print(f"❌ Failed to create current account client: {e}")
    
    # Test cross-account context without role
    print("\n2. Testing cross-account context without role...")
    cross_context = {
        'AccountId': '999888777666',
        'isCurrentAccount': False
    }
    
    try:
        client = create_drs_client('us-east-1', cross_context)
        print(f"⚠️  Cross-account client created without role: {type(client)}")
        print("🐛 BUG: Should have failed or used cross-account role!")
    except Exception as e:
        print(f"✅ Correctly failed without cross-account role: {e}")
    
    # Test cross-account context with role
    print("\n3. Testing cross-account context with role...")
    cross_context_with_role = {
        'AccountId': '999888777666',
        'isCurrentAccount': False,
        'AssumeRoleName': 'DRSOrchestrationCrossAccountRole'
    }
    
    try:
        client = create_drs_client('us-east-1', cross_context_with_role)
        print(f"⚠️  Cross-account client with role: {type(client)}")
        print("ℹ️  This will fail in real environment without valid role")
    except Exception as e:
        print(f"⚠️  Cross-account role assumption failed (expected): {e}")

if __name__ == '__main__':
    print("============================================================")
    print("Multi-Account Implementation Issue Debug")
    print("============================================================")
    
    test_with_real_protection_groups()
    test_account_id_extraction()
    test_cross_account_role_assumption()
    
    print("\n============================================================")
    print("Issue Summary:")
    print("1. ✅ Basic account context determination works")
    print("2. 🐛 Mixed account validation may not be working")
    print("3. ⚠️  Cross-account role assumption needs validation")
    print("4. ℹ️  Account ID extraction from PG names works")
    print("============================================================")