"""
Property-based tests for account utilities.

Feature: standardized-cross-account-role-naming
Properties:
- Property 1: ARN construction follows standardized pattern
- Property 7: Account ID extraction is inverse of construction

Validates: Requirements 1.2, 2.2, 4.2
"""

import os
import sys

import pytest
from hypothesis import given, settings, strategies as st

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.account_utils import (
    STANDARD_ROLE_NAME,
    construct_role_arn,
    extract_account_id_from_arn,
    validate_account_id,
)


# Strategy for valid AWS account IDs (12 digits)
account_id_strategy = st.text(alphabet="0123456789", min_size=12, max_size=12)


@settings(max_examples=100)
@given(account_id=account_id_strategy)
def test_property_arn_construction_pattern(account_id):
    """
    Property 1: ARN construction follows standardized pattern.

    Feature: standardized-cross-account-role-naming
    Property 1: For any valid 12-digit AWS account ID, constructed ARN
                must match pattern arn:aws:iam::{account-id}:role/DRSOrchestrationRole

    Validates: Requirements 1.2, 2.2, 4.2
    """
    # Act
    arn = construct_role_arn(account_id)

    # Assert - Verify exact pattern
    expected = f"arn:aws:iam::{account_id}:role/{STANDARD_ROLE_NAME}"
    assert arn == expected, (
        f"ARN should match pattern. Expected: {expected}, Got: {arn}"
    )

    # Assert - Verify structure components
    assert arn.startswith("arn:aws:iam::"), (
        f"ARN should start with 'arn:aws:iam::'. Got: {arn}"
    )
    assert arn.endswith(f":role/{STANDARD_ROLE_NAME}"), (
        f"ARN should end with ':role/{STANDARD_ROLE_NAME}'. Got: {arn}"
    )
    assert account_id in arn, (
        f"ARN should contain account ID {account_id}. Got: {arn}"
    )

    # Assert - Verify no extra characters
    parts = arn.split("::")
    assert len(parts) == 2, f"ARN should have exactly one '::'. Got: {arn}"

    # Assert - Verify account ID position
    account_part = parts[1].split(":role/")[0]
    assert account_part == account_id, (
        f"Account ID in ARN should be {account_id}. Got: {account_part}"
    )


@settings(max_examples=100)
@given(account_id=account_id_strategy)
def test_property_account_id_extraction_inverse(account_id):
    """
    Property 7: Account ID extraction is inverse of construction.

    Feature: standardized-cross-account-role-naming
    Property 7: For any valid account ID, extracting from constructed ARN
                must return original account ID (round-trip)

    Validates: Requirements 1.2, 2.2 (indirectly validates correctness)
    """
    # Act - Construct ARN
    arn = construct_role_arn(account_id)

    # Act - Extract account ID
    extracted_id = extract_account_id_from_arn(arn)

    # Assert - Must match original
    assert extracted_id == account_id, (
        f"Extracted account ID should match original. "
        f"Original: {account_id}, Extracted: {extracted_id}, ARN: {arn}"
    )

    # Assert - Extracted ID should be valid
    assert validate_account_id(extracted_id), (
        f"Extracted account ID should be valid. Got: {extracted_id}"
    )


@settings(max_examples=100)
@given(
    account_id=account_id_strategy,
    role_name=st.text(
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="-_",
        ),
        min_size=1,
        max_size=64,
    ),
)
def test_property_extraction_works_for_any_role_name(account_id, role_name):
    """
    Property: Account ID extraction works for any valid role name.

    Validates that extraction logic is not tied to specific role name.
    """
    # Arrange - Create ARN with custom role name
    custom_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

    # Act
    extracted_id = extract_account_id_from_arn(custom_arn)

    # Assert
    assert extracted_id == account_id, (
        f"Should extract account ID from any valid ARN. "
        f"ARN: {custom_arn}, Expected: {account_id}, Got: {extracted_id}"
    )


@settings(max_examples=100)
@given(
    account_id=account_id_strategy,
    prefix=st.text(
        alphabet=st.characters(
            blacklist_categories=("Cc", "Cs", "Zs", "Zl", "Zp")
        ),
        min_size=0,
        max_size=10,
    ),
    suffix=st.text(
        alphabet=st.characters(
            blacklist_categories=("Cc", "Cs", "Zs", "Zl", "Zp")
        ),
        min_size=0,
        max_size=10,
    ),
)
def test_property_validation_rejects_invalid_formats(
    account_id, prefix, suffix
):
    """
    Property: Validation correctly identifies invalid account IDs.

    Tests that validation rejects account IDs with extra characters.
    Excludes control characters (Cc), surrogates (Cs), and all
    whitespace categories (Zs, Zl, Zp).
    """
    # Arrange - Create invalid account ID
    invalid_id = f"{prefix}{account_id}{suffix}"

    # Act
    is_valid = validate_account_id(invalid_id)

    # Assert
    if prefix or suffix:
        # Should be invalid if we added any characters
        assert not is_valid, (
            f"Should reject account ID with extra characters. "
            f"Input: {invalid_id}, prefix='{prefix}', suffix='{suffix}'"
        )
    else:
        # Should be valid if no prefix/suffix
        assert is_valid, (
            f"Should accept valid 12-digit account ID. Input: {invalid_id}"
        )


def test_arn_construction_specific_examples():
    """Unit test examples for ARN construction"""
    # Example 1: Standard account ID
    arn = construct_role_arn("123456789012")
    assert arn == "arn:aws:iam::123456789012:role/DRSOrchestrationRole"

    # Example 2: Different account ID
    arn = construct_role_arn("999999999999")
    assert arn == "arn:aws:iam::999999999999:role/DRSOrchestrationRole"

    # Example 3: Account ID with leading zeros
    arn = construct_role_arn("000000000001")
    assert arn == "arn:aws:iam::000000000001:role/DRSOrchestrationRole"


def test_arn_construction_invalid_inputs():
    """Unit test examples for invalid inputs"""
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

    # None
    with pytest.raises(ValueError, match="Invalid account ID"):
        construct_role_arn(None)


def test_account_id_validation_specific_examples():
    """Unit test examples for account ID validation"""
    # Valid
    assert validate_account_id("123456789012") is True
    assert validate_account_id("000000000001") is True
    assert validate_account_id("999999999999") is True

    # Invalid - too short
    assert validate_account_id("12345") is False

    # Invalid - too long
    assert validate_account_id("1234567890123") is False

    # Invalid - non-numeric
    assert validate_account_id("12345678901a") is False
    assert validate_account_id("abcdefghijkl") is False

    # Invalid - empty
    assert validate_account_id("") is False

    # Invalid - None
    assert validate_account_id(None) is False

    # Invalid - with spaces
    assert validate_account_id("123 456 789 012") is False


def test_account_id_extraction_specific_examples():
    """Unit test examples for account ID extraction"""
    # Standard ARN
    account_id = extract_account_id_from_arn(
        "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
    )
    assert account_id == "123456789012"

    # Custom role name
    account_id = extract_account_id_from_arn(
        "arn:aws:iam::999999999999:role/CustomRole"
    )
    assert account_id == "999999999999"

    # Invalid ARN - returns None
    assert extract_account_id_from_arn("invalid-arn") is None
    assert extract_account_id_from_arn("") is None
    assert extract_account_id_from_arn("arn:aws:s3:::bucket") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
