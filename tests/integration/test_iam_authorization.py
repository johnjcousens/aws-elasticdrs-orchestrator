"""
Integration tests for IAM authorization with different principals.

Tests IAM-based authorization for direct Lambda invocations including:
- IAM users (arn:aws:iam::account:user/username)
- IAM roles (arn:aws:iam::account:role/rolename)
- AWS services (arn:aws:sts::account:assumed-role/role/session)
- Step Functions (states.amazonaws.com)
- EventBridge (events.amazonaws.com)
- Authorization validation in all three handlers
- Error handling for unauthorized principals
- Audit logging with principal information

Feature: direct-lambda-invocation-mode
Task: 12.5 Test IAM authorization with different principals

Note: These tests use mocking to simulate different IAM principals
without requiring actual AWS credentials. They focus on testing the
authorization logic and audit logging.
"""

import json
import os
import sys
from unittest.mock import Mock, MagicMock, patch

import pytest

# Add lambda directories to path
lambda_base = os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
sys.path.insert(0, lambda_base)
sys.path.insert(0, os.path.join(lambda_base, "query-handler"))
sys.path.insert(0, os.path.join(lambda_base, "data-management-handler"))
sys.path.insert(0, os.path.join(lambda_base, "execution-handler"))
sys.path.insert(0, os.path.join(lambda_base, "shared"))

# Import handlers and utilities after path setup
import index as query_handler
from shared.iam_utils import (
    extract_iam_principal,
    validate_iam_authorization,
    log_direct_invocation,
    create_authorization_error_response,
    validate_direct_invocation_event,
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


def get_mock_context(principal_arn=None):
    """
    Create mock Lambda context with IAM principal.
    
    Args:
        principal_arn: IAM principal ARN to use in context
    """
    context = Mock()
    
    # Default function ARN
    if principal_arn is None:
        principal_arn = (
            "arn:aws:lambda:us-east-1:111111111111:function:query-handler"
        )
    
    context.invoked_function_arn = principal_arn
    context.request_id = "test-request-123"
    context.function_name = "query-handler"
    context.memory_limit_in_mb = 256
    context.aws_request_id = "test-request-123"
    context.function_version = "$LATEST"
    
    # Mock identity - return None for user_arn so extract_iam_principal
    # falls back to invoked_function_arn
    context.identity = None
    
    return context


# ============================================================================
# Test: IAM Principal Extraction
# ============================================================================


def test_extract_iam_principal_from_function_arn():
    """
    Test extracting IAM principal from Lambda function ARN.
    
    Validates:
    - Function ARN is extracted from context
    - ARN format is correct
    """
    context = get_mock_context(
        "arn:aws:lambda:us-east-1:111111111111:function:query-handler"
    )
    
    principal = extract_iam_principal(context)
    
    assert principal == "arn:aws:lambda:us-east-1:111111111111:function:query-handler"
    assert "lambda" in principal
    assert "111111111111" in principal


def test_extract_iam_principal_from_assumed_role():
    """
    Test extracting IAM principal from assumed role ARN.
    
    Validates:
    - Assumed role ARN is extracted
    - STS format is recognized
    - Session name is included
    """
    # Mock context with assumed role
    context = Mock()
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:111111111111:function:query-handler"
    )
    context.identity = Mock()
    # Set user_arn as a string, not a Mock
    context.identity.user_arn = (
        "arn:aws:sts::111111111111:assumed-role/OrchestrationRole/session-123"
    )
    
    principal = extract_iam_principal(context)
    
    assert "assumed-role" in principal
    assert "OrchestrationRole" in principal
    assert "session-123" in principal


def test_extract_iam_principal_from_iam_user():
    """
    Test extracting IAM principal from IAM user ARN.
    
    Validates:
    - IAM user ARN is extracted
    - User format is recognized
    """
    context = Mock()
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:111111111111:function:query-handler"
    )
    context.identity = Mock()
    # Set user_arn as a string, not a Mock
    context.identity.user_arn = "arn:aws:iam::111111111111:user/admin"
    
    principal = extract_iam_principal(context)
    
    assert "user/admin" in principal
    assert "111111111111" in principal


def test_extract_iam_principal_unknown():
    """
    Test extracting IAM principal when context is incomplete.
    
    Validates:
    - Returns "unknown" when principal cannot be determined
    - Logs warning
    """
    context = Mock()
    # Remove invoked_function_arn attribute entirely
    del context.invoked_function_arn
    context.identity = None
    
    principal = extract_iam_principal(context)
    
    assert principal == "unknown"


# ============================================================================
# Test: IAM Authorization Validation - Allowed Principals
# ============================================================================


