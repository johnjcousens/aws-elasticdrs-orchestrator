"""
Unit tests for lambda/shared/security_utils.py

Tests the three core security functions:
1. sanitize_string() - Input sanitization
2. validate_drs_server_id() - DRS server ID validation
3. sanitize_dynamodb_input() - DynamoDB input sanitization

Validates: Requirements FR1, FR5 (Verify Existing Shared Utilities)
"""

import os
import sys

import pytest

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.security_utils import (  # noqa: E402
    InputValidationError,
    sanitize_dynamodb_input,
    sanitize_string,
    validate_drs_server_id,
)


class TestSanitizeString:
    """Test sanitize_string() function"""

    def test_sanitize_string_removes_dangerous_characters(self):
        """Test that dangerous characters are removed"""
        # XSS attempt
        result = sanitize_string("<script>alert('xss')</script>")
        assert "<" not in result
        assert ">" not in result
        assert "script" in result

        # SQL injection attempt
        result = sanitize_string("'; DROP TABLE users; --")
        assert ";" not in result
        assert "'" not in result

    def test_sanitize_string_removes_control_characters(self):
        """Test that control characters are removed"""
        # Null byte
        result = sanitize_string("test\x00string")
        assert "\x00" not in result
        assert result == "teststring"

        # Other control characters
        result = sanitize_string("test\x01\x02\x03string")
        assert result == "teststring"

    def test_sanitize_string_preserves_safe_strings(self):
        """Test that safe strings are preserved"""
        safe_strings = [
            "server-123",
            "test_value",
            "plan.name",
            "region:us-east-1",
            "alphanumeric123",
        ]

        for safe_str in safe_strings:
            result = sanitize_string(safe_str)
            assert result == safe_str

    def test_sanitize_string_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped"""
        result = sanitize_string("  test  ")
        assert result == "test"

        result = sanitize_string("\t\ntest\t\n")
        assert result == "test"

    def test_sanitize_string_enforces_max_length(self):
        """Test that max_length is enforced"""
        long_string = "a" * 300

        with pytest.raises(InputValidationError) as exc_info:
            sanitize_string(long_string, max_length=255)

        assert "exceeds maximum length" in str(exc_info.value)

    def test_sanitize_string_custom_max_length(self):
        """Test custom max_length parameter"""
        result = sanitize_string("test", max_length=10)
        assert result == "test"

        with pytest.raises(InputValidationError):
            sanitize_string("test string", max_length=5)

    def test_sanitize_string_rejects_non_string_input(self):
        """Test that non-string input is rejected"""
        with pytest.raises(InputValidationError) as exc_info:
            sanitize_string(123)

        assert "must be a string" in str(exc_info.value)

        with pytest.raises(InputValidationError):
            sanitize_string(None)

        with pytest.raises(InputValidationError):
            sanitize_string(["list"])

    def test_sanitize_string_performance_optimization_safe_strings(self):
        """Test performance optimization for safe alphanumeric strings"""
        # Safe strings should skip expensive regex processing
        safe_strings = [
            "server123",
            "test-value",
            "plan_name",
            "region.us-east-1",
        ]

        for safe_str in safe_strings:
            result = sanitize_string(safe_str)
            assert result == safe_str

    def test_sanitize_string_performance_optimization_large_strings(self):
        """Test that large strings (>1000 chars) skip sanitization"""
        # Large safe string
        large_safe = "a" * 1500
        result = sanitize_string(large_safe, max_length=2000)
        assert result == large_safe

    def test_sanitize_string_handles_empty_string(self):
        """Test handling of empty strings"""
        result = sanitize_string("")
        assert result == ""

        result = sanitize_string("   ")
        assert result == ""

    def test_sanitize_string_removes_backslashes(self):
        """Test that backslashes are removed"""
        result = sanitize_string("test\\string")
        assert "\\" not in result
        assert result == "teststring"

    def test_sanitize_string_removes_quotes(self):
        """Test that quotes are removed"""
        result = sanitize_string('test"string')
        assert '"' not in result

        result = sanitize_string("test'string")
        assert "'" not in result


class TestValidateDrsServerId:
    """Test validate_drs_server_id() function"""

    def test_validate_drs_server_id_valid_format(self):
        """Test valid DRS server ID format"""
        # Valid DRS server IDs (s- followed by 17 hex chars)
        valid_ids = [
            "s-0123456789abcdef0",
            "s-abcdef0123456789a",
            "s-ffffffffffffffff0",
            "s-00000000000000000",
        ]

        for server_id in valid_ids:
            assert validate_drs_server_id(server_id) is True

    def test_validate_drs_server_id_invalid_prefix(self):
        """Test invalid prefix"""
        invalid_ids = [
            "i-0123456789abcdef0",  # EC2 instance ID
            "x-0123456789abcdef0",  # Wrong prefix
            "0123456789abcdef0",  # No prefix
            "s0123456789abcdef0",  # Missing hyphen
        ]

        for server_id in invalid_ids:
            assert validate_drs_server_id(server_id) is False

    def test_validate_drs_server_id_invalid_length(self):
        """Test invalid length"""
        invalid_ids = [
            "s-0123456789abcdef",  # Too short (16 chars)
            "s-0123456789abcdef00",  # Too long (18 chars)
            "s-0123456789",  # Way too short
            "s-0123456789abcdef0123456789",  # Way too long
        ]

        for server_id in invalid_ids:
            assert validate_drs_server_id(server_id) is False

    def test_validate_drs_server_id_invalid_characters(self):
        """Test invalid characters (non-hex)"""
        invalid_ids = [
            "s-0123456789abcdefg",  # 'g' is not hex
            "s-0123456789ABCDEF0",  # Uppercase not allowed
            "s-0123456789abcdef!",  # Special character
            "s-0123456789abcdef ",  # Space
        ]

        for server_id in invalid_ids:
            assert validate_drs_server_id(server_id) is False

    def test_validate_drs_server_id_non_string_input(self):
        """Test non-string input"""
        assert validate_drs_server_id(123) is False
        assert validate_drs_server_id(None) is False
        assert validate_drs_server_id(["s-0123456789abcdef0"]) is False
        assert validate_drs_server_id({"id": "s-0123456789abcdef0"}) is False

    def test_validate_drs_server_id_empty_string(self):
        """Test empty string"""
        assert validate_drs_server_id("") is False

    def test_validate_drs_server_id_case_sensitivity(self):
        """Test that validation is case-sensitive (lowercase only)"""
        # Lowercase hex is valid
        assert validate_drs_server_id("s-0123456789abcdef0") is True

        # Uppercase hex is invalid
        assert validate_drs_server_id("s-0123456789ABCDEF0") is False

        # Mixed case is invalid
        assert validate_drs_server_id("s-0123456789AbCdEf0") is False


class TestSanitizeDynamodbInput:
    """Test sanitize_dynamodb_input() function"""

    def test_sanitize_dynamodb_input_sanitizes_string_values(self):
        """Test that string values are sanitized"""
        data = {
            "planName": "<script>alert('xss')</script>",
            "description": "Test'; DROP TABLE users; --",
        }

        result = sanitize_dynamodb_input(data)

        assert "<" not in result["planName"]
        assert ">" not in result["planName"]
        assert ";" not in result["description"]
        assert "'" not in result["description"]

    def test_sanitize_dynamodb_input_preserves_numeric_types(self):
        """Test that numeric types are preserved"""
        data = {
            "waveNumber": 1,
            "serverCount": 42,
            "progress": 75.5,
            "isActive": True,
            "isComplete": False,
        }

        result = sanitize_dynamodb_input(data)

        assert result["waveNumber"] == 1
        assert result["serverCount"] == 42
        assert result["progress"] == 75.5
        assert result["isActive"] is True
        assert result["isComplete"] is False

    def test_sanitize_dynamodb_input_handles_nested_dicts(self):
        """Test that nested dictionaries are sanitized recursively"""
        # Use keys that are NOT in the skip list
        data = {
            "customData": {
                "name": "<script>test</script>",
                "metadata": {"field1": {"name": "Wave'; DROP TABLE"}},
            }
        }

        result = sanitize_dynamodb_input(data)

        assert "<" not in result["customData"]["name"]
        assert ";" not in result["customData"]["metadata"]["field1"]["name"]

    def test_sanitize_dynamodb_input_handles_lists(self):
        """Test that lists are sanitized"""
        data = {
            "servers": [
                "s-0123456789abcdef0",
                "<script>alert('xss')</script>",
            ],
            "tags": ["tag1", "tag2"],
        }

        result = sanitize_dynamodb_input(data)

        assert result["servers"][0] == "s-0123456789abcdef0"
        assert "<" not in result["servers"][1]
        assert result["tags"] == ["tag1", "tag2"]

    def test_sanitize_dynamodb_input_handles_none_values(self):
        """Test that None values are preserved"""
        data = {"optionalField": None, "requiredField": "value"}

        result = sanitize_dynamodb_input(data)

        assert result["optionalField"] is None
        assert result["requiredField"] == "value"

    def test_sanitize_dynamodb_input_sanitizes_keys(self):
        """Test that dictionary keys are sanitized"""
        data = {"<script>key</script>": "value"}

        result = sanitize_dynamodb_input(data)

        # Key should be sanitized
        assert "<script>key</script>" not in result
        assert "scriptkey/script" in result or "scriptkeyscript" in result

    def test_sanitize_dynamodb_input_rejects_empty_keys(self):
        """Test that empty keys are rejected"""
        data = {"": "value"}

        with pytest.raises(InputValidationError) as exc_info:
            sanitize_dynamodb_input(data)

        assert "Invalid key" in str(exc_info.value)

    def test_sanitize_dynamodb_input_rejects_non_string_keys(self):
        """Test that non-string keys are rejected"""
        data = {123: "value"}

        with pytest.raises(InputValidationError) as exc_info:
            sanitize_dynamodb_input(data)

        assert "Invalid key" in str(exc_info.value)

    def test_sanitize_dynamodb_input_performance_optimization_safe_keys(
        self,
    ):
        """Test performance optimization for safe execution keys"""
        # These keys should skip sanitization
        data = {
            "executionId": "exec-123",
            "planId": "plan-456",
            "status": "IN_PROGRESS",
            "region": "us-east-1",
            "waves": [{"waveNumber": 1}],
            "enrichedServers": [{"serverId": "s-123"}],
            "stateMachineArn": "arn:aws:states:...",
            "createdAt": "2025-01-01T00:00:00Z",
            "updatedAt": "2025-01-01T00:00:00Z",
            "startTime": "2025-01-01T00:00:00Z",
            "endTime": "2025-01-01T00:00:00Z",
        }

        result = sanitize_dynamodb_input(data)

        # All values should be preserved unchanged
        assert result == data

    def test_sanitize_dynamodb_input_performance_optimization_large_objects(
        self,
    ):
        """Test performance optimization for large execution data"""
        # Large execution data (>50 fields) should skip deep sanitization
        data = {
            "executionId": "exec-123",
            "planId": "plan-456",
            "status": "IN_PROGRESS",
        }

        # Add 50+ fields to trigger optimization
        for i in range(60):
            data[f"field{i}"] = f"value{i}"

        result = sanitize_dynamodb_input(data)

        # Should return data unchanged (minimal sanitization)
        assert result == data

    def test_sanitize_dynamodb_input_performance_optimization_large_strings(
        self,
    ):
        """Test that large strings (>1000 chars) skip sanitization"""
        data = {"largeField": "a" * 1500}

        result = sanitize_dynamodb_input(data)

        # Large string should be preserved unchanged
        assert result["largeField"] == "a" * 1500

    def test_sanitize_dynamodb_input_performance_optimization_large_lists(
        self,
    ):
        """Test that large lists (>20 items) skip deep sanitization"""
        data = {"servers": [f"server-{i}" for i in range(30)]}

        result = sanitize_dynamodb_input(data)

        # Large list should be preserved unchanged
        assert result["servers"] == data["servers"]

    def test_sanitize_dynamodb_input_handles_list_of_dicts(self):
        """Test that lists of dictionaries are sanitized"""
        # Use a key that is NOT in the skip list
        data = {
            "items": [
                {"waveNumber": 1, "name": "<script>Wave 1</script>"},
                {"waveNumber": 2, "name": "Wave 2"},
            ]
        }

        result = sanitize_dynamodb_input(data)

        assert "<" not in result["items"][0]["name"]
        assert result["items"][1]["name"] == "Wave 2"

    def test_sanitize_dynamodb_input_preserves_data_types(self):
        """Test that all data types are preserved correctly"""
        data = {
            "string": "test",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }

        result = sanitize_dynamodb_input(data)

        assert isinstance(result["string"], str)
        assert isinstance(result["integer"], int)
        assert isinstance(result["float"], float)
        assert isinstance(result["boolean"], bool)
        assert result["none"] is None
        assert isinstance(result["list"], list)
        assert isinstance(result["dict"], dict)

    def test_sanitize_dynamodb_input_handles_bytes(self):
        """Test that bytes are converted to sanitized strings"""
        data = {"binaryData": b"test data"}

        result = sanitize_dynamodb_input(data)

        # Bytes should be converted to string and sanitized
        assert isinstance(result["binaryData"], str)
        assert "test data" in result["binaryData"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
