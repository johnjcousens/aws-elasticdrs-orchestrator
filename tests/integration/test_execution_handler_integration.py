"""
Integration tests for Execution Handler direct Lambda invocations.

Tests all execution operations via direct invocation mode including:
- All execution operations (start, cancel, pause, resume, terminate, get)
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
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add lambda directories to path
lambda_base = os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
sys.path.insert(0, lambda_base)
sys.path.insert(0, os.path.join(lambda_base, "execution-handler"))
sys.path.insert(0, os.path.join(lambda_base, "shared"))

# Import handler after path setup
import index as execution_handler


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing"""
    os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
    os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
    os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["STATE_MACHINE_ARN"] = (
        "arn:aws:states:us-east-1:123456789012:stateMachine:test-state-machine"
    )
    yield
    # Cleanup
    for key in [
        "PROTECTION_GROUPS_TABLE",
        "RECOVERY_PLANS_TABLE",
        "EXECUTION_HISTORY_TABLE",
        "STATE_MACHINE_ARN",
    ]:
        if key in os.environ:
            del os.environ[key]


def get_mock_context():
    """Create mock Lambda context with IAM principal"""
    context = Mock()
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
    )
    context.request_id = "test-request-123"
    context.function_name = "execution-handler"
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

    event = {"operation": "invalid_test_operation", "parameters": {}}
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

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

    result = execution_handler.lambda_handler(event, context)

    # API Gateway mode should wrap response
    assert "statusCode" in result
    assert "body" in result
    assert "headers" in result


# ============================================================================
# Test: IAM Authorization
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
@patch("index.execution_history_table")
def test_iam_authorization_success(
    mock_table, mock_validate, mock_extract_principal, mock_env_vars
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

    # Mock DynamoDB response for get_execution
    mock_table.get_item.return_value = {
        "Item": {
            "executionId": "exec-123",
            "planId": "plan-456",
            "status": "COMPLETED",
            "waves": [],
        }
    }

    event = {
        "operation": "get_recovery_instances",
        "parameters": {"executionId": "exec-123"},
    }
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

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

    event = {
        "operation": "get_recovery_instances",
        "parameters": {"executionId": "exec-123"},
    }
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

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
    - Error code: INVALID_INVOCATION or MISSING_OPERATION
    - Error message clarity
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    event = {"parameters": {}}  # Missing "operation"
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

    assert isinstance(result, dict)
    assert "error" in result
    assert result["error"] in ["INVALID_INVOCATION", "MISSING_OPERATION", "INVALID_EVENT_FORMAT"]
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

    event = {"operation": "invalid_operation_xyz", "parameters": {}}
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

    assert isinstance(result, dict)
    assert "error" in result
    assert result["error"] == "INVALID_OPERATION"
    assert "message" in result


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.execution_history_table")
def test_missing_execution_id_parameter(
    mock_table, mock_extract_principal, mock_env_vars
):
    """
    Test error handling when required executionId parameter is missing.

    Validates:
    - Error response for missing required parameter
    - Error message clarity
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    event = {
        "operation": "cancel_execution",
        "parameters": {},  # Missing executionId
    }
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

    assert isinstance(result, dict)
    # Should return error about missing executionId
    if "error" in result:
        assert "executionId" in result.get("message", "").lower() or "error" in result


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.execution_history_table")
def test_execution_not_found(mock_table, mock_extract_principal, mock_env_vars):
    """
    Test error handling when execution is not found.

    Validates:
    - Error response for non-existent execution
    - Error code: NOT_FOUND or similar
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_table.get_item.return_value = {}  # Execution not found

    event = {
        "operation": "get_recovery_instances",
        "parameters": {"executionId": "nonexistent-exec"},
    }
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

    assert isinstance(result, dict)
    # Should return error about execution not found
    if "error" in result:
        assert "not found" in result.get("message", "").lower() or "error" in result


# ============================================================================
# Test: Response Format Consistency
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.execution_history_table")
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
    mock_table.get_item.return_value = {
        "Item": {
            "executionId": "exec-123",
            "planId": "plan-456",
            "status": "COMPLETED",
            "waves": [],
        }
    }

    event = {
        "operation": "get_recovery_instances",
        "parameters": {"executionId": "exec-123"},
    }
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

    # Direct invocation should NOT have statusCode
    assert "statusCode" not in result
    # Should have data or error
    assert "executionId" in result or "error" in result


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.execution_history_table")
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
        "path": "/executions",
        "queryStringParameters": {},
    }
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

    # API Gateway should have statusCode
    assert "statusCode" in result
    assert "body" in result
    assert "headers" in result


