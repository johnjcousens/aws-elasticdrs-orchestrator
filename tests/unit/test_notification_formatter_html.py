"""
Unit tests for notification formatter HTML email templates.

Tests cover:
- format_start_notification: plan name, execution ID, timestamp, wave count
- format_complete_notification: plan name, execution ID, timestamp, duration
- format_failure_notification: plan name, execution ID, timestamp, error
- format_pause_notification: plan name, execution ID, timestamp, action URLs
- format_notification_message: routing for all event types + unknown fallback
- HTML well-formedness (DOCTYPE, closing tags)
- Console link presence in all templates
- Pause button href attributes

Validates: Requirements 5.4, 5.10, 6.2, 6.3
"""

import pytest

from shared.notifications import (
    format_complete_notification,
    format_failure_notification,
    format_notification_message,
    format_pause_notification,
    format_start_notification,
)


# ── Shared test fixtures ────────────────────────────────────────

@pytest.fixture()
def base_details():
    """Minimal details dict shared by all formatters."""
    return {
        "planName": "Production DR Plan",
        "executionId": "exec-abc-123",
        "accountId": "123456789012",
        "timestamp": "2026-02-11 14:30:00 UTC",
        "consoleLink": "https://console.aws.amazon.com/test",
    }


@pytest.fixture()
def start_details(base_details):
    """Details for a start notification."""
    return {
        **base_details,
        "waveCount": 3,
        "executionType": "RECOVERY",
    }


@pytest.fixture()
def complete_details(base_details):
    """Details for a completion notification."""
    return {
        **base_details,
        "duration": "12m 34s",
        "wavesCompleted": 3,
    }


@pytest.fixture()
def failure_details(base_details):
    """Details for a failure notification."""
    return {
        **base_details,
        "errorMessage": "Timeout waiting for instances",
        "failedWave": "Wave 2",
    }


@pytest.fixture()
def pause_details(base_details):
    """Details for a pause notification with action URLs."""
    return {
        **base_details,
        "pauseReason": "Pre-wave approval required",
        "resumeUrl": (
            "https://api.example.com/execution-callback"
            "?action=resume&taskToken=tok123"
        ),
        "cancelUrl": (
            "https://api.example.com/execution-callback"
            "?action=cancel&taskToken=tok123"
        ),
    }


# ── HTML well-formedness helpers ────────────────────────────────

def _assert_well_formed_html(html: str) -> None:
    """Assert the HTML string has basic well-formedness."""
    assert html.startswith("<!DOCTYPE html>")
    assert "<html>" in html
    assert "</html>" in html
    assert "<head>" in html
    assert "</head>" in html
    assert "<body>" in html
    assert "</body>" in html


def _assert_contains_info_box_fields(
    html: str,
    details: dict,
) -> None:
    """Assert the info box contains plan name, exec ID, timestamp."""
    assert details["planName"] in html
    assert details["executionId"] in html
    assert details["timestamp"] in html


def _assert_contains_console_link(html: str) -> None:
    """Assert the HTML contains a console link."""
    assert "View in AWS Console" in html
    assert 'href="' in html


# ── format_start_notification tests ─────────────────────────────

class TestFormatStartNotification:
    """Tests for format_start_notification."""

    def test_contains_plan_name_and_execution_id(
        self, start_details
    ):
        """Start email includes plan name and execution ID."""
        html = format_start_notification(start_details)
        _assert_contains_info_box_fields(html, start_details)

    def test_contains_wave_count(self, start_details):
        """Start email shows total wave count."""
        html = format_start_notification(start_details)
        assert "3" in html

    def test_contains_execution_type(self, start_details):
        """Start email shows execution type."""
        html = format_start_notification(start_details)
        assert "RECOVERY" in html

    def test_html_is_well_formed(self, start_details):
        """Start email is a complete HTML document."""
        html = format_start_notification(start_details)
        _assert_well_formed_html(html)

    def test_contains_console_link(self, start_details):
        """Start email includes a console link."""
        html = format_start_notification(start_details)
        _assert_contains_console_link(html)

    def test_contains_started_indicator(self, start_details):
        """Start email indicates the execution started."""
        html = format_start_notification(start_details)
        assert "started" in html.lower()


# ── format_complete_notification tests ──────────────────────────

class TestFormatCompleteNotification:
    """Tests for format_complete_notification."""

    def test_contains_plan_name_and_execution_id(
        self, complete_details
    ):
        """Complete email includes plan name and execution ID."""
        html = format_complete_notification(complete_details)
        _assert_contains_info_box_fields(
            html, complete_details
        )

    def test_contains_duration(self, complete_details):
        """Complete email shows execution duration."""
        html = format_complete_notification(complete_details)
        assert "12m 34s" in html

    def test_contains_waves_completed(self, complete_details):
        """Complete email shows waves completed count."""
        html = format_complete_notification(complete_details)
        assert "3" in html

    def test_html_is_well_formed(self, complete_details):
        """Complete email is a complete HTML document."""
        html = format_complete_notification(complete_details)
        _assert_well_formed_html(html)

    def test_contains_console_link(self, complete_details):
        """Complete email includes a console link."""
        html = format_complete_notification(complete_details)
        _assert_contains_console_link(html)

    def test_contains_completed_indicator(
        self, complete_details
    ):
        """Complete email indicates successful completion."""
        html = format_complete_notification(complete_details)
        assert "completed" in html.lower()


