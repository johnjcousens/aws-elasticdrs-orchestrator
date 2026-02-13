"""
Property-based tests for account utilities.

Feature: standardized-cross-account-role-naming
Properties:
- Property 1: ARN construction follows standardized pattern
- Property 7: Account ID extraction is inverse of construction

Feature: account-context-improvements
Properties:
- Property 2: Account ID Format Validation
- Property 3: Invocation Source Detection
- Property 4: Direct Invocation Requires Account ID

Validates: Requirements 1.2, 1.6, 1.7, 1.9, 1.10, 2.2, 4.2
"""

import json  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402

import pytest  # noqa: F401
from hypothesis import assume, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.account_utils import (  # noqa: E402
    STANDARD_ROLE_NAME,
    construct_role_arn,
    detect_invocation_source,
    extract_account_id_from_arn,
    validate_account_context_for_invocation,
    validate_account_id,
)
from shared.security_utils import (  # noqa: E402
    InputValidationError,
)


# Strategy for valid AWS account IDs (12 digits)
account_id_strategy = st.text(alphabet="0123456789", min_size=12, max_size=12)


@settings(max_examples=100)
@given(account_id=account_id_strategy)
@pytest.mark.property
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
    assert arn == expected, f"ARN should match pattern. Expected: {expected}, Got: {arn}"

    # Assert - Verify structure components
    assert arn.startswith("arn:aws:iam::"), f"ARN should start with 'arn:aws:iam::'. Got: {arn}"
    assert arn.endswith(f":role/{STANDARD_ROLE_NAME}"), f"ARN should end with ':role/{STANDARD_ROLE_NAME}'. Got: {arn}"
    assert account_id in arn, f"ARN should contain account ID {account_id}. Got: {arn}"

    # Assert - Verify no extra characters
    parts = arn.split("::")
    assert len(parts) == 2, f"ARN should have exactly one '::'. Got: {arn}"

    # Assert - Verify account ID position
    account_part = parts[1].split(":role/")[0]
    assert account_part == account_id, f"Account ID in ARN should be {account_id}. Got: {account_part}"


@settings(max_examples=100)
@given(account_id=account_id_strategy)
@pytest.mark.property
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
        "Extracted account ID should match original. " f"Original: {account_id}, Extracted: {extracted_id}, ARN: {arn}"
    )

    # Assert - Extracted ID should be valid
    assert validate_account_id(extracted_id), f"Extracted account ID should be valid. Got: {extracted_id}"


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
@pytest.mark.property
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
        "Should extract account ID from any valid ARN. "
        f"ARN: {custom_arn}, Expected: {account_id}, Got: {extracted_id}"
    )


@settings(max_examples=100)
@given(
    account_id=account_id_strategy,
    prefix=st.text(
        alphabet=st.characters(blacklist_categories=("Cc", "Cs", "Zs", "Zl", "Zp")),
        min_size=0,
        max_size=10,
    ),
    suffix=st.text(
        alphabet=st.characters(blacklist_categories=("Cc", "Cs", "Zs", "Zl", "Zp")),
        min_size=0,
        max_size=10,
    ),
)
@pytest.mark.property
def test_property_validation_rejects_invalid_formats(account_id, prefix, suffix):
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
            "Should reject account ID with extra characters. "
            f"Input: {invalid_id}, prefix='{prefix}', suffix='{suffix}'"
        )
    else:
        # Should be valid if no prefix/suffix
        assert is_valid, f"Should accept valid 12-digit account ID. Input: {invalid_id}"


@pytest.mark.property
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


@pytest.mark.property
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


@pytest.mark.property
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


@pytest.mark.property
def test_account_id_extraction_specific_examples():
    """Unit test examples for account ID extraction"""
    # Standard ARN
    account_id = extract_account_id_from_arn("arn:aws:iam::123456789012:role/DRSOrchestrationRole")  # noqa: F841
    assert account_id == "123456789012"  # noqa: F841

    # Custom role name
    account_id = extract_account_id_from_arn("arn:aws:iam::999999999999:role/CustomRole")  # noqa: F841
    assert account_id == "999999999999"  # noqa: F841

    # Invalid ARN - returns None
    assert extract_account_id_from_arn("invalid-arn") is None
    assert extract_account_id_from_arn("") is None
    assert extract_account_id_from_arn("arn:aws:s3:::bucket") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])


# ============================================================
# Strategies for account-context-improvements properties
# ============================================================


@st.composite
def api_gateway_event_strategy(draw):
    """Generate API Gateway event with requestContext."""
    return {
        "requestContext": {
            "requestId": draw(st.uuids()).hex,
            "apiId": draw(st.text(min_size=10, max_size=10)),
            "identity": {"cognitoIdentityId": draw(st.uuids()).hex},
        },
        "body": json.dumps({"groupName": draw(st.text(min_size=1, max_size=255))}),
    }


