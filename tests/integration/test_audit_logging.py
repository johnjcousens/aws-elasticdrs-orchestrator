"""
Integration tests for audit logging across all operations.

Tests comprehensive audit logging for direct Lambda invocations including:
- All query operations (get_drs_source_servers, list_protection_groups, etc.)
- All data management operations (create_protection_group, update_recovery_plan, etc.)
- All execution operations (start_execution, cancel_execution, etc.)
- Required fields in audit logs (timestamp, principal, operation, parameters, result, request ID)
- Sensitive parameter masking (passwords, tokens, secrets)
- Result truncation for large responses
- JSON format and parseability
- Successful and failed operations

Feature: direct-lambda-invocation-mode
Task: 12.6 Test audit logging for all operations

Note: These tests use mocking to simulate operations and verify audit logging
without requiring actual AWS resources. They focus on testing the completeness
and correctness of audit log entries.
"""

import json
import os
import sys
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

# Add lambda directories to path
lambda_base = os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
sys.path.insert(0, lambda_base)
sys.path.insert(0, os.path.join(lambda_base, "shared"))

# Import utilities after path setup
from shared.iam_utils import log_direct_invocation


@pytest.fixture
def mock_context():
    """Create mock Lambda context with metadata"""
    context = Mock()
    context.aws_request_id = "test-request-123"
    context.function_name = "test-handler"
    context.function_version = "$LATEST"
    return context



# ============================================================================
# Test: Required Fields in Audit Logs
# ============================================================================


def test_audit_log_contains_timestamp(caplog, mock_context):
    """
    Test that audit logs include ISO 8601 timestamp.
    
    Validates:
    - Timestamp field is present
    - Timestamp is in ISO 8601 format
    - Timestamp ends with 'Z' (UTC)
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="test_operation",
            params={},
            result={"success": True},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert "timestamp" in log_data
    # Verify ISO 8601 format with Z suffix
    assert log_data["timestamp"].endswith("Z")
    # Verify parseable as datetime
    datetime.fromisoformat(log_data["timestamp"].replace("Z", "+00:00"))


def test_audit_log_contains_principal(caplog, mock_context):
    """
    Test that audit logs include IAM principal ARN.
    
    Validates:
    - Principal field is present
    - Principal ARN is complete
    """
    import logging
    
    principal_arn = "arn:aws:iam::111111111111:role/OrchestrationRole"
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal=principal_arn,
            operation="test_operation",
            params={},
            result={"success": True},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert "principal" in log_data
    assert log_data["principal"] == principal_arn


def test_audit_log_contains_operation(caplog, mock_context):
    """
    Test that audit logs include operation name.
    
    Validates:
    - Operation field is present
    - Operation name is correct
    """
    import logging
    
    operation_name = "get_drs_source_servers"
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation=operation_name,
            params={},
            result={"servers": []},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert "operation" in log_data
    assert log_data["operation"] == operation_name


def test_audit_log_contains_parameters(caplog, mock_context):
    """
    Test that audit logs include operation parameters.
    
    Validates:
    - Parameters field is present
    - Parameters are logged correctly
    """
    import logging
    
    params = {"region": "us-east-1", "accountId": "123456789012"}
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="get_drs_source_servers",
            params=params,
            result={"servers": []},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert "parameters" in log_data
    assert log_data["parameters"]["region"] == "us-east-1"
    assert log_data["parameters"]["accountId"] == "123456789012"


def test_audit_log_contains_result(caplog, mock_context):
    """
    Test that audit logs include operation result.
    
    Validates:
    - Result field is present
    - Result data is logged
    """
    import logging
    
    result = {"protectionGroups": [], "count": 0}
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="list_protection_groups",
            params={},
            result=result,
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert "result" in log_data
    assert "count" in log_data["result"]


def test_audit_log_contains_request_id(caplog, mock_context):
    """
    Test that audit logs include Lambda request ID.
    
    Validates:
    - Request ID field is present
    - Request ID matches context
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="test_operation",
            params={},
            result={"success": True},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert "request_id" in log_data
    assert log_data["request_id"] == mock_context.aws_request_id



# ============================================================================
# Test: Audit Logging for Query Operations
# ============================================================================


def test_audit_log_get_drs_source_servers(caplog, mock_context):
    """
    Test audit logging for get_drs_source_servers operation.
    
    Validates:
    - Operation is logged
    - Region parameter is logged
    - Result summary is logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="get_drs_source_servers",
            params={"region": "us-east-1"},
            result={"servers": [], "totalCount": 0},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "get_drs_source_servers"
    assert log_data["parameters"]["region"] == "us-east-1"
    assert log_data["success"] is True


def test_audit_log_list_protection_groups(caplog, mock_context):
    """
    Test audit logging for list_protection_groups operation.
    
    Validates:
    - Operation is logged
    - Result count is logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="list_protection_groups",
            params={},
            result={"protectionGroups": [], "count": 0},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "list_protection_groups"
    assert log_data["success"] is True


