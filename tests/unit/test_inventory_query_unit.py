"""
Unit tests for inventory query module.

Tests specific examples, edge cases, and error conditions for
inventory database queries and freshness checks.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from botocore.exceptions import ClientError

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

# Set environment variables before importing module
os.environ["SOURCE_SERVER_INVENTORY_TABLE"] = "test-inventory-table"

from shared.inventory_query import (
    get_inventory_table,
    get_server_by_id,
    is_inventory_fresh,
    query_inventory_by_regions,
    query_inventory_by_staging_account,
)


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table for testing."""
    table = Mock()
    table.scan = Mock()
    table.get_item = Mock()
    return table


@pytest.fixture
def fresh_timestamp():
    """Generate a fresh timestamp (5 minutes ago)."""
    return (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()


@pytest.fixture
def stale_timestamp():
    """Generate a stale timestamp (20 minutes ago)."""
    return (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()


class TestIsInventoryFresh:
    """Test inventory freshness checking."""

    def test_fresh_inventory_returns_true(
        self, mock_dynamodb_table, fresh_timestamp
    ):
        """Test that fresh inventory (< 15 minutes) returns True."""
        mock_dynamodb_table.scan.return_value = {
            "Items": [{"sourceServerID": "s-123", "lastUpdated": fresh_timestamp}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            result = is_inventory_fresh()

        assert result is True
        mock_dynamodb_table.scan.assert_called_once_with(Limit=1)

    def test_stale_inventory_returns_false(
        self, mock_dynamodb_table, stale_timestamp
    ):
        """Test that stale inventory (> 15 minutes) returns False."""
        mock_dynamodb_table.scan.return_value = {
            "Items": [{"sourceServerID": "s-123", "lastUpdated": stale_timestamp}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            result = is_inventory_fresh()

        assert result is False

    def test_empty_inventory_returns_false(self, mock_dynamodb_table):
        """Test that empty inventory table returns False."""
        mock_dynamodb_table.scan.return_value = {"Items": []}

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            result = is_inventory_fresh()

        assert result is False

    def test_missing_timestamp_returns_false(self, mock_dynamodb_table):
        """Test that record without lastUpdated returns False."""
        mock_dynamodb_table.scan.return_value = {
            "Items": [{"sourceServerID": "s-123"}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            result = is_inventory_fresh()

        assert result is False

    def test_table_not_configured_returns_false(self):
        """Test that unconfigured table returns False."""
        with patch(
            "shared.inventory_query.get_inventory_table", return_value=None
        ):
            result = is_inventory_fresh()

        assert result is False

    def test_dynamodb_error_returns_false(self, mock_dynamodb_table):
        """Test that DynamoDB error returns False."""
        mock_dynamodb_table.scan.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable"}}, "Scan"
        )

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            result = is_inventory_fresh()

        assert result is False

    def test_custom_max_age(self, mock_dynamodb_table):
        """Test custom max_age_minutes parameter."""
        # Timestamp 10 minutes ago
        timestamp = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        mock_dynamodb_table.scan.return_value = {
            "Items": [{"sourceServerID": "s-123", "lastUpdated": timestamp}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            # Fresh with 15 minute threshold
            assert is_inventory_fresh(max_age_minutes=15) is True

            # Stale with 5 minute threshold
            assert is_inventory_fresh(max_age_minutes=5) is False


class TestQueryInventoryByRegions:
    """Test querying inventory by regions."""

    def test_query_single_region(self, mock_dynamodb_table, fresh_timestamp):
        """Test querying a single region."""
        mock_dynamodb_table.scan.side_effect = [
            {"Items": [{"sourceServerID": "s-123", "lastUpdated": fresh_timestamp}]},
            {
                "Items": [
                    {
                        "sourceServerID": "s-123",
                        "replicationRegion": "us-east-1",
                        "hostname": "server1",
                    }
                ]
            },
        ]

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            servers = query_inventory_by_regions(["us-east-1"])

        assert len(servers) == 1
        assert servers[0]["sourceServerID"] == "s-123"
        assert servers[0]["replicationRegion"] == "us-east-1"

    def test_query_multiple_regions(self, mock_dynamodb_table, fresh_timestamp):
        """Test querying multiple regions."""
        mock_dynamodb_table.scan.side_effect = [
            {"Items": [{"sourceServerID": "s-123", "lastUpdated": fresh_timestamp}]},
            {
                "Items": [
                    {
                        "sourceServerID": "s-123",
                        "replicationRegion": "us-east-1",
                    },
                    {
                        "sourceServerID": "s-456",
                        "replicationRegion": "us-west-2",
                    },
                ]
            },
        ]

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            servers = query_inventory_by_regions(["us-east-1", "us-west-2"])

        assert len(servers) == 2

    def test_query_with_hostname_filter(
        self, mock_dynamodb_table, fresh_timestamp
    ):
        """Test querying with hostname filter."""
        mock_dynamodb_table.scan.side_effect = [
            {"Items": [{"sourceServerID": "s-123", "lastUpdated": fresh_timestamp}]},
            {
                "Items": [
                    {
                        "sourceServerID": "s-123",
                        "hostname": "web-server-01",
                    }
                ]
            },
        ]

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            servers = query_inventory_by_regions(
                ["us-east-1"], filters={"hostname": "web-server-01"}
            )

        assert len(servers) == 1
        assert servers[0]["hostname"] == "web-server-01"

    def test_query_with_replication_state_filter(
        self, mock_dynamodb_table, fresh_timestamp
    ):
        """Test querying with replicationState filter."""
        mock_dynamodb_table.scan.side_effect = [
            {"Items": [{"sourceServerID": "s-123", "lastUpdated": fresh_timestamp}]},
            {
                "Items": [
                    {
                        "sourceServerID": "s-123",
                        "replicationState": "CONTINUOUS",
                    }
                ]
            },
        ]

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            servers = query_inventory_by_regions(
                ["us-east-1"], filters={"replicationState": "CONTINUOUS"}
            )

        assert len(servers) == 1
        assert servers[0]["replicationState"] == "CONTINUOUS"

    def test_query_with_pagination(self, mock_dynamodb_table, fresh_timestamp):
        """Test querying with DynamoDB pagination."""
        mock_dynamodb_table.scan.side_effect = [
            {"Items": [{"sourceServerID": "s-123", "lastUpdated": fresh_timestamp}]},
            {
                "Items": [{"sourceServerID": "s-123"}],
                "LastEvaluatedKey": {"sourceServerID": "s-123"},
            },
            {"Items": [{"sourceServerID": "s-456"}]},
        ]

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            servers = query_inventory_by_regions(["us-east-1"])

        assert len(servers) == 2

    def test_stale_inventory_returns_empty_list(
        self, mock_dynamodb_table, stale_timestamp
    ):
        """Test that stale inventory returns empty list for fallback."""
        mock_dynamodb_table.scan.return_value = {
            "Items": [{"sourceServerID": "s-123", "lastUpdated": stale_timestamp}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            servers = query_inventory_by_regions(["us-east-1"])

        assert servers == []

    def test_table_not_configured_returns_empty_list(self):
        """Test that unconfigured table returns empty list."""
        with patch(
            "shared.inventory_query.get_inventory_table", return_value=None
        ):
            servers = query_inventory_by_regions(["us-east-1"])

        assert servers == []

    def test_dynamodb_error_returns_empty_list(
        self, mock_dynamodb_table, fresh_timestamp
    ):
        """Test that DynamoDB error returns empty list."""
        mock_dynamodb_table.scan.side_effect = [
            {"Items": [{"sourceServerID": "s-123", "lastUpdated": fresh_timestamp}]},
            ClientError({"Error": {"Code": "ServiceUnavailable"}}, "Scan"),
        ]

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            servers = query_inventory_by_regions(["us-east-1"])

        assert servers == []


class TestQueryInventoryByStagingAccount:
    """Test querying inventory by staging account."""

    def test_query_staging_account(self, mock_dynamodb_table, fresh_timestamp):
        """Test querying by staging account ID."""
        mock_dynamodb_table.scan.side_effect = [
            {"Items": [{"sourceServerID": "s-123", "lastUpdated": fresh_timestamp}]},
            {
                "Items": [
                    {
                        "sourceServerID": "s-123",
                        "stagingAccountId": "123456789012",
                    }
                ]
            },
        ]

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            servers = query_inventory_by_staging_account("123456789012")

        assert len(servers) == 1
        assert servers[0]["stagingAccountId"] == "123456789012"

    def test_query_staging_account_with_regions(
        self, mock_dynamodb_table, fresh_timestamp
    ):
        """Test querying staging account with region filter."""
        mock_dynamodb_table.scan.side_effect = [
            {"Items": [{"sourceServerID": "s-123", "lastUpdated": fresh_timestamp}]},
            {
                "Items": [
                    {
                        "sourceServerID": "s-123",
                        "stagingAccountId": "123456789012",
                        "replicationRegion": "us-east-1",
                    }
                ]
            },
        ]

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            servers = query_inventory_by_staging_account(
                "123456789012", regions=["us-east-1"]
            )

        assert len(servers) == 1


class TestGetServerById:
    """Test getting server by ID."""

    def test_get_server_with_region(self, mock_dynamodb_table, fresh_timestamp):
        """Test getting server with replication region (direct lookup)."""
        mock_dynamodb_table.scan.return_value = {
            "Items": [{"sourceServerID": "s-123", "lastUpdated": fresh_timestamp}]
        }
        mock_dynamodb_table.get_item.return_value = {
            "Item": {
                "sourceServerID": "s-123",
                "replicationRegion": "us-east-1",
                "hostname": "server1",
            }
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            server = get_server_by_id("s-123", "us-east-1")

        assert server is not None
        assert server["sourceServerID"] == "s-123"
        mock_dynamodb_table.get_item.assert_called_once()

    def test_get_server_without_region(
        self, mock_dynamodb_table, fresh_timestamp
    ):
        """Test getting server without region (scan lookup)."""
        mock_dynamodb_table.scan.side_effect = [
            {"Items": [{"sourceServerID": "s-123", "lastUpdated": fresh_timestamp}]},
            {
                "Items": [
                    {
                        "sourceServerID": "s-123",
                        "hostname": "server1",
                    }
                ]
            },
        ]

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            server = get_server_by_id("s-123")

        assert server is not None
        assert server["sourceServerID"] == "s-123"

    def test_get_server_not_found(self, mock_dynamodb_table, fresh_timestamp):
        """Test getting server that doesn't exist."""
        mock_dynamodb_table.scan.side_effect = [
            {"Items": [{"sourceServerID": "s-123", "lastUpdated": fresh_timestamp}]},
            {"Items": []},
        ]

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            server = get_server_by_id("s-999")

        assert server is None

    def test_stale_inventory_returns_none(
        self, mock_dynamodb_table, stale_timestamp
    ):
        """Test that stale inventory returns None for fallback."""
        mock_dynamodb_table.scan.return_value = {
            "Items": [{"sourceServerID": "s-123", "lastUpdated": stale_timestamp}]
        }

        with patch(
            "shared.inventory_query.get_inventory_table",
            return_value=mock_dynamodb_table,
        ):
            server = get_server_by_id("s-123", "us-east-1")

        assert server is None