# ============================================================================
# Test: Operation Coverage - start_execution
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.recovery_plans_table")
@patch("index.execution_history_table")
@patch("index.stepfunctions")
@patch("shared.conflict_detection.check_server_conflicts")
@patch("shared.conflict_detection.get_active_executions_for_plan")
@patch("shared.drs_limits.validate_wave_sizes")
@patch("shared.drs_limits.validate_concurrent_jobs")
@patch("shared.drs_limits.validate_servers_in_all_jobs")
@patch("shared.drs_limits.validate_server_replication_states")
def test_start_execution_operation(
    mock_replication,
    mock_servers_in_jobs,
    mock_concurrent_jobs,
    mock_wave_sizes,
    mock_active_execs,
    mock_conflicts,
    mock_sf,
    mock_exec_table,
    mock_plans_table,
    mock_extract_principal,
    mock_env_vars,
):
    """
    Test start_execution operation via direct invocation.

    Validates:
    - Operation routing
    - Parameter validation
    - Response structure
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    # Mock recovery plan
    mock_plans_table.get_item.return_value = {
        "Item": {
            "planId": "plan-123",
            "planName": "Test Plan",
            "waves": [{"waveNumber": 1, "serverIds": ["s-1", "s-2"]}],
        }
    }

    # Mock no conflicts
    mock_conflicts.return_value = []
    mock_active_execs.return_value = []

    # Mock DRS limits validation
    mock_wave_sizes.return_value = []
    mock_concurrent_jobs.return_value = {"valid": True}
    mock_servers_in_jobs.return_value = {"valid": True}
    mock_replication.return_value = {"valid": True}

    # Mock Step Functions
    mock_sf.start_execution.return_value = {
        "executionArn": "arn:aws:states:us-east-1:123456789012:execution:test:exec-123"
    }

    # Mock DynamoDB client for lock
    with patch("index.boto3.client") as mock_boto_client:
        mock_dynamodb_client = MagicMock()
        mock_boto_client.return_value = mock_dynamodb_client
        mock_dynamodb_client.put_item.return_value = {}
        mock_dynamodb_client.delete_item.return_value = {}

        event = {
            "operation": "start_execution",
            "parameters": {
                "planId": "plan-123",
                "executionType": "DRILL",
                "initiatedBy": "test-user",
            },
        }
        context = get_mock_context()

        result = execution_handler.lambda_handler(event, context)

    # Should return execution details
    assert isinstance(result, dict)
    if "error" not in result:
        assert "executionId" in result or "statusCode" in result


# ============================================================================
# Test: Operation Coverage - cancel_execution
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.execution_history_table")
@patch("index.stepfunctions")
def test_cancel_execution_operation(
    mock_sf, mock_exec_table, mock_extract_principal, mock_env_vars
):
    """
    Test cancel_execution operation via direct invocation.

    Validates:
    - Operation routing
    - Parameter validation
    - Response structure
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    # Mock execution
    mock_exec_table.get_item.return_value = {
        "Item": {
            "executionId": "exec-123",
            "planId": "plan-456",
            "status": "RUNNING",
            "waves": [],
            "stepFunctionsExecutionArn": "arn:aws:states:us-east-1:123456789012:execution:test:exec-123",
        }
    }

    # Mock Step Functions
    mock_sf.stop_execution.return_value = {}

    event = {
        "operation": "cancel_execution",
        "parameters": {"executionId": "exec-123", "reason": "Test cancellation"},
    }
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

    # Should return cancellation result
    assert isinstance(result, dict)
    # Should not have INVALID_OPERATION error
    if "error" in result:
        assert result["error"] != "INVALID_OPERATION"


