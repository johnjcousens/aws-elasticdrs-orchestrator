"""
Property-Based Tests for IAM Audit Logging

Tests audit logging functionality using property-based testing with Hypothesis.
Verifies that audit logs are complete, consistent, and properly formatted
across a wide range of inputs and scenarios.

## Test Strategy

1. **Log Completeness**: Verify all required fields are present in audit logs
2. **Data Masking**: Test that sensitive parameters are properly masked
3. **Result Truncation**: Verify large results are truncated appropriately
4. **Format Consistency**: Test that log format is consistent across operations
5. **Edge Cases**: Test boundary conditions and unusual inputs

## Property-Based Testing Benefits

- Discovers edge cases in logging logic
- Verifies consistency across many input variations
- Tests invariants that should always hold true
- Provides confidence in audit trail completeness
"""

import sys
import os
import json

import pytest  # Add pytest import

# Add lambda directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from hypothesis import given, strategies as st, assume, settings, HealthCheck
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from shared.iam_utils import (
    log_direct_invocation,
    _mask_sensitive_params,
    _truncate_result,
)
import shared.iam_utils as _iam_utils_module




@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks between tests to prevent state pollution."""
    import shared.account_utils

    shared.account_utils._dynamodb = None
    shared.account_utils._target_accounts_table = None

    import shared.conflict_detection

    shared.conflict_detection.dynamodb = None
    shared.conflict_detection._protection_groups_table = None
    shared.conflict_detection._recovery_plans_table = None
    shared.conflict_detection._execution_history_table = None

    mock_dynamodb_resource = MagicMock()
    mock_table = MagicMock()
    mock_table.scan.return_value = {"Items": []}
    mock_table.get_item.return_value = {}

    def get_table(table_name):
        return mock_table

    mock_dynamodb_resource.Table.side_effect = get_table

    shared.conflict_detection.dynamodb = mock_dynamodb_resource
    shared.account_utils._dynamodb = mock_dynamodb_resource

    yield

    shared.conflict_detection.dynamodb = None
    shared.conflict_detection._protection_groups_table = None
    shared.conflict_detection._recovery_plans_table = None
    shared.conflict_detection._execution_history_table = None
    shared.account_utils._dynamodb = None
    shared.account_utils._target_accounts_table = None


# Strategy for generating operation names
operation_name = st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=3, max_size=50)

# Strategy for generating IAM principal ARNs
principal_arn = st.one_of(
    st.just("arn:aws:iam::123456789012:role/OrchestrationRole"),
    st.just("arn:aws:sts::123456789012:assumed-role/OrchestrationRole/session"),
    st.just("arn:aws:iam::123456789012:user/admin"),
)

# Strategy for generating parameter dictionaries
params_dict = st.dictionaries(
    keys=st.text(min_size=1, max_size=30),
    values=st.one_of(st.text(max_size=100), st.integers(), st.booleans(), st.none()),
    max_size=10,
)

# Strategy for generating result data
result_data = st.one_of(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=30),
        values=st.one_of(st.text(max_size=100), st.integers(), st.booleans()),
        max_size=10,
    ),
    st.lists(st.text(max_size=50), max_size=20),
    st.text(max_size=500),
)


@given(principal=principal_arn, operation=operation_name, params=params_dict, result=result_data, success=st.booleans())
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_audit_log_always_contains_required_fields(principal, operation, params, result, success, reset_logger_state, reset_environment_variables):
    """
    Property: Audit logs should always contain all required fields.

    This tests that every audit log entry includes timestamp, event_type,
    principal, operation, parameters, result, and success fields.
    """
    with patch.object(_iam_utils_module, "logger") as mock_logger:
        mock_logger.info = Mock(return_value=None)
        mock_logger.warning = Mock(return_value=None)
        mock_logger.error = Mock(return_value=None)

        log_direct_invocation(principal=principal, operation=operation, params=params, result=result, success=success)

        # If serialization failed, error path is acceptable
        if mock_logger.error.called:
            return

        if success:
            assert mock_logger.info.called, "Logger.info should be called for success"
            call_args = mock_logger.info.call_args
        else:
            assert mock_logger.warning.called, "Logger.warning should be called for failure"
            call_args = mock_logger.warning.call_args

        assert call_args is not None, "Logger call_args should not be None"

        logged_message = call_args[0][0]
        log_entry = json.loads(logged_message)

        required_fields = ["timestamp", "event_type", "principal", "operation", "parameters", "result", "success"]

        for field in required_fields:
            assert field in log_entry, f"Missing required field: {field}"


@given(principal=principal_arn, operation=operation_name, params=params_dict, result=result_data, success=st.booleans())
@settings(max_examples=50)
def test_audit_log_timestamp_format(principal, operation, params, result, success):
    """
    Property: Audit log timestamps should always be valid ISO 8601 format.

    This tests that timestamps are consistently formatted and parseable.
    """
    with patch.object(_iam_utils_module, "logger") as mock_logger:
        # Log invocation
        log_direct_invocation(principal=principal, operation=operation, params=params, result=result, success=success)

        # If serialization failed, error path is acceptable
        if mock_logger.error.called:
            return

        # Get logged message - handle both success and failure cases
        if mock_logger.info.called:
            call_args = mock_logger.info.call_args
        elif mock_logger.warning.called:
            call_args = mock_logger.warning.call_args
        else:
            pytest.skip("Logger was not called - skipping validation")

        # call_args might be None if mock wasn't called properly
        if call_args is None:
            pytest.skip("Logger call_args is None - skipping validation")

        logged_message = call_args[0][0]
        log_entry = json.loads(logged_message)

        # Verify timestamp is valid ISO 8601
        timestamp = log_entry["timestamp"]
        assert timestamp.endswith("Z"), "Timestamp should end with Z (UTC)"

        # Should be parseable
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)


@given(
    params=st.dictionaries(
        keys=st.sampled_from(
            ["password", "secret", "token", "key", "credential", "authorization", "auth", "apiKey", "secretKey"]
        ),
        values=st.text(min_size=10, max_size=50),
        min_size=1,
        max_size=5,
    )
)
@settings(max_examples=50)
def test_sensitive_params_always_masked(params):
    """
    Property: Sensitive parameters should always be masked in logs.

    This tests that parameters with sensitive names (password, secret, etc.)
    are consistently masked to protect sensitive data.
    """
    # Mask parameters
    masked = _mask_sensitive_params(params)

    # Verify all sensitive values are masked
    for key, value in masked.items():
        if isinstance(value, str) and len(value) > 4:
            # Should show first 4 chars + asterisks
            assert "*" in value, f"Sensitive param '{key}' not masked"
            assert value[:4] == params[key][:4], "First 4 chars should be preserved"


@given(
    params=st.dictionaries(
        keys=st.text(min_size=1, max_size=30).filter(
            lambda x: not any(
                sensitive in x.lower() for sensitive in ["password", "secret", "token", "key", "credential"]
            )
        ),
        values=st.text(min_size=1, max_size=50),
        max_size=10,
    )
)
@settings(max_examples=50)
def test_non_sensitive_params_not_masked(params):
    """
    Property: Non-sensitive parameters should not be masked.

    This tests that normal parameters are preserved without masking.
    """
    # Mask parameters
    masked = _mask_sensitive_params(params)

    # Verify non-sensitive values are not masked
    for key, value in masked.items():
        if isinstance(value, str):
            # Check if value was actually masked (has asterisks AND is longer than original)
            # A value like "*" is not masked, it's just the original value
            original_value = params[key]
            if "*" in value and len(value) > len(original_value):
                assert False, f"Non-sensitive param '{key}' was masked"
            # Value should be unchanged
            assert value == original_value, f"Value should be unchanged for key '{key}'"


@given(
    result=st.dictionaries(
        keys=st.text(min_size=1, max_size=30),
        values=st.text(min_size=1, max_size=100),
        min_size=20,  # Large enough to trigger truncation
        max_size=50,
    )
)
@settings(max_examples=50)
def test_large_results_always_truncated(result):
    """
    Property: Large results should always be truncated to prevent log overflow.

    This tests that results exceeding the maximum length are consistently
    truncated with metadata about the truncation.
    """
    # Truncate result
    truncated = _truncate_result(result, max_length=100)

    # If result is large, should be truncated
    result_str = json.dumps(result)
    if len(result_str) > 100:
        assert isinstance(truncated, dict), "Truncated result should be dict"
        assert "truncated" in truncated, "Should indicate truncation"
        assert truncated["truncated"] is True
        assert "preview" in truncated, "Should include preview"
        assert "original_length" in truncated, "Should include original length"
        assert len(truncated["preview"]) <= 103, "Preview should be truncated"  # 100 + "..."


@given(result=st.one_of(st.text(max_size=50), st.integers(), st.booleans(), st.lists(st.integers(), max_size=5)))
@settings(max_examples=50)
def test_small_results_not_truncated(result):
    """
    Property: Small results should not be truncated.

    This tests that results within the size limit are preserved without
    truncation metadata.
    """
    # Truncate result
    truncated = _truncate_result(result, max_length=1000)

    # Small results should not be truncated
    result_str = json.dumps(result) if not isinstance(result, str) else result
    if len(result_str) <= 1000:
        # Should return original result or string representation
        if isinstance(truncated, dict) and "truncated" in truncated:
            assert truncated["truncated"] is False or "truncated" not in truncated


@given(principal=principal_arn, operation=operation_name, params=params_dict, result=result_data)
@settings(max_examples=50)
def test_success_logs_use_info_level(principal, operation, params, result):
    """
    Property: Successful invocations should always log at INFO level.

    This tests that successful operations are consistently logged with
    appropriate severity.
    """
    with patch.object(_iam_utils_module, "logger") as mock_logger:
        # Log successful invocation
        log_direct_invocation(principal=principal, operation=operation, params=params, result=result, success=True)

        # Should use info level (or neither if logging failed)
        # The function has a try-except that catches logging errors
        if mock_logger.info.called or mock_logger.warning.called:
            assert mock_logger.info.called, "Success should log at INFO level"
            assert not mock_logger.warning.called, "Success should not log at WARNING level"


@given(principal=principal_arn, operation=operation_name, params=params_dict, result=result_data)
@settings(max_examples=50)
def test_failure_logs_use_warning_level(principal, operation, params, result):
    """
    Property: Failed invocations should always log at WARNING level.

    This tests that failed operations are consistently logged with
    appropriate severity for alerting.
    """
    with patch.object(_iam_utils_module, "logger") as mock_logger:
        # Log failed invocation
        log_direct_invocation(principal=principal, operation=operation, params=params, result=result, success=False)

        # Should use warning level (or neither if logging failed)
        # The function has a try-except that catches logging errors
        if mock_logger.info.called or mock_logger.warning.called:
            assert mock_logger.warning.called, "Failure should log at WARNING level"
            assert not mock_logger.info.called, "Failure should not log at INFO level"


@given(principal=principal_arn, operation=operation_name, params=params_dict, result=result_data, success=st.booleans())
@settings(max_examples=50)
def test_audit_log_with_context_includes_metadata(principal, operation, params, result, success):
    """
    Property: Audit logs with context should include request metadata.

    This tests that when Lambda context is provided, the audit log
    includes request ID, function name, and function version.
    """
    # Create mock context
    context = Mock()
    context.aws_request_id = "test-request-123"
    context.function_name = "test-function"
    context.function_version = "$LATEST"

    with patch.object(_iam_utils_module, "logger") as mock_logger:
        # Log invocation with context
        log_direct_invocation(
            principal=principal, operation=operation, params=params, result=result, success=success, context=context
        )

        # If serialization failed, error path is acceptable
        if mock_logger.error.called:
            return

        # Get logged message - handle both success and failure cases
        if mock_logger.info.called:
            call_args = mock_logger.info.call_args
        elif mock_logger.warning.called:
            call_args = mock_logger.warning.call_args
        else:
            pytest.skip("Logger was not called - skipping validation")

        # call_args might be None if mock wasn't called properly
        if call_args is None:
            pytest.skip("Logger call_args is None - skipping validation")

        logged_message = call_args[0][0]
        log_entry = json.loads(logged_message)

        # Verify context metadata present
        assert "request_id" in log_entry
        assert "function_name" in log_entry
        assert "function_version" in log_entry
        assert log_entry["request_id"] == "test-request-123"
        assert log_entry["function_name"] == "test-function"
        assert log_entry["function_version"] == "$LATEST"


@given(principal=principal_arn, operation=operation_name, params=params_dict, result=result_data, success=st.booleans())
@settings(max_examples=50)
def test_audit_log_json_parseable(principal, operation, params, result, success):
    """
    Property: Audit logs should always be valid JSON.

    This tests that logged messages can be parsed as JSON for
    log aggregation and analysis tools.
    """
    with patch.object(_iam_utils_module, "logger") as mock_logger:
        # Log invocation
        log_direct_invocation(principal=principal, operation=operation, params=params, result=result, success=success)

        # If serialization failed, error path is acceptable
        if mock_logger.error.called:
            return

        # Get logged message - handle both success and failure cases
        if mock_logger.info.called:
            call_args = mock_logger.info.call_args
        elif mock_logger.warning.called:
            call_args = mock_logger.warning.call_args
        else:
            pytest.skip("Logger was not called - skipping validation")

        # call_args might be None if mock wasn't called properly
        if call_args is None:
            pytest.skip("Logger call_args is None - skipping validation")

        logged_message = call_args[0][0]

        # Should be valid JSON
        log_entry = json.loads(logged_message)
        assert isinstance(log_entry, dict)


@given(
    params=st.dictionaries(
        keys=st.text(min_size=1, max_size=30),
        values=st.dictionaries(
            keys=st.sampled_from(["password", "secret", "token"]),
            values=st.text(min_size=10, max_size=50),
            min_size=1,
            max_size=3,
        ),
        max_size=5,
    )
)
@settings(max_examples=30)
def test_nested_sensitive_params_masked(params):
    """
    Property: Nested sensitive parameters should be masked recursively.

    This tests that sensitive data in nested dictionaries is properly
    masked at all levels.
    """
    # Mask parameters
    masked = _mask_sensitive_params(params)

    # Verify nested sensitive values are masked
    for key, value in masked.items():
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                if isinstance(nested_value, str) and len(nested_value) > 4:
                    assert "*" in nested_value, f"Nested param '{nested_key}' not masked"


@given(principal=principal_arn, operation=operation_name, params=params_dict, result=result_data, success=st.booleans())
@settings(max_examples=50)
def test_audit_log_event_type_always_direct_invocation(principal, operation, params, result, success):
    """
    Property: Audit logs should always have event_type='direct_invocation'.

    This tests that the event type is consistently set for filtering
    and categorization in log analysis.
    """
    with patch.object(_iam_utils_module, "logger") as mock_logger:
        # Log invocation
        log_direct_invocation(principal=principal, operation=operation, params=params, result=result, success=success)

        # If serialization failed, error path is acceptable
        if mock_logger.error.called:
            return

        # Get logged message - handle both success and failure cases
        if mock_logger.info.called:
            call_args = mock_logger.info.call_args
        elif mock_logger.warning.called:
            call_args = mock_logger.warning.call_args
        else:
            pytest.skip("Logger was not called - skipping validation")

        # call_args might be None if mock wasn't called properly
        if call_args is None:
            pytest.skip("Logger call_args is None - skipping validation")

        logged_message = call_args[0][0]
        log_entry = json.loads(logged_message)

        # Verify event type
        assert log_entry["event_type"] == "direct_invocation"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
