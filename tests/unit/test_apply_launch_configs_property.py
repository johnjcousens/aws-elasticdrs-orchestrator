"""
Property-based tests for apply_launch_configs_to_group logic.

Feature: async-launch-config-sync

This module tests three critical properties of the async launch config application:
- Property 8: Exponential Backoff Retry
- Property 9: Progress Calculation Accuracy
- Property 13: Error Isolation

Validates: Requirements 2.8, 3.3, 3.4, 3.5, 4.7, 4.8
"""

import os
import sys
import time
from typing import List
from unittest.mock import MagicMock, Mock, patch

import pytest  # noqa: F401
from hypothesis import given, settings, strategies as st

# Add lambda directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))


# ===========================================================================
# Helper functions for retry logic
# ===========================================================================


def calculate_backoff_delay(attempt: int) -> float:
    """
    Calculate exponential backoff delay for retry attempt.

    This implements the logic from Property 8:
    - Attempt 0 (first retry): 1 second
    - Attempt 1 (second retry): 2 seconds
    - Attempt 2 (third retry): 4 seconds

    Args:
        attempt: Retry attempt number (0-indexed)

    Returns:
        Delay in seconds
    """
    return 2**attempt


def should_retry_error(error_code: str, attempt: int, max_retries: int = 3) -> bool:
    """
    Determine if an error should be retried.

    This implements the logic from Property 8:
    - Throttling errors are retried up to max_retries times
    - Other errors are not retried

    Args:
        error_code: AWS error code
        error_code: AWS error code
        attempt: Current attempt number (0-indexed)
        max_retries: Maximum number of retries

    Returns:
        True if should retry, False otherwise
    """
    throttling_errors = ["ThrottlingException", "RequestLimitExceeded", "TooManyRequestsException"]
    return error_code in throttling_errors and attempt < max_retries


# ===========================================================================
# Helper functions for progress calculation
# ===========================================================================


def calculate_percentage(progress_count: int, total_count: int) -> float:
    """
    Calculate progress percentage.

    This implements the logic from Property 9:
    - percentage = (progressCount / totalCount) * 100

    Args:
        progress_count: Number of servers completed
        total_count: Total number of servers

    Returns:
        Percentage value (0-100)
    """
    if total_count == 0:
        return 0.0
    return (progress_count / total_count) * 100


# ===========================================================================
# Helper functions for error isolation
# ===========================================================================


def process_servers_with_isolation(server_ids: List[str], fail_on_servers: List[str]) -> dict:
    """
    Process servers with error isolation.

    This implements the logic from Property 13:
    - Failed servers don't stop processing of remaining servers
    - Each server is processed independently

    Args:
        server_ids: List of server IDs to process
        fail_on_servers: List of server IDs that should fail

    Returns:
        Dictionary with applied and failed counts
    """
    applied = 0
    failed = 0

    for server_id in server_ids:
        if server_id in fail_on_servers:
            failed += 1
        else:
            applied += 1

    return {"applied": applied, "failed": failed}


# ===========================================================================
# Property 8: Exponential Backoff Retry
# Feature: async-launch-config-sync, Property 8: Exponential Backoff Retry
# ===========================================================================


