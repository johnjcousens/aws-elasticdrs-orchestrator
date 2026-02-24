"""
Unit tests for execution-handler recovery instance sync integration.

Tests wave completion sync in update_wave_completion_status() and
terminate instances cache cleanup in terminate_recovery_instances().

Test Coverage:
- Wave completion triggers recovery instance sync
- Sync errors don't block wave completion
- Terminate instances cleans up cache records
- Cache cleanup errors don't block termination
"""

import json
import os
import sys
import time
from contextlib import contextmanager
from unittest.mock import MagicMock, Mock, patch, call

import pytest
from botocore.exceptions import ClientError


lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
execution_handler_dir = os.path.join(lambda_dir, "execution-handler")


@contextmanager
def setup_eh_test_environment():
    """Context manager to set up test environment for execution-handler tests."""
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    if "index" in sys.modules:
        del sys.modules["index"]

    sys.path.insert(0, execution_handler_dir)
    sys.path.insert(0, lambda_dir)

    with patch.dict(
        os.environ,
        {
            "EXECUTION_HISTORY_TABLE": "test-execution-history",
            "PROTECTION_GROUPS_TABLE": "test-protection-groups",
            "RECOVERY_PLANS_TABLE": "test-recovery-plans",
            "TARGET_ACCOUNTS_TABLE": "test-target-accounts",
            "RECOVERY_INSTANCES_TABLE": "test-recovery-instances",
        },
    ):
        sys.modules["shared"] = Mock()
        sys.modules["shared.account_utils"] = Mock()
        sys.modules["shared.config_merge"] = Mock()
        sys.modules["shared.conflict_detection"] = Mock()
        sys.modules["shared.cross_account"] = Mock()
        sys.modules["shared.drs_limits"] = Mock()
        sys.modules["shared.drs_utils"] = Mock()
        sys.modules["shared.execution_utils"] = Mock()
        sys.modules["shared.iam_utils"] = Mock()
        sys.modules["shared.recovery_instance_sync"] = Mock()

        mock_response_utils = Mock()

        def mock_response(status_code, body, headers=None):
            return {
                "statusCode": status_code,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(body, default=str),
            }

        def mock_error_response(code, message, details=None):
            result = {"error": code, "message": message}
            if details:
                result["details"] = details
            return result

        mock_response_utils.response = mock_response
        mock_response_utils.error_response = mock_error_response
        mock_response_utils.DecimalEncoder = json.JSONEncoder
        mock_response_utils.ERROR_INVALID_OPERATION = "INVALID_OPERATION"
        mock_response_utils.ERROR_MISSING_PARAMETER = "MISSING_PARAMETER"
        mock_response_utils.ERROR_INVALID_PARAMETER = "INVALID_PARAMETER"
        mock_response_utils.ERROR_NOT_FOUND = "NOT_FOUND"
        mock_response_utils.ERROR_ALREADY_EXISTS = "ALREADY_EXISTS"
        mock_response_utils.ERROR_INVALID_STATE = "INVALID_STATE"
        mock_response_utils.ERROR_DRS_ERROR = "DRS_ERROR"
        mock_response_utils.ERROR_STS_ERROR = "STS_ERROR"
        mock_response_utils.ERROR_INTERNAL_ERROR = "INTERNAL_ERROR"
        sys.modules["shared.response_utils"] = mock_response_utils

        try:
            yield
        finally:
            sys.path = original_path
            if "index" in sys.modules:
                del sys.modules["index"]
            if original_index is not None:
                sys.modules["index"] = original_index
            for module_name in list(sys.modules.keys()):
                if module_name.startswith("shared"):
                    del sys.modules[module_name]


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table."""
    return MagicMock()


@pytest.fixture
def eh_handler_module(mock_dynamodb_table):
    """Import execution-handler with mocked dependencies."""
    with setup_eh_test_environment():
        with patch("boto3.resource") as mock_resource, patch("boto3.client"):
            mock_resource.return_value.Table.return_value = mock_dynamodb_table
            import index

            yield index, mock_dynamodb_table



# ============================================================================
# 12.4 - Wave Completion Sync Integration Tests
# ============================================================================


class TestWaveCompletionSync:
    """Test recovery instance sync triggered by wave completion."""

    def test_completed_wave_triggers_sync(self, eh_handler_module):
        """COMPLETED status with server_ids and region triggers recovery instance sync."""
        index_module, mock_table = eh_handler_module

        mock_sync = sys.modules["shared.recovery_instance_sync"].sync_recovery_instances_for_account
        mock_sync.return_value = {"instancesUpdated": 3, "errors": []}

        # Mock get_current_account_id
        sys.modules["shared.cross_account"].get_current_account_id.return_value = "123456789012"

        wave_data = {
            "wave_number": 1,
            "server_ids": ["s-abc123", "s-def456"],
            "region": "us-east-2",
            "account_context": {"accountId": "123456789012"},
        }

        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="COMPLETED",
            wave_data=wave_data,
        )

        assert result["statusCode"] == 200
        mock_sync.assert_called_once_with(
            "123456789012", "us-east-2", {"accountId": "123456789012"}
        )

    def test_completed_wave_without_server_ids_skips_sync(self, eh_handler_module):
        """COMPLETED status without server_ids skips sync."""
        index_module, mock_table = eh_handler_module

        mock_sync = sys.modules["shared.recovery_instance_sync"].sync_recovery_instances_for_account

        wave_data = {
            "wave_number": 1,
            "server_ids": [],
            "region": "us-east-2",
        }

        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="COMPLETED",
            wave_data=wave_data,
        )

        assert result["statusCode"] == 200
        mock_sync.assert_not_called()

    def test_completed_wave_without_region_skips_sync(self, eh_handler_module):
        """COMPLETED status without region skips sync."""
        index_module, mock_table = eh_handler_module

        mock_sync = sys.modules["shared.recovery_instance_sync"].sync_recovery_instances_for_account

        wave_data = {
            "wave_number": 1,
            "server_ids": ["s-abc123"],
            "region": None,
        }

        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="COMPLETED",
            wave_data=wave_data,
        )

        assert result["statusCode"] == 200
        mock_sync.assert_not_called()

    def test_sync_error_does_not_block_wave_completion(self, eh_handler_module):
        """Sync failure should NOT prevent wave completion from succeeding."""
        index_module, mock_table = eh_handler_module

        mock_sync = sys.modules["shared.recovery_instance_sync"].sync_recovery_instances_for_account
        mock_sync.side_effect = Exception("DRS API timeout")

        sys.modules["shared.cross_account"].get_current_account_id.return_value = "123456789012"

        wave_data = {
            "wave_number": 1,
            "server_ids": ["s-abc123"],
            "region": "us-east-2",
            "account_context": {"accountId": "123456789012"},
        }

        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="COMPLETED",
            wave_data=wave_data,
        )

        # Wave completion should still succeed
        assert result["statusCode"] == 200
        assert "COMPLETED" in result["message"]

    def test_non_completed_status_does_not_trigger_sync(self, eh_handler_module):
        """FAILED, CANCELLED, PAUSED statuses should NOT trigger sync."""
        index_module, mock_table = eh_handler_module

        mock_sync = sys.modules["shared.recovery_instance_sync"].sync_recovery_instances_for_account

        for status in ["FAILED", "CANCELLED", "PAUSED"]:
            mock_sync.reset_mock()

            wave_data = {
                "wave_number": 1,
                "server_ids": ["s-abc123"],
                "region": "us-east-2",
            }

            result = index_module.update_wave_completion_status(
                execution_id="exec-123",
                plan_id="plan-456",
                status=status,
                wave_data=wave_data,
            )

            assert result["statusCode"] == 200
            mock_sync.assert_not_called()

    def test_completed_without_wave_data_skips_sync(self, eh_handler_module):
        """COMPLETED status without wave_data skips sync."""
        index_module, mock_table = eh_handler_module

        mock_sync = sys.modules["shared.recovery_instance_sync"].sync_recovery_instances_for_account

        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="COMPLETED",
            wave_data=None,
        )

        assert result["statusCode"] == 200
        mock_sync.assert_not_called()

    def test_sync_uses_current_account_when_no_context(self, eh_handler_module):
        """When account_context is missing, sync uses current account ID."""
        index_module, mock_table = eh_handler_module

        mock_sync = sys.modules["shared.recovery_instance_sync"].sync_recovery_instances_for_account
        mock_sync.return_value = {"instancesUpdated": 1, "errors": []}

        sys.modules["shared.cross_account"].get_current_account_id.return_value = "999888777666"

        wave_data = {
            "wave_number": 1,
            "server_ids": ["s-abc123"],
            "region": "us-east-2",
            "account_context": None,
        }

        result = index_module.update_wave_completion_status(
            execution_id="exec-123",
            plan_id="plan-456",
            status="COMPLETED",
            wave_data=wave_data,
        )

        assert result["statusCode"] == 200
        mock_sync.assert_called_once_with("999888777666", "us-east-2", None)



# ============================================================================
# 12.6 - Terminate Instances Cache Operations Tests
# ============================================================================


class TestTerminateInstancesCacheCleanup:
    """Test cache cleanup in terminate_recovery_instances()."""

    def _build_execution_with_wave(self, execution_id: str = "exec-123", plan_id: str = "plan-456"):
        """Helper to build a mock execution record with wave data."""
        return {
            "executionId": execution_id,
            "planId": plan_id,
            "waves": [
                {
                    "waveNumber": 0,
                    "jobId": "drsjob-001",
                    "region": "us-east-2",
                    "status": "COMPLETED",
                    "serverStatuses": [
                        {"sourceServerId": "s-abc123"},
                        {"sourceServerId": "s-def456"},
                    ],
                }
            ],
        }

    def test_cache_cleanup_after_successful_termination(self, eh_handler_module):
        """Cache records deleted after successful DRS termination."""
        index_module, mock_table = eh_handler_module

        execution = self._build_execution_with_wave()

        # Mock execution history query
        mock_table.query.return_value = {"Items": [execution]}

        # Mock recovery plans table
        mock_plans_table = MagicMock()
        mock_plans_table.get_item.return_value = {"Item": {"planId": "plan-456"}}

        # Mock DRS client
        mock_drs = MagicMock()
        mock_drs.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "drsjob-001",
                    "participatingServers": [
                        {"sourceServerID": "s-abc123", "recoveryInstanceID": "ri-001"},
                        {"sourceServerID": "s-def456", "recoveryInstanceID": "ri-002"},
                    ],
                }
            ]
        }
        mock_drs.describe_recovery_instances.side_effect = [
            {"items": [{"ec2InstanceID": "i-001", "recoveryInstanceID": "ri-001"}]},
            {"items": [{"ec2InstanceID": "i-002", "recoveryInstanceID": "ri-002"}]},
        ]
        mock_drs.terminate_recovery_instances.return_value = {
            "job": {"jobID": "drsjob-term-001", "type": "TERMINATE", "status": "PENDING"}
        }

        # Mock recovery instances cache table
        mock_cache_table = MagicMock()
        mock_batch_writer = MagicMock()
        mock_cache_table.batch_writer.return_value.__enter__ = Mock(return_value=mock_batch_writer)
        mock_cache_table.batch_writer.return_value.__exit__ = Mock(return_value=False)

        with patch.object(index_module, "recovery_plans_table", mock_plans_table), \
             patch.object(index_module, "determine_target_account_context", return_value=None), \
             patch.object(index_module, "create_drs_client", return_value=mock_drs), \
             patch.object(index_module, "get_recovery_instances_table", return_value=mock_cache_table):

            # Set execution_history_table on the module
            index_module.execution_history_table = mock_table

            result = index_module.terminate_recovery_instances("exec-123")

            assert result["statusCode"] == 200

            # Verify cache cleanup was called
            mock_cache_table.batch_writer.assert_called_once()
            # Verify delete_item was called for each source server
            delete_calls = mock_batch_writer.delete_item.call_args_list
            deleted_keys = {c[1]["Key"]["sourceServerId"] for c in delete_calls}
            assert "s-abc123" in deleted_keys
            assert "s-def456" in deleted_keys

    def test_cache_cleanup_error_does_not_block_termination(self, eh_handler_module):
        """Cache cleanup failure should NOT prevent termination from succeeding."""
        index_module, mock_table = eh_handler_module

        execution = self._build_execution_with_wave()
        mock_table.query.return_value = {"Items": [execution]}

        mock_plans_table = MagicMock()
        mock_plans_table.get_item.return_value = {"Item": {"planId": "plan-456"}}

        mock_drs = MagicMock()
        mock_drs.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "drsjob-001",
                    "participatingServers": [
                        {"sourceServerID": "s-abc123", "recoveryInstanceID": "ri-001"},
                    ],
                }
            ]
        }
        mock_drs.describe_recovery_instances.return_value = {
            "items": [{"ec2InstanceID": "i-001", "recoveryInstanceID": "ri-001"}]
        }
        mock_drs.terminate_recovery_instances.return_value = {
            "job": {"jobID": "drsjob-term-001", "type": "TERMINATE", "status": "PENDING"}
        }

        # Cache table raises error
        mock_cache_table = MagicMock()
        mock_cache_table.batch_writer.side_effect = Exception("DynamoDB error")

        with patch.object(index_module, "recovery_plans_table", mock_plans_table), \
             patch.object(index_module, "determine_target_account_context", return_value=None), \
             patch.object(index_module, "create_drs_client", return_value=mock_drs), \
             patch.object(index_module, "get_recovery_instances_table", return_value=mock_cache_table):

            index_module.execution_history_table = mock_table

            result = index_module.terminate_recovery_instances("exec-123")

            # Termination should still succeed
            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["totalTerminated"] == 1

    def test_no_cache_table_skips_cleanup(self, eh_handler_module):
        """When cache table is not configured, cleanup is skipped gracefully."""
        index_module, mock_table = eh_handler_module

        execution = self._build_execution_with_wave()
        mock_table.query.return_value = {"Items": [execution]}

        mock_plans_table = MagicMock()
        mock_plans_table.get_item.return_value = {"Item": {"planId": "plan-456"}}

        mock_drs = MagicMock()
        mock_drs.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "drsjob-001",
                    "participatingServers": [
                        {"sourceServerID": "s-abc123", "recoveryInstanceID": "ri-001"},
                    ],
                }
            ]
        }
        mock_drs.describe_recovery_instances.return_value = {
            "items": [{"ec2InstanceID": "i-001", "recoveryInstanceID": "ri-001"}]
        }
        mock_drs.terminate_recovery_instances.return_value = {
            "job": {"jobID": "drsjob-term-001", "type": "TERMINATE", "status": "PENDING"}
        }

        with patch.object(index_module, "recovery_plans_table", mock_plans_table), \
             patch.object(index_module, "determine_target_account_context", return_value=None), \
             patch.object(index_module, "create_drs_client", return_value=mock_drs), \
             patch.object(index_module, "get_recovery_instances_table", return_value=None):

            index_module.execution_history_table = mock_table

            result = index_module.terminate_recovery_instances("exec-123")

            # Should succeed without cache cleanup
            assert result["statusCode"] == 200

    def test_execution_not_found_returns_404(self, eh_handler_module):
        """Non-existent execution returns 404."""
        index_module, mock_table = eh_handler_module

        mock_table.query.return_value = {"Items": []}
        index_module.execution_history_table = mock_table

        result = index_module.terminate_recovery_instances("exec-nonexistent")

        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert body["error"] == "EXECUTION_NOT_FOUND"

    def test_no_instances_to_terminate(self, eh_handler_module):
        """Execution with no recovery instances returns appropriate message."""
        index_module, mock_table = eh_handler_module

        execution = {
            "executionId": "exec-123",
            "planId": "plan-456",
            "waves": [
                {
                    "waveNumber": 0,
                    "status": "PENDING",
                    "region": "us-east-2",
                    "serverStatuses": [],
                }
            ],
        }
        mock_table.query.return_value = {"Items": [execution]}

        mock_plans_table = MagicMock()
        mock_plans_table.get_item.return_value = {"Item": {"planId": "plan-456"}}

        with patch.object(index_module, "recovery_plans_table", mock_plans_table), \
             patch.object(index_module, "determine_target_account_context", return_value=None):

            index_module.execution_history_table = mock_table

            result = index_module.terminate_recovery_instances("exec-123")

            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["noInstancesFound"] is True

    def test_cache_cleanup_skips_unknown_server_ids(self, eh_handler_module):
        """Cache cleanup skips instances with 'unknown' server IDs."""
        index_module, mock_table = eh_handler_module

        execution = {
            "executionId": "exec-123",
            "planId": "plan-456",
            "waves": [
                {
                    "waveNumber": 0,
                    "jobId": "drsjob-001",
                    "region": "us-east-2",
                    "status": "COMPLETED",
                    "serverStatuses": [
                        {"sourceServerId": "s-abc123"},
                    ],
                }
            ],
        }
        mock_table.query.return_value = {"Items": [execution]}

        mock_plans_table = MagicMock()
        mock_plans_table.get_item.return_value = {"Item": {"planId": "plan-456"}}

        mock_drs = MagicMock()
        mock_drs.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "drsjob-001",
                    "participatingServers": [
                        # One server with known ID, one with "unknown"
                        {"sourceServerID": "s-abc123", "recoveryInstanceID": "ri-001"},
                        {"sourceServerID": "unknown", "recoveryInstanceID": "ri-002"},
                    ],
                }
            ]
        }
        mock_drs.describe_recovery_instances.side_effect = [
            {"items": [{"ec2InstanceID": "i-001", "recoveryInstanceID": "ri-001"}]},
            {"items": [{"ec2InstanceID": "i-002", "recoveryInstanceID": "ri-002"}]},
        ]
        mock_drs.terminate_recovery_instances.return_value = {
            "job": {"jobID": "drsjob-term-001", "type": "TERMINATE", "status": "PENDING"}
        }

        mock_cache_table = MagicMock()
        mock_batch_writer = MagicMock()
        mock_cache_table.batch_writer.return_value.__enter__ = Mock(return_value=mock_batch_writer)
        mock_cache_table.batch_writer.return_value.__exit__ = Mock(return_value=False)

        with patch.object(index_module, "recovery_plans_table", mock_plans_table), \
             patch.object(index_module, "determine_target_account_context", return_value=None), \
             patch.object(index_module, "create_drs_client", return_value=mock_drs), \
             patch.object(index_module, "get_recovery_instances_table", return_value=mock_cache_table):

            index_module.execution_history_table = mock_table

            result = index_module.terminate_recovery_instances("exec-123")

            assert result["statusCode"] == 200

            # Only s-abc123 should be deleted, not "unknown"
            delete_calls = mock_batch_writer.delete_item.call_args_list
            deleted_keys = {c[1]["Key"]["sourceServerId"] for c in delete_calls}
            assert "s-abc123" in deleted_keys
            assert "unknown" not in deleted_keys
