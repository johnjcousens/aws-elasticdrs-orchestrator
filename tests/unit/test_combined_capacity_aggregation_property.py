"""
Property-Based Test: Combined Capacity Aggregation

Feature: staging-accounts-management
Property 3: For any set of accounts (target + staging) with known server counts,
the combined replicating servers should equal the sum of replicating servers
across all accounts. With multiple staging accounts, capacity = num_accounts × 300.

**Validates: Requirements 4.2, 4.3, 9.6**

**Multiple Staging Account Model**:
- Each account (target + staging) has 300 replicating server limit per region
- Max capacity = number of accounts × 300
- Example: 1 target + 1 staging = 600 capacity
- Example: 1 target + 2 staging = 900 capacity
"""

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent.parent / "lambda" / "query-handler"
sys.path.insert(0, str(lambda_dir))

from hypothesis import given, strategies as st, settings  # noqa: E402
import pytest  # noqa: F401

# Import the function under test
from index import calculate_combined_metrics  # noqa: E402


# ============================================================================
# Hypothesis Strategies
# ============================================================================


@st.composite
def account_result_strategy(draw, account_type="staging"):
    """Generate a valid account capacity result."""
    accessible = draw(st.booleans())

    if accessible:
        replicating_servers = draw(st.integers(min_value=0, max_value=300))
        total_servers = draw(
            st.integers(min_value=replicating_servers, max_value=300)
        )
    else:
        replicating_servers = 0
        total_servers = 0

    return {
        "accountId": draw(st.from_regex(r"\d{12}", fullmatch=True)),
        "accountName": draw(st.text(min_size=1, max_size=50)),
        "accountType": account_type,
        "replicatingServers": replicating_servers,
        "totalServers": total_servers,
        "regionalBreakdown": [],
        "accessible": accessible,
    }


@st.composite
def account_results_list_strategy(draw):
    """Generate a list of account results (target + staging accounts)."""
    # Always have at least 1 target account
    target_account = draw(account_result_strategy(account_type="target"))

    # Generate 0-10 staging accounts
    num_staging = draw(st.integers(min_value=0, max_value=10))
    staging_accounts = [
        draw(account_result_strategy(account_type="staging"))
        for _ in range(num_staging)
    ]

    return [target_account] + staging_accounts


# ============================================================================
# Property Tests
# ============================================================================


@settings(max_examples=100)
@given(account_results=account_results_list_strategy())
@pytest.mark.property
def test_property_combined_capacity_aggregation(account_results):
    """
    Property 3: Combined Capacity Aggregation (Staging Account Model)

    For any set of accounts with known server counts:
    1. Combined replicating servers = sum of replicating servers across all accessible accounts
    2. Maximum capacity = 300 (fixed target account limit)
    3. Percentage used = (total replicating / 300) × 100
    4. Available slots = 300 - total replicating

    Note: Staging accounts provide extended source servers but don't add to replicating capacity.
    """
    # Calculate combined metrics
    result = calculate_combined_metrics(account_results)  # noqa: F841

    # Filter accessible accounts
    accessible_accounts = [
        a for a in account_results if a.get("accessible", False)
    ]

    # Property 1: Total replicating = sum of replicating across accessible accounts
    expected_total_replicating = sum(
        a.get("replicatingServers", 0) for a in accessible_accounts
    )
    assert result["totalReplicating"] == expected_total_replicating, (
        f"Total replicating mismatch: expected {expected_total_replicating}, "
        f"got {result['totalReplicating']}"
    )

    # Property 2: Total servers = sum of total servers across accessible accounts
    expected_total_servers = sum(
        a.get("totalServers", 0) for a in accessible_accounts
    )
    assert result["totalServers"] == expected_total_servers, (
        f"Total servers mismatch: expected {expected_total_servers}, "
        f"got {result['totalServers']}"
    )

    # Property 3: Max capacity = num_accessible_accounts × 300
    expected_max_capacity = len(accessible_accounts) * 300
    assert result["maxReplicating"] == expected_max_capacity, (
        f"Max capacity mismatch: expected {expected_max_capacity}, "
        f"got {result['maxReplicating']}"
    )

    # Property 4: Percentage used calculation
    if expected_max_capacity > 0:
        expected_percent = (
            expected_total_replicating / expected_max_capacity * 100
        )
        # Allow small floating point differences
        assert abs(result["percentUsed"] - expected_percent) < 0.01, (
            f"Percent used mismatch: expected {expected_percent:.2f}, "
            f"got {result['percentUsed']}"
        )
    else:
        assert (
            result["percentUsed"] == 0.0
        ), "Percent used should be 0 when max capacity is 0"

    # Property 5: Available slots = max capacity - total replicating
    expected_available = expected_max_capacity - expected_total_replicating
    assert result["availableSlots"] == expected_available, (
        f"Available slots mismatch: expected {expected_available}, "
        f"got {result['availableSlots']}"
    )

    # Property 6: Accessible accounts count
    assert result["accessibleAccounts"] == len(accessible_accounts), (
        f"Accessible accounts count mismatch: expected {len(accessible_accounts)}, "
        f"got {result['accessibleAccounts']}"
    )

    # Property 7: Total accounts count
    assert result["totalAccounts"] == len(account_results), (
        f"Total accounts count mismatch: expected {len(account_results)}, "
        f"got {result['totalAccounts']}"
    )


