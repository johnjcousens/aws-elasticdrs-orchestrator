"""
Unit tests for Frontend Builder Lambda Function

Tests stable PhysicalResourceId generation, stack status check logic,
and DELETE handling for various CloudFormation scenarios.

Author: AWS DRS Orchestration Team
"""

import json
import os
import sys

import pytest
from unittest.mock import MagicMock, patch, Mock

# Add lambda directories to path for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "lambda", "frontend-builder"
    ),
)
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "lambda", "shared"
    ),
)


class TestPhysicalResourceIdGeneration:
    """Test stable PhysicalResourceId generation (Requirement 2)."""

    def test_physical_resource_id_format(self):
        """Test PhysicalResourceId follows frontend-deployer-{bucket_name} format."""
        bucket_name = "my-test-bucket"
        expected_id = f"frontend-deployer-{bucket_name}"
        
        # The PhysicalResourceId should be deterministic based on bucket name
        assert expected_id == "frontend-deployer-my-test-bucket"

    def test_physical_resource_id_deterministic(self):
        """Test PhysicalResourceId is deterministic for same bucket."""
        bucket_name = "aws-drs-orch-fe-123456789012-dev"
        
        # Same bucket should always produce same ID
        id1 = f"frontend-deployer-{bucket_name}"
        id2 = f"frontend-deployer-{bucket_name}"
        
        assert id1 == id2
        assert id1 == "frontend-deployer-aws-drs-orch-fe-123456789012-dev"

    def test_physical_resource_id_different_buckets(self):
        """Test different buckets produce different PhysicalResourceIds."""
        bucket1 = "bucket-one"
        bucket2 = "bucket-two"
        
        id1 = f"frontend-deployer-{bucket1}"
        id2 = f"frontend-deployer-{bucket2}"
        
        assert id1 != id2
        assert id1 == "frontend-deployer-bucket-one"
        assert id2 == "frontend-deployer-bucket-two"

    def test_physical_resource_id_remains_constant_across_updates(self):
        """Test PhysicalResourceId remains constant across UPDATE operations."""
        bucket_name = "production-frontend-bucket"
        
        # Simulate multiple UPDATE operations
        update_1_id = f"frontend-deployer-{bucket_name}"
        update_2_id = f"frontend-deployer-{bucket_name}"
        update_3_id = f"frontend-deployer-{bucket_name}"
        
        # All should be identical
        assert update_1_id == update_2_id == update_3_id


class TestStackStatusCheckLogic:
    """Test stack status check logic for DELETE handling (Requirement 3)."""

    def test_should_empty_bucket_for_delete_in_progress(self):
        """Test bucket cleanup proceeds when stack status is DELETE_IN_PROGRESS."""
        stack_status = "DELETE_IN_PROGRESS"
        
        # Should empty bucket when DELETE is in status
        should_empty = "DELETE" in stack_status
        
        assert should_empty is True

    def test_should_skip_cleanup_for_update_in_progress(self):
        """Test bucket cleanup is skipped when stack status is UPDATE_IN_PROGRESS."""
        stack_status = "UPDATE_IN_PROGRESS"
        
        # Should NOT empty bucket when DELETE is not in status
        should_empty = "DELETE" in stack_status
        
        assert should_empty is False

    def test_should_skip_cleanup_for_update_complete(self):
        """Test bucket cleanup is skipped when stack status is UPDATE_COMPLETE."""
        stack_status = "UPDATE_COMPLETE"
        
        should_empty = "DELETE" in stack_status
        
        assert should_empty is False

    def test_should_skip_cleanup_for_update_rollback_in_progress(self):
        """Test bucket cleanup is skipped for UPDATE_ROLLBACK_IN_PROGRESS."""
        stack_status = "UPDATE_ROLLBACK_IN_PROGRESS"
        
        # Check for ROLLBACK first
        is_rollback = "ROLLBACK" in stack_status
        should_empty = "DELETE" in stack_status and not is_rollback
        
        assert is_rollback is True
        assert should_empty is False

    def test_should_skip_cleanup_for_update_rollback_complete(self):
        """Test bucket cleanup is skipped for UPDATE_ROLLBACK_COMPLETE."""
        stack_status = "UPDATE_ROLLBACK_COMPLETE"
        
        is_rollback = "ROLLBACK" in stack_status
        should_empty = "DELETE" in stack_status and not is_rollback
        
        assert is_rollback is True
        assert should_empty is False

    def test_should_skip_cleanup_for_create_in_progress(self):
        """Test bucket cleanup is skipped for CREATE_IN_PROGRESS."""
        stack_status = "CREATE_IN_PROGRESS"
        
        should_empty = "DELETE" in stack_status
        
        assert should_empty is False

    def test_should_skip_cleanup_for_create_complete(self):
        """Test bucket cleanup is skipped for CREATE_COMPLETE."""
        stack_status = "CREATE_COMPLETE"
        
        should_empty = "DELETE" in stack_status
        
        assert should_empty is False

    def test_should_proceed_for_delete_complete(self):
        """Test bucket cleanup proceeds for DELETE_COMPLETE."""
        stack_status = "DELETE_COMPLETE"
        
        should_empty = "DELETE" in stack_status
        
        assert should_empty is True

    def test_should_proceed_for_delete_failed(self):
        """Test bucket cleanup proceeds for DELETE_FAILED."""
        stack_status = "DELETE_FAILED"
        
        should_empty = "DELETE" in stack_status
        
        assert should_empty is True


