"""
Unit Tests: Protection Group Create with Launch Config Integration

Tests for Task 6.1: Write unit tests for create integration

This test file validates the integration between create_protection_group()
and launch_config_service for pre-applying launch configurations during
protection group creation.

Test Coverage:
- Successful group creation with config application
- Group creation with config application timeout
- Group creation with config application failure
- Status persistence after creation
- Cross-account config application

Requirements: 5.1 (Launch config pre-application during group operations)
"""

import json
import os
import sys
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
create_protection_group = data_management_handler.create_protection_group

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


# Helper function to create proper event structure
def create_api_gateway_event(account_id="123456789012"):
    """Create properly structured API Gateway event for tests."""
    return {
        "requestContext": {
            "authorizer": {
                "claims": {"cognito:username": "test@example.com"}
            },
            "identity": {
                "cognitoAuthenticationProvider": (
                    f"cognito-idp.us-east-1.amazonaws.com"
                    f"/us-east-1_abc:CognitoSignIn"
                    f":{account_id}"
                )
            }
        }
    }


# ============================================================================
# Test: Successful group creation with config application
# ============================================================================


def test_create_protection_group_with_launch_config_success():
    """
    Test successful protection group creation with launch config application.
    
    Validates:
    - Group is created in DynamoDB
    - Launch configs are applied to all servers
    - Config status is persisted with "ready" status
    - Response includes launchConfigStatus
    
    Requirements: 5.1
    """
    # Setup mocks
    mock_table = MagicMock()
    mock_table.put_item.return_value = {}
    
    # Mock apply_launch_configs_to_group to return success
    mock_apply_result = {
        "status": "ready",
        "appliedServers": 2,
        "failedServers": 0,
        "serverConfigs": {
            "s-abc123": {
                "status": "ready",
                "lastApplied": "2025-02-16T10:30:00Z",
                "configHash": "sha256:abc123",
                "errors": []
            },
            "s-def456": {
                "status": "ready",
                "lastApplied": "2025-02-16T10:30:00Z",
                "configHash": "sha256:abc123",
                "errors": []
            }
        },
        "errors": []
    }
    
    # Request body with launch config
    body = {
        "groupName": "Test Group",
        "region": "us-east-2",
        "sourceServerIds": ["s-abc123", "s-def456"],
        "launchConfig": {
            "instanceType": "t3.medium",
            "copyPrivateIp": True
        }
    }
    
    event = create_api_gateway_event()
    
    with patch.object(
        data_management_handler,
        "get_protection_groups_table",
        return_value=mock_table
    ):
        with patch.object(
            data_management_handler,
            "validate_unique_pg_name",
            return_value=True
        ):
            with patch.object(
                data_management_handler,
                "check_server_conflicts_for_create",
                return_value=[]
            ):
                with patch.object(
                    data_management_handler,
                    "create_drs_client"
                ) as mock_drs_client:
                    # Mock DRS describe_source_servers
                    mock_drs = MagicMock()
                    mock_drs.describe_source_servers.return_value = {
                        "items": [
                            {"sourceServerID": "s-abc123"},
                            {"sourceServerID": "s-def456"}
                        ]
                    }
                    mock_drs_client.return_value = mock_drs
                    
                    with patch.object(
                        data_management_handler,
                        "apply_launch_configs_to_group",
                        return_value=mock_apply_result
                    ) as mock_apply:
                        with patch.object(
                            data_management_handler,
                            "persist_config_status"
                        ) as mock_persist:
                            with patch.object(
                                data_management_handler,
                                "get_current_account_id",
                                return_value="123456789012"
                            ):
                                result = create_protection_group(event, body)
                                
                                # Verify response
                                assert result["statusCode"] == 201
                                response_body = json.loads(result["body"])
                                
                                # Verify group was created
                                assert "groupId" in response_body
                                assert response_body["groupName"] == "Test Group"
                                assert response_body["region"] == "us-east-2"
                                
                                # Verify launch config status is included
                                assert "launchConfigStatus" in response_body
                                assert response_body["launchConfigStatus"]["status"] == "ready"
                                # Note: serverConfigs contains the per-server status
                                assert "serverConfigs" in response_body["launchConfigStatus"]
                                assert len(response_body["launchConfigStatus"]["serverConfigs"]) == 2
                                
                                # Verify apply_launch_configs_to_group was called
                                mock_apply.assert_called_once()
                                call_args = mock_apply.call_args
                                assert call_args[1]["group_id"] is not None
                                assert call_args[1]["region"] == "us-east-2"
                                assert set(call_args[1]["server_ids"]) == {"s-abc123", "s-def456"}
                                assert call_args[1]["timeout_seconds"] == 60
                                
                                # Verify config status was persisted
                                mock_persist.assert_called_once()
                                persist_args = mock_persist.call_args
                                assert persist_args[0][1]["status"] == "ready"


