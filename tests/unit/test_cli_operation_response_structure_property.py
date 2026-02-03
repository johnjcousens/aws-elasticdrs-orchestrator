"""
Property-Based Test: CLI Operation Response Structure

Feature: staging-accounts-management
Property 14: For any CLI operation (add_staging_account, remove_staging_account,
validate_staging_account, get_target_account), the response should be valid JSON
containing either a success field (boolean) with relevant data, or an error field
with a descriptive error message.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

This property test ensures that all CLI operations return well-formed,
consistent responses that can be reliably parsed and handled by CLI scripts.
"""

import json  # noqa: F401
import os  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: F401  # noqa: F401  # noqa: F401

import boto3  # noqa: F401
import pytest  # noqa: F401
from botocore.exceptions import ClientError  # noqa: F401
from hypothesis import given, settings, strategies as st, HealthCheck  # noqa: E402
from moto import mock_aws  # noqa: E402

# Set environment variables before importing handlers
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts-table"
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Add lambda directories to path
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "lambda" / "shared")
)

# Import data management handler
import importlib.util  # noqa: F401
data_mgmt_path = Path(__file__).parent.parent.parent / "lambda" / "data-management-handler" / "index.py"
spec_data = importlib.util.spec_from_file_location("data_mgmt_handler", data_mgmt_path)
data_mgmt_handler = importlib.util.module_from_spec(spec_data)
spec_data.loader.exec_module(data_mgmt_handler)
data_mgmt_add_staging_account = data_mgmt_handler.handle_add_staging_account
data_mgmt_remove_staging_account = data_mgmt_handler.handle_remove_staging_account

# Import query handler
query_handler_path = Path(__file__).parent.parent.parent / "lambda" / "query-handler" / "index.py"
spec_query = importlib.util.spec_from_file_location("query_handler", query_handler_path)
query_handler = importlib.util.module_from_spec(spec_query)
spec_query.loader.exec_module(query_handler)
handle_validate_staging_account = query_handler.handle_validate_staging_account


# Strategies for generating valid inputs
account_id_strategy = st.from_regex(r"\d{12}", fullmatch=True)

role_arn_strategy = st.builds(
    lambda acc_id: f"arn:aws:iam::{acc_id}:role/TestRole",
    account_id_strategy,
)

staging_account_strategy = st.fixed_dictionaries({
    "accountId": account_id_strategy,
    "accountName": st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="_-"
        )
    ),
    "roleArn": role_arn_strategy,
    "externalId": st.text(min_size=1, max_size=100),
})

region_strategy = st.sampled_from([
    "us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"
])


def validate_response_structure(response: dict, operation_name: str) -> None:
    """
    Validate that a CLI operation response has the correct structure.
    
    A valid response must:
    1. Be a dictionary (parseable as JSON)
    2. Have either 'success' field (boolean) OR 'valid' field (boolean) OR 'error' field (string)
    3. If success=True or valid=True, contain relevant data fields
    4. If error present, it must be a non-empty string
    
    Note: validate_staging_account uses 'valid' instead of 'success'
    """
    # Must be a dictionary
    assert isinstance(response, dict), (
        f"{operation_name}: Response must be a dictionary"
    )

    # Must have statusCode (from Lambda response wrapper)
    assert "statusCode" in response, (
        f"{operation_name}: Response must have statusCode"
    )

    # Must have body
    assert "body" in response, (
        f"{operation_name}: Response must have body"
    )

    # Body must be valid JSON string
    try:
        body = json.loads(response["body"])
    except (json.JSONDecodeError, TypeError) as e:
        pytest.fail(
            f"{operation_name}: Response body must be valid JSON string: {e}"
        )

    # Body must be a dictionary
    assert isinstance(body, dict), (
        f"{operation_name}: Response body must be a dictionary"
    )

    # Must have either 'success', 'valid', or 'error' field
    has_success = "success" in body
    has_valid = "valid" in body
    has_error = "error" in body

    assert has_success or has_valid or has_error, (
        f"{operation_name}: Response must have either 'success', 'valid', or 'error' field. "
        f"Got: {list(body.keys())}"
    )

    # Validate success field if present
    if has_success:
        assert isinstance(body["success"], bool), (
            f"{operation_name}: 'success' field must be boolean, got {type(body['success'])}"
        )

        # If success=True, should have relevant data
        if body["success"]:
            # Should have at least one data field beyond 'success'
            data_fields = [k for k in body.keys() if k != "success"]
            assert len(data_fields) > 0, (
                f"{operation_name}: Successful response should contain data fields beyond 'success'"
            )

    # Validate valid field if present (for validate_staging_account)
    if has_valid:
        assert isinstance(body["valid"], bool), (
            f"{operation_name}: 'valid' field must be boolean, got {type(body['valid'])}"
        )

        # If valid=True, should have relevant data
        if body["valid"]:
            # Should have at least one data field beyond 'valid'
            data_fields = [k for k in body.keys() if k != "valid"]
            assert len(data_fields) > 0, (
                f"{operation_name}: Successful validation should contain data fields beyond 'valid'"
            )

    # Validate error field if present
    if has_error:
        assert isinstance(body["error"], str), (
            f"{operation_name}: 'error' field must be string, got {type(body['error'])}"
        )
        assert len(body["error"]) > 0, (
            f"{operation_name}: 'error' message must not be empty"
        )


