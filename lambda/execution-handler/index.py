"""
Execution Handler - AWS Elastic DR (DRS) Execution Operations

Central Lambda function for DRS execution lifecycle management including
recovery initiation, pause/resume, cancellation, and status polling.

HANDLER ARCHITECTURE:
The platform uses four specialized handlers with distinct responsibilities:

    +-------------------------------------------------------------------------+
    |                        API Gateway + Cognito                            |
    |                         (User Authentication)                           |
    +-------------------------------------------------------------------------+
                |                    |                    |
                v                    v                    v
    +---------------------+ +---------------------+ +---------------------+
    | data-management     | | execution-handler   | |  query-handler      |
    |     handler         | |    (this Lambda)    | |                     |
    +---------------------+ +---------------------+ +---------------------+
    | CRUD Operations:    | | Recovery Actions:   | | Read Operations:    |
    | - Protection Grps   | | - Start recovery    | | - List executions   |
    | - Recovery Plans    | | - Cancel exec       | | - Poll DRS jobs     |
    | - Tag sync          | | - Terminate inst    | | - Server status     |
    | - Launch configs    | | - Apply configs     | | - Dashboard data    |
    +---------------------+ +---------------------+ +---------------------+
                                  |                    |
                                  |   Direct Invoke    |
                                  |   (No API Gateway) |
                                  v                    v
    +-------------------------------------------------------------------------+
    |              dr-orchestration-stepfunction                              |
    |                                                                         |
    |  Step Functions invokes this Lambda for wave recovery operations        |
    +-------------------------------------------------------------------------+
                                       |
                                       v
    +-------------------------------------------------------------------------+
    |                    AWS DRS (Target Account)                             |
    |              Cross-account via DRSOrchestrationRole                     |
    +-------------------------------------------------------------------------+

INVOCATION PATTERNS:
1. API Gateway (HTTP requests from frontend/CLI):
   - POST /executions - Start recovery plan execution
   - GET /executions - List all executions
   - GET /executions/{id} - Get execution details
   - POST /executions/{id}/cancel - Cancel running execution
   - POST /executions/{id}/pause - Pause at next wave boundary
   - POST /executions/{id}/resume - Resume paused execution
   - POST /executions/{id}/terminate - Terminate recovery instances

2. Direct Lambda Invocation (Step Functions orchestration):
   - action="start_wave_recovery" - Initiate DRS StartRecovery for wave
   - action="apply_launch_configs" - Apply Protection Group configs to DRS
   - action="poll_wave_status" - Check DRS job and instance status

3. EventBridge Scheduled (background polling):
   - operation="find" - Find active executions needing status updates
   - operation="poll" - Poll DRS job status for specific execution

DYNAMODB DATA FLOW:
This handler reads/writes to 3 DynamoDB tables:

    +-------------------------+     +-------------------------+
    |   protection-groups     |     |     recovery-plans      |
    +-------------------------+     +-------------------------+
    | PK: groupId             |     | PK: planId              |
    | - launchConfig{}        |     | - waves[]               |
    | - servers[] (per-srv)   |     | - planName              |
    | - sourceServerIds[]     |     +-------------------------+
    +-------------------------+               |
              |                               |
              | Read configs at wave start    | Read plan at execution start
              v                               v
    +-------------------------------------------------------------------+
    |                      execution-history                            |
    +-------------------------------------------------------------------+
    | PK: executionId                                                   |
    | SK: planId                                                        |
    |                                                                   |
    | - status: RUNNING | PAUSED | COMPLETED | FAILED | CANCELLED       |
    | - currentWave, waveStatuses[], serverExecutions[]                 |
    | - taskToken: Step Functions callback for pause/resume             |
    +-------------------------------------------------------------------+

EXECUTION LIFECYCLE:
1. Start: Validate plan, check conflicts, create execution record, start Step Functions
2. Wave Start: Apply launch configs to DRS, call StartRecovery API
3. Polling: Monitor DRS job status, update execution record
4. Pause: Store taskToken, update status to PAUSED, send SNS notification
5. Resume: Retrieve taskToken, call SendTaskSuccess, continue next wave
6. Complete: Update final status, record recovery instance details

SHARED UTILITIES (lambda/shared/):
    +-------------------------------+--------------------------------------------+
    | Module                        | Purpose                                    |
    +-------------------------------+--------------------------------------------+
    | config_merge.py               | Merge group defaults with per-server       |
    | conflict_detection.py         | Check server conflicts across executions   |
    | cross_account.py              | create_drs_client() with role assumption   |
    | drs_limits.py                 | Validate DRS service limits and quotas     |
    | drs_utils.py                  | enrich_server_data() for EC2 details       |
    | execution_utils.py            | can_terminate_execution() helper           |
    | response_utils.py             | API Gateway response formatting            |
    +-------------------------------+--------------------------------------------+
"""

import json
import os
import time
import uuid
from typing import Dict, List

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

# Import shared utilities
from shared.config_merge import get_effective_launch_config
from shared.conflict_detection import (
    check_server_conflicts,
    get_active_executions_for_plan,
    query_drs_servers_by_tags,
)
from shared.cross_account import (
    create_drs_client,
    determine_target_account_context,
)
from shared.drs_limits import (
    DRS_LIMITS,
    validate_concurrent_jobs,
    validate_server_replication_states,
    validate_servers_in_all_jobs,
    validate_wave_sizes,
)
from shared.execution_utils import can_terminate_execution
from shared.response_utils import DecimalEncoder, response

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client("lambda")
stepfunctions = boto3.client("stepfunctions")

# Environment variables
PROTECTION_GROUPS_TABLE = os.environ.get("PROTECTION_GROUPS_TABLE")
RECOVERY_PLANS_TABLE = os.environ.get("RECOVERY_PLANS_TABLE")
EXECUTION_HISTORY_TABLE = os.environ.get("EXECUTION_HISTORY_TABLE")

# DynamoDB tables (conditional initialization)
protection_groups_table = dynamodb.Table(PROTECTION_GROUPS_TABLE) if PROTECTION_GROUPS_TABLE else None
recovery_plans_table = dynamodb.Table(RECOVERY_PLANS_TABLE) if RECOVERY_PLANS_TABLE else None
execution_history_table = dynamodb.Table(EXECUTION_HISTORY_TABLE) if EXECUTION_HISTORY_TABLE else None


def analyze_execution_outcome(waves: List[Dict]) -> Dict:
    """
    Analyze wave and server outcomes to determine execution status.

    Returns a dict with:
    - status: COMPLETED, FAILED, PARTIAL, or CANCELLED
    - summary: Human-readable summary of outcomes
    - details: Structured breakdown of successes/failures

    PARTIAL status is used when:
    - Some waves completed successfully but others failed
    - Some servers launched but others failed within a wave
    - Execution was cancelled but some waves/servers had already completed
    """
    if not waves:
        return {
            "status": "FAILED",
            "summary": "No waves executed",
            "details": {"wavesCompleted": 0, "wavesFailed": 0, "wavesCancelled": 0},
        }

    # Analyze wave outcomes
    waves_completed = []
    waves_failed = []
    waves_cancelled = []
    waves_pending = []

    # Analyze server outcomes across all waves
    total_servers = 0
    servers_launched = 0
    servers_failed = 0
    servers_cancelled = 0
    servers_pending = 0

    for i, wave in enumerate(waves):
        wave_name = wave.get("waveName", f"Wave {i + 1}")
        wave_status = wave.get("status", "").upper()
        server_statuses = wave.get("serverStatuses", [])

        # Count servers in this wave
        wave_launched = 0
        wave_failed = 0
        wave_cancelled = 0
        wave_pending = 0

        for server in server_statuses:
            total_servers += 1
            launch_status = server.get("launchStatus", "").upper()

            if launch_status == "LAUNCHED":
                servers_launched += 1
                wave_launched += 1
            elif launch_status == "FAILED":
                servers_failed += 1
                wave_failed += 1
            elif launch_status in ["CANCELLED", "TERMINATED"]:
                servers_cancelled += 1
                wave_cancelled += 1
            else:
                servers_pending += 1
                wave_pending += 1

        # Categorize wave
        wave_info = {
            "name": wave_name,
            "serversLaunched": wave_launched,
            "serversFailed": wave_failed,
            "serversCancelled": wave_cancelled,
        }

        if wave_status == "COMPLETED":
            waves_completed.append(wave_info)
        elif wave_status == "FAILED":
            waves_failed.append(wave_info)
        elif wave_status in ["CANCELLED", "TERMINATED"]:
            waves_cancelled.append(wave_info)
        else:
            waves_pending.append(wave_info)

    # Determine overall status
    total_waves = len(waves)
    completed_count = len(waves_completed)
    failed_count = len(waves_failed)
    cancelled_count = len(waves_cancelled)

    # Build summary message
    summary_parts = []

    if servers_launched > 0:
        summary_parts.append(f"{servers_launched} server(s) launched successfully")
    if servers_failed > 0:
        summary_parts.append(f"{servers_failed} server(s) failed")
    if servers_cancelled > 0:
        summary_parts.append(f"{servers_cancelled} server(s) cancelled")

    # Determine status
    if completed_count == total_waves and failed_count == 0 and cancelled_count == 0:
        # All waves completed successfully
        status = "COMPLETED"
        summary = f"All {total_waves} wave(s) completed successfully. {servers_launched} server(s) launched."
    elif failed_count == total_waves or (failed_count > 0 and completed_count == 0 and servers_launched == 0):
        # All waves failed or no successes at all
        status = "FAILED"
        summary = f"Execution failed. {failed_count} wave(s) failed. {servers_failed} server(s) failed to launch."
    elif cancelled_count == total_waves or (
        cancelled_count > 0 and completed_count == 0 and failed_count == 0 and servers_launched == 0
    ):
        # All waves cancelled with no successes
        status = "CANCELLED"
        summary = f"Execution cancelled. {cancelled_count} wave(s) cancelled."
    else:
        # Mixed results - PARTIAL status
        status = "PARTIAL"
        summary = "; ".join(summary_parts) if summary_parts else "Partial execution"

        # Add wave breakdown to summary
        wave_summary_parts = []
        if completed_count > 0:
            wave_summary_parts.append(f"{completed_count} wave(s) completed")
        if failed_count > 0:
            wave_summary_parts.append(f"{failed_count} wave(s) failed")
        if cancelled_count > 0:
            wave_summary_parts.append(f"{cancelled_count} wave(s) cancelled")

        if wave_summary_parts:
            summary = f"{summary}. Waves: {', '.join(wave_summary_parts)}."

    return {
        "status": status,
        "summary": summary,
        "details": {
            "totalWaves": total_waves,
            "wavesCompleted": completed_count,
            "wavesFailed": failed_count,
            "wavesCancelled": cancelled_count,
            "wavesPending": len(waves_pending),
            "totalServers": total_servers,
            "serversLaunched": servers_launched,
            "serversFailed": servers_failed,
            "serversCancelled": servers_cancelled,
            "serversPending": servers_pending,
            "completedWaves": waves_completed,
            "failedWaves": waves_failed,
            "cancelledWaves": waves_cancelled,
        },
    }


# Helper functions for table access
def get_protection_groups_table():
    """Get Protection Groups table reference"""
    return protection_groups_table


def get_execution_history_table():
    """Get Execution History table reference"""
    return execution_history_table


def get_account_context(state: Dict) -> Dict:
    """
    Extract account context from state, handling both camelCase and snake_case.

    Supports two input formats:
    - Initial execution: camelCase (accountContext) from Step Functions input
    - Resume after pause: snake_case (account_context) from SendTaskSuccess

    Returns:
        Dict containing accountId, assumeRoleName, and isCurrentAccount flags
    """
    return state.get("accountContext") or state.get("account_context", {})


def get_cognito_user_from_event(event: Dict) -> Dict:
    """Extract Cognito user info from API Gateway event"""
    try:
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})
        claims = authorizer.get("claims", {})

        return {
            "email": claims.get("email", "unknown"),
            "userId": claims.get("sub", "unknown"),
            "username": claims.get("cognito:username", "unknown"),
        }
    except Exception as e:
        print(f"Error extracting Cognito user: {e}")
        return {"email": "unknown", "userId": "unknown", "username": "unknown"}


def execute_recovery_plan(body: Dict, event: Dict = None) -> Dict:
    """
    Start DRS recovery plan execution (API Gateway entry point).

    ASYNC PATTERN: Returns 202 Accepted immediately, executes in background.
    Prevents API Gateway 30s timeout for long-running operations.

    WORKFLOW:
    1. Validate request (planId, executionType, initiatedBy)
    2. Validate DRS service limits (wave sizes, concurrent jobs, replication)
    3. Check server conflicts (no overlapping executions or active DRS jobs)
    4. Create execution record in DynamoDB (status=PENDING)
    5. Self-invoke Lambda async (worker=true) for background processing
    6. Return 202 with executionId and status URL

    REQUIRED FIELDS:
        planId: Recovery plan UUID
        executionType: "DRILL" or "RECOVERY"
        initiatedBy: User/system identifier

    OPTIONAL FIELDS:
        accountContext: {accountId, assumeRoleName} for cross-account

    DRS LIMITS VALIDATED:
        - Wave size: max 100 servers per wave
        - Concurrent jobs: max 20 active DRS jobs
        - Servers in jobs: max 500 servers across all jobs
        - Replication health: all servers must be HEALTHY

    API INVOCATION:
        POST /executions
        {
            "planId": "uuid",
            "executionType": "DRILL",
            "initiatedBy": "user@example.com"
        }

    RETURNS:
        202 Accepted
        {
            "executionId": "uuid",
            "status": "PENDING",
            "message": "Execution started - check status with GET /executions/{id}",
            "statusUrl": "/executions/uuid"
        }

    ERROR RESPONSES:
        400: Missing/invalid fields, wave size exceeded, unhealthy replication
        409: Server conflicts (overlapping executions or active DRS jobs)
        429: DRS service limits exceeded (concurrent jobs, servers in jobs)
        500: Internal error
    """
    try:
        # Extract Cognito user if event provided
        cognito_user = get_cognito_user_from_event(event) if event else {"email": "system", "userId": "system"}

        # Validate required fields with helpful messages
        if "planId" not in body:
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "planId is required - specify which Recovery Plan to execute",
                    "field": "planId",
                },
            )

        if "executionType" not in body:
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "executionType is required - must be DRILL or RECOVERY",
                    "field": "executionType",
                    "allowedValues": ["DRILL", "RECOVERY"],
                },
            )

        if "initiatedBy" not in body:
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "initiatedBy is required - identify who/what started this execution",
                    "field": "initiatedBy",
                },
            )

        plan_id = body["planId"]
        execution_type = body["executionType"].upper() if body["executionType"] else ""

        # Validate execution type
        if execution_type not in ["DRILL", "RECOVERY"]:
            return response(
                400,
                {
                    "error": "INVALID_EXECUTION_TYPE",
                    "message": f'executionType must be DRILL or RECOVERY, got: {body["executionType"]}',
                    "field": "executionType",
                    "providedValue": body["executionType"],
                    "allowedValues": ["DRILL", "RECOVERY"],
                },
            )

        # Get Recovery Plan
        plan_result = recovery_plans_table.get_item(Key={"planId": plan_id})
        if "Item" not in plan_result:
            return response(
                404,
                {
                    "error": "RECOVERY_PLAN_NOT_FOUND",
                    "message": f"Recovery Plan with ID {plan_id} not found",
                    "planId": plan_id,
                },
            )

        plan = plan_result["Item"]

        # Validate plan has waves
        if not plan.get("waves"):
            return response(
                400,
                {
                    "error": "PLAN_HAS_NO_WAVES",
                    "message": f'Recovery Plan "{plan.get("planName", plan_id)}" has no waves configured - add at least one wave before executing',  # noqa: E501
                    "planId": plan_id,
                    "planName": plan.get("planName"),
                },
            )

        # Check for server conflicts with other running executions OR active DRS jobs
        account_context = body.get("accountContext") or body.get("AccountContext")
        server_conflicts = check_server_conflicts(plan, account_context)
        if server_conflicts:
            # Separate execution conflicts from DRS job conflicts
            execution_conflicts = [c for c in server_conflicts if c.get("conflictSource") == "execution"]
            drs_job_conflicts = [c for c in server_conflicts if c.get("conflictSource") == "drs_job"]

            # Group execution conflicts by execution
            conflict_executions = {}
            for conflict in execution_conflicts:
                exec_id = conflict.get("conflictingExecutionId")
                if exec_id and exec_id not in conflict_executions:
                    conflict_executions[exec_id] = {
                        "executionId": exec_id,
                        "planId": conflict.get("conflictingPlanId"),
                        "servers": [],
                    }
                if exec_id:
                    conflict_executions[exec_id]["servers"].append(conflict["serverId"])

            # Group DRS job conflicts by job
            conflict_drs_jobs = {}
            for conflict in drs_job_conflicts:
                job_id = conflict.get("conflictingJobId")
                if job_id and job_id not in conflict_drs_jobs:
                    conflict_drs_jobs[job_id] = {
                        "jobId": job_id,
                        "jobStatus": conflict.get("conflictingJobStatus"),
                        "servers": [],
                    }
                if job_id:
                    conflict_drs_jobs[job_id]["servers"].append(conflict["serverId"])

            # Build appropriate error message
            if drs_job_conflicts and not execution_conflicts:
                message = f"{len(drs_job_conflicts)} server(s) are being processed by active DRS jobs"
            elif execution_conflicts and not drs_job_conflicts:
                message = f"{len(execution_conflicts)} server(s) are already in active executions"
            else:
                message = f"{len(server_conflicts)} server(s) are in use (executions: {len(execution_conflicts)}, DRS jobs: {len(drs_job_conflicts)})"  # noqa: E501

            return response(
                409,
                {
                    "error": "SERVER_CONFLICT",
                    "message": message,
                    "conflicts": server_conflicts,
                    "conflictingExecutions": list(conflict_executions.values()),
                    "conflictingDrsJobs": list(conflict_drs_jobs.values()),
                },
            )

        # Cannot execute plan that already has an active execution (excluding CANCELLING)
        # ATOMIC CHECK: Query Step Functions directly to prevent race conditions
        active_executions = get_active_executions_for_plan(plan_id)
        truly_active_executions = [e for e in active_executions if e.get("status", "").upper() != "CANCELLING"]
        if truly_active_executions:
            exec_ids = [e.get("executionId") for e in truly_active_executions]
            return response(
                409,
                {
                    "error": "PLAN_ALREADY_EXECUTING",
                    "message": "This Recovery Plan already has an execution in progress",
                    "activeExecutions": exec_ids,
                    "planId": plan_id,
                },
            )

        # CRITICAL: Add execution lock to prevent race conditions
        # Create a lock record in DynamoDB before proceeding
        lock_key = f"execution-lock-{plan_id}"
        lock_timestamp = int(time.time())
        try:
            # Try to acquire lock with conditional write
            # This will fail if another request already acquired the lock
            dynamodb_client = boto3.client("dynamodb")
            dynamodb_client.put_item(
                TableName=EXECUTION_HISTORY_TABLE,
                Item={
                    "executionId": {"S": lock_key},
                    "planId": {"S": plan_id},
                    "status": {"S": "LOCK"},
                    "startTime": {"N": str(lock_timestamp)},
                    "lockExpiry": {"N": str(lock_timestamp + 30)},  # 30 second TTL
                },
                ConditionExpression="attribute_not_exists(executionId) OR lockExpiry < :now",
                ExpressionAttributeValues={":now": {"N": str(lock_timestamp)}},
            )
            print(f"✅ Acquired execution lock for plan {plan_id}")
        except dynamodb_client.exceptions.ConditionalCheckFailedException:
            print(f"❌ Failed to acquire lock - another execution is starting for plan {plan_id}")
            return response(
                409,
                {
                    "error": "PLAN_EXECUTION_CONFLICT",
                    "message": "Another execution of this Recovery Plan is in progress. Please wait and try again.",  # noqa: E501
                    "planId": plan_id,
                },
            )

        # DRS SERVICE LIMITS VALIDATION

        # Get region from first wave's protection group
        first_wave = plan.get("waves", [{}])[0]
        pg_id = first_wave.get("protectionGroupId")
        if pg_id:
            pg_result = protection_groups_table.get_item(Key={"groupId": pg_id})
            region = pg_result.get("Item", {}).get("region", "us-east-1")
        else:
            region = "us-east-1"  # Default fallback

        # Collect all server IDs from all waves
        all_server_ids = []
        for wave in plan.get("waves", []):
            all_server_ids.extend(wave.get("serverIds", []))
        total_servers_in_plan = len(all_server_ids)

        # 1. Validate wave sizes (max 100 servers per wave)
        wave_size_errors = validate_wave_sizes(plan)
        if wave_size_errors:
            return response(
                400,
                {
                    "error": "WAVE_SIZE_LIMIT_EXCEEDED",
                    "message": f'{len(wave_size_errors)} wave(s) exceed the DRS limit of {DRS_LIMITS["MAX_SERVERS_PER_JOB"]} servers per job',  # noqa: E501
                    "errors": wave_size_errors,
                    "limit": DRS_LIMITS["MAX_SERVERS_PER_JOB"],
                },
            )

        # 2. Validate concurrent jobs (max 20)
        concurrent_jobs_result = validate_concurrent_jobs(region)
        if not concurrent_jobs_result.get("valid"):
            return response(
                429,
                {
                    "error": "CONCURRENT_JOBS_LIMIT_EXCEEDED",
                    "message": concurrent_jobs_result.get("message"),
                    "currentJobs": concurrent_jobs_result.get("currentJobs"),
                    "maxJobs": concurrent_jobs_result.get("maxJobs"),
                    "activeJobs": concurrent_jobs_result.get("activeJobs", []),
                },
            )

        # 3. Validate servers in all jobs (max 500)
        servers_in_jobs_result = validate_servers_in_all_jobs(region, total_servers_in_plan)
        if not servers_in_jobs_result.get("valid"):
            return response(
                429,
                {
                    "error": "SERVERS_IN_JOBS_LIMIT_EXCEEDED",
                    "message": servers_in_jobs_result.get("message"),
                    "currentServersInJobs": servers_in_jobs_result.get("currentServersInJobs"),
                    "newServerCount": servers_in_jobs_result.get("newServerCount"),
                    "totalAfterNew": servers_in_jobs_result.get("totalAfterNew"),
                    "maxServers": servers_in_jobs_result.get("maxServers"),
                },
            )

        # 4. Validate server replication states
        replication_result = validate_server_replication_states(region, all_server_ids)
        if not replication_result.get("valid"):
            return response(
                400,
                {
                    "error": "UNHEALTHY_SERVER_REPLICATION",
                    "message": replication_result.get("message"),
                    "unhealthyServers": replication_result.get("unhealthyServers"),
                    "healthyCount": replication_result.get("healthyCount"),
                    "unhealthyCount": replication_result.get("unhealthyCount"),
                },
            )

        print(f"✅ DRS service limits validation passed for plan {plan_id}")

        # Generate execution ID
        execution_id = str(uuid.uuid4())
        timestamp = int(time.time())

        print(f"Creating async execution {execution_id} for plan {plan_id}")

        # Create initial execution history record with PENDING status
        account_context = body.get("accountContext") or body.get("AccountContext")
        if not account_context:
            # Derive from plan if not provided in request
            account_context = determine_target_account_context(plan)

        history_item = {
            "executionId": execution_id,
            "planId": plan_id,
            "planName": plan.get("planName", "Unknown"),
            "executionType": execution_type,
            "status": "PENDING",
            "startTime": timestamp,
            "initiatedBy": body["initiatedBy"],
            "waves": [],
            "totalWaves": len(plan.get("waves", [])),
            "accountContext": account_context,
            # Store accountId at top level for efficient filtering
            "accountId": account_context.get("accountId") if account_context else None,
        }

        # Store execution history immediately
        execution_history_table.put_item(Item=history_item)

        # Release the execution lock now that the execution record exists
        try:
            dynamodb_client.delete_item(
                TableName=EXECUTION_HISTORY_TABLE,
                Key={
                    "executionId": {"S": lock_key},
                    "planId": {"S": plan_id},
                },
            )
            print(f"✅ Released execution lock for plan {plan_id}")
        except Exception as lock_error:
            print(f"⚠️ Failed to release lock (non-critical): {lock_error}")

        # Invoke this same Lambda asynchronously to do the actual work
        current_function_name = os.environ["AWS_LAMBDA_FUNCTION_NAME"]

        # Prepare payload for async worker
        worker_payload = {
            "worker": True,
            "executionId": execution_id,
            "planId": plan_id,
            "executionType": execution_type,
            "isDrill": execution_type == "DRILL",
            "plan": plan,
            "cognitoUser": cognito_user,
        }

        # Invoke async (Event invocation type = fire and forget)
        try:
            invoke_response = lambda_client.invoke(
                FunctionName=current_function_name,
                InvocationType="Event",
                Payload=json.dumps(worker_payload, cls=DecimalEncoder),
            )
            status_code = invoke_response.get("StatusCode", 0)
            if status_code != 202:
                raise Exception(f"Async invocation returned unexpected status: {status_code}")
            print(f"Async worker invoked for execution {execution_id}, StatusCode: {status_code}")
        except Exception as invoke_error:
            print(f"ERROR: Failed to invoke async worker: {str(invoke_error)}")
            execution_history_table.update_item(
                Key={"executionId": execution_id, "planId": plan_id},
                UpdateExpression="SET #status = :status, endTime = :end_time, errorMessage = :error",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "FAILED",
                    ":end_time": timestamp,
                    ":error": f"Failed to start worker: {str(invoke_error)}",
                },
            )
            return response(
                500,
                {
                    "error": f"Failed to start execution worker: {str(invoke_error)}",
                    "executionId": execution_id,
                },
            )

        # Return immediately with 202 Accepted
        return response(
            202,
            {
                "executionId": execution_id,
                "status": "PENDING",
                "message": "Execution started - check status with GET /executions/{id}",
                "statusUrl": f"/executions/{execution_id}",
            },
        )

    except Exception as e:
        print(f"Error starting execution: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def execute_with_step_functions(
    execution_id: str,
    plan_id: str,
    plan: Dict,
    is_drill: bool,
    state_machine_arn: str,
    resume_from_wave: int = None,
) -> None:
    """
    Execute recovery plan using Step Functions.

    Args:
        resume_from_wave: If set, this is a resumed execution starting from this wave index
    """
    try:
        if resume_from_wave is not None:
            print(f"RESUMING Step Functions execution for {execution_id} from wave {resume_from_wave}")
        else:
            print(f"Starting NEW Step Functions execution for {execution_id}")

        # Determine target account context for multi-account hub and spoke architecture
        account_context = determine_target_account_context(plan)

        # Prepare Step Functions input
        sfn_input = {
            "Execution": {"Id": execution_id},
            "Plan": {
                "planId": plan_id,
                "planName": plan.get("planName", "Unknown"),
                "waves": plan.get("waves", []),
            },
            "isDrill": is_drill,
            "resumeFromWave": resume_from_wave,
            "accountContext": account_context,
        }

        # For resumed executions, use a unique name suffix to avoid conflicts
        sfn_name = execution_id if resume_from_wave is None else f"{execution_id}-resume-{resume_from_wave}"

        # Start Step Functions execution
        sfn_response = stepfunctions.start_execution(
            stateMachineArn=state_machine_arn,
            name=sfn_name,
            input=json.dumps(sfn_input, cls=DecimalEncoder),
        )

        print(f"Step Functions execution started: {sfn_response['executionArn']}")

        # Update DynamoDB with Step Functions execution ARN
        execution_history_table.update_item(
            Key={"executionId": execution_id, "planId": plan_id},
            UpdateExpression="SET stateMachineArn = :arn, #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":arn": sfn_response["executionArn"],
                ":status": "RUNNING",
            },
        )

        print("✅ Step Functions execution initiated successfully")

    except Exception as e:
        print(f"❌ Error starting Step Functions execution: {e}")
        import traceback

        traceback.print_exc()

        # Update execution as failed
        try:
            execution_history_table.update_item(
                Key={"executionId": execution_id, "planId": plan_id},
                UpdateExpression="SET #status = :status, errorMessage = :error",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "FAILED",
                    ":error": str(e),
                },
            )
        except Exception as update_error:
            print(f"Error updating execution failure: {update_error}")


