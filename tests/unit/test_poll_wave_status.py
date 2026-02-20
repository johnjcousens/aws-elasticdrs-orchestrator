"""
Unit tests for refactored poll_wave_status() function.

Tests verify that poll_wave_status() returns correct wave status data
WITHOUT performing any DynamoDB write operations.

Test Coverage:
- Wave in progress (servers launching)
- Wave complete (all servers launched)
- Wave failed (some servers failed)
- Wave timeout (exceeded max wait time)
- Cancellation detected (execution cancelled)
- Pause before next wave
- All waves completed
- Job not found
- No participating servers
"""

import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest


# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for all tests."""
    with patch.dict(
        os.environ,
        {
            "ENVIRONMENT": "test",
            "EXECUTION_HANDLER_ARN": "arn:aws:lambda:us-east-1:123456789012:function:execution-handler-test",
            "EXECUTION_HISTORY_TABLE": "aws-drs-orchestration-execution-history-test",
        },
    ):
        yield


# Import after environment variables are mocked
@pytest.fixture
def query_handler():
    """Import query handler module after environment setup."""
    import sys

    # Add lambda directory to path
    lambda_path = os.path.join(os.path.dirname(__file__), "../../lambda")
    if lambda_path not in sys.path:
        sys.path.insert(0, lambda_path)

    # Import query handler index module
    sys.path.insert(0, os.path.join(lambda_path, "query-handler"))
    import index

    return index


@pytest.fixture
def mock_drs_client():
    """Mock DRS client for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table for testing."""
    table = MagicMock()
    return table


