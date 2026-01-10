#!/usr/bin/env python3
"""
Manually fix the execution data by updating wave statuses based on DRS job results
"""

import boto3
import json
import time

def fix_execution_manually():
    """Manually update the execution with correct wave statuses"""
    
    # Connect to DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('aws-drs-orchestrator-fresh-execution-history-dev')
    
    execution_id = "7b3e357a-dc1a-4f04-9ab8-d3a6b1a584ad"
    plan_id = "b70ba3d2-64a5-4e4e-a71a-5252b5f53d8a"
    
    try:
        # Get the current execution
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('ExecutionId').eq(execution_id)
        )
        
        if not response['Items']:
            print(f"❌ Execution {execution_id} not found")
            return
        
        execution = response['Items'][0]
        waves = execution.get('Waves', [])
        
        print(f"🔧 Fixing execution {execution_id}")
        print(f"   Current status: {execution.get('Status')}")
        print(f"   Waves to fix: {len(waves)}")
        
        # Update each wave based on DRS job results
        updated_waves = []
        
        for i, wave in enumerate(waves):
            job_id = wave.get('JobId')
            region = wave.get('Region', 'us-west-2')
            current_status = wave.get('Status', 'UNKNOWN')
            
            print(f"   Wave {i}: {current_status} -> ", end="")
            
            if job_id:
                try:
                    # Query DRS for job status
                    drs_client = boto3.client('drs', region_name=region)
                    drs_response = drs_client.describe_jobs(filters={'jobIDs': [job_id]})
                    
                    if drs_response.get('items'):
                        job = drs_response['items'][0]
                        drs_status = job.get('status', 'UNKNOWN')
                        participating_servers = job.get('participatingServers', [])
                        
                        if drs_status == 'COMPLETED':
                            # Check if all servers launched
                            all_launched = all(
                                server.get('launchStatus') == 'LAUNCHED'
                                for server in participating_servers
                            )
                            
                            if all_launched:
                                wave['Status'] = 'COMPLETED'
                                wave['EndTime'] = int(time.time())
                                print("COMPLETED ✅")
                            else:
                                wave['Status'] = 'FAILED'
                                wave['EndTime'] = int(time.time())
                                print("FAILED (not all servers launched) ❌")
                        else:
                            print(f"DRS status: {drs_status} (no change)")
                    else:
                        print("DRS job not found (no change)")
                        
                except Exception as e:
                    print(f"Error querying DRS: {e}")
            else:
                print("No JobId (no change)")
            
            updated_waves.append(wave)
        
        # Update the execution in DynamoDB
        try:
            print(f"\n💾 Updating DynamoDB...")
            table.update_item(
                Key={
                    'ExecutionId': execution_id,
                    'PlanId': plan_id
                },
                UpdateExpression='SET Waves = :waves',
                ExpressionAttributeValues={
                    ':waves': updated_waves
                }
            )
            print(f"✅ Successfully updated execution {execution_id}")
            
            # Verify the update
            print(f"\n🔍 Verifying update...")
            verify_response = table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('ExecutionId').eq(execution_id)
            )
            
            if verify_response['Items']:
                updated_execution = verify_response['Items'][0]
                updated_waves_check = updated_execution.get('Waves', [])
                
                for i, wave in enumerate(updated_waves_check):
                    status = wave.get('Status', 'unknown')
                    print(f"   Wave {i}: {status}")
                    
                print(f"✅ Verification complete")
            
        except Exception as e:
            print(f"❌ Error updating DynamoDB: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_execution_manually()