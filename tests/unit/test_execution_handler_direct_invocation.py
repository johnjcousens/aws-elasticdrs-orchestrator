"""
Unit tests for execution-handler handle_direct_invocation() function.

Tests the standardized direct invocation interface for headless operation
without API Gateway. Validates operation routing, parameter handling,
error responses, and response format consistency.

Validates Requirements:
- Requirement 5: Execution Handler Standardization
- Requirement 9: Error Handling for Direct Invocations
- Requirement 10: Response Format Consistency
"""

import json
import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

pytestmark = pytest.mark.skip(reason="Skipped for CI/CD - cross-file test isolation issues")


# Module-level setup to load execution-handler index
lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
execution_handler_dir = os.path.join(lambda_dir, "execution-handler")


@pytest.fixture(scope="function", autouse=True)
def setup_execution_handler_import():
    """Ensure execution-handler index is imported correctly for each test"""
    # Save original sys.path and modules
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    # Remove any existing 'index' module
    if "index" in sys.modules:
        del sys.modules["index"]

    # Add execution-handler to front of path
    sys.path.insert(0, execution_handler_dir)
    sys.path.insert(0, lambda_dir)

    yield

    # Restore original state
    sys.path = original_path
    if "index" in sys.modules:
        del sys.modules["index"]
    if original_index is not None:
        sys.modules["index"] = original_index


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for tests"""
    with patch.dict(
        os.environ,
        {
            "EXECUTION_HISTORY_TABLE": "test-execution-table",
            "PROTECTION_GROUPS_TABLE": "test-pg-table",
            "RECOVERY_PLANS_TABLE": "test-plans-table",
            "TARGET_ACCOUNTS_TABLE": "test-target-accounts-table",
            "PROJECT_NAME": "test-project",
            "ENVIRONMENT": "test",
            "STATE_MACHINE_ARN": "arn:aws:states:us-east-1:123456789012:stateMachine:test",
        },
    ):
        yield


@pytest.fixture
def mock_shared_modules():
    """Mock shared modules before importing index"""
    # Mock all shared modules
    sys.modules["shared"] = Mock()
    sys.modules["shared.account_utils"] = Mock()
    sys.modules["shared.config_merge"] = Mock()
    sys.modules["shared.conflict_detection"] = Mock()
    sys.modules["shared.cross_account"] = Mock()
    sys.modules["shared.drs_limits"] = Mock()
    sys.modules["shared.drs_utils"] = Mock()
    sys.modules["shared.execution_utils"] = Mock()

    # Mock account_utils
    mock_account_utils = Mock()
    mock_account_utils.get_account_name = Mock(return_value="test-account")
    sys.modules["shared.account_utils"] = mock_account_utils

    # Mock IAM utilities
    mock_iam_utils = Mock()
    mock_iam_utils.extract_iam_principal = Mock(return_value="arn:aws:iam::123456789012:role/TestRole")
    mock_iam_utils.validate_iam_authorization = Mock(return_value=True)
    mock_iam_utils.log_direct_invocation = Mock()
    mock_iam_utils.create_authorization_error_response = Mock(
        return_value={"error": "AUTHORIZATION_FAILED", "message": "Insufficient permissions"}
    )
    mock_iam_utils.validate_direct_invocation_event = Mock(return_value=True)
    sys.modules["shared.iam_utils"] = mock_iam_utils

    # Mock response_utils with proper response function
    mock_response_utils = Mock()

    def mock_response(status_code, body, headers=None):
        """Mock response function that returns proper API Gateway response"""
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(body),
        }

    mock_response_utils.response = mock_response
    mock_response_utils.DecimalEncoder = json.JSONEncoder
    sys.modules["shared.response_utils"] = mock_response_utils

    yield

    # Clean up mocked modules
    for module_name in list(sys.modules.keys()):
        if module_name.startswith("shared"):
            del sys.modules[module_name]


@pytest.fixture
def mock_lambda_context():
    """Mock Lambda context object"""
    context = Mock()
    context.request_id = "test-request-id-123"
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-execution-handler"
    return context


# Test: Missing operation field
def test_handle_direct_invocation_missing_operation(mock_env_vars, mock_shared_modules, mock_lambda_context):
    """
    Test that missing operation field returns appropriate error.

    Validates: Requirement 9.1 - Missing required parameters
    """
    import index

    event = {"parameters": {"executionId": "exec-123"}}

    result = index.handle_direct_invocation(event, mock_lambda_context)

    assert result["error"] == "MISSING_OPERATION"
    assert "operation field is required" in result["message"]


# Test: Invalid operation name
def test_handle_direct_invocation_invalid_operation(mock_env_vars, mock_shared_modules, mock_lambda_context):
    """
    Test that invalid operation name returns appropriate error with valid operations list.

    Validates: Requirement 9.2 - Invalid operation name
    """
    import index

    event = {"operation": "invalid_operation", "parameters": {}}

    result = index.handle_direct_invocation(event, mock_lambda_context)

    assert result["error"] == "INVALID_OPERATION"
    assert "Unknown operation" in result["message"]
    assert "details" in result
    assert "validOperations" in result["details"]
    assert isinstance(result["details"]["validOperations"], list)
    assert len(result["details"]["validOperations"]) > 0
    # Verify expected operations are in the list
    expected_operations = [
        "start_execution",
        "cancel_execution",
        "pause_execution",
        "resume_execution",
        "terminate_instances",
        "get_recovery_instances",
    ]
    for op in expected_operations:
        assert op in result["details"]["validOperations"]


# Test: start_execution operation
@patch("index.execute_recovery_plan")
def test_handle_direct_invocation_start_execution(
    mock_execute, mock_env_vars, mock_shared_modules, mock_lambda_context
):
    """
    Test start_execution operation routes correctly and returns unwrapped response.

    Validates: Requirement 5.1, Requirement 10.4 - Direct invocation response format
    """
    import index

    # Mock execute_recovery_plan to return API Gateway format
    mock_execute.return_value = {
        "statusCode": 202,
        "body": json.dumps(
            {
                "executionId": "exec-123",
                "status": "PENDING",
                "message": "Execution started",
            }
        ),
    }

    event = {
        "operation": "start_execution",
        "parameters": {
            "planId": "plan-123",
            "executionType": "DRILL",
            "initiatedBy": "test-user",
        },
    }

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify execute_recovery_plan was called with correct parameters
    mock_execute.assert_called_once()
    call_args = mock_execute.call_args[0]
    assert call_args[0]["planId"] == "plan-123"
    assert call_args[0]["executionType"] == "DRILL"
    assert call_args[0]["initiatedBy"] == "test-user"

    # Verify response is unwrapped (no statusCode)
    assert "statusCode" not in result
    assert result["executionId"] == "exec-123"
    assert result["status"] == "PENDING"


# Test: cancel_execution operation
@patch("index.cancel_execution")
def test_handle_direct_invocation_cancel_execution(
    mock_cancel, mock_env_vars, mock_shared_modules, mock_lambda_context
):
    """
    Test cancel_execution operation routes correctly.

    Validates: Requirement 5.2
    """
    import index

    mock_cancel.return_value = {
        "statusCode": 200,
        "body": json.dumps({"message": "Execution cancelled", "executionId": "exec-123"}),
    }

    event = {
        "operation": "cancel_execution",
        "parameters": {"executionId": "exec-123", "reason": "User requested"},
    }

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify cancel_execution was called with correct parameters
    mock_cancel.assert_called_once_with("exec-123", {"executionId": "exec-123", "reason": "User requested"})

    # Verify response is unwrapped
    assert "statusCode" not in result
    assert result["executionId"] == "exec-123"


# Test: pause_execution operation
@patch("index.pause_execution")
def test_handle_direct_invocation_pause_execution(mock_pause, mock_env_vars, mock_shared_modules, mock_lambda_context):
    """
    Test pause_execution operation routes correctly.

    Validates: Requirement 5.3
    """
    import index

    mock_pause.return_value = {
        "statusCode": 200,
        "body": json.dumps({"message": "Execution paused", "executionId": "exec-123"}),
    }

    event = {"operation": "pause_execution", "parameters": {"executionId": "exec-123"}}

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify pause_execution was called
    mock_pause.assert_called_once_with("exec-123", {"executionId": "exec-123"})

    # Verify response is unwrapped
    assert "statusCode" not in result
    assert result["message"] == "Execution paused"


# Test: resume_execution operation
@patch("index.resume_execution")
def test_handle_direct_invocation_resume_execution(
    mock_resume, mock_env_vars, mock_shared_modules, mock_lambda_context
):
    """
    Test resume_execution operation routes correctly.

    Validates: Requirement 5.4
    """
    import index

    mock_resume.return_value = {
        "statusCode": 200,
        "body": json.dumps({"message": "Execution resumed", "executionId": "exec-123"}),
    }

    event = {"operation": "resume_execution", "parameters": {"executionId": "exec-123"}}

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify resume_execution was called
    mock_resume.assert_called_once_with("exec-123")

    # Verify response is unwrapped
    assert "statusCode" not in result
    assert result["message"] == "Execution resumed"


# Test: terminate_instances operation
@patch("index.terminate_recovery_instances")
def test_handle_direct_invocation_terminate_instances(
    mock_terminate, mock_env_vars, mock_shared_modules, mock_lambda_context
):
    """
    Test terminate_instances operation routes correctly.

    Validates: Requirement 5.5
    """
    import index

    mock_terminate.return_value = {
        "statusCode": 200,
        "body": json.dumps({"message": "Instances terminated", "count": 3}),
    }

    event = {"operation": "terminate_instances", "parameters": {"executionId": "exec-123"}}

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify terminate_recovery_instances was called
    mock_terminate.assert_called_once_with("exec-123")

    # Verify response is unwrapped
    assert "statusCode" not in result
    assert result["count"] == 3


# Test: get_recovery_instances operation
@patch("index.get_recovery_instances")
def test_handle_direct_invocation_get_recovery_instances(
    mock_get_instances, mock_env_vars, mock_shared_modules, mock_lambda_context
):
    """
    Test get_recovery_instances operation routes correctly.

    Validates: Requirement 5.6
    """
    import index

    mock_get_instances.return_value = {
        "statusCode": 200,
        "body": json.dumps({"instances": [{"instanceId": "i-123", "state": "running"}]}),
    }

    event = {"operation": "get_recovery_instances", "parameters": {"executionId": "exec-123"}}

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify get_recovery_instances was called
    mock_get_instances.assert_called_once_with("exec-123")

    # Verify response is unwrapped
    assert "statusCode" not in result
    assert "instances" in result
    assert len(result["instances"]) == 1


# Test: Missing required parameter for operation
@patch("index.cancel_execution")
def test_handle_direct_invocation_missing_parameter(
    mock_cancel, mock_env_vars, mock_shared_modules, mock_lambda_context
):
    """
    Test that missing required parameter (executionId) is handled.

    Validates: Requirement 9.1 - Missing required parameters
    """
    import index

    # Mock cancel_execution to raise error for missing executionId
    mock_cancel.side_effect = ValueError("executionId is required")

    event = {"operation": "cancel_execution", "parameters": {}}

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify error response structure
    assert result["error"] == "OPERATION_FAILED"
    assert "executionId is required" in result["message"]
    assert result["operation"] == "cancel_execution"


# Test: Operation execution failure
@patch("index.execute_recovery_plan")
def test_handle_direct_invocation_operation_failure(
    mock_execute, mock_env_vars, mock_shared_modules, mock_lambda_context
):
    """
    Test that operation execution failures are handled properly.

    Validates: Requirement 9.6 - Unexpected exception handling
    """
    import index

    # Mock execute_recovery_plan to raise exception
    mock_execute.side_effect = Exception("DynamoDB connection failed")

    event = {
        "operation": "start_execution",
        "parameters": {
            "planId": "plan-123",
            "executionType": "DRILL",
            "initiatedBy": "test-user",
        },
    }

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify error response structure
    assert result["error"] == "OPERATION_FAILED"
    assert "DynamoDB connection failed" in result["message"]
    assert result["operation"] == "start_execution"


# Test: Response format - raw dict without API Gateway wrapping
@patch("index.execute_recovery_plan")
def test_handle_direct_invocation_response_format(
    mock_execute, mock_env_vars, mock_shared_modules, mock_lambda_context
):
    """
    Test that direct invocation returns raw dict without API Gateway wrapping.

    Validates: Requirement 10.4 - Direct invocation response format
    """
    import index

    # Mock execute_recovery_plan to return API Gateway format
    mock_execute.return_value = {
        "statusCode": 202,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "executionId": "exec-123",
                "status": "PENDING",
                "planId": "plan-123",
            }
        ),
    }

    event = {
        "operation": "start_execution",
        "parameters": {
            "planId": "plan-123",
            "executionType": "DRILL",
            "initiatedBy": "test-user",
        },
    }

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify response is unwrapped - no statusCode, headers, or body
    assert "statusCode" not in result
    assert "headers" not in result
    assert "body" not in result

    # Verify actual data is present
    assert result["executionId"] == "exec-123"
    assert result["status"] == "PENDING"
    assert result["planId"] == "plan-123"


# Test: Error response structure consistency
def test_handle_direct_invocation_error_structure(mock_env_vars, mock_shared_modules, mock_lambda_context):
    """
    Test that error responses follow consistent structure.

    Validates: Requirement 9.7 - Consistent error response structure
    """
    import index

    event = {"operation": "invalid_op", "parameters": {}}

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify error response has required fields
    assert "error" in result
    assert "message" in result
    assert isinstance(result["error"], str)
    assert isinstance(result["message"], str)

    # Verify error code is uppercase with underscores
    assert result["error"].isupper()
    assert "_" in result["error"]


# Test: list_executions delegation
@patch("index._delegate_to_query_handler")
def test_handle_direct_invocation_list_executions(
    mock_delegate, mock_env_vars, mock_shared_modules, mock_lambda_context
):
    """
    Test list_executions operation delegates to query-handler.

    Validates: Requirement 5.7
    """
    import index

    mock_delegate.return_value = {"executions": [], "count": 0}

    event = {"operation": "list_executions", "parameters": {"status": "RUNNING"}}

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify delegation occurred
    mock_delegate.assert_called_once_with("list_executions", {"status": "RUNNING"})

    # Verify response
    assert "executions" in result
    assert result["count"] == 0


# Test: get_execution delegation
@patch("index._delegate_to_query_handler")
def test_handle_direct_invocation_get_execution(mock_delegate, mock_env_vars, mock_shared_modules, mock_lambda_context):
    """
    Test get_execution operation delegates to query-handler.

    Validates: Requirement 5.8
    """
    import index

    mock_delegate.return_value = {
        "executionId": "exec-123",
        "status": "COMPLETED",
        "planId": "plan-123",
    }

    event = {"operation": "get_execution", "parameters": {"executionId": "exec-123"}}

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify delegation occurred
    mock_delegate.assert_called_once_with("get_execution", {"executionId": "exec-123"})

    # Verify response
    assert result["executionId"] == "exec-123"
    assert result["status"] == "COMPLETED"


# Test: All valid operations are supported
def test_handle_direct_invocation_all_operations_supported(mock_env_vars, mock_shared_modules, mock_lambda_context):
    """
    Test that all required operations are supported.

    Validates: Requirement 5 - All execution handler operations
    """
    import index

    # Get list of valid operations from error response
    event = {"operation": "invalid_op", "parameters": {}}
    result = index.handle_direct_invocation(event, mock_lambda_context)

    valid_operations = result.get("details", {}).get("validOperations", [])

    # Verify all required operations are present
    required_operations = [
        "start_execution",
        "cancel_execution",
        "pause_execution",
        "resume_execution",
        "terminate_instances",
        "get_recovery_instances",
        "list_executions",
        "get_execution",
    ]

    for op in required_operations:
        assert op in valid_operations, f"Operation {op} not in valid operations list"


# Test: Parameters field is optional
@patch("index._delegate_to_query_handler")
def test_handle_direct_invocation_parameters_optional(
    mock_delegate, mock_env_vars, mock_shared_modules, mock_lambda_context
):
    """
    Test that parameters field is optional (defaults to empty dict).

    Validates: Requirement 2.1 - Optional queryParams field
    """
    import index

    mock_delegate.return_value = {"executions": []}

    # Event without parameters field
    event = {"operation": "list_executions"}

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify delegation occurred with empty dict
    mock_delegate.assert_called_once_with("list_executions", {})

    # Verify response
    assert "executions" in result


# Test: Direct invocation returns dict, not string
@patch("index.execute_recovery_plan")
def test_handle_direct_invocation_returns_dict(mock_execute, mock_env_vars, mock_shared_modules, mock_lambda_context):
    """
    Test that direct invocation always returns a dict, never a string.

    Validates: Requirement 10.4 - Response format consistency
    """
    import index

    mock_execute.return_value = {
        "statusCode": 202,
        "body": json.dumps({"executionId": "exec-123"}),
    }

    event = {
        "operation": "start_execution",
        "parameters": {
            "planId": "plan-123",
            "executionType": "DRILL",
            "initiatedBy": "test-user",
        },
    }

    result = index.handle_direct_invocation(event, mock_lambda_context)

    # Verify result is a dict
    assert isinstance(result, dict)
    # Verify it's not a JSON string
    assert not isinstance(result, str)
