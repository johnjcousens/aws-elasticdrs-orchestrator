"""
Unit tests for Security Utilities

Tests input validation, sanitization, and security helper functions
used across the AWS DRS Orchestration platform.
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
    SecurityError,
    create_security_headers,
    mask_sensitive_data,
    sanitize_dynamodb_input,
    sanitize_string,
    validate_api_gateway_event,
    validate_aws_account_id,
    validate_aws_region,
    validate_drs_server_id,
    validate_email,
    validate_file_path,
    validate_json_input,
    validate_protection_group_name,
    validate_uuid,
)


class TestSanitizeString:
    """Test sanitize_string function."""

    def test_basic_string(self):
        """Should return sanitized string unchanged."""
        result = sanitize_string("hello world")
        assert result == "hello world"

    def test_removes_dangerous_characters(self):
        """Should remove potentially dangerous characters."""
        result = sanitize_string("<script>alert('xss')</script>")
        assert "<" not in result
        assert ">" not in result
        assert "'" not in result

    def test_removes_quotes(self):
        """Should remove single and double quotes."""
        result = sanitize_string('test"value\'here')
        assert '"' not in result
        assert "'" not in result

    def test_removes_backslash(self):
        """Should remove backslashes."""
        result = sanitize_string("path\\to\\file")
        assert "\\" not in result

    def test_removes_semicolon(self):
        """Should remove semicolons."""
        result = sanitize_string("command; rm -rf /")
        assert ";" not in result

    def test_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        result = sanitize_string("  hello  ")
        assert result == "hello"

    def test_removes_null_bytes(self):
        """Should remove null bytes."""
        result = sanitize_string("hello\x00world")
        assert "\x00" not in result

    def test_removes_control_characters(self):
        """Should remove control characters."""
        result = sanitize_string("hello\x1fworld")
        assert "\x1f" not in result

    def test_max_length_enforcement(self):
        """Should raise error when exceeding max length."""
        with pytest.raises(InputValidationError) as exc_info:
            sanitize_string("a" * 300, max_length=255)
        assert "maximum length" in str(exc_info.value)

    def test_non_string_input(self):
        """Should raise error for non-string input."""
        with pytest.raises(InputValidationError) as exc_info:
            sanitize_string(12345)
        assert "must be a string" in str(exc_info.value)

    def test_custom_max_length(self):
        """Should respect custom max length."""
        result = sanitize_string("hello", max_length=10)
        assert result == "hello"

        with pytest.raises(InputValidationError):
            sanitize_string("hello world", max_length=5)


class TestValidateAwsRegion:
    """Test validate_aws_region function."""

    def test_valid_us_east_1(self):
        """Should accept us-east-1."""
        assert validate_aws_region("us-east-1") is True

    def test_valid_us_west_2(self):
        """Should accept us-west-2."""
        assert validate_aws_region("us-west-2") is True

    def test_valid_eu_west_1(self):
        """Should accept eu-west-1."""
        assert validate_aws_region("eu-west-1") is True

    def test_valid_ap_southeast_1(self):
        """Should accept ap-southeast-1."""
        assert validate_aws_region("ap-southeast-1") is True

    def test_valid_govcloud(self):
        """Should accept GovCloud regions."""
        assert validate_aws_region("us-gov-west-1") is True
        assert validate_aws_region("us-gov-east-1") is True

    def test_invalid_format(self):
        """Should reject invalid format."""
        assert validate_aws_region("invalid") is False
        assert validate_aws_region("us-east") is False
        assert validate_aws_region("us-east-1a") is False

    def test_non_string_input(self):
        """Should reject non-string input."""
        assert validate_aws_region(123) is False
        assert validate_aws_region(None) is False


class TestValidateDrsServerId:
    """Test validate_drs_server_id function."""

    def test_valid_server_id(self):
        """Should accept valid DRS server ID."""
        assert validate_drs_server_id("s-1234567890abcdef0") is True

    def test_valid_server_id_all_hex(self):
        """Should accept server ID with all hex characters."""
        assert validate_drs_server_id("s-abcdef1234567890a") is True

    def test_invalid_prefix(self):
        """Should reject invalid prefix."""
        assert validate_drs_server_id("x-1234567890abcdef0") is False
        assert validate_drs_server_id("1234567890abcdef0") is False

    def test_invalid_length(self):
        """Should reject invalid length."""
        assert validate_drs_server_id("s-123456") is False
        assert validate_drs_server_id("s-1234567890abcdef01234") is False

    def test_invalid_characters(self):
        """Should reject non-hex characters."""
        assert validate_drs_server_id("s-1234567890ghijkl0") is False

    def test_non_string_input(self):
        """Should reject non-string input."""
        assert validate_drs_server_id(123) is False
        assert validate_drs_server_id(None) is False


class TestValidateUuid:
    """Test validate_uuid function."""

    def test_valid_uuid(self):
        """Should accept valid UUID."""
        assert validate_uuid("550e8400-e29b-41d4-a716-446655440000") is True

    def test_valid_uuid_lowercase(self):
        """Should accept lowercase UUID."""
        assert validate_uuid("550e8400-e29b-41d4-a716-446655440000") is True

    def test_valid_uuid_uppercase(self):
        """Should accept uppercase UUID (converted to lowercase)."""
        assert validate_uuid("550E8400-E29B-41D4-A716-446655440000") is True

    def test_invalid_format(self):
        """Should reject invalid format."""
        assert validate_uuid("not-a-uuid") is False
        assert validate_uuid("550e8400e29b41d4a716446655440000") is False

    def test_non_string_input(self):
        """Should reject non-string input."""
        assert validate_uuid(123) is False
        assert validate_uuid(None) is False


class TestValidateEmail:
    """Test validate_email function."""

    def test_valid_email(self):
        """Should accept valid email."""
        assert validate_email("user@example.com") is True

    def test_valid_email_with_subdomain(self):
        """Should accept email with subdomain."""
        assert validate_email("user@mail.example.com") is True

    def test_valid_email_with_plus(self):
        """Should accept email with plus sign."""
        assert validate_email("user+tag@example.com") is True

    def test_invalid_email_no_at(self):
        """Should reject email without @."""
        assert validate_email("userexample.com") is False

    def test_invalid_email_no_domain(self):
        """Should reject email without domain."""
        assert validate_email("user@") is False

    def test_invalid_email_no_tld(self):
        """Should reject email without TLD."""
        assert validate_email("user@example") is False

    def test_non_string_input(self):
        """Should reject non-string input."""
        assert validate_email(123) is False
        assert validate_email(None) is False


class TestValidateJsonInput:
    """Test validate_json_input function."""

    def test_valid_json_object(self):
        """Should parse valid JSON object."""
        result = validate_json_input('{"key": "value"}')
        assert result == {"key": "value"}

    def test_valid_json_array(self):
        """Should parse valid JSON array."""
        result = validate_json_input('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_valid_json_nested(self):
        """Should parse nested JSON."""
        result = validate_json_input('{"outer": {"inner": "value"}}')
        assert result == {"outer": {"inner": "value"}}

    def test_invalid_json(self):
        """Should raise error for invalid JSON."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_json_input("{invalid json}")
        assert "Invalid JSON format" in str(exc_info.value)

    def test_json_too_large(self):
        """Should raise error for JSON exceeding max size."""
        large_json = '{"data": "' + "x" * 2000000 + '"}'
        with pytest.raises(InputValidationError) as exc_info:
            validate_json_input(large_json, max_size=1024 * 1024)
        assert "exceeds maximum size" in str(exc_info.value)

    def test_non_string_input(self):
        """Should raise error for non-string input."""
        with pytest.raises(InputValidationError):
            validate_json_input({"key": "value"})


