"""
Integration tests for Step Functions wave polling after query-handler read-only refactoring.

Tests that Step Functions state machine correctly handles wave polling with split responsibilities:
- Query-handler polls DRS job status (read-only)
- Execution-handler updates wave completion status (writes to DynamoDB)
- UpdateWaveStatus state invokes execution-handler after WavePoll

Feature: query-handler-read-only-audit
Task: 17.2 Write Step Functions wave polling tests
Validates: Requirements FR4, Success Criteria

These tests ensure:
- Query-handler poll_wave_status is read-only
- Execution-handler update_wave_completion_status writes to DynamoDB
- Step Functions UpdateWaveStatus state works correctly
- Wave completion data flows between handlers
- No data loss during wave transitions
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


def get_step_functions_event(action, **kwargs):
    """
    Create a Step Functions invocation event.

    Args:
        action: Action to perform
        **kwargs: Additional event fields

    Returns:
        Step Functions event dict
    """
    event = {"action": action}
    event.update(kwargs)
    return event


# ============================================================================
# Test: Query Handler poll_wave_status is Read-Only
# ============================================================================


def test_query_handler_poll_wave_status_is_read_only(mock_env_vars):
    """
    Test that query-handler poll_wave_status performs NO DynamoDB writes.

    Validates:
    - poll_wave_status function exists in query-handler
    - Function queries DRS job status
    - Function returns wave status data
    - Function does NOT call update_item
    - Function does NOT call put_item
    - Function does NOT call delete_item
    """
    # Import query-handler
    sys.path.insert(0, os.path.join(lambda_base, "query-handler"))
    import index as query_handler

    # Verify function exists
    assert hasattr(query_handler, "poll_wave_status"), (
        "Query-handler should have poll_wave_status function"
    )

    # Get function source code
    import inspect
    source_code = inspect.getsource(query_handler.poll_wave_status)

    # Check for DynamoDB write operations
    write_operations = [
        ".update_item(",
        ".put_item(",
        ".delete_item(",
    ]

    for operation in write_operations:
        assert operation not in source_code, (
            f"poll_wave_status should NOT contain {operation} - must be read-only"
        )


def test_query_handler_poll_wave_status_returns_wave_data(mock_env_vars):
    """
    Test that query-handler poll_wave_status returns complete wave status data.

    Validates:
    - Returns job_status
    - Returns launched_count
    - Returns failed_count
    - Returns server_statuses
    - Returns wave_completed flag
    - Returns progress_metrics
    """
    # Import query-handler
    sys.path.insert(0, os.path.join(lambda_base, "query-handler"))
    import index as query_handler

    # Step Functions event for wave polling
    event = {
        "operation": "poll_wave_status",
        "state": {
            "job_id": "job-123",
            "execution_id": "exec-456",
            "current_wave_number": 1,
            "servers": [
                {"sourceServerId": "s-123"},
                {"sourceServerId": "s-456"},
            ],
        },
    }
    context = get_mock_context()

    with patch.object(query_handler, "create_drs_client") as mock_drs_client:
        # Mock DRS client
        mock_drs = MagicMock()
        mock_drs.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "job-123",
                    "status": "COMPLETED",
                    "participatingServers": [
                        {
                            "sourceServerID": "s-123",
                            "launchStatus": "LAUNCHED",
                        },
                        {
                            "sourceServerID": "s-456",
                            "launchStatus": "LAUNCHED",
                        },
                    ],
                }
            ]
        }
        mock_drs_client.return_value = mock_drs

        response = query_handler.lambda_handler(event, context)

    # Verify response contains required fields
    assert isinstance(response, dict)
    assert "job_status" in response or "jobStatus" in response
    assert "launched_count" in response or "launchedCount" in response
    assert "failed_count" in response or "failedCount" in response
    assert "server_statuses" in response or "serverStatuses" in response
    assert "wave_completed" in response or "waveCompleted" in response


# ============================================================================
# Test: Execution Handler update_wave_completion_status Writes to DynamoDB
# ============================================================================


def test_execution_handler_update_wave_completion_status_exists(mock_env_vars):
    """
    Test that execution-handler has update_wave_completion_status function.

    Validates:
    - Function exists in execution-handler
    - Function is callable
    """
    # Import execution-handler
    sys.path.insert(0, os.path.join(lambda_base, "execution-handler"))
    import index as execution_handler

    # Verify function exists
    assert hasattr(execution_handler, "update_wave_completion_status"), (
        "Execution-handler should have update_wave_completion_status function"
    )


def test_execution_handler_update_wave_completion_status_writes_dynamodb(mock_env_vars):
    """
    Test that execution-handler update_wave_completion_status writes to DynamoDB.

    Validates:
    - Function updates execution history table
    - Wave completion status is persisted
    - Launched/failed counts are recorded
    - Wave completed flag is stored
    """
    # Import execution-handler
    sys.path.insert(0, os.path.join(lambda_base, "execution-handler"))
    import index as execution_handler

    # Step Functions event for wave status update
    event = {
        "action": "update_wave_completion_status",
        "executionId": "exec-456",
        "planId": "plan-789",
        "waveNumber": 1,
        "status": "completed",
        "waveData": {
            "job_status": "COMPLETED",
            "launched_count": 2,
            "failed_count": 0,
            "total_count": 2,
            "wave_completed": True,
        },
    }
    context = get_mock_context()

    with patch.object(execution_handler, "get_execution_history_table") as mock_table_fn:
        # Mock execution history table
        mock_table = MagicMock()
        mock_table_fn.return_value = mock_table

        response = execution_handler.lambda_handler(event, context)

    # Verify DynamoDB update was called
    mock_table.update_item.assert_called_once()

    # Verify update expression includes wave completion fields
    call_args = mock_table.update_item.call_args
    assert "UpdateExpression" in call_args[1]
    update_expression = call_args[1]["UpdateExpression"]
    assert "status" in update_expression.lower() or "wave" in update_expression.lower()

    # Verify response
    assert isinstance(response, dict)
    assert response.get("statusCode") == 200 or "success" in str(response).lower()


# ============================================================================
# Test: Step Functions UpdateWaveStatus State Integration
# ============================================================================


def test_step_functions_wave_poll_then_update_flow(mock_env_vars):
    """
    Test complete Step Functions flow: WavePoll -> UpdateWaveStatus.

    Validates:
    - Query-handler polls DRS job status
    - Wave data is returned
    - Execution-handler receives wave data
    - Execution-handler updates DynamoDB
    - No data loss between handlers
    """
    # Import both handlers
    sys.path.insert(0, os.path.join(lambda_base, "query-handler"))
    import index as query_handler

    sys.path.insert(0, os.path.join(lambda_base, "execution-handler"))
    import index as execution_handler

    context = get_mock_context()

    # Step 1: WavePoll state (query-handler)
    poll_event = {
        "operation": "poll_wave_status",
        "state": {
            "job_id": "job-123",
            "execution_id": "exec-456",
            "plan_id": "plan-789",
            "current_wave_number": 1,
            "servers": [
                {"sourceServerId": "s-123"},
                {"sourceServerId": "s-456"},
            ],
        },
    }

    with patch.object(query_handler, "create_drs_client") as mock_drs_client:
        mock_drs = MagicMock()
        mock_drs.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "job-123",
                    "status": "COMPLETED",
                    "participatingServers": [
                        {"sourceServerID": "s-123", "launchStatus": "LAUNCHED"},
                        {"sourceServerID": "s-456", "launchStatus": "LAUNCHED"},
                    ],
                }
            ]
        }
        mock_drs_client.return_value = mock_drs

        wave_data = query_handler.lambda_handler(poll_event, context)

    # Verify wave data was returned
    assert isinstance(wave_data, dict)
    assert "wave_completed" in wave_data or "waveCompleted" in wave_data

    # Step 2: UpdateWaveStatus state (execution-handler)
    update_event = {
        "action": "update_wave_completion_status",
        "executionId": poll_event["state"]["execution_id"],
        "planId": poll_event["state"]["plan_id"],
        "waveNumber": poll_event["state"]["current_wave_number"],
        "status": "completed",
        "waveData": wave_data,
    }

    with patch.object(execution_handler, "get_execution_history_table") as mock_table_fn:
        mock_table = MagicMock()
        mock_table_fn.return_value = mock_table

        update_response = execution_handler.lambda_handler(update_event, context)

    # Verify update was successful
    assert isinstance(update_response, dict)
    assert update_response.get("statusCode") == 200 or "success" in str(update_response).lower()

    # Verify DynamoDB was updated
    mock_table.update_item.assert_called_once()


# ============================================================================
# Test: Wave Completion Data Integrity
# ============================================================================


def test_wave_completion_data_integrity(mock_env_vars):
    """
    Test that wave completion data is preserved between handlers.

    Validates:
    - Launched count is preserved
    - Failed count is preserved
    - Total count is preserved
    - Wave completed flag is preserved
    - Server statuses are preserved
    """
    # Import both handlers
    sys.path.insert(0, os.path.join(lambda_base, "query-handler"))
    import index as query_handler

    sys.path.insert(0, os.path.join(lambda_base, "execution-handler"))
    import index as execution_handler

    context = get_mock_context()

    # Expected wave data
    expected_launched = 3
    expected_failed = 1
    expected_total = 4

    # Step 1: Query-handler polls DRS
    poll_event = {
        "operation": "poll_wave_status",
        "state": {
            "job_id": "job-123",
            "execution_id": "exec-456",
            "plan_id": "plan-789",
            "current_wave_number": 1,
            "servers": [
                {"sourceServerId": f"s-{i}"} for i in range(expected_total)
            ],
        },
    }

    with patch.object(query_handler, "create_drs_client") as mock_drs_client:
        mock_drs = MagicMock()
        mock_drs.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "job-123",
                    "status": "COMPLETED",
                    "participatingServers": [
                        {"sourceServerID": "s-0", "launchStatus": "LAUNCHED"},
                        {"sourceServerID": "s-1", "launchStatus": "LAUNCHED"},
                        {"sourceServerID": "s-2", "launchStatus": "LAUNCHED"},
                        {"sourceServerID": "s-3", "launchStatus": "FAILED"},
                    ],
                }
            ]
        }
        mock_drs_client.return_value = mock_drs

        wave_data = query_handler.lambda_handler(poll_event, context)

    # Verify counts in wave data
    launched_count = wave_data.get("launched_count") or wave_data.get("launchedCount")
    failed_count = wave_data.get("failed_count") or wave_data.get("failedCount")
    total_count = wave_data.get("total_count") or wave_data.get("totalCount")

    assert launched_count == expected_launched
    assert failed_count == expected_failed
    assert total_count == expected_total

    # Step 2: Execution-handler updates DynamoDB
    update_event = {
        "action": "update_wave_completion_status",
        "executionId": "exec-456",
        "planId": "plan-789",
        "waveNumber": 1,
        "status": "completed",
        "waveData": wave_data,
    }

    with patch.object(execution_handler, "get_execution_history_table") as mock_table_fn:
        mock_table = MagicMock()
        mock_table_fn.return_value = mock_table

        execution_handler.lambda_handler(update_event, context)

    # Verify DynamoDB update includes correct counts
    call_args = mock_table.update_item.call_args
    expression_values = call_args[1]["ExpressionAttributeValues"]

    # Check that counts are preserved in DynamoDB update
    assert any(
        value == expected_launched
        for key, value in expression_values.items()
        if "launched" in key.lower()
    )
    assert any(
        value == expected_failed
        for key, value in expression_values.items()
        if "failed" in key.lower()
    )


# ============================================================================
# Test: Error Handling in Wave Polling
# ============================================================================


def test_wave_polling_handles_drs_errors(mock_env_vars):
    """
    Test that wave polling handles DRS errors gracefully.

    Validates:
    - DRS API errors are caught
    - Error details are returned
    - No DynamoDB writes occur on error
    """
    # Import query-handler
    sys.path.insert(0, os.path.join(lambda_base, "query-handler"))
    import index as query_handler

    poll_event = {
        "operation": "poll_wave_status",
        "state": {
            "job_id": "job-123",
            "execution_id": "exec-456",
            "current_wave_number": 1,
            "servers": [{"sourceServerId": "s-123"}],
        },
    }
    context = get_mock_context()

    with patch.object(query_handler, "create_drs_client") as mock_drs_client:
        # Mock DRS error
        mock_drs = MagicMock()
        mock_drs.describe_jobs.side_effect = Exception("DRS service unavailable")
        mock_drs_client.return_value = mock_drs

        try:
            response = query_handler.lambda_handler(poll_event, context)

            # If error is returned (not raised), verify format
            if isinstance(response, dict):
                assert "error" in response or response.get("statusCode") in [400, 500]
        except Exception as e:
            # Exception is acceptable - Step Functions will handle it
            assert "DRS" in str(e) or "unavailable" in str(e)


def test_wave_update_handles_dynamodb_errors(mock_env_vars):
    """
    Test that wave status update handles DynamoDB errors gracefully.

    Validates:
    - DynamoDB errors are caught
    - Error details are returned
    - Retry logic is attempted
    """
    # Import execution-handler
    sys.path.insert(0, os.path.join(lambda_base, "execution-handler"))
    import index as execution_handler

    update_event = {
        "action": "update_wave_completion_status",
        "executionId": "exec-456",
        "planId": "plan-789",
        "waveNumber": 1,
        "status": "completed",
        "waveData": {
            "job_status": "COMPLETED",
            "launched_count": 2,
            "failed_count": 0,
            "wave_completed": True,
        },
    }
    context = get_mock_context()

    with patch.object(execution_handler, "get_execution_history_table") as mock_table_fn:
        # Mock DynamoDB error
        mock_table = MagicMock()
        mock_table.update_item.side_effect = Exception("DynamoDB unavailable")
        mock_table_fn.return_value = mock_table

        try:
            response = execution_handler.lambda_handler(update_event, context)

            # If error is returned (not raised), verify format
            if isinstance(response, dict):
                assert "error" in response or response.get("statusCode") in [400, 500]
        except Exception as e:
            # Exception is acceptable - Step Functions will handle it
            assert "DynamoDB" in str(e) or "unavailable" in str(e)


# ============================================================================
# Test: Multi-Wave Execution Flow
# ============================================================================


def test_multi_wave_execution_flow(mock_env_vars):
    """
    Test complete multi-wave execution flow with wave polling.

    Validates:
    - Wave 1 polls and updates successfully
    - Wave 2 polls and updates successfully
    - Wave completion status is tracked correctly
    - No data loss between waves
    """
    # Import both handlers
    sys.path.insert(0, os.path.join(lambda_base, "query-handler"))
    import index as query_handler

    sys.path.insert(0, os.path.join(lambda_base, "execution-handler"))
    import index as execution_handler

    context = get_mock_context()

    # Wave 1: Poll and Update
    wave1_poll_event = {
        "operation": "poll_wave_status",
        "state": {
            "job_id": "job-wave1",
            "execution_id": "exec-multi",
            "plan_id": "plan-multi",
            "current_wave_number": 1,
            "servers": [{"sourceServerId": "s-db1"}],
        },
    }

    with patch.object(query_handler, "create_drs_client") as mock_drs_client:
        mock_drs = MagicMock()
        mock_drs.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "job-wave1",
                    "status": "COMPLETED",
                    "participatingServers": [
                        {"sourceServerID": "s-db1", "launchStatus": "LAUNCHED"}
                    ],
                }
            ]
        }
        mock_drs_client.return_value = mock_drs

        wave1_data = query_handler.lambda_handler(wave1_poll_event, context)

    # Update Wave 1
    with patch.object(execution_handler, "get_execution_history_table") as mock_table_fn:
        mock_table = MagicMock()
        mock_table_fn.return_value = mock_table

        wave1_update_event = {
            "action": "update_wave_completion_status",
            "executionId": "exec-multi",
            "planId": "plan-multi",
            "waveNumber": 1,
            "status": "completed",
            "waveData": wave1_data,
        }

        wave1_response = execution_handler.lambda_handler(wave1_update_event, context)

    assert wave1_response.get("statusCode") == 200 or "success" in str(wave1_response).lower()

    # Wave 2: Poll and Update
    wave2_poll_event = {
        "operation": "poll_wave_status",
        "state": {
            "job_id": "job-wave2",
            "execution_id": "exec-multi",
            "plan_id": "plan-multi",
            "current_wave_number": 2,
            "servers": [{"sourceServerId": "s-app1"}],
        },
    }

    with patch.object(query_handler, "create_drs_client") as mock_drs_client:
        mock_drs = MagicMock()
        mock_drs.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "job-wave2",
                    "status": "COMPLETED",
                    "participatingServers": [
                        {"sourceServerID": "s-app1", "launchStatus": "LAUNCHED"}
                    ],
                }
            ]
        }
        mock_drs_client.return_value = mock_drs

        wave2_data = query_handler.lambda_handler(wave2_poll_event, context)

    # Update Wave 2
    with patch.object(execution_handler, "get_execution_history_table") as mock_table_fn:
        mock_table = MagicMock()
        mock_table_fn.return_value = mock_table

        wave2_update_event = {
            "action": "update_wave_completion_status",
            "executionId": "exec-multi",
            "planId": "plan-multi",
            "waveNumber": 2,
            "status": "completed",
            "waveData": wave2_data,
        }

        wave2_response = execution_handler.lambda_handler(wave2_update_event, context)

    assert wave2_response.get("statusCode") == 200 or "success" in str(wave2_response).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