# ============================================================================
# Test: Group creation with config application timeout
# ============================================================================


def test_create_protection_group_with_launch_config_timeout():
    """
    Test protection group creation when launch config application times out.
    
    Validates:
    - Group creation succeeds despite timeout
    - Config status is marked as "pending"
    - Timeout error is captured in status
    - Response includes launchConfigStatus with pending status
    
    Requirements: 5.1
    """
    # Setup mocks
    mock_table = MagicMock()
    mock_table.put_item.return_value = {}
    
    # Request body with launch config
    body = {
        "groupName": "Test Group Timeout",
        "region": "us-east-2",
        "sourceServerIds": ["s-abc123"],
        "launchConfig": {
            "instanceType": "t3.medium"
        }
    }
    
    event = create_api_gateway_event()
    
    with patch.object(
        data_management_handler,
        "get_protection_groups_table",
        return_value=mock_table
    ):
        with patch.object(
            data_management_handler,
            "validate_unique_pg_name",
            return_value=True
        ):
            with patch.object(
                data_management_handler,
                "check_server_conflicts_for_create",
                return_value=[]
            ):
                with patch.object(
                    data_management_handler,
                    "create_drs_client"
                ) as mock_drs_client:
                    mock_drs = MagicMock()
                    mock_drs.describe_source_servers.return_value = {
                        "items": [{"sourceServerID": "s-abc123"}]
                    }
                    mock_drs_client.return_value = mock_drs
                    
                    with patch.object(
                        data_management_handler,
                        "apply_launch_configs_to_group",
                        side_effect=LaunchConfigTimeoutError(
                            "Configuration application timed out"
                        )
                    ):
                        with patch.object(
                            data_management_handler,
                            "persist_config_status"
                        ) as mock_persist:
                            with patch.object(
                                data_management_handler,
                                "get_current_account_id",
                                return_value="123456789012"
                            ):
                                result = create_protection_group(event, body)
                                
                                # Verify response - group creation should succeed
                                assert result["statusCode"] == 201
                                response_body = json.loads(result["body"])
                                
                                # Verify group was created
                                assert "groupId" in response_body
                                assert response_body["groupName"] == "Test Group Timeout"
                                
                                # Verify launch config status shows pending
                                assert "launchConfigStatus" in response_body
                                assert response_body["launchConfigStatus"]["status"] == "pending"
                                assert len(response_body["launchConfigStatus"]["errors"]) > 0
                                assert "timed out" in response_body["launchConfigStatus"]["errors"][0].lower()
                                
                                # Verify config status was persisted with pending status
                                mock_persist.assert_called_once()
                                persist_args = mock_persist.call_args
                                assert persist_args[0][1]["status"] == "pending"


# ============================================================================
# Test: Group creation with config application failure
# ============================================================================


def test_create_protection_group_with_launch_config_failure():
    """
    Test protection group creation when launch config application fails.
    
    Validates:
    - Group creation succeeds despite application failure
    - Config status is marked as "failed"
    - Error details are captured in status
    - Response includes launchConfigStatus with failed status
    
    Requirements: 5.1
    """
    # Setup mocks
    mock_table = MagicMock()
    mock_table.put_item.return_value = {}
    
    # Request body with launch config
    body = {
        "groupName": "Test Group Failure",
        "region": "us-east-2",
        "sourceServerIds": ["s-abc123"],
        "launchConfig": {
            "instanceType": "t3.medium"
        }
    }
    
    event = create_api_gateway_event()
    
    with patch.object(
        data_management_handler,
        "get_protection_groups_table",
        return_value=mock_table
    ):
        with patch.object(
            data_management_handler,
            "validate_unique_pg_name",
            return_value=True
        ):
            with patch.object(
                data_management_handler,
                "check_server_conflicts_for_create",
                return_value=[]
            ):
                with patch.object(
                    data_management_handler,
                    "create_drs_client"
                ) as mock_drs_client:
                    mock_drs = MagicMock()
                    mock_drs.describe_source_servers.return_value = {
                        "items": [{"sourceServerID": "s-abc123"}]
                    }
                    mock_drs_client.return_value = mock_drs
                    
                    with patch.object(
                        data_management_handler,
                        "apply_launch_configs_to_group",
                        side_effect=LaunchConfigApplicationError(
                            "DRS API error: ThrottlingException"
                        )
                    ):
                        with patch.object(
                            data_management_handler,
                            "persist_config_status"
                        ) as mock_persist:
                            with patch.object(
                                data_management_handler,
                                "get_current_account_id",
                                return_value="123456789012"
                            ):
                                result = create_protection_group(event, body)
                                
                                # Verify response - group creation should succeed
                                assert result["statusCode"] == 201
                                response_body = json.loads(result["body"])
                                
                                # Verify group was created
                                assert "groupId" in response_body
                                assert response_body["groupName"] == "Test Group Failure"
                                
                                # Verify launch config status shows failed
                                assert "launchConfigStatus" in response_body
                                assert response_body["launchConfigStatus"]["status"] == "failed"
                                assert len(response_body["launchConfigStatus"]["errors"]) > 0
                                assert "DRS API error" in response_body["launchConfigStatus"]["errors"][0]
                                
                                # Verify config status was persisted with failed status
                                mock_persist.assert_called_once()
                                persist_args = mock_persist.call_args
                                assert persist_args[0][1]["status"] == "failed"


