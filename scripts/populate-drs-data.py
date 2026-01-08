#!/usr/bin/env python3
"""
Populate DRS Data Script

This script enriches existing executions with missing DRS job information
by querying DRS APIs and updating DynamoDB with complete server details.

Fixes the missing Instance IDs, Types, Private IPs, and Launch Times
that should be showing in the Wave Progress UI.
"""

import boto3
import json
import time
from typing import Dict, List, Any, Optional

# Initialize AWS clients
dynamodb = boto3.client('dynamodb')
drs = boto3.client('drs')
ec2 = boto3.client('ec2')

# Configuration
EXECUTION_HISTORY_TABLE = 'aws-elasticdrs-orchestrator-execution-history-dev'
DRS_REGION = 'us-west-2'  # Where recovery instances exist
DRY_RUN = False  # Set to False to actually update DynamoDB

def get_all_executions() -> List[Dict]:
    """Get all executions from DynamoDB."""
    try:
        print("📋 Scanning execution history table...")
        
        response = dynamodb.scan(TableName=EXECUTION_HISTORY_TABLE)
        executions = []
        
        for item in response.get('Items', []):
            execution = parse_dynamodb_item(item)
            executions.append(execution)
        
        print(f"📋 Found {len(executions)} executions")
        return executions
        
    except Exception as e:
        print(f"❌ Error scanning executions: {e}")
        return []

def parse_dynamodb_item(item: Dict) -> Dict:
    """Parse DynamoDB item to Python dict."""
    result = {}
    
    for key, value in item.items():
        if 'S' in value:
            result[key] = value['S']
        elif 'N' in value:
            result[key] = int(value['N']) if '.' not in value['N'] else float(value['N'])
        elif 'L' in value:
            result[key] = [parse_dynamodb_value(v) for v in value['L']]
        elif 'M' in value:
            result[key] = parse_dynamodb_item(value['M'])
        elif 'BOOL' in value:
            result[key] = value['BOOL']
        elif 'NULL' in value:
            result[key] = None
    
    return result

def parse_dynamodb_value(value: Dict) -> Any:
    """Parse a single DynamoDB value."""
    if 'S' in value:
        return value['S']
    elif 'N' in value:
        return int(value['N']) if '.' not in value['N'] else float(value['N'])
    elif 'L' in value:
        return [parse_dynamodb_value(v) for v in value['L']]
    elif 'M' in value:
        return parse_dynamodb_item(value['M'])
    elif 'BOOL' in value:
        return value['BOOL']
    elif 'NULL' in value:
        return None
    else:
        return value

def get_recovery_instances() -> Dict[str, Dict]:
    """Get all recovery instances from DRS."""
    try:
        print(f"🔍 Querying DRS recovery instances in {DRS_REGION}...")
        
        drs_client = boto3.client('drs', region_name=DRS_REGION)
        response = drs_client.describe_recovery_instances()
        
        instances = {}
        for instance in response.get('items', []):
            source_server_id = instance.get('sourceServerID')
            if source_server_id:
                instances[source_server_id] = {
                    'recoveryInstanceID': instance.get('recoveryInstanceID'),
                    'ec2InstanceID': instance.get('ec2InstanceID'),
                    'ec2InstanceState': instance.get('ec2InstanceState'),
                    'ec2InstanceType': instance.get('ec2InstanceType'),
                    'jobID': instance.get('jobID'),
                    'pointInTimeDateTime': instance.get('pointInTimeDateTime'),
                }
        
        print(f"🔍 Found {len(instances)} recovery instances")
        return instances
        
    except Exception as e:
        print(f"❌ Error getting recovery instances: {e}")
        return {}

