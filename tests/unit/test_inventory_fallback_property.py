"""
Property-Based Tests for Inventory Fallback and Topology Preservation

Tests Properties 10 and 13 from the design document:
- Property 10: Inventory Database Updates During Fallback
- Property 13: Failback Topology Preservation

Uses Hypothesis for property-based testing with minimum 100 iterations.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest
from hypothesis import given, settings, strategies as st

# Add lambda directory to path
lambda_path = os.path.join(os.path.dirname(__file__), "../../lambda")
sys.path.insert(0, lambda_path)

# Set environment variables before importing
os.environ["DRS_REGION_STATUS_TABLE"] = "test-drs-region-status"
os.environ["SOURCE_SERVER_INVENTORY_TABLE"] = "test-source-server-inventory"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

from shared import inventory_query
from shared.drs_regions import DRS_REGIONS


# Test data generators
@st.composite
def server_id(draw):
    """Generate a valid DRS source server ID."""
    hex_chars = "0123456789abcdef"
    return "s-" + "".join(draw(st.sampled_from(hex_chars)) for _ in range(17))


@st.composite
def region_list(draw):
    """Generate a list of 1-5 regions from DRS_REGIONS."""
    count = draw(st.integers(min_value=1, max_value=5))
    return draw(st.lists(st.sampled_from(DRS_REGIONS), min_size=count, max_size=count, unique=True))


@st.composite
def source_server_data(draw):
    """Generate source server data from DRS API."""
    account_id = "123456789012"
    instance_id = "i-" + "".join(draw(st.sampled_from("0123456789abcdef")) for _ in range(17))
    region = draw(st.sampled_from(DRS_REGIONS))
    
    return {
        "sourceServerID": draw(server_id()),
        "hostname": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "Pd")))),
        "arn": f"arn:aws:drs:{region}:{account_id}:source-server/{draw(server_id())}",
        "tags": {},
        "dataReplicationInfo": {"dataReplicationState": "CONTINUOUS"},
        "lifeCycle": {"state": "READY_FOR_LAUNCH"},
        "sourceProperties": {
            "cpus": [{"cores": draw(st.integers(min_value=1, max_value=64))}],
            "ram": draw(st.integers(min_value=1024, max_value=1048576)),
            "disks": [],
            "identificationHints": {
                "awsInstanceID": f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"
            },
        },
    }


@st.composite
def inventory_record(draw, with_topology=True):
    """Generate an inventory database record."""
    record = {
        "sourceServerID": draw(server_id()),
        "region": draw(st.sampled_from(DRS_REGIONS)),
        "hostname": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "Pd")))),
        "replicationState": draw(st.sampled_from(["CONTINUOUS", "STOPPED", "DISCONNECTED"])),
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
    }

    if with_topology:
        record.update(
            {
                "originalSourceRegion": draw(st.sampled_from(DRS_REGIONS)),
                "originalAccountId": draw(
                    st.text(min_size=12, max_size=12, alphabet=st.characters(whitelist_categories=("Nd",)))
                ),
                "originalReplicationConfigTemplateId": f"rct-{draw(st.text(min_size=6, max_size=6, alphabet='0123456789abcdef'))}",
                "topologyLastUpdated": datetime.now(timezone.utc).isoformat(),
            }
        )

    return record


@st.composite
def stale_timestamp(draw):
    """Generate a timestamp that makes inventory stale (>5 minutes old)."""
    minutes_old = draw(st.integers(min_value=6, max_value=60))
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_old)).isoformat()


# Property 10: Inventory Database Updates During Fallback
@settings(max_examples=100, deadline=None)
@given(regions=region_list(), servers=st.lists(source_server_data(), min_size=1, max_size=5))
def test_property_10_inventory_updated_during_fallback(regions, servers):
    """
    Feature: active-region-filtering
    Property 10: Inventory Database Updates During Fallback

    For any operation that falls back to DRS API calls due to stale or missing
    inventory data, the operation should update the inventory database with the
    retrieved server data before returning results.

    Validates: Requirements 12.10
    """
    with patch("shared.inventory_query.get_inventory_table") as mock_table:
        with patch("shared.inventory_query._get_drs_client") as mock_get_client:
            with patch("shared.inventory_query.is_inventory_fresh") as mock_is_fresh:
                # Setup: Mock inventory as stale (triggers fallback)
                mock_is_fresh.return_value = False

                # Setup: Mock DynamoDB table
                mock_dynamodb_table = MagicMock()
                mock_table.return_value = mock_dynamodb_table

                # Setup: Mock inventory table returns empty (no cached data)
                mock_dynamodb_table.query.return_value = {"Items": []}

                # Setup: Mock DRS client
                mock_drs_client = MagicMock()
                mock_get_client.return_value = mock_drs_client

                # Setup: Mock DRS API response (describe_source_servers returns items directly)
                mock_drs_client.describe_source_servers.return_value = {"items": servers}

                # Execute: Call query_inventory_by_regions with update_on_fallback=True
                result = inventory_query.query_inventory_by_regions(regions, update_on_fallback=True)

                # Verify: DRS API was called (fallback occurred)
                assert mock_get_client.called, "Should call DRS API when inventory is stale"

                # Verify: Inventory database was updated
                assert mock_dynamodb_table.put_item.called, "Should update inventory database during fallback"

                # Verify: Number of put_item calls matches number of servers * regions
                put_item_calls = mock_dynamodb_table.put_item.call_count
                expected_calls = len(servers) * len(regions)
                assert put_item_calls == expected_calls, (
                    f"Should update inventory for all {len(servers)} servers in {len(regions)} regions, "
                    f"expected {expected_calls} updates, got {put_item_calls}"
                )

                # Verify: Result contains server data
                assert len(result) >= len(servers), f"Should return at least {len(servers)} servers from fallback"


@settings(max_examples=100, deadline=None)
@given(regions=region_list())
def test_property_10_no_update_when_inventory_fresh(regions):
    """
    Feature: active-region-filtering
    Property 10: Inventory Database Updates During Fallback

    When inventory is fresh, no fallback should occur and no database updates
    should be made.

    Validates: Requirements 12.10
    """
    with patch("shared.inventory_query.get_inventory_table") as mock_table:
        with patch("shared.inventory_query._get_drs_client") as mock_get_client:
            with patch("shared.inventory_query.is_inventory_fresh") as mock_is_fresh:
                # Setup: Mock inventory as fresh (no fallback)
                mock_is_fresh.return_value = True

                # Setup: Mock DynamoDB table
                mock_dynamodb_table = MagicMock()
                mock_table.return_value = mock_dynamodb_table

                # Setup: Mock inventory table scan returns cached data
                mock_dynamodb_table.scan.return_value = {"Items": []}

                # Execute: Call query_inventory_by_regions with update_on_fallback=True
                result = inventory_query.query_inventory_by_regions(regions, update_on_fallback=True)

                # Verify: DRS API was NOT called (no fallback)
                assert not mock_get_client.called, "Should not call DRS API when inventory is fresh"

                # Verify: Inventory database was NOT updated
                assert not mock_dynamodb_table.put_item.called, "Should not update inventory when fresh"


@settings(max_examples=100, deadline=None)
@given(regions=region_list(), servers=st.lists(source_server_data(), min_size=1, max_size=5))
def test_property_10_no_update_when_update_on_fallback_false(regions, servers):
    """
    Feature: active-region-filtering
    Property 10: Inventory Database Updates During Fallback

    When update_on_fallback=False, even if inventory is stale, the database
    should not be updated (backward compatibility).

    Validates: Requirements 12.10
    """
    with patch("shared.inventory_query.get_inventory_table") as mock_table:
        with patch("shared.inventory_query._get_drs_client") as mock_get_client:
            with patch("shared.inventory_query.is_inventory_fresh") as mock_is_fresh:
                # Setup: Mock inventory as stale
                mock_is_fresh.return_value = False

                # Setup: Mock DynamoDB table
                mock_dynamodb_table = MagicMock()
                mock_table.return_value = mock_dynamodb_table

                # Setup: Mock inventory table scan returns empty
                mock_dynamodb_table.scan.return_value = {"Items": []}

                # Setup: Mock DRS client
                mock_drs_client = MagicMock()
                mock_get_client.return_value = mock_drs_client

                # Setup: Mock DRS API response
                mock_drs_client.describe_source_servers.return_value = {"items": servers}

                # Execute: Call query_inventory_by_regions with update_on_fallback=False
                result = inventory_query.query_inventory_by_regions(regions, update_on_fallback=False)

                # Verify: DRS API was NOT called (no fallback when update_on_fallback=False)
                assert not mock_get_client.called, "Should not call DRS API when update_on_fallback=False"

                # Verify: Inventory database was NOT updated
                assert not mock_dynamodb_table.put_item.called, "Should not update inventory when update_on_fallback=False"

                # Verify: Result is empty (stale inventory, no fallback)
                assert len(result) == 0, "Should return empty list when inventory is stale and update_on_fallback=False"


# Property 13: Failback Topology Preservation
@settings(max_examples=100, deadline=None)
@given(existing_record=inventory_record(with_topology=True), new_server_data=source_server_data())
def test_property_13_topology_preserved_on_update(existing_record, new_server_data):
    """
    Feature: active-region-filtering
    Property 13: Failback Topology Preservation

    When updating an existing server record during inventory sync, the original
    topology fields (originalSourceRegion, originalAccountId, originalReplicationConfigTemplateId)
    should be preserved from the existing record.

    Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9
    """
    # Make server IDs match
    new_server_data["sourceServerID"] = existing_record["sourceServerID"]

    with patch("shared.inventory_query.get_inventory_table") as mock_table:
        # Setup: Mock DynamoDB table
        mock_dynamodb_table = MagicMock()
        mock_table.return_value = mock_dynamodb_table

        # Setup: Mock get_item to return existing record with topology
        mock_dynamodb_table.get_item.return_value = {"Item": existing_record}

        # Execute: Call _update_inventory_with_topology_preservation
        inventory_query._update_inventory_with_topology_preservation(
            new_server_data, existing_record["region"]
        )

        # Verify: put_item was called
        assert mock_dynamodb_table.put_item.called, "Should update inventory record"

        # Verify: Topology fields were preserved
        put_item_call = mock_dynamodb_table.put_item.call_args
        updated_item = put_item_call[1]["Item"]

        assert updated_item["originalSourceRegion"] == existing_record["originalSourceRegion"], (
            f"Should preserve originalSourceRegion: {existing_record['originalSourceRegion']}, "
            f"got {updated_item.get('originalSourceRegion')}"
        )

        assert updated_item["originalAccountId"] == existing_record["originalAccountId"], (
            f"Should preserve originalAccountId: {existing_record['originalAccountId']}, "
            f"got {updated_item.get('originalAccountId')}"
        )

        if "originalReplicationConfigTemplateId" in existing_record:
            assert updated_item["originalReplicationConfigTemplateId"] == existing_record["originalReplicationConfigTemplateId"], (
                f"Should preserve originalReplicationConfigTemplateId: "
                f"{existing_record['originalReplicationConfigTemplateId']}, "
                f"got {updated_item.get('originalReplicationConfigTemplateId')}"
            )


@settings(max_examples=100, deadline=None)
@given(new_server_data=source_server_data(), region=st.sampled_from(DRS_REGIONS))
def test_property_13_topology_captured_for_new_server(new_server_data, region):
    """
    Feature: active-region-filtering
    Property 13: Failback Topology Preservation

    When adding a new server to inventory (no existing record), the current
    region and account should be captured as the original topology.

    Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9
    """
    with patch("shared.inventory_query.get_inventory_table") as mock_table:
        # Setup: Mock DynamoDB table
        mock_dynamodb_table = MagicMock()
        mock_table.return_value = mock_dynamodb_table

        # Setup: Mock get_item to return no existing record
        mock_dynamodb_table.get_item.return_value = {}

        # Execute: Call _update_inventory_with_topology_preservation
        account_id = "123456789012"
        inventory_query._update_inventory_with_topology_preservation(new_server_data, region)

        # Verify: put_item was called
        assert mock_dynamodb_table.put_item.called, "Should create inventory record"

        # Verify: Topology fields were captured from current state
        put_item_call = mock_dynamodb_table.put_item.call_args
        updated_item = put_item_call[1]["Item"]

        assert updated_item["originalSourceRegion"] == region, (
            f"Should capture current region as originalSourceRegion: {region}, " f"got {updated_item.get('originalSourceRegion')}"
        )

        assert updated_item["originalAccountId"] == account_id, (
            f"Should capture current account as originalAccountId: {account_id}, " f"got {updated_item.get('originalAccountId')}"
        )

        assert "topologyLastUpdated" in updated_item, "Should set topologyLastUpdated timestamp"


@settings(max_examples=100, deadline=None)
@given(record=inventory_record(with_topology=True))
def test_property_13_get_failback_topology_returns_correct_data(record):
    """
    Feature: active-region-filtering
    Property 13: Failback Topology Preservation

    The get_failback_topology function should return the original topology
    fields from the inventory record for use in failback operations.

    Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9
    """
    with patch("shared.inventory_query.get_inventory_table") as mock_table:
        # Setup: Mock DynamoDB table
        mock_dynamodb_table = MagicMock()
        mock_table.return_value = mock_dynamodb_table

        # Setup: Mock get_item to return record with topology
        mock_dynamodb_table.get_item.return_value = {"Item": record}

        # Execute: Call get_failback_topology
        result = inventory_query.get_failback_topology(record["sourceServerID"], record["region"])

        # Verify: Result contains original topology fields
        assert result["originalSourceRegion"] == record["originalSourceRegion"], (
            f"Should return originalSourceRegion: {record['originalSourceRegion']}, " f"got {result.get('originalSourceRegion')}"
        )

        assert result["originalAccountId"] == record["originalAccountId"], (
            f"Should return originalAccountId: {record['originalAccountId']}, " f"got {result.get('originalAccountId')}"
        )

        if "originalReplicationConfigTemplateId" in record:
            assert result["originalReplicationConfigTemplateId"] == record["originalReplicationConfigTemplateId"], (
                f"Should return originalReplicationConfigTemplateId: "
                f"{record['originalReplicationConfigTemplateId']}, "
                f"got {result.get('originalReplicationConfigTemplateId')}"
            )

        assert "topologyLastUpdated" in result, "Should return topologyLastUpdated timestamp"


@settings(max_examples=100, deadline=None)
@given(server_id_val=server_id(), region=st.sampled_from(DRS_REGIONS))
def test_property_13_get_failback_topology_handles_missing_server(server_id_val, region):
    """
    Feature: active-region-filtering
    Property 13: Failback Topology Preservation

    When get_failback_topology is called for a server that doesn't exist in
    inventory, it should return None.

    Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9
    """
    with patch("shared.inventory_query.get_inventory_table") as mock_table:
        # Setup: Mock DynamoDB table
        mock_dynamodb_table = MagicMock()
        mock_table.return_value = mock_dynamodb_table

        # Setup: Mock get_item to return no record
        mock_dynamodb_table.get_item.return_value = {}

        # Execute: Call get_failback_topology
        result = inventory_query.get_failback_topology(server_id_val, region)

        # Verify: Should return None for missing server
        assert result is None, f"Should return None for missing server {server_id_val}"


@settings(max_examples=100, deadline=None)
@given(record=inventory_record(with_topology=False))
def test_property_13_get_failback_topology_handles_missing_topology(record):
    """
    Feature: active-region-filtering
    Property 13: Failback Topology Preservation

    When get_failback_topology is called for a server that exists but has no
    topology data (legacy server), it should return None for topology fields
    and log a warning.

    Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9
    """
    with patch("shared.inventory_query.get_inventory_table") as mock_table:
        with patch("shared.inventory_query.logger") as mock_logger:
            # Setup: Mock DynamoDB table
            mock_dynamodb_table = MagicMock()
            mock_table.return_value = mock_dynamodb_table

            # Setup: Mock get_item to return record without topology
            mock_dynamodb_table.get_item.return_value = {"Item": record}

            # Execute: Call get_failback_topology
            result = inventory_query.get_failback_topology(record["sourceServerID"], record["region"])

            # Verify: Should return None for server without topology
            assert result is None, "Should return None for server without topology data"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