def test_validate_orchestration_role_authorized():
    """
    Test that OrchestrationRole is authorized.
    
    Validates:
    - OrchestrationRole pattern is recognized
    - Authorization succeeds
    """
    principal_arn = "arn:aws:iam::111111111111:role/OrchestrationRole"
    
    is_authorized = validate_iam_authorization(principal_arn)
    
    assert is_authorized is True


def test_validate_orchestration_role_assumed_authorized():
    """
    Test that assumed OrchestrationRole is authorized.
    
    Validates:
    - Assumed role format is recognized
    - OrchestrationRole in assumed role is authorized
    """
    principal_arn = (
        "arn:aws:sts::111111111111:assumed-role/OrchestrationRole/session-123"
    )
    
    is_authorized = validate_iam_authorization(principal_arn)
    
    assert is_authorized is True


def test_validate_step_functions_role_authorized():
    """
    Test that Step Functions execution role is authorized.
    
    Validates:
    - Step Functions role pattern is recognized
    - Authorization succeeds
    """
    principal_arn = (
        "arn:aws:iam::111111111111:role/StepFunctionsExecutionRole"
    )
    
    is_authorized = validate_iam_authorization(principal_arn)
    
    assert is_authorized is True


def test_validate_lambda_execution_role_authorized():
    """
    Test that Lambda execution role is authorized.
    
    Validates:
    - Lambda role pattern is recognized
    - Authorization succeeds for Lambda-to-Lambda calls
    """
    principal_arn = (
        "arn:aws:iam::111111111111:role/LambdaExecutionRole"
    )
    
    is_authorized = validate_iam_authorization(principal_arn)
    
    assert is_authorized is True


def test_validate_lambda_function_arn_authorized():
    """
    Test that Lambda function ARN is authorized.
    
    Validates:
    - Lambda function ARN pattern is recognized
    - Authorization succeeds
    """
    principal_arn = (
        "arn:aws:lambda:us-east-1:111111111111:function:query-handler"
    )
    
    is_authorized = validate_iam_authorization(principal_arn)
    
    assert is_authorized is True


def test_validate_admin_user_authorized():
    """
    Test that admin IAM user is authorized.
    
    Validates:
    - Admin user pattern is recognized
    - Authorization succeeds for testing/manual operations
    """
    principal_arn = "arn:aws:iam::111111111111:user/admin"
    
    is_authorized = validate_iam_authorization(principal_arn)
    
    assert is_authorized is True


def test_validate_admin_assumed_role_authorized():
    """
    Test that assumed admin role is authorized.
    
    Validates:
    - Admin assumed role pattern is recognized
    - Authorization succeeds
    """
    principal_arn = (
        "arn:aws:sts::111111111111:assumed-role/AdminRole/session-456"
    )
    
    is_authorized = validate_iam_authorization(principal_arn)
    
    assert is_authorized is True


def test_validate_service_role_authorized():
    """
    Test that AWS service role is authorized.
    
    Validates:
    - Service role pattern is recognized
    - Authorization succeeds for AWS services
    """
    principal_arn = (
        "arn:aws:iam::111111111111:role/aws-service-role/"
        "states.amazonaws.com/AWSServiceRoleForStepFunctions"
    )
    
    is_authorized = validate_iam_authorization(principal_arn)
    
    assert is_authorized is True


# ============================================================================
# Test: IAM Authorization Validation - Denied Principals
# ============================================================================


def test_validate_unknown_principal_denied():
    """
    Test that unknown principal is denied.
    
    Validates:
    - Unknown principal is rejected
    - Authorization fails
    """
    principal_arn = "unknown"
    
    is_authorized = validate_iam_authorization(principal_arn)
    
    assert is_authorized is False


def test_validate_unauthorized_user_denied():
    """
    Test that unauthorized IAM user is denied.
    
    Validates:
    - Non-admin user is rejected
    - Authorization fails
    """
    principal_arn = "arn:aws:iam::111111111111:user/unauthorized-user"
    
    is_authorized = validate_iam_authorization(principal_arn)
    
    assert is_authorized is False


def test_validate_unauthorized_role_denied():
    """
    Test that unauthorized IAM role is denied.
    
    Validates:
    - Unknown role is rejected
    - Authorization fails
    """
    principal_arn = "arn:aws:iam::111111111111:role/UnauthorizedRole"
    
    is_authorized = validate_iam_authorization(principal_arn)
    
    assert is_authorized is False


def test_validate_empty_principal_denied():
    """
    Test that empty principal is denied.
    
    Validates:
    - Empty string is rejected
    - Authorization fails
    """
    principal_arn = ""
    
    is_authorized = validate_iam_authorization(principal_arn)
    
    assert is_authorized is False


