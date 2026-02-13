"""
Unit tests for query-handler response format handling.

Tests verify that query-handler returns:
- Raw data for direct invocations (no API Gateway wrapper)
- API Gateway wrapped responses for API Gateway invocations
- Automatic detection of invocation source

Validates Requirements:
- 10.1: Direct invocations return raw data without API Gateway wrapper
- 10.2: API Gateway invocations receive wrapped responses
- 10.7: Response format detection is automatic
"""

import json
import os
import sys
import importlib.util
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

# Mock environment variables before importing handler
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
os.environ["ORCHESTRATION_ROLE_ARN"] = "arn:aws:iam::123456789012:role/orchestration-role"

# Load query-handler module dynamically
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))
query_handler_index = importlib.import_module("query-handler.index")

# Import response helper from the loaded module
response = query_handler_index.response


class TestDirectInvocationResponseFormat:
    """Test direct invocation returns raw data without API Gateway wrapper"""

    def test_direct_invocation_returns_raw_dict(self):
        """
        Test that direct invocation returns raw dictionary without statusCode/body wrapper.

        Validates Requirement 10.1: Direct invocations return raw data
        """
        with (
            patch("shared.iam_utils.validate_iam_authorization") as mock_validate,
            patch.object(query_handler_index, "boto3") as mock_boto3,
            patch.object(query_handler_index, "get_current_account_id") as mock_get_account,
        ):

            mock_validate.return_value = True
            mock_get_account.return_value = "123456789012"

            # Direct invocation event
            event = {"operation": "get_current_account_id"}
            context = MagicMock()
            context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
            context.request_id = "test-request-id-123"

            result = query_handler_index.lambda_handler(event, context)

            # Verify raw data returned (no API Gateway wrapper)
            assert isinstance(result, dict)
            assert "statusCode" not in result
            assert "body" not in result
            assert "headers" not in result
            assert "accountId" in result
            assert result["accountId"] == "123456789012"

    def test_direct_invocation_extracts_body_from_api_gateway_response(self):
        """
        Test that direct invocation extracts body from API Gateway response format.

        Some operations return API Gateway format internally. Direct invocation
        should extract the body and return raw data.

        Validates Requirement 10.1: Direct invocations return raw data
        """
        with (
            patch("shared.iam_utils.validate_iam_authorization") as mock_validate,
            patch.object(query_handler_index, "boto3") as mock_boto3,
            patch.object(query_handler_index, "get_target_accounts") as mock_get,
        ):

            mock_validate.return_value = True

            # Mock operation that returns API Gateway format
            mock_accounts = [
                {"accountId": "111111111111", "accountName": "Account 1"},
                {"accountId": "222222222222", "accountName": "Account 2"},
            ]

            # Return API Gateway format
            mock_get.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"accounts": mock_accounts}),
            }

            event = {"operation": "get_target_accounts"}
            context = MagicMock()
            context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
            context.request_id = "test-request-id-123"

            result = query_handler_index.lambda_handler(event, context)

            # Verify body extracted and returned as raw data
            assert isinstance(result, dict)
            assert "statusCode" not in result
            assert "body" not in result
            assert "accounts" in result
            assert result["accounts"] == mock_accounts

    def test_direct_invocation_error_response_format(self):
        """
        Test that direct invocation errors return raw error dict without wrapper.

        Validates Requirement 10.1: Direct invocations return raw data (including errors)
        """
        with (
            patch("shared.iam_utils.validate_iam_authorization") as mock_validate,
            patch.object(query_handler_index, "boto3") as mock_boto3,
        ):

            mock_validate.return_value = True

            # Invalid operation
            event = {"operation": "invalid_operation"}
            context = MagicMock()
            context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
            context.request_id = "test-request-id-123"

            result = query_handler_index.lambda_handler(event, context)

            # Verify raw error response
            assert isinstance(result, dict)
            assert "statusCode" not in result
            assert "body" not in result
            assert "error" in result
            assert result["error"] == "INVALID_OPERATION"
            assert "message" in result


class TestApiGatewayResponseFormat:
    """Test API Gateway invocations return wrapped responses"""

    def test_api_gateway_returns_wrapped_response(self):
        """
        Test that API Gateway invocation returns wrapped response with statusCode/body/headers.

        Validates Requirement 10.2: API Gateway invocations receive wrapped responses
        """
        with (
            patch.object(query_handler_index, "boto3") as mock_boto3,
            patch.object(query_handler_index, "get_current_account_id") as mock_get,
        ):

            mock_get.return_value = "123456789012"

            # API Gateway event
            event = {
                "requestContext": {"authorizer": {"claims": {}}},
                "httpMethod": "GET",
                "path": "/accounts/current",
                "queryStringParameters": {},
            }
            context = MagicMock()
            context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
            context.request_id = "test-request-id-123"

            result = query_handler_index.lambda_handler(event, context)

            # Verify API Gateway format
            assert isinstance(result, dict)
            assert "statusCode" in result
            assert "headers" in result
            assert "body" in result
            assert result["statusCode"] == 200
            assert result["headers"]["Content-Type"] == "application/json"

            # Verify body is JSON string
            body = json.loads(result["body"])
            assert "accountId" in body
            assert body["accountId"] == "123456789012"

    def test_api_gateway_error_returns_wrapped_response(self):
        """
        Test that API Gateway errors return wrapped response with appropriate status code.

        Validates Requirement 10.2: API Gateway invocations receive wrapped responses
        """
        with patch.object(query_handler_index, "boto3") as mock_boto3:

            # API Gateway event with invalid path
            event = {
                "requestContext": {"authorizer": {"claims": {}}},
                "httpMethod": "GET",
                "path": "/invalid/path",
                "queryStringParameters": {},
            }
            context = MagicMock()
            context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
            context.request_id = "test-request-id-123"

            result = query_handler_index.lambda_handler(event, context)

            # Verify API Gateway error format
            assert isinstance(result, dict)
            assert "statusCode" in result
            assert "headers" in result
            assert "body" in result
            assert result["statusCode"] == 404

            # Verify error in body
            body = json.loads(result["body"])
            assert "error" in body
            assert body["error"] == "NOT_FOUND"


