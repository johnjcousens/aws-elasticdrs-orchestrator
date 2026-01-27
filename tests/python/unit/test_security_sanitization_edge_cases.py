"""
Unit tests for Security Sanitization Edge Cases

Tests to ensure security utilities don't break legitimate inputs while
still blocking malicious ones. Focuses on real-world data patterns that
should pass through sanitization unchanged.
"""

import json
import os
import sys

import pytest

# Add lambda/shared directory to path for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "lambda", "shared"
    ),
)

from security_utils import (
    InputValidationError,
    sanitize_dynamodb_input,
    sanitize_string,
)


class TestLegitimateInputsNotBroken:
    """Test that legitimate inputs pass through sanitization correctly."""

    def test_aws_arns_preserved(self):
        """AWS ARNs should pass through unchanged."""
        arn = "arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0"
        result = sanitize_string(arn, max_length=512)
        assert result == arn

    def test_aws_resource_ids_preserved(self):
        """AWS resource IDs should pass through unchanged."""
        # DRS server ID
        server_id = "s-1234567890abcdef0"
        assert sanitize_string(server_id, max_length=64) == server_id

        # EC2 instance ID
        instance_id = "i-1234567890abcdef0"
        assert sanitize_string(instance_id, max_length=64) == instance_id

        # VPC ID
        vpc_id = "vpc-1234567890abcdef0"
        assert sanitize_string(vpc_id, max_length=64) == vpc_id

    def test_ip_addresses_preserved(self):
        """IP addresses should pass through unchanged."""
        ipv4 = "192.168.1.100"
        assert sanitize_string(ipv4, max_length=64) == ipv4

        ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        assert sanitize_string(ipv6, max_length=64) == ipv6

    def test_cidr_blocks_preserved(self):
        """CIDR blocks should pass through unchanged."""
        cidr = "10.0.0.0/16"
        assert sanitize_string(cidr, max_length=64) == cidr

    def test_dns_names_preserved(self):
        """DNS names should pass through unchanged."""
        dns = "ec2-54-123-45-67.compute-1.amazonaws.com"
        assert sanitize_string(dns, max_length=256) == dns

    def test_email_addresses_preserved(self):
        """Email addresses should pass through unchanged."""
        email = "user@example.com"
        assert sanitize_string(email, max_length=256) == email

        email_with_plus = "user+tag@example.com"
        assert sanitize_string(email_with_plus, max_length=256) == email_with_plus

    def test_urls_preserved(self):
        """URLs should pass through unchanged."""
        url = "https://example.com/path/to/resource"
        assert sanitize_string(url, max_length=512) == url

    def test_timestamps_preserved(self):
        """ISO 8601 timestamps should pass through unchanged."""
        timestamp = "2025-01-17T12:34:56.789Z"
        assert sanitize_string(timestamp, max_length=64) == timestamp

    def test_uuids_preserved(self):
        """UUIDs should pass through unchanged."""
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert sanitize_string(uuid, max_length=64) == uuid

    def test_json_strings_preserved(self):
        """JSON strings should pass through unchanged (when not containing dangerous chars)."""
        # Simple JSON without quotes in values
        json_str = '{"key":"value","number":42}'
        # Note: sanitize_string will remove quotes, so we test with validate_json_input instead
        from security_utils import validate_json_input
        result = validate_json_input(json_str)
        assert result == {"key": "value", "number": 42}

    def test_base64_encoded_data_preserved(self):
        """Base64 encoded data should pass through unchanged."""
        base64_data = "SGVsbG8gV29ybGQh"
        assert sanitize_string(base64_data, max_length=256) == base64_data

    def test_aws_tags_preserved(self):
        """AWS tag key-value pairs should pass through unchanged."""
        tag_key = "aws:cloudformation:stack-name"
        assert sanitize_string(tag_key, max_length=128) == tag_key

        tag_value = "aws-drs-orch-dev"
        assert sanitize_string(tag_value, max_length=256) == tag_value

    def test_file_paths_preserved(self):
        """Legitimate file paths should pass through unchanged."""
        # Lambda paths
        lambda_path = "/var/task/lambda/api-handler/index.py"
        assert sanitize_string(lambda_path, max_length=512) == lambda_path

        # Relative paths
        relative_path = "./frontend/dist/index.html"
        assert sanitize_string(relative_path, max_length=512) == relative_path

    def test_version_numbers_preserved(self):
        """Version numbers should pass through unchanged."""
        version = "1.2.3"
        assert sanitize_string(version, max_length=64) == version

        semver = "2.0.0-beta.1"
        assert sanitize_string(semver, max_length=64) == semver

    def test_aws_region_names_preserved(self):
        """AWS region names should pass through unchanged."""
        regions = [
            "us-east-1",
            "us-west-2",
            "eu-west-1",
            "ap-southeast-1",
            "us-gov-west-1",
        ]
        for region in regions:
            assert sanitize_string(region, max_length=64) == region

    def test_numbers_as_strings_preserved(self):
        """Numeric strings should pass through unchanged."""
        number_str = "123456789"
        assert sanitize_string(number_str, max_length=64) == number_str

    def test_alphanumeric_with_hyphens_preserved(self):
        """Alphanumeric strings with hyphens should pass through unchanged."""
        name = "web-server-tier-1"
        assert sanitize_string(name, max_length=64) == name

    def test_alphanumeric_with_underscores_preserved(self):
        """Alphanumeric strings with underscores should pass through unchanged."""
        name = "web_server_tier_1"
        assert sanitize_string(name, max_length=64) == name