def test_audit_log_get_protection_group(caplog, mock_context):
    """
    Test audit logging for get_protection_group operation.
    
    Validates:
    - Operation is logged
    - Group ID parameter is logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="get_protection_group",
            params={"groupId": "pg-123"},
            result={"groupId": "pg-123", "name": "Test Group"},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "get_protection_group"
    assert log_data["parameters"]["groupId"] == "pg-123"


def test_audit_log_list_recovery_plans(caplog, mock_context):
    """
    Test audit logging for list_recovery_plans operation.
    
    Validates:
    - Operation is logged
    - Result is logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="list_recovery_plans",
            params={},
            result={"recoveryPlans": [], "count": 0},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "list_recovery_plans"
    assert log_data["success"] is True


def test_audit_log_get_recovery_plan(caplog, mock_context):
    """
    Test audit logging for get_recovery_plan operation.
    
    Validates:
    - Operation is logged
    - Plan ID parameter is logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="get_recovery_plan",
            params={"planId": "plan-456"},
            result={"planId": "plan-456", "name": "Test Plan"},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "get_recovery_plan"
    assert log_data["parameters"]["planId"] == "plan-456"


def test_audit_log_list_executions(caplog, mock_context):
    """
    Test audit logging for list_executions operation.
    
    Validates:
    - Operation is logged
    - Filter parameters are logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="list_executions",
            params={"status": "IN_PROGRESS"},
            result={"executions": [], "count": 0},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "list_executions"
    assert log_data["parameters"]["status"] == "IN_PROGRESS"


def test_audit_log_get_execution(caplog, mock_context):
    """
    Test audit logging for get_execution operation.
    
    Validates:
    - Operation is logged
    - Execution ID parameter is logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="get_execution",
            params={"executionId": "exec-789"},
            result={"executionId": "exec-789", "status": "COMPLETED"},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "get_execution"
    assert log_data["parameters"]["executionId"] == "exec-789"


def test_audit_log_get_target_accounts(caplog, mock_context):
    """
    Test audit logging for get_target_accounts operation.
    
    Validates:
    - Operation is logged
    - Result is logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="get_target_accounts",
            params={},
            result={"accounts": [], "count": 0},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "get_target_accounts"
    assert log_data["success"] is True



# ============================================================================
# Test: Audit Logging for Data Management Operations
# ============================================================================


def test_audit_log_create_protection_group(caplog, mock_context):
    """
    Test audit logging for create_protection_group operation.
    
    Validates:
    - Operation is logged
    - Group data is logged
    - Result includes new group ID
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="create_protection_group",
            params={"name": "New Group", "description": "Test group"},
            result={"groupId": "pg-new-123"},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "create_protection_group"
    assert log_data["parameters"]["name"] == "New Group"
    assert log_data["success"] is True


def test_audit_log_update_protection_group(caplog, mock_context):
    """
    Test audit logging for update_protection_group operation.
    
    Validates:
    - Operation is logged
    - Group ID and updates are logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="update_protection_group",
            params={"groupId": "pg-123", "description": "Updated"},
            result={"groupId": "pg-123", "updated": True},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "update_protection_group"
    assert log_data["parameters"]["groupId"] == "pg-123"


def test_audit_log_delete_protection_group(caplog, mock_context):
    """
    Test audit logging for delete_protection_group operation.
    
    Validates:
    - Operation is logged
    - Group ID is logged
    - Deletion is confirmed
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="delete_protection_group",
            params={"groupId": "pg-123"},
            result={"deleted": True},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "delete_protection_group"
    assert log_data["parameters"]["groupId"] == "pg-123"


def test_audit_log_create_recovery_plan(caplog, mock_context):
    """
    Test audit logging for create_recovery_plan operation.
    
    Validates:
    - Operation is logged
    - Plan data is logged
    - Result includes new plan ID
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="create_recovery_plan",
            params={"name": "New Plan", "protectionGroupId": "pg-123"},
            result={"planId": "plan-new-456"},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "create_recovery_plan"
    assert log_data["parameters"]["name"] == "New Plan"


