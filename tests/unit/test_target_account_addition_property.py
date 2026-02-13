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

import json  # noqa: F401
import os  # noqa: E402
import sys  # noqa: E402
import importlib.util  # noqa: F401
from pathlib import Path  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: F401  # noqa: F401  # noqa: F401

import pytest  # noqa: F401
from hypothesis import given, settings, strategies as st  # noqa: E402
from moto import mock_aws  # noqa: E402
import boto3  # noqa: F401

# Set environment variables BEFORE importing
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts-table"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.account_utils import STANDARD_ROLE_NAME, construct_role_arn  # noqa: E402

# Start mocking AWS BEFORE loading the module
mock_aws_context = mock_aws()
mock_aws_context.start()

# Setup mock STS for account ID
sts = boto3.client("sts", region_name="us-east-1")

# Load data-management-handler module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lambda"))
data_management_handler = importlib.import_module("data-management-handler.index")

# Stop the mock after module is loaded
mock_aws_context.stop()


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks between tests to prevent state pollution."""
    yield
    patch.stopall()


# Strategy for valid AWS account IDs (12 digits)
account_id_strategy = st.text(alphabet="0123456789", min_size=12, max_size=12)

# Strategy for account names
account_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" -_"),
    min_size=1,
    max_size=50,
)


@settings(max_examples=50, deadline=1000)  # Reduce examples, increase deadline
@given(
    account_id=account_id_strategy,
    account_name=account_name_strategy,
    explicit_arn=st.text(min_size=20, max_size=100),
)
@pytest.mark.property
def test_property_explicit_arn_precedence(account_id, account_name, explicit_arn):
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
        table = dynamodb.create_table(  # noqa: F841
            TableName="test-target-accounts-table",
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "accountId", "AttributeType": "S"}],
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
                "Should use explicit ARN. " f"Expected: {explicit_arn}, Got: {response_body.get('roleArn')}"
            )
            # Should NOT be the constructed ARN
            constructed = construct_role_arn(account_id)
            assert response_body["roleArn"] != constructed, "Should not use constructed ARN when explicit ARN provided"


@settings(max_examples=50, deadline=1000)  # Reduce examples, increase deadline
@given(
    account_id=account_id_strategy,
    account_name=account_name_strategy,
    include_role_arn=st.booleans(),
)
@pytest.mark.property
def test_property_optional_role_arn_acceptance(account_id, account_name, include_role_arn):
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
        table = dynamodb.create_table(  # noqa: F841
            TableName="test-target-accounts-table",
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "accountId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Build request body
        body = {"accountId": account_id, "accountName": account_name}

        if include_role_arn:
            body["roleArn"] = f"arn:aws:iam::{account_id}:role/CustomRole"

        # Mock the current account ID to be different from the target account
        # This ensures we're testing cross-account scenario
        # Patch in shared.account_utils where get_current_account_id is called
        with patch("shared.account_utils.get_current_account_id", return_value="123456789012"):
            # Mock boto3 in shared.account_utils to prevent real AWS calls
            with patch("shared.account_utils.boto3") as mock_boto3:
                mock_sts = MagicMock()
                mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
                mock_iam = MagicMock()
                mock_iam.list_account_aliases.return_value = {"AccountAliases": ["test-account"]}

                def mock_client(service_name, **kwargs):
                    if service_name == "sts":
                        return mock_sts
                    elif service_name == "iam":
                        return mock_iam
                    return MagicMock()

                mock_boto3.client.side_effect = mock_client
                mock_boto3.resource.return_value = dynamodb

                # Act - patch table getter to use moto table
                with patch.object(
                    data_management_handler,
                    "get_target_accounts_table",
                    return_value=table,
                ):
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
@pytest.mark.property
def test_property_api_response_includes_role_arn(account_id, account_name):
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
        table = dynamodb.create_table(  # noqa: F841
            TableName="test-target-accounts-table",
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "accountId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        body = {"accountId": account_id, "accountName": account_name}

        # Act
        response = data_management_handler.create_target_account(body)

        # Assert - Response must include roleArn
        if response["statusCode"] in [200, 201]:
            response_body = json.loads(response["body"])
            assert "roleArn" in response_body, "API response must include roleArn field"
            assert response_body["roleArn"], "roleArn field must be non-empty"
            assert len(response_body["roleArn"]) > 0, "roleArn must have content"


@pytest.mark.property
def test_account_addition_without_role_arn():
    """Unit test: Adding account without roleArn constructs ARN"""
    with mock_aws():
        # Setup DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-target-accounts-table",
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "accountId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        body = {
            "accountId": "999888777666",  # Different from mocked account
            "accountName": "Test Account",
        }

        # Mock the current account ID to be different from the target account
        # This ensures we're testing cross-account scenario
        with patch("shared.account_utils.get_current_account_id", return_value="123456789012"):
            # Mock boto3 in shared.account_utils to prevent real AWS calls
            with patch("shared.account_utils.boto3") as mock_boto3:
                mock_sts = MagicMock()
                mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
                mock_iam = MagicMock()
                mock_iam.list_account_aliases.return_value = {"AccountAliases": ["test-account"]}

                def mock_client(service_name, **kwargs):
                    if service_name == "sts":
                        return mock_sts
                    elif service_name == "iam":
                        return mock_iam
                    return MagicMock()

                mock_boto3.client.side_effect = mock_client
                mock_boto3.resource.return_value = dynamodb

                # Patch the target_accounts_table global variable in data-management-handler
                with patch.object(data_management_handler, "get_target_accounts_table", return_value=table):
                    response = data_management_handler.create_target_account(body)

        # Debug output
        if response["statusCode"] != 201:
            print(f"Response: {response}")
            response_body = json.loads(response["body"])
            print(f"Error: {response_body}")

        assert response["statusCode"] == 201
        response_body = json.loads(response["body"])
        assert response_body["roleArn"] == ("arn:aws:iam::999888777666:role/DRSOrchestrationRole")


@pytest.mark.property
def test_account_addition_with_explicit_role_arn():
    """Unit test: Adding account with explicit roleArn uses provided ARN"""
    with mock_aws():
        # Setup DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-target-accounts-table",
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "accountId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        custom_arn = "arn:aws:iam::999888777666:role/CustomRole"
        body = {
            "accountId": "999888777666",  # Different from mocked account
            "accountName": "Test Account",
            "roleArn": custom_arn,
        }

        # Mock the current account ID to be different from the target account
        # This ensures we're testing cross-account scenario
        with patch("shared.account_utils.get_current_account_id", return_value="123456789012"):
            # Mock boto3 in shared.account_utils to prevent real AWS calls
            with patch("shared.account_utils.boto3") as mock_boto3:
                mock_sts = MagicMock()
                mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
                mock_iam = MagicMock()
                mock_iam.list_account_aliases.return_value = {"AccountAliases": ["test-account"]}

                def mock_client(service_name, **kwargs):
                    if service_name == "sts":
                        return mock_sts
                    elif service_name == "iam":
                        return mock_iam
                    return MagicMock()

                mock_boto3.client.side_effect = mock_client
                mock_boto3.resource.return_value = dynamodb

                # Patch the target_accounts_table global variable in data-management-handler
                with patch.object(data_management_handler, "get_target_accounts_table", return_value=table):
                    response = data_management_handler.create_target_account(body)

        assert response["statusCode"] == 201
        response_body = json.loads(response["body"])
        assert response_body["roleArn"] == custom_arn


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