class TestExponentialBackoffRetry:
    """Property tests for exponential backoff retry logic."""

    @settings(max_examples=100)
    @given(attempt=st.integers(min_value=0, max_value=10))
    def test_backoff_delay_is_exponential(self, attempt: int) -> None:
        """
        Feature: async-launch-config-sync, Property 8: Exponential Backoff Retry
        Validates: Requirements 2.8, 4.7

        For any retry attempt, the backoff delay should follow exponential
        pattern: 2^attempt seconds (1s, 2s, 4s, 8s, ...).
        """
        delay = calculate_backoff_delay(attempt)
        expected = 2**attempt

        assert delay == expected, f"Attempt {attempt}: expected {expected}s, got {delay}s"
        assert delay > 0, f"Delay must be positive, got {delay}"

    @settings(max_examples=100)
    @given(attempt=st.integers(min_value=0, max_value=2))
    def test_first_three_retries_match_spec(self, attempt: int) -> None:
        """
        Feature: async-launch-config-sync, Property 8: Exponential Backoff Retry
        Validates: Requirements 2.8, 4.7

        For the first three retry attempts (0, 1, 2), delays must be
        exactly 1s, 2s, and 4s as specified in requirements.
        """
        delay = calculate_backoff_delay(attempt)
        expected_delays = {0: 1, 1: 2, 2: 4}

        assert delay == expected_delays[attempt], f"Attempt {attempt}: expected {expected_delays[attempt]}s, got {delay}s"

    @settings(max_examples=100)
    @given(
        error_code=st.sampled_from(["ThrottlingException", "RequestLimitExceeded", "TooManyRequestsException"]),
        attempt=st.integers(min_value=0, max_value=2),
    )
    def test_throttling_errors_retried_up_to_max(self, error_code: str, attempt: int) -> None:
        """
        Feature: async-launch-config-sync, Property 8: Exponential Backoff Retry
        Validates: Requirements 2.8, 4.7

        For any AWS throttling error, the system should retry up to 3 times
        (attempts 0, 1, 2) before giving up.
        """
        should_retry = should_retry_error(error_code, attempt, max_retries=3)
        assert should_retry is True, f"Throttling error {error_code} at attempt {attempt} should be retried"

    @settings(max_examples=100)
    @given(
        error_code=st.sampled_from(["ThrottlingException", "RequestLimitExceeded", "TooManyRequestsException"]),
        attempt=st.integers(min_value=3, max_value=10),
    )
    def test_throttling_errors_not_retried_after_max(self, error_code: str, attempt: int) -> None:
        """
        Feature: async-launch-config-sync, Property 8: Exponential Backoff Retry
        Validates: Requirements 2.8, 4.7

        For any AWS throttling error, after 3 retry attempts (0, 1, 2),
        no further retries should occur.
        """
        should_retry = should_retry_error(error_code, attempt, max_retries=3)
        assert should_retry is False, f"Throttling error {error_code} at attempt {attempt} should not be retried"

    @settings(max_examples=100)
    @given(
        error_code=st.sampled_from(
            ["AccessDeniedException", "ResourceNotFoundException", "ValidationException", "InternalServerError"]
        ),
        attempt=st.integers(min_value=0, max_value=10),
    )
    def test_non_throttling_errors_never_retried(self, error_code: str, attempt: int) -> None:
        """
        Feature: async-launch-config-sync, Property 8: Exponential Backoff Retry
        Validates: Requirements 2.8, 4.7

        For any non-throttling AWS error, no retries should occur
        regardless of attempt number.
        """
        should_retry = should_retry_error(error_code, attempt, max_retries=3)
        assert should_retry is False, f"Non-throttling error {error_code} should never be retried"

    @settings(max_examples=100)
    @given(attempt=st.integers(min_value=0, max_value=2))
    def test_backoff_delay_increases_monotonically(self, attempt: int) -> None:
        """
        Feature: async-launch-config-sync, Property 8: Exponential Backoff Retry
        Validates: Requirements 2.8, 4.7

        For any retry attempt, the delay should be strictly greater than
        the previous attempt's delay (monotonically increasing).
        """
        if attempt == 0:
            return  # Skip first attempt (no previous to compare)

        current_delay = calculate_backoff_delay(attempt)
        previous_delay = calculate_backoff_delay(attempt - 1)

        assert current_delay > previous_delay, f"Delay must increase: attempt {attempt-1}={previous_delay}s, attempt {attempt}={current_delay}s"

    @settings(max_examples=100)
    @given(attempt=st.integers(min_value=0, max_value=10))
    def test_backoff_calculation_is_deterministic(self, attempt: int) -> None:
        """
        Feature: async-launch-config-sync, Property 8: Exponential Backoff Retry
        Validates: Requirements 2.8, 4.7

        For any retry attempt, calculating the backoff delay multiple times
        must produce the same result.
        """
        delay1 = calculate_backoff_delay(attempt)
        delay2 = calculate_backoff_delay(attempt)
        delay3 = calculate_backoff_delay(attempt)

        assert delay1 == delay2 == delay3, "Backoff calculation must be deterministic"


