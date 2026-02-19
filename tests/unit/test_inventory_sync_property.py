"""
Property-based tests for inventory sync region filtering and status updates.

Feature: active-region-filtering
Properties:
- Property 3: Region Status Table Updates
- Property 6: Cache Invalidation

Validates: Requirements 5.1, 5.3, 5.4, 5.5, 10.5
"""

import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.active_region_filter import (
    get_active_regions,
    invalidate_region_cache,
    update_region_status,
)
from shared.drs_regions import DRS_REGIONS


# ============================================================
# Strategies for generating test data
# ============================================================


@st.composite
def region_scan_result_strategy(draw):
    """
    Generate a region scan result with servers and status.

    Returns a dictionary with:
    - region: AWS region name
    - servers: List of server dictionaries
    - status: Region status (ACTIVE, ERROR, NOT_INITIALIZED, etc.)
    - serverCount: Number of servers
    - errorMessage: Optional error message
    """
    region = draw(st.sampled_from(DRS_REGIONS))
    server_count = draw(st.integers(min_value=0, max_value=100))

    # Generate servers
    servers = []
    for i in range(server_count):
        servers.append(
            {
                "sourceServerID": f"s-{region}-{i:04d}",
                "arn": f"arn:aws:drs:{region}:123456789012:source-server/s-{region}-{i:04d}",
                "_queryRegion": region,
                "_queryAccount": "123456789012",
            }
        )

    # Determine status based on server count and random error
    has_error = draw(st.booleans()) and server_count == 0
    if has_error:
        status = draw(
            st.sampled_from(
                [
                    "ERROR",
                    "NOT_INITIALIZED",
                    "IAM_PERMISSION_DENIED",
                    "SCP_DENIED",
                    "THROTTLED",
                    "REGION_NOT_OPTED_IN",
                    "REGION_NOT_ENABLED",
                    "ENDPOINT_UNREACHABLE",
                ]
            )
        )
        error_message = f"Mock error for {status}"
    else:
        status = "ACTIVE" if server_count > 0 else "NOT_INITIALIZED"
        error_message = None

    return {
        "region": region,
        "servers": servers,
        "status": status,
        "serverCount": server_count,
        "errorMessage": error_message,
    }


# ============================================================
# Property 3: Region Status Table Updates
# ============================================================


