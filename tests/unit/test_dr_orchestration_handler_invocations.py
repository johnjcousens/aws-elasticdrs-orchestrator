"""
Unit tests for DR Orchestration Lambda handler invocations.

Tests verify that the NEW orchestration Lambda correctly invokes
execution-handler and query-handler Lambdas instead of calling
DRS APIs directly.

**Validates**: Requirements 4.11-4.15
- Task 4.12: Test begin_wave_plan() invokes execution-handler correctly
- Task 4.13: Test poll_wave_status() invokes query-handler correctly
- Task 4.14: Test resume_wave() invokes execution-handler correctly
- Task 4.15: Test error handling for invocation failures
"""

import json
import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest


# Module-level setup to load dr-orchestration-stepfunction index
lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
dr_orch_dir = os.path.join(lambda_dir, "dr-orchestration-stepfunction")


@pytest.fixture(scope="function", autouse=True)
def setup_dr_orch_import():
    """Ensure dr-orchestration-stepfunction index is imported correctly"""
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    if "index" in sys.modules:
        del sys.modules["index"]

    sys.path.insert(0, dr_orch_dir)
    sys.path.insert(0, lambda_dir)

    yield

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
            "EXECUTION_HANDLER_ARN": (
                "arn:aws:lambda:us-east-1:123456789012:function:"
                "test-execution-handler"
            ),
            "QUERY_HANDLER_ARN": (
                "arn:aws:lambda:us-east-1:123456789012:function:"
                "test-query-handler"
            ),
        },
    ):
        yield


