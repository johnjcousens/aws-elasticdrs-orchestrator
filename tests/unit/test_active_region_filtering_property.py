"""
Property-based tests for active region filtering.

Feature: active-region-filtering
Properties:
- Property 1: Active Region Filtering Consistency

Validates: Requirements 1.2, 2.2, 3.2, 4.2, 9.2
"""

import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.active_region_filter import (
    get_active_regions,
    invalidate_region_cache,
)
from shared.drs_regions import DRS_REGIONS


# ============================================================
# Strategies for generating test data
# ============================================================


@st.composite
def region_status_items_strategy(draw):
    """
    Generate a list of region status items for DynamoDB.

    Returns a list of dictionaries with region and serverCount.
    Ensures regions are unique and from the DRS_REGIONS list.
    """
    # Select a random subset of DRS regions
    num_regions = draw(st.integers(min_value=0, max_value=len(DRS_REGIONS)))
    selected_regions = draw(
        st.lists(
            st.sampled_from(DRS_REGIONS),
            min_size=num_regions,
            max_size=num_regions,
            unique=True,
        )
    )

    # Generate status items with random server counts
    items = []
    for region in selected_regions:
        server_count = draw(st.integers(min_value=0, max_value=1000))
        items.append(
            {
                "region": region,
                "serverCount": server_count,
                "status": "AVAILABLE" if server_count > 0 else "UNINITIALIZED",
                "lastChecked": "2025-02-15T10:00:00Z",
            }
        )

    return items


# ============================================================
# Property 1: Active Region Filtering Consistency
# ============================================================


@settings(max_examples=100)
@given(region_statuses=region_status_items_strategy())
@pytest.mark.property
def test_property_active_region_filtering_consistency(region_statuses):
    """
    Property 1: Active Region Filtering Consistency.

    Feature: active-region-filtering
    Property 1: For any region status table state, get_active_regions
                should return only regions with serverCount > 0, OR
                fall back to all DRS regions if table is empty.

    **Validates: Requirements 1.2, 2.2, 3.2, 4.2, 9.2**
    """
    # Arrange: Clear cache before test
    invalidate_region_cache()

    # Calculate expected active regions (DynamoDB filter would do this)
    expected_active = [item["region"] for item in region_statuses if item["serverCount"] > 0]

    # Create mock DynamoDB table that simulates the FilterExpression behavior
    mock_table = MagicMock()
    # DynamoDB scan with FilterExpression only returns items matching the filter
    filtered_items = [item for item in region_statuses if item["serverCount"] > 0]
    mock_table.scan.return_value = {"Items": filtered_items}

    # Act: Get active regions
    active_regions = get_active_regions(region_status_table=mock_table, cache_ttl=0)

    # Assert: Behavior depends on whether table has active regions
    if expected_active:
        # Table has active regions - should return only those
        assert set(active_regions) == set(expected_active), (
            f"Active regions mismatch. "
            f"Expected: {sorted(expected_active)}, "
            f"Got: {sorted(active_regions)}, "
            f"Input statuses: {region_statuses}"
        )

        # Assert: No regions with serverCount = 0 should be returned
        inactive_regions = [item["region"] for item in region_statuses if item["serverCount"] == 0]
        for region in inactive_regions:
            assert region not in active_regions, f"Inactive region {region} should not be in active_regions"
    else:
        # Table is empty or has no active regions - should fall back to all DRS regions
        assert set(active_regions) == set(DRS_REGIONS), (
            f"Empty table should fall back to all DRS regions. "
            f"Expected {len(DRS_REGIONS)} regions, got {len(active_regions)}"
        )

    # Assert: All returned regions should be in DRS_REGIONS
    for region in active_regions:
        assert region in DRS_REGIONS, f"Region {region} not in DRS_REGIONS"


