"""
Property-based tests for update_protection_group async flow.

Feature: async-launch-config-sync

This module tests critical properties of the update_protection_group function
when handling launch configurations with async sync:

- Property 2: Initial Status Pending
- Property 20: Concurrent Update Rejection
- Property 21: Pending Update Replacement
- Property 24: Validation Error Response

These properties ensure correct behavior for async launch config updates,
concurrency control, and validation error handling.
"""

import importlib
import json
import os
import sys
from decimal import Decimal
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

# Import the function under test using importlib for hyphenated module name
data_management_handler = importlib.import_module("data-management-handler.index")
update_protection_group = data_management_handler.update_protection_group


# ===========================================================================
# Test Helpers
# ===========================================================================


def create_mock_protection_group(
    group_id: str,
    region: str = "us-east-2",
    launch_config_status: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Create a mock protection group for testing."""
    group = {
        "groupId": group_id,
        "groupName": f"Test Group {group_id}",
        "region": region,
        "accountId": "123456789012",
        "sourceServerIds": ["s-1234567890abcdef0"],
        "version": 1,
        "launchConfig": {},
    }
    if launch_config_status:
        # Convert any float values to Decimal for DynamoDB compatibility
        converted_status = {}
        for key, value in launch_config_status.items():
            if isinstance(value, float):
                converted_status[key] = Decimal(str(value))
            else:
                converted_status[key] = value
        group["launchConfigStatus"] = converted_status
    return group


def create_mock_table_response(item: Dict[str, Any]) -> Dict[str, Any]:
    """Create a mock DynamoDB table response."""
    return {"Item": item}


def create_mock_update_response(item: Dict[str, Any]) -> Dict[str, Any]:
    """Create a mock DynamoDB update response."""
    return {"Attributes": item}


# ===========================================================================
# Property 2: Initial Status Pending
# Feature: async-launch-config-sync, Property 2: Initial Status Pending
# Validates: Requirements 1.3, 1.4
# ===========================================================================


class TestProperty2InitialStatusPending:
    """
    Property 2: Initial Status Pending

    For any protection group save operation with launch configuration,
    the launchConfigStatus SHALL be initialized to "pending" with a
    timestamp, and this status SHALL be included in the API response body.
    """

    @settings(max_examples=100)
    @given(
        group_id=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        instance_type=st.sampled_from(["t3.micro", "t3.small", "m5.large", "c5.xlarge"]),
        subnet_id=st.from_regex(r"subnet-[0-9a-f]{8,17}", fullmatch=True),
    )
    def test_pending_status_always_set_for_new_launch_config(
        self, group_id: str, instance_type: str, subnet_id: str
    ) -> None:
        """
        Feature: async-launch-config-sync, Property 2: Initial Status Pending

        Validates: Requirements 1.3, 1.4

        For any protection group update with launch configuration,
        the response SHALL include launchConfigStatus with status "pending".
        """
        # Arrange
        existing_group = create_mock_protection_group(group_id)
        launch_config = {"instanceType": instance_type, "subnetId": subnet_id}

        body = {"launchConfig": launch_config}

        with patch.object(data_management_handler, "get_protection_groups_table") as mock_table:
            mock_table_instance = MagicMock()
            mock_table.return_value = mock_table_instance

            # Mock get_item to return existing group
            mock_table_instance.get_item.return_value = create_mock_table_response(existing_group)

            # Mock update_item to return updated group with pending status
            updated_group = dict(existing_group)
            updated_group["launchConfig"] = launch_config
            updated_group["launchConfigStatus"] = {
                "status": "pending",
                "groupId": group_id,
                "progressCount": 0,
                "totalCount": 1,
                "percentage": Decimal("0.0"),
                "appliedServers": 0,
                "failedServers": 0,
                "serverConfigs": {},
                "syncJobId": None,
            }
            mock_table_instance.update_item.return_value = create_mock_update_response(updated_group)

            # Mock persist_config_status to prevent real AWS calls
            with patch.object(data_management_handler, "persist_config_status"):
                # Mock async invocation
                with patch.object(data_management_handler, "_invoke_async_sync"):
                    # Act
                    result = update_protection_group(group_id, body, query_parameters={})

        # Assert
        assert result["statusCode"] == 200
        response_body = result["body"] if isinstance(result["body"], dict) else json.loads(result["body"])

        # Property: launchConfigStatus must be present
        assert "launchConfigStatus" in response_body

        # Property: status must be "pending"
        assert response_body["launchConfigStatus"]["status"] == "pending"

        # Property: progressCount and totalCount must be present
        assert "progressCount" in response_body["launchConfigStatus"]
        assert "totalCount" in response_body["launchConfigStatus"]

        # Property: percentage must be 0.0 for pending
        percentage = response_body["launchConfigStatus"]["percentage"]
        assert float(percentage) == 0.0


# ===========================================================================
# Property 20: Concurrent Update Rejection
# Feature: async-launch-config-sync, Property 20: Concurrent Update Rejection
# Validates: Requirements 8.2
# ===========================================================================


class TestProperty20ConcurrentUpdateRejection:
    """
    Property 20: Concurrent Update Rejection

    For any PUT request to /protection-groups/{id} when
    launchConfigStatus.status is "syncing", the handler SHALL
    return HTTP 409 Conflict.
    """

    @settings(max_examples=100, deadline=None)
    @given(
        group_id=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        sync_job_id=st.uuids(),
        instance_type=st.sampled_from(["t3.micro", "t3.small", "m5.large"]),
    )
    def test_syncing_status_always_rejects_update(
        self, group_id: str, sync_job_id: str, instance_type: str
    ) -> None:
        """
        Feature: async-launch-config-sync, Property 20: Concurrent Update Rejection

        Validates: Requirements 8.2

        For any protection group with status "syncing",
        update attempts SHALL return HTTP 409.
        """
        # Arrange
        existing_group = create_mock_protection_group(
            group_id,
            launch_config_status={
                "status": "syncing",
                "syncJobId": str(sync_job_id),
                "progressCount": 5,
                "totalCount": 10,
            },
        )

        body = {"launchConfig": {"instanceType": instance_type}}

        with patch.object(data_management_handler, "get_protection_groups_table") as mock_table:
            mock_table_instance = MagicMock()
            mock_table.return_value = mock_table_instance
            mock_table_instance.get_item.return_value = create_mock_table_response(existing_group)

            # Act
            result = update_protection_group(group_id, body, query_parameters={})

        # Assert
        # Property: HTTP 409 Conflict must be returned
        assert result["statusCode"] == 409

        response_body = result["body"] if isinstance(result["body"], dict) else json.loads(result["body"])

        # Property: Error code must indicate sync in progress
        assert "error" in response_body
        assert "SYNC" in response_body["error"].upper() or "PROGRESS" in response_body["error"].upper()


# ===========================================================================
# Property 21: Pending Update Replacement
# Feature: async-launch-config-sync, Property 21: Pending Update Replacement
# Validates: Requirements 8.3
# ===========================================================================


class TestProperty21PendingUpdateReplacement:
    """
    Property 21: Pending Update Replacement

    For any PUT request to /protection-groups/{id} when
    launchConfigStatus.status is "pending", the handler SHALL
    overwrite the pending configuration and trigger a new async
    self-invocation.
    """

    @settings(max_examples=100)
    @given(
        group_id=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        old_instance_type=st.sampled_from(["t3.micro", "t3.small"]),
        new_instance_type=st.sampled_from(["m5.large", "c5.xlarge"]),
    )
    def test_pending_status_allows_overwrite(
        self, group_id: str, old_instance_type: str, new_instance_type: str
    ) -> None:
        """
        Feature: async-launch-config-sync, Property 21: Pending Update Replacement

        Validates: Requirements 8.3

        For any protection group with status "pending",
        update SHALL succeed and overwrite the configuration.
        """
        # Arrange
        existing_group = create_mock_protection_group(
            group_id,
            launch_config_status={
                "status": "pending",
                "syncJobId": None,
                "progressCount": 0,
                "totalCount": 1,
            },
        )
        existing_group["launchConfig"] = {"instanceType": old_instance_type}

        body = {"launchConfig": {"instanceType": new_instance_type}}

        with patch.object(data_management_handler, "get_protection_groups_table") as mock_table:
            mock_table_instance = MagicMock()
            mock_table.return_value = mock_table_instance
            mock_table_instance.get_item.return_value = create_mock_table_response(existing_group)

            # Mock update_item to return updated group
            updated_group = dict(existing_group)
            updated_group["launchConfig"] = body["launchConfig"]
            updated_group["launchConfigStatus"]["status"] = "pending"
            mock_table_instance.update_item.return_value = create_mock_update_response(updated_group)

            # Mock persist_config_status to prevent real AWS calls
            with patch.object(data_management_handler, "persist_config_status"):
                # Mock async invocation
                with patch.object(data_management_handler, "_invoke_async_sync") as mock_invoke:
                    # Act
                    result = update_protection_group(group_id, body, query_parameters={})

                    # Assert
                    # Property: HTTP 200 must be returned (update succeeds)
                    assert result["statusCode"] == 200

                    # Property: Async invocation must be triggered
                    assert mock_invoke.called


# ===========================================================================
# Property 24: Validation Error Response
# Feature: async-launch-config-sync, Property 24: Validation Error Response
# Validates: Requirements 10.6, 10.7
# ===========================================================================


class TestProperty24ValidationErrorResponse:
    """
    Property 24: Validation Error Response

    For any launch configuration with format validation errors,
    the handler SHALL return HTTP 400 with specific error details
    and SHALL NOT trigger async self-invocation.
    """

    @settings(max_examples=100)
    @given(
        group_id=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        invalid_ip=st.text(min_size=1, max_size=20).filter(
            lambda x: not x.replace(".", "").replace("0", "").replace("1", "").replace("2", "").replace("5", "").isdigit()
        ),
    )
    def test_invalid_format_always_returns_400(self, group_id: str, invalid_ip: str) -> None:
        """
        Feature: async-launch-config-sync, Property 24: Validation Error Response

        Validates: Requirements 10.6, 10.7

        For any launch configuration with invalid field formats,
        the handler SHALL return HTTP 400 and NOT trigger async sync.
        """
        # Arrange
        existing_group = create_mock_protection_group(group_id)
        launch_config = {"staticPrivateIp": invalid_ip}

        body = {"launchConfig": launch_config}

        with patch.object(data_management_handler, "get_protection_groups_table") as mock_table:
            mock_table_instance = MagicMock()
            mock_table.return_value = mock_table_instance
            mock_table_instance.get_item.return_value = create_mock_table_response(existing_group)

            # Mock async invocation
            with patch.object(data_management_handler, "_invoke_async_sync") as mock_invoke:
                # Act
                result = update_protection_group(group_id, body, query_parameters={})

                # Assert
                # Property: HTTP 400 must be returned for validation errors
                assert result["statusCode"] == 400

                response_body = result["body"] if isinstance(result["body"], dict) else json.loads(result["body"])

                # Property: Error message must indicate validation failure
                assert "error" in response_body
                assert "INVALID" in response_body["error"].upper() or "VALIDATION" in str(response_body).upper()

                # Property: Async invocation must NOT be triggered
                assert not mock_invoke.called

    @settings(max_examples=100)
    @given(
        group_id=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        invalid_subnet=st.text(min_size=1, max_size=20).filter(lambda x: not x.startswith("subnet-")),
    )
    def test_invalid_subnet_format_returns_400(self, group_id: str, invalid_subnet: str) -> None:
        """
        Feature: async-launch-config-sync, Property 24: Validation Error Response

        Validates: Requirements 10.6, 10.7

        For any launch configuration with invalid subnet format,
        the handler SHALL return HTTP 400.
        """
        # Arrange
        existing_group = create_mock_protection_group(group_id)
        launch_config = {"subnetId": invalid_subnet}

        body = {"launchConfig": launch_config}

        with patch.object(data_management_handler, "get_protection_groups_table") as mock_table:
            mock_table_instance = MagicMock()
            mock_table.return_value = mock_table_instance
            mock_table_instance.get_item.return_value = create_mock_table_response(existing_group)

            # Act
            result = update_protection_group(group_id, body, query_parameters={})

            # Assert
            # Property: HTTP 400 must be returned
            assert result["statusCode"] == 400
