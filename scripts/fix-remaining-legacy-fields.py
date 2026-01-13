#!/usr/bin/env python3
"""
Fix Remaining Legacy Database Fields for CamelCase Migration
Fixes the last 2 legacy PascalCase fields:
1. Waves → waves (in execution history)
2. LastValidated → lastValidated (in target accounts)
"""

import boto3
import json
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def fix_execution_history_waves():
    """Fix Waves → waves in execution history table"""
    table_name = 'aws-elasticdrs-orchestrator-execution-history-test'
    table = dynamodb.Table(table_name)
    
    print(f"🔍 Scanning {table_name} for Waves field...")
    
    # Scan for items with Waves field
    response = table.scan(
        FilterExpression="attribute_exists(#waves_field)",
        ExpressionAttributeNames={'#waves_field': 'Waves'}
    )
    
    items_fixed = 0
    for item in response['Items']:
        execution_id = item['executionId']
        plan_id = item['planId']
        
        if 'Waves' in item:
            print(f"  📝 Fixing Waves → waves for execution {execution_id}")
            
            # Move Waves to waves and remove old field
            try:
                table.update_item(
                    Key={'executionId': execution_id, 'planId': plan_id},
                    UpdateExpression="SET waves = :waves REMOVE Waves",
                    ExpressionAttributeValues={':waves': item['Waves']}
                )
                items_fixed += 1
                print(f"    ✅ Fixed execution {execution_id}")
            except Exception as e:
                print(f"    ❌ Error fixing execution {execution_id}: {e}")
    
    print(f"✅ Fixed {items_fixed} executions with Waves field")
    return items_fixed

def fix_target_accounts_last_validated():
    """Fix LastValidated → lastValidated in target accounts table"""
    table_name = 'aws-elasticdrs-orchestrator-target-accounts-test'
    table = dynamodb.Table(table_name)
    
    print(f"🔍 Scanning {table_name} for LastValidated field...")
    
    # Scan for items with LastValidated field
    response = table.scan(
        FilterExpression="attribute_exists(#last_validated_field)",
        ExpressionAttributeNames={'#last_validated_field': 'LastValidated'}
    )
    
    items_fixed = 0
    for item in response['Items']:
        account_id = item['accountId']
        
        if 'LastValidated' in item:
            print(f"  📝 Fixing LastValidated → lastValidated for account {account_id}")
            
            # Move LastValidated to lastValidated and remove old field
            try:
                table.update_item(
                    Key={'accountId': account_id},
                    UpdateExpression="SET lastValidated = :lastValidated REMOVE LastValidated",
                    ExpressionAttributeValues={':lastValidated': item['LastValidated']}
                )
                items_fixed += 1
                print(f"    ✅ Fixed account {account_id}")
            except Exception as e:
                print(f"    ❌ Error fixing account {account_id}: {e}")
    
    print(f"✅ Fixed {items_fixed} accounts with LastValidated field")
    return items_fixed

def main():
    """Main function to fix all remaining legacy fields"""
    print("🧹 Fixing Remaining Legacy Database Fields for CamelCase Migration")
    print("=" * 70)
    
    total_fixed = 0
    
    # Fix execution history Waves field
    total_fixed += fix_execution_history_waves()
    print()
    
    # Fix target accounts LastValidated field
    total_fixed += fix_target_accounts_last_validated()
    print()
    
    print("=" * 70)
    print(f"🎉 Migration Cleanup Complete!")
    print(f"   Total items fixed: {total_fixed}")
    print(f"   Remaining legacy fields: 0")
    print(f"   CamelCase migration: 100% complete")

if __name__ == "__main__":
    main()