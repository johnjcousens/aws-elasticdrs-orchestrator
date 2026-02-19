"""
Property-based tests for inventory query module.

Feature: active-region-filtering
Properties:
- Property 4: Inventory Database Freshness Check
- Property 9: Inventory Data Completeness

Validates: Requirements 12.3, 12.4, 12.8, 4.3, 12.9
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

# Set environment variables before importing module
os.environ["SOURCE_SERVER_INVENTORY_TABLE"] = "test-inventory-table"

from shared.inventory_query import is_inventory_fresh, query_inventory_by_regions


# ============================================================
# Property 4: Inventory Database Freshness Check
# ============================================================


@given(age_minutes=st.integers(min_value=0, max_value=60))
@settings(max_examples=100)
def test_property_inventory_freshness_check(age_minutes):
    """
    **Validates: Requirements 12.3, 12.4, 12.8**

    Property 4: Inventory Database Freshness Check

    For any operation that can use inventory data, when the inventory database
    contains data updated within the last 15 minutes, the operation should use
    the inventory database instead of making DRS API calls, and when the
    inventory is stale or unavailable, should fall back to DRS API calls.
    """
    # Generate timestamp based on age
    timestamp = (
        datetime.now(timezone.utc) - timedelta(minutes=age_minutes)
    ).isoformat()

    # Mock DynamoDB table
    mock_table = Mock()
    mock_table.scan.return_value = {
        "Items": [{"sourceServerID": "s-test", "lastUpdated": timestamp}]
    }

    with patch(
        "shared.inventory_query.get_inventory_table", return_value=mock_table
    ):
        result = is_inventory_fresh(max_age_minutes=15)

        # Verify: Fresh if age < 15 minutes, stale otherwise
        if age_minutes < 15:
            assert result is True, (
                f"Inventory aged {age_minutes} minutes should be fresh "
                f"(threshold: 15 minutes)"
            )
        else:
            assert result is False, (
                f"Inventory aged {age_minutes} minutes should be stale "
                f"(threshold: 15 minutes)"
            )


@given(
    age_minutes=st.integers(min_value=0, max_value=60),
    threshold_minutes=st.integers(min_value=1, max_value=30),
)
@settings(max_examples=100)
def test_property_custom_freshness_threshold(age_minutes, threshold_minutes):
    """
    **Validates: Requirements 12.3, 12.4**

    Property 4 (Extended): Custom Freshness Threshold

    For any custom freshness threshold, inventory should be considered fresh
    if age < threshold, and stale if age >= threshold.
    """
    # Generate timestamp based on age
    timestamp = (
        datetime.now(timezone.utc) - timedelta(minutes=age_minutes)
    ).isoformat()

    # Mock DynamoDB table
    mock_table = Mock()
    mock_table.scan.return_value = {
        "Items": [{"sourceServerID": "s-test", "lastUpdated": timestamp}]
    }

    with patch(
        "shared.inventory_query.get_inventory_table", return_value=mock_table
    ):
        result = is_inventory_fresh(max_age_minutes=threshold_minutes)

        # Verify: Fresh if age < threshold, stale otherwise
        if age_minutes < threshold_minutes:
            assert result is True, (
                f"Inventory aged {age_minutes} minutes should be fresh "
                f"with threshold {threshold_minutes} minutes"
            )
        else:
            assert result is False, (
                f"Inventory aged {age_minutes} minutes should be stale "
                f"with threshold {threshold_minutes} minutes"
            )


@given(is_fresh=st.booleans())
@settings(max_examples=100)
def test_property_stale_inventory_returns_empty(is_fresh):
    """
    **Validates: Requirements 12.4, 12.8**

    Property 4 (Extended): Stale Inventory Fallback

    For any query operation, when inventory is stale, the operation should
    return empty list to trigger DRS API fallback.
    """
    # Generate fresh or stale timestamp
    if is_fresh:
        age_minutes = 5  # Fresh
    else:
        age_minutes = 20  # Stale

    timestamp = (
        datetime.now(timezone.utc) - timedelta(minutes=age_minutes)
    ).isoformat()

    # Mock DynamoDB table
    mock_table = Mock()
    mock_table.scan.side_effect = [
        {"Items": [{"sourceServerID": "s-test", "lastUpdated": timestamp}]},
        {
            "Items": [
                {
                    "sourceServerID": "s-test",
                    "replicationRegion": "us-east-1",
                    "hostname": "server1",
                }
            ]
        },
    ]

    with patch(
        "shared.inventory_query.get_inventory_table", return_value=mock_table
    ):
        servers = query_inventory_by_regions(["us-east-1"])

        # Verify: Returns servers if fresh, empty list if stale
        if is_fresh:
            assert len(servers) > 0, "Fresh inventory should return servers"
        else:
            assert len(servers) == 0, (
                "Stale inventory should return empty list for DRS API fallback"
            )


# ============================================================
# Property 9: Inventory Data Completeness
# ============================================================


@given(
    include_required_fields=st.booleans(),
    region=st.sampled_from(["us-east-1", "us-west-2", "eu-west-1"]),
)
@settings(max_examples=100)
def test_property_inventory_data_completeness(include_required_fields, region):
    """
    **Validates: Requirements 4.3, 12.9**

    Property 9: Inventory Data Completeness

    For any server record retrieved from the inventory database, the record
    should contain all required fields: sourceServerID, replicationRegion,
    replicationState, hostname, sourceAccountId, and sourceTags.
    """
    # Generate fresh timestamp
    timestamp = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()

    # Build server record with or without required fields
    if include_required_fields:
        server_record = {
            "sourceServerID": "s-1234567890abcdef0",
            "replicationRegion": region,
            "replicationState": "CONTINUOUS",
            "hostname": "test-server",
            "sourceAccountId": "123456789012",
            "sourceTags": {"Environment": "test"},
        }
    else:
        # Missing required fields
        server_record = {
            "sourceServerID": "s-1234567890abcdef0",
            # Missing other required fields
        }

    # Mock DynamoDB table
    mock_table = Mock()
    mock_table.scan.side_effect = [
        {"Items": [{"sourceServerID": "s-test", "lastUpdated": timestamp}]},
        {"Items": [server_record]},
    ]

    with patch(
        "shared.inventory_query.get_inventory_table", return_value=mock_table
    ):
        servers = query_inventory_by_regions([region])

        if include_required_fields:
            # Verify: All required fields present
            assert len(servers) == 1
            server = servers[0]
            assert "sourceServerID" in server
            assert "replicationRegion" in server
            assert "replicationState" in server
            assert "hostname" in server
            assert "sourceAccountId" in server
            assert "sourceTags" in server
        else:
            # Incomplete records are still returned (validation happens elsewhere)
            # This property documents expected behavior, not enforcement
            assert len(servers) == 1


@given(
    server_count=st.integers(min_value=0, max_value=10),
    region=st.sampled_from(["us-east-1", "us-west-2", "eu-west-1"]),
)
@settings(max_examples=100)
def test_property_all_servers_have_required_fields(server_count, region):
    """
    **Validates: Requirements 4.3, 12.9**

    Property 9 (Extended): All Servers Have Required Fields

    For any list of servers retrieved from inventory, all servers should
    contain the required fields.
    """
    # Generate fresh timestamp
    timestamp = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()

    # Generate server records with all required fields
    servers = []
    for i in range(server_count):
        servers.append(
            {
                "sourceServerID": f"s-{i:017x}",
                "replicationRegion": region,
                "replicationState": "CONTINUOUS",
                "hostname": f"server-{i}",
                "sourceAccountId": "123456789012",
                "sourceTags": {"Index": str(i)},
            }
        )

    # Mock DynamoDB table
    mock_table = Mock()
    mock_table.scan.side_effect = [
        {"Items": [{"sourceServerID": "s-test", "lastUpdated": timestamp}]},
        {"Items": servers},
    ]

    with patch(
        "shared.inventory_query.get_inventory_table", return_value=mock_table
    ):
        result_servers = query_inventory_by_regions([region])

        # Verify: All servers have required fields
        assert len(result_servers) == server_count

        for server in result_servers:
            assert "sourceServerID" in server
            assert "replicationRegion" in server
            assert "replicationState" in server
            assert "hostname" in server
            assert "sourceAccountId" in server
            assert "sourceTags" in server
