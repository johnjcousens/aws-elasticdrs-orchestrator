"""
Unit Tests: handle_get_combined_capacity Operation

Tests the main combined capacity query operation with specific examples
and edge cases.

**Validates: Requirements 4.1, 9.5**
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from moto import mock_aws

# Set environment variables BEFORE importing index
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts-table"
os.environ["STAGING_ACCOUNTS_TABLE"] = "test-staging-accounts-table"

# Clear any existing index module to avoid conflicts
if "index" in sys.modules:
    del sys.modules["index"]

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent.parent / "lambda" / "query-handler"
sys.path.insert(0, str(lambda_dir))

from index import handle_get_combined_capacity


@mock_aws
def test_combined_capacity_no_staging_accounts():
    """
    Test query with no staging accounts (target account only).

    Validates:
    - Single account query works correctly
    - Combined metrics reflect single account
    - Recovery capacity calculated correctly
    """
    target_account_id = "111122223333"

    # Target account with NO staging accounts
    target_account = {
        "accountId": target_account_id,
        "accountName": "Target Account",
        "roleArn": f"arn:aws:iam::{target_account_id}:role/TestRole",
        "externalId": f"test-external-id-{target_account_id}",
        "stagingAccounts": [],  # Empty list
    }

    # Mock DynamoDB table
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": target_account}

    # Mock query_all_accounts_parallel
    def mock_query_all_accounts(target, staging_list):
        assert len(staging_list) == 0, "Should have no staging accounts"

        return [
            {
                "accountId": target["accountId"],
                "accountName": target.get("accountName"),
                "accountType": "target",
                "replicatingServers": 150,
                "totalServers": 150,
                "regionalBreakdown": [
                    {
                        "region": "us-east-1",
                        "totalServers": 150,
                        "replicatingServers": 150,
                    }
                ],
                "accessible": True,
            }
        ]

    with (
        patch("index.target_accounts_table", mock_table),
        patch(
            "index.query_all_accounts_parallel",
            side_effect=mock_query_all_accounts,
        ),
    ):
        result = handle_get_combined_capacity(
            {"targetAccountId": target_account_id}
        )

        assert result["statusCode"] == 200
        body = json.loads(result["body"])

        # Verify combined metrics
        assert body["combined"]["totalReplicating"] == 150
        assert body["combined"]["maxReplicating"] == 300  # 1 account × 300
        assert body["combined"]["percentUsed"] == 50.0
        assert body["combined"]["status"] == "OK"

        # Verify accounts list
        assert len(body["accounts"]) == 1
        assert body["accounts"][0]["accountType"] == "target"
        assert body["accounts"][0]["replicatingServers"] == 150

        # Verify recovery capacity (target account only)
        assert body["recoveryCapacity"]["currentServers"] == 150
        assert body["recoveryCapacity"]["maxRecoveryInstances"] == 4000
        assert body["recoveryCapacity"]["status"] == "OK"


@mock_aws
def test_combined_capacity_multiple_staging_accounts():
    """
    Test query with multiple staging accounts.

    Validates:
    - All accounts queried in parallel
    - Combined metrics aggregate correctly
    - Per-account status calculated correctly
    """
    target_account_id = "111122223333"

    # Target account with 3 staging accounts
    target_account = {
        "accountId": target_account_id,
        "accountName": "Target Account",
        "roleArn": f"arn:aws:iam::{target_account_id}:role/TestRole",
        "externalId": f"test-external-id-{target_account_id}",
        "stagingAccounts": [
            {
                "accountId": "444455556666",
                "accountName": "Staging_01",
                "roleArn": "arn:aws:iam::444455556666:role/TestRole",
                "externalId": "test-external-id-444455556666",
            },
            {
                "accountId": "777777777777",
                "accountName": "Staging_02",
                "roleArn": "arn:aws:iam::777777777777:role/TestRole",
                "externalId": "test-external-id-777777777777",
            },
            {
                "accountId": "888888888888",
                "accountName": "Staging_03",
                "roleArn": "arn:aws:iam::888888888888:role/TestRole",
                "externalId": "test-external-id-888888888888",
            },
        ],
    }

    # Mock DynamoDB table
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": target_account}

    # Mock query_all_accounts_parallel
    def mock_query_all_accounts(target, staging_list):
        assert len(staging_list) == 3, "Should have 3 staging accounts"

        # Staging account model: Total replicating across all accounts
        # should not exceed 300 (target account limit)
        return [
            {
                "accountId": target["accountId"],
                "accountName": "Target Account",
                "accountType": "target",
                "replicatingServers": 150,  # 50% of target capacity
                "totalServers": 150,
                "regionalBreakdown": [
                    {
                        "region": "us-east-1",
                        "totalServers": 150,
                        "replicatingServers": 150,
                    }
                ],
                "accessible": True,
            },
            {
                "accountId": "444455556666",
                "accountName": "Staging_01",
                "accountType": "staging",
                "replicatingServers": 75,  # OK
                "totalServers": 75,
                "regionalBreakdown": [
                    {
                        "region": "us-west-2",
                        "totalServers": 75,
                        "replicatingServers": 75,
                    }
                ],
                "accessible": True,
            },
            {
                "accountId": "777777777777",
                "accountName": "Staging_02",
                "accountType": "staging",
                "replicatingServers": 50,  # OK
                "totalServers": 50,
                "regionalBreakdown": [
                    {
                        "region": "eu-west-1",
                        "totalServers": 50,
                        "replicatingServers": 50,
                    }
                ],
                "accessible": True,
            },
            {
                "accountId": "888888888888",
                "accountName": "Staging_03",
                "accountType": "staging",
                "replicatingServers": 25,  # OK
                "totalServers": 25,
                "regionalBreakdown": [
                    {
                        "region": "ap-southeast-1",
                        "totalServers": 25,
                        "replicatingServers": 25,
                    }
                ],
                "accessible": True,
            },
        ]

    with (
        patch("index.target_accounts_table", mock_table),
        patch(
            "index.query_all_accounts_parallel",
            side_effect=mock_query_all_accounts,
        ),
    ):
        result = handle_get_combined_capacity(
            {"targetAccountId": target_account_id}
        )

        assert result["statusCode"] == 200
        body = json.loads(result["body"])

        # Verify combined metrics
        total_expected = 150 + 75 + 50 + 25  # 300
        assert body["combined"]["totalReplicating"] == total_expected
        # Multi-account model: 4 accounts × 300 = 1200 max capacity
        assert body["combined"]["maxReplicating"] == 1200

        # Verify accounts list
        assert len(body["accounts"]) == 4

        # Verify per-account status (each account evaluated against its own 300 limit)
        target_acct = next(
            a for a in body["accounts"] if a["accountType"] == "target"
        )
        assert target_acct["status"] == "OK"  # 150/300 = 50%
        assert target_acct["percentUsed"] == 50.0

        staging_01 = next(
            a for a in body["accounts"] if a["accountId"] == "444455556666"
        )
        assert staging_01["status"] == "OK"  # 75/300 = 25%

        staging_02 = next(
            a for a in body["accounts"] if a["accountId"] == "777777777777"
        )
        assert staging_02["status"] == "OK"  # 50/300 = 16.7%

        # Verify combined status (300/1200 = 25% = OK)
        assert body["combined"]["status"] == "OK"

        # Verify recovery capacity (target account only)
        assert body["recoveryCapacity"]["currentServers"] == 150


@mock_aws
def test_combined_capacity_one_staging_account_inaccessible():
    """
    Test query with one staging account inaccessible.

    Validates:
    - Query continues with remaining accessible accounts
    - Inaccessible account marked with error
    - Combined metrics exclude inaccessible account
    """
    target_account_id = "111122223333"

    # Target account with 2 staging accounts
    target_account = {
        "accountId": target_account_id,
        "accountName": "Target Account",
        "roleArn": f"arn:aws:iam::{target_account_id}:role/TestRole",
        "externalId": f"test-external-id-{target_account_id}",
        "stagingAccounts": [
            {
                "accountId": "444455556666",
                "accountName": "Staging_01",
                "roleArn": "arn:aws:iam::444455556666:role/TestRole",
                "externalId": "test-external-id-444455556666",
            },
            {
                "accountId": "777777777777",
                "accountName": "Staging_02",
                "roleArn": "arn:aws:iam::777777777777:role/TestRole",
                "externalId": "test-external-id-777777777777",
            },
        ],
    }

    # Mock DynamoDB table
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": target_account}

    # Mock query_all_accounts_parallel
    def mock_query_all_accounts(target, staging_list):
        return [
            {
                "accountId": target["accountId"],
                "accountName": "Target Account",
                "accountType": "target",
                "replicatingServers": 200,
                "totalServers": 200,
                "regionalBreakdown": [
                    {
                        "region": "us-east-1",
                        "totalServers": 200,
                        "replicatingServers": 200,
                    }
                ],
                "accessible": True,
            },
            {
                "accountId": "444455556666",
                "accountName": "Staging_01",
                "accountType": "staging",
                "replicatingServers": 150,
                "totalServers": 150,
                "regionalBreakdown": [
                    {
                        "region": "us-west-2",
                        "totalServers": 150,
                        "replicatingServers": 150,
                    }
                ],
                "accessible": True,
            },
            {
                # Staging_02 is INACCESSIBLE
                "accountId": "777777777777",
                "accountName": "Staging_02",
                "accountType": "staging",
                "replicatingServers": 0,
                "totalServers": 0,
                "regionalBreakdown": [],
                "accessible": False,
                "error": "Role assumption failed: Access Denied",
            },
        ]

    with (
        patch("index.target_accounts_table", mock_table),
        patch(
            "index.query_all_accounts_parallel",
            side_effect=mock_query_all_accounts,
        ),
    ):
        result = handle_get_combined_capacity(
            {"targetAccountId": target_account_id}
        )

        assert result["statusCode"] == 200
        body = json.loads(result["body"])

        # Verify combined metrics exclude inaccessible account
        # Only target (200) + Staging_01 (150) = 350
        assert body["combined"]["totalReplicating"] == 350
        # Only 2 accessible accounts × 300 = 600
        assert body["combined"]["maxReplicating"] == 600

        # Verify all 3 accounts in list
        assert len(body["accounts"]) == 3

        # Verify inaccessible account marked
        staging_02 = next(
            a for a in body["accounts"] if a["accountId"] == "777777777777"
        )
        assert staging_02["accessible"] is False
        assert "error" in staging_02


@mock_aws
def test_combined_capacity_all_staging_accounts_inaccessible():
    """
    Test query with all staging accounts inaccessible.

    Validates:
    - Query succeeds with target account only
    - Combined metrics reflect only target account
    - All staging accounts marked as inaccessible
    """
    target_account_id = "111122223333"

    # Target account with 2 staging accounts
    target_account = {
        "accountId": target_account_id,
        "accountName": "Target Account",
        "roleArn": f"arn:aws:iam::{target_account_id}:role/TestRole",
        "externalId": f"test-external-id-{target_account_id}",
        "stagingAccounts": [
            {
                "accountId": "444455556666",
                "accountName": "Staging_01",
                "roleArn": "arn:aws:iam::444455556666:role/TestRole",
                "externalId": "test-external-id-444455556666",
            },
            {
                "accountId": "777777777777",
                "accountName": "Staging_02",
                "roleArn": "arn:aws:iam::777777777777:role/TestRole",
                "externalId": "test-external-id-777777777777",
            },
        ],
    }

    # Mock DynamoDB table
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": target_account}

    # Mock query_all_accounts_parallel
    def mock_query_all_accounts(target, staging_list):
        return [
            {
                "accountId": target["accountId"],
                "accountName": "Target Account",
                "accountType": "target",
                "replicatingServers": 280,  # HYPER-CRITICAL
                "totalServers": 280,
                "regionalBreakdown": [
                    {
                        "region": "us-east-1",
                        "totalServers": 280,
                        "replicatingServers": 280,
                    }
                ],
                "accessible": True,
            },
            {
                # Staging_01 is INACCESSIBLE
                "accountId": "444455556666",
                "accountName": "Staging_01",
                "accountType": "staging",
                "replicatingServers": 0,
                "totalServers": 0,
                "regionalBreakdown": [],
                "accessible": False,
                "error": "Role assumption failed: Access Denied",
            },
            {
                # Staging_02 is INACCESSIBLE
                "accountId": "777777777777",
                "accountName": "Staging_02",
                "accountType": "staging",
                "replicatingServers": 0,
                "totalServers": 0,
                "regionalBreakdown": [],
                "accessible": False,
                "error": "Role assumption failed: Invalid credentials",
            },
        ]

    with (
        patch("index.target_accounts_table", mock_table),
        patch(
            "index.query_all_accounts_parallel",
            side_effect=mock_query_all_accounts,
        ),
    ):
        result = handle_get_combined_capacity(
            {"targetAccountId": target_account_id}
        )

        assert result["statusCode"] == 200
        body = json.loads(result["body"])

        # Verify combined metrics reflect only target account
        assert body["combined"]["totalReplicating"] == 280
        assert body["combined"]["maxReplicating"] == 300  # 1 accessible × 300

        # Verify all 3 accounts in list
        assert len(body["accounts"]) == 3

        # Verify target account accessible
        target_acct = next(
            a for a in body["accounts"] if a["accountType"] == "target"
        )
        assert target_acct["accessible"] is True
        assert target_acct["status"] == "HYPER-CRITICAL"  # 280 servers

        # Verify both staging accounts inaccessible
        staging_accounts = [
            a for a in body["accounts"] if a["accountType"] == "staging"
        ]
        assert len(staging_accounts) == 2
        for staging in staging_accounts:
            assert staging["accessible"] is False
            assert "error" in staging


@mock_aws
def test_combined_capacity_missing_target_account_id():
    """Test error handling when targetAccountId is missing."""
    result = handle_get_combined_capacity({})

    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert "error" in body
    assert "targetAccountId" in body["error"]


@mock_aws
def test_combined_capacity_invalid_account_id_format():
    """Test error handling when account ID format is invalid."""
    result = handle_get_combined_capacity({"targetAccountId": "invalid-id"})

    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert "error" in body
    assert "Invalid account ID format" in body["error"]


@mock_aws
def test_combined_capacity_target_account_not_found():
    """Test error handling when target account doesn't exist in DynamoDB."""
    target_account_id = "999999999999"

    # Mock DynamoDB table - account not found
    mock_table = MagicMock()
    mock_table.get_item.return_value = {}  # No Item

    with patch("index.target_accounts_table", mock_table):
        result = handle_get_combined_capacity(
            {"targetAccountId": target_account_id}
        )

        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert body["error"] == "TARGET_ACCOUNT_NOT_FOUND"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