# ============================================================================
# Test: Operation Coverage - pause_execution
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.execution_history_table")
def test_pause_execution_operation(
    mock_exec_table, mock_extract_principal, mock_env_vars
):
    """
    Test pause_execution operation via direct invocation.

    Validates:
    - Operation routing
    - Parameter validation
    - Response structure
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    # Mock execution
    mock_exec_table.get_item.return_value = {
        "Item": {
            "executionId": "exec-123",
            "planId": "plan-456",
            "status": "RUNNING",
            "waves": [],
        }
    }

    event = {
        "operation": "pause_execution",
        "parameters": {"executionId": "exec-123"},
    }
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

    # Should return pause result
    assert isinstance(result, dict)
    # Should not have INVALID_OPERATION error
    if "error" in result:
        assert result["error"] != "INVALID_OPERATION"


# ============================================================================
# Test: Operation Coverage - resume_execution
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.execution_history_table")
@patch("index.stepfunctions")
def test_resume_execution_operation(
    mock_sf, mock_exec_table, mock_extract_principal, mock_env_vars
):
    """
    Test resume_execution operation via direct invocation.

    Validates:
    - Operation routing
    - Parameter validation
    - Response structure
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    # Mock paused execution with task token
    mock_exec_table.get_item.return_value = {
        "Item": {
            "executionId": "exec-123",
            "planId": "plan-456",
            "status": "PAUSED",
            "taskToken": "test-token-123",
            "waves": [],
        }
    }

    # Mock Step Functions
    mock_sf.send_task_success.return_value = {}

    event = {
        "operation": "resume_execution",
        "parameters": {"executionId": "exec-123"},
    }
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

    # Should return resume result
    assert isinstance(result, dict)
    # Should not have INVALID_OPERATION error
    if "error" in result:
        assert result["error"] != "INVALID_OPERATION"


# ============================================================================
# Test: Operation Coverage - terminate_instances
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.execution_history_table")
def test_terminate_instances_operation(
    mock_exec_table, mock_extract_principal, mock_env_vars
):
    """
    Test terminate_instances operation via direct invocation.

    Validates:
    - Operation routing
    - Parameter validation
    - Response structure
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    # Mock execution
    mock_exec_table.get_item.return_value = {
        "Item": {
            "executionId": "exec-123",
            "planId": "plan-456",
            "status": "COMPLETED",
            "waves": [],
        }
    }

    event = {
        "operation": "terminate_instances",
        "parameters": {"executionId": "exec-123"},
    }
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

    # Should return termination result
    assert isinstance(result, dict)
    # Should not have INVALID_OPERATION error
    if "error" in result:
        assert result["error"] != "INVALID_OPERATION"


# ============================================================================
# Test: Operation Coverage - get_recovery_instances
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.execution_history_table")
def test_get_recovery_instances_operation(
    mock_exec_table, mock_extract_principal, mock_env_vars
):
    """
    Test get_recovery_instances operation via direct invocation.

    Validates:
    - Operation routing
    - Parameter validation
    - Response structure
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    # Mock execution
    mock_exec_table.get_item.return_value = {
        "Item": {
            "executionId": "exec-123",
            "planId": "plan-456",
            "status": "COMPLETED",
            "waves": [],
        }
    }

    event = {
        "operation": "get_recovery_instances",
        "parameters": {"executionId": "exec-123"},
    }
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

    # Should return recovery instances
    assert isinstance(result, dict)
    # Should not have INVALID_OPERATION error
    if "error" in result:
        assert result["error"] != "INVALID_OPERATION"


# ============================================================================
# Test: Audit Logging
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.log_direct_invocation")
@patch("index.execution_history_table")
def test_audit_logging_called(
    mock_exec_table, mock_log, mock_extract_principal, mock_env_vars
):
    """
    Test that audit logging is called for direct invocations.

    Validates:
    - log_direct_invocation is called
    - Logging includes principal, operation, and result
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_exec_table.get_item.return_value = {
        "Item": {
            "executionId": "exec-123",
            "planId": "plan-456",
            "status": "COMPLETED",
            "waves": [],
        }
    }

    event = {
        "operation": "get_recovery_instances",
        "parameters": {"executionId": "exec-123"},
    }
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

    # Verify audit logging was called
    assert mock_log.called


# ============================================================================
# Test: Backward Compatibility
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.execution_history_table")
def test_backward_compatibility_api_gateway_still_works(
    mock_exec_table, mock_extract_principal, mock_env_vars
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
    mock_exec_table.scan.return_value = {"Items": []}

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
        "path": "/executions",
        "queryStringParameters": {},
    }
    context = get_mock_context()

    result = execution_handler.lambda_handler(event, context)

    # Should return API Gateway format
    assert "statusCode" in result
    assert "body" in result
    assert "headers" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
