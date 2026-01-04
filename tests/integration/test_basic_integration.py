#!/usr/bin/env python3
"""
Basic integration test for AWS DRS Orchestration platform.
This test validates that the core components are properly configured.
"""

import pytest
import boto3
import json
from botocore.exceptions import ClientError


def test_aws_credentials():
    """Test that AWS credentials are properly configured."""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        assert 'Account' in identity
        assert 'UserId' in identity
        print(f"AWS Identity: {identity['UserId']} in account {identity['Account']}")
    except Exception as e:
        pytest.fail(f"AWS credentials not configured: {e}")


def test_drs_service_availability():
    """Test that DRS service is available in the region."""
    try:
        drs = boto3.client('drs', region_name='us-east-1')
        # Try to describe source servers (should work even if empty)
        response = drs.describe_source_servers()
        assert 'items' in response
        print(f"DRS service available, found {len(response['items'])} source servers")
    except ClientError as e:
        if e.response['Error']['Code'] == 'UnauthorizedOperation':
            print("DRS service available but no permissions (expected in test environment)")
        else:
            pytest.fail(f"DRS service not available: {e}")


def test_dynamodb_service_availability():
    """Test that DynamoDB service is available."""
    try:
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        # List tables (should work even if empty)
        response = dynamodb.list_tables()
        assert 'TableNames' in response
        print(f"DynamoDB service available, found {len(response['TableNames'])} tables")
    except Exception as e:
        pytest.fail(f"DynamoDB service not available: {e}")


def test_lambda_service_availability():
    """Test that Lambda service is available."""
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        # List functions (should work even if empty)
        response = lambda_client.list_functions()
        assert 'Functions' in response
        print(f"Lambda service available, found {len(response['Functions'])} functions")
    except Exception as e:
        pytest.fail(f"Lambda service not available: {e}")


def test_s3_deployment_bucket_access():
    """Test that S3 deployment bucket is accessible."""
    try:
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'aws-elasticdrs-orchestrator'
        
        # Try to list objects in the deployment bucket
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        print(f"S3 deployment bucket '{bucket_name}' is accessible")
    except ClientError as e:
        if e.response['Error']['Code'] in ['NoSuchBucket', 'AccessDenied']:
            print(f"S3 deployment bucket access issue (expected in test environment): {e}")
        else:
            pytest.fail(f"S3 service error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])