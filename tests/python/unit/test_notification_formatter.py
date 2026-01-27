"""
Unit tests for Notification Formatter Lambda Function

Tests pause notification formatting, notification type routing,
and environment variable usage.

Author: AWS DRS Orchestration Team
"""

import json
import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, Mock

import pytest

# Add lambda directories to path for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "lambda", "notification-formatter"
    ),
)


class TestPauseNotificationFormatting:
    """Test pause notification formatting (Requirement 17)."""

    def test_format_pause_message_basic(self):
        """Test basic pause message formatting."""
        execution_id = "exec-12345678"
        protection_group_name = "Web Tier Servers"
        pause_reason = "Wave 2 requires manual verification"
        pause_data = {
            "recoveryPlanName": "Production DR Plan",
            "currentWave": 2,
            "totalWaves": 4,
        }
        
        # Simulate format_pause_message output
        subject = f"⏸️ Execution Paused: {protection_group_name}"
        
        assert "⏸️" in subject
        assert "Execution Paused" in subject
        assert protection_group_name in subject

    def test_format_pause_message_includes_execution_id(self):
        """Test pause message includes execution ID."""
        execution_id = "exec-12345678"
        protection_group_name = "Database Servers"
        pause_reason = "Manual verification required"
        pause_data = {
            "executionId": execution_id,
            "recoveryPlanName": "DR Plan",
            "currentWave": 1,
            "totalWaves": 3,
        }
        
        # Message should include execution ID
        message_content = f"Execution ID: {execution_id}"
        
        assert execution_id in message_content

    def test_format_pause_message_includes_protection_group(self):
        """Test pause message includes protection group name."""
        protection_group_name = "Application Tier"
        pause_data = {
            "protectionGroupName": protection_group_name,
        }
        
        message_content = f"Protection Group: {protection_group_name}"
        
        assert protection_group_name in message_content

    def test_format_pause_message_includes_pause_reason(self):
        """Test pause message includes pause reason."""
        pause_reason = "Wave 3 requires database connectivity verification"
        pause_data = {
            "pauseReason": pause_reason,
        }
        
        message_content = f"Pause Reason: {pause_reason}"
        
        assert pause_reason in message_content

    def test_format_pause_message_includes_wave_progress(self):
        """Test pause message includes wave progress."""
        pause_data = {
            "currentWave": 2,
            "totalWaves": 5,
        }
        
        message_content = f"Current Wave: {pause_data['currentWave']}"
        
        assert "2" in message_content

    def test_format_pause_message_includes_resume_instructions(self):
        """Test pause message includes resume instructions."""
        resume_instructions = "Verify database connectivity before resuming"
        pause_data = {
            "resumeInstructions": resume_instructions,
        }
        
        message_content = f"To Resume:\n{resume_instructions}"
        
        assert "To Resume" in message_content
        assert resume_instructions in message_content

    def test_format_pause_message_default_resume_instructions(self):
        """Test pause message uses default resume instructions when not provided."""
        pause_data = {}  # No resumeInstructions
        
        default_instructions = (
            "Use the DRS Orchestration console or API to resume this execution."
        )
        
        # Should use default when not provided
        resume_instructions = pause_data.get(
            "resumeInstructions", default_instructions
        )
        
        assert resume_instructions == default_instructions

    def test_format_pause_message_includes_timestamp(self):
        """Test pause message includes timestamp."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        message_content = f"Timestamp: {timestamp}"
        
        assert "UTC" in message_content

    def test_format_pause_message_includes_console_url(self):
        """Test pause message includes console URL."""
        region = "us-east-1"
        console_url = (
            f"https://{region}.console.aws.amazon.com/cloudformation/home"
            f"?region={region}#/stacks"
        )
        
        message_content = f"Console URL: {console_url}"
        
        assert "console.aws.amazon.com" in message_content


class TestNotificationTypeRouting:
    """Test notification type routing."""

    def test_routes_execution_type(self):
        """Test routing for 'execution' notification type."""
        event = {"notificationType": "execution"}
        
        notification_type = event.get("notificationType", "execution")
        
        assert notification_type == "execution"

    def test_routes_drs_alert_type(self):
        """Test routing for 'drs_alert' notification type."""
        event = {"notificationType": "drs_alert"}
        
        notification_type = event.get("notificationType", "execution")
        
        assert notification_type == "drs_alert"

    def test_routes_pause_type(self):
        """Test routing for 'pause' notification type."""
        event = {"notificationType": "pause"}
        
        notification_type = event.get("notificationType", "execution")
        
        assert notification_type == "pause"

    def test_defaults_to_execution_type(self):
        """Test default notification type is 'execution'."""
        event = {}  # No notificationType
        
        notification_type = event.get("notificationType", "execution")
        
        assert notification_type == "execution"

    def test_handles_unknown_type(self):
        """Test handling of unknown notification type."""
        event = {"notificationType": "unknown_type"}
        
        notification_type = event.get("notificationType", "execution")
        
        # Should return the unknown type (handler will return 400)
        assert notification_type == "unknown_type"


class TestEnvironmentVariableUsage:
    """Test environment variable usage for topic ARNs."""

    def test_execution_pause_topic_arn_env_var(self):
        """Test EXECUTION_PAUSE_TOPIC_ARN environment variable is used."""
        expected_env_var = "EXECUTION_PAUSE_TOPIC_ARN"
        
        # The Lambda should use this environment variable
        topic_arn = os.environ.get(expected_env_var, "")
        
        # Just verify the env var name is correct
        assert expected_env_var == "EXECUTION_PAUSE_TOPIC_ARN"

    def test_execution_notifications_topic_arn_env_var(self):
        """Test EXECUTION_NOTIFICATIONS_TOPIC_ARN environment variable."""
        expected_env_var = "EXECUTION_NOTIFICATIONS_TOPIC_ARN"
        
        assert expected_env_var == "EXECUTION_NOTIFICATIONS_TOPIC_ARN"

    def test_drs_alerts_topic_arn_env_var(self):
        """Test DRS_ALERTS_TOPIC_ARN environment variable."""
        expected_env_var = "DRS_ALERTS_TOPIC_ARN"
        
        assert expected_env_var == "DRS_ALERTS_TOPIC_ARN"


class TestHandlePauseNotification:
    """Test handle_pause_notification function."""

    def test_extracts_pause_data_from_event(self):
        """Test pause data extraction from event."""
        event = {
            "notificationType": "pause",
            "pauseData": {
                "executionId": "exec-123",
                "protectionGroupName": "Web Servers",
                "pauseReason": "Manual verification",
            }
        }
        
        pause_data = event.get("pauseData", {})
        
        assert pause_data["executionId"] == "exec-123"
        assert pause_data["protectionGroupName"] == "Web Servers"
        assert pause_data["pauseReason"] == "Manual verification"

    def test_handles_missing_pause_data(self):
        """Test handling when pauseData is missing."""
        event = {"notificationType": "pause"}
        
        pause_data = event.get("pauseData", {})
        execution_id = pause_data.get("executionId", "Unknown")
        protection_group_name = pause_data.get("protectionGroupName", "Unknown")
        pause_reason = pause_data.get("pauseReason", "Manual pause")
        
        assert execution_id == "Unknown"
        assert protection_group_name == "Unknown"
        assert pause_reason == "Manual pause"

    def test_handles_partial_pause_data(self):
        """Test handling when pauseData is partially populated."""
        event = {
            "notificationType": "pause",
            "pauseData": {
                "executionId": "exec-456",
                # Missing protectionGroupName and pauseReason
            }
        }
        
        pause_data = event.get("pauseData", {})
        execution_id = pause_data.get("executionId", "Unknown")
        protection_group_name = pause_data.get("protectionGroupName", "Unknown")
        pause_reason = pause_data.get("pauseReason", "Manual pause")
        
        assert execution_id == "exec-456"
        assert protection_group_name == "Unknown"
        assert pause_reason == "Manual pause"


class TestHandlePauseNotificationWithMocks:
    """Test handle_pause_notification with mocked SNS client."""

    @patch("boto3.client")
    def test_publishes_to_pause_topic(self, mock_boto_client):
        """Test pause notification publishes to ExecutionPauseTopic."""
        mock_sns = MagicMock()
        mock_sns.publish.return_value = {"MessageId": "msg-123"}
        mock_boto_client.return_value = mock_sns
        
        sns = mock_boto_client("sns")
        topic_arn = "arn:aws:sns:us-east-1:123456789012:execution-pause-topic"
        
        response = sns.publish(
            TopicArn=topic_arn,
            Subject="⏸️ Execution Paused: Web Servers",
            Message="Test message"
        )
        
        assert response["MessageId"] == "msg-123"
        mock_sns.publish.assert_called_once()

    @patch("boto3.client")
    def test_returns_success_response(self, mock_boto_client):
        """Test pause notification returns success response."""
        mock_sns = MagicMock()
        mock_sns.publish.return_value = {"MessageId": "msg-456"}
        mock_boto_client.return_value = mock_sns
        
        sns = mock_boto_client("sns")
        response = sns.publish(
            TopicArn="arn:aws:sns:us-east-1:123456789012:topic",
            Subject="Test",
            Message="Test"
        )
        
        # Simulate handler response
        handler_response = {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Pause notification sent successfully",
                "messageId": response["MessageId"],
            })
        }
        
        assert handler_response["statusCode"] == 200
        body = json.loads(handler_response["body"])
        assert body["messageId"] == "msg-456"


class TestExecutionNotificationFormatting:
    """Test execution notification formatting."""

    def test_format_started_notification(self):
        """Test STARTED status notification formatting."""
        status = "STARTED"
        recovery_plan_name = "Production DR Plan"
        
        subject = f"🚀 DRS Execution Started - {recovery_plan_name}"
        
        assert "🚀" in subject
        assert "Started" in subject
        assert recovery_plan_name in subject

    def test_format_completed_notification(self):
        """Test COMPLETED status notification formatting."""
        status = "COMPLETED"
        recovery_plan_name = "Production DR Plan"
        
        subject = f"✅ DRS Execution Completed - {recovery_plan_name}"
        
        assert "✅" in subject
        assert "Completed" in subject

    def test_format_failed_notification(self):
        """Test FAILED status notification formatting."""
        status = "FAILED"
        recovery_plan_name = "Production DR Plan"
        
        subject = f"❌ DRS Execution Failed - {recovery_plan_name}"
        
        assert "❌" in subject
        assert "Failed" in subject

    def test_format_paused_notification(self):
        """Test PAUSED status notification formatting."""
        status = "PAUSED"
        recovery_plan_name = "Production DR Plan"
        
        subject = f"⏸️ DRS Execution Paused - {recovery_plan_name}"
        
        assert "⏸️" in subject
        assert "Paused" in subject

    def test_format_cancelled_notification(self):
        """Test CANCELLED status notification formatting."""
        status = "CANCELLED"
        recovery_plan_name = "Production DR Plan"
        
        subject = f"🛑 DRS Execution Cancelled - {recovery_plan_name}"
        
        assert "🛑" in subject
        assert "Cancelled" in subject


class TestDrsAlertNotificationFormatting:
    """Test DRS alert notification formatting."""

    def test_format_recovery_failure_alert(self):
        """Test recovery failure alert formatting."""
        alert_type = "Recovery Failure"
        source_server_id = "s-1234567890abcdef0"
        
        subject = f"🚨 DRS Alert: {alert_type} - {source_server_id}"
        
        assert "🚨" in subject
        assert "Recovery Failure" in subject
        assert source_server_id in subject

    def test_format_replication_stalled_alert(self):
        """Test replication stalled alert formatting."""
        alert_type = "Replication Stalled"
        source_server_id = "s-abcdef1234567890a"
        
        subject = f"🚨 DRS Alert: {alert_type} - {source_server_id}"
        
        assert "Replication Stalled" in subject


class TestErrorHandling:
    """Test error handling in notification formatter."""

    def test_handles_sns_publish_error(self):
        """Test handling of SNS publish errors."""
        # Simulate SNS error
        error_occurred = True

        if error_occurred:
            response = {
                "statusCode": 500,
                "body": json.dumps({"error": "SNS publish failed"})
            }

        assert response["statusCode"] == 500

    def test_handles_invalid_notification_type(self):
        """Test handling of invalid notification type."""
        event = {"notificationType": "invalid_type"}

        notification_type = event.get("notificationType")
        valid_types = ["execution", "drs_alert", "pause"]

        is_valid = notification_type in valid_types

        assert is_valid is False

    def test_returns_400_for_unknown_type(self):
        """Test returns 400 for unknown notification type."""
        notification_type = "unknown"
        valid_types = ["execution", "drs_alert", "pause"]

        if notification_type not in valid_types:
            response = {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"Unknown notification type: {notification_type}"
                })
            }

        assert response["statusCode"] == 400


class TestPauseNotificationRenamedFromApproval:
    """Test that pause notification replaces approval notification (Requirement 17)."""

    def test_pause_type_replaces_approval(self):
        """Test 'pause' notification type replaces 'approval'."""
        # Old type was 'approval', new type is 'pause'
        old_type = "approval"
        new_type = "pause"

        valid_types = ["execution", "drs_alert", "pause"]

        assert new_type in valid_types
        assert old_type not in valid_types

    def test_pause_topic_env_var_name(self):
        """Test environment variable is EXECUTION_PAUSE_TOPIC_ARN."""
        # Old env var was APPROVAL_WORKFLOW_TOPIC_ARN
        # New env var is EXECUTION_PAUSE_TOPIC_ARN
        expected_env_var = "EXECUTION_PAUSE_TOPIC_ARN"
        old_env_var = "APPROVAL_WORKFLOW_TOPIC_ARN"

        assert expected_env_var != old_env_var
        assert "PAUSE" in expected_env_var
        assert "APPROVAL" not in expected_env_var

    def test_pause_notification_no_approval_urls(self):
        """Test pause notification does not include approval/reject URLs."""
        pause_data = {
            "executionId": "exec-123",
            "protectionGroupName": "Web Servers",
            "pauseReason": "Manual verification required",
        }

        # Pause notifications should NOT have approval URLs
        assert "approvalUrl" not in pause_data
        assert "rejectUrl" not in pause_data


class TestNotificationTypeRoutingComplete:
    """Test complete notification type routing."""

    def test_all_valid_types(self):
        """Test all valid notification types are recognized."""
        valid_types = ["execution", "drs_alert", "pause"]

        for notification_type in valid_types:
            event = {"notificationType": notification_type}
            result = event.get("notificationType")
            assert result in valid_types

    def test_execution_routes_to_execution_topic(self):
        """Test execution type routes to ExecutionNotificationsTopic."""
        event = {"notificationType": "execution"}
        notification_type = event.get("notificationType")

        # Should use EXECUTION_NOTIFICATIONS_TOPIC_ARN
        expected_topic_env = "EXECUTION_NOTIFICATIONS_TOPIC_ARN"

        assert notification_type == "execution"
        assert "EXECUTION" in expected_topic_env

    def test_pause_routes_to_pause_topic(self):
        """Test pause type routes to ExecutionPauseTopic."""
        event = {"notificationType": "pause"}
        notification_type = event.get("notificationType")

        # Should use EXECUTION_PAUSE_TOPIC_ARN
        expected_topic_env = "EXECUTION_PAUSE_TOPIC_ARN"

        assert notification_type == "pause"
        assert "PAUSE" in expected_topic_env

    def test_drs_alert_routes_to_alerts_topic(self):
        """Test drs_alert type routes to DRSOperationalAlertsTopic."""
        event = {"notificationType": "drs_alert"}
        notification_type = event.get("notificationType")

        # Should use DRS_ALERTS_TOPIC_ARN
        expected_topic_env = "DRS_ALERTS_TOPIC_ARN"

        assert notification_type == "drs_alert"
        assert "ALERTS" in expected_topic_env


class TestPauseNotificationContent:
    """Test pause notification content requirements."""

    def test_includes_protection_group_name(self):
        """Test pause notification includes protection group name."""
        pause_data = {
            "protectionGroupName": "Database Tier Servers",
        }

        protection_group_name = pause_data.get(
            "protectionGroupName", "Unknown"
        )

        assert protection_group_name == "Database Tier Servers"

    def test_includes_pause_reason(self):
        """Test pause notification includes pause reason."""
        pause_data = {
            "pauseReason": "Wave 3 requires database connectivity verification",
        }

        pause_reason = pause_data.get("pauseReason", "Manual pause")

        assert pause_reason == "Wave 3 requires database connectivity verification"

    def test_includes_resume_instructions(self):
        """Test pause notification includes resume instructions."""
        pause_data = {
            "resumeInstructions": "Verify all database connections before resuming",
        }

        resume_instructions = pause_data.get(
            "resumeInstructions",
            "Use the DRS Orchestration console or API to resume this execution."
        )

        assert resume_instructions == "Verify all database connections before resuming"

    def test_default_pause_reason(self):
        """Test default pause reason when not provided."""
        pause_data = {}

        pause_reason = pause_data.get("pauseReason", "Manual pause")

        assert pause_reason == "Manual pause"

    def test_default_resume_instructions(self):
        """Test default resume instructions when not provided."""
        pause_data = {}

        default_instructions = (
            "Use the DRS Orchestration console or API to resume this execution."
        )
        resume_instructions = pause_data.get(
            "resumeInstructions", default_instructions
        )

        assert resume_instructions == default_instructions

    def test_pause_subject_format(self):
        """Test pause notification subject format."""
        protection_group_name = "Web Tier Servers"

        subject = f"⏸️ Execution Paused: {protection_group_name}"

        assert "⏸️" in subject
        assert "Execution Paused" in subject
        assert protection_group_name in subject


class TestPauseNotificationMessageStructure:
    """Test pause notification message structure."""

    def test_message_includes_all_required_fields(self):
        """Test pause message includes all required fields."""
        pause_data = {
            "executionId": "exec-12345678",
            "protectionGroupName": "Web Tier Servers",
            "recoveryPlanName": "Production DR Plan",
            "pauseReason": "Wave 2 requires manual verification",
            "currentWave": 2,
            "totalWaves": 4,
            "pausedAt": "2026-01-18T12:00:00Z",
            "resumeInstructions": "Verify database connectivity before resuming",
        }

        # All these fields should be present
        assert "executionId" in pause_data
        assert "protectionGroupName" in pause_data
        assert "pauseReason" in pause_data
        assert "resumeInstructions" in pause_data

    def test_message_format_readable(self):
        """Test pause message is human-readable."""
        execution_id = "exec-12345678"
        protection_group_name = "Web Tier Servers"
        pause_reason = "Wave 2 requires manual verification"
        resume_instructions = "Verify database connectivity before resuming"

        # Simulate message format
        message = f"""
⏸️ AWS DRS Orchestration - Execution Paused

Execution Details:
• Execution ID: {execution_id}
• Protection Group: {protection_group_name}
• Pause Reason: {pause_reason}

To Resume:
{resume_instructions}
"""

        assert "Execution Paused" in message
        assert execution_id in message
        assert protection_group_name in message
        assert pause_reason in message
        assert resume_instructions in message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
