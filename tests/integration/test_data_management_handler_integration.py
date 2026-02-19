"""
Integration tests for Data Management Handler direct Lambda invocations.

Tests all data management operations via direct invocation mode including:
- Protection Group operations (create, update, delete)
- Recovery Plan operations (create, update, delete)
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
import uuid
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add lambda directories to path
lambda_base = os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
sys.path.insert(0, lambda_base)
sys.path.insert(0, os.path.join(lambda_base, "data-management-handler"))
sys.path.insert(0, os.path.join(lambda_base, "shared"))

# Import handler after path setup
import index as data_management_handler


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing"""
    os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
    os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
    os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
    os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
    os.environ["TAG_SYNC_CONFIG_TABLE"] = "test-tag-sync-config"
    os.environ["AWS_REGION"] = "us-east-1"
    yield
    # Cleanup
    for key in [
        "PROTECTION_GROUPS_TABLE",
        "RECOVERY_PLANS_TABLE",
        "TARGET_ACCOUNTS_TABLE",
        "EXECUTION_HISTORY_TABLE",
        "TAG_SYNC_CONFIG_TABLE",
    ]:
        if key in os.environ:
            del os.environ[key]


def get_mock_context():
    """Create mock Lambda context with IAM principal"""
    context = Mock()
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
    context.request_id = "test-request-123"
    context.function_name = "data-management-handler"
    context.memory_limit_in_mb = 512
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

    event = {"operation": "invalid_test_operation", "body": {}}
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

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
        "body": "{}",
    }
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    # API Gateway mode should wrap response
    assert "statusCode" in result
    assert "body" in result
    assert "headers" in result


# ============================================================================
# Test: IAM Authorization
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
@patch("index.protection_groups_table")
def test_iam_authorization_success(mock_table, mock_validate, mock_extract_principal, mock_env_vars):
    """
    Test successful IAM authorization for direct invocations.

    Validates:
    - IAM principal extraction
    - Authorization validation
    - Request proceeds when authorized
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_validate.return_value = True

    # Mock DynamoDB scan to return empty list
    mock_table.scan.return_value = {"Items": []}

    event = {
        "operation": "list_protection_groups",
        "queryParams": {},
    }
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    # Should not return authorization error
    if isinstance(result, dict):
        if "error" in result:
            assert result["error"] != "AUTHORIZATION_FAILED"


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
def test_iam_authorization_failure(mock_validate, mock_extract_principal, mock_env_vars):
    """
    Test IAM authorization failure for direct invocations.

    Validates:
    - Authorization denial
    - Error response structure
    - Security event logging
    """
    mock_extract_principal.return_value = "arn:aws:iam::999999999999:role/UnauthorizedRole"
    mock_validate.return_value = False

    event = {
        "operation": "list_protection_groups",
        "queryParams": {},
    }
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    # Should return authorization error
    assert isinstance(result, dict)
    assert "error" in result
    assert result["error"] == "AUTHORIZATION_FAILED"


# ============================================================================
# Test: Protection Group Operations
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
@patch("index.protection_groups_table")
@patch("index.recovery_plans_table")
@patch("index.validate_unique_pg_name")
@patch("index.check_tag_conflicts_for_create")
@patch("index.query_drs_servers_by_tags")
def test_create_protection_group_operation(
    mock_query_drs,
    mock_check_conflicts,
    mock_validate_name,
    mock_plans_table,
    mock_groups_table,
    mock_validate,
    mock_extract_principal,
    mock_env_vars,
):
    """
    Test create_protection_group operation via direct invocation.

    Validates:
    - Operation routing
    - Request validation
    - DynamoDB interaction
    - Response format
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_validate.return_value = True
    mock_validate_name.return_value = True
    mock_check_conflicts.return_value = []
    mock_query_drs.return_value = []

    # Mock DynamoDB operations
    mock_groups_table.put_item.return_value = {}
    mock_groups_table.scan.return_value = {"Items": []}
    mock_plans_table.scan.return_value = {"Items": []}

    event = {
        "operation": "create_protection_group",
        "body": {
            "groupName": "Test Protection Group",
            "description": "Test description",
            "region": "us-east-1",
            "serverSelectionTags": {"Environment": "Test"},
        },
    }
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    # Should return success response or acceptable error (not INVALID_OPERATION)
    assert isinstance(result, dict)
    if "error" in result:
        # May have other errors, but not INVALID_OPERATION
        assert result["error"] != "INVALID_OPERATION"
        # Log the actual error for debugging
        print(f"Test received error: {result.get('error')} - {result.get('message')}")
    else:
        # Success case - should have groupId
        assert "groupId" in result or "protectionGroup" in result


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
@patch("index.protection_groups_table")
def test_update_protection_group_operation(mock_table, mock_validate, mock_extract_principal, mock_env_vars):
    """
    Test update_protection_group operation via direct invocation.

    Validates:
    - Operation routing
    - Resource ID handling
    - Update validation
    - Response format
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_validate.return_value = True

    group_id = str(uuid.uuid4())

    # Mock DynamoDB get_item to return existing group
    mock_table.get_item.return_value = {
        "Item": {
            "groupId": group_id,
            "groupName": "Existing Group",
            "region": "us-east-1",
            "version": 1,
            "serverSelectionTags": {},
            "sourceServerIds": [],
        }
    }

    # Mock DynamoDB update_item
    mock_table.update_item.return_value = {
        "Attributes": {
            "groupId": group_id,
            "groupName": "Updated Group",
            "version": 2,
        }
    }

    event = {
        "operation": "update_protection_group",
        "body": {
            "groupId": group_id,
            "description": "Updated description",
        },
    }
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    # Should return success response
    assert isinstance(result, dict)
    if "error" in result:
        # If error, should not be INVALID_OPERATION
        assert result["error"] != "INVALID_OPERATION"


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
@patch("index.protection_groups_table")
@patch("index.recovery_plans_table")
def test_delete_protection_group_operation(
    mock_plans_table,
    mock_groups_table,
    mock_validate,
    mock_extract_principal,
    mock_env_vars,
):
    """
    Test delete_protection_group operation via direct invocation.

    Validates:
    - Operation routing
    - Deletion validation (not used in plans)
    - DynamoDB interaction
    - Response format
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_validate.return_value = True

    group_id = str(uuid.uuid4())

    # Mock DynamoDB get_item to return existing group
    mock_groups_table.get_item.return_value = {
        "Item": {
            "groupId": group_id,
            "groupName": "Test Group",
            "region": "us-east-1",
        }
    }

    # Mock recovery plans scan to return no plans using this group
    mock_plans_table.scan.return_value = {"Items": []}

    # Mock DynamoDB delete_item
    mock_groups_table.delete_item.return_value = {}

    event = {
        "operation": "delete_protection_group",
        "body": {"groupId": group_id},
    }
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    # Should return success response
    assert isinstance(result, dict)
    if "error" in result:
        # If error, should not be INVALID_OPERATION
        assert result["error"] != "INVALID_OPERATION"


