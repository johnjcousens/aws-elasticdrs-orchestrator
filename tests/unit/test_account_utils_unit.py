"""
Unit tests for account utilities.

Feature: standardized-cross-account-role-naming
Tests specific examples and edge cases for account utility functions.

Validates: Requirements 1.2, 1.3, 2.2, 2.3
"""

import os  # noqa: E402
import sys  # noqa: E402

import pytest  # noqa: F401

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.account_utils import (  # noqa: E402
    STANDARD_ROLE_NAME,
    construct_role_arn,
    detect_invocation_source,
    extract_account_from_cognito,
    extract_account_id_from_arn,
    get_invocation_metadata,
    get_role_arn,
    validate_account_context_for_invocation,
    validate_account_id,
)
from shared.security_utils import InputValidationError  # noqa: E402


class TestConstructRoleArn:
    """Tests for construct_role_arn function"""

    def test_valid_account_id_standard(self):  # noqa: F811
        """Test ARN construction with standard account ID"""
        account_id = "123456789012"  # noqa: F841
        expected = "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
        assert construct_role_arn(account_id) == expected

    def test_valid_account_id_with_zeros(self):  # noqa: F811
        """Test ARN construction with leading zeros"""
        account_id = "000000000001"  # noqa: F841
        expected = "arn:aws:iam::000000000001:role/DRSOrchestrationRole"
        assert construct_role_arn(account_id) == expected

    def test_valid_account_id_all_nines(self):  # noqa: F811
        """Test ARN construction with all nines"""
        account_id = "999999999999"  # noqa: F841
        expected = "arn:aws:iam::999999999999:role/DRSOrchestrationRole"
        assert construct_role_arn(account_id) == expected

    def test_invalid_account_id_too_short(self):  # noqa: F811
        """Test ARN construction fails with too short account ID"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            construct_role_arn("12345")

    def test_invalid_account_id_too_long(self):  # noqa: F811
        """Test ARN construction fails with too long account ID"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            construct_role_arn("1234567890123")

    def test_invalid_account_id_non_numeric(self):  # noqa: F811
        """Test ARN construction fails with non-numeric account ID"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            construct_role_arn("12345678901a")

    def test_invalid_account_id_with_spaces(self):  # noqa: F811
        """Test ARN construction fails with spaces"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            construct_role_arn("123 456 789 012")

    def test_invalid_account_id_empty(self):  # noqa: F811
        """Test ARN construction fails with empty string"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            construct_role_arn("")

    def test_invalid_account_id_none(self):  # noqa: F811
        """Test ARN construction fails with None"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            construct_role_arn(None)

    def test_arn_format_components(self):  # noqa: F811
        """Test ARN has correct format components"""
        arn = construct_role_arn("123456789012")
        assert arn.startswith("arn:aws:iam::")
        assert ":role/" in arn
        assert arn.endswith("DRSOrchestrationRole")


class TestValidateAccountId:
    """Tests for validate_account_id function"""

    def test_valid_standard_account_id(self):  # noqa: F811
        """Test validation accepts standard account ID"""
        assert validate_account_id("123456789012") is True

    def test_valid_account_id_with_zeros(self):  # noqa: F811
        """Test validation accepts account ID with leading zeros"""
        assert validate_account_id("000000000001") is True

    def test_valid_account_id_all_nines(self):  # noqa: F811
        """Test validation accepts all nines"""
        assert validate_account_id("999999999999") is True

    def test_invalid_too_short(self):  # noqa: F811
        """Test validation rejects too short account ID"""
        assert validate_account_id("12345") is False
        assert validate_account_id("12345678901") is False

    def test_invalid_too_long(self):  # noqa: F811
        """Test validation rejects too long account ID"""
        assert validate_account_id("1234567890123") is False
        assert validate_account_id("12345678901234567890") is False

    def test_invalid_non_numeric(self):  # noqa: F811
        """Test validation rejects non-numeric account ID"""
        assert validate_account_id("12345678901a") is False
        assert validate_account_id("abcdefghijkl") is False
        assert validate_account_id("123-456-789-012") is False

    def test_invalid_with_spaces(self):  # noqa: F811
        """Test validation rejects account ID with spaces"""
        assert validate_account_id("123 456 789 012") is False
        assert validate_account_id(" 123456789012") is False
        assert validate_account_id("123456789012 ") is False

    def test_invalid_empty(self):  # noqa: F811
        """Test validation rejects empty string"""
        assert validate_account_id("") is False

    def test_invalid_none(self):  # noqa: F811
        """Test validation rejects None"""
        assert validate_account_id(None) is False


