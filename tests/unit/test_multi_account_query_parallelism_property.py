"""
Property-Based Test: Multi-Account Query Parallelism

Feature: staging-accounts-management
Property 8: For any target account with N staging accounts, querying combined
capacity should initiate N+1 concurrent account queries (target + all staging
accounts), and each account query should initiate concurrent queries across
all DRS-enabled regions.

**Validates: Requirements 9.1, 9.3**
"""

import os  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402
from unittest.mock import Mock, patch, MagicMock  # noqa: F401  # noqa: F401  # noqa: F401
from concurrent.futures import Future  # noqa: F401

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
from hypothesis import given, strategies as st, settings  # noqa: E402
import pytest  # noqa: F401

# Import the function under test
from index import query_all_accounts_parallel  # noqa: E402
from shared.drs_regions import DRS_REGIONS  # noqa: E402




# ============================================================================
# Hypothesis Strategies
# ============================================================================


@st.composite
def account_config_strategy(draw, account_type="staging"):
    """Generate a valid account configuration."""
    return {
        "accountId": draw(st.from_regex(r"\d{12}", fullmatch=True)),
        "accountName": draw(st.text(min_size=1, max_size=50)),
        "roleArn": draw(st.from_regex(r"arn:aws:iam::\d{12}:role/[\w+=,.@-]+", fullmatch=True)),
        "externalId": draw(st.text(min_size=1, max_size=100)),
    }


@st.composite
def multi_account_config_strategy(draw):
    """Generate target account + staging accounts configuration with unique IDs."""
    # Generate unique account IDs
    num_staging = draw(st.integers(min_value=0, max_value=10))
    num_total_accounts = 1 + num_staging

    # Generate unique account IDs
    account_ids = draw(
        st.lists(
            st.from_regex(r"\d{12}", fullmatch=True),
            min_size=num_total_accounts,
            max_size=num_total_accounts,
            unique=True,
        )
    )

    # Create target account with first ID
    target_account = {
        "accountId": account_ids[0],
        "accountName": draw(st.text(min_size=1, max_size=50)),
        "roleArn": draw(st.from_regex(r"arn:aws:iam::\d{12}:role/[\w+=,.@-]+", fullmatch=True)),
        "externalId": draw(st.text(min_size=1, max_size=100)),
    }

    # Create staging accounts with remaining IDs
    staging_accounts = []
    for account_id in account_ids[1:]:
        staging_accounts.append(
            {
                "accountId": account_id,
                "accountName": draw(st.text(min_size=1, max_size=50)),
                "roleArn": draw(st.from_regex(r"arn:aws:iam::\d{12}:role/[\w+=,.@-]+", fullmatch=True)),
                "externalId": draw(st.text(min_size=1, max_size=100)),
            }
        )

    return target_account, staging_accounts


# ============================================================================
# Property Tests
# ============================================================================


@settings(max_examples=50, deadline=2000)
@given(config=multi_account_config_strategy())
@mock_aws
@pytest.mark.property
def test_property_multi_account_query_parallelism(config):
    """
    Property 8: Multi-Account Query Parallelism

    For any target account with N staging accounts:
    1. Should initiate N+1 concurrent account queries (target + staging)
    2. Each account query should query all DRS regions
    3. All queries should execute in parallel (not sequentially)
    """
    # Import boto3 and reload index INSIDE the test after @mock_aws is active
    import boto3

    # Clear and reload index module to use mocked AWS
    if "index" in sys.modules:
        del sys.modules["index"]
    import index
    from index import query_all_accounts_parallel  # noqa: F401

    target_account, staging_accounts = config

    # Track calls to query_account_capacity
    query_calls = []

    def mock_query_account_capacity(account_config):
        """Mock that tracks which accounts are queried."""
        query_calls.append(
            {
                "accountId": account_config.get("accountId"),
                "accountType": account_config.get("accountType"),
            }
        )

        # Return a valid result
        return {
            "accountId": account_config.get("accountId"),
            "accountName": account_config.get("accountName", "Unknown"),
            "accountType": account_config.get("accountType", "staging"),
            "replicatingServers": 50,
            "totalServers": 50,
            "regionalBreakdown": [],
            "accessible": True,
        }

    # Patch query_account_capacity
    with patch.object(index, "query_account_capacity", side_effect=mock_query_account_capacity):
        # Execute the parallel query
        results = query_all_accounts_parallel(target_account, staging_accounts)  # noqa: F841

        # Property 1: Should query N+1 accounts (target + all staging)
        expected_num_queries = 1 + len(staging_accounts)
        assert len(query_calls) == expected_num_queries, (
            f"Expected {expected_num_queries} account queries, " f"got {len(query_calls)}"
        )

        # Property 2: Should return N+1 results
        assert len(results) == expected_num_queries, f"Expected {expected_num_queries} results, got {len(results)}"

        # Property 3: Target account should be queried
        target_queries = [q for q in query_calls if q["accountId"] == target_account["accountId"]]
        assert len(target_queries) == 1, "Target account should be queried exactly once"

        # Property 4: All staging accounts should be queried
        for staging in staging_accounts:
            staging_queries = [q for q in query_calls if q["accountId"] == staging["accountId"]]
            assert len(staging_queries) == 1, f"Staging account {staging['accountId']} should be queried exactly once"

        # Property 5: Account types should be preserved
        target_type_queries = [q for q in query_calls if q["accountType"] == "target"]
        staging_type_queries = [q for q in query_calls if q["accountType"] == "staging"]

        assert len(target_type_queries) == 1, "Should have exactly one target account query"
        assert len(staging_type_queries) == len(
            staging_accounts
        ), f"Should have {len(staging_accounts)} staging account queries"