class TestDynamoDBInputPreservation:
    """Test that DynamoDB inputs preserve data types and structure."""

    def test_preserves_execution_data_structure(self):
        """Large execution data should pass through with minimal sanitization."""
        execution_data = {
            "executionId": "550e8400-e29b-41d4-a716-446655440000",
            "planId": "plan-123",
            "status": "IN_PROGRESS",
            "region": "us-east-1",
            "waves": [
                {
                    "waveId": "wave-1",
                    "priority": 1,
                    "servers": ["s-1234567890abcdef0", "s-0987654321fedcba0"],
                }
            ],
            "enrichedServers": [
                {
                    "sourceServerID": "s-1234567890abcdef0",
                    "hostname": "web-server-01",
                    "ipAddress": "10.0.1.100",
                }
            ],
            "stateMachineArn": "arn:aws:states:us-east-1:123456789012:stateMachine:DROrchestrator",
            "createdAt": "2025-01-17T12:34:56.789Z",
        }

        result = sanitize_dynamodb_input(execution_data)

        # Verify structure preserved
        assert result["executionId"] == execution_data["executionId"]
        assert result["planId"] == execution_data["planId"]
        assert result["status"] == execution_data["status"]
        assert result["region"] == execution_data["region"]
        assert len(result["waves"]) == 1
        assert len(result["enrichedServers"]) == 1
        assert result["stateMachineArn"] == execution_data["stateMachineArn"]

    def test_preserves_numeric_types(self):
        """Numeric types should remain as numbers, not converted to strings."""
        data = {
            "count": 42,
            "price": 19.99,
            "percentage": 0.75,
            "negative": -10,
        }

        result = sanitize_dynamodb_input(data)

        assert isinstance(result["count"], int)
        assert result["count"] == 42
        assert isinstance(result["price"], float)
        assert result["price"] == 19.99
        assert isinstance(result["percentage"], float)
        assert isinstance(result["negative"], int)

    def test_preserves_boolean_types(self):
        """Boolean types should remain as booleans, not converted to strings."""
        data = {
            "active": True,
            "deleted": False,
            "enabled": True,
        }

        result = sanitize_dynamodb_input(data)

        assert isinstance(result["active"], bool)
        assert result["active"] is True
        assert isinstance(result["deleted"], bool)
        assert result["deleted"] is False

    def test_preserves_none_values(self):
        """None values should remain as None, not converted to strings."""
        data = {
            "optional_field": None,
            "nullable_value": None,
        }

        result = sanitize_dynamodb_input(data)

        assert result["optional_field"] is None
        assert result["nullable_value"] is None

    def test_preserves_nested_structure(self):
        """Nested dictionaries and lists should preserve structure."""
        data = {
            "metadata": {
                "version": "1.0",
                "author": "system",
                "tags": ["production", "critical"],
            },
            "config": {
                "timeout": 300,
                "retries": 3,
                "enabled": True,
            },
        }

        result = sanitize_dynamodb_input(data)

        assert isinstance(result["metadata"], dict)
        assert isinstance(result["metadata"]["tags"], list)
        assert len(result["metadata"]["tags"]) == 2
        assert isinstance(result["config"]["timeout"], int)
        assert isinstance(result["config"]["enabled"], bool)

    def test_preserves_large_lists(self):
        """Large lists should pass through without deep sanitization."""
        # Create a list with 50 items (exceeds the 20-item threshold)
        large_list = [f"server-{i}" for i in range(50)]
        data = {"servers": large_list}

        result = sanitize_dynamodb_input(data)

        assert len(result["servers"]) == 50
        assert result["servers"][0] == "server-0"
        assert result["servers"][49] == "server-49"

    def test_preserves_large_nested_objects(self):
        """Large nested objects should pass through without deep sanitization."""
        # Create a dict with 30 keys (exceeds the 20-key threshold)
        large_dict = {f"key{i}": f"value{i}" for i in range(30)}
        data = {"config": large_dict}

        result = sanitize_dynamodb_input(data)

        assert len(result["config"]) == 30
        assert result["config"]["key0"] == "value0"
        assert result["config"]["key29"] == "value29"