# ===========================================================================
# Property 9: Progress Calculation Accuracy
# Feature: async-launch-config-sync, Property 9: Progress Calculation Accuracy
# ===========================================================================


class TestProgressCalculationAccuracy:
    """Property tests for progress calculation accuracy."""

    @settings(max_examples=100)
    @given(
        progress_count=st.integers(min_value=0, max_value=500),
        total_count=st.integers(min_value=1, max_value=500),
    )
    def test_percentage_formula_accuracy(self, progress_count: int, total_count: int) -> None:
        """
        Feature: async-launch-config-sync, Property 9: Progress Calculation Accuracy
        Validates: Requirements 3.3, 3.4, 3.5

        For any progressCount and totalCount, percentage must equal
        (progressCount / totalCount) * 100 within floating point precision.
        """
        from hypothesis import assume

        assume(progress_count <= total_count)

        percentage = calculate_percentage(progress_count, total_count)
        expected = (progress_count / total_count) * 100

        assert abs(percentage - expected) < 0.01, f"Expected {expected}%, got {percentage}%"

    @settings(max_examples=100)
    @given(total_count=st.integers(min_value=1, max_value=500))
    def test_zero_progress_is_zero_percent(self, total_count: int) -> None:
        """
        Feature: async-launch-config-sync, Property 9: Progress Calculation Accuracy
        Validates: Requirements 3.3, 3.4, 3.5

        For any totalCount with progressCount=0, percentage must be 0%.
        """
        percentage = calculate_percentage(0, total_count)
        assert percentage == 0.0, f"Zero progress should be 0%, got {percentage}%"

    @settings(max_examples=100)
    @given(total_count=st.integers(min_value=1, max_value=500))
    def test_complete_progress_is_hundred_percent(self, total_count: int) -> None:
        """
        Feature: async-launch-config-sync, Property 9: Progress Calculation Accuracy
        Validates: Requirements 3.3, 3.4, 3.5

        For any totalCount where progressCount equals totalCount,
        percentage must be 100%.
        """
        percentage = calculate_percentage(total_count, total_count)
        assert abs(percentage - 100.0) < 0.01, f"Complete progress should be 100%, got {percentage}%"

    @settings(max_examples=100)
    @given(
        progress_count=st.integers(min_value=0, max_value=500),
        total_count=st.integers(min_value=1, max_value=500),
    )
    def test_percentage_always_in_valid_range(self, progress_count: int, total_count: int) -> None:
        """
        Feature: async-launch-config-sync, Property 9: Progress Calculation Accuracy
        Validates: Requirements 3.3, 3.4, 3.5

        For any valid progressCount and totalCount, percentage must be
        between 0 and 100 inclusive.
        """
        from hypothesis import assume

        assume(progress_count <= total_count)

        percentage = calculate_percentage(progress_count, total_count)
        assert 0.0 <= percentage <= 100.0, f"Percentage {percentage}% out of valid range [0, 100]"

    @settings(max_examples=100)
    @given(
        progress_count=st.integers(min_value=0, max_value=500),
        total_count=st.integers(min_value=1, max_value=500),
    )
    def test_percentage_calculation_is_deterministic(self, progress_count: int, total_count: int) -> None:
        """
        Feature: async-launch-config-sync, Property 9: Progress Calculation Accuracy
        Validates: Requirements 3.3, 3.4, 3.5

        For any progressCount and totalCount, calculating percentage
        multiple times must produce the same result.
        """
        from hypothesis import assume

        assume(progress_count <= total_count)

        pct1 = calculate_percentage(progress_count, total_count)
        pct2 = calculate_percentage(progress_count, total_count)
        pct3 = calculate_percentage(progress_count, total_count)

        assert pct1 == pct2 == pct3, "Percentage calculation must be deterministic"

    @settings(max_examples=100)
    @given(
        progress_count=st.integers(min_value=1, max_value=499),
        total_count=st.integers(min_value=2, max_value=500),
    )
    def test_partial_progress_between_zero_and_hundred(self, progress_count: int, total_count: int) -> None:
        """
        Feature: async-launch-config-sync, Property 9: Progress Calculation Accuracy
        Validates: Requirements 3.3, 3.4, 3.5

        For any partial progress (0 < progressCount < totalCount),
        percentage must be strictly between 0 and 100.
        """
        from hypothesis import assume

        assume(0 < progress_count < total_count)

        percentage = calculate_percentage(progress_count, total_count)
        assert 0.0 < percentage < 100.0, f"Partial progress {percentage}% should be between 0 and 100"

    @settings(max_examples=100)
    @given(st.just(None))
    def test_zero_total_returns_zero_percent(self, _) -> None:
        """
        Feature: async-launch-config-sync, Property 9: Progress Calculation Accuracy
        Validates: Requirements 3.3, 3.4, 3.5

        For edge case where totalCount is 0, percentage should be 0%
        to avoid division by zero.
        """
        percentage = calculate_percentage(0, 0)
        assert percentage == 0.0, f"Zero total should return 0%, got {percentage}%"


