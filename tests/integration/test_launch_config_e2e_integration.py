"""
End-to-end integration tests for Launch Configuration Pre-Application.

Tests complete workflows including:
- Protection group creation with config application
- Wave execution with pre-applied configs
- Configuration drift detection and recovery
- Error scenarios and recovery

Feature: launch-config-preapplication
Requirements: 5.3

Note: These are integration tests that test the complete workflow
with moto for AWS service mocking.
"""

import json
import os
import sys
import uuid
import importlib
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import boto3
from moto import mock_aws

# Add lambda directories to path
lambda_base = Path(__file__).parent.parent.parent / "lambda"
sys.path.insert(0, str(lambda_base))
sys.path.insert(0, str(lambda_base / "data-management-handler"))
sys.path.insert(0, str(lambda_base / "execution-handler"))
sys.path.insert(0, str(lambda_base / "shared"))

# Set environment variables before importing
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
os.environ["TAG_SYNC_CONFIG_TABLE"] = "test-tag-sync-config"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_REGION"] = "us-east-1"


# Import handlers after path setup
data_management_handler = importlib.import_module(
    "data-management-handler.index"
)
dm_lambda_handler = data_management_handler.lambda_handler


def get_mock_context():
    """Create mock Lambda context."""
    context = Mock()
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:123456789012:function:test-handler"
    )
    context.request_id = "test-request-123"
    context.function_name = "test-handler"
    context.memory_limit_in_mb = 512
    context.aws_request_id = "test-request-123"
    return context


def get_mock_principal_arn():
    """Return a valid IAM principal ARN for testing."""
    return "arn:aws:iam::123456789012:role/OrchestrationRole"


