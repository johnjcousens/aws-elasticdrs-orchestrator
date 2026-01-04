"""
Execution Registry Lambda
Creates and updates execution records in DynamoDB for all invocation sources.
Enables dual-mode orchestration where executions from UI, CLI, EventBridge,
SSM, and Step Functions all appear in the frontend.
"""

import json
import os
import time
import uuid
from decimal import Decimal
from typing import Any, Dict

import boto3

from security_utils import (
    log_security_event,
    mask_sensitive_data,
    safe_aws_client_call,
    sanitize_dynamodb_input,
    sanitize_string,
    validate_email,
    validate_uuid,
)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")

# Environment variables
EXECUTION_HISTORY_TABLE = os.environ.get(
    "EXECUTION_HISTORY_TABLE", "execution-history"
)

# Get table reference
execution_table = dynamodb.Table(EXECUTION_HISTORY_TABLE)


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for DynamoDB Decimal types"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event: Dict, context: Any) -> Dict:
    """
    Main handler - routes to appropriate action.

    Actions:
    - register: Create new execution record
    - update: Update execution status/waves
    - complete: Mark execution as complete
    - get: Get execution by ID
    """
    # Log security event for function invocation
    log_security_event(
        "lambda_invocation",
        {
            "function_name": "execution_registry",
            "action": event.get("action", "unknown"),
            "event_keys": (
                list(event.keys()) if isinstance(event, dict) else []
            ),
            "context_request_id": getattr(
                context, "aws_request_id", "unknown"
            ),
        },
    )

    print(
        f"Execution Registry received: {json.dumps(mask_sensitive_data(event), cls=DecimalEncoder)}"
    )

    action = event.get("action", "register")

    try:
        # Validate and sanitize input
        sanitized_event = sanitize_dynamodb_input(event)

        if action == "register":
            return register_execution(sanitized_event)
        elif action == "update":
            return update_execution(sanitized_event)
        elif action == "complete":
            return complete_execution(sanitized_event)
        elif action == "get":
            return get_execution(sanitized_event)
        else:
            log_security_event("invalid_action", {"action": action}, "WARN")
            raise ValueError(f"Unknown action: {action}")
    except Exception as e:
        log_security_event(
            "execution_registry_error",
            {"action": action, "error": str(e)},
            "ERROR",
        )
        print(f"Error in execution registry: {str(e)}")
        raise


def register_execution(event: Dict) -> Dict:
    """
    Create new execution record.

    Supports both:
    - Plan-based: Traditional UI flow with PlanId
    - Tag-based: Automation flow with tags for server selection
    """
    execution_id = str(uuid.uuid4())
    timestamp = int(time.time())

    # Determine selection mode
    selection_mode = "TAGS" if event.get("tags") else "PLAN"

    # Get invocation source and details
    invocation_source = event.get("invocationSource", "API")
    invocation_details = event.get("invocationDetails", {})

    # Build human-readable InitiatedBy string
    initiated_by = build_initiated_by(invocation_source, invocation_details)

    # Determine execution type
    options = event.get("options", {})
    is_drill = options.get("isDrill", True)
    execution_type = "DRILL" if is_drill else "RECOVERY"

    # Build execution record
    item = {
        "ExecutionId": execution_id,
        "PlanId": event.get("planId"),  # null for tag-based
        "ExecutionType": execution_type,
        "Status": "PENDING",
        "StartTime": timestamp,
        # Dual-mode fields
        "InvocationSource": invocation_source,
        "InvocationDetails": invocation_details,
        "SelectionMode": selection_mode,
        "Tags": event.get("tags", {}),
        # Display fields
        "InitiatedBy": initiated_by,
        "Waves": [],
        "TotalWaves": 0,
        "TotalServers": 0,
        # Options
        "Options": options,
    }

    # Store in DynamoDB
    execution_table.put_item(Item=item)

    print(f"Registered execution {execution_id} from {invocation_source}")

    return {
        "executionId": execution_id,
        "status": "PENDING",
        "invocationSource": invocation_source,
        "selectionMode": selection_mode,
        "initiatedBy": initiated_by,
    }


def build_initiated_by(source: str, details: Dict) -> str:
    """Build human-readable InitiatedBy string for display"""

    if source == "UI":
        email = sanitize_string(details.get("userEmail", "UI User"), 100)
        # Validate email format for additional security
        if validate_email(email):
            return email
        else:
            log_security_event(
                "invalid_email_format",
                {"email": email[:20] + "..." if len(email) > 20 else email},
                "WARN",
            )
            return "UI User"
    elif source == "CLI":
        user = details.get("iamUser") or details.get(
            "correlationId", "unknown"
        )
        user = sanitize_string(str(user), 50)
        return f"cli: {user}"
    elif source == "EVENTBRIDGE":
        rule = sanitize_string(details.get("scheduleRuleName", "unknown"), 50)
        return f"schedule: {rule}"
    elif source == "SSM":
        doc = sanitize_string(details.get("ssmDocumentName", "unknown"), 50)
        return f"ssm: {doc}"
    elif source == "STEPFUNCTIONS":
        parent = sanitize_string(
            details.get("parentExecutionId", "unknown"), 50
        )
        return (
            f"stepfunctions: {parent[:8]}..."
            if len(parent) > 8
            else f"stepfunctions: {parent}"
        )
    else:
        correlation = sanitize_string(
            details.get("correlationId", "unknown"), 50
        )
        return f"api: {correlation}"