@settings(max_examples=100)
@given(scan_results=st.lists(region_scan_result_strategy(), min_size=1, max_size=28, unique_by=lambda x: x["region"]))
@pytest.mark.property
def test_property_region_status_table_updates(scan_results):
    """
    Property 3: Region Status Table Updates.

    Feature: active-region-filtering
    Property 3: For any source server inventory sync operation, when scanning
                a region, the operation should update the region status table
                with the current server count for that region, and if the scan
                fails, should record the error message in the table.

    **Validates: Requirements 5.1, 5.3, 5.4, 5.5**
    """
    # Arrange: Create mock region status table
    mock_table = MagicMock()

    # Track all put_item calls
    put_item_calls = []

    def capture_put_item(Item):
        put_item_calls.append(Item)
        return {}

    mock_table.put_item.side_effect = capture_put_item

    # Patch get_region_status_table to return our mock
    with patch("shared.active_region_filter.get_region_status_table", return_value=mock_table):
        # Act: Update region status for each scan result
        for result in scan_results:
            update_region_status(
                region=result["region"],
                server_count=result["serverCount"],
                error_message=result["errorMessage"],
            )

    # Assert: Each region should have been updated
    assert len(put_item_calls) == len(scan_results), (
        f"Expected {len(scan_results)} region status updates, " f"got {len(put_item_calls)}"
    )

    # Assert: Verify each update has correct data
    for result in scan_results:
        # Find the corresponding put_item call
        matching_calls = [call for call in put_item_calls if call["region"] == result["region"]]

        assert len(matching_calls) == 1, (
            f"Expected exactly 1 update for region {result['region']}, " f"got {len(matching_calls)}"
        )

        item = matching_calls[0]

        # Verify region
        assert item["region"] == result["region"], f"Region mismatch for {result['region']}"

        # Verify server count
        assert item["serverCount"] == result["serverCount"], (
            f"Server count mismatch for {result['region']}: "
            f"expected {result['serverCount']}, got {item['serverCount']}"
        )

        # Verify status is set correctly
        if result["errorMessage"]:
            assert item["status"] == "ERROR", (
                f"Status should be ERROR when error message present for {result['region']}, " f"got {item['status']}"
            )
        elif result["serverCount"] > 0:
            assert item["status"] == "AVAILABLE", (
                f"Status should be AVAILABLE when serverCount > 0 for {result['region']}, " f"got {item['status']}"
            )
        else:
            assert item["status"] == "UNINITIALIZED", (
                f"Status should be UNINITIALIZED when serverCount = 0 and no error for {result['region']}, "
                f"got {item['status']}"
            )

        # Verify error message handling
        if result["errorMessage"]:
            assert item["errorMessage"] == result["errorMessage"], (
                f"Error message mismatch for {result['region']}: "
                f"expected {result['errorMessage']}, got {item.get('errorMessage')}"
            )
        else:
            # Error message should be None when no error
            assert item["errorMessage"] is None, (
                f"Error message should be None when no error for {result['region']}, " f"got {item.get('errorMessage')}"
            )

        # Verify lastChecked timestamp is present and valid
        assert "lastChecked" in item, f"lastChecked missing for {result['region']}"
        assert isinstance(item["lastChecked"], str), f"lastChecked should be string for {result['region']}"
        # Verify timestamp format (ISO 8601)
        try:
            datetime.fromisoformat(item["lastChecked"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid timestamp format for {result['region']}: {item['lastChecked']}")


@settings(max_examples=50)
@given(
    region=st.sampled_from(DRS_REGIONS),
    server_count=st.integers(min_value=0, max_value=1000),
    error_message=st.one_of(st.none(), st.text(min_size=1, max_size=500)),
)
@pytest.mark.property
def test_property_region_status_update_idempotency(region, server_count, error_message):
    """
    Property 3 (supplemental): Region status updates are idempotent.

    Tests that calling update_region_status multiple times with the same
    data produces consistent results (last write wins).

    **Validates: Requirements 5.1, 5.3**
    """
    # Arrange: Create mock region status table
    mock_table = MagicMock()
    put_item_calls = []

    def capture_put_item(Item):
        put_item_calls.append(Item)
        return {}

    mock_table.put_item.side_effect = capture_put_item

    # Patch get_region_status_table to return our mock
    with patch("shared.active_region_filter.get_region_status_table", return_value=mock_table):
        # Act: Update region status multiple times with same data
        for _ in range(3):
            update_region_status(region=region, server_count=server_count, error_message=error_message)

    # Assert: All updates should have been called
    assert len(put_item_calls) == 3, f"Expected 3 updates, got {len(put_item_calls)}"

    # Assert: All updates should have identical data (idempotent)
    first_item = put_item_calls[0]
    for item in put_item_calls[1:]:
        # Compare all fields except lastChecked (timestamp will differ)
        assert item["region"] == first_item["region"], "Region should be consistent"
        assert item["serverCount"] == first_item["serverCount"], "Server count should be consistent"
        assert item["status"] == first_item["status"], "Status should be consistent"
        assert item["errorMessage"] == first_item["errorMessage"], "Error message should be consistent"


@settings(max_examples=50)
@given(
    region=st.sampled_from(DRS_REGIONS),
    initial_count=st.integers(min_value=0, max_value=100),
    updated_count=st.integers(min_value=0, max_value=100),
)
@pytest.mark.property
def test_property_region_status_update_overwrites_previous(region, initial_count, updated_count):
    """
    Property 3 (supplemental): Region status updates overwrite previous values.

    Tests that updating region status with new server count correctly
    overwrites the previous value (last write wins).

    **Validates: Requirements 5.1, 5.3**
    """
    # Arrange: Create mock region status table
    mock_table = MagicMock()
    put_item_calls = []

    def capture_put_item(Item):
        put_item_calls.append(Item)
        return {}

    mock_table.put_item.side_effect = capture_put_item

    # Patch get_region_status_table to return our mock
    with patch("shared.active_region_filter.get_region_status_table", return_value=mock_table):
        # Act: Update with initial count
        update_region_status(region=region, server_count=initial_count, error_message=None)

        # Act: Update with new count (should overwrite)
        update_region_status(region=region, server_count=updated_count, error_message=None)

    # Assert: Both updates should have been called
    assert len(put_item_calls) == 2, f"Expected 2 updates, got {len(put_item_calls)}"

    # Assert: Second update should have the new count
    second_item = put_item_calls[1]
    assert second_item["serverCount"] == updated_count, (
        f"Second update should have new count {updated_count}, " f"got {second_item['serverCount']}"
    )

    # Assert: Status should reflect the new count
    if updated_count > 0:
        assert second_item["status"] == "AVAILABLE", "Status should be AVAILABLE when count > 0"
    else:
        assert second_item["status"] == "UNINITIALIZED", "Status should be UNINITIALIZED when count = 0"


# ============================================================
# Property 6: Cache Invalidation
# ============================================================


@settings(max_examples=100)
@given(
    initial_regions=st.lists(
        st.fixed_dictionaries(
            {
                "region": st.sampled_from(DRS_REGIONS),
                "serverCount": st.integers(min_value=1, max_value=100),
            }
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x["region"],
    ),
    updated_regions=st.lists(
        st.fixed_dictionaries(
            {
                "region": st.sampled_from(DRS_REGIONS),
                "serverCount": st.integers(min_value=1, max_value=100),
            }
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x["region"],
    ),
)
@pytest.mark.property
def test_property_cache_invalidation_after_inventory_sync(initial_regions, updated_regions):
    """
    Property 6: Cache Invalidation.

    Feature: active-region-filtering
    Property 6: For any sequence of operations where source server inventory
                sync completes, the region status cache should be invalidated,
                and the next call to get_active_regions should query DynamoDB
                instead of using cached data.

    **Validates: Requirements 10.5**
    """
    # Arrange: Clear cache before test
    invalidate_region_cache()

    # Create mock table with initial regions
    mock_table = MagicMock()
    mock_table.scan.return_value = {"Items": initial_regions}

    # Act: First call - populates cache with initial regions
    first_result = get_active_regions(region_status_table=mock_table, cache_ttl=60)

    # Assert: First call returns initial regions
    expected_initial = [item["region"] for item in initial_regions]
    assert set(first_result) == set(expected_initial), (
        f"First call should return initial regions. "
        f"Expected: {sorted(expected_initial)}, Got: {sorted(first_result)}"
    )

    # Act: Second call immediately - should use cache (no new query)
    second_result = get_active_regions(region_status_table=mock_table, cache_ttl=60)

    # Assert: Second call returns same cached result
    assert first_result == second_result, "Second call should return cached result"

    # Assert: Only one DynamoDB query so far (cache was used)
    assert mock_table.scan.call_count == 1, f"Expected 1 DynamoDB query, got {mock_table.scan.call_count}"

    # Act: Simulate inventory sync completion - invalidate cache
    invalidate_region_cache()

    # Act: Update mock table with new regions (simulates inventory sync updating table)
    mock_table.scan.return_value = {"Items": updated_regions}

    # Act: Third call after cache invalidation - should query DynamoDB again
    third_result = get_active_regions(region_status_table=mock_table, cache_ttl=60)

    # Assert: Third call returns updated regions (not cached)
    expected_updated = [item["region"] for item in updated_regions]
    assert set(third_result) == set(expected_updated), (
        f"Third call should return updated regions after cache invalidation. "
        f"Expected: {sorted(expected_updated)}, Got: {sorted(third_result)}"
    )

    # Assert: DynamoDB was queried again (cache was invalidated)
    assert mock_table.scan.call_count == 2, (
        f"Expected 2 DynamoDB queries after cache invalidation, " f"got {mock_table.scan.call_count}"
    )


@settings(max_examples=50)
@given(
    regions=st.lists(
        st.fixed_dictionaries(
            {
                "region": st.sampled_from(DRS_REGIONS),
                "serverCount": st.integers(min_value=1, max_value=100),
            }
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x["region"],
    ),
    num_calls_before_invalidation=st.integers(min_value=1, max_value=5),
)
@pytest.mark.property
def test_property_cache_invalidation_clears_all_cached_data(regions, num_calls_before_invalidation):
    """
    Property 6 (supplemental): Cache invalidation clears all cached data.

    Tests that invalidate_region_cache() completely clears the cache,
    regardless of how many times get_active_regions was called before.

    **Validates: Requirements 10.5**
    """
    # Arrange: Clear cache before test
    invalidate_region_cache()

    # Create mock table
    mock_table = MagicMock()
    mock_table.scan.return_value = {"Items": regions}

    # Act: Call get_active_regions multiple times to populate cache
    for _ in range(num_calls_before_invalidation):
        get_active_regions(region_status_table=mock_table, cache_ttl=60)

    # Assert: Only one DynamoDB query (cache was used for subsequent calls)
    assert mock_table.scan.call_count == 1, (
        f"Expected 1 DynamoDB query before invalidation, " f"got {mock_table.scan.call_count}"
    )

    # Act: Invalidate cache
    invalidate_region_cache()

    # Act: Call get_active_regions again
    get_active_regions(region_status_table=mock_table, cache_ttl=60)

    # Assert: DynamoDB was queried again (cache was cleared)
    assert mock_table.scan.call_count == 2, (
        f"Expected 2 DynamoDB queries after invalidation, " f"got {mock_table.scan.call_count}"
    )


@settings(max_examples=50)
@given(
    regions=st.lists(
        st.fixed_dictionaries(
            {
                "region": st.sampled_from(DRS_REGIONS),
                "serverCount": st.integers(min_value=1, max_value=100),
            }
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x["region"],
    )
)
@pytest.mark.property
def test_property_cache_invalidation_idempotent(regions):
    """
    Property 6 (supplemental): Cache invalidation is idempotent.

    Tests that calling invalidate_region_cache() multiple times
    has the same effect as calling it once.

    **Validates: Requirements 10.5**
    """
    # Arrange: Clear cache before test
    invalidate_region_cache()

    # Create mock table
    mock_table = MagicMock()
    mock_table.scan.return_value = {"Items": regions}

    # Act: Populate cache
    get_active_regions(region_status_table=mock_table, cache_ttl=60)

    # Act: Invalidate cache multiple times
    invalidate_region_cache()
    invalidate_region_cache()
    invalidate_region_cache()

    # Act: Call get_active_regions again
    get_active_regions(region_status_table=mock_table, cache_ttl=60)

    # Assert: DynamoDB was queried twice (once before, once after invalidation)
    assert mock_table.scan.call_count == 2, (
        f"Expected 2 DynamoDB queries (before and after invalidation), " f"got {mock_table.scan.call_count}"
    )


# ============================================================
# Unit test examples for specific scenarios
# ============================================================


@pytest.mark.property
def test_region_status_update_specific_examples():
    """Unit test examples for region status updates."""
    # Arrange: Create mock table
    mock_table = MagicMock()
    put_item_calls = []

    def capture_put_item(Item):
        put_item_calls.append(Item)
        return {}

    mock_table.put_item.side_effect = capture_put_item

    # Patch get_region_status_table
    with patch("shared.active_region_filter.get_region_status_table", return_value=mock_table):
        # Example 1: Region with servers (AVAILABLE)
        update_region_status(region="us-east-1", server_count=42, error_message=None)

        # Example 2: Region with no servers (UNINITIALIZED)
        update_region_status(region="us-west-2", server_count=0, error_message=None)

        # Example 3: Region with error (ERROR)
        update_region_status(region="eu-west-1", server_count=0, error_message="DRS not initialized")

    # Assert: Three updates
    assert len(put_item_calls) == 3

    # Verify Example 1
    assert put_item_calls[0]["region"] == "us-east-1"
    assert put_item_calls[0]["serverCount"] == 42
    assert put_item_calls[0]["status"] == "AVAILABLE"
    assert put_item_calls[0]["errorMessage"] is None

    # Verify Example 2
    assert put_item_calls[1]["region"] == "us-west-2"
    assert put_item_calls[1]["serverCount"] == 0
    assert put_item_calls[1]["status"] == "UNINITIALIZED"
    assert put_item_calls[1]["errorMessage"] is None

    # Verify Example 3
    assert put_item_calls[2]["region"] == "eu-west-1"
    assert put_item_calls[2]["serverCount"] == 0
    assert put_item_calls[2]["status"] == "ERROR"
    assert put_item_calls[2]["errorMessage"] == "DRS not initialized"


@pytest.mark.property
def test_cache_invalidation_specific_example():
    """Unit test example for cache invalidation."""
    # Arrange: Clear cache
    invalidate_region_cache()

    # Create mock table
    mock_table = MagicMock()
    mock_table.scan.return_value = {
        "Items": [
            {"region": "us-east-1", "serverCount": 10},
            {"region": "us-west-2", "serverCount": 5},
        ]
    }

    # Act: First call - populates cache
    first_result = get_active_regions(region_status_table=mock_table, cache_ttl=60)
    assert set(first_result) == {"us-east-1", "us-west-2"}
    assert mock_table.scan.call_count == 1

    # Act: Second call - uses cache
    second_result = get_active_regions(region_status_table=mock_table, cache_ttl=60)
    assert first_result == second_result
    assert mock_table.scan.call_count == 1  # Still 1 (cache used)

    # Act: Invalidate cache (simulates inventory sync completion)
    invalidate_region_cache()

    # Act: Update table data (simulates new inventory data)
    mock_table.scan.return_value = {
        "Items": [
            {"region": "us-east-1", "serverCount": 15},  # Updated count
            {"region": "eu-west-1", "serverCount": 3},  # New region
        ]
    }

    # Act: Third call - queries DynamoDB again
    third_result = get_active_regions(region_status_table=mock_table, cache_ttl=60)
    assert set(third_result) == {"us-east-1", "eu-west-1"}
    assert mock_table.scan.call_count == 2  # Cache was invalidated


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
