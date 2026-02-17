"""
Unit tests for launch configuration service.

Feature: launch-config-preapplication
Tests specific examples and edge cases for launch config service functions.

Validates: Requirements 5.1
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.launch_config_service import (
    LaunchConfigApplicationError,
    LaunchConfigTimeoutError,
    LaunchConfigValidationError,
    calculate_config_hash,
    detect_config_drift,
    get_config_status,
    persist_config_status,
)


class TestCalculateConfigHash:
    """Tests for calculate_config_hash function.

    Validates: Requirements 4.4 (drift detection)
    """

    def test_empty_config_returns_empty_hash(self):
        """Test empty configuration returns special empty hash."""
        result = calculate_config_hash({})
        assert result == "sha256:empty"

    def test_none_config_returns_empty_hash(self):
        """Test None configuration returns special empty hash."""
        result = calculate_config_hash(None)
        assert result == "sha256:empty"

    def test_simple_config_returns_valid_hash(self):
        """Test simple configuration returns valid SHA-256 hash."""
        config = {"instanceType": "t3.medium"}
        result = calculate_config_hash(config)
        assert result.startswith("sha256:")
        assert len(result) == 71  # "sha256:" (7) + 64 hex chars

    def test_hash_is_deterministic(self):
        """Test same configuration produces same hash."""
        config = {"instanceType": "t3.medium", "copyPrivateIp": True}
        hash1 = calculate_config_hash(config)
        hash2 = calculate_config_hash(config)
        assert hash1 == hash2

    def test_hash_independent_of_key_order(self):
        """Test hash is same regardless of key insertion order."""
        config1 = {"instanceType": "t3.medium", "copyPrivateIp": True}
        config2 = {"copyPrivateIp": True, "instanceType": "t3.medium"}
        hash1 = calculate_config_hash(config1)
        hash2 = calculate_config_hash(config2)
        assert hash1 == hash2

    def test_different_configs_produce_different_hashes(self):
        """Test different configurations produce different hashes."""
        config1 = {"instanceType": "t3.medium"}
        config2 = {"instanceType": "t3.large"}
        hash1 = calculate_config_hash(config1)
        hash2 = calculate_config_hash(config2)
        assert hash1 != hash2

    def test_nested_config_hashing(self):
        """Test nested configuration structures are hashed correctly."""
        config = {
            "instanceType": "t3.medium",
            "licensing": {"osByol": True},
            "copyPrivateIp": False,
        }
        result = calculate_config_hash(config)
        assert result.startswith("sha256:")
        assert len(result) == 71

    def test_config_with_lists(self):
        """Test configuration with list values."""
        config = {
            "instanceType": "t3.medium",
            "securityGroupIds": ["sg-123", "sg-456"],
        }
        result = calculate_config_hash(config)
        assert result.startswith("sha256:")

    def test_config_with_numbers(self):
        """Test configuration with numeric values."""
        config = {"instanceType": "t3.medium", "ebsOptimized": True, "count": 5}
        result = calculate_config_hash(config)
        assert result.startswith("sha256:")

    def test_config_with_boolean_values(self):
        """Test configuration with boolean values."""
        config = {"copyPrivateIp": True, "copyTags": False}
        hash1 = calculate_config_hash(config)
        # Different boolean values should produce different hash
        config2 = {"copyPrivateIp": False, "copyTags": True}
        hash2 = calculate_config_hash(config2)
        assert hash1 != hash2

    def test_hash_format_is_consistent(self):
        """Test hash format always starts with sha256: prefix."""
        configs = [
            {"instanceType": "t3.medium"},
            {"copyPrivateIp": True},
            {"licensing": {"osByol": True}},
        ]
        for config in configs:
            result = calculate_config_hash(config)
            assert result.startswith("sha256:")
            assert ":" in result
            parts = result.split(":")
            assert len(parts) == 2
            assert parts[0] == "sha256"
            assert len(parts[1]) == 64  # SHA-256 produces 64 hex chars


class TestPersistConfigStatus:
    """Tests for persist_config_status function.

    Validates: Requirements 1.4 (status persistence)
    """

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_persist_valid_status_succeeds(self, mock_get_table):
        """Test persisting valid configuration status succeeds."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        config_status = {
            "status": "ready",
            "lastApplied": "2025-02-16T10:30:00Z",
            "appliedBy": "user@example.com",
            "serverConfigs": {},
            "errors": [],
        }

        persist_config_status("pg-123", config_status)

        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args
        assert call_args[1]["Key"] == {"groupId": "pg-123"}
        assert ":status" in call_args[1]["ExpressionAttributeValues"]
        assert (
            call_args[1]["ExpressionAttributeValues"][":status"]
            == config_status
        )

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_persist_with_server_configs(self, mock_get_table):
        """Test persisting status with per-server configurations."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        config_status = {
            "status": "ready",
            "lastApplied": "2025-02-16T10:30:00Z",
            "appliedBy": "user@example.com",
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": "2025-02-16T10:30:00Z",
                    "configHash": "sha256:abc123",
                    "errors": [],
                }
            },
            "errors": [],
        }

        persist_config_status("pg-123", config_status)

        mock_table.update_item.assert_called_once()

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_persist_with_errors(self, mock_get_table):
        """Test persisting status with error messages."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        config_status = {
            "status": "failed",
            "lastApplied": "2025-02-16T10:30:00Z",
            "appliedBy": "user@example.com",
            "serverConfigs": {},
            "errors": ["DRS API timeout", "Invalid configuration"],
        }

        persist_config_status("pg-123", config_status)

        mock_table.update_item.assert_called_once()

    def test_persist_empty_group_id_raises_error(self):
        """Test persisting with empty group ID raises validation error."""
        config_status = {
            "status": "ready",
            "serverConfigs": {},
            "errors": [],
        }

        with pytest.raises(
            LaunchConfigValidationError, match="group_id is required"
        ):
            persist_config_status("", config_status)

    def test_persist_none_group_id_raises_error(self):
        """Test persisting with None group ID raises validation error."""
        config_status = {
            "status": "ready",
            "serverConfigs": {},
            "errors": [],
        }

        with pytest.raises(
            LaunchConfigValidationError, match="group_id is required"
        ):
            persist_config_status(None, config_status)

    def test_persist_none_config_status_raises_error(self):
        """Test persisting None config status raises validation error."""
        with pytest.raises(
            LaunchConfigValidationError, match="config_status is required"
        ):
            persist_config_status("pg-123", None)

    def test_persist_empty_config_status_raises_error(self):
        """Test persisting empty config status raises validation error."""
        with pytest.raises(
            LaunchConfigValidationError, match="config_status is required"
        ):
            persist_config_status("pg-123", {})

    def test_persist_missing_status_field_raises_error(self):
        """Test persisting without status field raises validation error."""
        config_status = {"serverConfigs": {}, "errors": []}

        with pytest.raises(
            LaunchConfigValidationError,
            match="config_status missing required field: status",
        ):
            persist_config_status("pg-123", config_status)

    def test_persist_missing_server_configs_field_raises_error(self):
        """Test persisting without serverConfigs field raises error."""
        config_status = {"status": "ready", "errors": []}

        with pytest.raises(
            LaunchConfigValidationError,
            match="config_status missing required field: serverConfigs",
        ):
            persist_config_status("pg-123", config_status)

    def test_persist_missing_errors_field_raises_error(self):
        """Test persisting without errors field raises validation error."""
        config_status = {"status": "ready", "serverConfigs": {}}

        with pytest.raises(
            LaunchConfigValidationError,
            match="config_status missing required field: errors",
        ):
            persist_config_status("pg-123", config_status)

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_persist_dynamodb_client_error_raises_application_error(
        self, mock_get_table
    ):
        """Test DynamoDB ClientError is wrapped in application error."""
        from botocore.exceptions import ClientError

        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.update_item.side_effect = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid"}},
            "UpdateItem",
        )

        config_status = {
            "status": "ready",
            "serverConfigs": {},
            "errors": [],
        }

        with pytest.raises(
            LaunchConfigApplicationError, match="DynamoDB update failed"
        ):
            persist_config_status("pg-123", config_status)

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_persist_uses_atomic_update(self, mock_get_table):
        """Test persist uses atomic DynamoDB update operation."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        config_status = {
            "status": "ready",
            "serverConfigs": {},
            "errors": [],
        }

        persist_config_status("pg-123", config_status)

        # Verify update_item was called (atomic operation)
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args
        assert "UpdateExpression" in call_args[1]
        assert "SET launchConfigStatus" in call_args[1]["UpdateExpression"]


class TestGetConfigStatus:
    """Tests for get_config_status function.

    Validates: Requirements 2.1, 2.2 (status retrieval)
    """

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_get_existing_status_returns_status(self, mock_get_table):
        """Test retrieving existing configuration status."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        expected_status = {
            "status": "ready",
            "lastApplied": "2025-02-16T10:30:00Z",
            "appliedBy": "user@example.com",
            "serverConfigs": {},
            "errors": [],
        }

        mock_table.get_item.return_value = {
            "Item": {"groupId": "pg-123", "launchConfigStatus": expected_status}
        }

        result = get_config_status("pg-123")

        assert result == expected_status
        mock_table.get_item.assert_called_once_with(Key={"groupId": "pg-123"})

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_get_status_without_launch_config_returns_default(
        self, mock_get_table
    ):
        """Test retrieving status for group without config returns default."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        mock_table.get_item.return_value = {
            "Item": {"groupId": "pg-123", "groupName": "Test Group"}
        }

        result = get_config_status("pg-123")

        assert result["status"] == "not_configured"
        assert result["lastApplied"] is None
        assert result["appliedBy"] is None
        assert result["serverConfigs"] == {}
        assert result["errors"] == []

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_get_status_group_not_found_raises_error(self, mock_get_table):
        """Test retrieving status for non-existent group raises error."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        mock_table.get_item.return_value = {}

        with pytest.raises(
            LaunchConfigApplicationError,
            match="Protection group pg-123 not found",
        ):
            get_config_status("pg-123")

    def test_get_status_empty_group_id_raises_error(self):
        """Test retrieving status with empty group ID raises error."""
        with pytest.raises(
            LaunchConfigValidationError, match="group_id is required"
        ):
            get_config_status("")

    def test_get_status_none_group_id_raises_error(self):
        """Test retrieving status with None group ID raises error."""
        with pytest.raises(
            LaunchConfigValidationError, match="group_id is required"
        ):
            get_config_status(None)

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_get_status_dynamodb_client_error_raises_application_error(
        self, mock_get_table
    ):
        """Test DynamoDB ClientError is wrapped in application error."""
        from botocore.exceptions import ClientError

        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.get_item.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Not found"}},
            "GetItem",
        )

        with pytest.raises(
            LaunchConfigApplicationError, match="DynamoDB query failed"
        ):
            get_config_status("pg-123")

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_get_status_with_server_configs(self, mock_get_table):
        """Test retrieving status with per-server configurations."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        expected_status = {
            "status": "ready",
            "lastApplied": "2025-02-16T10:30:00Z",
            "appliedBy": "user@example.com",
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": "2025-02-16T10:30:00Z",
                    "configHash": "sha256:abc123",
                    "errors": [],
                }
            },
            "errors": [],
        }

        mock_table.get_item.return_value = {
            "Item": {"groupId": "pg-123", "launchConfigStatus": expected_status}
        }

        result = get_config_status("pg-123")

        assert result == expected_status
        assert "s-1234567890abcdef0" in result["serverConfigs"]

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_get_status_with_errors(self, mock_get_table):
        """Test retrieving status with error messages."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        expected_status = {
            "status": "failed",
            "lastApplied": "2025-02-16T10:30:00Z",
            "appliedBy": "user@example.com",
            "serverConfigs": {},
            "errors": ["DRS API timeout", "Invalid configuration"],
        }

        mock_table.get_item.return_value = {
            "Item": {"groupId": "pg-123", "launchConfigStatus": expected_status}
        }

        result = get_config_status("pg-123")

        assert result == expected_status
        assert len(result["errors"]) == 2


