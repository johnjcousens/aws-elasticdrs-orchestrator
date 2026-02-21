"""
Unit tests for Protection Group update integration with launch config pre-application.

Tests the selective config re-application logic in update_protection_group():
- Re-applies configs when servers change (sourceServerIds or serverSelectionTags)
- Re-applies configs when launchConfig changes
- Preserves status when no changes detected
- Handles timeouts gracefully (update succeeds, status "pending")
- Handles application failures gracefully (update succeeds, status "failed")

**Validates: Requirements 5.1**
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add lambda directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lambda"))

# Set environment variables before importing handler
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
os.environ["TAG_SYNC_CONFIG_TABLE"] = "test-tag-sync-config"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Import handler module
import importlib

data_management_handler = importlib.import_module("data-management-handler.index")
update_protection_group = data_management_handler.update_protection_group

# Import launch config service for exception types
from shared.launch_config_service import (
    LaunchConfigApplicationError,
    LaunchConfigTimeoutError,
)



@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks between tests to prevent state pollution."""
    yield
    patch.stopall()


def create_existing_group():
    """Create existing protection group with launch config"""
    return {
        "groupId": "pg-12345",
        "groupName": "Test Group",
        "region": "us-east-1",
        "accountId": "123456789012",
        "sourceServerIds": ["s-111", "s-222"],
        "serverSelectionTags": {},
        "launchConfig": {
            "instanceType": "t3.medium",
            "subnetId": "subnet-111",
            "securityGroupIds": ["sg-111"],
        },
        "version": 1,
        "createdDate": int(time.time()),
        "lastModifiedDate": int(time.time()),
    }


# ============================================================================
# Test: Update with server changes triggers config re-application
# ============================================================================


def test_update_with_server_list_changes_reapplies_configs():
    """
    Test that updating sourceServerIds triggers config re-application.
    
    **Validates: Requirements 5.1**
    """
    # Setup
    existing_group = create_existing_group()
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": existing_group}
    mock_table.update_item.return_value = {
        "Attributes": {**existing_group, "version": 2}
    }

    mock_apply_result = {
        "status": "applied",
        "serverConfigs": {
            "s-111": {"status": "applied"},
            "s-333": {"status": "applied"},
        },
        "errors": [],
    }

    with patch.object(
        data_management_handler,
        "get_protection_groups_table",
        return_value=mock_table
    ):
        with patch.object(
            data_management_handler,
            "get_active_execution_for_protection_group",
            return_value=None
        ):
            with patch.object(
                data_management_handler,
                "check_server_conflicts_for_update",
                return_value=[]
            ):
                with patch.object(
                    data_management_handler,
                    "get_current_account_id",
                    return_value="123456789012"
                ):
                    with patch.object(
                        data_management_handler,
                        "apply_launch_configs_to_group",
                        return_value=mock_apply_result
                    ) as mock_apply:
                        with patch.object(
                            data_management_handler,
                            "persist_config_status"
                        ) as mock_persist:
                            # Act: Update with different server list
                            body = {
                                "sourceServerIds": ["s-111", "s-333"],
                                "launchConfig": existing_group["launchConfig"],
                                "version": 1,
                            }

                            result = update_protection_group("pg-12345", body)

                            # Assert
                            assert result["statusCode"] == 200
                            mock_apply.assert_called_once()
                            mock_persist.assert_called_once()
                            
                            # Verify correct servers passed
                            call_args = mock_apply.call_args
                            assert set(call_args[1]["server_ids"]) == {"s-111", "s-333"}


# ============================================================================
# Test: Update with config changes triggers re-application
# ============================================================================


def test_update_with_config_changes_reapplies_configs():
    """
    Test that updating launchConfig triggers config re-application.
    
    **Validates: Requirements 5.1**
    """
    # Setup
    existing_group = create_existing_group()
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": existing_group}
    mock_table.update_item.return_value = {
        "Attributes": {**existing_group, "version": 2}
    }

    mock_apply_result = {
        "status": "applied",
        "serverConfigs": {
            "s-111": {"status": "applied"},
            "s-222": {"status": "applied"},
        },
        "errors": [],
    }

    with patch.object(
        data_management_handler,
        "get_protection_groups_table",
        return_value=mock_table
    ):
        with patch.object(
            data_management_handler,
            "get_active_execution_for_protection_group",
            return_value=None
        ):
            with patch.object(
                data_management_handler,
                "check_server_conflicts_for_update",
                return_value=[]
            ):
                with patch.object(
                    data_management_handler,
                    "get_current_account_id",
                    return_value="123456789012"
                ):
                    with patch.object(
                        data_management_handler,
                        "apply_launch_configs_to_group",
                        return_value=mock_apply_result
                    ) as mock_apply:
                        with patch.object(
                            data_management_handler,
                            "persist_config_status"
                        ):
                            # Act: Update with different launch config
                            body = {
                                "sourceServerIds": existing_group["sourceServerIds"],
                                "launchConfig": {
                                    "instanceType": "t3.large",  # Changed
                                    "subnetId": "subnet-111",
                                    "securityGroupIds": ["sg-111"],
                                },
                                "version": 1,
                            }

                            result = update_protection_group("pg-12345", body)

                            # Assert
                            assert result["statusCode"] == 200
                            mock_apply.assert_called_once()
                            
                            # Verify new config was applied
                            call_args = mock_apply.call_args
                            applied_config = call_args[1]["launch_configs"]["s-111"]
                            assert applied_config["instanceType"] == "t3.large"


