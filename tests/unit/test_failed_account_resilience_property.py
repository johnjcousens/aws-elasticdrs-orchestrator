"""
Property-Based Test: Failed Account Resilience

Feature: staging-accounts-management
Property 10: For any combined capacity query where role assumption fails for
one or more staging accounts, the query should mark those accounts as
inaccessible, continue querying remaining accessible accounts, and return
partial results with error indicators for failed accounts.

**Validates: Requirements 9.5**
"""

import os  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402
from unittest.mock import Mock, patch, MagicMock  # noqa: F401  # noqa: F401  # noqa: F401
from botocore.exceptions import ClientError  # noqa: F401

# Set environment variables BEFORE importing index
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts-table"
os.environ["STAGING_ACCOUNTS_TABLE"] = "test-staging-accounts-table"

# Clear any existing index module to avoid conflicts
if "index" in sys.modules:
    del sys.modules["index"]

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent.parent / "lambda" / "query-handler"
sys.path.insert(0, str(lambda_dir))

from moto import mock_aws  # noqa: E402
from hypothesis import given, strategies as st, settings, assume  # noqa: E402
import pytest  # noqa: F401

# Import the function under test
from index import query_all_accounts_parallel  # noqa: E402


# ============================================================================
# Hypothesis Strategies
# ============================================================================


@st.composite
def account_failure_scenario_strategy(draw):
    """
    Generate a scenario with some accounts failing and others succeeding.

    Returns:
    - target_account: Target account config
    - staging_accounts: List of staging account configs
    - failed_account_ids: Set of account IDs that should fail
    """
    # Generate 1-10 staging accounts
    num_staging = draw(st.integers(min_value=1, max_value=10))

    # Generate unique account IDs
    account_ids = draw(
        st.lists(
            st.from_regex(r"\d{12}", fullmatch=True), min_size=num_staging + 1, max_size=num_staging + 1, unique=True
        )
    )

    # Create target account
    target_account = {
        "accountId": account_ids[0],
        "accountName": "Target Account",
        "roleArn": f"arn:aws:iam::{account_ids[0]}:role/TestRole",
        "externalId": f"external-id-{account_ids[0]}",
    }

    # Create staging accounts
    staging_accounts = []
    for account_id in account_ids[1:]:
        staging_accounts.append(
            {
                "accountId": account_id,
                "accountName": f"Staging_{account_id}",
                "roleArn": f"arn:aws:iam::{account_id}:role/TestRole",
                "externalId": f"external-id-{account_id}",
            }
        )

    # Randomly select which accounts should fail (at least 1, but not all)
    num_failed = draw(st.integers(min_value=1, max_value=num_staging))
    failed_indices = draw(
        st.lists(
            st.integers(min_value=0, max_value=num_staging - 1), min_size=num_failed, max_size=num_failed, unique=True
        )
    )

    # Convert indices to account IDs (skip target account at index 0)
    failed_account_ids = {account_ids[i + 1] for i in failed_indices}

    return target_account, staging_accounts, failed_account_ids


# ============================================================================
# Property Tests
# ============================================================================


