"""
Unit tests for account utilities.

Feature: standardized-cross-account-role-naming
Tests specific examples and edge cases for account utility functions.

Validates: Requirements 1.2, 1.3, 2.2, 2.3
"""

import os
import sys

import pytest

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.account_utils import (
    STANDARD_ROLE_NAME,
    construct_role_arn,
    extract_account_id_from_arn,
    get_role_arn,
    validate_account_id,
)


class TestConstructRoleArn:
    """Tests for construct_role_arn function"""

    def test_valid_account_id_standard(self):
        """Test ARN construction with standard account ID"""
        account_id = "123456789012"
        expected = "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
        assert construct_role_arn(account_id) == expected

    def test_valid_account_id_with_zeros(self):
        """Test ARN construction with leading zeros"""
        account_id = "000000000001"
        expected = "arn:aws:iam::000000000001:role/DRSOrchestrationRole"
        assert construct_role_arn(account_id) == expected

    def test_valid_account_id_all_nines(self):
        """Test ARN construction with all nines"""
        account_id = "999999999999"
        expected = "arn:aws:iam::999999999999:role/DRSOrchestrationRole"
        assert construct_role_arn(account_id) == expected

    def test_invalid_account_id_too_short(self):
        """Test ARN construction fails with too short account ID"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            construct_role_arn("12345")

    def test_invalid_account_id_too_long(self):
        """Test ARN construction fails with too long account ID"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            construct_role_arn("1234567890123")

    def test_invalid_account_id_non_numeric(self):
        """Test ARN construction fails with non-numeric account ID"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            construct_role_arn("12345678901a")

    def test_invalid_account_id_with_spaces(self):
        """Test ARN construction fails with spaces"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            construct_role_arn("123 456 789 012")

    def test_invalid_account_id_empty(self):
        """Test ARN construction fails with empty string"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            construct_role_arn("")

    def test_invalid_account_id_none(self):
        """Test ARN construction fails with None"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            construct_role_arn(None)

    def test_arn_format_components(self):
        """Test ARN has correct format components"""
        arn = construct_role_arn("123456789012")
        assert arn.startswith("arn:aws:iam::")
        assert ":role/" in arn
        assert arn.endswith("DRSOrchestrationRole")


class TestValidateAccountId:
    """Tests for validate_account_id function"""

    def test_valid_standard_account_id(self):
        """Test validation accepts standard account ID"""
        assert validate_account_id("123456789012") is True

    def test_valid_account_id_with_zeros(self):
        """Test validation accepts account ID with leading zeros"""
        assert validate_account_id("000000000001") is True

    def test_valid_account_id_all_nines(self):
        """Test validation accepts all nines"""
        assert validate_account_id("999999999999") is True

    def test_invalid_too_short(self):
        """Test validation rejects too short account ID"""
        assert validate_account_id("12345") is False
        assert validate_account_id("12345678901") is False

    def test_invalid_too_long(self):
        """Test validation rejects too long account ID"""
        assert validate_account_id("1234567890123") is False
        assert validate_account_id("12345678901234567890") is False

    def test_invalid_non_numeric(self):
        """Test validation rejects non-numeric account ID"""
        assert validate_account_id("12345678901a") is False
        assert validate_account_id("abcdefghijkl") is False
        assert validate_account_id("123-456-789-012") is False

    def test_invalid_with_spaces(self):
        """Test validation rejects account ID with spaces"""
        assert validate_account_id("123 456 789 012") is False
        assert validate_account_id(" 123456789012") is False
        assert validate_account_id("123456789012 ") is False

    def test_invalid_empty(self):
        """Test validation rejects empty string"""
        assert validate_account_id("") is False

    def test_invalid_none(self):
        """Test validation rejects None"""
        assert validate_account_id(None) is False


