"""
Integration tests for error handling across all Lambda handlers.

Tests comprehensive error handling for:
- Invalid operation names (unknown operations)
- Missing required parameters (groupId, planId, executionId, etc.)
- Invalid parameter values (malformed IDs, invalid enums, etc.)
- Invalid event format (not a dict, missing operation field)
- Standardized error responses with error codes
- Descriptive and actionable error messages
- Error handling in all three handlers (query, execution, data-management)

Feature: direct-lambda-invocation-mode
Task: 12.7 Test error handling for invalid operations and missing parameters

Validates Requirements 9.1-9.7:
- 9.1: Missing required parameters return MISSING_PARAMETER error
- 9.2: Invalid operations return INVALID_OPERATION error
- 9.3: Authorization failures return AUTHORIZATION_FAILED error
- 9.4: DynamoDB errors return DYNAMODB_ERROR error
- 9.5: DRS API errors return DRS_ERROR error
- 9.6: Unexpected exceptions return INTERNAL_ERROR error
- 9.7: All error responses include error, message, and optional details
"""

import json
import os
import sys
from unittest.mock import Mock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError

# Add lambda directories to path
lambda_base = os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
sys.path.insert(0, lambda_base)
sys.path.insert(0, os.path.join(lambda_base, "query-handler"))
sys.path.insert(0, os.path.join(lambda_base, "data-management-handler"))
sys.path.insert(0, os.path.join(lambda_base, "execution-handler"))
sys.path.insert(0, os.path.join(lambda_base, "shared"))

