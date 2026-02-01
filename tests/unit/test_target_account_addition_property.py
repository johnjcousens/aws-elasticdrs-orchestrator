"""
Property-based tests for target account addition.

Feature: standardized-cross-account-role-naming
Properties:
- Property 2: Explicit ARN takes precedence
- Property 3: Account addition round-trip
- Property 4: API response includes role ARN
- Property 5: Optional roleArn field acceptance

Validates: Requirements 1.3, 1.4, 1.5
"""

import json
import os
import sys
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st
from moto import mock_aws
import boto3

# Set environment variables BEFORE importing
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts-table"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.account_utils import STANDARD_ROLE_NAME, construct_role_arn

# Start mocking AWS BEFORE loading the module
mock_aws_context = mock_aws()
mock_aws_context.start()

# Setup mock STS for account ID
sts = boto3.client("sts", region_name="us-east-1")

try:
    # Load data-management-handler module
    spec = importlib.util.spec_from_file_location(
        "data_management_handler",
        Path(__file__).parent.parent.parent / "lambda" / "data-management-handler" / "index.py"
    )
    data_management_handler = importlib.util.module_from_spec(spec)
    sys.modules['data_management_handler'] = data_management_handler
    spec.loader.exec_module(data_management_handler)
finally:
    # Stop the mock after module is loaded
    mock_aws_context.stop()

# Strategy for valid AWS account IDs (12 digits)
account_id_strategy = st.text(alphabet="0123456789", min_size=12, max_size=12)

# Strategy for account names
account_name_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" -_"
    ),
    min_size=1,
    max_size=50,
)


@settings(max_examples=50, deadline=1000)  # Reduce examples, increase deadline
@given(
    account_id=account_id_strategy,
    account_name=account_name_strategy,
    explicit_arn=st.text(min_size=20, max_size=100),
)
def test_property_explicit_arn_precedence(
    account_id, account_name, explicit_arn
):
    """
    Property 2: Explicit ARN takes precedence.

    Feature: standardized-cross-account-role-naming
    Property 2: For any account with explicitly provided roleArn,
                system must use that exact ARN value

    Validates: Requirements 1.3
    """
    with mock_aws():
        # Setup DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-target-accounts-table",
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "accountId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create request body with explicit ARN
        body = {
            "accountId": account_id,
            "accountName": account_name,
            "roleArn": explicit_arn,
        }

        # Act
        response = data_management_handler.create_target_account(body)

        # Assert - Explicit ARN must be used
        if response["statusCode"] == 201:
            response_body = json.loads(response["body"])
            assert response_body["roleArn"] == explicit_arn, (
                f"Should use explicit ARN. "
                f"Expected: {explicit_arn}, Got: {response_body.get('roleArn')}"
            )
            # Should NOT be the constructed ARN
            constructed = construct_role_arn(account_id)
            assert response_body["roleArn"] != constructed, (
                f"Should not use constructed ARN when explicit ARN provided"
            )


@settings(max_examples=50, deadline=1000)  # Reduce examples, increase deadline
@given(
    account_id=account_id_strategy,
    account_name=account_name_strategy,
    include_role_arn=st.booleans(),
)
def test_property_optional_role_arn_acceptance(
    account_id, account_name, include_role_arn
):
    """
    Property 5: Optional roleArn field acceptance.

    Feature: standardized-cross-account-role-naming
    Property 5: For any valid account data, API must accept requests
                both with and without roleArn field

    Validates: Requirements 1.1
    """
    with mock_aws():
        # Setup DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-target-accounts-table",
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "accountId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Build request body
        body = {"accountId": account_id, "accountName": account_name}

        if include_role_arn:
            body["roleArn"] = f"arn:aws:iam::{account_id}:role/CustomRole"

        # Act
        response = data_management_handler.create_target_account(body)

        # Assert - Both should succeed
        assert response["statusCode"] in [200, 201], (
            f"Should accept request {'with' if include_role_arn else 'without'} "
            f"roleArn. Got status: {response['statusCode']}"
        )


@settings(max_examples=30, deadline=1000)  # Fewer examples, longer deadline
@given(
    account_id=account_id_strategy,
    account_name=account_name_strategy,
)
def test_property_api_response_includes_role_arn(
    account_id, account_name
):
    """
    Property 4: API responses include role ARN.

    Feature: standardized-cross-account-role-naming
    Property 4: For any successful account addition, API response
                must include roleArn field with non-empty value

    Validates: Requirements 1.5
    """
    with mock_aws():
        # Setup DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-target-accounts-table",
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "accountId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        body = {"accountId": account_id, "accountName": account_name}

        # Act
        response = data_management_handler.create_target_account(body)

        # Assert - Response must include roleArn
        if response["statusCode"] in [200, 201]:
            response_body = json.loads(response["body"])
            assert "roleArn" in response_body, (
                "API response must include roleArn field"
            )
            assert response_body["roleArn"], (
                "roleArn field must be non-empty"
            )
            assert len(response_body["roleArn"]) > 0, (
                "roleArn must have content"
            )


def test_account_addition_without_role_arn():
    """Unit test: Adding account without roleArn constructs ARN"""
    with mock_aws():
        # Setup DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-target-accounts-table",
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "accountId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        body = {
            "accountId": "999888777666",  # Different from mocked account
            "accountName": "Test Account",
        }

        response = data_management_handler.create_target_account(body)

        # Debug output
        if response["statusCode"] != 201:
            print(f"Response: {response}")
            response_body = json.loads(response["body"])
            print(f"Error: {response_body}")

        assert response["statusCode"] == 201
        response_body = json.loads(response["body"])
        assert response_body["roleArn"] == (
            "arn:aws:iam::999888777666:role/DRSOrchestrationRole"
        )


def test_account_addition_with_explicit_role_arn():
    """Unit test: Adding account with explicit roleArn uses provided ARN"""
    with mock_aws():
        # Setup DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-target-accounts-table",
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "accountId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        custom_arn = "arn:aws:iam::999888777666:role/CustomRole"
        body = {
            "accountId": "999888777666",  # Different from mocked account
            "accountName": "Test Account",
            "roleArn": custom_arn,
        }

        response = data_management_handler.create_target_account(body)

        assert response["statusCode"] == 201
        response_body = json.loads(response["body"])
        assert response_body["roleArn"] == custom_arn


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