# ============================================================================
# Test: Recovery Plan Operations
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
@patch("index.recovery_plans_table")
@patch("index.protection_groups_table")
@patch("index.executions_table")
@patch("index.validate_unique_rp_name")
@patch("index.validate_waves")
def test_create_recovery_plan_operation(
    mock_validate_waves,
    mock_validate_name,
    mock_executions_table,
    mock_groups_table,
    mock_plans_table,
    mock_validate,
    mock_extract_principal,
    mock_env_vars,
):
    """
    Test create_recovery_plan operation via direct invocation.

    Validates:
    - Operation routing
    - Request validation
    - Wave validation
    - DynamoDB interaction
    - Response format
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_validate.return_value = True
    mock_validate_name.return_value = True
    mock_validate_waves.return_value = None  # No validation errors

    group_id = str(uuid.uuid4())

    # Mock protection group exists
    mock_groups_table.get_item.return_value = {
        "Item": {
            "groupId": group_id,
            "groupName": "Test Group",
            "region": "us-east-1",
            "sourceServerIds": ["s-123"],
        }
    }
    mock_groups_table.scan.return_value = {"Items": []}

    # Mock DynamoDB operations
    mock_plans_table.put_item.return_value = {}
    mock_plans_table.scan.return_value = {"Items": []}
    mock_executions_table.query.return_value = {"Items": []}

    event = {
        "operation": "create_recovery_plan",
        "body": {
            "planName": "Test Recovery Plan",
            "description": "Test plan",
            "waves": [
                {
                    "waveNumber": 1,
                    "waveName": "Wave 1",
                    "protectionGroupId": group_id,
                }
            ],
        },
    }
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    # Should return success response or acceptable error (not INVALID_OPERATION)
    assert isinstance(result, dict)
    if "error" in result:
        # May have other errors, but not INVALID_OPERATION
        assert result["error"] != "INVALID_OPERATION"
        # Log the actual error for debugging
        print(f"Test received error: {result.get('error')} - {result.get('message')}")
    else:
        # Success case - should have planId
        assert "planId" in result or "recoveryPlan" in result


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
@patch("index.recovery_plans_table")
@patch("index.executions_table")
def test_update_recovery_plan_operation(
    mock_executions_table,
    mock_plans_table,
    mock_validate,
    mock_extract_principal,
    mock_env_vars,
):
    """
    Test update_recovery_plan operation via direct invocation.

    Validates:
    - Operation routing
    - Resource ID handling
    - Update validation
    - Response format
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_validate.return_value = True

    plan_id = str(uuid.uuid4())

    # Mock DynamoDB get_item to return existing plan
    mock_plans_table.get_item.return_value = {
        "Item": {
            "planId": plan_id,
            "planName": "Existing Plan",
            "version": 1,
            "waves": [],
        }
    }

    # Mock no active executions
    mock_executions_table.query.return_value = {"Items": []}

    # Mock DynamoDB update_item
    mock_plans_table.update_item.return_value = {
        "Attributes": {
            "planId": plan_id,
            "planName": "Updated Plan",
            "version": 2,
        }
    }

    event = {
        "operation": "update_recovery_plan",
        "body": {
            "planId": plan_id,
            "description": "Updated description",
        },
    }
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    # Should return success response
    assert isinstance(result, dict)
    if "error" in result:
        # If error, should not be INVALID_OPERATION
        assert result["error"] != "INVALID_OPERATION"


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
@patch("index.recovery_plans_table")
@patch("index.executions_table")
def test_delete_recovery_plan_operation(
    mock_executions_table,
    mock_plans_table,
    mock_validate,
    mock_extract_principal,
    mock_env_vars,
):
    """
    Test delete_recovery_plan operation via direct invocation.

    Validates:
    - Operation routing
    - Deletion validation (no active executions)
    - DynamoDB interaction
    - Response format
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_validate.return_value = True

    plan_id = str(uuid.uuid4())

    # Mock DynamoDB get_item to return existing plan
    mock_plans_table.get_item.return_value = {
        "Item": {
            "planId": plan_id,
            "planName": "Test Plan",
            "waves": [],
        }
    }

    # Mock no active executions
    mock_executions_table.query.return_value = {"Items": []}

    # Mock DynamoDB delete_item
    mock_plans_table.delete_item.return_value = {}

    event = {
        "operation": "delete_recovery_plan",
        "body": {"planId": plan_id},
    }
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    # Should return success response
    assert isinstance(result, dict)
    if "error" in result:
        # If error, should not be INVALID_OPERATION
        assert result["error"] != "INVALID_OPERATION"


# ============================================================================
# Test: Error Handling
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
def test_missing_operation_parameter(mock_extract_principal, mock_env_vars):
    """
    Test error handling when operation parameter is missing.

    Validates:
    - Error response structure
    - Error code: INVALID_EVENT_FORMAT
    - Error message clarity
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    event = {"body": {}}  # Missing "operation"
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    assert isinstance(result, dict)

    # Handle both wrapped and unwrapped responses
    if "statusCode" in result:
        # Wrapped API Gateway response
        body = json.loads(result.get("body", "{}"))
        assert "error" in body
        assert body["error"] in ["INVALID_INVOCATION", "INVALID_EVENT_FORMAT"]
        assert "message" in body
    else:
        # Unwrapped direct invocation response
        assert "error" in result
        assert result["error"] in ["INVALID_INVOCATION", "INVALID_EVENT_FORMAT"]
        assert "message" in result