class TestInvocationModeDetection:
    """Test automatic detection of invocation source"""

    def test_detects_api_gateway_invocation(self):
        """
        Test that lambda_handler detects API Gateway invocation from requestContext.

        Validates Requirement 10.7: Response format detection is automatic
        """
        with (
            patch.object(query_handler_index, "boto3") as mock_boto3,
            patch.object(query_handler_index, "get_current_account_id") as mock_get,
        ):

            mock_get.return_value = "123456789012"

            # API Gateway event
            event = {
                "requestContext": {"authorizer": {"claims": {}}},
                "httpMethod": "GET",
                "path": "/accounts/current",
                "queryStringParameters": {},
            }
            context = MagicMock()
            context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
            context.request_id = "test-request-id-123"

            result = query_handler_index.lambda_handler(event, context)

            # Verify API Gateway format returned
            assert "statusCode" in result
            assert "headers" in result
            assert "body" in result

    def test_detects_direct_invocation(self):
        """
        Test that lambda_handler detects direct invocation from operation field.

        Validates Requirement 10.7: Response format detection is automatic
        """
        with (
            patch("shared.iam_utils.validate_iam_authorization") as mock_validate,
            patch.object(query_handler_index, "boto3") as mock_boto3,
            patch.object(query_handler_index, "get_current_account_id") as mock_get,
        ):

            mock_validate.return_value = True
            mock_get.return_value = "123456789012"

            # Direct invocation event
            event = {"operation": "get_current_account_id"}
            context = MagicMock()
            context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
            context.request_id = "test-request-id-123"

            result = query_handler_index.lambda_handler(event, context)

            # Verify raw format returned
            assert "statusCode" not in result
            assert "body" not in result
            assert "accountId" in result

    def test_detects_action_based_invocation(self):
        """
        Test that lambda_handler detects action-based invocation (Step Functions).

        Validates Requirement 10.7: Response format detection is automatic
        """
        with (
            patch.object(query_handler_index, "boto3") as mock_boto3,
            patch.object(query_handler_index, "query_drs_servers_by_tags") as mock_query,
        ):

            mock_query.return_value = ["s-123", "s-456"]

            # Action-based event (Step Functions)
            event = {"action": "query_servers_by_tags", "region": "us-east-1", "tags": {"Environment": "production"}}
            context = MagicMock()
            context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
            context.request_id = "test-request-id-123"

            result = query_handler_index.lambda_handler(event, context)

            # Verify raw format returned
            assert isinstance(result, dict)
            assert "server_ids" in result
            assert result["server_ids"] == ["s-123", "s-456"]

    def test_invalid_invocation_returns_error(self):
        """
        Test that invalid invocation (no requestContext, operation, or action) returns error.

        Validates Requirement 10.7: Response format detection is automatic
        """
        with patch.object(query_handler_index, "boto3") as mock_boto3:

            # Invalid event (no invocation pattern)
            event = {"someField": "someValue"}
            context = MagicMock()
            context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
            context.request_id = "test-request-id-123"

            result = query_handler_index.lambda_handler(event, context)

            # Verify error response (wrapped in API Gateway format for consistency)
            assert isinstance(result, dict)
            assert result["statusCode"] == 500
            body = json.loads(result["body"])
            assert "error" in body
            assert body["error"] == "INVALID_OPERATION"


class TestBackwardCompatibility:
    """Test that existing API Gateway deployments continue working"""

    def test_existing_api_gateway_endpoints_unchanged(self):
        """
        Test that existing API Gateway endpoints return same format as before.

        Validates Requirement 12.1: Existing API Gateway deployments continue working
        """
        with patch.object(query_handler_index, "boto3") as mock_boto3:

            # Test multiple existing endpoints
            endpoints = [
                {
                    "path": "/accounts/current",
                    "method": "GET",
                    "mock_func": "get_current_account_info",
                    "mock_return": response(200, {"accountId": "123456789012", "region": "us-east-1"}),
                    "expected_key": "accountId",
                },
                {
                    "path": "/drs/accounts",
                    "method": "GET",
                    "mock_func": "get_target_accounts",
                    "mock_return": response(200, {"accounts": []}),
                    "expected_key": "accounts",
                },
            ]

            for endpoint in endpoints:
                event = {
                    "requestContext": {"authorizer": {"claims": {}}},
                    "httpMethod": endpoint["method"],
                    "path": endpoint["path"],
                    "queryStringParameters": {},
                }
                context = MagicMock()
                context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
                context.request_id = "test-request-id-123"

                with patch.object(query_handler_index, endpoint["mock_func"]) as mock_func:
                    mock_func.return_value = endpoint["mock_return"]

                    result = query_handler_index.lambda_handler(event, context)

                    # Verify API Gateway format maintained
                    assert result["statusCode"] == 200
                    assert "headers" in result
                    assert "body" in result
                    body = json.loads(result["body"])
                    assert endpoint["expected_key"] in body


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
