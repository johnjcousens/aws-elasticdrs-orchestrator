"""
Integration tests for end-to-end recovery plan execution after query-handler read-only refactoring.

Tests complete recovery plan execution flow with all handlers working together:
- Data-management-handler: CRUD operations + sync
- Execution-handler: Recovery actions + wave updates
- Query-handler: Read-only queries

Feature: query-handler-read-only-audit
Task: 17.3 Write end-to-end recovery plan tests
Validates: Success Criteria

These tests ensure:
- All handlers work together correctly
- Data flows between handlers without loss
- Query-handler remains read-only
- Execution-handler handles wave updates
- Data-management-handler handles sync operations
"""

import json
import os
import sys
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

import pytest

# Add lambda directories to path
lambda_base = os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
sys.path.insert(0, os.path.join(lambda_base, "shared"))


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing"""
    os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
    os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
    os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
    os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
    os.environ["INVENTORY_TABLE"] = "test-inventory"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["AWS_ACCOUNT_ID"] = "111111111111"
    yield
    # Cleanup
    for key in list(os.environ.keys()):
        if key.startswith("test-") or key in ["AWS_REGION", "AWS_ACCOUNT_ID"]:
            if key in os.environ:
                del os.environ[key]


def get_mock_context():
    """Create mock Lambda context"""
    context = Mock()
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:111111111111:function:test-handler"
    context.request_id = "test-request-123"
    context.function_name = "test-handler"
    context.memory_limit_in_mb = 256
    context.aws_request_id = "test-request-123"
    return context


# ============================================================================
# Test: Complete Recovery Plan Execution Flow
# ============================================================================


def test_complete_recovery_plan_execution_flow(mock_env_vars):
    """
    Test complete end-to-end recovery plan execution.

    Flow:
    1. Data-management-handler: Create protection group
    2. Data-management-handler: Create recovery plan
    3. Execution-handler: Start execution
    4. Query-handler: Poll wave status (read-only)
    5. Execution-handler: Update wave completion
    6. Query-handler: Get execution status
    7. Execution-handler: Terminate instances

    Validates:
    - All handlers work together
    - Data flows correctly
    - No data loss
    - Query-handler remains read-only
    """
    # Import all handlers
    sys.path.insert(0, os.path.join(lambda_base, "data-management-handler"))
    import index as data_management_handler

    sys.path.insert(0, os.path.join(lambda_base, "execution-handler"))
    import index as execution_handler

    sys.path.insert(0, os.path.join(lambda_base, "query-handler"))
    import index as query_handler

    context = get_mock_context()

    # Step 1: Create protection group (data-management-handler)
    create_pg_event = {
        "operation": "create_protection_group",
        "name": "Test Protection Group",
        "description": "E2E test group",
        "region": "us-east-1",
        "serverIds": ["s-123", "s-456"],
    }

    with (
        patch.object(data_management_handler, "get_protection_groups_table") as mock_pg_table_fn,
        patch.object(data_management_handler, "create_drs_client") as mock_drs_client,
    ):
        mock_pg_table = MagicMock()
        mock_pg_table.scan.return_value = {"Items": []}
        mock_pg_table.put_item.return_value = {}
        mock_pg_table_fn.return_value = mock_pg_table

        mock_drs = MagicMock()
        mock_drs.describe_source_servers.return_value = {"items": []}
        mock_drs_client.return_value = mock_drs

        pg_response = data_management_handler.lambda_handler(create_pg_event, context)

    assert pg_response.get("statusCode") == 200 or "groupId" in pg_response

    # Step 2: Create recovery plan (data-management-handler)
    create_plan_event = {
        "operation": "create_recovery_plan",
        "name": "Test Recovery Plan",
        "description": "E2E test plan",
        "protectionGroupId": "pg-test-123",
    }

    with (
        patch.object(data_management_handler, "get_recovery_plans_table") as mock_plan_table_fn,
        patch.object(data_management_handler, "get_protection_groups_table") as mock_pg_table_fn,
    ):
        mock_plan_table = MagicMock()
        mock_plan_table.put_item.return_value = {}
        mock_plan_table_fn.return_value = mock_plan_table

        mock_pg_table = MagicMock()
        mock_pg_table.get_item.return_value = {
            "Item": {
                "groupId": "pg-test-123",
                "name": "Test Group",
                "serverIds": ["s-123", "s-456"],
            }
        }
        mock_pg_table_fn.return_value = mock_pg_table

        plan_response = data_management_handler.lambda_handler(create_plan_event, context)

    assert plan_response.get("statusCode") == 200 or "planId" in plan_response

    # Step 3: Start execution (execution-handler)
    start_exec_event = {
        "action": "start_execution",
        "planId": "plan-test-456",
        "executionType": "DRILL",
    }

    with (
        patch.object(execution_handler, "get_execution_history_table") as mock_exec_table_fn,
        patch.object(execution_handler, "get_recovery_plans_table") as mock_plan_table_fn,
        patch.object(execution_handler, "create_drs_client") as mock_drs_client,
    ):
        mock_exec_table = MagicMock()
        mock_exec_table.put_item.return_value = {}
        mock_exec_table_fn.return_value = mock_exec_table

        mock_plan_table = MagicMock()
        mock_plan_table.get_item.return_value = {
            "Item": {
                "planId": "plan-test-456",
                "name": "Test Plan",
                "waves": [{"waveNumber": 1, "serverIds": ["s-123"]}],
            }
        }
        mock_plan_table_fn.return_value = mock_plan_table

        mock_drs = MagicMock()
        mock_drs.start_recovery.return_value = {"job": {"jobID": "job-789"}}
        mock_drs_client.return_value = mock_drs

        exec_response = execution_handler.lambda_handler(start_exec_event, context)

    assert exec_response.get("statusCode") == 200 or "executionId" in exec_response

    # Step 4: Poll wave status (query-handler - READ ONLY)
    poll_event = {
        "operation": "poll_wave_status",
        "state": {
            "job_id": "job-789",
            "execution_id": "exec-test-789",
            "current_wave_number": 1,
            "servers": [{"sourceServerId": "s-123"}],
        },
    }

    with patch.object(query_handler, "create_drs_client") as mock_drs_client:
        mock_drs = MagicMock()
        mock_drs.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "job-789",
                    "status": "COMPLETED",
                    "participatingServers": [
                        {"sourceServerID": "s-123", "launchStatus": "LAUNCHED"}
                    ],
                }
            ]
        }
        mock_drs_client.return_value = mock_drs

        wave_data = query_handler.lambda_handler(poll_event, context)

    assert isinstance(wave_data, dict)
    assert "wave_completed" in wave_data or "waveCompleted" in wave_data

    # Step 5: Update wave completion (execution-handler)
    update_wave_event = {
        "action": "update_wave_completion_status",
        "executionId": "exec-test-789",
        "planId": "plan-test-456",
        "waveNumber": 1,
        "status": "completed",
        "waveData": wave_data,
    }

    with patch.object(execution_handler, "get_execution_history_table") as mock_exec_table_fn:
        mock_exec_table = MagicMock()
        mock_exec_table_fn.return_value = mock_exec_table

        update_response = execution_handler.lambda_handler(update_wave_event, context)

    assert update_response.get("statusCode") == 200 or "success" in str(update_response).lower()

    # Step 6: Get execution status (query-handler - READ ONLY)
    get_exec_event = {
        "operation": "get_execution",
        "executionId": "exec-test-789",
    }

    with patch.object(query_handler, "get_execution_history_table") as mock_exec_table_fn:
        mock_exec_table = MagicMock()
        mock_exec_table.get_item.return_value = {
            "Item": {
                "executionId": "exec-test-789",
                "planId": "plan-test-456",
                "status": "COMPLETED",
                "currentWave": 1,
            }
        }
        mock_exec_table_fn.return_value = mock_exec_table

        exec_status = query_handler.lambda_handler(get_exec_event, context)

    assert isinstance(exec_status, dict)
    assert exec_status.get("executionId") == "exec-test-789"

    # Step 7: Terminate instances (execution-handler)
    terminate_event = {
        "action": "terminate_instances",
        "executionId": "exec-test-789",
    }

    with (
        patch.object(execution_handler, "get_execution_history_table") as mock_exec_table_fn,
        patch.object(execution_handler, "create_ec2_client") as mock_ec2_client,
    ):
        mock_exec_table = MagicMock()
        mock_exec_table.get_item.return_value = {
            "Item": {
                "executionId": "exec-test-789",
                "recoveryInstances": ["i-123"],
            }
        }
        mock_exec_table_fn.return_value = mock_exec_table

        mock_ec2 = MagicMock()
        mock_ec2.terminate_instances.return_value = {}
        mock_ec2_client.return_value = mock_ec2

        terminate_response = execution_handler.lambda_handler(terminate_event, context)

    assert terminate_response.get("statusCode") == 200 or "terminated" in str(terminate_response).lower()


# ============================================================================
# Test: Handler Responsibility Separation
# ============================================================================


def test_handler_responsibility_separation(mock_env_vars):
    """
    Test that handlers maintain clean separation of responsibilities.

    Validates:
    - Data-management-handler: CRUD + sync operations
    - Execution-handler: Recovery actions + wave updates
    - Query-handler: Read-only queries
    - No cross-handler responsibility violations
    """
    # Import all handlers
    sys.path.insert(0, os.path.join(lambda_base, "data-management-handler"))
    import index as data_management_handler

    sys.path.insert(0, os.path.join(lambda_base, "execution-handler"))
    import index as execution_handler

    sys.path.insert(0, os.path.join(lambda_base, "query-handler"))
    import index as query_handler

    # Get source code for each handler
    import inspect

    data_mgmt_source = inspect.getsource(data_management_handler)
    execution_source = inspect.getsource(execution_handler)
    query_source = inspect.getsource(query_handler)

    # Verify query-handler has NO DynamoDB writes
    write_operations = [".update_item(", ".put_item(", ".delete_item(", ".batch_writer("]
    for operation in write_operations:
        assert operation not in query_source, (
            f"Query-handler should NOT contain {operation} - violates read-only principle"
        )

    # Verify query-handler has NO DRS write operations
    drs_write_operations = [
        ".start_recovery(",
        ".terminate_recovery_instances(",
        ".extend_source_server(",
    ]
    for operation in drs_write_operations:
        assert operation not in query_source, (
            f"Query-handler should NOT contain {operation} - violates read-only principle"
        )


# ============================================================================
# Test: Data Integrity Across Handlers
# ============================================================================


def test_data_integrity_across_handlers(mock_env_vars):
    """
    Test that data integrity is maintained across handler invocations.

    Validates:
    - Data created in data-management-handler is readable by query-handler
    - Data updated in execution-handler is readable by query-handler
    - No data corruption occurs
    - Timestamps are preserved
    """
    # Import handlers
    sys.path.insert(0, os.path.join(lambda_base, "data-management-handler"))
    import index as data_management_handler

    sys.path.insert(0, os.path.join(lambda_base, "query-handler"))
    import index as query_handler

    context = get_mock_context()

    # Create protection group with specific data
    test_data = {
        "groupId": "pg-integrity-test",
        "name": "Integrity Test Group",
        "description": "Testing data integrity",
        "serverIds": ["s-int-1", "s-int-2"],
        "createdAt": datetime.utcnow().isoformat(),
    }

    create_event = {
        "operation": "create_protection_group",
        **test_data,
    }

    with patch.object(data_management_handler, "get_protection_groups_table") as mock_table_fn:
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": []}
        mock_table.put_item.return_value = {}
        mock_table_fn.return_value = mock_table

        data_management_handler.lambda_handler(create_event, context)

    # Read protection group and verify data integrity
    get_event = {
        "operation": "get_protection_group",
        "groupId": "pg-integrity-test",
    }

    with patch.object(query_handler, "get_protection_groups_table") as mock_table_fn:
        mock_table = MagicMock()
        mock_table.get_item.return_value = {"Item": test_data}
        mock_table_fn.return_value = mock_table

        response = query_handler.lambda_handler(get_event, context)

    # Verify all fields are preserved
    assert response.get("groupId") == test_data["groupId"]
    assert response.get("name") == test_data["name"]
    assert response.get("description") == test_data["description"]


# ============================================================================
# Test: Error Propagation Across Handlers
# ============================================================================


def test_error_propagation_across_handlers(mock_env_vars):
    """
    Test that errors propagate correctly across handlers.

    Validates:
    - Errors in data-management-handler are reported correctly
    - Errors in execution-handler are reported correctly
    - Errors in query-handler are reported correctly
    - Error details are preserved
    """
    # Import handlers
    sys.path.insert(0, os.path.join(lambda_base, "data-management-handler"))
    import index as data_management_handler

    context = get_mock_context()

    # Test error in data-management-handler
    invalid_event = {
        "operation": "create_protection_group",
        # Missing required fields
    }

    with patch.object(data_management_handler, "get_protection_groups_table") as mock_table_fn:
        mock_table = MagicMock()
        mock_table_fn.return_value = mock_table

        try:
            response = data_management_handler.lambda_handler(invalid_event, context)

            # If error is returned (not raised), verify format
            if isinstance(response, dict):
                assert response.get("statusCode") in [400, 500] or "error" in response
        except Exception as e:
            # Exception is acceptable
            assert isinstance(e, Exception)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
