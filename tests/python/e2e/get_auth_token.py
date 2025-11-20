#!/usr/bin/env python3
"""
Helper script to get ID token for E2E API testing.
Uses Cognito credentials to authenticate and retrieve ID token.
"""
import os
import json
import boto3
from botocore.exceptions import ClientError

# Cognito Configuration (from .env.test or CloudFormation outputs)
USER_POOL_ID = os.getenv('USER_POOL_ID', 'us-east-1_tj03fVI31')
CLIENT_ID = os.getenv('CLIENT_ID', '7l8f5q9llq1qjbbte3u8f6pfbh')
USERNAME = os.getenv('TEST_USERNAME', '***REMOVED***')
PASSWORD = os.getenv('TEST_PASSWORD', 'IiG2b1o+D$')


def get_id_token():
    """Authenticate with Cognito and get ID token."""
    try:
        client = boto3.client('cognito-idp', region_name='us-east-1')
        
        response = client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': USERNAME,
                'PASSWORD': PASSWORD
            }
        )
        
        id_token = response['AuthenticationResult']['IdToken']
        return id_token
        
    except ClientError as e:
        print(f"❌ Authentication failed: {e}")
        return None


if __name__ == "__main__":
    print("Getting ID token for E2E testing...")
    token = get_id_token()
    
    if token:
        print(f"✅ ID Token retrieved successfully")
        print(f"\nSet environment variable:")
        print(f"export ID_TOKEN='{token}'")
        print(f"\nOr run tests directly:")
        print(f"ID_TOKEN='{token}' python tests/python/e2e/test_recovery_plan_bugs.py")
    else:
        print("❌ Failed to get ID token")
        exit(1)
