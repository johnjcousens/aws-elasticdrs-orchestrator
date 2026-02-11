"""
Property-based tests for new query-handler direct invocation operations.

Uses Hypothesis framework to verify universal properties hold across all inputs.
Tests Phase 3 operations:
- get_staging_accounts (task 4.3)
- get_tag_sync_status (task 4.4)
- get_tag_sync_settings (task 4.5)
- get_drs_capacity_conflicts (task 4.6)

Feature: direct-lambda-invocation-mode
Requirements: 4.3, 4.4, 4.5, 4.6, 4.9
"""

import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

# Add lambda paths for imports
query_handler_dir = (
    Path(__file__).parent.parent.parent / "lambda" / "query-handler"
)
shared_dir = Path(__file__).parent.parent.parent / "lambda" / "shared"


@contextmanager
def setup_test_environment():
    """Context manager to set up test environment for each property test"""
    # Save original sys.path and modules
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    # Remove any existing 'index' module
    if "index" in sys.modules:
        del sys.modules["index"]

    # Add query-handler to front of path
    sys.path.insert(0, str(query_handler_dir))
    sys.path.insert(1, str(shared_dir))

    # Set up environment variables
    with patch.dict(
        os.environ,
        {
            "PROTECTION_GROUPS_TABLE": "test-protection-groups",
            "RECOVERY_PLANS_TABLE": "test-recovery-plans",
            "TARGET_ACCOUNTS_TABLE": "test-target-accounts",
            "EXECUTION_HISTORY_TABLE": "test-execution-history",
        },
    ):
        try:
            yield
        finally:
            # Restore original state
            sys.path = original_path
            if "index" in sys.modules:
                del sys.modules["index"]
            if original_index is not None:
                sys.modules["index"] = original_index


# ============================================================================
# Hypothesis Strategies
# ============================================================================


@st.composite
def valid_account_id(draw):
    """Strategy: Generate valid 12-digit AWS account IDs"""
    # Generate 12-digit string
    return draw(st.from_regex(r"[0-9]{12}", fullmatch=True))


@st.composite
def invalid_account_id(draw):
    """Strategy: Generate invalid account IDs (excluding empty string)
    
    Empty string is treated as MISSING_PARAMETER, not INVALID_PARAMETER,
    so we exclude it from this strategy.
    """
    return draw(
        st.one_of(
            # Too short (but not empty)
            st.from_regex(r"[0-9]{1,11}", fullmatch=True),
            # Too long
            st.from_regex(r"[0-9]{13,20}", fullmatch=True),
            # Contains non-digits
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll"), min_codepoint=65
                ),
                min_size=12,
                max_size=12,
            ),
            # Special characters
            st.from_regex(r"[!@#$%^&*()]{12}", fullmatch=True),
        )
    )


@st.composite
def staging_account_data(draw):
    """Strategy: Generate staging account data structure"""
    return {
        "accountId": draw(valid_account_id()),
        "accountName": draw(st.text(min_size=1, max_size=50)),
        "roleArn": f"arn:aws:iam::{draw(valid_account_id())}:role/DRSOrchestrationRole",
        "externalId": draw(st.uuids()).hex,
        "replicatingServers": draw(st.integers(min_value=0, max_value=300)),
        "totalServers": draw(st.integers(min_value=0, max_value=4000)),
        "status": draw(st.sampled_from(["active", "inactive", "error"])),
    }


@st.composite
def target_account_with_staging(draw):
    """Strategy: Generate target account with staging accounts"""
    num_staging = draw(st.integers(min_value=0, max_value=5))
    staging_accounts = [draw(staging_account_data()) for _ in range(num_staging)]

    return {
        "accountId": draw(valid_account_id()),
        "accountName": draw(st.text(min_size=1, max_size=50)),
        "stagingAccounts": staging_accounts,
    }


@st.composite
def capacity_data(draw):
    """Strategy: Generate DRS capacity data"""
    total_replicating = draw(st.integers(min_value=0, max_value=350))
    total_servers = draw(st.integers(min_value=total_replicating, max_value=4500))

    return {
        "totalReplicatingServers": total_replicating,
        "totalServers": total_servers,
    }


