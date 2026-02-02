"""
Unit tests for staging account data models and DynamoDB operations.

Tests cover:
- Data model creation and serialization
- Validation functions
- CRUD operations
- Error handling
- Edge cases (empty lists, missing attributes)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

# Add lambda/shared to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from staging_account_models import (
    StagingAccount,
    TargetAccount,
    validate_staging_account_structure,
    check_duplicate_staging_account,
    get_staging_accounts,
    add_staging_account,
    remove_staging_account,
    update_staging_accounts,
)


# Test Data
VALID_STAGING_ACCOUNT = {
    "accountId": "444455556666",
    "accountName": "STAGING_01",
    "roleArn": "arn:aws:iam::444455556666:role/DRSOrchestrationRole-test",
    "externalId": "drs-orchestration-test-444455556666",
}

TARGET_ACCOUNT_ID = "111122223333"


class TestStagingAccountDataClass:
    """Test StagingAccount data class."""

    def test_create_staging_account(self):
        """Test creating a StagingAccount object."""
        account = StagingAccount(
            accountId="444455556666",
            accountName="STAGING_01",
            roleArn="arn:aws:iam::444455556666:role/DRSRole",
            externalId="external-id-123",
        )

        assert account.accountId == "444455556666"
        assert account.accountName == "STAGING_01"
        assert account.roleArn == "arn:aws:iam::444455556666:role/DRSRole"
        assert account.externalId == "external-id-123"
        assert account.addedBy == "system"
        assert account.addedAt  # Should have timestamp

    def test_staging_account_to_dict(self):
        """Test converting StagingAccount to dictionary."""
        account = StagingAccount(
            accountId="444455556666",
            accountName="STAGING_01",
            roleArn="arn:aws:iam::444455556666:role/DRSRole",
            externalId="external-id-123",
            addedBy="user@example.com",
        )

        data = account.to_dict()

        assert data["accountId"] == "444455556666"
        assert data["accountName"] == "STAGING_01"
        assert data["roleArn"] == "arn:aws:iam::444455556666:role/DRSRole"
        assert data["externalId"] == "external-id-123"
        assert data["addedBy"] == "user@example.com"
        assert "addedAt" in data

    def test_staging_account_from_dict(self):
        """Test creating StagingAccount from dictionary."""
        data = {
            "accountId": "444455556666",
            "accountName": "STAGING_01",
            "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
            "externalId": "external-id-123",
            "addedAt": "2024-01-15T10:30:00Z",
            "addedBy": "user@example.com",
        }

        account = StagingAccount.from_dict(data)

        assert account.accountId == "444455556666"
        assert account.accountName == "STAGING_01"
        assert account.addedAt == "2024-01-15T10:30:00Z"
        assert account.addedBy == "user@example.com"


class TestTargetAccountDataClass:
    """Test TargetAccount data class."""

    def test_create_target_account(self):
        """Test creating a TargetAccount object."""
        account = TargetAccount(
            accountId="111122223333",
            accountName="DEMO_TARGET",
            roleArn="arn:aws:iam::111122223333:role/DRSRole",
            externalId="external-id-123",
        )

        assert account.accountId == "111122223333"
        assert account.accountName == "DEMO_TARGET"
        assert account.stagingAccounts == []
        assert account.status == "active"

    def test_target_account_with_staging_accounts(self):
        """Test TargetAccount with staging accounts."""
        staging1 = StagingAccount(
            accountId="444455556666",
            accountName="STAGING_01",
            roleArn="arn:aws:iam::444455556666:role/DRSRole",
            externalId="external-id-1",
        )
        staging2 = StagingAccount(
            accountId="777777777777",
            accountName="STAGING_02",
            roleArn="arn:aws:iam::777777777777:role/DRSRole",
            externalId="external-id-2",
        )

        account = TargetAccount(
            accountId="111122223333",
            accountName="DEMO_TARGET",
            stagingAccounts=[staging1, staging2],
        )

        assert len(account.stagingAccounts) == 2
        assert account.stagingAccounts[0].accountName == "STAGING_01"
        assert account.stagingAccounts[1].accountName == "STAGING_02"

    def test_target_account_to_dict(self):
        """Test converting TargetAccount to dictionary."""
        staging = StagingAccount(
            accountId="444455556666",
            accountName="STAGING_01",
            roleArn="arn:aws:iam::444455556666:role/DRSRole",
            externalId="external-id-1",
        )

        account = TargetAccount(
            accountId="111122223333",
            accountName="DEMO_TARGET",
            stagingAccounts=[staging],
        )

        data = account.to_dict()

        assert data["accountId"] == "111122223333"
        assert data["accountName"] == "DEMO_TARGET"
        assert len(data["stagingAccounts"]) == 1
        assert isinstance(data["stagingAccounts"][0], dict)
        assert data["stagingAccounts"][0]["accountId"] == "444455556666"

    def test_target_account_from_dict(self):
        """Test creating TargetAccount from dictionary."""
        data = {
            "accountId": "111122223333",
            "accountName": "DEMO_TARGET",
            "roleArn": "arn:aws:iam::111122223333:role/DRSRole",
            "externalId": "external-id-123",
            "stagingAccounts": [
                {
                    "accountId": "444455556666",
                    "accountName": "STAGING_01",
                    "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
                    "externalId": "external-id-1",
                    "addedAt": "2024-01-15T10:30:00Z",
                    "addedBy": "user@example.com",
                }
            ],
            "status": "active",
            "createdAt": "2024-01-10T08:00:00Z",
            "updatedAt": "2024-01-15T10:30:00Z",
        }

        account = TargetAccount.from_dict(data)

        assert account.accountId == "111122223333"
        assert len(account.stagingAccounts) == 1
        assert isinstance(account.stagingAccounts[0], StagingAccount)
        assert account.stagingAccounts[0].accountName == "STAGING_01"


class TestValidationFunctions:
    """Test validation functions."""

    def test_validate_valid_staging_account(self):
        """Test validation with valid staging account."""
        result = validate_staging_account_structure(VALID_STAGING_ACCOUNT)

        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_missing_required_field(self):
        """Test validation with missing required field."""
        invalid_account = {
            "accountId": "444455556666",
            "accountName": "STAGING_01",
            # Missing roleArn and externalId
        }

        result = validate_staging_account_structure(invalid_account)

        assert result["valid"] is False
        assert len(result["errors"]) == 2
        assert any("roleArn" in error for error in result["errors"])
        assert any("externalId" in error for error in result["errors"])

    def test_validate_empty_field(self):
        """Test validation with empty field."""
        invalid_account = {
            "accountId": "444455556666",
            "accountName": "",  # Empty
            "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
            "externalId": "external-id-123",
        }

        result = validate_staging_account_structure(invalid_account)

        assert result["valid"] is False
        assert any("accountName" in error for error in result["errors"])

    def test_validate_invalid_account_id_format(self):
        """Test validation with invalid account ID format."""
        invalid_account = {
            "accountId": "12345",  # Not 12 digits
            "accountName": "STAGING_01",
            "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
            "externalId": "external-id-123",
        }

        result = validate_staging_account_structure(invalid_account)

        assert result["valid"] is False
        assert any("account ID" in error for error in result["errors"])

    def test_validate_invalid_role_arn_format(self):
        """Test validation with invalid role ARN format."""
        invalid_account = {
            "accountId": "444455556666",
            "accountName": "STAGING_01",
            "roleArn": "invalid-arn",  # Invalid format
            "externalId": "external-id-123",
        }

        result = validate_staging_account_structure(invalid_account)

        assert result["valid"] is False
        assert any("role ARN" in error for error in result["errors"])


class TestDynamoDBOperations:
    """Test DynamoDB CRUD operations."""

    @patch("staging_account_models._get_target_accounts_table")
    def test_check_duplicate_staging_account_exists(self, mock_get_table):
        """Test checking for duplicate staging account (exists)."""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {
                "accountId": TARGET_ACCOUNT_ID,
                "stagingAccounts": [VALID_STAGING_ACCOUNT],
            }
        }
        mock_get_table.return_value = mock_table

        result = check_duplicate_staging_account(
            TARGET_ACCOUNT_ID, "444455556666"
        )

        assert result is True

    @patch("staging_account_models._get_target_accounts_table")
    def test_check_duplicate_staging_account_not_exists(
        self, mock_get_table
    ):
        """Test checking for duplicate staging account (not exists)."""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {
                "accountId": TARGET_ACCOUNT_ID,
                "stagingAccounts": [],
            }
        }
        mock_get_table.return_value = mock_table

        result = check_duplicate_staging_account(
            TARGET_ACCOUNT_ID, "444455556666"
        )

        assert result is False

    @patch("staging_account_models._get_target_accounts_table")
    def test_get_staging_accounts_success(self, mock_get_table):
        """Test getting staging accounts successfully."""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {
                "accountId": TARGET_ACCOUNT_ID,
                "stagingAccounts": [VALID_STAGING_ACCOUNT],
            }
        }
        mock_get_table.return_value = mock_table

        result = get_staging_accounts(TARGET_ACCOUNT_ID)

        assert len(result) == 1
        assert isinstance(result[0], StagingAccount)
        assert result[0].accountId == "444455556666"
        assert result[0].accountName == "STAGING_01"

    @patch("staging_account_models._get_target_accounts_table")
    def test_get_staging_accounts_empty_list(self, mock_get_table):
        """Test getting staging accounts returns empty list if not present."""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {
                "accountId": TARGET_ACCOUNT_ID,
                # No stagingAccounts attribute
            }
        }
        mock_get_table.return_value = mock_table

        result = get_staging_accounts(TARGET_ACCOUNT_ID)

        assert result == []

    @patch("staging_account_models._get_target_accounts_table")
    def test_get_staging_accounts_target_not_found(self, mock_get_table):
        """Test getting staging accounts when target account not found."""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # No Item
        mock_get_table.return_value = mock_table

        with pytest.raises(ValueError, match="not found"):
            get_staging_accounts(TARGET_ACCOUNT_ID)

    @patch("staging_account_models._get_target_accounts_table")
    @patch("staging_account_models.get_staging_accounts")
    @patch("staging_account_models.check_duplicate_staging_account")
    def test_add_staging_account_success(
        self, mock_check_dup, mock_get_staging, mock_get_table
    ):
        """Test adding staging account successfully."""
        mock_table = MagicMock()
        mock_table.update_item.return_value = {
            "Attributes": {
                "accountId": TARGET_ACCOUNT_ID,
                "stagingAccounts": [VALID_STAGING_ACCOUNT],
            }
        }
        mock_get_table.return_value = mock_table
        mock_check_dup.return_value = False
        mock_get_staging.return_value = []

        result = add_staging_account(
            TARGET_ACCOUNT_ID, VALID_STAGING_ACCOUNT
        )

        assert result["success"] is True
        assert "STAGING_01" in result["message"]
        assert len(result["stagingAccounts"]) == 1

    @patch("staging_account_models._get_target_accounts_table")
    @patch("staging_account_models.check_duplicate_staging_account")
    def test_add_staging_account_duplicate(
        self, mock_check_dup, mock_get_table
    ):
        """Test adding duplicate staging account raises error."""
        mock_get_table.return_value = MagicMock()
        mock_check_dup.return_value = True

        with pytest.raises(ValueError, match="already exists"):
            add_staging_account(TARGET_ACCOUNT_ID, VALID_STAGING_ACCOUNT)

    @patch("staging_account_models._get_target_accounts_table")
    def test_add_staging_account_invalid_structure(self, mock_get_table):
        """Test adding staging account with invalid structure."""
        mock_get_table.return_value = MagicMock()

        invalid_account = {
            "accountId": "invalid",  # Invalid format
            "accountName": "STAGING_01",
            "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
            "externalId": "external-id-123",
        }

        with pytest.raises(ValueError, match="Invalid staging account"):
            add_staging_account(TARGET_ACCOUNT_ID, invalid_account)

    @patch("staging_account_models._get_target_accounts_table")
    @patch("staging_account_models.get_staging_accounts")
    def test_remove_staging_account_success(
        self, mock_get_staging, mock_get_table
    ):
        """Test removing staging account successfully."""
        staging1 = StagingAccount(
            accountId="444455556666",
            accountName="STAGING_01",
            roleArn="arn:aws:iam::444455556666:role/DRSRole",
            externalId="external-id-1",
        )
        staging2 = StagingAccount(
            accountId="777777777777",
            accountName="STAGING_02",
            roleArn="arn:aws:iam::777777777777:role/DRSRole",
            externalId="external-id-2",
        )

        mock_get_staging.return_value = [staging1, staging2]

        mock_table = MagicMock()
        mock_table.update_item.return_value = {
            "Attributes": {
                "accountId": TARGET_ACCOUNT_ID,
                "stagingAccounts": [staging2.to_dict()],
            }
        }
        mock_get_table.return_value = mock_table

        result = remove_staging_account(TARGET_ACCOUNT_ID, "444455556666")

        assert result["success"] is True
        assert "STAGING_01" in result["message"]
        assert len(result["stagingAccounts"]) == 1

    @patch("staging_account_models._get_target_accounts_table")
    @patch("staging_account_models.get_staging_accounts")
    def test_remove_staging_account_not_found(
        self, mock_get_staging, mock_get_table
    ):
        """Test removing non-existent staging account raises error."""
        mock_get_staging.return_value = []
        mock_get_table.return_value = MagicMock()

        with pytest.raises(ValueError, match="not found"):
            remove_staging_account(TARGET_ACCOUNT_ID, "444455556666")

    @patch("staging_account_models._get_target_accounts_table")
    def test_update_staging_accounts_success(self, mock_get_table):
        """Test updating entire staging accounts list."""
        mock_table = MagicMock()
        mock_table.update_item.return_value = {
            "Attributes": {
                "accountId": TARGET_ACCOUNT_ID,
                "stagingAccounts": [VALID_STAGING_ACCOUNT],
            }
        }
        mock_get_table.return_value = mock_table

        result = update_staging_accounts(
            TARGET_ACCOUNT_ID, [VALID_STAGING_ACCOUNT]
        )

        assert result["success"] is True
        assert "1 staging accounts" in result["message"]
        assert len(result["stagingAccounts"]) == 1

    @patch("staging_account_models._get_target_accounts_table")
    def test_update_staging_accounts_invalid_structure(self, mock_get_table):
        """Test updating with invalid staging account structure."""
        mock_get_table.return_value = MagicMock()

        invalid_account = {
            "accountId": "invalid",
            "accountName": "STAGING_01",
            "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
            "externalId": "external-id-123",
        }

        with pytest.raises(ValueError, match="Invalid staging account"):
            update_staging_accounts(TARGET_ACCOUNT_ID, [invalid_account])


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch("staging_account_models._get_target_accounts_table")
    def test_operations_with_no_table_configured(self, mock_get_table):
        """Test operations when table is not configured."""
        mock_get_table.return_value = None

        with pytest.raises(ValueError, match="not configured"):
            get_staging_accounts(TARGET_ACCOUNT_ID)

        with pytest.raises(ValueError, match="not configured"):
            add_staging_account(TARGET_ACCOUNT_ID, VALID_STAGING_ACCOUNT)

        with pytest.raises(ValueError, match="not configured"):
            remove_staging_account(TARGET_ACCOUNT_ID, "444455556666")

    @patch("staging_account_models._get_target_accounts_table")
    @patch("staging_account_models.get_staging_accounts")
    @patch("staging_account_models.check_duplicate_staging_account")
    def test_add_staging_account_target_not_found(
        self, mock_check_dup, mock_get_staging, mock_get_table
    ):
        """Test adding staging account when target account not found."""
        mock_table = MagicMock()
        mock_table.update_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ConditionalCheckFailedException",
                    "Message": "Item not found",
                }
            },
            "UpdateItem",
        )
        mock_get_table.return_value = mock_table
        mock_check_dup.return_value = False
        mock_get_staging.return_value = []

        with pytest.raises(ValueError, match="not found"):
            add_staging_account(TARGET_ACCOUNT_ID, VALID_STAGING_ACCOUNT)

    @patch("staging_account_models._get_target_accounts_table")
    @patch("staging_account_models.get_staging_accounts")
    def test_remove_staging_account_target_not_found(
        self, mock_get_staging, mock_get_table
    ):
        """Test removing staging account when target account not found."""
        staging = StagingAccount(
            accountId="444455556666",
            accountName="STAGING_01",
            roleArn="arn:aws:iam::444455556666:role/DRSRole",
            externalId="external-id-1",
        )
        mock_get_staging.return_value = [staging]

        mock_table = MagicMock()
        mock_table.update_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ConditionalCheckFailedException",
                    "Message": "Item not found",
                }
            },
            "UpdateItem",
        )
        mock_get_table.return_value = mock_table

        with pytest.raises(ValueError, match="not found"):
            remove_staging_account(TARGET_ACCOUNT_ID, "444455556666")
