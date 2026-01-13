#!/usr/bin/env python3
"""
Database CamelCase Cleanup Script
Fixes remaining PascalCase fields and values in DynamoDB tables
"""

import boto3
import json
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def fix_protection_groups():
    """Fix PascalCase values in serverSelectionTags"""
    table = dynamodb.Table('aws-elasticdrs-orchestrator-protection-groups-test')
    
    print("🔍 Scanning Protection Groups table...")
    response = table.scan()
    items = response['Items']
    
    for item in items:
        group_id = item['groupId']
        needs_update = False
        update_expression_parts = []
        expression_attribute_values = {}
        
        # Fix serverSelectionTags - convert PascalCase keys to camelCase
        if 'serverSelectionTags' in item and item['serverSelectionTags']:
            tags = item['serverSelectionTags']
            fixed_tags = {}
            
            for key, value in tags.items():
                # Convert PascalCase keys to camelCase
                if key == 'Purpose':
                    fixed_tags['purpose'] = value
                    needs_update = True
                elif key == 'Environment':
                    fixed_tags['environment'] = value
                    needs_update = True
                elif key == 'Application':
                    fixed_tags['application'] = value
                    needs_update = True
                elif key == 'Tier':
                    fixed_tags['tier'] = value
                    needs_update = True
                else:
                    # Keep other keys as-is (already camelCase)
                    fixed_tags[key] = value
            
            if needs_update:
                update_expression_parts.append("serverSelectionTags = :tags")
                expression_attribute_values[':tags'] = fixed_tags
                print(f"  📝 Fixing serverSelectionTags for {group_id}: {tags} → {fixed_tags}")
        
        # Apply updates if needed
        if needs_update:
            update_expression_parts.append("lastModifiedDate = :timestamp")
            expression_attribute_values[':timestamp'] = int(time.time())
            
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            try:
                table.update_item(
                    Key={'groupId': group_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values
                )
                print(f"  ✅ Updated protection group {group_id}")
            except Exception as e:
                print(f"  ❌ Failed to update {group_id}: {e}")

def fix_executions():
    """Fix PascalCase field names in executions"""
    table = dynamodb.Table('aws-elasticdrs-orchestrator-execution-history-test')
    
    print("🔍 Scanning Execution History table...")
    response = table.scan()
    items = response['Items']
    
    for item in items:
        execution_id = item['executionId']
        needs_update = False
        update_expression_parts = []
        expression_attribute_values = {}
        remove_parts = []
        
        # Fix AccountContext → accountContext
        if 'AccountContext' in item:
            update_expression_parts.append("accountContext = :accountContext")
            expression_attribute_values[':accountContext'] = item['AccountContext']
            remove_parts.append("AccountContext")
            needs_update = True
            print(f"  📝 Moving AccountContext → accountContext for {execution_id}")
        
        # Fix EndTime → endTime
        if 'EndTime' in item:
            update_expression_parts.append("endTime = :endTime")
            expression_attribute_values[':endTime'] = item['EndTime']
            remove_parts.append("EndTime")
            needs_update = True
            print(f"  📝 Moving EndTime → endTime for {execution_id}")
        
        # Fix Status → status (if different from existing status)
        if 'Status' in item and item.get('Status') != item.get('status'):
            # Use the PascalCase Status as the authoritative value
            update_expression_parts.append("#status = :statusValue")
            expression_attribute_values[':statusValue'] = item['Status']
            remove_parts.append("#statusOld")
            needs_update = True
            print(f"  📝 Moving Status → status for {execution_id}: {item['Status']}")
        
        # Fix Waves → waves
        if 'Waves' in item:
            update_expression_parts.append("waves = :waves")
            expression_attribute_values[':waves'] = item['Waves']
            remove_parts.append("Waves")
            needs_update = True
            print(f"  📝 Moving Waves → waves for {execution_id}")
        
        # Fix StateMachineArn → stateMachineArn
        if 'StateMachineArn' in item:
            update_expression_parts.append("stateMachineArn = :stateMachineArn")
            expression_attribute_values[':stateMachineArn'] = item['StateMachineArn']
            remove_parts.append("StateMachineArn")
            needs_update = True
            print(f"  📝 Moving StateMachineArn → stateMachineArn for {execution_id}")
        
        # Apply updates if needed
        if needs_update:
            update_expression_parts.append("lastModifiedDate = :timestamp")
            expression_attribute_values[':timestamp'] = int(time.time())
            
            update_expression = "SET " + ", ".join(update_expression_parts)
            if remove_parts:
                update_expression += " REMOVE " + ", ".join(remove_parts)
            
            expression_attribute_names = {}
            if "#status" in update_expression:
                expression_attribute_names["#status"] = "status"
                expression_attribute_names["#statusOld"] = "Status"
            
            try:
                update_params = {
                    'Key': {
                        'executionId': execution_id,
                        'planId': item['planId']
                    },
                    'UpdateExpression': update_expression,
                    'ExpressionAttributeValues': expression_attribute_values
                }
                if expression_attribute_names:
                    update_params['ExpressionAttributeNames'] = expression_attribute_names
                
                table.update_item(**update_params)
                print(f"  ✅ Updated execution {execution_id}")
            except Exception as e:
                print(f"  ❌ Failed to update {execution_id}: {e}")

def fix_recovery_plans():
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
    """Check and fix any PascalCase issues in recovery plans"""
    table = dynamodb.Table('aws-elasticdrs-orchestrator-recovery-plans-test')
    
    print("🔍 Scanning Recovery Plans table...")
    response = table.scan()
    items = response['Items']
    
    for item in items:
        plan_id = item['planId']
        needs_update = False
        update_expression_parts = []
        expression_attribute_values = {}
        remove_parts = []
        
        # Fix HasServerConflict → hasServerConflict
        if 'HasServerConflict' in item:
            update_expression_parts.append("hasServerConflict = :hasServerConflict")
            expression_attribute_values[':hasServerConflict'] = item['HasServerConflict']
            remove_parts.append("HasServerConflict")
            needs_update = True
            print(f"  📝 Moving HasServerConflict → hasServerConflict for {plan_id}")
        
        # Fix ConflictInfo → conflictInfo
        if 'ConflictInfo' in item:
            update_expression_parts.append("conflictInfo = :conflictInfo")
            expression_attribute_values[':conflictInfo'] = item['ConflictInfo']
            remove_parts.append("ConflictInfo")
            needs_update = True
            print(f"  📝 Moving ConflictInfo → conflictInfo for {plan_id}")
        
        # Fix LastExecutionStatus → lastExecutionStatus
        if 'LastExecutionStatus' in item:
            update_expression_parts.append("lastExecutionStatus = :lastExecutionStatus")
            expression_attribute_values[':lastExecutionStatus'] = item['LastExecutionStatus']
            remove_parts.append("LastExecutionStatus")
            needs_update = True
            print(f"  📝 Moving LastExecutionStatus → lastExecutionStatus for {plan_id}")
        
        # Fix WaveCount → waveCount
        if 'WaveCount' in item:
            update_expression_parts.append("waveCount = :waveCount")
            expression_attribute_values[':waveCount'] = item['WaveCount']
            remove_parts.append("WaveCount")
            needs_update = True
            print(f"  📝 Moving WaveCount → waveCount for {plan_id}")
        
        # Apply updates if needed
        if needs_update:
            update_expression_parts.append("lastModifiedDate = :timestamp")
            expression_attribute_values[':timestamp'] = int(time.time())
            
            update_expression = "SET " + ", ".join(update_expression_parts)
            if remove_parts:
                update_expression += " REMOVE " + ", ".join(remove_parts)
            
            try:
                table.update_item(
                    Key={'planId': plan_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values
                )
                print(f"  ✅ Updated recovery plan {plan_id}")
            except Exception as e:
                print(f"  ❌ Failed to update {plan_id}: {e}")

if __name__ == "__main__":
    import time
    
    print("🚀 Starting Database CamelCase Cleanup...")
    print("=" * 50)
    
    # Fix Protection Groups
    print("\n1. 📁 PROTECTION GROUPS")
    fix_protection_groups()
    
    # Fix Executions
    print("\n2. ⚡ EXECUTIONS")
    fix_executions()
    
    # Fix Target Accounts
    print("\n4. 🎯 TARGET ACCOUNTS")
    fix_target_accounts()
    
    # Fix Recovery Plans
    print("\n5. 📋 RECOVERY PLANS")
    fix_recovery_plans()
    
    print("\n" + "=" * 50)
    print("✅ Database cleanup completed!")
    print("🧪 Run endpoint tests to verify fixes")