@settings(max_examples=100, deadline=None)
@given(scenario=account_failure_scenario_strategy())
@mock_aws
@pytest.mark.property
def test_property_failed_account_resilience(scenario):
    """
    Property 10: Failed Account Resilience

    For any combined capacity query where some accounts fail:
    1. Failed accounts should be marked as inaccessible
    2. Failed accounts should have error field
    3. Successful accounts should return normal results
    4. Query should return results for all accounts (failed + successful)
    5. Total number of results should equal total number of accounts
    """
    # Import boto3 and reload index INSIDE the test after @mock_aws is active
    import boto3

    # Clear and reload index module to use mocked AWS
    if "index" in sys.modules:
        del sys.modules["index"]
    import index
    from index import query_all_accounts_parallel  # noqa: F401

    target_account, staging_accounts, failed_account_ids = scenario

    def mock_query_account_capacity(account_config):
        """Mock that simulates account query with some failures."""
        account_id = account_config.get("accountId")  # noqa: F841

        if account_id in failed_account_ids:
            # Simulate role assumption failure
            return {
                "accountId": account_id,
                "accountName": account_config.get("accountName", "Unknown"),
                "accountType": account_config.get("accountType", "staging"),
                "replicatingServers": 0,
                "totalServers": 0,
                "regionalBreakdown": [],
                "accessible": False,
                "error": "Role assumption failed: Access Denied",
            }
        else:
            # Successful query
            return {
                "accountId": account_id,
                "accountName": account_config.get("accountName", "Unknown"),
                "accountType": account_config.get("accountType", "staging"),
                "replicatingServers": 50,
                "totalServers": 50,
                "regionalBreakdown": [{"region": "us-east-1", "totalServers": 50, "replicatingServers": 50}],
                "accessible": True,
            }

    with patch.object(index, "query_account_capacity", side_effect=mock_query_account_capacity):
        results = query_all_accounts_parallel(target_account, staging_accounts)  # noqa: F841

    # Property 1: Should return results for all accounts
    expected_num_accounts = 1 + len(staging_accounts)
    assert len(results) == expected_num_accounts, f"Expected {expected_num_accounts} results, got {len(results)}"

    # Property 2: Failed accounts should be marked as inaccessible
    failed_results = [r for r in results if r["accountId"] in failed_account_ids]  # noqa: F841
    assert len(failed_results) == len(failed_account_ids), f"Expected {len(failed_account_ids)} failed results"

    for result in failed_results:
        assert result["accessible"] is False, f"Account {result['accountId']} should be marked as inaccessible"
        assert "error" in result, f"Account {result['accountId']} should have error field"
        assert result["replicatingServers"] == 0, "Failed account should have 0 replicating servers"

    # Property 3: Successful accounts should return normal results
    successful_results = [r for r in results if r["accountId"] not in failed_account_ids]  # noqa: F841

    for result in successful_results:
        assert result["accessible"] is True, f"Account {result['accountId']} should be accessible"
        assert "error" not in result, "Successful account should not have error field"
        assert result["replicatingServers"] > 0, "Successful account should have servers"

    # Property 4: Number of successful + failed = total
    assert len(successful_results) + len(failed_results) == expected_num_accounts


@settings(max_examples=50, deadline=None)
@given(num_staging=st.integers(min_value=2, max_value=10), num_failed=st.integers(min_value=1, max_value=5))
@mock_aws
@pytest.mark.property
def test_property_partial_failure_continues_query(num_staging, num_failed):
    """
    Property: Partial failure continues query

    When some accounts fail, the query should:
    - Continue querying remaining accounts
    - Return results for all accounts
    - Not raise exceptions
    """
    # Import boto3 and reload index INSIDE the test after @mock_aws is active
    import boto3

    # Clear and reload index module to use mocked AWS
    if "index" in sys.modules:
        del sys.modules["index"]
    import index
    from index import query_all_accounts_parallel  # noqa: F401

    assume(num_failed < num_staging)  # At least one account succeeds

    # Generate unique account IDs
    account_ids = [f"{i:012d}" for i in range(num_staging + 1)]

    target_account = {
        "accountId": account_ids[0],
        "accountName": "Target",
        "roleArn": f"arn:aws:iam::{account_ids[0]}:role/TestRole",
        "externalId": "test-external-id",
    }

    staging_accounts = [
        {
            "accountId": account_ids[i],
            "accountName": f"Staging_{i}",
            "roleArn": f"arn:aws:iam::{account_ids[i]}:role/TestRole",
            "externalId": f"test-external-id-{i}",
        }
        for i in range(1, num_staging + 1)
    ]

    # First num_failed staging accounts will fail
    failed_account_ids = set(account_ids[1 : num_failed + 1])

    def mock_query_account_capacity(account_config):
        account_id = account_config.get("accountId")  # noqa: F841

        if account_id in failed_account_ids:
            return {
                "accountId": account_id,
                "accountName": account_config.get("accountName", "Unknown"),
                "accountType": account_config.get("accountType", "staging"),
                "replicatingServers": 0,
                "totalServers": 0,
                "regionalBreakdown": [],
                "accessible": False,
                "error": "Access Denied",
            }
        else:
            return {
                "accountId": account_id,
                "accountName": account_config.get("accountName", "Unknown"),
                "accountType": account_config.get("accountType", "staging"),
                "replicatingServers": 100,
                "totalServers": 100,
                "regionalBreakdown": [],
                "accessible": True,
            }

    with patch.object(index, "query_account_capacity", side_effect=mock_query_account_capacity):
        results = query_all_accounts_parallel(target_account, staging_accounts)  # noqa: F841

    # Verify all accounts returned results
    assert len(results) == num_staging + 1

    # Verify correct number of failures
    failed_results = [r for r in results if not r["accessible"]]  # noqa: F841
    assert len(failed_results) == num_failed

    # Verify correct number of successes
    successful_results = [r for r in results if r["accessible"]]  # noqa: F841
    assert len(successful_results) == num_staging + 1 - num_failed


