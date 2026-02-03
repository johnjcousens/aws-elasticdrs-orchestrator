"""
Property-Based Test: Warning Generation Based on Thresholds

Feature: staging-accounts-management
Property 5: For any account capacity state, warnings should be generated when:
- Any account reaches 200-225 servers (INFO warning)
- Any account reaches 225-250 servers (WARNING)
- Any account reaches 250-280 servers (CRITICAL warning)
- Any account reaches 280-300 servers (HYPER-CRITICAL warning)
- Combined capacity exceeds operational limits (combined warning)

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6**
"""

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

# Clear any existing index module to avoid conflicts
if "index" in sys.modules:
    del sys.modules["index"]

# Add lambda directory to path - query-handler FIRST
query_handler_dir = (
    Path(__file__).parent.parent.parent / "lambda" / "query-handler"
)
sys.path.insert(0, str(query_handler_dir))

from hypothesis import given, strategies as st, settings  # noqa: E402
import pytest  # noqa: F401

# Import the functions under test
from index import (  # noqa: E402
    generate_warnings,
    calculate_combined_metrics,
    calculate_account_status,
)


# ============================================================================
# Hypothesis Strategies
# ============================================================================


@st.composite
def account_with_status_strategy(draw, status_level):
    """Generate an account with a specific status level."""
    # Map status to server count ranges
    status_ranges = {
        "OK": (0, 199),
        "INFO": (200, 224),
        "WARNING": (225, 249),
        "CRITICAL": (250, 279),
        "HYPER-CRITICAL": (280, 300),
    }

    min_servers, max_servers = status_ranges[status_level]
    replicating_servers = draw(
        st.integers(min_value=min_servers, max_value=max_servers)
    )

    return {
        "accountId": draw(st.from_regex(r"\d{12}", fullmatch=True)),
        "accountName": draw(st.text(min_size=1, max_size=50)),
        "accountType": draw(st.sampled_from(["target", "staging"])),
        "replicatingServers": replicating_servers,
        "totalServers": replicating_servers,
        "regionalBreakdown": [],
        "accessible": True,
    }


@st.composite
def account_results_with_warnings_strategy(draw):
    """Generate account results that should trigger warnings."""
    accounts = []

    # Always have at least one account
    num_accounts = draw(st.integers(min_value=1, max_value=10))

    for i in range(num_accounts):
        # Mix of different status levels
        status = draw(
            st.sampled_from(
                ["OK", "INFO", "WARNING", "CRITICAL", "HYPER-CRITICAL"]
            )
        )
        account = draw(account_with_status_strategy(status))
        account["accountType"] = "target" if i == 0 else "staging"
        accounts.append(account)

    return accounts


# ============================================================================
# Property Tests
# ============================================================================


@settings(max_examples=100)
@given(account_results=account_results_with_warnings_strategy())
@pytest.mark.property
def test_property_warning_generation_per_account(account_results):
    """
    Property 5: Warning Generation Based on Thresholds

    For any account capacity state, warnings should be generated
    for accounts that exceed thresholds.
    """
    combined_metrics = calculate_combined_metrics(account_results)
    warnings = generate_warnings(account_results, combined_metrics)

    # Check each account for expected warnings
    for account in account_results:
        if not account.get("accessible", False):
            continue

        account_id = account.get("accountId")  # noqa: F841
        account_name = account.get("accountName")
        replicating = account.get("replicatingServers", 0)
        status = calculate_account_status(replicating)

        # Check if appropriate warning exists for this account
        if status == "INFO":
            # Should have INFO warning
            assert any(
                "INFO" in w and account_name in w for w in warnings
            ), f"Missing INFO warning for {account_name} with {replicating} servers"

        elif status == "WARNING":
            # Should have WARNING
            assert any(
                "WARNING" in w and account_name in w for w in warnings
            ), f"Missing WARNING for {account_name} with {replicating} servers"

        elif status == "CRITICAL":
            # Should have CRITICAL warning
            assert any(
                "CRITICAL" in w and account_name in w for w in warnings
            ), f"Missing CRITICAL warning for {account_name} with {replicating} servers"

        elif status == "HYPER-CRITICAL":
            # Should have HYPER-CRITICAL warning
            assert any(
                "HYPER-CRITICAL" in w and account_name in w for w in warnings
            ), f"Missing HYPER-CRITICAL warning for {account_name} with {replicating} servers"


