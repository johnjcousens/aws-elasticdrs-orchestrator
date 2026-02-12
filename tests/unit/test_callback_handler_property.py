"""
Property-based tests for callback handler task token validation.

Feature: account-context-improvements
Properties:
- Property 10: Invalid Task Token Rejection — For any string
  that is not a valid task token format (length < 100), both
  resume and cancel operations reject it with a ValueError.

**Validates: Requirements 6.5, 6.10**
"""

import importlib
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import (
    given,
    settings,
    HealthCheck,
)
from hypothesis import strategies as st

# Environment variables must be set before importing handler
os.environ.setdefault(
    "PROTECTION_GROUPS_TABLE", "test-pg"
)
os.environ.setdefault(
    "RECOVERY_PLANS_TABLE", "test-rp"
)
os.environ.setdefault(
    "EXECUTION_HISTORY_TABLE", "test-exec"
)
os.environ.setdefault(
    "TARGET_ACCOUNTS_TABLE", "test-accounts"
)
os.environ.setdefault(
    "TAG_SYNC_CONFIG_TABLE", "test-tag-sync"
)
os.environ.setdefault(
    "EXECUTION_NOTIFICATIONS_TOPIC_ARN",
    "arn:aws:sns:us-east-1:123456789012:test-notif",
)

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../lambda")
)

exec_module = importlib.import_module(
    "execution-handler.index"
)


# ============================================================
# Strategies
# ============================================================

# Strings of length 0..99 — all should be rejected
short_token_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "S", "Z"),
    ),
    min_size=0,
    max_size=99,
)

action_strategy = st.sampled_from(["resume", "cancel"])


# ============================================================
# Helpers
# ============================================================

def _build_callback_event(action: str, task_token: str):
    """Build an API Gateway GET event for /execution-callback."""
    return {
        "httpMethod": "GET",
        "path": "/execution-callback",
        "queryStringParameters": {
            "action": action,
            "taskToken": task_token,
        },
        "requestContext": {
            "requestId": "test-cb-prop",
            "apiId": "abc123",
        },
    }


# ============================================================
# Property 10: Invalid Task Token Rejection
# ============================================================

@settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    token=short_token_strategy,
    action=action_strategy,
)
@pytest.mark.property
def test_property_validate_task_token_rejects_short(
    token, action
):
    """
    Property 10: Invalid Task Token Rejection
    (_validate_task_token level).

    For any string with length < 100, _validate_task_token
    raises ValueError regardless of content.

    **Validates: Requirements 6.5, 6.10**
    """
    assert len(token) < 100

    with pytest.raises(ValueError):
        exec_module._validate_task_token(token)


@settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    token=short_token_strategy,
    action=action_strategy,
)
@pytest.mark.property
def test_property_callback_handler_rejects_short_token(
    token, action
):
    """
    Property 10: Invalid Task Token Rejection
    (handle_execution_callback level).

    For any string with length < 100, handle_execution_callback
    returns HTTP 400 for both resume and cancel actions.

    **Validates: Requirements 6.5, 6.10**
    """
    assert len(token) < 100

    event = _build_callback_event(action, token)

    mock_sf = MagicMock()
    with patch.object(
        exec_module, "stepfunctions", mock_sf
    ):
        result = exec_module.handle_execution_callback(event)

    # Must be rejected with 400
    assert result["statusCode"] == 400, (
        f"Expected 400 for short token (len={len(token)}), "
        f"got {result['statusCode']}. "
        f"Action: {action}"
    )
    assert result["headers"]["Content-Type"] == "text/html"

    # Step Functions must NOT be called
    mock_sf.send_task_success.assert_not_called()
    mock_sf.send_task_failure.assert_not_called()


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(action=action_strategy)
@pytest.mark.property
def test_property_empty_token_rejected(action):
    """
    Property 10 (edge case): Empty string tokens are
    always rejected by handle_execution_callback.

    **Validates: Requirements 6.5, 6.10**
    """
    event = _build_callback_event(action, "")

    mock_sf = MagicMock()
    with patch.object(
        exec_module, "stepfunctions", mock_sf
    ):
        result = exec_module.handle_execution_callback(event)

    assert result["statusCode"] == 400
    mock_sf.send_task_success.assert_not_called()
    mock_sf.send_task_failure.assert_not_called()


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(action=action_strategy)
@pytest.mark.property
def test_property_whitespace_only_token_rejected(action):
    """
    Property 10 (edge case): Whitespace-only tokens are
    always rejected by _validate_task_token.

    **Validates: Requirements 6.5, 6.10**
    """
    # Whitespace-only strings of various lengths
    for ws_token in ["", " ", "  ", "\t", "\n", " " * 50]:
        with pytest.raises(ValueError):
            exec_module._validate_task_token(ws_token)


if __name__ == "__main__":
    pytest.main([
        __file__, "-v", "--hypothesis-show-statistics"
    ])