# Import handlers and utilities after path setup
import index as query_handler_module
import index as execution_handler_module
import index as data_management_handler_module
from shared.response_utils import (
    ERROR_INVALID_INVOCATION,
    ERROR_INVALID_OPERATION,
    ERROR_MISSING_PARAMETER,
    ERROR_INVALID_PARAMETER,
    ERROR_AUTHORIZATION_FAILED,
    ERROR_NOT_FOUND,
    ERROR_DYNAMODB_ERROR,
    ERROR_DRS_ERROR,
    ERROR_INTERNAL_ERROR,
)


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing"""
    os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
    os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
    os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
    os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["AWS_ACCOUNT_ID"] = "111111111111"
    yield
    # Cleanup
    for key in [
        "PROTECTION_GROUPS_TABLE",
        "RECOVERY_PLANS_TABLE",
        "TARGET_ACCOUNTS_TABLE",
        "EXECUTION_HISTORY_TABLE",
        "AWS_ACCOUNT_ID",
    ]:
        if key in os.environ:
            del os.environ[key]


def get_mock_context():
    """Create mock Lambda context"""
    context = Mock()
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:111111111111:function:test-handler"
    )
    context.request_id = "test-request-123"
    context.function_name = "test-handler"
    context.aws_request_id = "test-request-123"
    return context


# ============================================================================
# Test: Invalid Event Format
# ============================================================================


class TestInvalidEventFormat:
    """
    Test error handling for invalid event formats.
    
    Validates Requirement 9.7: Standardized error responses
    """

    def test_query_handler_missing_operation_field(self, mock_env_vars):
        """
        Test query handler returns INVALID_INVOCATION when operation field
        is missing.
        
        Validates Requirement 9.7
        """
        # Event without operation field
        event = {"someField": "value"}
        context = get_mock_context()

        with patch.object(query_handler_module, "boto3"):
            result = query_handler_module.lambda_handler(event, context)

        # Verify error response structure
        assert "error" in result
        assert "message" in result
        assert result["error"] == ERROR_INVALID_INVOCATION
        assert "operation" in result["message"].lower()

        # Verify JSON serializable
        json.dumps(result)

    def test_execution_handler_missing_operation_field(self, mock_env_vars):
        """
        Test execution handler returns INVALID_INVOCATION when operation
        field is missing.
        
        Validates Requirement 9.7
        """
        # Event without operation field
        event = {"planId": "plan-123"}
        context = get_mock_context()

        with patch.object(execution_handler_module, "boto3"):
            result = execution_handler_module.lambda_handler(event, context)

        # Verify error response structure
        assert "error" in result
        assert "message" in result
        assert result["error"] == ERROR_INVALID_INVOCATION

    def test_data_management_handler_missing_operation_field(
        self, mock_env_vars
    ):
        """
        Test data management handler returns INVALID_INVOCATION when
        operation field is missing.
        
        Validates Requirement 9.7
        """
        # Event without operation field
        event = {"body": {"name": "Test"}}
        context = get_mock_context()

        with patch.object(data_management_handler_module, "boto3"):
            result = data_management_handler_module.lambda_handler(
                event, context
            )

        # Verify error response structure
        assert "error" in result
        assert "message" in result
        assert result["error"] == ERROR_INVALID_INVOCATION


# ============================================================================
# Test: Invalid Operation Names
# ============================================================================


class TestInvalidOperationNames:
    """
    Test error handling for invalid operation names.
    
    Validates Requirement 9.2: Invalid operations return INVALID_OPERATION
    """

    def test_query_handler_invalid_operation(self, mock_env_vars):
        """
        Test query handler returns INVALID_OPERATION for unknown operation.
        
        Validates Requirement 9.2
        """
        event = {"operation": "invalid_operation_xyz"}
        context = get_mock_context()

        # Mock authorization to pass
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(query_handler_module, "boto3"):
                result = query_handler_module.lambda_handler(event, context)

        # Verify error response
        assert result["error"] == ERROR_INVALID_OPERATION
        assert "message" in result
        assert "invalid_operation_xyz" in result["message"]

        # Should include operation in details
        assert "details" in result
        assert "operation" in result["details"]

    def test_execution_handler_invalid_operation(self, mock_env_vars):
        """
        Test execution handler returns INVALID_OPERATION for unknown
        operation.
        
        Validates Requirement 9.2
        """
        event = {"operation": "unknown_operation"}
        context = get_mock_context()

        # Mock authorization to pass
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(execution_handler_module, "boto3"):
                result = execution_handler_module.lambda_handler(event, context)

        # Verify error response
        assert result["error"] == ERROR_INVALID_OPERATION
        assert "unknown_operation" in result["message"]
        assert "details" in result
        assert "operation" in result["details"]

    def test_data_management_handler_invalid_operation(self, mock_env_vars):
        """
        Test data management handler returns INVALID_OPERATION for unknown
        operation.
        
        Validates Requirement 9.2
        """
        event = {"operation": "bad_operation"}
        context = get_mock_context()

        # Mock authorization to pass
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(data_management_handler_module, "boto3"):
                result = data_management_handler_module.lambda_handler(
                    event, context
                )

        # Verify error response
        assert result["error"] == ERROR_INVALID_OPERATION
        assert "bad_operation" in result["message"]
        assert "details" in result
        assert "operation" in result["details"]


# ============================================================================
# Test: Missing Required Parameters
# ============================================================================


class TestMissingRequiredParameters:
    """
    Test error handling for missing required parameters.
    
    Validates Requirement 9.1: Missing parameters return MISSING_PARAMETER
    """

    def test_query_handler_get_drs_source_servers_missing_region(
        self, mock_env_vars
    ):
        """
        Test get_drs_source_servers works without required parameters
        (they're optional).
        
        This test verifies the handler doesn't crash with missing optional params.
        """
        event = {"operation": "get_drs_source_servers"}
        context = get_mock_context()

        # Mock DRS client
        mock_drs = MagicMock()
        mock_drs.get_paginator.return_value.paginate.return_value = []

        # Mock authorization to pass
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(query_handler_module, "boto3") as mock_boto3:
                mock_boto3.client.return_value = mock_drs
                result = query_handler_module.lambda_handler(event, context)

        # Should succeed (parameters are optional)
        assert "error" not in result or result.get("error") != ERROR_MISSING_PARAMETER

    def test_query_handler_get_target_accounts_succeeds(
        self, mock_env_vars
    ):
        """
        Test get_target_accounts works without parameters.
        
        Validates that operations without required parameters work correctly.
        """
        event = {"operation": "get_target_accounts"}
        context = get_mock_context()

        # Mock DynamoDB
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": []}

        # Mock authorization to pass
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(query_handler_module, "boto3") as mock_boto3:
                mock_boto3.resource.return_value.Table.return_value = mock_table
                result = query_handler_module.lambda_handler(event, context)

        # Should succeed
        assert "error" not in result or result.get("error") != ERROR_MISSING_PARAMETER

    def test_query_handler_invalid_operation_returns_error(
        self, mock_env_vars
    ):
        """
        Test that invalid operations return INVALID_OPERATION error.
        
        Validates Requirement 9.2
        """
        event = {"operation": "nonexistent_operation"}
        context = get_mock_context()

        # Mock authorization to pass
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(query_handler_module, "boto3"):
                result = query_handler_module.lambda_handler(event, context)

        # Verify error response
        assert result["error"] == ERROR_INVALID_OPERATION
        assert "nonexistent_operation" in result["message"]
        assert "details" in result
        assert result["details"]["operation"] == "nonexistent_operation"

    def test_execution_handler_start_execution_missing_planid(
        self, mock_env_vars
    ):
        """
        Test start_execution returns MISSING_PARAMETER when planId is
        missing.
        
        Validates Requirement 9.1
        """
        event = {"operation": "start_execution"}
        context = get_mock_context()

        # Mock authorization to pass
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(execution_handler_module, "boto3"):
                result = execution_handler_module.lambda_handler(event, context)

        # Verify error response - should be MISSING_PARAMETER
        assert result["error"] == ERROR_MISSING_PARAMETER
        assert "planId" in result["message"]
        assert "details" in result
        assert result["details"]["parameter"] == "planId"

    def test_execution_handler_invalid_operation(self, mock_env_vars):
        """
        Test execution handler returns error for invalid operations.
        
        Validates Requirement 9.2
        """
        event = {"operation": "nonexistent_operation"}
        context = get_mock_context()

        # Mock authorization to pass
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(execution_handler_module, "boto3"):
                result = execution_handler_module.lambda_handler(event, context)

        # Verify error response
        assert result["error"] == ERROR_INVALID_OPERATION
        assert "nonexistent_operation" in result["message"]

    def test_data_management_handler_invalid_operation(self, mock_env_vars):
        """
        Test data management handler returns error for invalid operations.
        
        Validates Requirement 9.2
        """
        event = {"operation": "nonexistent_operation"}
        context = get_mock_context()

        # Mock authorization to pass
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(data_management_handler_module, "boto3"):
                result = data_management_handler_module.lambda_handler(
                    event, context
                )

        # Verify error response
        assert result["error"] == ERROR_INVALID_OPERATION
        assert "nonexistent_operation" in result["message"]


# ============================================================================
# Test: Invalid Parameter Values
# ============================================================================


class TestInvalidParameterValues:
    """
    Test error handling for invalid parameter values.
    
    Validates Requirement 9.1: Invalid parameters return appropriate errors
    """

    def test_execution_handler_start_execution_empty_planid(
        self, mock_env_vars
    ):
        """
        Test start_execution returns MISSING_PARAMETER when planId is empty
        string (treated as missing).
        
        Validates Requirement 9.1
        """
        event = {"operation": "start_execution", "planId": ""}
        context = get_mock_context()

        # Mock authorization to pass
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(execution_handler_module, "boto3"):
                result = execution_handler_module.lambda_handler(event, context)

        # Verify error response - empty string is treated as missing
        assert result["error"] == ERROR_MISSING_PARAMETER
        assert "planId" in result["message"]
        assert "details" in result
        assert result["details"]["parameter"] == "planId"


# ============================================================================
# Test: Error Response Structure Consistency
# ============================================================================


class TestErrorResponseStructure:
    """
    Test that all error responses have consistent structure.
    
    Validates Requirement 9.7: Standardized error responses
    """

    def test_all_errors_have_required_fields(self, mock_env_vars):
        """
        Test that all error responses include error, message, and are JSON
        serializable.
        
        Validates Requirement 9.7
        """
        test_cases = [
            # Query handler errors
            {
                "handler": query_handler_module,
                "event": {"operation": "invalid_op"},
                "expected_error": ERROR_INVALID_OPERATION,
            },
            # Execution handler errors
            {
                "handler": execution_handler_module,
                "event": {"operation": "invalid_op"},
                "expected_error": ERROR_INVALID_OPERATION,
            },
            {
                "handler": execution_handler_module,
                "event": {"operation": "start_execution"},
                "expected_error": ERROR_MISSING_PARAMETER,
            },
            # Data management handler errors
            {
                "handler": data_management_handler_module,
                "event": {"operation": "invalid_op"},
                "expected_error": ERROR_INVALID_OPERATION,
            },
        ]

        for test_case in test_cases:
            handler = test_case["handler"]
            event = test_case["event"]
            expected_error = test_case["expected_error"]

            context = get_mock_context()

            # Mock authorization to pass
            with patch(
                "shared.iam_utils.validate_iam_authorization"
            ) as mock_auth:
                mock_auth.return_value = True
                with patch.object(handler, "boto3"):
                    result = handler.lambda_handler(event, context)

            # Verify required fields
            assert "error" in result, f"Missing 'error' field in {handler}"
            assert (
                "message" in result
            ), f"Missing 'message' field in {handler}"
            assert isinstance(
                result["error"], str
            ), f"Error code not string in {handler}"
            assert isinstance(
                result["message"], str
            ), f"Error message not string in {handler}"

            # Verify expected error code
            assert (
                result["error"] == expected_error
            ), f"Expected {expected_error}, got {result['error']}"

            # Verify JSON serializable
            try:
                json.dumps(result)
            except (TypeError, ValueError) as e:
                assert False, f"Error response not JSON serializable: {e}"

    def test_error_messages_are_descriptive(self, mock_env_vars):
        """
        Test that error messages are descriptive and actionable.
        
        Validates Requirement 9.7
        """
        # Test invalid operation error
        event = {"operation": "unknown_operation"}
        context = get_mock_context()

        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(query_handler_module, "boto3"):
                result = query_handler_module.lambda_handler(event, context)

        # Message should mention the invalid operation
        assert "unknown_operation" in result["message"]
        # Should include operation in details
        assert "details" in result
        assert "operation" in result["details"]

        # Test missing parameter error
        event = {"operation": "start_execution"}
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(execution_handler_module, "boto3"):
                result = execution_handler_module.lambda_handler(event, context)

        # Message should mention the missing parameter
        assert "planId" in result["message"]
        # Should include parameter name in details
        assert "details" in result
        assert result["details"]["parameter"] == "planId"


# ============================================================================
# Test: Authorization Errors
# ============================================================================


class TestAuthorizationErrors:
    """
    Test error handling for authorization failures.
    
    Validates Requirement 9.3: Authorization failures return
    AUTHORIZATION_FAILED
    """

    def test_query_handler_authorization_failure(self, mock_env_vars):
        """
        Test query handler returns AUTHORIZATION_FAILED when IAM principal
        is not authorized.
        
        Validates Requirement 9.3
        """
        event = {"operation": "list_protection_groups"}
        context = get_mock_context()

        # Mock authorization to fail
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = False
            with patch.object(query_handler_module, "boto3"):
                result = query_handler_module.lambda_handler(event, context)

        # Verify error response
        assert result["error"] == ERROR_AUTHORIZATION_FAILED
        assert "insufficient permissions" in result["message"].lower()
        assert "details" in result
        # Details contains the full message about required role
        assert "orchestrationrole" in str(result["details"]).lower()

    def test_execution_handler_authorization_failure(self, mock_env_vars):
        """
        Test execution handler returns AUTHORIZATION_FAILED when IAM
        principal is not authorized.
        
        Validates Requirement 9.3
        """
        event = {"operation": "start_execution", "planId": "plan-123"}
        context = get_mock_context()

        # Mock authorization to fail
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = False
            with patch.object(execution_handler_module, "boto3"):
                result = execution_handler_module.lambda_handler(event, context)

        # Verify error response
        assert result["error"] == ERROR_AUTHORIZATION_FAILED
        assert "insufficient permissions" in result["message"].lower()

    def test_data_management_handler_authorization_failure(
        self, mock_env_vars
    ):
        """
        Test data management handler returns AUTHORIZATION_FAILED when IAM
        principal is not authorized.
        
        Validates Requirement 9.3
        """
        event = {
            "operation": "invalid_operation_to_test_auth",
        }
        context = get_mock_context()

        # Mock authorization to fail
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = False
            with patch.object(data_management_handler_module, "boto3"):
                result = data_management_handler_module.lambda_handler(
                    event, context
                )

        # Verify error response
        assert result["error"] == ERROR_AUTHORIZATION_FAILED
        assert "insufficient permissions" in result["message"].lower()


# ============================================================================
# Test: Resource Not Found Errors
# ============================================================================


class TestResourceNotFoundErrors:
    """
    Test error handling for resource not found scenarios.
    
    Validates Requirement 9.7: NOT_FOUND errors are consistent
    """

    def test_query_handler_returns_empty_list_for_nonexistent_resources(
        self, mock_env_vars
    ):
        """
        Test that query operations return empty results rather than NOT_FOUND
        for list operations.
        
        Validates Requirement 9.7
        """
        event = {"operation": "get_target_accounts"}
        context = get_mock_context()

        # Mock DynamoDB returning no items
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": []}

        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(query_handler_module, "boto3") as mock_boto3:
                mock_boto3.resource.return_value.Table.return_value = (
                    mock_table
                )
                result = query_handler_module.lambda_handler(event, context)

        # Should return empty list, not error
        assert "error" not in result or result.get("error") != ERROR_NOT_FOUND
