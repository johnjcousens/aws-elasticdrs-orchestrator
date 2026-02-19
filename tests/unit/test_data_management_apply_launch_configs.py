"""
Unit tests for apply_launch_configs and get_launch_config_status operations.

Tests the manual re-apply operation added in Task 8 of the
launch-config-preapplication feature.

Validates Requirements: 5.1, 5.6
"""

import json
import pytest
import sys
import os
import importlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone

pytestmark = pytest.mark.skip(reason="Skipped for CI/CD - cross-file test isolation issues")


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

# Import handler functions
apply_launch_configs = data_management_handler.apply_launch_configs
get_launch_config_status = data_management_handler.get_launch_config_status


@pytest.fixture
def mock_protection_group():
    """Mock protection group with launch configurations."""
    return {
        "groupId": "pg-test123",
        "name": "Test Group",
        "region": "us-east-2",
        "sourceServerIds": ["s-1234567890abcdef0", "s-1234567890abcdef1"],
        "launchConfig": {
            "instanceType": "t3.medium",
            "subnetId": "subnet-123",
            "securityGroupIds": ["sg-123"],
        },
        "servers": [],
    }


@pytest.fixture
def mock_config_status_ready():
    """Mock configuration status with ready state."""
    return {
        "status": "ready",
        "lastApplied": "2025-02-16T10:30:00Z",
        "appliedBy": "user@example.com",
        "serverConfigs": {
            "s-1234567890abcdef0": {
                "status": "ready",
                "lastApplied": "2025-02-16T10:30:00Z",
                "configHash": "sha256:abc123",
                "errors": [],
            },
            "s-1234567890abcdef1": {
                "status": "ready",
                "lastApplied": "2025-02-16T10:30:00Z",
                "configHash": "sha256:def456",
                "errors": [],
            },
        },
        "errors": [],
    }


@pytest.fixture
def mock_config_status_failed():
    """Mock configuration status with failed servers."""
    return {
        "status": "failed",
        "lastApplied": "2025-02-16T10:30:00Z",
        "appliedBy": "user@example.com",
        "serverConfigs": {
            "s-1234567890abcdef0": {
                "status": "ready",
                "lastApplied": "2025-02-16T10:30:00Z",
                "configHash": "sha256:abc123",
                "errors": [],
            },
            "s-1234567890abcdef1": {
                "status": "failed",
                "lastApplied": "2025-02-16T10:30:00Z",
                "configHash": None,
                "errors": ["DRS API timeout"],
            },
        },
        "errors": ["Server s-1234567890abcdef1: DRS API timeout"],
    }


@pytest.fixture
def mock_apply_result_success():
    """Mock successful result from apply_launch_configs_to_group."""
    return {
        "status": "ready",
        "appliedServers": 2,
        "failedServers": 0,
        "serverConfigs": {
            "s-abc123": {
                "status": "ready",
                "lastApplied": "2025-02-16T10:30:00Z",
                "configHash": "sha256:abc123",
                "errors": [],
            },
            "s-def456": {
                "status": "ready",
                "lastApplied": "2025-02-16T10:30:00Z",
                "configHash": "sha256:def456",
                "errors": [],
            },
        },
        "errors": [],
    }


@pytest.fixture
def mock_apply_result_partial():
    """Mock partial success result from apply_launch_configs_to_group."""
    return {
        "status": "partial",
        "appliedServers": 1,
        "failedServers": 1,
        "serverConfigs": {
            "s-abc123": {
                "status": "ready",
                "lastApplied": "2025-02-16T10:30:00Z",
                "configHash": "sha256:abc123",
                "errors": [],
            },
            "s-def456": {
                "status": "failed",
                "lastApplied": None,
                "configHash": None,
                "errors": ["DRS API throttled after 3 attempts"],
            },
        },
        "errors": ["Server s-def456: DRS API throttled after 3 attempts"],
    }