@st.composite
def direct_lambda_event_strategy(draw):
    """Generate direct Lambda invocation event (no requestContext)."""
    include_account = draw(st.booleans())
    body = {"groupName": draw(st.text(min_size=1, max_size=255))}
    if include_account:
        body["accountId"] = draw(st.from_regex(r"^\d{12}$", fullmatch=True))
    return {"body": json.dumps(body)}


@st.composite
def direct_event_without_account_strategy(draw):
    """Generate direct Lambda event without accountId in body."""
    body = {"groupName": draw(st.text(min_size=1, max_size=255))}
    # Optionally include empty accountId
    if draw(st.booleans()):
        body["accountId"] = ""
    return {"body": json.dumps(body)}


# ============================================================
# Property 2: Account ID Format Validation
# ============================================================


@settings(max_examples=200)
@given(account_id=st.text())
@pytest.mark.property
def test_property_account_id_format_validation(account_id):
    """
    Property 2: Account ID Format Validation.

    For any string, validate_account_id returns True if and only
    if the string is exactly 12 digits.

    **Validates: Requirements 1.6, 1.7**
    """
    is_valid = validate_account_id(account_id)

    expected_valid = len(account_id) == 12 and account_id.isdigit()

    assert is_valid == expected_valid, (
        f"validate_account_id('{account_id}') returned " f"{is_valid}, expected {expected_valid}"
    )


# ============================================================
# Property 3: Invocation Source Detection
# ============================================================


@settings(max_examples=200)
@given(
    event=st.one_of(
        api_gateway_event_strategy(),
        direct_lambda_event_strategy(),
    )
)
@pytest.mark.property
def test_property_invocation_source_detection(event):
    """
    Property 3: Invocation Source Detection.

    For any Lambda event, events with requestContext are detected
    as api_gateway, events without are detected as direct.

    **Validates: Requirements 1.10**
    """
    source = detect_invocation_source(event)

    if "requestContext" in event:
        assert source == "api_gateway", f"Event with requestContext should be 'api_gateway'" f", got '{source}'"
    else:
        assert source == "direct", f"Event without requestContext should be 'direct'" f", got '{source}'"


@settings(max_examples=100)
@given(
    extra_keys=st.dictionaries(
        keys=st.text(min_size=1, max_size=30).filter(lambda k: k != "requestContext"),
        values=st.text(min_size=1, max_size=50),
        min_size=0,
        max_size=5,
    )
)
@pytest.mark.property
def test_property_invocation_source_direct_no_request_context(
    extra_keys,
):
    """
    Property 3 (supplemental): Any dict without requestContext
    is detected as direct invocation.

    **Validates: Requirements 1.10**
    """
    event = dict(extra_keys)
    assert "requestContext" not in event
    source = detect_invocation_source(event)
    assert source == "direct", f"Event without requestContext should be 'direct'" f", got '{source}'"


# ============================================================
# Property 4: Direct Invocation Requires Account ID
# ============================================================


@settings(max_examples=200)
@given(event=direct_event_without_account_strategy())
@pytest.mark.property
def test_property_direct_invocation_requires_account_id(event):
    """
    Property 4: Direct Invocation Requires Account ID.

    For any direct Lambda event without accountId in body,
    validate_account_context_for_invocation raises
    InputValidationError.

    **Validates: Requirements 1.7, 1.9**
    """
    body = json.loads(event.get("body", "{}"))

    # Confirm this is a direct invocation event
    assert "requestContext" not in event

    # Body has no accountId or empty accountId
    account_id = body.get("accountId")
    assert not account_id

    with pytest.raises(InputValidationError):
        validate_account_context_for_invocation(event, body)


@settings(max_examples=100)
@given(event=direct_lambda_event_strategy())
@pytest.mark.property
def test_property_direct_invocation_with_valid_account_succeeds(
    event,
):
    """
    Property 4 (supplemental): Direct invocation with valid
    accountId succeeds and returns the provided accountId.

    **Validates: Requirements 1.6, 1.9**
    """
    body = json.loads(event.get("body", "{}"))
    account_id = body.get("accountId")

    if not account_id:
        # No accountId — should raise
        with pytest.raises(InputValidationError):
            validate_account_context_for_invocation(event, body)
    else:
        # Has valid 12-digit accountId — should succeed
        result = validate_account_context_for_invocation(event, body)
        assert result["accountId"] == account_id, f"Expected accountId '{account_id}', " f"got '{result['accountId']}'"