@settings(max_examples=100)
@given(
    num_accounts=st.integers(min_value=1, max_value=20),
    servers_per_account=st.integers(min_value=0, max_value=300),
)
@pytest.mark.property
def test_property_uniform_capacity_distribution(
    num_accounts, servers_per_account
):
    """
    Property: Uniform capacity distribution (Staging Account Model)

    When all accounts have the same number of servers:
    - Total replicating = num_accounts × servers_per_account
    - Max capacity = 300 (fixed target account limit)
    """
    # Create uniform account results
    account_results = [  # noqa: F841
        {
            "accountId": f"{i:012d}",
            "accountName": f"Account_{i}",
            "accountType": "target" if i == 0 else "staging",
            "replicatingServers": servers_per_account,
            "totalServers": servers_per_account,
            "regionalBreakdown": [],
            "accessible": True,
        }
        for i in range(num_accounts)
    ]

    result = calculate_combined_metrics(account_results)  # noqa: F841

    # Verify uniform distribution properties
    assert result["totalReplicating"] == num_accounts * servers_per_account
    # Max capacity = num_accounts × 300
    assert result["maxReplicating"] == num_accounts * 300
    assert result["accessibleAccounts"] == num_accounts


@settings(max_examples=100)
@given(account_results=account_results_list_strategy())
@pytest.mark.property
def test_property_inaccessible_accounts_excluded(account_results):
    """
    Property: Inaccessible accounts are excluded from capacity calculations (Staging Account Model)

    Inaccessible accounts should not contribute to:
    - Total replicating servers
    - Total servers
    But should be counted in totalAccounts

    Note: Max capacity is fixed at 300 regardless of accessible accounts.
    """
    result = calculate_combined_metrics(account_results)  # noqa: F841

    # Count accessible vs inaccessible
    accessible = [a for a in account_results if a.get("accessible", False)]
    inaccessible = [
        a for a in account_results if not a.get("accessible", False)
    ]

    # Verify inaccessible accounts don't contribute to capacity
    if inaccessible:
        # Max capacity = num_accessible_accounts × 300
        assert result["maxReplicating"] == len(accessible) * 300

        # Total accounts should include both accessible and inaccessible
        assert result["totalAccounts"] == len(accessible) + len(inaccessible)

        # Accessible accounts count should match
        assert result["accessibleAccounts"] == len(accessible)


# ============================================================================
# Edge Case Tests
# ============================================================================


