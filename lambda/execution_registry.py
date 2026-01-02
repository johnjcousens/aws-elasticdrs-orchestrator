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

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")

# Environment variables
EXECUTION_HISTORY_TABLE = os.environ.get("EXECUTION_HISTORY_TABLE", "execution-history")

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
    print(f"Execution Registry received: {json.dumps(event, cls=DecimalEncoder)}")

    action = event.get("action", "register")

    try:
        if action == "register":
            return register_execution(event)
        elif action == "update":
            return update_execution(event)
        elif action == "complete":
            return complete_execution(event)
        elif action == "get":
            return get_execution(event)
        else:
            raise ValueError(f"Unknown action: {action}")
    except Exception as e:
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
    import re

    def sanitize_input(value: str) -> str:
        """Sanitize user input to prevent XSS"""
        if not isinstance(value, str):
            return "unknown"
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\'\/\\&]', "", str(value))
        return sanitized[:50] if sanitized else "unknown"

    if source == "UI":
        email = sanitize_input(details.get("userEmail", "UI User"))
        return email
    elif source == "CLI":
        user = details.get("iamUser") or details.get("correlationId", "unknown")
        user = sanitize_input(user)
        return f"cli:{user}"  # noqa: E231
    elif source == "EVENTBRIDGE":
        rule = sanitize_input(details.get("scheduleRuleName", "unknown"))
        return f"schedule:{rule}"  # noqa: E231
    elif source == "SSM":
        doc = sanitize_input(details.get("ssmDocumentName", "unknown"))
        return f"ssm:{doc}"  # noqa: E231
    elif source == "STEPFUNCTIONS":
        parent = sanitize_input(details.get("parentExecutionId", "unknown"))
        return (
            f"stepfunctions:{parent[:8]}..."  # noqa: E231
            if len(parent) > 8
            else f"stepfunctions:{parent}"  # noqa: E231
        )
    else:
        correlation = sanitize_input(details.get("correlationId", "unknown"))
        return f"api:{correlation}"


def update_execution(event: Dict) -> Dict:
    """Update execution status, waves, or other fields"""
    execution_id = event["executionId"]

    # Validate execution_id to prevent injection
    if not isinstance(execution_id, str) or not execution_id.strip():
        raise ValueError("Invalid execution ID format")

    # Sanitize execution_id (should be UUID format)
    import re

    if not re.match(r"^[a-fA-F0-9-]{36}$", execution_id.strip()):
        raise ValueError(f"Invalid execution ID format: {execution_id}")

    update_parts = ["LastUpdated = :updated"]
    expr_names = {}
    expr_values = {":updated": int(time.time())}

    # Status update
    if "status" in event:
        update_parts.append("#status = :status")
        expr_names["#status"] = "Status"
        expr_values[":status"] = str(event["status"])  # Ensure string type

    # Waves update
    if "waves" in event:
        update_parts.append("Waves = :waves")
        expr_values[":waves"] = event["waves"]

    # Total waves
    if "totalWaves" in event:
        update_parts.append("TotalWaves = :totalWaves")
        expr_values[":totalWaves"] = int(event["totalWaves"])  # Ensure integer type

    # Total servers
    if "totalServers" in event:
        update_parts.append("TotalServers = :totalServers")
        expr_values[":totalServers"] = int(event["totalServers"])  # Ensure integer type

    # Current wave
    if "currentWave" in event:
        update_parts.append("CurrentWave = :currentWave")
        expr_values[":currentWave"] = int(event["currentWave"])  # Ensure integer type

    # Error message
    if "errorMessage" in event:
        update_parts.append("ErrorMessage = :errorMessage")
        expr_values[":errorMessage"] = str(event["errorMessage"])  # Ensure string type

    update_expr = "SET " + ", ".join(update_parts)

    update_kwargs = {
        "Key": {"ExecutionId": execution_id.strip()},
        "UpdateExpression": update_expr,
        "ExpressionAttributeValues": expr_values,
        "ConditionExpression": "attribute_exists(ExecutionId)",
    }

    if expr_names:
        update_kwargs["ExpressionAttributeNames"] = expr_names

    execution_table.update_item(**update_kwargs)

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

    # Validate execution_id format to prevent injection
    if not isinstance(execution_id, str) or not execution_id.strip():
        raise ValueError("Invalid execution ID format")

    # Sanitize execution_id (should be UUID format)
    import re

    if not re.match(r"^[a-f0-9-]{36}$", execution_id.strip()):
        raise ValueError(f"Invalid execution ID format: {execution_id}")

    result = execution_table.get_item(Key={"ExecutionId": execution_id.strip()})
    item = result.get("Item")

    if not item:
        raise ValueError(f"Execution not found: {execution_id}")

    return item