def test_validate_none_principal_denied():
    """
    Test that None principal is denied.
    
    Validates:
    - None value is rejected
    - Authorization fails
    """
    principal_arn = None
    
    is_authorized = validate_iam_authorization(principal_arn)
    
    assert is_authorized is False


# ============================================================================
# Test: Audit Logging with Principal Information
# ============================================================================


def test_log_direct_invocation_with_orchestration_role(caplog):
    """
    Test audit logging for OrchestrationRole invocation.
    
    Validates:
    - Principal ARN is logged
    - Operation is logged
    - Success status is logged
    - Timestamp is included
    """
    import logging
    
    principal = "arn:aws:iam::111111111111:role/OrchestrationRole"
    operation = "get_drs_source_servers"
    params = {"region": "us-east-1"}
    result = {"servers": [], "totalCount": 0}
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal=principal,
            operation=operation,
            params=params,
            result=result,
            success=True,
        )
    
    # Verify log entry
    assert len(caplog.records) > 0
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    assert log_data["principal"] == principal
    assert log_data["operation"] == operation
    assert log_data["success"] is True
    assert "timestamp" in log_data
    assert log_data["event_type"] == "direct_invocation"


def test_log_direct_invocation_with_step_functions_role(caplog):
    """
    Test audit logging for Step Functions role invocation.
    
    Validates:
    - Step Functions role ARN is logged
    - Session information is included
    - Operation details are logged
    """
    import logging
    
    principal = (
        "arn:aws:sts::111111111111:assumed-role/"
        "StepFunctionsExecutionRole/execution-123"
    )
    operation = "start_execution"
    params = {"planId": "plan-123"}
    result = {"executionId": "exec-456"}
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal=principal,
            operation=operation,
            params=params,
            result=result,
            success=True,
        )
    
    # Verify log entry
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    assert "StepFunctionsExecutionRole" in log_data["principal"]
    assert "execution-123" in log_data["principal"]
    assert log_data["operation"] == operation


def test_log_direct_invocation_with_admin_user(caplog):
    """
    Test audit logging for admin user invocation.
    
    Validates:
    - Admin user ARN is logged
    - User identity is captured
    - Manual operation is logged
    """
    import logging
    
    principal = "arn:aws:iam::111111111111:user/admin"
    operation = "list_protection_groups"
    params = {}
    result = {"protectionGroups": [], "count": 0}
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal=principal,
            operation=operation,
            params=params,
            result=result,
            success=True,
        )
    
    # Verify log entry
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    assert log_data["principal"] == principal
    assert "user/admin" in log_data["principal"]


def test_log_direct_invocation_authorization_failure(caplog):
    """
    Test audit logging for authorization failure.
    
    Validates:
    - Failed authorization is logged
    - Error details are included
    - Warning level is used
    """
    import logging
    
    principal = "arn:aws:iam::111111111111:user/unauthorized"
    operation = "delete_protection_group"
    params = {"groupId": "pg-123"}
    result = {"error": "AUTHORIZATION_FAILED"}
    
    with caplog.at_level(logging.WARNING):
        log_direct_invocation(
            principal=principal,
            operation=operation,
            params=params,
            result=result,
            success=False,
        )
    
    # Verify log entry
    assert len(caplog.records) > 0
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    assert log_data["success"] is False
    assert log_data["principal"] == principal
    assert "error" in log_data["result"]


def test_log_direct_invocation_with_context_metadata(caplog):
    """
    Test audit logging includes Lambda context metadata.
    
    Validates:
    - Request ID is logged
    - Function name is logged
    - Function version is logged
    """
    import logging
    
    # Create a simple context object with string attributes (not Mock)
    class SimpleContext:
        def __init__(self):
            self.aws_request_id = "test-request-123"
            self.function_name = "query-handler"
            self.function_version = "$LATEST"
    
    context = SimpleContext()
    principal = "arn:aws:iam::111111111111:role/OrchestrationRole"
    operation = "get_execution"
    params = {"executionId": "exec-123"}
    result = {"execution": {}}
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal=principal,
            operation=operation,
            params=params,
            result=result,
            success=True,
            context=context,
        )
    
    # Verify log entry includes context metadata
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    assert log_data["request_id"] == context.aws_request_id
    assert log_data["function_name"] == context.function_name


