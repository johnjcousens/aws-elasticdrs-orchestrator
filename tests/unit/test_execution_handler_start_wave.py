"""
Unit tests for start_wave_recovery in execution-handler.

Tests the start_wave_recovery function that was moved from
orchestration-stepfunctions to execution-handler as part of the
generic orchestration refactoring.

**Validates**: Requirements 1.8-1.13
- Task 1.8: Test function independently with mocked DRS client
- Task 1.9: Test successful wave start
- Task 1.10: Test Protection Group not found
- Task 1.11: Test empty server list (no tags matched)
- Task 1.12: Test DRS API error handling
- Task 1.13: Test cross-account context handling

**Updated for launch-config-preapplication**:
- Tests now mock launch_config_service functions (get_config_status,
  detect_config_drift, apply_launch_configs_to_group, persist_config_status)
- Tests verify fast path (configs pre-applied) and fallback path behavior
"""

import json
import os
import sys
import time
from unittest.mock import MagicMock, Mock, patch

import pytest
from botocore.exceptions import ClientError




# Module-level setup to load execution-handler index
lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
execution_handler_dir = os.path.join(lambda_dir, "execution-handler")


@pytest.fixture(scope="function", autouse=True)
def setup_execution_handler_import():
    """Ensure execution-handler index is imported correctly"""
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
    """Set up environment variables for tests"""
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
    """Mock DynamoDB tables"""
    protection_groups_table = Mock()
    execution_history_table = Mock()
    return {
        "protection_groups_table": protection_groups_table,
        "execution_history_table": execution_history_table,
    }


@pytest.fixture
def mock_drs_client():
    """Mock DRS client"""
    client = Mock()
    client.start_recovery = Mock()
    return client


