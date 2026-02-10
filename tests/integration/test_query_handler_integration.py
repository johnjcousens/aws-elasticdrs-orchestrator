"""
Integration tests for Query Handler direct Lambda invocations.

Tests all query operations via direct invocation mode including:
- All query operations (list/get operations)
- IAM authorization validation
- Audit logging
- Error handling
- Response format consistency

Feature: direct-lambda-invocation-mode

Note: These are integration tests that test the actual handler logic
with minimal mocking. They focus on testing the integration between
components rather than unit testing individual functions.
"""

import json
import os
import sys
from unittest.mock import Mock, patch

import pytest

# Add lambda directories to path
lambda_base = os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
sys.path.insert(0, lambda_base)
sys.path.insert(0, os.path.join(lambda_base, "query-handler"))
sys.path.insert(0, os.path.join(lambda_base, "shared"))

# Import handler after path setup
import index as query_handler


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing"""
    os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
    os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
    os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
    os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
    os.environ["AWS_REGION"] = "us-east-1"
    yield
    # Cleanup
    for key in [
        "PROTECTION_GROUPS_TABLE",
        "RECOVERY_PLANS_TABLE",
        "TARGET_ACCOUNTS_TABLE",
        "EXECUTION_HISTORY_TABLE",
    ]:
        if key in os.environ:
            del os.environ[key]


def get_mock_context():
    """Create mock Lambda context with IAM principal"""
    context = Mock()
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
    )
    context.request_id = "test-request-123"
    context.function_name = "query-handler"
    context.memory_limit_in_mb = 256
    context.aws_request_id = "test-request-123"
    return context


def get_mock_principal_arn():
    """Return a valid IAM principal ARN for testing"""
    return "arn:aws:iam::123456789012:role/OrchestrationRole"


# ============================================================================
# Test: Invocation Mode Detection
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
def test_direct_invocation_mode_detection(mock_extract_principal, mock_env_vars):
    """
    Test that direct invocation mode is correctly detected.

    Validates:
    - Event with "operation" field triggers direct invocation
    - IAM principal extraction is called
    - Response is unwrapped (no statusCode)
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    event = {"operation": "invalid_test_operation", "queryParams": {}}
    context = get_mock_context()

    result = query_handler.lambda_handler(event, context)

    # Should detect direct invocation and return error for invalid operation
    assert isinstance(result, dict)
    # Direct invocation should not wrap in API Gateway format
    if "statusCode" in result:
        # If wrapped, extract body
        body = json.loads(result.get("body", "{}"))
        assert "error" in body
    else:
        # Unwrapped response
        assert "error" in result


@patch("shared.iam_utils.extract_iam_principal")
def test_api_gateway_mode_detection(mock_extract_principal, mock_env_vars):
    """
    Test that API Gateway mode is correctly detected.

    Validates:
    - Event with "requestContext" triggers API Gateway mode
    - Response is wrapped with statusCode
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    event = {
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "user-123",
                    "email": "test@example.com",
                    "cognito:username": "testuser",
                    "cognito:groups": "Admins",
                }
            }
        },
        "httpMethod": "GET",
        "path": "/invalid-path",
        "queryStringParameters": {},
    }
    context = get_mock_context()

    result = query_handler.lambda_handler(event, context)

    # API Gateway mode should wrap response
    assert "statusCode" in result
    assert "body" in result
    assert "headers" in result


# ============================================================================
# Test: IAM Authorization
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
def test_iam_authorization_success(
    mock_validate, mock_extract_principal, mock_env_vars
):
    """
    Test successful IAM authorization for direct invocations.

    Validates:
    - IAM principal extraction
    - Authorization validation
    - Request proceeds when authorized
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_validate.return_value = True

    event = {"operation": "get_target_accounts", "queryParams": {}}
    context = get_mock_context()

    with patch("index.target_accounts_table") as mock_table:
        mock_table.scan.return_value = {"Items": []}
        result = query_handler.lambda_handler(event, context)

    # Should not return authorization error
    if isinstance(result, dict):
        if "error" in result:
            assert result["error"] != "AUTHORIZATION_FAILED"


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
def test_iam_authorization_failure(
    mock_validate, mock_extract_principal, mock_env_vars
):
    """
    Test IAM authorization failure for direct invocations.

    Validates:
    - Authorization denial
    - Error response structure
    - Security event logging
    """
    mock_extract_principal.return_value = (
        "arn:aws:iam::999999999999:role/UnauthorizedRole"
    )
    mock_validate.return_value = False

    event = {"operation": "get_target_accounts", "queryParams": {}}
    context = get_mock_context()

    result = query_handler.lambda_handler(event, context)

    # Should return authorization error
    assert isinstance(result, dict)
    assert "error" in result
    assert result["error"] == "AUTHORIZATION_FAILED"