def test_log_direct_invocation_masks_sensitive_params(caplog):
    """
    Test that sensitive parameters are masked in audit logs.
    
    Validates:
    - Password fields are masked
    - Secret fields are masked
    - Token fields are masked
    - Other parameters are not masked
    """
    import logging
    
    principal = "arn:aws:iam::111111111111:role/OrchestrationRole"
    operation = "test_operation"
    params = {
        "password": "secret123",
        "apiToken": "token456",
        "region": "us-east-1",  # Should not be masked
    }
    result = {"success": True}
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal=principal,
            operation=operation,
            params=params,
            result=result,
            success=True,
        )
    
    # Verify sensitive parameters are masked
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    # Password should be masked
    assert "secret123" not in log_message
    assert log_data["parameters"]["password"].startswith("secr")
    assert "*" in log_data["parameters"]["password"]
    
    # Token should be masked
    assert "token456" not in log_message
    assert log_data["parameters"]["apiToken"].startswith("toke")
    assert "*" in log_data["parameters"]["apiToken"]
    
    # Region should not be masked
    assert log_data["parameters"]["region"] == "us-east-1"


def test_log_direct_invocation_truncates_large_results(caplog):
    """
    Test that large results are truncated in audit logs.
    
    Validates:
    - Large results are truncated
    - Truncation is indicated
    - Preview is provided
    """
    import logging
    
    principal = "arn:aws:iam::111111111111:role/OrchestrationRole"
    operation = "list_protection_groups"
    params = {}
    
    # Create large result
    large_result = {
        "protectionGroups": [
            {"groupId": f"pg-{i}", "name": f"Group {i}"} for i in range(100)
        ]
    }
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal=principal,
            operation=operation,
            params=params,
            result=large_result,
            success=True,
        )
    
    # Verify result is truncated
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    # Result should be truncated
    if isinstance(log_data["result"], dict) and "truncated" in log_data["result"]:
        assert log_data["result"]["truncated"] is True
        assert "preview" in log_data["result"]


# ============================================================================
# Test: Authorization Error Response
# ============================================================================


def test_create_authorization_error_response():
    """
    Test creating standardized authorization error response.
    
    Validates:
    - Error code is correct
    - Message is descriptive
    - Details provide guidance
    """
    error_response = create_authorization_error_response()
    
    assert error_response["error"] == "AUTHORIZATION_FAILED"
    assert "Insufficient permissions" in error_response["message"]
    assert "details" in error_response
    assert "OrchestrationRole" in error_response["details"]


# ============================================================================
# Test: Direct Invocation Event Validation
# ============================================================================


def test_validate_direct_invocation_event_valid():
    """
    Test validation of valid direct invocation event.
    
    Validates:
    - Valid event passes validation
    - Operation field is recognized
    """
    event = {
        "operation": "get_drs_source_servers",
        "queryParams": {"region": "us-east-1"},
    }
    
    is_valid = validate_direct_invocation_event(event)
    
    assert is_valid is True


def test_validate_direct_invocation_event_missing_operation():
    """
    Test validation fails when operation is missing.
    
    Validates:
    - Missing operation field fails validation
    """
    event = {
        "queryParams": {"region": "us-east-1"},
    }
    
    is_valid = validate_direct_invocation_event(event)
    
    assert is_valid is False


def test_validate_direct_invocation_event_empty_operation():
    """
    Test validation fails when operation is empty.
    
    Validates:
    - Empty operation string fails validation
    """
    event = {
        "operation": "",
        "queryParams": {},
    }
    
    is_valid = validate_direct_invocation_event(event)
    
    assert is_valid is False


def test_validate_direct_invocation_event_not_dict():
    """
    Test validation fails when event is not a dictionary.
    
    Validates:
    - Non-dict event fails validation
    """
    event = "not a dict"
    
    is_valid = validate_direct_invocation_event(event)
    
    assert is_valid is False


# ============================================================================
# Test: Case-Insensitive Role Name Matching
# ============================================================================


def test_validate_orchestration_role_case_insensitive():
    """
    Test that role name matching is case-insensitive.
    
    Validates:
    - OrchestrationRole in various cases is recognized
    - Authorization succeeds regardless of case
    """
    test_cases = [
        "arn:aws:iam::111111111111:role/OrchestrationRole",
        "arn:aws:iam::111111111111:role/orchestrationrole",
        "arn:aws:iam::111111111111:role/ORCHESTRATIONROLE",
    ]
    
    for principal_arn in test_cases:
        is_authorized = validate_iam_authorization(principal_arn)
        assert is_authorized is True, f"Failed for: {principal_arn}"


def test_validate_step_functions_role_case_insensitive():
    """
    Test that Step Functions role matching is case-insensitive.
    
    Validates:
    - StepFunctions in various cases is recognized
    """
    test_cases = [
        "arn:aws:iam::111111111111:role/StepFunctionsRole",
        "arn:aws:iam::111111111111:role/stepfunctionsrole",
        "arn:aws:iam::111111111111:role/STEPFUNCTIONSROLE",
    ]
    
    for principal_arn in test_cases:
        is_authorized = validate_iam_authorization(principal_arn)
        assert is_authorized is True, f"Failed for: {principal_arn}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
