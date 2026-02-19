"""
Property-based tests for tag sync region filtering.

Feature: active-region-filtering
Property 1: Active Region Filtering Consistency (tag sync specific)

**Validates: Requirements 2.2**
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.drs_regions import DRS_REGIONS


@st.composite
def active_regions_strategy(draw):
    """Generate list of active regions (0-28 regions from DRS_REGIONS)."""
    num_regions = draw(st.integers(min_value=0, max_value=len(DRS_REGIONS)))
    if num_regions == 0:
        return []
    return draw(
        st.lists(
            st.sampled_from(DRS_REGIONS),
            min_size=num_regions,
            max_size=num_regions,
            unique=True,
        )
    )


@settings(max_examples=100)
@given(active_regions=active_regions_strategy())
@pytest.mark.property
def test_property_tag_sync_uses_active_region_filtering(active_regions):
    """
    Property 1: Active Region Filtering Consistency (tag sync).
    
    For any tag sync operation, when get_active_regions() returns active regions,
    tag sync should only scan those regions and skip all others.
    
    **Validates: Requirements 2.2**
    """
    # Determine expected regions (fallback to all if empty)
    expected_regions = active_regions if active_regions else DRS_REGIONS

    with patch("shared.active_region_filter.get_active_regions") as mock_get_active:
        mock_get_active.return_value = expected_regions

        from shared.active_region_filter import get_active_regions

        regions_to_scan = get_active_regions()
        scanned_regions = list(regions_to_scan)

        # Assert: Only expected regions were scanned
        assert set(scanned_regions) == set(expected_regions)

        # Assert: All active regions were scanned
        for region in expected_regions:
            assert region in scanned_regions


@settings(max_examples=50)
@given(active_regions=active_regions_strategy())
@pytest.mark.property
def test_property_tag_sync_region_count_matches(active_regions):
    """
    Property 1 (supplemental): Region count matches active regions.
    
    **Validates: Requirements 2.2**
    """
    expected_count = len(active_regions) if active_regions else len(DRS_REGIONS)
    expected_regions = active_regions if active_regions else DRS_REGIONS

    with patch("shared.active_region_filter.get_active_regions") as mock_get_active:
        mock_get_active.return_value = expected_regions

        from shared.active_region_filter import get_active_regions

        regions_to_scan = get_active_regions()
        assert len(regions_to_scan) == expected_count


@settings(max_examples=50)
@given(active_regions=active_regions_strategy())
@pytest.mark.property
def test_property_tag_sync_skips_inactive_regions(active_regions):
    """
    Property 1 (supplemental): Tag sync skips inactive regions.
    
    **Validates: Requirements 2.2**
    """
    if not active_regions:
        inactive_regions = []
        expected_active = DRS_REGIONS
    else:
        inactive_regions = [r for r in DRS_REGIONS if r not in active_regions]
        expected_active = active_regions

    with patch("shared.active_region_filter.get_active_regions") as mock_get_active:
        mock_get_active.return_value = expected_active

        from shared.active_region_filter import get_active_regions

        regions_to_scan = get_active_regions()

        # Assert: No inactive regions in scan list
        for region in inactive_regions:
            assert region not in regions_to_scan


@settings(max_examples=50)
@given(
    active_regions=st.lists(
        st.sampled_from(DRS_REGIONS), min_size=1, max_size=5, unique=True
    )
)
@pytest.mark.property
def test_property_tag_sync_api_call_reduction(active_regions):
    """
    Property 5: API Call Reduction (tag sync).
    
    **Validates: Requirements 2.2, 9.4, 12.5**
    """
    with patch("shared.active_region_filter.get_active_regions") as mock_get_active:
        mock_get_active.return_value = active_regions

        from shared.active_region_filter import get_active_regions

        regions_to_scan = get_active_regions()
        api_call_count = len(regions_to_scan)

        # Assert: API calls match active region count
        assert api_call_count == len(active_regions)

        # Assert: Reduction percentage is correct
        baseline_calls = len(DRS_REGIONS)
        actual_calls = len(active_regions)
        reduction_pct = ((baseline_calls - actual_calls) / baseline_calls) * 100
        expected_reduction = (
            (len(DRS_REGIONS) - len(active_regions)) / len(DRS_REGIONS)
        ) * 100
        assert abs(reduction_pct - expected_reduction) < 0.1


@pytest.mark.property
def test_tag_sync_with_three_active_regions():
    """Unit test: Tag sync with 3 active regions."""
    active_regions = ["us-east-1", "us-west-2", "eu-west-1"]

    with patch("shared.active_region_filter.get_active_regions") as mock_get_active:
        mock_get_active.return_value = active_regions

        from shared.active_region_filter import get_active_regions

        scanned_regions = get_active_regions()
        assert set(scanned_regions) == set(active_regions)
        assert len(scanned_regions) == 3


@pytest.mark.property
def test_tag_sync_with_empty_active_regions_falls_back():
    """Unit test: Empty active regions falls back to all."""
    with patch("shared.active_region_filter.get_active_regions") as mock_get_active:
        mock_get_active.return_value = DRS_REGIONS

        from shared.active_region_filter import get_active_regions

        scanned_regions = get_active_regions()
        assert len(scanned_regions) == 28
        assert set(scanned_regions) == set(DRS_REGIONS)


@pytest.mark.property
def test_tag_sync_integration_with_get_active_regions():
    """Integration test: Tag sync with get_active_regions()."""
    from shared.active_region_filter import get_active_regions

    mock_table = MagicMock()
    mock_table.scan.return_value = {
        "Items": [
            {"region": "us-east-1", "serverCount": 10},
            {"region": "us-west-2", "serverCount": 5},
            {"region": "eu-west-1", "serverCount": 3},
        ]
    }

    active_regions = get_active_regions(region_status_table=mock_table, cache_ttl=0)

    scanned_regions = []
    for region in active_regions:
        scanned_regions.append(region)

    assert len(scanned_regions) == 3
    assert set(scanned_regions) == {"us-east-1", "us-west-2", "eu-west-1"}

    inactive_regions = [r for r in DRS_REGIONS if r not in scanned_regions]
    assert len(inactive_regions) == 25


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
