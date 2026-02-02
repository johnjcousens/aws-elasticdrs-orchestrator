"""
Property-Based Test: Account Breakdown Completeness

**Validates: Requirements 5.1, 5.2, 5.7**

Property 12: Account Breakdown Completeness
For any combined capacity query result, the account breakdown should include
all accounts (target + all staging accounts), and each account entry should
contain all required fields: account ID, account name, account type,
replicating servers, maximum capacity, percentage used, status, and regional
breakdown.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from hypothesis import given, settings, strategies as st

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent.parent / "lambda" / "query-handler"
sys.path.insert(0, str(lambda_dir))

from index import handle_get_combined_capacity


# Strategy for generating account configurations
def account_config_strategy():
    """Generate valid account configuration."""
    return st.fixed_dictionaries({
        "accountId": st.from_regex(r"\d{12}", fullmatch=True),
        "accountName": st.text(min_size=1, max_size=50),
        "roleArn": st.from_regex(
            r"arn:aws:iam::\d{12}:role/[\w+=,.@-]+",
            fullmatch=True
        ),
        "externalId": st.text(min_size=1, max_size=100),
    })


@settings(max_examples=100, deadline=1000)  # 1 second deadline for jobs metrics query
@given(
    num_staging_accounts=st.integers(min_value=0, max_value=10),
    target_servers=st.integers(min_value=0, max_value=300),
    staging_servers=st.lists(
        st.integers(min_value=0, max_value=300),
        min_size=0,
        max_size=10
    ),
)
def test_property_12_account_breakdown_completeness(
    num_staging_accounts, target_servers, staging_servers
):
    """
    Feature: staging-accounts-management
    Property 12: For any combined capacity query result, the account
    breakdown should include all accounts (target + all staging accounts),
    and each account entry should contain all required fields.

    **Validates: Requirements 5.1, 5.2, 5.7**
    """
    # Ensure staging_servers list matches num_staging_accounts
    staging_servers = staging_servers[:num_staging_accounts]
    while len(staging_servers) < num_staging_accounts:
        staging_servers.append(0)

    # Mock target account ID
    target_account_id = "111122223333"

    # Build target account configuration
    target_account = {
        "accountId": target_account_id,
        "accountName": "Target Account",
        "roleArn": f"arn:aws:iam::{target_account_id}:role/TestRole",
        "externalId": f"test-external-id-{target_account_id}",
        "stagingAccounts": []
    }

    # Build staging accounts
    for i in range(num_staging_accounts):
        staging_id = f"{444455556666 + i:012d}"
        target_account["stagingAccounts"].append({
            "accountId": staging_id,
            "accountName": f"Staging_{i+1}",
            "roleArn": f"arn:aws:iam::{staging_id}:role/TestRole",
            "externalId": f"test-external-id-{staging_id}",
        })

    # Mock DynamoDB table
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": target_account}

    # Mock query_all_accounts_parallel to return predictable results
    def mock_query_all_accounts(target, staging_list):
        results = []

        # Add target account result
        results.append({
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
        })

        # Add staging account results
        for i, staging in enumerate(staging_list):
            servers = staging_servers[i] if i < len(staging_servers) else 0
            results.append({
                "accountId": staging["accountId"],
                "accountName": staging.get("accountName", f"Staging_{i+1}"),
                "accountType": "staging",
                "replicatingServers": servers,
                "totalServers": servers,
                "regionalBreakdown": [
                    {
                        "region": "us-west-2",
                        "totalServers": servers,
                        "replicatingServers": servers,
                    }
                ],
                "accessible": True,
            })

        return results

    with patch(
        "index.target_accounts_table", mock_table
    ), patch(
        "index.query_all_accounts_parallel",
        side_effect=mock_query_all_accounts
    ):
        # Call handle_get_combined_capacity
        result = handle_get_combined_capacity(
            {"targetAccountId": target_account_id}
        )

        # Parse response
        assert result["statusCode"] == 200
        body = json.loads(result["body"])

        # Property: Account breakdown should include all accounts
        accounts = body.get("accounts", [])
        expected_account_count = 1 + num_staging_accounts  # target + staging

        assert len(accounts) == expected_account_count, (
            f"Expected {expected_account_count} accounts, "
            f"got {len(accounts)}"
        )

        # Property: Should have exactly one target account
        target_accounts = [
            a for a in accounts if a.get("accountType") == "target"
        ]
        assert len(target_accounts) == 1, (
            f"Expected 1 target account, got {len(target_accounts)}"
        )

        # Property: Should have correct number of staging accounts
        staging_accounts_result = [
            a for a in accounts if a.get("accountType") == "staging"
        ]
        assert len(staging_accounts_result) == num_staging_accounts, (
            f"Expected {num_staging_accounts} staging accounts, "
            f"got {len(staging_accounts_result)}"
        )

        # Property: Each account must have all required fields
        required_fields = [
            "accountId",
            "accountName",
            "accountType",
            "replicatingServers",
            "maxReplicating",
            "percentUsed",
            "status",
            "regionalBreakdown",
            "availableSlots",
            "warnings",
        ]

        for account in accounts:
            for field in required_fields:
                assert field in account, (
                    f"Account {account.get('accountId')} missing "
                    f"required field: {field}"
                )

            # Validate field types
            assert isinstance(account["accountId"], str)
            assert isinstance(account["accountName"], str)
            assert account["accountType"] in ["target", "staging"]
            assert isinstance(account["replicatingServers"], int)
            assert isinstance(account["maxReplicating"], int)
            assert isinstance(account["percentUsed"], (int, float))
            assert account["status"] in [
                "OK", "INFO", "WARNING", "CRITICAL", "HYPER-CRITICAL"
            ]
            assert isinstance(account["regionalBreakdown"], list)
            assert isinstance(account["availableSlots"], int)
            assert isinstance(account["warnings"], list)

            # Validate regional breakdown structure
            for region in account["regionalBreakdown"]:
                assert "region" in region
                assert "totalServers" in region
                assert "replicatingServers" in region
                assert isinstance(region["region"], str)
                assert isinstance(region["totalServers"], int)
                assert isinstance(region["replicatingServers"], int)

        # Property: maxReplicating should always be 300
        for account in accounts:
            assert account["maxReplicating"] == 300, (
                f"Account {account['accountId']} has maxReplicating="
                f"{account['maxReplicating']}, expected 300"
            )

        # Property: percentUsed should match calculation
        for account in accounts:
            expected_percent = round(
                (account["replicatingServers"] / 300 * 100), 2
            )
            assert account["percentUsed"] == expected_percent, (
                f"Account {account['accountId']} percentUsed="
                f"{account['percentUsed']}, expected {expected_percent}"
            )

        # Property: availableSlots should match calculation
        for account in accounts:
            expected_slots = 300 - account["replicatingServers"]
            assert account["availableSlots"] == expected_slots, (
                f"Account {account['accountId']} availableSlots="
                f"{account['availableSlots']}, expected {expected_slots}"
            )


if __name__ == "__main__":
    # Run a single test for debugging
    test_property_12_account_breakdown_completeness()
    print("✅ Property 12 test passed")