class TestValidateProtectionGroupName:
    """Test validate_protection_group_name function."""

    def test_valid_name(self):
        """Should accept valid name."""
        assert validate_protection_group_name("Web Servers") is True

    def test_valid_name_with_hyphen(self):
        """Should accept name with hyphen."""
        assert validate_protection_group_name("web-servers") is True

    def test_valid_name_with_underscore(self):
        """Should accept name with underscore."""
        assert validate_protection_group_name("web_servers") is True

    def test_valid_name_with_numbers(self):
        """Should accept name with numbers."""
        assert validate_protection_group_name("tier1-servers") is True

    def test_name_too_short(self):
        """Should reject name shorter than 3 characters."""
        assert validate_protection_group_name("ab") is False

    def test_name_too_long(self):
        """Should reject name longer than 50 characters."""
        assert validate_protection_group_name("a" * 51) is False

    def test_name_with_special_characters(self):
        """Should reject name with special characters."""
        assert validate_protection_group_name("web@servers") is False
        assert validate_protection_group_name("web#servers") is False

    def test_non_string_input(self):
        """Should reject non-string input."""
        assert validate_protection_group_name(123) is False
        assert validate_protection_group_name(None) is False


class TestValidateAwsAccountId:
    """Test validate_aws_account_id function."""

    def test_valid_account_id(self):
        """Should accept valid 12-digit account ID."""
        assert validate_aws_account_id("123456789012") is True

    def test_invalid_too_short(self):
        """Should reject account ID shorter than 12 digits."""
        assert validate_aws_account_id("12345678901") is False

    def test_invalid_too_long(self):
        """Should reject account ID longer than 12 digits."""
        assert validate_aws_account_id("1234567890123") is False

    def test_invalid_non_numeric(self):
        """Should reject non-numeric account ID."""
        assert validate_aws_account_id("12345678901a") is False

    def test_non_string_input(self):
        """Should reject non-string input."""
        assert validate_aws_account_id(123456789012) is False
        assert validate_aws_account_id(None) is False