def update_execution(event: Dict) -> Dict:
    """Update execution status, waves, or other fields"""
    execution_id = event["executionId"]

    # Validate execution_id format using security utils
    if not validate_uuid(execution_id):
        log_security_event(
            "invalid_execution_id",
            {
                "execution_id": (
                    execution_id[:20] + "..."
                    if len(execution_id) > 20
                    else execution_id
                )
            },
            "WARN",
        )
        raise ValueError(f"Invalid execution ID format: {execution_id}")

    update_parts = ["LastUpdated = :updated"]
    expr_names = {}
    expr_values = {":updated": int(time.time())}

    # Status update
    if "status" in event:
        status = sanitize_string(str(event["status"]), 50)
        update_parts.append("#status = :status")
        expr_names["#status"] = "Status"
        expr_values[":status"] = status

    # Waves update
    if "waves" in event:
        # Sanitize waves data
        sanitized_waves = sanitize_dynamodb_input({"waves": event["waves"]})[
            "waves"
        ]
        update_parts.append("Waves = :waves")
        expr_values[":waves"] = sanitized_waves

    # Total waves
    if "totalWaves" in event:
        update_parts.append("TotalWaves = :totalWaves")
        expr_values[":totalWaves"] = int(event["totalWaves"])

    # Total servers
    if "totalServers" in event:
        update_parts.append("TotalServers = :totalServers")
        expr_values[":totalServers"] = int(event["totalServers"])

    # Current wave
    if "currentWave" in event:
        update_parts.append("CurrentWave = :currentWave")
        expr_values[":currentWave"] = int(event["currentWave"])

    # Error message
    if "errorMessage" in event:
        error_msg = sanitize_string(str(event["errorMessage"]), 1000)
        update_parts.append("ErrorMessage = :errorMessage")
        expr_values[":errorMessage"] = error_msg

    update_expr = "SET " + ", ".join(update_parts)

    update_kwargs = {
        "Key": {"ExecutionId": execution_id.strip()},
        "UpdateExpression": update_expr,
        "ExpressionAttributeValues": expr_values,
        "ConditionExpression": "attribute_exists(ExecutionId)",
    }

    if expr_names:
        update_kwargs["ExpressionAttributeNames"] = expr_names

    # Use safe AWS client call
    try:
        safe_aws_client_call(execution_table.update_item, **update_kwargs)
        log_security_event(
            "execution_updated",
            {
                "execution_id": execution_id,
                "status": event.get("status", "no status change"),
            },
        )
    except Exception as e:
        log_security_event(
            "dynamodb_update_error",
            {"execution_id": execution_id, "error": str(e)},
            "ERROR",
        )
        raise

    print(
        f"Updated execution {execution_id}: {event.get('status', 'no status change')}"
    )

    return {
        "executionId": execution_id,
        "status": event.get("status", "UPDATED"),
    }


def complete_execution(event: Dict) -> Dict:
    """Mark execution as complete with final result"""
    execution_id = event["executionId"]
    result = event.get("result", {})

    # Normalize status
    status = result.get("status", "COMPLETED").upper()
    if status == "SUCCESS":
        status = "COMPLETED"
    elif status == "PARTIAL":
        status = "PARTIAL"
    elif status in ["FAILED", "ERROR"]:
        status = "FAILED"
    elif status == "TIMEOUT":
        status = "TIMEOUT"

    timestamp = int(time.time())

    update_expr = "SET #status = :status, EndTime = :endTime, #result = :result, LastUpdated = :updated"
    expr_names = {"#status": "Status", "#result": "Result"}
    expr_values = {
        ":status": status,
        ":endTime": timestamp,
        ":result": result,
        ":updated": timestamp,
    }

    # Update summary fields if provided
    summary = result.get("summary", {})
    if summary:
        if "totalServers" in summary:
            update_expr += ", TotalServers = :totalServers"
            expr_values[":totalServers"] = summary["totalServers"]
        if "succeeded" in summary:
            update_expr += ", SucceededServers = :succeeded"
            expr_values[":succeeded"] = summary["succeeded"]
        if "failed" in summary:
            update_expr += ", FailedServers = :failed"
            expr_values[":failed"] = summary["failed"]

    execution_table.update_item(
        Key={"ExecutionId": execution_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
        ConditionExpression="attribute_exists(ExecutionId)",
    )

    print(f"Completed execution {execution_id} with status {status}")

    return {
        "executionId": execution_id,
        "status": status,
        "endTime": timestamp,
    }


def get_execution(event: Dict) -> Dict:
    """Get execution by ID"""
    execution_id = event["executionId"]

    # Validate execution_id format using security utils
    if not validate_uuid(execution_id):
        log_security_event(
            "invalid_execution_id_get",
            {
                "execution_id": (
                    execution_id[:20] + "..."
                    if len(execution_id) > 20
                    else execution_id
                )
            },
            "WARN",
        )
        raise ValueError(f"Invalid execution ID format: {execution_id}")

    try:
        result = safe_aws_client_call(
            execution_table.get_item, Key={"ExecutionId": execution_id.strip()}
        )

        if not result:
            log_security_event(
                "dynamodb_get_error", {"execution_id": execution_id}, "ERROR"
            )
            raise ValueError("Failed to query DynamoDB")

        item = result.get("Item")

        if not item:
            log_security_event(
                "execution_not_found", {"execution_id": execution_id}, "WARN"
            )
            raise ValueError(f"Execution not found: {execution_id}")

        return item

    except Exception as e:
        log_security_event(
            "get_execution_error",
            {"execution_id": execution_id, "error": str(e)},
            "ERROR",
        )
        raise
