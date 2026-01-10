#!/usr/bin/env python3
"""
Quick diagnostic for execution 7b3e357a-dc1a-4f04-9ab8-d3a6b1a584ad
"""

import boto3
import json
from datetime import datetime

def main():
    execution_id = "7b3e357a-dc1a-4f04-9ab8-d3a6b1a584ad"
    
    print(f"🔍 Investigating Execution: {execution_id}")
    print("=" * 60)
    
    # Check DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('aws-drs-orchestrator-fresh-execution-history-dev')
    
    try:
        # First scan to find the execution and get the PlanId
        scan_response = table.scan(
            FilterExpression='ExecutionId = :exec_id',
            ExpressionAttributeValues={':exec_id': execution_id}
        )
        
        if not scan_response['Items']:
            print(f"❌ Execution not found in DynamoDB")
            return
            
        execution = scan_response['Items'][0]
        plan_id = execution['PlanId']
        
        # Now get the full item with proper key
        response = table.get_item(Key={'ExecutionId': execution_id, 'PlanId': plan_id})
        
        if 'Item' in response:
            execution = response['Item']
            print(f"✅ Found execution in DynamoDB")
            print(f"Plan ID: {plan_id}")
            print(f"Status: {execution.get('Status', 'N/A')}")
            print(f"Created: {execution.get('CreatedAt', 'N/A')}")
            print(f"Total Waves: {execution.get('TotalWaves', 'N/A')}")
            print(f"Completed Waves: {execution.get('CompletedWaves', 'N/A')}")
            
            if 'Waves' in execution:
                print(f"\n🌊 Wave Status:")
                polling_count = 0
                completed_count = 0
                paused_count = 0
                
                for wave_id, wave_data in execution['Waves'].items():
                    status = wave_data.get('Status', 'N/A')
                    drs_job_id = wave_data.get('DrsJobId', 'N/A')
                    updated_at = wave_data.get('UpdatedAt', 'N/A')
                    
                    print(f"  Wave {wave_id}: {status}")
                    print(f"    DRS Job: {drs_job_id}")
                    print(f"    Updated: {updated_at}")
                    
                    if status == 'POLLING':
                        polling_count += 1
                    elif status == 'COMPLETED':
                        completed_count += 1
                    elif status == 'PAUSED':
                        paused_count += 1
                
                print(f"\n📊 Summary:")
                print(f"  POLLING waves: {polling_count}")
                print(f"  COMPLETED waves: {completed_count}")
                print(f"  PAUSED waves: {paused_count}")
                
                if polling_count > 0:
                    print(f"\n⚠️ ISSUE: {polling_count} waves stuck in POLLING")
                    print(f"💡 These need reconciliation with DRS API")
                elif paused_count > 0:
                    print(f"\n⏸️ INFO: {paused_count} waves are PAUSED")
                    print(f"💡 Execution is waiting for manual resume")
        else:
            print(f"❌ Could not retrieve full execution details")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Check Lambda functions
    print(f"\n🔧 Checking Lambda Functions:")
    lambda_client = boto3.client('lambda')
    
    functions = [
        'aws-drs-orchestrator-fresh-api-handler-dev',
        'aws-drs-orchestrator-fresh-execution-finder-dev', 
        'aws-drs-orchestrator-fresh-execution-poller-dev'
    ]
    
    for func_name in functions:
        try:
            response = lambda_client.get_function(FunctionName=func_name)
            config = response['Configuration']
            print(f"✅ {func_name}")
            print(f"   Modified: {config['LastModified']}")
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"❌ {func_name} - NOT FOUND")
        except Exception as e:
            print(f"❌ {func_name} - Error: {e}")

if __name__ == "__main__":
    main()