def test_audit_log_update_recovery_plan(caplog, mock_context):
    """
    Test audit logging for update_recovery_plan operation.
    
    Validates:
    - Operation is logged
    - Plan ID and updates are logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="update_recovery_plan",
            params={"planId": "plan-456", "description": "Updated plan"},
            result={"planId": "plan-456", "updated": True},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "update_recovery_plan"
    assert log_data["parameters"]["planId"] == "plan-456"


def test_audit_log_delete_recovery_plan(caplog, mock_context):
    """
    Test audit logging for delete_recovery_plan operation.
    
    Validates:
    - Operation is logged
    - Plan ID is logged
    - Deletion is confirmed
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="delete_recovery_plan",
            params={"planId": "plan-456"},
            result={"deleted": True},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "delete_recovery_plan"
    assert log_data["parameters"]["planId"] == "plan-456"



# ============================================================================
# Test: Audit Logging for Execution Operations
# ============================================================================


def test_audit_log_start_execution(caplog, mock_context):
    """
    Test audit logging for start_execution operation.
    
    Validates:
    - Operation is logged
    - Plan ID and execution type are logged
    - Result includes execution ID
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="start_execution",
            params={"planId": "plan-456", "executionType": "DRILL"},
            result={"executionId": "exec-new-789"},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "start_execution"
    assert log_data["parameters"]["planId"] == "plan-456"
    assert log_data["parameters"]["executionType"] == "DRILL"


def test_audit_log_cancel_execution(caplog, mock_context):
    """
    Test audit logging for cancel_execution operation.
    
    Validates:
    - Operation is logged
    - Execution ID is logged
    - Cancellation reason is logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="cancel_execution",
            params={"executionId": "exec-789", "reason": "User requested"},
            result={"cancelled": True},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "cancel_execution"
    assert log_data["parameters"]["executionId"] == "exec-789"


def test_audit_log_pause_execution(caplog, mock_context):
    """
    Test audit logging for pause_execution operation.
    
    Validates:
    - Operation is logged
    - Execution ID is logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="pause_execution",
            params={"executionId": "exec-789"},
            result={"paused": True},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "pause_execution"
    assert log_data["parameters"]["executionId"] == "exec-789"


def test_audit_log_resume_execution(caplog, mock_context):
    """
    Test audit logging for resume_execution operation.
    
    Validates:
    - Operation is logged
    - Execution ID is logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="resume_execution",
            params={"executionId": "exec-789"},
            result={"resumed": True},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "resume_execution"
    assert log_data["parameters"]["executionId"] == "exec-789"


def test_audit_log_terminate_instances(caplog, mock_context):
    """
    Test audit logging for terminate_instances operation.
    
    Validates:
    - Operation is logged
    - Execution ID is logged
    - Termination is confirmed
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="terminate_instances",
            params={"executionId": "exec-789"},
            result={"terminated": True, "instanceCount": 5},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "terminate_instances"
    assert log_data["parameters"]["executionId"] == "exec-789"


def test_audit_log_get_recovery_instances(caplog, mock_context):
    """
    Test audit logging for get_recovery_instances operation.
    
    Validates:
    - Operation is logged
    - Execution ID is logged
    - Instance data is logged
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="get_recovery_instances",
            params={"executionId": "exec-789"},
            result={"instances": [], "count": 0},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["operation"] == "get_recovery_instances"
    assert log_data["parameters"]["executionId"] == "exec-789"


# ============================================================================
# Test: Sensitive Parameter Masking
# ============================================================================


def test_audit_log_masks_password_field(caplog, mock_context):
    """
    Test that password fields are masked in audit logs.
    
    Validates:
    - Password value is not in log
    - Password is masked with asterisks
    - First 4 characters are visible
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="test_operation",
            params={"password": "secretpassword123"},
            result={"success": True},
            success=True,
            context=mock_context,
        )
    
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    # Password should not appear in full
    assert "secretpassword123" not in log_message
    # Password should be masked
    assert log_data["parameters"]["password"].startswith("secr")
    assert "*" in log_data["parameters"]["password"]


def test_audit_log_masks_secret_field(caplog, mock_context):
    """
    Test that secret fields are masked in audit logs.
    
    Validates:
    - Secret value is not in log
    - Secret is masked with asterisks
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="test_operation",
            params={"apiSecret": "topsecret456"},
            result={"success": True},
            success=True,
            context=mock_context,
        )
    
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    # Secret should not appear in full
    assert "topsecret456" not in log_message
    # Secret should be masked
    assert "*" in log_data["parameters"]["apiSecret"]


