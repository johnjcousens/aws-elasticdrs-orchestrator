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
        subject, message = format_execution_message(execution_id, status, recovery_plan_name, execution_data)

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
        subject, message = format_drs_alert_message(alert_type, source_server_id, region, alert_data)

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
        subject, message = format_pause_message(execution_id, protection_group_name, pause_reason, pause_data)

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
    Format execution pause notification message (plain text).

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
        "Use the DRS Orchestration console or API " "to resume this execution.",
    )

    subject = f"⏸️ Execution Paused: {protection_group_name}"

    console_url = f"https://{AWS_REGION}.console.aws.amazon.com" f"/cloudformation/home?region={AWS_REGION}#/stacks"

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


def _get_base_email_styles() -> str:
    """
    Return shared inline CSS for HTML email templates.

    Uses inline styles for maximum email client compatibility.
    Includes responsive breakpoints for mobile devices.

    Returns:
        CSS style block as a string
    """
    return """
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont,
                    'Segoe UI', Roboto, Arial, sans-serif;
                line-height: 1.6;
                color: #16191f;
                margin: 0;
                padding: 0;
                background-color: #f2f3f3;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                padding: 16px;
            }
            .header {
                background-color: #232f3e;
                color: #ffffff;
                padding: 20px;
                text-align: center;
                border-radius: 4px 4px 0 0;
            }
            .header h1 {
                margin: 0;
                font-size: 20px;
                font-weight: 700;
            }
            .content {
                background-color: #ffffff;
                padding: 24px;
                border: 1px solid #d5dbdb;
                border-top: none;
                border-radius: 0 0 4px 4px;
            }
            .info-box {
                background-color: #f2f3f3;
                padding: 16px;
                margin: 16px 0;
                border-left: 4px solid #0972d3;
                border-radius: 0 4px 4px 0;
            }
            .info-box p {
                margin: 4px 0;
                font-size: 14px;
            }
            .actions {
                text-align: center;
                margin: 24px 0;
            }
            .button {
                display: inline-block;
                padding: 10px 24px;
                margin: 0 8px;
                text-decoration: none;
                border-radius: 4px;
                font-weight: 700;
                font-size: 14px;
            }
            .button-resume {
                background-color: #037f0c;
                color: #ffffff;
            }
            .button-cancel {
                background-color: #d13212;
                color: #ffffff;
            }
            .footer {
                text-align: center;
                color: #5f6b7a;
                font-size: 12px;
                margin-top: 16px;
                padding: 8px;
            }
            .console-link {
                text-align: center;
                margin-top: 20px;
            }
            .console-link a {
                color: #0972d3;
                text-decoration: none;
            }
            @media only screen and (max-width: 620px) {
                .container { padding: 8px; }
                .content { padding: 16px; }
                .button {
                    display: block;
                    margin: 8px auto;
                    width: 80%;
                    text-align: center;
                }
            }
        </style>
    """


def _build_info_box(details: Dict[str, Any]) -> str:
    """
    Build the common info box HTML with execution details.

    All email templates share this block showing Recovery Plan
    name, execution ID, account ID, and timestamp.

    Args:
        details: Event details dictionary

    Returns:
        HTML string for the info box section
    """
    execution_id = details.get("executionId", "Unknown")
    plan_name = details.get("planName", "Unknown")
    account_id = details.get("accountId", "")
    timestamp = details.get(
        "timestamp",
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )

    lines = [
        f"<p><strong>Recovery Plan:</strong> {plan_name}</p>",
        f"<p><strong>Execution ID:</strong>" f" {execution_id}</p>",
    ]
    if account_id:
        lines.append(f"<p><strong>Account ID:</strong>" f" {account_id}</p>")
    lines.append(f"<p><strong>Timestamp:</strong> {timestamp}</p>")

    return '<div class="info-box">' + "\n".join(lines) + "</div>"


def _build_console_link(details: Dict[str, Any]) -> str:
    """
    Build the console link HTML section.

    Args:
        details: Event details dictionary

    Returns:
        HTML string for the console link
    """
    console_link = details.get("consoleLink", "")
    if not console_link:
        region = details.get("region", AWS_REGION)
        console_link = f"https://{region}.console.aws.amazon.com" f"/cloudformation/home?region={region}" "#/stacks"
    return '<div class="console-link">' f'<a href="{console_link}">' "View in AWS Console</a>" "</div>"


def _wrap_html_email(
    title: str,
    body_content: str,
    details: Dict[str, Any],
) -> str:
    """
    Wrap body content in the standard HTML email template.

    Produces a complete HTML document with header, info box,
    console link, and footer. Mobile-friendly via responsive
    CSS media queries.

    Args:
        title: Header title text
        body_content: Inner HTML content for the email body
        details: Event details for info box and console link

    Returns:
        Complete HTML email string
    """
    styles = _get_base_email_styles()
    info_box = _build_info_box(details)
    console_link = _build_console_link(details)

    return (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head>\n"
        '    <meta charset="utf-8">\n'
        '    <meta name="viewport"'
        ' content="width=device-width, initial-scale=1.0">\n'
        f"    {styles}\n"
        "</head>\n"
        "<body>\n"
        '    <div class="container">\n'
        '        <div class="header">\n'
        f"            <h1>{title}</h1>\n"
        "        </div>\n"
        '        <div class="content">\n'
        f"            {body_content}\n"
        f"            {info_box}\n"
        f"            {console_link}\n"
        "        </div>\n"
        '        <div class="footer">\n'
        "            <p>AWS DRS Orchestration Platform"
        f" &middot; {PROJECT_NAME}"
        f" &middot; {ENVIRONMENT}</p>\n"
        "        </div>\n"
        "    </div>\n"
        "</body>\n"
        "</html>"
    )


