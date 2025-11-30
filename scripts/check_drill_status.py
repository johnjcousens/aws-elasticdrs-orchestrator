#!/usr/bin/env python3
import boto3
import json
from datetime import datetime

def check_status(job_id):
    """Quick status check for DRS job"""
    
    drs_client = boto3.client('drs', region_name='us-east-1')
    
    print(f"📊 Quick Status Check: {job_id}")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Get job status
        response = drs_client.describe_jobs(
            filters={'jobIDs': [job_id]}
        )
        
        if not response.get('items'):
            print(f"❌ Job {job_id} not found")
            return
        
        job = response['items'][0]
        
        print(f"Job Status: {job['status']}")
        print(f"Type: {'Drill' if job.get('isDrill') else 'Recovery'}")
        print(f"Created: {job.get('creationDateTime', 'Unknown')}")
        
        if job.get('endDateTime'):
            print(f"Ended: {job['endDateTime']}")
        
        print(f"\nParticipating Servers:")
        if 'participatingServers' in job:
            for server in job['participatingServers']:
                server_id = server['sourceServerID']
                launch_status = server.get('launchStatus', 'UNKNOWN')
                recovery_instance = server.get('recoveryInstanceID', 'None')
                
                print(f"  • {server_id}")
                print(f"    Launch Status: {launch_status}")
                print(f"    Recovery Instance: {recovery_instance}")
        else:
            print("  No participating servers found")
        
        # Check recovery instances
        print(f"\n📋 All Recovery Instances:")
        instances = drs_client.describe_recovery_instances()
        
        if instances.get('items'):
            for instance in instances['items']:
                print(f"  • EC2 Instance: {instance.get('ec2InstanceID', 'None')}")
                print(f"    State: {instance.get('ec2InstanceState', 'Unknown')}")
                print(f"    Job ID: {instance.get('jobID', 'Unknown')}")
                print(f"    Source Server: {instance.get('sourceServerID', 'Unknown')}")
        else:
            print("  ⚠️ No recovery instances found yet")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 check_drill_status.py <job-id>")
        sys.exit(1)
    
    job_id = sys.argv[1]
    check_status(job_id)