@pytest.mark.property
def test_edge_case_no_accounts():
    """Edge case: Empty account list."""
    result = calculate_combined_metrics([])  # noqa: F841

    assert result["totalReplicating"] == 0
    assert result["totalServers"] == 0
    # Multi-account model: 0 accounts × 300 = 0
    assert result["maxReplicating"] == 0
    assert result["percentUsed"] == 0.0
    # Available slots = 0 - 0 = 0
    assert result["availableSlots"] == 0
    assert result["accessibleAccounts"] == 0
    assert result["totalAccounts"] == 0


@pytest.mark.property
def test_edge_case_all_accounts_inaccessible():
    """Edge case: All accounts are inaccessible."""
    account_results = [  # noqa: F841
        {
            "accountId": f"{i:012d}",
            "accountName": f"Account_{i}",
            "accountType": "staging",
            "replicatingServers": 0,
            "totalServers": 0,
            "regionalBreakdown": [],
            "accessible": False,
            "error": "Access denied",
        }
        for i in range(5)
    ]

    result = calculate_combined_metrics(account_results)  # noqa: F841

    assert result["totalReplicating"] == 0
    # Multi-account model: 0 accessible accounts × 300 = 0
    assert result["maxReplicating"] == 0
    assert result["percentUsed"] == 0.0
    assert result["accessibleAccounts"] == 0
    assert result["totalAccounts"] == 5


@pytest.mark.property
def test_edge_case_at_max_capacity():
    """Edge case: All accounts at maximum capacity (300 servers each)."""
    # Multi-account model: each account has 300 limit
    account_results = [  # noqa: F841
        {
            "accountId": "000000000000",
            "accountName": "Target",
            "accountType": "target",
            "replicatingServers": 300,
            "totalServers": 300,
            "regionalBreakdown": [],
            "accessible": True,
        },
        {
            "accountId": "111111111111",
            "accountName": "Staging_1",
            "accountType": "staging",
            "replicatingServers": 300,
            "totalServers": 300,
            "regionalBreakdown": [],
            "accessible": True,
        },
        {
            "accountId": "222222222222",
            "accountName": "Staging_2",
            "accountType": "staging",
            "replicatingServers": 300,
            "totalServers": 300,
            "regionalBreakdown": [],
            "accessible": True,
        },
    ]

    result = calculate_combined_metrics(account_results)  # noqa: F841

    # Total replicating = 300 + 300 + 300 = 900
    assert result["totalReplicating"] == 900
    # Max capacity = 3 accounts × 300 = 900
    assert result["maxReplicating"] == 900
    assert result["percentUsed"] == 100.0
    assert result["availableSlots"] == 0


@pytest.mark.property
def test_edge_case_mixed_accessibility():
    """Edge case: Mix of accessible and inaccessible accounts."""
    account_results = [  # noqa: F841
        {
            "accountId": "111111111111",
            "accountName": "Target",
            "accountType": "target",
            "replicatingServers": 150,
            "totalServers": 150,
            "regionalBreakdown": [],
            "accessible": True,
        },
        {
            "accountId": "222222222222",
            "accountName": "Staging_1",
            "accountType": "staging",
            "replicatingServers": 100,
            "totalServers": 100,
            "regionalBreakdown": [],
            "accessible": True,
        },
        {
            "accountId": "333333333333",
            "accountName": "Staging_2",
            "accountType": "staging",
            "replicatingServers": 0,
            "totalServers": 0,
            "regionalBreakdown": [],
            "accessible": False,
            "error": "Access denied",
        },
    ]

    result = calculate_combined_metrics(account_results)  # noqa: F841

    # Total replicating = 150 + 100 = 250 (only accessible accounts)
    assert result["totalReplicating"] == 250
    # Max capacity = 2 accessible accounts × 300 = 600
    assert result["maxReplicating"] == 600
    # Percent used = 250/600 = 41.67%
    assert result["percentUsed"] == pytest.approx(41.67, rel=0.01)
    # Available = 600 - 250 = 350
    assert result["availableSlots"] == 350
    assert result["accessibleAccounts"] == 2
    assert result["totalAccounts"] == 3
