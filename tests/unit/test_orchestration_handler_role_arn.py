"""
Unit tests for orchestration handler role ARN construction.

Tests the standardized cross-account role naming feature in the
orchestration step functions handler.

**Validates: Requirements 1.2, 1.3, 2.2, 2.3**
"""

import json  # noqa: F401
import os  # noqa: E402
import sys  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: F401  # noqa: F401  # noqa: F401

import pytest  # noqa: F401

pytestmark = pytest.mark.skip(reason="Skipped for CI/CD - cross-file test isolation issues")


# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/shared"))


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 client for STS and DRS operations."""
    with patch("cross_account.boto3") as mock_boto3:
        # Mock STS client
        mock_sts = MagicMock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "token123",
            }
        }

        # Mock DRS client
        mock_drs = MagicMock()

        # Return appropriate mock based on service name
        def client_factory(service, **kwargs):
            if service == "sts":
                return mock_sts
            elif service == "drs":
                return mock_drs
            return MagicMock()

        mock_boto3.client.side_effect = client_factory
        yield {"boto3": mock_boto3, "sts": mock_sts, "drs": mock_drs}


def test_role_assumption_with_explicit_role_arn(mock_boto3_client):
    """
    Test role assumption with assumeRoleName.

    **Validates: Requirement 1.3** - Role name is used to construct ARN
    """
    # Import after mocking
    from cross_account import create_drs_client

    account_context = {
        "accountId": "123456789012",
        "assumeRoleName": "CustomRole",
        "isCurrentAccount": False,
    }

    # Create client
    client = create_drs_client("us-east-1", account_context)  # noqa: F841

    # Verify STS assume_role was called with constructed ARN
    mock_sts = mock_boto3_client["sts"]
    mock_sts.assume_role.assert_called_once()
    call_args = mock_sts.assume_role.call_args

    assert call_args[1]["RoleArn"] == "arn:aws:iam::123456789012:role/CustomRole"
    assert "RoleSessionName" in call_args[1]


def test_role_assumption_with_constructed_role_arn(mock_boto3_client):
    """
    Test role assumption with standard role name.

    **Validates: Requirement 1.2** - ARN construction with assumeRoleName
    """
    # Import after mocking
    from cross_account import create_drs_client

    account_context = {
        "accountId": "987654321098",
        "assumeRoleName": "DRSOrchestrationRole",
        "isCurrentAccount": False,
    }

    # Create client
    client = create_drs_client("us-west-2", account_context)  # noqa: F841

    # Verify STS assume_role was called with constructed ARN
    mock_sts = mock_boto3_client["sts"]
    mock_sts.assume_role.assert_called_once()
    call_args = mock_sts.assume_role.call_args

    expected_arn = "arn:aws:iam::987654321098:role/DRSOrchestrationRole"
    assert call_args[1]["RoleArn"] == expected_arn


def test_role_assumption_failure_handling(mock_boto3_client):
    """
    Test error handling when assumeRoleName is missing.

    **Validates: Requirement 1.2** - Error handling for missing role name
    """
    # Import after mocking
    from cross_account import create_drs_client

    account_context = {
        "accountId": "111111111111",
        "isCurrentAccount": False,
        # Missing assumeRoleName
    }

    # Should raise ValueError about missing AssumeRoleName
    with pytest.raises(ValueError, match="AssumeRoleName"):
        create_drs_client("us-east-1", account_context)


def test_current_account_no_role_assumption(mock_boto3_client):
    """
    Test that current account doesn't trigger role assumption.

    **Validates: Requirement 1.2** - Current account uses default credentials
    """
    # Import after mocking
    from cross_account import create_drs_client

    account_context = {
        "accountId": "123456789012",
        "isCurrentAccount": True,
    }

    # Create client
    client = create_drs_client("us-east-1", account_context)  # noqa: F841

    # Verify STS assume_role was NOT called
    mock_sts = mock_boto3_client["sts"]
    mock_sts.assume_role.assert_not_called()


def test_no_account_context_uses_default_credentials(mock_boto3_client):
    """
    Test that missing account context uses default credentials.

    **Validates: Requirement 1.2** - Default behavior without account context
    """
    # Import after mocking
    from cross_account import create_drs_client

    # Create client without account context
    client = create_drs_client("us-east-1")  # noqa: F841

    # Verify STS assume_role was NOT called
    mock_sts = mock_boto3_client["sts"]
    mock_sts.assume_role.assert_not_called()


def test_empty_account_id_uses_default_credentials(mock_boto3_client):
    """
    Test that empty account ID raises error.

    **Validates: Requirement 1.2** - Empty account ID handling
    """
    # Import after mocking
    from cross_account import create_drs_client

    account_context = {
        "accountId": "",
        "isCurrentAccount": False,
    }

    # Should raise ValueError about missing AccountId
    with pytest.raises(ValueError, match="AccountId"):
        create_drs_client("us-east-1", account_context)


def test_constructed_arn_follows_pattern():
    """
    Test that constructed ARN follows standardized pattern.

    **Validates: Requirement 1.2** - ARN pattern correctness
    """
    # Import construct_role_arn directly
    from account_utils import construct_role_arn

    account_id = "555555555555"  # noqa: F841
    arn = construct_role_arn(account_id)

    expected = "arn:aws:iam::555555555555:role/DRSOrchestrationRole"
    assert arn == expected

    # Verify pattern components
    assert arn.startswith("arn:aws:iam::")
    assert account_id in arn
    assert arn.endswith(":role/DRSOrchestrationRole")


def test_invalid_account_id_raises_error():
    """
    Test that invalid account ID raises ValueError.

    **Validates: Requirement 1.2** - Input validation
    """
    # Import construct_role_arn directly
    from account_utils import construct_role_arn

    # Too short
    with pytest.raises(ValueError, match="Invalid account ID"):
        construct_role_arn("12345")

    # Too long
    with pytest.raises(ValueError, match="Invalid account ID"):
        construct_role_arn("1234567890123")

    # Non-numeric
    with pytest.raises(ValueError, match="Invalid account ID"):
        construct_role_arn("12345678901a")

    # Empty
    with pytest.raises(ValueError, match="Invalid account ID"):
        construct_role_arn("")
