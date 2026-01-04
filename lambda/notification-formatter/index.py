"""
AWS DRS Orchestration - Notification Formatter Lambda
Formats CodePipeline and CodeBuild events into user-friendly email notifications
"""

import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any

# Import security utilities
try:
    from security_utils import (
        validate_api_gateway_event,
        sanitize_string_input,
        log_security_event,
        safe_aws_client_call,
        create_response_with_security_headers,
    )

    SECURITY_ENABLED = True
except ImportError:
    SECURITY_ENABLED = False
    print(
        "WARNING: security_utils not available - running without security features"
    )

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
sns = boto3.client("sns")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Format pipeline and security scan notifications into user-friendly messages.

    Args:
        event: EventBridge event containing pipeline or build state changes
        context: Lambda context object

    Returns:
        Dict containing statusCode and response message
    """
    try:
        # Security validation
        if SECURITY_ENABLED:
            log_security_event(
                "notification_formatter_invoked",
                {
                    "function_name": context.function_name,
                    "request_id": context.aws_request_id,
                    "event_source": event.get("source", "unknown"),
                },
            )

        logger.info(
            f"Processing notification event: {json.dumps(event, default=str)}"
        )

        # Extract and sanitize event details
        if SECURITY_ENABLED:
            detail = event.get("detail", {})
            source = sanitize_string_input(event.get("source", ""))
            detail_type = sanitize_string_input(event.get("detail-type", ""))
            region = sanitize_string_input(event.get("region", "us-east-1"))
            account = sanitize_string_input(event.get("account", ""))
        else:
            detail = event.get("detail", {})
            source = event.get("source", "")
            detail_type = event.get("detail-type", "")
            region = event.get("region", "us-east-1")
            account = event.get("account", "")

        # Format message based on event source
        if source == "aws.codepipeline":
            formatted_message = format_pipeline_notification(
                detail, detail_type, region, account
            )
        elif source == "aws.codebuild":
            formatted_message = format_build_notification(
                detail, detail_type, region, account
            )
        else:
            logger.warning(f"Unknown event source: {source}")
            if SECURITY_ENABLED:
                log_security_event("unknown_event_source", {"source": source})
                return create_response_with_security_headers(
                    200, {"message": "Unknown event source"}
                )
            else:
                return {"statusCode": 200, "body": "Unknown event source"}

        # Send formatted notification
        topic_arn = get_sns_topic_arn()
        if topic_arn:
            send_formatted_notification(topic_arn, formatted_message)
            logger.info("Formatted notification sent successfully")
        else:
            logger.error("SNS topic ARN not found")
            if SECURITY_ENABLED:
                log_security_event("sns_topic_not_configured", {})
                return create_response_with_security_headers(
                    500, {"message": "SNS topic not configured"}
                )
            else:
                return {"statusCode": 500, "body": "SNS topic not configured"}

        if SECURITY_ENABLED:
            return create_response_with_security_headers(
                200, {"message": "Notification processed successfully"}
            )
        else:
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {"message": "Notification processed successfully"}
                ),
            }

    except Exception as e:
        logger.error(f"Error processing notification: {str(e)}")
        if SECURITY_ENABLED:
            log_security_event(
                "notification_formatter_error",
                {
                    "error": str(e),
                    "event_source": event.get("source", "unknown"),
                },
            )
            return create_response_with_security_headers(
                500, {"error": str(e)}
            )
        else:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def format_pipeline_notification(
    detail: Dict[str, Any], detail_type: str, region: str, account: str
) -> Dict[str, str]:
    """Format CodePipeline notification into user-friendly message."""

    # Sanitize inputs if security is enabled
    if SECURITY_ENABLED:
        pipeline_name = sanitize_string_input(
            detail.get("pipeline", "Unknown Pipeline")
        )
        execution_id = sanitize_string_input(
            detail.get("execution-id", "Unknown")
        )
        state = sanitize_string_input(detail.get("state", "Unknown"))
        stage = sanitize_string_input(detail.get("stage", ""))
        action = sanitize_string_input(detail.get("action", ""))
    else:
        pipeline_name = detail.get("pipeline", "Unknown Pipeline")
        execution_id = detail.get("execution-id", "Unknown")
        state = detail.get("state", "Unknown")
        stage = detail.get("stage", "")
        action = detail.get("action", "")

    # Format timestamp
    start_time = detail.get("start-time", "")
    if start_time:
        try:
            dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            formatted_time = start_time
    else:
        formatted_time = "Unknown"

    # Create console URLs
    pipeline_url = f"https://console.aws.amazon.com/codesuite/codepipeline/pipelines/{pipeline_name}/view"
    execution_url = f"https://console.aws.amazon.com/codesuite/codepipeline/pipelines/{pipeline_name}/executions/{execution_id}/timeline"

    # Determine severity and create appropriate message
    if state == "FAILED":
        severity = "🚨 CRITICAL"
        status_emoji = "❌"
        if stage:
            subject = f"Pipeline Stage Failed: {pipeline_name} - {stage}"
            stage_info = f"\n**Failed Stage:** {stage}"
            if action:
                stage_info += f"\n**Failed Action:** {action}"
        else:
            subject = f"Pipeline Failed: {pipeline_name}"
            stage_info = ""
    else:
        severity = "ℹ️ INFO"
        status_emoji = "✅" if state == "SUCCEEDED" else "🔄"
        subject = f"Pipeline {state.title()}: {pipeline_name}"
        stage_info = f"\n**Stage:** {stage}" if stage else ""

    # Create formatted message
    message = f"""
{severity} AWS DRS Orchestration Pipeline Notification