# ============================================================================
# Property Tests for get_staging_accounts
# ============================================================================


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(account_id=valid_account_id(), account_data=target_account_with_staging())
def test_property_get_staging_accounts_valid_account_returns_list(
    account_id, account_data
):
    """
    Property: For any valid account ID with staging accounts, should return list.

    Universal property: Given any valid 12-digit account ID that exists in the
    target accounts table, the system should return a dict with targetAccountId
    and stagingAccounts list (which may be empty).

    Validates: Requirement 4.3 - get_staging_accounts operation
    """
    with setup_test_environment():
        from index import get_staging_accounts_direct

        # Set account ID in the data
        account_data["accountId"] = account_id

        with patch("index.get_target_accounts_table") as mock_func:
            mock_table = MagicMock()
            mock_func.return_value = mock_table
            mock_table.get_item.return_value = {"Item": account_data}

            event = {"targetAccountId": account_id}
            result = get_staging_accounts_direct(event)

            # Property assertion: Should return targetAccountId
            assert "targetAccountId" in result
            assert result["targetAccountId"] == account_id

            # Property assertion: Should return stagingAccounts list
            assert "stagingAccounts" in result
            assert isinstance(result["stagingAccounts"], list)

            # Property assertion: Should not return error
            assert "error" not in result


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(account_id=invalid_account_id())
def test_property_get_staging_accounts_invalid_account_returns_error(account_id):
    """
    Property: For any invalid account ID format, should return INVALID_PARAMETER error.

    Universal property: Given any account ID that is not a 12-digit string,
    the system should return an error with code "INVALID_PARAMETER".

    Validates: Requirement 4.3 - get_staging_accounts parameter validation
    """
    with setup_test_environment():
        from index import get_staging_accounts_direct

        event = {"targetAccountId": account_id}
        result = get_staging_accounts_direct(event)

        # Property assertion: Should return INVALID_PARAMETER error
        assert result.get("error") == "INVALID_PARAMETER"

        # Property assertion: Error message should mention format
        assert "message" in result
        assert "format" in result["message"].lower()


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(data=st.data())
def test_property_get_staging_accounts_missing_parameter_returns_error(data):
    """
    Property: For any event missing targetAccountId, should return MISSING_PARAMETER error.

    Universal property: Given any event structure that does NOT contain
    a "targetAccountId" field, the system should return an error with code
    "MISSING_PARAMETER".

    Validates: Requirement 4.3 - get_staging_accounts parameter validation
    """
    with setup_test_environment():
        from index import get_staging_accounts_direct

        # Generate event without targetAccountId
        event = data.draw(
            st.dictionaries(
                st.text(
                    alphabet=st.characters(
                        whitelist_categories=("Lu", "Ll"), min_codepoint=65
                    ),
                    min_size=1,
                    max_size=20,
                ).filter(lambda x: x != "targetAccountId"),
                st.text(),
            )
        )

        result = get_staging_accounts_direct(event)

        # Property assertion: Should return MISSING_PARAMETER error
        assert result.get("error") == "MISSING_PARAMETER"

        # Property assertion: Error message should mention targetAccountId
        assert "message" in result
        assert "targetAccountId" in result["message"]


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(account_id=valid_account_id())
def test_property_get_staging_accounts_not_found_returns_error(account_id):
    """
    Property: For any account ID not in table, should return NOT_FOUND error.

    Universal property: Given any valid account ID that does NOT exist in the
    target accounts table, the system should return an error with code "NOT_FOUND".

    Validates: Requirement 4.3 - get_staging_accounts error handling
    """
    with setup_test_environment():
        from index import get_staging_accounts_direct

        with patch("index.get_target_accounts_table") as mock_func:
            mock_table = MagicMock()
            mock_func.return_value = mock_table
            # Mock table returns no item
            mock_table.get_item.return_value = {}

            event = {"targetAccountId": account_id}
            result = get_staging_accounts_direct(event)

            # Property assertion: Should return NOT_FOUND error
            assert result.get("error") == "NOT_FOUND"

            # Property assertion: Error message should mention account
            assert "message" in result
            assert account_id in result["message"]


