#!/usr/bin/env python3
import boto3
import json
import time
from datetime import datetime
from botocore.exceptions import ClientError

def run_drs_drill(source_server_id="s-3c1730a9e0771ea14", region="us-east-1"):
    """
    Run a disaster recovery drill using AWS DRS for the specified source server
    """
    
    # Initialize AWS DRS client
    drs_client = boto3.client('drs', region_name=region)
    
    try:
        print(f"=== AWS DRS Drill for Source Server: {source_server_id} ===")
        print(f"Region: {region}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Step 1: Get source server information
        print("Step 1: Retrieving source server information...")
        server_info = get_source_server_info(drs_client, source_server_id)
        
        if not server_info:
            print(f"Error: Source server {source_server_id} not found or not accessible")
            return None
            
        print(f"Source Server found: {server_info['sourceProperties']['identificationHints']['hostname']}")
        print(f"Replication Status: {server_info['dataReplicationInfo']['dataReplicationState']}")
        
        # Step 2: Get available recovery snapshots
        print("\nStep 2: Finding available recovery snapshots...")
        snapshots = get_recovery_snapshots(drs_client, source_server_id)
        
        if snapshots:
            latest_snapshot = snapshots[0]  # Most recent snapshot
            print(f"Latest snapshot: {latest_snapshot['snapshotID']}")
            print(f"Snapshot timestamp: {latest_snapshot['timestamp']}")
        else:
            print("No recovery snapshots found. Will use latest data with on-demand snapshot.")
            latest_snapshot = None
        
        # Step 3: Start the recovery drill
        print("\nStep 3: Starting recovery drill...")
        drill_job = start_recovery_drill(drs_client, source_server_id, latest_snapshot)
        
        if not drill_job:
            print("Failed to start recovery drill")
            return None
            
        job_id = drill_job['jobID']
        print(f"Drill job started successfully!")
        print(f"Job ID: {job_id}")
        
        # Step 4: Monitor the drill progress
        print("\nStep 4: Monitoring drill progress...")
        recovery_instance = monitor_drill_progress(drs_client, job_id, source_server_id)
        
        if recovery_instance:
            print(f"\nDrill completed successfully!")
            print(f"Recovery Instance ID: {recovery_instance['recoveryInstanceID']}")
            print(f"EC2 Instance ID: {recovery_instance['ec2InstanceID']}")
            print(f"EC2 Instance State: {recovery_instance['ec2InstanceState']}")
            
            # Step 5: Provide cleanup instructions
            print_cleanup_instructions(recovery_instance['recoveryInstanceID'])
            
            return {
                'job_id': job_id,
                'recovery_instance_id': recovery_instance['recoveryInstanceID'],
                'ec2_instance_id': recovery_instance['ec2InstanceID']
            }
        else:
            print("Drill failed or timed out")
            return None
            
    except ClientError as e:
        print(f"AWS API Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_source_server_info(drs_client, source_server_id):
    """
    Get information about the source server
    """
    try:
        response = drs_client.describe_source_servers(
            filters={
                'sourceServerIDs': [source_server_id]
            }
        )
        
        if response['items']:
            return response['items'][0]
        else:
            return None
            
    except ClientError as e:
        print(f"Error retrieving source server info: {e}")
        return None

def get_recovery_snapshots(drs_client, source_server_id):
    """
    Get available recovery snapshots for the source server
    """
    try:
        response = drs_client.describe_recovery_snapshots(
            sourceServerID=source_server_id
        )
        
        # Filter to only completed snapshots (with timestamp)
        completed_snapshots = [s for s in response['items'] if 'timestamp' in s]
        
        # Sort by timestamp (most recent first)
        snapshots = sorted(completed_snapshots, 
                         key=lambda x: x['timestamp'], 
                         reverse=True)
        
        return snapshots
        
    except ClientError as e:
        print(f"Error retrieving recovery snapshots: {e}")
        return []

def start_recovery_drill(drs_client, source_server_id, recovery_snapshot=None):
    """
    Start the recovery drill
    """
    try:
        # Prepare source server configuration
        source_server_config = {
            'sourceServerID': source_server_id
        }
        
        # Add recovery snapshot if available
        if recovery_snapshot:
            source_server_config['recoverySnapshotID'] = recovery_snapshot['snapshotID']
        
        # Start the recovery drill
        response = drs_client.start_recovery(
            sourceServers=[source_server_config],
            isDrill=True,  # This is the key parameter for drill mode
            tags={
                'DrillType': 'Automated',
                'Timestamp': datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
                'SourceServer': source_server_id
            }
        )
        
        return response['job']
        
    except ClientError as e:
        print(f"Error starting recovery drill: {e}")
        return None

def monitor_drill_progress(drs_client, job_id, source_server_id, timeout_minutes=30):
    """
    Monitor the drill progress and wait for completion
    """
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    print(f"Monitoring job {job_id} (timeout: {timeout_minutes} minutes)")
    
    while time.time() - start_time < timeout_seconds:
        try:
            # Check job status
            job_response = drs_client.describe_jobs(
                filters={
                    'jobIDs': [job_id]
                }
            )
            
            if job_response['items']:
                job = job_response['items'][0]
                status = job['status']
                
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed}s] Job status: {status}")
                
                # Check participating servers
                if 'participatingServers' in job:
                    for server in job['participatingServers']:
                        launch_status = server.get('launchStatus', 'UNKNOWN')
                        print(f"  Server {server['sourceServerID']}: launchStatus={launch_status}")
                
                if status == 'COMPLETED':
                    # Get recovery instance information
                    print("\nJob completed! Looking for recovery instance...")
                    recovery_instances = drs_client.describe_recovery_instances(
                        filters={
                            'sourceServerIDs': [source_server_id]
                        }
                    )
                    
                    # Find the drill instance
                    for instance in recovery_instances['items']:
                        if instance.get('isDrill', False) and instance.get('jobID') == job_id:
                            return instance
                    
                    print("Warning: Job completed but no recovery instance found")
                    return None
                    
                elif status in ['FAILED', 'TERMINATED']:
                    print(f"Job failed with status: {status}")
                    
                    # Print detailed error if available
                    if 'participatingServers' in job:
                        for server in job['participatingServers']:
                            if 'launchStatus' in server and server['launchStatus'] == 'FAILED':
                                print(f"Server {server['sourceServerID']} launch failed")
                    
                    return None
                    
            time.sleep(30)  # Wait 30 seconds before checking again
            
        except ClientError as e:
            print(f"Error monitoring job: {e}")
            time.sleep(30)
    
    print("Timeout reached while waiting for drill completion")
    return None

