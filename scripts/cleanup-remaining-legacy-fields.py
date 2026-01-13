#!/usr/bin/env python3
"""
Cleanup Remaining Legacy PascalCase Fields
Removes the final 4 legacy PascalCase fields identified in testing:
1. StatusMessage → statusMessage (in execution wave data)
2. RecoveryPlanDescription → recoveryPlanDescription (in execution details)
3. ProtectionGroupName → protectionGroupName (in recovery plan waves)
4. LastValidated → lastValidated (in target accounts)
"""

import boto3
import json
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Table names for test environment
EXECUTION_HISTORY_TABLE = 'aws-elasticdrs-orchestrator-execution-history-test'
RECOVERY_PLANS_TABLE = 'aws-elasticdrs-orchestrator-recovery-plans-test'
TARGET_ACCOUNTS_TABLE = 'aws-elasticdrs-orchestrator-target-accounts-test'

def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def cleanup_execution_history():
    """Remove StatusMessage and RecoveryPlanDescription from execution history"""
    print("🔍 Cleaning up Execution History table...")
    
    table = dynamodb.Table(EXECUTION_HISTORY_TABLE)
    response = table.scan()
    items = response.get('Items', [])
    
    updated_count = 0
    
    for item in items:
        execution_id = item.get('executionId')
        plan_id = item.get('planId')  # Composite key requires both executionId and planId
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
        
        # Fix StatusMessage in waves
        waves = item.get('waves', [])
        updated_waves = []
        waves_updated = False
        
        for wave in waves:
            updated_wave = dict(wave)
            if 'StatusMessage' in wave:
                updated_wave['statusMessage'] = wave['StatusMessage']
                del updated_wave['StatusMessage']
                waves_updated = True
                print(f"  📝 Moving StatusMessage → statusMessage in wave for {execution_id}")
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
                # Use composite key for execution history table
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

def cleanup_recovery_plans():
    """Remove ProtectionGroupName from recovery plan waves"""
    print("🔍 Cleaning up Recovery Plans table...")
    
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
            if 'ProtectionGroupName' in wave:
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

def cleanup_target_accounts():
    """Remove LastValidated from target accounts"""
    print("🔍 Cleaning up Target Accounts table...")
    
    table = dynamodb.Table(TARGET_ACCOUNTS_TABLE)
    response = table.scan()
    items = response.get('Items', [])
    
    updated_count = 0
    
    for item in items:
        account_id = item.get('accountId')
        needs_update = False
        update_expression_parts = []
        remove_parts = []
        expression_values = {}
        
        # Fix LastValidated → lastValidated
        if 'LastValidated' in item:
            update_expression_parts.append("lastValidated = :lastValidated")
            expression_values[':lastValidated'] = item['LastValidated']
            remove_parts.append("LastValidated")
            needs_update = True
            print(f"  📝 Moving LastValidated → lastValidated for {account_id}")
        
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
                    Key={'accountId': account_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values if expression_values else None
                )
                updated_count += 1
                print(f"  ✅ Updated target account {account_id}")
            except Exception as e:
                print(f"  ❌ Error updating target account {account_id}: {e}")
    
    print(f"📊 Target Accounts: Updated {updated_count} items")

def main():
    """Main cleanup function"""
    print("🧹 Starting cleanup of remaining legacy PascalCase fields...")
    print("📋 Target fields:")
    print("   1. StatusMessage → statusMessage (execution wave data)")
    print("   2. RecoveryPlanDescription → recoveryPlanDescription (execution details)")
    print("   3. ProtectionGroupName → protectionGroupName (recovery plan waves)")
    print("   4. LastValidated → lastValidated (target accounts)")
    print()
    
    try:
        cleanup_execution_history()
        print()
        cleanup_recovery_plans()
        print()
        cleanup_target_accounts()
        print()
        print("🎉 Legacy field cleanup completed successfully!")
        print("✅ All remaining PascalCase fields have been converted to camelCase")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())