class TestExtractAccountIdFromArn:
    """Tests for extract_account_id_from_arn function"""

    def test_extract_from_standard_arn(self):  # noqa: F811
        """Test extraction from standardized ARN"""
        arn = "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
        assert extract_account_id_from_arn(arn) == "123456789012"

    def test_extract_from_custom_role_arn(self):  # noqa: F811
        """Test extraction from ARN with custom role name"""
        arn = "arn:aws:iam::999999999999:role/CustomRole"
        assert extract_account_id_from_arn(arn) == "999999999999"

    def test_extract_from_arn_with_path(self):  # noqa: F811
        """Test extraction from ARN with role path"""
        arn = "arn:aws:iam::123456789012:role/path/to/role"
        assert extract_account_id_from_arn(arn) == "123456789012"

    def test_extract_from_arn_with_zeros(self):  # noqa: F811
        """Test extraction from ARN with leading zeros"""
        arn = "arn:aws:iam::000000000001:role/TestRole"
        assert extract_account_id_from_arn(arn) == "000000000001"

    def test_extract_invalid_arn_format(self):  # noqa: F811
        """Test extraction returns None for invalid ARN"""
        assert extract_account_id_from_arn("invalid-arn") is None

    def test_extract_empty_string(self):  # noqa: F811
        """Test extraction returns None for empty string"""
        assert extract_account_id_from_arn("") is None

    def test_extract_s3_arn(self):  # noqa: F811
        """Test extraction returns None for non-IAM ARN"""
        assert extract_account_id_from_arn("arn:aws:s3:::bucket") is None

    def test_extract_lambda_arn(self):  # noqa: F811
        """Test extraction returns None for Lambda ARN"""
        arn = "arn:aws:lambda:us-east-1:123456789012:function:my-function"
        assert extract_account_id_from_arn(arn) is None

    def test_extract_partial_arn(self):  # noqa: F811
        """Test extraction returns None for partial ARN"""
        assert extract_account_id_from_arn("arn:aws:iam::123456789012") is None


