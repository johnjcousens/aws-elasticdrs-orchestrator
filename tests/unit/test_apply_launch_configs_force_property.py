"""
Property-based tests for apply_launch_configs force reapplication.

Feature: async-launch-config-sync

This module tests:
- Property 15: Force Reapplication
- Property 26: Drift Re-sync Allowed

Validates: Requirements 5.7, 11.2, 11.3
"""

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock, Mock, patch

import pytest
from hypothesis import given, settings, strategies as st

# Set up environment variables before importing handler
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
os.environ["TAG_SYNC_CONFIG_TABLE"] = "test-tag-sync-config"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Import from data-management-handler using importlib
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lambda"))
data_management_handler = importlib.import_module("data-management-handler.index")

# Import handler function
apply_launch_configs = data_management_handler.apply_launch_configs


# ===========================================================================
# Property 15: Force Reapplication
# ===========================================================================


@settings(max_examples=100, deadline=None)
@given(
    server_count=st.integers(min_value=1, max_value=50),
    current_status=st.sampled_from(["ready", "partial", "failed", "drifted", "not_configured"]),
    force_flag=st.booleans(),
)
def test_force_reapplication_property(server_count: int, current_status: str, force_flag: bool):
    """
    Feature: async-launch-config-sync, Property 15: Force Reapplication

    For any POST request to /protection-groups/{id}/apply-launch-configs with force=true,
    the handler SHALL re-apply configurations to all servers regardless of their current status.

    Validates: Requirements 5.7
    """
    group_id = "pg-test-123"
    server_ids = [f"s-{i:016x}" for i in range(server_count)]

    # Mock DynamoDB table
    mock_table = MagicMock()
    mock_table.get_item.return_value = {
        "Item": {
            "groupId": group_id,
            "sourceServerIds": server_ids,
            "region": "us-east-1",
            "launchConfig": {"instanceType": "t3.micro"},
        }
    }

    # Mock config status
    mock_config_status = {
        "status": current_status,
        "serverConfigs": {sid: {"status": current_status} for sid in server_ids},
    }

    with patch.object(data_management_handler, "get_protection_groups_table", return_value=mock_table):
        with patch("shared.launch_config_service.get_config_status", return_value=mock_config_status):
            with patch("shared.launch_config_service.persist_config_status") as mock_persist:
                with patch.object(data_management_handler, "_invoke_async_sync") as mock_invoke:
                    # Call apply_launch_configs
                    result = apply_launch_configs(group_id, {"force": force_flag})

                    # If force=true, should always trigger async sync regardless of status
                    if force_flag:
                        assert result["statusCode"] == 202
                        body = json.loads(result["body"])
                        assert "syncJobId" in body
                        mock_invoke.assert_called_once()
                        # Verify force flag is passed to async invocation
                        call_kwargs = mock_invoke.call_args[1]
                        assert call_kwargs["force"] is True
                    else:
                        # Without force, behavior depends on current status
                        if current_status == "syncing":
                            # Should reject with 409
                            assert result["statusCode"] == 409
                        elif current_status in ["drifted", "partial", "failed", "not_configured"]:
                            # Should allow re-sync
                            assert result["statusCode"] == 202
                            mock_invoke.assert_called_once()
                        elif current_status == "ready":
                            # Should allow re-sync (ready is in allowed_states)
                            assert result["statusCode"] == 202
                            mock_invoke.assert_called_once()


# ===========================================================================
# Property 26: Drift Re-sync Allowed
# ===========================================================================


@settings(max_examples=100, deadline=None)
@given(
    server_count=st.integers(min_value=1, max_value=50),
    drifted_server_count=st.integers(min_value=1, max_value=10),
)
def test_drift_resync_allowed_property(server_count: int, drifted_server_count: int):
    """
    Feature: async-launch-config-sync, Property 26: Drift Re-sync Allowed

    For any launchConfigStatus with "drifted" status, POST /protection-groups/{id}/apply-launch-configs
    SHALL be accepted and trigger re-synchronization.

    Validates: Requirements 11.2, 11.3
    """
    from hypothesis import assume

    # Ensure drifted count doesn't exceed total
    assume(drifted_server_count <= server_count)

    group_id = "pg-test-drift-123"
    server_ids = [f"s-{i:016x}" for i in range(server_count)]
    drifted_servers = server_ids[:drifted_server_count]

    # Mock DynamoDB table
    mock_table = MagicMock()
    mock_table.get_item.return_value = {
        "Item": {
            "groupId": group_id,
            "sourceServerIds": server_ids,
            "region": "us-east-1",
            "launchConfig": {"instanceType": "t3.micro"},
        }
    }

    # Mock config status with drift
    server_configs = {}
    for sid in server_ids:
        if sid in drifted_servers:
            server_configs[sid] = {"status": "drifted", "configHash": "old-hash"}
        else:
            server_configs[sid] = {"status": "ready", "configHash": "current-hash"}

    mock_config_status = {
        "status": "drifted",
        "serverConfigs": server_configs,
        "driftedServers": drifted_servers,
    }

    with patch.object(data_management_handler, "get_protection_groups_table", return_value=mock_table):
        with patch("shared.launch_config_service.get_config_status", return_value=mock_config_status):
            with patch("shared.launch_config_service.persist_config_status") as mock_persist:
                with patch.object(data_management_handler, "_invoke_async_sync") as mock_invoke:
                    # Call apply_launch_configs without force flag
                    result = apply_launch_configs(group_id, {})

                    # Should accept and trigger re-sync for drifted status
                    assert result["statusCode"] == 202
                    body = json.loads(result["body"])
                    assert "syncJobId" in body
                    assert body["message"] == "Launch configuration sync initiated"

                    # Verify async invocation was triggered
                    mock_invoke.assert_called_once()

                    # Verify status was set to pending
                    mock_persist.assert_called_once()
                    persist_call = mock_persist.call_args[1]
                    assert persist_call["config_status"]["status"] == "pending"
                    assert persist_call["config_status"]["totalCount"] == server_count


# ===========================================================================
# Additional test: Syncing status rejection
# ===========================================================================


@settings(max_examples=50, deadline=None)
@given(server_count=st.integers(min_value=1, max_value=50))
def test_syncing_status_rejection_property(server_count: int):
    """
    Feature: async-launch-config-sync, Property 20: Concurrent Update Rejection

    For any apply_launch_configs request when status is "syncing",
    the handler SHALL return HTTP 409 Conflict.

    Validates: Requirements 8.2
    """
    group_id = "pg-test-syncing-123"
    server_ids = [f"s-{i:016x}" for i in range(server_count)]

    # Mock DynamoDB table
    mock_table = MagicMock()
    mock_table.get_item.return_value = {
        "Item": {
            "groupId": group_id,
            "sourceServerIds": server_ids,
            "region": "us-east-1",
            "launchConfig": {"instanceType": "t3.micro"},
        }
    }

    # Mock config status as syncing
    mock_config_status = {
        "status": "syncing",
        "syncJobId": "existing-job-123",
        "progressCount": 5,
        "totalCount": server_count,
    }

    with patch.object(data_management_handler, "get_protection_groups_table", return_value=mock_table):
        with patch("shared.launch_config_service.get_config_status", return_value=mock_config_status):
            with patch.object(data_management_handler, "_invoke_async_sync") as mock_invoke:
                # Call apply_launch_configs
                result = apply_launch_configs(group_id, {})

                # Should reject with 409 Conflict
                assert result["statusCode"] == 409
                body = json.loads(result["body"])
                assert "SYNC_IN_PROGRESS" in body["error"]

                # Should NOT trigger async invocation
                mock_invoke.assert_not_called()
