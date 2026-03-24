# Copyright Amazon.com and Affiliates. All rights reserved.
# This deliverable is considered Developed Content as defined in the AWS Service Terms.

"""
Unit tests for inventory query GSI-based performance optimizations.

Tests the behavior where query_inventory_by_regions(),
query_inventory_by_staging_account(), and is_inventory_fresh()
use GSI queries instead of full table scans.

These tests validate the design described in:
    .kiro/specs/inventory-query-performance-fix/design.md
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, call

import pytest
from botocore.exceptions import ClientError

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

# Set environment variables before importing module
os.environ["SOURCE_SERVER_INVENTORY_TABLE"] = "test-inventory-table"
os.environ["DRS_REGION_STATUS_TABLE"] = "test-region-status-table"

from shared.inventory_query import (
    is_inventory_fresh,
    query_inventory_by_regions,
    query_inventory_by_staging_account,
)


@pytest.fixture
def mock_inventory_table():
    """Mock DynamoDB inventory table with query and scan support."""
    table = Mock()
    table.scan = Mock()
    table.query = Mock()
    table.get_item = Mock()
    return table


@pytest.fixture
def mock_region_status_table():
    """Mock DynamoDB region status table."""
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



def _make_server(server_id: str, region: str, **kwargs) -> dict:
    """Helper to create a server record for tests."""
    server = {
        "sourceServerID": server_id,
        "sourceServerArn": f"arn:aws:drs:us-east-2:123456789012:source-server/{server_id}",
        "replicationRegion": region,
        "stagingAccountId": kwargs.get("staging_account_id", "123456789012"),
        "sourceAccountId": kwargs.get("source_account_id", "111111111111"),
        "hostname": kwargs.get("hostname", f"host-{server_id}"),
        "replicationState": kwargs.get("replication_state", "CONTINUOUS"),
        "lastUpdated": kwargs.get("last_updated", datetime.now(timezone.utc).isoformat()),
        "lastUpdatedDateTime": kwargs.get("last_updated_dt", datetime.now(timezone.utc).isoformat()),
    }
    if "cpu_cores" in kwargs:
        server["cpuCores"] = kwargs["cpu_cores"]
    if "ram_bytes" in kwargs:
        server["ramBytes"] = kwargs["ram_bytes"]
    return server



class TestIsInventoryFreshRegionStatusTable:
    """Tests for is_inventory_fresh() using region status table instead of inventory scan."""

    def test_fresh_region_status_returns_true(self, mock_region_status_table, fresh_timestamp):
        """After fix: is_inventory_fresh() should check region status table's lastChecked field."""
        mock_region_status_table.scan.return_value = {
            "Items": [{"region": "us-east-1", "lastChecked": fresh_timestamp, "serverCount": 5}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=Mock(),
        ) as mock_get_inv, patch(
            "shared.active_region_filter.get_region_status_table",
            return_value=mock_region_status_table,
        ):
            result = is_inventory_fresh()

        assert result is True
        # Region status table scan should be called
        mock_region_status_table.scan.assert_called_once()

    def test_stale_region_status_returns_false(self, mock_region_status_table, stale_timestamp):
        """After fix: stale lastChecked in region status table should return False."""
        mock_region_status_table.scan.return_value = {
            "Items": [{"region": "us-east-1", "lastChecked": stale_timestamp, "serverCount": 5}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=Mock(),
        ), patch(
            "shared.active_region_filter.get_region_status_table",
            return_value=mock_region_status_table,
        ):
            result = is_inventory_fresh()

        assert result is False
        mock_region_status_table.scan.assert_called_once()

    def test_empty_region_status_table_returns_false(self, mock_region_status_table):
        """After fix: empty region status table should return False."""
        mock_region_status_table.scan.return_value = {"Items": []}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=Mock(),
        ), patch(
            "shared.active_region_filter.get_region_status_table",
            return_value=mock_region_status_table,
        ):
            result = is_inventory_fresh()

        assert result is False

    def test_region_status_table_available_does_not_scan_inventory(
        self, mock_inventory_table, mock_region_status_table, fresh_timestamp
    ):
        """When region status table is available, inventory_table.scan() should NOT be called."""
        mock_region_status_table.scan.return_value = {
            "Items": [{"region": "us-east-1", "lastChecked": fresh_timestamp, "serverCount": 5}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.active_region_filter.get_region_status_table",
            return_value=mock_region_status_table,
        ):
            result = is_inventory_fresh()

        assert result is True
        mock_region_status_table.scan.assert_called_once()
        mock_inventory_table.scan.assert_not_called()

    def test_region_status_table_unavailable_falls_back(self, mock_inventory_table, fresh_timestamp):
        """After fix: if region status table unavailable, fall back to inventory table scan."""
        mock_inventory_table.scan.return_value = {
            "Items": [{"sourceServerID": "s-123", "lastUpdated": fresh_timestamp}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.active_region_filter.get_region_status_table",
            return_value=None,
        ):
            result = is_inventory_fresh()

        # Should still work via fallback to inventory table
        assert result is True

    def test_freshness_threshold_preserved(self, mock_inventory_table):
        """Regression: custom max_age_minutes parameter must still work."""
        timestamp_10m = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        mock_inventory_table.scan.return_value = {
            "Items": [{"sourceServerID": "s-123", "lastUpdated": timestamp_10m}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ):
            assert is_inventory_fresh(max_age_minutes=15) is True
            assert is_inventory_fresh(max_age_minutes=5) is False

    def test_dynamodb_error_returns_false(self, mock_inventory_table):
        """Regression: DynamoDB errors must still return False."""
        mock_inventory_table.scan.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable"}}, "Scan"
        )

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ):
            result = is_inventory_fresh()

        assert result is False



class TestQueryByRegionsGSI:
    """Tests for query_inventory_by_regions() using GSI queries instead of scans."""

    def test_region_only_query_uses_replication_region_index(self, mock_inventory_table, fresh_timestamp):
        """Fix 2 Case B: region-only queries should use ReplicationRegionIndex GSI."""
        server = _make_server("s-001", "us-east-1")

        # GSI query returns results
        mock_inventory_table.query.return_value = {"Items": [server]}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_regions(["us-east-1"])

        assert len(result) == 1
        assert result[0]["sourceServerID"] == "s-001"
        assert result[0]["replicationRegion"] == "us-east-1"
        # Verify GSI query was used with ReplicationRegionIndex
        mock_inventory_table.query.assert_called()
        query_call_kwargs = mock_inventory_table.query.call_args_list[0][1]
        assert query_call_kwargs["IndexName"] == "ReplicationRegionIndex"

    def test_multiple_regions_merge_results(self, mock_inventory_table, fresh_timestamp):
        """Fix 2 Case B: multiple regions should query each and merge results."""
        server_east = _make_server("s-001", "us-east-1")
        server_west = _make_server("s-002", "us-west-2")

        # GSI query returns results per region
        mock_inventory_table.query.side_effect = [
            {"Items": [server_east]},
            {"Items": [server_west]},
        ]

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_regions(["us-east-1", "us-west-2"])

        assert len(result) == 2
        server_ids = {s["sourceServerID"] for s in result}
        assert server_ids == {"s-001", "s-002"}
        # Should have queried ReplicationRegionIndex twice (once per region)
        assert mock_inventory_table.query.call_count == 2
        for call_obj in mock_inventory_table.query.call_args_list:
            assert call_obj[1]["IndexName"] == "ReplicationRegionIndex"

    def test_source_account_filter_uses_source_account_index(self, mock_inventory_table, fresh_timestamp):
        """Fix 2 Case A: sourceAccountId filter should use SourceAccountIndex GSI."""
        server = _make_server("s-001", "us-east-1", source_account_id="111111111111")

        # GSI query returns results
        mock_inventory_table.query.return_value = {"Items": [server]}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_regions(
                ["us-east-1"],
                filters={"sourceAccountId": "111111111111"},
            )

        assert len(result) == 1
        assert result[0]["sourceAccountId"] == "111111111111"
        # Verify SourceAccountIndex GSI was used
        mock_inventory_table.query.assert_called()
        query_call_kwargs = mock_inventory_table.query.call_args_list[0][1]
        assert query_call_kwargs["IndexName"] == "SourceAccountIndex"

    def test_staging_account_filter_uses_staging_account_index(self, mock_inventory_table, fresh_timestamp):
        """Fix 2 Case C: stagingAccountId filter should use StagingAccountIndex GSI."""
        server = _make_server("s-001", "us-east-1", staging_account_id="222222222222")

        # GSI query returns results
        mock_inventory_table.query.return_value = {"Items": [server]}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_regions(
                ["us-east-1"],
                filters={"stagingAccountId": "222222222222"},
            )

        assert len(result) == 1
        assert result[0]["stagingAccountId"] == "222222222222"
        # Verify StagingAccountIndex GSI was used
        mock_inventory_table.query.assert_called()
        query_call_kwargs = mock_inventory_table.query.call_args_list[0][1]
        assert query_call_kwargs["IndexName"] == "StagingAccountIndex"

    def test_hostname_filter_applied_after_gsi_query(self, mock_inventory_table, fresh_timestamp):
        """Regression 3.5: hostname filter must still work correctly."""
        server_match = _make_server("s-001", "us-east-1", hostname="web-server-01")
        server_other = _make_server("s-002", "us-east-1", hostname="db-server-01")

        # GSI query returns all servers for the region, post-filter applies hostname
        mock_inventory_table.query.return_value = {"Items": [server_match, server_other]}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_regions(
                ["us-east-1"],
                filters={"hostname": "web-server-01"},
            )

        assert len(result) == 1
        assert result[0]["hostname"] == "web-server-01"

    def test_replication_state_filter_applied_after_gsi_query(self, mock_inventory_table, fresh_timestamp):
        """Regression 3.5: replicationState filter must still work correctly."""
        server_continuous = _make_server("s-001", "us-east-1", replication_state="CONTINUOUS")
        server_stopped = _make_server("s-002", "us-east-1", replication_state="STOPPED")

        # GSI query returns all servers, post-filter applies replicationState
        mock_inventory_table.query.return_value = {"Items": [server_continuous, server_stopped]}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_regions(
                ["us-east-1"],
                filters={"replicationState": "CONTINUOUS"},
            )

        assert len(result) == 1
        assert result[0]["replicationState"] == "CONTINUOUS"

    def test_min_cpu_cores_filter(self, mock_inventory_table, fresh_timestamp):
        """Regression 3.5: minCpuCores filter must still work correctly."""
        server_big = _make_server("s-001", "us-east-1", cpu_cores=8)
        server_small = _make_server("s-002", "us-east-1", cpu_cores=2)

        # GSI query returns all servers, post-filter applies minCpuCores
        mock_inventory_table.query.return_value = {"Items": [server_big, server_small]}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_regions(
                ["us-east-1"],
                filters={"minCpuCores": 4},
            )

        assert len(result) == 1
        assert result[0]["sourceServerID"] == "s-001"

    def test_min_ram_bytes_filter(self, mock_inventory_table, fresh_timestamp):
        """Regression 3.5: minRamBytes filter must still work correctly."""
        server_big = _make_server("s-001", "us-east-1", ram_bytes=8589934592)
        server_small = _make_server("s-002", "us-east-1", ram_bytes=2147483648)

        # GSI query returns all servers, post-filter applies minRamBytes
        mock_inventory_table.query.return_value = {"Items": [server_big, server_small]}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_regions(
                ["us-east-1"],
                filters={"minRamBytes": 4294967296},
            )

        assert len(result) == 1
        assert result[0]["sourceServerID"] == "s-001"



class TestQueryByRegionsDeduplication:
    """Tests for deduplication behavior preservation (Regression 3.1)."""

    def test_deduplicates_by_source_server_id(self, mock_inventory_table, fresh_timestamp):
        """Regression 3.1: must deduplicate by sourceServerID, keeping most recent."""
        older_time = "2025-01-01T00:00:00+00:00"
        newer_time = "2025-06-01T00:00:00+00:00"

        server_old = _make_server("s-001", "us-east-1", last_updated_dt=older_time)
        server_new = _make_server("s-001", "us-east-1", last_updated_dt=newer_time)
        server_new["hostname"] = "updated-host"

        # GSI query returns duplicates
        mock_inventory_table.query.return_value = {"Items": [server_old, server_new]}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_regions(["us-east-1"])

        assert len(result) == 1
        assert result[0]["hostname"] == "updated-host"

    def test_no_duplicates_passes_through(self, mock_inventory_table, fresh_timestamp):
        """Regression 3.1: unique servers should all be returned."""
        servers = [_make_server(f"s-{i:03d}", "us-east-1") for i in range(5)]

        # GSI query returns unique servers
        mock_inventory_table.query.return_value = {"Items": servers}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_regions(["us-east-1"])

        assert len(result) == 5


class TestQueryByRegionsFallbackBehavior:
    """Tests for fallback and error handling behavior preservation."""

    def test_stale_inventory_returns_empty(self, mock_inventory_table, stale_timestamp):
        """Regression 3.2: stale inventory without update_on_fallback returns empty list."""
        mock_inventory_table.scan.return_value = {
            "Items": [{"sourceServerID": "s-123", "lastUpdated": stale_timestamp}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ):
            result = query_inventory_by_regions(["us-east-1"])

        assert result == []

    def test_stale_inventory_with_update_on_fallback(self, mock_inventory_table, stale_timestamp):
        """Regression 3.2: stale inventory with update_on_fallback=True triggers DRS API fallback."""
        mock_inventory_table.scan.return_value = {
            "Items": [{"sourceServerID": "s-123", "lastUpdated": stale_timestamp}]
        }

        mock_drs_client = Mock()
        mock_drs_client.describe_source_servers.return_value = {
            "items": [{"sourceServerID": "s-001", "hostname": "web-01"}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query._get_drs_client",
            return_value=mock_drs_client,
        ), patch(
            "shared.inventory_query.publish_metric",
        ):
            result = query_inventory_by_regions(
                ["us-east-1"], update_on_fallback=True
            )

        assert len(result) == 1
        assert result[0]["sourceServerID"] == "s-001"

    def test_table_not_configured_returns_empty(self):
        """Regression 3.4: unconfigured table returns empty list."""
        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=None,
        ):
            result = query_inventory_by_regions(["us-east-1"])

        assert result == []

    def test_client_error_returns_empty(self, mock_inventory_table, fresh_timestamp):
        """Regression 3.4: ClientError during query returns empty list."""
        # GSI query raises ClientError
        mock_inventory_table.query.side_effect = ClientError(
            {"Error": {"Code": "ValidationException"}}, "Query"
        )
        # Fallback scan also raises to trigger outer error handler
        mock_inventory_table.scan.side_effect = ClientError(
            {"Error": {"Code": "ValidationException"}}, "Scan"
        )

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_regions(["us-east-1"])

        assert result == []

    def test_gsi_not_found_falls_back_to_scan(self, mock_inventory_table, fresh_timestamp):
        """Design: if GSI doesn't exist yet, should fall back to scan gracefully."""
        server = _make_server("s-001", "us-east-1")

        mock_inventory_table.query.side_effect = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "GSI not found"}},
            "Query",
        )
        mock_inventory_table.scan.return_value = {"Items": [server]}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_regions(["us-east-1"])

        assert len(result) == 1
        assert result[0]["sourceServerID"] == "s-001"


