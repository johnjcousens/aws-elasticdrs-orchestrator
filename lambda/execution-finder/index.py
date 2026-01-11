"""
Execution Finder Lambda
Queries DynamoDB StatusIndex GSI for executions in POLLING status.
Implements adaptive polling intervals based on execution phase.
Invokes Execution Poller Lambda asynchronously per execution.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

import boto3

from shared.security_utils import (
    log_security_event,
    safe_aws_client_call,
    sanitize_string_input,
    validate_dynamodb_input,
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.client("dynamodb")
lambda_client = boto3.client("lambda")

# Environment variables (with defaults for testing)
EXECUTION_HISTORY_TABLE = os.environ.get(
    "EXECUTION_HISTORY_TABLE", "test-execution-table"
)
STATUS_INDEX_NAME = "StatusIndex"
EXECUTION_POLLER_FUNCTION = os.environ.get(
    "EXECUTION_POLLER_FUNCTION", "test-execution-poller"
)

# Adaptive polling interval thresholds (seconds)
POLLING_INTERVAL_PENDING = 45  # PENDING phase: 45s (slow, predictable)
POLLING_INTERVAL_STARTED = (
    15  # STARTED phase: 15s (rapid, critical transition)
)
POLLING_INTERVAL_IN_PROGRESS = 30  # IN_PROGRESS phase: 30s (normal)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for Execution Finder.

    Invoked by EventBridge on a schedule (default: 30s intervals).
    Queries StatusIndex GSI for executions with Status=POLLING.
    Applies adaptive polling intervals based on execution phase.
    Invokes Execution Poller Lambda asynchronously per execution.

    Args:
        event: EventBridge scheduled event
        context: Lambda context object

    Returns:
        Dict containing invocation results
    """
    try:
        # Enhanced security logging
        log_security_event(
            "execution_finder_invoked",
            {
                "function_name": context.function_name,
                "event_source": event.get("source", "eventbridge"),
                "context_request_id": context.aws_request_id,
                "event_detail_type": event.get("detail-type", "Scheduled Event"),
            },
        )

        # Validate EventBridge event structure
        source = sanitize_string_input(event.get("source", ""))
        if not source:
            log_security_event("invalid_eventbridge_event", {"event_keys": list(event.keys())})
            return {"statusCode": 400, "body": "Invalid EventBridge event"}

        logger.info("Execution Finder Lambda invoked")
        logger.info(
            f"Querying table: {EXECUTION_HISTORY_TABLE}, "
            f"index: {STATUS_INDEX_NAME}"
        )

        # Query StatusIndex GSI for POLLING executions with safe AWS call
        def query_polling_executions_safe():
            return query_polling_executions()

        polling_executions = safe_aws_client_call(query_polling_executions_safe)

        logger.info(
            f"Found {len(polling_executions)} executions in POLLING status"
        )

        if not polling_executions:
            logger.info("No executions found in POLLING status")
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "executionCount": 0,
                        "invocations": 0,
                        "message": "No executions in POLLING status",
                    }
                ),
            }

        # Filter executions that need polling now (adaptive intervals)
        executions_to_poll = []
        skipped_executions = []

        for execution in polling_executions:
            if should_poll_now(execution):
                executions_to_poll.append(execution)
            else:
                skipped_executions.append(execution["executionId"])

        logger.info(f"Executions to poll now: {len(executions_to_poll)}")
        if skipped_executions:
            logger.info(
                f"Skipped executions (not yet time): {skipped_executions}"
            )

        # Invoke Execution Poller Lambda for each execution (async)
        invocation_results = invoke_pollers_for_executions(executions_to_poll)

        log_security_event(
            "execution_finder_completed",
            {
                "total_executions": len(polling_executions),
                "executions_polled": len(executions_to_poll),
                "executions_skipped": len(skipped_executions),
            },
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "executionCount": len(polling_executions),
                    "executionsPolled": len(executions_to_poll),
                    "executionsSkipped": len(skipped_executions),
                    "invocations": invocation_results,
                    "message": (
                        f"Invoked poller for {len(executions_to_poll)} "
                        f"executions"
                    ),
                }
            ),
        }

    except Exception as e:
        log_security_event(
            "execution_finder_error", {"error": str(e)}, "ERROR"
        )
        logger.error(f"Error in Execution Finder: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": str(e),
                    "message": (
                        "Failed to query and invoke polling executions"
                    ),
                }
            ),
        }


