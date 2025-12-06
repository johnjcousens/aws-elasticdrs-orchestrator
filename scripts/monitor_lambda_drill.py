#!/usr/bin/env python3
"""
Monitor Lambda drill execution and check for EC2 instance creation
"""
import boto3
import time
import sys

def monitor_execution(execution_id, plan_id, max_wait_minutes=10):
    """Monitor execution until completion or timeout"""
    
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    drs = boto3.client('drs', region_name='us-east-1')
    ec2 = boto3.client('ec2', region_name='us-east-1')
    
    print(f"🔍 Monitoring execution: {execution_id}")
    print("=" * 60)
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    job_id = None
    source_server_id = None
    
    while (time.time() - start_time) < max_wait_seconds:
        try:
            # Get execution status
            response = dynamodb.get_item(
                TableName='drs-orchestration-execution-history-test',
                Key={
                    'ExecutionId': {'S': execution_id},
                    'PlanId': {'S': plan_id}
                }
            )
            
            if 'Item' not in response:
                print("❌ Execution not found")
                return False
            
            item = response['Item']
            status = item.get('Status', {}).get('S', 'UNKNOWN')
            waves = item.get('Waves', {}).get('L', [])
            
            if waves:
                wave = waves[0].get('M', {})
                wave_status = wave.get('Status', {}).get('S', 'UNKNOWN')
                job_id = wave.get('JobId', {}).get('S')
                servers = wave.get('Servers', {}).get('L', [])
                if servers:
                    source_server_id = servers[0].get('M', {}).get('SourceServerId', {}).get('S')
                
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed}s] Execution: {status}, Wave: {wave_status}, Job: {job_id or 'N/A'}")
                
                # Check if job completed
                if job_id and wave_status in ['COMPLETED', 'FAILED']:
                    print(f"\n✅ Wave {wave_status}!")
                    
                    # Check for EC2 instances
                    if source_server_id:
                        print(f"\n🔍 Checking for EC2 instances (source: {source_server_id})...")
                        instances = ec2.describe_instances(
                            Filters=[
                                {'Name': 'tag:AWSElasticDisasterRecoverySourceServerID', 'Values': [source_server_id]},
                                {'Name': 'instance-state-name', 'Values': ['pending', 'running']}
                            ]
                        )
                        
                        if instances['Reservations']:
                            for reservation in instances['Reservations']:
                                for instance in reservation['Instances']:
                                    print(f"   ✅ Instance: {instance['InstanceId']}")
                                    print(f"      State: {instance['State']['Name']}")
                                    print(f"      Launch Time: {instance['LaunchTime']}")
                                    print(f"      Private IP: {instance.get('PrivateIpAddress', 'N/A')}")
                            return True
                        else:
                            print("   ❌ No EC2 instances found")
                            return False
                    
                    return wave_status == 'COMPLETED'
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        
        time.sleep(15)
    
    print(f"\n⏱️ Timeout after {max_wait_minutes} minutes")
    return False

if __name__ == "__main__":
    execution_id = sys.argv[1] if len(sys.argv) > 1 else "e11a2dbc-5279-4829-b23c-2d4862ca8c68"
    plan_id = sys.argv[2] if len(sys.argv) > 2 else "ba8b28e2-7568-4c03-bff0-9f289262c1a6"
    
    success = monitor_execution(execution_id, plan_id)
    sys.exit(0 if success else 1)