@settings(max_examples=50, deadline=None)
@given(num_staging=st.integers(min_value=1, max_value=10))
@mock_aws
@pytest.mark.property
def test_property_all_staging_accounts_fail_target_succeeds(num_staging):
    """
    Property: All staging accounts fail, target succeeds

    When all staging accounts fail but target succeeds:
    - Should return results for all accounts
    - Target should be accessible
    - All staging accounts should be inaccessible
    """
    # Import boto3 and reload index INSIDE the test after @mock_aws is active
    import boto3

    # Clear and reload index module to use mocked AWS
    if "index" in sys.modules:
        del sys.modules["index"]
    import index
    from index import query_all_accounts_parallel  # noqa: F401

    account_ids = [f"{i:012d}" for i in range(num_staging + 1)]

    target_account = {
        "accountId": account_ids[0],
        "accountName": "Target",
        "roleArn": f"arn:aws:iam::{account_ids[0]}:role/TestRole",
        "externalId": "test-external-id",
    }

    staging_accounts = [
        {
            "accountId": account_ids[i],
            "accountName": f"Staging_{i}",
            "roleArn": f"arn:aws:iam::{account_ids[i]}:role/TestRole",
            "externalId": f"test-external-id-{i}",
        }
        for i in range(1, num_staging + 1)
    ]

    def mock_query_account_capacity(account_config):
        account_id = account_config.get("accountId")  # noqa: F841
        account_type = account_config.get("accountType")

        if account_type == "target":
            # Target succeeds
            return {
                "accountId": account_id,
                "accountName": account_config.get("accountName", "Unknown"),
                "accountType": account_type,
                "replicatingServers": 150,
                "totalServers": 150,
                "regionalBreakdown": [],
                "accessible": True,
            }
        else:
            # All staging accounts fail
            return {
                "accountId": account_id,
                "accountName": account_config.get("accountName", "Unknown"),
                "accountType": account_type,
                "replicatingServers": 0,
                "totalServers": 0,
                "regionalBreakdown": [],
                "accessible": False,
                "error": "Access Denied",
            }

    with patch.object(index, "query_account_capacity", side_effect=mock_query_account_capacity):
        results = query_all_accounts_parallel(target_account, staging_accounts)  # noqa: F841

    # Verify all accounts returned results
    assert len(results) == num_staging + 1

    # Verify target is accessible
    target_results = [r for r in results if r["accountType"] == "target"]  # noqa: F841
    assert len(target_results) == 1
    assert target_results[0]["accessible"] is True

    # Verify all staging accounts are inaccessible
    staging_results = [r for r in results if r["accountType"] == "staging"]  # noqa: F841
    assert len(staging_results) == num_staging
    for result in staging_results:
        assert result["accessible"] is False


# ============================================================================
# Edge Case Tests
# ============================================================================