@settings(max_examples=100)
@given(
    num_accounts=st.integers(min_value=1, max_value=10),
    servers_per_account=st.integers(min_value=0, max_value=300),
)
@pytest.mark.property
def test_property_combined_warnings(num_accounts, servers_per_account):
    """
    Property: Combined capacity warnings are generated when appropriate.
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

    combined_metrics = calculate_combined_metrics(account_results)
    warnings = generate_warnings(account_results, combined_metrics)

    total_replicating = num_accounts * servers_per_account
    operational_capacity = num_accounts * 250
    hard_capacity = num_accounts * 300

    # Check for combined warnings based on thresholds
    if total_replicating >= hard_capacity:
        # Should have HYPER-CRITICAL combined warning
        assert any(
            "HYPER-CRITICAL" in w and "Combined capacity" in w
            for w in warnings
        ), f"Missing HYPER-CRITICAL combined warning for {total_replicating}/{hard_capacity}"

    elif total_replicating >= operational_capacity:
        # Should have CRITICAL combined warning
        assert any(
            "CRITICAL" in w and "Combined capacity" in w for w in warnings
        ), f"Missing CRITICAL combined warning for {total_replicating}/{operational_capacity}"


@settings(max_examples=100)
@given(replicating_servers=st.integers(min_value=0, max_value=199))
@pytest.mark.property
def test_property_no_warnings_for_ok_status(replicating_servers):
    """
    Property: No warnings should be generated for accounts in OK status.
    """
    account_results = [  # noqa: F841
        {
            "accountId": "111111111111",
            "accountName": "Test_Account",
            "accountType": "target",
            "replicatingServers": replicating_servers,
            "totalServers": replicating_servers,
            "regionalBreakdown": [],
            "accessible": True,
        }
    ]

    combined_metrics = calculate_combined_metrics(account_results)
    warnings = generate_warnings(account_results, combined_metrics)

    # Should not have any warnings for this account
    assert not any(
        "Test_Account" in w for w in warnings
    ), f"Unexpected warning for account with {replicating_servers} servers (OK status)"


# ============================================================================
# Warning Content Tests
# ============================================================================


@pytest.mark.property
def test_warning_contains_actionable_guidance():
    """Test that warnings contain actionable guidance."""
    account_results = [  # noqa: F841
        {
            "accountId": "111111111111",
            "accountName": "Critical_Account",
            "accountType": "target",
            "replicatingServers": 260,  # CRITICAL
            "totalServers": 260,
            "regionalBreakdown": [],
            "accessible": True,
        }
    ]

    combined_metrics = calculate_combined_metrics(account_results)
    warnings = generate_warnings(account_results, combined_metrics)

    # Find the CRITICAL warning
    critical_warnings = [
        w for w in warnings if "CRITICAL" in w and "Critical_Account" in w
    ]
    assert len(critical_warnings) > 0, "Should have CRITICAL warning"

    # Check for actionable guidance
    warning = critical_warnings[0]
    assert (
        "Add a staging account" in warning or "add" in warning.lower()
    ), "Warning should contain actionable guidance"


@pytest.mark.property
def test_warning_includes_server_count():
    """Test that warnings include the server count."""
    account_results = [  # noqa: F841
        {
            "accountId": "111111111111",
            "accountName": "Test_Account",
            "accountType": "target",
            "replicatingServers": 210,  # INFO
            "totalServers": 210,
            "regionalBreakdown": [],
            "accessible": True,
        }
    ]

    combined_metrics = calculate_combined_metrics(account_results)
    warnings = generate_warnings(account_results, combined_metrics)

    # Find the INFO warning
    info_warnings = [
        w for w in warnings if "INFO" in w and "Test_Account" in w
    ]
    assert len(info_warnings) > 0, "Should have INFO warning"

    # Check that server count is mentioned
    warning = info_warnings[0]
    assert "210" in warning, "Warning should include server count"


@pytest.mark.property
def test_warning_includes_account_identification():
    """Test that warnings include account name and ID."""
    account_results = [  # noqa: F841
        {
            "accountId": "123456789012",
            "accountName": "Production_Account",
            "accountType": "target",
            "replicatingServers": 230,  # WARNING
            "totalServers": 230,
            "regionalBreakdown": [],
            "accessible": True,
        }
    ]

    combined_metrics = calculate_combined_metrics(account_results)
    warnings = generate_warnings(account_results, combined_metrics)

    # Find the WARNING
    warning_msgs = [
        w for w in warnings if "WARNING" in w and "Production_Account" in w
    ]
    assert len(warning_msgs) > 0, "Should have WARNING"

    # Check that both name and ID are present
    warning = warning_msgs[0]
    assert (
        "Production_Account" in warning
    ), "Warning should include account name"
    assert "123456789012" in warning, "Warning should include account ID"


# ============================================================================
# Edge Case Tests
# ============================================================================


@pytest.mark.property
def test_edge_case_no_warnings_all_ok():
    """Edge case: No warnings when all accounts are OK."""
    account_results = [  # noqa: F841
        {
            "accountId": f"{i:012d}",
            "accountName": f"Account_{i}",
            "accountType": "target" if i == 0 else "staging",
            "replicatingServers": 50,  # OK status
            "totalServers": 50,
            "regionalBreakdown": [],
            "accessible": True,
        }
        for i in range(3)
    ]

    combined_metrics = calculate_combined_metrics(account_results)
    warnings = generate_warnings(account_results, combined_metrics)

    # Should have no warnings
    assert (
        len(warnings) == 0
    ), "Should have no warnings when all accounts are OK"


@pytest.mark.property
def test_edge_case_multiple_warnings_same_account():
    """
    Edge case: Account can trigger both per-account and combined warnings.
    """
    # Single account at CRITICAL level
    account_results = [  # noqa: F841
        {
            "accountId": "111111111111",
            "accountName": "Critical_Account",
            "accountType": "target",
            "replicatingServers": 260,  # CRITICAL
            "totalServers": 260,
            "regionalBreakdown": [],
            "accessible": True,
        }
    ]

    combined_metrics = calculate_combined_metrics(account_results)
    warnings = generate_warnings(account_results, combined_metrics)

    # Should have at least one warning (per-account CRITICAL)
    assert len(warnings) >= 1, "Should have at least one warning"

    # Should have CRITICAL warning for the account
    assert any(
        "CRITICAL" in w and "Critical_Account" in w for w in warnings
    ), "Should have CRITICAL warning for account"


@pytest.mark.property
def test_edge_case_inaccessible_accounts_no_warnings():
    """Edge case: Inaccessible accounts should not generate warnings."""
    account_results = [  # noqa: F841
        {
            "accountId": "111111111111",
            "accountName": "Accessible_OK",
            "accountType": "target",
            "replicatingServers": 100,
            "totalServers": 100,
            "regionalBreakdown": [],
            "accessible": True,
        },
        {
            "accountId": "222222222222",
            "accountName": "Inaccessible_High",
            "accountType": "staging",
            "replicatingServers": 0,  # Inaccessible accounts report 0
            "totalServers": 0,
            "regionalBreakdown": [],
            "accessible": False,
            "error": "Access denied",
        },
    ]

    combined_metrics = calculate_combined_metrics(account_results)
    warnings = generate_warnings(account_results, combined_metrics)

    # Should not have warnings for inaccessible account
    assert not any(
        "Inaccessible_High" in w for w in warnings
    ), "Should not generate warnings for inaccessible accounts"


@pytest.mark.property
def test_edge_case_all_accounts_at_limit():
    """Edge case: All accounts at hard limit (300 servers)."""
    account_results = [  # noqa: F841
        {
            "accountId": f"{i:012d}",
            "accountName": f"Account_{i}",
            "accountType": "target" if i == 0 else "staging",
            "replicatingServers": 300,
            "totalServers": 300,
            "regionalBreakdown": [],
            "accessible": True,
        }
        for i in range(3)
    ]

    combined_metrics = calculate_combined_metrics(account_results)
    warnings = generate_warnings(account_results, combined_metrics)

    # Should have HYPER-CRITICAL warnings for all accounts
    hyper_critical_count = sum(1 for w in warnings if "HYPER-CRITICAL" in w)
    assert (
        hyper_critical_count >= 3
    ), "Should have HYPER-CRITICAL warnings for all accounts"


# ============================================================================
# Warning Severity Tests
# ============================================================================


@pytest.mark.property
def test_warning_severity_levels_distinct():
    """Test that different severity levels produce distinct warnings."""
    # Create accounts at each severity level
    account_results = [  # noqa: F841
        {
            "accountId": "111111111111",
            "accountName": "Info_Account",
            "accountType": "target",
            "replicatingServers": 210,  # INFO
            "totalServers": 210,
            "regionalBreakdown": [],
            "accessible": True,
        },
        {
            "accountId": "222222222222",
            "accountName": "Warning_Account",
            "accountType": "staging",
            "replicatingServers": 230,  # WARNING
            "totalServers": 230,
            "regionalBreakdown": [],
            "accessible": True,
        },
        {
            "accountId": "333333333333",
            "accountName": "Critical_Account",
            "accountType": "staging",
            "replicatingServers": 260,  # CRITICAL
            "totalServers": 260,
            "regionalBreakdown": [],
            "accessible": True,
        },
        {
            "accountId": "444444444444",
            "accountName": "HyperCritical_Account",
            "accountType": "staging",
            "replicatingServers": 290,  # HYPER-CRITICAL
            "totalServers": 290,
            "regionalBreakdown": [],
            "accessible": True,
        },
    ]

    combined_metrics = calculate_combined_metrics(account_results)
    warnings = generate_warnings(account_results, combined_metrics)

    # Should have warnings at each severity level
    assert any("INFO" in w for w in warnings), "Should have INFO warning"
    assert any("WARNING" in w for w in warnings), "Should have WARNING"
    assert any(
        "CRITICAL" in w for w in warnings
    ), "Should have CRITICAL warning"
    assert any(
        "HYPER-CRITICAL" in w for w in warnings
    ), "Should have HYPER-CRITICAL warning"