def print_cleanup_instructions(recovery_instance_id):
    """
    Print instructions for cleaning up the drill resources
    """
    print("\n" + "=" * 60)
    print("IMPORTANT: CLEANUP INSTRUCTIONS")
    print("=" * 60)
    print("The drill has created recovery instances that will incur charges.")
    print("Remember to terminate the drill instances when testing is complete.")
    print()
    print("To terminate the drill instance:")
    print(f"1. Via AWS CLI:")
    print(f"   aws drs terminate-recovery-instances --recovery-instance-ids {recovery_instance_id}")
    print()
    print("2. Via AWS Console:")
    print("   - Go to AWS DRS Console")
    print("   - Select the recovery instance")
    print("   - Choose 'Terminate recovery instances'")
    print("=" * 60)

if __name__ == "__main__":
    # Configuration
    SOURCE_SERVER_ID = "s-3c1730a9e0771ea14"
    AWS_REGION = "us-east-1"  # Update with your region
    
    print("Starting AWS DRS Drill...")
    
    # Run the drill
    result = run_drs_drill(SOURCE_SERVER_ID, AWS_REGION)
    
    if result:
        print(f"\n✅ Drill completed successfully!")
        print(f"Job ID: {result['job_id']}")
        print(f"Recovery Instance: {result['recovery_instance_id']}")
        print(f"EC2 Instance: {result['ec2_instance_id']}")
    else:
        print("\n❌ Drill failed. Check the error messages above.")