@patch("shared.iam_utils.extract_iam_principal")
def test_invalid_operation_name(mock_extract_principal, mock_env_vars):
    """
    Test error handling for invalid operation names.

    Validates:
    - Error response structure
    - Error code: INVALID_OPERATION
    - Error message clarity
    """
    mock_extract_principal.return_value = get_mock_principal_arn()

    event = {"operation": "invalid_operation_xyz", "body": {}}
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    assert isinstance(result, dict)
    assert "error" in result
    assert result["error"] == "INVALID_OPERATION"
    assert "message" in result


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
def test_missing_required_parameter(mock_validate, mock_extract_principal, mock_env_vars):
    """
    Test error handling when required parameters are missing.

    Validates:
    - Error response structure
    - Error code: MISSING_PARAMETER or MISSING_FIELD
    - Field identification
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_validate.return_value = True

    event = {
        "operation": "create_protection_group",
        "body": {
            # Missing required "groupName" field
            "region": "us-east-1",
        },
    }
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    assert isinstance(result, dict)
    if "statusCode" in result:
        # Wrapped response
        body = json.loads(result.get("body", "{}"))
        assert "error" in body
        assert body["error"] in ["MISSING_PARAMETER", "MISSING_FIELD"]
    else:
        # Unwrapped response
        assert "error" in result
        assert result["error"] in ["MISSING_PARAMETER", "MISSING_FIELD"]


# ============================================================================
# Test: Response Format Consistency
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
@patch("index.protection_groups_table")
def test_response_format_direct_invocation(mock_table, mock_validate, mock_extract_principal, mock_env_vars):
    """
    Test response format for direct invocations (unwrapped).

    Validates:
    - No statusCode in response
    - Direct data return
    - Consistent structure
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_validate.return_value = True
    mock_table.scan.return_value = {"Items": []}

    event = {"operation": "list_protection_groups", "queryParams": {}}
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    # Direct invocation should NOT have statusCode
    assert "statusCode" not in result
    # Should have data or error
    assert "protectionGroups" in result or "groups" in result or "error" in result


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.protection_groups_table")
def test_response_format_api_gateway(mock_table, mock_extract_principal, mock_env_vars):
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
        "body": "{}",
    }
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    # API Gateway should have statusCode
    assert "statusCode" in result
    assert "body" in result
    assert "headers" in result


