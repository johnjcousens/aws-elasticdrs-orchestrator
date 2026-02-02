"""
SNS Notification Helper Module

Provides formatted SNS notifications for DRS orchestration lifecycle events.
Sends real-time alerts to operations teams via email, SMS, or other SNS subscribers.

## Architecture Pattern

Event-Driven Notifications:
- Execution lifecycle events (started, completed, failed, paused)
- Wave-level events (completed, failed)
- Sent to SNS topics with multiple subscribers (email, SMS, PagerDuty, Slack)
- Non-blocking: failures logged but don't stop execution

## Integration Points

### 1. Execution Lifecycle (Step Functions + Lambda)
```python
from shared.notifications import (
    send_execution_started,
    send_execution_completed,
    send_execution_failed
)

# At execution start
send_execution_started(
    execution_id="exec-123",
    plan_name="Production DR Plan",
    wave_count=5,
    execution_type="RECOVERY"
)

# At execution completion
send_execution_completed(
    execution_id="exec-123",
    plan_name="Production DR Plan",
    waves_completed=5,
    duration_seconds=1800  # 30 minutes
)

# On execution failure
send_execution_failed(
    execution_id="exec-123",
    plan_name="Production DR Plan",
    error_message="DRS service limit exceeded",
    failed_wave=3
)
```

### 2. Wave Progress (Execution Handler)
```python
from shared.notifications import send_wave_completed, send_wave_failed

# When wave completes successfully
send_wave_completed(
    execution_id="exec-123",
    plan_name="Production DR Plan",
    wave_number=1,
    wave_name="Critical Infrastructure",
    servers_launched=25
)

# When wave fails
send_wave_failed(
    execution_id="exec-123",
    plan_name="Production DR Plan",
    wave_number=2,
    wave_name="Application Tier",
    failed_servers=3
)
```

### 3. Manual Approval Workflow (Step Functions)
```python
from shared.notifications import send_execution_paused

# When execution pauses for approval
send_execution_paused(
    execution_id="exec-123",
    plan_name="Production DR Plan",
    paused_before_wave=3,
    wave_name="Database Tier"
)
```

## SNS Topic Configuration

### Environment Variables
- `EXECUTION_NOTIFICATIONS_TOPIC_ARN`: Topic for execution/wave events
- `DRS_ALERTS_TOPIC_ARN`: Topic for DRS service alerts (reserved for future use)

### Topic Subscribers
Configure SNS subscriptions for:
- Email: Operations team distribution lists
- SMS: On-call engineers for critical alerts
- PagerDuty: Incident management integration
- Slack: Team notification channels
- Lambda: Custom notification handlers

## Message Format

### Subject Line Pattern
```
[Emoji] [Event Type] - [Plan Name]

Examples:
🚀 DRS Execution Started - Production DR Plan
✅ DRS Execution Completed - Production DR Plan
❌ DRS Execution Failed - Production DR Plan
⏸️ DRS Execution Paused - Production DR Plan
✅ Wave 1 Completed - Production DR Plan
❌ Wave 2 Failed - Production DR Plan
```

### Message Body Structure
```
[Emoji] [Event Description]

Execution Details:
• Execution ID: exec-123
• Recovery Plan: Production DR Plan
• [Event-specific fields]
• Timestamp: 2026-01-25 12:00:00 UTC

[Action guidance or next steps]
```

## Error Handling

All notification functions are non-blocking:
- Failures logged to CloudWatch but don't raise exceptions
- Missing topic ARN logs warning and returns silently
- SNS publish errors logged but don't stop execution

This ensures DR operations continue even if notifications fail.

## Testing Considerations

### Local Testing
```python
import os
os.environ["EXECUTION_NOTIFICATIONS_TOPIC_ARN"] = "arn:aws:sns:us-east-1:123456789012:test-topic"

# Notifications will attempt to publish to test topic
send_execution_started("test-exec", "Test Plan", 3)
```

### Mocking SNS
```python
from unittest.mock import patch

with patch('shared.notifications.sns.publish') as mock_publish:
    send_execution_started("test-exec", "Test Plan", 3)
    assert mock_publish.called
```
"""

import os
from datetime import datetime, timezone
from typing import Optional

import boto3

# Initialize SNS client
sns = boto3.client("sns")

# Environment variables for SNS topic ARNs
EXECUTION_TOPIC_ARN = os.environ.get("EXECUTION_NOTIFICATIONS_TOPIC_ARN", "")
DRS_ALERTS_TOPIC_ARN = os.environ.get("DRS_ALERTS_TOPIC_ARN", "")