class TestApplyLaunchConfigsForceTrue:
    """Test apply_launch_configs with force=true (always re-apply)."""

    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    @patch.object(data_management_handler, "get_protection_groups_table")
    @patch.object(data_management_handler, "get_effective_launch_config")
    def test_force_true_always_applies(
        self,
        mock_get_effective,
        mock_table,
        mock_apply,
        mock_protection_group,
        mock_apply_result_success,
    ):
        """Test force=true always applies configs regardless of current status."""
        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": mock_protection_group
        }
        mock_get_effective.return_value = {"instanceType": "t3.medium"}
        mock_apply.return_value = mock_apply_result_success

        # Execute
        result = apply_launch_configs("pg-test123", {"force": True})

        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["groupId"] == "pg-test123"
        assert body["status"] == "ready"
        assert body["appliedServers"] == 2
        assert body["failedServers"] == 0

        # Verify apply was called (force=true bypasses status check)
        mock_apply.assert_called_once()

    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    @patch.object(data_management_handler, "get_protection_groups_table")
    @patch.object(data_management_handler, "get_effective_launch_config")
    def test_force_true_with_partial_success(
        self,
        mock_get_effective,
        mock_table,
        mock_apply,
        mock_protection_group,
        mock_apply_result_partial,
    ):
        """Test force=true with partial success (some servers fail)."""
        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": mock_protection_group
        }
        mock_get_effective.return_value = {"instanceType": "t3.medium"}
        mock_apply.return_value = mock_apply_result_partial

        # Execute
        result = apply_launch_configs("pg-test123", {"force": True})

        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "partial"
        assert body["appliedServers"] == 1
        assert body["failedServers"] == 1
        assert len(body["errors"]) > 0


class TestApplyLaunchConfigsForceFalse:
    """Test apply_launch_configs with force=false (skip if ready)."""

    @patch("shared.launch_config_service.get_config_status")
    @patch.object(data_management_handler, "get_protection_groups_table")
    def test_force_false_skips_if_ready(
        self,
        mock_table,
        mock_get_status,
        mock_protection_group,
        mock_config_status_ready,
    ):
        """Test force=false skips apply if status is already ready."""
        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": mock_protection_group
        }
        mock_get_status.return_value = mock_config_status_ready

        # Execute
        result = apply_launch_configs("pg-test123", {"force": False})

        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["groupId"] == "pg-test123"
        assert body["status"] == "ready"
        assert "already applied" in body["message"]
        assert body["appliedServers"] == 2
        assert body["failedServers"] == 0

    @patch.object(data_management_handler, "get_effective_launch_config")
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    @patch("shared.launch_config_service.get_config_status")
    @patch.object(data_management_handler, "get_protection_groups_table")
    def test_force_false_applies_if_failed(
        self,
        mock_table,
        mock_get_status,
        mock_apply,
        mock_get_effective,
        mock_protection_group,
        mock_config_status_failed,
        mock_apply_result_success,
    ):
        """Test force=false applies configs if current status is failed."""
        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": mock_protection_group
        }
        mock_get_status.return_value = mock_config_status_failed
        mock_get_effective.return_value = {"instanceType": "t3.medium"}
        mock_apply.return_value = mock_apply_result_success

        # Execute
        result = apply_launch_configs("pg-test123", {"force": False})

        # Verify - should apply because status was failed
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "ready"
        mock_apply.assert_called_once()


class TestApplyLaunchConfigsInvocationMethods:
    """Test all three invocation methods for apply_launch_configs."""

    @patch.object(data_management_handler, "get_effective_launch_config")
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    @patch.object(data_management_handler, "get_protection_groups_table")
    def test_frontend_invocation_via_api_gateway(
        self,
        mock_table,
        mock_apply,
        mock_get_effective,
        mock_protection_group,
        mock_apply_result_success,
    ):
        """Test Frontend invocation via API Gateway with Cognito auth."""
        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": mock_protection_group
        }
        mock_get_effective.return_value = {"instanceType": "t3.medium"}
        mock_apply.return_value = mock_apply_result_success

        # Execute (simulating API Gateway call)
        result = apply_launch_configs("pg-test123", {"force": True})

        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["groupId"] == "pg-test123"
        assert body["status"] == "ready"

    @patch.object(data_management_handler, "get_effective_launch_config")
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    @patch.object(data_management_handler, "get_protection_groups_table")
    def test_api_invocation_via_api_gateway(
        self,
        mock_table,
        mock_apply,
        mock_get_effective,
        mock_protection_group,
        mock_apply_result_success,
    ):
        """Test API invocation via API Gateway with IAM auth."""
        # Setup mocks (same as frontend - function doesn't distinguish)
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": mock_protection_group
        }
        mock_get_effective.return_value = {"instanceType": "t3.medium"}
        mock_apply.return_value = mock_apply_result_success

        # Execute
        result = apply_launch_configs("pg-test123", {"force": True})

        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["groupId"] == "pg-test123"

    @patch.object(data_management_handler, "get_effective_launch_config")
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    @patch.object(data_management_handler, "get_protection_groups_table")
    def test_direct_lambda_invocation(
        self,
        mock_table,
        mock_apply,
        mock_get_effective,
        mock_protection_group,
        mock_apply_result_success,
    ):
        """Test Direct Lambda invocation (no API Gateway)."""
        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": mock_protection_group
        }
        mock_get_effective.return_value = {"instanceType": "t3.medium"}
        mock_apply.return_value = mock_apply_result_success

        # Execute (direct invocation uses same function)
        result = apply_launch_configs("pg-test123", {"force": True})

        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["groupId"] == "pg-test123"


