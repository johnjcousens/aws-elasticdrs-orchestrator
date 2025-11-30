#!/usr/bin/env python3
import boto3
import json
import time
from datetime import datetime

def monitor_job(job_id, check_interval=30, max_checks=60):
    """Monitor DRS job progress"""
    
    drs_client = boto3.client('drs', region_name='us-east-1')
    ec2_client = boto3.client('ec2', region_name='us-east-1')
    
    print(f"🔍 Monitoring Job: {job_id}")
    print("=" * 50)
    
    checks = 0
    
    while checks < max_checks:
        checks += 1
        
        try:
            # Get job status
            response = drs_client.describe_jobs(
                filters={'jobIDs': [job_id]}
            )
            
            if not response.get('items'):
                print(f"❌ Job {job_id} not found")
                break
            
            job = response['items'][0]
            status = job['status']
            
            print(f"\n⏰ Check {checks} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"   Status: {status}")
            
            # Check participating servers
            if 'participatingServers' in job:
                for server in job['participatingServers']:
                    server_id = server['sourceServerID']
                    launch_status = server.get('launchStatus', 'UNKNOWN')
                    recovery_instance_id = server.get('recoveryInstanceID', 'None')
                    
                    print(f"   Server {server_id}:")
                    print(f"     Launch Status: {launch_status}")
                    print(f"     Recovery Instance: {recovery_instance_id}")
            
            # Check if job completed
            if status in ['COMPLETED', 'FAILED']:
                print(f"\n{'✅' if status == 'COMPLETED' else '❌'} Job {status}!")
                
                # Get recovery instances
                print("\n📋 Checking Recovery Instances...")
                instances = drs_client.describe_recovery_instances()
                
                if instances.get('items'):
                    for instance in instances['items']:
                        if instance.get('jobID') == job_id:
                            print(f"   Recovery Instance: {instance.get('ec2InstanceID', 'None')}")
                            print(f"   State: {instance.get('ec2InstanceState', 'Unknown')}")
                else:
                    print("   ⚠️ No recovery instances found")
                
                break
            
            # Wait before next check
            if checks < max_checks:
                print(f"   ⏳ Waiting {check_interval} seconds...")
                time.sleep(check_interval)
                
        except Exception as e:
            print(f"\n❌ Error monitoring job: {e}")
            break
    
    if checks >= max_checks:
        print(f"\n⏰ Timeout: Reached maximum {max_checks} checks")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 monitor_drill.py <job-id>")
        sys.exit(1)
    
    job_id = sys.argv[1]
    monitor_job(job_id)