# ============================================================================
# Test: Update without changes preserves status
# ============================================================================


def test_update_without_changes_preserves_status():
    """
    Test that updating without server/config changes preserves status.
    
    **Validates: Requirements 5.1**
    """
    # Setup
    existing_group = create_existing_group()
    existing_group["launchConfigStatus"] = {
        "status": "applied",
        "lastApplied": "2025-01-15T10:00:00Z",
    }
    
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": existing_group}
    mock_table.update_item.return_value = {
        "Attributes": {**existing_group, "version": 2}
    }

    with patch.object(
        data_management_handler,
        "get_protection_groups_table",
        return_value=mock_table
    ):
        with patch.object(
            data_management_handler,
            "get_active_execution_for_protection_group",
            return_value=None
        ):
            with patch.object(
                data_management_handler,
                "validate_unique_pg_name",
                return_value=True
            ):
                with patch.object(
                    data_management_handler,
                    "apply_launch_configs_to_group"
                ) as mock_apply:
                    # Act: Update only description
                    body = {
                        "description": "Updated description",
                        "version": 1,
                    }

                    result = update_protection_group("pg-12345", body)

                    # Assert: Config re-application was NOT triggered
                    assert result["statusCode"] == 200
                    mock_apply.assert_not_called()


# ============================================================================
# Test: Update with timeout
# ============================================================================


def test_update_succeeds_when_config_application_times_out():
    """
    Test that update succeeds even when config application times out.
    Status should be "pending".
    
    **Validates: Requirements 5.1**
    """
    # Setup
    existing_group = create_existing_group()
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": existing_group}
    mock_table.update_item.return_value = {
        "Attributes": {**existing_group, "version": 2}
    }

    with patch.object(
        data_management_handler,
        "get_protection_groups_table",
        return_value=mock_table
    ):
        with patch.object(
            data_management_handler,
            "get_active_execution_for_protection_group",
            return_value=None
        ):
            with patch.object(
                data_management_handler,
                "check_server_conflicts_for_update",
                return_value=[]
            ):
                with patch.object(
                    data_management_handler,
                    "get_current_account_id",
                    return_value="123456789012"
                ):
                    with patch.object(
                        data_management_handler,
                        "apply_launch_configs_to_group",
                        side_effect=LaunchConfigTimeoutError("Timeout after 60s")
                    ):
                        with patch.object(
                            data_management_handler,
                            "persist_config_status"
                        ) as mock_persist:
                            # Act: Update with server changes
                            body = {
                                "sourceServerIds": ["s-111", "s-333"],
                                "launchConfig": existing_group["launchConfig"],
                                "version": 1,
                            }

                            result = update_protection_group("pg-12345", body)

                            # Assert: Update succeeded despite timeout
                            assert result["statusCode"] == 200
                            
                            # Verify status persisted as "pending"
                            mock_persist.assert_called_once()
                            status_call = mock_persist.call_args
                            assert status_call[0][0] == "pg-12345"
                            assert status_call[0][1]["status"] == "pending"


# ============================================================================
# Test: Update with application failure
# ============================================================================


def test_update_succeeds_when_config_application_fails():
    """
    Test that update succeeds even when config application fails.
    Status should be "failed".
    
    **Validates: Requirements 5.1**
    """
    # Setup
    existing_group = create_existing_group()
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": existing_group}
    mock_table.update_item.return_value = {
        "Attributes": {**existing_group, "version": 2}
    }

    with patch.object(
        data_management_handler,
        "get_protection_groups_table",
        return_value=mock_table
    ):
        with patch.object(
            data_management_handler,
            "get_active_execution_for_protection_group",
            return_value=None
        ):
            with patch.object(
                data_management_handler,
                "check_server_conflicts_for_update",
                return_value=[]
            ):
                with patch.object(
                    data_management_handler,
                    "get_current_account_id",
                    return_value="123456789012"
                ):
                    with patch.object(
                        data_management_handler,
                        "apply_launch_configs_to_group",
                        side_effect=LaunchConfigApplicationError("Invalid subnet")
                    ):
                        with patch.object(
                            data_management_handler,
                            "persist_config_status"
                        ) as mock_persist:
                            # Act: Update with config changes
                            body = {
                                "sourceServerIds": existing_group["sourceServerIds"],
                                "launchConfig": {
                                    "instanceType": "t3.large",
                                    "subnetId": "subnet-invalid",
                                    "securityGroupIds": ["sg-111"],
                                },
                                "version": 1,
                            }

                            result = update_protection_group("pg-12345", body)

                            # Assert: Update succeeded despite failure
                            assert result["statusCode"] == 200
                            
                            # Verify status persisted as "failed"
                            mock_persist.assert_called_once()
                            status_call = mock_persist.call_args
                            assert status_call[0][0] == "pg-12345"
                            assert status_call[0][1]["status"] == "failed"