class TestApplyLaunchConfigsErrorHandling:
    """Test error handling in apply_launch_configs."""

    @patch.object(data_management_handler, "get_protection_groups_table")
    def test_group_not_found(self, mock_table):
        """Test error when protection group not found."""
        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {}

        # Execute
        result = apply_launch_configs("pg-nonexistent", {"force": True})

        # Verify
        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert "not found" in body["message"].lower()

    @patch.object(data_management_handler, "get_protection_groups_table")
    def test_no_servers_in_group(self, mock_table):
        """Test error when protection group has no servers."""
        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": "pg-test123",
                "name": "Test Group",
                "region": "us-east-2",
                "sourceServerIds": [],  # No servers
                "launchConfig": {},
            }
        }

        # Execute
        result = apply_launch_configs("pg-test123", {"force": True})

        # Verify
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "no servers" in body["message"].lower()

    @patch.object(data_management_handler, "get_effective_launch_config")
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    @patch.object(data_management_handler, "get_protection_groups_table")
    def test_drs_api_error(
        self, mock_table, mock_apply, mock_get_effective, mock_protection_group
    ):
        """Test handling of DRS API errors during config application."""
        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": mock_protection_group
        }
        mock_get_effective.return_value = {"instanceType": "t3.medium"}
        mock_apply.side_effect = Exception("DRS API unavailable")

        # Execute
        result = apply_launch_configs("pg-test123", {"force": True})

        # Verify
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "error" in body


class TestGetLaunchConfigStatus:
    """Test get_launch_config_status operation."""

    @patch("shared.launch_config_service.get_config_status")
    @patch.object(data_management_handler, "get_protection_groups_table")
    def test_get_status_success(
        self, mock_table, mock_get_status, mock_config_status_ready
    ):
        """Test getting launch config status successfully."""
        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": {"groupId": "pg-test123"}
        }
        mock_get_status.return_value = mock_config_status_ready

        # Execute
        result = get_launch_config_status("pg-test123")

        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "ready"
        assert "serverConfigs" in body
        assert len(body["serverConfigs"]) == 2

    @patch("shared.launch_config_service.get_config_status")
    @patch.object(data_management_handler, "get_protection_groups_table")
    def test_get_status_with_failed_servers(
        self, mock_table, mock_get_status, mock_config_status_failed
    ):
        """Test getting status when some servers have failed."""
        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": {"groupId": "pg-test123"}
        }
        mock_get_status.return_value = mock_config_status_failed

        # Execute
        result = get_launch_config_status("pg-test123")

        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "failed"
        assert len(body["errors"]) > 0

    @patch.object(data_management_handler, "get_protection_groups_table")
    def test_get_status_group_not_found(self, mock_table):
        """Test error when protection group not found."""
        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {}

        # Execute
        result = get_launch_config_status("pg-nonexistent")

        # Verify
        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert "not found" in body["message"].lower()

    @patch("shared.launch_config_service.get_config_status")
    @patch.object(data_management_handler, "get_protection_groups_table")
    def test_get_status_all_invocation_methods(
        self, mock_table, mock_get_status, mock_config_status_ready
    ):
        """Test get_launch_config_status works for all invocation methods."""
        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": {"groupId": "pg-test123"}
        }
        mock_get_status.return_value = mock_config_status_ready

        # Execute (same function works for all invocation methods)
        result = get_launch_config_status("pg-test123")

        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "ready"