class TestMaliciousInputsBlocked:
    """Test that malicious inputs are properly sanitized."""

    def test_blocks_xss_attempts(self):
        """XSS attempts should be sanitized."""
        xss = "<script>alert('xss')</script>"
        result = sanitize_string(xss, max_length=256)
        assert "<" not in result
        assert ">" not in result
        assert "script" in result  # Text remains, tags removed

    def test_blocks_sql_injection_attempts(self):
        """SQL injection attempts should be sanitized."""
        sql = "'; DROP TABLE users; --"
        result = sanitize_string(sql, max_length=256)
        assert "'" not in result
        assert ";" not in result

    def test_blocks_command_injection_attempts(self):
        """Command injection attempts should be sanitized."""
        cmd = "test; rm -rf /"
        result = sanitize_string(cmd, max_length=256)
        assert ";" not in result

    def test_blocks_path_traversal_attempts(self):
        """Path traversal attempts should be sanitized."""
        path = "../../etc/passwd"
        result = sanitize_string(path, max_length=256)
        # Dots and slashes are allowed, but validate_file_path would catch this
        from security_utils import validate_file_path
        with pytest.raises(InputValidationError):
            validate_file_path(path)

    def test_blocks_null_byte_injection(self):
        """Null byte injection should be sanitized."""
        null_byte = "test\x00malicious"
        result = sanitize_string(null_byte, max_length=256)
        assert "\x00" not in result

    def test_blocks_control_characters(self):
        """Control characters should be removed."""
        control = "test\x1fmalicious\x7f"
        result = sanitize_string(control, max_length=256)
        assert "\x1f" not in result
        assert "\x7f" not in result


