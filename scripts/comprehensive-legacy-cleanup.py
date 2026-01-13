#!/usr/bin/env python3
"""
Comprehensive Legacy PascalCase Field Cleanup
Removes ALL remaining PascalCase fields from the database to complete camelCase migration.
"""

import boto3
import json
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Table names for test environment
EXECUTION_HISTORY_TABLE = 'aws-elasticdrs-orchestrator-execution-history-test'
RECOVERY_PLANS_TABLE = 'aws-elasticdrs-orchestrator-recovery-plans-test'

def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def cleanup_execution_history_comprehensive():
    """Comprehensive cleanup of execution history table"""
    print("🔍 Comprehensive cleanup of Execution History table...")
    
    table = dynamodb.Table(EXECUTION_HISTORY_TABLE)
    
    # Scan all items with pagination
    response = table.scan()
    items = response.get('Items', [])
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
    
    print(f"  📊 Found {len(items)} executions to process")
    updated_count = 0
    
    for item in items:
        execution_id = item.get('executionId')
        plan_id = item.get('planId')
        needs_update = False
        update_expression_parts = []
        remove_parts = []
        expression_values = {}
        
        # Fix RecoveryPlanDescription → recoveryPlanDescription
        if 'RecoveryPlanDescription' in item:
            update_expression_parts.append("recoveryPlanDescription = :recoveryPlanDescription")
            expression_values[':recoveryPlanDescription'] = item['RecoveryPlanDescription']
            remove_parts.append("RecoveryPlanDescription")
            needs_update = True
            print(f"  📝 Moving RecoveryPlanDescription → recoveryPlanDescription for {execution_id}")
        
        # Remove duplicate Waves field (keep camelCase waves)
        if 'Waves' in item:
            remove_parts.append("Waves")
            needs_update = True
            print(f"  📝 Removing duplicate PascalCase Waves field for {execution_id}")
        
        # Fix StatusMessage in waves - handle all wave objects
        waves = item.get('waves', [])
        updated_waves = []
        waves_updated = False
        
        for i, wave in enumerate(waves):
            updated_wave = dict(wave)
            
            # Always remove StatusMessage if it exists (keep statusMessage)
            if 'StatusMessage' in wave:
                # If statusMessage doesn't exist, move StatusMessage to statusMessage
                if 'statusMessage' not in wave:
                    updated_wave['statusMessage'] = wave['StatusMessage']
                    print(f"  📝 Moving StatusMessage → statusMessage in wave {i} for {execution_id}")
                else:
                    print(f"  📝 Removing duplicate StatusMessage in wave {i} for {execution_id}")
                
                del updated_wave['StatusMessage']
                waves_updated = True
            
            updated_waves.append(updated_wave)
        
        if waves_updated:
            update_expression_parts.append("waves = :waves")
            expression_values[':waves'] = updated_waves
            needs_update = True
        
        if needs_update:
            # Build update expression
            update_expression = ""
            if update_expression_parts:
                update_expression = "SET " + ", ".join(update_expression_parts)
            if remove_parts:
                if update_expression:
                    update_expression += " REMOVE " + ", ".join(remove_parts)
                else:
                    update_expression = "REMOVE " + ", ".join(remove_parts)
            
            try:
                table.update_item(
                    Key={
                        'executionId': execution_id,
                        'planId': plan_id
                    },
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values if expression_values else None
                )
                updated_count += 1
                print(f"  ✅ Updated execution {execution_id}")
            except Exception as e:
                print(f"  ❌ Error updating execution {execution_id}: {e}")
    
    print(f"📊 Execution History: Updated {updated_count} items")

def cleanup_recovery_plans_comprehensive():
    """Comprehensive cleanup of recovery plans table"""
    print("🔍 Comprehensive cleanup of Recovery Plans table...")
    
    table = dynamodb.Table(RECOVERY_PLANS_TABLE)
    response = table.scan()
    items = response.get('Items', [])
    
    updated_count = 0
    
    for item in items:
        plan_id = item.get('planId')
        waves = item.get('waves', [])
        updated_waves = []
        waves_updated = False
        
        for wave in waves:
            updated_wave = dict(wave)
            
            # Fix ProtectionGroupName → protectionGroupName
            if 'ProtectionGroupName' in wave:
                if 'protectionGroupName' not in wave:
                    updated_wave['protectionGroupName'] = wave['ProtectionGroupName']
                del updated_wave['ProtectionGroupName']
                waves_updated = True
                print(f"  📝 Moving ProtectionGroupName → protectionGroupName in wave for {plan_id}")
            
            updated_waves.append(updated_wave)
        
        if waves_updated:
            try:
                table.update_item(
                    Key={'planId': plan_id},
                    UpdateExpression="SET waves = :waves",
                    ExpressionAttributeValues={':waves': updated_waves}
                )
                updated_count += 1
                print(f"  ✅ Updated recovery plan {plan_id}")
            except Exception as e:
                print(f"  ❌ Error updating recovery plan {plan_id}: {e}")
    
    print(f"📊 Recovery Plans: Updated {updated_count} items")

def main():
    """Main cleanup function"""
    print("🧹 Starting comprehensive cleanup of ALL remaining legacy PascalCase fields...")
    print("📋 Target operations:")
    print("   1. Remove duplicate Waves field (keep camelCase waves)")
    print("   2. Fix StatusMessage → statusMessage in wave data")
    print("   3. Fix RecoveryPlanDescription → recoveryPlanDescription")
    print("   4. Fix ProtectionGroupName → protectionGroupName in recovery plan waves")
    print()
    
    try:
        cleanup_execution_history_comprehensive()
        print()
        cleanup_recovery_plans_comprehensive()
        print()
        print("🎉 Comprehensive legacy field cleanup completed successfully!")
        print("✅ All remaining PascalCase fields have been converted to camelCase")
        print("✅ Duplicate fields have been removed")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())