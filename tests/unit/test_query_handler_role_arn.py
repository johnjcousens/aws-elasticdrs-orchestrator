"""
Unit tests for query handler role ARN construction.

Tests the query handler's ability to construct role ARNs when not provided
and use explicit role ARNs when provided.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add lambda paths for imports
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "lambda" / "shared")
)
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "lambda" / "query-handler")
)

# Set environment variables before importing
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts-table"
os.environ["STAGING_ACCOUNTS_TABLE"] = "test-staging-accounts-table"

from index import handle_get_combined_capacity, handle_validate_staging_account


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table"""
    table = MagicMock()
    return table


@pytest.fixture
def mock_sts_client():
    """Mock STS client for role assumption"""
    client = MagicMock()
    client.assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "SessionToken": "token123",
            "Expiration": "2026-01-30T12:00:00Z",
        }
    }
    return client


@pytest.fixture
def mock_drs_client():
    """Mock DRS client"""
    client = MagicMock()
    client.describe_source_servers.return_value = {"items": []}
    return client


def test_validate_staging_account_constructs_arn_when_not_provided(
    mock_dynamodb_table, mock_sts_client, mock_drs_client
):
    """Test validation constructs ARN when roleArn not provided"""
    account_data = {
        "accountId": "123456789012",
        "accountName": "Test Account",
        "externalId": "test-external-id",
        "region": "us-east-1",
        # No roleArn provided
    }

    with patch("boto3.client") as mock_boto_client:
        mock_boto_client.return_value = mock_sts_client

        with patch("index.create_drs_client") as mock_create_drs:
            mock_create_drs.return_value = mock_drs_client

            result = handle_validate_staging_account(account_data)

            # Should construct ARN
            expected_arn = (
                "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
            )

            # Verify STS assume_role was called with constructed ARN
            mock_sts_client.assume_role.assert_called_once()
            call_args = mock_sts_client.assume_role.call_args
            assert call_args[1]["RoleArn"] == expected_arn
            assert call_args[1]["ExternalId"] == "test-external-id"


def test_validate_staging_account_uses_explicit_arn(
    mock_dynamodb_table, mock_sts_client, mock_drs_client
):
    """Test validation uses explicit roleArn when provided"""
    custom_arn = "arn:aws:iam::123456789012:role/CustomRole"
    account_data = {
        "accountId": "123456789012",
        "accountName": "Test Account",
        "externalId": "test-external-id",
        "region": "us-east-1",
        "roleArn": custom_arn,  # Explicit ARN provided
    }

    with patch("boto3.client") as mock_boto_client:
        mock_boto_client.return_value = mock_sts_client

        with patch("index.create_drs_client") as mock_create_drs:
            mock_create_drs.return_value = mock_drs_client

            result = handle_validate_staging_account(account_data)

            # Should use explicit ARN
            mock_sts_client.assume_role.assert_called_once()
            call_args = mock_sts_client.assume_role.call_args
            assert call_args[1]["RoleArn"] == custom_arn


def test_combined_capacity_constructs_arn_when_not_in_db(
    mock_dynamodb_table, mock_sts_client, mock_drs_client
):
    """Test combined capacity constructs ARN when not in DynamoDB"""
    # Mock target account without roleArn
    mock_dynamodb_table.get_item.return_value = {
        "Item": {
            "accountId": "123456789012",
            "accountName": "Test Account",
            "externalId": "test-external-id",
            # No roleArn in DynamoDB
        }
    }

    query_params = {"targetAccountId": "123456789012"}

    with patch("boto3.client") as mock_boto_client:
        mock_boto_client.return_value = mock_sts_client

        with patch("index.target_accounts_table", mock_dynamodb_table):
            with patch("index.create_drs_client") as mock_create_drs:
                mock_create_drs.return_value = mock_drs_client

                # Mock DRS describe_source_servers to return empty
                mock_drs_client.get_paginator.return_value.paginate.return_value = [
                    {"items": []}
                ]

                result = handle_get_combined_capacity(query_params)

                # Should construct ARN
                expected_arn = (
                    "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
                )

                # Verify STS assume_role was called with constructed ARN
                mock_sts_client.assume_role.assert_called()
                call_args = mock_sts_client.assume_role.call_args
                assert call_args[1]["RoleArn"] == expected_arn