class TestErrorHandling:
    """Tests for error handling and exception classes."""

    def test_launch_config_application_error_is_exception(self):
        """Test LaunchConfigApplicationError is an Exception."""
        error = LaunchConfigApplicationError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_launch_config_timeout_error_inherits_from_application_error(
        self,
    ):
        """Test LaunchConfigTimeoutError inherits from base error."""
        error = LaunchConfigTimeoutError("Timeout")
        assert isinstance(error, LaunchConfigApplicationError)
        assert isinstance(error, Exception)

    def test_launch_config_validation_error_inherits_from_application_error(
        self,
    ):
        """Test LaunchConfigValidationError inherits from base error."""
        error = LaunchConfigValidationError("Validation failed")
        assert isinstance(error, LaunchConfigApplicationError)
        assert isinstance(error, Exception)

    def test_error_messages_are_preserved(self):
        """Test error messages are preserved correctly."""
        message = "Configuration application failed"
        error = LaunchConfigApplicationError(message)
        assert str(error) == message

    def test_timeout_error_can_be_caught_as_application_error(self):
        """Test timeout error can be caught as application error."""
        try:
            raise LaunchConfigTimeoutError("Timeout")
        except LaunchConfigApplicationError as e:
            assert "Timeout" in str(e)

    def test_validation_error_can_be_caught_as_application_error(self):
        """Test validation error can be caught as application error."""
        try:
            raise LaunchConfigValidationError("Invalid")
        except LaunchConfigApplicationError as e:
            assert "Invalid" in str(e)