@pytest.fixture
def sample_state():
    """Sample state object for testing"""
    return {
        "execution_id": "exec-123",
        "plan_id": "plan-456",
        "is_drill": True,
        "waves": [
            {
                "waveNumber": 0,
                "waveName": "Wave 1",
                "protectionGroupId": "pg-789",
                # Note: serverIds not included by default - tests add them as needed
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
    """Sample Protection Group for testing"""
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
    """Mock launch_config_service functions for wave execution tests.
    
    This fixture provides mocks for the launch config service functions
    used in start_wave_recovery for the fast path/fallback path optimization.
    """
    with patch("shared.launch_config_service.get_config_status") as mock_get_status, \
         patch("shared.launch_config_service.detect_config_drift") as mock_detect_drift, \
         patch("shared.launch_config_service.apply_launch_configs_to_group") as mock_apply, \
         patch("shared.launch_config_service.persist_config_status") as mock_persist:
        
        # Default: configs are ready (fast path)
        mock_get_status.return_value = {
            "status": "ready",
            "lastApplied": "2025-02-16T10:30:00Z",
            "appliedBy": "user@example.com",
            "serverConfigs": {},
            "errors": []
        }
        
        # Default: no drift detected
        mock_detect_drift.return_value = {
            "hasDrift": False,
            "driftedServers": [],
            "details": {}
        }
        
        # Default: apply succeeds
        mock_apply.return_value = {
            "status": "ready",
            "appliedServers": 0,
            "failedServers": 0,
            "serverConfigs": {},
            "errors": []
        }
        
        mock_persist.return_value = None
        
        yield {
            "get_config_status": mock_get_status,
            "detect_config_drift": mock_detect_drift,
            "apply_launch_configs_to_group": mock_apply,
            "persist_config_status": mock_persist
        }


class TestStartWaveRecoverySuccessful:
    """Test successful wave start (Task 1.9)"""

    def test_successful_wave_start_with_tag_resolution(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
        mock_launch_config_service,
    ):
        """Test successful wave start with tag-based server resolution"""
        from index import start_wave_recovery

        # Add serverIds to wave for this test
        sample_state["waves"][0]["serverIds"] = ["s-001", "s-002", "s-003"]

        # Mock Protection Group lookup
        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        # Mock execution history table
        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        # Mock query_drs_servers_by_tags to return server objects (not just IDs)
        mock_server_ids = ["s-001", "s-002", "s-003"]
        mock_resolved_servers = [
            {"sourceServerID": "s-001"},
            {"sourceServerID": "s-002"},
            {"sourceServerID": "s-003"},
        ]

        # Mock start_drs_recovery_for_wave response (includes Name tags)
        mock_wave_job_result = {
            "jobId": "drsjob-abc123",
            "servers": [
                {
                    "sourceServerId": "s-001",
                    "serverName": "server-001",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
                {
                    "sourceServerId": "s-002",
                    "serverName": "server-002",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
                {
                    "sourceServerId": "s-003",
                    "serverName": "server-003",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
            ],
        }

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", return_value=mock_drs_client):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=mock_resolved_servers,
                    ):
                        with patch("index.apply_launch_config_before_recovery"):
                            with patch(
                                "index.start_drs_recovery_for_wave",
                                return_value=mock_wave_job_result,
                            ):
                                with patch("time.time", return_value=1234567890):
                                    start_wave_recovery(sample_state, 0)

        # Verify state was updated correctly
        assert sample_state["current_wave_number"] == 0
        assert sample_state["job_id"] == "drsjob-abc123"
        assert sample_state["region"] == "us-east-1"
        assert sample_state["server_ids"] == mock_server_ids
        assert sample_state["wave_completed"] is False
        assert len(sample_state["wave_results"]) == 1

        # Verify wave result structure
        wave_result = sample_state["wave_results"][0]
        assert wave_result["waveNumber"] == 0
        assert wave_result["waveName"] == "Wave 1"
        assert wave_result["status"] == "STARTED"
        assert wave_result["jobId"] == "drsjob-abc123"
        assert wave_result["serverIds"] == mock_server_ids
        assert len(wave_result["serverStatuses"]) == 3

        # Verify server statuses include Name tags
        for i, server_status in enumerate(wave_result["serverStatuses"]):
            assert server_status["sourceServerId"] == mock_server_ids[i]
            assert server_status["serverName"] == f"server-{mock_server_ids[i][-3:]}"

        # Verify DynamoDB update was called
        exec_table.update_item.assert_called_once()

    def test_successful_wave_start_with_explicit_server_ids(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        mock_launch_config_service,
    ):
        """Test successful wave start with explicit server IDs (no tags)"""
        from index import start_wave_recovery

        # Protection Group without serverSelectionTags
        pg_no_tags = {
            "groupId": "pg-789",
            "groupName": "Test PG",
            "region": "us-west-2",
        }

        # Wave with explicit serverIds
        sample_state["waves"][0]["serverIds"] = ["s-100", "s-101"]

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": pg_no_tags}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        # Mock start_drs_recovery_for_wave response
        mock_wave_job_result = {
            "jobId": "drsjob-xyz789",
            "servers": [
                {
                    "sourceServerId": "s-100",
                    "serverName": "server-100",
                    "RecoveryJobId": "drsjob-xyz789",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
                {
                    "sourceServerId": "s-101",
                    "serverName": "server-101",
                    "RecoveryJobId": "drsjob-xyz789",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
            ],
        }

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", return_value=mock_drs_client):
                    with patch(
                        "index.start_drs_recovery_for_wave",
                        return_value=mock_wave_job_result,
                    ):
                        with patch("time.time", return_value=1234567890):
                            start_wave_recovery(sample_state, 0)

        # Verify explicit server IDs were used
        assert sample_state["server_ids"] == ["s-100", "s-101"]
        assert sample_state["region"] == "us-west-2"
        assert sample_state["job_id"] == "drsjob-xyz789"
        assert sample_state["wave_completed"] is False


class TestStartWaveRecoveryProtectionGroupNotFound:
    """Test Protection Group not found (Task 1.10)"""

    def test_protection_group_not_found(self, mock_env_vars, mock_dynamodb_tables, sample_state):
        """Test handling when Protection Group does not exist"""
        from index import start_wave_recovery

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {}  # No Item

        with patch("index.protection_groups_table", pg_table):
            start_wave_recovery(sample_state, 0)

        # Verify error state
        assert sample_state["wave_completed"] is True
        assert sample_state["status"] == "failed"
        assert "not found" in sample_state["error"]
        assert "pg-789" in sample_state["error"]

    def test_wave_missing_protection_group_id(self, mock_env_vars, sample_state):
        """Test handling when wave has no protectionGroupId"""
        from index import start_wave_recovery

        # Remove protectionGroupId from wave
        del sample_state["waves"][0]["protectionGroupId"]

        start_wave_recovery(sample_state, 0)

        # Verify error state
        assert sample_state["wave_completed"] is True
        assert sample_state["status"] == "failed"
        assert "No protectionGroupId" in sample_state["error"]


class TestStartWaveRecoveryEmptyServerList:
    """Test empty server list (Task 1.11)"""

    def test_empty_server_list_no_tags_matched(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        sample_state,
        sample_protection_group,
    ):
        """Test handling when no servers match tags (empty list)"""
        from index import start_wave_recovery

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        # Mock query_drs_servers_by_tags to return empty list
        with patch("index.protection_groups_table", pg_table):
            with patch("index.query_drs_servers_by_tags", return_value=[]):
                start_wave_recovery(sample_state, 0)

        # Verify wave marked complete with error (no servers to launch)
        assert sample_state["wave_completed"] is True
        assert sample_state["status"] == "failed"
        assert "error" in sample_state

    def test_empty_server_list_no_explicit_ids(self, mock_env_vars, mock_dynamodb_tables, sample_state):
        """Test handling when wave has no serverIds and PG has no tags"""
        from index import start_wave_recovery

        # Protection Group without tags
        pg_no_tags = {
            "groupId": "pg-789",
            "groupName": "Test PG",
            "region": "us-east-1",
        }

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": pg_no_tags}

        # Wave without explicit serverIds
        # (serverIds defaults to empty list)

        with patch("index.protection_groups_table", pg_table):
            start_wave_recovery(sample_state, 0)

        # Verify wave marked complete with error (no servers to launch)
        assert sample_state["wave_completed"] is True
        assert sample_state["status"] == "failed"
        assert "error" in sample_state


class TestStartWaveRecoveryDRSAPIError:
    """Test DRS API error handling (Task 1.12)"""

    def test_drs_start_recovery_api_error(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
        mock_launch_config_service,
    ):
        """Test handling when DRS start_recovery API fails"""
        from index import start_wave_recovery

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        # Mock start_drs_recovery_for_wave to return failure
        mock_wave_job_result = {
            "jobId": None,
            "servers": [
                {
                    "sourceServerId": "s-001",
                    "status": "FAILED",
                    "error": "ThrottlingException: Rate exceeded",
                    "launchTime": 1234567890,
                },
                {
                    "sourceServerId": "s-002",
                    "status": "FAILED",
                    "error": "ThrottlingException: Rate exceeded",
                    "launchTime": 1234567890,
                },
            ],
        }

        with patch("index.protection_groups_table", pg_table):
            with patch(
                "index.query_drs_servers_by_tags",
                return_value=[{"sourceServerID": "s-001"}, {"sourceServerID": "s-002"}],
            ):
                with patch("index.apply_launch_config_before_recovery"):
                    with patch(
                        "index.start_drs_recovery_for_wave",
                        return_value=mock_wave_job_result,
                    ):
                        start_wave_recovery(sample_state, 0)

        # Verify error state
        assert sample_state["wave_completed"] is True
        assert sample_state["status"] == "failed"
        assert "error" in sample_state
        assert len(sample_state["error"]) > 0

    def test_drs_describe_source_servers_error(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        sample_state,
        sample_protection_group,
        mock_launch_config_service,
    ):
        """Test handling when query_drs_servers_by_tags fails"""
        from index import start_wave_recovery

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        # Mock query_drs_servers_by_tags to raise exception
        with patch("index.protection_groups_table", pg_table):
            with patch(
                "index.query_drs_servers_by_tags",
                side_effect=ClientError(
                    {
                        "Error": {
                            "Code": "AccessDeniedException",
                            "Message": "Not authorized",
                        }
                    },
                    "DescribeSourceServers",
                ),
            ):
                start_wave_recovery(sample_state, 0)

        # Verify error state
        assert sample_state["wave_completed"] is True
        assert sample_state["status"] == "failed"
        assert "error" in sample_state

    def test_dynamodb_update_error_non_fatal(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
        mock_launch_config_service,
    ):
        """Test that DynamoDB update errors don't fail wave start"""
        from index import start_wave_recovery

        # Add explicit serverIds to wave
        sample_state["waves"][0]["serverIds"] = ["s-001"]

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.side_effect = ClientError(
            {"Error": {"Code": "ProvisionedThroughputExceededException"}},
            "UpdateItem",
        )

        # Mock start_drs_recovery_for_wave response
        mock_wave_job_result = {
            "jobId": "drsjob-abc123",
            "servers": [
                {
                    "sourceServerId": "s-001",
                    "serverName": "server-001",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
            ],
        }

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", return_value=mock_drs_client):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=[{"sourceServerID": "s-001"}],
                    ):
                        with patch("index.apply_launch_config_before_recovery"):
                            with patch(
                                "index.start_drs_recovery_for_wave",
                                return_value=mock_wave_job_result,
                            ):
                                with patch("time.time", return_value=1234567890):
                                    start_wave_recovery(sample_state, 0)

        # Verify wave started successfully despite DynamoDB error
        assert sample_state["job_id"] == "drsjob-abc123"
        assert sample_state["wave_completed"] is False
        # DynamoDB error is logged but doesn't fail the wave


class TestStartWaveRecoveryCrossAccountContext:
    """Test cross-account context handling (Task 1.13)"""

    def test_cross_account_context_passed_to_drs_client(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
        mock_launch_config_service,
    ):
        """Test that cross-account context is passed to DRS client"""
        from index import start_wave_recovery

        # Add serverIds to wave for this test
        sample_state["waves"][0]["serverIds"] = ["s-001"]

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_drs_client.start_recovery.return_value = {"job": {"jobID": "drsjob-abc123"}}

        mock_create_drs_client = Mock(return_value=mock_drs_client)

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", mock_create_drs_client):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=[{"sourceServerID": "s-001"}],
                    ):
                        with patch("index.apply_launch_config_before_recovery"):
                            with patch("time.time", return_value=1234567890):
                                start_wave_recovery(sample_state, 0)

        # Verify create_drs_client was called with account context
        mock_create_drs_client.assert_called_once()
        call_args = mock_create_drs_client.call_args
        assert call_args[0][0] == "us-east-1"  # region
        account_context = call_args[0][1]
        assert account_context["accountId"] == "123456789012"
        assert account_context["assumeRoleName"] == "DRSRole"
        assert account_context["isCurrentAccount"] is False

    def test_cross_account_context_snake_case_format(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_protection_group,
        mock_launch_config_service,
    ):
        """Test handling of snake_case account_context (resume format)"""
        from index import start_wave_recovery

        # State with snake_case account_context (from resume)
        state_snake_case = {
            "execution_id": "exec-123",
            "plan_id": "plan-456",
            "is_drill": True,
            "waves": [
                {
                    "waveNumber": 0,
                    "waveName": "Wave 1",
                    "protectionGroupId": "pg-789",
                    "serverIds": ["s-001"],  # Add serverIds for this test
                }
            ],
            "wave_results": [],
            "account_context": {
                "accountId": "987654321098",
                "assumeRoleName": "CrossAccountRole",
                "isCurrentAccount": False,
            },
        }

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_drs_client.start_recovery.return_value = {"job": {"jobID": "drsjob-abc123"}}

        mock_create_drs_client = Mock(return_value=mock_drs_client)

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", mock_create_drs_client):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=[{"sourceServerID": "s-001"}],
                    ):
                        with patch("index.apply_launch_config_before_recovery"):
                            with patch("time.time", return_value=1234567890):
                                start_wave_recovery(state_snake_case, 0)

        # Verify snake_case context was used
        call_args = mock_create_drs_client.call_args
        account_context = call_args[0][1]
        assert account_context["accountId"] == "987654321098"
        assert account_context["assumeRoleName"] == "CrossAccountRole"

    def test_current_account_context(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
        mock_launch_config_service,
    ):
        """Test handling when using current account (no role assumption)"""
        from index import start_wave_recovery

        # Add explicit serverIds to wave
        sample_state["waves"][0]["serverIds"] = ["s-001"]

        # State with current account context
        sample_state["accountContext"] = {
            "accountId": "123456789012",
            "isCurrentAccount": True,
        }

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_drs_client.start_recovery.return_value = {"job": {"jobID": "drsjob-abc123"}}

        mock_create_drs_client = Mock(return_value=mock_drs_client)

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", mock_create_drs_client):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=[{"sourceServerID": "s-001"}],
                    ):
                        with patch("index.apply_launch_config_before_recovery"):
                            with patch("time.time", return_value=1234567890):
                                start_wave_recovery(sample_state, 0)

        # Verify current account context was passed
        call_args = mock_create_drs_client.call_args
        account_context = call_args[0][1]
        assert account_context["isCurrentAccount"] is True
        assert "assumeRoleName" not in account_context


class TestStartWaveRecoveryLaunchConfig:
    """Test launch configuration application"""

    def test_launch_config_applied_when_present(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
        mock_launch_config_service,
    ):
        """Test that launch config is applied when present in PG and status not ready"""
        from index import start_wave_recovery

        # Add serverIds to wave for this test (2 servers as expected by test)
        sample_state["waves"][0]["serverIds"] = ["s-001", "s-002"]

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_drs_client.start_recovery.return_value = {"job": {"jobID": "drsjob-abc123"}}

        mock_apply_launch_config = Mock()

        # Override fixture to return not_configured status (triggers fallback path)
        mock_launch_config_service["get_config_status"].return_value = {
            "status": "not_configured",
            "lastApplied": None,
            "appliedBy": None,
            "serverConfigs": {},
            "errors": []
        }

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", return_value=mock_drs_client):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=[{"sourceServerID": "s-001"}, {"sourceServerID": "s-002"}],
                    ):
                        with patch(
                            "index.apply_launch_config_before_recovery",
                            mock_apply_launch_config,
                        ):
                            with patch("time.time", return_value=1234567890):
                                start_wave_recovery(sample_state, 0)

        # Verify apply_launch_config_before_recovery was called
        mock_apply_launch_config.assert_called_once()
        call_args = mock_apply_launch_config.call_args
        assert call_args[0][0] == mock_drs_client
        assert call_args[0][1] == ["s-001", "s-002"]
        assert call_args[0][2] == sample_protection_group["launchConfig"]
        assert call_args[0][3] == "us-east-1"
        assert call_args[0][4] == sample_protection_group

    def test_launch_config_skipped_when_absent(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        mock_launch_config_service,
    ):
        """Test that launch config is skipped when not in PG"""
        from index import start_wave_recovery

        # Protection Group without launchConfig
        pg_no_config = {
            "groupId": "pg-789",
            "groupName": "Test PG",
            "region": "us-east-1",
        }

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": pg_no_config}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_drs_client.start_recovery.return_value = {"job": {"jobID": "drsjob-abc123"}}

        mock_apply_launch_config = Mock()

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", return_value=mock_drs_client):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=[{"sourceServerID": "s-001"}],
                    ):
                        with patch(
                            "index.apply_launch_config_before_recovery",
                            mock_apply_launch_config,
                        ):
                            with patch("time.time", return_value=1234567890):
                                start_wave_recovery(sample_state, 0)

        # Verify apply_launch_config_before_recovery was NOT called
        mock_apply_launch_config.assert_not_called()


class TestStartWaveRecoveryStateUpdates:
    """Test state object updates"""

    def test_state_modified_in_place(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
    ):
        """Test that state is modified in-place (archive pattern)"""
        from index import start_wave_recovery

        # Add explicit serverIds to wave
        sample_state["waves"][0]["serverIds"] = ["s-001"]

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        # Mock start_drs_recovery_for_wave response
        mock_wave_job_result = {
            "jobId": "drsjob-abc123",
            "servers": [
                {
                    "sourceServerId": "s-001",
                    "serverName": "server-001",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
            ],
        }

        # Store original state reference
        original_state_id = id(sample_state)

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", return_value=mock_drs_client):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=[{"sourceServerID": "s-001"}],
                    ):
                        with patch("index.apply_launch_config_before_recovery"):
                            with patch(
                                "index.start_drs_recovery_for_wave",
                                return_value=mock_wave_job_result,
                            ):
                                with patch("time.time", return_value=1234567890):
                                    result = start_wave_recovery(sample_state, 0)

        # Verify function returns None (modifies in-place)
        assert result is None

        # Verify same state object was modified
        assert id(sample_state) == original_state_id

        # Verify all expected state fields were set
        assert "current_wave_number" in sample_state
        assert "job_id" in sample_state
        assert "region" in sample_state
        assert "server_ids" in sample_state
        assert "wave_completed" in sample_state
        assert "current_wave_total_wait_time" in sample_state

    def test_wave_result_appended_to_list(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
    ):
        """Test that wave result is appended to wave_results list"""
        from index import start_wave_recovery

        # Add existing wave result
        sample_state["wave_results"] = [{"waveNumber": 0, "status": "COMPLETED"}]

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        # Mock start_drs_recovery_for_wave response
        mock_wave_job_result = {
            "jobId": "drsjob-abc123",
            "servers": [
                {
                    "sourceServerId": "s-001",
                    "serverName": "server-001",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
            ],
        }

        # Start wave 1 (second wave)
        sample_state["waves"].append(
            {
                "waveNumber": 1,
                "waveName": "Wave 2",
                "protectionGroupId": "pg-789",
                "serverIds": ["s-001"],  # Add serverIds for this test
            }
        )

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", return_value=mock_drs_client):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=[{"sourceServerID": "s-001"}],
                    ):
                        with patch("index.apply_launch_config_before_recovery"):
                            with patch(
                                "index.start_drs_recovery_for_wave",
                                return_value=mock_wave_job_result,
                            ):
                                with patch("time.time", return_value=1234567890):
                                    start_wave_recovery(sample_state, 1)

        # Verify wave result was appended (not replaced)
        assert len(sample_state["wave_results"]) == 2
        assert sample_state["wave_results"][0]["waveNumber"] == 0
        assert sample_state["wave_results"][1]["waveNumber"] == 1

    def test_server_statuses_initialized_correctly(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
    ):
        """Test that server statuses are initialized with correct structure"""
        from index import start_wave_recovery

        # Add serverIds to wave for this test
        sample_state["waves"][0]["serverIds"] = ["s-001", "s-002"]

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        # Mock start_drs_recovery_for_wave response
        mock_wave_job_result = {
            "jobId": "drsjob-abc123",
            "servers": [
                {
                    "sourceServerId": "s-001",
                    "serverName": "server-001",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
                {
                    "sourceServerId": "s-002",
                    "serverName": "server-002",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
            ],
        }

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", return_value=mock_drs_client):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=[{"sourceServerID": "s-001"}, {"sourceServerID": "s-002"}],
                    ):
                        with patch("index.apply_launch_config_before_recovery"):
                            with patch(
                                "index.start_drs_recovery_for_wave",
                                return_value=mock_wave_job_result,
                            ):
                                with patch("time.time", return_value=1234567890):
                                    start_wave_recovery(sample_state, 0)

        # Verify server statuses structure
        wave_result = sample_state["wave_results"][0]
        server_statuses = wave_result["serverStatuses"]

        assert len(server_statuses) == 2

        for status in server_statuses:
            assert "sourceServerId" in status
            assert "serverName" in status
            assert "hostname" in status
            assert "launchStatus" in status
            assert status["launchStatus"] == "PENDING"
            assert "instanceId" in status
            assert "privateIp" in status
            assert "instanceType" in status
            assert "launchTime" in status


class TestStartWaveRecoveryDuplicateResolutionFix:
    """Test duplicate server resolution fix (Task 0 and 0.1)"""

    def test_wave_execution_uses_wave_server_ids(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
        mock_launch_config_service,
    ):
        """Test that wave execution uses pre-resolved serverIds from recovery plan wave"""
        from index import start_wave_recovery

        # Wave has explicit serverIds from recovery plan
        sample_state["waves"][0]["serverIds"] = ["s-100", "s-101", "s-102"]

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        # Mock start_drs_recovery_for_wave response
        mock_wave_job_result = {
            "jobId": "drsjob-abc123",
            "servers": [
                {
                    "sourceServerId": "s-100",
                    "serverName": "server-100",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
                {
                    "sourceServerId": "s-101",
                    "serverName": "server-101",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
                {
                    "sourceServerId": "s-102",
                    "serverName": "server-102",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
            ],
        }

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", return_value=mock_drs_client):
                    with patch(
                        "index.start_drs_recovery_for_wave",
                        return_value=mock_wave_job_result,
                    ):
                        with patch("time.time", return_value=1234567890):
                            start_wave_recovery(sample_state, 0)

        # Verify wave used pre-resolved serverIds
        assert sample_state["server_ids"] == ["s-100", "s-101", "s-102"]
        assert sample_state["job_id"] == "drsjob-abc123"
        assert sample_state["wave_completed"] is False

    def test_wave_execution_fails_gracefully_without_server_ids(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        sample_state,
        sample_protection_group,
    ):
        """Test that wave execution fails gracefully if wave has no serverIds"""
        from index import start_wave_recovery

        # Wave has NO serverIds (should not happen in practice)
        sample_state["waves"][0]["serverIds"] = []

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        with patch("index.protection_groups_table", pg_table):
            start_wave_recovery(sample_state, 0)

        # Verify wave marked as failed with clear error
        assert sample_state["wave_completed"] is True
        assert sample_state["status"] == "failed"
        assert "no server IDs" in sample_state["error"]

    def test_wave_execution_does_not_call_query_drs_servers_by_tags(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
        mock_launch_config_service,
    ):
        """Test that wave execution does NOT call query_drs_servers_by_tags()"""
        from index import start_wave_recovery

        # Wave has explicit serverIds
        sample_state["waves"][0]["serverIds"] = ["s-200", "s-201"]

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        # Mock start_drs_recovery_for_wave response
        mock_wave_job_result = {
            "jobId": "drsjob-xyz789",
            "servers": [
                {
                    "sourceServerId": "s-200",
                    "serverName": "server-200",
                    "RecoveryJobId": "drsjob-xyz789",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
                {
                    "sourceServerId": "s-201",
                    "serverName": "server-201",
                    "RecoveryJobId": "drsjob-xyz789",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
            ],
        }

        # Mock query_drs_servers_by_tags to track if it's called
        mock_query_drs = Mock()

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", return_value=mock_drs_client):
                    with patch("index.query_drs_servers_by_tags", mock_query_drs):
                        with patch(
                            "index.start_drs_recovery_for_wave",
                            return_value=mock_wave_job_result,
                        ):
                            with patch("time.time", return_value=1234567890):
                                start_wave_recovery(sample_state, 0)

        # CRITICAL: Verify query_drs_servers_by_tags was NOT called
        mock_query_drs.assert_not_called()

        # Verify wave used pre-resolved serverIds
        assert sample_state["server_ids"] == ["s-200", "s-201"]

    def test_wave_execution_logs_correct_server_count(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
        mock_launch_config_service,
        capsys,
    ):
        """Test that wave execution logs the correct server count from pre-resolved list"""
        from index import start_wave_recovery

        # Wave has 5 pre-resolved servers
        sample_state["waves"][0]["serverIds"] = ["s-001", "s-002", "s-003", "s-004", "s-005"]

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        # Mock start_drs_recovery_for_wave response
        mock_wave_job_result = {
            "jobId": "drsjob-abc123",
            "servers": [
                {
                    "sourceServerId": f"s-00{i}",
                    "serverName": f"server-00{i}",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                }
                for i in range(1, 6)
            ],
        }

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", return_value=mock_drs_client):
                    with patch(
                        "index.start_drs_recovery_for_wave",
                        return_value=mock_wave_job_result,
                    ):
                        with patch("time.time", return_value=1234567890):
                            start_wave_recovery(sample_state, 0)

        # Verify log message contains correct server count (using print statements)
        captured = capsys.readouterr()
        assert "5 pre-resolved servers" in captured.out


class TestStartWaveRecoveryDrillVsRecovery:
    """Test drill vs recovery execution type"""

    def test_drill_execution_type(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
    ):
        """Test that isDrill=True is passed for drill executions"""
        from index import start_wave_recovery

        # Add explicit serverIds to wave
        sample_state["waves"][0]["serverIds"] = ["s-001"]

        sample_state["is_drill"] = True

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        # Mock start_drs_recovery_for_wave response
        mock_wave_job_result = {
            "jobId": "drsjob-abc123",
            "servers": [
                {
                    "sourceServerId": "s-001",
                    "serverName": "server-001",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
            ],
        }

        mock_start_drs_recovery = Mock(return_value=mock_wave_job_result)

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", return_value=mock_drs_client):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=[{"sourceServerID": "s-001"}],
                    ):
                        with patch("index.apply_launch_config_before_recovery"):
                            with patch(
                                "index.start_drs_recovery_for_wave",
                                mock_start_drs_recovery,
                            ):
                                with patch("time.time", return_value=1234567890):
                                    start_wave_recovery(sample_state, 0)

        # Verify isDrill=True was passed to start_drs_recovery_for_wave
        call_args = mock_start_drs_recovery.call_args
        assert call_args[1]["is_drill"] is True

    def test_recovery_execution_type(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
    ):
        """Test that isDrill=False is passed for recovery executions"""
        from index import start_wave_recovery

        # Add explicit serverIds to wave
        sample_state["waves"][0]["serverIds"] = ["s-001"]

        sample_state["is_drill"] = False

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        # Mock start_drs_recovery_for_wave response
        mock_wave_job_result = {
            "jobId": "drsjob-abc123",
            "servers": [
                {
                    "sourceServerId": "s-001",
                    "serverName": "server-001",
                    "RecoveryJobId": "drsjob-abc123",
                    "status": "LAUNCHING",
                    "launchTime": 1234567890,
                },
            ],
        }

        mock_start_drs_recovery = Mock(return_value=mock_wave_job_result)

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch("index.create_drs_client", return_value=mock_drs_client):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=[{"sourceServerID": "s-001"}],
                    ):
                        with patch("index.apply_launch_config_before_recovery"):
                            with patch(
                                "index.start_drs_recovery_for_wave",
                                mock_start_drs_recovery,
                            ):
                                with patch("time.time", return_value=1234567890):
                                    start_wave_recovery(sample_state, 0)

        # Verify isDrill=False was passed to start_drs_recovery_for_wave
        call_args = mock_start_drs_recovery.call_args
        assert call_args[1]["is_drill"] is False