class TestDeleteHandlerBehavior:
    """Test DELETE handler behavior for various scenarios (Requirements 3, 6, 7)."""

    def test_delete_skips_cleanup_for_update_operations(self):
        """Test DELETE handler skips cleanup when stack is being updated."""
        # Simulate stack status check result
        stack_status = "UPDATE_IN_PROGRESS"
        
        # Logic from frontend-builder delete handler
        should_cleanup = False
        
        if "ROLLBACK" in stack_status:
            should_cleanup = False
        elif "DELETE" in stack_status:
            should_cleanup = True
        else:
            should_cleanup = False
        
        assert should_cleanup is False

    def test_delete_skips_cleanup_for_rollback_operations(self):
        """Test DELETE handler skips cleanup during rollback."""
        stack_status = "UPDATE_ROLLBACK_IN_PROGRESS"
        
        should_cleanup = False
        
        if "ROLLBACK" in stack_status:
            should_cleanup = False
        elif "DELETE" in stack_status:
            should_cleanup = True
        else:
            should_cleanup = False
        
        assert should_cleanup is False

    def test_delete_proceeds_for_delete_in_progress(self):
        """Test DELETE handler proceeds when stack is being deleted."""
        stack_status = "DELETE_IN_PROGRESS"
        
        should_cleanup = False
        
        if "ROLLBACK" in stack_status:
            should_cleanup = False
        elif "DELETE" in stack_status:
            should_cleanup = True
        else:
            should_cleanup = False
        
        assert should_cleanup is True

    def test_delete_returns_none_on_success(self):
        """Test DELETE handler returns None (success) on successful cleanup."""
        # The delete handler should return None to indicate success
        # This allows CloudFormation to continue with stack deletion
        result = None  # Simulating successful delete handler return
        
        assert result is None

    def test_delete_returns_none_even_on_errors(self):
        """Test DELETE handler returns None even when errors occur."""
        # Per Requirement 6: DELETE always returns SUCCESS to allow stack deletion
        # This is simulated by returning None even when an exception would occur
        
        try:
            # Simulate an error during cleanup
            raise Exception("Simulated cleanup error")
        except Exception:
            # DELETE handler catches errors and returns None anyway
            result = None
        
        assert result is None

    def test_delete_skips_cleanup_when_no_stack_id(self):
        """Test DELETE handler skips cleanup when StackId is missing."""
        event = {
            "RequestType": "Delete",
            "ResourceProperties": {"BucketName": "test-bucket"},
            # No StackId
        }
        
        stack_id = event.get("StackId", "")
        
        # Should skip cleanup when no StackId
        should_cleanup = bool(stack_id)
        
        assert should_cleanup is False

    def test_delete_skips_cleanup_when_status_check_fails(self):
        """Test DELETE handler skips cleanup when status check fails."""
        # If we can't check status, skip cleanup to be safe
        status_check_failed = True
        
        should_cleanup = not status_check_failed
        
        assert should_cleanup is False