def get_ec2_instance_details(instance_id: str) -> Optional[Dict]:
    """Get EC2 instance details."""
    try:
        ec2_client = boto3.client('ec2', region_name=DRS_REGION)
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        
        if not response.get('Reservations'):
            return None
            
        instance = response['Reservations'][0]['Instances'][0]
        
        # Get hostname from Name tag or private DNS
        tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
        hostname = tags.get('Name', instance.get('PrivateDnsName', ''))
        
        return {
            'hostname': hostname,
            'privateIpAddress': instance.get('PrivateIpAddress', ''),
            'instanceType': instance.get('InstanceType', ''),
            'launchTime': instance.get('LaunchTime'),
            'state': instance.get('State', {}).get('Name', ''),
        }
        
    except Exception as e:
        print(f"⚠️ Error getting EC2 details for {instance_id}: {e}")
        return None

def enrich_execution_with_drs_data(execution: Dict, recovery_instances: Dict[str, Dict]) -> Dict:
    """Enrich execution with DRS data."""
    execution_id = execution.get('ExecutionId', 'unknown')
    waves = execution.get('Waves', [])
    
    print(f"\n🔧 Processing execution {execution_id}")
    print(f"🔧 Found {len(waves)} waves")
    
    updated_waves = []
    enriched_servers = 0
    
    for wave_idx, wave in enumerate(waves):
        wave_name = wave.get('WaveName', f'Wave {wave_idx + 1}')
        job_id = wave.get('JobId')
        region = wave.get('Region', DRS_REGION)
        server_ids = wave.get('ServerIds', [])
        
        print(f"  📊 Wave: {wave_name} (JobId: {job_id})")
        
        # Get existing servers from both formats
        servers = wave.get('Servers', [])
        server_statuses = wave.get('ServerStatuses', [])
        
        print(f"    📋 Legacy Servers: {len(servers)}")
        print(f"    📋 ServerStatuses: {len(server_statuses)}")
        print(f"    📋 ServerIds in wave: {len(server_ids)}")
        
        # If we have a JobId but no server data, query DRS directly
        if job_id and not servers and not server_statuses and server_ids:
            print(f"    🔍 Querying DRS for job {job_id} in region {region}")
            
            try:
                drs_client = boto3.client('drs', region_name=region)
                response = drs_client.describe_jobs(filters={"jobIDs": [job_id]})
                
                if response.get('items'):
                    job = response['items'][0]
                    drs_status = job.get('status', 'UNKNOWN')
                    participating_servers = job.get('participatingServers', [])
                    
                    print(f"    ✅ Found DRS job: status={drs_status}, servers={len(participating_servers)}")
                    
                    # Update wave status based on DRS job
                    if drs_status == 'COMPLETED':
                        all_launched = all(s.get('launchStatus') == 'LAUNCHED' for s in participating_servers)
                        if all_launched:
                            wave['Status'] = 'completed'
                            wave['StatusMessage'] = 'All servers launched successfully'
                        else:
                            wave['Status'] = 'FAILED'
                            wave['StatusMessage'] = 'Some servers failed to launch'
                    elif drs_status == 'FAILED':
                        wave['Status'] = 'FAILED'
                        wave['StatusMessage'] = 'DRS job failed'
                    
                    # Build ServerStatuses array
                    server_statuses = []
                    servers = []
                    
                    for drs_server in participating_servers:
                        source_server_id = drs_server.get('sourceServerID')
                        launch_status = drs_server.get('launchStatus', 'UNKNOWN')
                        recovery_info = recovery_instances.get(source_server_id, {})
                        
                        # Get instance ID from multiple sources
                        instance_id = (
                            drs_server.get('recoveryInstanceID') or
                            recovery_info.get('recoveryInstanceID') or
                            recovery_info.get('ec2InstanceID')
                        )
                        
                        # ServerStatuses format (new)
                        server_status = {
                            'SourceServerId': source_server_id,
                            'LaunchStatus': launch_status,
                            'RecoveryInstanceID': instance_id,
                        }
                        server_statuses.append(server_status)
                        
                        # Legacy Servers format
                        server_data = {
                            'SourceServerId': source_server_id,
                            'Status': launch_status,
                            'HostName': '',
                            'LaunchTime': int(time.time()),
                            'InstanceId': instance_id or '',
                            'PrivateIpAddress': '',
                        }
                        
                        # Enrich with EC2 data if we have instance ID
                        if instance_id:
                            ec2_details = get_ec2_instance_details(instance_id)
                            if ec2_details:
                                server_data['HostName'] = ec2_details.get('hostname', '')
                                server_data['PrivateIpAddress'] = ec2_details.get('privateIpAddress', '')
                                server_data['InstanceType'] = ec2_details.get('instanceType', '')
                                
                                if ec2_details.get('launchTime'):
                                    server_data['LaunchTime'] = int(ec2_details['launchTime'].timestamp())
                                
                                print(f"      ✅ Enriched {source_server_id}: {instance_id} ({ec2_details.get('instanceType', 'unknown')})")
                                enriched_servers += 1
                        
                        servers.append(server_data)
                    
                    # Store both formats in wave
                    wave['ServerStatuses'] = server_statuses
                    wave['Servers'] = servers
                    
                else:
                    print(f"    ❌ DRS job {job_id} not found")
                    
            except Exception as e:
                print(f"    ❌ Error querying DRS: {e}")
        
        # Enrich existing servers with DRS data if missing
        else:
            # Process ServerStatuses (new format)
            enriched_server_statuses = []
            for server_status in server_statuses:
                source_server_id = server_status.get('SourceServerId', '')
                recovery_info = recovery_instances.get(source_server_id, {})
                
                # Get instance ID from multiple sources
                instance_id = (
                    server_status.get('RecoveryInstanceID') or
                    recovery_info.get('recoveryInstanceID') or
                    recovery_info.get('ec2InstanceID')
                )
                
                if instance_id and not server_status.get('RecoveryInstanceID'):
                    print(f"      ✅ Found instance ID for {source_server_id}: {instance_id}")
                    server_status['RecoveryInstanceID'] = instance_id
                    enriched_servers += 1
                
                # Add additional DRS data
                if recovery_info:
                    server_status['InstanceType'] = recovery_info.get('ec2InstanceType', '')
                    server_status['JobID'] = recovery_info.get('jobID', job_id)
                    server_status['PointInTimeDateTime'] = recovery_info.get('pointInTimeDateTime', '')
                
                enriched_server_statuses.append(server_status)
            
            # Process legacy Servers format
            enriched_servers_list = []
            for server in servers:
                source_server_id = server.get('SourceServerId', '')
                recovery_info = recovery_instances.get(source_server_id, {})
                
                # Get instance ID from multiple sources
                instance_id = (
                    server.get('InstanceId') or
                    recovery_info.get('recoveryInstanceID') or
                    recovery_info.get('ec2InstanceID')
                )
                
                if instance_id:
                    server['InstanceId'] = instance_id
                    
                    # Get EC2 details if we have instance ID
                    ec2_details = get_ec2_instance_details(instance_id)
                    if ec2_details:
                        server['HostName'] = ec2_details.get('hostname', server.get('HostName', ''))
                        server['PrivateIpAddress'] = ec2_details.get('privateIpAddress', server.get('PrivateIpAddress', ''))
                        server['InstanceType'] = ec2_details.get('instanceType', '')
                        
                        if ec2_details.get('launchTime'):
                            server['LaunchTime'] = int(ec2_details['launchTime'].timestamp())
                        
                        print(f"      ✅ Enriched {source_server_id}: {instance_id} ({ec2_details.get('instanceType', 'unknown')})")
                        enriched_servers += 1
                
                enriched_servers_list.append(server)
            
            # Update wave with enriched data
            wave['Servers'] = enriched_servers_list
            wave['ServerStatuses'] = enriched_server_statuses
        
        updated_waves.append(wave)
    
    execution['Waves'] = updated_waves
    print(f"🔧 Enriched {enriched_servers} servers in execution {execution_id}")
    
    return execution

