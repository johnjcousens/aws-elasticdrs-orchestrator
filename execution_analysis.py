#!/usr/bin/env python3
"""
Comprehensive analysis of execution 7b3e357a-dc1a-4f04-9ab8-d3a6b1a584ad
"""

import boto3
import json
from datetime import datetime

def analyze_execution():
    execution_id = "7b3e357a-dc1a-4f04-9ab8-d3a6b1a584ad"
    plan_id = "b70ba3d2-64a5-4e4e-a71a-5252b5f53d8a"
    
    print(f"🔍 COMPREHENSIVE ANALYSIS")
    print(f"Execution ID: {execution_id}")
    print(f"Plan ID: {plan_id}")
    print("=" * 60)
    
    # Get execution details
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('aws-drs-orchestrator-fresh-execution-history-dev')
    
    response = table.get_item(Key={'ExecutionId': execution_id, 'PlanId': plan_id})
    execution = response['Item']
    
    print(f"📊 EXECUTION STATUS:")
    print(f"  Status: {execution['Status']}")
    print(f"  Execution Type: {execution['ExecutionType']}")
    print(f"  Plan Name: {execution['PlanName']}")
    print(f"  DRS Region: {execution['DrsRegion']}")
    print(f"  Total Waves: {execution['TotalWaves']}")
    print(f"  Paused Before Wave: {execution.get('PausedBeforeWave', 'N/A')}")
    
    # Convert timestamps
    start_time = datetime.fromtimestamp(int(execution['StartTime']))
    last_polled = datetime.fromtimestamp(int(execution['LastPolledTime']))
    
    print(f"  Start Time: {start_time}")
    print(f"  Last Polled: {last_polled}")
    
    # Analyze waves
    print(f"\n🌊 WAVE ANALYSIS:")
    waves = execution['Waves']
    
    for i, wave in enumerate(waves):
        # Handle both DynamoDB format and Python dict format
        if isinstance(wave, dict) and 'M' in wave:
            wave_data = wave['M']
            wave_num = wave_data['WaveNumber']['N']
            wave_name = wave_data['WaveName']['S']
            status = wave_data['Status']['S']
            job_id = wave_data.get('JobId', {}).get('S', 'N/A')
            status_msg = wave_data.get('StatusMessage', {}).get('S', 'N/A')
            server_ids = [s['S'] for s in wave_data.get('ServerIds', {}).get('L', [])]
        else:
            # Direct Python dict format
            wave_data = wave
            wave_num = wave_data.get('WaveNumber', i)
            wave_name = wave_data.get('WaveName', f'Wave {i}')
            status = wave_data.get('Status', 'N/A')
            job_id = wave_data.get('JobId', 'N/A')
            status_msg = wave_data.get('StatusMessage', 'N/A')
            server_ids = wave_data.get('ServerIds', [])
        
        print(f"  Wave {wave_num}: {wave_name}")
        print(f"    Status: {status}")
        print(f"    Job ID: {job_id}")
        print(f"    Status Message: {status_msg}")
        
        if server_ids:
            print(f"    Servers: {len(server_ids)} servers")
            for server_id in server_ids:
                print(f"      - {server_id}")
    
    # Check DRS job status
    print(f"\n🔧 DRS JOB ANALYSIS:")
    drs_job_id = execution['DrsJobId']
    drs_region = execution['DrsRegion']
    
    print(f"  DRS Job ID: {drs_job_id}")
    print(f"  DRS Region: {drs_region}")
    
    # Try to get DRS job details
    try:
        drs_client = boto3.client('drs', region_name=drs_region)
        jobs_response = drs_client.describe_jobs(filters={'jobIDs': [drs_job_id]})
        
        if jobs_response['items']:
            job = jobs_response['items'][0]
            print(f"  ✅ DRS Job Found:")
            print(f"    Status: {job['status']}")
            print(f"    Type: {job['type']}")
            print(f"    Creation Time: {job['creationDateTime']}")
            print(f"    End Time: {job.get('endDateTime', 'N/A')}")
            
            if 'participatingServers' in job:
                print(f"    Participating Servers: {len(job['participatingServers'])}")
                for server in job['participatingServers']:
                    server_id = server['sourceServerID']
                    launch_status = server.get('launchStatus', 'N/A')
                    print(f"      {server_id}: {launch_status}")
        else:
            print(f"  ❌ DRS Job Not Found")
            print(f"    This explains the 'Job not found' status message")
            
    except Exception as e:
        print(f"  ❌ Error checking DRS job: {e}")
    
    # Check Step Functions execution
    print(f"\n⚙️ STEP FUNCTIONS ANALYSIS:")
    sf_arn = execution['StateMachineArn']
    task_token = execution.get('TaskToken', 'N/A')
    
    print(f"  State Machine ARN: {sf_arn}")
    print(f"  Task Token: {'Present' if task_token != 'N/A' else 'Missing'}")
    
    try:
        sf_client = boto3.client('stepfunctions')
        sf_response = sf_client.describe_execution(executionArn=sf_arn)
        
        print(f"  ✅ Step Functions Execution Found:")
        print(f"    Status: {sf_response['status']}")
        print(f"    Start Date: {sf_response['startDate']}")
        print(f"    Stop Date: {sf_response.get('stopDate', 'N/A')}")
        
    except Exception as e:
        print(f"  ❌ Error checking Step Functions: {e}")
    
    # Analysis and recommendations
    print(f"\n🎯 ANALYSIS & RECOMMENDATIONS:")
    print("=" * 40)
    
    status = execution['Status']
    
    if status == 'PAUSED':
        paused_before = execution.get('PausedBeforeWave', 0)
        print(f"✅ FINDING: Execution is correctly PAUSED before wave {paused_before}")
        print(f"💡 This is expected behavior - execution is waiting for manual resume")
        print(f"🔧 ACTION: Use resume API to continue execution")
        
        # Check if first wave has issues
        if waves and waves[0]['M']['Status']['S'] == 'UNKNOWN':
            print(f"\n⚠️ ISSUE: First wave has UNKNOWN status with 'Job not found'")
            print(f"💡 This suggests the DRS job completed but status wasn't updated")
            print(f"🔧 RECOMMENDATION: Call reconcile function to update wave status")
    
    print(f"\n🧪 TESTING RECOMMENDATIONS:")
    print(f"1. Test resume functionality:")
    print(f"   curl -X POST /executions/{execution_id}/resume")
    print(f"2. Test reconcile function:")
    print(f"   curl -X GET /executions/{execution_id}")
    print(f"3. Check Step Functions execution status")
    print(f"4. Verify DRS permissions for cross-region access")

if __name__ == "__main__":
    analyze_execution()