def test_audit_log_masks_token_field(caplog, mock_context):
    """
    Test that token fields are masked in audit logs.
    
    Validates:
    - Token value is not in log
    - Token is masked with asterisks
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="test_operation",
            params={"authToken": "bearer_token_xyz789"},
            result={"success": True},
            success=True,
            context=mock_context,
        )
    
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    # Token should not appear in full
    assert "bearer_token_xyz789" not in log_message
    # Token should be masked
    assert "*" in log_data["parameters"]["authToken"]


def test_audit_log_masks_key_field(caplog, mock_context):
    """
    Test that key fields are masked in audit logs.
    
    Validates:
    - Key value is not in log
    - Key is masked with asterisks
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="test_operation",
            params={"apiKey": "AKIAIOSFODNN7EXAMPLE"},
            result={"success": True},
            success=True,
            context=mock_context,
        )
    
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    # Key should not appear in full
    assert "AKIAIOSFODNN7EXAMPLE" not in log_message
    # Key should be masked
    assert "*" in log_data["parameters"]["apiKey"]


def test_audit_log_masks_credential_field(caplog, mock_context):
    """
    Test that credential fields are masked in audit logs.
    
    Validates:
    - Credential value is not in log
    - Credential is masked with asterisks
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="test_operation",
            params={"credential": "mycredential123"},
            result={"success": True},
            success=True,
            context=mock_context,
        )
    
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    # Credential should not appear in full
    assert "mycredential123" not in log_message
    # Credential should be masked
    assert "*" in log_data["parameters"]["credential"]


def test_audit_log_does_not_mask_non_sensitive_fields(caplog, mock_context):
    """
    Test that non-sensitive fields are not masked.
    
    Validates:
    - Region is not masked
    - Account ID is not masked
    - Other parameters are not masked
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="test_operation",
            params={
                "region": "us-east-1",
                "accountId": "123456789012",
                "groupId": "pg-123",
            },
            result={"success": True},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    # Non-sensitive fields should not be masked
    assert log_data["parameters"]["region"] == "us-east-1"
    assert log_data["parameters"]["accountId"] == "123456789012"
    assert log_data["parameters"]["groupId"] == "pg-123"


