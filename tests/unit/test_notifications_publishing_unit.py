"""
Unit tests for notification publishing in notifications.py.

Tests publish_recovery_plan_notification() and the updated
send_execution_* functions with optional plan_id parameter
and MessageAttributes.

Validates: Requirements 5.3, 5.4, 5.8, 5.9, 5.11
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch, call

import pytest

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #


@pytest.fixture(autouse=True)
def _env_vars(monkeypatch):
    """Set required environment variables for every test."""
    monkeypatch.setenv(
        "EXECUTION_NOTIFICATIONS_TOPIC_ARN",
        "arn:aws:sns:us-east-1:123456789012:test-topic",
    )


@pytest.fixture(autouse=True)
def _patch_topic_arn():
    """Patch the module-level cached topic ARN."""
    with patch(
        "shared.notifications.EXECUTION_TOPIC_ARN",
        "arn:aws:sns:us-east-1:123456789012:test-topic",
    ):
        yield


@pytest.fixture()
def mock_sns():
    """Patch the module-level SNS client."""
    with patch("shared.notifications.sns") as m:
        yield m


# ------------------------------------------------------------------ #
# publish_recovery_plan_notification
# ------------------------------------------------------------------ #


class TestPublishRecoveryPlanNotification:
    """Tests for publish_recovery_plan_notification."""

    def test_publishes_with_correct_attributes(self, mock_sns):
        """Publish includes recoveryPlanId and eventType."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        publish_recovery_plan_notification(
            plan_id="plan-001",
            event_type="start",
            details={
                "planName": "Prod DR",
                "executionId": "exec-1",
            },
        )

        mock_sns.publish.assert_called_once()
        kwargs = mock_sns.publish.call_args[1]

        assert kwargs["TopicArn"] == ("arn:aws:sns:us-east-1:123456789012:test-topic")
        attrs = kwargs["MessageAttributes"]
        assert attrs["recoveryPlanId"]["StringValue"] == ("plan-001")
        assert attrs["eventType"]["StringValue"] == "start"

    def test_message_body_is_structured_json(self, mock_sns):
        """Message body has default and email keys."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        details = {
            "planName": "Test Plan",
            "executionId": "exec-2",
            "accountId": "123456789012",
        }

        publish_recovery_plan_notification(
            plan_id="plan-002",
            event_type="complete",
            details=details,
        )

        kwargs = mock_sns.publish.call_args[1]
        body = json.loads(kwargs["Message"])
        assert "default" in body
        assert "email" in body
        assert "Test Plan" in body["default"]

    def test_subject_includes_plan_name_and_event(self, mock_sns):
        """Subject line contains plan name and event type."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        publish_recovery_plan_notification(
            plan_id="plan-003",
            event_type="fail",
            details={"planName": "Web Tier DR"},
        )

        kwargs = mock_sns.publish.call_args[1]
        assert "Web Tier DR" in kwargs["Subject"]
        assert "fail" in kwargs["Subject"]

    def test_subject_truncated_at_100_chars(self, mock_sns):
        """SNS subject is capped at 100 characters."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        long_name = "A" * 120
        publish_recovery_plan_notification(
            plan_id="plan-004",
            event_type="start",
            details={"planName": long_name},
        )

        kwargs = mock_sns.publish.call_args[1]
        assert len(kwargs["Subject"]) <= 100
        assert kwargs["Subject"].endswith("...")

    def test_skips_when_topic_not_configured(self, mock_sns):
        """No publish when topic ARN is empty."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        with patch("shared.notifications.EXECUTION_TOPIC_ARN", ""):
            publish_recovery_plan_notification(
                plan_id="plan-005",
                event_type="start",
                details={"planName": "Test"},
            )

        mock_sns.publish.assert_not_called()

    def test_sns_failure_does_not_raise(self, mock_sns):
        """SNS errors are logged but not propagated."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        mock_sns.publish.side_effect = Exception("SNS down")

        # Should not raise
        publish_recovery_plan_notification(
            plan_id="plan-006",
            event_type="fail",
            details={"planName": "Test"},
        )

    def test_all_event_types_publish_correctly(self, mock_sns):
        """All four event types produce valid publishes."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        for event_type in ("start", "complete", "fail", "pause"):
            mock_sns.reset_mock()
            publish_recovery_plan_notification(
                plan_id="plan-007",
                event_type=event_type,
                details={"planName": "Multi-test"},
            )

            kwargs = mock_sns.publish.call_args[1]
            attrs = kwargs["MessageAttributes"]
            assert attrs["eventType"]["StringValue"] == (event_type)

    def test_unknown_plan_name_defaults_to_unknown(self, mock_sns):
        """Missing planName in details defaults to Unknown."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        publish_recovery_plan_notification(
            plan_id="plan-008",
            event_type="start",
            details={},
        )

        kwargs = mock_sns.publish.call_args[1]
        assert "Unknown" in kwargs["Subject"]


# ------------------------------------------------------------------ #
# send_execution_started — MessageAttributes
# ------------------------------------------------------------------ #


class TestSendExecutionStartedAttributes:
    """Tests for send_execution_started with plan_id."""

    def test_includes_attributes_when_plan_id_given(self, mock_sns):
        """MessageAttributes present when plan_id provided."""
        from shared.notifications import (
            send_execution_started,
        )

        send_execution_started(
            execution_id="exec-10",
            plan_name="DR Plan",
            wave_count=3,
            plan_id="plan-100",
        )

        kwargs = mock_sns.publish.call_args[1]
        attrs = kwargs["MessageAttributes"]
        assert attrs["recoveryPlanId"]["StringValue"] == ("plan-100")
        assert attrs["eventType"]["StringValue"] == "start"

    def test_no_attributes_when_plan_id_none(self, mock_sns):
        """No MessageAttributes when plan_id is None."""
        from shared.notifications import (
            send_execution_started,
        )

        send_execution_started(
            execution_id="exec-11",
            plan_name="DR Plan",
            wave_count=3,
        )

        kwargs = mock_sns.publish.call_args[1]
        assert "MessageAttributes" not in kwargs

    def test_backward_compatible_without_plan_id(self, mock_sns):
        """Existing callers without plan_id still work."""
        from shared.notifications import (
            send_execution_started,
        )

        send_execution_started(
            execution_id="exec-12",
            plan_name="Legacy Plan",
            wave_count=2,
            execution_type="DRILL",
        )

        mock_sns.publish.assert_called_once()
        kwargs = mock_sns.publish.call_args[1]
        assert "Legacy Plan" in kwargs["Subject"]


# ------------------------------------------------------------------ #
# send_execution_completed — MessageAttributes
# ------------------------------------------------------------------ #


class TestSendExecutionCompletedAttributes:
    """Tests for send_execution_completed with plan_id."""

    def test_includes_attributes_when_plan_id_given(self, mock_sns):
        """MessageAttributes present when plan_id provided."""
        from shared.notifications import (
            send_execution_completed,
        )

        send_execution_completed(
            execution_id="exec-20",
            plan_name="DR Plan",
            waves_completed=5,
            duration_seconds=1800,
            plan_id="plan-200",
        )

        kwargs = mock_sns.publish.call_args[1]
        attrs = kwargs["MessageAttributes"]
        assert attrs["recoveryPlanId"]["StringValue"] == ("plan-200")
        assert attrs["eventType"]["StringValue"] == "complete"

    def test_no_attributes_when_plan_id_none(self, mock_sns):
        """No MessageAttributes when plan_id is None."""
        from shared.notifications import (
            send_execution_completed,
        )

        send_execution_completed(
            execution_id="exec-21",
            plan_name="DR Plan",
            waves_completed=5,
            duration_seconds=600,
        )

        kwargs = mock_sns.publish.call_args[1]
        assert "MessageAttributes" not in kwargs


# ------------------------------------------------------------------ #
# send_execution_failed — MessageAttributes
# ------------------------------------------------------------------ #


class TestSendExecutionFailedAttributes:
    """Tests for send_execution_failed with plan_id."""

    def test_includes_attributes_when_plan_id_given(self, mock_sns):
        """MessageAttributes present when plan_id provided."""
        from shared.notifications import (
            send_execution_failed,
        )

        send_execution_failed(
            execution_id="exec-30",
            plan_name="DR Plan",
            error_message="Timeout",
            failed_wave=2,
            plan_id="plan-300",
        )

        kwargs = mock_sns.publish.call_args[1]
        attrs = kwargs["MessageAttributes"]
        assert attrs["recoveryPlanId"]["StringValue"] == ("plan-300")
        assert attrs["eventType"]["StringValue"] == "fail"

    def test_no_attributes_when_plan_id_none(self, mock_sns):
        """No MessageAttributes when plan_id is None."""
        from shared.notifications import (
            send_execution_failed,
        )

        send_execution_failed(
            execution_id="exec-31",
            plan_name="DR Plan",
            error_message="Error",
        )

        kwargs = mock_sns.publish.call_args[1]
        assert "MessageAttributes" not in kwargs


# ------------------------------------------------------------------ #
# send_execution_paused — MessageAttributes
# ------------------------------------------------------------------ #


class TestSendExecutionPausedAttributes:
    """Tests for send_execution_paused with plan_id."""

    def test_includes_attributes_when_plan_id_given(self, mock_sns):
        """MessageAttributes present when plan_id provided."""
        from shared.notifications import (
            send_execution_paused,
        )

        send_execution_paused(
            execution_id="exec-40",
            plan_name="DR Plan",
            paused_before_wave=3,
            wave_name="DB Tier",
            plan_id="plan-400",
        )

        kwargs = mock_sns.publish.call_args[1]
        attrs = kwargs["MessageAttributes"]
        assert attrs["recoveryPlanId"]["StringValue"] == ("plan-400")
        assert attrs["eventType"]["StringValue"] == "pause"

    def test_no_attributes_when_plan_id_none(self, mock_sns):
        """No MessageAttributes when plan_id is None."""
        from shared.notifications import (
            send_execution_paused,
        )

        send_execution_paused(
            execution_id="exec-41",
            plan_name="DR Plan",
            paused_before_wave=1,
            wave_name="Infra",
        )

        kwargs = mock_sns.publish.call_args[1]
        assert "MessageAttributes" not in kwargs


# ------------------------------------------------------------------ #
# Graceful failure handling across all send_* functions
# ------------------------------------------------------------------ #


class TestGracefulFailureHandling:
    """All send_* functions log but don't raise on SNS errors."""

    def test_started_does_not_raise_on_sns_error(self, mock_sns):
        """send_execution_started swallows SNS errors."""
        from shared.notifications import (
            send_execution_started,
        )

        mock_sns.publish.side_effect = Exception("boom")
        send_execution_started("exec-e1", "Plan", 1, plan_id="p-1")

    def test_completed_does_not_raise_on_sns_error(self, mock_sns):
        """send_execution_completed swallows SNS errors."""
        from shared.notifications import (
            send_execution_completed,
        )

        mock_sns.publish.side_effect = Exception("boom")
        send_execution_completed("exec-e2", "Plan", 1, 60, plan_id="p-2")

    def test_failed_does_not_raise_on_sns_error(self, mock_sns):
        """send_execution_failed swallows SNS errors."""
        from shared.notifications import (
            send_execution_failed,
        )

        mock_sns.publish.side_effect = Exception("boom")
        send_execution_failed("exec-e3", "Plan", "err", plan_id="p-3")

    def test_paused_does_not_raise_on_sns_error(self, mock_sns):
        """send_execution_paused swallows SNS errors."""
        from shared.notifications import (
            send_execution_paused,
        )

        mock_sns.publish.side_effect = Exception("boom")
        send_execution_paused("exec-e4", "Plan", 1, "Wave", plan_id="p-4")