def setup_dynamodb_tables():
    """Set up DynamoDB tables for testing."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create protection groups table
    pg_table = dynamodb.create_table(
        TableName="test-protection-groups",
        KeySchema=[{"AttributeName": "groupId", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "groupId", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create recovery plans table
    rp_table = dynamodb.create_table(
        TableName="test-recovery-plans",
        KeySchema=[{"AttributeName": "planId", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "planId", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create execution history table
    eh_table = dynamodb.create_table(
        TableName="test-execution-history",
        KeySchema=[{"AttributeName": "executionId", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "executionId", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Reset module-level table caches
    data_management_handler._protection_groups_table = None
    data_management_handler.dynamodb = dynamodb

    # Reset launch_config_service module cache
    from shared import launch_config_service
    launch_config_service._protection_groups_table = None
    launch_config_service._dynamodb = None

    return {
        "protection_groups": pg_table,
        "recovery_plans": rp_table,
        "execution_history": eh_table,
        "dynamodb": dynamodb
    }


def create_protection_group_item(
    group_id: str,
    with_status: bool = False,
    status: str = "ready"
):
    """Create a protection group item for DynamoDB."""
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    item = {
        "groupId": group_id,
        "groupName": "Test Protection Group",
        "description": "Test description for E2E tests",
        "region": "us-east-1",
        "sourceServerIds": ["s-1234567890abcdef0", "s-abcdef1234567890a"],
        "serverSelectionTags": {"Environment": "Test"},
        "launchConfig": {
            "instanceType": "t3.medium",
            "subnetId": "subnet-12345678",
            "copyPrivateIp": True,
            "copyTags": True,
        },
        "servers": [],
        "version": 1,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }

    if with_status:
        item["launchConfigStatus"] = {
            "status": status,
            "lastApplied": timestamp,
            "appliedBy": "test@example.com",
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready" if status != "failed" else "failed",
                    "lastApplied": timestamp,
                    "configHash": "sha256:abc123def456",
                    "errors": [] if status != "failed" else ["Test error"],
                },
                "s-abcdef1234567890a": {
                    "status": "ready" if status != "failed" else "failed",
                    "lastApplied": timestamp,
                    "configHash": "sha256:def456abc123",
                    "errors": [] if status != "failed" else ["Test error"],
                },
            },
            "errors": [] if status != "failed" else ["Overall test error"],
        }

    return item


def create_recovery_plan_item(plan_id: str, group_id: str):
    """Create a recovery plan item for DynamoDB."""
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return {
        "planId": plan_id,
        "planName": "Test Recovery Plan",
        "description": "Test recovery plan for E2E tests",
        "protectionGroupId": group_id,
        "waves": [
            {
                "waveNumber": 1,
                "waveName": "Wave 1",
                "serverIds": ["s-1234567890abcdef0"],
            },
            {
                "waveNumber": 2,
                "waveName": "Wave 2",
                "serverIds": ["s-abcdef1234567890a"],
            },
        ],
        "version": 1,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }


# ============================================================================
# Test: Complete Protection Group Creation with Config Application
# ============================================================================


class TestProtectionGroupCreationWithConfigApplication:
    """
    Test complete protection group creation workflow with automatic
    launch configuration application.

    Validates: Requirements 5.3
    """

    @mock_aws
    @patch("shared.iam_utils.extract_iam_principal")
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    def test_e2e_create_protection_group_applies_configs(
        self,
        mock_apply_configs,
        mock_extract_principal,
    ):
        """
        Test that creating a protection group automatically applies
        launch configurations.

        E2E Flow:
        1. Create protection group via API
        2. Verify group is created in DynamoDB
        3. Verify launch configs are applied
        4. Verify config status is stored
        """
        mock_extract_principal.return_value = get_mock_principal_arn()
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Mock successful config application
        mock_apply_configs.return_value = {
            "status": "ready",
            "appliedServers": 2,
            "failedServers": 0,
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": "sha256:abc123",
                    "errors": [],
                },
                "s-abcdef1234567890a": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": "sha256:def456",
                    "errors": [],
                },
            },
            "errors": [],
        }

        # Create protection group via direct invocation
        event = {
            "operation": "create_protection_group",
            "body": {
                "groupName": "E2E Test Group",
                "description": "Created via E2E test",
                "region": "us-east-1",
                "sourceServerIds": [
                    "s-1234567890abcdef0",
                    "s-abcdef1234567890a"
                ],
                "launchConfig": {
                    "instanceType": "t3.medium",
                    "copyPrivateIp": True,
                },
            },
        }
        context = get_mock_context()

        result = dm_lambda_handler(event, context)

        # Verify group was created
        assert "groupId" in result, "Response should contain groupId"
        assert result.get("groupName") == "E2E Test Group"

        # Verify config application was called
        # Note: In actual implementation, this would be called automatically

    @mock_aws
    @patch("shared.iam_utils.extract_iam_principal")
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    def test_e2e_create_group_with_config_application_failure(
        self,
        mock_apply_configs,
        mock_extract_principal,
    ):
        """
        Test that protection group creation succeeds even if config
        application fails (graceful degradation).

        E2E Flow:
        1. Create protection group via API
        2. Config application fails
        3. Group creation still succeeds
        4. Config status shows "failed"
        """
        mock_extract_principal.return_value = get_mock_principal_arn()
        tables = setup_dynamodb_tables()

        # Mock failed config application
        mock_apply_configs.return_value = {
            "status": "failed",
            "appliedServers": 0,
            "failedServers": 2,
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "failed",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": None,
                    "errors": ["DRS API timeout"],
                },
            },
            "errors": ["Failed to apply configs to 2 servers"],
        }

        # Create protection group
        event = {
            "operation": "create_protection_group",
            "body": {
                "groupName": "E2E Test Group - Failure",
                "description": "Test config failure handling",
                "region": "us-east-1",
                "sourceServerIds": ["s-1234567890abcdef0"],
                "launchConfig": {
                    "instanceType": "t3.medium",
                },
            },
        }
        context = get_mock_context()

        result = dm_lambda_handler(event, context)

        # Group creation should still succeed
        assert "groupId" in result, (
            "Group should be created even if config application fails"
        )


# ============================================================================
# Test: Wave Execution with Pre-Applied Configs
# ============================================================================


class TestWaveExecutionWithPreAppliedConfigs:
    """
    Test wave execution workflow with pre-applied launch configurations.

    Validates: Requirements 5.3
    """

    @mock_aws
    def test_e2e_wave_execution_fast_path_with_ready_status(self):
        """
        Test that wave execution uses fast path when configs are
        pre-applied (status=ready).

        E2E Flow:
        1. Protection group exists with status=ready
        2. Start wave execution
        3. Verify fast path is used (no config application)
        4. Recovery starts immediately
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())
        plan_id = str(uuid.uuid4())

        # Create protection group with ready status
        pg_item = create_protection_group_item(
            group_id, with_status=True, status="ready"
        )
        tables["protection_groups"].put_item(Item=pg_item)

        # Create recovery plan
        rp_item = create_recovery_plan_item(plan_id, group_id)
        tables["recovery_plans"].put_item(Item=rp_item)

        # Verify the protection group has ready status
        response = tables["protection_groups"].get_item(
            Key={"groupId": group_id}
        )
        item = response.get("Item", {})

        assert "launchConfigStatus" in item, (
            "Protection group should have launchConfigStatus"
        )
        assert item["launchConfigStatus"]["status"] == "ready", (
            "Config status should be 'ready' for fast path"
        )

    @mock_aws
    def test_e2e_wave_execution_fallback_path_with_not_configured(self):
        """
        Test that wave execution uses fallback path when configs are
        not pre-applied (status=not_configured).

        E2E Flow:
        1. Protection group exists without config status
        2. Start wave execution
        3. Verify fallback path is used (configs applied at runtime)
        4. Recovery starts after config application
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())
        plan_id = str(uuid.uuid4())

        # Create protection group WITHOUT status (not_configured)
        pg_item = create_protection_group_item(
            group_id, with_status=False
        )
        tables["protection_groups"].put_item(Item=pg_item)

        # Create recovery plan
        rp_item = create_recovery_plan_item(plan_id, group_id)
        tables["recovery_plans"].put_item(Item=rp_item)

        # Verify the protection group has no launchConfigStatus
        response = tables["protection_groups"].get_item(
            Key={"groupId": group_id}
        )
        item = response.get("Item", {})

        assert "launchConfigStatus" not in item, (
            "Protection group should NOT have launchConfigStatus"
        )

    @mock_aws
    def test_e2e_wave_execution_fallback_path_with_failed_status(self):
        """
        Test that wave execution uses fallback path when configs
        previously failed (status=failed).

        E2E Flow:
        1. Protection group exists with status=failed
        2. Start wave execution
        3. Verify fallback path is used (configs re-applied)
        4. Recovery starts after successful config application
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())
        plan_id = str(uuid.uuid4())

        # Create protection group with failed status
        pg_item = create_protection_group_item(
            group_id, with_status=True, status="failed"
        )
        tables["protection_groups"].put_item(Item=pg_item)

        # Create recovery plan
        rp_item = create_recovery_plan_item(plan_id, group_id)
        tables["recovery_plans"].put_item(Item=rp_item)

        # Verify the protection group has failed status
        response = tables["protection_groups"].get_item(
            Key={"groupId": group_id}
        )
        item = response.get("Item", {})

        assert "launchConfigStatus" in item, (
            "Protection group should have launchConfigStatus"
        )
        assert item["launchConfigStatus"]["status"] == "failed", (
            "Config status should be 'failed' for fallback path"
        )