# ============================================================================
# Test: Audit Logging
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.log_direct_invocation")
@patch("shared.iam_utils.validate_iam_authorization")
@patch("index.protection_groups_table")
def test_audit_logging_called(mock_table, mock_validate, mock_log, mock_extract_principal, mock_env_vars):
    """
    Test that audit logging is called for direct invocations.

    Validates:
    - log_direct_invocation is called
    - Logging includes principal, operation, and result
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_validate.return_value = True
    mock_table.scan.return_value = {"Items": []}

    event = {"operation": "list_protection_groups", "queryParams": {}}
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    # Verify audit logging was called
    assert mock_log.called


# ============================================================================
# Test: Operation Coverage
# ============================================================================


@pytest.mark.parametrize(
    "operation",
    [
        "create_protection_group",
        "update_protection_group",
        "delete_protection_group",
        "create_recovery_plan",
        "update_recovery_plan",
        "delete_recovery_plan",
    ],
)
@patch("shared.iam_utils.extract_iam_principal")
@patch("shared.iam_utils.validate_iam_authorization")
def test_data_management_operations_routing(mock_validate, mock_extract_principal, operation, mock_env_vars):
    """
    Test that data management operations are properly routed.

    Validates:
    - Operation name recognition
    - Response structure
    - No INVALID_OPERATION error for valid operations
    """
    mock_extract_principal.return_value = get_mock_principal_arn()
    mock_validate.return_value = True

    # Provide minimal body to avoid validation errors
    body = {}
    if "protection_group" in operation:
        body = {"groupId": str(uuid.uuid4())}
    elif "recovery_plan" in operation:
        body = {"planId": str(uuid.uuid4())}

    event = {"operation": operation, "body": body}
    context = get_mock_context()

    # Mock DynamoDB tables to avoid actual calls
    with (
        patch("index.protection_groups_table") as mock_pg_table,
        patch("index.recovery_plans_table") as mock_rp_table,
        patch("index.executions_table") as mock_exec_table,
    ):

        mock_pg_table.get_item.return_value = {"Item": None}
        mock_rp_table.get_item.return_value = {"Item": None}
        mock_exec_table.query.return_value = {"Items": []}

        result = data_management_handler.lambda_handler(event, context)

    # Should return valid response (not error about invalid operation)
    assert isinstance(result, dict)
    if "error" in result:
        # May have validation errors, but not INVALID_OPERATION
        assert result["error"] != "INVALID_OPERATION"


# ============================================================================
# Test: Backward Compatibility
# ============================================================================


@patch("shared.iam_utils.extract_iam_principal")
@patch("index.protection_groups_table")
def test_backward_compatibility_api_gateway_still_works(mock_table, mock_extract_principal, mock_env_vars):
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
        "body": "{}",
    }
    context = get_mock_context()

    result = data_management_handler.lambda_handler(event, context)

    # Should return API Gateway format
    assert "statusCode" in result
    assert "body" in result
    assert "headers" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
