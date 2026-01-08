"""
Execution Poller Lambda
Polls DRS job status for a single execution.
Updates DynamoDB with wave/server status.
Handles timeouts and detects completion.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3

# Import security utilities
try:
    from security_utils import (
        create_response_with_security_headers,
        log_security_event,
        safe_aws_client_call,
        sanitize_string_input,
        validate_dynamodb_input,
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
dynamodb = boto3.client("dynamodb")
drs = boto3.client("drs")
cloudwatch = boto3.client("cloudwatch")

# Environment variables (with defaults for testing)
EXECUTION_HISTORY_TABLE = os.environ.get(
    "EXECUTION_HISTORY_TABLE", "test-execution-table"
)
TIMEOUT_THRESHOLD_SECONDS = int(
    os.environ.get("TIMEOUT_THRESHOLD_SECONDS", "1800")
)  # 30 minutes

# Execution completion statuses (include both cases for consistency)
COMPLETED_STATUSES = {"COMPLETED", "completed", "FAILED", "TERMINATED", "TIMEOUT"}

# DRS job statuses that indicate completion
DRS_COMPLETED_STATUSES = {"COMPLETED", "FAILED"}


def lambda_handler(
    event: Dict[str, Any], context: Any
) -> Dict[str, Any]:  # noqa: C901
    """
    Main Lambda handler for Execution Poller.

    Invoked by Execution Finder for each execution in POLLING or CANCELLING status.
    Polls DRS job status and updates DynamoDB.

    Args:
        event: Payload from Execution Finder
            - ExecutionId: Unique execution identifier
            - PlanId: Recovery plan ID
            - ExecutionType: DRILL or RECOVERY
            - StartTime: Execution start timestamp
        context: Lambda context object

    Returns:
        Dict containing polling results
    """
    try:
        # Security validation
        if SECURITY_ENABLED:
            log_security_event(
                "execution_poller_invoked",
                {
                    "function_name": context.function_name,
                    "request_id": context.aws_request_id,
                    "event_keys": list(event.keys()) if event else [],
                },
            )

            # Validate and sanitize inputs
            execution_id = sanitize_string_input(event.get("ExecutionId", ""))
            plan_id = sanitize_string_input(event.get("PlanId", ""))
            execution_type = sanitize_string_input(
                event.get("ExecutionType", "DRILL")
            )

            if not execution_id or not plan_id:
                log_security_event(
                    "invalid_input_detected",
                    {
                        "error": "Missing required parameters",
                        "execution_id": bool(execution_id),
                        "plan_id": bool(plan_id),
                    },
                )
                return create_response_with_security_headers(
                    400,
                    {
                        "error": "Missing required parameters: ExecutionId and PlanId"
                    },
                )
        else:
            execution_id = event["ExecutionId"]
            plan_id = event["PlanId"]
            execution_type = event.get("ExecutionType", "DRILL")

        start_time = event.get("StartTime")

        logger.info(
            f"Polling execution: {execution_id} (Type: {execution_type})"
        )

        # Get current execution state from DynamoDB
        execution = get_execution_from_dynamodb(execution_id, plan_id)

        if not execution:
            logger.error(f"Execution not found: {execution_id}")
            if SECURITY_ENABLED:
                log_security_event(
                    "execution_not_found",
                    {"execution_id": execution_id, "plan_id": plan_id},
                )
                return create_response_with_security_headers(
                    404,
                    {
                        "error": "Execution not found",
                        "ExecutionId": execution_id,
                    },
                )
            else:
                return {
                    "statusCode": 404,
                    "body": json.dumps(
                        {
                            "error": "Execution not found",
                            "ExecutionId": execution_id,
                        }
                    ),
                }

        # Check if execution is being cancelled
        execution_status = execution.get("Status", "POLLING")
        is_cancelling = execution_status == "CANCELLING"

        if is_cancelling:
            logger.info(
                f"Execution {execution_id} is CANCELLING - polling in-progress waves only"
            )

        # Check if execution has timed out (skip timeout for CANCELLING - we want to finalize)
        if not is_cancelling and has_execution_timed_out(
            execution, start_time
        ):
            logger.warning(
                f"Execution {execution_id} has timed out (>{TIMEOUT_THRESHOLD_SECONDS}s)"
            )
            handle_timeout(execution_id, plan_id, execution)
            if SECURITY_ENABLED:
                return create_response_with_security_headers(
                    200,
                    {
                        "ExecutionId": execution_id,
                        "Status": "TIMEOUT",
                        "message": "Execution timed out",
                    },
                )
            else:
                return {
                    "statusCode": 200,
                    "body": json.dumps(
                        {
                            "ExecutionId": execution_id,
                            "Status": "TIMEOUT",
                            "message": "Execution timed out",
                        }
                    ),
                }

        # Poll wave status from DRS
        waves = execution.get("Waves", [])
        updated_waves = []
        all_active_waves_complete = True
        waves_polled = 0

        # Statuses that indicate a wave is in-progress and needs polling
        IN_PROGRESS_STATUSES = {
            "IN_PROGRESS",
            "POLLING",
            "LAUNCHING",
            "INITIATED",
            "STARTED",
            "PENDING",
        }

        for wave in waves:
            wave_status = wave.get("Status", "")

            # For CANCELLING executions, only poll waves that are in-progress
            if is_cancelling:
                if wave_status in IN_PROGRESS_STATUSES:
                    logger.info(
                        f"Polling in-progress wave {wave.get('WaveId')} (status: {wave_status})"
                    )
                    updated_wave = poll_wave_status(wave, execution_type)
                    waves_polled += 1

                    # Set EndTime on wave if it just completed
                    if updated_wave.get(
                        "Status"
                    ) in COMPLETED_STATUSES and not updated_wave.get(
                        "EndTime"
                    ):
                        updated_wave["EndTime"] = int(
                            datetime.now(timezone.utc).timestamp()
                        )
                        logger.info(
                            f"Wave {wave.get('WaveId')} completed, set EndTime"
                        )

                    updated_waves.append(updated_wave)

                    # Check if this wave is still in progress
                    if updated_wave.get("Status") not in COMPLETED_STATUSES:
                        all_active_waves_complete = False
                else:
                    # Wave already completed or cancelled - keep as-is
                    updated_waves.append(wave)
            else:
                # Normal polling - poll all waves
                updated_wave = poll_wave_status(wave, execution_type)

                # Set EndTime on wave if it just completed
                if updated_wave.get(
                    "Status"
                ) in COMPLETED_STATUSES and not updated_wave.get("EndTime"):
                    updated_wave["EndTime"] = int(
                        datetime.now(timezone.utc).timestamp()
                    )

                updated_waves.append(updated_wave)

                # Check if wave is complete
                if updated_wave.get("Status") not in COMPLETED_STATUSES:
                    all_active_waves_complete = False

        # Update execution in DynamoDB
        update_execution_waves(execution_id, plan_id, updated_waves)

        # Update LastPolledTime for adaptive polling
        update_last_polled_time(execution_id, plan_id)

        # Check if execution is complete
        if all_active_waves_complete:
            if is_cancelling:
                logger.info(
                    f"All in-progress waves complete for CANCELLING execution {execution_id}"
                )
                finalize_execution(
                    execution_id,
                    plan_id,
                    updated_waves,
                    final_status="CANCELLED",
                )

                if SECURITY_ENABLED:
                    return create_response_with_security_headers(
                        200,
                        {
                            "ExecutionId": execution_id,
                            "Status": "CANCELLED",
                            "message": "Cancelled execution finalized after in-progress waves completed",
                        },
                    )
                else:
                    return {
                        "statusCode": 200,
                        "body": json.dumps(
                            {
                                "ExecutionId": execution_id,
                                "Status": "CANCELLED",
                                "message": "Cancelled execution finalized after in-progress waves completed",
                            }
                        ),
                    }
            else:
                logger.info(f"All waves complete for execution {execution_id}")
                finalize_execution(execution_id, plan_id, updated_waves)

                if SECURITY_ENABLED:
                    return create_response_with_security_headers(
                        200,
                        {
                            "ExecutionId": execution_id,
                            "Status": "COMPLETED",
                            "message": "Execution completed successfully",
                        },
                    )
                else:
                    return {
                        "statusCode": 200,
                        "body": json.dumps(
                            {
                                "ExecutionId": execution_id,
                                "Status": "COMPLETED",
                                "message": "Execution completed successfully",
                            }
                        ),
                    }

        # Record polling metrics
        record_poller_metrics(execution_id, execution_type, updated_waves)

        if SECURITY_ENABLED:
            return create_response_with_security_headers(
                200,
                {
                    "ExecutionId": execution_id,
                    "Status": execution_status,
                    "WavesPolled": (
                        waves_polled if is_cancelling else len(updated_waves)
                    ),
                    "message": "Polling in progress",
                },
            )
        else:
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "ExecutionId": execution_id,
                        "Status": execution_status,
                        "WavesPolled": (
                            waves_polled
                            if is_cancelling
                            else len(updated_waves)
                        ),
                        "message": "Polling in progress",
                    }
                ),
            }

    except Exception as e:
        logger.error(f"Error in Execution Poller: {str(e)}", exc_info=True)
        if SECURITY_ENABLED:
            log_security_event(
                "execution_poller_error",
                {
                    "error": str(e),
                    "execution_id": event.get("ExecutionId", "unknown"),
                    "plan_id": event.get("PlanId", "unknown"),
                },
            )
            return create_response_with_security_headers(
                500, {"error": str(e), "message": "Failed to poll execution"}
            )
        else:
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {"error": str(e), "message": "Failed to poll execution"}
                ),
            }


def get_execution_from_dynamodb(
    execution_id: str, plan_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get execution record from DynamoDB.

    Args:
        execution_id: Execution ID
        plan_id: Plan ID

    Returns:
        Execution record or None if not found
    """
    try:
        # Security validation for DynamoDB inputs
        if SECURITY_ENABLED:
            validate_dynamodb_input("ExecutionId", execution_id)
            validate_dynamodb_input("PlanId", plan_id)

        response = (
            safe_aws_client_call(
                dynamodb.get_item,
                TableName=EXECUTION_HISTORY_TABLE,
                Key={
                    "ExecutionId": {"S": execution_id},
                    "PlanId": {"S": plan_id},
                },
            )
            if SECURITY_ENABLED
            else dynamodb.get_item(
                TableName=EXECUTION_HISTORY_TABLE,
                Key={
                    "ExecutionId": {"S": execution_id},
                    "PlanId": {"S": plan_id},
                },
            )
        )

        if "Item" not in response:
            return None

        return parse_dynamodb_item(response["Item"])

    except Exception as e:
        logger.error(
            f"Error getting execution from DynamoDB: {str(e)}", exc_info=True
        )
        if SECURITY_ENABLED:
            log_security_event(
                "dynamodb_get_error",
                {
                    "error": str(e),
                    "table": EXECUTION_HISTORY_TABLE,
                    "execution_id": execution_id,
                },
            )
        raise