def format_start_notification(
    details: Dict[str, Any],
) -> str:
    """
    Format HTML email for execution start events.

    Args:
        details: Event details including planName, executionId,
            accountId, timestamp, consoleLink, waveCount,
            executionType

    Returns:
        HTML email body string
    """
    wave_count = details.get("waveCount", "N/A")
    execution_type = details.get("executionType", "RECOVERY")

    body = (
        "<p>A disaster recovery execution has been "
        "<strong>started</strong>.</p>"
        "<p>"
        f"<strong>Execution Type:</strong> {execution_type}"
        "<br>"
        f"<strong>Total Waves:</strong> {wave_count}"
        "</p>"
        "<p>You will receive updates as the execution "
        "progresses through each wave.</p>"
    )

    return _wrap_html_email("\U0001f680 DR Execution Started", body, details)


def format_complete_notification(
    details: Dict[str, Any],
) -> str:
    """
    Format HTML email for execution completion events.

    Args:
        details: Event details including planName, executionId,
            accountId, timestamp, consoleLink, duration,
            wavesCompleted

    Returns:
        HTML email body string
    """
    duration = details.get("duration", "N/A")
    waves_completed = details.get("wavesCompleted", "N/A")

    body = (
        "<p>The disaster recovery execution has "
        "<strong>completed successfully</strong>.</p>"
        "<p>"
        f"<strong>Duration:</strong> {duration}"
        "<br>"
        f"<strong>Waves Completed:</strong>"
        f" {waves_completed}"
        "</p>"
        "<p>Please verify the recovered infrastructure "
        "in the target account.</p>"
    )

    return _wrap_html_email("\u2705 DR Execution Completed", body, details)


def format_failure_notification(
    details: Dict[str, Any],
) -> str:
    """
    Format HTML email for execution failure events.

    Args:
        details: Event details including planName, executionId,
            accountId, timestamp, consoleLink, errorMessage,
            failedWave

    Returns:
        HTML email body string
    """
    error_message = details.get("errorMessage", "Unknown error")
    failed_wave = details.get("failedWave", "N/A")

    body = (
        "<p>The disaster recovery execution has "
        "<strong>failed</strong>.</p>"
        "<p>"
        f"<strong>Failed Wave:</strong> {failed_wave}"
        "<br>"
        f"<strong>Error:</strong> {error_message}"
        "</p>"
        "<p>Please review the execution logs and take "
        "appropriate action to resolve the issue.</p>"
    )

    return _wrap_html_email("\u274c DR Execution Failed", body, details)


def format_pause_notification(
    details: Dict[str, Any],
) -> str:
    """
    Format HTML email for pause events with action buttons.

    The email includes Resume and Cancel buttons that link
    to the API Gateway callback endpoint using the embedded
    task token. Resume continues execution from the pause
    point; Cancel stops it permanently.

    Args:
        details: Event details including planName, executionId,
            accountId, timestamp, consoleLink, resumeUrl,
            cancelUrl, pauseReason

    Returns:
        HTML email body with interactive action buttons
    """
    pause_reason = details.get("pauseReason", "Manual pause requested")
    resume_url = details.get("resumeUrl", "")
    cancel_url = details.get("cancelUrl", "")

    body = (
        "<p>The disaster recovery execution has been "
        "<strong>paused</strong> and requires your action."
        "</p>"
        f"<p><strong>Reason:</strong> {pause_reason}</p>"
    )

    if resume_url and cancel_url:
        body += (
            '<div class="actions">'
            f'<a href="{resume_url}" class="button '
            'button-resume">'
            "\u25b6 Resume Execution</a>"
            f'<a href="{cancel_url}" class="button '
            'button-cancel">'
            "\u2715 Cancel Execution</a>"
            "</div>"
            '<p style="text-align:center;color:#5f6b7a;'
            'font-size:12px;">'
            "<strong>Resume</strong> continues the "
            "execution from where it paused.<br>"
            "<strong>Cancel</strong> stops the execution "
            "permanently.</p>"
        )

    return _wrap_html_email("\U0001f6d1 DR Execution Paused", body, details)


def format_notification_message(
    event_type: str,
    details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Route to the appropriate HTML email formatter by event type.

    Args:
        event_type: One of "start", "complete", "fail", "pause"
        details: Event details dictionary

    Returns:
        Dict with "default" (plain text) and "email" (HTML)
    """
    plan_name = details.get("planName", "Unknown")

    formatters = {
        "start": (
            f"DR Execution Started: {plan_name}",
            format_start_notification,
        ),
        "complete": (
            f"DR Execution Completed: {plan_name}",
            format_complete_notification,
        ),
        "fail": (
            f"DR Execution Failed: {plan_name}",
            format_failure_notification,
        ),
        "pause": (
            f"DR Execution Paused: {plan_name}",
            format_pause_notification,
        ),
    }

    if event_type in formatters:
        default_msg, formatter_fn = formatters[event_type]
        return {
            "default": default_msg,
            "email": formatter_fn(details),
        }

    return {
        "default": f"DR Event: {event_type}",
        "email": (f"Event: {event_type}\n" f"Details: {json.dumps(details, indent=2)}"),
    }