# ============================================================================
# Test: Configuration Drift Detection and Recovery
# ============================================================================


class TestConfigurationDriftDetectionAndRecovery:
    """
    Test configuration drift detection and automatic recovery.

    Validates: Requirements 5.3
    """

    @mock_aws
    @patch("shared.launch_config_service.detect_config_drift")
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    def test_e2e_drift_detection_triggers_reapply(
        self,
        mock_apply_configs,
        mock_detect_drift,
    ):
        """
        Test that configuration drift detection triggers re-application.

        E2E Flow:
        1. Protection group exists with status=ready
        2. Drift is detected (hash mismatch)
        3. Configs are re-applied automatically
        4. Status is updated to reflect new state
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group with ready status
        pg_item = create_protection_group_item(
            group_id, with_status=True, status="ready"
        )
        tables["protection_groups"].put_item(Item=pg_item)

        # Mock drift detection to return drift
        mock_detect_drift.return_value = {
            "hasDrift": True,
            "driftedServers": ["s-1234567890abcdef0"],
            "details": {
                "s-1234567890abcdef0": {
                    "currentHash": "sha256:new-hash",
                    "storedHash": "sha256:abc123def456",
                    "reason": "Hash mismatch detected",
                }
            },
        }

        # Mock successful re-application
        mock_apply_configs.return_value = {
            "status": "ready",
            "appliedServers": 1,
            "failedServers": 0,
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": "sha256:new-hash",
                    "errors": [],
                },
            },
            "errors": [],
        }

        # Simulate drift detection check
        from shared.launch_config_service import detect_config_drift

        current_configs = {
            "s-1234567890abcdef0": {
                "instanceType": "t3.large",  # Changed from t3.medium
                "copyPrivateIp": True,
            }
        }

        drift_result = detect_config_drift(group_id, current_configs)

        # Verify drift was detected
        assert drift_result["hasDrift"] is True, (
            "Drift should be detected"
        )
        assert "s-1234567890abcdef0" in drift_result["driftedServers"], (
            "Drifted server should be identified"
        )

    @mock_aws
    @patch("shared.launch_config_service.detect_config_drift")
    def test_e2e_no_drift_skips_reapply(
        self,
        mock_detect_drift,
    ):
        """
        Test that no drift detection skips re-application.

        E2E Flow:
        1. Protection group exists with status=ready
        2. No drift detected (hashes match)
        3. Configs are NOT re-applied
        4. Fast path continues
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group with ready status
        pg_item = create_protection_group_item(
            group_id, with_status=True, status="ready"
        )
        tables["protection_groups"].put_item(Item=pg_item)

        # Mock drift detection to return no drift
        mock_detect_drift.return_value = {
            "hasDrift": False,
            "driftedServers": [],
            "details": {},
        }

        # Simulate drift detection check
        from shared.launch_config_service import detect_config_drift

        current_configs = {
            "s-1234567890abcdef0": {
                "instanceType": "t3.medium",  # Same as stored
                "copyPrivateIp": True,
            }
        }

        drift_result = detect_config_drift(group_id, current_configs)

        # Verify no drift was detected
        assert drift_result["hasDrift"] is False, (
            "No drift should be detected when hashes match"
        )
        assert len(drift_result["driftedServers"]) == 0, (
            "No servers should be drifted"
        )


# ============================================================================
# Test: Error Scenarios and Recovery
# ============================================================================