def test_combined_capacity_uses_explicit_arn_from_db(
    mock_dynamodb_table, mock_sts_client, mock_drs_client
):
    """Test combined capacity uses explicit roleArn from DynamoDB"""
    custom_arn = "arn:aws:iam::123456789012:role/CustomRole"

    # Mock target account with explicit roleArn
    mock_dynamodb_table.get_item.return_value = {
        "Item": {
            "accountId": "123456789012",
            "accountName": "Test Account",
            "externalId": "test-external-id",
            "roleArn": custom_arn,  # Explicit ARN in DynamoDB
        }
    }

    query_params = {"targetAccountId": "123456789012"}

    with patch("boto3.client") as mock_boto_client:
        mock_boto_client.return_value = mock_sts_client

        with patch("index.target_accounts_table", mock_dynamodb_table):
            with patch("index.create_drs_client") as mock_create_drs:
                mock_create_drs.return_value = mock_drs_client

                # Mock DRS describe_source_servers to return empty
                mock_drs_client.get_paginator.return_value.paginate.return_value = [
                    {"items": []}
                ]

                result = handle_get_combined_capacity(query_params)

                # Should use explicit ARN
                mock_sts_client.assume_role.assert_called()
                call_args = mock_sts_client.assume_role.call_args
                assert call_args[1]["RoleArn"] == custom_arn


def test_validation_handles_missing_account():
    """Test validation handles missing account gracefully"""
    account_data = {
        "accountId": "999999999999",
        "accountName": "Missing Account",
        "externalId": "test-external-id",
        "region": "us-east-1",
    }

    with patch("boto3.client") as mock_boto_client:
        mock_sts = MagicMock()
        mock_sts.assume_role.side_effect = Exception(
            "No such role: DRSOrchestrationRole"
        )
        mock_boto_client.return_value = mock_sts

        result = handle_validate_staging_account(account_data)

        # Should return error response (500 for unexpected errors)
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert body["valid"] is False
        assert "error" in body


def test_capacity_query_with_explicit_role_arn():
    """
    Test capacity query with account that has explicit roleArn.
    
    Validates: Requirements 1.3, 2.3 (backward compatibility)
    Task: 11.1
    """
    custom_arn = "arn:aws:iam::123456789012:role/CustomDRSRole"
    
    # Mock target account with explicit roleArn
    mock_table = MagicMock()
    mock_table.get_item.return_value = {
        "Item": {
            "accountId": "123456789012",
            "accountName": "Test Account",
            "externalId": "test-external-id",
            "roleArn": custom_arn,  # Explicit ARN
            "stagingAccounts": []
        }
    }
    
    mock_sts = MagicMock()
    mock_sts.assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "SessionToken": "token123",
            "Expiration": "2026-01-30T12:00:00Z",
        }
    }
    
    mock_drs = MagicMock()
    mock_drs.get_paginator.return_value.paginate.return_value = [
        {"items": []}
    ]
    
    with patch("index.target_accounts_table", mock_table):
        with patch("boto3.client") as mock_boto_client:
            mock_boto_client.return_value = mock_sts
            
            with patch("index.create_drs_client") as mock_create_drs:
                mock_create_drs.return_value = mock_drs
                
                result = handle_get_combined_capacity(
                    {"targetAccountId": "123456789012"}
                )
                
                # Should succeed
                assert result["statusCode"] == 200
                
                # Verify STS assume_role was called with explicit ARN
                mock_sts.assume_role.assert_called()
                call_args = mock_sts.assume_role.call_args
                assert call_args[1]["RoleArn"] == custom_arn
                assert call_args[1]["ExternalId"] == "test-external-id"


def test_capacity_query_with_constructed_role_arn():
    """
    Test capacity query with account that needs constructed roleArn.
    
    Validates: Requirements 1.2, 2.2 (ARN construction)
    Task: 11.2
    """
    # Mock target account without roleArn
    mock_table = MagicMock()
    mock_table.get_item.return_value = {
        "Item": {
            "accountId": "987654321098",
            "accountName": "Test Account",
            "externalId": "test-external-id",
            # No roleArn - should be constructed
            "stagingAccounts": []
        }
    }
    
    mock_sts = MagicMock()
    mock_sts.assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "SessionToken": "token123",
            "Expiration": "2026-01-30T12:00:00Z",
        }
    }
    
    mock_drs = MagicMock()
    mock_drs.get_paginator.return_value.paginate.return_value = [
        {"items": []}
    ]
    
    with patch("index.target_accounts_table", mock_table):
        with patch("boto3.client") as mock_boto_client:
            mock_boto_client.return_value = mock_sts
            
            with patch("index.create_drs_client") as mock_create_drs:
                mock_create_drs.return_value = mock_drs
                
                result = handle_get_combined_capacity(
                    {"targetAccountId": "987654321098"}
                )
                
                # Should succeed
                assert result["statusCode"] == 200
                
                # Verify STS assume_role was called with constructed ARN
                expected_arn = (
                    "arn:aws:iam::987654321098:role/DRSOrchestrationRole"
                )
                mock_sts.assume_role.assert_called()
                call_args = mock_sts.assume_role.call_args
                assert call_args[1]["RoleArn"] == expected_arn
                assert call_args[1]["ExternalId"] == "test-external-id"