# ── format_failure_notification tests ───────────────────────────

class TestFormatFailureNotification:
    """Tests for format_failure_notification."""

    def test_contains_plan_name_and_execution_id(
        self, failure_details
    ):
        """Failure email includes plan name and execution ID."""
        html = format_failure_notification(failure_details)
        _assert_contains_info_box_fields(
            html, failure_details
        )

    def test_contains_error_message(self, failure_details):
        """Failure email shows the error message."""
        html = format_failure_notification(failure_details)
        assert "Timeout waiting for instances" in html

    def test_contains_failed_wave(self, failure_details):
        """Failure email shows which wave failed."""
        html = format_failure_notification(failure_details)
        assert "Wave 2" in html

    def test_html_is_well_formed(self, failure_details):
        """Failure email is a complete HTML document."""
        html = format_failure_notification(failure_details)
        _assert_well_formed_html(html)

    def test_contains_console_link(self, failure_details):
        """Failure email includes a console link."""
        html = format_failure_notification(failure_details)
        _assert_contains_console_link(html)

    def test_contains_failed_indicator(self, failure_details):
        """Failure email indicates the execution failed."""
        html = format_failure_notification(failure_details)
        assert "failed" in html.lower()


# ── format_pause_notification tests ─────────────────────────────

class TestFormatPauseNotification:
    """Tests for format_pause_notification."""

    def test_contains_plan_name_and_execution_id(
        self, pause_details
    ):
        """Pause email includes plan name and execution ID."""
        html = format_pause_notification(pause_details)
        _assert_contains_info_box_fields(
            html, pause_details
        )

    def test_contains_resume_url(self, pause_details):
        """Pause email contains the resume action URL."""
        html = format_pause_notification(pause_details)
        assert pause_details["resumeUrl"] in html

    def test_contains_cancel_url(self, pause_details):
        """Pause email contains the cancel action URL."""
        html = format_pause_notification(pause_details)
        assert pause_details["cancelUrl"] in html

    def test_resume_button_has_correct_href(
        self, pause_details
    ):
        """Resume button href points to the resume URL."""
        html = format_pause_notification(pause_details)
        expected = f'href="{pause_details["resumeUrl"]}"'
        assert expected in html

    def test_cancel_button_has_correct_href(
        self, pause_details
    ):
        """Cancel button href points to the cancel URL."""
        html = format_pause_notification(pause_details)
        expected = f'href="{pause_details["cancelUrl"]}"'
        assert expected in html

    def test_contains_pause_reason(self, pause_details):
        """Pause email shows the pause reason."""
        html = format_pause_notification(pause_details)
        assert "Pre-wave approval required" in html

    def test_html_is_well_formed(self, pause_details):
        """Pause email is a complete HTML document."""
        html = format_pause_notification(pause_details)
        _assert_well_formed_html(html)

    def test_contains_console_link(self, pause_details):
        """Pause email includes a console link."""
        html = format_pause_notification(pause_details)
        _assert_contains_console_link(html)

    def test_contains_paused_indicator(self, pause_details):
        """Pause email indicates the execution is paused."""
        html = format_pause_notification(pause_details)
        assert "paused" in html.lower()

    def test_no_buttons_when_urls_missing(
        self, base_details
    ):
        """Pause email omits action buttons when URLs absent."""
        html = format_pause_notification(base_details)
        assert "Resume Execution" not in html
        assert "Cancel Execution" not in html


# ── format_notification_message routing tests ───────────────────

class TestFormatNotificationMessage:
    """Tests for format_notification_message routing."""

    def test_routes_start_event(self, start_details):
        """'start' event routes to start formatter."""
        result = format_notification_message(
            "start", start_details
        )
        assert "default" in result
        assert "email" in result
        assert "Started" in result["default"]
        _assert_well_formed_html(result["email"])

    def test_routes_complete_event(self, complete_details):
        """'complete' event routes to complete formatter."""
        result = format_notification_message(
            "complete", complete_details
        )
        assert "Completed" in result["default"]
        _assert_well_formed_html(result["email"])

    def test_routes_fail_event(self, failure_details):
        """'fail' event routes to failure formatter."""
        result = format_notification_message(
            "fail", failure_details
        )
        assert "Failed" in result["default"]
        _assert_well_formed_html(result["email"])

    def test_routes_pause_event(self, pause_details):
        """'pause' event routes to pause formatter."""
        result = format_notification_message(
            "pause", pause_details
        )
        assert "Paused" in result["default"]
        _assert_well_formed_html(result["email"])

    def test_unknown_event_returns_fallback(
        self, base_details
    ):
        """Unknown event type returns plain-text fallback."""
        result = format_notification_message(
            "unknown_event", base_details
        )
        assert "unknown_event" in result["default"]
        # Fallback is not HTML — no DOCTYPE
        assert "<!DOCTYPE html>" not in result["email"]

    def test_default_message_includes_plan_name(
        self, base_details
    ):
        """Default text message includes the plan name."""
        for event_type in ("start", "complete", "fail", "pause"):
            result = format_notification_message(
                event_type, base_details
            )
            assert "Production DR Plan" in result["default"]
