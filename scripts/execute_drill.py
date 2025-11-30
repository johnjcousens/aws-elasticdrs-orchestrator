#!/usr/bin/env python3
import boto3
import json
from datetime import datetime

def execute_drill_now():
    """Execute the drill immediately"""
    
    print("🚀 Executing DRS Drill for EC2AMAZ-3B0B3UD")
    print("=" * 50)
    
    # Initialize DRS client
    drs_client = boto3.client('drs', region_name='us-east-1')
    
    try:
        # Execute the API call
        print("📡 Making start_recovery API call...")
        
        response = drs_client.start_recovery(
            isDrill=True,
            sourceServers=[
                {
                    'sourceServerID': 's-3b9401c1cd270a7a8'
                }
            ],
            tags={
                'Environment': 'Drill',
                'Purpose': 'Python-Direct-Execution',
                'Server': 'EC2AMAZ-3B0B3UD',
                'Timestamp': datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
                'ExecutedBy': 'Cline-Agent'
            }
        )
        
        # Extract response details
        job_id = response['job']['jobID']
        job_arn = response['job']['arn']
        status = response['job']['status']
        creation_time = response['job']['creationDateTime']
        
        print("\n✅ SUCCESS! Drill initiated successfully!")
        print(f"   Job ID: {job_id}")
        print(f"   Job ARN: {job_arn}")
        print(f"   Status: {status}")
        print(f"   Created: {creation_time}")
        
        # Show participating servers
        if 'participatingServers' in response['job']:
            print(f"   Participating Servers:")
            for server in response['job']['participatingServers']:
                print(f"     - {server['sourceServerID']}: {server.get('launchStatus', 'PENDING')}")
        
        return job_id
        
    except Exception as e:
        print(f"\n❌ FAILED! Error executing drill:")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        return None

if __name__ == "__main__":
    job_id = execute_drill_now()
    
    if job_id:
        print(f"\n📊 Monitor the drill progress with:")
        print(f"   aws drs describe-jobs --region us-east-1 --job-ids {job_id}")
        print(f"\n🔍 Check recovery instances with:")
        print(f"   aws drs describe-recovery-instances --region us-east-1")
