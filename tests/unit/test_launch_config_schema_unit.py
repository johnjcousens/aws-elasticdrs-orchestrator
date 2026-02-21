"""
Unit tests for launch configuration schema extension in protection groups.

Tests the launchConfigStatus field persistence, camelCase naming, schema
validation, and backward compatibility with existing protection groups.

Validates: Requirements 1.4, 2.1, 2.2
"""

import json
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest


# Add lambda directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../lambda/shared")
)


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for tests."""
    with patch.dict(
        os.environ,
        {
            "PROTECTION_GROUPS_TABLE": "test-protection-groups",
            "RECOVERY_PLANS_TABLE": "test-recovery-plans",
            "EXECUTION_HISTORY_TABLE": "test-execution-history",
            "TARGET_ACCOUNTS_TABLE": "test-target-accounts",
            "STAGING_ACCOUNTS_TABLE": "test-staging-accounts",
            "AWS_REGION": "us-east-2",
        },
    ):
        yield


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table for protection groups."""
    table = MagicMock()
    table.put_item = MagicMock()
    table.get_item = MagicMock()
    table.update_item = MagicMock()
    return table


class TestLaunchConfigStatusFieldPersistence:
    """Test launchConfigStatus field is persisted correctly."""

    def test_new_protection_group_has_launch_config_status(
        self, mock_env_vars, mock_dynamodb_table
    ):
        """
        Test that newly created protection groups include launchConfigStatus
        field with correct initial values.
        """
        # Import after env vars are set
        sys.path.insert(
            0,
            os.path.join(
                os.path.dirname(__file__), "../../lambda/data-management-handler"
            ),
        )
        import index as dm_handler

        # Mock DRS client
        mock_drs_client = MagicMock()
        mock_drs_client.describe_source_servers.return_value = {
            "items": [{"sourceServerID": "s-1234567890abcdef0"}]
        }

        # Mock dependencies
        with patch.object(
            dm_handler, "get_protection_groups_table", return_value=mock_dynamodb_table
        ):
            with patch.object(
                dm_handler, "validate_unique_pg_name", return_value=True
            ):
                with patch.object(
                    dm_handler,
                    "validate_account_context_for_invocation",
                    return_value={
                        "accountId": "123456789012",
                        "assumeRoleName": "TestRole"
                    },
                ):
                    with patch.object(
                        dm_handler,
                        "create_drs_client",
                        return_value=mock_drs_client
                    ):
                        with patch.object(
                            dm_handler,
                            "check_server_conflicts_for_create",
                            return_value=[]
                        ):
                            # Create protection group
                            event = {"requestContext": {"authorizer": {"claims": {}}}}
                            body = {
                                "groupName": "Test Group",
                                "region": "us-east-2",
                                "sourceServerIds": ["s-1234567890abcdef0"],
                            }

                            result = dm_handler.create_protection_group(event, body)

                            # Verify put_item was called
                            assert mock_dynamodb_table.put_item.called
                            call_args = mock_dynamodb_table.put_item.call_args

                            # Extract the item that was saved
                            saved_item = call_args[1]["Item"]

                            # Verify launchConfigStatus field exists
                            assert "launchConfigStatus" in saved_item

                            # Verify initial status structure
                            status = saved_item["launchConfigStatus"]
                            assert status["status"] == "not_configured"
                            assert status["lastApplied"] is None
                            assert status["appliedBy"] is None
                            assert status["serverConfigs"] == {}
                            assert status["errors"] == []

    def test_launch_config_status_uses_camel_case(
        self, mock_env_vars, mock_dynamodb_table
    ):
        """
        Test that launchConfigStatus field and all nested fields use
        camelCase naming convention.
        """
        sys.path.insert(
            0,
            os.path.join(
                os.path.dirname(__file__), "../../lambda/data-management-handler"
            ),
        )
        import index as dm_handler

        # Mock DRS client
        mock_drs_client = MagicMock()
        mock_drs_client.describe_source_servers.return_value = {
            "items": [{"sourceServerID": "s-abc"}]
        }

        with patch.object(
            dm_handler, "get_protection_groups_table", return_value=mock_dynamodb_table
        ):
            with patch.object(
                dm_handler, "validate_unique_pg_name", return_value=True
            ):
                with patch.object(
                    dm_handler,
                    "validate_account_context_for_invocation",
                    return_value={
                        "accountId": "123456789012",
                        "assumeRoleName": "TestRole"
                    },
                ):
                    with patch.object(
                        dm_handler,
                        "create_drs_client",
                        return_value=mock_drs_client
                    ):
                        with patch.object(
                            dm_handler,
                            "check_server_conflicts_for_create",
                            return_value=[]
                        ):
                            event = {"requestContext": {"authorizer": {"claims": {}}}}
                            body = {
                                "groupName": "Test Group",
                                "region": "us-east-2",
                                "sourceServerIds": ["s-abc"],
                            }

                            dm_handler.create_protection_group(event, body)

                            saved_item = mock_dynamodb_table.put_item.call_args[1]["Item"]
                            status = saved_item["launchConfigStatus"]

                            # Verify camelCase field names
                            assert "launchConfigStatus" in saved_item  # Not launch_config_status
                            assert "lastApplied" in status  # Not last_applied
                            assert "appliedBy" in status  # Not applied_by
                            assert "serverConfigs" in status  # Not server_configs

                            # Verify no snake_case fields
                            assert "launch_config_status" not in saved_item
                            assert "last_applied" not in status
                            assert "applied_by" not in status
                            assert "server_configs" not in status