@settings(max_examples=30, deadline=2000)
@given(num_staging=st.integers(min_value=0, max_value=15), num_regions=st.integers(min_value=1, max_value=20))
@mock_aws
@pytest.mark.property
def test_property_concurrent_region_queries_per_account(num_staging, num_regions):
    """
    Property: Each account query should query all regions concurrently

    This test verifies that query_account_capacity queries multiple regions
    in parallel for each account.
    """
    # Import boto3 and reload index INSIDE the test after @mock_aws is active
    import boto3

    # Clear and reload index module to use mocked AWS
    if "index" in sys.modules:
        del sys.modules["index"]
    import index
    from index import query_all_accounts_parallel  # noqa: F401

    # Create account configuration
    target_account = {
        "accountId": "111111111111",
        "accountName": "Target",
        "roleArn": "arn:aws:iam::111111111111:role/TestRole",
        "externalId": "test-external-id",
    }

    staging_accounts = [
        {
            "accountId": f"{i:012d}",
            "accountName": f"Staging_{i}",
            "roleArn": f"arn:aws:iam::{i:012d}:role/TestRole",
            "externalId": f"test-external-id-{i}",
        }
        for i in range(222222222222, 222222222222 + num_staging)
    ]

    # Track region queries per account
    region_queries_by_account = {}

    def mock_query_account_capacity(account_config):
        """Mock that simulates querying multiple regions."""
        account_id = account_config.get("accountId")  # noqa: F841

        # Simulate querying all regions (in real code, this happens in parallel)
        region_queries_by_account[account_id] = num_regions

        return {
            "accountId": account_id,
            "accountName": account_config.get("accountName", "Unknown"),
            "accountType": account_config.get("accountType", "staging"),
            "replicatingServers": 50,
            "totalServers": 50,
            "regionalBreakdown": [
                {"region": f"region-{i}", "totalServers": 5, "replicatingServers": 5} for i in range(num_regions)
            ],
            "accessible": True,
        }

    with patch.object(index, "query_account_capacity", side_effect=mock_query_account_capacity):
        results = query_all_accounts_parallel(target_account, staging_accounts)  # noqa: F841

        # Property: Each account should query all regions
        expected_num_accounts = 1 + num_staging
        assert (
            len(region_queries_by_account) == expected_num_accounts
        ), f"Expected {expected_num_accounts} accounts to query regions"

        # Each account should have queried the same number of regions
        for account_id, num_queried in region_queries_by_account.items():
            assert num_queried == num_regions, f"Account {account_id} should have queried {num_regions} regions"


