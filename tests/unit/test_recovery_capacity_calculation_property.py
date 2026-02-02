"""
Property-Based Test: Recovery Capacity Status Calculation

Feature: staging-accounts-management
Property 11: For any target account with a given number of replicating
servers PER REGION, the recovery capacity status should be:
- OK when servers are below 240 (< 80% of 300)
- WARNING when servers are 240-270 (80-90%)
- CRITICAL when servers exceed 270 (> 90%)

DRS Quota: 300 replicating servers per account PER REGION

**Validates: Requirements 10.2, 10.3, 10.4, 10.5**
"""

import sys
from pathlib import Path

# Clear any existing index module to avoid conflicts
if "index" in sys.modules:
    del sys.modules["index"]

# Add lambda directory to path - query-handler FIRST
query_handler_dir = (
    Path(__file__).parent.parent.parent / "lambda" / "query-handler"
)
sys.path.insert(0, str(query_handler_dir))

from hypothesis import given, strategies as st, settings
import pytest

# Import the function under test
from index import calculate_recovery_capacity


# ============================================================================
# Hypothesis Strategies
# ============================================================================


@st.composite
def target_account_servers_strategy(draw):
    """Generate a valid number of servers for target account."""
    # Generate servers from 0 to 4,500 (beyond the limit to test edge cases)
    return draw(st.integers(min_value=0, max_value=4500))


# ============================================================================
# Property Tests
# ============================================================================


@settings(max_examples=100)
@given(target_servers=target_account_servers_strategy())
def test_property_recovery_capacity_status_calculation(target_servers):
    """
    Property 11: Recovery Capacity Status Calculation
    
    For any target account with a given number of replicating servers:
    1. Status is OK when servers < 3,200 (< 80%)
    2. Status is WARNING when servers are 3,200-3,600 (80-90%)
    3. Status is CRITICAL when servers > 3,600 (> 90%)
    4. Recovery capacity only counts target account servers
    5. Max recovery instances is always 4,000
    6. Percentage and available slots are calculated correctly
    """
    # Calculate recovery capacity
    result = calculate_recovery_capacity(target_servers)
    
    # Property 1: Result contains all required fields
    assert "currentServers" in result, "Missing currentServers field"
    assert "maxRecoveryInstances" in result, (
        "Missing maxRecoveryInstances field"
    )
    assert "percentUsed" in result, "Missing percentUsed field"
    assert "availableSlots" in result, "Missing availableSlots field"
    assert "status" in result, "Missing status field"
    
    # Property 2: Current servers matches input
    assert result["currentServers"] == target_servers, (
        f"Current servers mismatch: expected {target_servers}, "
        f"got {result['currentServers']}"
    )
    
    # Property 3: Max recovery instances is always 4,000
    assert result["maxRecoveryInstances"] == 4000, (
        f"Max recovery instances should be 4,000, "
        f"got {result['maxRecoveryInstances']}"
    )
    
    # Property 4: Percentage used calculation
    expected_percent = (target_servers / 4000) * 100
    # Allow small floating point differences
    assert abs(result["percentUsed"] - expected_percent) < 0.01, (
        f"Percent used mismatch: expected {expected_percent:.2f}, "
        f"got {result['percentUsed']}"
    )
    
    # Property 5: Available slots calculation
    expected_available = 4000 - target_servers
    assert result["availableSlots"] == expected_available, (
        f"Available slots mismatch: expected {expected_available}, "
        f"got {result['availableSlots']}"
    )
    
    # Property 6: Status thresholds
    percent_used = result["percentUsed"]
    status = result["status"]
    
    if percent_used < 80:
        assert status == "OK", (
            f"Status should be OK for {percent_used:.2f}% usage "
            f"(< 80%), got {status}"
        )
    elif percent_used < 90:
        assert status == "WARNING", (
            f"Status should be WARNING for {percent_used:.2f}% usage "
            f"(80-90%), got {status}"
        )
    else:
        assert status == "CRITICAL", (
            f"Status should be CRITICAL for {percent_used:.2f}% usage "
            f"(>= 90%), got {status}"
        )


@settings(max_examples=100)
@given(
    target_servers=st.integers(min_value=0, max_value=300),
    staging_servers=st.integers(min_value=0, max_value=3000)
)
def test_property_recovery_capacity_excludes_staging_accounts(
    target_servers, staging_servers
):
    """
    Property 11 (Part 2): Recovery Capacity Excludes Staging Accounts
    
    Recovery capacity should only count servers in the target account,
    not staging account servers. This test verifies that the function
    only considers the target account parameter.
    """
    # Calculate recovery capacity with only target servers
    result = calculate_recovery_capacity(target_servers)
    
    # The result should only reflect target servers, not staging
    assert result["currentServers"] == target_servers, (
        f"Recovery capacity should only count target servers "
        f"({target_servers}), not staging servers ({staging_servers})"
    )
    
    # Verify percentage is based only on target servers
    expected_percent = (target_servers / 4000) * 100
    assert abs(result["percentUsed"] - expected_percent) < 0.01, (
        f"Percentage should be based only on target servers"
    )