@settings(max_examples=100)
@given(region_statuses=region_status_items_strategy())
@pytest.mark.property
def test_property_active_region_filtering_with_pagination(region_statuses):
    """
    Property 7: Pagination Handling.

    Feature: active-region-filtering
    Property 7: For any region status table containing more than 28 entries,
                get_active_regions should handle DynamoDB pagination and
                return all active regions, not just the first page.

    Tests that get_active_regions correctly handles DynamoDB pagination
    when the result set is split across multiple pages, including:
    - Two-page pagination (most common)
    - Multi-page pagination (3+ pages)
    - Single page (no pagination needed)
    - Empty pages (fallback behavior)

    **Validates: Requirements 10.3**
    """
    # Arrange: Clear cache before test
    invalidate_region_cache()

    # Calculate expected active regions (DynamoDB filter would do this)
    expected_active = [item["region"] for item in region_statuses if item["serverCount"] > 0]
    filtered_items = [item for item in region_statuses if item["serverCount"] > 0]

    # Split filtered region statuses into multiple pages
    if len(filtered_items) > 2:
        # Multi-page pagination (3+ pages) - split into thirds
        page_size = max(1, len(filtered_items) // 3)
        page1_items = filtered_items[:page_size]
        page2_items = filtered_items[page_size : page_size * 2]
        page3_items = filtered_items[page_size * 2 :]

        # Create mock table with 3-page pagination
        mock_table = MagicMock()
        mock_table.scan.side_effect = [
            {"Items": page1_items, "LastEvaluatedKey": {"region": "marker1"}},
            {"Items": page2_items, "LastEvaluatedKey": {"region": "marker2"}},
            {"Items": page3_items},  # Last page has no LastEvaluatedKey
        ]
    elif len(filtered_items) > 1:
        # Two-page pagination (most common case)
        mid_point = len(filtered_items) // 2
        page1_items = filtered_items[:mid_point]
        page2_items = filtered_items[mid_point:]

        # Create mock table with 2-page pagination
        mock_table = MagicMock()
        mock_table.scan.side_effect = [
            {"Items": page1_items, "LastEvaluatedKey": {"region": "marker"}},
            {"Items": page2_items},  # Last page has no LastEvaluatedKey
        ]
    else:
        # Single page (no pagination needed)
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": filtered_items}

    # Act: Get active regions
    active_regions = get_active_regions(region_status_table=mock_table, cache_ttl=0)

    # Assert: Behavior depends on whether table has active regions
    if expected_active:
        # Table has active regions - should return only those
        assert set(active_regions) == set(expected_active), (
            f"Active regions mismatch with pagination. "
            f"Expected: {sorted(expected_active)}, "
            f"Got: {sorted(active_regions)}, "
            f"Pages: {len(filtered_items)} items split across "
            f"{mock_table.scan.call_count} pages"
        )

        # Assert: All pages were fetched (verify pagination loop worked)
        if len(filtered_items) > 2:
            assert mock_table.scan.call_count == 3, (
                f"Expected 3 DynamoDB scans for multi-page pagination, "
                f"got {mock_table.scan.call_count}"
            )
        elif len(filtered_items) > 1:
            assert mock_table.scan.call_count == 2, (
                f"Expected 2 DynamoDB scans for two-page pagination, "
                f"got {mock_table.scan.call_count}"
            )
        else:
            assert mock_table.scan.call_count == 1, (
                f"Expected 1 DynamoDB scan for single page, "
                f"got {mock_table.scan.call_count}"
            )

        # Assert: No duplicates in result (pagination should not duplicate regions)
        assert len(active_regions) == len(set(active_regions)), (
            f"Pagination should not create duplicate regions. "
            f"Got {len(active_regions)} regions but only "
            f"{len(set(active_regions))} unique"
        )
    else:
        # Table is empty or has no active regions - should fall back to all DRS regions
        assert set(active_regions) == set(DRS_REGIONS), (
            f"Empty table should fall back to all DRS regions. "
            f"Expected {len(DRS_REGIONS)} regions, got {len(active_regions)}"
        )


@settings(max_examples=50)
@given(
    region_statuses=region_status_items_strategy(),
    cache_ttl=st.integers(min_value=1, max_value=120),
)
@pytest.mark.property
def test_property_active_region_filtering_cache_behavior(region_statuses, cache_ttl):
    """
    Property 1 (supplemental): Cache returns same results within TTL.

    Tests that get_active_regions returns cached results on subsequent
    calls within the cache TTL window.

    **Validates: Requirements 10.4**
    """
    # Arrange: Clear cache before test
    invalidate_region_cache()

    # Calculate expected active regions (DynamoDB filter would do this)
    expected_active = [item["region"] for item in region_statuses if item["serverCount"] > 0]
    filtered_items = [item for item in region_statuses if item["serverCount"] > 0]

    # Create mock table that simulates the FilterExpression behavior
    mock_table = MagicMock()
    mock_table.scan.return_value = {"Items": filtered_items}

    # Act: First call - should query DynamoDB
    first_result = get_active_regions(region_status_table=mock_table, cache_ttl=cache_ttl)

    # Act: Second call immediately - should use cache
    second_result = get_active_regions(region_status_table=mock_table, cache_ttl=cache_ttl)

    # Assert: Both calls should return same results
    assert first_result == second_result, "Cached result should match first result"

    # Assert: DynamoDB query count depends on whether table has active regions
    if expected_active:
        # Table has active regions - cache should work, only 1 query
        assert mock_table.scan.call_count == 1, f"Expected 1 DynamoDB query, got {mock_table.scan.call_count}"
    else:
        # Table is empty - falls back to all regions, no caching on fallback
        # The implementation returns DRS_REGIONS directly without caching
        assert mock_table.scan.call_count == 2, (
            f"Empty table fallback should query twice (no cache). " f"Got {mock_table.scan.call_count} queries"
        )


@settings(max_examples=50)
@given(region_statuses=region_status_items_strategy())
@pytest.mark.property
def test_property_active_region_filtering_cache_expiry(region_statuses):
    """
    Property 1 (supplemental): Cache expires after TTL.

    Tests that get_active_regions queries DynamoDB again after
    cache TTL expires.

    **Validates: Requirements 10.4**
    """
    # Arrange: Clear cache before test
    invalidate_region_cache()

    # Create mock table
    mock_table = MagicMock()
    mock_table.scan.return_value = {"Items": region_statuses}

    # Use very short TTL for testing
    short_ttl = 1

    # Act: First call - should query DynamoDB
    first_result = get_active_regions(region_status_table=mock_table, cache_ttl=short_ttl)

    # Wait for cache to expire
    time.sleep(short_ttl + 0.1)

    # Act: Second call after TTL - should query DynamoDB again
    second_result = get_active_regions(region_status_table=mock_table, cache_ttl=short_ttl)

    # Assert: Both calls should return same results
    assert first_result == second_result, "Results should be consistent"

    # Assert: DynamoDB should be queried twice (cache expired)
    assert mock_table.scan.call_count == 2, f"Expected 2 DynamoDB queries, got {mock_table.scan.call_count}"


# ============================================================
# Property 2: Fallback to All Regions
# ============================================================


@settings(max_examples=100)
@given(
    table_state=st.sampled_from(["empty", "error", "none"]),
    # Add variation to test different error scenarios
    error_variation=st.integers(min_value=0, max_value=10),
)
@pytest.mark.property
def test_property_fallback_to_all_regions(table_state, error_variation):
    """
    Property 2: Fallback to All Regions.

    Feature: active-region-filtering
    Property 2: For any error condition (empty table, DynamoDB error,
                table unavailable), operations should fall back to
                scanning all 28 DRS regions.

    **Validates: Requirements 1.3, 1.4, 2.3, 3.3, 6.1, 6.2, 6.4, 8.1**
    """
    # Arrange: Clear cache before test
    invalidate_region_cache()

    if table_state == "empty":
        # Table exists but has no items
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": []}
    elif table_state == "error":
        # DynamoDB error - vary the error type based on error_variation
        mock_table = MagicMock()
        from botocore.exceptions import ClientError

        error_codes = [
            "ServiceUnavailable",
            "InternalServerError",
            "ThrottlingException",
            "ResourceNotFoundException",
            "AccessDeniedException",
        ]
        error_code = error_codes[error_variation % len(error_codes)]

        mock_table.scan.side_effect = ClientError(
            {"Error": {"Code": error_code, "Message": f"Mock {error_code} error"}},
            "Scan",
        )
    else:  # table_state == "none"
        # Table not configured
        mock_table = None

    # Act: Get active regions
    active_regions = get_active_regions(region_status_table=mock_table, cache_ttl=0)

    # Assert: Should fall back to all DRS regions
    assert set(active_regions) == set(DRS_REGIONS), (
        f"Should fall back to all DRS regions for table_state={table_state}. "
        f"Expected {len(DRS_REGIONS)} regions, got {len(active_regions)}"
    )

    # Assert: Should return exactly 28 regions
    assert len(active_regions) == 28, f"Should return all 28 DRS regions, got {len(active_regions)}"

    # Assert: All returned regions should be valid DRS regions
    for region in active_regions:
        assert region in DRS_REGIONS, f"Region {region} not in DRS_REGIONS"


@settings(max_examples=100)
@given(
    error_code=st.sampled_from(
        [
            "ServiceUnavailable",
            "InternalServerError",
            "ThrottlingException",
            "ResourceNotFoundException",
            "AccessDeniedException",
        ]
    )
)
@pytest.mark.property
def test_property_fallback_handles_all_dynamodb_errors(error_code):
    """
    Property 2 (supplemental): Fallback handles all DynamoDB error types.

    Tests that get_active_regions falls back to all regions for any
    DynamoDB ClientError, not just specific error codes.

    **Validates: Requirements 1.4, 6.2**
    """
    # Arrange: Clear cache before test
    invalidate_region_cache()

    # Create mock table that raises ClientError
    mock_table = MagicMock()
    from botocore.exceptions import ClientError

    mock_table.scan.side_effect = ClientError(
        {"Error": {"Code": error_code, "Message": f"Mock {error_code} error"}},
        "Scan",
    )

    # Act: Get active regions
    active_regions = get_active_regions(region_status_table=mock_table, cache_ttl=0)

    # Assert: Should fall back to all DRS regions for any error
    assert set(active_regions) == set(DRS_REGIONS), (
        f"Should fall back to all DRS regions for error_code={error_code}. "
        f"Expected {len(DRS_REGIONS)} regions, got {len(active_regions)}"
    )

    # Assert: Should return exactly 28 regions
    assert len(active_regions) == 28, f"Should return all 28 DRS regions, got {len(active_regions)}"


@settings(max_examples=100)
@given(
    exception_type=st.sampled_from(
        [
            ValueError("Invalid table configuration"),
            KeyError("Missing required field"),
            AttributeError("Table object has no attribute"),
            TypeError("Invalid type for scan operation"),
        ]
    )
)
@pytest.mark.property
def test_property_fallback_handles_unexpected_exceptions(exception_type):
    """
    Property 2 (supplemental): Fallback handles unexpected exceptions.

    Tests that get_active_regions falls back to all regions for any
    unexpected exception during DynamoDB query, not just ClientError.

    **Validates: Requirements 1.4, 6.2**
    """
    # Arrange: Clear cache before test
    invalidate_region_cache()

    # Create mock table that raises unexpected exception
    mock_table = MagicMock()
    mock_table.scan.side_effect = exception_type

    # Act: Get active regions
    active_regions = get_active_regions(region_status_table=mock_table, cache_ttl=0)

    # Assert: Should fall back to all DRS regions for any exception
    assert set(active_regions) == set(DRS_REGIONS), (
        f"Should fall back to all DRS regions for exception={type(exception_type).__name__}. "
        f"Expected {len(DRS_REGIONS)} regions, got {len(active_regions)}"
    )

    # Assert: Should return exactly 28 regions
    assert len(active_regions) == 28, f"Should return all 28 DRS regions, got {len(active_regions)}"


@settings(max_examples=50)
@given(
    table_state=st.sampled_from(["empty", "error", "none"]),
    subsequent_call_delay=st.floats(min_value=0.0, max_value=0.5),
)
@pytest.mark.property
def test_property_fallback_consistency_across_calls(table_state, subsequent_call_delay):
    """
    Property 2 (supplemental): Fallback returns consistent results across multiple calls.

    Tests that get_active_regions returns the same fallback result (all DRS regions)
    consistently across multiple calls when the table remains in error state.

    **Validates: Requirements 6.1, 6.2, 8.1**
    """
    # Arrange: Clear cache before test
    invalidate_region_cache()

    # Setup mock table based on state
    if table_state == "empty":
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": []}
    elif table_state == "error":
        mock_table = MagicMock()
        from botocore.exceptions import ClientError

        mock_table.scan.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service unavailable"}},
            "Scan",
        )
    else:  # table_state == "none"
        mock_table = None

    # Act: First call
    first_result = get_active_regions(region_status_table=mock_table, cache_ttl=0)

    # Wait a bit (simulates real-world timing)
    time.sleep(subsequent_call_delay)

    # Act: Second call
    second_result = get_active_regions(region_status_table=mock_table, cache_ttl=0)

    # Assert: Both calls should return all DRS regions
    assert set(first_result) == set(DRS_REGIONS), "First call should return all DRS regions"
    assert set(second_result) == set(DRS_REGIONS), "Second call should return all DRS regions"

    # Assert: Results should be consistent
    assert first_result == second_result, (
        f"Fallback results should be consistent across calls. "
        f"First: {len(first_result)} regions, Second: {len(second_result)} regions"
    )


