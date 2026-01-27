"""
Unit tests for cross_account shared utilities.

Tests cross-account IAM role assumption and DRS client creation.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add lambda directory to path for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "lambda"
    ),
)

# Set environment variables before importing module
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"

from shared.cross_account import (
    create_drs_client,
    determine_target_account_context,
    get_current_account_id,
)


@pytest.fixture
def mock_dynamodb_tables():
    """Mock DynamoDB tables using lazy initialization functions"""
    mock_pg = MagicMock()
    mock_ta = MagicMock()
    
    with patch("shared.cross_account._get_protection_groups_table", return_value=mock_pg), \
         patch("shared.cross_account._get_target_accounts_table", return_value=mock_ta):
        yield {
            "protection_groups": mock_pg,
            "target_accounts": mock_ta,
        }


@pytest.fixture
def sample_recovery_plan():
    """Sample Recovery Plan"""
    return {
        "planId": "plan-123",
        "planName": "Test Plan",
        "waves": [
            {
                "waveName": "Wave 1",
                "protectionGroupId": "pg-123",
            }
        ],
    }


@pytest.fixture
def sample_protection_group_current_account():
    """Sample Protection Group in current account"""
    return {
        "groupId": "pg-123",
        "groupName": "Test PG",
        "region": "us-east-1",
        "sourceServerIds": ["s-111", "s-222"],
        # No accountId means current account
    }


@pytest.fixture
def sample_protection_group_cross_account():
    """Sample Protection Group in cross account"""
    return {
        "groupId": "pg-123",
        "groupName": "Test PG",
        "region": "us-east-1",
        "sourceServerIds": ["s-111", "s-222"],
        "accountId": "999888777666",
        "assumeRoleName": "DRSOrchestrationCrossAccountRole",
    }


@patch("boto3.client")
def test_get_current_account_id_success(mock_boto_client):
    """Test get_current_account_id returns account ID"""
    mock_sts = MagicMock()
    mock_boto_client.return_value = mock_sts
    mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}

    account_id = get_current_account_id()

    assert account_id == "123456789012"
    mock_sts.get_caller_identity.assert_called_once()


@patch("boto3.client")
def test_get_current_account_id_error(mock_boto_client):
    """Test get_current_account_id handles errors"""
    mock_sts = MagicMock()
    mock_boto_client.return_value = mock_sts
    mock_sts.get_caller_identity.side_effect = Exception("STS error")

    account_id = get_current_account_id()

    assert account_id == "unknown"


@patch("shared.cross_account.get_current_account_id")
def test_determine_target_account_context_current_account(
    mock_get_account,
    mock_dynamodb_tables,
    sample_recovery_plan,
    sample_protection_group_current_account,
):
    """Test determine_target_account_context for current account"""
    mock_get_account.return_value = "123456789012"
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": sample_protection_group_current_account
    }

    context = determine_target_account_context(sample_recovery_plan)

    assert context["accountId"] == "123456789012"
    assert context["assumeRoleName"] is None
    assert context["isCurrentAccount"] is True


@patch("shared.cross_account.get_current_account_id")
def test_determine_target_account_context_cross_account(
    mock_get_account,
    mock_dynamodb_tables,
    sample_recovery_plan,
    sample_protection_group_cross_account,
):
    """Test determine_target_account_context for cross account"""
    mock_get_account.return_value = "123456789012"
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": sample_protection_group_cross_account
    }
    mock_dynamodb_tables["target_accounts"].get_item.return_value = {
        "Item": {
            "accountId": "999888777666",
            "assumeRoleName": "DRSOrchestrationCrossAccountRole",
        }
    }

    context = determine_target_account_context(sample_recovery_plan)

    assert context["accountId"] == "999888777666"
    assert context["assumeRoleName"] == "DRSOrchestrationCrossAccountRole"
    assert context["isCurrentAccount"] is False


@patch("shared.cross_account.get_current_account_id")
def test_determine_target_account_context_mixed_accounts_error(
    mock_get_account, mock_dynamodb_tables, sample_recovery_plan
):
    """Test determine_target_account_context raises error for mixed accounts"""
    mock_get_account.return_value = "123456789012"

    # Mock two PGs with different account IDs
    def get_item_side_effect(*args, **kwargs):
        pg_id = kwargs["Key"]["groupId"]
        if pg_id == "pg-123":
            return {
                "Item": {
                    "groupId": "pg-123",
                    "accountId": "999888777666",
                }
            }
        else:
            return {
                "Item": {
                    "groupId": "pg-456",
                    "accountId": "111222333444",
                }
            }

    mock_dynamodb_tables["protection_groups"].get_item.side_effect = (
        get_item_side_effect
    )

    # Add second wave with different account
    sample_recovery_plan["waves"].append(
        {"waveName": "Wave 2", "protectionGroupId": "pg-456"}
    )

    with pytest.raises(ValueError) as exc_info:
        determine_target_account_context(sample_recovery_plan)

    assert "multiple accounts" in str(exc_info.value).lower()


@patch("boto3.client")
def test_create_drs_client_current_account(mock_boto_client):
    """Test create_drs_client for current account"""
    mock_drs = MagicMock()
    mock_boto_client.return_value = mock_drs

    client = create_drs_client("us-east-1")

    assert client == mock_drs
    mock_boto_client.assert_called_once_with("drs", region_name="us-east-1")


@patch("boto3.client")
def test_create_drs_client_current_account_explicit(mock_boto_client):
    """Test create_drs_client with explicit current account context"""
    mock_drs = MagicMock()
    mock_boto_client.return_value = mock_drs

    account_context = {
        "accountId": "123456789012",
        "assumeRoleName": None,
        "isCurrentAccount": True,
    }

    client = create_drs_client("us-east-1", account_context)

    assert client == mock_drs
    mock_boto_client.assert_called_once_with("drs", region_name="us-east-1")


@patch("boto3.client")
def test_create_drs_client_cross_account_success(mock_boto_client):
    """Test create_drs_client for cross account"""
    mock_sts = MagicMock()
    mock_drs = MagicMock()

    def client_side_effect(service, **kwargs):
        if service == "sts":
            return mock_sts
        elif service == "drs":
            return mock_drs
        return MagicMock()

    mock_boto_client.side_effect = client_side_effect

    # Mock STS assume_role
    mock_sts.assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "AKIATEST",
            "SecretAccessKey": "secret",
            "SessionToken": "token",
        }
    }

    account_context = {
        "accountId": "999888777666",
        "assumeRoleName": "DRSOrchestrationCrossAccountRole",
        "isCurrentAccount": False,
    }

    client = create_drs_client("us-east-1", account_context)

    assert client == mock_drs
    mock_sts.assume_role.assert_called_once()
    call_args = mock_sts.assume_role.call_args
    assert "arn:aws:iam::999888777666:role/DRSOrchestrationCrossAccountRole" in str(
        call_args
    )


@patch("boto3.client")
def test_create_drs_client_cross_account_missing_account_id(mock_boto_client):
    """Test create_drs_client raises error for missing account ID"""
    account_context = {
        "assumeRoleName": "DRSOrchestrationCrossAccountRole",
        "isCurrentAccount": False,
    }

    with pytest.raises(ValueError) as exc_info:
        create_drs_client("us-east-1", account_context)

    assert "AccountId" in str(exc_info.value)


@patch("boto3.client")
def test_create_drs_client_cross_account_missing_role_name(mock_boto_client):
    """Test create_drs_client raises error for missing role name"""
    account_context = {
        "accountId": "999888777666",
        "isCurrentAccount": False,
    }

    with pytest.raises(ValueError) as exc_info:
        create_drs_client("us-east-1", account_context)

    assert "AssumeRoleName" in str(exc_info.value)


@patch("boto3.client")
def test_create_drs_client_cross_account_access_denied(mock_boto_client):
    """Test create_drs_client handles AccessDenied error"""
    mock_sts = MagicMock()

    def client_side_effect(service, **kwargs):
        if service == "sts":
            return mock_sts
        return MagicMock()

    mock_boto_client.side_effect = client_side_effect

    # Mock STS assume_role to raise AccessDenied
    mock_sts.assume_role.side_effect = Exception("AccessDenied")

    account_context = {
        "accountId": "999888777666",
        "assumeRoleName": "DRSOrchestrationCrossAccountRole",
        "isCurrentAccount": False,
    }

    with pytest.raises(RuntimeError) as exc_info:
        create_drs_client("us-east-1", account_context)

    error_msg = str(exc_info.value)
    assert "AccessDenied" in error_msg or "Failed to assume" in error_msg
    assert "999888777666" in error_msg