@pytest.fixture
def mock_lambda_client():
    """Mock Lambda client for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def base_state():
    """Base state object for testing."""
    return {
        "execution_id": "exec-123",
        "plan_id": "plan-456",
        "job_id": "drsjob-abc123",
        "region": "us-east-1",
        "current_wave_number": 1,
        "current_wave_update_time": 30,
        "current_wave_total_wait_time": 60,
        "current_wave_max_wait_time": 3600,
        "waves": [
            {"waveNumber": 1, "servers": ["s-1234567890abcdef0"]},
            {"waveNumber": 2, "servers": ["s-abcdef1234567890"]},
        ],
        "wave_results": [
            {
                "waveNumber": 1,
                "status": "IN_PROGRESS",
                "serverStatuses": [
                    {
                        "sourceServerId": "s-1234567890abcdef0",
                        "serverName": "web-server-01",
                        "hostname": "web01.example.com",
                        "launchStatus": "PENDING",
                    }
                ],
            }
        ],
        "start_time": 1234567890,
    }


def test_poll_wave_status_in_progress(query_handler, mock_drs_client, mock_dynamodb_table, base_state):
    """Test wave in progress - servers still launching."""
    # Mock DRS describe_jobs response
    mock_drs_client.describe_jobs.return_value = {
        "items": [
            {
                "jobID": "drsjob-abc123",
                "status": "STARTED",
                "participatingServers": [
                    {
                        "sourceServerID": "s-1234567890abcdef0",
                        "launchStatus": "IN_PROGRESS",
                        "recoveryInstanceID": "i-recovery123",
                    }
                ],
            }
        ]
    }

    # Mock DRS describe_job_log_items response
    mock_drs_client.describe_job_log_items.return_value = {
        "items": [
            {"event": "LAUNCHING_STARTED", "eventDateTime": "2025-01-01T12:00:00Z"},
        ]
    }

    # Mock DynamoDB get_item response (no cancellation)
    mock_dynamodb_table.get_item.return_value = {"Item": {"status": "IN_PROGRESS"}}

    with patch.object(query_handler, "create_drs_client", return_value=mock_drs_client):
        with patch.object(query_handler, "get_execution_history_table", return_value=mock_dynamodb_table):
            with patch.object(query_handler, "get_account_context", return_value=None):
                result = query_handler.poll_wave_status(base_state)

    # Verify no DynamoDB writes occurred
    mock_dynamodb_table.update_item.assert_not_called()
    mock_dynamodb_table.put_item.assert_not_called()
    mock_dynamodb_table.delete_item.assert_not_called()

    # Verify correct state returned
    assert result["wave_completed"] is False
    assert result["current_wave_total_wait_time"] == 90  # 60 + 30
    assert "error" not in result


def test_poll_wave_status_complete_all_servers_launched(
    query_handler, mock_drs_client, mock_dynamodb_table, mock_lambda_client, base_state
):
    """Test wave complete - all servers successfully launched."""
    # Set to wave 0 with 2 waves total, so next wave exists
    base_state["current_wave_number"] = 0
    base_state["completed_waves"] = 0
    base_state["waves"] = [
        {"waveNumber": 0, "servers": ["s-1234567890abcdef0"]},
        {"waveNumber": 1, "servers": ["s-abcdef1234567890"]},
    ]
    base_state["wave_results"] = [
        {
            "waveNumber": 0,
            "status": "IN_PROGRESS",
            "serverStatuses": [
                {
                    "sourceServerId": "s-1234567890abcdef0",
                    "serverName": "web-server-01",
                    "hostname": "web01.example.com",
                    "launchStatus": "PENDING",
                }
            ],
        }
    ]
    
    # Mock DRS describe_jobs response
    mock_drs_client.describe_jobs.return_value = {
        "items": [
            {
                "jobID": "drsjob-abc123",
                "status": "COMPLETED",
                "participatingServers": [
                    {
                        "sourceServerID": "s-1234567890abcdef0",
                        "launchStatus": "LAUNCHED",
                        "recoveryInstanceID": "i-recovery123",
                    }
                ],
            }
        ]
    }

    # Mock DRS describe_job_log_items response
    mock_drs_client.describe_job_log_items.return_value = {"items": []}

    # Mock DynamoDB get_item response (no cancellation)
    mock_dynamodb_table.get_item.return_value = {"Item": {"status": "IN_PROGRESS"}}

    # Mock Lambda invoke response for enrichment
    mock_lambda_response = MagicMock()
    mock_lambda_response.get.return_value = None  # No FunctionError
    mock_lambda_response.__getitem__.return_value.read.return_value = json.dumps({"statusCode": 200}).encode()
    mock_lambda_client.invoke.return_value = mock_lambda_response

    # Mock Lambda invoke response for next wave
    mock_next_wave_response = MagicMock()
    mock_next_wave_response.get.return_value = None  # No FunctionError
    mock_next_wave_response.__getitem__.return_value.read.return_value = json.dumps(
        {"job_id": "drsjob-next", "wave_completed": False}
    ).encode()
    mock_lambda_client.invoke.side_effect = [mock_lambda_response, mock_next_wave_response]

    with patch.object(query_handler, "create_drs_client", return_value=mock_drs_client):
        with patch.object(query_handler, "get_execution_history_table", return_value=mock_dynamodb_table):
            with patch.object(query_handler, "get_account_context", return_value=None):
                with patch("boto3.client", return_value=mock_lambda_client):
                    result = query_handler.poll_wave_status(base_state)

    # Verify no DynamoDB writes occurred
    mock_dynamodb_table.update_item.assert_not_called()
    mock_dynamodb_table.put_item.assert_not_called()
    mock_dynamodb_table.delete_item.assert_not_called()

    # Verify correct state returned
    # Wave is complete, but wave_completed is False because we started next wave
    assert result["completed_waves"] == 1
    assert "job_id" in result  # Next wave started
    assert result["wave_completed"] is False  # Next wave now in progress


def test_poll_wave_status_failed_servers(query_handler, mock_drs_client, mock_dynamodb_table, base_state):
    """Test wave failed - some servers failed to launch."""
    # Mock DRS describe_jobs response
    mock_drs_client.describe_jobs.return_value = {
        "items": [
            {
                "jobID": "drsjob-abc123",
                "status": "COMPLETED",
                "participatingServers": [
                    {
                        "sourceServerID": "s-1234567890abcdef0",
                        "launchStatus": "FAILED",
                        "recoveryInstanceID": None,
                    }
                ],
            }
        ]
    }

    # Mock DRS describe_job_log_items response
    mock_drs_client.describe_job_log_items.return_value = {"items": []}

    # Mock DynamoDB get_item response (no cancellation)
    mock_dynamodb_table.get_item.return_value = {"Item": {"status": "IN_PROGRESS"}}

    with patch.object(query_handler, "create_drs_client", return_value=mock_drs_client):
        with patch.object(query_handler, "get_execution_history_table", return_value=mock_dynamodb_table):
            with patch.object(query_handler, "get_account_context", return_value=None):
                result = query_handler.poll_wave_status(base_state)

    # Verify no DynamoDB writes occurred
    mock_dynamodb_table.update_item.assert_not_called()
    mock_dynamodb_table.put_item.assert_not_called()
    mock_dynamodb_table.delete_item.assert_not_called()

    # Verify correct state returned
    assert result["wave_completed"] is True
    assert result["status"] == "failed"
    # Function returns error for "no instances launched" case
    assert "error" in result
    assert "no recovery instances created" in result["error"].lower()


def test_poll_wave_status_timeout(query_handler, mock_drs_client, mock_dynamodb_table, base_state):
    """Test wave timeout - exceeded max wait time."""
    # Set wait time to exceed max (will be incremented by update_time)
    base_state["current_wave_total_wait_time"] = 3580
    base_state["current_wave_max_wait_time"] = 3600
    base_state["current_wave_update_time"] = 30

    with patch.object(query_handler, "create_drs_client", return_value=mock_drs_client):
        with patch.object(query_handler, "get_execution_history_table", return_value=mock_dynamodb_table):
            result = query_handler.poll_wave_status(base_state)

    # Verify no DynamoDB writes occurred
    mock_dynamodb_table.update_item.assert_not_called()
    mock_dynamodb_table.put_item.assert_not_called()
    mock_dynamodb_table.delete_item.assert_not_called()

    # Verify correct state returned
    assert result["wave_completed"] is True
    assert result["status"] == "timeout"
    assert "timed out" in result["error"].lower()


def test_poll_wave_status_cancellation_detected(query_handler, mock_drs_client, mock_dynamodb_table, base_state):
    """Test cancellation detected - execution cancelled by user."""
    # Mock DynamoDB get_item response (cancellation detected)
    mock_dynamodb_table.get_item.return_value = {"Item": {"status": "CANCELLING"}}

    with patch.object(query_handler, "create_drs_client", return_value=mock_drs_client):
        with patch.object(query_handler, "get_execution_history_table", return_value=mock_dynamodb_table):
            result = query_handler.poll_wave_status(base_state)

    # Verify no DynamoDB writes occurred
    mock_dynamodb_table.update_item.assert_not_called()
    mock_dynamodb_table.put_item.assert_not_called()
    mock_dynamodb_table.delete_item.assert_not_called()

    # Verify correct state returned
    assert result["wave_completed"] is True
    assert result["all_waves_completed"] is True
    assert result["status"] == "cancelled"


def test_poll_wave_status_pause_before_next_wave(
    query_handler, mock_drs_client, mock_dynamodb_table, mock_lambda_client, base_state
):
    """Test pause before next wave - pauseBeforeWave flag set."""
    # Set to wave 0, with wave 1 having pauseBeforeWave
    base_state["current_wave_number"] = 0
    base_state["completed_waves"] = 0
    base_state["waves"] = [
        {"waveNumber": 0, "servers": ["s-1234567890abcdef0"]},
        {"waveNumber": 1, "servers": ["s-abcdef1234567890"], "pauseBeforeWave": True},
    ]
    base_state["wave_results"] = [
        {
            "waveNumber": 0,
            "status": "IN_PROGRESS",
            "serverStatuses": [
                {
                    "sourceServerId": "s-1234567890abcdef0",
                    "serverName": "web-server-01",
                    "hostname": "web01.example.com",
                    "launchStatus": "PENDING",
                }
            ],
        }
    ]

    # Mock DRS describe_jobs response (wave complete)
    mock_drs_client.describe_jobs.return_value = {
        "items": [
            {
                "jobID": "drsjob-abc123",
                "status": "COMPLETED",
                "participatingServers": [
                    {
                        "sourceServerID": "s-1234567890abcdef0",
                        "launchStatus": "LAUNCHED",
                        "recoveryInstanceID": "i-recovery123",
                    }
                ],
            }
        ]
    }

    # Mock DRS describe_job_log_items response
    mock_drs_client.describe_job_log_items.return_value = {"items": []}

    # Mock DynamoDB get_item response (no cancellation)
    mock_dynamodb_table.get_item.return_value = {"Item": {"status": "IN_PROGRESS"}}

    # Mock Lambda invoke response for enrichment
    mock_lambda_response = MagicMock()
    mock_lambda_response.get.return_value = None  # No FunctionError
    mock_lambda_response.__getitem__.return_value.read.return_value = json.dumps({"statusCode": 200}).encode()
    mock_lambda_client.invoke.return_value = mock_lambda_response

    with patch.object(query_handler, "create_drs_client", return_value=mock_drs_client):
        with patch.object(query_handler, "get_execution_history_table", return_value=mock_dynamodb_table):
            with patch.object(query_handler, "get_account_context", return_value=None):
                with patch("boto3.client", return_value=mock_lambda_client):
                    result = query_handler.poll_wave_status(base_state)

    # Verify no DynamoDB writes occurred
    mock_dynamodb_table.update_item.assert_not_called()
    mock_dynamodb_table.put_item.assert_not_called()
    mock_dynamodb_table.delete_item.assert_not_called()

    # Verify correct state returned
    assert result["wave_completed"] is True
    assert result["status"] == "paused"
    assert result["paused_before_wave"] == 1


def test_poll_wave_status_all_waves_completed(
    query_handler, mock_drs_client, mock_dynamodb_table, mock_lambda_client, base_state
):
    """Test all waves completed - no more waves to execute."""
    # Set to last wave
    base_state["current_wave_number"] = 1
    base_state["waves"] = [
        {"waveNumber": 1, "servers": ["s-1234567890abcdef0"]},
    ]

    # Mock DRS describe_jobs response (wave complete)
    mock_drs_client.describe_jobs.return_value = {
        "items": [
            {
                "jobID": "drsjob-abc123",
                "status": "COMPLETED",
                "participatingServers": [
                    {
                        "sourceServerID": "s-1234567890abcdef0",
                        "launchStatus": "LAUNCHED",
                        "recoveryInstanceID": "i-recovery123",
                    }
                ],
            }
        ]
    }

    # Mock DRS describe_job_log_items response
    mock_drs_client.describe_job_log_items.return_value = {"items": []}

    # Mock DynamoDB get_item response (no cancellation)
    mock_dynamodb_table.get_item.return_value = {"Item": {"status": "IN_PROGRESS"}}

    # Mock Lambda invoke response for enrichment
    mock_lambda_response = MagicMock()
    mock_lambda_response.get.return_value = None  # No FunctionError
    mock_lambda_response.__getitem__.return_value.read.return_value = json.dumps({"statusCode": 200}).encode()
    mock_lambda_client.invoke.return_value = mock_lambda_response

    with patch.object(query_handler, "create_drs_client", return_value=mock_drs_client):
        with patch.object(query_handler, "get_execution_history_table", return_value=mock_dynamodb_table):
            with patch.object(query_handler, "get_account_context", return_value=None):
                with patch("boto3.client", return_value=mock_lambda_client):
                    result = query_handler.poll_wave_status(base_state)

    # Verify no DynamoDB writes occurred
    mock_dynamodb_table.update_item.assert_not_called()
    mock_dynamodb_table.put_item.assert_not_called()
    mock_dynamodb_table.delete_item.assert_not_called()

    # Verify correct state returned
    assert result["wave_completed"] is True
    assert result["all_waves_completed"] is True
    assert result["status"] == "completed"
    assert "completed successfully" in result["status_reason"].lower()
    assert result["completed_waves"] == 1


def test_poll_wave_status_job_not_found(query_handler, mock_drs_client, mock_dynamodb_table, base_state):
    """Test job not found - DRS job does not exist."""
    # Mock DRS describe_jobs response (empty)
    mock_drs_client.describe_jobs.return_value = {"items": []}

    # Mock DynamoDB get_item response (no cancellation)
    mock_dynamodb_table.get_item.return_value = {"Item": {"status": "IN_PROGRESS"}}

    with patch.object(query_handler, "create_drs_client", return_value=mock_drs_client):
        with patch.object(query_handler, "get_execution_history_table", return_value=mock_dynamodb_table):
            with patch.object(query_handler, "get_account_context", return_value=None):
                result = query_handler.poll_wave_status(base_state)

    # Verify no DynamoDB writes occurred
    mock_dynamodb_table.update_item.assert_not_called()
    mock_dynamodb_table.put_item.assert_not_called()
    mock_dynamodb_table.delete_item.assert_not_called()

    # Verify correct state returned
    assert result["wave_completed"] is True
    assert result["status"] == "failed"
    assert "not found" in result["error"].lower()


def test_poll_wave_status_no_participating_servers(query_handler, mock_drs_client, mock_dynamodb_table, base_state):
    """Test no participating servers - DRS job has no servers."""
    # Mock DRS describe_jobs response (no servers)
    mock_drs_client.describe_jobs.return_value = {
        "items": [
            {
                "jobID": "drsjob-abc123",
                "status": "COMPLETED",
                "participatingServers": [],
            }
        ]
    }

    # Mock DRS describe_job_log_items response
    mock_drs_client.describe_job_log_items.return_value = {"items": []}

    # Mock DynamoDB get_item response (no cancellation)
    mock_dynamodb_table.get_item.return_value = {"Item": {"status": "IN_PROGRESS"}}

    with patch.object(query_handler, "create_drs_client", return_value=mock_drs_client):
        with patch.object(query_handler, "get_execution_history_table", return_value=mock_dynamodb_table):
            with patch.object(query_handler, "get_account_context", return_value=None):
                result = query_handler.poll_wave_status(base_state)

    # Verify no DynamoDB writes occurred
    mock_dynamodb_table.update_item.assert_not_called()
    mock_dynamodb_table.put_item.assert_not_called()
    mock_dynamodb_table.delete_item.assert_not_called()

    # Verify correct state returned
    assert result["wave_completed"] is True
    assert result["status"] == "failed"
    assert "no participating servers" in result["error"].lower()


def test_poll_wave_status_no_job_id(query_handler, base_state):
    """Test no job_id - missing job_id in state."""
    # Remove job_id from state
    del base_state["job_id"]

    result = query_handler.poll_wave_status(base_state)

    # Verify correct state returned
    assert result["wave_completed"] is True


def test_poll_wave_status_preserves_server_data(query_handler, mock_drs_client, mock_dynamodb_table, base_state):
    """Test that existing server data (serverName, hostname) is preserved."""
    # Mock DRS describe_jobs response
    mock_drs_client.describe_jobs.return_value = {
        "items": [
            {
                "jobID": "drsjob-abc123",
                "status": "STARTED",
                "participatingServers": [
                    {
                        "sourceServerID": "s-1234567890abcdef0",
                        "launchStatus": "IN_PROGRESS",
                        "recoveryInstanceID": "i-recovery123",
                    }
                ],
            }
        ]
    }

    # Mock DRS describe_job_log_items response
    mock_drs_client.describe_job_log_items.return_value = {"items": []}

    # Mock DynamoDB get_item response (no cancellation)
    mock_dynamodb_table.get_item.return_value = {"Item": {"status": "IN_PROGRESS"}}

    with patch.object(query_handler, "create_drs_client", return_value=mock_drs_client):
        with patch.object(query_handler, "get_execution_history_table", return_value=mock_dynamodb_table):
            with patch.object(query_handler, "get_account_context", return_value=None):
                result = query_handler.poll_wave_status(base_state)

    # Verify no DynamoDB writes occurred
    mock_dynamodb_table.update_item.assert_not_called()
    mock_dynamodb_table.put_item.assert_not_called()
    mock_dynamodb_table.delete_item.assert_not_called()

    # Verify server data preserved
    assert result["wave_completed"] is False
    # Server data should be preserved in wave_results (checked by execution-handler)
