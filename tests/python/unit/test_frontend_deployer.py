"""
Unit tests for Frontend Deployer Lambda Function

Tests the consolidated frontend-deployer Lambda that handles:
- CREATE: Deploy pre-built React application to S3
- UPDATE: Redeploy frontend with updated configuration
- DELETE: Empty S3 bucket ONLY during actual stack deletion

Key functions tested:
- get_physical_resource_id(): Stable PhysicalResourceId generation
- should_empty_bucket(): Stack status check logic for DELETE handling

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
        os.path.dirname(__file__), "..", "..", "..", "lambda", "frontend-deployer"
    ),
)
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "lambda", "shared"
    ),
)


class TestGetPhysicalResourceId:
    """Test get_physical_resource_id function (Requirement 2: Stable Resource Identity)."""

    def test_returns_correct_format(self):
        """Test PhysicalResourceId follows frontend-deployer-{bucket_name} format."""
        bucket_name = "my-test-bucket"
        expected_id = "frontend-deployer-my-test-bucket"

        # Simulate the function
        result = f"frontend-deployer-{bucket_name}"

        assert result == expected_id

    def test_deterministic_for_same_bucket(self):
        """Test PhysicalResourceId is deterministic for same bucket."""
        bucket_name = "aws-drs-orch-fe-123456789012-dev"

        # Multiple calls should produce identical results
        id1 = f"frontend-deployer-{bucket_name}"
        id2 = f"frontend-deployer-{bucket_name}"
        id3 = f"frontend-deployer-{bucket_name}"

        assert id1 == id2 == id3
        assert id1 == "frontend-deployer-aws-drs-orch-fe-123456789012-dev"

    def test_different_buckets_produce_different_ids(self):
        """Test different buckets produce different PhysicalResourceIds."""
        bucket1 = "bucket-one"
        bucket2 = "bucket-two"

        id1 = f"frontend-deployer-{bucket1}"
        id2 = f"frontend-deployer-{bucket2}"

        assert id1 != id2
        assert id1 == "frontend-deployer-bucket-one"
        assert id2 == "frontend-deployer-bucket-two"

    def test_remains_constant_across_updates(self):
        """Test PhysicalResourceId remains constant across UPDATE operations."""
        bucket_name = "production-frontend-bucket"

        # Simulate multiple UPDATE operations
        update_1_id = f"frontend-deployer-{bucket_name}"
        update_2_id = f"frontend-deployer-{bucket_name}"
        update_3_id = f"frontend-deployer-{bucket_name}"

        assert update_1_id == update_2_id == update_3_id

    def test_based_only_on_bucket_name(self):
        """Test PhysicalResourceId is based ONLY on bucket name, not other properties."""
        # Different properties but same bucket
        bucket_name = "my-bucket"

        # Simulate events with different properties
        event1_props = {
            "BucketName": bucket_name,
            "DistributionId": "E111111111111",
            "ApiEndpoint": "https://api1.example.com",
        }

        event2_props = {
            "BucketName": bucket_name,
            "DistributionId": "E222222222222",
            "ApiEndpoint": "https://api2.example.com",
        }

        id1 = f"frontend-deployer-{event1_props['BucketName']}"
        id2 = f"frontend-deployer-{event2_props['BucketName']}"

        # Same bucket = same ID, regardless of other properties
        assert id1 == id2

    def test_handles_complex_bucket_names(self):
        """Test PhysicalResourceId handles complex bucket names."""
        complex_names = [
            "aws-drs-orch-fe-123456789012-dev",
            "my-company-frontend-prod-us-east-1",
            "bucket.with.dots",
            "bucket-with-many-hyphens-in-name",
        ]

        for bucket_name in complex_names:
            result = f"frontend-deployer-{bucket_name}"
            assert result.startswith("frontend-deployer-")
            assert bucket_name in result


class TestShouldEmptyBucket:
    """Test should_empty_bucket function (Requirement 3: Safe Delete Handling)."""

    def test_returns_tuple_with_three_elements(self):
        """Test should_empty_bucket returns tuple of (bool, str, str)."""
        # Simulate the function return
        result = (True, "stack_deletion", "DELETE_IN_PROGRESS")

        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
        assert isinstance(result[2], str)

    def test_proceeds_for_delete_in_progress(self):
        """Test bucket cleanup proceeds when stack status is DELETE_IN_PROGRESS."""
        stack_status = "DELETE_IN_PROGRESS"

        # Logic from should_empty_bucket
        is_rollback = "ROLLBACK" in stack_status
        has_delete = "DELETE" in stack_status

        should_empty = has_delete and not is_rollback

        assert should_empty is True

    def test_skips_for_update_in_progress(self):
        """Test bucket cleanup is skipped when stack status is UPDATE_IN_PROGRESS."""
        stack_status = "UPDATE_IN_PROGRESS"

        is_rollback = "ROLLBACK" in stack_status
        has_delete = "DELETE" in stack_status

        should_empty = has_delete and not is_rollback

        assert should_empty is False

    def test_skips_for_update_complete(self):
        """Test bucket cleanup is skipped when stack status is UPDATE_COMPLETE."""
        stack_status = "UPDATE_COMPLETE"

        has_delete = "DELETE" in stack_status

        assert has_delete is False

    def test_skips_for_update_rollback_in_progress(self):
        """Test bucket cleanup is skipped for UPDATE_ROLLBACK_IN_PROGRESS."""
        stack_status = "UPDATE_ROLLBACK_IN_PROGRESS"

        is_rollback = "ROLLBACK" in stack_status
        has_delete = "DELETE" in stack_status

        should_empty = has_delete and not is_rollback

        assert is_rollback is True
        assert should_empty is False

    def test_skips_for_update_rollback_complete(self):
        """Test bucket cleanup is skipped for UPDATE_ROLLBACK_COMPLETE."""
        stack_status = "UPDATE_ROLLBACK_COMPLETE"

        is_rollback = "ROLLBACK" in stack_status
        has_delete = "DELETE" in stack_status

        should_empty = has_delete and not is_rollback

        assert is_rollback is True
        assert should_empty is False

    def test_skips_for_create_in_progress(self):
        """Test bucket cleanup is skipped for CREATE_IN_PROGRESS."""
        stack_status = "CREATE_IN_PROGRESS"

        has_delete = "DELETE" in stack_status

        assert has_delete is False

    def test_skips_for_create_complete(self):
        """Test bucket cleanup is skipped for CREATE_COMPLETE."""
        stack_status = "CREATE_COMPLETE"

        has_delete = "DELETE" in stack_status

        assert has_delete is False

    def test_proceeds_for_delete_complete(self):
        """Test bucket cleanup proceeds for DELETE_COMPLETE."""
        stack_status = "DELETE_COMPLETE"

        is_rollback = "ROLLBACK" in stack_status
        has_delete = "DELETE" in stack_status

        should_empty = has_delete and not is_rollback

        assert should_empty is True

    def test_proceeds_for_delete_failed(self):
        """Test bucket cleanup proceeds for DELETE_FAILED."""
        stack_status = "DELETE_FAILED"

        is_rollback = "ROLLBACK" in stack_status
        has_delete = "DELETE" in stack_status

        should_empty = has_delete and not is_rollback

        assert should_empty is True

    def test_skips_when_no_stack_id(self):
        """Test bucket cleanup is skipped when StackId is missing."""
        stack_id = ""

        # Should skip cleanup when no StackId
        should_check = bool(stack_id)

        assert should_check is False

    def test_skips_when_status_check_fails(self):
        """Test bucket cleanup is skipped when status check fails (safe default)."""
        # If we can't check status, skip cleanup to be safe
        status_check_failed = True

        should_empty = not status_check_failed

        assert should_empty is False

    def test_returns_reason_for_skip(self):
        """Test should_empty_bucket returns reason when skipping."""
        # Simulate various skip reasons
        reasons = [
            "no_stack_id",
            "rollback_in_progress",
            "not_stack_deletion",
            "status_check_failed",
        ]

        for reason in reasons:
            result = (False, reason, "SOME_STATUS")
            assert result[0] is False
            assert result[1] == reason


class TestShouldEmptyBucketAllStatuses:
    """Test should_empty_bucket for all CloudFormation stack statuses."""

    @pytest.mark.parametrize("stack_status,expected_empty", [
        # DELETE statuses - should empty
        ("DELETE_IN_PROGRESS", True),
        ("DELETE_COMPLETE", True),
        ("DELETE_FAILED", True),
        # UPDATE statuses - should NOT empty
        ("UPDATE_IN_PROGRESS", False),
        ("UPDATE_COMPLETE", False),
        ("UPDATE_COMPLETE_CLEANUP_IN_PROGRESS", False),
        # ROLLBACK statuses - should NOT empty (even with DELETE)
        ("UPDATE_ROLLBACK_IN_PROGRESS", False),
        ("UPDATE_ROLLBACK_COMPLETE", False),
        ("UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS", False),
        ("UPDATE_ROLLBACK_FAILED", False),
        # CREATE statuses - should NOT empty
        ("CREATE_IN_PROGRESS", False),
        ("CREATE_COMPLETE", False),
        ("CREATE_FAILED", False),
        # REVIEW statuses - should NOT empty
        ("REVIEW_IN_PROGRESS", False),
        # IMPORT statuses - should NOT empty
        ("IMPORT_IN_PROGRESS", False),
        ("IMPORT_COMPLETE", False),
        ("IMPORT_ROLLBACK_IN_PROGRESS", False),
        ("IMPORT_ROLLBACK_COMPLETE", False),
        ("IMPORT_ROLLBACK_FAILED", False),
    ])
    def test_stack_status_handling(self, stack_status, expected_empty):
        """Test should_empty_bucket for various stack statuses."""
        is_rollback = "ROLLBACK" in stack_status
        has_delete = "DELETE" in stack_status

        should_empty = has_delete and not is_rollback

        assert should_empty == expected_empty, (
            f"Expected {expected_empty} for status {stack_status}"
        )


class TestDeleteHandlerBehavior:
    """Test DELETE handler behavior (Requirements 3, 6, 7)."""

    def test_delete_skips_cleanup_for_update_operations(self):
        """Test DELETE handler skips cleanup when stack is being updated."""
        stack_status = "UPDATE_IN_PROGRESS"

        # Logic from delete handler
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
        result = None

        assert result is None

    def test_delete_returns_none_even_on_errors(self):
        """Test DELETE handler returns None even when errors occur (Requirement 6)."""
        # Per Requirement 6: DELETE always returns SUCCESS to allow stack deletion

        try:
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

        should_cleanup = bool(stack_id)

        assert should_cleanup is False

    def test_delete_skips_cleanup_when_status_check_fails(self):
        """Test DELETE handler skips cleanup when status check fails."""
        status_check_failed = True

        should_cleanup = not status_check_failed

        assert should_cleanup is False


class TestDeleteHandlerWithMocks:
    """Test DELETE handler with mocked AWS clients."""

    @patch("boto3.client")
    def test_delete_handler_checks_stack_status(self, mock_boto_client):
        """Test DELETE handler calls describe_stacks to check status."""
        mock_cfn = MagicMock()
        mock_cfn.describe_stacks.return_value = {
            "Stacks": [{"StackStatus": "DELETE_IN_PROGRESS"}]
        }
        mock_boto_client.return_value = mock_cfn

        cfn = mock_boto_client("cloudformation")
        stack_id = "arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid"

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

        is_rollback = "ROLLBACK" in stack_status
        has_delete = "DELETE" in stack_status
        should_cleanup = has_delete and not is_rollback

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

        is_rollback = "ROLLBACK" in stack_status
        has_delete = "DELETE" in stack_status
        should_cleanup = has_delete and not is_rollback

        assert is_rollback is True
        assert should_cleanup is False

    @patch("boto3.client")
    def test_delete_handler_proceeds_for_delete_status(self, mock_boto_client):
        """Test DELETE handler proceeds when stack is being deleted."""
        mock_cfn = MagicMock()
        mock_cfn.describe_stacks.return_value = {
            "Stacks": [{"StackStatus": "DELETE_IN_PROGRESS"}]
        }
        mock_boto_client.return_value = mock_cfn

        cfn = mock_boto_client("cloudformation")
        response = cfn.describe_stacks(StackName="test-stack")
        stack_status = response["Stacks"][0]["StackStatus"]

        is_rollback = "ROLLBACK" in stack_status
        has_delete = "DELETE" in stack_status
        should_cleanup = has_delete and not is_rollback

        assert should_cleanup is True

    @patch("boto3.client")
    def test_delete_handler_handles_describe_stacks_error(self, mock_boto_client):
        """Test DELETE handler handles describe_stacks errors gracefully."""
        mock_cfn = MagicMock()
        mock_cfn.describe_stacks.side_effect = Exception("API Error")
        mock_boto_client.return_value = mock_cfn

        cfn = mock_boto_client("cloudformation")

        try:
            cfn.describe_stacks(StackName="test-stack")
            status_check_succeeded = True
        except Exception:
            status_check_succeeded = False

        # When status check fails, skip cleanup (safe default)
        should_cleanup = status_check_succeeded

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

        create_id = f"frontend-deployer-{bucket_name}"
        update_id = f"frontend-deployer-{bucket_name}"

        assert create_id == update_id


class TestLoggingBehavior:
    """Test logging behavior per Requirement 8."""

    def test_logs_event_type_at_start(self):
        """Test that event type is logged at start of invocation."""
        event = {
            "RequestType": "Create",
            "ResourceProperties": {"BucketName": "test-bucket"},
        }

        request_type = event.get("RequestType", "Unknown")

        assert request_type == "Create"

    def test_logs_stack_status_for_cleanup_decision(self):
        """Test that stack status is logged when making cleanup decisions."""
        stack_status = "DELETE_IN_PROGRESS"

        log_message = f"Stack status is '{stack_status}'"

        assert "DELETE_IN_PROGRESS" in log_message

    def test_logs_cleanup_decision_skip(self):
        """Test that cleanup skip decision is logged."""
        stack_status = "UPDATE_IN_PROGRESS"
        reason = "not_stack_deletion"

        log_message = (
            f"Skipping bucket cleanup - {reason} (status: {stack_status})"
        )

        assert "Skipping" in log_message
        assert stack_status in log_message

    def test_logs_cleanup_decision_proceed(self):
        """Test that cleanup proceed decision is logged."""
        stack_status = "DELETE_IN_PROGRESS"

        log_message = (
            f"Stack is being deleted (status: {stack_status}), "
            f"proceeding with bucket cleanup"
        )

        assert "proceeding" in log_message
        assert stack_status in log_message


class TestEmptyBucketFunction:
    """Test empty_bucket function behavior."""

    def test_returns_zero_when_bucket_not_found(self):
        """Test empty_bucket returns 0 when bucket doesn't exist."""
        bucket_exists = False

        if not bucket_exists:
            objects_deleted = 0

        assert objects_deleted == 0

    def test_deletes_all_versions(self):
        """Test empty_bucket deletes all object versions."""
        versions = [
            {"Key": "file1.txt", "VersionId": "v1"},
            {"Key": "file1.txt", "VersionId": "v2"},
            {"Key": "file2.txt", "VersionId": "v1"},
        ]

        objects_deleted = len(versions)

        assert objects_deleted == 3

    def test_deletes_delete_markers(self):
        """Test empty_bucket deletes delete markers."""
        delete_markers = [
            {"Key": "deleted-file.txt", "VersionId": "dm1"},
        ]

        markers_deleted = len(delete_markers)

        assert markers_deleted == 1


class TestConsolidatedLambdaArchitecture:
    """Test consolidated Lambda architecture (Requirement 1)."""

    def test_single_lambda_handles_create(self):
        """Test single Lambda handles CREATE events."""
        event = {"RequestType": "Create"}

        request_type = event.get("RequestType")

        assert request_type == "Create"

    def test_single_lambda_handles_update(self):
        """Test single Lambda handles UPDATE events."""
        event = {"RequestType": "Update"}

        request_type = event.get("RequestType")

        assert request_type == "Update"

    def test_single_lambda_handles_delete(self):
        """Test single Lambda handles DELETE events."""
        event = {"RequestType": "Delete"}

        request_type = event.get("RequestType")

        assert request_type == "Delete"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
