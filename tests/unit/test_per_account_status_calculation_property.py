"""
Property-Based Test: Per-Account Status Calculation

Feature: staging-accounts-management
Property 4: For any account with a given number of replicating servers,
the status should be:
- OK when servers are 0-200 (0-67%)
- INFO when servers are 200-225 (67-75%)
- WARNING when servers are 225-250 (75-83%)
- CRITICAL when servers are 250-280 (83-93%)
- HYPER-CRITICAL when servers are 280-300 (93-100%)

**Validates: Requirements 5.3, 5.4, 5.5, 5.6**
"""

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent.parent / "lambda" / "query-handler"
sys.path.insert(0, str(lambda_dir))

from hypothesis import given, strategies as st, settings  # noqa: E402
import pytest  # noqa: F401

# Import the function under test
from index import calculate_account_status  # noqa: E402


# ============================================================================
# Property Tests
# ============================================================================


@settings(max_examples=100)
@given(replicating_servers=st.integers(min_value=0, max_value=300))
def test_property_per_account_status_calculation(replicating_servers):
    """
    Property 4: Per-Account Status Calculation

    For any account with a given number of replicating servers,
    the status should match the defined thresholds.
    """
    status = calculate_account_status(replicating_servers)

    # Verify status matches threshold
    if replicating_servers < 200:
        assert (
            status == "OK"
        ), f"Expected OK for {replicating_servers} servers, got {status}"
    elif replicating_servers < 225:
        assert (
            status == "INFO"
        ), f"Expected INFO for {replicating_servers} servers, got {status}"
    elif replicating_servers < 250:
        assert status == "WARNING", (
            f"Expected WARNING for {replicating_servers} servers, "
            f"got {status}"
        )
    elif replicating_servers < 280:
        assert status == "CRITICAL", (
            f"Expected CRITICAL for {replicating_servers} servers, "
            f"got {status}"
        )
    else:
        assert status == "HYPER-CRITICAL", (
            f"Expected HYPER-CRITICAL for {replicating_servers} servers, "
            f"got {status}"
        )


@settings(max_examples=100)
@given(servers_in_range=st.integers(min_value=0, max_value=199))
def test_property_ok_status_range(servers_in_range):
    """Property: OK status for 0-199 servers."""
    status = calculate_account_status(servers_in_range)
    assert status == "OK"


@settings(max_examples=100)
@given(servers_in_range=st.integers(min_value=200, max_value=224))
def test_property_info_status_range(servers_in_range):
    """Property: INFO status for 200-224 servers."""
    status = calculate_account_status(servers_in_range)
    assert status == "INFO"


@settings(max_examples=100)
@given(servers_in_range=st.integers(min_value=225, max_value=249))
def test_property_warning_status_range(servers_in_range):
    """Property: WARNING status for 225-249 servers."""
    status = calculate_account_status(servers_in_range)
    assert status == "WARNING"


@settings(max_examples=100)
@given(servers_in_range=st.integers(min_value=250, max_value=279))
def test_property_critical_status_range(servers_in_range):
    """Property: CRITICAL status for 250-279 servers."""
    status = calculate_account_status(servers_in_range)
    assert status == "CRITICAL"


@settings(max_examples=100)
@given(servers_in_range=st.integers(min_value=280, max_value=300))
def test_property_hyper_critical_status_range(servers_in_range):
    """Property: HYPER-CRITICAL status for 280-300 servers."""
    status = calculate_account_status(servers_in_range)
    assert status == "HYPER-CRITICAL"


# ============================================================================
# Boundary Tests
# ============================================================================


def test_boundary_ok_to_info():
    """Test boundary between OK and INFO status (200 servers)."""
    assert calculate_account_status(199) == "OK"
    assert calculate_account_status(200) == "INFO"


def test_boundary_info_to_warning():
    """Test boundary between INFO and WARNING status (225 servers)."""
    assert calculate_account_status(224) == "INFO"
    assert calculate_account_status(225) == "WARNING"


def test_boundary_warning_to_critical():
    """Test boundary between WARNING and CRITICAL status (250 servers)."""
    assert calculate_account_status(249) == "WARNING"
    assert calculate_account_status(250) == "CRITICAL"


def test_boundary_critical_to_hyper_critical():
    """
    Test boundary between CRITICAL and HYPER-CRITICAL status
    (280 servers).
    """
    assert calculate_account_status(279) == "CRITICAL"
    assert calculate_account_status(280) == "HYPER-CRITICAL"


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_edge_case_zero_servers():
    """Edge case: Zero servers should be OK."""
    assert calculate_account_status(0) == "OK"


def test_edge_case_max_servers():
    """Edge case: Maximum 300 servers should be HYPER-CRITICAL."""
    assert calculate_account_status(300) == "HYPER-CRITICAL"


def test_edge_case_operational_limit():
    """Edge case: Operational limit (250 servers) should be CRITICAL."""
    assert calculate_account_status(250) == "CRITICAL"


def test_edge_case_near_operational_limit():
    """Edge case: Just below operational limit should be WARNING."""
    assert calculate_account_status(249) == "WARNING"


def test_edge_case_near_hard_limit():
    """Edge case: Near hard limit (299 servers) should be HYPER-CRITICAL."""
    assert calculate_account_status(299) == "HYPER-CRITICAL"


# ============================================================================
# Status Progression Tests
# ============================================================================


def test_status_progression_monotonic():
    """
    Test that status severity increases monotonically with server count.

    Status severity order: OK < INFO < WARNING < CRITICAL < HYPER-CRITICAL
    """
    status_order = ["OK", "INFO", "WARNING", "CRITICAL", "HYPER-CRITICAL"]

    # Test representative values from each range
    test_values = [0, 100, 200, 225, 250, 280, 300]
    statuses = [calculate_account_status(v) for v in test_values]

    # Verify statuses are in order (or equal)
    for i in range(len(statuses) - 1):
        current_idx = status_order.index(statuses[i])
        next_idx = status_order.index(statuses[i + 1])
        assert current_idx <= next_idx, (
            f"Status should not decrease: {statuses[i]} -> {statuses[i+1]} "
            f"for servers {test_values[i]} -> {test_values[i+1]}"
        )


def test_status_all_thresholds_covered():
    """Test that all status levels are reachable."""
    # Test one value from each range
    assert calculate_account_status(100) == "OK"
    assert calculate_account_status(210) == "INFO"
    assert calculate_account_status(235) == "WARNING"
    assert calculate_account_status(260) == "CRITICAL"
    assert calculate_account_status(290) == "HYPER-CRITICAL"
