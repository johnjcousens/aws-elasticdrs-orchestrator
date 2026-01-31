"""
Unit Tests: handle_get_combined_capacity Operation

Tests the main combined capacity query operation with specific examples
and edge cases.

**Validates: Requirements 4.1, 9.5**
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent.parent / "lambda" / "query-handler"
sys.path.insert(0, str(lambda_dir))

from index import handle_get_combined_capacity


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
        "stagingAccounts": []  # Empty list
    }

    # Mock DynamoDB table
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": target_account}

    # Mock query_all_accounts_parallel
    def mock_query_all_accounts(target, staging_list):
        assert len(staging_list) == 0, "Should have no staging accounts"

        return [{
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
        }]

    with patch(
        "index.target_accounts_table", mock_table
    ), patch(
        "index.query_all_accounts_parallel",
        side_effect=mock_query_all_accounts
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
        ]
    }

    # Mock DynamoDB table
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": target_account}

    # Mock query_all_accounts_parallel
    def mock_query_all_accounts(target, staging_list):
        assert len(staging_list) == 3, "Should have 3 staging accounts"

        return [
            {
                "accountId": target["accountId"],
                "accountName": "Target Account",
                "accountType": "target",
                "replicatingServers": 225,  # WARNING threshold
                "totalServers": 225,
                "regionalBreakdown": [
                    {
                        "region": "us-east-1",
                        "totalServers": 225,
                        "replicatingServers": 225,
                    }
                ],
                "accessible": True,
            },
            {
                "accountId": "444455556666",
                "accountName": "Staging_01",
                "accountType": "staging",
                "replicatingServers": 100,  # OK
                "totalServers": 100,
                "regionalBreakdown": [
                    {
                        "region": "us-west-2",
                        "totalServers": 100,
                        "replicatingServers": 100,
                    }
                ],
                "accessible": True,
            },
            {
                "accountId": "777777777777",
                "accountName": "Staging_02",
                "accountType": "staging",
                "replicatingServers": 250,  # CRITICAL threshold
                "totalServers": 250,
                "regionalBreakdown": [
                    {
                        "region": "eu-west-1",
                        "totalServers": 250,
                        "replicatingServers": 250,
                    }
                ],
                "accessible": True,
            },
            {
                "accountId": "888888888888",
                "accountName": "Staging_03",
                "accountType": "staging",
                "replicatingServers": 50,  # OK
                "totalServers": 50,
                "regionalBreakdown": [
                    {
                        "region": "ap-southeast-1",
                        "totalServers": 50,
                        "replicatingServers": 50,
                    }
                ],
                "accessible": True,
            },
        ]

    with patch(
        "index.target_accounts_table", mock_table
    ), patch(
        "index.query_all_accounts_parallel",
        side_effect=mock_query_all_accounts
    ):
        result = handle_get_combined_capacity(
            {"targetAccountId": target_account_id}
        )

        assert result["statusCode"] == 200
        body = json.loads(result["body"])

        # Verify combined metrics
        total_expected = 225 + 100 + 250 + 50  # 625
        assert body["combined"]["totalReplicating"] == total_expected
        assert body["combined"]["maxReplicating"] == 1200  # 4 accounts × 300

        # Verify accounts list
        assert len(body["accounts"]) == 4

        # Verify per-account status
        target_acct = next(
            a for a in body["accounts"] if a["accountType"] == "target"
        )
        assert target_acct["status"] == "WARNING"  # 225 servers
        assert target_acct["percentUsed"] == 75.0

        staging_01 = next(
            a for a in body["accounts"] if a["accountId"] == "444455556666"
        )
        assert staging_01["status"] == "OK"  # 100 servers

        staging_02 = next(
            a for a in body["accounts"] if a["accountId"] == "777777777777"
        )
        assert staging_02["status"] == "CRITICAL"  # 250 servers

        # Verify warnings generated
        assert len(body["warnings"]) > 0
        warning_text = " ".join(body["warnings"])
        assert "WARNING" in warning_text or "CRITICAL" in warning_text

        # Verify recovery capacity (target account only)
        assert body["recoveryCapacity"]["currentServers"] == 225


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
        ]
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

    with patch(
        "index.target_accounts_table", mock_table
    ), patch(
        "index.query_all_accounts_parallel",
        side_effect=mock_query_all_accounts
    ):
        result = handle_get_combined_capacity(
            {"targetAccountId": target_account_id}
        )

        assert result["statusCode"] == 200
        body = json.loads(result["body"])

        # Verify combined metrics exclude inaccessible account
        # Only target (200) + Staging_01 (150) = 350
        assert body["combined"]["totalReplicating"] == 350
        # Only 2 accessible accounts
        assert body["combined"]["maxReplicating"] == 600  # 2 × 300

        # Verify all 3 accounts in list
        assert len(body["accounts"]) == 3

        # Verify inaccessible account marked
        staging_02 = next(
            a for a in body["accounts"] if a["accountId"] == "777777777777"
        )
        assert staging_02["accessible"] is False
        assert "error" in staging_02


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
        ]
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

    with patch(
        "index.target_accounts_table", mock_table
    ), patch(
        "index.query_all_accounts_parallel",
        side_effect=mock_query_all_accounts
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


def test_combined_capacity_missing_target_account_id():
    """Test error handling when targetAccountId is missing."""
    result = handle_get_combined_capacity({})

    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert "error" in body
    assert "targetAccountId" in body["error"]


def test_combined_capacity_invalid_account_id_format():
    """Test error handling when account ID format is invalid."""
    result = handle_get_combined_capacity(
        {"targetAccountId": "invalid-id"}
    )

    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert "error" in body
    assert "Invalid account ID format" in body["error"]


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