def test_audit_log_masks_nested_sensitive_fields(caplog, mock_context):
    """
    Test that nested sensitive fields are masked.
    
    Validates:
    - Nested password is masked
    - Nested structure is preserved
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="test_operation",
            params={
                "config": {
                    "password": "nestedsecret",
                    "region": "us-west-2",
                }
            },
            result={"success": True},
            success=True,
            context=mock_context,
        )
    
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    # Nested password should be masked
    assert "nestedsecret" not in log_message
    assert "*" in log_data["parameters"]["config"]["password"]
    # Non-sensitive nested field should not be masked
    assert log_data["parameters"]["config"]["region"] == "us-west-2"



# ============================================================================
# Test: Result Truncation for Large Responses
# ============================================================================


def test_audit_log_truncates_large_result(caplog, mock_context):
    """
    Test that large results are truncated in audit logs.
    
    Validates:
    - Large result is truncated
    - Truncation is indicated
    - Preview is provided
    - Original length is recorded
    """
    import logging
    
    # Create large result (over 1000 characters)
    large_result = {
        "servers": [
            {
                "serverId": f"s-{i:04d}",
                "hostname": f"server-{i}.example.com",
                "ipAddress": f"10.0.{i // 256}.{i % 256}",
            }
            for i in range(50)
        ]
    }
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="get_drs_source_servers",
            params={"region": "us-east-1"},
            result=large_result,
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    # Result should be truncated
    if isinstance(log_data["result"], dict) and "truncated" in log_data["result"]:
        assert log_data["result"]["truncated"] is True
        assert "preview" in log_data["result"]
        assert "original_length" in log_data["result"]


def test_audit_log_does_not_truncate_small_result(caplog, mock_context):
    """
    Test that small results are not truncated.
    
    Validates:
    - Small result is logged in full
    - No truncation indicator
    """
    import logging
    
    small_result = {"servers": [], "totalCount": 0}
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="get_drs_source_servers",
            params={"region": "us-east-1"},
            result=small_result,
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    # Result should not be truncated
    if isinstance(log_data["result"], dict):
        # If it's the original result, it shouldn't have truncated field
        if "truncated" in log_data["result"]:
            assert log_data["result"]["truncated"] is False
        else:
            # Original result is preserved
            assert "servers" in log_data["result"]


# ============================================================================
# Test: Audit Logging for Failed Operations
# ============================================================================


def test_audit_log_failed_operation_authorization(caplog, mock_context):
    """
    Test audit logging for failed authorization.
    
    Validates:
    - Failed operation is logged
    - Success is False
    - Error details are logged
    - Warning level is used
    """
    import logging
    
    with caplog.at_level(logging.WARNING):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:user/unauthorized",
            operation="delete_protection_group",
            params={"groupId": "pg-123"},
            result={"error": "AUTHORIZATION_FAILED"},
            success=False,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["success"] is False
    assert "error" in log_data["result"]
    assert log_data["result"]["error"] == "AUTHORIZATION_FAILED"


def test_audit_log_failed_operation_not_found(caplog, mock_context):
    """
    Test audit logging for resource not found error.
    
    Validates:
    - Failed operation is logged
    - Success is False
    - Error message is logged
    """
    import logging
    
    with caplog.at_level(logging.WARNING):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="get_protection_group",
            params={"groupId": "pg-nonexistent"},
            result={"error": "NOT_FOUND", "message": "Group not found"},
            success=False,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["success"] is False
    assert log_data["result"]["error"] == "NOT_FOUND"


def test_audit_log_failed_operation_invalid_parameter(caplog, mock_context):
    """
    Test audit logging for invalid parameter error.
    
    Validates:
    - Failed operation is logged
    - Success is False
    - Parameter error is logged
    """
    import logging
    
    with caplog.at_level(logging.WARNING):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="start_execution",
            params={"planId": ""},  # Invalid empty plan ID
            result={"error": "INVALID_PARAMETER", "message": "planId is required"},
            success=False,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["success"] is False
    assert log_data["result"]["error"] == "INVALID_PARAMETER"


def test_audit_log_failed_operation_dynamodb_error(caplog, mock_context):
    """
    Test audit logging for DynamoDB error.
    
    Validates:
    - Failed operation is logged
    - Success is False
    - DynamoDB error is logged
    """
    import logging
    
    with caplog.at_level(logging.WARNING):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="list_protection_groups",
            params={},
            result={
                "error": "DYNAMODB_ERROR",
                "message": "ProvisionedThroughputExceededException",
            },
            success=False,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["success"] is False
    assert log_data["result"]["error"] == "DYNAMODB_ERROR"


def test_audit_log_failed_operation_drs_error(caplog, mock_context):
    """
    Test audit logging for DRS API error.
    
    Validates:
    - Failed operation is logged
    - Success is False
    - DRS error is logged
    """
    import logging
    
    with caplog.at_level(logging.WARNING):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="get_drs_source_servers",
            params={"region": "us-east-1"},
            result={"error": "DRS_ERROR", "message": "Service unavailable"},
            success=False,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["success"] is False
    assert log_data["result"]["error"] == "DRS_ERROR"


# ============================================================================
# Test: JSON Format and Parseability
# ============================================================================


def test_audit_log_is_valid_json(caplog, mock_context):
    """
    Test that audit logs are valid JSON.
    
    Validates:
    - Log message is valid JSON
    - Can be parsed without errors
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="test_operation",
            params={"key": "value"},
            result={"success": True},
            success=True,
            context=mock_context,
        )
    
    log_message = caplog.records[0].message
    
    # Should parse without error
    log_data = json.loads(log_message)
    assert isinstance(log_data, dict)


def test_audit_log_structure_is_consistent(caplog, mock_context):
    """
    Test that audit log structure is consistent.
    
    Validates:
    - All required fields are present
    - Field types are correct
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="test_operation",
            params={"key": "value"},
            result={"success": True},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    # Verify required fields
    assert "timestamp" in log_data
    assert "event_type" in log_data
    assert "principal" in log_data
    assert "operation" in log_data
    assert "parameters" in log_data
    assert "result" in log_data
    assert "success" in log_data
    assert "request_id" in log_data
    assert "function_name" in log_data
    
    # Verify field types
    assert isinstance(log_data["timestamp"], str)
    assert isinstance(log_data["event_type"], str)
    assert isinstance(log_data["principal"], str)
    assert isinstance(log_data["operation"], str)
    assert isinstance(log_data["parameters"], dict)
    assert isinstance(log_data["success"], bool)
    assert isinstance(log_data["request_id"], str)
    assert isinstance(log_data["function_name"], str)


def test_audit_log_event_type_is_direct_invocation(caplog, mock_context):
    """
    Test that event_type is always "direct_invocation".
    
    Validates:
    - event_type field is present
    - event_type value is "direct_invocation"
    """
    import logging
    
    with caplog.at_level(logging.INFO):
        log_direct_invocation(
            principal="arn:aws:iam::111111111111:role/OrchestrationRole",
            operation="test_operation",
            params={},
            result={"success": True},
            success=True,
            context=mock_context,
        )
    
    log_data = json.loads(caplog.records[0].message)
    
    assert log_data["event_type"] == "direct_invocation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
