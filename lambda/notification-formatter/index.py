"""
AWS DRS Orchestration - Notification Formatter Lambda Function

This function formats and sends notifications for various DRS orchestration events:
- Execution status updates (started, completed, failed, paused)
- DRS operational alerts (recovery failures, replication issues)
- Execution pause notifications (for manual intervention)
- System health alerts

Author: AWS DRS Orchestration Team
Version: 1.1.0
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
sns = boto3.client("sns")

# Environment variables
EXECUTION_TOPIC_ARN = os.environ.get("EXECUTION_NOTIFICATIONS_TOPIC_ARN")
DRS_ALERTS_TOPIC_ARN = os.environ.get("DRS_ALERTS_TOPIC_ARN")
EXECUTION_PAUSE_TOPIC_ARN = os.environ.get("EXECUTION_PAUSE_TOPIC_ARN")
PROJECT_NAME = os.environ.get("PROJECT_NAME", "aws-elasticdrs-orchestrator")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for processing notification events.

    Args:
        event: Lambda event containing notification data
        context: Lambda context object

    Returns:
        Dict containing response status and details
    """
    try:
        logger.info(f"Processing notification event: {json.dumps(event, default=str)}")

        # Determine notification type
        notification_type = event.get("notificationType", "execution")

        if notification_type == "execution":
            return handle_execution_notification(event)
        elif notification_type == "drs_alert":
            return handle_drs_alert_notification(event)
        elif notification_type == "pause":
            return handle_pause_notification(event)
        else:
            logger.error(f"Unknown notification type: {notification_type}")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Unknown notification type: {notification_type}"}),
            }

    except Exception as e:
        logger.error(f"Error processing notification: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def handle_execution_notification(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle execution-related notifications.

    Args:
        event: Event containing execution notification data

    Returns:
        Dict containing response status
    """
    try:
        execution_data = event.get("executionData", {})
        execution_id = execution_data.get("executionId", "Unknown")
        status = execution_data.get("status", "Unknown")
        recovery_plan_name = execution_data.get("recoveryPlanName", "Unknown")

        # Format message based on status
        subject, message = format_execution_message(
            execution_id, status, recovery_plan_name, execution_data
        )

        # Send notification
        response = sns.publish(TopicArn=EXECUTION_TOPIC_ARN, Subject=subject, Message=message)

        logger.info(f"Execution notification sent: {response['MessageId']}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Execution notification sent successfully",
                    "messageId": response["MessageId"],
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error sending execution notification: {str(e)}")
        raise


def handle_drs_alert_notification(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle DRS operational alert notifications.

    Args:
        event: Event containing DRS alert data

    Returns:
        Dict containing response status
    """
    try:
        alert_data = event.get("alertData", {})
        alert_type = alert_data.get("alertType", "DRS Alert")
        source_server_id = alert_data.get("sourceServerId", "Unknown")
        region = alert_data.get("region", "Unknown")

        # Format DRS alert message
        subject, message = format_drs_alert_message(
            alert_type, source_server_id, region, alert_data
        )

        # Send notification
        response = sns.publish(TopicArn=DRS_ALERTS_TOPIC_ARN, Subject=subject, Message=message)

        logger.info(f"DRS alert notification sent: {response['MessageId']}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "DRS alert notification sent successfully",
                    "messageId": response["MessageId"],
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error sending DRS alert notification: {str(e)}")
        raise


def handle_pause_notification(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle execution pause notifications.

    Sends notifications when an execution is paused for manual intervention,
    such as wave completion verification or protection group pause.

    Args:
        event: Event containing pause notification data

    Returns:
        Dict containing response status
    """
    try:
        pause_data = event.get("pauseData", {})
        execution_id = pause_data.get("executionId", "Unknown")
        protection_group_name = pause_data.get("protectionGroupName", "Unknown")
        pause_reason = pause_data.get("pauseReason", "Manual pause")

        # Format pause message
        subject, message = format_pause_message(
            execution_id, protection_group_name, pause_reason, pause_data
        )

        # Send notification
        response = sns.publish(
            TopicArn=EXECUTION_PAUSE_TOPIC_ARN,
            Subject=subject,
            Message=message,
        )

        logger.info(f"Pause notification sent: {response['MessageId']}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Pause notification sent successfully",
                    "messageId": response["MessageId"],
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error sending pause notification: {str(e)}")
        raise


def format_execution_message(
    execution_id: str,
    status: str,
    recovery_plan_name: str,
    execution_data: Dict[str, Any],
) -> tuple[str, str]:
    """
    Format execution notification message.

    Args:
        execution_id: Execution identifier
        status: Current execution status
        recovery_plan_name: Name of the recovery plan
        execution_data: Additional execution data

    Returns:
        Tuple of (subject, message)
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Status-specific formatting
    status_messages = {
        "STARTED": {
            "subject": f"🚀 DRS Execution Started - {recovery_plan_name}",
            "emoji": "🚀",
            "color": "blue",
        },
        "COMPLETED": {
            "subject": f"✅ DRS Execution Completed - {recovery_plan_name}",
            "emoji": "✅",
            "color": "green",
        },
        "FAILED": {
            "subject": f"❌ DRS Execution Failed - {recovery_plan_name}",
            "emoji": "❌",
            "color": "red",
        },
        "PAUSED": {
            "subject": f"⏸️ DRS Execution Paused - {recovery_plan_name}",
            "emoji": "⏸️",
            "color": "orange",
        },
        "CANCELLED": {
            "subject": f"🛑 DRS Execution Cancelled - {recovery_plan_name}",
            "emoji": "🛑",
            "color": "red",
        },
    }

    status_info = status_messages.get(
        status,
        {
            "subject": f"📋 DRS Execution Update - {recovery_plan_name}",
            "emoji": "📋",
            "color": "gray",
        },
    )

    subject = status_info["subject"]

    # Build detailed message
    message = f"""
{status_info['emoji']} AWS DRS Orchestration Execution Update

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {recovery_plan_name}
• Status: {status}
• Timestamp: {timestamp}
• Environment: {ENVIRONMENT.upper()}

"""

    # Add additional details based on status
    if status == "STARTED":
        wave_count = execution_data.get("waveCount", "Unknown")
        execution_type = execution_data.get("executionType", "RECOVERY")
        message += f"""
Execution Information:
• Type: {execution_type}
• Total Waves: {wave_count}
• Started At: {timestamp}

The disaster recovery execution has been initiated. You will receive updates as each wave progresses.
"""

    elif status == "COMPLETED":
        duration = execution_data.get("duration", "Unknown")
        waves_completed = execution_data.get("wavesCompleted", "Unknown")
        message += f"""
Completion Summary:
• Duration: {duration}
• Waves Completed: {waves_completed}
• Completed At: {timestamp}

All recovery waves have been successfully executed. Please verify the recovered infrastructure.
"""

    elif status == "FAILED":
        error_message = execution_data.get("errorMessage", "Unknown error")
        failed_wave = execution_data.get("failedWave", "Unknown")
        message += f"""
Failure Details:
• Failed Wave: {failed_wave}
• Error: {error_message}
• Failed At: {timestamp}

Please review the execution logs and take appropriate action to resolve the issue.
"""

    elif status == "PAUSED":
        current_wave = execution_data.get("currentWave", "Unknown")
        pause_reason = execution_data.get("pauseReason", "Manual pause")
        message += f"""
Pause Information:
• Current Wave: {current_wave}
• Reason: {pause_reason}
• Paused At: {timestamp}

The execution is waiting for approval to continue. Use the DRS Orchestration console to resume.
"""

    # Add console link
    console_url = "https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks"
    message += f"""
---
AWS DRS Orchestration Console: {console_url}
Project: {PROJECT_NAME}
Environment: {ENVIRONMENT}
"""

    return subject, message


def format_drs_alert_message(
    alert_type: str,
    source_server_id: str,
    region: str,
    alert_data: Dict[str, Any],
) -> tuple[str, str]:
    """
    Format DRS operational alert message.

    Args:
        alert_type: Type of DRS alert
        source_server_id: DRS source server ID
        region: AWS region
        alert_data: Additional alert data

    Returns:
        Tuple of (subject, message)
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    subject = f"🚨 DRS Alert: {alert_type} - {source_server_id}"

    message = f"""
🚨 AWS DRS Operational Alert

Alert Details:
• Type: {alert_type}
• Source Server: {source_server_id}
• Region: {region}
• Timestamp: {timestamp}
• Environment: {ENVIRONMENT.upper()}

"""

    # Add specific details based on alert type
    if "Recovery Failure" in alert_type:
        message += f"""
Recovery Failure Information:
• The DRS recovery launch failed for source server {source_server_id}
• This may indicate issues with launch templates, IAM permissions, or resource limits
• Check the DRS console for detailed error information

Recommended Actions:
1. Review DRS job logs in the AWS console
2. Verify launch template configuration
3. Check IAM permissions for DRS operations
4. Ensure sufficient EC2 capacity in the target region
"""

    elif "Replication Stalled" in alert_type:
        message += f"""
Replication Stalled Information:
• Data replication has stalled for source server {source_server_id}
• This may indicate network connectivity issues or agent problems
• Immediate attention required to maintain recovery readiness

Recommended Actions:
1. Check network connectivity between source and AWS
2. Verify DRS agent status on the source server
3. Review CloudWatch logs for replication errors
4. Consider restarting the DRS agent if necessary
"""

    # Add console links
    drs_console_url = f"https://console.aws.amazon.com/drs/home?region={region}#/sourceServers"
    message += f"""
---
DRS Console: {drs_console_url}
CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups
Project: {PROJECT_NAME}
Environment: {ENVIRONMENT}
"""

    return subject, message


def format_pause_message(
    execution_id: str,
    protection_group_name: str,
    pause_reason: str,
    pause_data: Dict[str, Any],
) -> tuple[str, str]:
    """
    Format execution pause notification message.

    Args:
        execution_id: Execution identifier
        protection_group_name: Name of the protection group
        pause_reason: Reason for the pause
        pause_data: Additional pause data

    Returns:
        Tuple of (subject, message)
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    recovery_plan_name = pause_data.get("recoveryPlanName", "Unknown")
    current_wave = pause_data.get("currentWave", "Unknown")
    total_waves = pause_data.get("totalWaves", "Unknown")
    resume_instructions = pause_data.get(
        "resumeInstructions",
        "Use the DRS Orchestration console or API to resume this execution.",
    )

    subject = f"⏸️ Execution Paused: {protection_group_name}"

    # Build console URL
    console_url = (
        f"https://{AWS_REGION}.console.aws.amazon.com/cloudformation/home"
        f"?region={AWS_REGION}#/stacks"
    )

    message = f"""
⏸️ AWS DRS Orchestration - Execution Paused

Execution Details:
• Execution ID: {execution_id}
• Protection Group: {protection_group_name}
• Recovery Plan: {recovery_plan_name}
• Pause Reason: {pause_reason}
• Timestamp: {timestamp}
• Environment: {ENVIRONMENT.upper()}

Wave Progress:
• Current Wave: {current_wave}
• Total Waves: {total_waves}

To Resume:
{resume_instructions}

Console URL: {console_url}

---
Note: The execution will remain paused until manually resumed.
Project: {PROJECT_NAME}
Environment: {ENVIRONMENT}
"""

    return subject, message