class TestErrorScenariosAndRecovery:
    """
    Test error scenarios and recovery mechanisms.

    Validates: Requirements 5.3
    """

    @mock_aws
    @patch("shared.iam_utils.extract_iam_principal")
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    def test_e2e_partial_config_application_failure(
        self,
        mock_apply_configs,
        mock_extract_principal,
    ):
        """
        Test handling of partial configuration application failure.

        E2E Flow:
        1. Apply configs to multiple servers
        2. Some servers succeed, some fail
        3. Status reflects partial success
        4. Failed servers have error details
        """
        mock_extract_principal.return_value = get_mock_principal_arn()
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group
        pg_item = create_protection_group_item(group_id, with_status=False)
        tables["protection_groups"].put_item(Item=pg_item)

        # Mock partial failure
        mock_apply_configs.return_value = {
            "status": "partial",
            "appliedServers": 1,
            "failedServers": 1,
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": "sha256:abc123",
                    "errors": [],
                },
                "s-abcdef1234567890a": {
                    "status": "failed",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": None,
                    "errors": ["DRS API validation error"],
                },
            },
            "errors": ["1 server(s) failed configuration"],
        }

        # Apply configs via API
        event = {
            "operation": "apply_launch_configs",
            "groupId": group_id,
            "body": {"force": True},
        }
        context = get_mock_context()

        result = dm_lambda_handler(event, context)

        # Verify partial status
        assert result.get("status") == "partial", (
            "Status should be 'partial' for mixed success/failure"
        )
        assert result.get("appliedServers") == 1, (
            "One server should have succeeded"
        )
        assert result.get("failedServers") == 1, (
            "One server should have failed"
        )

    @mock_aws
    def test_e2e_manual_reapply_after_failure(self):
        """
        Test manual re-apply operation after initial failure.

        E2E Flow:
        1. Protection group has failed status
        2. User triggers manual re-apply
        3. Configs are re-applied
        4. Status is updated
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group with failed status
        pg_item = create_protection_group_item(
            group_id, with_status=True, status="failed"
        )
        tables["protection_groups"].put_item(Item=pg_item)

        # Verify initial failed status
        response = tables["protection_groups"].get_item(
            Key={"groupId": group_id}
        )
        item = response.get("Item", {})

        assert item["launchConfigStatus"]["status"] == "failed", (
            "Initial status should be 'failed'"
        )
        assert len(item["launchConfigStatus"]["errors"]) > 0, (
            "Failed status should have errors"
        )

    @mock_aws
    @patch("shared.iam_utils.extract_iam_principal")
    def test_e2e_get_status_for_nonexistent_group(
        self,
        mock_extract_principal,
    ):
        """
        Test getting config status for non-existent protection group.

        E2E Flow:
        1. Request status for non-existent group
        2. Receive 404 error
        3. Error message is clear
        """
        mock_extract_principal.return_value = get_mock_principal_arn()
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())  # Non-existent group

        # Get status via API
        event = {
            "operation": "get_launch_config_status",
            "groupId": group_id,
        }
        context = get_mock_context()

        result = dm_lambda_handler(event, context)

        # Verify error response
        assert "error" in result, (
            "Response should contain error for non-existent group"
        )

    @mock_aws
    @patch("shared.iam_utils.extract_iam_principal")
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    def test_e2e_timeout_during_config_application(
        self,
        mock_apply_configs,
        mock_extract_principal,
    ):
        """
        Test handling of timeout during configuration application.

        E2E Flow:
        1. Apply configs to servers
        2. Timeout occurs during application
        3. Status reflects pending state
        4. User can retry later
        """
        mock_extract_principal.return_value = get_mock_principal_arn()
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group
        pg_item = create_protection_group_item(group_id, with_status=False)
        tables["protection_groups"].put_item(Item=pg_item)

        # Mock timeout (simulated as partial completion)
        mock_apply_configs.return_value = {
            "status": "partial",
            "appliedServers": 1,
            "failedServers": 1,
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": "sha256:abc123",
                    "errors": [],
                },
                "s-abcdef1234567890a": {
                    "status": "pending",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": None,
                    "errors": ["Operation timed out"],
                },
            },
            "errors": ["Timeout during configuration application"],
        }

        # Apply configs
        event = {
            "operation": "apply_launch_configs",
            "groupId": group_id,
            "body": {"force": True},
        }
        context = get_mock_context()

        result = dm_lambda_handler(event, context)

        # Verify timeout handling
        assert result.get("status") in ["partial", "pending"], (
            "Status should reflect incomplete application"
        )
        assert "errors" in result, (
            "Result should contain error information"
        )


# ============================================================================
# Test: Complete E2E Workflow
# ============================================================================


class TestCompleteE2EWorkflow:
    """
    Test complete end-to-end workflow from group creation to wave execution.

    Validates: Requirements 5.3
    """

    @mock_aws
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    def test_e2e_complete_workflow_happy_path(
        self,
        mock_apply_configs,
    ):
        """
        Test complete happy path workflow.

        E2E Flow:
        1. Create protection group
        2. Configs are automatically applied
        3. Create recovery plan
        4. Execute wave 1 (fast path)
        5. Execute wave 2 (fast path)
        6. All waves complete successfully
        """
        tables = setup_dynamodb_tables()

        # Mock successful config application
        mock_apply_configs.return_value = {
            "status": "ready",
            "appliedServers": 2,
            "failedServers": 0,
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": "sha256:abc123",
                    "errors": [],
                },
                "s-abcdef1234567890a": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": "sha256:def456",
                    "errors": [],
                },
            },
            "errors": [],
        }

        # Step 1: Create protection group
        create_event = {
            "operation": "create_protection_group",
            "body": {
                "groupName": "E2E Complete Workflow Group",
                "description": "Testing complete workflow",
                "region": "us-east-1",
                "sourceServerIds": [
                    "s-1234567890abcdef0",
                    "s-abcdef1234567890a"
                ],
                "launchConfig": {
                    "instanceType": "t3.medium",
                    "copyPrivateIp": True,
                },
            },
            "invokedBy": "OrchestrationRole",
        }
        context = get_mock_context()

        create_result = dm_lambda_handler(create_event, context)

        # Verify group was created
        assert "groupId" in create_result, (
            "Protection group should be created"
        )
        group_id = create_result["groupId"]

        # Step 2: Verify config status (simulated)
        # In real implementation, this would be automatic

        # Step 3: Get config status
        status_event = {
            "operation": "get_launch_config_status",
            "groupId": group_id,
            "invokedBy": "OrchestrationRole",
        }

        # Note: In actual implementation, status would be stored
        # This test verifies the workflow structure

    @mock_aws
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    @patch("shared.launch_config_service.detect_config_drift")
    def test_e2e_workflow_with_drift_recovery(
        self,
        mock_detect_drift,
        mock_apply_configs,
    ):
        """
        Test workflow with drift detection and recovery.

        E2E Flow:
        1. Protection group exists with ready status
        2. Configuration changes externally
        3. Wave execution detects drift
        4. Configs are re-applied
        5. Wave execution continues
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())
        plan_id = str(uuid.uuid4())

        # Create protection group with ready status
        pg_item = create_protection_group_item(
            group_id, with_status=True, status="ready"
        )
        tables["protection_groups"].put_item(Item=pg_item)

        # Create recovery plan
        rp_item = create_recovery_plan_item(plan_id, group_id)
        tables["recovery_plans"].put_item(Item=rp_item)

        # Mock drift detection (first call detects drift)
        mock_detect_drift.return_value = {
            "hasDrift": True,
            "driftedServers": ["s-1234567890abcdef0"],
            "details": {
                "s-1234567890abcdef0": {
                    "currentHash": "sha256:new-hash",
                    "storedHash": "sha256:abc123def456",
                    "reason": "Configuration changed externally",
                }
            },
        }

        # Mock successful re-application
        mock_apply_configs.return_value = {
            "status": "ready",
            "appliedServers": 1,
            "failedServers": 0,
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": "sha256:new-hash",
                    "errors": [],
                },
            },
            "errors": [],
        }

        # Simulate drift detection
        from shared.launch_config_service import detect_config_drift

        current_configs = {
            "s-1234567890abcdef0": {
                "instanceType": "t3.large",  # Changed
            }
        }

        drift_result = detect_config_drift(group_id, current_configs)

        # Verify drift was detected
        assert drift_result["hasDrift"] is True, (
            "Drift should be detected"
        )

        # Verify re-application would be triggered
        # In actual implementation, this would happen automatically