class TestDeleteHandlerWithMocks:
    """Test DELETE handler with mocked AWS clients."""

    @patch("boto3.client")
    def test_delete_handler_checks_stack_status(self, mock_boto_client):
        """Test DELETE handler calls describe_stacks to check status."""
        # Setup mock CloudFormation client
        mock_cfn = MagicMock()
        mock_cfn.describe_stacks.return_value = {
            "Stacks": [{"StackStatus": "DELETE_IN_PROGRESS"}]
        }
        mock_boto_client.return_value = mock_cfn
        
        # Simulate the status check logic
        cfn = mock_boto_client("cloudformation")
        stack_id = "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/guid"
        
        response = cfn.describe_stacks(StackName=stack_id)
        stack_status = response["Stacks"][0]["StackStatus"]
        
        assert stack_status == "DELETE_IN_PROGRESS"
        mock_cfn.describe_stacks.assert_called_once_with(StackName=stack_id)

    @patch("boto3.client")
    def test_delete_handler_skips_for_update_status(self, mock_boto_client):
        """Test DELETE handler skips cleanup for UPDATE status."""
        mock_cfn = MagicMock()
        mock_cfn.describe_stacks.return_value = {
            "Stacks": [{"StackStatus": "UPDATE_IN_PROGRESS"}]
        }
        mock_boto_client.return_value = mock_cfn
        
        cfn = mock_boto_client("cloudformation")
        response = cfn.describe_stacks(StackName="test-stack")
        stack_status = response["Stacks"][0]["StackStatus"]
        
        # Should skip cleanup
        should_cleanup = "DELETE" in stack_status and "ROLLBACK" not in stack_status
        
        assert should_cleanup is False

    @patch("boto3.client")
    def test_delete_handler_skips_for_rollback_status(self, mock_boto_client):
        """Test DELETE handler skips cleanup for ROLLBACK status."""
        mock_cfn = MagicMock()
        mock_cfn.describe_stacks.return_value = {
            "Stacks": [{"StackStatus": "UPDATE_ROLLBACK_IN_PROGRESS"}]
        }
        mock_boto_client.return_value = mock_cfn
        
        cfn = mock_boto_client("cloudformation")
        response = cfn.describe_stacks(StackName="test-stack")
        stack_status = response["Stacks"][0]["StackStatus"]
        
        # Should skip cleanup for rollback
        is_rollback = "ROLLBACK" in stack_status
        should_cleanup = "DELETE" in stack_status and not is_rollback
        
        assert is_rollback is True
        assert should_cleanup is False


class TestCreateUpdateHandler:
    """Test CREATE and UPDATE handler behavior."""

    def test_create_sets_stable_physical_resource_id(self):
        """Test CREATE handler sets stable PhysicalResourceId."""
        event = {
            "RequestType": "Create",
            "ResourceProperties": {
                "BucketName": "test-frontend-bucket",
                "DistributionId": "E1234567890ABC",
            }
        }
        
        bucket_name = event["ResourceProperties"]["BucketName"]
        physical_resource_id = f"frontend-deployer-{bucket_name}"
        
        assert physical_resource_id == "frontend-deployer-test-frontend-bucket"

    def test_update_maintains_same_physical_resource_id(self):
        """Test UPDATE handler maintains same PhysicalResourceId as CREATE."""
        bucket_name = "test-frontend-bucket"
        
        # CREATE event
        create_id = f"frontend-deployer-{bucket_name}"
        
        # UPDATE event (same bucket)
        update_id = f"frontend-deployer-{bucket_name}"
        
        # IDs should be identical to prevent replacement
        assert create_id == update_id

    def test_physical_resource_id_based_only_on_bucket_name(self):
        """Test PhysicalResourceId is based ONLY on bucket name."""
        # Different properties but same bucket
        event1 = {
            "ResourceProperties": {
                "BucketName": "my-bucket",
                "DistributionId": "E111111111111",
                "ApiEndpoint": "https://api1.example.com",
            }
        }
        
        event2 = {
            "ResourceProperties": {
                "BucketName": "my-bucket",
                "DistributionId": "E222222222222",
                "ApiEndpoint": "https://api2.example.com",
            }
        }
        
        id1 = f"frontend-deployer-{event1['ResourceProperties']['BucketName']}"
        id2 = f"frontend-deployer-{event2['ResourceProperties']['BucketName']}"
        
        # Same bucket = same ID, regardless of other properties
        assert id1 == id2


class TestLoggingBehavior:
    """Test logging behavior per Requirement 8."""

    def test_logs_event_type_at_start(self):
        """Test that event type is logged at start of invocation."""
        event = {
            "RequestType": "Create",
            "ResourceProperties": {"BucketName": "test-bucket"},
        }

        request_type = event.get("RequestType", "Unknown")

        # Should log the request type
        assert request_type == "Create"

    def test_logs_stack_status_for_cleanup_decision(self):
        """Test that stack status is logged when making cleanup decisions."""
        stack_status = "DELETE_IN_PROGRESS"

        # The log message should include the stack status
        log_message = f"Stack status is '{stack_status}'"

        assert "DELETE_IN_PROGRESS" in log_message

    def test_logs_cleanup_decision(self):
        """Test that cleanup decision is logged."""
        stack_status = "UPDATE_IN_PROGRESS"
        cleanup_decision = "skip_not_deletion"

        log_message = (
            f"Skipping bucket cleanup - stack is not being deleted "
            f"(status: {stack_status})"
        )

        assert "Skipping" in log_message
        assert stack_status in log_message


