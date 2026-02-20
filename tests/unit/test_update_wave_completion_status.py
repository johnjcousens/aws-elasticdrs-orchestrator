"""
Unit tests for update_wave_completion_status() function.

Tests the wave completion status update functionality that was moved from
query-handler to execution-handler as part of FR4 (query-handler read-only audit).

Test Coverage:
- CANCELLED status updates (sets endTime)
- PAUSED status updates (sets pausedBeforeWave if provided)
- COMPLETED status updates (sets endTime, completedWaves, duration)
- FAILED status updates (sets endTime, error details, failedWaves, duration)
- Error handling (execution not found, DynamoDB errors)
"""

import json
import os
import sys
import time
from contextlib import contextmanager
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from botocore.exceptions import ClientError


# Module-level setup to load execution-handler index
lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
execution_handler_dir = os.path.join(lambda_dir, "execution-handler")


@contextmanager
def setup_test_environment():
    """Context manager to set up test environment for each test"""
    # Save original sys.path and modules
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    # Remove any existing 'index' module
    if "index" in sys.modules:
        del sys.modules["index"]

    # Add execution-handler to front of path
    sys.path.insert(0, execution_handler_dir)
    sys.path.insert(0, lambda_dir)

    # Set up environment variables
    with patch.dict(
        os.environ,
        {
            "EXECUTION_HISTORY_TABLE": "test-execution-history",
            "PROTECTION_GROUPS_TABLE": "test-protection-groups",
            "RECOVERY_PLANS_TABLE": "test-recovery-plans",
            "TARGET_ACCOUNTS_TABLE": "test-target-accounts",
        },
    ):
        # Mock shared modules
        sys.modules["shared"] = Mock()
        sys.modules["shared.account_utils"] = Mock()
        sys.modules["shared.config_merge"] = Mock()
        sys.modules["shared.conflict_detection"] = Mock()
        sys.modules["shared.cross_account"] = Mock()
        sys.modules["shared.drs_limits"] = Mock()
        sys.modules["shared.drs_utils"] = Mock()
        sys.modules["shared.execution_utils"] = Mock()
        sys.modules["shared.iam_utils"] = Mock()

        mock_response_utils = Mock()

        def mock_response(status_code, body, headers=None):
            return {
                "statusCode": status_code,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(body),
            }

        mock_response_utils.response = mock_response
        mock_response_utils.DecimalEncoder = json.JSONEncoder
        sys.modules["shared.response_utils"] = mock_response_utils

        try:
            yield
        finally:
            # Restore original state
            sys.path = original_path
            if "index" in sys.modules:
                del sys.modules["index"]
            if original_index is not None:
                sys.modules["index"] = original_index

            # Clean up mocked modules
            for module_name in list(sys.modules.keys()):
                if module_name.startswith("shared"):
                    del sys.modules[module_name]


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table."""
    mock_table = MagicMock()
    return mock_table


@pytest.fixture
def execution_handler_module(mock_dynamodb_table):
    """Import execution handler with mocked dependencies."""
    with setup_test_environment():
        # Mock boto3 before importing
        with patch("boto3.resource") as mock_resource, patch("boto3.client"):
            # Mock the table resource
            mock_resource.return_value.Table.return_value = mock_dynamodb_table

            # Import the module
            import index

            yield index, mock_dynamodb_table


class TestUpdateWaveCompletionStatusCancelled:
    """Test CANCELLED status updates."""

    def test_cancelled_status_basic(self, execution_handler_module):
        """Test CANCELLED status sets endTime and updates status."""
        index_module, mock_table = execution_handler_module

        # Execute
        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="CANCELLED",
        )

        # Verify response
        assert result["statusCode"] == 200
        assert "CANCELLED" in result["message"]

        # Verify DynamoDB update
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args

        # Verify Key
        assert call_args[1]["Key"] == {"executionId": "exec-123", "planId": "plan-456"}

        # Verify UpdateExpression contains status and endTime
        update_expr = call_args[1]["UpdateExpression"]
        assert "#status = :status" in update_expr
        assert "endTime = :end_time" in update_expr
        assert "lastUpdated = :last_updated" in update_expr

        # Verify ExpressionAttributeValues
        attr_values = call_args[1]["ExpressionAttributeValues"]
        assert attr_values[":status"] == "CANCELLED"
        assert isinstance(attr_values[":end_time"], int)
        assert isinstance(attr_values[":last_updated"], int)

    def test_cancelled_status_lowercase_input(self, execution_handler_module):
        """Test CANCELLED status normalizes lowercase input."""
        index_module, mock_table = execution_handler_module

        # Execute with lowercase
        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="cancelled",
        )

        # Verify status normalized to uppercase
        assert result["statusCode"] == 200
        call_args = mock_table.update_item.call_args
        assert call_args[1]["ExpressionAttributeValues"][":status"] == "CANCELLED"


class TestUpdateWaveCompletionStatusPaused:
    """Test PAUSED status updates."""

    def test_paused_status_without_wave_data(self, execution_handler_module):
        """Test PAUSED status without wave_data parameter."""
        index_module, mock_table = execution_handler_module

        # Execute
        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="PAUSED",
        )

        # Verify response
        assert result["statusCode"] == 200
        assert "PAUSED" in result["message"]

        # Verify DynamoDB update
        call_args = mock_table.update_item.call_args
        update_expr = call_args[1]["UpdateExpression"]

        # Should NOT include pausedBeforeWave
        assert "pausedBeforeWave" not in update_expr
        assert "#status = :status" in update_expr

    def test_paused_status_with_wave_data(self, execution_handler_module):
        """Test PAUSED status with paused_before_wave in wave_data."""
        index_module, mock_table = execution_handler_module

        # Execute with wave_data
        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="PAUSED",
            wave_data={"paused_before_wave": 3},
        )

        # Verify response
        assert result["statusCode"] == 200

        # Verify DynamoDB update includes pausedBeforeWave
        call_args = mock_table.update_item.call_args
        update_expr = call_args[1]["UpdateExpression"]
        assert "pausedBeforeWave = :wave" in update_expr

        attr_values = call_args[1]["ExpressionAttributeValues"]
        assert attr_values[":wave"] == 3


class TestUpdateWaveCompletionStatusCompleted:
    """Test COMPLETED status updates."""

    def test_completed_status_basic(self, execution_handler_module):
        """Test COMPLETED status sets endTime."""
        index_module, mock_table = execution_handler_module

        # Execute
        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="COMPLETED",
        )

        # Verify response
        assert result["statusCode"] == 200
        assert "COMPLETED" in result["message"]

        # Verify DynamoDB update
        call_args = mock_table.update_item.call_args
        update_expr = call_args[1]["UpdateExpression"]

        assert "#status = :status" in update_expr
        assert "endTime = :end_time" in update_expr

        attr_values = call_args[1]["ExpressionAttributeValues"]
        assert attr_values[":status"] == "COMPLETED"
        assert isinstance(attr_values[":end_time"], int)

    def test_completed_status_with_completed_waves(self, execution_handler_module):
        """Test COMPLETED status with completed_waves count."""
        index_module, mock_table = execution_handler_module

        # Execute with wave_data
        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="COMPLETED",
            wave_data={"completed_waves": 5},
        )

        # Verify completedWaves included
        call_args = mock_table.update_item.call_args
        update_expr = call_args[1]["UpdateExpression"]
        assert "completedWaves = :completed_waves" in update_expr

        attr_values = call_args[1]["ExpressionAttributeValues"]
        assert attr_values[":completed_waves"] == 5

    def test_completed_status_with_duration(self, execution_handler_module):
        """Test COMPLETED status calculates duration from start_time."""
        index_module, mock_table = execution_handler_module

        # Mock current time
        current_time = int(time.time())
        start_time = current_time - 3600  # 1 hour ago

        # Execute with start_time
        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="COMPLETED",
            wave_data={"start_time": start_time},
        )

        # Verify duration calculated
        call_args = mock_table.update_item.call_args
        update_expr = call_args[1]["UpdateExpression"]
        assert "durationSeconds = :duration" in update_expr

        attr_values = call_args[1]["ExpressionAttributeValues"]
        # Duration should be approximately 3600 seconds (allow 5 second tolerance)
        assert 3595 <= attr_values[":duration"] <= 3605


class TestUpdateWaveCompletionStatusFailed:
    """Test FAILED status updates."""

    def test_failed_status_basic(self, execution_handler_module):
        """Test FAILED status sets endTime."""
        index_module, mock_table = execution_handler_module

        # Execute
        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="FAILED",
        )

        # Verify response
        assert result["statusCode"] == 200
        assert "FAILED" in result["message"]

        # Verify DynamoDB update
        call_args = mock_table.update_item.call_args
        update_expr = call_args[1]["UpdateExpression"]

        assert "#status = :status" in update_expr
        assert "endTime = :end_time" in update_expr

        attr_values = call_args[1]["ExpressionAttributeValues"]
        assert attr_values[":status"] == "FAILED"

    def test_failed_status_with_error_message(self, execution_handler_module):
        """Test FAILED status with error message."""
        index_module, mock_table = execution_handler_module

        # Execute with error
        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="FAILED",
            wave_data={"error": "DRS job failed: timeout"},
        )

        # Verify error message included
        call_args = mock_table.update_item.call_args
        update_expr = call_args[1]["UpdateExpression"]
        assert "errorMessage = :error" in update_expr

        attr_values = call_args[1]["ExpressionAttributeValues"]
        assert attr_values[":error"] == "DRS job failed: timeout"

    def test_failed_status_with_all_fields(self, execution_handler_module):
        """Test FAILED status with all error fields."""
        index_module, mock_table = execution_handler_module

        current_time = int(time.time())
        start_time = current_time - 600  # 10 minutes ago

        # Execute with all error fields
        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="FAILED",
            wave_data={
                "error": "Wave 2 failed: 3 servers failed to launch",
                "error_code": "LAUNCH_FAILED",
                "failed_waves": 1,
                "start_time": start_time,
            },
        )

        # Verify all fields included
        call_args = mock_table.update_item.call_args
        update_expr = call_args[1]["UpdateExpression"]
        assert "errorMessage = :error" in update_expr
        assert "errorCode = :error_code" in update_expr
        assert "failedWaves = :failed_waves" in update_expr
        assert "durationSeconds = :duration" in update_expr

        attr_values = call_args[1]["ExpressionAttributeValues"]
        assert attr_values[":error"] == "Wave 2 failed: 3 servers failed to launch"
        assert attr_values[":error_code"] == "LAUNCH_FAILED"
        assert attr_values[":failed_waves"] == 1
        assert 595 <= attr_values[":duration"] <= 605


class TestUpdateWaveCompletionStatusErrorHandling:
    """Test error handling scenarios."""

    def test_execution_not_found(self, execution_handler_module):
        """Test error when execution doesn't exist in DynamoDB."""
        index_module, mock_table = execution_handler_module

        # Mock ConditionalCheckFailedException
        mock_table.update_item.side_effect = ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException", "Message": "Item not found"}},
            "UpdateItem",
        )

        # Execute
        result = index_module.update_wave_completion_status(
            execution_id="nonexistent-exec",
            plan_id="plan-456",
            status="COMPLETED",
        )

        # Verify 404 response
        assert result["statusCode"] == 404
        assert "not found" in result["error"]
        assert "nonexistent-exec" in result["error"]

    def test_dynamodb_error_propagates(self, execution_handler_module):
        """Test that non-conditional DynamoDB errors are raised."""
        index_module, mock_table = execution_handler_module

        # Mock generic DynamoDB error
        mock_table.update_item.side_effect = ClientError(
            {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "Rate exceeded"}},
            "UpdateItem",
        )

        # Execute and expect exception
        with pytest.raises(ClientError) as exc_info:
            index_module.update_wave_completion_status(
                execution_id="exec-123",
                plan_id="plan-456",
                status="COMPLETED",
            )

        # Verify error code
        assert exc_info.value.response["Error"]["Code"] == "ProvisionedThroughputExceededException"


class TestUpdateWaveCompletionStatusEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_wave_data(self, execution_handler_module):
        """Test with empty wave_data dictionary."""
        index_module, mock_table = execution_handler_module

        # Execute with empty dict
        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="COMPLETED",
            wave_data={},
        )

        # Should succeed without optional fields
        assert result["statusCode"] == 200

    def test_mixed_case_status(self, execution_handler_module):
        """Test status normalization with mixed case."""
        index_module, mock_table = execution_handler_module

        # Execute with mixed case
        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="CoMpLeTeD",
        )

        # Verify normalized to uppercase
        call_args = mock_table.update_item.call_args
        assert call_args[1]["ExpressionAttributeValues"][":status"] == "COMPLETED"

    def test_zero_duration(self, execution_handler_module):
        """Test duration calculation when start_time equals current time."""
        index_module, mock_table = execution_handler_module

        current_time = int(time.time())

        # Execute with start_time = current time
        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="COMPLETED",
            wave_data={"start_time": current_time},
        )

        # Duration should be 0 or very small
        call_args = mock_table.update_item.call_args
        attr_values = call_args[1]["ExpressionAttributeValues"]
        assert 0 <= attr_values[":duration"] <= 2  # Allow 2 second tolerance