# ============================================================================
# Wave Execution Functions (Batch 4)
# ============================================================================


def check_existing_recovery_instances(plan_id: str) -> Dict:
    """Check if servers in this plan have existing recovery instances from completed executions.

    Returns info about any recovery instances that haven't been terminated yet.
    Used by frontend to prompt user before starting a new drill.
    """
    try:
        # Get the recovery plan
        plan_result = recovery_plans_table.get_item(Key={"planId": plan_id})
        if "Item" not in plan_result:
            return response(
                404,
                {
                    "error": "RECOVERY_PLAN_NOT_FOUND",
                    "message": f"Recovery Plan with ID {plan_id} not found",
                    "planId": plan_id,
                },
            )

        plan = plan_result["Item"]

        # Collect all server IDs from all waves by resolving protection groups
        all_server_ids = set()
        region = "us-east-1"

        for wave in plan.get("waves", []):
            pg_id = wave.get("protectionGroupId")
            if not pg_id:
                continue

            pg_result = protection_groups_table.get_item(Key={"groupId": pg_id})
            pg = pg_result.get("Item", {})
            if not pg:
                continue

            # Get region from protection group
            pg_region = pg.get("region", "us-east-1")
            if pg_region:
                region = pg_region

            # Check for explicit server IDs first
            explicit_servers = pg.get("sourceServerIds", [])
            if explicit_servers:
                print(f"PG {pg_id} has explicit servers: {explicit_servers}")
                for server_id in explicit_servers:
                    all_server_ids.add(server_id)
            else:
                # Resolve servers from tags using EC2 instance tags (not DRS tags)
                selection_tags = pg.get("serverSelectionTags", {})
                print(f"PG {pg_id} has selection tags: {selection_tags}")
                if selection_tags:
                    try:
                        # Extract account context from Protection Group
                        account_context = None
                        if pg.get("accountId"):
                            account_context = {
                                "accountId": pg.get("accountId"),
                                "assumeRoleName": pg.get("assumeRoleName"),
                                "externalId": pg.get("externalId"),
                            }
                        resolved = query_drs_servers_by_tags(pg_region, selection_tags, account_context)
                        print(f"Resolved {len(resolved)} servers from tags")
                        for server in resolved:
                            server_id = server.get("sourceServerID")
                            if server_id:
                                all_server_ids.add(server_id)
                                print(f"Added server {server_id} to check list")
                    except Exception as e:
                        print(f"Error resolving tags for PG {pg_id}: {e}")

        print(f"Total servers to check for recovery instances: {len(all_server_ids)}: {all_server_ids}")

        if not all_server_ids:
            return response(
                200,
                {
                    "hasExistingInstances": False,
                    "existingInstances": [],
                    "planId": plan_id,
                },
            )

        # Query DRS for recovery instances
        drs_client = boto3.client("drs", region_name=region)

        existing_instances = []
        try:
            # Get all recovery instances in the region
            paginator = drs_client.get_paginator("describe_recovery_instances")
            ri_count = 0
            for page in paginator.paginate():
                for ri in page.get("items", []):
                    ri_count += 1
                    source_server_id = ri.get("sourceServerID")
                    ec2_state = ri.get("ec2InstanceState")
                    print(
                        f"Recovery instance: source={source_server_id}, state={ec2_state}, in_list={source_server_id in all_server_ids}"  # noqa: E501
                    )
                    if source_server_id in all_server_ids:
                        ec2_instance_id = ri.get("ec2InstanceID")
                        recovery_instance_id = ri.get("recoveryInstanceID")

                        # Find which execution created this instance
                        source_execution = None
                        source_plan_name = None

                        # Search execution history for this recovery instance
                        try:
                            # Scan recent executions that have Waves data
                            exec_scan = execution_history_table.scan(
                                FilterExpression="attribute_exists(Waves)",
                                Limit=100,
                            )

                            # Sort by StartTime descending to find most recent match
                            exec_items = sorted(
                                exec_scan.get("Items", []),
                                key=lambda x: x.get("startTime", 0),
                                reverse=True,
                            )

                            for exec_item in exec_items:
                                exec_waves = exec_item.get("waves", [])
                                found = False
                                for wave in exec_waves:
                                    # Check ServerStatuses array
                                    for server in wave.get("serverStatuses", []):
                                        # Match by source server ID
                                        if server.get("sourceServerId") == source_server_id:
                                            source_execution = exec_item.get("executionId")
                                            # Get plan name
                                            exec_plan_id = exec_item.get("planId")
                                            if exec_plan_id:
                                                plan_lookup = recovery_plans_table.get_item(
                                                    Key={"planId": exec_plan_id}
                                                )
                                                source_plan_name = plan_lookup.get("Item", {}).get(
                                                    "planName",
                                                    exec_plan_id,
                                                )
                                            found = True
                                            break
                                    if found:
                                        break
                                if found:
                                    break
                        except Exception as e:
                            print(f"Error looking up execution for recovery instance: {e}")

                        existing_instances.append(
                            {
                                "sourceServerId": source_server_id,
                                "recoveryInstanceId": recovery_instance_id,
                                "ec2InstanceId": ec2_instance_id,
                                "ec2InstanceState": ri.get("ec2InstanceState"),
                                "sourceExecutionId": source_execution,
                                "sourcePlanName": source_plan_name,
                                "region": region,
                            }
                        )
        except Exception as e:
            print(f"Error querying DRS recovery instances: {e}")

        # Enrich with EC2 instance details (Name tag, IP, launch time)
        if existing_instances:
            try:
                ec2_client = boto3.client("ec2", region_name=region)
                ec2_ids = [inst["ec2InstanceId"] for inst in existing_instances if inst.get("ec2InstanceId")]
                if ec2_ids:
                    ec2_response = ec2_client.describe_instances(InstanceIds=ec2_ids)
                    ec2_details = {}
                    for reservation in ec2_response.get("Reservations", []):
                        for instance in reservation.get("Instances", []):
                            inst_id = instance.get("instanceId")
                            name_tag = next(
                                (t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"),
                                None,
                            )
                            ec2_details[inst_id] = {
                                "name": name_tag,
                                "privateIp": instance.get("PrivateIpAddress"),
                                "publicIp": instance.get("PublicIpAddress"),
                                "instanceType": instance.get("InstanceType"),
                                "launchTime": (
                                    instance.get("LaunchTime").isoformat() if instance.get("LaunchTime") else None
                                ),
                            }
                    # Merge EC2 details into existing_instances
                    for inst in existing_instances:
                        ec2_id = inst.get("ec2InstanceId")
                        if ec2_id and ec2_id in ec2_details:
                            inst.update(ec2_details[ec2_id])
            except Exception as e:
                print(f"Error fetching EC2 details: {e}")

        return response(
            200,
            {
                "hasExistingInstances": len(existing_instances) > 0,
                "existingInstances": existing_instances,
                "instanceCount": len(existing_instances),
                "planId": plan_id,
            },
        )

    except Exception as e:
        print(f"Error checking existing recovery instances for plan {plan_id}: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            {
                "error": "CHECK_FAILED",
                "message": f"Failed to check existing recovery instances: {str(e)}",
                "planId": plan_id,
            },
        )


def initiate_wave(
    wave: Dict,
    protection_group_id: str,
    execution_id: str,
    is_drill: bool,
    execution_type: str = "DRILL",
    plan_name: str = None,
    wave_name: str = None,
    wave_number: int = None,
    cognito_user: Dict = None,
) -> Dict:
    """Initiate DRS recovery jobs for a wave without waiting for completion"""
    try:
        # Get Protection Group
        pg_result = protection_groups_table.get_item(Key={"groupId": protection_group_id})
        if "Item" not in pg_result:
            return {
                "waveName": wave.get("name", "Unknown"),
                "protectionGroupId": protection_group_id,
                "status": "FAILED",
                "error": "Protection Group not found",
                "servers": [],
                "startTime": int(time.time()),
            }

        pg = pg_result["Item"]
        region = pg["region"]

        # Get servers from both wave and protection group
        pg_servers = pg.get("sourceServerIds", [])
        wave_servers = wave.get("serverIds", [])

        # Filter to only launch servers specified in this wave
        if wave_servers:
            # Wave has explicit server list - filter PG servers to this subset
            server_ids = [s for s in wave_servers if s in pg_servers]
            print(f"Wave specifies {len(wave_servers)} servers, {len(server_ids)} are in Protection Group")
        else:
            # No ServerIds in wave - launch all PG servers
            server_ids = pg_servers
            print(f"Wave has no ServerIds field, launching all {len(server_ids)} Protection Group servers")

        if not server_ids:
            return {
                "waveName": wave.get("name", "Unknown"),
                "protectionGroupId": protection_group_id,
                "status": "INITIATED",
                "servers": [],
                "startTime": int(time.time()),
            }

        print(f"Initiating recovery for {len(server_ids)} servers in region {region}")

        # Launch ALL servers in wave with ONE DRS API call
        wave_job_result = start_drs_recovery_for_wave(
            server_ids,
            region,
            is_drill,
            execution_id,
            execution_type,
            plan_name=plan_name,
            wave_name=wave_name,
            wave_number=wave_number,
            cognito_user=cognito_user,
        )

        # Extract job ID and server results
        wave_job_id = wave_job_result.get("jobId")
        server_results = wave_job_result.get("servers", [])

        # Wave status is INITIATED (not IN_PROGRESS)
        has_failures = any(s["status"] == "FAILED" for s in server_results)
        wave_status = "PARTIAL" if has_failures else "INITIATED"

        return {
            "waveName": wave.get("name", "Unknown"),
            "waveId": wave.get("waveId") or wave.get("waveNumber"),
            "jobId": wave_job_id,
            "protectionGroupId": protection_group_id,
            "region": region,
            "status": wave_status,
            "servers": server_results,
            "startTime": int(time.time()),
        }

    except Exception as e:
        print(f"Error initiating wave: {str(e)}")
        import traceback

        traceback.print_exc()
        return {
            "waveName": wave.get("name", "Unknown"),
            "protectionGroupId": protection_group_id,
            "status": "FAILED",
            "error": str(e),
            "servers": [],
            "startTime": int(time.time()),
        }


def get_server_launch_configurations(region: str, server_ids: List[str]) -> Dict[str, Dict]:
    """
    Fetch launch configurations for all servers in wave from DRS.

    Retrieves DRS launch configuration settings for each server to determine how
    instances are launched during recovery. Uses safe defaults if configuration
    query fails to ensure recovery can proceed.

    ## Use Cases

    ### 1. Pre-Launch Configuration Retrieval
    ```python
    configs = get_server_launch_configurations(
        region="us-east-1",
        server_ids=["s-1234", "s-5678"]
    )
    for server_id, config in configs.items():
        print(f"{server_id}: {config['launchDisposition']}")
    ```

    ### 2. Wave Launch Preparation
    ```python
    # Get configs for all servers in wave before launching
    configs = get_server_launch_configurations(region, wave_server_ids)
    # Configs used to validate launch settings
    ```

    ## Behavior

    ### Configuration Retrieval
    1. Queries DRS GetLaunchConfiguration for each server
    2. Extracts key launch settings
    3. Falls back to safe defaults if query fails
    4. Returns configuration map for all servers

    ### Configuration Fields
    - targetInstanceTypeRightSizingMethod: BASIC (default) or NONE
    - copyPrivateIp: Whether to preserve private IP (default: False)
    - copyTags: Whether to copy tags to recovery instance (default: True)
    - launchDisposition: STARTED (default) or STOPPED
    - bootMode: USE_DEFAULT (default), LEGACY_BIOS, or UEFI

    ### Fallback Defaults
    If GetLaunchConfiguration fails for a server:
    ```python
    {
        "targetInstanceTypeRightSizingMethod": "BASIC",
        "copyPrivateIp": False,
        "copyTags": True,
        "launchDisposition": "STARTED",
        "bootMode": "USE_DEFAULT"
    }
    ```

    ## Args

    region: AWS region containing DRS servers
    server_ids: List of DRS source server IDs

    ## Returns

    Dict mapping server_id to launch configuration:
        - targetInstanceTypeRightSizingMethod: Right-sizing method
        - copyPrivateIp: Preserve private IP flag
        - copyTags: Copy tags flag
        - launchDisposition: Launch state (STARTED/STOPPED)
        - bootMode: Boot mode setting

    ## Example Response

    ```python
    {
        "s-1234567890abcdef0": {
            "targetInstanceTypeRightSizingMethod": "BASIC",
            "copyPrivateIp": True,
            "copyTags": True,
            "launchDisposition": "STARTED",
            "bootMode": "USE_DEFAULT"
        },
        "s-abcdef1234567890": {
            "targetInstanceTypeRightSizingMethod": "NONE",
            "copyPrivateIp": False,
            "copyTags": True,
            "launchDisposition": "STARTED",
            "bootMode": "UEFI"
        }
    }
    ```

    ## Performance

    ### Execution Time
    - Small wave (< 10 servers): 1-3 seconds
    - Medium wave (10-50 servers): 3-10 seconds
    - Large wave (50+ servers): 10-20 seconds

    ### API Calls
    - DRS GetLaunchConfiguration: 1 per server
    - Sequential execution (not parallelized)

    ## Error Handling

    ### Per-Server Fallback
    If GetLaunchConfiguration fails for a server:
    - Logs error with server ID
    - Uses safe fallback defaults
    - Continues processing remaining servers
    - Does NOT fail entire wave

    ## Related Functions

    - `apply_launch_config_to_servers()`: Apply launch config to servers
    - `start_drs_recovery_for_wave()`: Launch recovery with configs

    Fetch launch configurations for all servers in wave from DRS
    """
    drs_client = boto3.client("drs", region_name=region)
    configs = {}

    for server_id in server_ids:
        try:
            response = drs_client.get_launch_configuration(sourceServerID=server_id)

            configs[server_id] = {
                "targetInstanceTypeRightSizingMethod": response.get("targetInstanceTypeRightSizingMethod", "BASIC"),
                "copyPrivateIp": response.get("copyPrivateIp", False),
                "copyTags": response.get("copyTags", True),
                "launchDisposition": response.get("launchDisposition", "STARTED"),
                "bootMode": response.get("bootMode", "USE_DEFAULT"),
            }

            print(
                f"[Launch Config] {server_id}: rightSizing={configs[server_id]['targetInstanceTypeRightSizingMethod']}"
            )

        except Exception as e:
            print(f"[Launch Config] ERROR for {server_id}: {str(e)}")
            # FALLBACK: Use safe defaults if config query fails
            configs[server_id] = {
                "targetInstanceTypeRightSizingMethod": "BASIC",
                "copyPrivateIp": False,
                "copyTags": True,
                "launchDisposition": "STARTED",
                "bootMode": "USE_DEFAULT",
            }
            print(f"[Launch Config] {server_id}: Using fallback defaults")

    return configs


def start_drs_recovery_with_retry(server_id: str, region: str, is_drill: bool, execution_id: str) -> Dict:
    """Launch DRS recovery with ConflictException retry logic"""
    from botocore.exceptions import ClientError

    max_retries = 3
    base_delay = 30

    for attempt in range(max_retries):
        try:
            return start_drs_recovery(server_id, region, is_drill, execution_id)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            # Only retry on ConflictException
            if error_code == "ConflictException" and attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                print(f"ConflictException for server {server_id} (attempt {attempt + 1}/{max_retries})")
                print(f"Server is being processed by another job, retrying in {delay}s...")
                time.sleep(delay)
                continue

            # Re-raise if not ConflictException or last attempt
            raise
        except Exception:
            # Re-raise non-ClientError exceptions immediately
            raise


def start_drs_recovery(
    server_id: str,
    region: str,
    is_drill: bool,
    execution_id: str,
    execution_type: str = "DRILL",
) -> Dict:
    """Launch DRS recovery for a single source server"""
    try:
        drs_client = boto3.client("drs", region_name=region)

        print(f"Starting {execution_type} {'drill' if is_drill else 'recovery'} for server {server_id}")

        # Start recovery job
        response = drs_client.start_recovery(sourceServers=[{"sourceServerID": server_id}], isDrill=is_drill)

        job = response.get("job", {})
        job_id = job.get("jobID", "unknown")

        print(f"Started recovery job {job_id} for server {server_id}")

        return {
            "sourceServerId": server_id,
            "RecoveryJobId": job_id,
            "status": "LAUNCHING",
            "instanceId": None,
            "launchTime": int(time.time()),
            "error": None,
        }

    except Exception as e:
        error_msg = str(e)
        print(f"Failed to start recovery for server {server_id}: {error_msg}")
        return {
            "sourceServerId": server_id,
            "status": "FAILED",
            "error": error_msg,
            "launchTime": int(time.time()),
        }


def start_drs_recovery_for_wave(
    server_ids: List[str],
    region: str,
    is_drill: bool,
    execution_id: str,
    execution_type: str = "DRILL",
    plan_name: str = None,
    wave_name: str = None,
    wave_number: int = None,
    cognito_user: Dict = None,
) -> Dict:
    """
    Launch DRS recovery for all servers in a wave with ONE API call

    Args:
        server_ids: List of DRS source server IDs to launch
        region: AWS region for DRS API call
        is_drill: True for drill, False for actual recovery
        execution_id: Execution ID for tracking
        execution_type: 'DRILL' or 'RECOVERY'

    Returns:
        Dict with JobId (wave-level) and Servers array
    """
    try:
        drs_client = boto3.client("drs", region_name=region)

        print(f"[DRS API] Starting {execution_type} {'drill' if is_drill else 'recovery'}")
        print(f"[DRS API] Region: {region}, Servers: {len(server_ids)}")
        print(f"[DRS API] Server IDs: {server_ids}")

        # Build sourceServers array
        source_servers = [{"sourceServerID": sid} for sid in server_ids]
        print(f"[DRS API] Built sourceServers array for {len(server_ids)} servers")

        # Start recovery for ALL servers in ONE API call WITHOUT TAGS
        print("[DRS API] Calling start_recovery() WITHOUT tags (reference implementation pattern)")
        print(f"[DRS API]   sourceServers: {len(source_servers)} servers")
        print(f"[DRS API]   isDrill: {is_drill}")

        response = drs_client.start_recovery(
            sourceServers=source_servers,
            isDrill=is_drill,
        )

        # Validate response structure
        if "job" not in response:
            raise Exception("DRS API response missing 'job' field")

        job = response["job"]
        job_id = job.get("jobID")

        if not job_id:
            raise Exception("DRS API response missing 'jobID' field")

        job_status = job.get("status", "UNKNOWN")
        job_type = job.get("type", "UNKNOWN")

        print("[DRS API] ✅ Job created successfully")
        print(f"[DRS API]   Job ID: {job_id}")
        print(f"[DRS API]   Status: {job_status}")
        print(f"[DRS API]   Type: {job_type}")
        print(f"[DRS API]   Servers: {len(server_ids)} (all share this job ID)")

        # Build server results array (all servers share same job ID)
        server_results = []
        for server_id in server_ids:
            server_results.append(
                {
                    "sourceServerId": server_id,
                    "RecoveryJobId": job_id,
                    "status": "LAUNCHING",
                    "instanceId": None,
                    "launchTime": int(time.time()),
                    "error": None,
                }
            )

        print(f"[DRS API] Wave initiation complete - ExecutionPoller will track job {job_id}")

        return {
            "jobId": job_id,
            "servers": server_results,
        }

    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__

        print("[DRS API] ❌ Failed to start recovery for wave")
        print(f"[DRS API]   Error Type: {error_type}")
        print(f"[DRS API]   Error Message: {error_msg}")
        print(f"[DRS API]   Region: {region}")
        print(f"[DRS API]   Server Count: {len(server_ids)}")

        # Log full traceback for debugging
        import traceback

        traceback.print_exc()

        # Return failed results for all servers
        server_results = []
        for server_id in server_ids:
            server_results.append(
                {
                    "sourceServerId": server_id,
                    "status": "FAILED",
                    "error": f"{error_type}: {error_msg}",
                    "launchTime": int(time.time()),
                }
            )

        return {"jobId": None, "servers": server_results}


def apply_launch_config_before_recovery(
    drs_client,
    server_ids: List[str],
    launch_config: Dict,
    region: str,
    protection_group: Dict = None,
) -> None:
    """
    Apply Protection Group launch configuration to DRS servers before
    recovery.

    Updates both DRS launch settings and EC2 launch templates to ensure
    recovered instances use correct network, security, and instance
    configurations.

    Supports per-server configuration overrides:
    - If protection_group contains 'servers' array, applies per-server
      configs
    - Server-specific settings override protection group defaults
    - Supports static private IP assignment per server

    DRS Launch Settings Updated:
    - copyPrivateIp: Preserve source server private IP
    - copyTags: Copy source server tags to recovery instance
    - licensing: OS licensing configuration
    - targetInstanceTypeRightSizingMethod: Instance sizing strategy
    - launchDisposition: Launch behavior (STARTED/STOPPED)

    EC2 Launch Template Updated:
    - InstanceType: EC2 instance type for recovery
    - NetworkInterfaces: Subnet, security groups, and static private IP
    - IamInstanceProfile: IAM role for recovered instance

    Args:
        drs_client: Boto3 DRS client (may be cross-account)
        server_ids: List of DRS source server IDs
        launch_config: Protection Group launch configuration dict (group
                       defaults)
        region: AWS region for EC2 operations
        protection_group: Full protection group dict with per-server
                          configs (optional)

    Note:
        Failures for individual servers are logged but don't stop
        recovery. This ensures partial success when some servers have
        configuration issues.
    """
    ec2_client = boto3.client("ec2", region_name=region)

    # Import config merge function for per-server overrides
    try:
        from shared.config_merge import get_effective_launch_config
    except ImportError:
        print("Warning: config_merge module not found, per-server configs " "disabled")
        get_effective_launch_config = None

    for server_id in server_ids:
        try:
            # Get effective config (group defaults + per-server overrides)
            if protection_group and get_effective_launch_config:
                effective_config = get_effective_launch_config(protection_group, server_id)
            else:
                effective_config = launch_config

            # Get DRS launch configuration to find EC2 launch template
            current_config = drs_client.get_launch_configuration(sourceServerID=server_id)
            template_id = current_config.get("ec2LaunchTemplateID")

            if not template_id:
                print(f"No launch template found for {server_id}, skipping")
                continue

            # Update DRS launch configuration settings
            drs_update = {"sourceServerID": server_id}
            if "copyPrivateIp" in effective_config:
                drs_update["copyPrivateIp"] = effective_config["copyPrivateIp"]
            if "copyTags" in effective_config:
                drs_update["copyTags"] = effective_config["copyTags"]
            if "licensing" in effective_config:
                drs_update["licensing"] = effective_config["licensing"]
            if "targetInstanceTypeRightSizingMethod" in effective_config:
                drs_update["targetInstanceTypeRightSizingMethod"] = effective_config[
                    "targetInstanceTypeRightSizingMethod"
                ]
            if "launchDisposition" in effective_config:
                drs_update["launchDisposition"] = effective_config["launchDisposition"]

            if len(drs_update) > 1:
                drs_client.update_launch_configuration(**drs_update)
                print(f"Updated DRS launch config for {server_id}")

            # Update EC2 launch template with network/instance settings
            template_data = {}

            if effective_config.get("instanceType"):
                template_data["InstanceType"] = effective_config["instanceType"]

            # Handle network interfaces with static IP support
            if (
                effective_config.get("subnetId")
                or effective_config.get("securityGroupIds")
                or effective_config.get("staticPrivateIp")
            ):
                network_interface = {"DeviceIndex": 0}

                # Static private IP takes precedence
                if effective_config.get("staticPrivateIp"):
                    network_interface["PrivateIpAddress"] = effective_config["staticPrivateIp"]
                    print(f"Setting static IP " f"{effective_config['staticPrivateIp']} for " f"{server_id}")

                if effective_config.get("subnetId"):
                    network_interface["SubnetId"] = effective_config["subnetId"]
                if effective_config.get("securityGroupIds"):
                    network_interface["Groups"] = effective_config["securityGroupIds"]
                template_data["NetworkInterfaces"] = [network_interface]

            if effective_config.get("instanceProfileName"):
                template_data["IamInstanceProfile"] = {"Name": effective_config["instanceProfileName"]}

            if template_data:
                ec2_client.create_launch_template_version(
                    LaunchTemplateId=template_id,
                    LaunchTemplateData=template_data,
                    VersionDescription="DRS Orchestration pre-recovery update",
                )
                ec2_client.modify_launch_template(LaunchTemplateId=template_id, DefaultVersion="$Latest")
                print(f"Updated EC2 launch template {template_id} for " f"{server_id}")

        except Exception as e:
            print(f"Warning: Failed to apply launch config to {server_id}: {e}")
            # Continue with other servers - partial success is acceptable


