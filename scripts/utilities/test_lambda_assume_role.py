#!/usr/bin/env python3
"""
Test if Lambda can assume cross-account role directly.
"""

import json
import boto3

def test_lambda_assume_role():
    """Test Lambda's ability to assume cross-account role."""
    
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    
    # Create a simple test payload that just tries to assume the role
    test_payload = {
        "httpMethod": "POST",
        "path": "/test-assume-role",
        "body": json.dumps({
            "targetAccountId": "851725249649",
            "assumeRoleName": "DRSOrchestrationRole",
            "externalId": "drs-orchestration-cross-account"
        })
    }
    
    print("Testing Lambda's ability to assume cross-account role...")
    print(f"Target: arn:aws:iam::851725249649:role/DRSOrchestrationRole")
    print()
    
    try:
        response = lambda_client.invoke(
            FunctionName='hrp-drs-tech-adapter-data-management-handler-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(response['Payload'].read())
        print("Lambda Response:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error invoking Lambda: {e}")

if __name__ == "__main__":
    test_lambda_assume_role()