def test_capacity_query_missing_account():
    """
    Test capacity query error handling for missing accounts.
    
    Validates: Error handling for non-existent accounts
    Task: 11.3
    """
    # Mock DynamoDB returning no item
    mock_table = MagicMock()
    mock_table.get_item.return_value = {}  # No Item key
    
    with patch("index.target_accounts_table", mock_table):
        result = handle_get_combined_capacity(
            {"targetAccountId": "999999999999"}
        )
        
        # Should return 404 error
        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert body["error"] == "TARGET_ACCOUNT_NOT_FOUND"
        assert "999999999999" in body["message"]


def test_capacity_query_invalid_account_id():
    """
    Test capacity query error handling for invalid account ID format.
    
    Validates: Input validation
    Task: 11.3
    """
    # Test with non-numeric account ID
    result = handle_get_combined_capacity(
        {"targetAccountId": "invalid-id"}
    )
    
    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert "Invalid account ID format" in body["error"]
    
    # Test with wrong length
    result = handle_get_combined_capacity(
        {"targetAccountId": "12345"}
    )
    
    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert "Invalid account ID format" in body["error"]


def test_capacity_query_missing_target_account_id():
    """
    Test capacity query error handling for missing targetAccountId parameter.
    
    Validates: Required parameter validation
    Task: 11.3
    """
    result = handle_get_combined_capacity({})
    
    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert "Missing required field: targetAccountId" in body["error"]


def test_capacity_query_drs_api_mocked():
    """
    Test capacity query with mocked DRS API calls.
    
    Validates: DRS API integration with mocking
    Task: 11.4
    
    This test verifies that the capacity query function properly:
    - Retrieves account configuration from DynamoDB
    - Calls AWS APIs (STS, DRS) with proper mocking
    - Returns properly structured response
    """
    # Mock target account
    mock_table = MagicMock()
    mock_table.get_item.return_value = {
        "Item": {
            "accountId": "123456789012",
            "accountName": "Test Account",
            "externalId": "test-external-id",
            "roleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationRole",
            "stagingAccounts": []
        }
    }
    
    # Mock STS client
    mock_sts = MagicMock()
    mock_sts.assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "SessionToken": "token123",
            "Expiration": "2026-01-30T12:00:00Z",
        }
    }
    
    # Mock DRS client with realistic data
    mock_drs = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [
        {
            "items": [
                {
                    "sourceServerID": "s-123",
                    "dataReplicationInfo": {
                        "dataReplicationState": "CONTINUOUS"
                    }
                },
                {
                    "sourceServerID": "s-456",
                    "dataReplicationInfo": {
                        "dataReplicationState": "INITIAL_SYNC"
                    }
                },
                {
                    "sourceServerID": "s-789",
                    "dataReplicationInfo": {
                        "dataReplicationState": "DISCONNECTED"
                    }
                }
            ]
        }
    ]
    mock_drs.get_paginator.return_value = mock_paginator
    
    with patch("index.target_accounts_table", mock_table):
        with patch("boto3.client") as mock_boto_client:
            mock_boto_client.return_value = mock_sts
            
            with patch("index.create_drs_client") as mock_create_drs:
                mock_create_drs.return_value = mock_drs
                
                result = handle_get_combined_capacity(
                    {"targetAccountId": "123456789012"}
                )
                
                # Should succeed
                assert result["statusCode"] == 200
                body = json.loads(result["body"])
                
                # Verify response structure (main validation)
                assert "combined" in body
                assert "accounts" in body
                assert len(body["accounts"]) == 1
                
                # Verify account data
                account = body["accounts"][0]
                assert account["accountId"] == "123456789012"
                assert account["accountName"] == "Test Account"
                assert account["accountType"] == "target"
                
                # Verify STS assume_role was called (proves AWS API mocking works)
                mock_sts.assume_role.assert_called()