@mock_aws
@pytest.mark.property
def test_edge_case_target_fails_all_staging_succeed():
    """Edge case: Target account fails, all staging accounts succeed."""
    # Import boto3 and reload index INSIDE the test after @mock_aws is active
    import boto3

    # Clear and reload index module to use mocked AWS
    if "index" in sys.modules:
        del sys.modules["index"]
    import index
    from index import query_all_accounts_parallel  # noqa: F401

    target_account = {
        "accountId": "111111111111",
        "accountName": "Target",
        "roleArn": "arn:aws:iam::111111111111:role/TestRole",
        "externalId": "test-external-id",
    }

    staging_accounts = [
        {
            "accountId": "222222222222",
            "accountName": "Staging_1",
            "roleArn": "arn:aws:iam::222222222222:role/TestRole",
            "externalId": "test-external-id-1",
        },
        {
            "accountId": "333333333333",
            "accountName": "Staging_2",
            "roleArn": "arn:aws:iam::333333333333:role/TestRole",
            "externalId": "test-external-id-2",
        },
    ]

    def mock_query_account_capacity(account_config):
        account_id = account_config.get("accountId")  # noqa: F841
        account_type = account_config.get("accountType")

        if account_id == "111111111111":  # noqa: F841
            # Target fails
            return {
                "accountId": account_id,
                "accountName": account_config.get("accountName", "Unknown"),
                "accountType": account_type,
                "replicatingServers": 0,
                "totalServers": 0,
                "regionalBreakdown": [],
                "accessible": False,
                "error": "Access Denied",
            }
        else:
            # Staging accounts succeed
            return {
                "accountId": account_id,
                "accountName": account_config.get("accountName", "Unknown"),
                "accountType": account_type,
                "replicatingServers": 100,
                "totalServers": 100,
                "regionalBreakdown": [],
                "accessible": True,
            }

    with patch.object(index, "query_account_capacity", side_effect=mock_query_account_capacity):
        results = query_all_accounts_parallel(target_account, staging_accounts)  # noqa: F841

    assert len(results) == 3

    # Target should be inaccessible
    target_result = next(r for r in results if r["accountId"] == "111111111111")  # noqa: F841
    assert target_result["accessible"] is False

    # Staging accounts should be accessible
    staging_results = [r for r in results if r["accountType"] == "staging"]  # noqa: F841
    assert len(staging_results) == 2
    for result in staging_results:
        assert result["accessible"] is True


@mock_aws
@pytest.mark.property
def test_edge_case_different_error_types():
    """Edge case: Different types of errors for different accounts."""
    # Import boto3 and reload index INSIDE the test after @mock_aws is active
    import boto3

    # Clear and reload index module to use mocked AWS
    if "index" in sys.modules:
        del sys.modules["index"]
    import index
    from index import query_all_accounts_parallel  # noqa: F401

    target_account = {
        "accountId": "111111111111",
        "accountName": "Target",
        "roleArn": "arn:aws:iam::111111111111:role/TestRole",
        "externalId": "test-external-id",
    }

    staging_accounts = [
        {
            "accountId": "222222222222",
            "accountName": "Staging_1",
            "roleArn": "arn:aws:iam::222222222222:role/TestRole",
            "externalId": "test-external-id-1",
        },
        {
            "accountId": "333333333333",
            "accountName": "Staging_2",
            "roleArn": "arn:aws:iam::333333333333:role/TestRole",
            "externalId": "test-external-id-2",
        },
        {
            "accountId": "444444444444",
            "accountName": "Staging_3",
            "roleArn": "arn:aws:iam::444444444444:role/TestRole",
            "externalId": "test-external-id-3",
        },
    ]

    def mock_query_account_capacity(account_config):
        account_id = account_config.get("accountId")  # noqa: F841

        if account_id == "111111111111":  # noqa: F841
            # Target succeeds
            return {
                "accountId": account_id,
                "accountName": account_config.get("accountName", "Unknown"),
                "accountType": "target",
                "replicatingServers": 150,
                "totalServers": 150,
                "regionalBreakdown": [],
                "accessible": True,
            }
        elif account_id == "222222222222":  # noqa: F841
            # Access denied error
            return {
                "accountId": account_id,
                "accountName": account_config.get("accountName", "Unknown"),
                "accountType": "staging",
                "replicatingServers": 0,
                "totalServers": 0,
                "regionalBreakdown": [],
                "accessible": False,
                "error": "Role assumption failed: Access Denied",
            }
        elif account_id == "333333333333":  # noqa: F841
            # Invalid credentials error
            return {
                "accountId": account_id,
                "accountName": account_config.get("accountName", "Unknown"),
                "accountType": "staging",
                "replicatingServers": 0,
                "totalServers": 0,
                "regionalBreakdown": [],
                "accessible": False,
                "error": "Invalid credentials",
            }
        else:
            # Network timeout error
            return {
                "accountId": account_id,
                "accountName": account_config.get("accountName", "Unknown"),
                "accountType": "staging",
                "replicatingServers": 0,
                "totalServers": 0,
                "regionalBreakdown": [],
                "accessible": False,
                "error": "Network timeout",
            }

    with patch.object(index, "query_account_capacity", side_effect=mock_query_account_capacity):
        results = query_all_accounts_parallel(target_account, staging_accounts)  # noqa: F841

    assert len(results) == 4

    # Verify each account has appropriate error
    for result in results:
        if result["accountId"] == "111111111111":
            assert result["accessible"] is True
        else:
            assert result["accessible"] is False
            assert "error" in result
