#!/usr/bin/env python3
"""
Fix server recovery instances by getting complete EC2 instance details
"""

import boto3
import json

def fix_server_recovery_instances():
    """Fix server recovery instances by querying EC2 for complete instance details"""
    
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
        
        print(f"🔧 Fixing server recovery instances for execution {execution_id}")
        print(f"   Waves to process: {len(waves)}")
        
        # Get all instance IDs from all waves
        all_instance_ids = []
        instance_to_server_map = {}
        
        for wave in waves:
            servers = wave.get('Servers', [])
            for server in servers:
                instance_id = server.get('InstanceId')
                if instance_id:
                    all_instance_ids.append(instance_id)
                    instance_to_server_map[instance_id] = server.get('SourceServerId')
        
        print(f"   Total instance IDs: {len(all_instance_ids)}")
        print(f"   Instance IDs: {all_instance_ids}")
        
        # Query EC2 for instance details
        region = 'us-west-2'  # EC2 region for recovery instances
        ec2_client = boto3.client('ec2', region_name=region)
        
        print(f"\n🔍 Querying EC2 for instance details in {region}...")
        
        try:
            # Get EC2 instance details
            ec2_response = ec2_client.describe_instances(
                InstanceIds=all_instance_ids
            )
            
            # Create mapping of instance ID to instance details
            instance_details = {}
            for reservation in ec2_response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance.get('InstanceId')
                    instance_type = instance.get('InstanceType')
                    private_ip = instance.get('PrivateIpAddress')
                    state = instance.get('State', {}).get('Name')
                    launch_time = instance.get('LaunchTime')
                    
                    instance_details[instance_id] = {
                        'instanceType': instance_type,
                        'privateIp': private_ip,
                        'state': state,
                        'launchTime': launch_time.isoformat() if launch_time else None
                    }
                    
                    server_id = instance_to_server_map.get(instance_id, 'unknown')
                    print(f"     {server_id} -> {instance_id} ({instance_type}, {private_ip}, {state})")
            
            # Now update the waves with complete server details
            updated_waves = []
            
            for wave in waves:
                servers = wave.get('Servers', [])
                
                print(f"\n   Wave {wave.get('WaveNumber', 0)}: {len(servers)} servers")
                
                # Update servers with complete EC2 details
                updated_servers = []
                for server in servers:
                    instance_id = server.get('InstanceId')
                    details = instance_details.get(instance_id, {})
                    
                    # Update server with complete details
                    updated_server = server.copy()
                    updated_server.update({
                        'InstanceType': details.get('instanceType'),
                        'PrivateIp': details.get('privateIp'),
                        'Ec2State': details.get('state'),
                        'ActualLaunchTime': details.get('launchTime')
                    })
                    
                    updated_servers.append(updated_server)
                    
                    server_id = server.get('SourceServerId')
                    instance_type = details.get('instanceType', 'None')
                    private_ip = details.get('privateIp', 'None')
                    print(f"     {server_id}: {instance_type}, {private_ip}")
                
                # Update wave with enhanced server details
                wave['Servers'] = updated_servers
                updated_waves.append(wave)
            
            # Update the execution in DynamoDB
            print(f"\n💾 Updating DynamoDB with complete server details...")
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
            print(f"✅ Successfully updated execution with complete server details")
            
        except Exception as e:
            print(f"❌ Error querying EC2: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_server_recovery_instances()