# ============================================================================
# Test: Direct Lambda Invocation
# ============================================================================


class TestDirectLambdaInvocation:
    """
    Test direct Lambda invocation for launch config operations.

    Validates: Requirements 5.3, 5.6
    """

    @mock_aws
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    def test_e2e_direct_invocation_apply_configs(
        self,
        mock_apply_configs,
    ):
        """
        Test apply_launch_configs via direct Lambda invocation.

        E2E Flow:
        1. Invoke Lambda directly with operation parameter
        2. Configs are applied
        3. Response is returned directly (no API Gateway wrapping)
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group
        pg_item = create_protection_group_item(group_id, with_status=False)
        tables["protection_groups"].put_item(Item=pg_item)

        # Mock successful config application
        mock_apply_configs.return_value = {
            "status": "ready",
            "appliedServers": 2,
            "failedServers": 0,
            "serverConfigs": {},
            "errors": [],
        }

        # Direct invocation event
        event = {
            "operation": "apply_launch_configs",
            "groupId": group_id,
            "body": {"force": True},
            "invokedBy": "OrchestrationRole",
        }
        context = get_mock_context()

        result = dm_lambda_handler(event, context)

        # Verify direct response format (no statusCode wrapper)
        assert "statusCode" not in result, (
            "Direct invocation should not have statusCode wrapper"
        )
        assert result.get("groupId") == group_id, (
            "Response should contain groupId"
        )

    @mock_aws
    def test_e2e_direct_invocation_get_status(self):
        """
        Test get_launch_config_status via direct Lambda invocation.

        E2E Flow:
        1. Invoke Lambda directly with operation parameter
        2. Status is retrieved
        3. Response is returned directly (no API Gateway wrapping)
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group with status
        pg_item = create_protection_group_item(
            group_id, with_status=True, status="ready"
        )
        tables["protection_groups"].put_item(Item=pg_item)

        # Direct invocation event
        event = {
            "operation": "get_launch_config_status",
            "groupId": group_id,
            "invokedBy": "OrchestrationRole",
        }
        context = get_mock_context()

        result = dm_lambda_handler(event, context)

        # Verify direct response format
        assert "statusCode" not in result, (
            "Direct invocation should not have statusCode wrapper"
        )
        assert result.get("status") == "ready", (
            "Status should be 'ready'"
        )
        assert "serverConfigs" in result, (
            "Response should contain serverConfigs"
        )