def send_execution_started(
    execution_id: str,
    plan_name: str,
    wave_count: int,
    execution_type: str = "RECOVERY",
) -> None:
    """
    Send notification when DR execution starts.

    Alerts operations team that disaster recovery has been initiated.
    Provides execution context and expected wave count.

    Args:
        execution_id: Unique execution identifier
        plan_name: Human-readable recovery plan name
        wave_count: Total number of waves in execution
        execution_type: Type of execution (RECOVERY, DRILL, FAILBACK)

    Example:
        >>> send_execution_started(
        ...     execution_id="exec-abc123",
        ...     plan_name="Production DR Plan",
        ...     wave_count=5,
        ...     execution_type="RECOVERY"
        ... )
        ✅ Sent execution started notification for exec-abc123
    """
    if not EXECUTION_TOPIC_ARN:
        print("No execution notifications topic configured")
        return

    try:
        subject = f"🚀 DRS Execution Started - {plan_name}"
        message = f"""
🚀 AWS DRS Orchestration Execution Started

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Type: {execution_type}
• Total Waves: {wave_count}
• Started At: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

The disaster recovery execution has been initiated. You will receive updates as each wave progresses.
"""

        sns.publish(TopicArn=EXECUTION_TOPIC_ARN, Subject=subject, Message=message)
        print(f"✅ Sent execution started notification for {execution_id}")
    except Exception as e:
        print(f"Warning: Failed to send execution started notification: {e}")


def send_execution_completed(
    execution_id: str,
    plan_name: str,
    waves_completed: int,
    duration_seconds: int,
) -> None:
    """
    Send notification when DR execution completes successfully.

    Alerts operations team that all waves completed and recovery is ready for validation.
    Includes execution duration for RTO tracking.

    Args:
        execution_id: Unique execution identifier
        plan_name: Human-readable recovery plan name
        waves_completed: Number of waves successfully completed
        duration_seconds: Total execution time in seconds

    Example:
        >>> send_execution_completed(
        ...     execution_id="exec-abc123",
        ...     plan_name="Production DR Plan",
        ...     waves_completed=5,
        ...     duration_seconds=1800  # 30 minutes
        ... )
        ✅ Sent execution completed notification for exec-abc123
    """
    if not EXECUTION_TOPIC_ARN:
        return

    try:
        duration_minutes = duration_seconds // 60
        subject = f"✅ DRS Execution Completed - {plan_name}"
        message = f"""
✅ AWS DRS Orchestration Execution Completed

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Waves Completed: {waves_completed}
• Duration: {duration_minutes} minutes ({duration_seconds} seconds)
• Completed At: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

All recovery waves have been successfully executed. Please verify the recovered infrastructure.
"""

        sns.publish(TopicArn=EXECUTION_TOPIC_ARN, Subject=subject, Message=message)
        print(f"✅ Sent execution completed notification for {execution_id}")
    except Exception as e:
        print(f"Warning: Failed to send execution completed notification: {e}")


def send_execution_failed(
    execution_id: str,
    plan_name: str,
    error_message: str,
    failed_wave: Optional[int] = None,
) -> None:
    """
    Send notification when DR execution fails.

    Alerts operations team of execution failure requiring immediate attention.
    Includes error details and failed wave for troubleshooting.

    Args:
        execution_id: Unique execution identifier
        plan_name: Human-readable recovery plan name
        error_message: Detailed error description
        failed_wave: Wave number where failure occurred (None if pre-wave failure)

    Example:
        >>> send_execution_failed(
        ...     execution_id="exec-abc123",
        ...     plan_name="Production DR Plan",
        ...     error_message="DRS service limit exceeded: max 20 concurrent jobs",
        ...     failed_wave=3
        ... )
        ✅ Sent execution failed notification for exec-abc123
    """
    if not EXECUTION_TOPIC_ARN:
        return

    try:
        subject = f"❌ DRS Execution Failed - {plan_name}"
        wave_info = f"Wave {failed_wave}" if failed_wave is not None else "Unknown wave"
        message = f"""
❌ AWS DRS Orchestration Execution Failed

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Failed At: {wave_info}
• Error: {error_message}
• Failed Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

Please review the execution logs and take appropriate action to resolve the issue.
"""

        sns.publish(TopicArn=EXECUTION_TOPIC_ARN, Subject=subject, Message=message)
        print(f"✅ Sent execution failed notification for {execution_id}")
    except Exception as e:
        print(f"Warning: Failed to send execution failed notification: {e}")


