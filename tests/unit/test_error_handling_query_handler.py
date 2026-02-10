"""
Unit tests for error handling in query-handler.

Tests comprehensive error scenarios including:
- Missing required parameters
- Invalid operation names
- Authorization failures
- DynamoDB errors
- DRS API errors
- Unexpected exceptions
- Error response structure consistency

Validates Requirements 9.1-9.7 from direct-lambda-invocation-mode spec.
"""

import json
import os
import sys
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.response_utils import (  # noqa: E402
    ERROR_AUTHORIZATION_FAILED,
    ERROR_DRS_ERROR,
    ERROR_DYNAMODB_ERROR,
    ERROR_INTERNAL_ERROR,
    ERROR_INVALID_INVOCATION,
    ERROR_INVALID_OPERATION,
    ERROR_INVALID_PARAMETER,
    ERROR_MISSING_PARAMETER,
    ERROR_NOT_FOUND,
)


class TestMissingParameterErrors:
    """Test missing required parameter error handling."""

    @patch("query_handler.index.boto3")
    def test_missing_operation_field(self, mock_boto3):
        """Test error when operation field is missing."""
        from query_handler.index import lambda_handler

        # Event without operation field
        event = {"queryParams": {"limit": 50}}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should return error response
        assert result["error"] == ERROR_INVALID_INVOCATION
        assert "operation" in result["message"].lower()

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_missing_required_parameter_for_operation(
        self, mock_validate, mock_boto3
    ):
        """Test error when required parameter for operation is missing."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        # get_protection_group requires groupId
        event = {"operation": "get_protection_group"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should return error indicating missing parameter
        assert result["error"] == ERROR_MISSING_PARAMETER
        assert "groupId" in result["message"]
        assert result["details"]["parameter"] == "groupId"

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_missing_server_id_for_launch_config(
        self, mock_validate, mock_boto3
    ):
        """Test error when serverId is missing for get_server_launch_config."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        # get_server_launch_config requires both groupId and serverId
        event = {
            "operation": "get_server_launch_config",
            "groupId": "pg-123",
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should return error indicating missing serverId
        assert result["error"] == ERROR_MISSING_PARAMETER
        assert "serverId" in result["message"]
        assert result["details"]["parameter"] == "serverId"


class TestInvalidOperationErrors:
    """Test invalid operation name error handling."""

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_invalid_operation_name(self, mock_validate, mock_boto3):
        """Test error when operation name is not supported."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        event = {"operation": "invalid_operation_name"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should return error with supported operations list
        assert result["error"] == ERROR_INVALID_OPERATION
        assert "invalid_operation_name" in result["message"]
        assert "operation" in result["details"]
        assert result["details"]["operation"] == "invalid_operation_name"

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_typo_in_operation_name(self, mock_validate, mock_boto3):
        """Test error when operation name has typo."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        # Common typo: list_protection_group (singular instead of plural)
        event = {"operation": "list_protection_group"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should return error indicating invalid operation
        assert result["error"] == ERROR_INVALID_OPERATION
        assert "list_protection_group" in result["message"]


class TestAuthorizationErrors:
    """Test IAM authorization failure error handling."""

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_authorization_failure(self, mock_validate, mock_boto3):
        """Test error when IAM principal is not authorized."""
        from query_handler.index import lambda_handler

        # Simulate authorization failure
        mock_validate.return_value = False

        event = {"operation": "list_protection_groups"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should return authorization error
        assert result["error"] == ERROR_AUTHORIZATION_FAILED
        assert "not authorized" in result["message"].lower()

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_authorization_error_includes_details(
        self, mock_validate, mock_boto3
    ):
        """Test authorization error includes helpful details."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = False

        event = {"operation": "list_protection_groups"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should include details about required role
        assert "details" in result
        assert "requiredRole" in result["details"]


class TestDynamoDBErrors:
    """Test DynamoDB error handling."""

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_dynamodb_throttling_error(self, mock_validate, mock_boto3):
        """Test error when DynamoDB throttles requests."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DynamoDB throttling error
        mock_table = MagicMock()
        mock_table.scan.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ProvisionedThroughputExceededException",
                    "Message": "Rate exceeded",
                }
            },
            "Scan",
        )
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {"operation": "list_protection_groups"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should return DynamoDB error with retry guidance
        assert result["error"] == ERROR_DYNAMODB_ERROR
        assert "retryable" in result
        assert result["retryable"] is True

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_dynamodb_resource_not_found(self, mock_validate, mock_boto3):
        """Test error when DynamoDB table doesn't exist."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DynamoDB resource not found error
        mock_table = MagicMock()
        mock_table.scan.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Table not found",
                }
            },
            "Scan",
        )
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {"operation": "list_protection_groups"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should return DynamoDB error
        assert result["error"] == ERROR_DYNAMODB_ERROR
        assert "details" in result


class TestDRSAPIErrors:
    """Test DRS API error handling."""

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_drs_service_unavailable(self, mock_validate, mock_boto3):
        """Test error when DRS service is temporarily unavailable."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DRS service unavailable error
        mock_drs = MagicMock()
        mock_drs.describe_source_servers.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ServiceUnavailable",
                    "Message": "Service temporarily unavailable",
                }
            },
            "DescribeSourceServers",
        )
        mock_boto3.client.return_value = mock_drs

        event = {
            "operation": "get_drs_source_servers",
            "queryParams": {"region": "us-east-1"},
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should return DRS error with retry guidance
        assert result["error"] == ERROR_DRS_ERROR
        assert "retryable" in result
        assert result["retryable"] is True

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_drs_uninitialized_account(self, mock_validate, mock_boto3):
        """Test error when DRS is not initialized in account."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DRS uninitialized account error
        mock_drs = MagicMock()
        mock_drs.describe_source_servers.side_effect = ClientError(
            {
                "Error": {
                    "Code": "UninitializedAccountException",
                    "Message": "DRS not initialized",
                }
            },
            "DescribeSourceServers",
        )
        mock_boto3.client.return_value = mock_drs

        event = {
            "operation": "get_drs_source_servers",
            "queryParams": {"region": "us-east-1"},
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should return DRS error with details
        assert result["error"] == ERROR_DRS_ERROR
        assert "details" in result


class TestUnexpectedExceptions:
    """Test unexpected exception handling."""

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_unexpected_exception_sanitized(self, mock_validate, mock_boto3):
        """Test unexpected exception returns sanitized error."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock unexpected exception
        mock_table = MagicMock()
        mock_table.scan.side_effect = Exception(
            "Unexpected internal error with sensitive data"
        )
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {"operation": "list_protection_groups"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should return internal error with sanitized message
        assert result["error"] == ERROR_INTERNAL_ERROR
        assert "message" in result
        # Should not expose internal details in message
        assert "sensitive data" not in result["message"].lower()

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_exception_includes_operation_context(
        self, mock_validate, mock_boto3
    ):
        """Test exception error includes operation context."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock exception
        mock_table = MagicMock()
        mock_table.scan.side_effect = Exception("Unexpected error")
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {"operation": "list_protection_groups"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should include operation in details
        assert "details" in result
        assert "operation" in result["details"]
        assert result["details"]["operation"] == "list_protection_groups"


class TestErrorResponseStructure:
    """Test error response structure consistency."""

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_error_response_has_required_fields(
        self, mock_validate, mock_boto3
    ):
        """Test all error responses have required fields."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        # Test with invalid operation
        event = {"operation": "invalid_operation"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should have error and message fields
        assert "error" in result
        assert "message" in result
        assert isinstance(result["error"], str)
        assert isinstance(result["message"], str)

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_error_response_optional_details_field(
        self, mock_validate, mock_boto3
    ):
        """Test error responses can include optional details field."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        # Test with missing parameter
        event = {"operation": "get_protection_group"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should have details field with parameter info
        assert "details" in result
        assert isinstance(result["details"], dict)
        assert "parameter" in result["details"]

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_error_response_json_serializable(
        self, mock_validate, mock_boto3
    ):
        """Test error responses are JSON serializable."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        event = {"operation": "invalid_operation"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should be JSON serializable
        try:
            json.dumps(result)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Error response not JSON serializable: {e}")

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_retryable_errors_include_retry_guidance(
        self, mock_validate, mock_boto3
    ):
        """Test retryable errors include retry guidance."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DynamoDB throttling (retryable error)
        mock_table = MagicMock()
        mock_table.scan.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ProvisionedThroughputExceededException",
                    "Message": "Rate exceeded",
                }
            },
            "Scan",
        )
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {"operation": "list_protection_groups"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        result = lambda_handler(event, context)

        # Should include retryable flag
        assert "retryable" in result
        assert result["retryable"] is True


class TestErrorConsistencyAcrossOperations:
    """Test error handling consistency across different operations."""

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_missing_parameter_error_consistent(
        self, mock_validate, mock_boto3
    ):
        """Test missing parameter errors are consistent across operations."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        # Test multiple operations with missing parameters
        operations = [
            ("get_protection_group", "groupId"),
            ("get_recovery_plan", "planId"),
            ("get_execution", "executionId"),
        ]

        for operation, expected_param in operations:
            event = {"operation": operation}
            result = lambda_handler(event, context)

            # All should return same error code
            assert result["error"] == ERROR_MISSING_PARAMETER
            assert "details" in result
            assert result["details"]["parameter"] == expected_param

    @patch("query_handler.index.boto3")
    @patch("query_handler.index.validate_iam_authorization")
    def test_not_found_error_consistent(self, mock_validate, mock_boto3):
        """Test not found errors are consistent across operations."""
        from query_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DynamoDB returning no items
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_boto3.resource.return_value.Table.return_value = mock_table

        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        )

        # Test multiple operations with non-existent resources
        operations = [
            ("get_protection_group", "groupId", "pg-nonexistent"),
            ("get_recovery_plan", "planId", "plan-nonexistent"),
            ("get_execution", "executionId", "exec-nonexistent"),
        ]

        for operation, param_name, param_value in operations:
            event = {"operation": operation, param_name: param_value}
            result = lambda_handler(event, context)

            # All should return same error code
            assert result["error"] == ERROR_NOT_FOUND
            assert param_value in result["message"]