@settings(max_examples=50)
@given(servers=st.integers(min_value=0, max_value=3199))
def test_property_ok_status_threshold(servers):
    """Test OK status threshold (< 80% = < 3,200 servers)."""
    result = calculate_recovery_capacity(servers)
    assert result["status"] == "OK", (
        f"Status should be OK for {servers} servers (< 3,200)"
    )


@settings(max_examples=50)
@given(servers=st.integers(min_value=3200, max_value=3599))
def test_property_warning_status_threshold(servers):
    """Test WARNING status threshold (80-90% = 3,200-3,599 servers)."""
    result = calculate_recovery_capacity(servers)
    assert result["status"] == "WARNING", (
        f"Status should be WARNING for {servers} servers (3,200-3,599)"
    )


@settings(max_examples=50)
@given(servers=st.integers(min_value=3600, max_value=4500))
def test_property_critical_status_threshold(servers):
    """Test CRITICAL status threshold (>= 90% = >= 3,600 servers)."""
    result = calculate_recovery_capacity(servers)
    assert result["status"] == "CRITICAL", (
        f"Status should be CRITICAL for {servers} servers (>= 3,600)"
    )


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_edge_case_zero_servers():
    """Test with zero servers."""
    result = calculate_recovery_capacity(0)
    assert result["currentServers"] == 0
    assert result["percentUsed"] == 0.0
    assert result["availableSlots"] == 4000
    assert result["status"] == "OK"


def test_edge_case_exactly_80_percent():
    """Test exactly at 80% threshold (3,200 servers)."""
    result = calculate_recovery_capacity(3200)
    assert result["percentUsed"] == 80.0
    assert result["status"] == "WARNING"


def test_edge_case_exactly_90_percent():
    """Test exactly at 90% threshold (3,600 servers)."""
    result = calculate_recovery_capacity(3600)
    assert result["percentUsed"] == 90.0
    assert result["status"] == "CRITICAL"


def test_edge_case_at_limit():
    """Test at the 4,000 server limit."""
    result = calculate_recovery_capacity(4000)
    assert result["currentServers"] == 4000
    assert result["percentUsed"] == 100.0
    assert result["availableSlots"] == 0
    assert result["status"] == "CRITICAL"


def test_edge_case_beyond_limit():
    """Test beyond the 4,000 server limit."""
    result = calculate_recovery_capacity(4500)
    assert result["currentServers"] == 4500
    assert result["percentUsed"] == 112.5
    assert result["availableSlots"] == -500
    assert result["status"] == "CRITICAL"



@st.composite
def target_account_servers_strategy(draw):
    """Generate a valid number of servers for target account."""
    # Generate servers from 0 to 4,500 (beyond the limit to test edge cases)
    return draw(st.integers(min_value=0, max_value=4500))


# ============================================================================
# Property Tests
# ============================================================================


@settings(max_examples=100)
@given(target_servers=target_account_servers_strategy())
def test_property_recovery_capacity_status_calculation(target_servers):
    """
    Property 11: Recovery Capacity Status Calculation
    
    For any target account with a given number of replicating servers:
    1. Status is OK when servers < 3,200 (< 80%)
    2. Status is WARNING when servers are 3,200-3,600 (80-90%)
    3. Status is CRITICAL when servers > 3,600 (> 90%)
    4. Recovery capacity only counts target account servers
    5. Max recovery instances is always 4,000
    6. Percentage and available slots are calculated correctly
    """
    # Calculate recovery capacity
    result = calculate_recovery_capacity(target_servers)
    
    # Property 1: Result contains all required fields
    assert "currentServers" in result, "Missing currentServers field"
    assert "maxRecoveryInstances" in result, (
        "Missing maxRecoveryInstances field"
    )
    assert "percentUsed" in result, "Missing percentUsed field"
    assert "availableSlots" in result, "Missing availableSlots field"
    assert "status" in result, "Missing status field"
    
    # Property 2: Current servers matches input
    assert result["currentServers"] == target_servers, (
        f"Current servers mismatch: expected {target_servers}, "
        f"got {result['currentServers']}"
    )
    
    # Property 3: Max recovery instances is always 4,000
    assert result["maxRecoveryInstances"] == 4000, (
        f"Max recovery instances should be 4,000, "
        f"got {result['maxRecoveryInstances']}"
    )
    
    # Property 4: Percentage used calculation
    expected_percent = (target_servers / 4000) * 100
    # Allow small floating point differences
    assert abs(result["percentUsed"] - expected_percent) < 0.01, (
        f"Percent used mismatch: expected {expected_percent:.2f}, "
        f"got {result['percentUsed']}"
    )
    
    # Property 5: Available slots calculation
    expected_available = 4000 - target_servers
    assert result["availableSlots"] == expected_available, (
        f"Available slots mismatch: expected {expected_available}, "
        f"got {result['availableSlots']}"
    )
    
    # Property 6: Status thresholds
    percent_used = result["percentUsed"]
    status = result["status"]
    
    if percent_used < 80:
        assert status == "OK", (
            f"Status should be OK for {percent_used:.2f}% usage "
            f"(< 80%), got {status}"
        )
    elif percent_used < 90:
        assert status == "WARNING", (
            f"Status should be WARNING for {percent_used:.2f}% usage "
            f"(80-90%), got {status}"
        )
    else:
        assert status == "CRITICAL", (
            f"Status should be CRITICAL for {percent_used:.2f}% usage "
            f"(>= 90%), got {status}"
        )