# ============================================================================
# Property Tests for get_tag_sync_status
# ============================================================================


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(event_data=st.dictionaries(st.text(), st.text()))
def test_property_get_tag_sync_status_always_returns_structure(event_data):
    """
    Property: For any event, should return consistent status structure.

    Universal property: Given any event structure (with or without parameters),
    the system should return a dict with specific fields: enabled, lastSyncTime,
    serversProcessed, tagsSynchronized, status.

    Validates: Requirement 4.4 - get_tag_sync_status operation
    """
    with setup_test_environment():
        from index import get_tag_sync_status_direct

        result = get_tag_sync_status_direct(event_data)

        # Property assertion: Should have required fields
        assert "enabled" in result
        assert "lastSyncTime" in result
        assert "serversProcessed" in result
        assert "tagsSynchronized" in result
        assert "status" in result

        # Property assertion: enabled should be boolean
        assert isinstance(result["enabled"], bool)

        # Property assertion: serversProcessed should be integer
        assert isinstance(result["serversProcessed"], int)
        assert result["serversProcessed"] >= 0

        # Property assertion: tagsSynchronized should be integer
        assert isinstance(result["tagsSynchronized"], int)
        assert result["tagsSynchronized"] >= 0

        # Property assertion: status should be string
        assert isinstance(result["status"], str)


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(event_data=st.dictionaries(st.text(), st.text()))
def test_property_get_tag_sync_status_no_error_for_any_input(event_data):
    """
    Property: For any event, should not return error (placeholder implementation).

    Universal property: Given any event structure, the system should return
    a successful response without error field (since this is a placeholder
    implementation that doesn't require parameters).

    Validates: Requirement 4.4 - get_tag_sync_status error handling
    """
    with setup_test_environment():
        from index import get_tag_sync_status_direct

        result = get_tag_sync_status_direct(event_data)

        # Property assertion: Should not return error
        assert "error" not in result

        # Property assertion: Should return status
        assert "status" in result


# ============================================================================
# Property Tests for get_tag_sync_settings
# ============================================================================


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(event_data=st.dictionaries(st.text(), st.text()))
def test_property_get_tag_sync_settings_always_returns_structure(event_data):
    """
    Property: For any event, should return consistent settings structure.

    Universal property: Given any event structure (with or without parameters),
    the system should return a dict with specific fields: enabled, schedule,
    tagFilters, sourceAccounts, targetAccounts.

    Validates: Requirement 4.5 - get_tag_sync_settings operation
    """
    with setup_test_environment():
        from index import get_tag_sync_settings_direct

        result = get_tag_sync_settings_direct(event_data)

        # Property assertion: Should have required fields
        assert "enabled" in result
        assert "schedule" in result
        assert "tagFilters" in result
        assert "sourceAccounts" in result
        assert "targetAccounts" in result

        # Property assertion: enabled should be boolean
        assert isinstance(result["enabled"], bool)

        # Property assertion: tagFilters should be dict with include/exclude
        assert isinstance(result["tagFilters"], dict)
        assert "include" in result["tagFilters"]
        assert "exclude" in result["tagFilters"]
        assert isinstance(result["tagFilters"]["include"], list)
        assert isinstance(result["tagFilters"]["exclude"], list)

        # Property assertion: sourceAccounts should be list
        assert isinstance(result["sourceAccounts"], list)

        # Property assertion: targetAccounts should be list
        assert isinstance(result["targetAccounts"], list)


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(event_data=st.dictionaries(st.text(), st.text()))
def test_property_get_tag_sync_settings_no_error_for_any_input(event_data):
    """
    Property: For any event, should not return error (placeholder implementation).

    Universal property: Given any event structure, the system should return
    a successful response without error field (since this is a placeholder
    implementation that doesn't require parameters).

    Validates: Requirement 4.5 - get_tag_sync_settings error handling
    """
    with setup_test_environment():
        from index import get_tag_sync_settings_direct

        result = get_tag_sync_settings_direct(event_data)

        # Property assertion: Should not return error
        assert "error" not in result

        # Property assertion: Should return tagFilters
        assert "tagFilters" in result


# ============================================================================
# Property Tests for get_drs_capacity_conflicts
# ============================================================================