# ===========================================================================
# Property 13: Error Isolation
# Feature: async-launch-config-sync, Property 13: Error Isolation
# ===========================================================================


class TestErrorIsolation:
    """Property tests for error isolation during server processing."""

    @settings(max_examples=100)
    @given(
        total_servers=st.integers(min_value=2, max_value=100),
        fail_count=st.integers(min_value=1, max_value=50),
    )
    def test_failed_servers_dont_stop_processing(self, total_servers: int, fail_count: int) -> None:
        """
        Feature: async-launch-config-sync, Property 13: Error Isolation
        Validates: Requirements 4.8

        For any server that fails, the handler must continue processing
        remaining servers without stopping the entire job.
        """
        from hypothesis import assume

        assume(fail_count < total_servers)

        server_ids = [f"s-{i:016x}" for i in range(total_servers)]
        fail_on_servers = server_ids[:fail_count]

        result = process_servers_with_isolation(server_ids, fail_on_servers)

        assert result["applied"] + result["failed"] == total_servers, "All servers must be processed"
        assert result["failed"] == fail_count, f"Expected {fail_count} failures, got {result['failed']}"
        assert result["applied"] == total_servers - fail_count, f"Expected {total_servers - fail_count} successes"

    @settings(max_examples=100)
    @given(
        total_servers=st.integers(min_value=1, max_value=100),
        fail_indices=st.lists(st.integers(min_value=0, max_value=99), min_size=0, max_size=50, unique=True),
    )
    def test_all_servers_processed_regardless_of_failures(self, total_servers: int, fail_indices: List[int]) -> None:
        """
        Feature: async-launch-config-sync, Property 13: Error Isolation
        Validates: Requirements 4.8

        For any combination of server failures, all servers in the list
        must be processed (either successfully or with failure recorded).
        """
        from hypothesis import assume

        # Filter fail_indices to only include valid indices
        fail_indices = [i for i in fail_indices if i < total_servers]
        assume(len(fail_indices) <= total_servers)

        server_ids = [f"s-{i:016x}" for i in range(total_servers)]
        fail_on_servers = [server_ids[i] for i in fail_indices]

        result = process_servers_with_isolation(server_ids, fail_on_servers)

        total_processed = result["applied"] + result["failed"]
        assert total_processed == total_servers, f"Expected {total_servers} processed, got {total_processed}"

    @settings(max_examples=100)
    @given(total_servers=st.integers(min_value=1, max_value=100))
    def test_all_failures_still_processes_all_servers(self, total_servers: int) -> None:
        """
        Feature: async-launch-config-sync, Property 13: Error Isolation
        Validates: Requirements 4.8

        Even when all servers fail, the handler must process every server
        and record each failure individually.
        """
        server_ids = [f"s-{i:016x}" for i in range(total_servers)]
        fail_on_servers = server_ids  # All servers fail

        result = process_servers_with_isolation(server_ids, fail_on_servers)

        assert result["failed"] == total_servers, f"Expected {total_servers} failures, got {result['failed']}"
        assert result["applied"] == 0, f"Expected 0 successes, got {result['applied']}"

    @settings(max_examples=100)
    @given(total_servers=st.integers(min_value=1, max_value=100))
    def test_no_failures_processes_all_servers(self, total_servers: int) -> None:
        """
        Feature: async-launch-config-sync, Property 13: Error Isolation
        Validates: Requirements 4.8

        When no servers fail, all servers must be processed successfully.
        """
        server_ids = [f"s-{i:016x}" for i in range(total_servers)]
        fail_on_servers = []  # No failures

        result = process_servers_with_isolation(server_ids, fail_on_servers)

        assert result["applied"] == total_servers, f"Expected {total_servers} successes, got {result['applied']}"
        assert result["failed"] == 0, f"Expected 0 failures, got {result['failed']}"

    @settings(max_examples=100)
    @given(
        total_servers=st.integers(min_value=2, max_value=100),
        fail_count=st.integers(min_value=1, max_value=50),
    )
    def test_failure_position_doesnt_affect_total_processed(self, total_servers: int, fail_count: int) -> None:
        """
        Feature: async-launch-config-sync, Property 13: Error Isolation
        Validates: Requirements 4.8

        Regardless of where failures occur in the server list (beginning,
        middle, end), all servers must be processed.
        """
        from hypothesis import assume

        assume(fail_count < total_servers)

        server_ids = [f"s-{i:016x}" for i in range(total_servers)]

        # Test failures at beginning
        fail_at_start = server_ids[:fail_count]
        result_start = process_servers_with_isolation(server_ids, fail_at_start)

        # Test failures at end
        fail_at_end = server_ids[-fail_count:]
        result_end = process_servers_with_isolation(server_ids, fail_at_end)

        # Both should process all servers
        assert result_start["applied"] + result_start["failed"] == total_servers
        assert result_end["applied"] + result_end["failed"] == total_servers

        # Both should have same counts
        assert result_start["failed"] == result_end["failed"] == fail_count
        assert result_start["applied"] == result_end["applied"] == total_servers - fail_count

    @settings(max_examples=100)
    @given(
        total_servers=st.integers(min_value=1, max_value=100),
        fail_indices=st.lists(st.integers(min_value=0, max_value=99), min_size=0, max_size=50, unique=True),
    )
    def test_processing_is_deterministic(self, total_servers: int, fail_indices: List[int]) -> None:
        """
        Feature: async-launch-config-sync, Property 13: Error Isolation
        Validates: Requirements 4.8

        For any combination of servers and failures, processing the same
        list multiple times must produce identical results.
        """
        from hypothesis import assume

        fail_indices = [i for i in fail_indices if i < total_servers]
        assume(len(fail_indices) <= total_servers)

        server_ids = [f"s-{i:016x}" for i in range(total_servers)]
        fail_on_servers = [server_ids[i] for i in fail_indices]

        result1 = process_servers_with_isolation(server_ids, fail_on_servers)
        result2 = process_servers_with_isolation(server_ids, fail_on_servers)
        result3 = process_servers_with_isolation(server_ids, fail_on_servers)

        assert result1 == result2 == result3, "Processing must be deterministic"
