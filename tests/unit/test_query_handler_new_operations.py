"""
Unit tests for new query-handler direct invocation operations.

Tests Phase 3 operations:
- get_staging_accounts (task 4.3)
- get_tag_sync_status (task 4.4)
- get_tag_sync_settings (task 4.5)
- get_drs_capacity_conflicts (task 4.6)

Feature: direct-lambda-invocation-mode
Requirements: 4.3, 4.4, 4.5, 4.6
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Set environment variables before importing handler
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"

# Clear any existing index module to avoid conflicts
if "index" in sys.modules:
    del sys.modules["index"]

# Add lambda paths for imports - query-handler FIRST
query_handler_dir = (
    Path(__file__).parent.parent.parent / "lambda" / "query-handler"
)
shared_dir = Path(__file__).parent.parent.parent / "lambda" / "shared"

sys.path.insert(0, str(query_handler_dir))
sys.path.insert(1, str(shared_dir))


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def lambda_context():
    """Mock Lambda context"""
    context = MagicMock()
    context.function_name = "query-handler"
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
    )
    return context


@pytest.fixture
def mock_target_accounts_table():
    """
    Mock target accounts DynamoDB table.
    
    IMPORTANT: This mocks the get_target_accounts_table() FUNCTION, not a module attribute.
    The Lambda handler uses lazy initialization via getter functions to avoid AWS API calls
    during module import. This pattern was changed from:
    
    OLD (incorrect): patch("index.target_accounts_table")
    NEW (correct):   patch("index.get_target_accounts_table")
    
    This fix resolved 21 AttributeError failures where tests tried to patch a non-existent
    module attribute.
    """
    with patch("index.get_target_accounts_table") as mock_func:
        mock_table = MagicMock()
        mock_func.return_value = mock_table
        yield mock_table


@pytest.fixture
def mock_get_drs_capacity():
    """Mock get_drs_account_capacity_all_regions function"""
    with patch("index.get_drs_account_capacity_all_regions") as mock_func:
        yield mock_func


# ============================================================================
# Test get_staging_accounts operation (task 4.3)
# ============================================================================


def test_get_staging_accounts_success(mock_target_accounts_table):
    """Test successful retrieval of staging accounts for a target account."""
    from index import get_staging_accounts_direct

    event = {"targetAccountId": "123456789012"}

    mock_target_account = {
        "accountId": "123456789012",
        "accountName": "Production Account",
        "stagingAccounts": [
            {
                "accountId": "987654321098",
                "accountName": "Staging Account 1",
                "roleArn": "arn:aws:iam::987654321098:role/DRSOrchestrationRole",
                "externalId": "unique-external-id-1",
                "replicatingServers": 25,
                "totalServers": 30,
                "status": "active",
            },
            {
                "accountId": "111222333444",
                "accountName": "Staging Account 2",
                "roleArn": "arn:aws:iam::111222333444:role/DRSOrchestrationRole",
                "externalId": "unique-external-id-2",
                "replicatingServers": 15,
                "totalServers": 20,
                "status": "active",
            },
        ],
    }

    mock_target_accounts_table.get_item.return_value = {"Item": mock_target_account}

    result = get_staging_accounts_direct(event)

    assert result["targetAccountId"] == "123456789012"
    assert len(result["stagingAccounts"]) == 2
    assert result["stagingAccounts"][0]["accountId"] == "987654321098"
    assert result["stagingAccounts"][1]["accountId"] == "111222333444"


def test_get_staging_accounts_missing_parameter():
    """Test error when targetAccountId parameter is missing."""
    from index import get_staging_accounts_direct

    event = {}

    result = get_staging_accounts_direct(event)

    assert result["error"] == "MISSING_PARAMETER"
    assert "targetAccountId is required" in result["message"]


def test_get_staging_accounts_invalid_account_id():
    """Test error when targetAccountId format is invalid."""
    from index import get_staging_accounts_direct

    event = {"targetAccountId": "invalid"}

    result = get_staging_accounts_direct(event)

    assert result["error"] == "INVALID_PARAMETER"
    assert "Invalid account ID format" in result["message"]


def test_get_staging_accounts_account_not_found(mock_target_accounts_table):
    """Test error when target account does not exist."""
    from index import get_staging_accounts_direct

    event = {"targetAccountId": "123456789012"}

    mock_target_accounts_table.get_item.return_value = {}

    result = get_staging_accounts_direct(event)

    assert result["error"] == "NOT_FOUND"
    assert "not found" in result["message"]


def test_get_staging_accounts_empty_list(mock_target_accounts_table):
    """Test successful response when target account has no staging accounts."""
    from index import get_staging_accounts_direct

    event = {"targetAccountId": "123456789012"}

    mock_target_account = {
        "accountId": "123456789012",
        "accountName": "Production Account",
        "stagingAccounts": [],
    }

    mock_target_accounts_table.get_item.return_value = {"Item": mock_target_account}

    result = get_staging_accounts_direct(event)

    assert result["targetAccountId"] == "123456789012"
    assert result["stagingAccounts"] == []


# ============================================================================
# Test get_tag_sync_status operation (task 4.4)
# ============================================================================


def test_get_tag_sync_status_not_implemented():
    """Test tag sync status returns not implemented placeholder."""
    from index import get_tag_sync_status_direct

    event = {}

    result = get_tag_sync_status_direct(event)

    assert result["enabled"] is False
    assert result["lastSyncTime"] is None
    assert result["serversProcessed"] == 0
    assert result["tagsSynchronized"] == 0
    assert result["status"] == "not_implemented"
    assert "not yet implemented" in result["note"]


def test_get_tag_sync_status_no_parameters_required():
    """Test tag sync status works without any parameters."""
    from index import get_tag_sync_status_direct

    event = {}

    result = get_tag_sync_status_direct(event)

    # Should not return error
    assert "error" not in result
    assert "status" in result


# ============================================================================
# Test get_tag_sync_settings operation (task 4.5)
# ============================================================================


def test_get_tag_sync_settings_not_implemented():
    """Test tag sync settings returns not implemented placeholder."""
    from index import get_tag_sync_settings_direct

    event = {}

    result = get_tag_sync_settings_direct(event)

    assert result["enabled"] is False
    assert result["schedule"] is None
    assert "tagFilters" in result
    assert result["tagFilters"]["include"] == []
    assert result["tagFilters"]["exclude"] == []
    assert result["sourceAccounts"] == []
    assert result["targetAccounts"] == []
    assert "not yet implemented" in result["note"]


def test_get_tag_sync_settings_no_parameters_required():
    """Test tag sync settings works without any parameters."""
    from index import get_tag_sync_settings_direct

    event = {}

    result = get_tag_sync_settings_direct(event)

    # Should not return error
    assert "error" not in result
    assert "tagFilters" in result


# ============================================================================
# Test get_drs_capacity_conflicts operation (task 4.6)
# ============================================================================


def test_get_drs_capacity_conflicts_no_conflicts(
    mock_target_accounts_table, mock_get_drs_capacity
):
    """Test capacity conflicts when all accounts are within limits."""
    from index import get_drs_capacity_conflicts_direct

    event = {}

    mock_accounts = [
        {
            "accountId": "123456789012",
            "accountName": "Production Account",
            "roleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationRole",
            "externalId": "external-id-1",
        }
    ]

    mock_capacity = {
        "totalReplicatingServers": 50,  # Well below 300 limit
        "totalServers": 100,  # Well below 4000 limit
    }

    mock_target_accounts_table.scan.return_value = {"Items": mock_accounts}
    mock_get_drs_capacity.return_value = mock_capacity

    result = get_drs_capacity_conflicts_direct(event)

    assert result["totalConflicts"] == 0
    assert result["conflicts"] == []
    assert "timestamp" in result


def test_get_drs_capacity_conflicts_warning_replication(
    mock_target_accounts_table, mock_get_drs_capacity
):
    """Test capacity conflicts when account approaches replication limit (>80%)."""
    from index import get_drs_capacity_conflicts_direct

    event = {}

    mock_accounts = [
        {
            "accountId": "123456789012",
            "accountName": "Production Account",
            "roleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationRole",
            "externalId": "external-id-1",
        }
    ]

    mock_capacity = {
        "totalReplicatingServers": 250,  # 83% of 300 limit
        "totalServers": 300,
    }

    mock_target_accounts_table.scan.return_value = {"Items": mock_accounts}
    mock_get_drs_capacity.return_value = mock_capacity

    result = get_drs_capacity_conflicts_direct(event)

    assert result["totalConflicts"] == 1
    assert result["conflicts"][0]["conflictType"] == "approaching_replication_limit"
    assert result["conflicts"][0]["severity"] == "warning"
    assert result["conflicts"][0]["currentUsage"] == 250
    assert result["conflicts"][0]["limit"] == 300


def test_get_drs_capacity_conflicts_critical_replication(
    mock_target_accounts_table, mock_get_drs_capacity
):
    """Test capacity conflicts when account critically close to replication limit (>90%)."""
    from index import get_drs_capacity_conflicts_direct

    event = {}

    mock_accounts = [
        {
            "accountId": "123456789012",
            "accountName": "Production Account",
            "roleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationRole",
            "externalId": "external-id-1",
        }
    ]

    mock_capacity = {
        "totalReplicatingServers": 280,  # 93% of 300 limit
        "totalServers": 350,
    }

    mock_target_accounts_table.scan.return_value = {"Items": mock_accounts}
    mock_get_drs_capacity.return_value = mock_capacity

    result = get_drs_capacity_conflicts_direct(event)

    assert result["totalConflicts"] == 1
    assert result["conflicts"][0]["conflictType"] == "critical_replication_limit"
    assert result["conflicts"][0]["severity"] == "critical"
    assert result["conflicts"][0]["currentUsage"] == 280
    assert result["conflicts"][0]["limit"] == 300


def test_get_drs_capacity_conflicts_warning_recovery(
    mock_target_accounts_table, mock_get_drs_capacity
):
    """Test capacity conflicts when account approaches recovery limit (>80%)."""
    from index import get_drs_capacity_conflicts_direct

    event = {}

    mock_accounts = [
        {
            "accountId": "123456789012",
            "accountName": "Production Account",
            "roleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationRole",
            "externalId": "external-id-1",
        }
    ]

    mock_capacity = {
        "totalReplicatingServers": 100,
        "totalServers": 3300,  # 82.5% of 4000 limit
    }

    mock_target_accounts_table.scan.return_value = {"Items": mock_accounts}
    mock_get_drs_capacity.return_value = mock_capacity

    result = get_drs_capacity_conflicts_direct(event)

    assert result["totalConflicts"] == 1
    assert result["conflicts"][0]["conflictType"] == "approaching_recovery_limit"
    assert result["conflicts"][0]["severity"] == "warning"
    assert result["conflicts"][0]["currentUsage"] == 3300
    assert result["conflicts"][0]["limit"] == 4000


def test_get_drs_capacity_conflicts_multiple_accounts(
    mock_target_accounts_table, mock_get_drs_capacity
):
    """Test capacity conflicts across multiple accounts."""
    from index import get_drs_capacity_conflicts_direct

    event = {}

    mock_accounts = [
        {
            "accountId": "123456789012",
            "accountName": "Production Account",
            "roleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationRole",
            "externalId": "external-id-1",
        },
        {
            "accountId": "987654321098",
            "accountName": "Staging Account",
            "roleArn": "arn:aws:iam::987654321098:role/DRSOrchestrationRole",
            "externalId": "external-id-2",
        },
    ]

    def mock_capacity_side_effect(account_context):
        account_id = account_context.get("accountId")
        if account_id == "123456789012":
            return {"totalReplicatingServers": 280, "totalServers": 350}  # Critical
        else:
            return {"totalReplicatingServers": 250, "totalServers": 300}  # Warning

    mock_target_accounts_table.scan.return_value = {"Items": mock_accounts}
    mock_get_drs_capacity.side_effect = mock_capacity_side_effect

    result = get_drs_capacity_conflicts_direct(event)

    assert result["totalConflicts"] == 2
    # Critical conflicts should be sorted first
    assert result["conflicts"][0]["severity"] == "critical"
    assert result["conflicts"][1]["severity"] == "warning"


def test_get_drs_capacity_conflicts_no_parameters_required(
    mock_target_accounts_table
):
    """Test capacity conflicts works without any parameters."""
    from index import get_drs_capacity_conflicts_direct

    event = {}

    mock_target_accounts_table.scan.return_value = {"Items": []}

    result = get_drs_capacity_conflicts_direct(event)

    # Should not return error
    assert "error" not in result
    assert "conflicts" in result
    assert result["totalConflicts"] == 0


# ============================================================================
# Test handle_direct_invocation routing (task 4.7)
# ============================================================================


@patch("shared.iam_utils.validate_iam_authorization")
def test_handle_direct_invocation_get_staging_accounts(
    mock_validate, mock_target_accounts_table, lambda_context
):
    """Test direct invocation routing for get_staging_accounts operation."""
    from index import handle_direct_invocation

    mock_validate.return_value = True

    event = {
        "operation": "get_staging_accounts",
        "targetAccountId": "123456789012",
    }

    mock_target_account = {
        "accountId": "123456789012",
        "stagingAccounts": [],
    }

    mock_target_accounts_table.get_item.return_value = {"Item": mock_target_account}

    result = handle_direct_invocation(event, lambda_context)

    assert result["targetAccountId"] == "123456789012"
    assert "stagingAccounts" in result


@patch("shared.iam_utils.validate_iam_authorization")
def test_handle_direct_invocation_get_tag_sync_status(mock_validate, lambda_context):
    """Test direct invocation routing for get_tag_sync_status operation."""
    from index import handle_direct_invocation

    mock_validate.return_value = True

    event = {"operation": "get_tag_sync_status"}

    result = handle_direct_invocation(event, lambda_context)

    assert "status" in result
    assert result["status"] == "not_implemented"


@patch("shared.iam_utils.validate_iam_authorization")
def test_handle_direct_invocation_get_tag_sync_settings(mock_validate, lambda_context):
    """Test direct invocation routing for get_tag_sync_settings operation."""
    from index import handle_direct_invocation

    mock_validate.return_value = True

    event = {"operation": "get_tag_sync_settings"}

    result = handle_direct_invocation(event, lambda_context)

    assert "tagFilters" in result
    assert "enabled" in result


@patch("shared.iam_utils.validate_iam_authorization")
def test_handle_direct_invocation_get_drs_capacity_conflicts(
    mock_validate, mock_target_accounts_table, lambda_context
):
    """Test direct invocation routing for get_drs_capacity_conflicts operation."""
    from index import handle_direct_invocation

    mock_validate.return_value = True

    event = {"operation": "get_drs_capacity_conflicts"}

    mock_target_accounts_table.scan.return_value = {"Items": []}

    result = handle_direct_invocation(event, lambda_context)

    assert "conflicts" in result
    assert "totalConflicts" in result