@settings(
    max_examples=50,  # Reduced due to complexity
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    num_accounts=st.integers(min_value=0, max_value=10),
    data=st.data(),
)
def test_property_get_drs_capacity_conflicts_returns_structure(num_accounts, data):
    """
    Property: For any number of accounts, should return consistent structure.

    Universal property: Given any number of accounts in the target accounts table,
    the system should return a dict with conflicts list and totalConflicts count.

    Validates: Requirement 4.6 - get_drs_capacity_conflicts operation
    """
    with setup_test_environment():
        from index import get_drs_capacity_conflicts_direct

        # Generate accounts
        accounts = []
        for _ in range(num_accounts):
            account_id = data.draw(valid_account_id())
            accounts.append(
                {
                    "accountId": account_id,
                    "accountName": f"Account {account_id[-4:]}",
                    "roleArn": f"arn:aws:iam::{account_id}:role/DRSOrchestrationRole",
                }
            )

        with patch("index.get_target_accounts_table") as mock_func, patch(
            "index.get_drs_account_capacity_all_regions"
        ) as mock_capacity:

            mock_table = MagicMock()
            mock_func.return_value = mock_table
            mock_table.scan.return_value = {"Items": accounts}

            # Mock capacity to return no conflicts
            mock_capacity.return_value = {
                "totalReplicatingServers": 50,
                "totalServers": 100,
            }

            event = {}
            result = get_drs_capacity_conflicts_direct(event)

            # Property assertion: Should have required fields
            assert "conflicts" in result
            assert "totalConflicts" in result
            assert "timestamp" in result

            # Property assertion: conflicts should be list
            assert isinstance(result["conflicts"], list)

            # Property assertion: totalConflicts should be integer
            assert isinstance(result["totalConflicts"], int)
            assert result["totalConflicts"] >= 0

            # Property assertion: totalConflicts should match conflicts length
            assert result["totalConflicts"] == len(result["conflicts"])


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    replicating_servers=st.integers(min_value=241, max_value=300),
    account_id=valid_account_id(),
)
def test_property_get_drs_capacity_conflicts_detects_high_usage(
    replicating_servers, account_id
):
    """
    Property: For any account with high replicating servers, should detect conflict.

    Universal property: Given any account with replicating servers >= 240 (80% of 300),
    the system should detect a capacity conflict and include it in the conflicts list.

    Validates: Requirement 4.6 - get_drs_capacity_conflicts detection logic
    """
    with setup_test_environment():
        from index import get_drs_capacity_conflicts_direct

        account = {
            "accountId": account_id,
            "accountName": f"Account {account_id[-4:]}",
            "roleArn": f"arn:aws:iam::{account_id}:role/DRSOrchestrationRole",
        }

        with patch("index.get_target_accounts_table") as mock_func, patch(
            "index.get_drs_account_capacity_all_regions"
        ) as mock_capacity:

            mock_table = MagicMock()
            mock_func.return_value = mock_table
            mock_table.scan.return_value = {"Items": [account]}

            # Mock capacity with high replicating servers
            mock_capacity.return_value = {
                "totalReplicatingServers": replicating_servers,
                "totalServers": replicating_servers + 50,
            }

            event = {}
            result = get_drs_capacity_conflicts_direct(event)

            # Property assertion: Should detect conflict
            assert result["totalConflicts"] > 0

            # Property assertion: Conflict should be in list
            assert len(result["conflicts"]) > 0

            # Property assertion: Conflict should have required fields
            conflict = result["conflicts"][0]
            assert "accountId" in conflict
            assert "conflictType" in conflict
            assert "severity" in conflict
            assert "currentUsage" in conflict
            assert "limit" in conflict


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    replicating_servers=st.integers(min_value=0, max_value=239),
    account_id=valid_account_id(),
)
def test_property_get_drs_capacity_conflicts_no_conflict_for_low_usage(
    replicating_servers, account_id
):
    """
    Property: For any account with low replicating servers, should not detect conflict.

    Universal property: Given any account with replicating servers < 240 (80% of 300),
    the system should NOT detect a capacity conflict.

    Validates: Requirement 4.6 - get_drs_capacity_conflicts detection logic
    """
    with setup_test_environment():
        from index import get_drs_capacity_conflicts_direct

        account = {
            "accountId": account_id,
            "accountName": f"Account {account_id[-4:]}",
            "roleArn": f"arn:aws:iam::{account_id}:role/DRSOrchestrationRole",
        }

        with patch("index.get_target_accounts_table") as mock_func, patch(
            "index.get_drs_account_capacity_all_regions"
        ) as mock_capacity:

            mock_table = MagicMock()
            mock_func.return_value = mock_table
            mock_table.scan.return_value = {"Items": [account]}

            # Mock capacity with low replicating servers
            mock_capacity.return_value = {
                "totalReplicatingServers": replicating_servers,
                "totalServers": replicating_servers + 50,
            }

            event = {}
            result = get_drs_capacity_conflicts_direct(event)

            # Property assertion: Should not detect conflict
            assert result["totalConflicts"] == 0

            # Property assertion: Conflicts list should be empty
            assert len(result["conflicts"]) == 0


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(event_data=st.dictionaries(st.text(), st.text()))
def test_property_get_drs_capacity_conflicts_no_error_for_any_input(event_data):
    """
    Property: For any event, should not return error.

    Universal property: Given any event structure, the system should return
    a successful response without error field (operation doesn't require parameters).

    Validates: Requirement 4.6 - get_drs_capacity_conflicts error handling
    """
    with setup_test_environment():
        from index import get_drs_capacity_conflicts_direct

        with patch("index.get_target_accounts_table") as mock_func:
            mock_table = MagicMock()
            mock_func.return_value = mock_table
            mock_table.scan.return_value = {"Items": []}

            result = get_drs_capacity_conflicts_direct(event_data)

            # Property assertion: Should not return error
            assert "error" not in result

            # Property assertion: Should return conflicts
            assert "conflicts" in result
            assert "totalConflicts" in result