@settings(max_examples=50)
@given(
    initial_state=st.sampled_from(["empty", "error"]),
    recovery_regions=st.lists(
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
def test_property_fallback_recovery_after_table_populated(initial_state, recovery_regions):
    """
    Property 2 (supplemental): System recovers from fallback when table is populated.

    Tests that after falling back to all regions due to empty/error state,
    the system correctly uses filtered regions once the table is populated.

    **Validates: Requirements 6.4, 6.5, 8.1**
    """
    # Arrange: Clear cache before test
    invalidate_region_cache()

    # Setup initial error state
    mock_table = MagicMock()
    if initial_state == "empty":
        mock_table.scan.return_value = {"Items": []}
    else:  # error
        from botocore.exceptions import ClientError

        mock_table.scan.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service unavailable"}},
            "Scan",
        )

    # Act: First call - should fall back to all regions
    first_result = get_active_regions(region_status_table=mock_table, cache_ttl=0)

    # Assert: First call returns all regions
    assert set(first_result) == set(DRS_REGIONS), "Initial call should fall back to all DRS regions"

    # Arrange: Simulate table recovery - now has active regions
    invalidate_region_cache()  # Clear cache to force new query
    expected_active = [item["region"] for item in recovery_regions]
    mock_table.scan.side_effect = None  # Clear error
    mock_table.scan.return_value = {"Items": recovery_regions}

    # Act: Second call - should use filtered regions
    second_result = get_active_regions(region_status_table=mock_table, cache_ttl=0)

    # Assert: Second call returns only active regions (recovery successful)
    assert set(second_result) == set(expected_active), (
        f"After table recovery, should return only active regions. "
        f"Expected: {sorted(expected_active)}, Got: {sorted(second_result)}"
    )

    # Assert: Should not return all regions anymore
    assert len(second_result) < len(DRS_REGIONS) or set(second_result) != set(DRS_REGIONS), (
        "After recovery, should not return all DRS regions (unless all are actually active)"
    )


# ============================================================
# Unit test examples for specific scenarios
# ============================================================


@pytest.mark.property
def test_active_region_filtering_specific_examples():
    """Unit test examples for active region filtering."""
    # Arrange: Clear cache
    invalidate_region_cache()

    # Example 1: Three active regions (mock DynamoDB FilterExpression behavior)
    mock_table = MagicMock()
    # DynamoDB scan with FilterExpression only returns items with serverCount > 0
    mock_table.scan.return_value = {
        "Items": [
            {"region": "us-east-1", "serverCount": 10},
            {"region": "us-west-2", "serverCount": 5},
            {"region": "eu-west-1", "serverCount": 3},
            # ap-southeast-1 with serverCount=0 is filtered out by DynamoDB
        ]
    }

    active_regions = get_active_regions(region_status_table=mock_table, cache_ttl=0)
    assert set(active_regions) == {"us-east-1", "us-west-2", "eu-west-1"}
    assert "ap-southeast-1" not in active_regions  # Region with 0 servers should not be included

    # Example 2: No active regions (empty table)
    invalidate_region_cache()
    mock_table.scan.return_value = {"Items": []}
    active_regions = get_active_regions(region_status_table=mock_table, cache_ttl=0)
    assert len(active_regions) == 28  # Falls back to all regions

    # Example 3: All regions inactive (DynamoDB filter returns empty)
    invalidate_region_cache()
    # DynamoDB scan with FilterExpression returns empty when all serverCount = 0
    mock_table.scan.return_value = {"Items": []}
    active_regions = get_active_regions(region_status_table=mock_table, cache_ttl=0)
    assert len(active_regions) == 28  # Falls back to all regions


@pytest.mark.property
def test_cache_invalidation():
    """Unit test for cache invalidation."""
    # Arrange: Clear cache
    invalidate_region_cache()

    # Setup mock table
    mock_table = MagicMock()
    mock_table.scan.return_value = {
        "Items": [
            {"region": "us-east-1", "serverCount": 10},
        ]
    }

    # Act: First call - populates cache
    get_active_regions(region_status_table=mock_table, cache_ttl=60)

    # Act: Invalidate cache
    invalidate_region_cache()

    # Act: Second call - should query DynamoDB again
    get_active_regions(region_status_table=mock_table, cache_ttl=60)

    # Assert: DynamoDB should be queried twice
    assert mock_table.scan.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
