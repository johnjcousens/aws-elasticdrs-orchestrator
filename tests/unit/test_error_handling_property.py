"""
Property-based tests for error response consistency across all handlers.

Tests that error handling is consistent across query-handler, execution-handler,
and data-management-handler using property-based testing with Hypothesis.

Validates Requirements 9.1-9.7 from direct-lambda-invocation-mode spec:
- 9.1: Missing required parameters return 400 with MISSING_PARAMETER
- 9.2: Invalid operations return 400 with INVALID_OPERATION
- 9.3: Authorization failures return 403 with AUTHORIZATION_FAILED
- 9.4: DynamoDB errors return 500 with DATABASE_ERROR
- 9.5: DRS API errors return 502 with DRS_API_ERROR
- 9.6: Unexpected exceptions return 500 with INTERNAL_ERROR
- 9.7: All error responses include errorCode, message, and optional details

Uses Hypothesis to generate various error scenarios and verify consistent
error response structure across all handlers.

PATCHING STRATEGY:
- validate_iam_authorization is imported from shared.iam_utils in all handlers
- We patch it at the source: "shared.iam_utils.validate_iam_authorization"
- This works because Python imports create references to the original function
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from hypothesis import given, settings, strategies as st

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.response_utils import (  # noqa: E402
    ERROR_AUTHORIZATION_FAILED,
    ERROR_DRS_ERROR,
    ERROR_DYNAMODB_ERROR,
    ERROR_INTERNAL_ERROR,
    ERROR_INVALID_INVOCATION,
    ERROR_INVALID_OPERATION,
    ERROR_MISSING_PARAMETER,
    ERROR_NOT_FOUND,
)


def get_lambda_handler_module(handler_name):
    """
    Import and return the handler module for patching and testing.
    
    Args:
        handler_name: One of 'query_handler', 'execution_handler', 'data_management_handler'
    
    Returns:
        Tuple of (lambda_handler function, module object for patching)
    """
    import importlib
    
    # Map handler names to module names (with hyphens)
    module_map = {
        "query_handler": "query-handler.index",
        "execution_handler": "execution-handler.index",
        "data_management_handler": "data-management-handler.index",
    }
    
    module_name = module_map[handler_name]
    module = importlib.import_module(module_name)
    return module.lambda_handler, module


# Strategy for generating handler names
handler_names = st.sampled_from(
    ["query_handler", "execution_handler", "data_management_handler"]
)

# Strategy for generating error codes
error_codes = st.sampled_from(
    [
        "ProvisionedThroughputExceededException",
        "ResourceNotFoundException",
        "ConditionalCheckFailedException",
        "ServiceUnavailable",
        "UninitializedAccountException",
        "AccessDeniedException",
    ]
)

# Strategy for generating operation names (valid and invalid)
valid_operations = st.sampled_from(
    [
        "list_protection_groups",
        "get_protection_group",
        "list_recovery_plans",
        "get_recovery_plan",
        "list_executions",
        "get_execution",
        "start_execution",
        "cancel_execution",
        "create_protection_group",
        "update_protection_group",
        "delete_protection_group",
    ]
)

invalid_operations = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu"), min_codepoint=97, max_codepoint=122
    ),
    min_size=5,
    max_size=30,
).filter(
    lambda x: x
    not in [
        "list_protection_groups",
        "get_protection_group",
        "list_recovery_plans",
        "get_recovery_plan",
        "list_executions",
        "get_execution",
        "start_execution",
        "cancel_execution",
        "create_protection_group",
        "update_protection_group",
        "delete_protection_group",
    ]
)


class TestErrorResponseStructureProperty:
    """
    Property-based tests for error response structure consistency.

    **Validates: Requirement 9.7**
    """

    @given(
        handler=handler_names,
        operation=invalid_operations,
    )
    @settings(max_examples=50)
    def test_invalid_operation_error_structure_consistent(
        self, handler, operation
    ):
        """
        Property: For any handler and any invalid operation name, the error
        response should have consistent structure with error, message, and
        details fields.

        **Validates: Requirements 9.2, 9.7**
        """
        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Create event with invalid operation
        event = {"operation": operation}
        context = MagicMock()
        context.invoked_function_arn = (
            f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"
        )

        # Mock authorization to pass - patch at source module
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(handler_module, "boto3"):
                result = lambda_handler(event, context)

        # Verify error response structure
        assert "error" in result, "Error response must have 'error' field"
        assert (
            "message" in result
        ), "Error response must have 'message' field"
        assert isinstance(
            result["error"], str
        ), "Error code must be a string"
        assert isinstance(
            result["message"], str
        ), "Error message must be a string"

        # For invalid operation, should return INVALID_OPERATION
        assert (
            result["error"] == ERROR_INVALID_OPERATION
        ), f"Invalid operation should return {ERROR_INVALID_OPERATION}"

        # Should include operation in details
        assert "details" in result, "Error should include details"
        assert (
            "operation" in result["details"]
        ), "Details should include operation"

        # Response should be JSON serializable
        try:
            json.dumps(result)
        except (TypeError, ValueError) as e:
            assert False, f"Error response not JSON serializable: {e}"

    @given(handler=handler_names)
    @settings(max_examples=50)
    def test_missing_operation_field_error_consistent(self, handler):
        """
        Property: For any handler, when the operation field is missing,
        the error response should be consistent with INVALID_INVOCATION
        error code.

        **Validates: Requirements 9.1, 9.7**
        """
        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Create event without operation field
        event = {"someField": "value"}
        context = MagicMock()
        context.invoked_function_arn = (
            f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"
        )

        with patch.object(handler_module, "boto3"):
            result = lambda_handler(event, context)

        # Verify error response structure
        assert "error" in result
        assert "message" in result
        assert result["error"] == ERROR_INVALID_INVOCATION
        assert "operation" in result["message"].lower()

        # Response should be JSON serializable
        json.dumps(result)

    @given(handler=handler_names)
    @settings(max_examples=50)
    def test_authorization_failure_error_consistent(self, handler):
        """
        Property: For any handler, when authorization fails, the error
        response should be consistent with AUTHORIZATION_FAILED error code.

        **Validates: Requirements 9.3, 9.7**
        """
        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Create valid event
        event = {"operation": "list_protection_groups"}
        context = MagicMock()
        context.invoked_function_arn = (
            f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"
        )

        # Mock authorization to fail - patch at source module
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = False
            with patch.object(handler_module, "boto3"):
                result = lambda_handler(event, context)

        # Verify error response structure
        assert "error" in result
        assert "message" in result
        assert result["error"] == ERROR_AUTHORIZATION_FAILED
        assert "not authorized" in result["message"].lower()

        # Should include required role in details
        assert "details" in result
        assert "requiredRole" in result["details"]

        # Response should be JSON serializable
        json.dumps(result)


class TestDynamoDBErrorConsistencyProperty:
    """
    Property-based tests for DynamoDB error handling consistency.

    **Validates: Requirement 9.4**
    """

    @given(handler=handler_names, error_code=error_codes)
    @settings(max_examples=50)
    def test_dynamodb_error_structure_consistent(self, handler, error_code):
        """
        Property: For any handler and any DynamoDB error code, the error
        response should have consistent structure with DYNAMODB_ERROR code
        and retryable flag for throttling errors.

        **Validates: Requirements 9.4, 9.7**
        """
        # Skip non-DynamoDB error codes for this test
        if error_code not in [
            "ProvisionedThroughputExceededException",
            "ResourceNotFoundException",
            "ConditionalCheckFailedException",
        ]:
            return

        # Determine operation based on handler
        if handler == "query_handler":
            operation = "list_protection_groups"
        elif handler == "execution_handler":
            operation = "get_execution"
        else:
            operation = "create_protection_group"

        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Create event
        event = {"operation": operation}
        if operation == "get_execution":
            event["executionId"] = "exec-123"
        elif operation == "create_protection_group":
            event["body"] = {"name": "Test"}

        context = MagicMock()
        context.invoked_function_arn = (
            f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"
        )

        # Mock DynamoDB error
        mock_table = MagicMock()
        if operation == "list_protection_groups":
            mock_table.scan.side_effect = ClientError(
                {"Error": {"Code": error_code, "Message": "DynamoDB error"}},
                "Scan",
            )
        elif operation == "get_execution":
            mock_table.get_item.side_effect = ClientError(
                {"Error": {"Code": error_code, "Message": "DynamoDB error"}},
                "GetItem",
            )
        else:
            mock_table.put_item.side_effect = ClientError(
                {"Error": {"Code": error_code, "Message": "DynamoDB error"}},
                "PutItem",
            )

        # Mock authorization to pass - patch at source module
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(handler_module, "boto3") as mock_boto3:
                mock_boto3.resource.return_value.Table.return_value = (
                    mock_table
                )
                result = lambda_handler(event, context)

        # Verify error response structure
        assert "error" in result
        assert "message" in result

        # Should return DYNAMODB_ERROR for DynamoDB errors
        assert result["error"] == ERROR_DYNAMODB_ERROR

        # Throttling errors should be retryable
        if error_code == "ProvisionedThroughputExceededException":
            assert "retryable" in result
            assert result["retryable"] is True

        # Response should be JSON serializable
        json.dumps(result)


class TestDRSErrorConsistencyProperty:
    """
    Property-based tests for DRS API error handling consistency.

    **Validates: Requirement 9.5**
    """

    @given(handler=handler_names, error_code=error_codes)
    @settings(max_examples=50)
    def test_drs_error_structure_consistent(self, handler, error_code):
        """
        Property: For any handler and any DRS error code, the error
        response should have consistent structure with DRS_ERROR code
        and retryable flag for service unavailable errors.

        **Validates: Requirements 9.5, 9.7**
        """
        # Skip non-DRS error codes for this test
        if error_code not in [
            "ServiceUnavailable",
            "UninitializedAccountException",
            "AccessDeniedException",
        ]:
            return

        # Determine operation and event based on handler
        if handler == "query_handler":
            operation = "get_drs_source_servers"
            event = {
                "operation": operation,
                "queryParams": {"region": "us-east-1"},
            }
        elif handler == "execution_handler":
            operation = "get_recovery_instances"
            event = {"operation": operation, "executionId": "exec-123"}
        else:
            operation = "sync_extended_source_servers"
            event = {"operation": operation, "targetAccountId": "123456789012"}

        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        context = MagicMock()
        context.invoked_function_arn = (
            f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"
        )

        # Mock DRS error
        mock_drs = MagicMock()
        mock_drs.describe_source_servers.side_effect = ClientError(
            {"Error": {"Code": error_code, "Message": "DRS error"}},
            "DescribeSourceServers",
        )
        mock_drs.describe_recovery_instances.side_effect = ClientError(
            {"Error": {"Code": error_code, "Message": "DRS error"}},
            "DescribeRecoveryInstances",
        )

        # Mock authorization to pass - patch at source module
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(handler_module, "boto3") as mock_boto3:
                mock_boto3.client.return_value = mock_drs
                result = lambda_handler(event, context)

        # Verify error response structure
        assert "error" in result
        assert "message" in result

        # Should return DRS_ERROR for DRS errors
        assert result["error"] == ERROR_DRS_ERROR

        # Service unavailable errors should be retryable
        if error_code == "ServiceUnavailable":
            assert "retryable" in result
            assert result["retryable"] is True

        # Should include details
        assert "details" in result

        # Response should be JSON serializable
        json.dumps(result)


class TestUnexpectedExceptionConsistencyProperty:
    """
    Property-based tests for unexpected exception handling consistency.

    **Validates: Requirement 9.6**
    """

    @given(handler=handler_names)
    @settings(max_examples=50)
    def test_unexpected_exception_error_consistent(self, handler):
        """
        Property: For any handler, when an unexpected exception occurs,
        the error response should be consistent with INTERNAL_ERROR code
        and sanitized message.

        **Validates: Requirements 9.6, 9.7**
        """
        # Determine operation based on handler
        if handler == "query_handler":
            operation = "list_protection_groups"
        elif handler == "execution_handler":
            operation = "get_execution"
        else:
            operation = "create_protection_group"

        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Create event
        event = {"operation": operation}
        if operation == "get_execution":
            event["executionId"] = "exec-123"
        elif operation == "create_protection_group":
            event["body"] = {"name": "Test"}

        context = MagicMock()
        context.invoked_function_arn = (
            f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"
        )

        # Mock unexpected exception with sensitive data
        mock_table = MagicMock()
        mock_table.scan.side_effect = Exception(
            "Unexpected error with sensitive data: password123"
        )
        mock_table.get_item.side_effect = Exception(
            "Unexpected error with sensitive data: password123"
        )
        mock_table.put_item.side_effect = Exception(
            "Unexpected error with sensitive data: password123"
        )

        # Mock authorization to pass - patch at source module
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(handler_module, "boto3") as mock_boto3:
                mock_boto3.resource.return_value.Table.return_value = (
                    mock_table
                )
                result = lambda_handler(event, context)

        # Verify error response structure
        assert "error" in result
        assert "message" in result

        # Should return INTERNAL_ERROR for unexpected exceptions
        assert result["error"] == ERROR_INTERNAL_ERROR

        # Message should be sanitized (not expose sensitive data)
        assert "password123" not in result["message"]
        assert "sensitive data" not in result["message"].lower()

        # Should include operation in details
        assert "details" in result
        assert "operation" in result["details"]
        assert result["details"]["operation"] == operation

        # Response should be JSON serializable
        json.dumps(result)


class TestMissingParameterConsistencyProperty:
    """
    Property-based tests for missing parameter error consistency.

    **Validates: Requirement 9.1**
    """

    @given(handler=handler_names)
    @settings(max_examples=50)
    def test_missing_parameter_error_consistent_across_handlers(
        self, handler
    ):
        """
        Property: For any handler, when a required parameter is missing,
        the error response should be consistent with MISSING_PARAMETER code
        and include the parameter name in details.

        **Validates: Requirements 9.1, 9.7**
        """
        # Determine operation and expected parameter based on handler
        if handler == "query_handler":
            # get_protection_group requires groupId
            operation = "get_protection_group"
            expected_param = "groupId"
        elif handler == "execution_handler":
            # start_execution requires planId
            operation = "start_execution"
            expected_param = "planId"
        else:
            # update_protection_group requires groupId
            operation = "update_protection_group"
            expected_param = "groupId"

        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Create event without required parameter
        event = {"operation": operation}
        if operation == "update_protection_group":
            event["body"] = {"name": "Test"}

        context = MagicMock()
        context.invoked_function_arn = (
            f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"
        )

        # Mock authorization to pass - patch at source module
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(handler_module, "boto3"):
                result = lambda_handler(event, context)

        # Verify error response structure
        assert "error" in result
        assert "message" in result

        # Should return MISSING_PARAMETER
        assert result["error"] == ERROR_MISSING_PARAMETER

        # Should include parameter name in message
        assert expected_param in result["message"]

        # Should include parameter in details
        assert "details" in result
        assert "parameter" in result["details"]
        assert result["details"]["parameter"] == expected_param

        # Response should be JSON serializable
        json.dumps(result)


class TestNotFoundErrorConsistencyProperty:
    """
    Property-based tests for resource not found error consistency.

    **Validates: Requirement 9.7**
    """

    @given(handler=handler_names)
    @settings(max_examples=50)
    def test_not_found_error_consistent_across_handlers(self, handler):
        """
        Property: For any handler, when a resource is not found,
        the error response should be consistent with NOT_FOUND code
        and include the resource identifier in the message.

        **Validates: Requirement 9.7**
        """
        # Determine operation and parameters based on handler
        if handler == "query_handler":
            operation = "get_protection_group"
            param_name = "groupId"
            param_value = "pg-nonexistent"
        elif handler == "execution_handler":
            operation = "get_execution"
            param_name = "executionId"
            param_value = "exec-nonexistent"
        else:
            operation = "update_protection_group"
            param_name = "groupId"
            param_value = "pg-nonexistent"

        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Create event
        event = {"operation": operation, param_name: param_value}
        if operation == "update_protection_group":
            event["body"] = {"name": "Test"}

        context = MagicMock()
        context.invoked_function_arn = (
            f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"
        )

        # Mock DynamoDB returning no item
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}

        # Mock authorization to pass - patch at source module
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(handler_module, "boto3") as mock_boto3:
                mock_boto3.resource.return_value.Table.return_value = (
                    mock_table
                )
                result = lambda_handler(event, context)

        # Verify error response structure
        assert "error" in result
        assert "message" in result

        # Should return NOT_FOUND
        assert result["error"] == ERROR_NOT_FOUND

        # Should include resource identifier in message
        assert param_value in result["message"]

        # Response should be JSON serializable
        json.dumps(result)


class TestErrorResponseJSONSerializability:
    """
    Property-based tests for error response JSON serializability.

    **Validates: Requirement 9.7**
    """

    @given(
        handler=handler_names,
        error_scenario=st.sampled_from(
            [
                "invalid_operation",
                "missing_parameter",
                "authorization_failed",
                "internal_error",
            ]
        ),
    )
    @settings(max_examples=100)
    def test_all_error_responses_json_serializable(
        self, handler, error_scenario
    ):
        """
        Property: For any handler and any error scenario, the error
        response should be JSON serializable.

        **Validates: Requirement 9.7**
        """
        # Determine operation based on handler
        if handler == "query_handler":
            operation = "list_protection_groups"
        elif handler == "execution_handler":
            operation = "start_execution"
        else:
            operation = "create_protection_group"

        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Create event based on error scenario
        if error_scenario == "invalid_operation":
            event = {"operation": "invalid_operation_xyz"}
        elif error_scenario == "missing_parameter":
            event = {"operation": operation}
        elif error_scenario == "authorization_failed":
            event = {"operation": operation}
            if operation == "start_execution":
                event["planId"] = "plan-123"
            elif operation == "create_protection_group":
                event["body"] = {"name": "Test"}
        else:  # internal_error
            event = {"operation": operation}
            if operation == "start_execution":
                event["planId"] = "plan-123"
            elif operation == "create_protection_group":
                event["body"] = {"name": "Test"}

        context = MagicMock()
        context.invoked_function_arn = (
            f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"
        )

        # Mock based on error scenario - patch at source module
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            if error_scenario == "authorization_failed":
                mock_auth.return_value = False
            else:
                mock_auth.return_value = True

            with patch.object(handler_module, "boto3") as mock_boto3:
                if error_scenario == "internal_error":
                    mock_table = MagicMock()
                    mock_table.scan.side_effect = Exception("Unexpected")
                    mock_table.get_item.side_effect = Exception("Unexpected")
                    mock_table.put_item.side_effect = Exception("Unexpected")
                    mock_boto3.resource.return_value.Table.return_value = (
                        mock_table
                    )

                result = lambda_handler(event, context)

        # Verify response is JSON serializable
        try:
            json_str = json.dumps(result)
            # Verify we can parse it back
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)
            assert "error" in parsed
            assert "message" in parsed
        except (TypeError, ValueError) as e:
            assert (
                False
            ), f"Error response not JSON serializable for {error_scenario}: {e}"