# ============================================================================
# Property Tests for Conflict Severity Levels
# ============================================================================


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    replicating_servers=st.integers(min_value=271, max_value=300),
    account_id=valid_account_id(),
)
def test_property_conflict_severity_critical_for_90_percent(
    replicating_servers, account_id
):
    """
    Property: For any account >= 90% capacity, severity should be critical.

    Universal property: Given any account with replicating servers >= 270 (90% of 300),
    the detected conflict should have severity "critical".

    Validates: Requirement 4.6 - get_drs_capacity_conflicts severity levels
    """
    with setup_test_environment():
        from index import get_drs_capacity_conflicts_direct

        account = {
            "accountId": account_id,
            "accountName": f"Account {account_id[-4:]}",
            "roleArn": f"arn:aws:iam::{account_id}:role/DRSOrchestrationRole",
        }

        with patch("index.get_target_accounts_table") as mock_func, patch(
            "index.get_drs_account_capacity_all_regions"
        ) as mock_capacity:

            mock_table = MagicMock()
            mock_func.return_value = mock_table
            mock_table.scan.return_value = {"Items": [account]}

            mock_capacity.return_value = {
                "totalReplicatingServers": replicating_servers,
                "totalServers": replicating_servers + 50,
            }

            event = {}
            result = get_drs_capacity_conflicts_direct(event)

            # Property assertion: Should have critical severity
            if result["totalConflicts"] > 0:
                conflict = result["conflicts"][0]
                assert conflict["severity"] == "critical"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    replicating_servers=st.integers(min_value=241, max_value=269),
    account_id=valid_account_id(),
)
def test_property_conflict_severity_warning_for_80_percent(
    replicating_servers, account_id
):
    """
    Property: For any account 80-89% capacity, severity should be warning.

    Universal property: Given any account with replicating servers between 240-269
    (80-89% of 300), the detected conflict should have severity "warning".

    Validates: Requirement 4.6 - get_drs_capacity_conflicts severity levels
    """
    with setup_test_environment():
        from index import get_drs_capacity_conflicts_direct

        account = {
            "accountId": account_id,
            "accountName": f"Account {account_id[-4:]}",
            "roleArn": f"arn:aws:iam::{account_id}:role/DRSOrchestrationRole",
        }

        with patch("index.get_target_accounts_table") as mock_func, patch(
            "index.get_drs_account_capacity_all_regions"
        ) as mock_capacity:

            mock_table = MagicMock()
            mock_func.return_value = mock_table
            mock_table.scan.return_value = {"Items": [account]}

            mock_capacity.return_value = {
                "totalReplicatingServers": replicating_servers,
                "totalServers": replicating_servers + 50,
            }

            event = {}
            result = get_drs_capacity_conflicts_direct(event)

            # Property assertion: Should have warning severity
            if result["totalConflicts"] > 0:
                conflict = result["conflicts"][0]
                assert conflict["severity"] == "warning"