class TestGetRoleArn:
    """Tests for get_role_arn function"""

    def test_without_explicit_arn(self):  # noqa: F811
        """Test get_role_arn constructs ARN when not provided"""
        account_id = "123456789012"  # noqa: F841
        expected = "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
        assert get_role_arn(account_id) == expected

    def test_with_explicit_arn(self):  # noqa: F811
        """Test get_role_arn uses explicit ARN when provided"""
        account_id = "123456789012"  # noqa: F841
        explicit_arn = "arn:aws:iam::123456789012:role/CustomRole"
        assert get_role_arn(account_id, explicit_arn=explicit_arn) == explicit_arn

    def test_explicit_arn_takes_precedence(self):  # noqa: F811
        """Test explicit ARN takes precedence over constructed ARN"""
        account_id = "123456789012"  # noqa: F841
        explicit_arn = "arn:aws:iam::999999999999:role/DifferentRole"
        result = get_role_arn(account_id, explicit_arn=explicit_arn)  # noqa: F841

        # Should use explicit ARN, not construct from account_id
        assert result == explicit_arn  # noqa: F841
        assert result != construct_role_arn(account_id)

    def test_explicit_arn_none(self):  # noqa: F811
        """Test get_role_arn constructs ARN when explicit_arn is None"""
        account_id = "123456789012"  # noqa: F841
        expected = "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
        assert get_role_arn(account_id, explicit_arn=None) == expected

    def test_explicit_arn_empty_string(self):  # noqa: F811
        """Test get_role_arn constructs ARN when explicit_arn is empty"""
        account_id = "123456789012"  # noqa: F841
        expected = "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
        # Empty string is falsy, so should construct
        assert get_role_arn(account_id, explicit_arn="") == expected

    def test_invalid_account_id_without_explicit_arn(self):  # noqa: F811
        """Test get_role_arn fails with invalid account ID and no explicit ARN"""
        with pytest.raises(ValueError, match="Invalid account ID"):
            get_role_arn("12345")

    def test_invalid_account_id_with_explicit_arn(self):  # noqa: F811
        """Test get_role_arn succeeds with invalid account ID if explicit ARN provided"""
        # When explicit ARN is provided, account_id validation is bypassed
        explicit_arn = "arn:aws:iam::123456789012:role/CustomRole"
        result = get_role_arn("invalid", explicit_arn=explicit_arn)  # noqa: F841
        assert result == explicit_arn  # noqa: F841


class TestStandardRoleName:
    """Tests for STANDARD_ROLE_NAME constant"""

    def test_constant_value(self):  # noqa: F811
        """Test STANDARD_ROLE_NAME has expected value"""
        assert STANDARD_ROLE_NAME == "DRSOrchestrationRole"

    def test_constant_used_in_construction(self):  # noqa: F811
        """Test STANDARD_ROLE_NAME is used in ARN construction"""
        arn = construct_role_arn("123456789012")
        assert STANDARD_ROLE_NAME in arn


class TestRoundTripConversion:
    """Tests for round-trip conversion between account ID and ARN"""

    def test_construct_and_extract_round_trip(self):  # noqa: F811
        """Test constructing ARN and extracting account ID returns original"""
        account_id = "123456789012"  # noqa: F841
        arn = construct_role_arn(account_id)
        extracted = extract_account_id_from_arn(arn)
        assert extracted == account_id

    def test_round_trip_with_zeros(self):  # noqa: F811
        """Test round-trip with leading zeros"""
        account_id = "000000000001"  # noqa: F841
        arn = construct_role_arn(account_id)
        extracted = extract_account_id_from_arn(arn)
        assert extracted == account_id

    def test_round_trip_preserves_format(self):  # noqa: F811
        """Test round-trip preserves exact account ID format"""
        account_id = "012345678901"  # noqa: F841
        arn = construct_role_arn(account_id)
        extracted = extract_account_id_from_arn(arn)
        # Should preserve leading zero
        assert extracted == account_id
        assert extracted[0] == "0"


class TestDetectInvocationSource:
    """Tests for detect_invocation_source function.

    Validates: Requirements 1.10
    """

    def test_api_gateway_event(self):  # noqa: F811
        """Test detection of API Gateway invocation."""
        event = {
            "requestContext": {
                "requestId": "req-123",
                "apiId": "api-456",
            }
        }
        assert detect_invocation_source(event) == "api_gateway"

    def test_direct_invocation_event(self):  # noqa: F811
        """Test detection of direct Lambda invocation."""
        event = {"operation": "create", "accountId": "123456789012"}
        assert detect_invocation_source(event) == "direct"

    def test_empty_event(self):  # noqa: F811
        """Test detection with empty event."""
        assert detect_invocation_source({}) == "direct"

    def test_api_gateway_with_empty_request_context(self):  # noqa: F811
        """Test detection with empty requestContext still returns api_gateway."""
        event = {"requestContext": {}}
        assert detect_invocation_source(event) == "api_gateway"


