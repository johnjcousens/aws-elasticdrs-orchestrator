"""
Unit tests for lambda/shared/cross_account.py module.

Tests the three core cross-account functions:
1. get_cross_account_session() - STS AssumeRole for cross-account access
2. create_drs_client() - DRS client with optional cross-account assumption
3. create_ec2_client() - EC2 client with optional cross-account assumption

Feature: query-handler-read-only-audit
Task: 1.2 Verify cross_account.py functions work correctly
"""

import os
import sys
from unittest.mock import Mock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError

# Add lambda directories to path
lambda_base = os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
sys.path.insert(0, os.path.join(lambda_base, "shared"))

# Import after path setup
from cross_account import (
    create_drs_client,
    create_ec2_client,
    get_cross_account_session,
    get_current_account_id,
)


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing"""
    os.environ["AWS_ACCOUNT_ID"] = "111111111111"
    os.environ["AWS_REGION"] = "us-east-1"
    yield
    # Cleanup
    for key in ["AWS_ACCOUNT_ID", "AWS_REGION"]:
        if key in os.environ:
            del os.environ[key]


# ============================================================================
# Test: get_cross_account_session()
# ============================================================================


class TestGetCrossAccountSession:
    """Test suite for get_cross_account_session() function"""

    @patch("cross_account.boto3.client")
    def test_successful_role_assumption_without_external_id(
        self, mock_boto_client, mock_env_vars
    ):
        """
        Test successful cross-account role assumption without external ID.

        Validates:
        - STS AssumeRole is called with correct role ARN
        - Session name is generated
        - boto3.Session is created with temporary credentials
        - No external ID is used
        """
        # Mock STS client
        mock_sts = Mock()
        mock_boto_client.return_value = mock_sts

        # Mock successful assume role response
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": "2026-01-31T12:00:00Z",
            }
        }

        role_arn = "arn:aws:iam::222222222222:role/DRSOrchestrationRole"

        # Execute
        session = get_cross_account_session(role_arn)

        # Verify STS assume role was called
        mock_sts.assume_role.assert_called_once()
        call_args = mock_sts.assume_role.call_args[1]

        # Verify role ARN
        assert call_args["RoleArn"] == role_arn

        # Verify session name is generated
        assert "RoleSessionName" in call_args
        assert call_args["RoleSessionName"].startswith("drs-orchestration-")

        # Verify no external ID
        assert "ExternalId" not in call_args

        # Verify session was created
        assert session is not None

    @patch("cross_account.boto3.client")
    def test_successful_role_assumption_with_external_id(
        self, mock_boto_client, mock_env_vars
    ):
        """
        Test successful cross-account role assumption with external ID.

        Validates:
        - STS AssumeRole is called with external ID
        - External ID is properly passed
        - Session is created successfully
        """
        # Mock STS client
        mock_sts = Mock()
        mock_boto_client.return_value = mock_sts

        # Mock successful assume role response
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
            }
        }

        role_arn = "arn:aws:iam::222222222222:role/DRSOrchestrationRole"
        external_id = "unique-external-id-123"

        # Execute
        session = get_cross_account_session(role_arn, external_id)

        # Verify STS assume role was called with external ID
        mock_sts.assume_role.assert_called_once()
        call_args = mock_sts.assume_role.call_args[1]

        assert call_args["RoleArn"] == role_arn
        assert call_args["ExternalId"] == external_id

        # Verify session was created
        assert session is not None

    @patch("cross_account.boto3.client")
    def test_role_assumption_access_denied(self, mock_boto_client, mock_env_vars):
        """
        Test role assumption failure due to AccessDenied.

        Validates:
        - AccessDenied error is caught
        - Exception is raised with error details
        """
        # Mock STS client
        mock_sts = Mock()
        mock_boto_client.return_value = mock_sts

        # Mock AccessDenied error
        mock_sts.assume_role.side_effect = ClientError(
            {
                "Error": {
                    "Code": "AccessDenied",
                    "Message": "User is not authorized to perform: sts:AssumeRole",
                }
            },
            "AssumeRole",
        )

        role_arn = "arn:aws:iam::222222222222:role/DRSOrchestrationRole"

        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            get_cross_account_session(role_arn)

        # Verify error message contains key information
        error_msg = str(exc_info.value)
        assert "AccessDenied" in error_msg or "not authorized" in error_msg

    @patch("cross_account.boto3.client")
    def test_role_assumption_invalid_role(self, mock_boto_client, mock_env_vars):
        """
        Test role assumption failure when role doesn't exist.

        Validates:
        - InvalidUserID.NotFound error is caught
        - Exception is raised
        """
        # Mock STS client
        mock_sts = Mock()
        mock_boto_client.return_value = mock_sts

        # Mock InvalidUserID error
        mock_sts.assume_role.side_effect = ClientError(
            {
                "Error": {
                    "Code": "InvalidUserID.NotFound",
                    "Message": "The user with name DRSOrchestrationRole cannot be found.",
                }
            },
            "AssumeRole",
        )

        role_arn = "arn:aws:iam::222222222222:role/NonExistentRole"

        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            get_cross_account_session(role_arn)

        error_msg = str(exc_info.value)
        assert "InvalidUserID" in error_msg or "cannot be found" in error_msg


# ============================================================================
# Test: create_drs_client()
# ============================================================================


class TestCreateDrsClient:
    """Test suite for create_drs_client() function"""

    @patch("cross_account.boto3.client")
    @patch("cross_account.get_current_account_id")
    def test_create_drs_client_current_account_no_context(
        self, mock_get_account_id, mock_boto_client, mock_env_vars
    ):
        """
        Test DRS client creation for current account without account context.

        Validates:
        - No role assumption occurs
        - Standard boto3 client is created
        - Correct region is used
        """
        mock_get_account_id.return_value = "111111111111"

        # Mock DRS client
        mock_drs_client = Mock()
        mock_boto_client.return_value = mock_drs_client

        # Execute without account context
        client = create_drs_client("us-east-1")

        # Verify standard boto3 client was created
        mock_boto_client.assert_called_once_with("drs", region_name="us-east-1")
        assert client == mock_drs_client

    @patch("cross_account.boto3.client")
    @patch("cross_account.get_current_account_id")
    def test_create_drs_client_current_account_with_context(
        self, mock_get_account_id, mock_boto_client, mock_env_vars
    ):
        """
        Test DRS client creation for current account with isCurrentAccount=True.

        Validates:
        - No role assumption occurs
        - Standard boto3 client is created
        """
        mock_get_account_id.return_value = "111111111111"

        # Mock DRS client
        mock_drs_client = Mock()
        mock_boto_client.return_value = mock_drs_client

        # Account context for current account
        account_context = {
            "accountId": "111111111111",
            "assumeRoleName": None,
            "isCurrentAccount": True,
        }

        # Execute
        client = create_drs_client("us-east-1", account_context)

        # Verify standard boto3 client was created
        mock_boto_client.assert_called_once_with("drs", region_name="us-east-1")
        assert client == mock_drs_client

    @patch("cross_account.get_cross_account_session")
    @patch("cross_account.get_current_account_id")
    def test_create_drs_client_cross_account_without_external_id(
        self, mock_get_account_id, mock_get_session, mock_env_vars
    ):
        """
        Test DRS client creation for cross-account without external ID.

        Validates:
        - Cross-account session is created
        - DRS client is created with assumed role credentials
        - Correct region is used
        - No external ID is passed
        """
        mock_get_account_id.return_value = "111111111111"

        # Mock cross-account session
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        # Mock DRS client
        mock_drs_client = Mock()
        mock_session.client.return_value = mock_drs_client

        # Account context for cross-account
        account_context = {
            "accountId": "222222222222",
            "assumeRoleName": "DRSOrchestrationRole",
            "isCurrentAccount": False,
        }

        # Execute
        client = create_drs_client("us-east-1", account_context)

        # Verify cross-account session was created
        mock_get_session.assert_called_once()
        call_args = mock_get_session.call_args[1]

        # Verify role ARN
        assert call_args["role_arn"] == "arn:aws:iam::222222222222:role/DRSOrchestrationRole"

        # Verify no external ID
        assert call_args["external_id"] is None

        # Verify DRS client was created with correct region
        mock_session.client.assert_called_once_with("drs", region_name="us-east-1")
        assert client == mock_drs_client

    @patch("cross_account.get_cross_account_session")
    @patch("cross_account.get_current_account_id")
    def test_create_drs_client_cross_account_with_external_id(
        self, mock_get_account_id, mock_get_session, mock_env_vars
    ):
        """
        Test DRS client creation for cross-account with external ID.

        Validates:
        - Cross-account session is created with external ID
        - External ID is properly passed
        - DRS client is created successfully
        """
        mock_get_account_id.return_value = "111111111111"

        # Mock cross-account session
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        # Mock DRS client
        mock_drs_client = Mock()
        mock_session.client.return_value = mock_drs_client

        # Account context with external ID
        account_context = {
            "accountId": "222222222222",
            "assumeRoleName": "DRSOrchestrationRole",
            "externalId": "external-id-123",
            "isCurrentAccount": False,
        }

        # Execute
        client = create_drs_client("us-east-1", account_context)

        # Verify cross-account session was created with external ID
        mock_get_session.assert_called_once()
        call_args = mock_get_session.call_args[1]

        assert call_args["role_arn"] == "arn:aws:iam::222222222222:role/DRSOrchestrationRole"
        assert call_args["external_id"] == "external-id-123"

        # Verify DRS client was created
        assert client == mock_drs_client

    @patch("cross_account.get_current_account_id")
    def test_create_drs_client_missing_account_id(
        self, mock_get_account_id, mock_env_vars
    ):
        """
        Test DRS client creation fails when account ID is missing.

        Validates:
        - ValueError is raised
        - Error message indicates missing account ID
        """
        mock_get_account_id.return_value = "111111111111"

        # Account context without account ID
        account_context = {
            "assumeRoleName": "DRSOrchestrationRole",
            "isCurrentAccount": False,
        }

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            create_drs_client("us-east-1", account_context)

        error_msg = str(exc_info.value)
        assert "AccountId" in error_msg

    @patch("cross_account.get_current_account_id")
    def test_create_drs_client_missing_role_name(
        self, mock_get_account_id, mock_env_vars
    ):
        """
        Test DRS client creation fails when role name is missing.

        Validates:
        - ValueError is raised
        - Error message indicates missing role name
        - Account ID is included in error message
        """
        mock_get_account_id.return_value = "111111111111"

        # Account context without role name
        account_context = {
            "accountId": "222222222222",
            "assumeRoleName": None,
            "isCurrentAccount": False,
        }

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            create_drs_client("us-east-1", account_context)

        error_msg = str(exc_info.value)
        assert "AssumeRoleName" in error_msg
        assert "222222222222" in error_msg

    @patch("cross_account.boto3.client")
    @patch("cross_account.get_current_account_id")
    def test_create_drs_client_skip_assumption_same_account(
        self, mock_get_account_id, mock_boto_client, mock_env_vars
    ):
        """
        Test DRS client skips role assumption when already in target account.

        Validates:
        - No role assumption occurs when current account matches target
        - Standard boto3 client is created
        """
        # Current account matches target account
        mock_get_account_id.return_value = "222222222222"

        # Mock DRS client
        mock_drs_client = Mock()
        mock_boto_client.return_value = mock_drs_client

        # Account context for "cross-account" that's actually current account
        account_context = {
            "accountId": "222222222222",
            "assumeRoleName": "DRSOrchestrationRole",
            "isCurrentAccount": False,
        }

        # Execute
        client = create_drs_client("us-east-1", account_context)

        # Verify standard boto3 client was created (no session)
        mock_boto_client.assert_called_once_with("drs", region_name="us-east-1")
        assert client == mock_drs_client

    @patch("cross_account.get_cross_account_session")
    @patch("cross_account.get_current_account_id")
    def test_create_drs_client_role_assumption_failure(
        self, mock_get_account_id, mock_get_session, mock_env_vars
    ):
        """
        Test DRS client creation handles role assumption failures.

        Validates:
        - RuntimeError is raised when role assumption fails
        - Error message includes account ID and role name
        - Detailed guidance is provided
        """
        mock_get_account_id.return_value = "111111111111"

        # Mock role assumption failure
        mock_get_session.side_effect = ClientError(
            {
                "Error": {
                    "Code": "AccessDenied",
                    "Message": "User is not authorized to perform: sts:AssumeRole",
                }
            },
            "AssumeRole",
        )

        account_context = {
            "accountId": "222222222222",
            "assumeRoleName": "DRSOrchestrationRole",
            "isCurrentAccount": False,
        }

        # Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            create_drs_client("us-east-1", account_context)

        error_msg = str(exc_info.value)
        assert "Failed to assume" in error_msg
        assert "222222222222" in error_msg
        assert "DRSOrchestrationRole" in error_msg


# ============================================================================
# Test: create_ec2_client()
# ============================================================================


class TestCreateEc2Client:
    """Test suite for create_ec2_client() function"""

    @patch("cross_account.boto3.client")
    @patch("cross_account.get_current_account_id")
    def test_create_ec2_client_current_account_no_context(
        self, mock_get_account_id, mock_boto_client, mock_env_vars
    ):
        """
        Test EC2 client creation for current account without account context.

        Validates:
        - No role assumption occurs
        - Standard boto3 client is created
        - Correct region is used
        """
        mock_get_account_id.return_value = "111111111111"

        # Mock EC2 client
        mock_ec2_client = Mock()
        mock_boto_client.return_value = mock_ec2_client

        # Execute without account context
        client = create_ec2_client("us-east-1")

        # Verify standard boto3 client was created
        mock_boto_client.assert_called_once_with("ec2", region_name="us-east-1")
        assert client == mock_ec2_client

    @patch("cross_account.boto3.client")
    @patch("cross_account.get_current_account_id")
    def test_create_ec2_client_current_account_with_context(
        self, mock_get_account_id, mock_boto_client, mock_env_vars
    ):
        """
        Test EC2 client creation for current account with isCurrentAccount=True.

        Validates:
        - No role assumption occurs
        - Standard boto3 client is created
        """
        mock_get_account_id.return_value = "111111111111"

        # Mock EC2 client
        mock_ec2_client = Mock()
        mock_boto_client.return_value = mock_ec2_client

        # Account context for current account
        account_context = {
            "accountId": "111111111111",
            "assumeRoleName": None,
            "isCurrentAccount": True,
        }

        # Execute
        client = create_ec2_client("us-east-1", account_context)

        # Verify standard boto3 client was created
        mock_boto_client.assert_called_once_with("ec2", region_name="us-east-1")
        assert client == mock_ec2_client

    @patch("cross_account.get_cross_account_session")
    @patch("cross_account.get_current_account_id")
    def test_create_ec2_client_cross_account_without_external_id(
        self, mock_get_account_id, mock_get_session, mock_env_vars
    ):
        """
        Test EC2 client creation for cross-account without external ID.

        Validates:
        - Cross-account session is created
        - EC2 client is created with assumed role credentials
        - Correct region is used
        """
        mock_get_account_id.return_value = "111111111111"

        # Mock cross-account session
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        # Mock EC2 client
        mock_ec2_client = Mock()
        mock_session.client.return_value = mock_ec2_client

        # Account context for cross-account
        account_context = {
            "accountId": "222222222222",
            "assumeRoleName": "DRSOrchestrationRole",
            "isCurrentAccount": False,
        }

        # Execute
        client = create_ec2_client("us-east-1", account_context)

        # Verify cross-account session was created
        mock_get_session.assert_called_once()
        call_args = mock_get_session.call_args[1]

        # Verify role ARN
        assert call_args["role_arn"] == "arn:aws:iam::222222222222:role/DRSOrchestrationRole"

        # Verify EC2 client was created with correct region
        mock_session.client.assert_called_once_with("ec2", region_name="us-east-1")
        assert client == mock_ec2_client

    @patch("cross_account.get_cross_account_session")
    @patch("cross_account.get_current_account_id")
    def test_create_ec2_client_cross_account_with_external_id(
        self, mock_get_account_id, mock_get_session, mock_env_vars
    ):
        """
        Test EC2 client creation for cross-account with external ID.

        Validates:
        - Cross-account session is created with external ID
        - External ID is properly passed
        - EC2 client is created successfully
        """
        mock_get_account_id.return_value = "111111111111"

        # Mock cross-account session
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        # Mock EC2 client
        mock_ec2_client = Mock()
        mock_session.client.return_value = mock_ec2_client

        # Account context with external ID
        account_context = {
            "accountId": "222222222222",
            "assumeRoleName": "DRSOrchestrationRole",
            "externalId": "external-id-456",
            "isCurrentAccount": False,
        }

        # Execute
        client = create_ec2_client("us-east-1", account_context)

        # Verify cross-account session was created with external ID
        mock_get_session.assert_called_once()
        call_args = mock_get_session.call_args[1]

        assert call_args["role_arn"] == "arn:aws:iam::222222222222:role/DRSOrchestrationRole"
        assert call_args["external_id"] == "external-id-456"

        # Verify EC2 client was created
        assert client == mock_ec2_client

    @patch("cross_account.get_current_account_id")
    def test_create_ec2_client_missing_account_id(
        self, mock_get_account_id, mock_env_vars
    ):
        """
        Test EC2 client creation fails when account ID is missing.

        Validates:
        - ValueError is raised
        - Error message indicates missing account ID
        """
        mock_get_account_id.return_value = "111111111111"

        # Account context without account ID
        account_context = {
            "assumeRoleName": "DRSOrchestrationRole",
            "isCurrentAccount": False,
        }

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            create_ec2_client("us-east-1", account_context)

        error_msg = str(exc_info.value)
        assert "AccountId" in error_msg

    @patch("cross_account.get_current_account_id")
    def test_create_ec2_client_missing_role_name(
        self, mock_get_account_id, mock_env_vars
    ):
        """
        Test EC2 client creation fails when role name is missing.

        Validates:
        - ValueError is raised
        - Error message indicates missing role name
        """
        mock_get_account_id.return_value = "111111111111"

        # Account context without role name
        account_context = {
            "accountId": "222222222222",
            "assumeRoleName": None,
            "isCurrentAccount": False,
        }

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            create_ec2_client("us-east-1", account_context)

        error_msg = str(exc_info.value)
        assert "AssumeRoleName" in error_msg

    @patch("cross_account.boto3.client")
    @patch("cross_account.get_current_account_id")
    def test_create_ec2_client_skip_assumption_same_account(
        self, mock_get_account_id, mock_boto_client, mock_env_vars
    ):
        """
        Test EC2 client skips role assumption when already in target account.

        Validates:
        - No role assumption occurs when current account matches target
        - Standard boto3 client is created
        """
        # Current account matches target account
        mock_get_account_id.return_value = "222222222222"

        # Mock EC2 client
        mock_ec2_client = Mock()
        mock_boto_client.return_value = mock_ec2_client

        # Account context for "cross-account" that's actually current account
        account_context = {
            "accountId": "222222222222",
            "assumeRoleName": "DRSOrchestrationRole",
            "isCurrentAccount": False,
        }

        # Execute
        client = create_ec2_client("us-east-1", account_context)

        # Verify standard boto3 client was created (no session)
        mock_boto_client.assert_called_once_with("ec2", region_name="us-east-1")
        assert client == mock_ec2_client

    @patch("cross_account.get_cross_account_session")
    @patch("cross_account.get_current_account_id")
    def test_create_ec2_client_role_assumption_failure(
        self, mock_get_account_id, mock_get_session, mock_env_vars
    ):
        """
        Test EC2 client creation handles role assumption failures.

        Validates:
        - RuntimeError is raised when role assumption fails
        - Error message includes account ID
        """
        mock_get_account_id.return_value = "111111111111"

        # Mock role assumption failure
        mock_get_session.side_effect = ClientError(
            {
                "Error": {
                    "Code": "AccessDenied",
                    "Message": "User is not authorized to perform: sts:AssumeRole",
                }
            },
            "AssumeRole",
        )

        account_context = {
            "accountId": "222222222222",
            "assumeRoleName": "DRSOrchestrationRole",
            "isCurrentAccount": False,
        }

        # Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            create_ec2_client("us-east-1", account_context)

        error_msg = str(exc_info.value)
        assert "Failed to assume" in error_msg
        assert "222222222222" in error_msg


# ============================================================================
# Test: get_current_account_id()
# ============================================================================


class TestGetCurrentAccountId:
    """Test suite for get_current_account_id() helper function"""

    @patch("cross_account.boto3.client")
    def test_get_current_account_id_success(self, mock_boto_client, mock_env_vars):
        """
        Test successful retrieval of current account ID via STS.

        Validates:
        - STS GetCallerIdentity is called
        - Account ID is returned
        """
        # Mock STS client
        mock_sts = Mock()
        mock_boto_client.return_value = mock_sts

        # Mock GetCallerIdentity response
        mock_sts.get_caller_identity.return_value = {"Account": "111111111111"}

        # Execute
        account_id = get_current_account_id()

        # Verify
        assert account_id == "111111111111"
        mock_sts.get_caller_identity.assert_called_once()

    @patch("cross_account.boto3.client")
    def test_get_current_account_id_sts_failure(self, mock_boto_client, mock_env_vars):
        """
        Test fallback when STS GetCallerIdentity fails.

        Validates:
        - Returns "unknown" when STS fails
        - Error is caught and handled gracefully
        """
        # Mock STS client
        mock_sts = Mock()
        mock_boto_client.return_value = mock_sts

        # Mock STS failure
        mock_sts.get_caller_identity.side_effect = Exception("STS unavailable")

        # Execute
        account_id = get_current_account_id()

        # Verify fallback to "unknown"
        assert account_id == "unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