class TestExtractAccountIdFromArn:
    """Tests for extract_account_id_from_arn function"""

    def test_extract_from_standard_arn(self):
        """Test extraction from standardized ARN"""
        arn = "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
        assert extract_account_id_from_arn(arn) == "123456789012"

    def test_extract_from_custom_role_arn(self):
        """Test extraction from ARN with custom role name"""
        arn = "arn:aws:iam::999999999999:role/CustomRole"
        assert extract_account_id_from_arn(arn) == "999999999999"

    def test_extract_from_arn_with_path(self):
        """Test extraction from ARN with role path"""
        arn = "arn:aws:iam::123456789012:role/path/to/role"
        assert extract_account_id_from_arn(arn) == "123456789012"

    def test_extract_from_arn_with_zeros(self):
        """Test extraction from ARN with leading zeros"""
        arn = "arn:aws:iam::000000000001:role/TestRole"
        assert extract_account_id_from_arn(arn) == "000000000001"

    def test_extract_invalid_arn_format(self):
        """Test extraction returns None for invalid ARN"""
        assert extract_account_id_from_arn("invalid-arn") is None

    def test_extract_empty_string(self):
        """Test extraction returns None for empty string"""
        assert extract_account_id_from_arn("") is None

    def test_extract_s3_arn(self):
        """Test extraction returns None for non-IAM ARN"""
        assert extract_account_id_from_arn("arn:aws:s3:::bucket") is None

    def test_extract_lambda_arn(self):
        """Test extraction returns None for Lambda ARN"""
        arn = "arn:aws:lambda:us-east-1:123456789012:function:my-function"
        assert extract_account_id_from_arn(arn) is None

    def test_extract_partial_arn(self):
        """Test extraction returns None for partial ARN"""
        assert extract_account_id_from_arn("arn:aws:iam::123456789012") is None


class TestGetRoleArn:
    """Tests for get_role_arn function"""

    def test_without_explicit_arn(self):
        """Test get_role_arn constructs ARN when not provided"""
        account_id = "123456789012"
        expected = "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
        assert get_role_arn(account_id) == expected

    def test_with_explicit_arn(self):
        """Test get_role_arn uses explicit ARN when provided"""
        account_id = "123456789012"
        explicit_arn = "arn:aws:iam::123456789012:role/CustomRole"
        assert get_role_arn(account_id, explicit_arn=explicit_arn) == explicit_arn

    def test_explicit_arn_takes_precedence(self):
        """Test explicit ARN takes precedence over constructed ARN"""
        account_id = "123456789012"
        explicit_arn = "arn:aws:iam::999999999999:role/DifferentRole"
        result = get_role_arn(account_id, explicit_arn=explicit_arn)
        
        # Should use explicit ARN, not construct from account_id
        assert result == explicit_arn
        assert result != construct_role_arn(account_id)

    def test_explicit_arn_none(self):
        """Test get_role_arn constructs ARN when explicit_arn is None"""
        account_id = "123456789012"
        expected = "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
        assert get_role_arn(account_id, explicit_arn=None) == expected

    def test_explicit_arn_empty_string(self):
        """Test get_role_arn constructs ARN when explicit_arn is empty"""
        account_id = "123456789012"
        expected = "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
        # Empty string is falsy, so should construct
        assert get_role_arn(account_id, explicit_arn="") == expected

    def test_invalid_account_id_without_explicit_arn(self):
        """Test get_role_arn fails with invalid account ID and no explicit ARN"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            get_role_arn("12345")

    def test_invalid_account_id_with_explicit_arn(self):
        """Test get_role_arn succeeds with invalid account ID if explicit ARN provided"""
        # When explicit ARN is provided, account_id validation is bypassed
        explicit_arn = "arn:aws:iam::123456789012:role/CustomRole"
        result = get_role_arn("invalid", explicit_arn=explicit_arn)
        assert result == explicit_arn


class TestStandardRoleName:
    """Tests for STANDARD_ROLE_NAME constant"""

    def test_constant_value(self):
        """Test STANDARD_ROLE_NAME has expected value"""
        assert STANDARD_ROLE_NAME == "DRSOrchestrationRole"

    def test_constant_used_in_construction(self):
        """Test STANDARD_ROLE_NAME is used in ARN construction"""
        arn = construct_role_arn("123456789012")
        assert STANDARD_ROLE_NAME in arn


class TestRoundTripConversion:
    """Tests for round-trip conversion between account ID and ARN"""

    def test_construct_and_extract_round_trip(self):
        """Test constructing ARN and extracting account ID returns original"""
        account_id = "123456789012"
        arn = construct_role_arn(account_id)
        extracted = extract_account_id_from_arn(arn)
        assert extracted == account_id

    def test_round_trip_with_zeros(self):
        """Test round-trip with leading zeros"""
        account_id = "000000000001"
        arn = construct_role_arn(account_id)
        extracted = extract_account_id_from_arn(arn)
        assert extracted == account_id

    def test_round_trip_preserves_format(self):
        """Test round-trip preserves exact account ID format"""
        account_id = "012345678901"
        arn = construct_role_arn(account_id)
        extracted = extract_account_id_from_arn(arn)
        # Should preserve leading zero
        assert extracted == account_id
        assert extracted[0] == "0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
