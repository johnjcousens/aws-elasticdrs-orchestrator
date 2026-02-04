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


class TestStartWaveRecoverySuccessful:
    """Test successful wave start (Task 1.9)"""

    def test_successful_wave_start_with_tag_resolution(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
    ):
        """Test successful wave start with tag-based server resolution"""
        from index import start_wave_recovery

        # Mock Protection Group lookup
        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        # Mock execution history table
        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        # Mock DRS start_recovery response
        mock_drs_client.start_recovery.return_value = {
            "job": {"jobID": "drsjob-abc123"}
        }

        # Mock query_drs_servers_by_tags to return server IDs
        mock_server_ids = ["s-001", "s-002", "s-003"]

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch(
                    "index.create_drs_client", return_value=mock_drs_client
                ):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=mock_server_ids,
                    ):
                        with patch(
                            "index.apply_launch_config_before_recovery"
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

        # Verify DRS start_recovery was called correctly
        mock_drs_client.start_recovery.assert_called_once()
        call_args = mock_drs_client.start_recovery.call_args
        assert call_args[1]["isDrill"] is True
        assert len(call_args[1]["sourceServers"]) == 3

        # Verify DynamoDB update was called
        exec_table.update_item.assert_called_once()


    def test_successful_wave_start_with_explicit_server_ids(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
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

        mock_drs_client.start_recovery.return_value = {
            "job": {"jobID": "drsjob-xyz789"}
        }

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch(
                    "index.create_drs_client", return_value=mock_drs_client
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

    def test_protection_group_not_found(
        self, mock_env_vars, mock_dynamodb_tables, sample_state
    ):
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

    def test_wave_missing_protection_group_id(
        self, mock_env_vars, sample_state
    ):
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

        # Verify wave marked complete without error
        assert sample_state["wave_completed"] is True
        assert "status" not in sample_state or sample_state.get(
            "status"
        ) != "failed"
        assert "error" not in sample_state

    def test_empty_server_list_no_explicit_ids(
        self, mock_env_vars, mock_dynamodb_tables, sample_state
    ):
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

        # Verify wave marked complete without error
        assert sample_state["wave_completed"] is True
        assert "status" not in sample_state or sample_state.get(
            "status"
        ) != "failed"


class TestStartWaveRecoveryDRSAPIError:
    """Test DRS API error handling (Task 1.12)"""

    def test_drs_start_recovery_api_error(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
        mock_drs_client,
        sample_state,
        sample_protection_group,
    ):
        """Test handling when DRS start_recovery API fails"""
        from index import start_wave_recovery

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        # Mock DRS API error
        mock_drs_client.start_recovery.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ThrottlingException",
                    "Message": "Rate exceeded",
                }
            },
            "StartRecovery",
        )

        with patch("index.protection_groups_table", pg_table):
            with patch("index.create_drs_client", return_value=mock_drs_client):
                with patch(
                    "index.query_drs_servers_by_tags",
                    return_value=["s-001", "s-002"],
                ):
                    with patch("index.apply_launch_config_before_recovery"):
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
    ):
        """Test that DynamoDB update errors don't fail wave start"""
        from index import start_wave_recovery

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.side_effect = ClientError(
            {"Error": {"Code": "ProvisionedThroughputExceededException"}},
            "UpdateItem",
        )

        mock_drs_client.start_recovery.return_value = {
            "job": {"jobID": "drsjob-abc123"}
        }

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch(
                    "index.create_drs_client", return_value=mock_drs_client
                ):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=["s-001"],
                    ):
                        with patch(
                            "index.apply_launch_config_before_recovery"
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
    ):
        """Test that cross-account context is passed to DRS client"""
        from index import start_wave_recovery

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_drs_client.start_recovery.return_value = {
            "job": {"jobID": "drsjob-abc123"}
        }

        mock_create_drs_client = Mock(return_value=mock_drs_client)

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch(
                    "index.create_drs_client", mock_create_drs_client
                ):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=["s-001"],
                    ):
                        with patch(
                            "index.apply_launch_config_before_recovery"
                        ):
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

        mock_drs_client.start_recovery.return_value = {
            "job": {"jobID": "drsjob-abc123"}
        }

        mock_create_drs_client = Mock(return_value=mock_drs_client)

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch(
                    "index.create_drs_client", mock_create_drs_client
                ):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=["s-001"],
                    ):
                        with patch(
                            "index.apply_launch_config_before_recovery"
                        ):
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
    ):
        """Test handling when using current account (no role assumption)"""
        from index import start_wave_recovery

        # State with current account context
        sample_state["accountContext"] = {
            "accountId": "123456789012",
            "isCurrentAccount": True,
        }

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_drs_client.start_recovery.return_value = {
            "job": {"jobID": "drsjob-abc123"}
        }

        mock_create_drs_client = Mock(return_value=mock_drs_client)

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch(
                    "index.create_drs_client", mock_create_drs_client
                ):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=["s-001"],
                    ):
                        with patch(
                            "index.apply_launch_config_before_recovery"
                        ):
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
    ):
        """Test that launch config is applied when present in PG"""
        from index import start_wave_recovery

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_drs_client.start_recovery.return_value = {
            "job": {"jobID": "drsjob-abc123"}
        }

        mock_apply_launch_config = Mock()

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch(
                    "index.create_drs_client", return_value=mock_drs_client
                ):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=["s-001", "s-002"],
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

        mock_drs_client.start_recovery.return_value = {
            "job": {"jobID": "drsjob-abc123"}
        }

        mock_apply_launch_config = Mock()

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch(
                    "index.create_drs_client", return_value=mock_drs_client
                ):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=["s-001"],
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

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_drs_client.start_recovery.return_value = {
            "job": {"jobID": "drsjob-abc123"}
        }

        # Store original state reference
        original_state_id = id(sample_state)

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch(
                    "index.create_drs_client", return_value=mock_drs_client
                ):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=["s-001"],
                    ):
                        with patch(
                            "index.apply_launch_config_before_recovery"
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
        sample_state["wave_results"] = [
            {"waveNumber": 0, "status": "COMPLETED"}
        ]

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_drs_client.start_recovery.return_value = {
            "job": {"jobID": "drsjob-abc123"}
        }

        # Start wave 1 (second wave)
        sample_state["waves"].append(
            {
                "waveNumber": 1,
                "waveName": "Wave 2",
                "protectionGroupId": "pg-789",
            }
        )

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch(
                    "index.create_drs_client", return_value=mock_drs_client
                ):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=["s-001"],
                    ):
                        with patch(
                            "index.apply_launch_config_before_recovery"
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

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_drs_client.start_recovery.return_value = {
            "job": {"jobID": "drsjob-abc123"}
        }

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch(
                    "index.create_drs_client", return_value=mock_drs_client
                ):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=["s-001", "s-002"],
                    ):
                        with patch(
                            "index.apply_launch_config_before_recovery"
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

        sample_state["is_drill"] = True

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_drs_client.start_recovery.return_value = {
            "job": {"jobID": "drsjob-abc123"}
        }

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch(
                    "index.create_drs_client", return_value=mock_drs_client
                ):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=["s-001"],
                    ):
                        with patch(
                            "index.apply_launch_config_before_recovery"
                        ):
                            with patch("time.time", return_value=1234567890):
                                start_wave_recovery(sample_state, 0)

        # Verify isDrill=True was passed
        call_args = mock_drs_client.start_recovery.call_args
        assert call_args[1]["isDrill"] is True

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

        sample_state["is_drill"] = False

        pg_table = mock_dynamodb_tables["protection_groups_table"]
        pg_table.get_item.return_value = {"Item": sample_protection_group}

        exec_table = mock_dynamodb_tables["execution_history_table"]
        exec_table.update_item.return_value = {}

        mock_drs_client.start_recovery.return_value = {
            "job": {"jobID": "drsjob-abc123"}
        }

        with patch("index.protection_groups_table", pg_table):
            with patch("index.execution_history_table", exec_table):
                with patch(
                    "index.create_drs_client", return_value=mock_drs_client
                ):
                    with patch(
                        "index.query_drs_servers_by_tags",
                        return_value=["s-001"],
                    ):
                        with patch(
                            "index.apply_launch_config_before_recovery"
                        ):
                            with patch("time.time", return_value=1234567890):
                                start_wave_recovery(sample_state, 0)

        # Verify isDrill=False was passed
        call_args = mock_drs_client.start_recovery.call_args
        assert call_args[1]["isDrill"] is False
