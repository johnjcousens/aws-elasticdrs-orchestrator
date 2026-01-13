"""
Execution Poller Lambda
Polls DRS job status for a single execution.
Updates DynamoDB with wave/server status.
Handles timeouts and detects completion.

Updated: 2026-01-09 - Fixed import paths for shared security utilities
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3

# Import security utilities (mandatory - no fallback)
from shared.security_utils import (
    create_response_with_security_headers,
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
drs = boto3.client("drs")
cloudwatch = boto3.client("cloudwatch")

# Environment variables (with defaults for testing)
EXECUTION_HISTORY_TABLE = os.environ.get(
    "EXECUTION_HISTORY_TABLE", "test-execution-table"
)
TIMEOUT_THRESHOLD_SECONDS = int(
    os.environ.get("TIMEOUT_THRESHOLD_SECONDS", "31536000")
)  # 1 year (Step Functions supports up to 1 year pauses)

# Execution completion statuses
COMPLETED_STATUSES = {"COMPLETED", "FAILED", "TERMINATED", "TIMEOUT"}

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
        # Mandatory security logging
        log_security_event(
            "execution_poller_invoked",
            {
                "function_name": context.function_name,
                "request_id": context.aws_request_id,
                "event_keys": list(event.keys()) if event else [],
            },
        )

        # Mandatory input validation and sanitization
        execution_id = sanitize_string_input(event.get("executionId", ""))
        plan_id = sanitize_string_input(event.get("planId", ""))
        execution_type = sanitize_string_input(
            event.get("executionType", "DRILL")
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
                400, {"error": "Missing required parameters: executionId and planId"}
            )

        start_time = event.get("startTime")

        logger.info(
            f"Polling execution: {execution_id} (Type: {execution_type})"
        )

        # Get current execution state from DynamoDB
        execution = get_execution_from_dynamodb(execution_id, plan_id)

        if not execution:
            logger.error(f"Execution not found: {execution_id}")
            log_security_event(
                "execution_not_found",
                {"execution_id": execution_id, "plan_id": plan_id},
            )
            return create_response_with_security_headers(
                404,
                {
                    "error": "Execution not found",
                    "executionId": execution_id,
                },
            )

        # Check if execution is being cancelled
        execution_status = execution.get("status", "POLLING")
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
            return create_response_with_security_headers(
                200,
                {
                    "executionId": execution_id,
                    "status": "TIMEOUT",
                    "message": "Execution timed out",
                },
            )

        # Poll wave status from DRS
        waves = execution.get("waves", [])
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
            wave_status = wave.get("status", "")

            # For CANCELLING executions, only poll waves that are in-progress
            if is_cancelling:
                if wave_status in IN_PROGRESS_STATUSES:
                    logger.info(
                        f"Polling in-progress wave {wave.get('waveId')} (status: {wave_status})"
                    )
                    updated_wave = poll_wave_status(wave, execution_type)
                    waves_polled += 1

                    # Set endTime on wave if it just completed
                    if updated_wave.get("status") in COMPLETED_STATUSES and not updated_wave.get("endTime"):
                        updated_wave["endTime"] = int(
                            datetime.now(timezone.utc).timestamp()
                        )
                        logger.info(
                            f"Wave {wave.get('waveId')} completed, set endTime"
                        )

                    updated_waves.append(updated_wave)

                    # Check if this wave is still in progress
                    if updated_wave.get("status") not in COMPLETED_STATUSES:
                        all_active_waves_complete = False
                else:
                    # Wave already completed or cancelled - keep as-is
                    updated_waves.append(wave)
            else:
                # Normal polling - poll all waves
                updated_wave = poll_wave_status(wave, execution_type)

                # Set EndTime on wave if it just completed
                if updated_wave.get("status") in COMPLETED_STATUSES and not updated_wave.get("endTime"):
                    updated_wave["endTime"] = int(
                        datetime.now(timezone.utc).timestamp()
                    )

                updated_waves.append(updated_wave)

                # Check if wave is complete
                if updated_wave.get("status") not in COMPLETED_STATUSES:
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

                return create_response_with_security_headers(
                    200,
                    {
                        "executionId": execution_id,
                        "status": "CANCELLED",
                        "message": "Cancelled execution finalized after in-progress waves completed",
                    },
                )
            else:
                logger.info(f"All waves complete for execution {execution_id}")
                finalize_execution(execution_id, plan_id, updated_waves)

                return create_response_with_security_headers(
                    200,
                    {
                        "executionId": execution_id,
                        "status": "COMPLETED",
                        "message": "Execution completed successfully",
                    },
                )

        # Record polling metrics
        record_poller_metrics(execution_id, execution_type, updated_waves)

        return create_response_with_security_headers(
            200,
            {
                "executionId": execution_id,
                "status": execution_status,
                "WavesPolled": (
                    waves_polled if is_cancelling else len(updated_waves)
                ),
                "message": "Polling in progress",
            },
        )

    except Exception as e:
        logger.error(f"Error in Execution Poller: {str(e)}", exc_info=True)
        log_security_event(
            "execution_poller_error",
            {
                "error": str(e),
                "execution_id": event.get("executionId", "unknown"),
                "plan_id": event.get("planId", "unknown"),
            },
        )
        return create_response_with_security_headers(
            500, {"error": str(e), "message": "Failed to poll execution"}
        )


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
        validate_dynamodb_input("executionId", execution_id)
        validate_dynamodb_input("planId", plan_id)

        def get_item_call():
            return dynamodb.get_item(
                TableName=EXECUTION_HISTORY_TABLE,
                Key={"executionId": {"S": execution_id},
                    "planId": {"S": plan_id},
                },
            )

        response = safe_aws_client_call(get_item_call)

        if "Item" not in response:
            return None

        return parse_dynamodb_item(response["Item"])

    except Exception as e:
        logger.error(
            f"Error getting execution from DynamoDB: {str(e)}", exc_info=True
        )
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
        start_time = execution.get("startTime", 0)

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
        waves = execution.get("waves", [])
        final_waves = []

        for wave in waves:
            # Get final status from DRS
            job_id = wave.get("jobId")
            if job_id:
                try:
                    wave_region = wave.get("region")
                    if not wave_region:
                        logger.error(f"Wave {wave.get('waveName')} missing region field")
                        continue
                    job_status = query_drs_job_status(job_id, wave_region)
                    wave["status"] = job_status.get("status", "TIMEOUT")
                    wave["statusMessage"] = job_status.get(
                        "statusMessage", "Execution timed out"
                    )
                except Exception as e:
                    logger.error(
                        f"Error querying DRS for job {job_id}: {str(e)}"
                    )
                    wave["status"] = "TIMEOUT"
                    wave["StatusMessage"] = (
                        f"Timeout after {TIMEOUT_THRESHOLD_SECONDS}s"
                    )
            else:
                wave["status"] = "TIMEOUT"
                wave["statusMessage"] = (
                    f"Timeout after {TIMEOUT_THRESHOLD_SECONDS}s"
                )

            final_waves.append(wave)

        # Update execution with timeout status
        dynamodb.update_item(
            TableName=EXECUTION_HISTORY_TABLE,
            Key={"executionId": {"S": execution_id}, "planId": {"S": plan_id}},
            UpdateExpression="SET #status = :status, waves = :waves, endTime = :end_time",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": {"S": "TIMEOUT"},
                ":waves": {
                    "L": [format_wave_for_dynamodb(w) for w in final_waves]
                },
                ":end_time": {
                    "N": str(int(datetime.now(timezone.utc).timestamp()))
                },
            },
            ConditionExpression="attribute_exists(executionId)",
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
        job_id = wave.get("jobId")

        if not job_id:
            logger.warning(f"Wave {wave.get('waveId')} has no JobId")
            return wave

        # Query DRS for job status
        wave_region = wave.get("region")
        if not wave_region:
            logger.error(f"Wave {wave.get("waveName")} missing Region field")
            return wave
        job_status = query_drs_job_status(job_id, wave_region)

        # Get DRS job status and message
        drs_status = job_status.get("status", "UNKNOWN")
        wave["status"] = drs_status  # Set wave status to DRS job status
        wave["StatusMessage"] = job_status.get("StatusMessage", "")

        # Update server statuses from DRS participating servers
        if "ParticipatingServers" in job_status:
            wave_region = wave.get("region")
            if not wave_region:
                logger.error(f"Wave {wave.get('waveName')} missing region field for server status update")
                return wave
            updated_server_statuses = []

            for drs_server in job_status["ParticipatingServers"]:
                # Get server name from DRS source server data
                source_server_id = drs_server.get("sourceServerID", "")
                server_name = get_drs_server_name(source_server_id, wave_region)
                
                server_data = {
                    "sourceServerId": source_server_id,
                    "launchStatus": drs_server.get("launchStatus", "UNKNOWN"),
                    "serverName": server_name,  # Add server name from DRS tags
                    "hostname": "",  # Fixed: Use 'hostname' not 'hostName'
                    "launchTime": 0,
                    "instanceId": "",
                    "privateIp": "",  # Fixed: Use 'privateIp' not 'privateIpAddress'
                }

                # Set launchTime when server starts launching
                if server_data["launchStatus"] in [
                    "PENDING",
                    "IN_PROGRESS",
                    "LAUNCHED",
                ]:
                    server_data["launchTime"] = int(
                        datetime.now(timezone.utc).timestamp()
                    )

                # Get EC2 instance details if recoveryInstanceID exists
                # AWS DRS API returns PascalCase by default - transform to camelCase for internal use
                recovery_instance_id = drs_server.get("recoveryInstanceID")
                if recovery_instance_id:
                    server_data["instanceId"] = recovery_instance_id

                    # Enrich with EC2 data
                    try:
                        ec2_data = get_ec2_instance_details(
                            recovery_instance_id, wave_region
                        )
                        if ec2_data:
                            server_data["hostname"] = ec2_data.get(
                                "hostname", ""
                            )
                            server_data["privateIp"] = ec2_data.get(
                                "privateIp", ""
                            )
                    except Exception as e:
                        logger.warning(
                            f"Could not fetch EC2 details for {recovery_instance_id}: {str(e)}"
                        )

                updated_server_statuses.append(server_data)

            wave["serverStatuses"] = updated_server_statuses

        # Determine wave status based on server launch results
        server_statuses = wave.get("serverStatuses", [])

        if execution_type == "DRILL":
            if server_statuses:
                # Check if ALL servers launched successfully
                all_launched = all(
                    s.get("launchStatus") == "LAUNCHED" for s in server_statuses
                )
                # Check if ANY servers failed to launch
                any_failed = any(
                    s.get("launchStatus")
                    in ["LAUNCH_FAILED", "FAILED", "TERMINATED"]
                    for s in server_statuses
                )

                if all_launched:
                    wave["status"] = "COMPLETED"
                    logger.info(
                        f"Wave {wave.get('waveId')} completed - all servers LAUNCHED"
                    )
                elif any_failed:
                    wave["status"] = "FAILED"
                    failed_servers = [
                        s.get("sourceServerId")
                        for s in server_statuses
                        if s.get("launchStatus")
                        in ["LAUNCH_FAILED", "FAILED", "TERMINATED"]
                    ]
                    logger.warning(
                        f"Wave {wave.get('waveId')} failed - servers {failed_servers} failed to launch"
                    )
                elif drs_status in ["PENDING", "STARTED"]:
                    wave["status"] = "LAUNCHING"
                elif drs_status == "COMPLETED" and not all_launched:
                    # CRITICAL BUG FIX: DRS job completed but servers never launched
                    wave["status"] = "FAILED"
                    not_launched_servers = [
                        s.get("sourceServerId")
                        for s in server_statuses
                        if s.get("launchStatus") != "LAUNCHED"
                    ]
                    logger.error(
                        f"Wave {wave.get('waveId')} FAILED - DRS job COMPLETED but servers {not_launched_servers} never launched"
                    )
                    wave["statusMessage"] = (
                        f"DRS job completed but {len(not_launched_servers)} servers failed to launch"
                    )
                else:
                    # Fallback to DRS status if no clear success/failure
                    wave["status"] = drs_status
            else:
                # No servers yet, use DRS job status
                wave["status"] = drs_status
        else:  # RECOVERY
            # RECOVERY complete when all servers LAUNCHED + post-launch complete
            if server_statuses:
                all_launched = all(
                    s.get("launchStatus") == "LAUNCHED" for s in server_statuses
                )
                any_failed = any(
                    s.get("launchStatus")
                    in ["LAUNCH_FAILED", "FAILED", "TERMINATED"]
                    for s in server_statuses
                )
                post_launch_complete = (
                    job_status.get("PostLaunchActionsStatus") == "COMPLETED"
                )

                if all_launched and post_launch_complete:
                    wave["status"] = "COMPLETED"
                    logger.info(
                        f"Wave {wave.get('waveId')} recovery completed"
                    )
                elif any_failed:
                    wave["status"] = "FAILED"
                    logger.warning(
                        f"Wave {wave.get('waveId')} recovery failed"
                    )
                elif drs_status in ["PENDING", "STARTED"]:
                    wave["status"] = "LAUNCHING"
                elif drs_status == "COMPLETED" and not all_launched:
                    # CRITICAL BUG FIX: DRS job completed but servers never launched
                    wave["status"] = "FAILED"
                    not_launched_servers = [
                        s.get("sourceServerId")
                        for s in server_statuses
                        if s.get("launchStatus") != "LAUNCHED"
                    ]
                    logger.error(
                        f"Wave {wave.get('waveId')} RECOVERY FAILED - DRS job COMPLETED but servers {not_launched_servers} never launched"
                    )
                    wave["statusMessage"] = (
                        f"DRS job completed but {len(not_launched_servers)} servers failed to launch"
                    )
                else:
                    wave["status"] = drs_status
            else:
                wave["status"] = drs_status

        return wave

    except Exception as e:
        logger.error(f"Error polling wave status: {str(e)}", exc_info=True)
        wave["status"] = "ERROR"
        wave["StatusMessage"] = f"Polling error: {str(e)}"
        return wave


def query_drs_job_status(job_id: str, region: str) -> Dict[str, Any]:
    """
    Query DRS API for job status.

    Args:
        job_id: DRS job ID
        region: AWS region where the DRS job exists

    Returns:
        Job status information
    """
    try:
        # Create region-specific DRS client
        drs_client = boto3.client("drs", region_name=region)
        response = drs_client.describe_jobs(filters={"jobIDs": [job_id]})

        if not response.get("items"):
            logger.warning(f"No job found for ID {job_id} in region {region}")
            return {"status": "UNKNOWN", "StatusMessage": "Job not found"}

        job = response["items"][0]

        return {
            "status": job.get("status", "UNKNOWN"),
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


def get_drs_server_name(source_server_id: str, region: str) -> str:
    """
    Get DRS server name from source server details.
    
    Args:
        source_server_id: DRS source server ID
        region: AWS region
        
    Returns:
        Server name from Name tag or hostname
    """
    try:
        drs_client = boto3.client("drs", region_name=region)
        response = drs_client.describe_source_servers(
            filters={"sourceServerIDs": [source_server_id]}
        )
        
        if not response.get("items"):
            return ""
            
        server = response["items"][0]
        
        # Try Name tag first
        name_tag = server.get("tags", {}).get("Name", "")
        if name_tag:
            return name_tag
            
        # Fallback to hostname from identification hints
        hostname = (
            server.get("sourceProperties", {})
            .get("identificationHints", {})
            .get("hostname", "")
        )
        
        return hostname or ""
        
    except Exception as e:
        logger.warning(f"Could not get DRS server name for {source_server_id}: {str(e)}")
        return ""


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
            "hostname": hostname,
            "privateIp": instance.get("PrivateIpAddress", ""),  # EC2 API returns PascalCase
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
        validate_dynamodb_input("executionId", execution_id)
        validate_dynamodb_input("planId", plan_id)

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
                Key={"executionId": {"S": execution_id.strip()},
                    "planId": {"S": plan_id.strip()},
                },
                UpdateExpression="SET waves = :waves",
                ExpressionAttributeValues={
                    ":waves": {
                        "L": [format_wave_for_dynamodb(w) for w in waves]
                    }
                },
                ConditionExpression="attribute_exists(executionId) AND attribute_exists(planId)",
            )

        safe_aws_client_call(update_call)

        logger.info(f"Updated {len(waves)} waves for execution {execution_id}")

    except Exception as e:
        logger.error(
            f"Error updating execution waves: {str(e)}", exc_info=True
        )
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
            Key={"executionId": {"S": execution_id}, "planId": {"S": plan_id}},
            UpdateExpression="SET lastPolledTime = :time",
            ExpressionAttributeValues={":time": {"N": str(current_time)}},
            ConditionExpression="attribute_exists(executionId)",
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
        elif all(w.get("status") == "COMPLETED" for w in waves):
            status = "COMPLETED"
        elif any(w.get("status") == "FAILED" for w in waves):
            status = "FAILED"
        else:
            status = "COMPLETED_WITH_WARNINGS"

        end_time = int(datetime.now(timezone.utc).timestamp())

        # Update execution with final status
        dynamodb.update_item(
            TableName=EXECUTION_HISTORY_TABLE,
            Key={"executionId": {"S": execution_id}, "planId": {"S": plan_id}},
            UpdateExpression="SET #status = :status, endTime = :end_time, waves = :waves",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": {"S": status},
                ":end_time": {"N": str(end_time)},
                ":waves": {"L": [format_wave_for_dynamodb(w) for w in waves]},
            },
            ConditionExpression="attribute_exists(executionId)",
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
            for server in wave.get("serverStatuses", []):
                status = server.get("launchStatus", "UNKNOWN")
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
