"""
Property-based tests for notification utilities.

Feature: account-context-improvements
Properties:
- Property 5: Email Format Validation
- Property 7: Notification Delivery for All Event Types

Validates: Requirements 5.3, 5.6
"""

import json
import os
import sys
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.security_utils import validate_email  # noqa: E402




# ============================================================
# Property 5: Email Format Validation
# ============================================================


@settings(max_examples=300)
@given(text=st.text())
@pytest.mark.property
def test_property_email_format_validation(text):
    """
    Property 5: Email Format Validation.

    For any string, validate_email returns True only if the
    string contains @ followed by a domain with at least
    one dot.

    **Validates: Requirements 5.3, 5.6**
    """
    result = validate_email(text)

    if result:
        # If validate_email says True, the string MUST
        # contain '@' followed by a domain with at least
        # one '.'.
        assert "@" in text, f"validate_email returned True but string " f"has no '@': {text!r}"
        local_part, _, domain = text.partition("@")
        assert "." in domain, (
            f"validate_email returned True but domain " f"has no '.': domain={domain!r}, " f"full={text!r}"
        )


@settings(max_examples=100)
@given(
    local=st.from_regex(r"[a-zA-Z0-9._%+-]+", fullmatch=True),
    domain=st.from_regex(r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", fullmatch=True),
)
@pytest.mark.property
def test_property_email_valid_format_accepted(local, domain):
    """
    Property 5 (supplemental): Well-formed emails are accepted.

    For any string matching local@domain.tld pattern,
    validate_email returns True.

    **Validates: Requirements 5.3, 5.6**
    """
    email = f"{local}@{domain}"
    assert validate_email(email), f"validate_email should accept well-formed email: " f"{email!r}"


@pytest.mark.property
def test_property_email_rejects_non_strings():
    """
    Property 5 (edge case): Non-string inputs return False.

    **Validates: Requirements 5.6**
    """
    assert validate_email(None) is False
    assert validate_email(123) is False
    assert validate_email([]) is False
    assert validate_email({}) is False


@pytest.mark.property
def test_property_email_rejects_missing_at():
    """
    Property 5 (edge case): Strings without @ are rejected.

    **Validates: Requirements 5.6**
    """
    assert validate_email("nodomain") is False
    assert validate_email("just.dots.here") is False
    assert validate_email("") is False


@pytest.mark.property
def test_property_email_rejects_missing_domain_dot():
    """
    Property 5 (edge case): Strings with @ but no domain dot
    are rejected.

    **Validates: Requirements 5.6**
    """
    assert validate_email("user@nodot") is False
    assert validate_email("user@") is False


# ============================================================
# Property 7: Notification Delivery for All Event Types
# ============================================================


@settings(max_examples=200)
@given(
    event_type=st.sampled_from(["start", "complete", "fail", "pause"]),
    plan_id=st.uuids().map(str),
    plan_name=st.text(min_size=1, max_size=100),
)
@pytest.mark.property
def test_property_notification_delivery_all_event_types(
    event_type,
    plan_id,
    plan_name,
):
    """
    Property 7: Notification Delivery for All Event Types.

    For any event type in ["start", "complete", "fail",
    "pause"], publish_recovery_plan_notification calls SNS
    publish with correct recoveryPlanId and eventType
    message attributes.

    **Validates: Requirements 5.3, 5.6**
    """
    topic_arn = "arn:aws:sns:us-east-1:123456789012:test-topic"

    with patch.dict(
        os.environ,
        {"EXECUTION_NOTIFICATIONS_TOPIC_ARN": topic_arn},
    ):
        # Re-import to pick up patched env var
        import shared.notifications as notif_mod

        original_arn = notif_mod.EXECUTION_TOPIC_ARN
        notif_mod.EXECUTION_TOPIC_ARN = topic_arn

        try:
            with patch.object(notif_mod, "sns") as mock_sns:
                notif_mod.publish_recovery_plan_notification(
                    plan_id=plan_id,
                    event_type=event_type,
                    details={
                        "planName": plan_name,
                        "executionId": "exec-test",
                    },
                )

                mock_sns.publish.assert_called_once()
                call_kwargs = mock_sns.publish.call_args[1]

                # Verify TopicArn
                assert call_kwargs["TopicArn"] == topic_arn

                # Verify MessageAttributes contain
                # recoveryPlanId
                attrs = call_kwargs["MessageAttributes"]
                assert "recoveryPlanId" in attrs, "MessageAttributes must include " "recoveryPlanId"
                assert attrs["recoveryPlanId"]["StringValue"] == plan_id, (
                    f"recoveryPlanId should be {plan_id}, " f"got " f"{attrs['recoveryPlanId']['StringValue']}"
                )
                assert attrs["recoveryPlanId"]["DataType"] == "String"

                # Verify MessageAttributes contain
                # eventType
                assert "eventType" in attrs, "MessageAttributes must include " "eventType"
                assert attrs["eventType"]["StringValue"] == event_type, (
                    f"eventType should be {event_type}, " f"got " f"{attrs['eventType']['StringValue']}"
                )
                assert attrs["eventType"]["DataType"] == "String"

                # Verify message body is structured JSON
                # with "default" and "email" keys
                # (MessageStructure="json" format)
                body = json.loads(call_kwargs["Message"])
                assert "default" in body, (
                    "Message body must contain 'default' key"
                )
                assert "email" in body, (
                    "Message body must contain 'email' key"
                )
                assert plan_name in body["default"], (
                    f"Plan name '{plan_name}' should appear "
                    f"in default message"
                )
                assert plan_name in body["email"], (
                    f"Plan name '{plan_name}' should appear "
                    f"in email HTML body"
                )
                assert (
                    call_kwargs.get("MessageStructure")
                    == "json"
                )
        finally:
            notif_mod.EXECUTION_TOPIC_ARN = original_arn


@pytest.mark.property
def test_property_notification_skips_without_topic():
    """
    Property 7 (edge case): When topic ARN is not configured,
    publish_recovery_plan_notification does not call SNS.

    **Validates: Requirements 5.3**
    """
    import shared.notifications as notif_mod

    original_arn = notif_mod.EXECUTION_TOPIC_ARN
    notif_mod.EXECUTION_TOPIC_ARN = ""

    try:
        with patch.object(notif_mod, "sns") as mock_sns:
            notif_mod.publish_recovery_plan_notification(
                plan_id="plan-123",
                event_type="start",
                details={"planName": "Test"},
            )
            mock_sns.publish.assert_not_called()
    finally:
        notif_mod.EXECUTION_TOPIC_ARN = original_arn
