# Copyright Amazon.com and Affiliates. All rights reserved.
# This deliverable is considered Developed Content as defined in the AWS Service Terms.

"""
Unit tests for wave execution error propagation and config check bypass.

Tests the fixes applied to start_wave_recovery in execution-handler:
- Error propagation: actual DRS error messages in state["error"]
- Config check bypass: skip config checks for PGs without launch config
- Timing logs: verify timing markers are emitted
- Large server groups: 25-server PG without config skips checks

**Validates**: Bugfix spec wave-execution-fix Tasks 5.1-5.9
"""

import os
import sys
import time
from unittest.mock import Mock, patch

import pytest


# Module-level setup to load execution-handler index
lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
execution_handler_dir = os.path.join(lambda_dir, "execution-handler")


@pytest.fixture(scope="function", autouse=True)
def setup_execution_handler_import():
    """Ensure execution-handler index is imported correctly."""
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    if "index" in sys.modules:
        del sys.modules["index"]

    sys.path.insert(0, execution_handler_dir)
    sys.path.insert(0, lambda_dir)

    yield

    sys.path = original_path
    if "index" in sys.modules:
        del sys.modules["index"]
    if original_index is not None:
        sys.modules["index"] = original_index


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for tests."""
    with patch.dict(
        os.environ,
        {
            "EXECUTION_HISTORY_TABLE": "test-execution-table",
            "PROTECTION_GROUPS_TABLE": "test-pg-table",
            "RECOVERY_PLANS_TABLE": "test-plans-table",
            "PROJECT_NAME": "test-project",
            "ENVIRONMENT": "test",
        },
    ):
        yield


@pytest.fixture
def mock_dynamodb_tables():
    """Mock DynamoDB tables."""
    protection_groups_table = Mock()
    execution_history_table = Mock()
    return {
        "protection_groups_table": protection_groups_table,
        "execution_history_table": execution_history_table,
    }


@pytest.fixture
def mock_drs_client():
    """Mock DRS client."""
    client = Mock()
    client.start_recovery = Mock()
    return client


@pytest.fixture
def sample_state():
    """Sample state object for testing."""
    return {
        "execution_id": "exec-123",
        "plan_id": "plan-456",
        "is_drill": True,
        "waves": [
            {
                "waveNumber": 0,
                "waveName": "Wave 1",
                "protectionGroupId": "pg-789",
            }
        ],
        "wave_results": [],
        "accountContext": {
            "accountId": "123456789012",
            "assumeRoleName": "DRSRole",
            "isCurrentAccount": False,
        },
    }


@pytest.fixture
def sample_protection_group():
    """Sample Protection Group for testing."""
    return {
        "groupId": "pg-789",
        "groupName": "Test PG",
        "region": "us-east-1",
        "serverSelectionTags": {"Environment": "prod", "App": "web"},
        "launchConfig": {
            "targetInstanceTypeRightSizing": "NONE",
            "copyPrivateIp": True,
            "copyTags": True,
        },
    }


@pytest.fixture
def mock_launch_config_service():
    """Mock launch_config_service functions for wave execution tests."""
    with patch("shared.launch_config_service.get_config_status") as mock_get_status, \
         patch("shared.launch_config_service.detect_config_drift") as mock_detect_drift, \
         patch("shared.launch_config_service.apply_launch_configs_to_group") as mock_apply, \
         patch("shared.launch_config_service.persist_config_status") as mock_persist:

        mock_get_status.return_value = {
            "status": "ready",
            "lastApplied": "2025-02-16T10:30:00Z",
            "appliedBy": "user@example.com",
            "serverConfigs": {},
            "errors": [],
        }

        mock_detect_drift.return_value = {
            "hasDrift": False,
            "driftedServers": [],
            "details": {},
        }

        mock_apply.return_value = {
            "status": "ready",
            "appliedServers": 0,
            "failedServers": 0,
            "serverConfigs": {},
            "errors": [],
        }

        mock_persist.return_value = None

        yield {
            "get_config_status": mock_get_status,
            "detect_config_drift": mock_detect_drift,
            "apply_launch_configs_to_group": mock_apply,
            "persist_config_status": mock_persist,
        }


def _make_valid_job_result(server_ids):
    """Helper to build a valid start_drs_recovery_for_wave result."""
    return {
        "jobId": "drsjob-abc123",
        "servers": [
            {
                "sourceServerId": sid,
                "serverName": f"server-{sid}",
                "RecoveryJobId": "drsjob-abc123",
                "status": "LAUNCHING",
                "launchTime": 1234567890,
            }
            for sid in server_ids
        ],
    }



class TestErrorPropagation:
    """Tests for error propagation fix in start_wave_recovery (Tasks 5.2, 5.3)."""

    def test_state_error_contains_actual_drs_error_message(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
    ):
        """Task 5.2: When DRS recovery fails, state['error'] contains the actual DRS error."""
        from index import start_wave_recovery

        sample_state["waves"][0]["serverIds"] = ["s-001"]

        pg_no_config = {"groupId": "pg-789", "groupName": "Test PG", "region": "us-east-1"}

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": pg_no_config}

        failed_job_result = {
            "jobId": None,
            "servers": [
                {
                    "sourceServerId": "s-001",
                    "status": "FAILED",
                    "error": "ConflictException: Recovery already in progress",
                    "launchTime": 1234567890,
                }
            ],
        }

        with patch("index.protection_groups_table", pg_table), \
             patch("index.create_drs_client", return_value=mock_drs_client), \
             patch("index.start_drs_recovery_for_wave", return_value=failed_job_result):
            start_wave_recovery(sample_state, 0)

        assert "ConflictException" in sample_state["error"]
        assert sample_state["error"] != "Failed to start DRS recovery"
        assert sample_state["status"] == "failed"
        assert sample_state["wave_completed"] is True

    def test_state_error_fallback_when_no_server_error(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
    ):
        """Task 5.3: When no server error available, state['error'] has a fallback message."""
        from index import start_wave_recovery

        sample_state["waves"][0]["serverIds"] = ["s-001"]

        pg_no_config = {"groupId": "pg-789", "groupName": "Test PG", "region": "us-east-1"}

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": pg_no_config}

        failed_job_result = {"jobId": None, "servers": []}

        with patch("index.protection_groups_table", pg_table), \
             patch("index.create_drs_client", return_value=mock_drs_client), \
             patch("index.start_drs_recovery_for_wave", return_value=failed_job_result):
            start_wave_recovery(sample_state, 0)

        assert sample_state["error"] is not None
        assert len(sample_state["error"]) > 0
        assert sample_state["status"] == "failed"



class TestConfigCheckBypass:
    """Tests for config check bypass logic (Tasks 5.4-5.7)."""

    def test_config_check_skipped_when_no_launch_config(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
    ):
        """Task 5.4: PG with no launchConfig key skips config checks entirely."""
        from index import start_wave_recovery

        sample_state["waves"][0]["serverIds"] = ["s-001"]

        pg_no_config = {"groupId": "pg-789", "groupName": "Test PG", "region": "us-east-1"}

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": pg_no_config}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        job_result = _make_valid_job_result(["s-001"])

        with patch("index.protection_groups_table", pg_table), \
             patch("index.execution_history_table", exec_table), \
             patch("index.create_drs_client", return_value=mock_drs_client), \
             patch("index.start_drs_recovery_for_wave", return_value=job_result), \
             patch("shared.launch_config_service.get_config_status") as mock_get_config_status:
            start_wave_recovery(sample_state, 0)

        mock_get_config_status.assert_not_called()
        assert sample_state["job_id"] == "drsjob-abc123"

    def test_config_check_skipped_when_empty_launch_config(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
    ):
        """Task 5.5: PG with empty launchConfig dict skips config checks."""
        from index import start_wave_recovery

        sample_state["waves"][0]["serverIds"] = ["s-001"]

        pg_empty_config = {
            "groupId": "pg-789",
            "groupName": "Test PG",
            "region": "us-east-1",
            "launchConfig": {},
        }

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": pg_empty_config}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        job_result = _make_valid_job_result(["s-001"])

        with patch("index.protection_groups_table", pg_table), \
             patch("index.execution_history_table", exec_table), \
             patch("index.create_drs_client", return_value=mock_drs_client), \
             patch("index.start_drs_recovery_for_wave", return_value=job_result), \
             patch("shared.launch_config_service.get_config_status") as mock_get_config_status:
            start_wave_recovery(sample_state, 0)

        mock_get_config_status.assert_not_called()
        assert sample_state["job_id"] == "drsjob-abc123"

    def test_config_check_runs_when_infra_config_present(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        mock_launch_config_service,
    ):
        """Task 5.6: PG with infrastructure config triggers config checks."""
        from index import start_wave_recovery

        sample_state["waves"][0]["serverIds"] = ["s-001"]

        pg_with_infra = {
            "groupId": "pg-789",
            "groupName": "Test PG",
            "region": "us-east-1",
            "launchConfig": {"subnetId": "subnet-abc123", "securityGroupIds": ["sg-123"]},
        }

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": pg_with_infra}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_launch_config_service["get_config_status"].return_value = {
            "status": "not_configured",
            "lastApplied": None,
            "appliedBy": None,
            "serverConfigs": {},
            "errors": [],
        }

        job_result = _make_valid_job_result(["s-001"])

        with patch("index.protection_groups_table", pg_table), \
             patch("index.execution_history_table", exec_table), \
             patch("index.create_drs_client", return_value=mock_drs_client), \
             patch("index.apply_launch_config_before_recovery"), \
             patch("index.start_drs_recovery_for_wave", return_value=job_result):
            start_wave_recovery(sample_state, 0)

        mock_launch_config_service["get_config_status"].assert_called()
        assert sample_state["job_id"] == "drsjob-abc123"

    def test_config_check_runs_when_drs_settings_present(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        mock_launch_config_service,
    ):
        """Task 5.7: PG with DRS settings (no infra) still triggers config checks."""
        from index import start_wave_recovery

        sample_state["waves"][0]["serverIds"] = ["s-001"]

        pg_drs_settings = {
            "groupId": "pg-789",
            "groupName": "Test PG",
            "region": "us-east-1",
            "launchConfig": {"copyPrivateIp": True, "copyTags": True},
        }

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": pg_drs_settings}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_launch_config_service["get_config_status"].return_value = {
            "status": "ready",
            "lastApplied": "2025-02-16T10:30:00Z",
            "appliedBy": "user@example.com",
            "serverConfigs": {},
            "errors": [],
        }

        job_result = _make_valid_job_result(["s-001"])

        with patch("index.protection_groups_table", pg_table), \
             patch("index.execution_history_table", exec_table), \
             patch("index.create_drs_client", return_value=mock_drs_client), \
             patch("index.start_drs_recovery_for_wave", return_value=job_result):
            start_wave_recovery(sample_state, 0)

        mock_launch_config_service["get_config_status"].assert_called()



class TestTimingLogs:
    """Tests for timing log emission (Task 5.8)."""

    def test_timing_logs_emitted_for_config_check(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        mock_launch_config_service,
        capsys,
    ):
        """Task 5.8: Timing markers are emitted during config check path."""
        from index import start_wave_recovery

        sample_state["waves"][0]["serverIds"] = ["s-001"]

        pg_with_infra = {
            "groupId": "pg-789",
            "groupName": "Test PG",
            "region": "us-east-1",
            "launchConfig": {"subnetId": "subnet-123"},
        }

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": pg_with_infra}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_launch_config_service["get_config_status"].return_value = {
            "status": "not_configured",
            "lastApplied": None,
            "appliedBy": None,
            "serverConfigs": {},
            "errors": [],
        }

        job_result = _make_valid_job_result(["s-001"])

        with patch("index.protection_groups_table", pg_table), \
             patch("index.execution_history_table", exec_table), \
             patch("index.create_drs_client", return_value=mock_drs_client), \
             patch("index.apply_launch_config_before_recovery"), \
             patch("index.start_drs_recovery_for_wave", return_value=job_result):
            start_wave_recovery(sample_state, 0)

        captured = capsys.readouterr()
        assert "⏱️" in captured.out


class TestLargeServerGroups:
    """Tests for large server group behavior (Task 5.9)."""

    def test_25_servers_no_config_skips_config_check(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
    ):
        """Task 5.9: 25-server PG without config skips config checks entirely."""
        from index import start_wave_recovery

        server_ids = [f"s-{i:017x}" for i in range(25)]
        sample_state["waves"][0]["serverIds"] = server_ids

        pg_no_config = {"groupId": "pg-789", "groupName": "Test PG", "region": "us-east-1"}

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": pg_no_config}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        job_result = _make_valid_job_result(server_ids)

        with patch("index.protection_groups_table", pg_table), \
             patch("index.execution_history_table", exec_table), \
             patch("index.create_drs_client", return_value=mock_drs_client), \
             patch("index.start_drs_recovery_for_wave", return_value=job_result), \
             patch("shared.launch_config_service.get_config_status") as mock_get_config_status:
            start_wave_recovery(sample_state, 0)

        mock_get_config_status.assert_not_called()
        assert sample_state["job_id"] == "drsjob-abc123"
        assert sample_state["wave_completed"] is False
        assert len(sample_state["server_ids"]) == 25