@settings(max_examples=100)
@given(
    target_servers=st.integers(min_value=0, max_value=300),
    staging_servers=st.integers(min_value=0, max_value=3000)
)
def test_property_recovery_capacity_excludes_staging_accounts(
    target_servers, staging_servers
):
    """
    Property 11 (Part 2): Recovery Capacity Excludes Staging Accounts
    
    Recovery capacity should only count servers in the target account,
    not staging account servers. This test verifies that the function
    only considers the target account parameter.
    """
    # Calculate recovery capacity with only target servers
    result = calculate_recovery_capacity(target_servers)
    
    # The result should only reflect target servers, not staging
    assert result["currentServers"] == target_servers, (
        f"Recovery capacity should only count target servers "
        f"({target_servers}), not staging servers ({staging_servers})"
    )
    
    # Verify percentage is based only on target servers
    expected_percent = (target_servers / 4000) * 100
    assert abs(result["percentUsed"] - expected_percent) < 0.01, (
        f"Percentage should be based only on target servers"
    )


@settings(max_examples=50)
@given(servers=st.integers(min_value=0, max_value=3199))
def test_property_ok_status_threshold(servers):
    """Test OK status threshold (< 80% = < 3,200 servers)."""
    result = calculate_recovery_capacity(servers)
    assert result["status"] == "OK", (
        f"Status should be OK for {servers} servers (< 3,200)"
    )


@settings(max_examples=50)
@given(servers=st.integers(min_value=3200, max_value=3599))
def test_property_warning_status_threshold(servers):
    """Test WARNING status threshold (80-90% = 3,200-3,599 servers)."""
    result = calculate_recovery_capacity(servers)
    assert result["status"] == "WARNING", (
        f"Status should be WARNING for {servers} servers (3,200-3,599)"
    )


@settings(max_examples=50)
@given(servers=st.integers(min_value=3600, max_value=4500))
def test_property_critical_status_threshold(servers):
    """Test CRITICAL status threshold (>= 90% = >= 3,600 servers)."""
    result = calculate_recovery_capacity(servers)
    assert result["status"] == "CRITICAL", (
        f"Status should be CRITICAL for {servers} servers (>= 3,600)"
    )


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_edge_case_zero_servers():
    """Test with zero servers."""
    result = calculate_recovery_capacity(0)
    assert result["currentServers"] == 0
    assert result["percentUsed"] == 0.0
    assert result["availableSlots"] == 4000
    assert result["status"] == "OK"


def test_edge_case_exactly_80_percent():
    """Test exactly at 80% threshold (3,200 servers)."""
    result = calculate_recovery_capacity(3200)
    assert result["percentUsed"] == 80.0
    assert result["status"] == "WARNING"


def test_edge_case_exactly_90_percent():
    """Test exactly at 90% threshold (3,600 servers)."""
    result = calculate_recovery_capacity(3600)
    assert result["percentUsed"] == 90.0
    assert result["status"] == "CRITICAL"


def test_edge_case_at_limit():
    """Test at the 4,000 server limit."""
    result = calculate_recovery_capacity(4000)
    assert result["currentServers"] == 4000
    assert result["percentUsed"] == 100.0
    assert result["availableSlots"] == 0
    assert result["status"] == "CRITICAL"


def test_edge_case_beyond_limit():
    """Test beyond the 4,000 server limit."""
    result = calculate_recovery_capacity(4500)
    assert result["currentServers"] == 4500
    assert result["percentUsed"] == 112.5
    assert result["availableSlots"] == -500
    assert result["status"] == "CRITICAL"
