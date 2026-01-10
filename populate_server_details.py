#!/usr/bin/env python3
"""
Populate server details with recovery instance information from DRS jobs
"""

import boto3
import json

def populate_server_details():
    """Populate server details with recovery instance IDs from DRS job results"""
    
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
        
        print(f"🔧 Populating server details for execution {execution_id}")
        print(f"   Waves to process: {len(waves)}")
        
        updated_waves = []
        
        for i, wave in enumerate(waves):
            job_id = wave.get('JobId')
            region = wave.get('Region', 'us-west-2')
            servers = wave.get('Servers', [])
            
            print(f"\n   Wave {i}: {len(servers)} servers")
            
            if job_id and servers:
                try:
                    # Query DRS for job details including recovery instances
                    drs_client = boto3.client('drs', region_name=region)
                    
                    # Get job details
                    job_response = drs_client.describe_jobs(filters={'jobIDs': [job_id]})
                    
                    if job_response.get('items'):
                        job = job_response['items'][0]
                        participating_servers = job.get('participatingServers', [])
                        
                        print(f"     DRS Job: {job_id} - {len(participating_servers)} participating servers")
                        
                        # Create a mapping of source server ID to recovery instance details
                        recovery_mapping = {}
                        for drs_server in participating_servers:
                            source_server_id = drs_server.get('sourceServerID')
                            launch_status = drs_server.get('launchStatus', 'UNKNOWN')
                            
                            # Try to get recovery instance details
                            try:
                                recovery_response = drs_client.describe_recovery_instances(
                                    filters={'sourceServerIDs': [source_server_id]}
                                )
                                
                                if recovery_response.get('items'):
                                    recovery_instance = recovery_response['items'][0]
                                    recovery_mapping[source_server_id] = {
                                        'recoveryInstanceID': recovery_instance.get('recoveryInstanceID'),
                                        'ec2InstanceID': recovery_instance.get('ec2InstanceID'),
                                        'ec2InstanceState': recovery_instance.get('ec2InstanceState'),
                                        'launchStatus': launch_status,
                                        'jobID': recovery_instance.get('jobID')
                                    }
                                    print(f"       {source_server_id}: Recovery Instance {recovery_instance.get('ec2InstanceID')}")
                                else:
                                    recovery_mapping[source_server_id] = {
                                        'launchStatus': launch_status
                                    }
                                    print(f"       {source_server_id}: No recovery instance found")
                                    
                            except Exception as e:
                                print(f"       {source_server_id}: Error getting recovery instance: {e}")
                                recovery_mapping[source_server_id] = {
                                    'launchStatus': launch_status
                                }
                        
                        # Update server details with recovery instance information
                        updated_servers = []
                        for server in servers:
                            source_server_id = server.get('sourceServerId')
                            
                            if source_server_id in recovery_mapping:
                                recovery_info = recovery_mapping[source_server_id]
                                
                                # Update server with recovery instance details
                                server['instanceId'] = recovery_info.get('ec2InstanceID')
                                server['recoveryInstanceId'] = recovery_info.get('recoveryInstanceID')
                                server['instanceState'] = recovery_info.get('ec2InstanceState')
                                server['launchStatus'] = recovery_info.get('launchStatus', server.get('status', 'UNKNOWN'))
                                
                                # Try to get instance details from EC2 if we have the instance ID
                                if recovery_info.get('ec2InstanceID'):
                                    try:
                                        ec2_client = boto3.client('ec2', region_name=region)
                                        ec2_response = ec2_client.describe_instances(
                                            InstanceIds=[recovery_info['ec2InstanceID']]
                                        )
                                        
                                        if ec2_response.get('Reservations'):
                                            instance = ec2_response['Reservations'][0]['Instances'][0]
                                            server['instanceType'] = instance.get('InstanceType')
                                            server['privateIp'] = instance.get('PrivateIpAddress')
                                            server['publicIp'] = instance.get('PublicIpAddress')
                                            server['availabilityZone'] = instance.get('Placement', {}).get('AvailabilityZone')
                                            
                                            print(f"         Updated with EC2 details: {instance.get('InstanceType')}, {instance.get('PrivateIpAddress')}")
                                        
                                    except Exception as e:
                                        print(f"         Error getting EC2 details: {e}")
                            
                            updated_servers.append(server)
                        
                        wave['Servers'] = updated_servers
                        
                    else:
                        print(f"     DRS Job {job_id} not found")
                        
                except Exception as e:
                    print(f"     Error processing wave {i}: {e}")
            
            updated_waves.append(wave)
        
        # Update the execution in DynamoDB
        try:
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
            print(f"✅ Successfully updated execution with server details")
            
        except Exception as e:
            print(f"❌ Error updating DynamoDB: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    populate_server_details()