def update_execution_in_dynamodb(execution: Dict) -> bool:
    """Update execution in DynamoDB."""
    try:
        execution_id = execution['ExecutionId']
        plan_id = execution['PlanId']
        
        if DRY_RUN:
            print(f"🔍 DRY RUN: Would update execution {execution_id}")
            return True
        
        print(f"💾 Updating execution {execution_id} in DynamoDB...")
        
        # Format waves for DynamoDB
        waves_dynamodb = []
        for wave in execution.get('Waves', []):
            waves_dynamodb.append(format_wave_for_dynamodb(wave))
        
        dynamodb.update_item(
            TableName=EXECUTION_HISTORY_TABLE,
            Key={
                'ExecutionId': {'S': execution_id},
                'PlanId': {'S': plan_id}
            },
            UpdateExpression='SET Waves = :waves',
            ExpressionAttributeValues={
                ':waves': {'L': waves_dynamodb}
            }
        )
        
        print(f"💾 ✅ Updated execution {execution_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating execution {execution['ExecutionId']}: {e}")
        return False

def format_wave_for_dynamodb(wave: Dict) -> Dict:
    """Format wave for DynamoDB storage."""
    formatted = {'M': {}}
    
    for key, value in wave.items():
        if isinstance(value, str):
            formatted['M'][key] = {'S': value}
        elif isinstance(value, bool):
            formatted['M'][key] = {'BOOL': value}
        elif isinstance(value, (int, float)):
            formatted['M'][key] = {'N': str(value)}
        elif isinstance(value, list):
            formatted['M'][key] = {'L': [format_value_for_dynamodb(v) for v in value]}
        elif isinstance(value, dict):
            formatted['M'][key] = format_wave_for_dynamodb(value)
        elif value is None:
            formatted['M'][key] = {'NULL': True}
    
    return formatted