@pytest.fixture
def mock_lambda_client():
    """Mock boto3 Lambda client"""
    client = Mock()
    return client


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table"""
    table = Mock()
    table.update_item.return_value = {}
    return table


@pytest.fixture
def sample_state():
    """Sample state object for testing"""
    return {
        "plan_id": "plan-123",
        "execution_id": "exec-456",
        "is_drill": True,
        "waves": [{"protectionGroupId": "pg-1", "waveNumber": 0}],
        "total_waves": 1,
        "current_wave_number": 0,
        "wave_results": [],
        "accountContext": {
            "accountId": "123456789012",
            "isCurrentAccount": True,
        },
    }


@pytest.fixture
def sample_plan():
    """Sample recovery plan for testing"""
    return {
        "planId": "plan-123",
        "planName": "Test Plan",
        "waves": [
            {
                "waveNumber": 0,
                "waveName": "Wave 1",
                "protectionGroupId": "pg-1",
            }
        ],
    }


class TestBeginWavePlanInvokesExecutionHandler:
    """Test begin_wave_plan() invokes execution-handler (Task 4.12)"""

    def test_begin_wave_plan_invokes_execution_handler_correctly(
        self,
        mock_env_vars,
        mock_lambda_client,
        mock_dynamodb_table,
        sample_plan,
    ):
        """
        Test that begin_wave_plan() invokes execution-handler with
        correct payload
        """
        from index import begin_wave_plan

        # Setup mock response from execution-handler
        mock_response = {
            "StatusCode": 200,
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {
                        "job_id": "drsjob-123",
                        "region": "us-east-1",
                        "server_ids": ["s-001"],
                        "wave_completed": False,
                    }
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        event = {
            "plan": sample_plan,
            "execution": "exec-456",
            "isDrill": True,
            "accountContext": {
                "accountId": "123456789012",
                "isCurrentAccount": True,
            },
        }

        with patch("boto3.client", return_value=mock_lambda_client):
            with patch(
                "index.get_execution_history_table",
                return_value=mock_dynamodb_table,
            ):
                result = begin_wave_plan(event)

        # Verify Lambda invocation
        mock_lambda_client.invoke.assert_called_once()
        call_args = mock_lambda_client.invoke.call_args

        # Verify function name
        assert (
            call_args[1]["FunctionName"]
            == os.environ["EXECUTION_HANDLER_ARN"]
        )
        assert call_args[1]["InvocationType"] == "RequestResponse"

        # Verify payload structure
        payload = json.loads(call_args[1]["Payload"])
        assert payload["action"] == "start_wave_recovery"
        assert payload["wave_number"] == 0
        assert "state" in payload

        # Verify state in payload
        state = payload["state"]
        assert state["plan_id"] == "plan-123"
        assert state["execution_id"] == "exec-456"
        assert state["is_drill"] is True
        assert state["total_waves"] == 1

        # Verify result contains updated state from handler
        assert result["job_id"] == "drsjob-123"
        assert result["region"] == "us-east-1"
        assert result["server_ids"] == ["s-001"]

    def test_begin_wave_plan_handles_empty_waves(
        self, mock_env_vars, mock_lambda_client, mock_dynamodb_table
    ):
        """Test begin_wave_plan() with no waves (edge case)"""
        from index import begin_wave_plan

        event = {
            "plan": {
                "planId": "plan-123",
                "planName": "Empty Plan",
                "waves": [],
            },
            "execution": "exec-456",
            "isDrill": True,
        }

        with patch("boto3.client", return_value=mock_lambda_client):
            with patch(
                "index.get_execution_history_table",
                return_value=mock_dynamodb_table,
            ):
                result = begin_wave_plan(event)

        # Verify Lambda was NOT invoked (no waves)
        mock_lambda_client.invoke.assert_not_called()

        # Verify state marked as completed
        assert result["all_waves_completed"] is True
        assert result["status"] == "completed"

    def test_begin_wave_plan_updates_dynamodb(
        self,
        mock_env_vars,
        mock_lambda_client,
        mock_dynamodb_table,
        sample_plan,
    ):
        """Test that begin_wave_plan() updates DynamoDB execution status"""
        from index import begin_wave_plan

        mock_response = {
            "StatusCode": 200,
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {"job_id": "drsjob-123", "wave_completed": False}
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        event = {
            "plan": sample_plan,
            "execution": "exec-456",
            "isDrill": True,
        }

        with patch("boto3.client", return_value=mock_lambda_client):
            with patch(
                "index.get_execution_history_table",
                return_value=mock_dynamodb_table,
            ):
                begin_wave_plan(event)

        # Verify DynamoDB update was called
        mock_dynamodb_table.update_item.assert_called_once()
        call_args = mock_dynamodb_table.update_item.call_args

        # Verify update sets status to RUNNING
        assert call_args[1]["Key"]["executionId"] == "exec-456"
        assert call_args[1]["Key"]["planId"] == "plan-123"
        assert (
            call_args[1]["ExpressionAttributeValues"][":status"] == "RUNNING"
        )


class TestPollWaveStatusInvokesQueryHandler:
    """Test poll_wave_status() invokes query-handler (Task 4.13)"""

    def test_poll_wave_status_invokes_query_handler_correctly(
        self, mock_env_vars, mock_lambda_client, sample_state
    ):
        """
        Test that poll_wave_status() invokes query-handler with
        correct payload
        """
        from index import poll_wave_status

        # Setup mock response from query-handler
        mock_response = {
            "StatusCode": 200,
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {
                        "wave_completed": False,
                        "status": "running",
                        "current_wave_total_wait_time": 30,
                    }
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        event = {"application": sample_state}

        with patch("boto3.client", return_value=mock_lambda_client):
            result = poll_wave_status(event)

        # Verify Lambda invocation
        mock_lambda_client.invoke.assert_called_once()
        call_args = mock_lambda_client.invoke.call_args

        # Verify function name
        assert (
            call_args[1]["FunctionName"] == os.environ["QUERY_HANDLER_ARN"]
        )
        assert call_args[1]["InvocationType"] == "RequestResponse"

        # Verify payload structure
        payload = json.loads(call_args[1]["Payload"])
        assert payload["action"] == "poll_wave_status"
        assert "state" in payload

        # Verify state in payload
        state = payload["state"]
        assert state["plan_id"] == "plan-123"
        assert state["execution_id"] == "exec-456"

        # Verify result contains updated state from handler
        assert result["wave_completed"] is False
        assert result["status"] == "running"

    def test_poll_wave_status_handles_wave_completed(
        self, mock_env_vars, mock_lambda_client, sample_state
    ):
        """Test poll_wave_status() when wave is completed"""
        from index import poll_wave_status

        # Setup mock response indicating wave completed
        mock_response = {
            "StatusCode": 200,
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {
                        "wave_completed": True,
                        "status": "completed",
                        "all_waves_completed": True,
                    }
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        event = {"application": sample_state}

        with patch("boto3.client", return_value=mock_lambda_client):
            result = poll_wave_status(event)

        # Verify result indicates completion
        assert result["wave_completed"] is True
        assert result["status"] == "completed"
        assert result["all_waves_completed"] is True

    def test_poll_wave_status_accepts_state_at_root(
        self, mock_env_vars, mock_lambda_client, sample_state
    ):
        """Test poll_wave_status() accepts state at root level"""
        from index import poll_wave_status

        mock_response = {
            "StatusCode": 200,
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {"wave_completed": False, "status": "running"}
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        # Pass state at root level (not nested under "application")
        event = sample_state

        with patch("boto3.client", return_value=mock_lambda_client):
            result = poll_wave_status(event)

        # Verify invocation succeeded
        mock_lambda_client.invoke.assert_called_once()
        assert result["wave_completed"] is False


class TestResumeWaveInvokesExecutionHandler:
    """Test resume_wave() invokes execution-handler (Task 4.14)"""

    def test_resume_wave_invokes_execution_handler_correctly(
        self,
        mock_env_vars,
        mock_lambda_client,
        mock_dynamodb_table,
        sample_state,
    ):
        """
        Test that resume_wave() invokes execution-handler with
        correct payload
        """
        from index import resume_wave

        # Setup state with paused_before_wave
        sample_state["paused_before_wave"] = 1
        sample_state["status"] = "paused"

        # Setup mock response from execution-handler
        mock_response = {
            "StatusCode": 200,
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {
                        "job_id": "drsjob-456",
                        "region": "us-west-2",
                        "wave_completed": False,
                    }
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        event = {"application": sample_state}

        with patch("boto3.client", return_value=mock_lambda_client):
            with patch(
                "index.get_execution_history_table",
                return_value=mock_dynamodb_table,
            ):
                result = resume_wave(event)

        # Verify Lambda invocation
        mock_lambda_client.invoke.assert_called_once()
        call_args = mock_lambda_client.invoke.call_args

        # Verify function name
        assert (
            call_args[1]["FunctionName"]
            == os.environ["EXECUTION_HANDLER_ARN"]
        )
        assert call_args[1]["InvocationType"] == "RequestResponse"

        # Verify payload structure
        payload = json.loads(call_args[1]["Payload"])
        assert payload["action"] == "start_wave_recovery"
        assert payload["wave_number"] == 1  # paused_before_wave
        assert "state" in payload

        # Verify result contains updated state
        assert result["job_id"] == "drsjob-456"
        assert result["region"] == "us-west-2"
        assert result["status"] == "running"
        assert result["paused_before_wave"] is None

    def test_resume_wave_updates_dynamodb(
        self,
        mock_env_vars,
        mock_lambda_client,
        mock_dynamodb_table,
        sample_state,
    ):
        """Test that resume_wave() updates DynamoDB execution status"""
        from index import resume_wave

        sample_state["paused_before_wave"] = 1

        mock_response = {
            "StatusCode": 200,
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {"job_id": "drsjob-456", "wave_completed": False}
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        event = {"application": sample_state}

        with patch("boto3.client", return_value=mock_lambda_client):
            with patch(
                "index.get_execution_history_table",
                return_value=mock_dynamodb_table,
            ):
                resume_wave(event)

        # Verify DynamoDB update was called
        mock_dynamodb_table.update_item.assert_called_once()
        call_args = mock_dynamodb_table.update_item.call_args

        # Verify update sets status to RUNNING and removes pause metadata
        assert call_args[1]["Key"]["executionId"] == "exec-456"
        assert call_args[1]["Key"]["planId"] == "plan-123"
        assert (
            call_args[1]["ExpressionAttributeValues"][":status"] == "RUNNING"
        )
        assert "REMOVE taskToken, pausedBeforeWave" in call_args[1][
            "UpdateExpression"
        ]

    def test_resume_wave_handles_decimal_wave_number(
        self,
        mock_env_vars,
        mock_lambda_client,
        mock_dynamodb_table,
        sample_state,
    ):
        """Test resume_wave() handles Decimal wave number from DynamoDB"""
        from decimal import Decimal

        from index import resume_wave

        # DynamoDB returns Decimal for numbers
        sample_state["paused_before_wave"] = Decimal("2")

        mock_response = {
            "StatusCode": 200,
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {"job_id": "drsjob-789", "wave_completed": False}
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        event = {"application": sample_state}

        with patch("boto3.client", return_value=mock_lambda_client):
            with patch(
                "index.get_execution_history_table",
                return_value=mock_dynamodb_table,
            ):
                result = resume_wave(event)

        # Verify wave number was converted to int
        call_args = mock_lambda_client.invoke.call_args
        payload = json.loads(call_args[1]["Payload"])
        assert payload["wave_number"] == 2
        assert isinstance(payload["wave_number"], int)


class TestInvocationErrorHandling:
    """Test error handling for invocation failures (Task 4.15)"""

    def test_begin_wave_plan_handles_lambda_invocation_error(
        self,
        mock_env_vars,
        mock_lambda_client,
        mock_dynamodb_table,
        sample_plan,
    ):
        """Test error handling when Lambda invocation fails"""
        from index import begin_wave_plan

        # Setup mock to raise exception
        mock_lambda_client.invoke.side_effect = Exception(
            "Lambda invocation failed"
        )

        event = {
            "plan": sample_plan,
            "execution": "exec-456",
            "isDrill": True,
        }

        with patch("boto3.client", return_value=mock_lambda_client):
            with patch(
                "index.get_execution_history_table",
                return_value=mock_dynamodb_table,
            ):
                result = begin_wave_plan(event)

        # Verify error state
        assert result["wave_completed"] is True
        assert result["status"] == "failed"
        assert "error" in result
        assert "Lambda invocation failed" in result["error"]

    def test_begin_wave_plan_handles_function_error_response(
        self,
        mock_env_vars,
        mock_lambda_client,
        mock_dynamodb_table,
        sample_plan,
    ):
        """Test error handling when handler returns FunctionError"""
        from index import begin_wave_plan

        # Setup mock response with FunctionError
        mock_response = {
            "StatusCode": 200,
            "FunctionError": "Unhandled",
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {"errorMessage": "Handler failed"}
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        event = {
            "plan": sample_plan,
            "execution": "exec-456",
            "isDrill": True,
        }

        with patch("boto3.client", return_value=mock_lambda_client):
            with patch(
                "index.get_execution_history_table",
                return_value=mock_dynamodb_table,
            ):
                result = begin_wave_plan(event)

        # Verify error state
        assert result["wave_completed"] is True
        assert result["status"] == "failed"
        assert "error" in result

    def test_poll_wave_status_handles_lambda_invocation_error(
        self, mock_env_vars, mock_lambda_client, sample_state
    ):
        """Test error handling when poll_wave_status invocation fails"""
        from index import poll_wave_status

        # Setup mock to raise exception
        mock_lambda_client.invoke.side_effect = Exception(
            "Query handler timeout"
        )

        event = {"application": sample_state}

        with patch("boto3.client", return_value=mock_lambda_client):
            result = poll_wave_status(event)

        # Verify error state
        assert result["wave_completed"] is True
        assert result["status"] == "failed"
        assert "error" in result
        assert "Query handler timeout" in result["error"]

    def test_poll_wave_status_handles_function_error_response(
        self, mock_env_vars, mock_lambda_client, sample_state
    ):
        """Test error handling when query-handler returns FunctionError"""
        from index import poll_wave_status

        # Setup mock response with FunctionError
        mock_response = {
            "StatusCode": 200,
            "FunctionError": "Unhandled",
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {"errorMessage": "DRS API error"}
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        event = {"application": sample_state}

        with patch("boto3.client", return_value=mock_lambda_client):
            result = poll_wave_status(event)

        # Verify error state
        assert result["wave_completed"] is True
        assert result["status"] == "failed"
        assert "error" in result

    def test_resume_wave_handles_lambda_invocation_error(
        self,
        mock_env_vars,
        mock_lambda_client,
        mock_dynamodb_table,
        sample_state,
    ):
        """Test error handling when resume_wave invocation fails"""
        from index import resume_wave

        sample_state["paused_before_wave"] = 1

        # Setup mock to raise exception
        mock_lambda_client.invoke.side_effect = Exception(
            "Execution handler unavailable"
        )

        event = {"application": sample_state}

        with patch("boto3.client", return_value=mock_lambda_client):
            with patch(
                "index.get_execution_history_table",
                return_value=mock_dynamodb_table,
            ):
                result = resume_wave(event)

        # Verify error state
        assert result["wave_completed"] is True
        assert result["status"] == "failed"
        assert "error" in result
        assert "Execution handler unavailable" in result["error"]

    def test_resume_wave_handles_function_error_response(
        self,
        mock_env_vars,
        mock_lambda_client,
        mock_dynamodb_table,
        sample_state,
    ):
        """Test error handling when execution-handler returns FunctionError"""
        from index import resume_wave

        sample_state["paused_before_wave"] = 1

        # Setup mock response with FunctionError
        mock_response = {
            "StatusCode": 200,
            "FunctionError": "Unhandled",
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {"errorMessage": "Protection Group not found"}
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        event = {"application": sample_state}

        with patch("boto3.client", return_value=mock_lambda_client):
            with patch(
                "index.get_execution_history_table",
                return_value=mock_dynamodb_table,
            ):
                result = resume_wave(event)

        # Verify error state
        assert result["wave_completed"] is True
        assert result["status"] == "failed"
        assert "error" in result


class TestInvocationPayloadStructure:
    """Test payload structure for Lambda invocations"""

    def test_begin_wave_plan_payload_contains_all_required_fields(
        self,
        mock_env_vars,
        mock_lambda_client,
        mock_dynamodb_table,
        sample_plan,
    ):
        """Test that begin_wave_plan sends complete state in payload"""
        from index import begin_wave_plan

        mock_response = {
            "StatusCode": 200,
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {"job_id": "drsjob-123", "wave_completed": False}
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        event = {
            "plan": sample_plan,
            "execution": "exec-456",
            "isDrill": False,
            "accountContext": {
                "accountId": "987654321098",
                "assumeRoleName": "CrossAccountRole",
                "isCurrentAccount": False,
            },
        }

        with patch("boto3.client", return_value=mock_lambda_client):
            with patch(
                "index.get_execution_history_table",
                return_value=mock_dynamodb_table,
            ):
                begin_wave_plan(event)

        # Verify payload structure
        call_args = mock_lambda_client.invoke.call_args
        payload = json.loads(call_args[1]["Payload"])

        # Verify required fields in state
        state = payload["state"]
        assert "plan_id" in state
        assert "execution_id" in state
        assert "is_drill" in state
        assert "waves" in state
        assert "total_waves" in state
        assert "wave_results" in state
        assert "accountContext" in state

        # Verify account context preserved
        assert state["accountContext"]["accountId"] == "987654321098"
        assert (
            state["accountContext"]["assumeRoleName"] == "CrossAccountRole"
        )

    def test_poll_wave_status_payload_preserves_state(
        self, mock_env_vars, mock_lambda_client, sample_state
    ):
        """Test that poll_wave_status preserves all state fields"""
        from index import poll_wave_status

        # Add additional state fields
        sample_state["job_id"] = "drsjob-existing"
        sample_state["region"] = "us-east-1"
        sample_state["server_ids"] = ["s-001", "s-002"]
        sample_state["current_wave_total_wait_time"] = 60

        mock_response = {
            "StatusCode": 200,
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {"wave_completed": False, "status": "running"}
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        event = {"application": sample_state}

        with patch("boto3.client", return_value=mock_lambda_client):
            poll_wave_status(event)

        # Verify all state fields preserved in payload
        call_args = mock_lambda_client.invoke.call_args
        payload = json.loads(call_args[1]["Payload"])
        state = payload["state"]

        assert state["job_id"] == "drsjob-existing"
        assert state["region"] == "us-east-1"
        assert state["server_ids"] == ["s-001", "s-002"]
        assert state["current_wave_total_wait_time"] == 60

    def test_resume_wave_payload_includes_paused_wave_number(
        self,
        mock_env_vars,
        mock_lambda_client,
        mock_dynamodb_table,
        sample_state,
    ):
        """Test that resume_wave sends correct wave number"""
        from index import resume_wave

        sample_state["paused_before_wave"] = 2
        sample_state["waves"] = [
            {"waveNumber": 0, "protectionGroupId": "pg-1"},
            {"waveNumber": 1, "protectionGroupId": "pg-2"},
            {"waveNumber": 2, "protectionGroupId": "pg-3"},
        ]

        mock_response = {
            "StatusCode": 200,
            "Payload": MagicMock(
                read=lambda: json.dumps(
                    {"job_id": "drsjob-789", "wave_completed": False}
                ).encode()
            ),
        }
        mock_lambda_client.invoke.return_value = mock_response

        event = {"application": sample_state}

        with patch("boto3.client", return_value=mock_lambda_client):
            with patch(
                "index.get_execution_history_table",
                return_value=mock_dynamodb_table,
            ):
                resume_wave(event)

        # Verify wave_number matches paused_before_wave
        call_args = mock_lambda_client.invoke.call_args
        payload = json.loads(call_args[1]["Payload"])
        assert payload["wave_number"] == 2
