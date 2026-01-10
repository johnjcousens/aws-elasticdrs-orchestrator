#!/usr/bin/env python3
"""
Fix Stuck Execution Script

Manually triggers the reconcile function for execution 7b3e357a-dc1a-4f04-9ab8-d3a6b1a584ad
to update server statuses from "UNKNOWN" to "LAUNCHED" based on actual DRS job results.
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

def call_api_endpoint(token):
    """Call the execution details API endpoint to trigger reconcile function."""
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
            data = response.json()
            print("✅ Successfully triggered reconcile function")
            print(f"Execution Status: {data.get('status', 'unknown')}")
            
            # Check wave statuses
            waves = data.get('waveExecutions', [])
            print(f"Total Waves: {len(waves)}")
            for wave in waves:
                wave_status = wave.get('status', 'unknown')
                job_id = wave.get('jobId', 'no-job-id')
                server_count = len(wave.get('serverExecutions', []))
                print(f"  Wave {wave.get('waveNumber', '?')}: {wave_status} (Job: {job_id}, Servers: {server_count})")
                
                # Check server statuses
                for server in wave.get('serverExecutions', []):
                    server_id = server.get('serverId', 'unknown')
                    server_status = server.get('launchStatus') or server.get('status', 'unknown')
                    recovery_instance = server.get('recoveredInstanceId', 'none')
                    print(f"    Server {server_id}: {server_status} (Instance: {recovery_instance})")
            
            return True
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        return False

def main():
    """Main function to fix stuck execution."""
    print(f"🔧 Fixing stuck execution: {EXECUTION_ID}")
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
    
    # Call API endpoint to trigger reconcile function
    print("2. Calling execution details API to trigger reconcile function...")
    success = call_api_endpoint(token)
    
    if success:
        print()
        print("✅ Reconcile function triggered successfully!")
        print("The execution status should now be updated based on actual DRS job results.")
        print()
        print("Next steps:")
        print("1. Check the frontend to verify execution shows correct status")
        print("2. Verify servers show 'LAUNCHED' status instead of 'UNKNOWN'")
        print("3. Test resume functionality if needed")
    else:
        print()
        print("❌ Failed to trigger reconcile function")
        print("Check the API Gateway logs for more details")
        sys.exit(1)

if __name__ == "__main__":
    main()