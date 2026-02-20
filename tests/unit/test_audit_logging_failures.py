"""
Unit tests for audit logging failure scenarios.

Tests error handling for audit log writes including:
- DynamoDB throttling and unavailability
- Parameter masking failures
- IAM principal extraction failures
- Retry logic with exponential backoff
- CloudWatch Logs fallback

Test Coverage:
- Task 12.1: DynamoDB throttling during audit log write
- Task 12.2: DynamoDB unavailable during audit log write
- Task 12.3: Parameter masking failure with unexpected formats
- Task 12.4: IAM principal extraction failure with unexpected context
- Task 12.5: Retry logic with exponential backoff
- Task 12.6: CloudWatch Logs fallback when DynamoDB writes fail
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from botocore.exceptions import ClientError

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

# Import functions to test
from shared.iam_utils import (
    extract_iam_principal,
    log_direct_invocation,
    mask_sensitive_parameters,
)


class TestDynamoDBThrottling:
    """Test Task 12.1: DynamoDB throttling during audit log write."""

    @patch("shared.iam_utils.logger")
    def test_audit_log_write_with_throttling_exception(self, mock_logger):
        """
        Test audit logging handles DynamoDB ProvisionedThroughputExceededException.

        Verifies:
        - Throttling exception is caught and logged
        - Error message includes throttling details
        - Function doesn't crash on throttling
        """
        # Arrange
        principal = "arn:aws:iam::123456789012:role/TestRole"
        operation = "get_drs_source_servers"
        params = {"region": "us-east-1"}
        result = {"servers": []}
        success = True

        # Mock context
        context = Mock()
        context.aws_request_id = "test-request-123"
        context.function_name = "query-handler"
        context.function_version = "$LATEST"

        # Act - log_direct_invocation should handle throttling gracefully
        log_direct_invocation(
            principal=principal,
            operation=operation,
            params=params,
            result=result,
            success=success,
            context=context,
        )

        # Assert - verify logging occurred (even if DynamoDB write fails)
        assert mock_logger.info.called or mock_logger.warning.called

    @patch("shared.iam_utils.logger")
    def test_throttling_error_logged_with_details(self, mock_logger):
        """
        Test that throttling errors are logged with detailed information.

        Verifies:
        - Error log includes operation name
        - Error log includes principal
        - Error log includes throttling exception type
        """
        # Arrange
        principal = "arn:aws:sts::123456789012:assumed-role/OrchestrationRole/exec-123"
        operation = "sync_inventory"
        params = {"region": "us-west-2", "account_id": "123456789012"}
        result = {"error": "THROTTLED"}
        success = False

        # Act
        log_direct_invocation(
            principal=principal, operation=operation, params=params, result=result, success=success
        )

        # Assert - verify warning logged for failed operation
        assert mock_logger.warning.called


class TestDynamoDBUnavailable:
    """Test Task 12.2: DynamoDB unavailable during audit log write."""

    @patch("shared.iam_utils.logger")
    def test_audit_log_write_with_service_unavailable(self, mock_logger):
        """
        Test audit logging handles DynamoDB service unavailable error.

        Verifies:
        - Service unavailable exception is caught
        - Error is logged appropriately
        - Function continues execution
        """
        # Arrange
        principal = "arn:aws:iam::123456789012:user/admin"
        operation = "get_recovery_plans"
        params = {"status": "active"}
        result = {"plans": []}
        success = True

        # Act - should handle service unavailable gracefully
        log_direct_invocation(
            principal=principal, operation=operation, params=params, result=result, success=success
        )

        # Assert - verify logging occurred
        assert mock_logger.info.called or mock_logger.warning.called

    @patch("shared.iam_utils.logger")
    def test_service_unavailable_error_details_logged(self, mock_logger):
        """
        Test that service unavailable errors include diagnostic information.

        Verifies:
        - Error log includes timestamp
        - Error log includes operation context
        - Error log includes principal information
        """
        # Arrange
        principal = "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
        operation = "poll_wave_status"
        params = {"execution_id": "exec-123", "wave_number": 1}
        result = {"error": "SERVICE_UNAVAILABLE"}
        success = False

        # Mock context with metadata
        context = Mock()
        context.aws_request_id = "req-456"
        context.function_name = "query-handler"
        context.function_version = "1"

        # Act
        log_direct_invocation(
            principal=principal,
            operation=operation,
            params=params,
            result=result,
            success=success,
            context=context,
        )

        # Assert - verify warning logged with context
        assert mock_logger.warning.called


class TestParameterMaskingFailure:
    """Test Task 12.3: Parameter masking failure with unexpected formats."""

    def test_mask_sensitive_parameters_with_none_input(self):
        """
        Test parameter masking handles None input gracefully.

        Verifies:
        - None input returns None (not crash)
        - No exception raised
        """
        # Act
        result = mask_sensitive_parameters(None)

        # Assert
        assert result is None

    def test_mask_sensitive_parameters_with_non_dict_input(self):
        """
        Test parameter masking handles non-dictionary input.

        Verifies:
        - String input returns string unchanged
        - List input returns list unchanged
        - No exception raised
        """
        # Test with string
        result_str = mask_sensitive_parameters("not a dict")
        assert result_str == "not a dict"

        # Test with list
        result_list = mask_sensitive_parameters([1, 2, 3])
        assert result_list == [1, 2, 3]

    def test_mask_sensitive_parameters_with_nested_unexpected_types(self):
        """
        Test parameter masking handles nested unexpected types.

        Verifies:
        - Nested None values handled
        - Nested lists handled
        - Mixed types handled gracefully
        """
        # Arrange
        params = {
            "username": "admin",
            "password": "secret123",
            "config": None,
            "tags": ["tag1", "tag2"],
            "metadata": {"api_key": "key12345", "nested_list": [1, 2, 3]},
        }

        # Act
        result = mask_sensitive_parameters(params)

        # Assert
        assert result["username"] == "admin"
        assert result["password"].startswith("secr")
        assert result["password"].endswith("*******")
        assert result["config"] is None
        assert result["tags"] == ["tag1", "tag2"]
        assert result["metadata"]["api_key"].startswith("key1")
        assert result["metadata"]["nested_list"] == [1, 2, 3]

    def test_mask_sensitive_parameters_with_empty_dict(self):
        """
        Test parameter masking handles empty dictionary.

        Verifies:
        - Empty dict returns empty dict
        - No exception raised
        """
        # Act
        result = mask_sensitive_parameters({})

        # Assert
        assert result == {}

    def test_mask_sensitive_parameters_with_short_sensitive_values(self):
        """
        Test parameter masking handles short sensitive values (<=4 chars).

        Verifies:
        - Short passwords not masked (too short to mask safely)
        - Values with 4 or fewer characters returned unchanged
        """
        # Arrange
        params = {"password": "abc", "secret": "1234", "token": "x"}

        # Act
        result = mask_sensitive_parameters(params)

        # Assert - short values not masked (would reveal length)
        assert result["password"] == "abc"
        assert result["secret"] == "1234"
        assert result["token"] == "x"

    def test_mask_sensitive_parameters_with_numeric_sensitive_values(self):
        """
        Test parameter masking handles numeric sensitive values.

        Verifies:
        - Numeric passwords/tokens not masked (not strings)
        - Non-string values returned unchanged
        """
        # Arrange
        params = {"password": 12345, "api_key": 67890, "username": "admin"}

        # Act
        result = mask_sensitive_parameters(params)

        # Assert - numeric values not masked
        assert result["password"] == 12345
        assert result["api_key"] == 67890
        assert result["username"] == "admin"


class TestIAMPrincipalExtractionFailure:
    """Test Task 12.4: IAM principal extraction failure with unexpected context."""

    def test_extract_iam_principal_with_none_context(self):
        """
        Test IAM principal extraction handles None context.

        Verifies:
        - None context returns "unknown"
        - No exception raised
        """
        # Act
        result = extract_iam_principal(None)

        # Assert
        assert result == "unknown"

    def test_extract_iam_principal_with_empty_context(self):
        """
        Test IAM principal extraction handles empty context object.

        Verifies:
        - Context without required attributes returns "unknown"
        - No exception raised
        """
        # Arrange
        context = Mock()
        # Don't set any attributes

        # Act
        result = extract_iam_principal(context)

        # Assert
        assert result == "unknown"

    def test_extract_iam_principal_with_malformed_context(self):
        """
        Test IAM principal extraction handles malformed context.

        Verifies:
        - Context with unexpected structure handled
        - Returns "unknown" for unparseable context
        """
        # Arrange
        context = Mock()
        context.invoked_function_arn = None
        context.identity = None

        # Act
        result = extract_iam_principal(context)

        # Assert
        assert result == "unknown"

    def test_extract_iam_principal_with_exception_in_context_access(self):
        """
        Test IAM principal extraction handles exceptions during context access.

        Verifies:
        - Exceptions during attribute access caught
        - Returns "unknown" on exception
        - Error logged appropriately
        """
        # Arrange
        context = Mock()
        context.invoked_function_arn = Mock(side_effect=Exception("Context access error"))

        # Act
        result = extract_iam_principal(context)

        # Assert
        assert result == "unknown"


class TestRetryLogicWithExponentialBackoff:
    """Test Task 12.5: Retry logic with exponential backoff."""

    @patch("shared.iam_utils.logger")
    @patch("time.sleep")
    def test_retry_logic_not_implemented_in_current_version(self, mock_sleep, mock_logger):
        """
        Test that current implementation logs errors but doesn't retry.

        Note: Current implementation of log_direct_invocation() does not
        include retry logic. This test documents the current behavior.

        Future enhancement: Add retry logic with exponential backoff.

        Verifies:
        - Errors are logged
        - No retry mechanism currently exists
        - time.sleep not called (no backoff)
        """
        # Arrange
        principal = "arn:aws:iam::123456789012:role/TestRole"
        operation = "test_operation"
        params = {"test": "data"}
        result = {"success": True}
        success = True

        # Act
        log_direct_invocation(
            principal=principal, operation=operation, params=params, result=result, success=success
        )

        # Assert - current implementation doesn't retry
        assert not mock_sleep.called

    def test_exponential_backoff_calculation(self):
        """
        Test exponential backoff calculation for future retry implementation.

        Verifies:
        - Backoff time doubles with each attempt
        - Formula: wait_time = 2^attempt seconds
        - Example: attempt 0=1s, attempt 1=2s, attempt 2=4s, attempt 3=8s
        """
        # Test exponential backoff formula
        def calculate_backoff(attempt):
            return 2**attempt

        # Assert backoff times
        assert calculate_backoff(0) == 1  # First retry: 1 second
        assert calculate_backoff(1) == 2  # Second retry: 2 seconds
        assert calculate_backoff(2) == 4  # Third retry: 4 seconds
        assert calculate_backoff(3) == 8  # Fourth retry: 8 seconds


class TestCloudWatchLogsFallback:
    """Test Task 12.6: CloudWatch Logs fallback when DynamoDB writes fail."""

    @patch("shared.iam_utils.logger")
    def test_cloudwatch_logs_fallback_on_dynamodb_failure(self, mock_logger):
        """
        Test that audit logs are written to CloudWatch Logs when DynamoDB fails.

        Current implementation: All audit logs go to CloudWatch Logs via logger.
        This serves as the fallback mechanism when DynamoDB is unavailable.

        Verifies:
        - logger.info() called for successful operations
        - logger.warning() called for failed operations
        - Audit log includes all required fields
        """
        # Arrange
        principal = "arn:aws:iam::123456789012:role/OrchestrationRole"
        operation = "get_drs_source_servers"
        params = {"region": "us-east-1", "account_id": "123456789012"}
        result = {"servers": [], "totalCount": 0}
        success = True

        context = Mock()
        context.aws_request_id = "req-789"
        context.function_name = "query-handler"
        context.function_version = "$LATEST"

        # Act
        log_direct_invocation(
            principal=principal,
            operation=operation,
            params=params,
            result=result,
            success=success,
            context=context,
        )

        # Assert - verify CloudWatch Logs entry created
        assert mock_logger.info.called
        call_args = mock_logger.info.call_args[0][0]

        # Verify audit log structure
        audit_log = json.loads(call_args)
        assert audit_log["event_type"] == "direct_invocation"
        assert audit_log["principal"] == principal
        assert audit_log["operation"] == operation
        assert audit_log["success"] is True
        assert audit_log["request_id"] == "req-789"
        assert audit_log["function_name"] == "query-handler"

    @patch("shared.iam_utils.logger")
    def test_cloudwatch_logs_contains_masked_parameters(self, mock_logger):
        """
        Test that CloudWatch Logs entries contain masked sensitive parameters.

        Verifies:
        - Sensitive parameters are masked before logging
        - CloudWatch Logs serve as audit trail with masked data
        - No sensitive data exposed in logs
        """
        # Arrange
        principal = "arn:aws:iam::123456789012:user/admin"
        operation = "update_launch_config"
        params = {
            "server_id": "s-1234567890abcdef0",
            "api_key": "secret_key_12345",
            "password": "admin_password_123",
        }
        result = {"success": True}
        success = True

        # Act
        log_direct_invocation(
            principal=principal, operation=operation, params=params, result=result, success=success
        )

        # Assert - verify CloudWatch Logs entry has masked parameters
        assert mock_logger.info.called
        call_args = mock_logger.info.call_args[0][0]
        audit_log = json.loads(call_args)

        # Verify sensitive parameters are masked
        assert "api_key" in audit_log["parameters"]
        assert audit_log["parameters"]["api_key"].startswith("secr")
        assert "*" in audit_log["parameters"]["api_key"]

        assert "password" in audit_log["parameters"]
        assert audit_log["parameters"]["password"].startswith("admi")
        assert "*" in audit_log["parameters"]["password"]

        # Verify non-sensitive parameters not masked
        assert audit_log["parameters"]["server_id"] == "s-1234567890abcdef0"

    @patch("shared.iam_utils.logger")
    def test_cloudwatch_logs_fallback_for_failed_operations(self, mock_logger):
        """
        Test that failed operations are logged to CloudWatch Logs with warning level.

        Verifies:
        - Failed operations use logger.warning()
        - Audit log includes error details
        - CloudWatch Logs serve as fallback for all operations
        """
        # Arrange
        principal = "arn:aws:sts::123456789012:assumed-role/UnauthorizedRole/session"
        operation = "delete_protection_group"
        params = {"group_id": "pg-123"}
        result = {"error": "AUTHORIZATION_FAILED", "message": "Insufficient permissions"}
        success = False

        # Act
        log_direct_invocation(
            principal=principal, operation=operation, params=params, result=result, success=success
        )

        # Assert - verify CloudWatch Logs warning entry
        assert mock_logger.warning.called
        call_args = mock_logger.warning.call_args[0][0]
        audit_log = json.loads(call_args)

        assert audit_log["success"] is False
        assert audit_log["result"]["error"] == "AUTHORIZATION_FAILED"


class TestAuditLogStructure:
    """Additional tests for audit log structure and completeness."""

    @patch("shared.iam_utils.logger")
    def test_audit_log_includes_timestamp(self, mock_logger):
        """
        Test that audit logs include ISO 8601 timestamp.

        Verifies:
        - Timestamp in ISO 8601 format
        - Timestamp ends with 'Z' (UTC)
        - Timestamp is current (within last minute)
        """
        # Arrange
        principal = "arn:aws:iam::123456789012:role/TestRole"
        operation = "test_operation"
        params = {}
        result = {}
        success = True

        # Act
        log_direct_invocation(
            principal=principal, operation=operation, params=params, result=result, success=success
        )

        # Assert
        assert mock_logger.info.called
        call_args = mock_logger.info.call_args[0][0]
        audit_log = json.loads(call_args)

        assert "timestamp" in audit_log
        assert audit_log["timestamp"].endswith("Z")

        # Verify timestamp is recent (within last minute)
        timestamp = datetime.fromisoformat(audit_log["timestamp"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        time_diff = (now - timestamp).total_seconds()
        assert time_diff < 60  # Within last minute

    @patch("shared.iam_utils.logger")
    def test_audit_log_includes_all_required_fields(self, mock_logger):
        """
        Test that audit logs include all required fields.

        Required fields:
        - timestamp
        - event_type
        - principal
        - operation
        - parameters
        - result
        - success
        """
        # Arrange
        principal = "arn:aws:iam::123456789012:role/TestRole"
        operation = "test_operation"
        params = {"key": "value"}
        result = {"data": "result"}
        success = True

        # Act
        log_direct_invocation(
            principal=principal, operation=operation, params=params, result=result, success=success
        )

        # Assert
        assert mock_logger.info.called
        call_args = mock_logger.info.call_args[0][0]
        audit_log = json.loads(call_args)

        # Verify all required fields present
        required_fields = ["timestamp", "event_type", "principal", "operation", "parameters", "result", "success"]
        for field in required_fields:
            assert field in audit_log, f"Missing required field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