# ============================================================================
# Test: Status persistence after creation
# ============================================================================


def test_create_protection_group_status_persistence():
    """
    Test that configuration status is properly persisted to DynamoDB.
    
    Validates:
    - persist_config_status is called with correct group_id
    - Status includes all required fields
    - Status matches apply_launch_configs_to_group result
    
    Requirements: 5.1
    """
    # Setup mocks
    mock_table = MagicMock()
    mock_table.put_item.return_value = {}
    
    mock_apply_result = {
        "status": "ready",
        "appliedServers": 1,
        "failedServers": 0,
        "serverConfigs": {
            "s-abc123": {
                "status": "ready",
                "lastApplied": "2025-02-16T10:30:00Z",
                "configHash": "sha256:abc123",
                "errors": []
            }
        },
        "errors": []
    }
    
    body = {
        "groupName": "Test Persistence",
        "region": "us-east-2",
        "sourceServerIds": ["s-abc123"],
        "launchConfig": {
            "instanceType": "t3.medium"
        }
    }
    
    event = create_api_gateway_event()
    
    with patch.object(
        data_management_handler,
        "get_protection_groups_table",
        return_value=mock_table
    ):
        with patch.object(
            data_management_handler,
            "validate_unique_pg_name",
            return_value=True
        ):
            with patch.object(
                data_management_handler,
                "check_server_conflicts_for_create",
                return_value=[]
            ):
                with patch.object(
                    data_management_handler,
                    "create_drs_client"
                ) as mock_drs_client:
                    mock_drs = MagicMock()
                    mock_drs.describe_source_servers.return_value = {
                        "items": [{"sourceServerID": "s-abc123"}]
                    }
                    mock_drs_client.return_value = mock_drs
                    
                    with patch.object(
                        data_management_handler,
                        "apply_launch_configs_to_group",
                        return_value=mock_apply_result
                    ):
                        with patch.object(
                            data_management_handler,
                            "persist_config_status"
                        ) as mock_persist:
                            with patch.object(
                                data_management_handler,
                                "get_current_account_id",
                                return_value="123456789012"
                            ):
                                result = create_protection_group(event, body)
                                
                                # Verify persist_config_status was called
                                mock_persist.assert_called_once()
                                
                                # Verify the persisted status structure
                                call_args = mock_persist.call_args
                                group_id = call_args[0][0]
                                config_status = call_args[0][1]
                                
                                # Verify group_id is a valid UUID
                                assert len(group_id) == 36  # UUID format
                                
                                # Verify config_status has all required fields
                                assert "status" in config_status
                                assert "lastApplied" in config_status
                                assert "appliedBy" in config_status
                                assert "serverConfigs" in config_status
                                assert "errors" in config_status
                                
                                # Verify status matches apply result
                                assert config_status["status"] == "ready"
                                assert config_status["serverConfigs"] == mock_apply_result["serverConfigs"]
                                assert config_status["errors"] == mock_apply_result["errors"]


# ============================================================================
# Test: Group creation without launch config
# ============================================================================