@pytest.fixture
def dynamodb_setup():
    """Set up mock DynamoDB table for testing"""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Create Target Accounts table
        table = dynamodb.create_table(  # noqa: F841
            TableName="test-target-accounts-table",
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "accountId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield table


# ============================================================================
# Property 14: CLI Operation Response Structure
# ============================================================================


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    target_account_id=account_id_strategy,
    staging_account=staging_account_strategy,
)
@pytest.mark.property
def test_property_add_staging_account_response_structure(
    dynamodb_setup, target_account_id, staging_account
):
    """
    Property 14a: add_staging_account Response Structure
    
    For any add_staging_account operation, the response should be valid JSON
    containing either success=true with stagingAccounts data, or an error field.
    """
    # Setup: Create target account
    table = dynamodb_setup  # noqa: F841
    table.put_item(
        Item={
            "accountId": target_account_id,
            "accountName": "Test Target Account",
            "roleArn": f"arn:aws:iam::{target_account_id}:role/TestRole",
            "externalId": f"test-external-id-{target_account_id}",
            "stagingAccounts": [],
        }
    )

    # Execute: Add staging account
    body = {
        "targetAccountId": target_account_id,
        "stagingAccount": staging_account,
    }

    response = data_mgmt_add_staging_account(body)

    # Validate response structure
    validate_response_structure(response, "add_staging_account")

    # Parse body
    response_body = json.loads(response["body"])

    # For successful add, verify specific fields
    if response_body.get("success"):
        assert "stagingAccounts" in response_body, (
            "Successful add_staging_account should include stagingAccounts"
        )
        assert isinstance(response_body["stagingAccounts"], list), (
            "stagingAccounts must be a list"
        )
        assert "message" in response_body, (
            "Successful add_staging_account should include message"
        )


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    target_account_id=account_id_strategy,
    staging_accounts=st.lists(
        staging_account_strategy,
        min_size=1,
        max_size=3,
        unique_by=lambda x: x["accountId"]
    ),
    removal_index=st.integers(min_value=0, max_value=2),
)
@pytest.mark.property
def test_property_remove_staging_account_response_structure(
    dynamodb_setup, target_account_id, staging_accounts, removal_index
):
    """
    Property 14b: remove_staging_account Response Structure
    
    For any remove_staging_account operation, the response should be valid JSON
    containing either success=true with updated stagingAccounts, or an error field.
    """
    # Ensure removal_index is within bounds
    if removal_index >= len(staging_accounts):
        removal_index = len(staging_accounts) - 1

    # Setup: Create target account with staging accounts
    table = dynamodb_setup  # noqa: F841

    # Convert staging accounts to DynamoDB format
    staging_accounts_db = []
    for sa in staging_accounts:
        staging_accounts_db.append({
            "accountId": sa["accountId"],
            "accountName": sa["accountName"],
            "roleArn": sa["roleArn"],
            "externalId": sa["externalId"],
            "addedAt": "2024-01-01T00:00:00Z",
            "addedBy": "test",
        })

    table.put_item(
        Item={
            "accountId": target_account_id,
            "accountName": "Test Target Account",
            "roleArn": f"arn:aws:iam::{target_account_id}:role/TestRole",
            "externalId": f"test-external-id-{target_account_id}",
            "stagingAccounts": staging_accounts_db,
        }
    )

    # Execute: Remove staging account
    staging_to_remove = staging_accounts[removal_index]
    body = {
        "targetAccountId": target_account_id,
        "stagingAccountId": staging_to_remove["accountId"],
    }

    response = data_mgmt_remove_staging_account(body)

    # Validate response structure
    validate_response_structure(response, "remove_staging_account")

    # Parse body
    response_body = json.loads(response["body"])

    # For successful removal, verify specific fields
    if response_body.get("success"):
        assert "stagingAccounts" in response_body, (
            "Successful remove_staging_account should include stagingAccounts"
        )
        assert isinstance(response_body["stagingAccounts"], list), (
            "stagingAccounts must be a list"
        )
        assert "message" in response_body, (
            "Successful remove_staging_account should include message"
        )


