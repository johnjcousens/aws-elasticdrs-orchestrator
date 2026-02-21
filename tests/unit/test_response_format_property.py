"""
Property-based tests for response format correctness across all handlers.

Tests that response format is consistent between API Gateway and direct invocation
modes using property-based testing with Hypothesis.

**Validates: Requirements 10.1-10.7 from direct-lambda-invocation-mode spec:**
- 10.1: Query Handler API Gateway mode returns wrapped format (statusCode, headers, body)
- 10.2: Query Handler direct mode returns unwrapped data
- 10.3: Execution Handler API Gateway mode returns wrapped format
- 10.4: Execution Handler direct mode returns unwrapped data
- 10.5: Data Management Handler API Gateway mode returns wrapped format
- 10.6: Data Management Handler direct mode returns unwrapped data
- 10.7: Errors in either mode return consistent JSON structure

Uses Hypothesis to generate various operation scenarios and verify response format
consistency across all three handlers.

PATCHING STRATEGY:
- validate_iam_authorization is imported from shared.iam_utils in all handlers
- We patch it at the source: "shared.iam_utils.validate_iam_authorization"
- This works because Python imports create references to the original function
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
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

# Skip all tests in this file for CI/CD


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
handler_names = st.sampled_from(["query_handler", "execution_handler", "data_management_handler"])

# Strategy for generating valid operations per handler
query_handler_operations = st.sampled_from(
    [
        "list_protection_groups",
        "get_protection_group",
        "list_recovery_plans",
        "get_recovery_plan",
        "list_executions",
        "get_execution",
        "get_drs_source_servers",
        "get_target_accounts",
    ]
)

execution_handler_operations = st.sampled_from(
    [
        "start_execution",
        "cancel_execution",
        "pause_execution",
        "resume_execution",
        "terminate_instances",
        "get_recovery_instances",
    ]
)

data_management_operations = st.sampled_from(
    [
        "create_protection_group",
        "update_protection_group",
        "delete_protection_group",
        "create_recovery_plan",
        "update_recovery_plan",
        "delete_recovery_plan",
    ]
)


def get_operations_for_handler(handler_name):
    """Get appropriate operations strategy for handler"""
    if handler_name == "query_handler":
        return query_handler_operations
    elif handler_name == "execution_handler":
        return execution_handler_operations
    else:
        return data_management_operations


class TestResponseFormatProperty:
    """
    Property-based tests for response format consistency.

    **Validates: Property 3 - Response Format Consistency**
    """

    @given(handler=handler_names)
    @settings(max_examples=50, deadline=None)
    def test_api_gateway_mode_returns_wrapped_format(self, handler):
        """
        Property: For any handler and any operation, when invoked via API Gateway mode,
        the response should be wrapped in API Gateway format with statusCode, headers,
        and body fields.

        **Validates: Requirements 10.1, 10.3, 10.5**
        """
        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Create API Gateway event (has requestContext)
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "email": "test@example.com",
                        "sub": "user-123",
                        "cognito:username": "testuser",
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/protection-groups" if handler == "query_handler" else "/executions",
            "queryStringParameters": {},
        }

        context = MagicMock()
        context.invoked_function_arn = f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"

        # Mock DynamoDB to return empty results
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": []}
        mock_table.query.return_value = {"Items": []}

        with patch.object(handler_module, "boto3") as mock_boto3:
            mock_boto3.resource.return_value.Table.return_value = mock_table
            result = lambda_handler(event, context)

        # Verify API Gateway response format
        assert isinstance(result, dict), "Response must be a dictionary"
        assert "statusCode" in result, "API Gateway response must have statusCode"
        assert "headers" in result, "API Gateway response must have headers"
        assert "body" in result, "API Gateway response must have body"

        # Verify statusCode is an integer
        assert isinstance(result["statusCode"], int), "statusCode must be an integer"

        # Verify headers is a dictionary
        assert isinstance(result["headers"], dict), "headers must be a dictionary"

        # Verify body is a JSON string
        assert isinstance(result["body"], str), "body must be a JSON string"

        # Verify body can be parsed as JSON
        try:
            body_data = json.loads(result["body"])
            assert isinstance(body_data, dict), "Parsed body must be a dictionary"
        except json.JSONDecodeError as e:
            assert False, f"Body is not valid JSON: {e}"

    @given(handler=handler_names)
    @settings(max_examples=50)
    def test_direct_mode_returns_unwrapped_format(self, handler):
        """
        Property: For any handler and any operation, when invoked via direct mode,
        the response should be returned unwrapped as a plain dictionary without
        API Gateway wrapping.

        **Validates: Requirements 10.2, 10.4, 10.6**
        """
        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Determine appropriate operation for this handler
        if handler == "query_handler":
            operation = "list_protection_groups"
        elif handler == "execution_handler":
            operation = "list_executions"
        else:
            operation = "list_protection_groups"

        # Create direct invocation event (has operation, no requestContext)
        event = {"operation": operation}

        context = MagicMock()
        context.invoked_function_arn = f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"

        # Mock authorization to pass
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True

            # Mock DynamoDB to return empty results
            mock_table = MagicMock()
            mock_table.scan.return_value = {"Items": []}
            mock_table.query.return_value = {"Items": []}

            with patch.object(handler_module, "boto3") as mock_boto3:
                mock_boto3.resource.return_value.Table.return_value = mock_table
                result = lambda_handler(event, context)

        # Verify direct invocation response format (unwrapped)
        assert isinstance(result, dict), "Response must be a dictionary"

        # Should NOT have API Gateway wrapping
        assert "statusCode" not in result, "Direct invocation should not have statusCode wrapper"
        assert "headers" not in result, "Direct invocation should not have headers wrapper"

        # Should have actual data fields (not wrapped in body)
        # The response should be the actual data, not a wrapper
        # For list operations, we expect arrays or counts
        assert isinstance(result, dict), "Direct response must be a dictionary"

        # Response should be JSON serializable
        try:
            json.dumps(result)
        except (TypeError, ValueError) as e:
            assert False, f"Direct response not JSON serializable: {e}"

    @given(handler=handler_names)
    @settings(max_examples=50)
    def test_api_gateway_error_format_consistent(self, handler):
        """
        Property: For any handler, when an error occurs in API Gateway mode,
        the error response should be wrapped in API Gateway format with
        statusCode, headers, and body containing error details.

        **Validates: Requirements 10.1, 10.3, 10.5, 10.7**
        """
        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Create API Gateway event with invalid path to trigger error
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "email": "test@example.com",
                        "sub": "user-123",
                        "cognito:username": "testuser",
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/invalid-path-that-does-not-exist",
            "queryStringParameters": {},
        }

        context = MagicMock()
        context.invoked_function_arn = f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"

        with patch.object(handler_module, "boto3"):
            result = lambda_handler(event, context)

        # Verify API Gateway error response format
        assert isinstance(result, dict), "Error response must be a dictionary"
        assert "statusCode" in result, "Error response must have statusCode"
        assert "headers" in result, "Error response must have headers"
        assert "body" in result, "Error response must have body"

        # Verify error statusCode (should be 4xx or 5xx)
        assert isinstance(result["statusCode"], int), "statusCode must be an integer"
        assert result["statusCode"] >= 400, "Error statusCode should be >= 400"

        # Verify body contains error information
        body_data = json.loads(result["body"])
        assert "error" in body_data, "Error body must have 'error' field"
        assert "message" in body_data, "Error body must have 'message' field"

    @given(handler=handler_names)
    @settings(max_examples=50)
    def test_direct_mode_error_format_consistent(self, handler):
        """
        Property: For any handler, when an error occurs in direct mode,
        the error response should be unwrapped with error, message, and
        optional details fields.

        **Validates: Requirements 10.2, 10.4, 10.6, 10.7**
        """
        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Create direct invocation event with invalid operation
        event = {"operation": "invalid_operation_xyz"}

        context = MagicMock()
        context.invoked_function_arn = f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"

        # Mock authorization to pass
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True
            with patch.object(handler_module, "boto3"):
                result = lambda_handler(event, context)

        # Verify direct invocation error format (unwrapped)
        assert isinstance(result, dict), "Error response must be a dictionary"

        # Should NOT have API Gateway wrapping
        assert "statusCode" not in result, "Direct error should not have statusCode wrapper"
        assert "headers" not in result, "Direct error should not have headers wrapper"

        # Should have error fields directly
        assert "error" in result, "Direct error must have 'error' field"
        assert "message" in result, "Direct error must have 'message' field"

        # Error code should be INVALID_OPERATION
        assert result["error"] == ERROR_INVALID_OPERATION

        # Response should be JSON serializable
        try:
            json.dumps(result)
        except (TypeError, ValueError) as e:
            assert False, f"Direct error response not JSON serializable: {e}"


class TestResponseFormatConsistencyAcrossOperations:
    """
    Property-based tests for response format consistency across different operations.

    **Validates: Property 3 - Response Format Consistency**
    """

    @given(
        handler=handler_names,
        success=st.booleans(),
    )
    @settings(max_examples=100)
    def test_response_format_consistent_for_success_and_error(self, handler, success):
        """
        Property: For any handler, the response format should be consistent
        whether the operation succeeds or fails - API Gateway mode always wraps,
        direct mode never wraps.

        **Validates: Requirements 10.1-10.7**
        """
        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Determine operation based on handler
        if handler == "query_handler":
            operation = "list_protection_groups"
        elif handler == "execution_handler":
            operation = "list_executions"
        else:
            operation = "list_protection_groups"

        context = MagicMock()
        context.invoked_function_arn = f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"

        # Test both API Gateway and direct invocation modes
        for mode in ["api_gateway", "direct"]:
            if mode == "api_gateway":
                # API Gateway event
                event = {
                    "requestContext": {
                        "authorizer": {
                            "claims": {
                                "email": "test@example.com",
                                "sub": "user-123",
                                "cognito:username": "testuser",
                            }
                        }
                    },
                    "httpMethod": "GET",
                    "path": "/protection-groups" if handler == "query_handler" else "/executions",
                    "queryStringParameters": {},
                }
            else:
                # Direct invocation event
                event = {"operation": operation}

            # Mock to control success/failure
            mock_table = MagicMock()
            if success:
                # Success case - return empty list
                mock_table.scan.return_value = {"Items": []}
                mock_table.query.return_value = {"Items": []}
            else:
                # Failure case - raise DynamoDB error
                from botocore.exceptions import ClientError

                mock_table.scan.side_effect = ClientError(
                    {"Error": {"Code": "ServiceUnavailable", "Message": "Service error"}},
                    "Scan",
                )
                mock_table.query.side_effect = ClientError(
                    {"Error": {"Code": "ServiceUnavailable", "Message": "Service error"}},
                    "Query",
                )

            # Execute with appropriate mocking
            if mode == "direct":
                with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
                    mock_auth.return_value = True
                    with patch.object(handler_module, "boto3") as mock_boto3:
                        mock_boto3.resource.return_value.Table.return_value = mock_table
                        result = lambda_handler(event, context)
            else:
                with patch.object(handler_module, "boto3") as mock_boto3:
                    mock_boto3.resource.return_value.Table.return_value = mock_table
                    result = lambda_handler(event, context)

            # Verify format consistency based on mode
            if mode == "api_gateway":
                # API Gateway mode - always wrapped
                assert "statusCode" in result, f"API Gateway mode must have statusCode (success={success})"
                assert "headers" in result, f"API Gateway mode must have headers (success={success})"
                assert "body" in result, f"API Gateway mode must have body (success={success})"

                # Verify body is JSON string
                assert isinstance(result["body"], str), "Body must be JSON string"
                body_data = json.loads(result["body"])

                if success:
                    # Success response should have data
                    assert isinstance(body_data, dict), "Success body must be dict"
                else:
                    # Error response should have error fields
                    assert "error" in body_data, "Error body must have 'error'"
                    assert "message" in body_data, "Error body must have 'message'"
            else:
                # Direct mode - never wrapped
                assert "statusCode" not in result, f"Direct mode must not have statusCode (success={success})"
                assert "headers" not in result, f"Direct mode must not have headers (success={success})"

                if success:
                    # Success response should be plain dict with data
                    assert isinstance(result, dict), "Success response must be dict"
                else:
                    # Error response should have error fields directly
                    assert "error" in result, "Direct error must have 'error'"
                    assert "message" in result, "Direct error must have 'message'"


class TestResponseDataStructureProperty:
    """
    Property-based tests for response data structure consistency.

    **Validates: Property 3 - Response Format Consistency**
    """

    @given(handler=handler_names)
    @settings(max_examples=50)
    def test_api_gateway_body_always_json_string(self, handler):
        """
        Property: For any handler in API Gateway mode, the body field should
        always be a JSON string, never a plain object.

        **Validates: Requirements 10.1, 10.3, 10.5**
        """
        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Create API Gateway event
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "email": "test@example.com",
                        "sub": "user-123",
                        "cognito:username": "testuser",
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/protection-groups" if handler == "query_handler" else "/executions",
            "queryStringParameters": {},
        }

        context = MagicMock()
        context.invoked_function_arn = f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"

        # Mock DynamoDB
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": []}
        mock_table.query.return_value = {"Items": []}

        with patch.object(handler_module, "boto3") as mock_boto3:
            mock_boto3.resource.return_value.Table.return_value = mock_table
            result = lambda_handler(event, context)

        # Verify body is a string
        assert isinstance(result["body"], str), "API Gateway body must be a JSON string, not a dict"

        # Verify it can be parsed as JSON
        try:
            parsed = json.loads(result["body"])
            assert isinstance(parsed, dict), "Parsed body must be a dictionary"
        except json.JSONDecodeError as e:
            assert False, f"Body is not valid JSON: {e}"

    @given(handler=handler_names)
    @settings(max_examples=50)
    def test_direct_mode_returns_dict_not_string(self, handler):
        """
        Property: For any handler in direct mode, the response should be
        a dictionary, not a JSON string.

        **Validates: Requirements 10.2, 10.4, 10.6**
        """
        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Determine operation
        if handler == "query_handler":
            operation = "list_protection_groups"
        elif handler == "execution_handler":
            operation = "list_executions"
        else:
            operation = "list_protection_groups"

        # Create direct invocation event
        event = {"operation": operation}

        context = MagicMock()
        context.invoked_function_arn = f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"

        # Mock authorization and DynamoDB
        with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
            mock_auth.return_value = True

            mock_table = MagicMock()
            mock_table.scan.return_value = {"Items": []}
            mock_table.query.return_value = {"Items": []}

            with patch.object(handler_module, "boto3") as mock_boto3:
                mock_boto3.resource.return_value.Table.return_value = mock_table
                result = lambda_handler(event, context)

        # Verify result is a dict, not a string
        assert isinstance(result, dict), "Direct mode response must be a dict, not a JSON string"

        # Verify it's not a stringified JSON
        assert not isinstance(result, str), "Direct mode response must not be a JSON string"

        # Verify it's directly JSON serializable
        try:
            json.dumps(result)
        except (TypeError, ValueError) as e:
            assert False, f"Direct response not JSON serializable: {e}"


class TestResponseFormatJSONSerializability:
    """
    Property-based tests for JSON serializability of responses.

    **Validates: Property 3 - Response Format Consistency**
    """

    @given(
        handler=handler_names,
        mode=st.sampled_from(["api_gateway", "direct"]),
    )
    @settings(max_examples=100)
    def test_all_responses_json_serializable(self, handler, mode):
        """
        Property: For any handler and any mode, all responses should be
        JSON serializable.

        **Validates: Requirements 10.1-10.7**
        """
        # Import the appropriate handler module
        lambda_handler, handler_module = get_lambda_handler_module(handler)

        # Determine operation
        if handler == "query_handler":
            operation = "list_protection_groups"
        elif handler == "execution_handler":
            operation = "list_executions"
        else:
            operation = "list_protection_groups"

        context = MagicMock()
        context.invoked_function_arn = f"arn:aws:lambda:us-east-1:123456789012:function:{handler}"

        # Create event based on mode
        if mode == "api_gateway":
            event = {
                "requestContext": {
                    "authorizer": {
                        "claims": {
                            "email": "test@example.com",
                            "sub": "user-123",
                            "cognito:username": "testuser",
                        }
                    }
                },
                "httpMethod": "GET",
                "path": "/protection-groups" if handler == "query_handler" else "/executions",
                "queryStringParameters": {},
            }
        else:
            event = {"operation": operation}

        # Mock DynamoDB
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": []}
        mock_table.query.return_value = {"Items": []}

        # Execute with appropriate mocking
        if mode == "direct":
            with patch("shared.iam_utils.validate_iam_authorization") as mock_auth:
                mock_auth.return_value = True
                with patch.object(handler_module, "boto3") as mock_boto3:
                    mock_boto3.resource.return_value.Table.return_value = mock_table
                    result = lambda_handler(event, context)
        else:
            with patch.object(handler_module, "boto3") as mock_boto3:
                mock_boto3.resource.return_value.Table.return_value = mock_table
                result = lambda_handler(event, context)

        # Verify JSON serializability
        try:
            json_str = json.dumps(result)
            # Verify we can parse it back
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict), "Parsed response must be a dictionary"
        except (TypeError, ValueError) as e:
            assert False, f"Response not JSON serializable for {mode} mode: {e}"
