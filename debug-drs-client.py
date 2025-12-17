#!/usr/bin/env python3

import boto3
import json

def create_drs_client(region: str, account_context=None):
    """Same function as in Lambda"""
    try:
        # If no account context provided, use current account
        if not account_context or not account_context.get('AccountId'):
            print(f"Creating DRS client for current account in region {region}")
            return boto3.client('drs', region_name=region)
        
        account_id = account_context.get('AccountId')
        assume_role_name = account_context.get('AssumeRoleName')
        
        if not assume_role_name:
            print(f"No AssumeRoleName provided for account {account_id}, using current account")
            return boto3.client('drs', region_name=region)
        
        print(f"Creating cross-account DRS client for account {account_id} using role {assume_role_name}")
        
        # Assume role in target account
        sts_client = boto3.client('sts', region_name=region)
        role_arn = f"arn:aws:iam::{account_id}:role/{assume_role_name}"
        session_name = f"drs-orchestration-{int(time.time())}"
        
        print(f"Assuming role: {role_arn}")
        
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
            DurationSeconds=3600  # 1 hour
        )
        
        credentials = assumed_role['Credentials']
        
        # Create DRS client with assumed role credentials
        drs_client = boto3.client(
            'drs',
            region_name=region,
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
        
        print(f"Successfully created cross-account DRS client for account {account_id}")
        return drs_client
        
    except Exception as e:
        print(f"Error creating DRS client for account {account_context}: {e}")
        # Fallback to current account client
        print("Falling back to current account DRS client")
        return boto3.client('drs', region_name=region)

def test_drs_client():
    """Test the DRS client creation and job log items call"""
    region = "us-west-2"
    job_id = "drsjob-5fd4a038aa391e2ef"
    account_context = {}  # Empty like in the execution
    
    print(f"Testing DRS client creation for region: {region}")
    print(f"Job ID: {job_id}")
    print(f"Account context: {account_context}")
    
    try:
        # Create DRS client same way as Lambda
        drs_client = create_drs_client(region, account_context)
        
        print(f"DRS client created successfully")
        print(f"Client region: {drs_client.meta.region_name}")
        
        # Test describe_job_log_items
        print(f"Calling describe_job_log_items for job: {job_id}")
        response = drs_client.describe_job_log_items(jobID=job_id)
        
        print(f"Success! Found {len(response.get('items', []))} log items")
        for item in response.get('items', [])[:3]:  # Show first 3
            print(f"  - {item.get('event')} at {item.get('logDateTime')}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_drs_client()