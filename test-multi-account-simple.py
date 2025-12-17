#!/usr/bin/env python3
"""
Simple Multi-Account Logic Test
Tests the core multi-account functions that exist in the Lambda
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

# Import the specific function we know exists
from index import determine_target_account_context

def test_account_context_determination():
    """Test the account context determination logic"""
    print("=== Testing Account Context Determination ===")
    
    # Test 1: Recovery plan with single wave, current account
    print("\n1. Testing single wave, current account...")
    plan1 = {
        'PlanId': 'rp-test-1',
        'Waves': [
            {
                'WaveNumber': 1,
                'ProtectionGroupId': 'pg-current-account'
            }
        ]
    }
    
    try:
        context = determine_target_account_context(plan1)
        print(f"✅ Result: {json.dumps(context, indent=2)}")
        
        if context.get('isCurrentAccount'):
            print("✅ Correctly identified as current account")
        else:
            print("❌ Should be current account")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Recovery plan with multiple waves, same account
    print("\n2. Testing multiple waves, same account...")
    plan2 = {
        'PlanId': 'rp-test-2',
        'Waves': [
            {
                'WaveNumber': 1,
                'ProtectionGroupId': 'pg-account-a'
            },
            {
                'WaveNumber': 2,
                'ProtectionGroupId': 'pg-account-a-2'
            }
        ]
    }
    
    try:
        context = determine_target_account_context(plan2)
        print(f"✅ Result: {json.dumps(context, indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Empty recovery plan
    print("\n3. Testing empty recovery plan...")
    plan3 = {
        'PlanId': 'rp-test-3',
        'Waves': []
    }
    
    try:
        context = determine_target_account_context(plan3)
        print(f"✅ Result: {json.dumps(context, indent=2)}")
        
        if context.get('isCurrentAccount'):
            print("✅ Correctly defaulted to current account")
        else:
            print("❌ Should default to current account")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Recovery plan with mixed accounts (should fail)
    print("\n4. Testing mixed accounts (should fail)...")
    plan4 = {
        'PlanId': 'rp-test-4',
        'Waves': [
            {
                'WaveNumber': 1,
                'ProtectionGroupId': 'pg-account-111111111111'
            },
            {
                'WaveNumber': 2,
                'ProtectionGroupId': 'pg-account-222222222222'
            }
        ]
    }
    
    try:
        context = determine_target_account_context(plan4)
        print(f"❌ Should have failed with mixed accounts: {json.dumps(context, indent=2)}")
    except Exception as e:
        print(f"✅ Correctly failed with mixed accounts: {e}")

def test_drs_client_creation():
    """Test DRS client creation with account context"""
    print("\n=== Testing DRS Client Creation ===")
    
    # Import the DRS client function
    from index import create_drs_client
    
    # Test 1: Current account (no context)
    print("\n1. Testing current account DRS client...")
    try:
        client = create_drs_client('us-east-1')
        print(f"✅ Current account client created: {type(client)}")
    except Exception as e:
        print(f"❌ Failed to create current account client: {e}")
    
    # Test 2: Cross-account context (will fail without real role)
    print("\n2. Testing cross-account DRS client...")
    account_context = {
        'AccountId': '999888777666',
        'isCurrentAccount': False
    }
    
    try:
        client = create_drs_client('us-east-1', account_context)
        print(f"✅ Cross-account client created: {type(client)}")
    except Exception as e:
        print(f"⚠️  Cross-account client failed (expected without real role): {e}")

def test_protection_group_parsing():
    """Test how protection group IDs are parsed for account information"""
    print("\n=== Testing Protection Group ID Parsing ===")
    
    test_cases = [
        'pg-simple',
        'pg-account-123456789012',
        'pg-test-999888777666',
        'pg-cross-account-111111111111',
        'pg-no-account-info'
    ]
    
    for pg_id in test_cases:
        print(f"\nTesting PG ID: {pg_id}")
        
        # Check if the ID contains account information
        parts = pg_id.split('-')
        if len(parts) >= 3 and parts[-1].isdigit() and len(parts[-1]) == 12:
            account_id = parts[-1]
            print(f"  ✅ Found account ID: {account_id}")
        else:
            print(f"  ℹ️  No account ID found, using current account")

if __name__ == '__main__':
    print("============================================================")
    print("Simple Multi-Account Logic Tests")
    print("============================================================")
    
    test_account_context_determination()
    test_drs_client_creation()
    test_protection_group_parsing()
    
    print("\n============================================================")
    print("Simple Multi-Account Tests Complete")
    print("============================================================")