{status_emoji} **Pipeline:** {pipeline_name}
📅 **Time:** {formatted_time}
🔄 **Status:** {state}{stage_info}
🆔 **Execution ID:** {execution_id}

**Quick Actions:**
• [View Pipeline]({pipeline_url})
• [View Execution Details]({execution_url})
• [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups)

**Account:** {account}
**Region:** {region}

---
AWS DRS Orchestration System
Automated notification from pipeline monitoring
""".strip()

    return {"subject": subject, "message": message}


def format_build_notification(
    detail: Dict[str, Any], detail_type: str, region: str, account: str
) -> Dict[str, str]:
    """Format CodeBuild notification into user-friendly message."""

    # Sanitize inputs if security is enabled
    if SECURITY_ENABLED:
        project_name = sanitize_string_input(
            detail.get("project-name", "Unknown Project")
        )
        build_id = sanitize_string_input(detail.get("build-id", "Unknown"))
        build_status = sanitize_string_input(
            detail.get("build-status", "Unknown")
        )
    else:
        project_name = detail.get("project-name", "Unknown Project")
        build_id = detail.get("build-id", "Unknown")
        build_status = detail.get("build-status", "Unknown")

    # Extract build number from build ID
    build_number = build_id.split(":")[-1] if ":" in build_id else build_id

    # Format timestamp
    start_time = detail.get("start-time", "")
    if start_time:
        try:
            dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            formatted_time = start_time
    else:
        formatted_time = "Unknown"

    # Create console URLs
    build_url = f"https://console.aws.amazon.com/codesuite/codebuild/projects/{project_name}/build/{build_id}"
    logs_url = f"https://console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups/log-group/$252Faws$252Fcodebuild$252F{project_name}"

    # Determine if this is a security scan failure
    is_security_scan = "security-scan" in project_name.lower()

    # Create appropriate message based on build type and status
    if build_status == "FAILED":
        if is_security_scan:
            severity = "🔒 SECURITY ALERT"
            status_emoji = "🛡️❌"
            subject = f"Security Scan Failed: {project_name}"
            alert_type = "Security vulnerabilities detected or scan failed"
        else:
            severity = "🚨 BUILD FAILURE"
            status_emoji = "🔨❌"
            subject = f"Build Failed: {project_name}"
            alert_type = "Build process encountered errors"
    else:
        severity = "ℹ️ BUILD INFO"
        status_emoji = "✅" if build_status == "SUCCEEDED" else "🔄"
        subject = f"Build {build_status.title()}: {project_name}"
        alert_type = f"Build {build_status.lower()}"

    # Create formatted message
    message = f"""
{severity}

{status_emoji} **Project:** {project_name}
📅 **Time:** {formatted_time}
🔄 **Status:** {build_status}
🆔 **Build:** {build_number}
📋 **Type:** {alert_type}

**Quick Actions:**
• [View Build Details]({build_url})
• [View Build Logs]({logs_url})
• [CodeBuild Console](https://console.aws.amazon.com/codesuite/codebuild/projects/{project_name}/history)

**Account:** {account}
**Region:** {region}

---
AWS DRS Orchestration System
Automated notification from build monitoring
""".strip()

    return {"subject": subject, "message": message}


def get_sns_topic_arn() -> str:
    """Get SNS topic ARN from environment variables or CloudFormation exports."""
    import os

    # Try environment variable first
    topic_arn = os.environ.get("SNS_TOPIC_ARN")
    if topic_arn:
        return topic_arn

    # Try to find topic by name pattern
    try:
        response = sns.list_topics()
        for topic in response.get("Topics", []):
            topic_arn = topic["TopicArn"]
            if "pipeline-notifications" in topic_arn:
                return topic_arn
    except Exception as e:
        logger.error(f"Error finding SNS topic: {str(e)}")

    return ""


def send_formatted_notification(
    topic_arn: str, formatted_message: Dict[str, str]
) -> None:
    """Send formatted notification to SNS topic."""

    try:
        # Security validation for SNS inputs
        if SECURITY_ENABLED:
            topic_arn = sanitize_string_input(topic_arn)
            subject = sanitize_string_input(
                formatted_message.get("subject", "")
            )
            message = sanitize_string_input(
                formatted_message.get("message", "")
            )

            publish_call = lambda: sns.publish(
                TopicArn=topic_arn, Subject=subject, Message=message
            )
            response = safe_aws_client_call(publish_call)
        else:
            response = sns.publish(
                TopicArn=topic_arn,
                Subject=formatted_message["subject"],
                Message=formatted_message["message"],
            )

        logger.info(f"SNS message sent successfully: {response['MessageId']}")

    except Exception as e:
        logger.error(f"Error sending SNS notification: {str(e)}")
        if SECURITY_ENABLED:
            log_security_event(
                "sns_publish_error",
                {
                    "error": str(e),
                    "topic_arn": (
                        topic_arn[:50] + "..."
                        if len(topic_arn) > 50
                        else topic_arn
                    ),
                },
            )
        raise