def start_wave_recovery(state: Dict, wave_number: int) -> None:
    """
    Start DRS recovery for a wave with tag-based server resolution.

    Modifies state in-place (state ownership pattern) to update current wave
    tracking, job details, and wave results.

    Workflow:
    1. Retrieve Protection Group configuration from DynamoDB
    2. Resolve servers using tag-based discovery (execution-time
       resolution)
    3. Apply Protection Group launch configuration to DRS servers
    4. Start DRS recovery job (drill or production)
    5. Update state with job details and initial server statuses
    6. Store wave result in DynamoDB for frontend display

    Tag-Based Resolution:
    Servers are resolved at execution time by querying DRS for servers
    matching the Protection Group's serverSelectionTags. This enables
    dynamic discovery without maintaining static server lists. The
    pattern supports:
    - Auto-scaling: New servers automatically included if tags match
    - Multi-tenant: Customer/Environment tags scope recovery operations
    - Priority-based waves: dr:priority maps to wave numbers
      (critical→1, high→2, etc.)

    Wave Execution:
    - Sequential waves: This wave must complete before next wave starts
    - Parallel within wave: All servers launched simultaneously via
      batch API
    - Failure tolerance: Individual server failures don't stop wave
      execution

    Args:
        state: Complete state object (modified in-place)
        wave_number: Zero-based wave index to start

    State Updates:
    - current_wave_number: Set to wave_number
    - job_id: DRS job ID for tracking
    - region: AWS region for recovery
    - server_ids: List of resolved server IDs
    - wave_completed: Set to False (polling will update)
    - wave_results: Appended with new wave result

    Note:
        Failures set wave_completed=True and status='failed' to stop
        execution. Empty server lists (no tags matched) mark wave
        complete without error.

    Platform Extension:
        Other technology adapters (Aurora, ECS, Lambda, Route53) can
        implement similar start_wave_recovery functions with
        service-specific APIs while maintaining the same wave execution
        pattern and state management.
    """
    waves = state["waves"]
    wave = waves[wave_number]
    is_drill = state["is_drill"]
    execution_id = state["execution_id"]

    wave_name = wave.get("waveName", f"Wave {wave_number + 1}")

    # Get Protection Group from DynamoDB
    protection_group_id = wave.get("protectionGroupId")
    if not protection_group_id:
        print(f"Wave {wave_number} has no protectionGroupId")
        state["wave_completed"] = True
        state["status"] = "failed"
        state["error"] = "No protectionGroupId in wave"
        return

    try:
        pg_response = protection_groups_table.get_item(Key={"groupId": protection_group_id})
        if "Item" not in pg_response:
            print(f"Protection Group {protection_group_id} not found")
            state["wave_completed"] = True
            state["status"] = "failed"
            state["error"] = f"Protection Group {protection_group_id} not found"
            return

        pg = pg_response["Item"]
        region = pg.get("region", "us-east-1")

        # Tag-based server resolution at execution time
        selection_tags = pg.get("serverSelectionTags", {})

        if selection_tags:
            print(f"Resolving servers for PG {protection_group_id} " f"with tags: {selection_tags}")
            account_context = state.get("accountContext") or state.get("account_context", {})
            server_ids = query_drs_servers_by_tags(region, selection_tags, account_context)
            print(f"Resolved {len(server_ids)} servers from tags")
        else:
            # Fallback: explicit serverIds from wave (legacy support)
            server_ids = wave.get("serverIds", [])
            print(f"Using explicit serverIds from wave: " f"{len(server_ids)} servers")

        if not server_ids:
            print(f"Wave {wave_number} has no servers (no tags matched), " f"marking complete")
            state["wave_completed"] = True
            return

        print(f"Starting DRS recovery for wave {wave_number} " f"({wave_name})")
        print(f"Region: {region}, Servers: {server_ids}, " f"isDrill: {is_drill}")

        # Create DRS client with cross-account support
        account_context = state.get("accountContext") or state.get("account_context", {})
        drs_client = create_drs_client(region, account_context)

        # Apply Protection Group launch config before recovery
        launch_config = pg.get("launchConfig")
        if launch_config:
            print(f"Applying launchConfig to {len(server_ids)} servers " f"before recovery")
            apply_launch_config_before_recovery(drs_client, server_ids, launch_config, region, pg)

        source_servers = [{"sourceServerID": sid} for sid in server_ids]

        response = drs_client.start_recovery(isDrill=is_drill, sourceServers=source_servers)

        job_id = response["job"]["jobID"]
        print(f"✅ DRS Job created: {job_id}")

        # Build initial serverStatuses - execution-poller enriches
        # with details
        server_statuses = []
        for server_id in server_ids:
            server_statuses.append(
                {
                    "sourceServerId": server_id,
                    "serverName": server_id,  # Poller updates with Name
                    "hostname": "",
                    "launchStatus": "PENDING",
                    "instanceId": "",
                    "privateIp": "",
                    "instanceType": "",
                    "launchTime": 0,
                }
            )

        # Update state in-place (state ownership pattern)
        state["current_wave_number"] = wave_number
        state["job_id"] = job_id
        state["region"] = region
        state["server_ids"] = server_ids
        state["wave_completed"] = False
        state["current_wave_total_wait_time"] = 0

        # Store wave result for frontend display
        wave_result = {
            "waveNumber": wave_number,
            "waveName": wave_name,
            "status": "STARTED",
            "jobId": job_id,
            "startTime": int(time.time()),
            "serverIds": server_ids,
            "serverStatuses": server_statuses,
            "region": region,
        }
        state["wave_results"].append(wave_result)

        # Update DynamoDB with wave data at specific index to preserve
        # completed waves
        try:
            execution_history_table.update_item(
                Key={"executionId": execution_id, "planId": state["plan_id"]},
                UpdateExpression=(
                    f"SET waves[{wave_number}] = :wave, "
                    f"drsJobId = :job_id, drsRegion = :region, "
                    f"#status = :status"
                ),
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":wave": wave_result,
                    ":job_id": job_id,
                    ":region": region,
                    ":status": "POLLING",
                },
                ConditionExpression="attribute_exists(executionId)",
            )
        except Exception as e:
            print(f"Error updating wave start in DynamoDB: {e}")

    except Exception as e:
        print(f"Error starting DRS recovery: {e}")
        import traceback

        traceback.print_exc()
        state["wave_completed"] = True
        state["status"] = "failed"
        state["error"] = str(e)


def execute_recovery_plan_worker(payload: Dict) -> None:
    """
    Background worker - executes recovery via Step Functions.

    Handles both new executions and resumed executions.
    """
    try:
        execution_id = payload["executionId"]
        plan_id = payload["planId"]
        is_drill = payload["isDrill"]
        plan = payload["plan"]
        cognito_user = payload.get("cognitoUser", {"email": "system", "userId": "system"})
        resume_from_wave = payload.get("resumeFromWave")

        if resume_from_wave is not None:
            print(f"Worker RESUMING execution {execution_id} from wave {resume_from_wave} (isDrill: {is_drill})")
        else:
            print(f"Worker initiating NEW execution {execution_id} (isDrill: {is_drill})")
        print(f"Initiated by: {cognito_user.get('email')}")

        # Always use Step Functions
        state_machine_arn = os.environ.get("STATE_MACHINE_ARN")
        if not state_machine_arn:
            raise ValueError("STATE_MACHINE_ARN environment variable not set")

        print(f"Using Step Functions for execution {execution_id}")
        return execute_with_step_functions(
            execution_id,
            plan_id,
            plan,
            is_drill,
            state_machine_arn,
            resume_from_wave,
        )

    except Exception as e:
        print(f"Worker error for execution {execution_id}: {str(e)}")
        import traceback

        traceback.print_exc()

        # Mark execution as failed
        try:
            execution_history_table.update_item(
                Key={"executionId": execution_id, "planId": plan_id},
                UpdateExpression="SET #status = :status, endTime = :endtime, errorMessage = :error",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "FAILED",
                    ":endtime": int(time.time()),
                    ":error": str(e),
                },
            )
        except Exception as update_error:
            print(f"Failed to update error status: {str(update_error)}")