class TestSanitizeDynamodbInput:
    """Test sanitize_dynamodb_input function."""

    def test_basic_dict(self):
        """Should sanitize basic dictionary."""
        data = {"name": "test", "value": "hello"}
        result = sanitize_dynamodb_input(data)
        assert result["name"] == "test"
        assert result["value"] == "hello"

    def test_removes_dangerous_chars(self):
        """Should remove dangerous characters from values."""
        data = {"name": "<script>alert('xss')</script>"}
        result = sanitize_dynamodb_input(data)
        assert "<" not in result["name"]
        assert ">" not in result["name"]

    def test_preserves_numbers(self):
        """Should preserve numeric values."""
        data = {"count": 42, "price": 19.99}
        result = sanitize_dynamodb_input(data)
        assert result["count"] == 42
        assert result["price"] == 19.99

    def test_preserves_booleans(self):
        """Should preserve boolean values."""
        data = {"active": True, "deleted": False}
        result = sanitize_dynamodb_input(data)
        assert result["active"] is True
        assert result["deleted"] is False

    def test_sanitizes_nested_dict(self):
        """Should sanitize nested dictionaries."""
        data = {"outer": {"inner": "<script>"}}
        result = sanitize_dynamodb_input(data)
        assert "<" not in result["outer"]["inner"]

    def test_sanitizes_list_values(self):
        """Should sanitize list values."""
        data = {"items": ["<script>", "normal"]}
        result = sanitize_dynamodb_input(data)
        assert "<" not in result["items"][0]

    def test_preserves_none(self):
        """Should preserve None values."""
        data = {"value": None}
        result = sanitize_dynamodb_input(data)
        assert result["value"] is None


