"""
Unit tests for execution and orchestration handler changes.

Covers:
- Notification publishing on execution start, complete, failure
- Pause handler with valid/missing task token
- Callback handler resume and cancel actions
- Invalid/expired task token rejection
- HTML response generation for success and error pages

Validates: Requirements 5.3, 6.5, 6.6, 6.7, 6.10
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Paths for module loading
lambda_dir = os.path.join(
    os.path.dirname(__file__), "../../lambda"
)
orch_dir = os.path.join(
    lambda_dir, "dr-orchestration-stepfunction"
)
exec_dir = os.path.join(lambda_dir, "execution-handler")


# ------------------------------------------------------------------ #
# Orchestration handler fixtures
# ------------------------------------------------------------------ #

@pytest.fixture()
def orch_module():
    """Import orchestration handler as 'index' module."""
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    if "index" in sys.modules:
        del sys.modules["index"]

    sys.path.insert(0, orch_dir)
    sys.path.insert(0, lambda_dir)

    import index as mod
    yield mod

    sys.path[:] = original_path
    if "index" in sys.modules:
        del sys.modules["index"]
    if original_index is not None:
        sys.modules["index"] = original_index


@pytest.fixture()
def exec_module():
    """Import execution handler as 'index' module."""
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    if "index" in sys.modules:
        del sys.modules["index"]

    sys.path.insert(0, exec_dir)
    sys.path.insert(0, lambda_dir)

    import index as mod
    yield mod

    sys.path[:] = original_path
    if "index" in sys.modules:
        del sys.modules["index"]
    if original_index is not None:
        sys.modules["index"] = original_index


# ------------------------------------------------------------------ #
# Orchestration: notification on execution start
# ------------------------------------------------------------------ #

class TestNotifyExecutionStart:
    """Tests for _notify_execution_start.

    Validates: Requirement 5.3
    """

    def test_publishes_start_notification(self, orch_module):
        """Verify publish called with event_type='start'."""
        mock_publish = MagicMock()
        orch_module.publish_recovery_plan_notification = (
            mock_publish
        )

        state = {
            "plan_id": "plan-001",
            "execution_id": "exec-001",
            "plan_name": "Prod DR",
            "total_waves": 3,
            "is_drill": True,
            "accountContext": {
                "accountId": "123456789012"
            },
        }

        orch_module._notify_execution_start(state)

        mock_publish.assert_called_once()
        kw = mock_publish.call_args[1]
        assert kw["plan_id"] == "plan-001"
        assert kw["event_type"] == "start"
        details = kw["details"]
        assert details["executionId"] == "exec-001"
        assert details["planName"] == "Prod DR"
        assert details["waveCount"] == 3
        assert details["isDrill"] is True
        assert details["accountId"] == "123456789012"
        assert "consoleLink" in details
        assert "timestamp" in details

    def test_start_notification_failure_does_not_raise(
        self, orch_module
    ):
        """Notification failure must not block execution."""
        mock_publish = MagicMock(
            side_effect=Exception("SNS down")
        )
        orch_module.publish_recovery_plan_notification = (
            mock_publish
        )

        state = {
            "plan_id": "plan-002",
            "execution_id": "exec-002",
            "plan_name": "Test",
            "accountContext": {},
        }

        # Should not raise
        orch_module._notify_execution_start(state)


# ------------------------------------------------------------------ #
# Orchestration: notification on execution complete
# ------------------------------------------------------------------ #

class TestNotifyExecutionComplete:
    """Tests for _notify_execution_complete.

    Validates: Requirement 5.3
    """

    def test_publishes_complete_notification(
        self, orch_module
    ):
        """Verify publish called with event_type='complete'."""
        mock_publish = MagicMock()
        orch_module.publish_recovery_plan_notification = (
            mock_publish
        )

        state = {
            "plan_id": "plan-010",
            "execution_id": "exec-010",
            "plan_name": "Web Tier DR",
            "wave_results": [
                {"status": "success"},
                {"status": "success"},
                {"status": "failed"},
            ],
            "duration_seconds": 1800,
            "accountContext": {
                "accountId": "111222333444"
            },
        }

        orch_module._notify_execution_complete(state)

        mock_publish.assert_called_once()
        kw = mock_publish.call_args[1]
        assert kw["plan_id"] == "plan-010"
        assert kw["event_type"] == "complete"
        details = kw["details"]
        assert details["successCount"] == 2
        assert details["failureCount"] == 1
        assert details["durationSeconds"] == 1800

    def test_complete_notification_failure_does_not_raise(
        self, orch_module
    ):
        """Notification failure must not block execution."""
        mock_publish = MagicMock(
            side_effect=Exception("SNS down")
        )
        orch_module.publish_recovery_plan_notification = (
            mock_publish
        )

        state = {
            "plan_id": "plan-011",
            "execution_id": "exec-011",
            "plan_name": "Test",
            "wave_results": [],
            "accountContext": {},
        }

        orch_module._notify_execution_complete(state)


# ------------------------------------------------------------------ #
# Orchestration: notification on execution failure
# ------------------------------------------------------------------ #

class TestNotifyExecutionFailure:
    """Tests for _notify_execution_failure.

    Validates: Requirement 5.3
    """

    def test_publishes_failure_notification(
        self, orch_module
    ):
        """Verify publish called with event_type='fail'."""
        mock_publish = MagicMock()
        orch_module.publish_recovery_plan_notification = (
            mock_publish
        )

        state = {
            "plan_id": "plan-020",
            "execution_id": "exec-020",
            "plan_name": "DB Tier DR",
            "error": "DRS timeout",
            "error_code": "TIMEOUT",
            "accountContext": {
                "accountId": "999888777666"
            },
        }

        orch_module._notify_execution_failure(state)

        mock_publish.assert_called_once()
        kw = mock_publish.call_args[1]
        assert kw["plan_id"] == "plan-020"
        assert kw["event_type"] == "fail"
        details = kw["details"]
        assert details["errorMessage"] == "DRS timeout"
        assert details["errorCode"] == "TIMEOUT"

    def test_failure_notification_failure_does_not_raise(
        self, orch_module
    ):
        """Notification failure must not block execution."""
        mock_publish = MagicMock(
            side_effect=Exception("SNS down")
        )
        orch_module.publish_recovery_plan_notification = (
            mock_publish
        )

        state = {
            "plan_id": "plan-021",
            "execution_id": "exec-021",
            "plan_name": "Test",
            "accountContext": {},
        }

        orch_module._notify_execution_failure(state)


# ------------------------------------------------------------------ #
# Orchestration: pause handler
# ------------------------------------------------------------------ #

class TestHandleExecutionPause:
    """Tests for handle_execution_pause.

    Validates: Requirements 6.5, 6.6
    """

    def test_pause_with_valid_task_token(self, orch_module):
        """Pause stores token, publishes notification with URLs."""
        mock_publish = MagicMock()
        orch_module.publish_recovery_plan_notification = (
            mock_publish
        )

        mock_table = MagicMock()
        orch_module.get_execution_history_table = (
            MagicMock(return_value=mock_table)
        )

        token = "A" * 200
        event = {
            "application": {
                "plan_id": "plan-030",
                "execution_id": "exec-030",
                "plan_name": "Pause Test",
                "accountContext": {
                    "accountId": "123456789012"
                },
            },
            "taskToken": token,
            "pauseReason": "Pre-wave approval",
        }

        result = orch_module.handle_execution_pause(
            event, None
        )

        # Notification published with resume/cancel URLs
        mock_publish.assert_called_once()
        kw = mock_publish.call_args[1]
        assert kw["event_type"] == "pause"
        details = kw["details"]
        assert "resumeUrl" in details
        assert "cancelUrl" in details
        assert "action=resume" in details["resumeUrl"]
        assert "action=cancel" in details["cancelUrl"]
        assert "taskToken=" in details["resumeUrl"]

        # DynamoDB updated with PAUSED status
        mock_table.update_item.assert_called_once()
        update_kw = mock_table.update_item.call_args[1]
        vals = update_kw["ExpressionAttributeValues"]
        assert vals[":status"] == "PAUSED"
        assert vals[":token"] == token

        # State returned with paused status
        assert result["status"] == "paused"

    def test_pause_without_task_token_raises(
        self, orch_module
    ):
        """Missing taskToken must raise ValueError."""
        event = {
            "application": {
                "plan_id": "plan-031",
                "execution_id": "exec-031",
                "plan_name": "No Token",
            },
        }

        with pytest.raises(ValueError, match="taskToken"):
            orch_module.handle_execution_pause(event, None)

    def test_pause_notification_failure_does_not_block(
        self, orch_module
    ):
        """Notification failure must not prevent pause."""
        mock_publish = MagicMock(
            side_effect=Exception("SNS down")
        )
        orch_module.publish_recovery_plan_notification = (
            mock_publish
        )

        mock_table = MagicMock()
        orch_module.get_execution_history_table = (
            MagicMock(return_value=mock_table)
        )

        event = {
            "application": {
                "plan_id": "plan-032",
                "execution_id": "exec-032",
                "plan_name": "Notify Fail",
                "accountContext": {},
            },
            "taskToken": "B" * 200,
        }

        result = orch_module.handle_execution_pause(
            event, None
        )

        # DynamoDB still updated despite notification failure
        mock_table.update_item.assert_called_once()
        assert result["status"] == "paused"


# ------------------------------------------------------------------ #
# Execution handler: callback — resume
# ------------------------------------------------------------------ #

class TestCallbackHandlerResume:
    """Tests for handle_execution_callback resume action.

    Validates: Requirements 6.6, 6.7
    """

    def test_resume_calls_send_task_success(
        self, exec_module
    ):
        """Resume action calls SendTaskSuccess."""
        mock_sf = MagicMock()
        mock_sf.send_task_success.return_value = {}

        # Wire up exception classes so except clauses work
        mock_sf.exceptions.InvalidToken = type(
            "InvalidToken", (Exception,), {}
        )
        mock_sf.exceptions.TaskTimedOut = type(
            "TaskTimedOut", (Exception,), {}
        )
        mock_sf.exceptions.TaskDoesNotExist = type(
            "TaskDoesNotExist", (Exception,), {}
        )

        exec_module.stepfunctions = mock_sf
        exec_module.get_execution_history_table = (
            MagicMock(return_value=MagicMock())
        )

        token = "C" * 200
        event = {
            "queryStringParameters": {
                "action": "resume",
                "taskToken": token,
            },
        }

        result = exec_module.handle_execution_callback(event)

        mock_sf.send_task_success.assert_called_once()
        call_kw = mock_sf.send_task_success.call_args[1]
        assert call_kw["taskToken"] == token
        output = json.loads(call_kw["output"])
        assert output["action"] == "resume"

        assert result["statusCode"] == 200
        assert result["headers"]["Content-Type"] == "text/html"


# ------------------------------------------------------------------ #
# Execution handler: callback — cancel
# ------------------------------------------------------------------ #

class TestCallbackHandlerCancel:
    """Tests for handle_execution_callback cancel action.

    Validates: Requirements 6.6, 6.7
    """

    def test_cancel_calls_send_task_failure(
        self, exec_module
    ):
        """Cancel action calls SendTaskFailure."""
        mock_sf = MagicMock()
        mock_sf.send_task_failure.return_value = {}
        mock_sf.exceptions.InvalidToken = type(
            "InvalidToken", (Exception,), {}
        )
        mock_sf.exceptions.TaskTimedOut = type(
            "TaskTimedOut", (Exception,), {}
        )
        mock_sf.exceptions.TaskDoesNotExist = type(
            "TaskDoesNotExist", (Exception,), {}
        )

        exec_module.stepfunctions = mock_sf
        exec_module.get_execution_history_table = (
            MagicMock(return_value=MagicMock())
        )

        token = "D" * 200
        event = {
            "queryStringParameters": {
                "action": "cancel",
                "taskToken": token,
            },
        }

        result = exec_module.handle_execution_callback(event)

        mock_sf.send_task_failure.assert_called_once()
        call_kw = mock_sf.send_task_failure.call_args[1]
        assert call_kw["taskToken"] == token

        assert result["statusCode"] == 200
        assert result["headers"]["Content-Type"] == "text/html"
        assert "cancel" in result["body"].lower()


# ------------------------------------------------------------------ #
# Execution handler: invalid task token rejection
# ------------------------------------------------------------------ #

class TestInvalidTaskTokenRejection:
    """Tests for task token validation.

    Validates: Requirement 6.10
    """

    def test_empty_token_rejected(self, exec_module):
        """Empty task token returns 400 error."""
        event = {
            "queryStringParameters": {
                "action": "resume",
                "taskToken": "",
            },
        }

        result = exec_module.handle_execution_callback(event)
        assert result["statusCode"] == 400
        assert result["headers"]["Content-Type"] == "text/html"

    def test_missing_token_rejected(self, exec_module):
        """Missing task token returns 400 error."""
        event = {
            "queryStringParameters": {
                "action": "resume",
            },
        }

        result = exec_module.handle_execution_callback(event)
        assert result["statusCode"] == 400

    def test_short_token_rejected(self, exec_module):
        """Token shorter than 100 chars is rejected."""
        event = {
            "queryStringParameters": {
                "action": "resume",
                "taskToken": "short-token",
            },
        }

        result = exec_module.handle_execution_callback(event)
        assert result["statusCode"] == 400
        body_lower = result["body"].lower()
        assert (
            "invalid" in body_lower or "too short" in body_lower
        )

    def test_invalid_action_rejected(self, exec_module):
        """Action other than resume/cancel returns 400."""
        event = {
            "queryStringParameters": {
                "action": "restart",
                "taskToken": "E" * 200,
            },
        }

        result = exec_module.handle_execution_callback(event)
        assert result["statusCode"] == 400

    def test_missing_query_params_rejected(
        self, exec_module
    ):
        """No query parameters returns 400."""
        event = {"queryStringParameters": None}

        result = exec_module.handle_execution_callback(event)
        assert result["statusCode"] == 400


# ------------------------------------------------------------------ #
# Execution handler: expired/invalid token from Step Functions
# ------------------------------------------------------------------ #

class TestExpiredTokenHandling:
    """Tests for Step Functions token exceptions.

    Validates: Requirement 6.10
    """

    def test_invalid_token_exception_returns_400(
        self, exec_module
    ):
        """InvalidToken from SF returns user-friendly error."""
        invalid_cls = type("InvalidToken", (Exception,), {})

        mock_sf = MagicMock()
        mock_sf.exceptions.InvalidToken = invalid_cls
        mock_sf.exceptions.TaskTimedOut = type(
            "TaskTimedOut", (Exception,), {}
        )
        mock_sf.exceptions.TaskDoesNotExist = type(
            "TaskDoesNotExist", (Exception,), {}
        )
        mock_sf.send_task_success.side_effect = (
            invalid_cls("bad token")
        )

        exec_module.stepfunctions = mock_sf
        exec_module.get_execution_history_table = (
            MagicMock(return_value=MagicMock())
        )

        event = {
            "queryStringParameters": {
                "action": "resume",
                "taskToken": "F" * 200,
            },
        }

        result = exec_module.handle_execution_callback(event)

        assert result["statusCode"] == 400
        assert result["headers"]["Content-Type"] == "text/html"
        body_lower = result["body"].lower()
        assert (
            "invalid" in body_lower or "expired" in body_lower
        )

    def test_task_timed_out_exception_returns_400(
        self, exec_module
    ):
        """TaskTimedOut from SF returns user-friendly error."""
        timed_out_cls = type(
            "TaskTimedOut", (Exception,), {}
        )

        mock_sf = MagicMock()
        mock_sf.exceptions.InvalidToken = type(
            "InvalidToken", (Exception,), {}
        )
        mock_sf.exceptions.TaskTimedOut = timed_out_cls
        mock_sf.exceptions.TaskDoesNotExist = type(
            "TaskDoesNotExist", (Exception,), {}
        )
        mock_sf.send_task_failure.side_effect = (
            timed_out_cls("timed out")
        )

        exec_module.stepfunctions = mock_sf
        exec_module.get_execution_history_table = (
            MagicMock(return_value=MagicMock())
        )

        event = {
            "queryStringParameters": {
                "action": "cancel",
                "taskToken": "G" * 200,
            },
        }

        result = exec_module.handle_execution_callback(event)

        assert result["statusCode"] == 400
        assert "timed out" in result["body"].lower()

    def test_task_does_not_exist_returns_400(
        self, exec_module
    ):
        """TaskDoesNotExist from SF returns user-friendly error."""
        not_exist_cls = type(
            "TaskDoesNotExist", (Exception,), {}
        )

        mock_sf = MagicMock()
        mock_sf.exceptions.InvalidToken = type(
            "InvalidToken", (Exception,), {}
        )
        mock_sf.exceptions.TaskTimedOut = type(
            "TaskTimedOut", (Exception,), {}
        )
        mock_sf.exceptions.TaskDoesNotExist = not_exist_cls
        mock_sf.send_task_success.side_effect = (
            not_exist_cls("gone")
        )

        exec_module.stepfunctions = mock_sf
        exec_module.get_execution_history_table = (
            MagicMock(return_value=MagicMock())
        )

        event = {
            "queryStringParameters": {
                "action": "resume",
                "taskToken": "H" * 200,
            },
        }

        result = exec_module.handle_execution_callback(event)

        assert result["statusCode"] == 400
        body_lower = result["body"].lower()
        assert (
            "no longer exists" in body_lower
            or "completed" in body_lower
        )


# ------------------------------------------------------------------ #
# HTML response generation
# ------------------------------------------------------------------ #

class TestHtmlResponseGeneration:
    """Tests for _callback_success_response / _callback_error_response.

    Validates: Requirement 6.10
    """

    def test_success_response_is_html(self, exec_module):
        """Success response has Content-Type text/html."""
        result = exec_module._callback_success_response(
            "All good", "resume"
        )

        assert result["statusCode"] == 200
        assert result["headers"]["Content-Type"] == "text/html"
        assert "<!DOCTYPE html>" in result["body"]
        assert "All good" in result["body"]

    def test_success_response_contains_action_label(
        self, exec_module
    ):
        """Success page shows the action that was performed."""
        result = exec_module._callback_success_response(
            "Done", "cancel"
        )

        assert "cancel" in result["body"].lower()

    def test_error_response_is_html(self, exec_module):
        """Error response has Content-Type text/html."""
        result = exec_module._callback_error_response(
            400, "Bad request"
        )

        assert result["statusCode"] == 400
        assert result["headers"]["Content-Type"] == "text/html"
        assert "<!DOCTYPE html>" in result["body"]
        assert "Bad request" in result["body"]

    def test_error_response_500(self, exec_module):
        """500 error response renders correctly."""
        result = exec_module._callback_error_response(
            500, "Internal error"
        )

        assert result["statusCode"] == 500
        assert result["headers"]["Content-Type"] == "text/html"
        assert "Internal error" in result["body"]

    def test_success_response_has_close_hint(
        self, exec_module
    ):
        """Success page tells user they can close the window."""
        result = exec_module._callback_success_response(
            "Resumed", "resume"
        )

        assert "close" in result["body"].lower()

    def test_error_response_has_contact_hint(
        self, exec_module
    ):
        """Error page suggests contacting administrator."""
        result = exec_module._callback_error_response(
            400, "Token expired"
        )

        assert "administrator" in result["body"].lower()