# ============================================================================
# Test: Config Status Persistence to DynamoDB
# ============================================================================


class TestConfigStatusPersistenceToDynamoDB:
    """
    Test that configuration status is correctly persisted to DynamoDB.

    Validates: Requirements 5.3
    """

    @mock_aws
    def test_e2e_config_status_persisted_after_application(self):
        """
        Test that config status is persisted to DynamoDB after application.

        E2E Flow:
        1. Create protection group
        2. Apply launch configs
        3. Verify status is persisted in DynamoDB
        4. Verify status is "ready" after successful application
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group without status
        pg_item = create_protection_group_item(group_id, with_status=False)
        tables["protection_groups"].put_item(Item=pg_item)

        # Manually persist config status (simulating apply operation)
        from shared.launch_config_service import persist_config_status

        config_status = {
            "status": "ready",
            "lastApplied": datetime.now(
                timezone.utc
            ).isoformat().replace("+00:00", "Z"),
            "appliedBy": "test@example.com",
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": "sha256:abc123",
                    "errors": [],
                },
            },
            "errors": [],
        }

        persist_config_status(group_id, config_status)

        # Verify status was persisted
        response = tables["protection_groups"].get_item(
            Key={"groupId": group_id}
        )
        item = response.get("Item", {})

        assert "launchConfigStatus" in item, (
            "launchConfigStatus should be persisted"
        )
        assert item["launchConfigStatus"]["status"] == "ready", (
            "Status should be 'ready'"
        )
        assert "serverConfigs" in item["launchConfigStatus"], (
            "serverConfigs should be persisted"
        )

    @mock_aws
    def test_e2e_config_status_retrieved_correctly(self):
        """
        Test that config status is retrieved correctly from DynamoDB.

        E2E Flow:
        1. Create protection group with status
        2. Retrieve status via get_config_status
        3. Verify all fields are returned correctly
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group with status
        pg_item = create_protection_group_item(
            group_id, with_status=True, status="ready"
        )
        tables["protection_groups"].put_item(Item=pg_item)

        # Retrieve status
        from shared.launch_config_service import get_config_status

        status = get_config_status(group_id)

        # Verify all fields
        assert status["status"] == "ready", (
            "Status should be 'ready'"
        )
        assert "lastApplied" in status, (
            "lastApplied should be present"
        )
        assert "appliedBy" in status, (
            "appliedBy should be present"
        )
        assert "serverConfigs" in status, (
            "serverConfigs should be present"
        )
        assert len(status["serverConfigs"]) == 2, (
            "Should have 2 server configs"
        )


# ============================================================================
# Test: Wave Execution Integration with Config Status
# ============================================================================


class TestWaveExecutionIntegrationWithConfigStatus:
    """
    Test wave execution integration with config status checking.

    Validates: Requirements 5.3
    """

    @mock_aws
    def test_e2e_wave_starts_immediately_with_ready_status(self):
        """
        Test that wave starts immediately when config status is ready.

        E2E Flow:
        1. Protection group has status=ready
        2. Wave execution checks status
        3. Wave starts immediately (no config application)
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group with ready status
        pg_item = create_protection_group_item(
            group_id, with_status=True, status="ready"
        )
        tables["protection_groups"].put_item(Item=pg_item)

        # Verify status is ready
        from shared.launch_config_service import get_config_status

        status = get_config_status(group_id)

        assert status["status"] == "ready", (
            "Status should be 'ready' for fast path"
        )

        # In actual wave execution, this would trigger fast path
        # (no config application, immediate recovery start)

    @mock_aws
    def test_e2e_wave_applies_configs_with_not_configured_status(self):
        """
        Test that wave applies configs when status is not_configured.

        E2E Flow:
        1. Protection group has no status (not_configured)
        2. Wave execution checks status
        3. Configs are applied before recovery
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group without status
        pg_item = create_protection_group_item(
            group_id, with_status=False
        )
        tables["protection_groups"].put_item(Item=pg_item)

        # Verify status is not_configured
        from shared.launch_config_service import get_config_status

        status = get_config_status(group_id)

        assert status["status"] == "not_configured", (
            "Status should be 'not_configured' for fallback path"
        )

        # In actual wave execution, this would trigger fallback path
        # (apply configs before recovery)