class TestEdgeCasesAndBoundaries:
    """Test edge cases and boundary conditions."""

    def test_empty_string_handled(self):
        """Empty string should be handled gracefully."""
        result = sanitize_string("", max_length=256)
        assert result == ""

    def test_whitespace_only_trimmed(self):
        """Whitespace-only strings should be trimmed."""
        result = sanitize_string("   ", max_length=256)
        assert result == ""

    def test_max_length_boundary(self):
        """Strings at max length should pass."""
        max_str = "a" * 255
        result = sanitize_string(max_str, max_length=255)
        assert len(result) == 255

    def test_exceeds_max_length_rejected(self):
        """Strings exceeding max length should be rejected."""
        too_long = "a" * 256
        with pytest.raises(InputValidationError):
            sanitize_string(too_long, max_length=255)

    def test_unicode_characters_preserved(self):
        """Unicode characters should be preserved."""
        unicode_str = "Hello 世界 🌍"
        result = sanitize_string(unicode_str, max_length=256)
        assert "世界" in result
        assert "🌍" in result

    def test_mixed_safe_and_dangerous_chars(self):
        """Mixed safe and dangerous characters should be partially sanitized."""
        mixed = "safe-value<script>dangerous</script>"
        result = sanitize_string(mixed, max_length=256)
        assert "safe-value" in result
        assert "<" not in result
        assert ">" not in result

    def test_performance_optimization_for_safe_strings(self):
        """Safe alphanumeric strings should use fast path."""
        # This tests the performance optimization in sanitize_string
        safe_str = "web-server-tier-1-production"
        result = sanitize_string(safe_str, max_length=256)
        assert result == safe_str

    def test_performance_optimization_for_large_safe_strings(self):
        """Large safe strings should skip expensive regex."""
        # Create a 500-char safe string
        safe_str = "a" * 500
        result = sanitize_string(safe_str, max_length=1000)
        assert result == safe_str


class TestRealWorldDataPatterns:
    """Test real-world data patterns from actual DRS operations."""

    def test_drs_job_id_preserved(self):
        """DRS job IDs should pass through unchanged."""
        job_id = "drsjob-1234567890abcdef0123456789abcdef"
        result = sanitize_string(job_id, max_length=128)
        assert result == job_id

    def test_cloudformation_stack_name_preserved(self):
        """CloudFormation stack names should pass through unchanged."""
        stack_name = "aws-drs-orch-dev"
        result = sanitize_string(stack_name, max_length=128)
        assert result == stack_name

    def test_lambda_function_name_preserved(self):
        """Lambda function names should pass through unchanged."""
        function_name = "aws-drs-orch-dev-api-handler"
        result = sanitize_string(function_name, max_length=128)
        assert function_name in result  # May have some chars removed

    def test_dynamodb_table_name_preserved(self):
        """DynamoDB table names should pass through unchanged."""
        table_name = "protection-groups-dev"
        result = sanitize_string(table_name, max_length=128)
        assert result == table_name

    def test_s3_bucket_name_preserved(self):
        """S3 bucket names should pass through unchanged."""
        bucket_name = "aws-drs-orch-dev"
        result = sanitize_string(bucket_name, max_length=128)
        assert result == bucket_name

    def test_api_gateway_path_preserved(self):
        """API Gateway paths should pass through unchanged."""
        path = "/api/v1/protection-groups"
        result = sanitize_string(path, max_length=256)
        assert result == path

    def test_cognito_user_pool_id_preserved(self):
        """Cognito User Pool IDs should pass through unchanged."""
        pool_id = "us-east-1_AbCdEfGhI"
        result = sanitize_string(pool_id, max_length=128)
        assert result == pool_id

    def test_step_functions_execution_arn_preserved(self):
        """Step Functions execution ARNs should pass through unchanged."""
        arn = "arn:aws:states:us-east-1:123456789012:execution:DROrchestrator:550e8400-e29b-41d4-a716-446655440000"
        result = sanitize_string(arn, max_length=512)
        assert result == arn

    def test_jwt_token_structure_preserved(self):
        """JWT token structure should pass through (though content may be sanitized)."""
        # Simplified JWT structure (real tokens have quotes which would be removed)
        jwt_header = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = sanitize_string(jwt_header, max_length=4096)
        assert result == jwt_header


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
