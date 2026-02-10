"""
Unit tests for error handling in execution-handler.

Tests comprehensive error scenarios including:
- Missing required parameters
- Invalid operation names
- Authorization failures
- DynamoDB errors
- DRS API errors
- Step Functions errors
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
    ERROR_STEP_FUNCTIONS_ERROR,
)


class TestMissingParameterErrors:
    """Test missing required parameter error handling."""

    @patch("execution_handler.index.boto3")
    def test_missing_operation_field(self, mock_boto3):
        """Test error when operation field is missing."""
        from execution_handler.index import lambda_handler

        # Event without operation, action, or requestContext
        event = {"someField": "value"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should return error response
        assert result["error"] == ERROR_INVALID_INVOCATION
        assert "operation" in result["message"].lower()

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_missing_plan_id_for_start_execution(
        self, mock_validate, mock_boto3
    ):
        """Test error when planId is missing for start_execution."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # start_execution requires planId
        event = {"operation": "start_execution", "executionType": "DRILL"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should return error indicating missing planId
        assert result["error"] == ERROR_MISSING_PARAMETER
        assert "planId" in result["message"]
        assert result["details"]["parameter"] == "planId"

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_missing_execution_id_for_cancel(self, mock_validate, mock_boto3):
        """Test error when executionId is missing for cancel_execution."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # cancel_execution requires executionId
        event = {"operation": "cancel_execution"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should return error indicating missing executionId
        assert result["error"] == ERROR_MISSING_PARAMETER
        assert "executionId" in result["message"]
        assert result["details"]["parameter"] == "executionId"


class TestInvalidOperationErrors:
    """Test invalid operation name error handling."""

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_invalid_operation_name(self, mock_validate, mock_boto3):
        """Test error when operation name is not supported."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        event = {"operation": "invalid_operation_name"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should return error with operation name
        assert result["error"] == ERROR_INVALID_OPERATION
        assert "invalid_operation_name" in result["message"]
        assert "operation" in result["details"]

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_typo_in_operation_name(self, mock_validate, mock_boto3):
        """Test error when operation name has typo."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # Common typo: start_executions (plural)
        event = {"operation": "start_executions", "planId": "plan-123"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should return error indicating invalid operation
        assert result["error"] == ERROR_INVALID_OPERATION
        assert "start_executions" in result["message"]


class TestAuthorizationErrors:
    """Test IAM authorization failure error handling."""

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_authorization_failure(self, mock_validate, mock_boto3):
        """Test error when IAM principal is not authorized."""
        from execution_handler.index import lambda_handler

        # Simulate authorization failure
        mock_validate.return_value = False

        event = {"operation": "start_execution", "planId": "plan-123"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should return authorization error
        assert result["error"] == ERROR_AUTHORIZATION_FAILED
        assert "not authorized" in result["message"].lower()

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_authorization_error_includes_required_role(
        self, mock_validate, mock_boto3
    ):
        """Test authorization error includes required role details."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = False

        event = {"operation": "start_execution", "planId": "plan-123"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should include details about required role
        assert "details" in result
        assert "requiredRole" in result["details"]


class TestDynamoDBErrors:
    """Test DynamoDB error handling."""

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_dynamodb_throttling_error(self, mock_validate, mock_boto3):
        """Test error when DynamoDB throttles requests."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DynamoDB throttling error
        mock_table = MagicMock()
        mock_table.get_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ProvisionedThroughputExceededException",
                    "Message": "Rate exceeded",
                }
            },
            "GetItem",
        )
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {"operation": "get_execution", "executionId": "exec-123"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should return DynamoDB error with retry guidance
        assert result["error"] == ERROR_DYNAMODB_ERROR
        assert "retryable" in result
        assert result["retryable"] is True

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_dynamodb_conditional_check_failed(
        self, mock_validate, mock_boto3
    ):
        """Test error when DynamoDB conditional check fails."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DynamoDB conditional check failure
        mock_table = MagicMock()
        mock_table.update_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ConditionalCheckFailedException",
                    "Message": "Condition not met",
                }
            },
            "UpdateItem",
        )
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {"operation": "cancel_execution", "executionId": "exec-123"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should return error indicating invalid state
        assert result["error"] in [
            ERROR_INVALID_STATE,
            ERROR_DYNAMODB_ERROR,
        ]


class TestDRSAPIErrors:
    """Test DRS API error handling."""

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_drs_service_unavailable(self, mock_validate, mock_boto3):
        """Test error when DRS service is temporarily unavailable."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DRS service unavailable error
        mock_drs = MagicMock()
        mock_drs.start_recovery.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ServiceUnavailable",
                    "Message": "Service temporarily unavailable",
                }
            },
            "StartRecovery",
        )
        mock_boto3.client.return_value = mock_drs

        # Mock DynamoDB to return valid plan
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {"planId": "plan-123", "status": "ACTIVE"}
        }
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {"operation": "start_execution", "planId": "plan-123"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should return DRS error with retry guidance
        assert result["error"] == ERROR_DRS_ERROR
        assert "retryable" in result
        assert result["retryable"] is True

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_drs_resource_not_found(self, mock_validate, mock_boto3):
        """Test error when DRS resource is not found."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DRS resource not found error
        mock_drs = MagicMock()
        mock_drs.describe_recovery_instances.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Recovery instance not found",
                }
            },
            "DescribeRecoveryInstances",
        )
        mock_boto3.client.return_value = mock_drs

        event = {
            "operation": "get_recovery_instances",
            "executionId": "exec-123",
        }
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should return DRS error
        assert result["error"] == ERROR_DRS_ERROR
        assert "details" in result