def list_executions(query_params: Dict) -> Dict:
    """
    List all executions with optional pagination and account filtering.

    Queries DynamoDB for execution history with filtering and pagination support.
    """
    try:
        limit = int(query_params.get("limit", 50))
        next_token = query_params.get("nextToken")
        account_id = query_params.get("accountId")

        # Scan execution history table
        scan_args = {"Limit": min(limit, 100)}  # Cap at 100

        if next_token:
            scan_args["ExclusiveStartKey"] = json.loads(next_token)

        result = execution_history_table.scan(**scan_args)

        executions = result.get("Items", [])

        # Filter by account if specified
        if account_id:
            filtered_executions = []
            for execution in executions:
                # Check both top-level accountId and accountContext.accountId
                exec_account = execution.get("accountId")
                if not exec_account:
                    # Fall back to accountContext.accountId
                    account_context = execution.get("accountContext", {})
                    exec_account = account_context.get("accountId")
                if exec_account == account_id:
                    filtered_executions.append(execution)
            executions = filtered_executions

        # Sort by startTime descending (most recent first)
        executions.sort(key=lambda x: x.get("startTime", 0), reverse=True)

        # Enrich with recovery plan names
        for execution in executions:
            try:
                # Use stored planName first (preserved even if plan deleted)
                if execution.get("planName"):
                    execution["recoveryPlanName"] = execution["planName"]
                else:
                    plan_id = execution.get("planId")
                    if plan_id:
                        plan_result = recovery_plans_table.get_item(Key={"planId": plan_id})
                        if "Item" in plan_result:
                            execution["recoveryPlanName"] = plan_result["Item"].get("planName", "Unknown")
                        else:
                            execution["recoveryPlanName"] = "Deleted Plan"
                    else:
                        execution["recoveryPlanName"] = "Unknown"

                # Add recoveryPlanId for frontend compatibility
                execution["recoveryPlanId"] = execution.get("planId")

                # Determine selection mode from protection groups
                plan_id = execution.get("planId")
                selection_mode = "PLAN"
                if plan_id:
                    plan_result = recovery_plans_table.get_item(Key={"planId": plan_id})
                    if "Item" in plan_result:
                        plan = plan_result["Item"]
                        waves = plan.get("waves", [])
                        pg_ids = set()
                        for wave in waves:
                            pg_id = wave.get("protectionGroupId")
                            if pg_id:
                                pg_ids.add(pg_id)

                        # Check each protection group for serverSelectionTags
                        for pg_id in pg_ids:
                            try:
                                pg_result = protection_groups_table.get_item(Key={"groupId": pg_id})
                                if "Item" in pg_result:
                                    pg = pg_result["Item"]
                                    tags = pg.get("serverSelectionTags", {})
                                    if tags and len(tags) > 0:
                                        selection_mode = "TAGS"
                                        break
                            except Exception as pg_err:
                                print(f"Error checking PG {pg_id}: {str(pg_err)}")

                execution["selectionMode"] = selection_mode
            except Exception as e:
                print(f"Error enriching execution {execution.get('executionId')}: {str(e)}")
                if not execution.get("recoveryPlanName"):
                    execution["recoveryPlanName"] = "Unknown"
                execution["selectionMode"] = "PLAN"

            # Check if any wave has an active DRS job
            has_active_jobs = False
            if "waves" in execution:
                for wave in execution["waves"]:
                    wave_status = wave.get("status", "").upper()
                    if wave_status in ["PENDING", "INITIATED", "STARTED"]:
                        has_active_jobs = True
                        break
            execution["hasActiveDrsJobs"] = has_active_jobs

            # Add termination metadata for frontend button visibility
            execution["terminationMetadata"] = can_terminate_execution(execution)

        # Build response with pagination
        response_data = {
            "items": executions,
            "count": len(executions),
        }

        if "LastEvaluatedKey" in result:
            response_data["nextToken"] = json.dumps(result["LastEvaluatedKey"])
        else:
            response_data["nextToken"] = None

        print(f"Listed {len(executions)} executions")
        return response(200, response_data)

    except Exception as e:
        print(f"Error listing executions: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def get_execution_details(execution_id: str, query_params: Dict) -> Dict:
    """
    Get execution details by ID - uses cached data for fast response.
    """
    try:
        # Handle both UUID and ARN formats for backwards compatibility
        if execution_id.startswith("arn:"):
            execution_id = execution_id.split(":")[-1]
            print(f"Extracted UUID from ARN: {execution_id}")

        # Get from DynamoDB
        result = execution_history_table.query(KeyConditionExpression=Key("executionId").eq(execution_id), Limit=1)

        if "Items" not in result or len(result["Items"]) == 0:
            return response(
                404,
                {
                    "error": "EXECUTION_NOT_FOUND",
                    "message": f"Execution with ID {execution_id} not found",
                    "executionId": execution_id,
                },
            )

        execution = result["Items"][0]

        # Ensure waves field exists (empty array if not present)
        if "waves" not in execution or execution.get("waves") is None:
            execution["waves"] = []

        # Basic enrichment with stored data only
        try:
            if execution.get("planName"):
                execution["recoveryPlanName"] = execution["planName"]

            plan_id = execution.get("planId")
            if plan_id:
                plan_result = recovery_plans_table.get_item(Key={"planId": plan_id})
                if "Item" in plan_result:
                    plan = plan_result["Item"]
                    if not execution.get("recoveryPlanName"):
                        execution["recoveryPlanName"] = plan.get("planName", "Unknown")
                    execution["recoveryPlanDescription"] = plan.get("description", "")
                    execution["totalWaves"] = len(plan.get("waves", []))
                elif not execution.get("recoveryPlanName"):
                    execution["recoveryPlanName"] = "Deleted Plan"
        except Exception as e:
            print(f"Error enriching execution with plan details: {str(e)}")

        # Mark as cached data for frontend
        execution["dataSource"] = "cached"
        execution["lastUpdated"] = execution.get("updatedAt", int(time.time()))

        # Add flag to indicate if real-time data is available
        execution["hasRealtimeData"] = execution.get("status") in [
            "RUNNING",
            "PAUSED",
        ]

        # Add termination metadata for frontend button visibility
        execution["terminationMetadata"] = can_terminate_execution(execution)

        # PERFORMANCE OPTIMIZATION: Enrich completed waves with recovery instance data
        # Only call DRS API for completed waves to populate Instance ID, Type, Private IP, Launch Time
        # This ensures UI shows recovery instance details without requiring /realtime endpoint
        try:
            waves = execution.get("waves", [])
            has_completed_waves = any(wave.get("status", "").upper() in ["COMPLETED", "FAILED"] for wave in waves)

            if has_completed_waves:
                print("DEBUG: Enriching completed waves with recovery instance data")
                execution = reconcile_wave_status_with_drs(execution)

                # CRITICAL FIX: Persist wave status updates to DynamoDB
                # The reconcile_wave_status_with_drs function updates wave status in memory,
                # but we need to persist these updates so termination logic works correctly
                try:
                    updated_waves = execution.get("waves", [])
                    execution_history_table.update_item(
                        Key={
                            "executionId": execution_id,
                            "planId": execution.get("planId"),
                        },
                        UpdateExpression="SET waves = :waves, updatedAt = :updated",
                        ExpressionAttributeValues={
                            ":waves": updated_waves,
                            ":updated": int(time.time()),
                        },
                    )
                    print(f"✅ Persisted wave status updates to DynamoDB for {execution_id}")
                except Exception as persist_error:
                    print(f"Error persisting wave updates: {persist_error}")
        except Exception as enrich_error:
            print(f"Error enriching completed waves: {enrich_error}")
            # Don't fail the request if enrichment fails

        return response(200, execution)

    except Exception as e:
        print(f"Error getting execution details: {str(e)}")
        return response(
            500,
            {
                "error": "INTERNAL_ERROR",
                "message": f"Error retrieving execution details: {str(e)}",
                "executionId": execution_id,
            },
        )


def cancel_execution(execution_id: str, body: Dict) -> Dict:
    """
    Cancel a running execution - cancels only pending waves, not completed or in-progress ones.

    Behavior:
    - COMPLETED waves: Preserved as-is
    - IN_PROGRESS/POLLING/LAUNCHING waves: Continue running (not interrupted)
    - PENDING/NOT_STARTED waves: Marked as CANCELLED
    - Waves not yet started (from plan): Added with CANCELLED status
    - Overall execution status: Set to CANCELLED only if no waves are still running
    """
    try:
        # Query by ExecutionId to get PlanId (composite key required)
        result = execution_history_table.query(KeyConditionExpression=Key("executionId").eq(execution_id), Limit=1)

        if not result.get("Items"):
            return response(
                404,
                {
                    "error": "EXECUTION_NOT_FOUND",
                    "message": f"Execution with ID {execution_id} not found",
                    "executionId": execution_id,
                },
            )

        execution = result["Items"][0]
        plan_id = execution.get("planId")

        # Check if execution is still running
        current_status = execution.get("status")
        cancellable_statuses = [
            "RUNNING",
            "PAUSED",
            "PAUSE_PENDING",
            "CANCELLING",
            "IN_PROGRESS",
            "POLLING",
            "INITIATED",
            "PENDING",
        ]
        if current_status not in cancellable_statuses:
            return response(
                400,
                {
                    "error": "EXECUTION_NOT_CANCELLABLE",
                    "message": f"Execution cannot be cancelled - status is {current_status}",
                    "currentStatus": current_status,
                    "cancellableStatuses": cancellable_statuses,
                    "reason": "Execution must be running, paused, or pending to cancel",
                },
            )

        # Get waves from execution and plan
        waves = execution.get("waves", [])
        timestamp = int(time.time())

        # Get recovery plan to find waves that haven't started yet
        plan_waves = []
        try:
            plan_result = recovery_plans_table.get_item(Key={"planId": plan_id})
            if "Item" in plan_result:
                plan_waves = plan_result["Item"].get("waves", [])
        except Exception as e:
            print(f"Error getting recovery plan: {e}")

        # Track wave states
        completed_waves = []
        in_progress_waves = []
        cancelled_waves = []

        # Statuses that indicate a wave is done
        completed_statuses = ["COMPLETED", "FAILED", "TIMEOUT"]
        # Statuses that indicate a wave is running
        in_progress_statuses = [
            "IN_PROGRESS",
            "POLLING",
            "LAUNCHING",
            "INITIATED",
            "STARTED",
        ]

        # Track which wave numbers exist in execution
        existing_wave_numbers = set()

        for i, wave in enumerate(waves):
            wave_status = (wave.get("status") or "").upper()
            wave_number = wave.get("waveNumber", i)
            existing_wave_numbers.add(wave_number)

            if wave_status in completed_statuses:
                completed_waves.append(wave_number)
            elif wave_status in in_progress_statuses:
                in_progress_waves.append(wave_number)
            else:
                # Pending/not started waves - mark as CANCELLED
                waves[i]["status"] = "CANCELLED"
                waves[i]["endTime"] = timestamp
                cancelled_waves.append(wave_number)

        # Add waves from plan that haven't started yet
        for i, plan_wave in enumerate(plan_waves):
            wave_number = plan_wave.get("waveNumber", i)
            if wave_number not in existing_wave_numbers:
                cancelled_wave = {
                    "waveNumber": wave_number,
                    "waveName": plan_wave.get("waveName", f"Wave {wave_number + 1}"),
                    "status": "CANCELLED",
                    "endTime": timestamp,
                    "protectionGroupId": plan_wave.get("protectionGroupId"),
                    "serverIds": plan_wave.get("serverIds", []),
                }
                waves.append(cancelled_wave)
                cancelled_waves.append(wave_number)

        # Sort waves by wave number
        waves.sort(key=lambda w: w.get("waveNumber", 0))

        # Stop Step Functions execution only if no waves are in progress
        if not in_progress_waves:
            try:
                stepfunctions.stop_execution(
                    executionArn=execution_id,
                    error="UserCancelled",
                    cause="Execution cancelled by user",
                )
                print(f"Stopped Step Functions execution: {execution_id}")
            except Exception as e:
                print(f"Error stopping Step Functions execution: {str(e)}")

        # Determine final execution status
        final_status = "CANCELLING" if in_progress_waves else "CANCELLED"

        # Update DynamoDB
        update_expression = "SET #status = :status, waves = :waves"
        expression_values = {":status": final_status, ":waves": waves}

        if not in_progress_waves:
            update_expression += ", endTime = :endtime"
            expression_values[":endtime"] = timestamp

        execution_history_table.update_item(
            Key={"executionId": execution_id, "planId": plan_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues=expression_values,
        )

        print(
            f"Cancel execution {execution_id}: completed={completed_waves}, in_progress={in_progress_waves}, cancelled={cancelled_waves}"  # noqa: E501
        )

        return response(
            200,
            {
                "executionId": execution_id,
                "status": final_status,
                "message": f'Execution {"cancelling" if in_progress_waves else "cancelled"} successfully',
                "details": {
                    "completedWaves": completed_waves,
                    "inProgressWaves": in_progress_waves,
                    "cancelledWaves": cancelled_waves,
                },
            },
        )

    except Exception as e:
        print(f"Error cancelling execution: {str(e)}")
        return response(500, {"error": str(e)})


def pause_execution(execution_id: str, body: Dict) -> Dict:
    """
    Pause execution - schedules pause after current wave completes.

    Behavior:
    - If wave is in progress AND pending waves exist: Mark as PAUSE_PENDING
    - If between waves AND pending waves exist: Mark as PAUSED immediately
    - If no pending waves: Error (nothing to pause)
    - Single wave executions cannot be paused
    """
    try:
        result = execution_history_table.query(KeyConditionExpression=Key("executionId").eq(execution_id), Limit=1)

        if not result.get("Items"):
            return response(
                404,
                {
                    "error": "EXECUTION_NOT_FOUND",
                    "message": f"Execution with ID {execution_id} not found",
                    "executionId": execution_id,
                },
            )

        execution = result["Items"][0]
        plan_id = execution.get("planId")
        current_status = execution.get("status", "")

        # Check if execution is in a pausable state
        pausable_statuses = ["RUNNING", "IN_PROGRESS", "POLLING"]
        if current_status not in pausable_statuses:
            return response(
                400,
                {
                    "error": "EXECUTION_NOT_PAUSABLE",
                    "message": f"Execution cannot be paused - status is {current_status}",
                    "currentStatus": current_status,
                    "pausableStatuses": pausable_statuses,
                    "reason": "Execution must be running to pause",
                },
            )

        # Check wave states
        waves = execution.get("waves", [])
        if not waves:
            return response(
                400,
                {
                    "error": "EXECUTION_NO_WAVES",
                    "message": "No waves found in execution - cannot pause",
                    "executionId": execution_id,
                    "currentStatus": current_status,
                },
            )

        # Single wave executions cannot be paused
        if len(waves) == 1:
            return response(
                400,
                {
                    "error": "SINGLE_WAVE_NOT_PAUSABLE",
                    "message": "Cannot pause single-wave execution - pause is only available for multi-wave recovery plans",  # noqa: E501
                    "executionId": execution_id,
                    "waveCount": 1,
                    "reason": "Pause is only available for multi-wave recovery plans",
                },
            )

        # Find current wave state
        completed_statuses = ["COMPLETED", "FAILED", "TIMEOUT", "CANCELLED"]
        in_progress_statuses = [
            "IN_PROGRESS",
            "POLLING",
            "LAUNCHING",
            "INITIATED",
            "STARTED",
        ]

        has_in_progress_wave = False
        has_pending_wave = False
        current_wave_number = 0
        last_completed_wave = 0

        for i, wave in enumerate(waves):
            wave_status = (wave.get("status") or "").upper()
            wave_number = wave.get("waveNumber", i + 1)

            if wave_status in completed_statuses:
                last_completed_wave = wave_number
            elif wave_status in in_progress_statuses:
                has_in_progress_wave = True
                current_wave_number = wave_number
            else:
                has_pending_wave = True

        # Must have pending waves to pause
        if not has_pending_wave:
            return response(
                400,
                {
                    "error": "NO_PENDING_WAVES",
                    "message": "Cannot pause - no pending waves remaining",
                    "executionId": execution_id,
                    "lastCompletedWave": last_completed_wave,
                    "reason": "All waves have already completed or failed",
                },
            )

        # Determine pause type
        if has_in_progress_wave:
            new_status = "PAUSE_PENDING"
            message = f"Pause scheduled - will pause after wave {current_wave_number} completes"
        else:
            new_status = "PAUSED"
            message = "Execution paused"

        execution_history_table.update_item(
            Key={"executionId": execution_id, "planId": plan_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": new_status},
        )

        print(f"Pause execution {execution_id}: status={new_status}, current_wave={current_wave_number}")
        return response(
            200,
            {
                "executionId": execution_id,
                "status": new_status,
                "message": message,
                "lastCompletedWave": last_completed_wave,
            },
        )

    except Exception as e:
        print(f"Error pausing execution: {str(e)}")
        return response(500, {"error": str(e)})


# ============================================================================
# Operation Handlers (Phase 2: Consolidation)
# ============================================================================


def handle_operation(event: Dict, context) -> Dict:
    """
    Route operation-based Lambda invocations to lifecycle handlers.

    DIRECT INVOCATION EXAMPLES:

    1. Find active executions (EventBridge trigger):
       aws lambda invoke --function-name execution-handler \\
         --payload '{"operation": "find"}' response.json

    2. Poll specific execution:
       aws lambda invoke --function-name execution-handler \\
         --payload '{"operation": "poll", "executionId": "uuid", "planId": "uuid"}' \\
         response.json

    3. Finalize execution (Step Functions only):
       aws lambda invoke --function-name execution-handler \\
         --payload '{"operation": "finalize", "executionId": "uuid", "planId": "uuid"}' \\
         response.json

    4. Pause execution:
       aws lambda invoke --function-name execution-handler \\
         --payload '{"operation": "pause", "executionId": "uuid", "reason": "Manual approval"}' \\
         response.json

    5. Resume execution:
       aws lambda invoke --function-name execution-handler \\
         --payload '{"operation": "resume", "executionId": "uuid"}' \\
         response.json

    OPERATION BEHAVIORS:
    - find: Queries DynamoDB, self-invokes poll for each active execution
    - poll: Updates wave status, enriches server data, NEVER finalizes
    - finalize: Marks execution COMPLETED (idempotent, requires all waves complete)
    - pause: Changes execution status to PAUSED
    - resume: Changes execution status to POLLING and resumes Step Functions

    RETURNS:
        Dict with statusCode and operation-specific response data
    """
    operation = event.get("operation")

    if operation == "find":
        return handle_find_operation(event, context)
    elif operation == "poll":
        return handle_poll_operation(event, context)
    elif operation == "finalize":
        return handle_finalize_operation(event, context)
    elif operation == "pause":
        return handle_pause_operation(event, context)
    elif operation == "resume":
        return handle_resume_operation(event, context)
    else:
        return response(
            400,
            {
                "error": "UNKNOWN_OPERATION",
                "message": f"Unknown operation: {operation}",
                "supportedOperations": [
                    "find",
                    "poll",
                    "finalize",
                    "pause",
                    "resume",
                ],
            },
        )


def handle_find_operation(event: Dict, context) -> Dict:
    """
    Find active executions and trigger polling for each.

    TRIGGER: EventBridge rule (30s schedule) OR direct invocation

    BEHAVIOR:
    1. Query DynamoDB StatusIndex for POLLING and CANCELLING executions
    2. Self-invoke with operation="poll" for each execution found
    3. Return summary of polling results

    WHY SELF-INVOKE: Allows parallel polling of multiple executions
    without blocking EventBridge trigger or exceeding Lambda timeout.

    DIRECT INVOCATION:
        aws lambda invoke --function-name execution-handler \\
          --payload '{"operation": "find"}' response.json
    """
    try:
        print("Finding executions that need polling")

        # Query for POLLING executions
        polling_result = execution_history_table.query(
            IndexName="StatusIndex",
            KeyConditionExpression=Key("status").eq("POLLING"),
        )

        # Query for CANCELLING executions
        cancelling_result = execution_history_table.query(
            IndexName="StatusIndex",
            KeyConditionExpression=Key("status").eq("CANCELLING"),
        )

        executions = polling_result.get("Items", []) + cancelling_result.get("Items", [])

        print(f"Found {len(executions)} executions needing polling")

        # Invoke polling for each execution
        poll_results = []
        for execution in executions:
            execution_id = execution.get("executionId")
            plan_id = execution.get("planId")

            if not execution_id or not plan_id:
                print(f"Skipping execution with missing ID: {execution}")
                continue

            try:
                # Invoke poll operation for this execution
                poll_event = {
                    "operation": "poll",
                    "executionId": execution_id,
                    "planId": plan_id,
                }

                poll_result = handle_poll_operation(poll_event, context)
                poll_results.append(
                    {
                        "executionId": execution_id,
                        "success": poll_result.get("statusCode") == 200,
                        "status": poll_result.get("status"),
                    }
                )

            except Exception as poll_error:
                print(f"Error polling execution {execution_id}: {poll_error}")
                poll_results.append(
                    {
                        "executionId": execution_id,
                        "success": False,
                        "error": str(poll_error),
                    }
                )

        return {
            "statusCode": 200,
            "executionsFound": len(executions),
            "executionsPolled": len(poll_results),
            "results": poll_results,
        }

    except Exception as e:
        print(f"Error finding executions: {e}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def handle_poll_operation(event: Dict, context) -> Dict:
    """
    Poll DRS job status and enrich server data with EC2 details.

    TRIGGER: Self-invoked by handle_find_operation OR direct invocation

    CRITICAL BEHAVIOR:
    - Updates wave status in DynamoDB (serverStatuses, lastPolledTime)
    - Enriches server data with DRS + EC2 instance details
    - NEVER changes execution status (Step Functions controls lifecycle)
    - NEVER calls finalize_execution() (prevents premature completion)

    WHY NO FINALIZATION: Multi-wave executions have waves created sequentially
    by Step Functions. Poller only sees the active wave, not subsequent waves.
    Only Step Functions knows when ALL waves complete.

    DATA ENRICHMENT:
    - DRS API: sourceServerId, launchStatus, recoveryInstanceId
    - EC2 API: instanceId, privateIp, hostname, instanceType
    - Normalized to camelCase via shared.drs_utils

    DIRECT INVOCATION:
        aws lambda invoke --function-name execution-handler \\
          --payload '{"operation": "poll", "executionId": "uuid", "planId": "uuid"}' \\
          response.json

    RETURNS:
        {
            "statusCode": 200,
            "executionId": "uuid",
            "status": "POLLING",
            "allWavesComplete": false,
            "waves": [...]
        }
    """
    try:
        execution_id = event.get("executionId")
        plan_id = event.get("planId")

        if not execution_id or not plan_id:
            return response(
                400,
                {
                    "error": "MISSING_PARAMETERS",
                    "message": "executionId and planId required",
                },
            )

        print(f"Polling execution {execution_id}")

        # Get execution from DynamoDB
        exec_result = execution_history_table.get_item(Key={"executionId": execution_id, "planId": plan_id})

        if "Item" not in exec_result:
            return response(
                404,
                {"error": "EXECUTION_NOT_FOUND", "executionId": execution_id},
            )

        execution = exec_result["Item"]
        execution_status = execution.get("status", "POLLING")

        # Skip if already completed
        if execution_status in [
            "COMPLETED",
            "FAILED",
            "TERMINATED",
            "TIMEOUT",
            "PARTIAL",
        ]:
            print(f"Execution {execution_id} already {execution_status} - skipping poll")
            return {
                "statusCode": 200,
                "executionId": execution_id,
                "status": execution_status,
                "allWavesComplete": True,
            }

        # CRITICAL: Check Step Functions status to detect failures
        # Step Functions is the source of truth for execution lifecycle
        state_machine_arn = execution.get("stateMachineArn")
        if state_machine_arn and execution_status in ["POLLING", "RUNNING"]:
            try:
                sf_response = stepfunctions.describe_execution(executionArn=state_machine_arn)
                sf_status = sf_response.get("status")
                print(f"Step Functions status for {execution_id}: {sf_status}")

                # If Step Functions shows terminal state, analyze outcome and update DynamoDB
                if sf_status in ["FAILED", "TIMED_OUT", "ABORTED", "SUCCEEDED"]:
                    # Get waves for outcome analysis
                    waves = execution.get("waves", [])

                    # Analyze actual wave/server outcomes
                    outcome = analyze_execution_outcome(waves)
                    analyzed_status = outcome["status"]
                    summary = outcome["summary"]
                    details = outcome["details"]

                    # For SF FAILED/TIMED_OUT/ABORTED, use analyzed status (could be PARTIAL)
                    # For SF SUCCEEDED, use analyzed status (should be COMPLETED but could be PARTIAL)
                    if sf_status in ["FAILED", "TIMED_OUT", "ABORTED"]:
                        # If some servers launched, use PARTIAL; otherwise use SF-derived status
                        if analyzed_status == "PARTIAL":
                            new_status = "PARTIAL"
                        elif analyzed_status == "COMPLETED":
                            # Rare: SF failed but all servers launched (maybe post-launch failure)
                            new_status = "PARTIAL"
                            summary = f"{summary} (Step Functions reported {sf_status})"
                        else:
                            # Map Step Functions status to our status
                            new_status = (
                                "FAILED"
                                if sf_status == "FAILED"
                                else "TIMEOUT" if sf_status == "TIMED_OUT" else "TERMINATED"
                            )
                    else:
                        # SF SUCCEEDED - use analyzed status
                        new_status = analyzed_status

                    # Build error message from SF and outcome analysis
                    error_message = None
                    if sf_status == "FAILED":
                        sf_error = sf_response.get("error", "")
                        sf_cause = sf_response.get("cause", "")
                        if sf_error or sf_cause:
                            error_message = f"{sf_error}: {sf_cause}" if sf_error and sf_cause else sf_error or sf_cause

                    # Use summary as message for PARTIAL status
                    if new_status == "PARTIAL":
                        error_message = summary

                    print(f"⚠️ Step Functions {sf_status} - analyzed outcome: {new_status}")
                    print(f"   Summary: {summary}")
                    print(f"   Details: {details}")

                    # Update DynamoDB with analyzed status
                    update_expr = "SET #status = :status, endTime = :endtime, lastPolledTime = :time"
                    expr_values = {
                        ":status": new_status,
                        ":endtime": int(time.time()),
                        ":time": int(time.time()),
                    }

                    if error_message:
                        update_expr += ", errorMessage = :error"
                        expr_values[":error"] = error_message

                    # Store outcome details for UI display
                    update_expr += ", outcomeDetails = :details, outcomeSummary = :summary"
                    expr_values[":details"] = details
                    expr_values[":summary"] = summary

                    execution_history_table.update_item(
                        Key={"executionId": execution_id, "planId": plan_id},
                        UpdateExpression=update_expr,
                        ExpressionAttributeNames={"#status": "status"},
                        ExpressionAttributeValues=expr_values,
                    )

                    print(f"✅ Execution {execution_id} marked as {new_status}")
                    return {
                        "statusCode": 200,
                        "executionId": execution_id,
                        "status": new_status,
                        "stepFunctionsStatus": sf_status,
                        "errorMessage": error_message,
                        "outcomeSummary": summary,
                        "outcomeDetails": details,
                        "allWavesComplete": True,
                    }

            except ClientError as sf_error:
                # Step Functions execution might not exist or be accessible
                error_code = sf_error.response.get("Error", {}).get("Code", "")
                if error_code == "ExecutionDoesNotExist":
                    print("⚠️ Step Functions execution not found - marking as FAILED")
                    execution_history_table.update_item(
                        Key={"executionId": execution_id, "planId": plan_id},
                        UpdateExpression="SET #status = :status, endTime = :endtime, errorMessage = :error",
                        ExpressionAttributeNames={"#status": "status"},
                        ExpressionAttributeValues={
                            ":status": "FAILED",
                            ":endtime": int(time.time()),
                            ":error": "Step Functions execution not found",
                        },
                    )
                    return {
                        "statusCode": 200,
                        "executionId": execution_id,
                        "status": "FAILED",
                        "errorMessage": "Step Functions execution not found",
                        "allWavesComplete": True,
                    }
                else:
                    print(f"Error checking Step Functions status: {sf_error}")
            except Exception as sf_error:
                print(f"Error checking Step Functions status: {sf_error}")

        # Poll each wave
        waves = execution.get("waves", [])
        updated_waves = []

        for wave in waves:
            wave_status = wave.get("status", "").upper()

            # Skip completed waves
            if wave_status in ["COMPLETED", "FAILED", "TERMINATED", "TIMEOUT"]:
                updated_waves.append(wave)
                continue

            # Poll in-progress waves
            if wave_status in [
                "IN_PROGRESS",
                "POLLING",
                "LAUNCHING",
                "INITIATED",
                "STARTED",
            ]:
                account_context = execution.get("accountContext")
                updated_wave = poll_wave_with_enrichment(wave, execution.get("executionType", "DRILL"), account_context)
                updated_waves.append(updated_wave)
            else:
                # PENDING or other status - don't poll yet
                updated_waves.append(wave)

        # Check if all waves are complete
        all_waves_complete = all(
            w.get("status", "").upper() in ["COMPLETED", "FAILED", "TERMINATED", "TIMEOUT", "CANCELLED"]
            for w in updated_waves
        )

        # Handle CANCELLING execution finalization
        if execution_status == "CANCELLING" and all_waves_complete:
            # Analyze outcome - may be PARTIAL if some servers launched before cancellation
            outcome = analyze_execution_outcome(updated_waves)
            # For cancelled executions, use CANCELLED unless some servers succeeded (PARTIAL)
            final_status = "PARTIAL" if outcome["status"] == "PARTIAL" else "CANCELLED"
            summary = outcome["summary"]
            details = outcome["details"]

            print(f"CANCELLING execution {execution_id} - analyzed outcome: {final_status}")
            print(f"   Summary: {summary}")

            execution_history_table.update_item(
                Key={"executionId": execution_id, "planId": plan_id},
                UpdateExpression="SET waves = :waves, lastPolledTime = :time, #status = :status, endTime = :endtime, outcomeSummary = :summary, outcomeDetails = :details, errorMessage = :error",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":waves": updated_waves,
                    ":time": int(time.time()),
                    ":status": final_status,
                    ":endtime": int(time.time()),
                    ":summary": summary,
                    ":details": details,
                    ":error": summary,
                },
            )
            print(f"✅ CANCELLING execution {execution_id} finalized to {final_status}")
            return {
                "statusCode": 200,
                "executionId": execution_id,
                "status": final_status,
                "waves": updated_waves,
                "outcomeSummary": summary,
                "outcomeDetails": details,
                "allWavesComplete": True,
            }

        # Update waves in DynamoDB (NO STATUS CHANGE for non-CANCELLING)
        execution_history_table.update_item(
            Key={"executionId": execution_id, "planId": plan_id},
            UpdateExpression="SET waves = :waves, lastPolledTime = :time",
            ExpressionAttributeValues={
                ":waves": updated_waves,
                ":time": int(time.time()),
            },
        )

        print(f"✅ Polling complete for {execution_id} - waves updated, execution status unchanged")

        return {
            "statusCode": 200,
            "executionId": execution_id,
            "status": execution_status,
            "waves": updated_waves,
            "allWavesComplete": all_waves_complete,
        }

    except Exception as e:
        print(f"Error polling execution: {e}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def poll_wave_with_enrichment(wave: Dict, execution_type: str, account_context: Dict = None) -> Dict:
    """
    Poll wave status from DRS and enrich with EC2 data.

    Combines DRS job status with EC2 instance details for complete server data.

    Args:
        wave: Wave record with jobId and region
        execution_type: DRILL or RECOVERY
        account_context: Target account credentials (accountId, assumeRoleName, externalId)
    """
    try:
        job_id = wave.get("jobId")
        region = wave.get("region", "us-east-1")

        if not job_id:
            print(f"Wave {wave.get('waveName')} has no jobId")
            return wave

        # Get credentials for target account if cross-account
        if account_context and not account_context.get("isCurrentAccount"):
            from shared.account_utils import get_target_account_session

            session = get_target_account_session(account_context)
            drs_client = session.client("drs", region_name=region)
            print(f"Using cross-account DRS client for account {account_context.get('accountId')}")
        else:
            drs_client = boto3.client("drs", region_name=region)

        # Query DRS for job status
        job_response = drs_client.describe_jobs(filters={"jobIDs": [job_id]})

        if not job_response.get("items"):
            print(f"No DRS job found for {job_id}")
            return wave

        job = job_response["items"][0]

        # Don't overwrite CANCELLED status - wave was cancelled by user
        current_status = wave.get("status", "").upper()
        if current_status != "CANCELLED":
            wave["status"] = job.get("status", "UNKNOWN")

        # Enrich server data with DRS + EC2 details
        from shared.drs_utils import enrich_server_data

        participating_servers = job.get("participatingServers", [])
        if participating_servers:
            # Use same session for EC2 client
            if account_context and not account_context.get("isCurrentAccount"):
                ec2_client = session.client("ec2", region_name=region)
            else:
                ec2_client = boto3.client("ec2", region_name=region)

            enriched_servers = enrich_server_data(participating_servers, drs_client, ec2_client)
            print(f"DEBUG: Enriched {len(enriched_servers)} servers")
            print(
                f"DEBUG: First enriched server: {json.dumps(enriched_servers[0] if enriched_servers else {}, cls=DecimalEncoder)}"  # noqa: E501
            )
            wave["serverStatuses"] = enriched_servers

        return wave

    except Exception as e:
        print(f"Error polling wave: {e}")
        wave["status"] = "ERROR"
        wave["statusMessage"] = str(e)
        return wave


def handle_finalize_operation(event: Dict, context) -> Dict:
    """
    Mark execution as COMPLETED after all waves finish.

    TRIGGER: Step Functions ONLY (after verifying all waves complete)

    CRITICAL BEHAVIOR:
    - Validates all waves have status=COMPLETED
    - Uses conditional write (prevents race conditions)
    - Idempotent (safe to call multiple times)
    - Updates: status=COMPLETED, completedTime=now()

    WHY STEP FUNCTIONS ONLY: Step Functions maintains authoritative list
    of all waves (including subsequent waves not yet created in DynamoDB).
    Only Step Functions knows when execution is truly complete.

    IDEMPOTENCY: Returns success if already COMPLETED/FAILED/TERMINATED.
    Uses DynamoDB conditional expression to prevent concurrent updates.

    DIRECT INVOCATION (testing only):
        aws lambda invoke --function-name execution-handler \\
          --payload '{"operation": "finalize", "executionId": "uuid", "planId": "uuid"}' \\
          response.json

    RETURNS:
        {
            "statusCode": 200,
            "executionId": "uuid",
            "status": "COMPLETED",
            "totalWaves": 3,
            "alreadyFinalized": false
        }
    """
    try:
        execution_id = event.get("executionId")
        plan_id = event.get("planId")

        if not execution_id or not plan_id:
            return response(
                400,
                {
                    "error": "MISSING_PARAMETERS",
                    "message": "executionId and planId required",
                },
            )

        print(f"Finalizing execution {execution_id}")

        # Get execution
        exec_result = execution_history_table.get_item(Key={"executionId": execution_id, "planId": plan_id})

        if "Item" not in exec_result:
            return response(
                404,
                {"error": "EXECUTION_NOT_FOUND", "executionId": execution_id},
            )

        execution = exec_result["Item"]
        current_status = execution.get("status", "")
        waves = execution.get("waves", [])

        # Idempotent: if already finalized, return success
        if current_status in ["COMPLETED", "FAILED", "TERMINATED", "PARTIAL"]:
            print(f"Execution {execution_id} already finalized with status {current_status}")
            return {
                "statusCode": 200,
                "executionId": execution_id,
                "status": current_status,
                "totalWaves": len(waves),
                "alreadyFinalized": True,
            }

        # Verify all waves complete (safety check)
        all_complete = all(
            w.get("status", "").upper() in ["COMPLETED", "FAILED", "TERMINATED", "CANCELLED"] for w in waves
        )

        if not all_complete:
            return response(
                400,
                {
                    "error": "WAVES_NOT_COMPLETE",
                    "message": "Cannot finalize - not all waves complete",
                    "executionId": execution_id,
                },
            )

        # Analyze actual wave/server outcomes to determine final status
        outcome = analyze_execution_outcome(waves)
        final_status = outcome["status"]
        summary = outcome["summary"]
        details = outcome["details"]

        print(f"Analyzed outcome for {execution_id}: {final_status}")
        print(f"   Summary: {summary}")

        # Idempotent update with conditional write
        # Only update if status is still POLLING/PAUSED (not already finalized)
        try:
            update_expr = "SET #status = :status, endTime = :time, outcomeSummary = :summary, outcomeDetails = :details"
            expr_values = {
                ":status": final_status,
                ":time": int(time.time()),
                ":polling": "POLLING",
                ":paused": "PAUSED",
                ":summary": summary,
                ":details": details,
            }

            # Add error message for non-COMPLETED statuses
            if final_status != "COMPLETED":
                update_expr += ", errorMessage = :error"
                expr_values[":error"] = summary

            execution_history_table.update_item(
                Key={"executionId": execution_id, "planId": plan_id},
                UpdateExpression=update_expr,
                ConditionExpression="#status IN (:polling, :paused)",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues=expr_values,
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                # Already finalized by another invocation - return success
                print(f"Execution {execution_id} already finalized by concurrent call")
                return {
                    "statusCode": 200,
                    "executionId": execution_id,
                    "status": final_status,
                    "totalWaves": len(waves),
                    "alreadyFinalized": True,
                }
            raise

        print(f"✅ Execution {execution_id} finalized as {final_status}")

        return {
            "statusCode": 200,
            "executionId": execution_id,
            "status": final_status,
            "totalWaves": len(waves),
            "outcomeSummary": summary,
            "outcomeDetails": details,
        }

    except Exception as e:
        print(f"Error finalizing execution: {e}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def handle_pause_operation(event: Dict, context) -> Dict:
    """
    Pause execution via operation-based invocation.

    TRIGGER: Direct invocation or Step Functions

    BEHAVIOR:
    - Changes execution status to PAUSED
    - Records pause reason and timestamp
    - Execution remains paused until resume operation called

    DIRECT INVOCATION:
        aws lambda invoke --function-name execution-handler \\
          --payload '{"operation": "pause", "executionId": "uuid", "reason": "Manual approval"}' \\
          response.json

    RETURNS:
        {
            "statusCode": 200,
            "executionId": "uuid",
            "status": "PAUSED"
        }
    """
    try:
        execution_id = event.get("executionId")
        reason = event.get("reason", "Manual pause")

        if not execution_id:
            return response(
                400,
                {
                    "error": "MISSING_PARAMETERS",
                    "message": "executionId required",
                },
            )

        print(f"Pausing execution {execution_id}: {reason}")

        # Call existing pause_execution function
        result = pause_execution(execution_id, {"reason": reason})
        return result

    except Exception as e:
        print(f"Error pausing execution: {e}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def handle_resume_operation(event: Dict, context) -> Dict:
    """
    Resume paused execution via operation-based invocation.

    TRIGGER: Direct invocation or Step Functions

    BEHAVIOR:
    - Changes execution status from PAUSED to POLLING
    - Resumes Step Functions execution if taskToken provided
    - Execution continues with next wave

    DIRECT INVOCATION:
        aws lambda invoke --function-name execution-handler \\
          --payload '{"operation": "resume", "executionId": "uuid"}' \\
          response.json

    RETURNS:
        {
            "statusCode": 200,
            "executionId": "uuid",
            "status": "POLLING"
        }
    """
    try:
        execution_id = event.get("executionId")

        if not execution_id:
            return response(
                400,
                {
                    "error": "MISSING_PARAMETERS",
                    "message": "executionId required",
                },
            )

        print(f"Resuming execution {execution_id}")

        # Call existing resume_execution function
        result = resume_execution(execution_id)
        return result

    except Exception as e:
        print(f"Error resuming execution: {e}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def lambda_handler(event, context):
    """
    Unified Lambda handler - routes requests based on invocation pattern.

    INVOCATION PATTERNS:

    1. API Gateway (HTTP REST API)
       Routes HTTP requests to appropriate handlers based on method + path.
       Example:
           POST /executions
           GET /executions/{id}
           POST /executions/{id}/cancel

    2. Direct Lambda Invocation - Worker Pattern
       Async background execution of recovery plans.
       Event: {"worker": true, "executionId": "...", "planId": "...", ...}
       Triggered by: execute_recovery_plan() for async processing

    3. Direct Lambda Invocation - Operation Pattern
       Operation-based routing for lifecycle management.
       Event: {"operation": "find|poll|finalize|pause|resume", "executionId": "...", "planId": "..."}

       Operations:
       - "find": Query DynamoDB for POLLING/CANCELLING executions, invoke poll for each
       - "poll": Query DRS job status, enrich with EC2 data, update wave status
       - "finalize": Mark execution COMPLETED (called by Step Functions only)

       Triggered by:
       - EventBridge (find operation, 30s schedule)
       - Self-invocation (poll operation, from find)
       - Step Functions (finalize operation, after all waves complete)

    4. EventBridge Scheduled Trigger
       Periodic polling of active executions.
       Event: {"source": "aws.events", ...}
       Routes to: handle_find_operation()

    ROUTING LOGIC:
       1. Check for worker=true → execute_recovery_plan_worker()
       2. Check for operation field → handle_operation()
       3. Check for source=aws.events → handle_find_operation()
       4. Default: API Gateway routing by httpMethod + path

    RETURNS:
       API Gateway format: {"statusCode": int, "headers": {...}, "body": json}
    """
    try:
        print(f"Event: {json.dumps(event)}")

        # Check if this is a worker invocation (async background task)
        if isinstance(event, dict) and event.get("worker"):
            print("Worker invocation detected - executing recovery plan worker")
            execute_recovery_plan_worker(event)
            return {"statusCode": 200, "body": "Worker completed"}

        # Check if this is an action-based invocation (for orchestration)
        if isinstance(event, dict) and event.get("action"):
            action = event.get("action")
            print(f"Action-based invocation detected: {action}")

            if action == "start_wave_recovery":
                state = event.get("state", {})
                wave_number = event.get("wave_number", 0)
                print(f"DEBUG: start_wave_recovery called with wave_number={wave_number}")
                print(f"DEBUG: state keys before: {list(state.keys())}")
                print(f"DEBUG: state job_id before: {state.get('job_id')}")
                try:
                    start_wave_recovery(state, wave_number)
                    print(f"DEBUG: state job_id after: {state.get('job_id')}")
                    print(f"DEBUG: state region after: {state.get('region')}")
                    print(f"DEBUG: state server_ids after: {state.get('server_ids')}")
                    print(f"DEBUG: state status after: {state.get('status')}")
                except Exception as e:
                    print(f"ERROR in start_wave_recovery: {e}")
                    import traceback

                    traceback.print_exc()
                    state["wave_completed"] = True
                    state["status"] = "failed"
                    state["error"] = str(e)
                return state
            else:
                return response(
                    400,
                    {
                        "error": "UNKNOWN_ACTION",
                        "message": f"Unknown action: {action}",
                        "supportedActions": ["start_wave_recovery"],
                    },
                )

        # Check if this is an operation-based invocation (find, poll, finalize)
        if isinstance(event, dict) and event.get("operation"):
            operation = event.get("operation")
            print(f"Operation-based invocation detected: {operation}")
            return handle_operation(event, context)

        # Check if this is an EventBridge scheduled invocation (polling trigger)
        if isinstance(event, dict) and event.get("source") == "aws.events":
            print("EventBridge scheduled invocation detected - finding executions to poll")
            return handle_find_operation(event, context)

        # API Gateway invocation - route based on HTTP method and path
        http_method = event.get("httpMethod", "")
        path = event.get("path", "")
        path_parameters = event.get("pathParameters") or {}
        query_parameters = event.get("queryStringParameters") or {}

        # Parse body for POST/PUT requests
        body = {}
        if event.get("body"):
            try:
                body = json.loads(event["body"])
            except json.JSONDecodeError:
                return response(400, {"error": "Invalid JSON in request body"})

        # Route to appropriate handler
        if http_method == "POST" and path == "/executions":
            return execute_recovery_plan(body, event)

        elif http_method == "POST" and "/recovery-plans/" in path and path.endswith("/execute"):
            # Support legacy /recovery-plans/{id}/execute endpoint
            plan_id = path_parameters.get("id")
            if not plan_id:
                return response(400, {"error": "Missing plan ID"})
            body["planId"] = plan_id
            return execute_recovery_plan(body, event)

        elif http_method == "GET" and path == "/executions":
            return list_executions(query_parameters)

        # Specific execution sub-routes must come before generic execution details
        elif http_method == "GET" and "/executions/" in path and "/job-logs" in path:
            execution_id = path_parameters.get("id")
            if not execution_id:
                return response(400, {"error": "Missing execution ID"})
            job_id = query_parameters.get("jobId")
            return get_job_log_items(execution_id, job_id)

        elif http_method == "GET" and "/executions/" in path and "/recovery-instances" in path:
            execution_id = path_parameters.get("id")
            if not execution_id:
                return response(400, {"error": "Missing execution ID"})
            return get_recovery_instances(execution_id)

        elif http_method == "GET" and "/executions/" in path:
            execution_id = path_parameters.get("id")
            if not execution_id:
                return response(400, {"error": "Missing execution ID"})
            return get_execution_details(execution_id, query_parameters)

        elif http_method == "POST" and "/executions/" in path and path.endswith("/cancel"):
            execution_id = path_parameters.get("id")
            if not execution_id:
                return response(400, {"error": "Missing execution ID"})
            return cancel_execution(execution_id, body)

        elif http_method == "POST" and "/executions/" in path and path.endswith("/pause"):
            execution_id = path_parameters.get("id")
            if not execution_id:
                return response(400, {"error": "Missing execution ID"})
            return pause_execution(execution_id, body)

        # Batch 2: Instance Management
        elif http_method == "POST" and "/executions/" in path and path.endswith("/resume"):
            execution_id = path_parameters.get("id")
            if not execution_id:
                return response(400, {"error": "Missing execution ID"})
            return resume_execution(execution_id)

        elif http_method == "GET" and "/executions/" in path and "/realtime" in path:
            execution_id = path_parameters.get("id")
            if not execution_id:
                return response(400, {"error": "Missing execution ID"})
            return get_execution_details_realtime(execution_id)

        elif http_method == "POST" and "/executions/" in path and "/terminate-instances" in path:
            execution_id = path_parameters.get("id")
            if not execution_id:
                return response(400, {"error": "Missing execution ID"})
            return terminate_recovery_instances(execution_id)

        elif http_method == "GET" and "/executions/" in path and "/termination-status" in path:
            execution_id = path_parameters.get("id")
            if not execution_id:
                return response(400, {"error": "Missing execution ID"})
            job_ids = query_parameters.get("jobIds", "")
            region = query_parameters.get("region", "us-west-2")
            return get_termination_job_status(execution_id, job_ids, region)

        # Batch 3: Execution Management
        elif http_method == "DELETE" and path == "/executions":
            # Bulk delete by IDs from query params
            execution_ids_str = query_parameters.get("ids", "")
            execution_ids = [id.strip() for id in execution_ids_str.split(",") if id.strip()]
            return delete_executions_by_ids(execution_ids)

        elif http_method == "DELETE" and "/executions/completed" in path:
            return delete_completed_executions()

        else:
            return response(
                404,
                {
                    "error": "NOT_FOUND",
                    "message": f"No handler for {http_method} {path}",
                },
            )

    except Exception as e:
        print(f"Unhandled error in lambda_handler: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": f"Internal server error: {str(e)}"})


def get_execution_details_realtime(execution_id: str) -> Dict:
    """Get real-time execution data - SLOW but current (5-15 seconds)"""
    try:
        # Handle both UUID and ARN formats for backwards compatibility
        if execution_id.startswith("arn:"):
            execution_id = execution_id.split(":")[-1]
            print(f"Extracted UUID from ARN: {execution_id}")

        # Get cached execution first
        result = execution_history_table.query(KeyConditionExpression=Key("executionId").eq(execution_id), Limit=1)

        if "Items" not in result or len(result["Items"]) == 0:
            return response(
                404,
                {
                    "error": "EXECUTION_NOT_FOUND",
                    "message": f"Execution with ID {execution_id} not found",
                    "executionId": execution_id,
                },
            )

        execution = result["Items"][0]

        # Only fetch real-time data for active executions
        if execution.get("status") not in ["RUNNING", "PAUSED"]:
            print(f"Execution {execution_id} is not active, skipping real-time data")
            execution["dataSource"] = "cached"
            execution["lastUpdated"] = execution.get("updatedAt", int(time.time()))
            # Add termination metadata for frontend button visibility
            execution["terminationMetadata"] = can_terminate_execution(execution)
            return response(200, execution)

        print(f"Fetching real-time data for active execution {execution_id}")

        # REAL-TIME DATA: Get current status from Step Functions if still running
        if execution.get("status") == "RUNNING" and execution.get("stateMachineArn"):
            try:
                print("Getting real-time Step Functions status for execution")
                sf_response = stepfunctions.describe_execution(executionArn=execution.get("stateMachineArn"))
                execution["stepFunctionsStatus"] = sf_response["status"]

                # Update DynamoDB if Step Functions shows completion
                if sf_response["status"] in [
                    "SUCCEEDED",
                    "FAILED",
                    "TIMED_OUT",
                    "ABORTED",
                ]:
                    print("Step Functions shows completion, updating DynamoDB")
                    execution_history_table.update_item(
                        Key={
                            "executionId": execution_id,
                            "planId": execution.get("planId"),
                        },
                        UpdateExpression="SET #status = :status, updatedAt = :updated",
                        ExpressionAttributeNames={"#status": "status"},
                        ExpressionAttributeValues={
                            ":status": sf_response["status"],
                            ":updated": int(time.time()),
                        },
                    )
                    execution["status"] = sf_response["status"]

            except Exception as sf_error:
                print(f"Error getting Step Functions status: {sf_error}")

        # REAL-TIME WAVE STATUS: Reconcile wave status with actual DRS job results
        try:
            print("Reconciling wave status with real-time DRS data")
            execution = reconcile_wave_status_with_drs(execution)
        except Exception as reconcile_error:
            print(f"Error reconciling wave status: {reconcile_error}")

        # REAL-TIME SERVER DETAILS: Enrich with current server and recovery instance details
        try:
            print("Enriching with real-time server details")
            execution = enrich_execution_with_server_details(execution)
        except Exception as e:
            print(f"Error enriching execution with server details: {str(e)}")

        # Recalculate overall execution status based on current wave statuses
        try:
            execution = recalculate_execution_status(execution)
        except Exception as recalc_error:
            print(f"Error recalculating execution status: {recalc_error}")

        # Mark as real-time data
        execution["dataSource"] = "realtime"
        execution["lastUpdated"] = int(time.time())

        # Add termination metadata for frontend button visibility
        # Centralized logic prevents frontend/backend inconsistencies
        execution["terminationMetadata"] = can_terminate_execution(execution)

        # CRITICAL FIX: Persist wave status updates to DynamoDB
        # The reconcile_wave_status_with_drs function updates wave status in memory,
        # but we need to persist these updates so termination logic works correctly
        try:
            waves = execution.get("waves", [])
            execution_history_table.update_item(
                Key={
                    "executionId": execution_id,
                    "planId": execution.get("planId"),
                },
                UpdateExpression="SET waves = :waves, updatedAt = :updated",
                ExpressionAttributeValues={
                    ":waves": waves,
                    ":updated": int(time.time()),
                },
            )
            print(f"✅ Persisted wave status updates to DynamoDB for {execution_id}")
        except Exception as persist_error:
            print(f"Error persisting wave updates: {persist_error}")

        return response(200, execution)

    except Exception as e:
        print(f"Error getting execution real-time details: {str(e)}")
        return response(
            500,
            {
                "error": "INTERNAL_ERROR",
                "message": f"Error retrieving real-time execution details: {str(e)}",
                "executionId": execution_id,
            },
        )


def resume_execution(execution_id: str) -> Dict:
    """Resume a paused execution using Step Functions callback pattern.

    Resume is only valid when execution status is PAUSED and has a TaskToken.
    Uses SendTaskSuccess to signal Step Functions to continue from WaitForResume state.

    This function:
    1. Validates the execution is paused
    2. Gets the stored TaskToken from DynamoDB
    3. Calls SendTaskSuccess to resume the Step Functions execution
    """
    print(f"=== RESUME_EXECUTION CALLED === execution_id: {execution_id}")
    print(f"Table name: {EXECUTION_HISTORY_TABLE}")

    try:
        print(f"Querying DynamoDB for execution {execution_id}...")
        result = execution_history_table.query(KeyConditionExpression=Key("executionId").eq(execution_id), Limit=1)
        # Extract safe information for logging
        item_count = len(result.get("Items", []))
        print(f"Query result: Found {item_count} items")

        if not result.get("Items"):
            print(f"No items found for execution {execution_id}")
            return response(
                404,
                {
                    "error": "EXECUTION_NOT_FOUND",
                    "message": f"Execution with ID {execution_id} not found",
                    "executionId": execution_id,
                },
            )

        execution = result["Items"][0]
        plan_id = execution.get("planId")
        current_status = execution.get("status", "")

        # Check if execution is paused
        if current_status != "PAUSED":
            return response(
                400,
                {
                    "error": "Execution is not paused",
                    "currentStatus": current_status,
                    "reason": "Only paused executions can be resumed",
                },
            )

        # Get the stored task token (camelCase per migration standards)
        task_token = execution.get("taskToken")
        if not task_token:
            return response(
                400,
                {
                    "error": "No task token found",
                    "reason": "Execution is paused but has no task token for callback. This may be a legacy execution.",
                },
            )

        # Get paused before wave info
        paused_before_wave = execution.get("pausedBeforeWave", 0)
        # Convert Decimal to int if needed
        if hasattr(paused_before_wave, "__int__"):
            paused_before_wave = int(paused_before_wave)

        print(f"Resuming execution {execution_id} from wave {paused_before_wave} using SendTaskSuccess")

        # Build the full application state that ResumeWavePlan expects
        # This must match the state structure from orchestration_stepfunctions.py
        # CRITICAL: Use execution history waves (with serverStatuses) for completed
        # waves, and plan waves for remaining waves to preserve server data
        try:
            # Get execution history waves (contains serverStatuses for completed)
            exec_waves = execution.get("waves", [])
            exec_waves_data = json.loads(json.dumps(exec_waves, cls=DecimalEncoder))
            print(f"Loaded {len(exec_waves_data)} waves from execution history")

            # Get plan waves for any waves not yet in execution history
            plan_response = recovery_plans_table.get_item(Key={"planId": plan_id})
            plan_waves = plan_response.get("Item", {}).get("waves", [])
            plan_waves_data = json.loads(json.dumps(plan_waves, cls=DecimalEncoder))
            print(f"Loaded {len(plan_waves_data)} waves from recovery plan")

            # Merge: use execution waves (with server data) for completed waves,
            # plan waves for remaining waves
            waves_data = []
            for i, plan_wave in enumerate(plan_waves_data):
                # Check if this wave exists in execution history
                exec_wave = next(
                    (w for w in exec_waves_data if w.get("waveNumber") == i),
                    None,
                )
                if exec_wave and exec_wave.get("serverStatuses"):
                    # Use execution wave (has server data from completed wave)
                    waves_data.append(exec_wave)
                    print(f"Wave {i}: Using execution history " f"({len(exec_wave.get('serverStatuses', []))} servers)")
                else:
                    # Use plan wave (not yet executed)
                    waves_data.append(plan_wave)
                    print(f"Wave {i}: Using plan definition")

            print(f"Final merged waves: {len(waves_data)}")
        except Exception as plan_error:
            print(f"Error loading plan waves: {plan_error}")
            return response(
                500,
                {"error": f"Failed to load recovery plan: {str(plan_error)}"},
            )

        # Get account context from execution record (stored when execution started)
        # This is needed for cross-account DRS operations on resume
        account_context = execution.get("accountContext", {})
        print(f"Account context for resume: {account_context}")

        # Build wave_results from completed waves in execution history
        # This preserves serverStatuses and other data from completed waves
        wave_results = []
        for wave in exec_waves_data:
            wave_status = wave.get("status", "").upper()
            if wave_status in ["COMPLETED", "FAILED"]:
                wave_results.append(wave)
                print(
                    f"Preserving wave_result for wave {wave.get('waveNumber')}: "
                    f"status={wave_status}, servers={len(wave.get('serverStatuses', []))}"
                )

        resume_state = {
            "plan_id": plan_id,
            "execution_id": execution_id,
            "is_drill": execution.get("executionType", "DRILL") == "DRILL",
            "waves": waves_data,
            "current_wave_number": paused_before_wave,
            "all_waves_completed": False,
            "wave_completed": False,
            "current_wave_update_time": 30,
            "current_wave_total_wait_time": 0,
            "current_wave_max_wait_time": 1800,
            "status": "running",
            "wave_results": wave_results,  # Preserve completed wave results
            "job_id": None,
            "region": None,
            "server_ids": [],
            "error": None,
            "paused_before_wave": paused_before_wave,
            "accountContext": account_context,  # camelCase for consistency
        }

        print(f"Resume state: {json.dumps(resume_state, cls=DecimalEncoder)}")

        # Call SendTaskSuccess to resume the Step Functions execution
        # The output becomes the state for ResumeWavePlan (no Payload wrapper for callbacks)
        try:
            stepfunctions.send_task_success(
                taskToken=task_token,
                output=json.dumps(resume_state, cls=DecimalEncoder),
            )
            print(f"✅ SendTaskSuccess called for execution {execution_id}")
        except stepfunctions.exceptions.TaskTimedOut:
            return response(
                400,
                {
                    "error": "Task timed out",
                    "reason": "The Step Functions task has timed out. The execution may need to be restarted.",
                },
            )
        except stepfunctions.exceptions.InvalidToken:
            return response(
                400,
                {
                    "error": "Invalid task token",
                    "reason": "The task token is no longer valid. The execution may have been cancelled or timed out.",
                },
            )
        except Exception as sfn_error:
            print(f"ERROR calling SendTaskSuccess: {str(sfn_error)}")
            return response(
                500,
                {"error": f"Failed to resume Step Functions: {str(sfn_error)}"},
            )

        # Note: The orchestration Lambda (resume_wave action) will update the status to RUNNING
        # and clear the TaskToken when it processes the resume

        wave_display = paused_before_wave + 1  # 0-indexed to 1-indexed for display
        print(f"Resumed execution {execution_id}, wave {wave_display} will start")
        return response(
            200,
            {
                "executionId": execution_id,
                "status": "RESUMING",
                "message": f"Execution resumed - wave {wave_display} will start",
                "nextWave": paused_before_wave,
            },
        )

    except Exception as e:
        print(f"Error resuming execution: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def get_recovery_instances(execution_id: str) -> Dict:
    """Get all recovery instances from an execution for display before termination.

    This finds all recovery instances created by this execution by:
    1. Querying DRS jobs from the execution waves
    2. Getting recovery instance details from DRS
    3. Falling back to querying by source server IDs if needed

    Returns the list of instances without terminating them.
    """
    try:
        # Get execution details
        result = execution_history_table.query(KeyConditionExpression=Key("executionId").eq(execution_id), Limit=1)

        if not result.get("Items"):
            return response(
                404,
                {
                    "error": "EXECUTION_NOT_FOUND",
                    "message": f"Execution with ID {execution_id} not found",
                    "executionId": execution_id,
                },
            )

        execution = result["Items"][0]
        plan_id = execution.get("planId")
        waves = execution.get("waves", [])

        # Get the Recovery Plan to determine account context
        account_context = None
        if plan_id:
            try:
                plan_result = recovery_plans_table.get_item(Key={"planId": plan_id})
                if "Item" in plan_result:
                    plan = plan_result["Item"]
                    account_context = determine_target_account_context(plan)
                    print(f"Using account context for get_recovery_instances: " f"{account_context}")
            except Exception as e:
                print(f"Could not get Recovery Plan {plan_id}: {e}")

        if not waves:
            return response(
                200,
                {
                    "executionId": execution_id,
                    "instances": [],
                    "totalInstances": 0,
                    "message": "No waves found in execution",
                },
            )

        # Collect recovery instances
        instances = []
        source_server_ids_by_region = {}

        print(f"Processing {len(waves)} waves for execution {execution_id}")
        print(
            f"DEBUG: Waves data structure: {[{k: v for k, v in w.items() if k in ['waveNumber', 'waveName', 'status', 'jobId', 'region']} for w in waves]}"  # noqa: E501
        )

        # First pass: collect source server IDs and try to get from DRS jobs
        for wave in waves:
            wave_number = wave.get("waveNumber", 0)
            wave_name = wave.get("waveName", f"Wave {wave_number}")
            job_id = wave.get("jobId")
            region = wave.get("region", "us-east-1")
            wave_status = wave.get("status", "")

            print(f"Wave {wave_number}: status={wave_status}, " f"job_id={job_id}, region={region}")

            # Collect source server IDs from wave
            wave_servers = wave.get("serverStatuses", []) or wave.get("servers", [])
            print(f"DEBUG: Wave {wave_number} has {len(wave_servers)} servers")
            print(f"DEBUG: First server structure: {wave_servers[0] if wave_servers else 'No servers'}")

            for srv in wave_servers:
                srv_id = srv.get("sourceServerId")
                srv_name = srv.get("serverName") or srv.get("hostname", "")
                print(f"DEBUG: Server data: sourceServerId={srv_id}, serverName={srv_name}")
                if srv_id:
                    if region not in source_server_ids_by_region:
                        source_server_ids_by_region[region] = {}
                    source_server_ids_by_region[region][srv_id] = srv_name

            # Try to get from DRS job if available
            if job_id and wave_status in [
                "COMPLETED",
                "LAUNCHED",
                "PARTIAL",
                "STARTED",
                "IN_PROGRESS",
                "RUNNING",
            ]:
                try:
                    drs_client = create_drs_client(region, account_context)
                    job_response = drs_client.describe_jobs(filters={"jobIDs": [job_id]})

                    if job_response.get("items"):
                        job = job_response["items"][0]
                        participating_servers = job.get("participatingServers", [])

                        for server in participating_servers:
                            recovery_instance_id = server.get("recoveryInstanceID")
                            source_server_id = server.get("sourceServerID", "unknown")

                            # Add to source server lookup
                            if source_server_id and source_server_id != "unknown":
                                if region not in source_server_ids_by_region:
                                    source_server_ids_by_region[region] = {}
                                if source_server_id not in source_server_ids_by_region[region]:
                                    source_server_ids_by_region[region][source_server_id] = ""

                            if recovery_instance_id:
                                try:
                                    ri_response = drs_client.describe_recovery_instances(
                                        filters={"recoveryInstanceIDs": [recovery_instance_id]}
                                    )
                                    if ri_response.get("items"):
                                        ri = ri_response["items"][0]
                                        ec2_instance_id = ri.get("ec2InstanceID")
                                        if ec2_instance_id:
                                            # Get server name from lookup
                                            srv_name = source_server_ids_by_region.get(region, {}).get(
                                                source_server_id, ""
                                            )
                                            instances.append(
                                                {
                                                    "instanceId": ec2_instance_id,
                                                    "recoveryInstanceId": recovery_instance_id,
                                                    "sourceServerId": source_server_id,
                                                    "region": region,
                                                    "waveName": wave_name,
                                                    "waveNumber": wave_number,
                                                    "jobId": job_id,
                                                    "status": "LAUNCHED",
                                                    "serverName": srv_name,
                                                }
                                            )
                                except Exception as ri_err:
                                    print(f"Could not get recovery instance " f"{recovery_instance_id}: {ri_err}")

                except Exception as drs_err:
                    print(f"Could not query DRS job {job_id} in {region}: " f"{drs_err}")

        # Alternative: Query by source server IDs if no instances found yet
        if not instances and source_server_ids_by_region:
            print("Trying alternative: query recovery instances by source " "server IDs")

            for region, server_map in source_server_ids_by_region.items():
                source_ids = list(server_map.keys())
                print(f"Querying recovery instances for {len(source_ids)} " f"source servers in {region}")

                try:
                    drs_client = create_drs_client(region, account_context)
                    ri_response = drs_client.describe_recovery_instances(filters={"sourceServerIDs": source_ids})

                    recovery_instances = ri_response.get("items", [])
                    print(f"Found {len(recovery_instances)} recovery instances " f"for source servers in {region}")

                    for ri in recovery_instances:
                        ec2_instance_id = ri.get("ec2InstanceID")
                        recovery_instance_id = ri.get("recoveryInstanceID")
                        source_server_id = ri.get("sourceServerID", "unknown")

                        if ec2_instance_id:
                            srv_name = server_map.get(source_server_id, "")
                            instances.append(
                                {
                                    "instanceId": ec2_instance_id,
                                    "recoveryInstanceId": recovery_instance_id,
                                    "sourceServerId": source_server_id,
                                    "region": region,
                                    "waveName": "Unknown",
                                    "waveNumber": 0,
                                    "jobId": "",
                                    "status": "LAUNCHED",
                                    "serverName": srv_name,
                                }
                            )

                except Exception as e:
                    print(f"Error querying recovery instances in {region}: {e}")

        print(f"Total recovery instances found: {len(instances)}")

        return response(
            200,
            {
                "executionId": execution_id,
                "instances": instances,
                "totalInstances": len(instances),
                "message": (
                    f"Found {len(instances)} recovery instances" if instances else "No recovery instances found"
                ),
            },
        )

    except Exception as e:
        print(f"Error getting recovery instances: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def terminate_recovery_instances(execution_id: str) -> Dict:
    """
    Terminate all recovery instances from a DR execution.

    Discovers and terminates all EC2 instances launched during a DR execution,
    including cross-account scenarios. Queries DRS jobs and recovery instances
    to find all launched instances, then terminates them to clean up after
    DR testing or failed recovery operations.

    ## Use Cases

    ### 1. Cleanup After DR Test
    ```bash
    curl -X POST https://api.example.com/executions/{executionId}/terminate \
      -H "Authorization: Bearer $TOKEN"
    ```

    ### 2. Cleanup Failed Recovery
    ```python
    # Terminate instances from failed execution
    result = terminate_recovery_instances("exec-123")
    print(f"Terminated {result['summary']['terminated']} instances")
    ```

    ### 3. Cross-Account Cleanup
    ```python
    # Automatically uses same account context as original execution
    result = terminate_recovery_instances("exec-456")
    # Terminates instances in target account
    ```

    ## Integration Points

    ### API Gateway Invocation
    ```bash
    curl -X POST https://api.example.com/executions/{executionId}/terminate \
      -H "Authorization: Bearer $TOKEN"
    ```

    ### Direct Lambda Invocation
    ```python
    lambda_client.invoke(
        FunctionName='execution-handler',
        Payload=json.dumps({
            "operation": "terminate_recovery_instances",
            "executionId": "exec-123"
        })
    )
    ```

    ## Behavior

    ### Instance Discovery Process
    1. Query execution record from DynamoDB
    2. Extract DRS job IDs from all waves
    3. Query DRS DescribeJobs for participating servers
    4. Query DRS DescribeRecoveryInstances for EC2 instance IDs
    5. Fallback: Query by source server IDs if job data incomplete
    6. Collect all unique EC2 instance IDs by region

    ### Termination Process
    1. Group instances by region
    2. For each region:
       - Disconnect instances from DRS (if applicable)
       - Terminate EC2 instances
       - Track success/failure per instance
    3. Return summary with terminated/failed counts

    ### Cross-Account Support
    - Retrieves Recovery Plan to determine target account
    - Uses same account context as original execution
    - Assumes cross-account role if needed
    - Falls back to current account if plan not found

    ### Wave Status Filtering
    Only processes waves with these statuses:
    - COMPLETED: Wave finished successfully
    - LAUNCHED: Instances launched
    - PARTIAL: Some servers launched
    - STARTED: Recovery in progress
    - IN_PROGRESS: Recovery in progress
    - RUNNING: Recovery in progress

    Skips waves that never launched (PENDING, FAILED without launch).

    ## Args

    execution_id: Execution ID to terminate instances for

    ## Returns

    Dict with termination results:
        - executionId: Execution ID
        - summary: Counts (total, terminated, failed, skipped)
        - instances: List of instance details with termination status
        - regions: List of regions processed
        - errors: List of errors encountered

    ## Example Response

    ```json
    {
      "executionId": "exec-123",
      "summary": {
        "total": 50,
        "terminated": 48,
        "failed": 2,
        "skipped": 0
      },
      "instances": [
        {
          "instanceId": "i-0abc123",
          "recoveryInstanceId": "ri-xyz789",
          "region": "us-east-1",
          "waveNumber": 0,
          "serverId": "s-1234",
          "status": "terminated"
        },
        {
          "instanceId": "i-0def456",
          "region": "us-east-1",
          "waveNumber": 1,
          "status": "failed",
          "error": "Instance not found"
        }
      ],
      "regions": ["us-east-1", "us-west-2"],
      "errors": []
    }
    ```

    ## Error Handling

    ### Execution Not Found (404)
    ```json
    {
      "error": "EXECUTION_NOT_FOUND",
      "message": "Execution with ID exec-123 not found",
      "executionId": "exec-123"
    }
    ```

    ### No Waves (400)
    ```json
    {
      "error": "No waves found in execution",
      "reason": "This execution has no wave data"
    }
    ```

    ### Partial Failures
    - Non-blocking: Instance failures don't stop termination
    - Continues processing remaining instances
    - Returns detailed error for each failed instance

    ## Performance

    ### Execution Time
    - Small execution (< 20 instances): 10-30 seconds
    - Medium execution (20-100 instances): 30-90 seconds
    - Large execution (100+ instances): 90-180 seconds

    ### API Calls
    - DynamoDB GetItem: 1 call (execution record)
    - DynamoDB GetItem: 1 call (recovery plan, if exists)
    - DRS DescribeJobs: 1 per wave with job ID
    - DRS DescribeRecoveryInstances: 1 per server
    - EC2 TerminateInstances: 1 per region (batch)

    ## Limitations

    ### Instance Discovery
    - Requires DRS job data in execution record
    - May miss instances if job data incomplete
    - Fallback to source server ID query helps

    ### Termination Scope
    - Only terminates instances from this execution
    - Does not affect source instances
    - Does not remove DRS replication

    ## Related Functions

    - `get_execution_history()`: Get execution history for cleanup
    - `finalize_execution()`: Mark execution complete after cleanup

    Terminate all recovery instances from an execution.

    This will:
    1. Find all recovery instances created by this execution (from DRS jobs)
    2. Disconnect them from DRS (if applicable)
    3. Terminate the EC2 instances

    Only works for executions that have launched recovery instances.
    Supports cross-account executions by using the same account context as the original execution.
    """
    try:
        # Get execution details
        result = execution_history_table.query(KeyConditionExpression=Key("executionId").eq(execution_id), Limit=1)

        if not result.get("Items"):
            return response(
                404,
                {
                    "error": "EXECUTION_NOT_FOUND",
                    "message": f"Execution with ID {execution_id} not found",
                    "executionId": execution_id,
                },
            )

        execution = result["Items"][0]
        plan_id = execution.get("planId")
        waves = execution.get("waves", [])

        # Get the Recovery Plan to determine account context (for cross-account support)
        account_context = None
        if plan_id:
            try:
                plan_result = recovery_plans_table.get_item(Key={"planId": plan_id})
                if "Item" in plan_result:
                    plan = plan_result["Item"]
                    account_context = determine_target_account_context(plan)
                    print(f"Using account context for terminate: {account_context}")
                else:
                    print(f"WARNING: Recovery Plan {plan_id} not found, using current account")
            except Exception as e:
                print(f"ERROR: Could not get Recovery Plan {plan_id} for account context: {e}")
                print("Falling back to current account for terminate operation")

        if not waves:
            return response(
                400,
                {
                    "error": "No waves found in execution",
                    "reason": "This execution has no wave data",
                },
            )

        # Collect all recovery instance IDs from all waves
        instances_to_terminate = []
        instances_by_region = {}

        print(f"Processing {len(waves)} waves for execution {execution_id}")

        # Collect source server IDs for alternative lookup
        source_server_ids_by_region = {}

        # First, try to get instance IDs from DRS jobs
        for wave in waves:
            wave_number = wave.get("waveNumber", 0)
            job_id = wave.get("jobId")
            region = wave.get("region", "us-east-1")
            wave_status = wave.get("status", "")

            print(f"Wave {wave_number}: status={wave_status}, job_id={job_id}, region={region}")

            # Collect source server IDs from wave for alternative lookup
            # Check both serverStatuses (current format) and servers (legacy format)
            wave_servers = wave.get("serverStatuses", []) or wave.get("servers", [])
            for srv in wave_servers:
                srv_id = srv.get("sourceServerId")
                if srv_id:
                    if region not in source_server_ids_by_region:
                        source_server_ids_by_region[region] = []
                    if srv_id not in source_server_ids_by_region[region]:
                        source_server_ids_by_region[region].append(srv_id)

            # Only process waves that have a job ID (were actually launched)
            # Include STARTED status since recovery instances may exist even if wave is still in progress
            if job_id and wave_status in [
                "COMPLETED",
                "LAUNCHED",
                "PARTIAL",
                "STARTED",
                "IN_PROGRESS",
                "RUNNING",
            ]:
                try:
                    drs_client = create_drs_client(region, account_context)

                    # Get recovery instances from DRS job
                    job_response = drs_client.describe_jobs(filters={"jobIDs": [job_id]})

                    print(f"DRS describe_jobs response for {job_id}: {len(job_response.get('items', []))} items")

                    if job_response.get("items"):
                        job = job_response["items"][0]
                        participating_servers = job.get("participatingServers", [])

                        print(f"Job {job_id} has {len(participating_servers)} participating servers")

                        for server in participating_servers:
                            recovery_instance_id = server.get("recoveryInstanceID")
                            source_server_id = server.get("sourceServerID", "unknown")

                            print(f"Server {source_server_id}: recoveryInstanceID={recovery_instance_id}")

                            # Collect source server ID for alternative lookup
                            if source_server_id and source_server_id != "unknown":
                                if region not in source_server_ids_by_region:
                                    source_server_ids_by_region[region] = []
                                if source_server_id not in source_server_ids_by_region[region]:
                                    source_server_ids_by_region[region].append(source_server_id)

                            if recovery_instance_id:
                                # Get EC2 instance ID from recovery instance
                                try:
                                    ri_response = drs_client.describe_recovery_instances(
                                        filters={"recoveryInstanceIDs": [recovery_instance_id]}
                                    )
                                    if ri_response.get("items"):
                                        ec2_instance_id = ri_response["items"][0].get("ec2InstanceID")
                                        if ec2_instance_id and ec2_instance_id.startswith("i-"):
                                            instances_to_terminate.append(
                                                {
                                                    "instanceId": ec2_instance_id,
                                                    "recoveryInstanceId": recovery_instance_id,
                                                    "region": region,
                                                    "waveNumber": wave_number,
                                                    "serverId": source_server_id,
                                                    "jobId": job_id,
                                                }
                                            )

                                            if region not in instances_by_region:
                                                instances_by_region[region] = []
                                            instances_by_region[region].append(ec2_instance_id)
                                except Exception as ri_err:
                                    print(
                                        f"Could not get EC2 instance for recovery instance {recovery_instance_id}: {ri_err}"  # noqa: E501
                                    )

                except Exception as drs_err:
                    print(f"Could not query DRS job {job_id} in {region}: {drs_err}")

        # Alternative approach: Query describe_recovery_instances by source server IDs
        # This works even when job's participatingServers doesn't have recoveryInstanceID
        if not instances_to_terminate and source_server_ids_by_region:
            print("Trying alternative approach: query recovery instances by source server IDs")

            for region, source_ids in source_server_ids_by_region.items():
                print(f"Querying recovery instances for {len(source_ids)} source servers in {region}: {source_ids}")

                try:
                    drs_client = create_drs_client(region, account_context)

                    # Query recovery instances by source server IDs
                    ri_response = drs_client.describe_recovery_instances(filters={"sourceServerIDs": source_ids})

                    recovery_instances = ri_response.get("items", [])
                    print(f"Found {len(recovery_instances)} recovery instances for source servers")

                    for ri in recovery_instances:
                        ec2_instance_id = ri.get("ec2InstanceID")
                        recovery_instance_id = ri.get("recoveryInstanceID")
                        source_server_id = ri.get("sourceServerID", "unknown")

                        print(
                            f"Recovery instance: ec2={ec2_instance_id}, ri={recovery_instance_id}, source={source_server_id}"  # noqa: E501
                        )

                        if ec2_instance_id and ec2_instance_id.startswith("i-"):
                            instances_to_terminate.append(
                                {
                                    "instanceId": ec2_instance_id,
                                    "recoveryInstanceId": recovery_instance_id,
                                    "region": region,
                                    "waveNumber": 0,  # Unknown wave
                                    "serverId": source_server_id,
                                }
                            )

                            if region not in instances_by_region:
                                instances_by_region[region] = []
                            if ec2_instance_id not in instances_by_region[region]:
                                instances_by_region[region].append(ec2_instance_id)

                except Exception as e:
                    print(f"Error querying recovery instances by source server IDs in {region}: {e}")

        # Fallback: check stored data in ServerStatuses or Servers
        if not instances_to_terminate:
            for wave in waves:
                wave_number = wave.get("waveNumber", 0)
                region = wave.get("region", "us-east-1")

                # Check ServerStatuses (newer format)
                server_statuses = wave.get("serverStatuses", [])
                for server in server_statuses:
                    instance_id = (
                        server.get("recoveryInstanceId")
                        or server.get("recoveryInstanceId")
                        or server.get("EC2InstanceId")
                        or server.get("ec2InstanceId")
                    )
                    if instance_id and isinstance(instance_id, str) and instance_id.startswith("i-"):
                        instances_to_terminate.append(
                            {
                                "instanceId": instance_id,
                                "region": region,
                                "waveNumber": wave_number,
                                "serverId": server.get("sourceServerId", "unknown"),
                            }
                        )
                        if region not in instances_by_region:
                            instances_by_region[region] = []
                        instances_by_region[region].append(instance_id)

                # Check Servers (older format)
                servers = wave.get("servers", [])
                for server in servers:
                    instance_id = (
                        server.get("RecoveryInstanceId")
                        or server.get("recoveryInstanceId")
                        or server.get("instanceId")
                        or server.get("instanceId")
                        or server.get("ec2InstanceId")
                        or server.get("EC2InstanceId")
                    )
                    if instance_id and isinstance(instance_id, str) and instance_id.startswith("i-"):
                        server_region = server.get("region", region)
                        instances_to_terminate.append(
                            {
                                "instanceId": instance_id,
                                "region": server_region,
                                "waveNumber": wave_number,
                                "serverId": server.get("sourceServerId", "unknown"),
                            }
                        )
                        if server_region not in instances_by_region:
                            instances_by_region[server_region] = []
                        instances_by_region[server_region].append(instance_id)

        if not instances_to_terminate:
            return response(
                200,
                {
                    "executionId": execution_id,
                    "message": "No recovery instances to terminate",
                    "reason": "This execution has no recovery instances to terminate. Instances may not have been launched yet, may have already been terminated, or the execution was cancelled before launch.",  # noqa: E501
                    "terminated": [],
                    "failed": [],
                    "jobs": [],
                    "totalFound": 0,
                    "totalTerminated": 0,
                    "totalFailed": 0,
                    "noInstancesFound": True,
                },
            )

        print(f"Found {len(instances_to_terminate)} recovery instances to terminate")

        # Group recovery instance IDs by region for DRS API call
        recovery_instances_by_region = {}
        for instance_info in instances_to_terminate:
            region = instance_info.get("region", "us-east-1")
            # The recovery instance ID is the same as the EC2 instance ID in DRS
            recovery_instance_id = instance_info.get("recoveryInstanceId") or instance_info.get("instanceId")
            if recovery_instance_id:
                if region not in recovery_instances_by_region:
                    recovery_instances_by_region[region] = []
                if recovery_instance_id not in recovery_instances_by_region[region]:
                    recovery_instances_by_region[region].append(recovery_instance_id)

        # Use DRS TerminateRecoveryInstances API - this properly terminates via DRS
        # and creates a TERMINATE job in DRS console
        terminated = []
        failed = []
        jobs_created = []

        for (
            region,
            recovery_instance_ids,
        ) in recovery_instances_by_region.items():
            try:
                drs_client = create_drs_client(region, account_context)

                print(
                    f"Calling DRS TerminateRecoveryInstances for {len(recovery_instance_ids)} instances in {region}: {recovery_instance_ids}"  # noqa: E501
                )

                # Call DRS TerminateRecoveryInstances API
                # This creates a TERMINATE job and properly cleans up in DRS
                terminate_response = drs_client.terminate_recovery_instances(recoveryInstanceIDs=recovery_instance_ids)

                # Get the job info from response
                job = terminate_response.get("job", {})
                job_id = job.get("jobID")

                if job_id:
                    jobs_created.append(
                        {
                            "jobId": job_id,
                            "region": region,
                            "type": job.get("type", "TERMINATE"),
                            "status": job.get("status", "PENDING"),
                        }
                    )
                    print(f"Created DRS terminate job: {job_id}")

                # Track terminated instances
                for ri_id in recovery_instance_ids:
                    terminated.append(
                        {
                            "recoveryInstanceId": ri_id,
                            "region": region,
                            "jobId": job_id,
                        }
                    )

            except drs_client.exceptions.ConflictException as e:
                # Instances already being terminated or don't exist
                error_msg = str(e)
                print(f"ConflictException terminating recovery instances in {region}: {error_msg}")
                for ri_id in recovery_instance_ids:
                    failed.append(
                        {
                            "recoveryInstanceId": ri_id,
                            "region": region,
                            "error": "Already terminated or being processed",
                            "errorType": "CONFLICT",
                        }
                    )
            except Exception as e:
                error_msg = str(e)
                print(f"Error terminating recovery instances in {region}: {error_msg}")
                for ri_id in recovery_instance_ids:
                    failed.append(
                        {
                            "recoveryInstanceId": ri_id,
                            "region": region,
                            "error": error_msg,
                        }
                    )

        print(f"Terminated {len(terminated)} recovery instances via DRS API")

        # Store termination job IDs for progress tracking
        # Do NOT set instancesTerminated=True yet - wait for jobs to complete
        try:
            plan_id = execution.get("planId")
            print(f"Updating execution {execution_id} with PlanId {plan_id} - storing termination jobs")

            update_response = execution_history_table.update_item(  # noqa: F841
                Key={"executionId": execution_id, "planId": plan_id},
                UpdateExpression="SET terminateJobs = :jobs, terminationInitiatedAt = :timestamp",
                ExpressionAttributeValues={
                    ":jobs": jobs_created,
                    ":timestamp": int(time.time()),
                },
                ReturnValues="ALL_NEW",
            )
            print(f"Successfully updated execution record with {len(jobs_created)} termination jobs")

        except Exception as e:
            print(f"ERROR: Could not update execution with termination jobs: {str(e)}")
            import traceback

            traceback.print_exc()

        # Check if all failures are due to conflict (already terminated)
        all_conflict = len(failed) > 0 and all(f.get("errorType") == "CONFLICT" for f in failed)

        if len(terminated) == 0 and all_conflict:
            # All instances already terminated or being processed
            return response(
                200,
                {
                    "executionId": execution_id,
                    "message": "Recovery instances already terminated or being processed",
                    "terminated": terminated,
                    "failed": failed,
                    "jobs": jobs_created,
                    "totalFound": len(instances_to_terminate),
                    "totalTerminated": len(terminated),
                    "totalFailed": len(failed),
                    "alreadyTerminated": True,
                },
            )

        return response(
            200,
            {
                "executionId": execution_id,
                "message": f"Initiated termination of {len(terminated)} recovery instances via DRS",
                "terminated": terminated,
                "failed": failed,
                "jobs": jobs_created,
                "totalFound": len(instances_to_terminate),
                "totalTerminated": len(terminated),
                "totalFailed": len(failed),
            },
        )

    except Exception as e:
        print(f"Error terminating recovery instances: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def get_termination_job_status(execution_id: str, job_ids_str: str, region: str) -> Dict:
    """Get status of DRS termination jobs for progress tracking.

    Args:
        execution_id: The execution ID
        job_ids_str: Comma-separated list of DRS job IDs
        region: AWS region where DRS jobs are running

    Returns:
        Job status with progress information
    """
    try:
        if not job_ids_str:
            return response(400, {"error": "jobIds parameter required"})

        job_ids = [j.strip() for j in job_ids_str.split(",") if j.strip()]
        if not job_ids:
            return response(400, {"error": "No valid job IDs provided"})

        # Validate DRS job ID format (drsjob- prefix + 17 character UUID)
        valid_job_ids = []
        for job_id in job_ids:
            if job_id.startswith("drsjob-") and len(job_id) >= 24:
                valid_job_ids.append(job_id)
            else:
                print(f"Warning: Invalid job ID format: {job_id} (expected: drsjob-xxxxxxxxxxxxxxxx)")

        if not valid_job_ids:
            return response(
                400,
                {"error": "No valid DRS job IDs provided. Expected format: drsjob-xxxxxxxxxxxxxxxx"},
            )

        print(f"Getting termination job status for {len(valid_job_ids)} jobs in {region}: {valid_job_ids}")

        drs_client = boto3.client("drs", region_name=region)

        jobs_response = drs_client.describe_jobs(filters={"jobIDs": valid_job_ids})

        jobs = jobs_response.get("items", [])
        print(f"Found {len(jobs)} jobs")

        # Calculate overall progress
        total_servers = 0
        completed_servers = 0
        all_completed = True
        any_failed = False
        job_details = []

        for job in jobs:
            job_id = job.get("jobID", "")
            status = job.get("status", "UNKNOWN")
            job_type = job.get("type", "")
            participating = job.get("participatingServers", [])

            print(f"Job {job_id}: status={status}, type={job_type}, servers={len(participating)}")

            job_total = len(participating)
            job_completed = 0
            job_failed = 0

            # DRS clears participatingServers when job completes
            # If job is COMPLETED with empty servers, treat as all completed
            if status == "COMPLETED" and job_total == 0:
                print(f"Job {job_id} COMPLETED with empty participatingServers - job finished successfully")
                # Job completed successfully - all servers terminated
                # Don't add to job_details here, let the final logic handle it
                # The all_completed check will set progress to 100%
                job_details.append(
                    {
                        "jobId": job_id,
                        "status": status,
                        "type": job_type,
                        "totalServers": 0,
                        "completedServers": 0,
                        "failedServers": 0,
                        "jobCompleted": True,
                    }
                )
                continue

            for server in participating:
                launch_status = server.get("launchStatus", "")
                # DRS launchStatus values: PENDING, IN_PROGRESS, LAUNCHED, FAILED, TERMINATED
                # For TERMINATE jobs: TERMINATED = success, FAILED = failure
                if launch_status == "TERMINATED":
                    job_completed += 1
                elif launch_status == "FAILED":
                    job_failed += 1
                    any_failed = True
                # Log for debugging
                print(f"  Server launchStatus: {launch_status}")

            total_servers += job_total
            completed_servers += job_completed

            # Job is complete if status is COMPLETED
            if status not in ["COMPLETED"]:
                all_completed = False

            job_details.append(
                {
                    "jobId": job_id,
                    "status": status,
                    "type": job_type,
                    "totalServers": job_total,
                    "completedServers": job_completed,
                    "failedServers": job_failed,
                }
            )

        # Calculate percentage
        progress_percent = 0
        if total_servers > 0:
            progress_percent = int((completed_servers / total_servers) * 100)

        # If all jobs completed, set to 100%
        # This handles the case where DRS clears participatingServers on completion
        if all_completed or all(j.get("status") == "COMPLETED" for j in jobs):
            progress_percent = 100
            all_completed = True

        result = {
            "executionId": execution_id,
            "jobs": job_details,
            "totalServers": total_servers,
            "completedServers": completed_servers,
            "progressPercent": progress_percent,
            "allCompleted": all_completed,
            "anyFailed": any_failed,
        }

        print(f"Termination progress: {progress_percent}% ({completed_servers}/{total_servers})")

        # Update execution record when termination completes
        if all_completed:
            try:
                exec_result = execution_history_table.query(
                    KeyConditionExpression=Key("executionId").eq(execution_id),
                    Limit=1,
                )
                if exec_result.get("Items"):
                    execution = exec_result["Items"][0]
                    plan_id = execution.get("planId")

                    # Only update if not already set
                    if not execution.get("instancesTerminated"):
                        print(
                            f"All termination jobs completed - setting instancesTerminated=True for execution {execution_id}"  # noqa: E501
                        )
                        execution_history_table.update_item(
                            Key={
                                "executionId": execution_id,
                                "planId": plan_id,
                            },
                            UpdateExpression="SET instancesTerminated = :terminated, instancesTerminatedAt = :timestamp",  # noqa: E501
                            ExpressionAttributeValues={
                                ":terminated": True,
                                ":timestamp": int(time.time()),
                            },
                        )
            except Exception as update_error:
                print(f"Error updating execution with termination completion: {update_error}")

        return response(200, result)

    except Exception as e:
        print(f"Error getting termination job status: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def get_job_log_items(execution_id: str, job_id: str = None) -> Dict:
    """Get DRS job log items for an execution's wave.

    Returns detailed progress events like:
    - SNAPSHOT_START / SNAPSHOT_END
    - CONVERSION_START / CONVERSION_END
    - LAUNCH_START / LAUNCH_END

    Args:
        execution_id: The execution ID
        job_id: Optional specific job ID. If not provided, returns logs for all waves.
    """
    try:
        # Get execution to find job IDs (use query since table has composite key)
        result = execution_history_table.query(KeyConditionExpression=Key("executionId").eq(execution_id), Limit=1)
        if not result.get("Items"):
            return response(
                404,
                {
                    "error": "EXECUTION_NOT_FOUND",
                    "message": f"Execution with ID {execution_id} not found",
                    "executionId": execution_id,
                },
            )

        execution = result["Items"][0]
        waves = execution.get("waves", [])

        # Get account context from execution (region is per-wave)
        account_context = execution.get("accountContext", {})

        all_job_logs = []

        for wave in waves:
            wave_job_id = wave.get("jobId")
            wave_number = wave.get("waveNumber", 0)

            # Get region from wave first, then execution, then default
            wave_region = wave.get("region") or execution.get("region", "us-east-1")

            # Skip if no job ID or if specific job requested and doesn't match
            if not wave_job_id:
                continue
            if job_id and wave_job_id != job_id:
                continue

            try:
                # Create regional DRS client with cross-account support
                # Use wave-specific region since DRS jobs are regional
                drs_client = create_drs_client(wave_region, account_context)

                # Get job log items from DRS
                log_response = drs_client.describe_job_log_items(jobID=wave_job_id)
                log_items = log_response.get("items", [])

                # Transform log items for frontend
                wave_logs = {
                    "waveNumber": wave_number,
                    "jobId": wave_job_id,
                    "events": [],
                }

                for item in log_items:
                    event = {
                        "event": item.get("event", "UNKNOWN"),
                        "eventData": item.get("eventData", {}),
                        "logDateTime": item.get("logDateTime", ""),
                    }

                    # Extract source server info if available
                    event_data = item.get("eventData", {})
                    if "sourceServerID" in event_data:
                        event["sourceServerId"] = event_data["sourceServerID"]
                    if "rawError" in event_data:
                        event["error"] = event_data["rawError"]
                    if "conversionServerID" in event_data:
                        event["conversionServerId"] = event_data["conversionServerID"]

                    wave_logs["events"].append(event)

                # Sort events by timestamp (newest first for display)
                wave_logs["events"].sort(key=lambda x: x.get("logDateTime", ""), reverse=True)

                all_job_logs.append(wave_logs)

            except Exception as e:
                print(f"Error getting job log items for job {wave_job_id}: {e}")
                all_job_logs.append(
                    {
                        "waveNumber": wave_number,
                        "jobId": wave_job_id,
                        "events": [],
                        "error": str(e),
                    }
                )

        return response(200, {"executionId": execution_id, "jobLogs": all_job_logs})

    except Exception as e:
        print(f"Error getting job log items: {str(e)}")
        return response(500, {"error": str(e)})


def apply_launch_config_to_servers(
    server_ids: List[str],
    launch_config: Dict,
    region: str,
    protection_group: Dict = None,
    protection_group_id: str = None,
    protection_group_name: str = None,
) -> Dict:
    """
    Apply launch configuration to all servers' EC2 launch templates and DRS settings.

    Updates both DRS launch configuration and EC2 launch template for each server
    when Protection Group is saved. Ensures recovery instances launch with correct
    network, security, and instance settings.

    Supports per-server configuration overrides via protection_group parameter.
    When protection_group is provided, merges group defaults with server-specific
    overrides using get_effective_launch_config().

    ## Use Cases

    ### 1. Protection Group Configuration
    ```python
    result = apply_launch_config_to_servers(
        server_ids=["s-1234", "s-5678"],
        launch_config={
            "subnetId": "subnet-abc123",
            "securityGroupIds": ["sg-xyz789"],
            "instanceType": "t3.medium",
            "copyPrivateIp": True
        },
        region="us-east-1",
        protection_group_id="pg-123",
        protection_group_name="Production Web Servers"
    )
    # Returns: {"applied": 2, "skipped": 0, "failed": 0, "details": [...]}
    ```

    ### 2. Bulk Server Configuration
    ```python
    # Apply same config to all servers in wave
    result = apply_launch_config_to_servers(
        server_ids=wave_server_ids,
        launch_config=standard_config,
        region="us-east-1"
    )
    ```

    ## Integration Points

    ### Protection Group Save
    Called automatically when Protection Group is saved via API:
    ```bash
    curl -X PUT https://api.example.com/protection-groups/pg-123 \
      -H "Authorization: Bearer $TOKEN" \
      -d '{
        "launchConfig": {
          "subnetId": "subnet-abc123",
          "securityGroupIds": ["sg-xyz789"]
        }
      }'
    ```

    ## Behavior

    ### Two-Phase Update Process
    1. **DRS Launch Configuration Update** (FIRST):
       - Updates copyPrivateIp, copyTags, licensing
       - Updates targetInstanceTypeRightSizingMethod
       - Updates launchDisposition
       - DRS creates new EC2 launch template version

    2. **EC2 Launch Template Update** (SECOND):
       - Updates instance type, subnet, security groups
       - Updates IAM instance profile
       - Adds static private IP if configured
       - Sets version description with tracking info
       - Sets new version as default

    ### Update Order Critical
    DRS update MUST happen first because DRS creates new EC2 template versions.
    If EC2 update happens first, DRS will overwrite it.

    ### Launch Config Fields
    - subnetId: Target subnet for recovery instances
    - securityGroupIds: Security groups for recovery instances
    - instanceType: EC2 instance type
    - instanceProfileName: IAM instance profile
    - staticPrivateIp: Static private IP address (per-server override)
    - copyPrivateIp: Preserve private IP (DRS setting)
    - copyTags: Copy tags to recovery instance (DRS setting)
    - licensing: License configuration (DRS setting)
    - targetInstanceTypeRightSizingMethod: Right-sizing method (DRS setting)
    - launchDisposition: Launch state STARTED/STOPPED (DRS setting)

    ### Version Description Tracking
    EC2 template version description includes:
    - Timestamp (UTC)
    - Protection Group name and ID
    - Configuration details (instance type, subnet, security groups, static IP, etc.)
    - Truncated to 255 characters (EC2 limit)

    ## Args

    server_ids: List of DRS source server IDs
    launch_config: Launch configuration settings (dict)
    region: AWS region
    protection_group: Optional full PG dict with servers array for per-server configs
    protection_group_id: Optional PG ID for version tracking
    protection_group_name: Optional PG name for version tracking

    ## Returns

    Dict with application results:
        - applied: Count of servers successfully updated
        - skipped: Count of servers skipped (no template)
        - failed: Count of servers that failed
        - details: List of per-server results with status

    ## Example Response

    ```json
    {
      "applied": 48,
      "skipped": 2,
      "failed": 0,
      "details": [
        {
          "serverId": "s-1234567890abcdef0",
          "status": "applied",
          "templateId": "lt-0abc123def456789"
        },
        {
          "serverId": "s-abcdef1234567890",
          "status": "skipped",
          "reason": "No EC2 launch template found"
        }
      ]
    }
    ```

    ## Performance

    ### Execution Time
    - Small group (< 10 servers): 5-15 seconds
    - Medium group (10-50 servers): 15-60 seconds
    - Large group (50+ servers): 60-180 seconds

    ### API Calls Per Server
    - DRS GetLaunchConfiguration: 1 call
    - DRS UpdateLaunchConfiguration: 1 call (if DRS settings changed)
    - EC2 CreateLaunchTemplateVersion: 1 call (if EC2 settings changed)
    - EC2 ModifyLaunchTemplate: 1 call (set default version)
    - Total: 2-4 calls per server

    ## Error Handling

    ### Per-Server Errors
    - Non-blocking: Server failures don't stop processing
    - Detailed logging: All errors logged with server context
    - Status tracking: Each server result tracked in details array

    ### Skipped Servers
    Servers without EC2 launch template are skipped (not failed):
    - Common for newly added servers
    - Template created during first recovery
    - Logged as "skipped" not "failed"

    ## Related Functions

    - `get_server_launch_configurations()`: Retrieve current configs
    - `start_drs_recovery_for_wave()`: Launch recovery with configs

    Apply launchConfig to all servers' EC2 launch templates and DRS settings.

    Called immediately when Protection Group is saved.
    Returns summary of results for each server.
    """
    if not launch_config or not server_ids:
        return {"applied": 0, "skipped": 0, "failed": 0, "details": []}

    regional_drs = boto3.client("drs", region_name=region)
    ec2 = boto3.client("ec2", region_name=region)

    results = {"applied": 0, "skipped": 0, "failed": 0, "details": []}

    for server_id in server_ids:
        try:
            # Get effective config (merge group defaults with server overrides)
            if protection_group:
                effective_config = get_effective_launch_config(protection_group, server_id)
            else:
                effective_config = launch_config

            # Get DRS launch configuration to find template ID
            drs_config = regional_drs.get_launch_configuration(sourceServerID=server_id)
            template_id = drs_config.get("ec2LaunchTemplateID")

            if not template_id:
                results["skipped"] += 1
                results["details"].append(
                    {
                        "serverId": server_id,
                        "status": "skipped",
                        "reason": "No EC2 launch template found",
                    }
                )
                continue

            # Build EC2 template data for the new version
            template_data = {}

            if effective_config.get("instanceType"):
                template_data["InstanceType"] = effective_config["instanceType"]

            # Network interface settings (subnet, security groups, static IP)
            if (
                effective_config.get("subnetId")
                or effective_config.get("securityGroupIds")
                or effective_config.get("staticPrivateIp")
            ):
                network_interface = {"DeviceIndex": 0}

                # Static private IP support
                if effective_config.get("staticPrivateIp"):
                    network_interface["PrivateIpAddress"] = effective_config["staticPrivateIp"]

                if effective_config.get("subnetId"):
                    network_interface["SubnetId"] = effective_config["subnetId"]
                if effective_config.get("securityGroupIds"):
                    network_interface["Groups"] = effective_config["securityGroupIds"]
                template_data["NetworkInterfaces"] = [network_interface]

            if effective_config.get("instanceProfileName"):
                template_data["IamInstanceProfile"] = {"Name": effective_config["instanceProfileName"]}

            # IMPORTANT: Update DRS launch configuration FIRST
            # DRS update_launch_configuration creates a new EC2 launch template version,
            # so we must call it before our EC2 template updates to avoid being overwritten
            drs_update = {"sourceServerID": server_id}
            if "copyPrivateIp" in effective_config:
                drs_update["copyPrivateIp"] = effective_config["copyPrivateIp"]
            if "copyTags" in effective_config:
                drs_update["copyTags"] = effective_config["copyTags"]
            if "licensing" in effective_config:
                drs_update["licensing"] = effective_config["licensing"]
            if "targetInstanceTypeRightSizingMethod" in effective_config:
                drs_update["targetInstanceTypeRightSizingMethod"] = effective_config[
                    "targetInstanceTypeRightSizingMethod"
                ]
            if "launchDisposition" in effective_config:
                drs_update["launchDisposition"] = effective_config["launchDisposition"]

            if len(drs_update) > 1:  # More than just sourceServerID
                regional_drs.update_launch_configuration(**drs_update)

            # THEN update EC2 launch template (after DRS, so our changes stick)
            if template_data:
                # Build detailed version description for tracking/reuse
                from datetime import datetime, timezone

                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                desc_parts = [f"DRS Orchestration | {timestamp}"]
                if protection_group_name:
                    desc_parts.append(f"PG: {protection_group_name}")
                if protection_group_id:
                    desc_parts.append(f"ID: {protection_group_id[:8]}")
                # Add config details
                config_details = []
                if effective_config.get("staticPrivateIp"):
                    config_details.append(f"IP:{effective_config['staticPrivateIp']}")
                if effective_config.get("instanceType"):
                    config_details.append(f"Type:{effective_config['instanceType']}")
                if effective_config.get("subnetId"):
                    config_details.append(f"Subnet:{effective_config['subnetId'][-8:]}")
                if effective_config.get("securityGroupIds"):
                    sg_count = len(effective_config["securityGroupIds"])
                    config_details.append(f"SGs:{sg_count}")
                if effective_config.get("instanceProfileName"):
                    profile = effective_config["instanceProfileName"]
                    # Truncate long profile names
                    if len(profile) > 20:
                        profile = profile[:17] + "..."
                    config_details.append(f"Profile:{profile}")
                if effective_config.get("copyPrivateIp"):
                    config_details.append("CopyIP")
                if effective_config.get("copyTags"):
                    config_details.append("Copy Tags")
                if effective_config.get("targetInstanceTypeRightSizingMethod"):
                    config_details.append(f"RightSize:{effective_config['targetInstanceTypeRightSizingMethod']}")
                if effective_config.get("launchDisposition"):
                    config_details.append(f"Launch:{effective_config['launchDisposition']}")
                if config_details:
                    desc_parts.append(" | ".join(config_details))
                # EC2 version description max 255 chars
                version_desc = " | ".join(desc_parts)[:255]

                ec2.create_launch_template_version(
                    LaunchTemplateId=template_id,
                    LaunchTemplateData=template_data,
                    VersionDescription=version_desc,
                )
                ec2.modify_launch_template(LaunchTemplateId=template_id, DefaultVersion="$Latest")

            results["applied"] += 1
            results["details"].append(
                {
                    "serverId": server_id,
                    "status": "applied",
                    "templateId": template_id,
                }
            )

        except Exception as e:
            print(f"Error applying launchConfig to {server_id}: {e}")
            results["failed"] += 1
            results["details"].append({"serverId": server_id, "status": "failed", "error": str(e)})

    return results


def delete_completed_executions() -> Dict:
    """
    Delete all completed executions (terminal states only)

    Safe operation that only removes:
    - COMPLETED executions
    - PARTIAL executions (some servers failed)
    - FAILED executions
    - CANCELLED executions (only if no active DRS jobs)

    Active executions (PENDING, POLLING, INITIATED, LAUNCHING, IN_PROGRESS, RUNNING) are preserved.
    Cancelled executions with active DRS jobs are also preserved to prevent orphaned jobs.
    """
    try:
        print("Starting bulk delete of completed executions")

        # Define terminal states that are safe to delete
        # Only delete truly completed executions, NOT active ones
        terminal_states = [
            "COMPLETED",
            "PARTIAL",
            "FAILED",
            "CANCELLED",
            "TIMEOUT",
        ]
        # Active states to preserve (never delete)
        active_states = [  # noqa: F841
            "PENDING",
            "POLLING",
            "INITIATED",
            "LAUNCHING",
            "STARTED",
            "IN_PROGRESS",
            "RUNNING",
            "PAUSED",
            "CANCELLING",
        ]

        # Scan for all executions
        scan_result = execution_history_table.scan()
        all_executions = scan_result.get("Items", [])

        # Handle pagination if there are more results
        while "LastEvaluatedKey" in scan_result:
            scan_result = execution_history_table.scan(ExclusiveStartKey=scan_result["LastEvaluatedKey"])
            all_executions.extend(scan_result.get("Items", []))

        print(f"Found {len(all_executions)} total executions")

        # Filter to only completed executions
        completed_executions = [ex for ex in all_executions if ex.get("status", "").upper() in terminal_states]

        # For CANCELLED executions, check if they have active DRS jobs
        # This prevents deleting executions that still have running DRS jobs
        safe_to_delete = []
        skipped_with_active_jobs = []

        for ex in completed_executions:
            status = ex.get("status", "").upper()
            if status == "CANCELLED":
                # Check if any wave has an active DRS job
                has_active_job = False
                for wave in ex.get("waves", []):
                    job_id = wave.get("jobId")
                    if job_id:
                        # Get region from wave or default
                        region = wave.get("region", "us-east-1")
                        try:
                            drs_client = create_drs_client(region)
                            job_response = drs_client.describe_jobs(filters={"jobIDs": [job_id]})
                            jobs = job_response.get("items", [])
                            if jobs:
                                job_status = jobs[0].get("status", "")
                                if job_status in ["PENDING", "STARTED"]:
                                    has_active_job = True
                                    print(
                                        f"Execution {ex.get('executionId')} has active DRS job {job_id} (status: {job_status})"  # noqa: E501
                                    )
                                    break
                        except Exception as e:
                            print(f"Error checking DRS job {job_id}: {e}")
                            # If we can't check, be safe and skip
                            has_active_job = True
                            break

                if has_active_job:
                    skipped_with_active_jobs.append(ex.get("executionId"))
                else:
                    safe_to_delete.append(ex)
            else:
                safe_to_delete.append(ex)

        if skipped_with_active_jobs:
            print(
                f"Skipping {len(skipped_with_active_jobs)} cancelled executions with active DRS jobs: {skipped_with_active_jobs}"  # noqa: E501
            )

        print(f"Found {len(safe_to_delete)} executions safe to delete")

        # Delete safe executions (DynamoDB requires ExecutionId + PlanId for delete)
        deleted_count = 0
        failed_deletes = []

        for execution in safe_to_delete:
            execution_id = execution.get("executionId")
            plan_id = execution.get("planId")

            if not execution_id or not plan_id:
                print(f"Skipping execution with missing keys: {execution}")
                continue

            try:
                execution_history_table.delete_item(Key={"executionId": execution_id, "planId": plan_id})
                deleted_count += 1
                print(f"Deleted execution: {execution_id}")
            except Exception as delete_error:
                error_msg = str(delete_error)
                print(f"Failed to delete execution {execution_id}: {error_msg}")
                failed_deletes.append({"executionId": execution_id, "error": error_msg})

        # Build response
        result = {
            "message": "Completed executions cleared successfully",
            "deletedCount": deleted_count,
            "totalScanned": len(all_executions),
            "completedFound": len(completed_executions),
            "safeToDelete": len(safe_to_delete),
            "skippedWithActiveJobs": len(skipped_with_active_jobs),
            "activePreserved": len(all_executions) - len(completed_executions),
        }

        if skipped_with_active_jobs:
            result["skippedExecutionIds"] = skipped_with_active_jobs
            result["warning"] = f"{len(skipped_with_active_jobs)} cancelled execution(s) skipped due to active DRS jobs"

        if failed_deletes:
            result["failedDeletes"] = failed_deletes
            if "warning" in result:
                result["warning"] += f"; {len(failed_deletes)} execution(s) failed to delete"
            else:
                result["warning"] = f"{len(failed_deletes)} execution(s) failed to delete"

        print(
            f"Bulk delete completed: {deleted_count} deleted, {len(skipped_with_active_jobs)} skipped (active jobs), {len(failed_deletes)} failed"  # noqa: E501
        )
        return response(200, result)

    except Exception as e:
        print(f"Error deleting completed executions: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            {
                "error": "DELETE_FAILED",
                "message": f"Failed to delete completed executions: {str(e)}",
            },
        )


def delete_executions_by_ids(execution_ids: List[str]) -> Dict:
    """
    Delete specific executions by their IDs

    Safe operation that only removes terminal state executions:
    - COMPLETED, PARTIAL, FAILED, CANCELLED (without active DRS jobs)

    Active executions are preserved and reported as errors.

    Args:
        execution_ids: List of execution IDs to delete

    Returns:
        Dict with deletion results including counts and any failures
    """
    try:
        print(f"Starting selective delete of {len(execution_ids)} executions")

        if not execution_ids:
            return response(
                400,
                {
                    "error": "MISSING_EXECUTION_IDS",
                    "message": "No execution IDs provided for deletion",
                },
            )

        # Define terminal states that are safe to delete
        terminal_states = [  # noqa: F841
            "COMPLETED",
            "PARTIAL",
            "FAILED",
            "CANCELLED",
            "TIMEOUT",
        ]
        active_states = [
            "PENDING",
            "POLLING",
            "INITIATED",
            "LAUNCHING",
            "STARTED",
            "IN_PROGRESS",
            "RUNNING",
            "PAUSED",
            "CANCELLING",
        ]

        deleted_count = 0
        failed_deletes = []
        active_executions_skipped = []
        not_found = []

        for execution_id in execution_ids:
            try:
                # First, find the execution to get its PlanId and Status
                # We need to scan since we only have ExecutionId
                print(f"Searching for execution: {execution_id}")

                scan_result = execution_history_table.scan(FilterExpression=Attr("executionId").eq(execution_id))

                executions = scan_result.get("Items", [])
                if not executions:
                    not_found.append(execution_id)
                    print(f"Execution {execution_id} not found")
                    continue

                execution = executions[0]
                plan_id = execution.get("planId")
                status = execution.get("status", "").upper()

                # Check if execution is in terminal state
                if status in active_states:
                    active_executions_skipped.append(
                        {
                            "executionId": execution_id,
                            "status": status,
                            "reason": "Execution is still active",
                        }
                    )
                    print(f"Skipping active execution {execution_id} (status: {status})")
                    continue

                # For CANCELLED executions, check if they have active DRS jobs
                if status == "CANCELLED":
                    has_active_job = False
                    for wave in execution.get("waves", []):
                        job_id = wave.get("jobId")
                        if job_id:
                            region = wave.get("region", "us-east-1")
                            try:
                                drs_client = create_drs_client(region)
                                job_response = drs_client.describe_jobs(filters={"jobIDs": [job_id]})
                                jobs = job_response.get("items", [])
                                if jobs:
                                    job_status = jobs[0].get("status", "")
                                    if job_status in ["PENDING", "STARTED"]:
                                        has_active_job = True
                                        print(
                                            f"Execution {execution_id} has active DRS job {job_id} (status: {job_status})"  # noqa: E501
                                        )
                                        break
                            except Exception as e:
                                print(f"Error checking DRS job {job_id}: {e}")
                                has_active_job = True
                                break

                    if has_active_job:
                        active_executions_skipped.append(
                            {
                                "executionId": execution_id,
                                "status": status,
                                "reason": "Has active DRS jobs",
                            }
                        )
                        continue

                # Safe to delete - execution is in terminal state
                if not plan_id:
                    failed_deletes.append(
                        {
                            "executionId": execution_id,
                            "error": "Missing PlanId - cannot delete",
                        }
                    )
                    continue

                # Delete the execution
                execution_history_table.delete_item(Key={"executionId": execution_id, "planId": plan_id})
                deleted_count += 1
                print(f"Deleted execution: {execution_id}")

            except Exception as delete_error:
                error_msg = str(delete_error)
                print(f"Failed to delete execution {execution_id}: {error_msg}")
                failed_deletes.append({"executionId": execution_id, "error": error_msg})

        # Build response
        result = {
            "message": f"Processed {len(execution_ids)} execution deletion requests",
            "deletedCount": deleted_count,
            "totalRequested": len(execution_ids),
            "notFound": len(not_found),
            "activeSkipped": len(active_executions_skipped),
            "failed": len(failed_deletes),
        }

        if not_found:
            result["notFoundIds"] = not_found

        if active_executions_skipped:
            result["activeExecutionsSkipped"] = active_executions_skipped
            result["warning"] = f"{len(active_executions_skipped)} active execution(s) skipped"

        if failed_deletes:
            result["failedDeletes"] = failed_deletes
            if "warning" in result:
                result["warning"] += f"; {len(failed_deletes)} execution(s) failed to delete"
            else:
                result["warning"] = f"{len(failed_deletes)} execution(s) failed to delete"

        print(
            f"Selective delete completed: {deleted_count} deleted, {len(active_executions_skipped)} skipped (active), {len(failed_deletes)} failed, {len(not_found)} not found"  # noqa: E501
        )
        return response(200, result)

    except Exception as e:
        print(f"Error deleting executions by IDs: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            {
                "error": "DELETE_FAILED",
                "message": f"Failed to delete executions: {str(e)}",
            },
        )


# ============================================================================
# DRS Source Servers Handler (AUTOMATIC DISCOVERY)
# ============================================================================


def get_execution_status(execution_id: str) -> Dict:
    """Get current execution status"""
    try:
        # Get from DynamoDB using Query (table has composite key: ExecutionId + PlanId)
        result = execution_history_table.query(KeyConditionExpression=Key("executionId").eq(execution_id), Limit=1)

        if not result.get("Items"):
            return response(
                404,
                {
                    "error": "EXECUTION_NOT_FOUND",
                    "message": f"Execution with ID {execution_id} not found",
                    "executionId": execution_id,
                },
            )

        execution = result["Items"][0]

        # Get current status from Step Functions if still running
        if execution["status"] == "RUNNING":
            try:
                # Build proper Step Functions execution ARN from execution ID
                state_machine_arn = execution.get("stateMachineArn")
                if state_machine_arn:
                    sf_response = stepfunctions.describe_execution(executionArn=state_machine_arn)
                    execution["StepFunctionsStatus"] = sf_response["status"]
            except Exception as e:
                print(f"Error getting Step Functions status: {str(e)}")

        return response(200, execution)

    except Exception as e:
        print(f"Error getting execution status: {str(e)}")
        return response(500, {"error": str(e)})


def get_execution_history(plan_id: str) -> Dict:
    """
    Get execution history for a Recovery Plan.

    Queries all executions for a specific Recovery Plan, sorted by start time
    descending (most recent first). Provides complete execution history for
    audit, troubleshooting, and reporting purposes.

    ## Use Cases

    ### 1. View Plan Execution History
    ```bash
    curl -X GET https://api.example.com/plans/{planId}/executions \
      -H "Authorization: Bearer $TOKEN"
    ```

    ### 2. Audit Trail
    ```python
    history = get_execution_history("plan-123")
    for execution in history['executions']:
        print(f"{execution['startTime']}: {execution['status']}")
    ```

    ### 3. Troubleshooting
    ```python
    # Find recent failures
    history = get_execution_history("plan-123")
    failed = [e for e in history['executions'] if e['status'] == 'FAILED']
    ```

    ## Integration Points

    ### API Gateway Invocation
    ```bash
    curl -X GET https://api.example.com/plans/{planId}/executions \
      -H "Authorization: Bearer $TOKEN"
    ```

    ### Direct Lambda Invocation
    ```python
    lambda_client.invoke(
        FunctionName='execution-handler',
        Payload=json.dumps({
            "operation": "get_execution_history",
            "planId": "plan-123"
        })
    )
    ```

    ## Behavior

    ### Query Process
    1. Query DynamoDB execution table using planIdIndex
    2. Sort by startTime descending (most recent first)
    3. Return all executions for the plan
    4. Include complete execution details

    ### Execution Data Included
    - executionId: Unique execution identifier
    - planId: Recovery Plan ID
    - planName: Recovery Plan name
    - status: Execution status
    - startTime: Execution start timestamp
    - completedTime: Execution completion timestamp (if complete)
    - waves: List of waves with status
    - totalWaves: Total wave count
    - completedWaves: Completed wave count

    ## Args

    plan_id: Recovery Plan ID to get history for

    ## Returns

    Dict with execution history:
        - executions: List of executions (sorted by startTime desc)
        - count: Total execution count

    ## Example Response

    ```json
    {
      "executions": [
        {
          "executionId": "exec-123",
          "planId": "plan-abc",
          "planName": "Production DR Plan",
          "status": "COMPLETED",
          "startTime": 1769370000,
          "completedTime": 1769373600,
          "totalWaves": 3,
          "completedWaves": 3,
          "waves": [
            {
              "waveNumber": 0,
              "waveName": "Database Wave",
              "status": "COMPLETED"
            }
          ]
        },
        {
          "executionId": "exec-456",
          "planId": "plan-abc",
          "planName": "Production DR Plan",
          "status": "FAILED",
          "startTime": 1769280000,
          "totalWaves": 3,
          "completedWaves": 1
        }
      ],
      "count": 2
    }
    ```

    ## Performance

    ### Execution Time
    - Small history (< 10 executions): < 1 second
    - Medium history (10-100 executions): 1-3 seconds
    - Large history (100+ executions): 3-10 seconds

    ### API Calls
    - DynamoDB Query: 1 call (using planIdIndex, paginated)

    ## Error Handling

    ### Query Failure (500)
    ```json
    {
      "error": "DynamoDB query failed: ..."
    }
    ```

    ## Sorting

    Results sorted by startTime descending:
    - Most recent executions first
    - Oldest executions last
    - Useful for viewing recent activity

    ## Related Functions

    - `get_execution()`: Get single execution details
    - `list_executions()`: List all executions (not filtered by plan)
    - `terminate_recovery_instances()`: Cleanup execution instances

    Get execution history for a Recovery Plan
    """
    try:
        result = execution_history_table.query(
            IndexName="planIdIndex",
            KeyConditionExpression=Key("planId").eq(plan_id),
            ScanIndexForward=False,  # Sort by StartTime descending
        )

        executions = result.get("Items", [])

        return response(200, {"executions": executions, "count": len(executions)})

    except Exception as e:
        print(f"Error getting execution history: {str(e)}")
        return response(500, {"error": str(e)})


def get_server_details_map(server_ids: List[str], region: str = "us-east-1") -> Dict[str, Dict]:
    """
    Get DRS source server details for a list of server IDs.
    PERFORMANCE OPTIMIZED: Faster API calls and better error handling.
    Returns a map of serverId -> {hostname, name, region, sourceInstanceId, sourceAccountId, ...}
    """
    server_map = {}
    if not server_ids:
        return server_map

    print(f"DEBUG: Getting server details for {len(server_ids)} servers in {region}")

    try:
        # Use regional DRS client
        drs_client = boto3.client("drs", region_name=region)

        # PERFORMANCE OPTIMIZATION: Use filters if possible to reduce data transfer
        # Get source servers (DRS API doesn't support filtering by ID list, so get all and filter)
        paginator = drs_client.get_paginator("describe_source_servers")

        servers_found = 0
        for page in paginator.paginate():
            for server in page.get("items", []):
                source_id = server.get("sourceServerID")
                if source_id in server_ids:
                    servers_found += 1

                    # Extract hostname and source instance ID from sourceProperties
                    source_props = server.get("sourceProperties", {})
                    hostname = source_props.get("identificationHints", {}).get("hostname", "")

                    # Get source EC2 instance ID (the original instance being replicated)
                    source_instance_id = source_props.get("identificationHints", {}).get("awsInstanceID", "")

                    # Get Name tag if available
                    tags = server.get("tags", {})
                    name_tag = tags.get("Name", "")

                    # Get source account ID from staging area info or ARN
                    source_account_id = ""
                    staging_area = server.get("stagingArea", {})
                    if staging_area:
                        source_account_id = staging_area.get("stagingAccountID", "")

                    # Fallback: extract from ARN if available
                    if not source_account_id:
                        arn = server.get("arn", "")
                        if arn:
                            # ARN format: arn:aws:drs:region:account:source-server/id
                            arn_parts = arn.split(":")
                            if len(arn_parts) >= 5:
                                source_account_id = arn_parts[4]

                    # Extract source IP from network interfaces
                    network_interfaces = source_props.get("networkInterfaces", [])
                    source_ip = ""
                    if network_interfaces:
                        # Get first private IP from first interface
                        first_iface = network_interfaces[0]
                        ips = first_iface.get("ips", [])
                        if ips:
                            source_ip = ips[0]

                    # Extract source region from replication info
                    source_region = region  # Default to current region
                    data_rep_info = server.get("dataReplicationInfo", {})

                    server_map[source_id] = {
                        "hostname": hostname or f"server-{source_id[-8:]}",
                        "nameTag": name_tag,  # Updated from EC2 if available
                        "region": region,
                        "sourceInstanceId": source_instance_id,
                        "sourceAccountId": source_account_id,
                        "sourceIp": source_ip,
                        "sourceRegion": source_region,
                        "replicationState": data_rep_info.get("dataReplicationState", "UNKNOWN"),
                        "lastLaunchResult": server.get("lastLaunchResult", "NOT_STARTED"),
                    }

        print(f"DEBUG: Found {servers_found} servers out of {len(server_ids)} requested")

        # PERFORMANCE OPTIMIZATION: Only fetch EC2 tags if we have source instance IDs
        # and only if we don't already have good name tags from DRS
        source_instance_ids = []
        for source_id, details in server_map.items():
            if details.get("sourceInstanceId") and not details.get("nameTag"):
                source_instance_ids.append(details["sourceInstanceId"])

        if source_instance_ids:
            try:
                print(f"DEBUG: Fetching EC2 Name tags for {len(source_instance_ids)} instances")
                ec2_client = boto3.client("ec2", region_name=region)

                # PERFORMANCE: Batch EC2 describe calls (max 1000 instances per call)
                batch_size = 200  # Conservative batch size
                for i in range(0, len(source_instance_ids), batch_size):
                    batch_ids = source_instance_ids[i : i + batch_size]

                    try:
                        ec2_response = ec2_client.describe_instances(InstanceIds=batch_ids)
                        ec2_name_tags = {}

                        for reservation in ec2_response.get("Reservations", []):
                            for instance in reservation.get("Instances", []):
                                instance_id = instance.get("instanceId", "")
                                for tag in instance.get("Tags", []):
                                    if tag.get("Key") == "Name":
                                        ec2_name_tags[instance_id] = tag.get("Value", "")
                                        break

                        # Update server_map with EC2 Name tags
                        for source_id, details in server_map.items():
                            instance_id = details.get("sourceInstanceId")
                            if instance_id and instance_id in ec2_name_tags:
                                details["nameTag"] = ec2_name_tags[instance_id]

                    except Exception as batch_error:
                        print(f"Error fetching EC2 tags for batch: {batch_error}")
                        # Continue with next batch

            except Exception as ec2_error:
                print(f"Error setting up EC2 Name tag fetch: {ec2_error}")

    except Exception as e:
        print(f"Error getting server details from DRS: {e}")
        # Return partial results if we have any
        if not server_map:
            # Create minimal fallback entries for all requested servers
            for server_id in server_ids:
                server_map[server_id] = {
                    "hostname": f"server-{server_id[-8:]}",
                    "nameTag": "",
                    "region": region,
                    "sourceInstanceId": "",
                    "sourceAccountId": "",
                    "sourceIp": "",
                    "sourceRegion": region,
                    "replicationState": "UNKNOWN",
                    "lastLaunchResult": "UNKNOWN",
                }

    print(f"DEBUG: Returning server details for {len(server_map)} servers")
    return server_map


def get_recovery_instances_for_wave(wave: Dict, server_ids: List[str]) -> Dict[str, Dict]:
    """
    Get recovery instance details for servers in a wave.
    PERFORMANCE OPTIMIZED: Faster API calls while maintaining real-time accuracy.
    Returns a map of sourceServerId -> {ec2InstanceID, instanceType, privateIp, ec2State}
    """
    recovery_map = {}
    job_id = wave.get("jobId")
    region = wave.get("region", "us-east-1")

    if not job_id or not server_ids:
        return recovery_map

    print(
        f"DEBUG: Getting recovery instances for wave {wave.get('waveName', 'Unknown')} with {len(server_ids)} servers"
    )

    try:
        drs_client = boto3.client("drs", region_name=region)

        # PERFORMANCE OPTIMIZATION: Get recovery instances with better error handling
        try:
            ri_response = drs_client.describe_recovery_instances(filters={"sourceServerIDs": server_ids})
            recovery_instances = ri_response.get("items", [])
            print(f"DEBUG: Found {len(recovery_instances)} recovery instances")
        except Exception as ri_error:
            print(f"Warning: Could not get recovery instances: {ri_error}")
            return recovery_map

        # REAL-TIME DATA: Get current EC2 instance details for accurate status
        instance_ids = []
        instance_to_source_map = {}

        for ri in recovery_instances:
            source_server_id = ri.get("sourceServerID")
            ec2_instance_id = ri.get("ec2InstanceID")

            if ec2_instance_id and source_server_id:
                instance_ids.append(ec2_instance_id)
                instance_to_source_map[ec2_instance_id] = source_server_id

                # Store basic recovery instance info
                recovery_map[source_server_id] = {
                    "ec2InstanceID": ec2_instance_id,
                    "instanceType": ri.get("instanceType", ""),
                    "privateIp": "",  # Updated from EC2 describe call
                    "ec2State": "unknown",  # Updated from EC2 describe call
                    "launchTime": ri.get("launchTime", ""),
                }

        # REAL-TIME EC2 DATA: Get current instance states and details
        if instance_ids:
            try:
                print(f"DEBUG: Getting real-time EC2 details for {len(instance_ids)} instances")
                ec2_client = boto3.client("ec2", region_name=region)

                # PERFORMANCE: Batch EC2 calls for better efficiency
                batch_size = 100  # EC2 describe_instances supports up to 1000
                for i in range(0, len(instance_ids), batch_size):
                    batch_ids = instance_ids[i : i + batch_size]

                    try:
                        ec2_response = ec2_client.describe_instances(InstanceIds=batch_ids)

                        for reservation in ec2_response.get("Reservations", []):
                            for instance in reservation.get("Instances", []):
                                instance_id = instance.get("instanceId", "")
                                source_server_id = instance_to_source_map.get(instance_id)

                                if source_server_id and source_server_id in recovery_map:
                                    # Update with REAL-TIME EC2 data
                                    recovery_map[source_server_id].update(
                                        {
                                            "ec2State": instance.get("State", {}).get("Name", "unknown"),
                                            "privateIp": instance.get("PrivateIpAddress", ""),
                                            "publicIp": instance.get("PublicIpAddress", ""),
                                            "instanceType": instance.get("InstanceType", ""),  # AWS API uses PascalCase
                                            "availabilityZone": instance.get("Placement", {}).get(
                                                "AvailabilityZone", ""
                                            ),
                                            "launchTime": (
                                                instance.get("LaunchTime", "").isoformat()
                                                if instance.get("LaunchTime")
                                                else ""
                                            ),  # AWS API uses PascalCase
                                            "platform": instance.get("Platform", "linux"),
                                            "architecture": instance.get("Architecture", ""),
                                            "hypervisor": instance.get("Hypervisor", ""),
                                            "virtualizationType": instance.get("VirtualizationType", ""),
                                        }
                                    )

                    except Exception as batch_error:
                        print(f"Error getting EC2 details for batch: {batch_error}")
                        # Continue with next batch - don't fail entire operation

            except Exception as ec2_error:
                print(f"Error setting up EC2 details fetch: {ec2_error}")

    except Exception as e:
        print(f"Error getting recovery instances for wave: {e}")

    print(f"DEBUG: Returning recovery details for {len(recovery_map)} instances")
    return recovery_map


def enrich_execution_with_server_details(execution: Dict) -> Dict:
    """
    Enrich execution waves with server details (hostname, name tag, region).
    PERFORMANCE OPTIMIZED: Maintain full functionality while improving speed.
    """
    waves = execution.get("waves", [])
    if not waves:
        return execution

    # PERFORMANCE: Quick check if already enriched (avoid duplicate work)
    if waves and waves[0].get("enrichedServers"):
        print("DEBUG: Execution already enriched, skipping duplicate enrichment")
        return execution

    # Collect all server IDs and regions from waves
    all_server_ids = set()
    regions = set()
    for wave in waves:
        server_ids = wave.get("serverIds", [])
        all_server_ids.update(server_ids)
        region = wave.get("region", "us-east-1")
        regions.add(region)

    if not all_server_ids:
        return execution

    print(f"DEBUG: Enriching execution with {len(all_server_ids)} servers across {len(regions)} regions")

    # PERFORMANCE OPTIMIZATION: Batch server details lookup by region
    server_details_map = {}
    for region in regions:
        try:
            print(f"DEBUG: Getting server details for region {region}")
            region_servers = get_server_details_map(list(all_server_ids), region)
            server_details_map.update(region_servers)
            print(f"DEBUG: Retrieved {len(region_servers)} server details for {region}")
        except Exception as e:
            print(f"Error getting server details for region {region}: {e}")
            # Continue with other regions - don't fail entire enrichment

    # PERFORMANCE OPTIMIZATION: Process waves in parallel-friendly way
    for wave_idx, wave in enumerate(waves):
        server_ids = wave.get("serverIds", [])
        region = wave.get("region", "us-east-1")
        wave_name = wave.get("waveName", f"Wave-{wave_idx}")

        print(f"DEBUG: Processing wave {wave_name} with {len(server_ids)} servers")

        # PERFORMANCE FIX: Skip expensive AWS API calls for list function
        # Real-time data available via /executions/{id}/realtime endpoint
        recovery_instances = {}
        print(f"DEBUG: Wave {wave_name} - using cached data only for performance")

        # Build enriched server list with full functionality
        enriched_servers = []
        for server_id in server_ids:
            details = server_details_map.get(server_id, {})
            recovery_info = recovery_instances.get(server_id, {})

            # Create enriched server entry with all available data
            enriched_server = {
                "sourceServerId": server_id,
                "Hostname": details.get("hostname", f"server-{server_id[-8:]}"),  # Fallback hostname
                "NameTag": details.get("nameTag", ""),
                "region": region,
                "SourceInstanceId": details.get("sourceInstanceId", ""),
                "SourceAccountId": details.get("sourceAccountId", ""),
                "SourceIp": details.get("sourceIp", ""),
                "SourceRegion": details.get("sourceRegion", region),
                "ReplicationState": details.get("replicationState", "UNKNOWN"),
                # Recovery instance details - maintain full functionality
                "RecoveryInstanceId": recovery_info.get("ec2InstanceID", ""),
                "instanceType": recovery_info.get("instanceType", ""),
                "privateIp": recovery_info.get("privateIp", ""),
                "ec2State": recovery_info.get("ec2State", ""),
                "launchTime": recovery_info.get("launchTime", ""),
            }

            enriched_servers.append(enriched_server)

        # Add enriched servers to wave
        wave["enrichedServers"] = enriched_servers
        print(f"DEBUG: Wave {wave_name} enriched with {len(enriched_servers)} servers")

    print(f"DEBUG: Execution enrichment completed for {len(waves)} waves")
    return execution


def reconcile_wave_status_with_drs(execution: Dict) -> Dict:
    """
    Reconcile wave status with actual DRS job results - REAL-TIME DATA.

    This ensures our UI shows the exact same status as the AWS Management Console
    by querying DRS directly for current job status.
    """
    try:
        waves = execution.get("waves", [])
        updated_waves = []

        print(f"DEBUG: Reconciling {len(waves)} waves with real-time DRS data")

        for wave in waves:
            wave_status = wave.get("status", "")
            job_id = wave.get("jobId")
            wave_name = wave.get("waveName", "Unknown")

            # REAL-TIME CHECK: Always check DRS for jobs that might have status updates
            # This ensures we match AWS Console exactly
            if job_id:
                try:
                    print(f"DEBUG: Checking real-time DRS status for wave {wave_name}, job {job_id}")

                    # Query DRS for actual job status - REAL-TIME
                    region = wave.get("region", "us-east-1")
                    drs_client = boto3.client("drs", region_name=region)

                    response = drs_client.describe_jobs(filters={"jobIDs": [job_id]})

                    if response.get("items"):
                        job = response["items"][0]
                        drs_status = job.get("status", "UNKNOWN")
                        participating_servers = job.get("participatingServers", [])

                        print(f"DEBUG: DRS job {job_id} real-time status: {drs_status} (was: {wave_status})")

                        # Update wave status based on REAL-TIME DRS job results
                        if drs_status == "COMPLETED":
                            # Check if all servers launched successfully
                            all_launched = all(
                                server.get("launchStatus") == "LAUNCHED" for server in participating_servers
                            )

                            if all_launched:
                                if wave_status != "COMPLETED":
                                    print(
                                        f"DEBUG: Wave {wave_name} updated from {wave_status} to COMPLETED (real-time)"
                                    )
                                wave["status"] = "COMPLETED"
                                wave["endTime"] = int(time.time())
                            else:
                                failed_servers = [
                                    server.get("sourceServerID", "unknown")
                                    for server in participating_servers
                                    if server.get("launchStatus") != "LAUNCHED"
                                ]
                                if wave_status != "FAILED":
                                    print(
                                        f"DEBUG: Wave {wave_name} updated from {wave_status} to FAILED - servers failed: {failed_servers}"  # noqa: E501
                                    )
                                wave["status"] = "FAILED"
                                wave["statusMessage"] = f"Servers failed to launch: {', '.join(failed_servers[:3])}"
                                wave["endTime"] = int(time.time())

                        elif drs_status == "FAILED":
                            if wave_status != "FAILED":
                                print(f"DEBUG: Wave {wave_name} updated from {wave_status} to FAILED (DRS job failed)")
                            wave["status"] = "FAILED"
                            wave["statusMessage"] = job.get("statusMessage", "DRS job failed")
                            wave["endTime"] = int(time.time())

                        elif drs_status in ["PENDING", "STARTED"]:
                            if wave_status in [
                                "UNKNOWN",
                                "",
                                "INITIATED",
                                "POLLING",
                            ]:
                                print(
                                    f"DEBUG: Wave {wave_name} updated from {wave_status} to IN_PROGRESS (DRS job active)"  # noqa: E501
                                )
                                wave["status"] = "IN_PROGRESS"

                        # Add real-time job details for frontend display
                        wave["DRSJobDetails"] = {
                            "status": drs_status,
                            "statusMessage": job.get("statusMessage", ""),
                            "creationDateTime": job.get("creationDateTime", ""),
                            "endDateTime": job.get("endDateTime", ""),
                            "participatingServers": len(participating_servers),
                            "launchedServers": len(
                                [s for s in participating_servers if s.get("launchStatus") == "LAUNCHED"]
                            ),
                        }

                        # CRITICAL FIX: Map participatingServers to servers field for frontend
                        # Frontend expects wave.servers or wave.serverExecutions for expandable server details
                        print(
                            f"DEBUG: Mapping {len(participating_servers)} participatingServers to wave.servers for {wave_name}"  # noqa: E501
                        )
                        wave["servers"] = []
                        source_server_ids = []
                        for server in participating_servers:
                            source_server_id = server.get("sourceServerID", "")
                            source_server_ids.append(source_server_id)

                        # CRITICAL: Look up source server details to get Name tags
                        # DRS participatingServers only has sourceServerID and launchStatus
                        source_server_details = {}
                        if source_server_ids:
                            try:
                                source_server_details = get_server_details_map(source_server_ids, region)
                                print(f"DEBUG: Got details for {len(source_server_details)} source servers")
                            except Exception as ss_error:
                                print(f"WARNING: Could not get source server details: {ss_error}")

                        # Build server data with Name tags from source server lookup
                        for server in participating_servers:
                            source_server_id = server.get("sourceServerID", "")
                            ss_details = source_server_details.get(source_server_id, {})

                            # Use Name tag from source server, fallback to hostname
                            server_name = (
                                ss_details.get("nameTag")
                                or ss_details.get("hostname")
                                or server.get("hostname", "")
                                or f"Server {source_server_id[-8:]}"
                            )

                            server_data = {
                                "sourceServerId": source_server_id,
                                "serverId": source_server_id,
                                "hostname": ss_details.get("hostname", ""),
                                "serverName": server_name,
                                "nameTag": ss_details.get("nameTag", ""),
                                "status": server.get("launchStatus", "pending"),
                                "launchStatus": server.get("launchStatus", "pending"),
                                "recoveredInstanceId": server.get("recoveryInstanceID", ""),
                                "instanceId": server.get("recoveryInstanceID", ""),
                                "ec2InstanceId": server.get("recoveryInstanceID", ""),
                                "region": region,
                                "sourceInstanceId": ss_details.get("sourceInstanceId", ""),
                                "sourceAccountId": ss_details.get("sourceAccountId", ""),
                                "sourceIp": ss_details.get("sourceIp", ""),
                                "replicationState": ss_details.get("replicationState", ""),
                                "launchTime": server.get("launchTime", ""),
                            }
                            print(
                                f"DEBUG: Server {source_server_id}: name={server_name}, recoveryInstanceID={server_data['recoveredInstanceId']}, launchStatus={server_data['launchStatus']}"  # noqa: E501
                            )
                            wave["servers"].append(server_data)

                        # CRITICAL FIX: Query recovery instances separately
                        # DRS clears recoveryInstanceID from participatingServers after job completes
                        # We need to query describe_recovery_instances to get the actual recovery instance details
                        print(
                            f"DEBUG: Checking if should query recovery instances: source_server_ids={len(source_server_ids)}, drs_status={drs_status}"  # noqa: E501
                        )
                        if source_server_ids and drs_status == "COMPLETED":
                            try:
                                print(
                                    f"DEBUG: Querying recovery instances for {len(source_server_ids)} source servers in {region}"  # noqa: E501
                                )
                                ri_response = drs_client.describe_recovery_instances(
                                    filters={"sourceServerIDs": source_server_ids}
                                )
                                recovery_instances = ri_response.get("items", [])
                                print(f"DEBUG: Found {len(recovery_instances)} recovery instances")

                                # Query EC2 for instance details (instance type, state, etc.)
                                ec2_instance_ids = [
                                    ri.get("ec2InstanceID") for ri in recovery_instances if ri.get("ec2InstanceID")
                                ]
                                ec2_instance_map = {}

                                if ec2_instance_ids:
                                    try:
                                        ec2_client = boto3.client("ec2", region_name=region)
                                        ec2_response = ec2_client.describe_instances(InstanceIds=ec2_instance_ids)

                                        # Build map of instance ID to instance details
                                        for reservation in ec2_response.get("Reservations", []):
                                            for instance in reservation.get("Instances", []):
                                                instance_id = instance.get("InstanceId")
                                                launch_time = instance.get("LaunchTime")
                                                # Convert datetime to ISO string for JSON serialization
                                                if launch_time:
                                                    launch_time = launch_time.isoformat()

                                                ec2_instance_map[instance_id] = {
                                                    "instanceType": instance.get("InstanceType", ""),
                                                    "state": instance.get("State", {}).get("Name", ""),
                                                    "launchTime": launch_time or "",
                                                }
                                        print(f"DEBUG: Queried EC2 for {len(ec2_instance_map)} instances")
                                    except Exception as ec2_error:
                                        print(f"ERROR: Failed to query EC2 instances: {ec2_error}")

                                # Map recovery instance data back to servers
                                for ri in recovery_instances:
                                    source_server_id = ri.get("sourceServerID", "")
                                    ec2_instance_id = ri.get("ec2InstanceID", "")
                                    ec2_details = ec2_instance_map.get(ec2_instance_id, {})

                                    # Find matching server in wave.servers
                                    for server in wave["servers"]:
                                        if server["sourceServerId"] == source_server_id:
                                            # Update with recovery instance details
                                            server["recoveredInstanceId"] = ec2_instance_id
                                            server["instanceId"] = ec2_instance_id
                                            server["ec2InstanceId"] = ec2_instance_id
                                            server["instanceType"] = ec2_details.get("instanceType", "")
                                            server["privateIp"] = (
                                                ri.get(
                                                    "recoveryInstanceProperties",
                                                    {},
                                                )
                                                .get("networkInterfaces", [{}])[0]
                                                .get("ips", [""])[0]
                                            )
                                            server["launchTime"] = ec2_details.get(
                                                "launchTime",
                                                ri.get(
                                                    "pointInTimeSnapshotDateTime",
                                                    "",
                                                ),
                                            )
                                            print(
                                                f"DEBUG: Enriched {source_server_id}: instanceId={server['instanceId']}, type={server['instanceType']}, ip={server['privateIp']}"  # noqa: E501
                                            )
                                            break
                            except Exception as ri_error:
                                print(f"ERROR: Failed to query recovery instances for {wave_name}: {ri_error}")

                    else:
                        print(f"DEBUG: DRS job {job_id} not found - may have been cleaned up")
                        if wave_status in [
                            "UNKNOWN",
                            "",
                            "INITIATED",
                            "POLLING",
                            "IN_PROGRESS",
                        ]:
                            wave["status"] = "COMPLETED"  # Assume completed if job not found
                            wave["statusMessage"] = "Job completed (not found in DRS)"
                            wave["endTime"] = int(time.time())

                except Exception as e:
                    print(f"Error getting real-time DRS status for wave {wave_name}, job {job_id}: {e}")
                    # Keep original wave status on error - don't break the UI

            # CRITICAL: Frontend expects serverExecutions field, not servers
            # Map servers array to serverExecutions for frontend compatibility
            if "servers" in wave:
                wave["serverExecutions"] = wave["servers"]
                print(f"DEBUG: Mapped {len(wave['servers'])} servers to serverExecutions for wave {wave_name}")

            updated_waves.append(wave)

        execution["waves"] = updated_waves
        print(f"DEBUG: Wave reconciliation completed - {len(updated_waves)} waves processed")
        return execution

    except Exception as e:
        print(f"Error in reconcile_wave_status_with_drs: {e}")
        return execution


def recalculate_execution_status(execution: Dict) -> Dict:
    """
    Recalculate overall execution status based on current wave statuses.
    This ensures the execution status accurately reflects the state of individual waves.
    """
    waves = execution.get("waves", [])
    if not waves:
        return execution

    # CRITICAL FIX: Preserve PAUSED status - don't recalculate for paused executions
    current_status = execution.get("status", "").upper()
    if current_status == "PAUSED":
        # Execution is paused - don't recalculate status based on waves
        # The pause state is managed by Step Functions orchestration
        return execution

    # Count waves by status
    active_statuses = [
        "PENDING",
        "POLLING",
        "INITIATED",
        "LAUNCHING",
        "STARTED",
        "IN_PROGRESS",
        "RUNNING",
        "CONVERTING",
    ]

    active_waves = []
    completed_waves = []
    failed_waves = []
    cancelled_waves = []

    for wave in waves:
        wave_status = (wave.get("status") or "").upper()
        if wave_status in active_statuses:
            active_waves.append(wave)
        elif wave_status == "COMPLETED":
            completed_waves.append(wave)
        elif wave_status == "FAILED":
            failed_waves.append(wave)
        elif wave_status == "CANCELLED":
            cancelled_waves.append(wave)

    # If any waves are still active, execution should be active
    if active_waves:
        # Keep execution as active - don't change to terminal state
        if current_status in ["COMPLETED", "FAILED", "CANCELLED", "PARTIAL"]:
            print(f"WARNING: Execution {execution.get('executionId')} has active waves but status is {current_status}")
            # Don't change status - let Step Functions orchestration handle it
        return execution

    # All waves are in terminal states
    if failed_waves and not active_waves:
        # Some waves failed
        if completed_waves:
            execution["status"] = "PARTIAL"  # Some completed, some failed
        else:
            execution["status"] = "FAILED"  # All failed
    elif cancelled_waves and not active_waves and not failed_waves:
        # All waves cancelled
        execution["status"] = "CANCELLED"
    elif completed_waves and not active_waves and not failed_waves and not cancelled_waves:
        # All waves completed successfully
        execution["status"] = "COMPLETED"

    return execution


def get_execution_details_fast(execution_id: str) -> Dict:
    """Get execution details using cached data only - FAST response (<1 second)"""
    try:
        # Handle both UUID and ARN formats for backwards compatibility
        if execution_id.startswith("arn:"):
            execution_id = execution_id.split(":")[-1]
            print(f"Extracted UUID from ARN: {execution_id}")

        # Get from DynamoDB using query (table has composite key: ExecutionId + PlanId)
        result = execution_history_table.query(KeyConditionExpression=Key("executionId").eq(execution_id), Limit=1)

        if "Items" not in result or len(result["Items"]) == 0:
            return response(
                404,
                {
                    "error": "EXECUTION_NOT_FOUND",
                    "message": f"Execution with ID {execution_id} not found",
                    "executionId": execution_id,
                },
            )

        execution = result["Items"][0]

        # Basic enrichment with stored data only (FAST operations)
        try:
            if execution.get("planName"):
                execution["recoveryPlanName"] = execution["planName"]

            plan_id = execution.get("planId")
            if plan_id:
                plan_result = recovery_plans_table.get_item(Key={"planId": plan_id})
                if "Item" in plan_result:
                    plan = plan_result["Item"]
                    if not execution.get("recoveryPlanName"):
                        execution["recoveryPlanName"] = plan.get("planName", "Unknown")
                    execution["recoveryPlanDescription"] = plan.get("description", "")
                    execution["totalWaves"] = len(plan.get("waves", []))
                elif not execution.get("recoveryPlanName"):
                    execution["recoveryPlanName"] = "Deleted Plan"
        except Exception as e:
            print(f"Error enriching execution with plan details: {str(e)}")

        # Mark as cached data for frontend
        execution["dataSource"] = "cached"
        execution["lastUpdated"] = execution.get("updatedAt", int(time.time()))

        # Add flag to indicate if real-time data is available
        execution["hasRealtimeData"] = execution.get("status") in [
            "RUNNING",
            "PAUSED",
        ]

        # Add termination metadata for frontend button visibility
        # Centralized logic prevents frontend/backend inconsistencies
        execution["terminationMetadata"] = can_terminate_execution(execution)

        return response(200, execution)

    except Exception as e:
        print(f"Error getting execution details (fast): {str(e)}")
        return response(
            500,
            {
                "error": "INTERNAL_ERROR",
                "message": f"Error retrieving execution details: {str(e)}",
                "executionId": execution_id,
            },
        )
