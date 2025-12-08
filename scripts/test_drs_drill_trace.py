#!/usr/bin/env python3
"""
DRS Drill Trace Test
Tests DRS recovery with detailed tracing to identify failure points
"""

import boto3
import json
import time
import sys

# Test configuration - using first 2 servers
SOURCE_SERVER_IDS = ['s-3c1730a9e0771ea14', 's-3d75cdc0d9a28a725']  # EC2AMAZ-4IMB9PN, EC2AMAZ-RLP9U5V
REGION = 'us-east-1'
IS_DRILL = True

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_drs_recovery():
    """Test DRS recovery with full tracing"""
    
    drs = boto3.client('drs', region_name=REGION)
    ec2 = boto3.client('ec2', region_name=REGION)
    
    print_section("STEP 1: Verify Source Servers Exist")
    
    try:
        response = drs.describe_source_servers()
        servers = response.get('items', [])
        print(f"✓ Found {len(servers)} source servers in DRS")
        
        for server in servers:
            sid = server['sourceServerID']
            state = server.get('lifeCycle', {}).get('state', 'UNKNOWN')
            print(f"  - {sid}: {state}")
            
            if sid in SOURCE_SERVER_IDS:
                print(f"    ✓ Target server found")
                
                # Check launch configuration
                try:
                    launch_config = drs.get_launch_configuration(sourceServerID=sid)
                    print(f"    Launch disposition: {launch_config.get('launchDisposition', 'UNKNOWN')}")
                    print(f"    Target instance type: {launch_config.get('targetInstanceTypeRightSizingMethod', 'UNKNOWN')}")
                except Exception as e:
                    print(f"    ⚠ Could not get launch config: {e}")
                    
    except Exception as e:
        print(f"✗ Failed to describe source servers: {e}")
        return False
    
    print_section("STEP 2: Start Recovery Job")
    
    try:
        source_servers = [{'sourceServerID': sid} for sid in SOURCE_SERVER_IDS]
        
        print(f"Calling drs.start_recovery():")
        print(f"  sourceServers: {source_servers}")
        print(f"  isDrill: {IS_DRILL}")
        
        response = drs.start_recovery(
            sourceServers=source_servers,
            isDrill=IS_DRILL
        )
        
        job = response.get('job', {})
        job_id = job.get('jobID')
        
        print(f"\n✓ Job created: {job_id}")
        print(f"  Status: {job.get('status')}")
        print(f"  Type: {job.get('type')}")
        
        participating_servers = job.get('participatingServers', [])
        print(f"  Participating servers: {len(participating_servers)}")
        
        for ps in participating_servers:
            print(f"    - {ps.get('sourceServerID')}: {ps.get('launchStatus', 'UNKNOWN')}")
            
    except Exception as e:
        print(f"✗ Failed to start recovery: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print_section("STEP 3: Poll Job Status")
    
    max_polls = 60  # 10 minutes
    poll_interval = 10
    
    for i in range(max_polls):
        try:
            time.sleep(poll_interval)
            
            response = drs.describe_jobs(filters={'jobIDs': [job_id]})
            jobs = response.get('items', [])
            
            if not jobs:
                print(f"✗ Job {job_id} not found")
                return False
            
            job = jobs[0]
            job_status = job.get('status')
            
            print(f"\nPoll {i+1}/{max_polls} - Job Status: {job_status}")
            
            participating_servers = job.get('participatingServers', [])
            
            for ps in participating_servers:
                sid = ps.get('sourceServerID')
                launch_status = ps.get('launchStatus', 'UNKNOWN')
                recovery_instance_id = ps.get('recoveryInstanceID', 'None')
                
                print(f"  {sid}:")
                print(f"    Launch Status: {launch_status}")
                print(f"    Recovery Instance ID: {recovery_instance_id}")
                
                # Check if EC2 instance exists
                if recovery_instance_id and recovery_instance_id != 'None':
                    try:
                        ec2_response = ec2.describe_instances(InstanceIds=[recovery_instance_id])
                        if ec2_response['Reservations']:
                            instance = ec2_response['Reservations'][0]['Instances'][0]
                            ec2_state = instance['State']['Name']
                            print(f"    EC2 State: {ec2_state}")
                            
                            # Check tags
                            tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
                            has_drs_tag = 'AWSElasticDisasterRecoveryManaged' in tags
                            print(f"    Has DRS Tag: {has_drs_tag}")
                    except Exception as e:
                        print(f"    ⚠ Could not describe EC2 instance: {e}")
            
            # Check completion
            if job_status == 'COMPLETED':
                print(f"\n✓ Job completed successfully")
                break
            elif job_status in ['FAILED', 'TERMINATED']:
                print(f"\n✗ Job failed with status: {job_status}")
                return False
                
        except Exception as e:
            print(f"✗ Error polling job: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print_section("STEP 4: Verify Recovery Instances")
    
    try:
        response = drs.describe_recovery_instances()
        recovery_instances = response.get('items', [])
        
        print(f"Found {len(recovery_instances)} recovery instances")
        
        for ri in recovery_instances:
            sid = ri.get('sourceServerID')
            if sid in SOURCE_SERVER_IDS:
                ec2_id = ri.get('ec2InstanceID')
                state = ri.get('ec2InstanceState')
                
                print(f"\n  {sid}:")
                print(f"    EC2 Instance: {ec2_id}")
                print(f"    State: {state}")
                print(f"    Recovery Instance ID: {ri.get('recoveryInstanceID')}")
                
                if not ec2_id:
                    print(f"    ✗ NO EC2 INSTANCE CREATED")
                    return False
                else:
                    print(f"    ✓ EC2 instance exists")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to describe recovery instances: {e}")
        return False

if __name__ == '__main__':
    print_section("DRS DRILL TRACE TEST")
    print(f"Region: {REGION}")
    print(f"Source Servers: {SOURCE_SERVER_IDS}")
    print(f"Drill Mode: {IS_DRILL}")
    
    success = test_drs_recovery()
    
    print_section("TEST RESULT")
    if success:
        print("✓ TEST PASSED - Recovery instances created successfully")
        sys.exit(0)
    else:
        print("✗ TEST FAILED - No recovery instances created")
        sys.exit(1)
