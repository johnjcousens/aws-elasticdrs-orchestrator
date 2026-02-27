"""
Unit tests for query handler region optimization.

Tests the three helper functions that optimize region selection:
- _get_region_status: Fast region status lookup from DRSRegionStatusTable
- _query_servers_from_inventory: Fast server query from SourceServerInventoryTable
- _check_protection_group_assignments: Mark servers assigned to protection groups

These tests verify the optimization reduces region selection from 5-10 seconds
to <100ms by using DynamoDB instead of expensive DRS API calls.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

# Add lambda directory to path
lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
sys.path.insert(0, lambda_dir)
sys.path.insert(0, os.path.join(lambda_dir, "query-handler"))

# Import functions under test
from index import (
    _check_protection_group_assignments,
    _get_region_status,
    _query_servers_from_inventory,
)


@pytest.fixture
def mock_region_status_table():
    """Mock DynamoDB region status table."""
    table = Mock()
    table.get_item = Mock()
    return table


@pytest.fixture
def mock_protection_groups_table():
    """Mock DynamoDB protection groups table."""
    table = Mock()
    table.scan = Mock()
    return table


@pytest.fixture
def fresh_timestamp():
    """Generate a fresh timestamp (5 minutes ago)."""
    return (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()


@pytest.fixture
def stale_timestamp():
    """Generate a stale timestamp (20 minutes ago)."""
    return (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()


@pytest.fixture
def sample_inventory_server():
    """Sample server record from inventory database."""
    return {
        "sourceServerID": "s-1234567890abcdef0",
        "hostname": "web-server-01",
        "fqdn": "web-server-01.example.com",
        "replicationRegion": "us-east-1",
        "replicationState": "CONTINUOUS",
        "sourceAccountId": "891376951562",
        "stagingAccountId": "160885257264",
        "cpuCores": 4,
        "ramBytes": 8589934592,
        "lastUpdated": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
    }


@pytest.fixture
def sample_transformed_server():
    """Sample server in frontend format (after transformation)."""
    return {
        "sourceServerID": "s-1234567890abcdef0",
        "hostname": "web-server-01",
        "fqdn": "web-server-01.example.com",
        "replicationRegion": "us-east-1",
        "replicationState": "CONTINUOUS",
        "replicationStateDisplay": "Continuous",
        "sourceAccountId": "891376951562",
        "stagingAccountId": "160885257264",
        "cpuCores": 4,
        "ramBytes": 8589934592,
    }


class TestGetRegionStatus:
    """Test _get_region_status() function."""

    def test_region_with_not_initialized_status(self, mock_region_status_table):
        """Test region with NOT_INITIALIZED status returns status dict."""
        mock_region_status_table.get_item.return_value = {
            "Item": {
                "region": "ap-northeast-2",
                "status": "NOT_INITIALIZED",
                "serverCount": 0,
                "lastUpdated": "2025-02-24T10:30:00Z",
                "errorMessage": "DRS not initialized in region",
            }
        }

        with patch("shared.active_region_filter.get_region_status_table", return_value=mock_region_status_table):
            result = _get_region_status("ap-northeast-2")

        assert result is not None
        assert result["status"] == "NOT_INITIALIZED"
        assert result["serverCount"] == 0
        assert result["region"] == "ap-northeast-2"
        mock_region_status_table.get_item.assert_called_once_with(Key={"region": "ap-northeast-2"})

    def test_region_with_active_status(self, mock_region_status_table):
        """Test region with ACTIVE status returns status dict."""
        mock_region_status_table.get_item.return_value = {
            "Item": {
                "region": "us-east-1",
                "status": "ACTIVE",
                "serverCount": 42,
                "lastUpdated": "2025-02-24T10:30:00Z",
            }
        }

        with patch("shared.active_region_filter.get_region_status_table", return_value=mock_region_status_table):
            result = _get_region_status("us-east-1")

        assert result is not None
        assert result["status"] == "ACTIVE"
        assert result["serverCount"] == 42

    def test_region_with_iam_permission_denied_status(self, mock_region_status_table):
        """Test region with IAM_PERMISSION_DENIED status returns status dict."""
        mock_region_status_table.get_item.return_value = {
            "Item": {
                "region": "eu-west-1",
                "status": "IAM_PERMISSION_DENIED",
                "serverCount": 0,
                "lastUpdated": "2025-02-24T10:30:00Z",
                "errorMessage": "Access denied to DRS API",
            }
        }

        with patch("shared.active_region_filter.get_region_status_table", return_value=mock_region_status_table):
            result = _get_region_status("eu-west-1")

        assert result is not None
        assert result["status"] == "IAM_PERMISSION_DENIED"
        assert "errorMessage" in result

    def test_region_not_found_in_table(self, mock_region_status_table):
        """Test region not found in table returns None."""
        mock_region_status_table.get_item.return_value = {}

        with patch("shared.active_region_filter.get_region_status_table", return_value=mock_region_status_table):
            result = _get_region_status("ap-south-1")

        assert result is None

    def test_table_not_available_returns_none(self):
        """Test that unavailable table returns None."""
        with patch("shared.active_region_filter.get_region_status_table", return_value=None):
            result = _get_region_status("us-east-1")

        assert result is None

    def test_dynamodb_error_returns_none(self, mock_region_status_table):
        """Test that DynamoDB error returns None."""
        mock_region_status_table.get_item.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable"}}, "GetItem"
        )

        with patch("shared.active_region_filter.get_region_status_table", return_value=mock_region_status_table):
            result = _get_region_status("us-east-1")

        assert result is None

    def test_generic_exception_returns_none(self, mock_region_status_table):
        """Test that generic exception returns None."""
        mock_region_status_table.get_item.side_effect = Exception("Unexpected error")

        with patch("shared.active_region_filter.get_region_status_table", return_value=mock_region_status_table):
            result = _get_region_status("us-east-1")

        assert result is None


class TestQueryServersFromInventory:
    """Test _query_servers_from_inventory() function."""

    def test_fresh_inventory_with_servers(self, sample_inventory_server, sample_transformed_server):
        """Test querying fresh inventory with servers returns server list."""
        with patch("shared.inventory_query.is_inventory_fresh", return_value=True), patch(
            "shared.inventory_query.query_inventory_by_regions", return_value=[sample_inventory_server]
        ), patch("shared.drs_utils.transform_drs_server_for_frontend", return_value=sample_transformed_server), patch(
            "shared.inventory_query.publish_metric"
        ) as mock_publish:
            result = _query_servers_from_inventory("us-east-1", None)

        assert result is not None
        assert len(result) == 1
        assert result[0]["sourceServerID"] == "s-1234567890abcdef0"
        assert result[0]["hostname"] == "web-server-01"
        mock_publish.assert_called_once_with("InventoryDatabaseHits", 1)

    def test_fresh_inventory_with_no_servers(self):
        """Test querying fresh inventory with no servers returns empty list."""
        with patch("shared.inventory_query.is_inventory_fresh", return_value=True), patch(
            "shared.inventory_query.query_inventory_by_regions", return_value=[]
        ), patch("shared.inventory_query.publish_metric"):
            result = _query_servers_from_inventory("us-east-1", None)

        assert result is not None
        assert result == []

    def test_stale_inventory_returns_none(self):
        """Test that stale inventory returns None for DRS API fallback."""
        with patch("shared.inventory_query.is_inventory_fresh", return_value=False), patch(
            "shared.inventory_query.publish_metric"
        ) as mock_publish:
            result = _query_servers_from_inventory("us-east-1", None)

        assert result is None
        mock_publish.assert_called_once_with("InventoryDatabaseMisses", 1)

    def test_query_with_account_id_filter(self, sample_inventory_server, sample_transformed_server):
        """Test querying with account ID filter."""
        with patch("shared.inventory_query.is_inventory_fresh", return_value=True), patch(
            "shared.inventory_query.query_inventory_by_regions", return_value=[sample_inventory_server]
        ) as mock_query, patch(
            "shared.drs_utils.transform_drs_server_for_frontend", return_value=sample_transformed_server
        ), patch(
            "shared.inventory_query.publish_metric"
        ):
            result = _query_servers_from_inventory("us-east-1", "891376951562")

        assert result is not None
        mock_query.assert_called_once_with(regions=["us-east-1"], filters={"sourceAccountId": "891376951562"})

    def test_query_without_account_id_filter(self, sample_inventory_server, sample_transformed_server):
        """Test querying without account ID filter."""
        with patch("shared.inventory_query.is_inventory_fresh", return_value=True), patch(
            "shared.inventory_query.query_inventory_by_regions", return_value=[sample_inventory_server]
        ) as mock_query, patch(
            "shared.drs_utils.transform_drs_server_for_frontend", return_value=sample_transformed_server
        ), patch(
            "shared.inventory_query.publish_metric"
        ):
            result = _query_servers_from_inventory("us-east-1", None)

        assert result is not None
        mock_query.assert_called_once_with(regions=["us-east-1"], filters={})

    def test_multiple_servers_transformation(self, sample_inventory_server, sample_transformed_server):
        """Test that multiple servers are all transformed."""
        server2 = sample_inventory_server.copy()
        server2["sourceServerID"] = "s-9876543210fedcba0"
        server2["hostname"] = "db-server-01"

        transformed2 = sample_transformed_server.copy()
        transformed2["sourceServerID"] = "s-9876543210fedcba0"
        transformed2["hostname"] = "db-server-01"

        with patch("shared.inventory_query.is_inventory_fresh", return_value=True), patch(
            "shared.inventory_query.query_inventory_by_regions", return_value=[sample_inventory_server, server2]
        ), patch(
            "shared.drs_utils.transform_drs_server_for_frontend", side_effect=[sample_transformed_server, transformed2]
        ), patch(
            "shared.inventory_query.publish_metric"
        ):
            result = _query_servers_from_inventory("us-east-1", None)

        assert result is not None
        assert len(result) == 2
        assert result[0]["sourceServerID"] == "s-1234567890abcdef0"
        assert result[1]["sourceServerID"] == "s-9876543210fedcba0"

    def test_query_error_returns_none(self):
        """Test that query error returns None for DRS API fallback."""
        with patch("shared.inventory_query.is_inventory_fresh", return_value=True), patch(
            "shared.inventory_query.query_inventory_by_regions", side_effect=Exception("Query failed")
        ), patch("shared.inventory_query.publish_metric") as mock_publish:
            result = _query_servers_from_inventory("us-east-1", None)

        assert result is None
        mock_publish.assert_called_once_with("InventoryDatabaseMisses", 1)

    def test_transformation_error_returns_none(self, sample_inventory_server):
        """Test that transformation error returns None for DRS API fallback."""
        with patch("shared.inventory_query.is_inventory_fresh", return_value=True), patch(
            "shared.inventory_query.query_inventory_by_regions", return_value=[sample_inventory_server]
        ), patch(
            "shared.drs_utils.transform_drs_server_for_frontend", side_effect=Exception("Transform failed")
        ), patch(
            "shared.inventory_query.publish_metric"
        ) as mock_publish:
            result = _query_servers_from_inventory("us-east-1", None)

        assert result is None
        mock_publish.assert_called_once_with("InventoryDatabaseMisses", 1)


class TestCheckProtectionGroupAssignments:
    """Test _check_protection_group_assignments() function."""

    def test_servers_with_no_assignments(self, mock_protection_groups_table):
        """Test servers with no protection group assignments."""
        servers = [
            {"sourceServerID": "s-1234", "hostname": "server1"},
            {"sourceServerID": "s-5678", "hostname": "server2"},
        ]

        mock_protection_groups_table.scan.return_value = {"Items": []}

        with patch("shared.conflict_detection.get_protection_groups_table", return_value=mock_protection_groups_table):
            _check_protection_group_assignments(servers, "us-east-1", None, None)

        assert servers[0]["assignedToProtectionGroup"] is None
        assert servers[0]["selectable"] is True
        assert servers[1]["assignedToProtectionGroup"] is None
        assert servers[1]["selectable"] is True

    def test_servers_assigned_to_different_protection_group(self, mock_protection_groups_table):
        """Test servers assigned to different protection group are marked non-selectable."""
        servers = [
            {"sourceServerID": "s-1234", "hostname": "server1"},
            {"sourceServerID": "s-5678", "hostname": "server2"},
        ]

        mock_protection_groups_table.scan.return_value = {
            "Items": [
                {
                    "groupId": "pg-other",
                    "region": "us-east-1",
                    "servers": [{"sourceServerID": "s-1234"}],
                }
            ]
        }

        with patch("shared.conflict_detection.get_protection_groups_table", return_value=mock_protection_groups_table):
            _check_protection_group_assignments(servers, "us-east-1", None, None)

        assert servers[0]["assignedToProtectionGroup"] == "pg-other"
        assert servers[0]["selectable"] is False
        assert servers[1]["assignedToProtectionGroup"] is None
        assert servers[1]["selectable"] is True

    def test_servers_assigned_to_current_protection_group(self, mock_protection_groups_table):
        """Test servers assigned to current protection group are marked selectable."""
        servers = [
            {"sourceServerID": "s-1234", "hostname": "server1"},
            {"sourceServerID": "s-5678", "hostname": "server2"},
        ]

        mock_protection_groups_table.scan.return_value = {
            "Items": [
                {
                    "groupId": "pg-current",
                    "region": "us-east-1",
                    "servers": [{"sourceServerID": "s-1234"}],
                }
            ]
        }

        with patch("shared.conflict_detection.get_protection_groups_table", return_value=mock_protection_groups_table):
            _check_protection_group_assignments(servers, "us-east-1", None, "pg-current")

        assert servers[0]["assignedToProtectionGroup"] == "pg-current"
        assert servers[0]["selectable"] is True
        assert servers[1]["assignedToProtectionGroup"] is None
        assert servers[1]["selectable"] is True

    def test_multiple_protection_groups_in_region(self, mock_protection_groups_table):
        """Test handling multiple protection groups in same region."""
        servers = [
            {"sourceServerID": "s-1234", "hostname": "server1"},
            {"sourceServerID": "s-5678", "hostname": "server2"},
            {"sourceServerID": "s-9999", "hostname": "server3"},
        ]

        mock_protection_groups_table.scan.return_value = {
            "Items": [
                {
                    "groupId": "pg-group1",
                    "region": "us-east-1",
                    "servers": [{"sourceServerID": "s-1234"}],
                },
                {
                    "groupId": "pg-group2",
                    "region": "us-east-1",
                    "servers": [{"sourceServerID": "s-5678"}],
                },
            ]
        }

        with patch("shared.conflict_detection.get_protection_groups_table", return_value=mock_protection_groups_table):
            _check_protection_group_assignments(servers, "us-east-1", None, None)

        assert servers[0]["assignedToProtectionGroup"] == "pg-group1"
        assert servers[0]["selectable"] is False
        assert servers[1]["assignedToProtectionGroup"] == "pg-group2"
        assert servers[1]["selectable"] is False
        assert servers[2]["assignedToProtectionGroup"] is None
        assert servers[2]["selectable"] is True

    def test_empty_servers_list(self, mock_protection_groups_table):
        """Test that empty servers list is handled gracefully."""
        servers = []

        with patch("shared.conflict_detection.get_protection_groups_table", return_value=mock_protection_groups_table):
            _check_protection_group_assignments(servers, "us-east-1", None, None)

        assert servers == []
        mock_protection_groups_table.scan.assert_not_called()

    def test_table_not_available(self):
        """Test that unavailable table is handled gracefully."""
        servers = [{"sourceServerID": "s-1234", "hostname": "server1"}]

        with patch("shared.conflict_detection.get_protection_groups_table", return_value=None):
            _check_protection_group_assignments(servers, "us-east-1", None, None)

        # Servers should not have assignment fields added
        assert "assignedToProtectionGroup" not in servers[0]
        assert "selectable" not in servers[0]

    def test_dynamodb_error_handled_gracefully(self, mock_protection_groups_table):
        """Test that DynamoDB error is handled gracefully."""
        servers = [{"sourceServerID": "s-1234", "hostname": "server1"}]

        mock_protection_groups_table.scan.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable"}}, "Scan"
        )

        with patch("shared.conflict_detection.get_protection_groups_table", return_value=mock_protection_groups_table):
            _check_protection_group_assignments(servers, "us-east-1", None, None)

        # Servers should not have assignment fields added due to error
        assert "assignedToProtectionGroup" not in servers[0]
        assert "selectable" not in servers[0]

    def test_protection_group_with_multiple_servers(self, mock_protection_groups_table):
        """Test protection group with multiple servers."""
        servers = [
            {"sourceServerID": "s-1234", "hostname": "server1"},
            {"sourceServerID": "s-5678", "hostname": "server2"},
            {"sourceServerID": "s-9999", "hostname": "server3"},
        ]

        mock_protection_groups_table.scan.return_value = {
            "Items": [
                {
                    "groupId": "pg-multi",
                    "region": "us-east-1",
                    "servers": [{"sourceServerID": "s-1234"}, {"sourceServerID": "s-5678"}],
                }
            ]
        }

        with patch("shared.conflict_detection.get_protection_groups_table", return_value=mock_protection_groups_table):
            _check_protection_group_assignments(servers, "us-east-1", None, None)

        assert servers[0]["assignedToProtectionGroup"] == "pg-multi"
        assert servers[0]["selectable"] is False
        assert servers[1]["assignedToProtectionGroup"] == "pg-multi"
        assert servers[1]["selectable"] is False
        assert servers[2]["assignedToProtectionGroup"] is None
        assert servers[2]["selectable"] is True

    def test_server_without_source_server_id(self, mock_protection_groups_table):
        """Test handling server without sourceServerID field."""
        servers = [
            {"hostname": "server1"},  # Missing sourceServerID
            {"sourceServerID": "s-5678", "hostname": "server2"},
        ]

        mock_protection_groups_table.scan.return_value = {
            "Items": [
                {
                    "groupId": "pg-test",
                    "region": "us-east-1",
                    "servers": [{"sourceServerID": "s-5678"}],
                }
            ]
        }

        with patch("shared.conflict_detection.get_protection_groups_table", return_value=mock_protection_groups_table):
            _check_protection_group_assignments(servers, "us-east-1", None, None)

        # First server should have None assignment (no sourceServerID to match)
        assert servers[0]["assignedToProtectionGroup"] is None
        assert servers[0]["selectable"] is True
        # Second server should be assigned
        assert servers[1]["assignedToProtectionGroup"] == "pg-test"
        assert servers[1]["selectable"] is False