def send_execution_paused(
    execution_id: str, plan_name: str, paused_before_wave: int, wave_name: str
) -> None:
    """
    Send notification when execution pauses for manual approval.

    Alerts operations team that execution requires approval to continue.
    Used for manual approval gates between waves (e.g., before database tier).

    Args:
        execution_id: Unique execution identifier
        plan_name: Human-readable recovery plan name
        paused_before_wave: Wave number waiting for approval
        wave_name: Human-readable wave name

    Example:
        >>> send_execution_paused(
        ...     execution_id="exec-abc123",
        ...     plan_name="Production DR Plan",
        ...     paused_before_wave=3,
        ...     wave_name="Database Tier"
        ... )
        ✅ Sent execution paused notification for exec-abc123
    """
    if not EXECUTION_TOPIC_ARN:
        return

    try:
        subject = f"⏸️ DRS Execution Paused - {plan_name}"
        message = f"""
⏸️ AWS DRS Orchestration Execution Paused

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Paused Before: Wave {paused_before_wave} ({wave_name})
• Paused At: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

The execution is waiting for manual approval to continue. Use the DRS Orchestration console to resume.
"""

        sns.publish(TopicArn=EXECUTION_TOPIC_ARN, Subject=subject, Message=message)
        print(f"✅ Sent execution paused notification for {execution_id}")
    except Exception as e:
        print(f"Warning: Failed to send execution paused notification: {e}")


def send_wave_completed(
    execution_id: str,
    plan_name: str,
    wave_number: int,
    wave_name: str,
    servers_launched: int,
) -> None:
    """
    Send notification when wave completes successfully.

    Provides progress updates as each wave finishes. Helps operations team
    track execution progress and identify when specific tiers are recovered.

    Args:
        execution_id: Unique execution identifier
        plan_name: Human-readable recovery plan name
        wave_number: Wave number that completed
        wave_name: Human-readable wave name
        servers_launched: Number of servers successfully launched in wave

    Example:
        >>> send_wave_completed(
        ...     execution_id="exec-abc123",
        ...     plan_name="Production DR Plan",
        ...     wave_number=1,
        ...     wave_name="Critical Infrastructure",
        ...     servers_launched=25
        ... )
        ✅ Sent wave completed notification for wave 1
    """
    if not EXECUTION_TOPIC_ARN:
        return

    try:
        subject = f"✅ Wave {wave_number} Completed - {plan_name}"
        message = f"""
✅ AWS DRS Orchestration Wave Completed

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Wave: {wave_number} ({wave_name})
• Servers Launched: {servers_launched}
• Completed At: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

Wave {wave_number} has completed successfully. All servers are launched.
"""

        sns.publish(TopicArn=EXECUTION_TOPIC_ARN, Subject=subject, Message=message)
        print(f"✅ Sent wave completed notification for wave {wave_number}")
    except Exception as e:
        print(f"Warning: Failed to send wave completed notification: {e}")


def send_wave_failed(
    execution_id: str,
    plan_name: str,
    wave_number: int,
    wave_name: str,
    failed_servers: int,
) -> None:
    """
    Send notification when wave fails.

    Alerts operations team of wave failure requiring immediate attention.
    Includes failed server count for impact assessment.

    Args:
        execution_id: Unique execution identifier
        plan_name: Human-readable recovery plan name
        wave_number: Wave number that failed
        wave_name: Human-readable wave name
        failed_servers: Number of servers that failed to launch

    Example:
        >>> send_wave_failed(
        ...     execution_id="exec-abc123",
        ...     plan_name="Production DR Plan",
        ...     wave_number=2,
        ...     wave_name="Application Tier",
        ...     failed_servers=3
        ... )
        ✅ Sent wave failed notification for wave 2
    """
    if not EXECUTION_TOPIC_ARN:
        return

    try:
        subject = f"❌ Wave {wave_number} Failed - {plan_name}"
        message = f"""
❌ AWS DRS Orchestration Wave Failed

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Wave: {wave_number} ({wave_name})
• Failed Servers: {failed_servers}
• Failed At: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

Wave {wave_number} has failed. {failed_servers} server(s) failed to launch.
Please review the DRS console for detailed error information.
"""

        sns.publish(TopicArn=EXECUTION_TOPIC_ARN, Subject=subject, Message=message)
        print(f"✅ Sent wave failed notification for wave {wave_number}")
    except Exception as e:
        print(f"Warning: Failed to send wave failed notification: {e}")