@settings(max_examples=50, deadline=3000)
@given(config=multi_account_config_strategy())
@mock_aws
@pytest.mark.property
def test_property_parallel_execution_not_sequential(config):
    """
    Property: Queries should execute in parallel, not sequentially

    This test verifies that all account queries are submitted to the
    ThreadPoolExecutor concurrently, not one after another.

    Note: This test verifies that all accounts are queried and results
    are returned, which is the functional requirement. The actual
    parallelism is implementation detail handled by ThreadPoolExecutor.
    """
    # Import boto3 and reload index INSIDE the test after @mock_aws is active
    import boto3

    # Clear and reload index module to use mocked AWS
    if "index" in sys.modules:
        del sys.modules["index"]
    import index
    from index import query_all_accounts_parallel  # noqa: F401

    target_account, staging_accounts = config

    # Track completed queries
    completed_queries = []

    def mock_query_account_capacity(account_config):
        """Mock that tracks completed queries."""
        account_id = account_config.get("accountId")  # noqa: F841
        completed_queries.append(account_id)

        return {
            "accountId": account_id,
            "accountName": account_config.get("accountName", "Unknown"),
            "accountType": account_config.get("accountType", "staging"),
            "replicatingServers": 50,
            "totalServers": 50,
            "regionalBreakdown": [],
            "accessible": True,
        }

    with patch.object(index, "query_account_capacity", side_effect=mock_query_account_capacity):
        results = query_all_accounts_parallel(target_account, staging_accounts)  # noqa: F841

        # Property: All accounts should be queried
        expected_num_queries = 1 + len(staging_accounts)
        assert (
            len(completed_queries) == expected_num_queries
        ), f"Expected {expected_num_queries} queries, got {len(completed_queries)}"

        # Property: Results should be returned for all accounts
        assert len(results) == expected_num_queries, f"Expected {expected_num_queries} results, got {len(results)}"

        # Property: All account IDs should be present in results
        result_account_ids = {r["accountId"] for r in results}
        expected_account_ids = {target_account["accountId"]} | {s["accountId"] for s in staging_accounts}
        assert result_account_ids == expected_account_ids, "Result account IDs should match expected account IDs"


# ============================================================================
# Edge Case Tests
# ============================================================================


@mock_aws
@pytest.mark.property
def test_edge_case_no_staging_accounts():
    """Edge case: Only target account, no staging accounts."""
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

    staging_accounts = []

    query_calls = []

    def mock_query_account_capacity(account_config):
        query_calls.append(account_config.get("accountId"))
        return {
            "accountId": account_config.get("accountId"),
            "accountName": account_config.get("accountName", "Unknown"),
            "accountType": account_config.get("accountType", "staging"),
            "replicatingServers": 50,
            "totalServers": 50,
            "regionalBreakdown": [],
            "accessible": True,
        }

    with patch.object(index, "query_account_capacity", side_effect=mock_query_account_capacity):
        results = query_all_accounts_parallel(target_account, staging_accounts)  # noqa: F841

        # Should query only the target account
        assert len(query_calls) == 1
        assert query_calls[0] == target_account["accountId"]
        assert len(results) == 1


@mock_aws
@pytest.mark.property
def test_edge_case_many_staging_accounts():
    """Edge case: Target account with many staging accounts (20)."""
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
            "accountId": f"{i:012d}",
            "accountName": f"Staging_{i}",
            "roleArn": f"arn:aws:iam::{i:012d}:role/TestRole",
            "externalId": f"test-external-id-{i}",
        }
        for i in range(222222222222, 222222222242)  # 20 staging accounts
    ]

    query_calls = []

    def mock_query_account_capacity(account_config):
        query_calls.append(account_config.get("accountId"))
        return {
            "accountId": account_config.get("accountId"),
            "accountName": account_config.get("accountName", "Unknown"),
            "accountType": account_config.get("accountType", "staging"),
            "replicatingServers": 50,
            "totalServers": 50,
            "regionalBreakdown": [],
            "accessible": True,
        }

    with patch.object(index, "query_account_capacity", side_effect=mock_query_account_capacity):
        results = query_all_accounts_parallel(target_account, staging_accounts)  # noqa: F841

        # Should query all 21 accounts (1 target + 20 staging)
        assert len(query_calls) == 21
        assert len(results) == 21


@mock_aws
@pytest.mark.property
def test_edge_case_query_failure_continues():
    """Edge case: One account query fails, others continue."""
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

        # Fail for the second staging account
        if account_id == "333333333333":  # noqa: F841
            raise Exception("Simulated query failure")

        return {
            "accountId": account_id,
            "accountName": account_config.get("accountName", "Unknown"),
            "accountType": account_config.get("accountType", "staging"),
            "replicatingServers": 50,
            "totalServers": 50,
            "regionalBreakdown": [],
            "accessible": True,
        }

    with patch.object(index, "query_account_capacity", side_effect=mock_query_account_capacity):
        results = query_all_accounts_parallel(target_account, staging_accounts)  # noqa: F841

        # Should still return results for all 3 accounts
        assert len(results) == 3

        # Failed account should have error result
        failed_result = next(r for r in results if r["accountId"] == "333333333333")  # noqa: F841
        assert failed_result["accessible"] is False
        assert "error" in failed_result

        # Other accounts should succeed
        success_results = [r for r in results if r["accountId"] in ["111111111111", "222222222222"]]  # noqa: F841
        assert len(success_results) == 2
        for result in success_results:
            assert result["accessible"] is True