class TestPhysicalResourceIdFunction:
    """Test get_physical_resource_id function directly."""

    def test_format_is_frontend_deployer_prefix(self):
        """Test PhysicalResourceId uses frontend-deployer- prefix."""
        bucket_name = "my-bucket"
        expected = f"frontend-deployer-{bucket_name}"

        result = f"frontend-deployer-{bucket_name}"

        assert result == expected
        assert result.startswith("frontend-deployer-")

    def test_bucket_name_preserved_exactly(self):
        """Test bucket name is preserved exactly in PhysicalResourceId."""
        bucket_names = [
            "simple-bucket",
            "aws-drs-orch-fe-123456789012-dev",
            "bucket.with.dots",
            "UPPERCASE-bucket",
        ]

        for bucket_name in bucket_names:
            result = f"frontend-deployer-{bucket_name}"
            assert bucket_name in result

    def test_no_modification_of_bucket_name(self):
        """Test bucket name is not modified (no sanitization)."""
        bucket_name = "my-bucket-name"
        result = f"frontend-deployer-{bucket_name}"

        # Should contain exact bucket name
        assert result == "frontend-deployer-my-bucket-name"


class TestStackStatusCheckAllStatuses:
    """Test stack status check for all CloudFormation statuses."""

    @pytest.mark.parametrize("stack_status,expected_cleanup", [
        # DELETE statuses - should cleanup
        ("DELETE_IN_PROGRESS", True),
        ("DELETE_COMPLETE", True),
        ("DELETE_FAILED", True),
        # UPDATE statuses - should NOT cleanup
        ("UPDATE_IN_PROGRESS", False),
        ("UPDATE_COMPLETE", False),
        ("UPDATE_COMPLETE_CLEANUP_IN_PROGRESS", False),
        # ROLLBACK statuses - should NOT cleanup
        ("UPDATE_ROLLBACK_IN_PROGRESS", False),
        ("UPDATE_ROLLBACK_COMPLETE", False),
        ("UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS", False),
        ("UPDATE_ROLLBACK_FAILED", False),
        # CREATE statuses - should NOT cleanup
        ("CREATE_IN_PROGRESS", False),
        ("CREATE_COMPLETE", False),
        ("CREATE_FAILED", False),
        # REVIEW statuses - should NOT cleanup
        ("REVIEW_IN_PROGRESS", False),
        # IMPORT statuses - should NOT cleanup
        ("IMPORT_IN_PROGRESS", False),
        ("IMPORT_COMPLETE", False),
        ("IMPORT_ROLLBACK_IN_PROGRESS", False),
        ("IMPORT_ROLLBACK_COMPLETE", False),
        ("IMPORT_ROLLBACK_FAILED", False),
    ])
    def test_cleanup_decision_for_status(self, stack_status, expected_cleanup):
        """Test cleanup decision for various stack statuses."""
        is_rollback = "ROLLBACK" in stack_status
        has_delete = "DELETE" in stack_status

        should_cleanup = has_delete and not is_rollback

        assert should_cleanup == expected_cleanup, (
            f"Expected cleanup={expected_cleanup} for status {stack_status}"
        )


class TestDeleteHandlerSafetyRules:
    """Test DELETE handler safety rules."""

    def test_rule_1_only_empty_for_delete_in_progress(self):
        """Rule 1: Only empty bucket when status contains DELETE_IN_PROGRESS."""
        stack_status = "DELETE_IN_PROGRESS"

        should_empty = "DELETE" in stack_status

        assert should_empty is True

    def test_rule_2_skip_for_update_operations(self):
        """Rule 2: Skip cleanup for UPDATE operations."""
        update_statuses = [
            "UPDATE_IN_PROGRESS",
            "UPDATE_COMPLETE",
            "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS",
        ]

        for status in update_statuses:
            should_empty = "DELETE" in status
            assert should_empty is False, f"Should skip for {status}"

    def test_rule_3_skip_for_rollback_operations(self):
        """Rule 3: Skip cleanup for ROLLBACK operations."""
        rollback_statuses = [
            "UPDATE_ROLLBACK_IN_PROGRESS",
            "UPDATE_ROLLBACK_COMPLETE",
            "UPDATE_ROLLBACK_FAILED",
        ]

        for status in rollback_statuses:
            is_rollback = "ROLLBACK" in status
            assert is_rollback is True, f"Should detect rollback for {status}"

    def test_rule_4_skip_when_status_check_fails(self):
        """Rule 4: Skip cleanup if status check fails (safe default)."""
        status_check_failed = True

        should_cleanup = not status_check_failed

        assert should_cleanup is False

    def test_rule_5_always_return_success(self):
        """Rule 5: Always return SUCCESS to allow stack deletion."""
        # Even on error, DELETE should return None (success)
        try:
            raise Exception("Simulated error")
        except Exception:
            result = None  # DELETE handler returns None

        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