class TestEnvironmentVariableHandling:
    """Tests for environment variable handling."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("shared.launch_config_service._get_dynamodb_resource")
    def test_missing_table_name_env_var_raises_error(self, mock_get_resource):
        """Test missing PROTECTION_GROUPS_TABLE env var raises error."""
        # Reset global variables
        import shared.launch_config_service as service

        service._protection_groups_table = None

        mock_dynamodb = MagicMock()
        mock_get_resource.return_value = mock_dynamodb

        with pytest.raises(
            LaunchConfigApplicationError,
            match="PROTECTION_GROUPS_TABLE environment variable not set",
        ):
            service._get_protection_groups_table()

    @patch.dict(
        os.environ, {"PROTECTION_GROUPS_TABLE": "test-table"}, clear=True
    )
    @patch("shared.launch_config_service._get_dynamodb_resource")
    def test_table_name_from_env_var_is_used(self, mock_get_resource):
        """Test table name from environment variable is used."""
        # Reset global variables
        import shared.launch_config_service as service

        service._protection_groups_table = None

        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_get_resource.return_value = mock_dynamodb

        result = service._get_protection_groups_table()

        mock_dynamodb.Table.assert_called_once_with("test-table")
        assert result == mock_table


class TestApplyLaunchConfigsToGroup:
    """Tests for apply_launch_configs_to_group function.

    Validates: Requirements 1.1, 1.2, 1.4
    """

    @patch("shared.launch_config_service.boto3.client")
    @patch("shared.launch_config_service.calculate_config_hash")
    def test_successful_application_all_servers(
        self, mock_hash, mock_boto_client
    ):
        """Test successful configuration application to all servers."""
        mock_drs = MagicMock()
        mock_boto_client.return_value = mock_drs
        mock_hash.return_value = "sha256:abc123"

        server_ids = ["s-1234567890abcdef0", "s-1234567890abcdef1"]
        launch_configs = {
            "s-1234567890abcdef0": {"instanceType": "t3.medium"},
            "s-1234567890abcdef1": {"instanceType": "t3.large"},
        }

        from shared.launch_config_service import (
            apply_launch_configs_to_group,
        )

        result = apply_launch_configs_to_group(
            group_id="pg-123",
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs,
        )

        assert result["status"] == "ready"
        assert result["appliedServers"] == 2
        assert result["failedServers"] == 0
        assert len(result["serverConfigs"]) == 2
        assert result["errors"] == []

        # Verify all servers marked as ready
        for server_id in server_ids:
            assert result["serverConfigs"][server_id]["status"] == "ready"
            assert (
                result["serverConfigs"][server_id]["configHash"]
                == "sha256:abc123"
            )
            assert result["serverConfigs"][server_id]["errors"] == []

    @patch("shared.launch_config_service.boto3.client")
    @patch("shared.launch_config_service.time.time")
    def test_timeout_handling_marks_remaining_as_pending(
        self, mock_time, mock_boto_client
    ):
        """Test timeout marks remaining servers as pending."""
        mock_drs = MagicMock()
        mock_boto_client.return_value = mock_drs

        # Simulate timeout after first server
        # Need more time.time() calls for logging
        mock_time.side_effect = [0, 0, 0, 0, 301, 301, 301]

        server_ids = ["s-abc", "s-def", "s-ghi"]
        launch_configs = {
            "s-abc": {"instanceType": "t3.medium"},
            "s-def": {"instanceType": "t3.large"},
            "s-ghi": {"instanceType": "t3.xlarge"},
        }

        from shared.launch_config_service import (
            apply_launch_configs_to_group,
        )

        result = apply_launch_configs_to_group(
            group_id="pg-123",
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs,
            timeout_seconds=300,
        )

        assert result["status"] == "partial"
        assert result["appliedServers"] == 1
        assert result["failedServers"] == 0

        # First server should be ready
        assert result["serverConfigs"]["s-abc"]["status"] == "ready"

        # Remaining servers should be pending
        assert result["serverConfigs"]["s-def"]["status"] == "pending"
        assert result["serverConfigs"]["s-ghi"]["status"] == "pending"
        assert (
            "timed out"
            in result["serverConfigs"]["s-def"]["errors"][0].lower()
        )

    @patch("shared.launch_config_service.boto3.client")
    def test_retry_logic_on_throttling(self, mock_boto_client):
        """Test exponential backoff retry on DRS API throttling."""
        from botocore.exceptions import ClientError

        mock_drs = MagicMock()
        mock_boto_client.return_value = mock_drs

        # First call throttles, second succeeds
        mock_drs.update_launch_configuration.side_effect = [
            ClientError(
                {
                    "Error": {
                        "Code": "ThrottlingException",
                        "Message": "Rate exceeded",
                    }
                },
                "UpdateLaunchConfiguration",
            ),
            None,
        ]

        server_ids = ["s-abc"]
        launch_configs = {"s-abc": {"instanceType": "t3.medium"}}

        from shared.launch_config_service import (
            apply_launch_configs_to_group,
        )

        result = apply_launch_configs_to_group(
            group_id="pg-123",
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs,
        )

        assert result["status"] == "ready"
        assert result["appliedServers"] == 1
        assert mock_drs.update_launch_configuration.call_count == 2

    @patch("shared.launch_config_service.boto3.client")
    def test_partial_success_some_servers_fail(self, mock_boto_client):
        """Test partial success when some servers fail."""
        from botocore.exceptions import ClientError

        mock_drs = MagicMock()
        mock_boto_client.return_value = mock_drs

        # First server succeeds, second fails
        mock_drs.update_launch_configuration.side_effect = [
            None,
            ClientError(
                {
                    "Error": {
                        "Code": "ValidationException",
                        "Message": "Invalid config",
                    }
                },
                "UpdateLaunchConfiguration",
            ),
        ]

        server_ids = ["s-abc", "s-def"]
        launch_configs = {
            "s-abc": {"instanceType": "t3.medium"},
            "s-def": {"instanceType": "invalid"},
        }

        from shared.launch_config_service import (
            apply_launch_configs_to_group,
        )

        result = apply_launch_configs_to_group(
            group_id="pg-123",
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs,
        )

        assert result["status"] == "partial"
        assert result["appliedServers"] == 1
        assert result["failedServers"] == 1
        assert result["serverConfigs"]["s-abc"]["status"] == "ready"
        assert result["serverConfigs"]["s-def"]["status"] == "failed"
        assert len(result["errors"]) > 0

    def test_validation_error_empty_group_id(self):
        """Test validation error when group_id is empty."""
        from shared.launch_config_service import (
            LaunchConfigValidationError,
            apply_launch_configs_to_group,
        )

        with pytest.raises(
            LaunchConfigValidationError, match="group_id is required"
        ):
            apply_launch_configs_to_group(
                group_id="",
                region="us-east-2",
                server_ids=["s-abc"],
                launch_configs={"s-abc": {}},
            )

    def test_validation_error_empty_region(self):
        """Test validation error when region is empty."""
        from shared.launch_config_service import (
            LaunchConfigValidationError,
            apply_launch_configs_to_group,
        )

        with pytest.raises(
            LaunchConfigValidationError, match="region is required"
        ):
            apply_launch_configs_to_group(
                group_id="pg-123",
                region="",
                server_ids=["s-abc"],
                launch_configs={"s-abc": {}},
            )

    def test_validation_error_empty_server_ids(self):
        """Test validation error when server_ids is empty."""
        from shared.launch_config_service import (
            LaunchConfigValidationError,
            apply_launch_configs_to_group,
        )

        with pytest.raises(
            LaunchConfigValidationError,
            match="server_ids list cannot be empty",
        ):
            apply_launch_configs_to_group(
                group_id="pg-123",
                region="us-east-2",
                server_ids=[],
                launch_configs={},
            )

    def test_validation_error_empty_launch_configs(self):
        """Test validation error when launch_configs is empty."""
        from shared.launch_config_service import (
            LaunchConfigValidationError,
            apply_launch_configs_to_group,
        )

        with pytest.raises(
            LaunchConfigValidationError,
            match="launch_configs dict cannot be empty",
        ):
            apply_launch_configs_to_group(
                group_id="pg-123",
                region="us-east-2",
                server_ids=["s-abc"],
                launch_configs={},
            )

    @patch("shared.launch_config_service.boto3.client")
    def test_drs_api_error_per_server_tracking(self, mock_boto_client):
        """Test DRS API errors are tracked per server."""
        from botocore.exceptions import ClientError

        mock_drs = MagicMock()
        mock_boto_client.return_value = mock_drs

        # Different errors for different servers
        mock_drs.update_launch_configuration.side_effect = [
            ClientError(
                {
                    "Error": {
                        "Code": "ValidationException",
                        "Message": "Invalid instance type",
                    }
                },
                "UpdateLaunchConfiguration",
            ),
            ClientError(
                {
                    "Error": {
                        "Code": "AccessDeniedException",
                        "Message": "Insufficient permissions",
                    }
                },
                "UpdateLaunchConfiguration",
            ),
        ]

        server_ids = ["s-abc", "s-def"]
        launch_configs = {
            "s-abc": {"instanceType": "invalid"},
            "s-def": {"instanceType": "t3.medium"},
        }

        from shared.launch_config_service import (
            apply_launch_configs_to_group,
        )

        result = apply_launch_configs_to_group(
            group_id="pg-123",
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs,
        )

        assert result["status"] == "failed"
        assert result["failedServers"] == 2

        # Verify per-server error tracking
        assert result["serverConfigs"]["s-abc"]["status"] == "failed"
        assert (
            "Invalid instance type"
            in result["serverConfigs"]["s-abc"]["errors"][0]
        )

        assert result["serverConfigs"]["s-def"]["status"] == "failed"
        assert (
            "Insufficient permissions"
            in result["serverConfigs"]["s-def"]["errors"][0]
        )

    @patch("shared.launch_config_service._get_cross_account_drs_client")
    @patch("shared.launch_config_service.boto3.client")
    def test_cross_account_configuration_application(
        self, mock_boto_client, mock_cross_account
    ):
        """Test cross-account config application with account_context."""
        mock_drs = MagicMock()
        mock_cross_account.return_value = mock_drs

        account_context = {
            "accountId": "123456789012",
            "roleName": "OrchestrationRole",
        }

        server_ids = ["s-abc"]
        launch_configs = {"s-abc": {"instanceType": "t3.medium"}}

        from shared.launch_config_service import (
            apply_launch_configs_to_group,
        )

        result = apply_launch_configs_to_group(
            group_id="pg-123",
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs,
            account_context=account_context,
        )

        assert result["status"] == "ready"
        mock_cross_account.assert_called_once_with(
            "us-east-2", account_context
        )

    @patch("shared.launch_config_service.boto3.client")
    def test_missing_config_for_server_marks_as_failed(
        self, mock_boto_client
    ):
        """Test server without config in launch_configs is marked failed."""
        mock_drs = MagicMock()
        mock_boto_client.return_value = mock_drs

        server_ids = ["s-abc", "s-def"]
        launch_configs = {
            "s-abc": {"instanceType": "t3.medium"}
            # s-def missing
        }

        from shared.launch_config_service import (
            apply_launch_configs_to_group,
        )

        result = apply_launch_configs_to_group(
            group_id="pg-123",
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs,
        )

        assert result["status"] == "partial"
        assert result["appliedServers"] == 1
        assert result["failedServers"] == 1
        assert result["serverConfigs"]["s-def"]["status"] == "failed"
        assert (
            "No launch config found"
            in result["serverConfigs"]["s-def"]["errors"][0]
        )

    @patch("shared.launch_config_service.boto3.client")
    def test_all_servers_fail_returns_failed_status(self, mock_boto_client):
        """Test all servers failing returns overall failed status."""
        from botocore.exceptions import ClientError

        mock_drs = MagicMock()
        mock_boto_client.return_value = mock_drs

        mock_drs.update_launch_configuration.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ValidationException",
                    "Message": "Invalid",
                }
            },
            "UpdateLaunchConfiguration",
        )

        server_ids = ["s-abc", "s-def"]
        launch_configs = {
            "s-abc": {"instanceType": "t3.medium"},
            "s-def": {"instanceType": "t3.large"},
        }

        from shared.launch_config_service import (
            apply_launch_configs_to_group,
        )

        result = apply_launch_configs_to_group(
            group_id="pg-123",
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs,
        )

        assert result["status"] == "failed"
        assert result["appliedServers"] == 0
        assert result["failedServers"] == 2

    @patch("shared.launch_config_service.boto3.client")
    def test_config_hash_calculated_for_successful_servers(
        self, mock_boto_client
    ):
        """Test config hash is calculated for successfully applied servers."""
        mock_drs = MagicMock()
        mock_boto_client.return_value = mock_drs

        server_ids = ["s-abc"]
        launch_configs = {
            "s-abc": {"instanceType": "t3.medium", "copyPrivateIp": True}
        }

        from shared.launch_config_service import (
            apply_launch_configs_to_group,
        )

        result = apply_launch_configs_to_group(
            group_id="pg-123",
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs,
        )

        assert result["status"] == "ready"
        config_hash = result["serverConfigs"]["s-abc"]["configHash"]
        assert config_hash.startswith("sha256:")
        assert len(config_hash) == 71

    @patch("shared.launch_config_service.boto3.client")
    def test_last_applied_timestamp_set_for_successful_servers(
        self, mock_boto_client
    ):
        """Test lastApplied timestamp is set for successful servers."""
        mock_drs = MagicMock()
        mock_boto_client.return_value = mock_drs

        server_ids = ["s-abc"]
        launch_configs = {"s-abc": {"instanceType": "t3.medium"}}

        from shared.launch_config_service import (
            apply_launch_configs_to_group,
        )

        result = apply_launch_configs_to_group(
            group_id="pg-123",
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs,
        )

        assert result["status"] == "ready"
        last_applied = result["serverConfigs"]["s-abc"]["lastApplied"]
        assert last_applied is not None
        assert last_applied.endswith("Z")

    @patch("shared.launch_config_service.boto3.client")
    def test_drs_client_creation_failure_raises_error(
        self, mock_boto_client
    ):
        """Test DRS client creation failure raises application error."""
        mock_boto_client.side_effect = Exception("AWS credentials not found")

        from shared.launch_config_service import (
            LaunchConfigApplicationError,
            apply_launch_configs_to_group,
        )

        with pytest.raises(
            LaunchConfigApplicationError,
            match="Failed to create DRS client",
        ):
            apply_launch_configs_to_group(
                group_id="pg-123",
                region="us-east-2",
                server_ids=["s-abc"],
                launch_configs={"s-abc": {}},
            )


class TestDetectConfigDrift:
    """Tests for detect_config_drift function.

    Validates: Requirements 5.1 (drift detection)
    """

    @patch("shared.launch_config_service.get_config_status")
    def test_no_drift_with_matching_hashes(self, mock_get_status):
        """Test drift detection with matching hashes returns no drift."""
        # Setup stored status with matching hash
        stored_hash = "sha256:abc123"
        mock_get_status.return_value = {
            "status": "ready",
            "serverConfigs": {
                "s-abc": {
                    "status": "ready",
                    "configHash": stored_hash,
                }
            },
        }

        # Current config that produces same hash
        current_configs = {"s-abc": {"instanceType": "t3.medium"}}

        from shared.launch_config_service import detect_config_drift

        # Mock calculate_config_hash to return matching hash
        with patch(
            "shared.launch_config_service.calculate_config_hash",
            return_value=stored_hash,
        ):
            result = detect_config_drift("pg-123", current_configs)

        assert result["hasDrift"] is False
        assert result["driftedServers"] == []
        assert result["details"] == {}

    @patch("shared.launch_config_service.get_config_status")
    def test_drift_detected_with_mismatched_hashes(self, mock_get_status):
        """Test drift detection with mismatched hashes detects drift."""
        # Setup stored status with different hash
        stored_hash = "sha256:old_hash"
        mock_get_status.return_value = {
            "status": "ready",
            "serverConfigs": {
                "s-abc": {
                    "status": "ready",
                    "configHash": stored_hash,
                }
            },
        }

        # Current config that produces different hash
        current_configs = {"s-abc": {"instanceType": "t3.large"}}
        current_hash = "sha256:new_hash"

        from shared.launch_config_service import detect_config_drift

        # Mock calculate_config_hash to return different hash
        with patch(
            "shared.launch_config_service.calculate_config_hash",
            return_value=current_hash,
        ):
            result = detect_config_drift("pg-123", current_configs)

        assert result["hasDrift"] is True
        assert "s-abc" in result["driftedServers"]
        assert "s-abc" in result["details"]
        assert result["details"]["s-abc"]["currentHash"] == current_hash
        assert result["details"]["s-abc"]["storedHash"] == stored_hash
        assert "mismatch" in result["details"]["s-abc"]["reason"].lower()

    @patch("shared.launch_config_service.get_config_status")
    def test_drift_detected_with_missing_stored_hash(self, mock_get_status):
        """Test drift detection with missing stored hash detects drift."""
        # Setup stored status without hash
        mock_get_status.return_value = {
            "status": "ready",
            "serverConfigs": {
                "s-abc": {
                    "status": "ready",
                    "configHash": None,
                }
            },
        }

        # Current config
        current_configs = {"s-abc": {"instanceType": "t3.medium"}}
        current_hash = "sha256:current_hash"

        from shared.launch_config_service import detect_config_drift

        # Mock calculate_config_hash
        with patch(
            "shared.launch_config_service.calculate_config_hash",
            return_value=current_hash,
        ):
            result = detect_config_drift("pg-123", current_configs)

        assert result["hasDrift"] is True
        assert "s-abc" in result["driftedServers"]
        assert result["details"]["s-abc"]["currentHash"] == current_hash
        assert result["details"]["s-abc"]["storedHash"] is None
        assert "no hash" in result["details"]["s-abc"]["reason"].lower()

    @patch("shared.launch_config_service.get_config_status")
    def test_drift_detected_with_no_stored_status(self, mock_get_status):
        """Test drift detection with no stored status detects drift."""
        # Setup not_configured status
        mock_get_status.return_value = {
            "status": "not_configured",
            "serverConfigs": {},
        }

        # Current config
        current_configs = {"s-abc": {"instanceType": "t3.medium"}}
        current_hash = "sha256:current_hash"

        from shared.launch_config_service import detect_config_drift

        # Mock calculate_config_hash
        with patch(
            "shared.launch_config_service.calculate_config_hash",
            return_value=current_hash,
        ):
            result = detect_config_drift("pg-123", current_configs)

        assert result["hasDrift"] is True
        assert "s-abc" in result["driftedServers"]
        assert result["details"]["s-abc"]["currentHash"] == current_hash
        assert result["details"]["s-abc"]["storedHash"] is None
        assert (
            "no stored configuration status"
            in result["details"]["s-abc"]["reason"].lower()
        )

    @patch("shared.launch_config_service.get_config_status")
    def test_no_drift_with_empty_current_configs(self, mock_get_status):
        """Test drift detection with empty current configs returns no drift."""
        # Setup stored status
        mock_get_status.return_value = {
            "status": "ready",
            "serverConfigs": {
                "s-abc": {
                    "status": "ready",
                    "configHash": "sha256:stored_hash",
                }
            },
        }

        # Empty current configs
        current_configs = {}

        from shared.launch_config_service import detect_config_drift

        result = detect_config_drift("pg-123", current_configs)

        assert result["hasDrift"] is False
        assert result["driftedServers"] == []
        assert result["details"] == {}

    @patch("shared.launch_config_service.get_config_status")
    def test_drift_detected_with_failed_dynamodb_query(
        self, mock_get_status
    ):
        """Test drift detection with failed DynamoDB query detects drift."""
        # Simulate DynamoDB query failure
        from shared.launch_config_service import (
            LaunchConfigApplicationError,
        )

        mock_get_status.side_effect = LaunchConfigApplicationError(
            "DynamoDB query failed"
        )

        # Current config
        current_configs = {"s-abc": {"instanceType": "t3.medium"}}
        current_hash = "sha256:current_hash"

        from shared.launch_config_service import detect_config_drift

        # Mock calculate_config_hash
        with patch(
            "shared.launch_config_service.calculate_config_hash",
            return_value=current_hash,
        ):
            result = detect_config_drift("pg-123", current_configs)

        assert result["hasDrift"] is True
        assert "s-abc" in result["driftedServers"]
        assert result["details"]["s-abc"]["currentHash"] == current_hash
        assert result["details"]["s-abc"]["storedHash"] is None
        assert (
            "unable to retrieve"
            in result["details"]["s-abc"]["reason"].lower()
        )

    @patch("shared.launch_config_service.get_config_status")
    def test_drift_detection_with_multiple_servers(self, mock_get_status):
        """Test drift detection with multiple servers."""
        # Setup stored status with mixed hashes
        mock_get_status.return_value = {
            "status": "ready",
            "serverConfigs": {
                "s-abc": {
                    "status": "ready",
                    "configHash": "sha256:hash_abc",
                },
                "s-def": {
                    "status": "ready",
                    "configHash": "sha256:hash_def",
                },
                "s-ghi": {
                    "status": "ready",
                    "configHash": "sha256:hash_ghi",
                },
            },
        }

        # Current configs - s-abc matches, s-def drifted, s-ghi matches
        current_configs = {
            "s-abc": {"instanceType": "t3.medium"},
            "s-def": {"instanceType": "t3.large"},
            "s-ghi": {"instanceType": "t3.small"},
        }

        from shared.launch_config_service import detect_config_drift

        # Mock calculate_config_hash to return matching/different hashes
        def mock_hash(config):
            if config["instanceType"] == "t3.medium":
                return "sha256:hash_abc"
            elif config["instanceType"] == "t3.large":
                return "sha256:hash_def_new"
            else:
                return "sha256:hash_ghi"

        with patch(
            "shared.launch_config_service.calculate_config_hash",
            side_effect=mock_hash,
        ):
            result = detect_config_drift("pg-123", current_configs)

        assert result["hasDrift"] is True
        assert "s-def" in result["driftedServers"]
        assert "s-abc" not in result["driftedServers"]
        assert "s-ghi" not in result["driftedServers"]
        assert len(result["driftedServers"]) == 1

    @patch("shared.launch_config_service.get_config_status")
    def test_drift_detection_with_missing_server_in_stored_config(
        self, mock_get_status
    ):
        """Test drift detection when server not in stored config."""
        # Setup stored status without s-new
        mock_get_status.return_value = {
            "status": "ready",
            "serverConfigs": {
                "s-abc": {
                    "status": "ready",
                    "configHash": "sha256:hash_abc",
                }
            },
        }

        # Current configs include new server
        current_configs = {
            "s-abc": {"instanceType": "t3.medium"},
            "s-new": {"instanceType": "t3.large"},
        }

        from shared.launch_config_service import detect_config_drift

        # Mock calculate_config_hash
        with patch(
            "shared.launch_config_service.calculate_config_hash",
            side_effect=lambda c: "sha256:hash_abc"
            if c["instanceType"] == "t3.medium"
            else "sha256:hash_new",
        ):
            result = detect_config_drift("pg-123", current_configs)

        assert result["hasDrift"] is True
        assert "s-new" in result["driftedServers"]
        assert "s-abc" not in result["driftedServers"]
        assert (
            "no stored configuration"
            in result["details"]["s-new"]["reason"].lower()
        )

    @patch("shared.launch_config_service.get_config_status")
    def test_drift_detection_validates_group_id(self, mock_get_status):
        """Test drift detection validates group_id parameter."""
        from shared.launch_config_service import (
            LaunchConfigValidationError,
            detect_config_drift,
        )

        with pytest.raises(
            LaunchConfigValidationError, match="group_id is required"
        ):
            detect_config_drift("", {"s-abc": {}})

        with pytest.raises(
            LaunchConfigValidationError, match="group_id is required"
        ):
            detect_config_drift(None, {"s-abc": {}})

    @patch("shared.launch_config_service.get_config_status")
    def test_drift_detection_handles_none_current_configs(
        self, mock_get_status
    ):
        """Test drift detection handles None current_configs gracefully."""
        mock_get_status.return_value = {
            "status": "ready",
            "serverConfigs": {},
        }

        from shared.launch_config_service import detect_config_drift

        result = detect_config_drift("pg-123", None)

        assert result["hasDrift"] is False
        assert result["driftedServers"] == []
        assert result["details"] == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
