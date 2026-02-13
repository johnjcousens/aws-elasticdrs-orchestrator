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
from botocore.exceptions import ClientError

# Initialize SNS client
sns = boto3.client("sns")

# Environment variables for SNS topic ARNs
EXECUTION_TOPIC_ARN = os.environ.get("EXECUTION_NOTIFICATIONS_TOPIC_ARN", "")
DRS_ALERTS_TOPIC_ARN = os.environ.get("DRS_ALERTS_TOPIC_ARN", "")
PROJECT_NAME = os.environ.get("PROJECT_NAME", "aws-elasticdrs-orchestrator")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def send_execution_started(
    execution_id: str,
    plan_name: str,
    wave_count: int,
    execution_type: str = "RECOVERY",
    plan_id: Optional[str] = None,
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
        plan_id: Optional Recovery Plan ID for message filtering

    Example:
        >>> send_execution_started(
        ...     execution_id="exec-abc123",
        ...     plan_name="Production DR Plan",
        ...     wave_count=5,
        ...     execution_type="RECOVERY",
        ...     plan_id="plan-xyz789"
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

        publish_kwargs = {
            "TopicArn": EXECUTION_TOPIC_ARN,
            "Subject": subject,
            "Message": message,
        }

        if plan_id:
            publish_kwargs["MessageAttributes"] = {
                "recoveryPlanId": {
                    "DataType": "String",
                    "StringValue": plan_id,
                },
                "eventType": {
                    "DataType": "String",
                    "StringValue": "start",
                },
            }

        sns.publish(**publish_kwargs)
        print(f"✅ Sent execution started notification " f"for {execution_id}")
    except Exception as e:
        print("Warning: Failed to send execution started " f"notification: {e}")


def send_execution_completed(
    execution_id: str,
    plan_name: str,
    waves_completed: int,
    duration_seconds: int,
    plan_id: Optional[str] = None,
) -> None:
    """
    Send notification when DR execution completes successfully.

    Alerts operations team that all waves completed and recovery
    is ready for validation. Includes execution duration for RTO
    tracking.

    Args:
        execution_id: Unique execution identifier
        plan_name: Human-readable recovery plan name
        waves_completed: Number of waves successfully completed
        duration_seconds: Total execution time in seconds
        plan_id: Optional Recovery Plan ID for message filtering

    Example:
        >>> send_execution_completed(
        ...     execution_id="exec-abc123",
        ...     plan_name="Production DR Plan",
        ...     waves_completed=5,
        ...     duration_seconds=1800,
        ...     plan_id="plan-xyz789"
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

        publish_kwargs = {
            "TopicArn": EXECUTION_TOPIC_ARN,
            "Subject": subject,
            "Message": message,
        }

        if plan_id:
            publish_kwargs["MessageAttributes"] = {
                "recoveryPlanId": {
                    "DataType": "String",
                    "StringValue": plan_id,
                },
                "eventType": {
                    "DataType": "String",
                    "StringValue": "complete",
                },
            }

        sns.publish(**publish_kwargs)
        print(f"✅ Sent execution completed notification " f"for {execution_id}")
    except Exception as e:
        print("Warning: Failed to send execution completed " f"notification: {e}")


def send_execution_failed(
    execution_id: str,
    plan_name: str,
    error_message: str,
    failed_wave: Optional[int] = None,
    plan_id: Optional[str] = None,
) -> None:
    """
    Send notification when DR execution fails.

    Alerts operations team of execution failure requiring
    immediate attention. Includes error details and failed wave
    for troubleshooting.

    Args:
        execution_id: Unique execution identifier
        plan_name: Human-readable recovery plan name
        error_message: Detailed error description
        failed_wave: Wave number where failure occurred
            (None if pre-wave failure)
        plan_id: Optional Recovery Plan ID for message filtering

    Example:
        >>> send_execution_failed(
        ...     execution_id="exec-abc123",
        ...     plan_name="Production DR Plan",
        ...     error_message="DRS service limit exceeded",
        ...     failed_wave=3,
        ...     plan_id="plan-xyz789"
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

        publish_kwargs = {
            "TopicArn": EXECUTION_TOPIC_ARN,
            "Subject": subject,
            "Message": message,
        }

        if plan_id:
            publish_kwargs["MessageAttributes"] = {
                "recoveryPlanId": {
                    "DataType": "String",
                    "StringValue": plan_id,
                },
                "eventType": {
                    "DataType": "String",
                    "StringValue": "fail",
                },
            }

        sns.publish(**publish_kwargs)
        print(f"✅ Sent execution failed notification " f"for {execution_id}")
    except Exception as e:
        print("Warning: Failed to send execution failed " f"notification: {e}")


def send_execution_paused(
    execution_id: str,
    plan_name: str,
    paused_before_wave: int,
    wave_name: str,
    plan_id: Optional[str] = None,
) -> None:
    """
    Send notification when execution pauses for manual approval.

    Alerts operations team that execution requires approval to
    continue. Used for manual approval gates between waves.

    Args:
        execution_id: Unique execution identifier
        plan_name: Human-readable recovery plan name
        paused_before_wave: Wave number waiting for approval
        wave_name: Human-readable wave name
        plan_id: Optional Recovery Plan ID for message filtering

    Example:
        >>> send_execution_paused(
        ...     execution_id="exec-abc123",
        ...     plan_name="Production DR Plan",
        ...     paused_before_wave=3,
        ...     wave_name="Database Tier",
        ...     plan_id="plan-xyz789"
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

        publish_kwargs = {
            "TopicArn": EXECUTION_TOPIC_ARN,
            "Subject": subject,
            "Message": message,
        }

        if plan_id:
            publish_kwargs["MessageAttributes"] = {
                "recoveryPlanId": {
                    "DataType": "String",
                    "StringValue": plan_id,
                },
                "eventType": {
                    "DataType": "String",
                    "StringValue": "pause",
                },
            }

        sns.publish(**publish_kwargs)
        print(f"✅ Sent execution paused notification " f"for {execution_id}")
    except Exception as e:
        print("Warning: Failed to send execution paused " f"notification: {e}")


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


# ---------------------------------------------------------------------------
# Recovery Plan Notification Publishing
# ---------------------------------------------------------------------------
# Publishes execution events scoped to a specific Recovery Plan.
# Messages include ``recoveryPlanId`` and ``eventType`` as SNS
# MessageAttributes so that filter policies route notifications
# to the correct subscriber.
# ---------------------------------------------------------------------------

import json  # noqa: E402
import logging  # noqa: E402
from typing import Dict, Any  # noqa: E402

logger = logging.getLogger(__name__)


def publish_recovery_plan_notification(
    plan_id: str,
    event_type: str,
    details: Dict[str, Any],
) -> None:
    """
    Publish a notification for a Recovery Plan execution event.

    Sends a JSON message to the execution notifications SNS topic
    with ``recoveryPlanId`` and ``eventType`` as MessageAttributes.
    SNS filter policies use these attributes to route the message
    only to subscribers of the given Recovery Plan.

    Failures are logged but never raised so that notification
    issues do not block DR execution.

    Args:
        plan_id: Recovery Plan ID (UUID)
        event_type: Event type string, e.g. ``"start"``,
            ``"complete"``, ``"fail"``, ``"pause"``
        details: Arbitrary event details dict that is
            serialised as the message body

    Example:
        >>> publish_recovery_plan_notification(
        ...     plan_id="plan-abc123",
        ...     event_type="start",
        ...     details={
        ...         "executionId": "exec-1",
        ...         "planName": "Prod DR",
        ...         "accountId": "123456789012",
        ...     },
        ... )
    """
    if not EXECUTION_TOPIC_ARN:
        logger.warning("EXECUTION_NOTIFICATIONS_TOPIC_ARN not " "configured, skipping notification")
        return

    plan_name = details.get("planName", "Unknown")
    subject = f"[DRS] Recovery Plan: {plan_name} - " f"{event_type}"
    # SNS subject max length is 100 characters
    if len(subject) > 100:
        subject = subject[:97] + "..."

    # Attempt HTML formatting; fall back to raw JSON on error
    try:
        formatted = format_notification_message(event_type, details)
        message_body = json.dumps(
            {
                "default": formatted["default"],
                "email": formatted["email"],
            }
        )
        message_structure = "json"
    except Exception as fmt_exc:
        logger.error(
            "Failed to format notification for %s: %s",
            event_type,
            fmt_exc,
        )
        message_body = json.dumps(details)
        message_structure = None

    try:
        publish_kwargs = {
            "TopicArn": EXECUTION_TOPIC_ARN,
            "Message": message_body,
            "Subject": subject,
            "MessageAttributes": {
                "recoveryPlanId": {
                    "DataType": "String",
                    "StringValue": plan_id,
                },
                "eventType": {
                    "DataType": "String",
                    "StringValue": event_type,
                },
            },
        }
        if message_structure is not None:
            publish_kwargs["MessageStructure"] = message_structure
        sns.publish(**publish_kwargs)
        logger.info(
            "Published notification for Recovery Plan " "%s, event %s",
            plan_id,
            event_type,
        )
    except Exception as exc:
        logger.error(
            "Failed to publish notification for Recovery " "Plan %s, event %s: %s",
            plan_id,
            event_type,
            exc,
        )


# ---------------------------------------------------------------------------
# SNS Subscription Management for Recovery Plans
# ---------------------------------------------------------------------------
# These functions manage per-Recovery-Plan email subscriptions with
# SNS filter policies so each subscriber only receives notifications
# for their specific Recovery Plan.
# ---------------------------------------------------------------------------

from .security_utils import validate_email, InputValidationError  # noqa: E402

# DynamoDB resource for subscription ARN lookups
_dynamodb_resource = None


def _get_dynamodb_resource():
    """
    Lazy-initialise the DynamoDB resource.

    Returns:
        boto3 DynamoDB service resource
    """
    global _dynamodb_resource
    if _dynamodb_resource is None:
        _dynamodb_resource = boto3.resource("dynamodb")
    return _dynamodb_resource


def get_subscription_arn_for_plan(plan_id: str) -> Optional[str]:
    """
    Retrieve SNS subscription ARN for a Recovery Plan from DynamoDB.

    Looks up the ``snsSubscriptionArn`` field stored on the Recovery
    Plan item.  Returns ``None`` when the plan does not exist or has
    no subscription.

    Args:
        plan_id: Recovery Plan ID (UUID)

    Returns:
        Subscription ARN string, or None if not found
    """
    table_name = os.environ.get("RECOVERY_PLANS_TABLE", "")
    if not table_name:
        logger.warning("RECOVERY_PLANS_TABLE not configured, " "cannot look up subscription ARN")
        return None

    try:
        dynamodb = _get_dynamodb_resource()
        table = dynamodb.Table(table_name)
        response = table.get_item(
            Key={"planId": plan_id},
            ProjectionExpression="snsSubscriptionArn",
        )
        item = response.get("Item", {})
        arn = item.get("snsSubscriptionArn")
        if arn:
            return str(arn)
        return None
    except Exception as exc:
        logger.error(
            "Failed to retrieve subscription ARN for " "plan %s: %s",
            plan_id,
            exc,
        )
        return None


def manage_recovery_plan_subscription(
    plan_id: str,
    email: str,
    action: str = "create",
) -> Optional[str]:
    """
    Create, update, or delete an SNS email subscription for a
    Recovery Plan.

    On **create** the function validates the email, then calls
    ``sns.subscribe()`` with a ``FilterPolicy`` scoped to the
    given ``recoveryPlanId`` so the subscriber only receives
    notifications for that plan.

    On **delete** the stored subscription ARN is retrieved from
    DynamoDB and ``sns.unsubscribe()`` is called.

    On **update** the old subscription is deleted first, then a
    new one is created with the (potentially changed) email.

    Args:
        plan_id: Recovery Plan ID (UUID)
        email: Notification email address
        action: One of ``"create"``, ``"update"``, or ``"delete"``

    Returns:
        The SNS subscription ARN on create/update, or ``None``
        on delete.

    Raises:
        InputValidationError: If the email format is invalid
            (create/update only).
        ValueError: If ``action`` is not recognised or the
            ``EXECUTION_NOTIFICATIONS_TOPIC_ARN`` env var is
            missing.
    """
    if action not in ("create", "update", "delete"):
        raise ValueError(f"Invalid action '{action}'. " "Must be 'create', 'update', or 'delete'.")

    topic_arn = os.environ.get("EXECUTION_NOTIFICATIONS_TOPIC_ARN", "")
    if not topic_arn:
        raise ValueError("EXECUTION_NOTIFICATIONS_TOPIC_ARN is not configured")

    if action == "create":
        return _create_subscription(topic_arn, plan_id, email)

    if action == "delete":
        return _delete_subscription(plan_id)

    # action == "update": delete old, then create new
    _delete_subscription(plan_id)
    return _create_subscription(topic_arn, plan_id, email)


def _create_subscription(
    topic_arn: str,
    plan_id: str,
    email: str,
) -> str:
    """
    Create or update an SNS email subscription for a Recovery Plan.

    If the email is already subscribed to the topic (from another
    plan), the existing subscription's filter policy is updated to
    include this plan ID.

    Args:
        topic_arn: SNS topic ARN
        plan_id: Recovery Plan ID for the filter policy
        email: Subscriber email address

    Returns:
        The subscription ARN (may be ``"PendingConfirmation"``
        until the recipient confirms).

    Raises:
        InputValidationError: If the email is invalid.
    """
    if not validate_email(email):
        raise InputValidationError(f"Invalid email format: {email}")

    filter_policy = json.dumps({"recoveryPlanId": [plan_id]})

    try:
        resp = sns.subscribe(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=email,
            Attributes={
                "FilterPolicy": filter_policy,
                "FilterPolicyScope": "MessageAttributes",
            },
            ReturnSubscriptionArn=True,
        )

        subscription_arn = resp.get("SubscriptionArn", "")
        logger.info(
            "Created SNS subscription for plan %s " "(email=%s): %s",
            plan_id,
            email,
            subscription_arn,
        )
        return subscription_arn

    except ClientError as exc:
        error_msg = str(exc)
        if "already exists with different attributes" not in error_msg:
            raise

        # Same email already subscribed — update filter policy
        # to include this plan ID
        logger.info(
            "Subscription for %s already exists on topic, " "updating filter policy to include plan %s",
            email,
            plan_id,
        )
        return _add_plan_to_existing_subscription(
            topic_arn,
            plan_id,
            email,
        )


def _add_plan_to_existing_subscription(
    topic_arn: str,
    plan_id: str,
    email: str,
) -> str:
    """
    Find an existing subscription for the email and add the
    plan ID to its filter policy.

    Args:
        topic_arn: SNS topic ARN
        plan_id: Plan ID to add to the filter
        email: Subscriber email

    Returns:
        The existing subscription ARN.
    """
    # Find the existing subscription for this email
    paginator = sns.get_paginator("list_subscriptions_by_topic")
    for page in paginator.paginate(TopicArn=topic_arn):
        for sub in page.get("Subscriptions", []):
            if sub.get("Protocol") == "email" and sub.get("Endpoint") == email:
                sub_arn = sub["SubscriptionArn"]
                if sub_arn == "PendingConfirmation":
                    logger.info(
                        "Existing subscription for %s is " "pending confirmation",
                        email,
                    )
                    return "PendingConfirmation"

                # Get current filter policy
                attrs = sns.get_subscription_attributes(
                    SubscriptionArn=sub_arn,
                )
                current_policy_str = attrs.get("Attributes", {}).get("FilterPolicy", "{}")
                current_policy = json.loads(current_policy_str)

                # Add plan ID to the list
                plan_ids = current_policy.get(
                    "recoveryPlanId",
                    [],
                )
                if plan_id not in plan_ids:
                    plan_ids.append(plan_id)

                new_policy = json.dumps(
                    {"recoveryPlanId": plan_ids},
                )
                sns.set_subscription_attributes(
                    SubscriptionArn=sub_arn,
                    AttributeName="FilterPolicy",
                    AttributeValue=new_policy,
                )
                logger.info(
                    "Updated filter policy for %s to " "include plan %s (now %d plans)",
                    sub_arn,
                    plan_id,
                    len(plan_ids),
                )
                return sub_arn

    raise ValueError(
        f"Could not find existing subscription for " f"{email} on topic {topic_arn}",
    )


def _delete_subscription(plan_id: str) -> None:
    """
    Remove a plan from its SNS subscription.

    If the subscription's filter policy includes other plan IDs,
    only this plan ID is removed from the filter. If this was the
    last plan ID, the subscription is fully unsubscribed.

    Args:
        plan_id: Recovery Plan ID

    Returns:
        None
    """
    subscription_arn = get_subscription_arn_for_plan(plan_id)

    if not subscription_arn:
        logger.info(
            "No subscription ARN found for plan %s, " "nothing to delete",
            plan_id,
        )
        return None

    if subscription_arn == "PendingConfirmation":
        logger.info(
            "Subscription for plan %s is still pending " "confirmation, cannot unsubscribe via API",
            plan_id,
        )
        return None

    try:
        # Check if other plans share this subscription
        attrs = sns.get_subscription_attributes(
            SubscriptionArn=subscription_arn,
        )
        policy_str = attrs.get("Attributes", {}).get("FilterPolicy", "{}")
        policy = json.loads(policy_str)
        plan_ids = policy.get("recoveryPlanId", [])

        if plan_id in plan_ids:
            plan_ids.remove(plan_id)

        if plan_ids:
            # Other plans still use this subscription —
            # just update the filter policy
            new_policy = json.dumps(
                {"recoveryPlanId": plan_ids},
            )
            sns.set_subscription_attributes(
                SubscriptionArn=subscription_arn,
                AttributeName="FilterPolicy",
                AttributeValue=new_policy,
            )
            logger.info(
                "Removed plan %s from subscription %s " "(%d plans remain)",
                plan_id,
                subscription_arn,
                len(plan_ids),
            )
        else:
            # Last plan — fully unsubscribe
            sns.unsubscribe(SubscriptionArn=subscription_arn)
            logger.info(
                "Deleted SNS subscription %s for plan %s",
                subscription_arn,
                plan_id,
            )
    except Exception as exc:
        logger.error(
            "Failed to delete subscription %s for " "plan %s: %s",
            subscription_arn,
            plan_id,
            exc,
        )
        raise

    return None


# ---------------------------------------------------------------------------
# HTML Email Formatting Functions
# ---------------------------------------------------------------------------
# Pure Python functions that produce HTML email content for SNS
# notifications.  Moved from lambda/notification-formatter/index.py
# to consolidate all notification logic in one module.
# ---------------------------------------------------------------------------


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
        f"<p><strong>Recovery Plan:</strong>" f" {plan_name}</p>",
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
    Format HTML email for pause events with Resume/Cancel buttons.

    Buttons link to the Lambda Function URL callback endpoint
    which calls SendTaskSuccess/SendTaskFailure on Step Functions.
    Works without API Gateway or frontend deployment.

    Args:
        details: Event details including planName, executionId,
            accountId, timestamp, resumeUrl, cancelUrl,
            pauseReason, pausedBeforeWave

    Returns:
        HTML email body with clickable action buttons
    """
    pause_reason = details.get("pauseReason", "Manual pause requested")
    resume_url = details.get("resumeUrl", "")
    cancel_url = details.get("cancelUrl", "")
    paused_before = details.get("pausedBeforeWave", "")

    body = (
        "<p>The disaster recovery execution has been "
        "<strong>paused</strong> and requires your action."
        "</p>"
        f"<p><strong>Reason:</strong> {pause_reason}</p>"
    )

    if paused_before:
        body += f"<p><strong>Waiting to start:</strong> Wave {paused_before}</p>"

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
            "Click <strong>Resume</strong> to continue "
            "the next wave.<br>"
            "Click <strong>Cancel</strong> to stop the "
            "execution permanently.</p>"
        )
    else:
        # Fallback: no callback URL configured
        task_token = details.get("taskToken", "")
        region = details.get("region", "us-east-1")
        if task_token:
            body += (
                '<div class="info-box">'
                "<p><strong>To resume</strong>, run:</p>"
                '<pre style="background:#f2f3f3;padding:8px;'
                "border-radius:4px;font-size:12px;"
                'overflow-x:auto;">'
                f"aws stepfunctions send-task-success \\\n"
                f"  --task-token '{task_token}' \\\n"
                f"  --task-output '{{}}' \\\n"
                f"  --region {region}</pre>"
                "<p><strong>To cancel</strong>, run:</p>"
                '<pre style="background:#f2f3f3;padding:8px;'
                "border-radius:4px;font-size:12px;"
                'overflow-x:auto;">'
                f"aws stepfunctions send-task-failure \\\n"
                f"  --task-token '{task_token}' \\\n"
                f'  --error "UserCancelled" \\\n'
                f'  --cause "Cancelled via email" \\\n'
                f"  --region {region}</pre>"
                "</div>"
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