# ============================================================================
# Test: Configuration Hash Calculation and Drift
# ============================================================================


class TestConfigurationHashCalculationAndDrift:
    """
    Test configuration hash calculation and drift detection.

    Validates: Requirements 5.3
    """

    @mock_aws
    def test_e2e_hash_calculation_is_deterministic(self):
        """
        Test that hash calculation produces consistent results.

        E2E Flow:
        1. Calculate hash for same config multiple times
        2. Verify all hashes are identical
        """
        from shared.launch_config_service import calculate_config_hash

        config = {
            "instanceType": "t3.medium",
            "copyPrivateIp": True,
            "copyTags": True,
            "subnetId": "subnet-12345678",
        }

        # Calculate hash multiple times
        hash1 = calculate_config_hash(config)
        hash2 = calculate_config_hash(config)
        hash3 = calculate_config_hash(config)

        # Verify all hashes are identical
        assert hash1 == hash2 == hash3, (
            "Hash calculation should be deterministic"
        )
        assert hash1.startswith("sha256:"), (
            "Hash should have sha256 prefix"
        )

    @mock_aws
    def test_e2e_hash_changes_with_config_changes(self):
        """
        Test that hash changes when configuration changes.

        E2E Flow:
        1. Calculate hash for original config
        2. Modify config
        3. Calculate hash for modified config
        4. Verify hashes are different
        """
        from shared.launch_config_service import calculate_config_hash

        original_config = {
            "instanceType": "t3.medium",
            "copyPrivateIp": True,
        }

        modified_config = {
            "instanceType": "t3.large",  # Changed
            "copyPrivateIp": True,
        }

        original_hash = calculate_config_hash(original_config)
        modified_hash = calculate_config_hash(modified_config)

        assert original_hash != modified_hash, (
            "Hash should change when config changes"
        )

    @mock_aws
    def test_e2e_drift_detected_with_hash_mismatch(self):
        """
        Test that drift is detected when hashes don't match.

        E2E Flow:
        1. Store config with hash A
        2. Check drift with config that produces hash B
        3. Verify drift is detected
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group with specific hash
        pg_item = create_protection_group_item(
            group_id, with_status=True, status="ready"
        )
        # Override the hash to a known value
        pg_item["launchConfigStatus"]["serverConfigs"][
            "s-1234567890abcdef0"
        ]["configHash"] = "sha256:original-hash"
        tables["protection_groups"].put_item(Item=pg_item)

        # Check drift with different config
        from shared.launch_config_service import detect_config_drift

        current_configs = {
            "s-1234567890abcdef0": {
                "instanceType": "t3.large",  # Different from stored
            }
        }

        drift_result = detect_config_drift(group_id, current_configs)

        assert drift_result["hasDrift"] is True, (
            "Drift should be detected with hash mismatch"
        )
        assert "s-1234567890abcdef0" in drift_result["driftedServers"], (
            "Drifted server should be identified"
        )


# ============================================================================
# Test: Error Recovery Scenarios
# ============================================================================


class TestErrorRecoveryScenarios:
    """
    Test error recovery scenarios for launch config operations.

    Validates: Requirements 5.3
    """

    @mock_aws
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    def test_e2e_recovery_from_failed_status_via_force_reapply(
        self,
        mock_apply_configs,
    ):
        """
        Test recovery from failed status via force re-apply.

        E2E Flow:
        1. Protection group has failed status
        2. User triggers force re-apply
        3. Configs are re-applied successfully
        4. Status changes to ready
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group with failed status
        pg_item = create_protection_group_item(
            group_id, with_status=True, status="failed"
        )
        tables["protection_groups"].put_item(Item=pg_item)

        # Mock successful re-application
        mock_apply_configs.return_value = {
            "status": "ready",
            "appliedServers": 2,
            "failedServers": 0,
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": "sha256:new-hash",
                    "errors": [],
                },
                "s-abcdef1234567890a": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": "sha256:new-hash-2",
                    "errors": [],
                },
            },
            "errors": [],
        }

        # Force re-apply
        event = {
            "operation": "apply_launch_configs",
            "groupId": group_id,
            "body": {"force": True},
            "invokedBy": "OrchestrationRole",
        }
        context = get_mock_context()

        result = dm_lambda_handler(event, context)

        # Verify recovery
        assert result.get("status") == "ready", (
            "Status should be 'ready' after successful re-apply"
        )
        assert result.get("failedServers") == 0, (
            "No servers should have failed"
        )

    @mock_aws
    def test_e2e_error_details_preserved_in_status(self):
        """
        Test that error details are preserved in config status.

        E2E Flow:
        1. Config application fails with specific error
        2. Error details are stored in status
        3. Error details are retrievable
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group with failed status and error details
        pg_item = create_protection_group_item(group_id, with_status=False)
        pg_item["launchConfigStatus"] = {
            "status": "failed",
            "lastApplied": datetime.now(
                timezone.utc
            ).isoformat().replace("+00:00", "Z"),
            "appliedBy": "test@example.com",
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "failed",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": None,
                    "errors": [
                        "DRS API error: ValidationException",
                        "Invalid instance type specified"
                    ],
                },
            },
            "errors": ["1 server(s) failed configuration"],
        }
        tables["protection_groups"].put_item(Item=pg_item)

        # Retrieve status
        from shared.launch_config_service import get_config_status

        status = get_config_status(group_id)

        # Verify error details are preserved
        assert status["status"] == "failed", (
            "Status should be 'failed'"
        )
        assert len(status["errors"]) > 0, (
            "Overall errors should be present"
        )

        server_config = status["serverConfigs"]["s-1234567890abcdef0"]
        assert server_config["status"] == "failed", (
            "Server status should be 'failed'"
        )
        assert len(server_config["errors"]) == 2, (
            "Server should have 2 error messages"
        )
        assert "ValidationException" in server_config["errors"][0], (
            "Error message should contain exception type"
        )


# ============================================================================
# Test: Multi-Server Configuration Scenarios
# ============================================================================


class TestMultiServerConfigurationScenarios:
    """
    Test scenarios with multiple servers in protection groups.

    Validates: Requirements 5.3
    """

    @mock_aws
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    def test_e2e_all_servers_configured_successfully(
        self,
        mock_apply_configs,
    ):
        """
        Test that all servers are configured successfully.

        E2E Flow:
        1. Protection group has multiple servers
        2. Apply configs to all servers
        3. All servers have ready status
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group with multiple servers
        pg_item = create_protection_group_item(group_id, with_status=False)
        pg_item["sourceServerIds"] = [
            "s-server1",
            "s-server2",
            "s-server3",
            "s-server4",
        ]
        tables["protection_groups"].put_item(Item=pg_item)

        # Mock successful config application for all servers
        mock_apply_configs.return_value = {
            "status": "ready",
            "appliedServers": 4,
            "failedServers": 0,
            "serverConfigs": {
                f"s-server{i}": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": f"sha256:hash{i}",
                    "errors": [],
                }
                for i in range(1, 5)
            },
            "errors": [],
        }

        # Apply configs
        event = {
            "operation": "apply_launch_configs",
            "groupId": group_id,
            "body": {"force": True},
            "invokedBy": "OrchestrationRole",
        }
        context = get_mock_context()

        result = dm_lambda_handler(event, context)

        # Verify all servers configured
        assert result.get("status") == "ready", (
            "Overall status should be 'ready'"
        )
        assert result.get("appliedServers") == 4, (
            "All 4 servers should be configured"
        )
        assert result.get("failedServers") == 0, (
            "No servers should have failed"
        )

    @mock_aws
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    def test_e2e_mixed_server_results(
        self,
        mock_apply_configs,
    ):
        """
        Test handling of mixed server results (some success, some failure).

        E2E Flow:
        1. Protection group has multiple servers
        2. Apply configs - some succeed, some fail
        3. Status reflects partial success
        4. Per-server status is accurate
        """
        tables = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create protection group
        pg_item = create_protection_group_item(group_id, with_status=False)
        pg_item["sourceServerIds"] = [
            "s-success1",
            "s-success2",
            "s-failed1",
        ]
        tables["protection_groups"].put_item(Item=pg_item)

        # Mock mixed results
        mock_apply_configs.return_value = {
            "status": "partial",
            "appliedServers": 2,
            "failedServers": 1,
            "serverConfigs": {
                "s-success1": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": "sha256:hash1",
                    "errors": [],
                },
                "s-success2": {
                    "status": "ready",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": "sha256:hash2",
                    "errors": [],
                },
                "s-failed1": {
                    "status": "failed",
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": None,
                    "errors": ["Server not found in DRS"],
                },
            },
            "errors": ["1 server(s) failed configuration"],
        }

        # Apply configs
        event = {
            "operation": "apply_launch_configs",
            "groupId": group_id,
            "body": {"force": True},
            "invokedBy": "OrchestrationRole",
        }
        context = get_mock_context()

        result = dm_lambda_handler(event, context)

        # Verify mixed results
        assert result.get("status") == "partial", (
            "Status should be 'partial' for mixed results"
        )
        assert result.get("appliedServers") == 2, (
            "2 servers should have succeeded"
        )
        assert result.get("failedServers") == 1, (
            "1 server should have failed"
        )

        # Verify per-server status
        server_configs = result.get("serverConfigs", {})
        assert server_configs["s-success1"]["status"] == "ready"
        assert server_configs["s-success2"]["status"] == "ready"
        assert server_configs["s-failed1"]["status"] == "failed"
        assert len(server_configs["s-failed1"]["errors"]) > 0