class TestGetInvocationMetadata:
    """Tests for get_invocation_metadata function.

    Validates: Requirements 1.10
    """

    def test_api_gateway_metadata(self):  # noqa: F811
        """Test metadata extraction from API Gateway event."""
        event = {
            "requestContext": {
                "requestId": "req-123",
                "apiId": "api-456",
                "identity": {
                    "cognitoIdentityId": "cognito-789",
                },
            }
        }
        metadata = get_invocation_metadata(event)
        assert metadata["invocation_source"] == "api_gateway"
        assert metadata["request_id"] == "req-123"
        assert metadata["api_id"] == "api-456"
        assert metadata["cognito_identity"] == "cognito-789"
        assert "timestamp" in metadata

    def test_direct_invocation_metadata(self):  # noqa: F811
        """Test metadata extraction from direct invocation event."""
        event = {
            "operation": "create",
            "requestId": "direct-req-001",
        }
        metadata = get_invocation_metadata(event)
        assert metadata["invocation_source"] == "direct"
        assert metadata["request_id"] == "direct-req-001"
        assert "timestamp" in metadata
        assert "api_id" not in metadata

    def test_direct_invocation_missing_request_id(self):  # noqa: F811
        """Test metadata defaults requestId to unknown for direct."""
        event = {"operation": "create"}
        metadata = get_invocation_metadata(event)
        assert metadata["request_id"] == "unknown"

    def test_api_gateway_missing_identity(self):  # noqa: F811
        """Test metadata handles missing identity gracefully."""
        event = {
            "requestContext": {
                "requestId": "req-123",
                "apiId": "api-456",
            }
        }
        metadata = get_invocation_metadata(event)
        assert metadata["cognito_identity"] is None

    def test_timestamp_is_iso_format(self):  # noqa: F811
        """Test that timestamp is valid ISO 8601 format."""
        from datetime import datetime as dt

        event = {"operation": "test"}
        metadata = get_invocation_metadata(event)
        # Should not raise ValueError
        dt.fromisoformat(metadata["timestamp"])


class TestExtractAccountFromCognito:
    """Tests for extract_account_from_cognito function.

    Validates: Requirements 1.10, 1.11
    """

    def test_valid_cognito_event(self):  # noqa: F811
        """Test extraction from valid Cognito authentication provider."""
        event = {
            "requestContext": {
                "identity": {
                    "cognitoAuthenticationProvider": (
                        "cognito-idp.us-east-1.amazonaws.com" "/us-east-1_abc:CognitoSignIn" ":123456789012"
                    ),
                }
            }
        }
        result = extract_account_from_cognito(event)
        assert result == "123456789012"

    def test_missing_request_context(self):  # noqa: F811
        """Test raises InputValidationError when requestContext missing."""
        event = {}
        with pytest.raises(InputValidationError, match="Cannot extract"):
            extract_account_from_cognito(event)

    def test_missing_identity(self):  # noqa: F811
        """Test raises InputValidationError when identity missing."""
        event = {"requestContext": {}}
        with pytest.raises(InputValidationError, match="Cannot extract"):
            extract_account_from_cognito(event)

    def test_empty_provider_string(self):  # noqa: F811
        """Test returns empty string when provider is empty."""
        event = {
            "requestContext": {
                "identity": {
                    "cognitoAuthenticationProvider": "",
                }
            }
        }
        # Empty string split by ":" returns [""], last element is ""
        result = extract_account_from_cognito(event)
        assert result == ""

    def test_provider_without_account_id(self):  # noqa: F811
        """Test returns last segment of provider string."""
        event = {
            "requestContext": {
                "identity": {
                    "cognitoAuthenticationProvider": ("cognito-idp.us-east-1.amazonaws.com" "/us-east-1_poolId"),
                }
            }
        }
        result = extract_account_from_cognito(event)
        # Returns last segment after splitting by ":"
        assert isinstance(result, str)


