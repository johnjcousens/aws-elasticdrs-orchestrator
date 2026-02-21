"""
Unit Tests for IAM Authorization and Audit Logging Utilities

Tests IAM principal extraction, authorization validation, and audit logging
for direct Lambda invocations.
"""

import json
import os  # noqa: E402
import sys  # noqa: E402
from datetime import datetime
from unittest.mock import Mock, patch

import pytest  # noqa: F401



# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))


def test_extract_iam_principal_from_invoked_function_arn():
    """Test extracting IAM principal from invoked_function_arn"""
    from shared.iam_utils import extract_iam_principal

    # Create mock context without identity
    context = Mock()
    context.identity = None
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:query-handler"

    principal = extract_iam_principal(context)

    assert principal == "arn:aws:lambda:us-east-1:123456789012:function:query-handler"


def test_extract_iam_principal_from_identity():
    """Test extracting IAM principal from context.identity"""
    from shared.iam_utils import extract_iam_principal

    # Create mock context with identity
    context = Mock()
    context.identity = Mock()
    context.identity.user_arn = "arn:aws:iam::123456789012:user/admin"

    principal = extract_iam_principal(context)

    assert principal == "arn:aws:iam::123456789012:user/admin"


def test_extract_iam_principal_unknown():
    """Test extracting IAM principal when not available"""
    from shared.iam_utils import extract_iam_principal

    # Create mock context without identity
    context = Mock()
    context.identity = None
    del context.invoked_function_arn

    principal = extract_iam_principal(context)

    assert principal == "unknown"


def test_validate_iam_authorization_orchestration_role():
    """Test authorization for OrchestrationRole"""
    from shared.iam_utils import validate_iam_authorization

    # Test IAM role
    principal = "arn:aws:iam::123456789012:role/OrchestrationRole"
    assert validate_iam_authorization(principal) is True

    # Test assumed role
    principal = "arn:aws:sts::123456789012:assumed-role/OrchestrationRole/exec-123"
    assert validate_iam_authorization(principal) is True


def test_validate_iam_authorization_step_functions_role():
    """Test authorization for Step Functions execution role"""
    from shared.iam_utils import validate_iam_authorization

    principal = "arn:aws:iam::123456789012:role/StepFunctionsExecutionRole"
    assert validate_iam_authorization(principal) is True

    principal = "arn:aws:sts::123456789012:assumed-role/StepFunctionsExecutionRole/exec-123"
    assert validate_iam_authorization(principal) is True


def test_validate_iam_authorization_lambda_role():
    """Test authorization for Lambda execution role"""
    from shared.iam_utils import validate_iam_authorization

    principal = "arn:aws:iam::123456789012:role/LambdaExecutionRole"
    assert validate_iam_authorization(principal) is True

    principal = "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
    assert validate_iam_authorization(principal) is True


def test_validate_iam_authorization_admin_user():
    """Test authorization for admin user"""
    from shared.iam_utils import validate_iam_authorization

    principal = "arn:aws:iam::123456789012:user/admin"
    assert validate_iam_authorization(principal) is True

    principal = "arn:aws:sts::123456789012:assumed-role/AdminRole/session"
    assert validate_iam_authorization(principal) is True


def test_validate_iam_authorization_service_role():
    """Test authorization for AWS service role"""
    from shared.iam_utils import validate_iam_authorization

    principal = "arn:aws:iam::123456789012:role/aws-service-role/" "states.amazonaws.com/AWSServiceRoleForStepFunctions"
    assert validate_iam_authorization(principal) is True


def test_validate_iam_authorization_unauthorized():
    """Test authorization denial for unauthorized principal"""
    from shared.iam_utils import validate_iam_authorization

    # Unknown principal
    assert validate_iam_authorization("unknown") is False

    # Empty principal
    assert validate_iam_authorization("") is False

    # Unauthorized user
    principal = "arn:aws:iam::123456789012:user/unauthorized"
    assert validate_iam_authorization(principal) is False

    # Unauthorized role
    principal = "arn:aws:iam::123456789012:role/UnauthorizedRole"
    assert validate_iam_authorization(principal) is False


def test_log_direct_invocation_success():
    """Test logging successful direct invocation"""
    from shared.iam_utils import log_direct_invocation

    with patch("shared.iam_utils.logger") as mock_logger:
        log_direct_invocation(
            principal="arn:aws:iam::123456789012:role/OrchestrationRole",
            operation="get_drs_source_servers",
            params={"region": "us-east-1"},
            result={"servers": [], "totalCount": 0},
            success=True,
        )

        # Verify info log was called
        assert mock_logger.info.called

        # Verify log contains expected fields
        log_call = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_call)

        assert log_data["event_type"] == "direct_invocation"
        assert log_data["principal"] == "arn:aws:iam::123456789012:role/OrchestrationRole"
        assert log_data["operation"] == "get_drs_source_servers"
        assert log_data["success"] is True