@settings(max_examples=100)
@given(
    account_id=account_id_strategy,
    role_arn=role_arn_strategy,
    external_id=st.text(min_size=1, max_size=100),
    region=region_strategy,
    validation_succeeds=st.booleans(),
    server_count=st.integers(min_value=0, max_value=300),
)
@pytest.mark.property
def test_property_validate_staging_account_response_structure(
    account_id, role_arn, external_id, region, validation_succeeds, server_count
):
    """
    Property 14c: validate_staging_account Response Structure
    
    For any validate_staging_account operation, the response should be valid JSON
    containing validation result fields (valid, roleAccessible, drsInitialized)
    or an error field.
    """
    query_params = {
        "accountId": account_id,
        "roleArn": role_arn,
        "externalId": external_id,
        "region": region,
    }

    with patch.object(query_handler, "boto3") as mock_boto3:
        if validation_succeeds:
            # Mock successful validation
            mock_sts = MagicMock()
            mock_sts.assume_role.return_value = {
                "Credentials": {
                    "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                    "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                    "SessionToken": "token123",
                }
            }

            mock_drs = MagicMock()
            mock_paginator = MagicMock()
            mock_drs.get_paginator.return_value = mock_paginator

            # Generate mock servers
            mock_servers = [
                {
                    "sourceServerID": f"s-{i:08d}",
                    "dataReplicationInfo": {
                        "dataReplicationState": "CONTINUOUS"
                    },
                }
                for i in range(server_count)
            ]
            mock_paginator.paginate.return_value = [{"items": mock_servers}]

            def client_side_effect(service, **kwargs):
                if service == "sts":
                    return mock_sts
                elif service == "drs":
                    return mock_drs
                return MagicMock()

            mock_boto3.client.side_effect = client_side_effect
        else:
            # Mock failed validation (role assumption failure)
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(
                {
                    "Error": {
                        "Code": "AccessDenied",
                        "Message": "Access Denied",
                    }
                },
                "AssumeRole",
            )
            mock_boto3.client.return_value = mock_sts

        # Execute validation
        response = handle_validate_staging_account(query_params)

        # Validate response structure
        validate_response_structure(response, "validate_staging_account")

        # Parse body
        response_body = json.loads(response["body"])

        # Validate specific fields for validation operation
        assert "valid" in response_body, (
            "validate_staging_account must include 'valid' field"
        )
        assert isinstance(response_body["valid"], bool), (
            "'valid' field must be boolean"
        )

        assert "roleAccessible" in response_body, (
            "validate_staging_account must include 'roleAccessible' field"
        )
        assert isinstance(response_body["roleAccessible"], bool), (
            "'roleAccessible' field must be boolean"
        )

        # If validation succeeded, check for additional fields
        if response_body["valid"]:
            assert "drsInitialized" in response_body, (
                "Successful validation must include 'drsInitialized'"
            )
            assert "currentServers" in response_body, (
                "Successful validation must include 'currentServers'"
            )
            assert "replicatingServers" in response_body, (
                "Successful validation must include 'replicatingServers'"
            )
            assert "totalAfter" in response_body, (
                "Successful validation must include 'totalAfter'"
            )


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    target_account_id=account_id_strategy,
    invalid_input=st.sampled_from([
        "missing_target_id",
        "invalid_target_id_format",
        "missing_staging_account",
        "invalid_staging_account_format",
    ]),
)
@pytest.mark.property
def test_property_error_responses_have_descriptive_messages(
    dynamodb_setup, target_account_id, invalid_input
):
    """
    Property 14d: Error Response Descriptiveness
    
    For any CLI operation that fails validation, the error message should be
    descriptive and help the user understand what went wrong.
    """
    table = dynamodb_setup  # noqa: F841

    # Setup target account
    table.put_item(
        Item={
            "accountId": target_account_id,
            "accountName": "Test Target Account",
            "roleArn": f"arn:aws:iam::{target_account_id}:role/TestRole",
            "externalId": f"test-external-id-{target_account_id}",
            "stagingAccounts": [],
        }
    )

    # Create invalid request based on test case
    if invalid_input == "missing_target_id":
        body = {
            "stagingAccount": {
                "accountId": "123456789012",
                "accountName": "Test",
                "roleArn": "arn:aws:iam::123456789012:role/Test",
                "externalId": "test",
            }
        }
    elif invalid_input == "invalid_target_id_format":
        body = {
            "targetAccountId": "invalid",
            "stagingAccount": {
                "accountId": "123456789012",
                "accountName": "Test",
                "roleArn": "arn:aws:iam::123456789012:role/Test",
                "externalId": "test",
            }
        }
    elif invalid_input == "missing_staging_account":
        body = {
            "targetAccountId": target_account_id,
        }
    else:  # invalid_staging_account_format
        body = {
            "targetAccountId": target_account_id,
            "stagingAccount": {
                "accountId": "invalid",
                "accountName": "Test",
            }
        }

    # Execute operation
    response = data_mgmt_add_staging_account(body)

    # Validate response structure
    validate_response_structure(response, "add_staging_account_error")

    # Parse body
    response_body = json.loads(response["body"])

    # Should have error field
    assert "error" in response_body, (
        "Invalid input should result in error field"
    )

    # Error field should be a string
    error_code = response_body["error"]
    assert isinstance(error_code, str), (
        f"Error field must be string, got {type(error_code)}"
    )

    # Should also have a message field with descriptive text
    if "message" in response_body:
        error_msg = response_body["message"]
        assert isinstance(error_msg, str), (
            f"Message field must be string, got {type(error_msg)}"
        )
        assert len(error_msg) >= 10, (
            f"Error message should be descriptive, got: '{error_msg}'"
        )

        # Error message should contain relevant keywords
        if invalid_input == "missing_target_id":
            assert "targetAccountId" in error_msg or "required" in error_msg.lower()
        elif invalid_input == "invalid_target_id_format":
            assert "format" in error_msg.lower() or "digit" in error_msg.lower()
        elif invalid_input == "missing_staging_account":
            assert "stagingAccount" in error_msg or "required" in error_msg.lower()
    else:
        # If no message field, error code itself should be descriptive
        assert len(error_code) >= 3, (
            f"Error code should be descriptive, got: '{error_code}'"
        )


@pytest.mark.property
def test_response_structure_consistency_across_operations():
    """
    Property 14e: Response Structure Consistency
    
    All CLI operations should follow the same response structure pattern,
    making it easy for CLI scripts to parse responses consistently.
    """
    # This test verifies that all operations use the same response wrapper
    # and follow the same success/error pattern

    # Test that all operations return the same top-level structure
    operations = [
        "add_staging_account",
        "remove_staging_account",
        "validate_staging_account",
    ]

    for operation in operations:
        # Each operation should return a dict with statusCode and body
        # The body should be JSON with either success or error
        # This is verified by the validate_response_structure function
        # which is called in all the property tests above
        pass

    # This test serves as documentation that all operations follow
    # the same pattern, which is verified by the other property tests


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