class TestQueryByRegionsCloudWatchMetrics:
    """Tests for CloudWatch metrics publishing preservation (Regression 3.7)."""

    def test_publishes_hit_metric_on_success(self, mock_inventory_table, fresh_timestamp):
        """Regression 3.7: successful query must publish InventoryDatabaseHits metric."""
        server = _make_server("s-001", "us-east-1")

        # GSI query returns results
        mock_inventory_table.query.return_value = {"Items": [server]}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ), patch(
            "shared.inventory_query.publish_metric",
        ) as mock_publish:
            query_inventory_by_regions(["us-east-1"])

        mock_publish.assert_called_with("InventoryDatabaseHits", 1)

    def test_publishes_miss_metric_on_fallback(self, mock_inventory_table, stale_timestamp):
        """Regression 3.7: DRS API fallback must publish InventoryDatabaseMisses metric."""
        mock_inventory_table.scan.return_value = {
            "Items": [{"sourceServerID": "s-123", "lastUpdated": stale_timestamp}]
        }

        mock_drs_client = Mock()
        mock_drs_client.describe_source_servers.return_value = {"items": []}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query._get_drs_client",
            return_value=mock_drs_client,
        ), patch(
            "shared.inventory_query.publish_metric",
        ) as mock_publish:
            query_inventory_by_regions(["us-east-1"], update_on_fallback=True)

        mock_publish.assert_called_with("InventoryDatabaseMisses", 1)