def format_value_for_dynamodb(value: Any) -> Dict:
    """Format value for DynamoDB."""
    if isinstance(value, str):
        return {'S': value}
    elif isinstance(value, bool):
        return {'BOOL': value}
    elif isinstance(value, (int, float)):
        return {'N': str(value)}
    elif isinstance(value, dict):
        return format_wave_for_dynamodb(value)
    elif isinstance(value, list):
        return {'L': [format_value_for_dynamodb(v) for v in value]}
    elif value is None:
        return {'NULL': True}
    else:
        return {'S': str(value)}

def main():
    """Main function."""
    print("🚀 AWS DRS Orchestration - Populate DRS Data Script")
    print("=" * 60)
    
    if DRY_RUN:
        print("🔍 DRY RUN MODE - No changes will be made to DynamoDB")
    else:
        print("⚠️  LIVE MODE - Changes will be written to DynamoDB")
    
    print()
    
    # Get all executions
    executions = get_all_executions()
    if not executions:
        print("❌ No executions found")
        return
    
    # Get recovery instances
    recovery_instances = get_recovery_instances()
    if not recovery_instances:
        print("❌ No recovery instances found")
        return
    
    # Process each execution
    total_enriched = 0
    total_updated = 0
    
    for execution in executions:
        execution_status = execution.get('Status', '')
        
        # Skip if no waves
        if not execution.get('Waves'):
            continue
        
        # Enrich with DRS data
        enriched_execution = enrich_execution_with_drs_data(execution, recovery_instances)
        
        # Update in DynamoDB
        if update_execution_in_dynamodb(enriched_execution):
            total_updated += 1
        
        total_enriched += 1
    
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY:")
    print(f"   Executions processed: {total_enriched}")
    print(f"   Executions updated: {total_updated}")
    print(f"   Recovery instances available: {len(recovery_instances)}")
    
    if DRY_RUN:
        print(f"\n🔍 This was a DRY RUN - set DRY_RUN=False to apply changes")
    else:
        print(f"\n✅ All updates applied to DynamoDB")

if __name__ == '__main__':
    main()