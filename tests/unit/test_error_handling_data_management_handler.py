"""
Unit tests for error handling in data-management-handler.

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
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.response_utils import (  # noqa: E402
    ERROR_ALREADY_EXISTS,
    ERROR_AUTHORIZATION_FAILED,
    ERROR_DRS_ERROR,
    ERROR_DYNAMODB_ERROR,
    ERROR_INTERNAL_ERROR,
    ERROR_INVALID_INVOCATION,
    ERROR_INVALID_OPERATION,
    ERROR_INVALID_PARAMETER,
    ERROR_INVALID_STATE,
    ERROR_MISSING_PARAMETER,
    ERROR_NOT_FOUND,
)


class TestMissingParameterErrors:
    """Test missing required parameter error handling."""

    @patch("data_management_handler.index.boto3")
    def test_missing_operation_field(self, mock_boto3):
        """Test error when operation field is missing."""
        from data_management_handler.index import lambda_handler

        # Event without operation or requestContext
        event = {"body": {"name": "Test"}}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return error response
        assert result["error"] == ERROR_INVALID_INVOCATION
        assert "operation" in result["message"].lower()

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_missing_body_for_create_operation(
        self, mock_validate, mock_boto3
    ):
        """Test error when body is missing for create operation."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # create_protection_group requires body
        event = {"operation": "create_protection_group"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return error indicating missing body
        assert result["error"] == ERROR_MISSING_PARAMETER
        assert "body" in result["message"]
        assert result["details"]["parameter"] == "body"

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_missing_group_id_for_update(self, mock_validate, mock_boto3):
        """Test error when groupId is missing for update operation."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # update_protection_group requires groupId
        event = {
            "operation": "update_protection_group",
            "body": {"name": "Updated"},
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return error indicating missing groupId
        assert result["error"] == ERROR_MISSING_PARAMETER
        assert "groupId" in result["message"]
        assert result["details"]["parameter"] == "groupId"

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_missing_server_id_for_launch_config(
        self, mock_validate, mock_boto3
    ):
        """Test error when serverId is missing for server launch config."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # update_server_launch_config requires both groupId and serverId
        event = {
            "operation": "update_server_launch_config",
            "groupId": "pg-123",
            "body": {"instanceType": "t3.medium"},
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return error indicating missing serverId
        assert result["error"] == ERROR_MISSING_PARAMETER
        assert "serverId" in result["message"]
        assert result["details"]["parameter"] == "serverId"


class TestInvalidOperationErrors:
    """Test invalid operation name error handling."""

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_invalid_operation_name(self, mock_validate, mock_boto3):
        """Test error when operation name is not supported."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        event = {"operation": "invalid_operation_name"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return error with operation name
        assert result["error"] == ERROR_INVALID_OPERATION
        assert "invalid_operation_name" in result["message"]
        assert "operation" in result["details"]

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_typo_in_operation_name(self, mock_validate, mock_boto3):
        """Test error when operation name has typo."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # Common typo: create_protection_groups (plural)
        event = {
            "operation": "create_protection_groups",
            "body": {"name": "Test"},
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return error indicating invalid operation
        assert result["error"] == ERROR_INVALID_OPERATION
        assert "create_protection_groups" in result["message"]


class TestAuthorizationErrors:
    """Test IAM authorization failure error handling."""

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_authorization_failure(self, mock_validate, mock_boto3):
        """Test error when IAM principal is not authorized."""
        from data_management_handler.index import lambda_handler

        # Simulate authorization failure
        mock_validate.return_value = False

        event = {
            "operation": "create_protection_group",
            "body": {"name": "Test"},
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return authorization error
        assert result["error"] == ERROR_AUTHORIZATION_FAILED
        assert "not authorized" in result["message"].lower()

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_authorization_error_includes_required_role(
        self, mock_validate, mock_boto3
    ):
        """Test authorization error includes required role details."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = False

        event = {
            "operation": "delete_protection_group",
            "groupId": "pg-123",
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should include details about required role
        assert "details" in result
        assert "requiredRole" in result["details"]


class TestDynamoDBErrors:
    """Test DynamoDB error handling."""

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_dynamodb_throttling_error(self, mock_validate, mock_boto3):
        """Test error when DynamoDB throttles requests."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DynamoDB throttling error
        mock_table = MagicMock()
        mock_table.put_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ProvisionedThroughputExceededException",
                    "Message": "Rate exceeded",
                }
            },
            "PutItem",
        )
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {
            "operation": "create_protection_group",
            "body": {"name": "Test Group"},
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return DynamoDB error with retry guidance
        assert result["error"] == ERROR_DYNAMODB_ERROR
        assert "retryable" in result
        assert result["retryable"] is True

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_dynamodb_conditional_check_failed(
        self, mock_validate, mock_boto3
    ):
        """Test error when DynamoDB conditional check fails."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DynamoDB conditional check failure (duplicate)
        mock_table = MagicMock()
        mock_table.put_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ConditionalCheckFailedException",
                    "Message": "Item already exists",
                }
            },
            "PutItem",
        )
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {
            "operation": "create_protection_group",
            "body": {"name": "Test Group"},
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return error indicating duplicate or invalid state
        assert result["error"] in [
            ERROR_ALREADY_EXISTS,
            ERROR_INVALID_STATE,
            ERROR_DYNAMODB_ERROR,
        ]

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_dynamodb_item_not_found(self, mock_validate, mock_boto3):
        """Test error when DynamoDB item is not found."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DynamoDB returning no item
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {
            "operation": "update_protection_group",
            "groupId": "pg-nonexistent",
            "body": {"name": "Updated"},
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return not found error
        assert result["error"] == ERROR_NOT_FOUND
        assert "pg-nonexistent" in result["message"]


class TestDRSAPIErrors:
    """Test DRS API error handling."""

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_drs_service_unavailable(self, mock_validate, mock_boto3):
        """Test error when DRS service is temporarily unavailable."""
        from data_management_handler.index import lambda_handler

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
            "operation": "sync_extended_source_servers",
            "targetAccountId": "123456789012",
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return DRS error with retry guidance
        assert result["error"] == ERROR_DRS_ERROR
        assert "retryable" in result
        assert result["retryable"] is True

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_drs_access_denied(self, mock_validate, mock_boto3):
        """Test error when DRS access is denied."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DRS access denied error
        mock_drs = MagicMock()
        mock_drs.describe_source_servers.side_effect = ClientError(
            {
                "Error": {
                    "Code": "AccessDeniedException",
                    "Message": "Access denied",
                }
            },
            "DescribeSourceServers",
        )
        mock_boto3.client.return_value = mock_drs

        event = {
            "operation": "sync_extended_source_servers",
            "targetAccountId": "123456789012",
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return DRS error
        assert result["error"] == ERROR_DRS_ERROR
        assert "details" in result


class TestUnexpectedExceptions:
    """Test unexpected exception handling."""

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_unexpected_exception_sanitized(self, mock_validate, mock_boto3):
        """Test unexpected exception returns sanitized error."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock unexpected exception
        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception(
            "Unexpected internal error with sensitive data"
        )
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {
            "operation": "create_protection_group",
            "body": {"name": "Test"},
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return internal error with sanitized message
        assert result["error"] == ERROR_INTERNAL_ERROR
        assert "message" in result
        # Should not expose internal details in message
        assert "sensitive data" not in result["message"].lower()

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_exception_includes_operation_context(
        self, mock_validate, mock_boto3
    ):
        """Test exception error includes operation context."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock exception
        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("Unexpected error")
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {
            "operation": "create_protection_group",
            "body": {"name": "Test"},
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should include operation in details
        assert "details" in result
        assert "operation" in result["details"]
        assert result["details"]["operation"] == "create_protection_group"


class TestErrorResponseStructure:
    """Test error response structure consistency."""

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_error_response_has_required_fields(
        self, mock_validate, mock_boto3
    ):
        """Test all error responses have required fields."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # Test with invalid operation
        event = {"operation": "invalid_operation"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should have error and message fields
        assert "error" in result
        assert "message" in result
        assert isinstance(result["error"], str)
        assert isinstance(result["message"], str)

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_error_response_optional_details_field(
        self, mock_validate, mock_boto3
    ):
        """Test error responses can include optional details field."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # Test with missing parameter
        event = {"operation": "update_protection_group", "body": {"name": "Test"}}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should have details field with parameter info
        assert "details" in result
        assert isinstance(result["details"], dict)
        assert "parameter" in result["details"]

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_error_response_json_serializable(
        self, mock_validate, mock_boto3
    ):
        """Test error responses are JSON serializable."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        event = {"operation": "invalid_operation"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should be JSON serializable
        try:
            json.dumps(result)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Error response not JSON serializable: {e}")

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_retryable_errors_include_retry_flag(
        self, mock_validate, mock_boto3
    ):
        """Test retryable errors include retry flag."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DynamoDB throttling (retryable error)
        mock_table = MagicMock()
        mock_table.put_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ProvisionedThroughputExceededException",
                    "Message": "Rate exceeded",
                }
            },
            "PutItem",
        )
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {
            "operation": "create_protection_group",
            "body": {"name": "Test"},
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should include retryable flag
        assert "retryable" in result
        assert result["retryable"] is True


class TestErrorConsistencyAcrossOperations:
    """Test error handling consistency across different operations."""

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_missing_parameter_error_consistent(
        self, mock_validate, mock_boto3
    ):
        """Test missing parameter errors are consistent across operations."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        # Test multiple operations with missing parameters
        operations = [
            ("create_protection_group", "body"),
            ("update_protection_group", "groupId"),
            ("delete_protection_group", "groupId"),
            ("create_recovery_plan", "body"),
            ("update_recovery_plan", "planId"),
            ("delete_recovery_plan", "planId"),
        ]

        for operation, expected_param in operations:
            event = {"operation": operation}
            result = lambda_handler(event, context)

            # All should return same error code
            assert result["error"] == ERROR_MISSING_PARAMETER
            assert "details" in result
            assert result["details"]["parameter"] == expected_param

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_not_found_error_consistent(self, mock_validate, mock_boto3):
        """Test not found errors are consistent across operations."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DynamoDB returning no items
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_boto3.resource.return_value.Table.return_value = mock_table

        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        # Test operations with non-existent resources
        operations = [
            ("update_protection_group", "groupId", "pg-nonexistent"),
            ("delete_protection_group", "groupId", "pg-nonexistent"),
            ("update_recovery_plan", "planId", "plan-nonexistent"),
            ("delete_recovery_plan", "planId", "plan-nonexistent"),
        ]

        for operation, param_name, param_value in operations:
            event = {
                "operation": operation,
                param_name: param_value,
                "body": {"name": "Test"},
            }
            result = lambda_handler(event, context)

            # All should return same error code
            assert result["error"] == ERROR_NOT_FOUND
            assert param_value in result["message"]


class TestValidationErrors:
    """Test input validation error handling."""

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_invalid_ip_address_format(self, mock_validate, mock_boto3):
        """Test error when IP address format is invalid."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        event = {
            "operation": "validate_static_ip",
            "ipAddress": "invalid-ip",
            "subnetId": "subnet-123",
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return invalid parameter error
        assert result["error"] == ERROR_INVALID_PARAMETER
        assert "ipAddress" in result["message"]

    @patch("data_management_handler.index.boto3")
    @patch("data_management_handler.index.validate_iam_authorization")
    def test_invalid_json_in_body(self, mock_validate, mock_boto3):
        """Test error when body contains invalid JSON structure."""
        from data_management_handler.index import lambda_handler

        mock_validate.return_value = True

        # Body with invalid structure (missing required fields)
        event = {
            "operation": "create_protection_group",
            "body": {},  # Missing required 'name' field
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
        )

        result = lambda_handler(event, context)

        # Should return invalid parameter or missing parameter error
        assert result["error"] in [
            ERROR_INVALID_PARAMETER,
            ERROR_MISSING_PARAMETER,
        ]