def parse_dynamodb_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse DynamoDB item format to Python dict.

    Args:
        item: DynamoDB item in typed format

    Returns:
        Parsed Python dictionary
    """
    result = {}

    for key, value in item.items():
        if "S" in value:
            result[key] = value["S"]
        elif "N" in value:
            result[key] = (
                int(value["N"]) if "." not in value["N"] else float(value["N"])
            )
        elif "L" in value:
            result[key] = [parse_dynamodb_value(v) for v in value["L"]]
        elif "M" in value:
            result[key] = parse_dynamodb_item(value["M"])
        elif "BOOL" in value:
            result[key] = value["BOOL"]
        elif "NULL" in value:
            result[key] = None

    return result


def parse_dynamodb_value(value: Dict[str, Any]) -> Any:
    """Parse a single DynamoDB value."""
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


def has_execution_timed_out(
    execution: Dict[str, Any], start_time: Optional[int]
) -> bool:
    """
    Check if execution has exceeded timeout threshold.

    Args:
        execution: Execution record
        start_time: Execution start timestamp

    Returns:
        True if execution has timed out
    """
    if not start_time:
        start_time = execution.get("StartTime", 0)

    current_time = datetime.now(timezone.utc).timestamp()
    elapsed_time = current_time - start_time

    return elapsed_time > TIMEOUT_THRESHOLD_SECONDS


def handle_timeout(
    execution_id: str, plan_id: str, execution: Dict[str, Any]
) -> None:
    """
    Handle execution timeout.

    After 30 minutes, query DRS for final status rather than arbitrarily failing.
    DRS is source of truth for job status.

    Args:
        execution_id: Execution ID
        plan_id: Plan ID
        execution: Execution record
    """
    try:
        logger.info(f"Handling timeout for execution {execution_id}")

        # Query DRS for final status
        waves = execution.get("Waves", [])
        final_waves = []

        for wave in waves:
            # Get final status from DRS
            job_id = wave.get("JobId")
            if job_id:
                try:
                    job_status = query_drs_job_status(job_id)
                    wave["Status"] = job_status.get("Status", "TIMEOUT")
                    wave["StatusMessage"] = job_status.get(
                        "StatusMessage", "Execution timed out"
                    )
                except Exception as e:
                    logger.error(
                        f"Error querying DRS for job {job_id}: {str(e)}"
                    )
                    wave["Status"] = "TIMEOUT"
                    wave["StatusMessage"] = (
                        f"Timeout after {TIMEOUT_THRESHOLD_SECONDS}s"
                    )
            else:
                wave["Status"] = "TIMEOUT"
                wave["StatusMessage"] = (
                    f"Timeout after {TIMEOUT_THRESHOLD_SECONDS}s"
                )

            final_waves.append(wave)

        # Update execution with timeout status
        dynamodb.update_item(
            TableName=EXECUTION_HISTORY_TABLE,
            Key={"ExecutionId": {"S": execution_id}, "PlanId": {"S": plan_id}},
            UpdateExpression="SET #status = :status, Waves = :waves, EndTime = :end_time",
            ExpressionAttributeNames={"#status": "Status"},
            ExpressionAttributeValues={
                ":status": {"S": "TIMEOUT"},
                ":waves": {
                    "L": [format_wave_for_dynamodb(w) for w in final_waves]
                },
                ":end_time": {
                    "N": str(int(datetime.now(timezone.utc).timestamp()))
                },
            },
            ConditionExpression="attribute_exists(ExecutionId)",
        )

        logger.info(f"Execution {execution_id} marked as TIMEOUT")

    except Exception as e:
        logger.error(f"Error handling timeout: {str(e)}", exc_info=True)
        raise


def poll_wave_status(
    wave: Dict[str, Any], execution_type: str
) -> Dict[str, Any]:  # noqa: C901
    """
    Poll DRS job status for a wave.

    Args:
        wave: Wave record with job information
        execution_type: DRILL or RECOVERY

    Returns:
        Updated wave record with current status
    """
    try:
        job_id = wave.get("JobId")

        if not job_id:
            logger.warning(f"Wave {wave.get('WaveId')} has no JobId")
            return wave

        # Query DRS for job status
        job_status = query_drs_job_status(job_id)

        # Get DRS job status and message
        drs_status = job_status.get("Status", "UNKNOWN")
        wave["StatusMessage"] = job_status.get("StatusMessage", "")

        # Update server statuses from DRS participating servers
        if "ParticipatingServers" in job_status:
            wave_region = wave.get("Region", "us-east-1")
            server_statuses = []

            # Get recovery instances to find instance IDs for completed jobs
            recovery_instances = {}
            try:
                drs_client = boto3.client("drs", region_name=wave_region)
                recovery_response = drs_client.describe_recovery_instances()
                for instance in recovery_response.get("items", []):
                    source_server_id = instance.get("sourceServerID")
                    if source_server_id:
                        recovery_instances[source_server_id] = {
                            "recoveryInstanceID": instance.get("recoveryInstanceID"),
                            "ec2InstanceID": instance.get("ec2InstanceID"),
                            "ec2InstanceState": instance.get("ec2InstanceState"),
                        }
                logger.info(f"Found {len(recovery_instances)} recovery instances in {wave_region}")
            except Exception as e:
                logger.warning(f"Could not get recovery instances: {e}")

            for drs_server in job_status["ParticipatingServers"]:
                source_server_id = drs_server.get("sourceServerID", "")
                
                # Get recovery instance ID from DRS job or recovery instances lookup
                recovery_instance_id = drs_server.get("recoveryInstanceID")
                if not recovery_instance_id and source_server_id in recovery_instances:
                    # Fallback to recovery instances lookup for completed jobs
                    recovery_info = recovery_instances[source_server_id]
                    recovery_instance_id = (
                        recovery_info.get("recoveryInstanceID") or
                        recovery_info.get("ec2InstanceID")
                    )
                    logger.info(f"Found instance ID {recovery_instance_id} for server {source_server_id} via recovery instances lookup")

                # Use ServerStatuses format (matches API transform function expectations)
                server_status = {
                    "SourceServerId": source_server_id,
                    "LaunchStatus": drs_server.get("launchStatus", "UNKNOWN"),
                    "RecoveryInstanceID": recovery_instance_id,
                    "Error": None,
                }

                server_statuses.append(server_status)
                logger.info(f"Updated server {source_server_id}: status={server_status['LaunchStatus']}, instanceId={recovery_instance_id}")

            # Store in ServerStatuses format (matches API transform function expectations)
            wave["ServerStatuses"] = server_statuses
            
            # Keep legacy Servers array for backward compatibility
            legacy_servers = []
            for server_status in server_statuses:
                source_server_id = server_status["SourceServerId"]
                recovery_instance_id = server_status["RecoveryInstanceID"]
                
                server_data = {
                    "SourceServerId": source_server_id,
                    "Status": server_status["LaunchStatus"],
                    "HostName": "",
                    "LaunchTime": int(datetime.now(timezone.utc).timestamp()),
                    "InstanceId": recovery_instance_id or "",
                    "PrivateIpAddress": "",
                }

                # Enrich with EC2 data if we have an instance ID
                if recovery_instance_id:
                    try:
                        ec2_data = get_ec2_instance_details(
                            recovery_instance_id, wave_region
                        )
                        if ec2_data:
                            server_data["HostName"] = ec2_data.get("HostName", "")
                            server_data["PrivateIpAddress"] = ec2_data.get("PrivateIpAddress", "")
                    except Exception as e:
                        logger.warning(f"Could not fetch EC2 details for {recovery_instance_id}: {str(e)}")

                legacy_servers.append(server_data)

            wave["Servers"] = legacy_servers

        # Determine wave status based on server launch results
        server_statuses = wave.get("ServerStatuses", [])
        legacy_servers = wave.get("Servers", [])

        if execution_type == "DRILL":
            if server_statuses:
                # Use new ServerStatuses format
                all_launched = all(
                    s.get("LaunchStatus") == "LAUNCHED" for s in server_statuses
                )
                any_failed = any(
                    s.get("LaunchStatus")
                    in ["LAUNCH_FAILED", "FAILED", "TERMINATED"]
                    for s in server_statuses
                )

                if all_launched:
                    wave["Status"] = "completed"
                    logger.info(
                        f"Wave {wave.get('WaveId')} completed - all servers LAUNCHED"
                    )
                elif any_failed:
                    wave["Status"] = "FAILED"
                    failed_servers = [
                        s.get("SourceServerId")
                        for s in server_statuses
                        if s.get("LaunchStatus")
                        in ["LAUNCH_FAILED", "FAILED", "TERMINATED"]
                    ]
                    logger.warning(
                        f"Wave {wave.get('WaveId')} failed - servers {failed_servers} failed to launch"
                    )
                elif drs_status in ["PENDING", "STARTED"]:
                    wave["Status"] = "LAUNCHING"
                elif drs_status == "COMPLETED" and not all_launched:
                    # CRITICAL BUG FIX: DRS job completed but servers never launched
                    wave["Status"] = "FAILED"
                    not_launched_servers = [
                        s.get("SourceServerId")
                        for s in server_statuses
                        if s.get("LaunchStatus") != "LAUNCHED"
                    ]
                    logger.error(
                        f"Wave {wave.get('WaveId')} FAILED - DRS job COMPLETED but servers {not_launched_servers} never launched"
                    )
                    wave["StatusMessage"] = (
                        f"DRS job completed but {len(not_launched_servers)} servers failed to launch"
                    )
                else:
                    # Fallback to DRS status if no clear success/failure
                    wave["Status"] = drs_status
            elif legacy_servers:
                # Fallback to legacy Servers format
                all_launched = all(
                    s.get("Status") == "LAUNCHED" for s in legacy_servers
                )
                any_failed = any(
                    s.get("Status")
                    in ["LAUNCH_FAILED", "FAILED", "TERMINATED"]
                    for s in legacy_servers
                )

                if all_launched:
                    wave["Status"] = "completed"
                    logger.info(
                        f"Wave {wave.get('WaveId')} completed - all servers LAUNCHED"
                    )
                elif any_failed:
                    wave["Status"] = "FAILED"
                    failed_servers = [
                        s.get("SourceServerID")
                        for s in legacy_servers
                        if s.get("Status")
                        in ["LAUNCH_FAILED", "FAILED", "TERMINATED"]
                    ]
                    logger.warning(
                        f"Wave {wave.get('WaveId')} failed - servers {failed_servers} failed to launch"
                    )
                elif drs_status in ["PENDING", "STARTED"]:
                    wave["Status"] = "LAUNCHING"
                elif drs_status == "COMPLETED" and not all_launched:
                    # CRITICAL BUG FIX: DRS job completed but servers never launched
                    wave["Status"] = "FAILED"
                    not_launched_servers = [
                        s.get("SourceServerId")
                        for s in legacy_servers
                        if s.get("Status") != "LAUNCHED"
                    ]
                    logger.error(
                        f"Wave {wave.get('WaveId')} FAILED - DRS job COMPLETED but servers {not_launched_servers} never launched"
                    )
                    wave["StatusMessage"] = (
                        f"DRS job completed but {len(not_launched_servers)} servers failed to launch"
                    )
                else:
                    # Fallback to DRS status if no clear success/failure
                    wave["Status"] = drs_status
            else:
                # No servers yet, use DRS job status
                wave["Status"] = drs_status
        else:  # RECOVERY
            # RECOVERY complete when all servers LAUNCHED + post-launch complete
            if server_statuses:
                # Use new ServerStatuses format
                all_launched = all(
                    s.get("LaunchStatus") == "LAUNCHED" for s in server_statuses
                )
                any_failed = any(
                    s.get("LaunchStatus")
                    in ["LAUNCH_FAILED", "FAILED", "TERMINATED"]
                    for s in server_statuses
                )
                post_launch_complete = (
                    job_status.get("PostLaunchActionsStatus") == "COMPLETED"
                )

                if all_launched and post_launch_complete:
                    wave["Status"] = "completed"
                    logger.info(
                        f"Wave {wave.get('WaveId')} recovery completed"
                    )
                elif any_failed:
                    wave["Status"] = "FAILED"
                    logger.warning(
                        f"Wave {wave.get('WaveId')} recovery failed"
                    )
                elif drs_status in ["PENDING", "STARTED"]:
                    wave["Status"] = "LAUNCHING"
                elif drs_status == "COMPLETED" and not all_launched:
                    # CRITICAL BUG FIX: DRS job completed but servers never launched
                    wave["Status"] = "FAILED"
                    not_launched_servers = [
                        s.get("SourceServerId")
                        for s in server_statuses
                        if s.get("LaunchStatus") != "LAUNCHED"
                    ]
                    logger.error(
                        f"Wave {wave.get('WaveId')} RECOVERY FAILED - DRS job COMPLETED but servers {not_launched_servers} never launched"
                    )
                    wave["StatusMessage"] = (
                        f"DRS job completed but {len(not_launched_servers)} servers failed to launch"
                    )
                else:
                    wave["Status"] = drs_status
            elif legacy_servers:
                # Fallback to legacy Servers format
                all_launched = all(
                    s.get("Status") == "LAUNCHED" for s in legacy_servers
                )
                any_failed = any(
                    s.get("Status")
                    in ["LAUNCH_FAILED", "FAILED", "TERMINATED"]
                    for s in legacy_servers
                )
                post_launch_complete = (
                    job_status.get("PostLaunchActionsStatus") == "COMPLETED"
                )

                if all_launched and post_launch_complete:
                    wave["Status"] = "completed"
                    logger.info(
                        f"Wave {wave.get('WaveId')} recovery completed"
                    )
                elif any_failed:
                    wave["Status"] = "FAILED"
                    logger.warning(
                        f"Wave {wave.get('WaveId')} recovery failed"
                    )
                elif drs_status in ["PENDING", "STARTED"]:
                    wave["Status"] = "LAUNCHING"
                elif drs_status == "COMPLETED" and not all_launched:
                    # CRITICAL BUG FIX: DRS job completed but servers never launched
                    wave["Status"] = "FAILED"
                    not_launched_servers = [
                        s.get("SourceServerId")
                        for s in legacy_servers
                        if s.get("Status") != "LAUNCHED"
                    ]
                    logger.error(
                        f"Wave {wave.get('WaveId')} RECOVERY FAILED - DRS job COMPLETED but servers {not_launched_servers} never launched"
                    )
                    wave["StatusMessage"] = (
                        f"DRS job completed but {len(not_launched_servers)} servers failed to launch"
                    )
                else:
                    wave["Status"] = drs_status
            else:
                wave["Status"] = drs_status

        return wave

    except Exception as e:
        logger.error(f"Error polling wave status: {str(e)}", exc_info=True)
        wave["Status"] = "ERROR"
        wave["StatusMessage"] = f"Polling error: {str(e)}"
        return wave


def query_drs_job_status(job_id: str) -> Dict[str, Any]:
    """
    Query DRS API for job status.

    Args:
        job_id: DRS job ID

    Returns:
        Job status information
    """
    try:
        response = drs.describe_jobs(filters={"jobIDs": [job_id]})

        if not response.get("items"):
            logger.warning(f"No job found for ID {job_id}")
            return {"Status": "UNKNOWN", "StatusMessage": "Job not found"}

        job = response["items"][0]

        return {
            "Status": job.get("status", "UNKNOWN"),
            "StatusMessage": job.get("statusMessage", ""),
            "ParticipatingServers": job.get("participatingServers", []),
            "PostLaunchActionsStatus": job.get(
                "postLaunchActionsStatus", "NOT_STARTED"
            ),
        }

    except Exception as e:
        logger.error(
            f"Error querying DRS job {job_id}: {str(e)}", exc_info=True
        )
        raise


def get_ec2_instance_details(
    instance_id: str, region: str
) -> Optional[Dict[str, Any]]:
    """
    Get EC2 instance details to enrich server data.

    Args:
        instance_id: EC2 instance ID
        region: AWS region

    Returns:
        Dict with HostName and PrivateIpAddress or None
    """
    try:
        ec2 = boto3.client("ec2", region_name=region)

        response = ec2.describe_instances(InstanceIds=[instance_id])

        if not response.get("Reservations"):
            logger.warning(f"No instance found for {instance_id}")
            return None

        instance = response["Reservations"][0]["Instances"][0]

        # Try to get hostname from Name tag
        tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
        hostname = tags.get("Name", "")

        # Fallback to private DNS name if no Name tag
        if not hostname:
            hostname = instance.get("PrivateDnsName", "")

        return {
            "HostName": hostname,
            "PrivateIpAddress": instance.get("PrivateIpAddress", ""),
        }

    except Exception as e:
        logger.error(
            f"Error getting EC2 details for {instance_id}: {str(e)}",
            exc_info=True,
        )
        return None


def update_execution_waves(
    execution_id: str, plan_id: str, waves: List[Dict[str, Any]]
) -> None:
    """
    Update execution waves in DynamoDB.

    Args:
        execution_id: Execution ID
        plan_id: Plan ID
        waves: Updated wave records
    """
    try:
        # Security validation for DynamoDB inputs
        if SECURITY_ENABLED:
            validate_dynamodb_input("ExecutionId", execution_id)
            validate_dynamodb_input("PlanId", plan_id)

            # Sanitize execution_id and plan_id
            execution_id = sanitize_string_input(execution_id)
            plan_id = sanitize_string_input(plan_id)

        # Validate input parameters to prevent injection
        if not execution_id or not isinstance(execution_id, str):
            raise ValueError("Invalid execution_id")
        if not plan_id or not isinstance(plan_id, str):
            raise ValueError("Invalid plan_id")

        def update_call():
            return dynamodb.update_item(
                TableName=EXECUTION_HISTORY_TABLE,
                Key={
                    "ExecutionId": {"S": execution_id.strip()},
                    "PlanId": {"S": plan_id.strip()},
                },
                UpdateExpression="SET Waves = :waves",
                ExpressionAttributeValues={
                    ":waves": {
                        "L": [format_wave_for_dynamodb(w) for w in waves]
                    }
                },
                ConditionExpression="attribute_exists(ExecutionId) AND attribute_exists(PlanId)",
            )

        if SECURITY_ENABLED:
            safe_aws_client_call(update_call)
        else:
            update_call()

        logger.info(f"Updated {len(waves)} waves for execution {execution_id}")

    except Exception as e:
        logger.error(
            f"Error updating execution waves: {str(e)}", exc_info=True
        )
        if SECURITY_ENABLED:
            log_security_event(
                "dynamodb_update_error",
                {
                    "error": str(e),
                    "table": EXECUTION_HISTORY_TABLE,
                    "execution_id": execution_id,
                },
            )
        raise


def update_last_polled_time(execution_id: str, plan_id: str) -> None:
    """
    Update LastPolledTime for adaptive polling intervals.

    Args:
        execution_id: Execution ID
        plan_id: Plan ID
    """
    try:
        current_time = int(datetime.now(timezone.utc).timestamp())

        dynamodb.update_item(
            TableName=EXECUTION_HISTORY_TABLE,
            Key={"ExecutionId": {"S": execution_id}, "PlanId": {"S": plan_id}},
            UpdateExpression="SET LastPolledTime = :time",
            ExpressionAttributeValues={":time": {"N": str(current_time)}},
            ConditionExpression="attribute_exists(ExecutionId)",
        )

    except Exception as e:
        logger.error(
            f"Error updating last polled time: {str(e)}", exc_info=True
        )
        # Non-critical error, don't raise


def finalize_execution(
    execution_id: str,
    plan_id: str,
    waves: List[Dict[str, Any]],
    final_status: Optional[str] = None,
) -> None:
    """
    Mark execution as complete.

    Determines overall execution status based on wave statuses.
    Updates Status, EndTime, and removes from POLLING.

    Args:
        execution_id: Execution ID
        plan_id: Plan ID
        waves: Final wave records
        final_status: Optional override for final status (e.g., 'CANCELLED')
    """
    try:
        # Determine overall status
        if final_status:
            # Use provided final status (e.g., CANCELLED)
            status = final_status
        elif all(w.get("Status") in ["COMPLETED", "completed"] for w in waves):
            status = "COMPLETED"
        elif any(w.get("Status") == "FAILED" for w in waves):
            status = "FAILED"
        else:
            status = "COMPLETED_WITH_WARNINGS"

        end_time = int(datetime.now(timezone.utc).timestamp())

        # Update execution with final status
        dynamodb.update_item(
            TableName=EXECUTION_HISTORY_TABLE,
            Key={"ExecutionId": {"S": execution_id}, "PlanId": {"S": plan_id}},
            UpdateExpression="SET #status = :status, EndTime = :end_time, Waves = :waves",
            ExpressionAttributeNames={"#status": "Status"},
            ExpressionAttributeValues={
                ":status": {"S": status},
                ":end_time": {"N": str(end_time)},
                ":waves": {"L": [format_wave_for_dynamodb(w) for w in waves]},
            },
            ConditionExpression="attribute_exists(ExecutionId)",
        )

        logger.info(f"Execution {execution_id} finalized with status {status}")

    except Exception as e:
        logger.error(f"Error finalizing execution: {str(e)}", exc_info=True)
        raise


def record_poller_metrics(
    execution_id: str, execution_type: str, waves: List[Dict[str, Any]]
) -> None:
    """
    Record custom CloudWatch metrics for monitoring.

    Args:
        execution_id: Execution ID
        execution_type: DRILL or RECOVERY
        waves: Wave records
    """
    try:
        # Count servers by status
        server_statuses = {}
        for wave in waves:
            for server in wave.get("Servers", []):
                status = server.get("Status", "UNKNOWN")
                server_statuses[status] = server_statuses.get(status, 0) + 1

        # Put metrics
        cloudwatch.put_metric_data(
            Namespace="AWS-DRS-Orchestration",
            MetricData=[
                {
                    "MetricName": "ActivePollingExecutions",
                    "Value": 1,
                    "Unit": "Count",
                    "Dimensions": [
                        {"Name": "ExecutionType", "Value": execution_type}
                    ],
                },
                {
                    "MetricName": "WavesPolled",
                    "Value": len(waves),
                    "Unit": "Count",
                    "Dimensions": [
                        {"Name": "ExecutionId", "Value": execution_id}
                    ],
                },
            ],
        )

    except Exception as e:
        logger.error(f"Error recording metrics: {str(e)}", exc_info=True)
        # Non-critical error, don't raise


def format_wave_for_dynamodb(wave: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format wave record for DynamoDB.

    Args:
        wave: Wave record

    Returns:
        DynamoDB formatted wave
    """
    formatted = {"M": {}}

    for key, value in wave.items():
        if isinstance(value, str):
            formatted["M"][key] = {"S": value}
        elif isinstance(
            value, bool
        ):  # Check bool BEFORE int (bool is subclass of int)
            formatted["M"][key] = {"BOOL": value}
        elif isinstance(value, (int, float)):
            formatted["M"][key] = {"N": str(value)}
        elif isinstance(value, list):
            formatted["M"][key] = {
                "L": [format_value_for_dynamodb(v) for v in value]
            }
        elif isinstance(value, dict):
            formatted["M"][key] = format_wave_for_dynamodb(value)

    return formatted


def format_value_for_dynamodb(value: Any) -> Dict[str, Any]:
    """Format a value for DynamoDB."""
    if isinstance(value, str):
        return {"S": value}
    elif isinstance(
        value, bool
    ):  # Check bool BEFORE int (bool is subclass of int)
        return {"BOOL": value}
    elif isinstance(value, (int, float)):
        return {"N": str(value)}
    elif isinstance(value, dict):
        return format_wave_for_dynamodb(value)
    elif isinstance(value, list):
        return {"L": [format_value_for_dynamodb(v) for v in value]}
    else:
        return {"S": str(value)}
