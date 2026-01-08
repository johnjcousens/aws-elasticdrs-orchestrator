#!/usr/bin/env python3
"""
Cancel a stuck execution via API call
"""

import requests
import json

# Stack configuration
API_ENDPOINT = "https://4btsule96b.execute-api.us-east-1.amazonaws.com/dev"
EXECUTION_ID = "ac0bc68e-31e1-4530-8f3e-216fe1600dd3"

# Get JWT token (using the shared Cognito credentials)
def get_jwt_token():
    import boto3
    
    cognito = boto3.client('cognito-idp', region_name='us-east-1')
    
    try:
        response = cognito.admin_initiate_auth(
            UserPoolId='us-east-1_7ClH0e1NS',
            ClientId='6fepnj59rp7qup2k3n6uda5p19',
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': 'testuser@example.com',
                'PASSWORD': 'TestPassword123!'
            }
        )
        return response['AuthenticationResult']['IdToken']
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

def cancel_execution(execution_id):
    """Cancel the execution via API"""
    token = get_jwt_token()
    if not token:
        print("Failed to get authentication token")
        return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Cancel the execution
    url = f"{API_ENDPOINT}/executions/{execution_id}/cancel"
    
    try:
        print(f"Cancelling execution {execution_id}...")
        response = requests.post(url, headers=headers)
        
        if response.status_code == 200:
            print("✅ Execution cancelled successfully")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Failed to cancel execution: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error cancelling execution: {e}")
        return False

if __name__ == "__main__":
    print(f"🛑 Cancelling stuck execution: {EXECUTION_ID}")
    success = cancel_execution(EXECUTION_ID)
    
    if success:
        print("✅ Execution cancelled. You can now start a new execution once the deployment completes.")
    else:
        print("❌ Failed to cancel execution. You may need to wait for it to timeout or check the API.")