class TestQueryByStagingAccountGSI:
    """Tests for query_inventory_by_staging_account() using StagingAccountIndex GSI."""

    def test_staging_account_query(self, mock_inventory_table, fresh_timestamp):
        """Fix 3: should use StagingAccountIndex GSI instead of scan."""
        server = _make_server("s-001", "us-east-1", staging_account_id="222222222222")

        # GSI query returns results
        mock_inventory_table.query.return_value = {"Items": [server]}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_staging_account("222222222222")

        assert len(result) == 1
        assert result[0]["stagingAccountId"] == "222222222222"
        # Verify StagingAccountIndex GSI was used
        mock_inventory_table.query.assert_called()
        query_call_kwargs = mock_inventory_table.query.call_args_list[0][1]
        assert query_call_kwargs["IndexName"] == "StagingAccountIndex"

    def test_staging_account_with_region_filter(self, mock_inventory_table, fresh_timestamp):
        """Fix 3: region post-filter should work after GSI query."""
        server_east = _make_server("s-001", "us-east-1", staging_account_id="222222222222")
        server_west = _make_server("s-002", "us-west-2", staging_account_id="222222222222")

        # GSI query returns all servers for the staging account
        mock_inventory_table.query.return_value = {"Items": [server_east, server_west]}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_staging_account(
                "222222222222", regions=["us-east-1"]
            )

        assert len(result) == 1
        assert result[0]["replicationRegion"] == "us-east-1"

    def test_staging_account_stale_returns_empty(self, mock_inventory_table, stale_timestamp):
        """Regression: stale inventory returns empty list."""
        mock_inventory_table.scan.return_value = {
            "Items": [{"sourceServerID": "s-123", "lastUpdated": stale_timestamp}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ):
            result = query_inventory_by_staging_account("222222222222")

        assert result == []

    def test_staging_account_table_not_configured(self):
        """Regression: unconfigured table returns empty list."""
        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=None,
        ):
            result = query_inventory_by_staging_account("222222222222")

        assert result == []

    def test_staging_account_client_error(self, mock_inventory_table, fresh_timestamp):
        """Regression: ClientError returns empty list."""
        # GSI query raises ClientError
        mock_inventory_table.query.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable"}}, "Query"
        )

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_staging_account("222222222222")

        assert result == []

    def test_staging_account_pagination(self, mock_inventory_table, fresh_timestamp):
        """Regression: pagination handling must be preserved."""
        server1 = _make_server("s-001", "us-east-1", staging_account_id="222222222222")
        server2 = _make_server("s-002", "us-east-1", staging_account_id="222222222222")

        # GSI query returns paginated results
        mock_inventory_table.query.side_effect = [
            {
                "Items": [server1],
                "LastEvaluatedKey": {"sourceServerArn": "arn:1"},
            },
            {"Items": [server2]},
        ]

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_inventory_table,
        ), patch(
            "shared.inventory_query.is_inventory_fresh",
            return_value=True,
        ):
            result = query_inventory_by_staging_account("222222222222")

        assert len(result) == 2
