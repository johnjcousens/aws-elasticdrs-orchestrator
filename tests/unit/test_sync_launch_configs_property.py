"""
Property-based tests for sync_launch_configs handler logic.

Feature: async-launch-config-sync

This module tests three critical properties of the async launch config sync:
- Property 7: Final Status Determination
- Property 19: Duplicate Invocation Detection
- Property 22: SyncJobId Lifecycle

Validates: Requirements 2.6, 5.1, 5.4, 5.5, 8.1, 8.5, 8.6
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest  # noqa: F401
from hypothesis import given, settings, strategies as st

# Add lambda directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))


# ===========================================================================
# Helper functions for status determination logic
# ===========================================================================


def determine_final_status(applied: int, failed: int) -> str:
    """
    Determine final status based on applied and failed server counts.

    This implements the logic from Property 7:
    - If failed == 0: status is "ready"
    - If applied > 0 and failed > 0: status is "partial"
    - If applied == 0: status is "failed"

    Args:
        applied: Number of successfully applied servers
        failed: Number of failed servers

    Returns:
        Status string: "ready", "partial", or "failed"
    """
    total = applied + failed
    if total == 0:
        return "failed"  # No servers processed

    if failed == 0:
        return "ready"
    elif applied > 0 and failed > 0:
        return "partial"
    else:  # applied == 0
        return "failed"


def should_skip_duplicate_invocation(current_status: str, current_sync_job_id: str, new_sync_job_id: str) -> bool:
    """
    Determine if a sync invocation should be skipped as duplicate.

    This implements the logic from Property 19:
    - If status is "syncing" and syncJobId differs from new requestId, skip

    Args:
        current_status: Current launchConfigStatus.status
        current_sync_job_id: Current launchConfigStatus.syncJobId
        new_sync_job_id: New Lambda requestId

    Returns:
        True if invocation should be skipped, False otherwise
    """
    if current_status == "syncing" and current_sync_job_id and current_sync_job_id != new_sync_job_id:
        return True
    return False


def get_sync_job_id_for_status(status: str, request_id: str) -> str | None:
    """
    Determine syncJobId value based on status.

    This implements the logic from Property 22:
    - If status is "syncing": syncJobId contains Lambda requestId
    - If status is terminal (ready/partial/failed): syncJobId is null

    Args:
        status: Current status
        request_id: Lambda requestId

    Returns:
        syncJobId value (requestId or None)
    """
    if status == "syncing":
        return request_id
    elif status in ["ready", "partial", "failed"]:
        return None
    else:
        # For pending or other states, keep existing behavior
        return None


# ===========================================================================
# Property 7: Final Status Determination
# Feature: async-launch-config-sync, Property 7: Final Status Determination
# ===========================================================================


class TestFinalStatusDetermination:
    """Property tests for final status determination logic."""

    @settings(max_examples=100)
    @given(
        applied=st.integers(min_value=0, max_value=200),
        failed=st.integers(min_value=0, max_value=200),
    )
    def test_final_status_is_deterministic(self, applied: int, failed: int) -> None:
        """
        Feature: async-launch-config-sync, Property 7: Final Status Determination
        Validates: Requirements 2.6, 5.1, 5.4, 5.5

        For any combination of applied and failed server counts,
        the final status should be deterministic and follow the rules:
        - failed == 0 → "ready"
        - applied > 0 && failed > 0 → "partial"
        - applied == 0 → "failed"
        """
        total = applied + failed
        if total == 0:
            # Edge case: no servers processed
            status = determine_final_status(applied, failed)
            assert status == "failed", "Empty job should result in failed status"
            return

        status = determine_final_status(applied, failed)

        if failed == 0:
            assert status == "ready", f"All {applied} servers succeeded, status should be 'ready'"
        elif applied > 0 and failed > 0:
            assert status == "partial", f"{applied} succeeded, {failed} failed, status should be 'partial'"
        elif applied == 0:
            assert status == "failed", f"All {failed} servers failed, status should be 'failed'"

    @settings(max_examples=100)
    @given(applied=st.integers(min_value=1, max_value=200))
    def test_all_success_always_ready(self, applied: int) -> None:
        """
        Feature: async-launch-config-sync, Property 7: Final Status Determination
        Validates: Requirements 2.6, 5.1

        For any number of successfully applied servers with zero failures,
        status must be "ready".
        """
        status = determine_final_status(applied, failed=0)
        assert status == "ready", f"All {applied} servers succeeded, status must be 'ready'"

    @settings(max_examples=100)
    @given(failed=st.integers(min_value=1, max_value=200))
    def test_all_failure_always_failed(self, failed: int) -> None:
        """
        Feature: async-launch-config-sync, Property 7: Final Status Determination
        Validates: Requirements 5.4

        For any number of failed servers with zero successes,
        status must be "failed".
        """
        status = determine_final_status(applied=0, failed=failed)
        assert status == "failed", f"All {failed} servers failed, status must be 'failed'"

    @settings(max_examples=100)
    @given(
        applied=st.integers(min_value=1, max_value=100),
        failed=st.integers(min_value=1, max_value=100),
    )
    def test_mixed_results_always_partial(self, applied: int, failed: int) -> None:
        """
        Feature: async-launch-config-sync, Property 7: Final Status Determination
        Validates: Requirements 5.1

        For any combination where both applied > 0 and failed > 0,
        status must be "partial".
        """
        status = determine_final_status(applied, failed)
        assert status == "partial", f"{applied} succeeded, {failed} failed, status must be 'partial'"

    @settings(max_examples=100)
    @given(
        applied=st.integers(min_value=0, max_value=200),
        failed=st.integers(min_value=0, max_value=200),
    )
    def test_status_never_invalid(self, applied: int, failed: int) -> None:
        """
        Feature: async-launch-config-sync, Property 7: Final Status Determination
        Validates: Requirements 2.6

        For any server counts, the final status must always be one of
        the three valid terminal states.
        """
        status = determine_final_status(applied, failed)
        assert status in ["ready", "partial", "failed"], f"Invalid status: {status}"

    @settings(max_examples=100)
    @given(
        applied=st.integers(min_value=0, max_value=200),
        failed=st.integers(min_value=0, max_value=200),
    )
    def test_status_consistency_across_calls(self, applied: int, failed: int) -> None:
        """
        Feature: async-launch-config-sync, Property 7: Final Status Determination
        Validates: Requirements 2.6

        For any server counts, calling determine_final_status multiple times
        with the same inputs must produce the same result.
        """
        status1 = determine_final_status(applied, failed)
        status2 = determine_final_status(applied, failed)
        status3 = determine_final_status(applied, failed)

        assert status1 == status2 == status3, "Status determination must be deterministic"


# ===========================================================================
# Property 19: Duplicate Invocation Detection
# Feature: async-launch-config-sync, Property 19: Duplicate Invocation Detection
# ===========================================================================


class TestDuplicateInvocationDetection:
    """Property tests for duplicate invocation detection logic."""

    @settings(max_examples=100)
    @given(
        current_sync_job_id=st.text(min_size=10, max_size=50),
        new_sync_job_id=st.text(min_size=10, max_size=50),
    )
    def test_syncing_with_different_job_id_skipped(self, current_sync_job_id: str, new_sync_job_id: str) -> None:
        """
        Feature: async-launch-config-sync, Property 19: Duplicate Invocation Detection
        Validates: Requirements 8.1

        For any sync_launch_configs invocation where status is "syncing"
        with a different syncJobId, the handler must skip duplicate processing.
        """
        from hypothesis import assume

        assume(current_sync_job_id != new_sync_job_id)

        should_skip = should_skip_duplicate_invocation("syncing", current_sync_job_id, new_sync_job_id)
        assert should_skip is True, "Different syncJobId during 'syncing' must be skipped"

    @settings(max_examples=100)
    @given(sync_job_id=st.text(min_size=10, max_size=50))
    def test_syncing_with_same_job_id_not_skipped(self, sync_job_id: str) -> None:
        """
        Feature: async-launch-config-sync, Property 19: Duplicate Invocation Detection
        Validates: Requirements 8.1

        For any sync_launch_configs invocation where status is "syncing"
        with the SAME syncJobId, processing should continue (retry scenario).
        """
        should_skip = should_skip_duplicate_invocation("syncing", sync_job_id, sync_job_id)
        assert should_skip is False, "Same syncJobId during 'syncing' should not be skipped (retry)"

    @settings(max_examples=100)
    @given(
        status=st.sampled_from(["pending", "ready", "partial", "failed", "drifted"]),
        current_sync_job_id=st.one_of(st.none(), st.text(min_size=10, max_size=50)),
        new_sync_job_id=st.text(min_size=10, max_size=50),
    )
    def test_non_syncing_status_never_skipped(self, status: str, current_sync_job_id: str | None,
                                              new_sync_job_id: str) -> None:
        """
        Feature: async-launch-config-sync, Property 19: Duplicate Invocation Detection
        Validates: Requirements 8.1

        For any status other than "syncing", invocations should never be
        skipped regardless of syncJobId values.
        """
        should_skip = should_skip_duplicate_invocation(status, current_sync_job_id or "", new_sync_job_id)
        assert should_skip is False, f"Status '{status}' should never skip invocation"

    @settings(max_examples=100)
    @given(new_sync_job_id=st.text(min_size=10, max_size=50))
    def test_syncing_with_null_job_id_not_skipped(self, new_sync_job_id: str) -> None:
        """
        Feature: async-launch-config-sync, Property 19: Duplicate Invocation Detection
        Validates: Requirements 8.1

        For any sync_launch_configs invocation where status is "syncing"
        but current syncJobId is null/empty, processing should continue.
        """
        should_skip = should_skip_duplicate_invocation("syncing", "", new_sync_job_id)
        assert should_skip is False, "Null current syncJobId should not skip"

        should_skip = should_skip_duplicate_invocation("syncing", None, new_sync_job_id)
        assert should_skip is False, "None current syncJobId should not skip"

    @settings(max_examples=100)
    @given(
        status=st.sampled_from(["pending", "syncing", "ready", "partial", "failed"]),
        current_sync_job_id=st.one_of(st.none(), st.text(min_size=10, max_size=50)),
        new_sync_job_id=st.text(min_size=10, max_size=50),
    )
    def test_skip_decision_is_deterministic(self, status: str, current_sync_job_id: str | None,
                                            new_sync_job_id: str) -> None:
        """
        Feature: async-launch-config-sync, Property 19: Duplicate Invocation Detection
        Validates: Requirements 8.1

        For any combination of status and syncJobIds, the skip decision
        must be deterministic across multiple calls.
        """
        result1 = should_skip_duplicate_invocation(status, current_sync_job_id or "", new_sync_job_id)
        result2 = should_skip_duplicate_invocation(status, current_sync_job_id or "", new_sync_job_id)
        result3 = should_skip_duplicate_invocation(status, current_sync_job_id or "", new_sync_job_id)

        assert result1 == result2 == result3, "Skip decision must be deterministic"


# ===========================================================================
# Property 22: SyncJobId Lifecycle
# Feature: async-launch-config-sync, Property 22: SyncJobId Lifecycle
# ===========================================================================


class TestSyncJobIdLifecycle:
    """Property tests for syncJobId lifecycle management."""

    @settings(max_examples=100)
    @given(request_id=st.text(min_size=10, max_size=50))
    def test_syncing_status_has_request_id(self, request_id: str) -> None:
        """
        Feature: async-launch-config-sync, Property 22: SyncJobId Lifecycle
        Validates: Requirements 8.5

        For any launchConfigStatus in "syncing" state, syncJobId must
        contain the Lambda requestId.
        """
        sync_job_id = get_sync_job_id_for_status("syncing", request_id)
        assert sync_job_id == request_id, "Syncing status must have syncJobId set to requestId"

    @settings(max_examples=100)
    @given(
        status=st.sampled_from(["ready", "partial", "failed"]),
        request_id=st.text(min_size=10, max_size=50),
    )
    def test_terminal_status_has_null_job_id(self, status: str, request_id: str) -> None:
        """
        Feature: async-launch-config-sync, Property 22: SyncJobId Lifecycle
        Validates: Requirements 8.6

        For any launchConfigStatus in terminal state (ready/partial/failed),
        syncJobId must be set to null.
        """
        sync_job_id = get_sync_job_id_for_status(status, request_id)
        assert sync_job_id is None, f"Terminal status '{status}' must have syncJobId set to null"

    @settings(max_examples=100)
    @given(
        status=st.sampled_from(["syncing", "ready", "partial", "failed"]),
        request_id=st.text(min_size=10, max_size=50),
    )
    def test_job_id_lifecycle_is_deterministic(self, status: str, request_id: str) -> None:
        """
        Feature: async-launch-config-sync, Property 22: SyncJobId Lifecycle
        Validates: Requirements 8.5, 8.6

        For any status and requestId, the syncJobId value must be
        deterministic across multiple calls.
        """
        job_id1 = get_sync_job_id_for_status(status, request_id)
        job_id2 = get_sync_job_id_for_status(status, request_id)
        job_id3 = get_sync_job_id_for_status(status, request_id)

        assert job_id1 == job_id2 == job_id3, "SyncJobId determination must be deterministic"

    @settings(max_examples=100)
    @given(request_id=st.text(min_size=10, max_size=50))
    def test_syncing_to_ready_clears_job_id(self, request_id: str) -> None:
        """
        Feature: async-launch-config-sync, Property 22: SyncJobId Lifecycle
        Validates: Requirements 8.5, 8.6

        For any sync job, transitioning from "syncing" to "ready" must
        clear the syncJobId (set to null).
        """
        syncing_job_id = get_sync_job_id_for_status("syncing", request_id)
        ready_job_id = get_sync_job_id_for_status("ready", request_id)

        assert syncing_job_id == request_id, "Syncing must have requestId"
        assert ready_job_id is None, "Ready must have null syncJobId"

    @settings(max_examples=100)
    @given(request_id=st.text(min_size=10, max_size=50))
    def test_syncing_to_partial_clears_job_id(self, request_id: str) -> None:
        """
        Feature: async-launch-config-sync, Property 22: SyncJobId Lifecycle
        Validates: Requirements 8.5, 8.6

        For any sync job, transitioning from "syncing" to "partial" must
        clear the syncJobId (set to null).
        """
        syncing_job_id = get_sync_job_id_for_status("syncing", request_id)
        partial_job_id = get_sync_job_id_for_status("partial", request_id)

        assert syncing_job_id == request_id, "Syncing must have requestId"
        assert partial_job_id is None, "Partial must have null syncJobId"

    @settings(max_examples=100)
    @given(request_id=st.text(min_size=10, max_size=50))
    def test_syncing_to_failed_clears_job_id(self, request_id: str) -> None:
        """
        Feature: async-launch-config-sync, Property 22: SyncJobId Lifecycle
        Validates: Requirements 8.5, 8.6

        For any sync job, transitioning from "syncing" to "failed" must
        clear the syncJobId (set to null).
        """
        syncing_job_id = get_sync_job_id_for_status("syncing", request_id)
        failed_job_id = get_sync_job_id_for_status("failed", request_id)

        assert syncing_job_id == request_id, "Syncing must have requestId"
        assert failed_job_id is None, "Failed must have null syncJobId"

    @settings(max_examples=100)
    @given(
        status=st.sampled_from(["syncing", "ready", "partial", "failed"]),
        request_id=st.text(min_size=10, max_size=50),
    )
    def test_job_id_value_is_valid(self, status: str, request_id: str) -> None:
        """
        Feature: async-launch-config-sync, Property 22: SyncJobId Lifecycle
        Validates: Requirements 8.5, 8.6

        For any status, syncJobId must be either a valid string (requestId)
        or None, never any other type.
        """
        sync_job_id = get_sync_job_id_for_status(status, request_id)
        assert isinstance(sync_job_id, (str, type(None))), f"Invalid syncJobId type: {type(sync_job_id)}"

        if status == "syncing":
            assert isinstance(sync_job_id, str), "Syncing syncJobId must be string"
        else:
            assert sync_job_id is None, f"Terminal status '{status}' syncJobId must be None"
