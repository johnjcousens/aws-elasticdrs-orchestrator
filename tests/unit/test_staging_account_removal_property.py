"""
Property-Based Test: Staging Account Removal Completeness

Feature: staging-accounts-management
Property 2: For any target account with staging accounts, removing a specific
staging account should result in that account no longer appearing in the
staging accounts list while all other staging accounts remain unchanged.

Validates: Requirements 2.2, 8.4
"""

import json
import os
from typing import Dict, List
from unittest.mock import patch

import boto3
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from moto import mock_aws

# Set environment variables before importing handler
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts-table"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Add lambda directory to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.staging_account_models import (
    add_staging_account,
    remove_staging_account,
    get_staging_accounts,
)


# Strategy for generating valid AWS account IDs
account_id_strategy = st.from_regex(r"\d{12}", fullmatch=True)

# Strategy for generating staging account configurations
staging_account_strategy = st.fixed_dictionaries(
    {
        "accountId": account_id_strategy,
        "accountName": st.text(
            min_size=1, max_size=50, alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"),
                whitelist_characters="_-"
            )
        ),
        "roleArn": st.builds(
            lambda acc_id: f"arn:aws:iam::{acc_id}:role/TestRole",
            account_id_strategy,
        ),
        "externalId": st.text(min_size=1, max_size=100),
    }
)


@pytest.fixture
def dynamodb_setup():
    """Set up mock DynamoDB table for testing"""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Create Target Accounts table
        table = dynamodb.create_table(
            TableName="test-target-accounts-table",
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "accountId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield table


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    target_account_id=account_id_strategy,
    staging_accounts=st.lists(
        staging_account_strategy, min_size=2, max_size=5, unique_by=lambda x: x["accountId"]
    ),
    removal_index=st.integers(min_value=0, max_value=4),
)
def test_property_staging_account_removal_completeness(
    dynamodb_setup, target_account_id, staging_accounts, removal_index
):
    """
    Property 2: Staging Account Removal Completeness

    For any target account with staging accounts, removing a specific staging
    account should result in that account no longer appearing in the staging
    accounts list while all other staging accounts remain unchanged.
    """
    # Ensure removal_index is within bounds
    if removal_index >= len(staging_accounts):
        removal_index = len(staging_accounts) - 1

    # Setup: Create target account
    table = dynamodb_setup
    table.put_item(
        Item={
            "accountId": target_account_id,
            "accountName": "Test Target Account",
            "roleArn": f"arn:aws:iam::{target_account_id}:role/TestRole",
            "externalId": f"test-external-id-{target_account_id}",
            "stagingAccounts": [],
        }
    )

    # Add all staging accounts
    for staging_account in staging_accounts:
        add_staging_account(
            target_account_id, staging_account, added_by="test"
        )

    # Get initial state
    initial_staging_accounts = get_staging_accounts(target_account_id)

    # Verify all staging accounts were added
    assert len(initial_staging_accounts) == len(staging_accounts)

    # Select staging account to remove
    staging_to_remove = staging_accounts[removal_index]
    staging_id_to_remove = staging_to_remove["accountId"]

    # Remove the staging account
    result = remove_staging_account(target_account_id, staging_id_to_remove)

    # Verify removal was successful
    assert result["success"] is True
    # Message contains either account ID or account name
    assert (
        staging_id_to_remove in result["message"]
        or staging_to_remove["accountName"] in result["message"]
    )

    # Get final state
    final_staging_accounts = get_staging_accounts(target_account_id)

    # Property Verification:
    # 1. Removed account should not appear in final list
    removed_account_ids = [
        acc.accountId for acc in final_staging_accounts
    ]
    assert (
        staging_id_to_remove not in removed_account_ids
    ), f"Removed staging account {staging_id_to_remove} still in list"

    # 2. All other staging accounts should remain unchanged
    expected_remaining_count = len(staging_accounts) - 1
    assert (
        len(final_staging_accounts) == expected_remaining_count
    ), f"Expected {expected_remaining_count} staging accounts, got {len(final_staging_accounts)}"

    # 3. Verify each remaining staging account is unchanged
    for staging_account in staging_accounts:
        if staging_account["accountId"] == staging_id_to_remove:
            continue

        # Find this staging account in final list
        final_account = next(
            (
                acc
                for acc in final_staging_accounts
                if acc.accountId == staging_account["accountId"]
            ),
            None,
        )

        assert (
            final_account is not None
        ), f"Staging account {staging_account['accountId']} was incorrectly removed"

        # Verify all fields remain unchanged
        assert (
            final_account.accountName == staging_account["accountName"]
        ), "Account name changed"
        assert (
            final_account.roleArn == staging_account["roleArn"]
        ), "Role ARN changed"
        assert (
            final_account.externalId == staging_account["externalId"]
        ), "External ID changed"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    target_account_id=account_id_strategy,
    staging_accounts=st.lists(
        staging_account_strategy, min_size=1, max_size=3, unique_by=lambda x: x["accountId"]
    ),
)
def test_property_remove_all_staging_accounts_sequentially(
    dynamodb_setup, target_account_id, staging_accounts
):
    """
    Property 2 Extension: Removing all staging accounts sequentially
    should result in an empty staging accounts list.
    """
    # Setup: Create target account
    table = dynamodb_setup
    table.put_item(
        Item={
            "accountId": target_account_id,
            "accountName": "Test Target Account",
            "roleArn": f"arn:aws:iam::{target_account_id}:role/TestRole",
            "externalId": f"test-external-id-{target_account_id}",
            "stagingAccounts": [],
        }
    )

    # Add all staging accounts
    for staging_account in staging_accounts:
        add_staging_account(
            target_account_id, staging_account, added_by="test"
        )

    # Remove all staging accounts one by one
    for staging_account in staging_accounts:
        staging_id = staging_account["accountId"]
        result = remove_staging_account(target_account_id, staging_id)
        assert result["success"] is True

    # Verify final state has no staging accounts
    final_staging_accounts = get_staging_accounts(target_account_id)

    assert (
        len(final_staging_accounts) == 0
    ), f"Expected empty staging accounts list, got {len(final_staging_accounts)}"


def test_remove_nonexistent_staging_account(dynamodb_setup):
    """
    Edge case: Removing a staging account that doesn't exist should fail
    """
    target_account_id = "123456789012"
    nonexistent_staging_id = "999999999999"

    # Setup: Create target account with no staging accounts
    table = dynamodb_setup
    table.put_item(
        Item={
            "accountId": target_account_id,
            "accountName": "Test Target Account",
            "roleArn": f"arn:aws:iam::{target_account_id}:role/TestRole",
            "externalId": f"test-external-id-{target_account_id}",
            "stagingAccounts": [],
        }
    )

    # Attempt to remove non-existent staging account
    with pytest.raises(ValueError, match="not found"):
        remove_staging_account(target_account_id, nonexistent_staging_id)


def test_remove_from_nonexistent_target_account(dynamodb_setup):
    """
    Edge case: Removing staging account from non-existent target account
    should fail
    """
    nonexistent_target_id = "123456789012"
    staging_id = "999999999999"

    # Attempt to remove from non-existent target account
    with pytest.raises(ValueError, match="not found"):
        remove_staging_account(nonexistent_target_id, staging_id)
