"""
Unit tests for handle_add_staging_account operation in data management handler.

Tests cover:
- Successful staging account addition
- Missing required fields validation
- Invalid account ID format validation
- Duplicate staging account handling
- Target account not found handling
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from decimal import Decimal

import pytest
import boto3
from moto import mock_aws

# Add lambda paths for imports
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "lambda" / "shared")
)
sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent.parent
        / "lambda"
        / "data-management-handler"
    ),
)

# Set environment variables before importing
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts-table"
os.environ["STAGING_ACCOUNTS_TABLE"] = "test-staging-accounts-table"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Import from data-management-handler
import importlib.util
spec = importlib.util.spec_from_file_location(
    "data_management_handler",
    Path(__file__).parent.parent.parent / "lambda" / "data-management-handler" / "index.py"
)
data_management_handler = importlib.util.module_from_spec(spec)
sys.modules['data_management_handler'] = data_management_handler
spec.loader.exec_module(data_management_handler)
handle_add_staging_account = data_management_handler.handle_add_staging_account


class TestHandleAddStagingAccount:
    """Test handle_add_staging_account operation."""

    def setup_dynamodb_table(self):
        """Set up test fixtures."""
        # Create DynamoDB table
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-target-accounts-table",
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "accountId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Add a test target account
        table.put_item(
            Item={
                "accountId": "111122223333",
                "accountName": "TEST_TARGET",
                "roleArn": "arn:aws:iam::111122223333:role/DRSOrchestrationRole-test",
                "externalId": "drs-orchestration-test-111122223333",
                "stagingAccounts": [],
            }
        )
        return table

    @mock_aws
    def test_add_staging_account_success(self):
        """Test successfully adding a staging account."""
        self.setup_dynamodb_table()
        
        body = {
            "targetAccountId": "111122223333",
            "stagingAccount": {
                "accountId": "444455556666",
                "accountName": "STAGING_01",
                "roleArn": (
                    "arn:aws:iam::444455556666:role/"
                    "DRSOrchestrationRole-test"
                ),
                "externalId": "drs-orchestration-test-444455556666",
            },
        }

        result = handle_add_staging_account(body)

        assert result["statusCode"] == 200
        response_body = json.loads(result["body"])
        assert response_body["success"] is True
        assert "STAGING_01" in response_body["message"]
        assert len(response_body["stagingAccounts"]) == 1
        assert response_body["stagingAccounts"][0]["accountId"] == "444455556666"

    @mock_aws
    def test_add_staging_account_missing_body(self):
        """Test adding staging account with missing body."""
        result = handle_add_staging_account(None)

        assert result["statusCode"] == 400
        response_body = json.loads(result["body"])
        assert response_body["error"] == "MISSING_BODY"

    @mock_aws
    def test_add_staging_account_missing_target_account_id(self):
        """Test adding staging account with missing targetAccountId."""
        body = {
            "stagingAccount": {
                "accountId": "444455556666",
                "accountName": "STAGING_01",
                "roleArn": (
                    "arn:aws:iam::444455556666:role/"
                    "DRSOrchestrationRole-test"
                ),
                "externalId": "drs-orchestration-test-444455556666",
            }
        }

        result = handle_add_staging_account(body)

        assert result["statusCode"] == 400
        response_body = json.loads(result["body"])
        assert response_body["error"] == "MISSING_FIELD"
        assert "targetAccountId" in response_body["message"]

    @mock_aws
    def test_add_staging_account_missing_staging_account(self):
        """Test adding staging account with missing stagingAccount."""
        body = {"targetAccountId": "111122223333"}

        result = handle_add_staging_account(body)

        assert result["statusCode"] == 400
        response_body = json.loads(result["body"])
        assert response_body["error"] == "MISSING_FIELD"
        assert "stagingAccount" in response_body["message"]

    @mock_aws
    def test_add_staging_account_invalid_target_account_id_format(self):
        """Test adding staging account with invalid targetAccountId format."""
        body = {
            "targetAccountId": "12345",  # Not 12 digits
            "stagingAccount": {
                "accountId": "444455556666",
                "accountName": "STAGING_01",
                "roleArn": (
                    "arn:aws:iam::444455556666:role/"
                    "DRSOrchestrationRole-test"
                ),
                "externalId": "drs-orchestration-test-444455556666",
            },
        }

        result = handle_add_staging_account(body)

        assert result["statusCode"] == 400
        response_body = json.loads(result["body"])
        assert response_body["error"] == "INVALID_FORMAT"
        assert "12 digits" in response_body["message"]

    @mock_aws
    def test_add_staging_account_target_not_found(self):
        """Test adding staging account when target account not found."""
        self.setup_dynamodb_table()
        
        body = {
            "targetAccountId": "999999999999",  # Non-existent account
            "stagingAccount": {
                "accountId": "444455556666",
                "accountName": "STAGING_01",
                "roleArn": (
                    "arn:aws:iam::444455556666:role/"
                    "DRSOrchestrationRole-test"
                ),
                "externalId": "drs-orchestration-test-444455556666",
            },
        }

        result = handle_add_staging_account(body)

        assert result["statusCode"] == 404
        response_body = json.loads(result["body"])
        assert response_body["error"] == "TARGET_ACCOUNT_NOT_FOUND"
        assert "not found" in response_body["message"]

    @mock_aws
    def test_add_staging_account_duplicate(self):
        """Test adding duplicate staging account."""
        self.setup_dynamodb_table()
        
        # First, add a staging account
        body = {
            "targetAccountId": "111122223333",
            "stagingAccount": {
                "accountId": "444455556666",
                "accountName": "STAGING_01",
                "roleArn": (
                    "arn:aws:iam::444455556666:role/"
                    "DRSOrchestrationRole-test"
                ),
                "externalId": "drs-orchestration-test-444455556666",
            },
        }

        # Add first time
        result1 = handle_add_staging_account(body)
        assert result1["statusCode"] == 200

        # Try to add again
        result2 = handle_add_staging_account(body)

        assert result2["statusCode"] == 409
        response_body = json.loads(result2["body"])
        assert response_body["error"] == "STAGING_ACCOUNT_EXISTS"
        assert "already exists" in response_body["message"]

    @mock_aws
    def test_add_staging_account_invalid_structure(self):
        """Test adding staging account with invalid structure."""
        self.setup_dynamodb_table()
        
        body = {
            "targetAccountId": "111122223333",
            "stagingAccount": {
                "accountId": "444455556666",
                "accountName": "STAGING_01",
                # Missing roleArn and externalId
            },
        }

        result = handle_add_staging_account(body)

        assert result["statusCode"] == 400
        response_body = json.loads(result["body"])
        assert response_body["error"] == "VALIDATION_ERROR"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