# ------------------------------------------------------------------ #
# HTML-formatted publish behaviour (Task 2.2)
# ------------------------------------------------------------------ #


class TestPublishHtmlFormattedMessages:
    """Tests for HTML-formatted SNS publishing.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 5.3
    """

    @pytest.mark.parametrize(
        "event_type",
        ["start", "complete", "fail", "pause"],
    )
    def test_valid_event_publishes_with_message_structure(self, mock_sns, event_type):
        """SNS publish uses MessageStructure=json for valid types."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        publish_recovery_plan_notification(
            plan_id="plan-html-01",
            event_type=event_type,
            details={
                "planName": "HTML Test Plan",
                "executionId": "exec-html-1",
            },
        )

        mock_sns.publish.assert_called_once()
        kwargs = mock_sns.publish.call_args[1]
        assert kwargs["MessageStructure"] == "json"

    @pytest.mark.parametrize(
        "event_type",
        ["start", "complete", "fail", "pause"],
    )
    def test_valid_event_message_has_default_and_email(self, mock_sns, event_type):
        """Message body contains default and email keys."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        publish_recovery_plan_notification(
            plan_id="plan-html-02",
            event_type=event_type,
            details={
                "planName": "Structured Plan",
                "executionId": "exec-html-2",
            },
        )

        kwargs = mock_sns.publish.call_args[1]
        body = json.loads(kwargs["Message"])
        assert "default" in body
        assert "email" in body

    @pytest.mark.parametrize(
        "event_type",
        ["start", "complete", "fail", "pause"],
    )
    def test_email_key_contains_formatted_text(self, mock_sns, event_type):
        """Email key contains formatted plain text from formatter."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        publish_recovery_plan_notification(
            plan_id="plan-html-03",
            event_type=event_type,
            details={
                "planName": "HTML Check",
                "executionId": "exec-html-3",
            },
        )

        kwargs = mock_sns.publish.call_args[1]
        body = json.loads(kwargs["Message"])
        assert "=" * 20 in body["email"]

    @pytest.mark.parametrize(
        "event_type",
        ["start", "complete", "fail", "pause"],
    )
    def test_default_key_contains_plan_name(self, mock_sns, event_type):
        """Default key contains the plan name as plain text."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        publish_recovery_plan_notification(
            plan_id="plan-html-04",
            event_type=event_type,
            details={
                "planName": "My DR Plan",
                "executionId": "exec-html-4",
            },
        )

        kwargs = mock_sns.publish.call_args[1]
        body = json.loads(kwargs["Message"])
        assert "My DR Plan" in body["default"]

    def test_formatter_exception_falls_back_to_raw_json(self, mock_sns):
        """Formatter error publishes raw JSON wrapped in default key."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        details = {
            "planName": "Fallback Plan",
            "executionId": "exec-fallback",
        }

        with patch(
            "shared.notifications.format_notification_message",
            side_effect=Exception("format error"),
        ):
            publish_recovery_plan_notification(
                plan_id="plan-fallback-01",
                event_type="start",
                details=details,
            )

        mock_sns.publish.assert_called_once()
        kwargs = mock_sns.publish.call_args[1]

        # MessageStructure is always present (SNS JSON routing)
        assert kwargs["MessageStructure"] == "json"

        # Message body wraps raw details JSON in default key
        body = json.loads(kwargs["Message"])
        assert json.loads(body["default"]) == details

    def test_formatter_exception_still_includes_attributes(self, mock_sns):
        """Fallback publish still includes MessageAttributes."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        with patch(
            "shared.notifications.format_notification_message",
            side_effect=Exception("format error"),
        ):
            publish_recovery_plan_notification(
                plan_id="plan-fallback-02",
                event_type="fail",
                details={"planName": "Attr Check"},
            )

        kwargs = mock_sns.publish.call_args[1]
        attrs = kwargs["MessageAttributes"]
        assert attrs["recoveryPlanId"]["StringValue"] == ("plan-fallback-02")
        assert attrs["eventType"]["StringValue"] == "fail"

    def test_unrecognized_event_type_produces_fallback(self, mock_sns):
        """Unknown event type still publishes with MessageStructure."""
        from shared.notifications import (
            publish_recovery_plan_notification,
        )

        publish_recovery_plan_notification(
            plan_id="plan-unknown-01",
            event_type="unknown_event",
            details={
                "planName": "Unknown Plan",
                "executionId": "exec-unknown",
            },
        )

        mock_sns.publish.assert_called_once()
        kwargs = mock_sns.publish.call_args[1]

        # format_notification_message handles unknown types
        # with a plain-text fallback, so MessageStructure
        # is still "json"
        assert kwargs["MessageStructure"] == "json"

        body = json.loads(kwargs["Message"])
        assert "default" in body
        assert "email" in body
        assert "unknown_event" in body["default"]
        assert "unknown_event" in body["email"]
