"""
Property-Based Test: Empty Staging Accounts Default

**Validates: Requirements 8.5**

Property 13: Empty Staging Accounts Default
For any target account where the stagingAccounts attribute does not exist in
DynamoDB, querying the target account should return an empty list for staging
accounts rather than null or undefined.
"""

import json  # noqa: F401
import os  # noqa: E402
import sys  # noqa: E402
import pytest
from pathlib import Path  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: F401  # noqa: F401  # noqa: F401

from moto import mock_aws  # noqa: E402
from hypothesis import given, settings, strategies as st  # noqa: E402

# Set environment variables BEFORE importing index
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts-table"
os.environ["STAGING_ACCOUNTS_TABLE"] = "test-staging-accounts-table"

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent.parent / "lambda" / "query-handler"
sys.path.insert(0, str(lambda_dir))


@mock_aws
@settings(max_examples=100, deadline=2000)  # 2 second deadline for jobs metrics query
@given(
    target_servers=st.integers(min_value=0, max_value=300),
    has_staging_accounts_attr=st.booleans(),
)
@pytest.mark.property
def test_property_13_empty_staging_accounts_default(target_servers, has_staging_accounts_attr):
    """
    Feature: staging-accounts-management
    Property 13: For any target account where the stagingAccounts attribute
    does not exist in DynamoDB, querying the target account should return an
    empty list for staging accounts rather than null or undefined.

    **Validates: Requirements 8.5**
    """
    # Import boto3 and reload index INSIDE the test after @mock_aws is active
    import boto3

    # Clear and reload index module to use mocked AWS
    if "index" in sys.modules:
        del sys.modules["index"]
    import index
    from index import handle_get_combined_capacity  # noqa: F401

    # Create mock DynamoDB table using moto
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Delete existing table if it exists
    try:
        existing_table = dynamodb.Table("test-target-accounts-table")  # noqa: F841
        existing_table.delete()
        existing_table.wait_until_not_exists()
    except Exception:  # noqa: E722
        pass

    # Create fresh table
    table = dynamodb.create_table(  # noqa: F841
        TableName="test-target-accounts-table",
        KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "accountId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Mock target account ID
    target_account_id = "111122223333"  # noqa: F841

    # Build target account configuration
    target_account = {
        "accountId": target_account_id,
        "accountName": "Target Account",
        "roleArn": f"arn:aws:iam::{target_account_id}:role/TestRole",
        "externalId": f"test-external-id-{target_account_id}",
    }

    # Conditionally add stagingAccounts attribute
    if has_staging_accounts_attr:
        # When attribute exists, it could be empty list or have accounts
        target_account["stagingAccounts"] = []

    # Put the target account in the table
    table.put_item(Item=target_account)

    # Mock query_all_accounts_parallel to return predictable results
    def mock_query_all_accounts(target, staging_list):
        # Property: staging_list should always be a list (never None)
        assert isinstance(staging_list, list), f"staging_list should be a list, got {type(staging_list)}"

        results = []  # noqa: F841

        # Add target account result
        results.append(
            {
                "accountId": target["accountId"],
                "accountName": target.get("accountName", "Target Account"),
                "accountType": "target",
                "replicatingServers": target_servers,
                "totalServers": target_servers,
                "regionalBreakdown": [
                    {
                        "region": "us-east-1",
                        "totalServers": target_servers,
                        "replicatingServers": target_servers,
                    }
                ],
                "accessible": True,
            }
        )

        # Add staging account results (should be empty if no staging accounts)
        for staging in staging_list:
            results.append(
                {
                    "accountId": staging["accountId"],
                    "accountName": staging.get("accountName", "Staging"),
                    "accountType": "staging",
                    "replicatingServers": 0,
                    "totalServers": 0,
                    "regionalBreakdown": [],
                    "accessible": True,
                }
            )

        return results

    # Patch the query function and table to use mocked versions
    with (
        patch.object(index, "query_all_accounts_parallel", side_effect=mock_query_all_accounts),
        patch.object(index, "get_target_accounts_table", return_value=table),
    ):
        # Call handle_get_combined_capacity
        result = handle_get_combined_capacity({"targetAccountId": target_account_id})  # noqa: F841

        # Parse response
        assert result["statusCode"] == 200
        body = json.loads(result["body"])

        # Property: Should always have accounts list
        assert "accounts" in body, "Response missing 'accounts' field"
        accounts = body["accounts"]
        assert isinstance(accounts, list), f"accounts should be a list, got {type(accounts)}"

        # Property: When stagingAccounts attribute is missing or empty,
        # should have exactly 1 account (target only)
        if not has_staging_accounts_attr or not target_account.get("stagingAccounts"):
            assert len(accounts) == 1, f"Expected 1 account (target only), got {len(accounts)}"

            # Should be the target account
            assert accounts[0]["accountType"] == "target"
            assert accounts[0]["accountId"] == target_account_id

        # Property: Should never have None or undefined in accounts list
        for account in accounts:
            assert account is not None, "Account should not be None"
            assert isinstance(account, dict), f"Account should be dict, got {type(account)}"

        # Property: Combined metrics should reflect only target account
        # when no staging accounts
        combined = body.get("combined", {})
        assert "totalReplicating" in combined
        assert "maxReplicating" in combined

        if not has_staging_accounts_attr or not target_account.get("stagingAccounts"):
            # With only target account, maxReplicating should be 300
            assert combined["maxReplicating"] == 300, (
                "Expected maxReplicating=300 for single account, " f"got {combined['maxReplicating']}"
            )

            # totalReplicating should match target account servers
            assert combined["totalReplicating"] == target_servers, (
                f"Expected totalReplicating={target_servers}, " f"got {combined['totalReplicating']}"
            )


@mock_aws
@settings(max_examples=50, deadline=2000)  # 2 second deadline for jobs metrics query
@given(
    target_servers=st.integers(min_value=0, max_value=300),
)
@pytest.mark.property
def test_property_13_missing_staging_accounts_attribute(target_servers):
    """
    Specific test case: stagingAccounts attribute completely missing from
    DynamoDB item.

    This tests the edge case where the attribute was never set (not even
    to an empty list).
    """
    # Import boto3 and reload index INSIDE the test after @mock_aws is active
    import boto3

    # Clear and reload index module to use mocked AWS
    if "index" in sys.modules:
        del sys.modules["index"]
    import index
    from index import handle_get_combined_capacity  # noqa: F401

    # Create mock DynamoDB table using moto
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Delete existing table if it exists
    try:
        existing_table = dynamodb.Table("test-target-accounts-table")  # noqa: F841
        existing_table.delete()
        existing_table.wait_until_not_exists()
    except Exception:  # noqa: E722
        pass

    # Create fresh table
    table = dynamodb.create_table(  # noqa: F841
        TableName="test-target-accounts-table",
        KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "accountId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Mock target account ID
    target_account_id = "111122223333"  # noqa: F841

    # Build target account WITHOUT stagingAccounts attribute
    target_account = {
        "accountId": target_account_id,
        "accountName": "Target Account",
        "roleArn": f"arn:aws:iam::{target_account_id}:role/TestRole",
        "externalId": f"test-external-id-{target_account_id}",
        # NOTE: stagingAccounts attribute is intentionally missing
    }

    # Put the target account in the table
    table.put_item(Item=target_account)

    # Track what was passed to query_all_accounts_parallel
    staging_list_passed = None

    def mock_query_all_accounts(target, staging_list):
        nonlocal staging_list_passed
        staging_list_passed = staging_list

        # Property: staging_list should be an empty list, not None
        assert staging_list is not None, "staging_list should not be None when attribute is missing"
        assert isinstance(staging_list, list), f"staging_list should be a list, got {type(staging_list)}"
        assert len(staging_list) == 0, (
            "staging_list should be empty when attribute is missing, " f"got {len(staging_list)} items"
        )

        # Return only target account
        return [
            {
                "accountId": target["accountId"],
                "accountName": target.get("accountName", "Target Account"),
                "accountType": "target",
                "replicatingServers": target_servers,
                "totalServers": target_servers,
                "regionalBreakdown": [
                    {
                        "region": "us-east-1",
                        "totalServers": target_servers,
                        "replicatingServers": target_servers,
                    }
                ],
                "accessible": True,
            }
        ]

    with (
        patch.object(index, "query_all_accounts_parallel", side_effect=mock_query_all_accounts),
        patch.object(index, "get_target_accounts_table", return_value=table),
    ):
        # Call handle_get_combined_capacity
        result = handle_get_combined_capacity({"targetAccountId": target_account_id})  # noqa: F841

        # Verify the function was called
        assert staging_list_passed is not None, "query_all_accounts_parallel was not called"

        # Parse response
        assert result["statusCode"] == 200
        body = json.loads(result["body"])

        # Property: Should have exactly 1 account (target only)
        accounts = body.get("accounts", [])
        assert len(accounts) == 1, "Expected 1 account when stagingAccounts missing, " f"got {len(accounts)}"

        # Property: The single account should be the target
        assert accounts[0]["accountType"] == "target"
        assert accounts[0]["accountId"] == target_account_id


if __name__ == "__main__":
    # Run tests for debugging
    test_property_13_empty_staging_accounts_default()
    print("✅ Property 13 main test passed")

    test_property_13_missing_staging_accounts_attribute()
    print("✅ Property 13 missing attribute test passed")
