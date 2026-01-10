#!/usr/bin/env python3
"""
Trigger reconcile function for execution 7b3e357a-dc1a-4f04-9ab8-d3a6b1a584ad
This will update stale wave and server statuses from DRS job results.
"""

import boto3
import json
import sys

def trigger_reconcile():
    """Trigger reconcile function by calling the execution details API"""
    
    # Get authentication token
    cognito = boto3.client('cognito-idp', region_name='us-east-1')
    
    try:
        response = cognito.admin_initiate_auth(
            UserPoolId='us-east-1_o3tXVi5h3',
            ClientId='5k6a5vbsmvgbvnb5a1iqs598oq',
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': 'testuser@example.com',
                'PASSWORD': 'TestPassword123!'
            }
        )
        
        token = response['AuthenticationResult']['IdToken']
        print("✅ Authentication successful")
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    
    # Call execution details API to trigger reconcile function
    import requests
    
    execution_id = "7b3e357a-dc1a-4f04-9ab8-d3a6b1a584ad"
    api_url = f"https://28e48oiajf.execute-api.us-east-1.amazonaws.com/dev/executions/{execution_id}"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"🔄 Calling API to trigger reconcile function...")
        print(f"   URL: {api_url}")
        
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API call successful")
            print(f"   Execution Status: {data.get('status', 'unknown')}")
            
            # Check wave statuses
            waves = data.get('waves', [])
            print(f"   Waves: {len(waves)} total")
            for i, wave in enumerate(waves):
                wave_status = wave.get('status', 'unknown')
                servers = wave.get('servers', [])
                server_statuses = [s.get('status', 'unknown') for s in servers]
                print(f"     Wave {i}: {wave_status} (servers: {server_statuses})")
            
            return True
            
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API call error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Triggering reconcile function for stuck execution...")
    success = trigger_reconcile()
    
    if success:
        print("\n✅ Reconcile function triggered successfully!")
        print("   The API call should have updated stale wave and server statuses.")
        print("   Check the frontend to see if data now displays correctly.")
    else:
        print("\n❌ Failed to trigger reconcile function")
        sys.exit(1)