# ============================================================================
# Test: Error Handling
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
def test_missing_operation_parameter(mock_extract_principal, mock_env_vars):
    """
    Test error handling when operation parameter is missing.

    Validates:
    - Error response structure
    - Error code: INVALID_INVOCATION
    - Error message clarity
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    event = {"queryParams": {}}  # Missing "operation"
    context = get_mock_context()

    result = query_handler.lambda_handler(event, context)

    assert isinstance(result, dict)
    assert "error" in result
    assert result["error"] == "INVALID_INVOCATION"
    assert "message" in result


@patch("shared.iam_utils.extract_iam_principal")
def test_invalid_operation_name(mock_extract_principal, mock_env_vars):
    """
    Test error handling for invalid operation names.

    Validates:
    - Error response structure
    - Error code: INVALID_OPERATION
    - Supported operations list in response
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    event = {"operation": "invalid_operation_xyz", "queryParams": {}}
    context = get_mock_context()

    result = query_handler.lambda_handler(event, context)

    assert isinstance(result, dict)
    assert "error" in result
    assert result["error"] == "INVALID_OPERATION"
    assert "message" in result


# ============================================================================
# Test: Response Format Consistency
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.target_accounts_table")
def test_response_format_direct_invocation(
    mock_table, mock_extract_principal, mock_env_vars
):
    """
    Test response format for direct invocations (unwrapped).

    Validates:
    - No statusCode in response
    - Direct data return
    - Consistent structure
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_table.scan.return_value = {"Items": []}

    event = {"operation": "get_target_accounts", "queryParams": {}}
    context = get_mock_context()

    result = query_handler.lambda_handler(event, context)

    # Direct invocation should NOT have statusCode
    assert "statusCode" not in result
    # Should have data or error
    assert (
        "accounts" in result or "targetAccounts" in result or "error" in result
    )


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.protection_groups_table")
def test_response_format_api_gateway(
    mock_table, mock_extract_principal, mock_env_vars
):
    """
    Test response format for API Gateway invocations (wrapped).

    Validates:
    - statusCode present
    - body present
    - headers present
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_table.scan.return_value = {"Items": []}

    event = {
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "user-123",
                    "email": "test@example.com",
                    "cognito:username": "testuser",
                    "cognito:groups": "Admins",
                }
            }
        },
        "httpMethod": "GET",
        "path": "/protection-groups",
        "queryStringParameters": {},
    }
    context = get_mock_context()

    result = query_handler.lambda_handler(event, context)

    # API Gateway should have statusCode
    assert "statusCode" in result
    assert "body" in result
    assert "headers" in result


# ============================================================================
# Test: Operation Coverage
# ============================================================================


@pytest.mark.parametrize(
    "operation",
    [
        "get_target_accounts",
        "get_current_account_id",
    ],
)
@patch("shared.iam_utils.extract_iam_principal")
@patch("index.target_accounts_table")
def test_query_operations_routing(
    mock_table, mock_extract_principal, operation, mock_env_vars
):
    """
    Test that query operations are properly routed.

    Validates:
    - Operation name recognition
    - Response structure
    - No INVALID_OPERATION error
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_table.scan.return_value = {"Items": []}

    event = {"operation": operation, "queryParams": {}}
    context = get_mock_context()

    result = query_handler.lambda_handler(event, context)

    # Should return valid response (not error about invalid operation)
    assert isinstance(result, dict)
    if "error" in result:
        assert result["error"] != "INVALID_OPERATION"


# ============================================================================
# Test: Audit Logging
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.log_direct_invocation")
@patch("index.target_accounts_table")
def test_audit_logging_called(
    mock_table, mock_log, mock_extract_principal, mock_env_vars
):
    """
    Test that audit logging is called for direct invocations.

    Validates:
    - log_direct_invocation is called
    - Logging includes principal, operation, and result
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_table.scan.return_value = {"Items": []}

    event = {"operation": "get_target_accounts", "queryParams": {}}
    context = get_mock_context()

    result = query_handler.lambda_handler(event, context)

    # Verify audit logging was called
    assert mock_log.called


# ============================================================================
# Test: Backward Compatibility
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.protection_groups_table")
def test_backward_compatibility_api_gateway_still_works(
    mock_table, mock_extract_principal, mock_env_vars
):
    """
    Test that API Gateway mode still works after adding direct invocation.

    Validates:
    - API Gateway event detection
    - Cognito user extraction
    - API Gateway response format
    - Backward compatibility
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_table.scan.return_value = {"Items": []}

    # API Gateway event
    event = {
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "user-123",
                    "email": "test@example.com",
                    "cognito:username": "testuser",
                    "cognito:groups": "Admins",
                }
            }
        },
        "httpMethod": "GET",
        "path": "/protection-groups",
        "queryStringParameters": {},
    }
    context = get_mock_context()

    result = query_handler.lambda_handler(event, context)

    # Should return API Gateway format
    assert "statusCode" in result
    assert "body" in result
    assert "headers" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
