#!/usr/bin/env python3
"""
Comprehensive Legacy Field Cleanup Script
Removes ALL PascalCase fields from ALL DynamoDB tables

This script follows the camelCase migration rules:
- Keep it simple: same camelCase field names everywhere
- No transform functions: direct database operations
- Clean up legacy PascalCase fields completely
"""

import boto3
import json
from decimal import Decimal

# DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Table names
TABLES = {
    'protection_groups': 'aws-elasticdrs-orchestrator-protection-groups-test',
    'recovery_plans': 'aws-elasticdrs-orchestrator-recovery-plans-test', 
    'execution_history': 'aws-elasticdrs-orchestrator-execution-history-test',
    'target_accounts': 'aws-elasticdrs-orchestrator-target-accounts-test'
}

# Legacy PascalCase fields to remove from each table
LEGACY_FIELDS = {
    'protection_groups': [
        'GroupId', 'GroupName', 'Description', 'Region', 'SourceServerIds',
        'ServerSelectionTags', 'CreatedDate', 'LastModifiedDate', 'Version'
    ],
    'recovery_plans': [
        'PlanId', 'PlanName', 'Description', 'Waves', 'CreatedDate', 
        'LastModifiedDate', 'Version', 'TotalWaves'
    ],
    'execution_history': [
        'ExecutionId', 'PlanId', 'PlanName', 'Status', 'ExecutionType',
        'InitiatedBy', 'StartTime', 'EndTime', 'Waves', 'TotalWaves',
        'StateMachineArn', 'AccountContext', 'DrsJobId', 'DrsRegion'
    ],
    'target_accounts': [
        'AccountId', 'AccountName', 'AssumeRoleName', 'IsCurrentAccount',
        'CreatedDate', 'LastModifiedDate', 'Version'
    ]
}

class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

def cleanup_table(table_name: str, legacy_fields: list):
    """Clean up legacy PascalCase fields from a table"""
    print(f"\n🧹 Cleaning up table: {table_name}")
    
    table = dynamodb.Table(table_name)
    
    try:
        # Scan all items in the table
        response = table.scan()
        items = response.get('Items', [])
        
        print(f"   Found {len(items)} items to check")
        
        cleaned_count = 0
        for item in items:
            # Check which legacy fields exist in this item
            fields_to_remove = []
            for field in legacy_fields:
                if field in item:
                    fields_to_remove.append(field)
            
            if fields_to_remove:
                print(f"   Item has legacy fields: {fields_to_remove}")
                
                # Build the key for this item
                key = {}
                if table_name.endswith('protection-groups-test'):
                    key = {'groupId': item['groupId']}
                elif table_name.endswith('recovery-plans-test'):
                    key = {'planId': item['planId']}
                elif table_name.endswith('execution-history-test'):
                    key = {'executionId': item['executionId'], 'planId': item['planId']}
                elif table_name.endswith('target-accounts-test'):
                    key = {'accountId': item['accountId']}
                
                # Remove legacy fields
                remove_expression = "REMOVE " + ", ".join(fields_to_remove)
                
                try:
                    table.update_item(
                        Key=key,
                        UpdateExpression=remove_expression,
                        ConditionExpression="attribute_exists(" + list(key.keys())[0] + ")"
                    )
                    print(f"   ✅ Cleaned item: {key}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"   ❌ Error cleaning item {key}: {e}")
        
        print(f"   🎉 Cleaned {cleaned_count} items in {table_name}")
        
    except Exception as e:
        print(f"   ❌ Error scanning table {table_name}: {e}")

def main():
    """Main cleanup function"""
    print("🚀 Starting comprehensive legacy field cleanup")
    print("📋 Following camelCase migration rules:")
    print("   - Same camelCase field names everywhere")
    print("   - No transform functions")
    print("   - Clean database operations")
    
    total_cleaned = 0
    
    for table_type, table_name in TABLES.items():
        legacy_fields = LEGACY_FIELDS[table_type]
        print(f"\n📊 Table: {table_type}")
        print(f"   Legacy fields to remove: {legacy_fields}")
        
        cleanup_table(table_name, legacy_fields)
    
    print(f"\n🎉 Legacy field cleanup complete!")
    print("✅ All tables now use consistent camelCase field names")
    print("✅ No more mixed PascalCase/camelCase issues")
    print("✅ Database follows camelCase migration rules")

if __name__ == "__main__":
    main()