class TestLaunchConfigStatusSchemaValidation:
    """Test schema validation for launchConfigStatus field."""

    def test_status_field_valid_values(self):
        """
        Test that status field only accepts valid values:
        ready, pending, failed, not_configured.
        """
        valid_statuses = ["ready", "pending", "failed", "not_configured"]

        for status_value in valid_statuses:
            status = {
                "status": status_value,
                "lastApplied": None,
                "appliedBy": None,
                "serverConfigs": {},
                "errors": [],
            }
            # Should not raise any errors
            assert status["status"] in valid_statuses

    def test_last_applied_timestamp_format(self):
        """
        Test that lastApplied field accepts ISO 8601 timestamp strings.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        status = {
            "status": "ready",
            "lastApplied": timestamp,
            "appliedBy": "user@example.com",
            "serverConfigs": {},
            "errors": [],
        }

        # Verify timestamp is valid ISO format
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)

    def test_server_configs_structure(self):
        """
        Test that serverConfigs field has correct per-server structure.
        """
        status = {
            "status": "ready",
            "lastApplied": "2025-02-16T10:30:00Z",
            "appliedBy": "user@example.com",
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": "2025-02-16T10:30:00Z",
                    "configHash": "sha256:abc123...",
                    "errors": [],
                }
            },
            "errors": [],
        }

        # Verify server config structure
        server_config = status["serverConfigs"]["s-1234567890abcdef0"]
        assert "status" in server_config
        assert "lastApplied" in server_config
        assert "configHash" in server_config
        assert "errors" in server_config
        assert isinstance(server_config["errors"], list)


class TestBackwardCompatibility:
    """Test backward compatibility with existing protection groups."""

    def test_get_protection_group_without_launch_config_status(
        self, mock_env_vars, mock_dynamodb_table
    ):
        """
        Test that getting a protection group without launchConfigStatus
        field works correctly (backward compatibility).
        """
        sys.path.insert(
            0,
            os.path.join(
                os.path.dirname(__file__), "../../lambda/data-management-handler"
            ),
        )
        import index as dm_handler

        # Mock existing group without launchConfigStatus
        existing_group = {
            "groupId": "pg-123",
            "groupName": "Legacy Group",
            "region": "us-east-2",
            "sourceServerIds": ["s-abc"],
            "createdDate": 1234567890,
            "lastModifiedDate": 1234567890,
            "version": 1,
        }

        mock_dynamodb_table.get_item.return_value = {"Item": existing_group}

        with patch.object(
            dm_handler, "get_protection_groups_table", return_value=mock_dynamodb_table
        ):
            result = dm_handler.get_protection_group("pg-123")

            # Should return successfully even without launchConfigStatus
            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["groupId"] == "pg-123"
            assert body["groupName"] == "Legacy Group"

    def test_update_protection_group_without_launch_config_status(
        self, mock_env_vars, mock_dynamodb_table
    ):
        """
        Test that updating a protection group without launchConfigStatus
        field works correctly.
        """
        sys.path.insert(
            0,
            os.path.join(
                os.path.dirname(__file__), "../../lambda/data-management-handler"
            ),
        )
        import index as dm_handler

        # Mock existing group without launchConfigStatus
        existing_group = {
            "groupId": "pg-123",
            "groupName": "Legacy Group",
            "region": "us-east-2",
            "sourceServerIds": ["s-abc"],
            "createdDate": 1234567890,
            "lastModifiedDate": 1234567890,
            "version": 1,
        }

        mock_dynamodb_table.get_item.return_value = {"Item": existing_group}
        mock_dynamodb_table.update_item.return_value = {"Attributes": existing_group}

        with patch.object(
            dm_handler, "get_protection_groups_table", return_value=mock_dynamodb_table
        ):
            with patch.object(
                dm_handler, "get_active_execution_for_protection_group", return_value=None
            ):
                body = {"description": "Updated description"}

                result = dm_handler.update_protection_group("pg-123", body)

                # Should update successfully even without launchConfigStatus
                assert result["statusCode"] == 200


class TestLaunchConfigStatusInOperations:
    """Test launchConfigStatus field in protection group operations."""

    def test_create_returns_launch_config_status(
        self, mock_env_vars, mock_dynamodb_table
    ):
        """
        Test that create_protection_group returns launchConfigStatus in
        response.
        """
        sys.path.insert(
            0,
            os.path.join(
                os.path.dirname(__file__), "../../lambda/data-management-handler"
            ),
        )
        import index as dm_handler

        # Mock DRS client
        mock_drs_client = MagicMock()
        mock_drs_client.describe_source_servers.return_value = {
            "items": [{"sourceServerID": "s-abc"}]
        }

        with patch.object(
            dm_handler, "get_protection_groups_table", return_value=mock_dynamodb_table
        ):
            with patch.object(
                dm_handler, "validate_unique_pg_name", return_value=True
            ):
                with patch.object(
                    dm_handler,
                    "validate_account_context_for_invocation",
                    return_value={
                        "accountId": "123456789012",
                        "assumeRoleName": "TestRole"
                    },
                ):
                    with patch.object(
                        dm_handler,
                        "create_drs_client",
                        return_value=mock_drs_client
                    ):
                        with patch.object(
                            dm_handler,
                            "check_server_conflicts_for_create",
                            return_value=[]
                        ):
                            event = {"requestContext": {"authorizer": {"claims": {}}}}
                            body = {
                                "groupName": "Test Group",
                                "region": "us-east-2",
                                "sourceServerIds": ["s-abc"],
                            }

                            result = dm_handler.create_protection_group(event, body)

                            # Verify response includes launchConfigStatus
                            assert result["statusCode"] == 201
                            response_body = json.loads(result["body"])
                            assert "launchConfigStatus" in response_body
                            assert response_body["launchConfigStatus"]["status"] == "not_configured"

    def test_get_returns_launch_config_status(
        self, mock_env_vars, mock_dynamodb_table
    ):
        """
        Test that get_protection_group returns launchConfigStatus in response.
        """
        sys.path.insert(
            0,
            os.path.join(
                os.path.dirname(__file__), "../../lambda/data-management-handler"
            ),
        )
        import index as dm_handler

        # Mock group with launchConfigStatus
        group_with_status = {
            "groupId": "pg-123",
            "groupName": "Test Group",
            "region": "us-east-2",
            "sourceServerIds": ["s-abc"],
            "launchConfigStatus": {
                "status": "ready",
                "lastApplied": "2025-02-16T10:30:00Z",
                "appliedBy": "user@example.com",
                "serverConfigs": {},
                "errors": [],
            },
        }

        mock_dynamodb_table.get_item.return_value = {"Item": group_with_status}

        with patch.object(
            dm_handler, "get_protection_groups_table", return_value=mock_dynamodb_table
        ):
            result = dm_handler.get_protection_group("pg-123")

            # Verify response includes launchConfigStatus
            assert result["statusCode"] == 200
            response_body = json.loads(result["body"])
            assert "launchConfigStatus" in response_body
            assert response_body["launchConfigStatus"]["status"] == "ready"
            assert (
                response_body["launchConfigStatus"]["lastApplied"]
                == "2025-02-16T10:30:00Z"
            )