def query_polling_executions() -> List[Dict[str, Any]]:
    """
    Query DynamoDB StatusIndex GSI for executions that need polling.

    Queries for:
    - Status=POLLING: Active executions being monitored
    - Status=CANCELLING: Cancelled executions with in-progress waves that need final status update
    - Status=PAUSED: Paused executions that still need DRS job monitoring

    CRITICAL: Status is a reserved keyword in DynamoDB.
    MUST use ExpressionAttributeNames to avoid ValidationException.

    Returns:
        List of execution records that need polling
    """
    executions = []

    # Statuses that need polling
    statuses_to_poll = ["POLLING", "CANCELLING"]

    for status in statuses_to_poll:
        try:
            # CRITICAL: Use expression attribute names for reserved keyword "Status"
            def dynamodb_query():
                return dynamodb.query(
                    TableName=EXECUTION_HISTORY_TABLE,
                    IndexName=STATUS_INDEX_NAME,
                    KeyConditionExpression="#status = :status",
                    ExpressionAttributeNames={
                        "#status": "Status"  # Required: Status is reserved keyword
                    },
                    ExpressionAttributeValues={":status": {"S": status}},
                )

            response = safe_aws_client_call(dynamodb_query)

            logger.info(
                f"DynamoDB query for {status} returned {response['Count']} "
                f"items"
            )

            # Parse DynamoDB items to Python dicts
            for item in response.get("Items", []):
                execution = parse_dynamodb_item(item)
                executions.append(execution)

        except Exception as e:
            logger.error(
                f"Error querying StatusIndex for {status}: {str(e)}",
                exc_info=True,
            )
            raise

    return executions


