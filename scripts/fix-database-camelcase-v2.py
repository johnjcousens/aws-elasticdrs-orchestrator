#!/usr/bin/env python3
"""
Database CamelCase Cleanup Script v2
Fixes remaining PascalCase fields and values in DynamoDB tables
"""

import boto3
import json
import time
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def fix_target_accounts():
    """Fix PascalCase field names in target accounts"""
    table = dynamodb.Table('aws-elasticdrs-orchestrator-target-accounts-test')
    
    print("🔍 Scanning Target Accounts table...")
    response = table.scan()
    items = response['Items']
    
    for item in items:
        account_id = item['accountId']
        needs_update = False
        update_expression_parts = []
        expression_attribute_values = {}
        remove_parts = []
        
        # Fix LastValidated → lastValidated
        if 'LastValidated' in item:
            update_expression_parts.append("lastValidated = :lastValidated")
            expression_attribute_values[':lastValidated'] = item['LastValidated']
            remove_parts.append("LastValidated")
            needs_update = True
            print(f"  📝 Moving LastValidated → lastValidated for {account_id}")
        
        # Fix IsDefault → isDefault
        if 'IsDefault' in item:
            update_expression_parts.append("isDefault = :isDefault")
            expression_attribute_values[':isDefault'] = item['IsDefault']
            remove_parts.append("IsDefault")
            needs_update = True
            print(f"  📝 Moving IsDefault → isDefault for {account_id}")
        
        # Fix IsCurrentAccount → isCurrentAccount
        if 'IsCurrentAccount' in item:
            update_expression_parts.append("isCurrentAccount = :isCurrentAccount")
            expression_attribute_values[':isCurrentAccount'] = item['IsCurrentAccount']
            remove_parts.append("IsCurrentAccount")
            needs_update = True
            print(f"  📝 Moving IsCurrentAccount → isCurrentAccount for {account_id}")
        
        # Apply updates if needed
        if needs_update:
            update_expression_parts.append("lastModifiedDate = :timestamp")
            expression_attribute_values[':timestamp'] = int(time.time())
            
            update_expression = "SET " + ", ".join(update_expression_parts)
            if remove_parts:
                update_expression += " REMOVE " + ", ".join(remove_parts)
            
            try:
                table.update_item(
                    Key={'accountId': account_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values
                )
                print(f"  ✅ Updated target account {account_id}")
            except Exception as e:
                print(f"  ❌ Failed to update {account_id}: {e}")

if __name__ == "__main__":
    print("🚀 Starting Target Accounts CamelCase Cleanup...")
    print("=" * 50)
    
    # Fix Target Accounts
    print("\n🎯 TARGET ACCOUNTS")
    fix_target_accounts()
    
    print("\n" + "=" * 50)
    print("✅ Target accounts cleanup completed!")
    print("🧪 Run endpoint tests to verify fixes")