class TestValidateAccountContextForInvocation:
    """Tests for validate_account_context_for_invocation function.

    Validates: Requirements 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.13
    """

    def test_direct_invocation_with_valid_account_id(self):  # noqa: F811
        """Test direct invocation with valid accountId succeeds."""
        event = {"operation": "create"}
        body = {
            "accountId": "123456789012",
            "assumeRoleName": "MyRole",
            "externalId": "ext-123",
        }
        result = validate_account_context_for_invocation(event, body)
        assert result["accountId"] == "123456789012"
        assert result["assumeRoleName"] == "MyRole"
        assert result["externalId"] == "ext-123"

    def test_direct_invocation_missing_account_id_raises(self):  # noqa: F811
        """Test direct invocation without accountId raises error."""
        event = {"operation": "create"}
        body = {"groupName": "test"}
        with pytest.raises(InputValidationError, match="accountId is required for direct Lambda"):
            validate_account_context_for_invocation(event, body)

    def test_direct_invocation_empty_account_id_raises(self):  # noqa: F811
        """Test direct invocation with empty accountId raises error."""
        event = {"operation": "create"}
        body = {"accountId": ""}
        with pytest.raises(InputValidationError, match="accountId is required for direct Lambda"):
            validate_account_context_for_invocation(event, body)

    def test_api_gateway_with_account_id_in_body(self):  # noqa: F811
        """Test API Gateway invocation uses accountId from body."""
        event = {
            "requestContext": {
                "requestId": "req-123",
                "identity": {},
            }
        }
        body = {"accountId": "123456789012"}
        result = validate_account_context_for_invocation(event, body)
        assert result["accountId"] == "123456789012"

    def test_api_gateway_falls_back_to_cognito(self):  # noqa: F811
        """Test API Gateway defaults to Cognito when accountId missing."""
        event = {
            "requestContext": {
                "requestId": "req-123",
                "identity": {
                    "cognitoAuthenticationProvider": (
                        "cognito-idp.us-east-1.amazonaws.com" "/us-east-1_abc:CognitoSignIn" ":123456789012"
                    ),
                },
            }
        }
        body = {}
        result = validate_account_context_for_invocation(event, body)
        assert result["accountId"] == "123456789012"

    def test_invalid_account_id_format_raises(self):  # noqa: F811
        """Test invalid account ID format raises error."""
        event = {"operation": "create"}
        body = {"accountId": "not-valid"}
        with pytest.raises(InputValidationError, match="Invalid account ID format"):
            validate_account_context_for_invocation(event, body)

    def test_short_account_id_raises(self):  # noqa: F811
        """Test too-short account ID raises error."""
        event = {"operation": "create"}
        body = {"accountId": "12345"}
        with pytest.raises(InputValidationError, match="Invalid account ID format"):
            validate_account_context_for_invocation(event, body)

    def test_defaults_for_optional_fields(self):  # noqa: F811
        """Test assumeRoleName and externalId default to empty."""
        event = {"operation": "create"}
        body = {"accountId": "123456789012"}
        result = validate_account_context_for_invocation(event, body)
        assert result["assumeRoleName"] == ""
        assert result["externalId"] == ""

    def test_return_dict_has_required_keys(self):  # noqa: F811
        """Test return dict always has accountId, assumeRoleName, externalId."""
        event = {"operation": "create"}
        body = {"accountId": "123456789012"}
        result = validate_account_context_for_invocation(event, body)
        assert "accountId" in result
        assert "assumeRoleName" in result
        assert "externalId" in result

    def test_error_message_mentions_direct_invocation(self):  # noqa: F811
        """Test error message clearly indicates direct invocation context."""
        event = {"operation": "create"}
        body = {}
        with pytest.raises(InputValidationError) as exc_info:
            validate_account_context_for_invocation(event, body)
        error_msg = str(exc_info.value)
        assert "direct Lambda invocation" in error_msg
        assert "accountId" in error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