def test_log_direct_invocation_failure():
    """Test logging failed direct invocation"""
    from shared.iam_utils import log_direct_invocation

    with patch("shared.iam_utils.logger") as mock_logger:
        log_direct_invocation(
            principal="arn:aws:iam::123456789012:user/unauthorized",
            operation="get_drs_source_servers",
            params={"region": "us-east-1"},
            result={"error": "AUTHORIZATION_FAILED"},
            success=False,
        )

        # Verify warning log was called
        assert mock_logger.warning.called

        # Verify log contains expected fields
        log_call = mock_logger.warning.call_args[0][0]
        log_data = json.loads(log_call)

        assert log_data["event_type"] == "direct_invocation"
        assert log_data["success"] is False
        assert "error" in log_data["result"]


def test_log_direct_invocation_with_context():
    """Test logging with Lambda context metadata"""
    from shared.iam_utils import log_direct_invocation

    # Create mock context
    context = Mock()
    context.aws_request_id = "abc-123-def-456"
    context.function_name = "query-handler"
    context.function_version = "$LATEST"

    with patch("shared.iam_utils.logger") as mock_logger:
        log_direct_invocation(
            principal="arn:aws:iam::123456789012:role/OrchestrationRole",
            operation="get_drs_source_servers",
            params={"region": "us-east-1"},
            result={"servers": []},
            success=True,
            context=context,
        )

        # Verify log contains context metadata
        log_call = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_call)

        assert log_data["request_id"] == "abc-123-def-456"
        assert log_data["function_name"] == "query-handler"
        assert log_data["function_version"] == "$LATEST"


def test_mask_sensitive_params():
    """Test masking sensitive parameters in audit logs"""
    from shared.iam_utils import _mask_sensitive_params

    params = {
        "region": "us-east-1",
        "password": "secret123",  # pragma: allowlist secret
        "api_token": "abc123xyz789",
        "accountId": "123456789012",
    }

    masked = _mask_sensitive_params(params)

    assert masked["region"] == "us-east-1"
    # Password is masked with first 4 chars + 7 asterisks (fixed length)
    assert masked["password"] == "secr*******"
    # Token is masked with first 4 chars + 7 asterisks (fixed length)
    assert masked["api_token"] == "abc1*******"
    assert masked["accountId"] == "123456789012"


def test_mask_sensitive_params_nested():
    """Test masking sensitive parameters in nested dictionaries"""
    from shared.iam_utils import _mask_sensitive_params

    params = {
        "region": "us-east-1",
        "credentials": {
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",  # pragma: allowlist secret  # noqa: E501
        },
    }

    masked = _mask_sensitive_params(params)

    assert masked["region"] == "us-east-1"
    # access_key is masked with first 4 chars + 7 asterisks (fixed length)
    assert masked["credentials"]["access_key"] == "AKIA*******"
    # secret_key is masked with first 4 chars + 7 asterisks (fixed length)
    assert masked["credentials"]["secret_key"] == "wJal*******"


def test_truncate_result_small():
    """Test truncating small result (no truncation)"""
    from shared.iam_utils import _truncate_result

    result = {"servers": [], "totalCount": 0}

    truncated = _truncate_result(result, max_length=1000)

    assert truncated == result


def test_truncate_result_large():
    """Test truncating large result"""
    from shared.iam_utils import _truncate_result

    # Create large result
    result = {"servers": [{"id": f"server-{i}"} for i in range(1000)]}

    truncated = _truncate_result(result, max_length=100)

    assert isinstance(truncated, dict)
    assert truncated["truncated"] is True
    assert "preview" in truncated
    assert "original_length" in truncated


def test_create_authorization_error_response():
    """Test creating authorization error response"""
    from shared.iam_utils import create_authorization_error_response

    error_response = create_authorization_error_response()

    assert error_response["error"] == "AUTHORIZATION_FAILED"
    assert "message" in error_response
    assert "details" in error_response


def test_validate_direct_invocation_event_valid():
    """Test validating valid direct invocation event"""
    from shared.iam_utils import validate_direct_invocation_event

    event = {
        "operation": "get_drs_source_servers",
        "queryParams": {"region": "us-east-1"},
    }

    assert validate_direct_invocation_event(event) is True


def test_validate_direct_invocation_event_missing_operation():
    """Test validating event missing operation field"""
    from shared.iam_utils import validate_direct_invocation_event

    event = {"queryParams": {"region": "us-east-1"}}

    assert validate_direct_invocation_event(event) is False


def test_validate_direct_invocation_event_empty_operation():
    """Test validating event with empty operation"""
    from shared.iam_utils import validate_direct_invocation_event

    event = {"operation": "", "queryParams": {"region": "us-east-1"}}

    assert validate_direct_invocation_event(event) is False


def test_validate_direct_invocation_event_invalid_type():
    """Test validating event with invalid type"""
    from shared.iam_utils import validate_direct_invocation_event

    # Not a dictionary
    assert validate_direct_invocation_event("invalid") is False

    # Operation not a string
    event = {"operation": 123}
    assert validate_direct_invocation_event(event) is False