class TestValidateApiGatewayEvent:
    """Test validate_api_gateway_event function."""

    def test_valid_get_request(self):
        """Should validate valid GET request."""
        event = {
            "httpMethod": "GET",
            "path": "/api/v1/resources",
            "headers": {"content-type": "application/json"},
            "queryStringParameters": {"limit": "10"},
        }
        result = validate_api_gateway_event(event)
        assert result["httpMethod"] == "GET"
        assert result["path"] == "/api/v1/resources"

    def test_valid_post_request(self):
        """Should validate valid POST request."""
        event = {
            "httpMethod": "POST",
            "path": "/api/v1/resources",
            "headers": {"content-type": "application/json"},
            "body": '{"name": "test"}',
        }
        result = validate_api_gateway_event(event)
        assert result["httpMethod"] == "POST"

    def test_missing_http_method(self):
        """Should raise error for missing httpMethod."""
        event = {"path": "/api/v1/resources"}
        with pytest.raises(InputValidationError) as exc_info:
            validate_api_gateway_event(event)
        assert "httpMethod" in str(exc_info.value)

    def test_missing_path(self):
        """Should raise error for missing path."""
        event = {"httpMethod": "GET"}
        with pytest.raises(InputValidationError) as exc_info:
            validate_api_gateway_event(event)
        assert "path" in str(exc_info.value)

    def test_invalid_http_method(self):
        """Should raise error for invalid HTTP method."""
        event = {"httpMethod": "INVALID", "path": "/api"}
        with pytest.raises(InputValidationError) as exc_info:
            validate_api_gateway_event(event)
        assert "Invalid HTTP method" in str(exc_info.value)

    def test_sanitizes_path(self):
        """Should sanitize path."""
        event = {
            "httpMethod": "GET",
            "path": "/api/<script>",
        }
        result = validate_api_gateway_event(event)
        assert "<" not in result["path"]

    def test_non_dict_event(self):
        """Should raise error for non-dict event."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_api_gateway_event("not a dict")
        assert "must be a dictionary" in str(exc_info.value)


class TestMaskSensitiveData:
    """Test mask_sensitive_data function."""

    def test_masks_password(self):
        """Should mask password field."""
        data = {"password": "secretpassword123"}
        result = mask_sensitive_data(data)
        assert result["password"].startswith("secr")
        assert result["password"].endswith("*" * 13)

    def test_masks_token(self):
        """Should mask token field."""
        data = {"access_token": "abc123xyz789"}
        result = mask_sensitive_data(data)
        assert "abc1" in result["access_token"]
        assert "*" in result["access_token"]

    def test_masks_secret(self):
        """Should mask secret field."""
        data = {"client_secret": "mysecretvalue"}
        result = mask_sensitive_data(data)
        assert "*" in result["client_secret"]

    def test_preserves_non_sensitive(self):
        """Should preserve non-sensitive fields."""
        data = {"username": "john", "email": "john@example.com"}
        result = mask_sensitive_data(data)
        assert result["username"] == "john"
        assert result["email"] == "john@example.com"

    def test_masks_nested_sensitive(self):
        """Should mask sensitive fields in nested dicts."""
        data = {"auth": {"password": "secret123"}}
        result = mask_sensitive_data(data)
        assert "*" in result["auth"]["password"]

    def test_short_values_not_masked(self):
        """Should not mask values 4 chars or shorter."""
        data = {"key": "abc"}
        result = mask_sensitive_data(data)
        assert result["key"] == "abc"


class TestCreateSecurityHeaders:
    """Test create_security_headers function."""

    def test_returns_dict(self):
        """Should return dictionary of headers."""
        headers = create_security_headers()
        assert isinstance(headers, dict)

    def test_includes_content_type_options(self):
        """Should include X-Content-Type-Options."""
        headers = create_security_headers()
        assert headers["X-Content-Type-Options"] == "nosniff"

    def test_includes_frame_options(self):
        """Should include X-Frame-Options."""
        headers = create_security_headers()
        assert headers["X-Frame-Options"] == "DENY"

    def test_includes_xss_protection(self):
        """Should include X-XSS-Protection."""
        headers = create_security_headers()
        assert "X-XSS-Protection" in headers

    def test_includes_hsts(self):
        """Should include Strict-Transport-Security."""
        headers = create_security_headers()
        assert "Strict-Transport-Security" in headers

    def test_includes_csp(self):
        """Should include Content-Security-Policy."""
        headers = create_security_headers()
        assert "Content-Security-Policy" in headers

    def test_includes_referrer_policy(self):
        """Should include Referrer-Policy."""
        headers = create_security_headers()
        assert "Referrer-Policy" in headers


class TestValidateFilePath:
    """Test validate_file_path function (Requirement 4: Defensive Security)."""

    def test_allows_lambda_runtime_path(self):
        """Should allow Lambda runtime paths like /var/task/frontend."""
        path = "/var/task/frontend/index.html"
        result = validate_file_path(path)
        assert result == path

    def test_allows_lambda_task_directory(self):
        """Should allow /var/task directory paths."""
        path = "/var/task/frontend"
        result = validate_file_path(path)
        assert result == path

    def test_allows_tmp_directory(self):
        """Should allow temporary directory paths like /tmp."""
        path = "/tmp/build/output.js"
        result = validate_file_path(path)
        assert result == path

    def test_allows_tmp_root(self):
        """Should allow /tmp root path."""
        path = "/tmp"
        result = validate_file_path(path)
        assert result == path

    def test_allows_relative_paths(self):
        """Should allow relative paths without traversal."""
        path = "frontend/dist/index.html"
        result = validate_file_path(path)
        assert result == path

    def test_allows_absolute_paths(self):
        """Should allow absolute paths without traversal."""
        path = "/home/user/project/file.txt"
        result = validate_file_path(path)
        assert result == path

    def test_allows_paths_with_dots_in_filename(self):
        """Should allow paths with dots in filename (not traversal)."""
        path = "/var/task/frontend/app.config.js"
        result = validate_file_path(path)
        assert result == path

    def test_allows_hidden_files(self):
        """Should allow hidden files starting with dot."""
        path = "/var/task/.env"
        result = validate_file_path(path)
        assert result == path

    def test_blocks_parent_directory_traversal(self):
        """Should block .. path traversal patterns."""
        path = "../../../etc/passwd"
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_path(path)
        assert "Path traversal detected" in str(exc_info.value)

    def test_blocks_traversal_in_middle_of_path(self):
        """Should block .. traversal in middle of path."""
        path = "/var/task/../../../etc/passwd"
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_path(path)
        assert "Path traversal detected" in str(exc_info.value)

    def test_blocks_url_encoded_traversal(self):
        """Should block URL-encoded .. (%2e%2e) traversal."""
        path = "%2e%2e/etc/passwd"
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_path(path)
        assert "Path traversal detected" in str(exc_info.value)

    def test_blocks_double_url_encoded_traversal(self):
        """Should block double URL-encoded .. (%252e%252e) traversal."""
        path = "%252e%252e/etc/passwd"
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_path(path)
        assert "Path traversal detected" in str(exc_info.value)

    def test_blocks_mixed_case_url_encoded_traversal(self):
        """Should block mixed case URL-encoded traversal."""
        path = "%2E%2E/etc/passwd"
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_path(path)
        assert "Path traversal detected" in str(exc_info.value)

    def test_raises_error_for_empty_path(self):
        """Should raise error for empty path."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_path("")
        assert "cannot be empty" in str(exc_info.value)

    def test_raises_error_for_none_path(self):
        """Should raise error for None path."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_path(None)
        assert "cannot be empty" in str(exc_info.value)

    def test_returns_path_unchanged(self):
        """Should return valid path unchanged (defensive, not offensive)."""
        original_path = "/var/task/frontend/dist/assets/index-abc123.js"
        result = validate_file_path(original_path)
        assert result == original_path

    def test_allows_deep_nested_paths(self):
        """Should allow deeply nested paths without traversal."""
        path = "/var/task/frontend/dist/assets/js/vendor/lodash.min.js"
        result = validate_file_path(path)
        assert result == path

    def test_allows_paths_with_special_chars(self):
        """Should allow paths with special characters (not traversal)."""
        path = "/var/task/frontend/dist/assets/file-name_v1.2.3.js"
        result = validate_file_path(path)
        assert result == path


class TestValidateFilePathDefensiveBehavior:
    """Test that validate_file_path is defensive, not offensive."""

    def test_does_not_modify_valid_paths(self):
        """Defensive validation should NOT modify valid paths."""
        test_paths = [
            "/var/task/frontend/index.html",
            "/tmp/build/output.js",
            "relative/path/file.txt",
            "/home/user/project/src/main.py",
            "/var/task/.hidden/config.json",
        ]

        for path in test_paths:
            result = validate_file_path(path)
            assert result == path, f"Path was modified: {path} -> {result}"

    def test_only_blocks_actual_attacks(self):
        """Should only block actual path traversal attacks."""
        # These should be blocked (actual attacks)
        attack_paths = [
            "../../../etc/passwd",
            "../../secret.txt",
            "/var/task/../../../etc/shadow",
            "%2e%2e/etc/passwd",
            "%252e%252e/etc/passwd",
        ]

        for path in attack_paths:
            with pytest.raises(InputValidationError):
                validate_file_path(path)

    def test_allows_legitimate_operations(self):
        """Should allow all legitimate Lambda operations."""
        # These should all be allowed (legitimate operations)
        legitimate_paths = [
            "/var/task/frontend/dist/index.html",
            "/var/task/frontend/dist/assets/index-abc123.js",
            "/var/task/frontend/dist/assets/index-def456.css",
            "/tmp/frontend-build/dist/index.html",
            "/tmp/config.json",
            "frontend/dist/index.html",
            "assets/aws-config.js",
        ]

        for path in legitimate_paths:
            result = validate_file_path(path)
            assert result == path


class TestValidateFilePathLambdaPaths:
    """Test validate_file_path allows Lambda runtime paths (Requirement 4)."""

    def test_allows_var_task_frontend(self):
        """Should allow /var/task/frontend path."""
        path = "/var/task/frontend"
        result = validate_file_path(path)
        assert result == path

    def test_allows_var_task_frontend_dist(self):
        """Should allow /var/task/frontend/dist path."""
        path = "/var/task/frontend/dist"
        result = validate_file_path(path)
        assert result == path

    def test_allows_var_task_frontend_nested(self):
        """Should allow deeply nested /var/task/frontend paths."""
        paths = [
            "/var/task/frontend/dist/index.html",
            "/var/task/frontend/dist/assets/index-abc123.js",
            "/var/task/frontend/dist/assets/css/styles.css",
            "/var/task/frontend/dist/assets/images/logo.png",
        ]

        for path in paths:
            result = validate_file_path(path)
            assert result == path

    def test_allows_tmp_directory(self):
        """Should allow /tmp directory paths."""
        paths = [
            "/tmp",
            "/tmp/build",
            "/tmp/build/output.js",
            "/tmp/frontend-build/dist/index.html",
            "/tmp/config.json",
        ]

        for path in paths:
            result = validate_file_path(path)
            assert result == path

    def test_allows_var_task_root(self):
        """Should allow /var/task root path."""
        path = "/var/task"
        result = validate_file_path(path)
        assert result == path


class TestValidateFilePathBlocksTraversal:
    """Test validate_file_path blocks path traversal patterns."""

    def test_blocks_simple_traversal(self):
        """Should block simple .. traversal."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_path("../etc/passwd")
        assert "Path traversal detected" in str(exc_info.value)

    def test_blocks_multiple_traversal(self):
        """Should block multiple .. traversal."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_path("../../../etc/passwd")
        assert "Path traversal detected" in str(exc_info.value)

    def test_blocks_traversal_in_middle(self):
        """Should block .. traversal in middle of path."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_path("/var/task/../../../etc/passwd")
        assert "Path traversal detected" in str(exc_info.value)

    def test_blocks_url_encoded_traversal_lowercase(self):
        """Should block URL-encoded .. (%2e%2e) traversal."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_path("%2e%2e/etc/passwd")
        assert "Path traversal detected" in str(exc_info.value)

    def test_blocks_url_encoded_traversal_uppercase(self):
        """Should block URL-encoded .. (%2E%2E) traversal."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_path("%2E%2E/etc/passwd")
        assert "Path traversal detected" in str(exc_info.value)

    def test_blocks_double_url_encoded_traversal(self):
        """Should block double URL-encoded .. (%252e%252e) traversal."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_path("%252e%252e/etc/passwd")
        assert "Path traversal detected" in str(exc_info.value)

    def test_blocks_mixed_traversal(self):
        """Should block mixed traversal patterns."""
        attack_paths = [
            "..%2f..%2f..%2fetc/passwd",
            "/var/task/..%2f..%2fetc/passwd",
        ]

        for path in attack_paths:
            # These contain .. so should be blocked
            if ".." in path:
                with pytest.raises(InputValidationError):
                    validate_file_path(path)


class TestValidateFilePathDoesNotBlockLegitimate:
    """Test validate_file_path does NOT block legitimate paths."""

    def test_does_not_block_based_on_depth(self):
        """Should NOT block paths based on directory depth."""
        deep_path = "/var/task/frontend/dist/assets/js/vendor/lodash/core.min.js"
        result = validate_file_path(deep_path)
        assert result == deep_path

    def test_does_not_block_absolute_paths(self):
        """Should NOT block absolute paths without traversal."""
        absolute_paths = [
            "/var/task/frontend",
            "/tmp/build",
            "/home/user/project",
            "/etc/config",  # Even sensitive paths without traversal
        ]

        for path in absolute_paths:
            result = validate_file_path(path)
            assert result == path

    def test_does_not_block_dots_in_filenames(self):
        """Should NOT block dots in filenames (not traversal)."""
        paths = [
            "/var/task/frontend/app.config.js",
            "/var/task/frontend/.env",
            "/var/task/frontend/file.min.js",
            "/var/task/frontend/v1.2.3/index.js",
        ]

        for path in paths:
            result = validate_file_path(path)
            assert result == path

    def test_does_not_block_hidden_files(self):
        """Should NOT block hidden files starting with dot."""
        paths = [
            "/var/task/.env",
            "/var/task/.hidden/config.json",
            "/tmp/.cache/data.json",
        ]

        for path in paths:
            result = validate_file_path(path)
            assert result == path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
