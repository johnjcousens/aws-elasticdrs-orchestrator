#!/usr/bin/env python3
"""
Detailed Execution Diagnostic Script

Provides comprehensive analysis of execution 7b3e357a-dc1a-4f04-9ab8-d3a6b1a584ad
to understand the current state and identify any issues.
"""

import boto3
import json
import sys
from datetime import datetime

# Configuration
EXECUTION_ID = "7b3e357a-dc1a-4f04-9ab8-d3a6b1a584ad"
REGION = "us-east-1"
API_GATEWAY_URL = "https://28e48oiajf.execute-api.us-east-1.amazonaws.com/dev"
USER_POOL_ID = "us-east-1_o3tXVi5h3"
CLIENT_ID = "5k6a5vbsmvgbvnb5a1iqs598oq"

def get_auth_token():
    """Get JWT token for API authentication."""
    try:
        cognito = boto3.client('cognito-idp', region_name=REGION)
        
        response = cognito.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': '***REMOVED***',
                'PASSWORD': '***REMOVED***'
            }
        )
        
        return response['AuthenticationResult']['IdToken']
    except Exception as e:
        print(f"Error getting auth token: {e}")
        return None

def get_execution_details(token):
    """Get detailed execution information."""
    import requests
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    url = f"{API_GATEWAY_URL}/executions/{EXECUTION_ID}"
    
    try:
        print(f"Calling API endpoint: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        return None

def analyze_execution_data(data):
    """Analyze and display execution data in detail."""
    print("=" * 80)
    print("EXECUTION ANALYSIS")
    print("=" * 80)
    
    # Basic execution info
    print(f"Execution ID: {data.get('executionId', 'unknown')}")
    print(f"Status: {data.get('status', 'unknown')}")
    print(f"Recovery Plan: {data.get('recoveryPlanName', 'unknown')} (ID: {data.get('recoveryPlanId', 'unknown')})")
    print(f"Protection Group: {data.get('protectionGroupName', 'unknown')} (ID: {data.get('protectionGroupId', 'unknown')})")
    print(f"Executed By: {data.get('executedBy', 'unknown')}")
    print(f"Start Time: {data.get('startTime', 'unknown')}")
    print(f"End Time: {data.get('endTime', 'unknown')}")
    print(f"Current Wave: {data.get('currentWave', 'unknown')}")
    print(f"Total Waves: {data.get('totalWaves', 'unknown')}")
    print(f"Paused Before Wave: {data.get('pausedBeforeWave', 'none')}")
    print()
    
    # Error information
    if data.get('error'):
        print("ERROR INFORMATION:")
        error = data['error']
        print(f"  Code: {error.get('code', 'unknown')}")
        print(f"  Message: {error.get('message', 'unknown')}")
        if error.get('details'):
            print(f"  Details: {json.dumps(error['details'], indent=2)}")
        print()
    
    # Wave executions
    waves = data.get('waveExecutions', [])
    print(f"WAVE EXECUTIONS ({len(waves)} waves):")
    if not waves:
        print("  No wave executions found")
    else:
        for i, wave in enumerate(waves):
            print(f"  Wave {i} (Number: {wave.get('waveNumber', 'unknown')}):")
            print(f"    Name: {wave.get('waveName', 'unknown')}")
            print(f"    Status: {wave.get('status', 'unknown')}")
            print(f"    Job ID: {wave.get('jobId', 'none')}")
            print(f"    Start Time: {wave.get('startTime', 'unknown')}")
            print(f"    End Time: {wave.get('endTime', 'unknown')}")
            
            # Server executions
            servers = wave.get('serverExecutions', [])
            print(f"    Servers ({len(servers)}):")
            if not servers:
                print("      No servers found")
            else:
                for server in servers:
                    server_id = server.get('serverId', 'unknown')
                    server_name = server.get('serverName', server.get('hostname', 'unknown'))
                    status = server.get('launchStatus') or server.get('status', 'unknown')
                    instance_id = server.get('recoveredInstanceId', 'none')
                    print(f"      {server_id} ({server_name}): {status} -> {instance_id}")
            print()
    
    # Metadata
    if data.get('metadata'):
        print("METADATA:")
        print(json.dumps(data['metadata'], indent=2))
        print()
    
    # Raw data (truncated)
    print("RAW DATA KEYS:")
    print(f"  Top-level keys: {list(data.keys())}")
    print()

def main():
    """Main diagnostic function."""
    print(f"🔍 Detailed Execution Diagnostic: {EXECUTION_ID}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Get authentication token
    print("1. Getting authentication token...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to get authentication token")
        sys.exit(1)
    print("✅ Got authentication token")
    print()
    
    # Get execution details
    print("2. Fetching execution details...")
    data = get_execution_details(token)
    
    if data:
        print("✅ Got execution data")
        print()
        analyze_execution_data(data)
    else:
        print("❌ Failed to get execution data")
        sys.exit(1)

if __name__ == "__main__":
    main()