class TestStepFunctionsErrors:
    """Test Step Functions error handling."""

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_step_functions_execution_not_found(
        self, mock_validate, mock_boto3
    ):
        """Test error when Step Functions execution is not found."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock Step Functions execution not found error
        mock_sfn = MagicMock()
        mock_sfn.stop_execution.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ExecutionDoesNotExist",
                    "Message": "Execution not found",
                }
            },
            "StopExecution",
        )
        mock_boto3.client.return_value = mock_sfn

        event = {"operation": "cancel_execution", "executionId": "exec-123"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should return Step Functions error
        assert result["error"] == ERROR_STEP_FUNCTIONS_ERROR
        assert "details" in result

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_step_functions_invalid_state(self, mock_validate, mock_boto3):
        """Test error when Step Functions execution is in invalid state."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock Step Functions invalid state error
        mock_sfn = MagicMock()
        mock_sfn.stop_execution.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ExecutionAlreadyStopped",
                    "Message": "Execution already stopped",
                }
            },
            "StopExecution",
        )
        mock_boto3.client.return_value = mock_sfn

        event = {"operation": "cancel_execution", "executionId": "exec-123"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should return invalid state error
        assert result["error"] in [
            ERROR_INVALID_STATE,
            ERROR_STEP_FUNCTIONS_ERROR,
        ]


class TestUnexpectedExceptions:
    """Test unexpected exception handling."""

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_unexpected_exception_sanitized(self, mock_validate, mock_boto3):
        """Test unexpected exception returns sanitized error."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock unexpected exception
        mock_table = MagicMock()
        mock_table.get_item.side_effect = Exception(
            "Unexpected internal error with sensitive data"
        )
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {"operation": "get_execution", "executionId": "exec-123"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should return internal error with sanitized message
        assert result["error"] == ERROR_INTERNAL_ERROR
        assert "message" in result
        # Should not expose internal details in message
        assert "sensitive data" not in result["message"].lower()

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_exception_includes_operation_context(
        self, mock_validate, mock_boto3
    ):
        """Test exception error includes operation context."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock exception
        mock_table = MagicMock()
        mock_table.get_item.side_effect = Exception("Unexpected error")
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {"operation": "get_execution", "executionId": "exec-123"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should include operation in details
        assert "details" in result
        assert "operation" in result["details"]
        assert result["details"]["operation"] == "get_execution"


class TestErrorResponseStructure:
    """Test error response structure consistency."""

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_error_response_has_required_fields(
        self, mock_validate, mock_boto3
    ):
        """Test all error responses have required fields."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # Test with invalid operation
        event = {"operation": "invalid_operation"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should have error and message fields
        assert "error" in result
        assert "message" in result
        assert isinstance(result["error"], str)
        assert isinstance(result["message"], str)

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_error_response_json_serializable(
        self, mock_validate, mock_boto3
    ):
        """Test error responses are JSON serializable."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        event = {"operation": "invalid_operation"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should be JSON serializable
        try:
            json.dumps(result)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Error response not JSON serializable: {e}")

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_retryable_errors_include_retry_flag(
        self, mock_validate, mock_boto3
    ):
        """Test retryable errors include retry flag."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DynamoDB throttling (retryable error)
        mock_table = MagicMock()
        mock_table.get_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ProvisionedThroughputExceededException",
                    "Message": "Rate exceeded",
                }
            },
            "GetItem",
        )
        mock_boto3.resource.return_value.Table.return_value = mock_table

        event = {"operation": "get_execution", "executionId": "exec-123"}
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        result = lambda_handler(event, context)

        # Should include retryable flag
        assert "retryable" in result
        assert result["retryable"] is True


class TestErrorConsistencyAcrossOperations:
    """Test error handling consistency across different operations."""

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_missing_parameter_error_consistent(
        self, mock_validate, mock_boto3
    ):
        """Test missing parameter errors are consistent across operations."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True
        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        # Test multiple operations with missing parameters
        operations = [
            ("start_execution", "planId"),
            ("cancel_execution", "executionId"),
            ("pause_execution", "executionId"),
            ("resume_execution", "executionId"),
            ("terminate_instances", "executionId"),
            ("get_recovery_instances", "executionId"),
        ]

        for operation, expected_param in operations:
            event = {"operation": operation}
            result = lambda_handler(event, context)

            # All should return same error code
            assert result["error"] == ERROR_MISSING_PARAMETER
            assert "details" in result
            assert result["details"]["parameter"] == expected_param

    @patch("execution_handler.index.boto3")
    @patch("execution_handler.index.validate_iam_authorization")
    def test_not_found_error_consistent(self, mock_validate, mock_boto3):
        """Test not found errors are consistent across operations."""
        from execution_handler.index import lambda_handler

        mock_validate.return_value = True

        # Mock DynamoDB returning no items
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_boto3.resource.return_value.Table.return_value = mock_table

        context = MagicMock()
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
        )

        # Test operations with non-existent resources
        operations = [
            ("get_execution", "executionId", "exec-nonexistent"),
            ("cancel_execution", "executionId", "exec-nonexistent"),
        ]

        for operation, param_name, param_value in operations:
            event = {"operation": operation, param_name: param_value}
            result = lambda_handler(event, context)

            # All should return same error code
            assert result["error"] == ERROR_NOT_FOUND
            assert param_value in result["message"]
