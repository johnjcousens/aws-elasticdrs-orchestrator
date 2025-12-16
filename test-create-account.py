#!/usr/bin/env python3
"""
Test script to create target account without cross-account role ARN
"""
import json
import boto3

def test_create_account():
    # Get the Lambda function name
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Test payload - current account without cross-account role ARN
    test_event = {
        'httpMethod': 'POST',
        'path': '/accounts/targets',
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'accountId': '438465159935',
            'accountName': 'Current Account Test',
            'stagingAccountId': '',
            'stagingAccountName': '',
            'crossAccountRoleArn': ''  # Empty - should be allowed
        })
    }
    
    try:
        print("Testing Lambda function directly...")
        print(f"Test payload: {json.dumps(test_event, indent=2)}")
        
        response = lambda_client.invoke(
            FunctionName='drsorchv4-api-handler-test',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"Lambda response: {json.dumps(result, indent=2)}")
        
        if result.get('statusCode') == 201:
            print("✅ SUCCESS: Account created successfully")
        else:
            print(f"❌ ERROR: {result}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

if __name__ == '__main__':
    test_create_account()