def parse_dynamodb_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse DynamoDB item format to Python dict.

    Converts DynamoDB's typed format {'S': 'value'} to simple values.
    Handles nested structures (Lists, Maps).

    Args:
        item: DynamoDB item in typed format

    Returns:
        Parsed Python dictionary
    """
    result = {}

    for key, value in item.items():
        if "S" in value:  # String
            result[key] = value["S"]
        elif "N" in value:  # Number
            result[key] = (
                int(value["N"]) if "." not in value["N"] else float(value["N"])
            )
        elif "L" in value:  # List
            result[key] = [parse_dynamodb_value(v) for v in value["L"]]
        elif "M" in value:  # Map
            result[key] = parse_dynamodb_item(value["M"])
        elif "BOOL" in value:  # Boolean
            result[key] = value["BOOL"]
        elif "NULL" in value:  # Null
            result[key] = None
        else:
            result[key] = value

    return result


def parse_dynamodb_value(value: Dict[str, Any]) -> Any:
    """
    Parse a single DynamoDB value.

    Args:
        value: DynamoDB value in typed format

    Returns:
        Parsed Python value
    """
    if "S" in value:
        return value["S"]
    elif "N" in value:
        return int(value["N"]) if "." not in value["N"] else float(value["N"])
    elif "L" in value:
        return [parse_dynamodb_value(v) for v in value["L"]]
    elif "M" in value:
        return parse_dynamodb_item(value["M"])
    elif "BOOL" in value:
        return value["BOOL"]
    elif "NULL" in value:
        return None
    else:
        return value


def should_poll_now(execution: Dict[str, Any]) -> bool:
    """
    Determine if execution should be polled now based on adaptive intervals.

    Implements adaptive polling strategy:
    - PENDING phase: 45s intervals (slow, predictable)
    - STARTED phase: 15s intervals (rapid, critical transition)
    - IN_PROGRESS phase: 30s intervals (normal)

    Args:
        execution: Execution record from DynamoDB

    Returns:
        True if execution should be polled now, False otherwise
    """
    try:
        # Get last polled timestamp (Unix timestamp in seconds)
        last_polled = execution.get("LastPolledTime", 0)
        current_time = datetime.now(timezone.utc).timestamp()

        # Calculate time since last poll
        time_since_poll = current_time - last_polled

        # Detect execution phase from waves data
        waves = execution.get("waves", [])
        phase = detect_execution_phase(waves)

        # Determine polling interval based on phase
        if phase == "PENDING":
            interval = POLLING_INTERVAL_PENDING
        elif phase == "STARTED":
            interval = POLLING_INTERVAL_STARTED
        else:  # IN_PROGRESS or unknown
            interval = POLLING_INTERVAL_IN_PROGRESS

        should_poll = time_since_poll >= interval

        if should_poll:
            logger.info(
                f"ExecutionId {execution["executionId"]}: "
                f"Phase={phase}, TimeSincePoll={time_since_poll:.1f}s, "
                f"Interval={interval}s - POLLING NOW"
            )
        else:
            logger.debug(
                f"ExecutionId {execution["executionId"]}: "
                f"Phase={phase}, TimeSincePoll={time_since_poll:.1f}s, "
                f"Interval={interval}s - Skipping (not time yet)"
            )

        return should_poll

    except Exception as e:
        logger.error(
            f"Error determining poll timing for "
            f"{execution.get("executionId")}: {str(e)}"
        )
        # Default to polling on error (fail-safe)
        return True


def detect_execution_phase(waves: List[Dict[str, Any]]) -> str:
    """
    Detect execution phase from wave server statuses.

    Phase Detection Logic:
    - PENDING: All servers NOT_STARTED (launch not initiated yet)
    - STARTED: At least one server PENDING_LAUNCH or LAUNCHING (transition phase)
    - IN_PROGRESS: At least one server in active state (LAUNCHED, RECOVERING, etc.)

    Args:
        waves: List of wave records with server status data

    Returns:
        Detected phase: 'PENDING', 'STARTED', or 'IN_PROGRESS'
    """
    if not waves:
        return "PENDING"

    try:
        # Collect all server statuses across waves
        all_server_statuses = []
        for wave in waves:
            servers = wave.get("servers", [])
            for server in servers:
                status = server.get("status", "NOT_STARTED")
                all_server_statuses.append(status)

        if not all_server_statuses:
            return "PENDING"

        # Phase detection based on server statuses
        started_statuses = {"PENDING_LAUNCH", "LAUNCHING"}
        in_progress_statuses = {
            "LAUNCHED",
            "RECOVERING",
            "RECOVERY_IN_PROGRESS",
            "FAILBACK",
        }

        # Check for STARTED phase (critical transition)
        if any(status in started_statuses for status in all_server_statuses):
            return "STARTED"

        # Check for IN_PROGRESS phase (active recovery)
        if any(
            status in in_progress_statuses for status in all_server_statuses
        ):
            return "IN_PROGRESS"

        # Default to PENDING if all servers NOT_STARTED
        return "PENDING"

    except Exception as e:
        logger.error(f"Error detecting execution phase: {str(e)}")
        # Default to IN_PROGRESS (most aggressive polling)
        return "IN_PROGRESS"


def invoke_pollers_for_executions(
    executions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Invoke Execution Poller Lambda asynchronously for each execution.

    Invokes separate Lambda per execution for parallel processing.
    Uses Event invocation type (async, no response wait).

    Args:
        executions: List of execution records to poll

    Returns:
        Dict with invocation results
    """
    successful_invocations = []
    failed_invocations = []

    for execution in executions:
        execution_id = execution["executionId"]

        try:
            # Validate and sanitize execution data
            execution_id = sanitize_string_input(execution["executionId"])
            plan_id = sanitize_string_input(execution.get("planId", ""))
            execution_type = sanitize_string_input(execution.get("executionType", "DRILL"))
            
            # Validate execution ID format
            validate_dynamodb_input("ExecutionId", execution_id)

            # Prepare payload for Execution Poller
            payload = {
                "executionId": execution_id,
                "planId": plan_id,
                "executionType": execution_type,
                "startTime": execution.get("startTime"),
            }

            # Invoke Execution Poller Lambda (async) with safe AWS call
            def lambda_invoke():
                return lambda_client.invoke(
                    FunctionName=EXECUTION_POLLER_FUNCTION,
                    InvocationType="Event",  # Async invocation
                    Payload=json.dumps(payload),
                )

            response = safe_aws_client_call(lambda_invoke)

            logger.info(
                f"Invoked Execution Poller for "
                f"{str(execution_id).replace('\n', '').replace('\r', '')}, "
                f"StatusCode: {response['StatusCode']}"
            )

            successful_invocations.append(
                {
                    "executionId": execution_id,
                    "StatusCode": response["StatusCode"],
                }
            )

        except Exception as e:
            logger.error(
                f"Failed to invoke Execution Poller for {execution_id}: "
                f"{str(e)}",
                exc_info=True,
            )
            failed_invocations.append(
                {"executionId": execution_id, "error": str(e)}
            )

    return {
        "successful": len(successful_invocations),
        "failed": len(failed_invocations),
        "details": {
            "successful": successful_invocations,
            "failed": failed_invocations,
        },
    }