def test_create_protection_group_without_launch_config():
    """
    Test protection group creation without launch config.
    
    Validates:
    - Group creation succeeds
    - apply_launch_configs_to_group is NOT called
    - launchConfigStatus shows "not_configured"
    
    Requirements: 5.1
    """
    # Setup mocks
    mock_table = MagicMock()
    mock_table.put_item.return_value = {}
    
    # Request body WITHOUT launch config
    body = {
        "groupName": "Test No Config",
        "region": "us-east-2",
        "sourceServerIds": ["s-abc123"]
    }
    
    event = create_api_gateway_event()
    
    with patch.object(
        data_management_handler,
        "get_protection_groups_table",
        return_value=mock_table
    ):
        with patch.object(
            data_management_handler,
            "validate_unique_pg_name",
            return_value=True
        ):
            with patch.object(
                data_management_handler,
                "check_server_conflicts_for_create",
                return_value=[]
            ):
                with patch.object(
                    data_management_handler,
                    "create_drs_client"
                ) as mock_drs_client:
                    mock_drs = MagicMock()
                    mock_drs.describe_source_servers.return_value = {
                        "items": [{"sourceServerID": "s-abc123"}]
                    }
                    mock_drs_client.return_value = mock_drs
                    
                    with patch.object(
                        data_management_handler,
                        "apply_launch_configs_to_group"
                    ) as mock_apply:
                        with patch.object(
                            data_management_handler,
                            "get_current_account_id",
                            return_value="123456789012"
                        ):
                            result = create_protection_group(event, body)
                            
                            # Verify response
                            assert result["statusCode"] == 201
                            response_body = json.loads(result["body"])
                            
                            # Verify group was created
                            assert "groupId" in response_body
                            assert response_body["groupName"] == "Test No Config"
                            
                            # Verify launch config status shows not_configured
                            assert "launchConfigStatus" in response_body
                            assert response_body["launchConfigStatus"]["status"] == "not_configured"
                            
                            # Verify apply_launch_configs_to_group was NOT called
                            mock_apply.assert_not_called()


# ============================================================================
# Test: Cross-account config application
# ============================================================================


def test_create_protection_group_cross_account_config_application():
    """
    Test protection group creation with cross-account config application.
    
    Validates:
    - apply_launch_configs_to_group is called with account_context
    - Account context includes accountId and roleName
    - Config application succeeds for cross-account scenario
    
    Requirements: 5.1
    """
    # Setup mocks
    mock_table = MagicMock()
    mock_table.put_item.return_value = {}
    
    mock_apply_result = {
        "status": "ready",
        "appliedServers": 1,
        "failedServers": 0,
        "serverConfigs": {
            "s-abc123": {
                "status": "ready",
                "lastApplied": "2025-02-16T10:30:00Z",
                "configHash": "sha256:abc123",
                "errors": []
            }
        },
        "errors": []
    }
    
    # Request body with cross-account context
    body = {
        "groupName": "Test Cross Account",
        "region": "us-east-2",
        "sourceServerIds": ["s-abc123"],
        "accountId": "999888777666",  # Different account
        "assumeRoleName": "OrchestrationRole",
        "launchConfig": {
            "instanceType": "t3.medium"
        }
    }
    
    event = create_api_gateway_event()
    
    with patch.object(
        data_management_handler,
        "get_protection_groups_table",
        return_value=mock_table
    ):
        with patch.object(
            data_management_handler,
            "validate_unique_pg_name",
            return_value=True
        ):
            with patch.object(
                data_management_handler,
                "check_server_conflicts_for_create",
                return_value=[]
            ):
                with patch.object(
                    data_management_handler,
                    "create_drs_client"
                ) as mock_drs_client:
                    mock_drs = MagicMock()
                    mock_drs.describe_source_servers.return_value = {
                        "items": [{"sourceServerID": "s-abc123"}]
                    }
                    mock_drs_client.return_value = mock_drs
                    
                    with patch.object(
                        data_management_handler,
                        "apply_launch_configs_to_group",
                        return_value=mock_apply_result
                    ) as mock_apply:
                        with patch.object(
                            data_management_handler,
                            "persist_config_status"
                        ):
                            with patch.object(
                                data_management_handler,
                                "get_current_account_id",
                                return_value="123456789012"  # Current account
                            ):
                                result = create_protection_group(event, body)
                                
                                # Verify response
                                assert result["statusCode"] == 201
                                
                                # Verify apply_launch_configs_to_group was called with account_context
                                mock_apply.assert_called_once()
                                call_args = mock_apply.call_args
                                
                                # Verify account_context is provided for cross-account
                                account_context = call_args[1]["account_context"]
                                assert account_context is not None
                                assert account_context["accountId"] == "999888777666"
                                assert account_context["roleName"] == "OrchestrationRole"
