"""
Unit Tests: Data Management Operations for Staging Accounts

Tests for add_staging_account and remove_staging_account operations
in the data management handler.

Requirements: 1.6, 2.2
"""

import json
import os
import sys
from unittest.mock import patch, MagicMock

import boto3
import pytest
from moto import mock_aws

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

# Set environment variables before importing handler
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts-table"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

from shared.staging_account_models import (
    add_staging_account,
    remove_staging_account,
)


def setup_dynamodb_table():
    """Set up mock DynamoDB table"""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create Target Accounts table
    table = dynamodb.create_table(
        TableName="test-target-accounts-table",
        KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "accountId", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Add test target account
    table.put_item(
        Item={
            "accountId": "123456789012",
            "accountName": "Test Target Account",
            "roleArn": "arn:aws:iam::123456789012:role/TestRole",
            "externalId": "test-external-id",
            "stagingAccounts": [],
        }
    )

    return table


@mock_aws
def test_add_staging_account_success():
    """Test adding a staging account successfully"""
    setup_dynamodb_table()
    
    target_account_id = "123456789012"
    staging_account = {
        "accountId": "444455556666",
        "accountName": "STAGING_01",
        "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
        "externalId": "external-id-123",
    }

    result = add_staging_account(
        target_account_id, staging_account, added_by="test_user"
    )

    assert result["success"] is True
    assert "STAGING_01" in result["message"]
    assert len(result["stagingAccounts"]) == 1
    assert result["stagingAccounts"][0]["accountId"] == "444455556666"
    assert result["stagingAccounts"][0]["accountName"] == "STAGING_01"


@mock_aws
def test_add_duplicate_staging_account():
    """Test adding a staging account that already exists"""
    setup_dynamodb_table()
    
    target_account_id = "123456789012"
    staging_account = {
        "accountId": "444455556666",
        "accountName": "STAGING_01",
        "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
        "externalId": "external-id-123",
    }

    # Add staging account first time
    result1 = add_staging_account(
        target_account_id, staging_account, added_by="test_user"
    )
    assert result1["success"] is True

    # Try to add same staging account again
    with pytest.raises(ValueError, match="already exists"):
        add_staging_account(
            target_account_id, staging_account, added_by="test_user"
        )


@mock_aws
def test_add_staging_account_invalid_structure():
    """Test adding staging account with invalid structure"""
    setup_dynamodb_table()
    
    target_account_id = "123456789012"

    # Missing required field
    invalid_staging_account = {
        "accountId": "444455556666",
        "accountName": "STAGING_01",
        # Missing roleArn and externalId
    }

    with pytest.raises(ValueError, match="Invalid staging account"):
        add_staging_account(
            target_account_id, invalid_staging_account, added_by="test_user"
        )


@mock_aws
def test_add_staging_account_invalid_account_id():
    """Test adding staging account with invalid account ID format"""
    setup_dynamodb_table()
    
    target_account_id = "123456789012"
    staging_account = {
        "accountId": "invalid",  # Not 12 digits
        "accountName": "STAGING_01",
        "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
        "externalId": "external-id-123",
    }

    with pytest.raises(ValueError, match="Invalid account ID format"):
        add_staging_account(
            target_account_id, staging_account, added_by="test_user"
        )


@mock_aws
def test_add_staging_account_target_not_found():
    """Test adding staging account to non-existent target account"""
    setup_dynamodb_table()
    
    nonexistent_target_id = "999999999999"
    staging_account = {
        "accountId": "444455556666",
        "accountName": "STAGING_01",
        "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
        "externalId": "external-id-123",
    }

    with pytest.raises(ValueError, match="not found"):
        add_staging_account(
            nonexistent_target_id, staging_account, added_by="test_user"
        )


@mock_aws
def test_remove_staging_account_success():
    """Test removing a staging account successfully"""
    setup_dynamodb_table()
    
    target_account_id = "123456789012"
    staging_account = {
        "accountId": "444455556666",
        "accountName": "STAGING_01",
        "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
        "externalId": "external-id-123",
    }

    # Add staging account first
    add_result = add_staging_account(
        target_account_id, staging_account, added_by="test_user"
    )
    assert add_result["success"] is True

    # Remove staging account
    remove_result = remove_staging_account(
        target_account_id, staging_account["accountId"]
    )

    assert remove_result["success"] is True
    assert "STAGING_01" in remove_result["message"]
    assert len(remove_result["stagingAccounts"]) == 0


@mock_aws
def test_remove_nonexistent_staging_account():
    """Test removing a staging account that doesn't exist"""
    setup_dynamodb_table()
    
    target_account_id = "123456789012"
    nonexistent_staging_id = "999999999999"

    with pytest.raises(ValueError, match="not found"):
        remove_staging_account(target_account_id, nonexistent_staging_id)


@mock_aws
def test_remove_staging_account_target_not_found():
    """Test removing staging account from non-existent target account"""
    setup_dynamodb_table()
    
    nonexistent_target_id = "999999999999"
    staging_id = "444455556666"

    with pytest.raises(ValueError, match="not found"):
        remove_staging_account(nonexistent_target_id, staging_id)


@mock_aws
def test_add_multiple_staging_accounts():
    """Test adding multiple staging accounts"""
    setup_dynamodb_table()
    
    target_account_id = "123456789012"

    staging_accounts = [
        {
            "accountId": "444455556666",
            "accountName": "STAGING_01",
            "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
            "externalId": "external-id-1",
        },
        {
            "accountId": "777777777777",
            "accountName": "STAGING_02",
            "roleArn": "arn:aws:iam::777777777777:role/DRSRole",
            "externalId": "external-id-2",
        },
        {
            "accountId": "888888888888",
            "accountName": "STAGING_03",
            "roleArn": "arn:aws:iam::888888888888:role/DRSRole",
            "externalId": "external-id-3",
        },
    ]

    # Add all staging accounts
    for staging_account in staging_accounts:
        result = add_staging_account(
            target_account_id, staging_account, added_by="test_user"
        )
        assert result["success"] is True

    # Verify all were added
    final_result = add_staging_account(
        target_account_id,
        {
            "accountId": "999999999999",
            "accountName": "STAGING_04",
            "roleArn": "arn:aws:iam::999999999999:role/DRSRole",
            "externalId": "external-id-4",
        },
        added_by="test_user",
    )

    assert len(final_result["stagingAccounts"]) == 4


@mock_aws
def test_remove_staging_account_preserves_others():
    """Test that removing one staging account preserves others"""
    setup_dynamodb_table()
    
    target_account_id = "123456789012"

    # Add three staging accounts
    staging_accounts = [
        {
            "accountId": "444455556666",
            "accountName": "STAGING_01",
            "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
            "externalId": "external-id-1",
        },
        {
            "accountId": "777777777777",
            "accountName": "STAGING_02",
            "roleArn": "arn:aws:iam::777777777777:role/DRSRole",
            "externalId": "external-id-2",
        },
        {
            "accountId": "888888888888",
            "accountName": "STAGING_03",
            "roleArn": "arn:aws:iam::888888888888:role/DRSRole",
            "externalId": "external-id-3",
        },
    ]

    for staging_account in staging_accounts:
        add_staging_account(
            target_account_id, staging_account, added_by="test_user"
        )

    # Remove middle staging account
    result = remove_staging_account(target_account_id, "777777777777")

    assert result["success"] is True
    assert len(result["stagingAccounts"]) == 2

    # Verify correct accounts remain
    remaining_ids = [
        acc["accountId"] for acc in result["stagingAccounts"]
    ]
    assert "444455556666" in remaining_ids
    assert "888888888888" in remaining_ids
    assert "777777777777" not in remaining_ids
