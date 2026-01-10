#!/usr/bin/env python3
"""
Fix server instance IDs by getting recovery instance details from DRS
"""

import boto3
import json

def fix_server_instance_ids():
    """Fix server instance IDs by querying DRS for recovery instances"""
    
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
        
        print(f"🔧 Fixing server instance IDs for execution {execution_id}")
        print(f"   Waves to process: {len(waves)}")
        
        # Get all server IDs from all waves
        all_server_ids = []
        for wave in waves:
            server_ids = wave.get('ServerIds', [])
            all_server_ids.extend(server_ids)
        
        print(f"   Total server IDs: {len(all_server_ids)}")
        print(f"   Server IDs: {all_server_ids}")
        
        # Query DRS for recovery instances by source server IDs
        region = 'us-west-2'  # DRS region for this execution
        drs_client = boto3.client('drs', region_name=region)
        
        print(f"\n🔍 Querying DRS for recovery instances in {region}...")
        
        try:
            # Get recovery instances for these source servers
            ri_response = drs_client.describe_recovery_instances(
                filters={'sourceServerIDs': all_server_ids}
            )
            
            recovery_instances = ri_response.get('items', [])
            print(f"   Found {len(recovery_instances)} recovery instances")
            
            # Create mapping of source server ID to recovery instance details
            recovery_mapping = {}
            for ri in recovery_instances:
                source_server_id = ri.get('sourceServerID')
                ec2_instance_id = ri.get('ec2InstanceID')
                recovery_instance_id = ri.get('recoveryInstanceID')
                ec2_state = ri.get('ec2InstanceState')
                
                recovery_mapping[source_server_id] = {
                    'ec2InstanceID': ec2_instance_id,
                    'recoveryInstanceID': recovery_instance_id,
                    'ec2InstanceState': ec2_state
                }
                
                print(f"     {source_server_id} -> {ec2_instance_id} ({ec2_state})")
            
            # Now update the waves with Servers array containing full details
            updated_waves = []
            
            for wave in waves:
                server_ids = wave.get('ServerIds', [])
                job_id = wave.get('JobId')
                wave_status = wave.get('Status', 'UNKNOWN')
                
                print(f"\n   Wave {wave.get('WaveNumber', 0)}: {len(server_ids)} servers")
                
                # Create Servers array with full details
                servers = []
                for server_id in server_ids:
                    recovery_info = recovery_mapping.get(server_id, {})
                    
                    server_data = {
                        'SourceServerId': server_id,
                        'RecoveryJobId': job_id,
                        'InstanceId': recovery_info.get('ec2InstanceID'),
                        'RecoveryInstanceID': recovery_info.get('recoveryInstanceID'),
                        'Status': 'COMPLETED' if wave_status == 'COMPLETED' else 'LAUNCHED',
                        'LaunchTime': wave.get('StartTime'),
                        'Error': None,
                        'Ec2InstanceState': recovery_info.get('ec2InstanceState')
                    }
                    
                    servers.append(server_data)
                    
                    instance_id = recovery_info.get('ec2InstanceID', 'None')
                    print(f"     {server_id}: {instance_id}")
                
                # Add Servers array to wave (keeping ServerIds for compatibility)
                wave['Servers'] = servers
                updated_waves.append(wave)
            
            # Update the execution in DynamoDB
            print(f"\n💾 Updating DynamoDB with server details...")
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
            print(f"✅ Successfully updated execution with server instance IDs")
            
        except Exception as e:
            print(f"❌ Error querying DRS: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_server_instance_ids()