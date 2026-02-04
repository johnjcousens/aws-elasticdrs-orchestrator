"""
Unit tests for query-handler action-based routing.

Tests the lambda_handler's ability to route action-based invocations
from the orchestration Lambda.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Set environment variables before importing
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts-table"
os.environ["STAGING_ACCOUNTS_TABLE"] = "test-staging-accounts-table"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history-table"
os.environ["EXECUTION_HANDLER_ARN"] = (
    "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
)

# Clear any existing index module to avoid conflicts
if "index" in sys.modules:
    del sys.modules["index"]

# Add lambda paths for imports - query-handler FIRST
query_handler_dir = (
    Path(__file__).parent.parent.parent / "lambda" / "query-handler"
)
shared_dir = Path(__file__).parent.parent.parent / "lambda" / "shared"

sys.path.insert(0, str(query_handler_dir))
sys.path.insert(1, str(shared_dir))


@pytest.fixture
def lambda_context():
    """Mock Lambda context"""
    context = MagicMock()
    context.function_name = "query-handler"
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
    )
    return context


def test_action_unknown_action(lambda_context):
    """Test that unknown action returns error"""
    from index import lambda_handler

    # Create event with unknown action
    event = {"action": "unknown_action", "state": {}}

    # Invoke lambda_handler
    result = lambda_handler(event, lambda_context)

    # Verify error response
    assert "error" in result
    assert result["error"] == "Unknown action"
    assert result["action"] == "unknown_action"


def test_action_poll_wave_status_exists(lambda_context):
    """Test that poll_wave_status action is recognized"""
    from index import lambda_handler

    # Create event with poll_wave_status action but minimal state
    # This will fail in poll_wave_status but proves routing works
    event = {"action": "poll_wave_status", "state": {}}

    # Invoke lambda_handler
    result = lambda_handler(event, lambda_context)

    # Should not return "Unknown action" error
    # Instead should return result from poll_wave_status
    assert "error" not in result or result.get("error") != "Unknown action"
    # Should have wave_completed flag from poll_wave_status
    assert "wave_completed" in result


def test_invocation_pattern_detection_api_gateway(lambda_context):
    """Test that API Gateway pattern is detected correctly"""
    from index import lambda_handler

    # Create API Gateway event
    event = {
        "requestContext": {"requestId": "test-123"},
        "httpMethod": "GET",
        "path": "/drs/accounts",
    }

    # Invoke lambda_handler
    result = lambda_handler(event, lambda_context)

    # Should return API Gateway response format
    assert "statusCode" in result


def test_invocation_pattern_detection_operation(lambda_context):
    """Test that operation pattern is detected correctly"""
    from index import lambda_handler

    # Create operation-based event
    event = {"operation": "get_target_accounts", "queryParams": {}}

    # Invoke lambda_handler
    result = lambda_handler(event, lambda_context)

    # Should return result (not error about unknown format)
    assert isinstance(result, (dict, list))


def test_invocation_pattern_invalid_format(lambda_context):
    """Test that invalid format returns error"""
    from index import lambda_handler

    # Create event with no recognized pattern
    event = {"someField": "someValue"}

    # Invoke lambda_handler
    result = lambda_handler(event, lambda_context)

    # Should return error about invalid format
    assert "error" in result
    assert "Invalid invocation format" in result["error"]
