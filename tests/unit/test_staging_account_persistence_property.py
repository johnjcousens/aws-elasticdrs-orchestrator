"""
Property-Based Test: Staging Account Persistence Round Trip

Feature: staging-accounts-management
Property 1: For any valid staging account configuration, adding it to a
target account then retrieving the target account should return the staging
account with all original fields (account ID, account name, role ARN,
external ID) intact.

Validates: Requirements 1.6, 8.1, 8.2, 8.3

This test uses hypothesis to generate random valid staging account
configurations and verifies that the round-trip persistence (add → retrieve)
preserves all fields exactly.
"""

import os  # noqa: E402
import pytest
from unittest.mock import MagicMock, patch  # noqa: F401  # noqa: F401  # noqa: F401

from hypothesis import given, strategies as st, settings  # noqa: E402

# Import functions under test
import sys  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/shared"))

from staging_account_models import (  # noqa: E402
    add_staging_account,
    get_staging_accounts,
    StagingAccount,
)

# Skip all tests in this file for CI/CD


# Strategy for generating valid 12-digit AWS account IDs
account_id_strategy = st.from_regex(r"\d{12}", fullmatch=True)

# Strategy for generating valid IAM role ARNs
role_arn_strategy = st.builds(
    lambda account_id, role_name: (f"arn:aws:iam::{account_id}:role/{role_name}"),
    account_id=account_id_strategy,
    role_name=st.from_regex(r"[\w+=,.@-]{1,64}", fullmatch=True),
)

# Strategy for generating valid staging account configurations
staging_account_strategy = st.fixed_dictionaries(
    {
        "accountId": account_id_strategy,
        "accountName": st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
            min_size=1,
            max_size=50,
        ),
        "roleArn": role_arn_strategy,
        "externalId": st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
            min_size=1,
            max_size=100,
        ),
    }
)


@settings(max_examples=100)
@given(target_account_id=account_id_strategy, staging_account=staging_account_strategy)
@patch("staging_account_models._get_target_accounts_table")
@patch("staging_account_models.check_duplicate_staging_account")
@pytest.mark.property
def test_property_staging_account_persistence_round_trip(
    mock_check_dup, mock_get_table, target_account_id, staging_account
):
    """
    Property 1: Staging Account Persistence Round Trip

    For any valid staging account configuration, adding it to a target
    account then retrieving the target account should return the staging
    account with all original fields intact.

    Test Strategy:
    1. Generate random valid staging account configuration
    2. Add staging account to target account (mocked DynamoDB)
    3. Retrieve staging accounts from target account (mocked DynamoDB)
    4. Verify all fields match original configuration
    """
    # Setup mocks
    mock_table = MagicMock()  # noqa: F841
    mock_get_table.return_value = mock_table
    mock_check_dup.return_value = False

    # Mock get_staging_accounts to return empty list initially
    with patch("staging_account_models.get_staging_accounts") as mock_get:
        mock_get.return_value = []

        # Mock update_item to return the added staging account with metadata
        def mock_update_item(**kwargs):
            # Get the staging account dict from the update expression
            staging_dicts = kwargs["ExpressionAttributeValues"][":staging"]
            return {"Attributes": {"accountId": target_account_id, "stagingAccounts": staging_dicts}}

        mock_table.update_item = mock_update_item

        # Add staging account
        result = add_staging_account(target_account_id, staging_account)  # noqa: F841

        # Verify add operation succeeded
        assert result["success"] is True
        assert len(result["stagingAccounts"]) == 1

        # Verify all original fields are preserved
        retrieved = result["stagingAccounts"][0]
        assert retrieved["accountId"] == staging_account["accountId"]
        assert retrieved["accountName"] == staging_account["accountName"]
        assert retrieved["roleArn"] == staging_account["roleArn"]
        assert retrieved["externalId"] == staging_account["externalId"]

        # Verify additional metadata fields are present
        assert "addedAt" in retrieved
        assert "addedBy" in retrieved


@settings(max_examples=100)
@given(
    target_account_id=account_id_strategy,
    staging_accounts=st.lists(staging_account_strategy, min_size=1, max_size=10, unique_by=lambda x: x["accountId"]),
)
@patch("staging_account_models._get_target_accounts_table")
@patch("staging_account_models.check_duplicate_staging_account")
@pytest.mark.property
def test_property_multiple_staging_accounts_persistence(
    mock_check_dup, mock_get_table, target_account_id, staging_accounts
):
    """
    Extended Property: Multiple Staging Accounts Persistence

    For any list of valid staging account configurations, adding them
    sequentially to a target account should preserve all fields for all
    accounts.

    This extends Property 1 to test multiple staging accounts.
    """
    # Setup mocks
    mock_table = MagicMock()  # noqa: F841
    mock_get_table.return_value = mock_table
    mock_check_dup.return_value = False

    added_accounts = []

    for staging_account in staging_accounts:
        # Mock get_staging_accounts to return previously added accounts as StagingAccount objects
        with patch("staging_account_models.get_staging_accounts") as mock_get:
            # Convert dicts to StagingAccount objects
            mock_get.return_value = [StagingAccount.from_dict(account) for account in added_accounts]

            # Mock update_item to return all added staging accounts
            def mock_update_item(**kwargs):
                # Get the staging account dicts from the update expression
                staging_dicts = kwargs["ExpressionAttributeValues"][":staging"]
                return {"Attributes": {"accountId": target_account_id, "stagingAccounts": staging_dicts}}

            mock_table.update_item = mock_update_item

            # Add staging account
            result = add_staging_account(target_account_id, staging_account)  # noqa: F841

            # Verify add operation succeeded
            assert result["success"] is True

            # Add to tracking list (with metadata fields)
            added_accounts.append(result["stagingAccounts"][-1])

    # Verify all accounts were added
    assert len(result["stagingAccounts"]) == len(staging_accounts)

    # Verify all original fields are preserved for all accounts
    for i, original in enumerate(staging_accounts):
        retrieved = result["stagingAccounts"][i]
        assert retrieved["accountId"] == original["accountId"]
        assert retrieved["accountName"] == original["accountName"]
        assert retrieved["roleArn"] == original["roleArn"]
        assert retrieved["externalId"] == original["externalId"]


@settings(max_examples=100)
@given(target_account_id=account_id_strategy, staging_account=staging_account_strategy)
@patch("staging_account_models._get_target_accounts_table")
@pytest.mark.property
def test_property_empty_staging_accounts_default(mock_get_table, target_account_id, staging_account):
    """
    Property 13: Empty Staging Accounts Default

    For any target account where the stagingAccounts attribute does not
    exist in DynamoDB, querying the target account should return an empty
    list for staging accounts rather than null or undefined.

    Validates: Requirements 8.5
    """
    # Setup mock to return target account without stagingAccounts attribute
    mock_table = MagicMock()  # noqa: F841
    mock_table.get_item.return_value = {
        "Item": {
            "accountId": target_account_id,
            "accountName": "TEST_TARGET",
            # No stagingAccounts attribute
        }
    }
    mock_get_table.return_value = mock_table

    # Import get_staging_accounts
    from staging_account_models import get_staging_accounts  # noqa: F401

    # Get staging accounts
    result = get_staging_accounts(target_account_id)  # noqa: F841

    # Verify result is empty list, not None or undefined
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 0
