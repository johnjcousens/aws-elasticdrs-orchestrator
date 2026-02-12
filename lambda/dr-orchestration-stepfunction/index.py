"""
DR Orchestration Step Functions Lambda

Orchestrates multi-wave disaster recovery operations using AWS DRS (Elastic Disaster Recovery).
Manages wave-based execution, cross-account operations, and pause/resume workflows.

HANDLER ARCHITECTURE:
The platform uses three specialized handlers with distinct responsibilities:

    ┌─────────────────────────────────────────────────────────────────────┐
    │                        API Gateway + Cognito                        │
    │                         (User Authentication)                       │
    └─────────────────────────────────────────────────────────────────────┘
                │                    │                    │
                ▼                    ▼                    ▼
    ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
    │ data-management   │ │ execution-handler │ │  query-handler    │
    │     handler       │ │                   │ │                   │
    ├───────────────────┤ ├───────────────────┤ ├───────────────────┤
    │ CRUD Operations:  │ │ Recovery Actions: │ │ Read Operations:  │
    │ - Protection Grps │ │ - Start recovery  │ │ - List executions │
    │ - Recovery Plans  │ │ - Cancel exec     │ │ - Poll DRS jobs   │
    │ - Tag sync        │ │ - Terminate inst  │ │ - Server status   │
    │ - Launch configs  │ │ - Apply configs   │ │ - Dashboard data  │
    └───────────────────┘ └───────────────────┘ └───────────────────┘
                                  │                    │
                                  │   Direct Invoke    │
                                  │   (No API Gateway) │
                                  ▼                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │              dr-orchestration-stepfunction (this Lambda)            │
    │                                                                     │
    │  Step Functions invokes this Lambda, which orchestrates waves by    │
    │  directly invoking execution-handler and query-handler via IAM      │
    └─────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                    AWS DRS (Target Account)                         │
    │              Cross-account via DRSOrchestrationRole                 │
    └─────────────────────────────────────────────────────────────────────┘

HANDLER RESPONSIBILITIES:
- data-management-handler: CRUD for Protection Groups, Recovery Plans, configs (API only)
- execution-handler: Start/cancel recovery, terminate instances, apply launch configs
- query-handler: Poll DRS jobs, list executions, dashboard metrics, server status
- dr-orchestration-stepfunction: Wave orchestration, state management, handler coordination

DIRECT INVOCATION (Step Functions → Handlers):
This Lambda invokes execution-handler and query-handler directly via Lambda invoke,
bypassing API Gateway and Cognito for internal operations:
- execution-handler: action=start_wave_recovery → Invokes DRS StartRecovery API
- query-handler: action=poll_wave_status → Monitors DRS job and server launch status

ARCHITECTURE PATTERN (State Ownership):
- Lambda owns ALL state via Step Functions OutputPath
- State exists at root level ($), not nested under $.application
- All functions return the COMPLETE state object for Step Functions to persist
- State modifications happen in-place to maintain consistency

SECURITY MODEL:
- API Gateway mode: Authentication via Cognito (user-facing)
- Direct invocation mode: IAM role assumption via DRSOrchestrationRole (internal)
- Cross-account DRS operations: IAM role assumption to target accounts

KEY CAPABILITIES:
- Multi-wave recovery execution with dependency management
- Cross-account DRS operations via IAM role assumption
- Tag-based server discovery and resolution at execution time
- Pause/resume support with callback tokens for manual approval gates
- Real-time DRS job polling and server launch status tracking
- Protection Group launch configuration application before recovery

WAVE EXECUTION MODEL:
- Sequential waves: Wave N+1 starts only after Wave N completes
- Parallel within wave: All resources in a wave recover simultaneously
- Failure tolerance: Wave continues even if individual resources fail
- Timeout support: Configurable max wait time for long-term pauses
- Cancellation: User-initiated cancellation checked at each poll cycle

DRS ADAPTER LIFECYCLE PHASES:
1. INSTANTIATE: Launch recovery EC2 instances via DRS StartRecovery API
2. ACTIVATE: Validate instance launch status and apply configurations
3. CLEANUP: Remove temporary resources after successful recovery
4. REPLICATE: Re-establish replication to primary region for failback

DYNAMODB DATA FLOW:
The platform uses 4 DynamoDB tables for configuration and state management:

    +-------------------------+     +----------------------------+
    |   protection-groups     |     |     recovery-plans         |
    +-------------------------+     +----------------------------+
    | PK: groupId             |     | PK: planId                 |
    |                         |     |                            |
    | - groupName             |<----| - waves[].protectionGroupId|
    | - sourceServerIds[]     |     | - waves[].waveNumber       |
    | - launchConfig{}        |     | - waves[].pauseBeforeWave  |
    | - servers[] (per-srv)   |     | - waves[].dependsOnWaves[] |
    | - region                |     | - planName                 |
    | - accountId             |     | - description              |
    +-------------------------+     +----------------------------+
              |                             |
              |  Read at execution start    |
              v                             v
    +-------------------------------------------------------------------+
    |                      execution-history                            |
    +-------------------------------------------------------------------+
    | PK: executionId                                                   |
    | SK: planId (GSI for querying executions by plan)                  |
    |                                                                   |
    | - status: RUNNING | PAUSED | COMPLETED | FAILED | CANCELLED       |
    | - currentWave: 0, 1, 2...                                         |
    | - waveStatuses[]: Per-wave status with DRS job IDs                |
    | - serverExecutions[]: Per-server recovery instance details        |
    | - startTime, endTime, lastUpdated                                 |
    | - taskToken: Step Functions callback token for pause/resume       |
    | - isDrill: true for DR drills, false for production recovery      |
    +-------------------------------------------------------------------+
              |
              |  Cross-account lookup
              v
    +-------------------------+
    |    target-accounts      |
    +-------------------------+
    | PK: accountId           |
    |                         |
    | - accountName           |
    | - roleArn (optional)    |
    | - externalId            |
    | - regions[]             |
    | - accountType: target   |
    +-------------------------+

DATA FLOW DURING EXECUTION:
1. Start Execution:
   - Read recovery-plans to get wave configuration
   - Read protection-groups for each wave's server list and launch configs
   - Read target-accounts for cross-account role ARN
   - Create execution-history record with status=RUNNING

2. Wave Execution:
   - Apply launch configs to DRS (per-server overrides merged with group defaults)
   - Call DRS StartRecovery API in target account
   - Update execution-history with DRS job ID and wave status

3. Polling:
   - Query DRS DescribeJobs for job completion status
   - Query DRS DescribeRecoveryInstances for launched instance details
   - Update execution-history with server recovery instance data

4. Pause/Resume:
   - Store Step Functions taskToken in execution-history
   - Update status to PAUSED, send SNS notification
   - On resume, retrieve taskToken and call SendTaskSuccess

5. Completion:
   - Update execution-history with final status and endTime
   - Record per-server recovery instance details (ID, type, IP, launch time)

SHARED UTILITIES (lambda/shared/):
Common modules used by this Lambda for cross-account operations:

    +---------------------------+------------------------------------------------+
    | Module                    | Purpose                                        |
    +---------------------------+------------------------------------------------+
    | account_utils.py          | construct_role_arn() - build IAM role ARN      |
    | cross_account.py          | create_drs_client() with IAM role assumption   |
    +---------------------------+------------------------------------------------+
"""

import json
import logging
import os
import time
from decimal import Decimal
from typing import Dict

import boto3

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Import shared utilities
try:
    from shared.account_utils import construct_role_arn
    from shared.cross_account import create_drs_client
    from shared.notifications import (
        publish_recovery_plan_notification,
    )
except ImportError:
    # Fallback for local testing
    def construct_role_arn(account_id: str) -> str:
        """Construct standardized role ARN from account ID."""
        if (
            not account_id
            or len(account_id) != 12
            or not account_id.isdigit()
        ):
            raise ValueError(
                f"Invalid account ID: {account_id}. "
                "Must be 12 digits."
            )
        return (
            f"arn:aws:iam::{account_id}:role/"
            "DRSOrchestrationRole"
        )

    # Fallback create_drs_client for local testing
    def create_drs_client(
        region: str, account_context: Dict = None
    ):
        """Fallback DRS client creation."""
        return boto3.client("drs", region_name=region)

    def publish_recovery_plan_notification(
        plan_id: str,
        event_type: str,
        details: dict,
    ) -> None:
        """Fallback no-op for local testing."""
        logger.info(
            "Notification stub: plan=%s event=%s",
            plan_id,
            event_type,
        )


# Environment variables
PROTECTION_GROUPS_TABLE = os.environ.get("PROTECTION_GROUPS_TABLE")
RECOVERY_PLANS_TABLE = os.environ.get("RECOVERY_PLANS_TABLE")
EXECUTION_HISTORY_TABLE = os.environ.get("EXECUTION_HISTORY_TABLE")

# AWS clients
dynamodb = boto3.resource("dynamodb")

# DynamoDB tables - lazy initialization for Lambda cold start optimization
_protection_groups_table = None
_recovery_plans_table = None
_execution_history_table = None


def get_protection_groups_table():
    """Lazy-load Protection Groups table to optimize Lambda cold starts"""
    global _protection_groups_table
    if _protection_groups_table is None:
        _protection_groups_table = dynamodb.Table(PROTECTION_GROUPS_TABLE)
    return _protection_groups_table


def get_recovery_plans_table():
    """Lazy-load Recovery Plans table to optimize Lambda cold starts"""
    global _recovery_plans_table
    if _recovery_plans_table is None:
        _recovery_plans_table = dynamodb.Table(RECOVERY_PLANS_TABLE)
    return _recovery_plans_table


def get_execution_history_table():
    """Lazy-load Execution History table to optimize Lambda cold starts"""
    global _execution_history_table
    if _execution_history_table is None:
        _execution_history_table = dynamodb.Table(EXECUTION_HISTORY_TABLE)
    return _execution_history_table


def get_account_context(state: Dict) -> Dict:
    """
    Extract account context from state, handling both camelCase and snake_case.

    Supports two input formats:
    - Initial execution: camelCase (accountContext) from Step Functions input
    - Resume after pause: snake_case (account_context) from SendTaskSuccess output

    Returns:
        Dict containing accountId, assumeRoleName, and isCurrentAccount flags
    """
    return state.get("accountContext") or state.get("account_context", {})


# DRS job status constants - determine when job polling should stop
DRS_JOB_STATUS_COMPLETE_STATES = ["COMPLETED"]
DRS_JOB_STATUS_WAIT_STATES = ["PENDING", "STARTED"]

# DRS server launch status constants - track individual server recovery progress
DRS_JOB_SERVERS_COMPLETE_SUCCESS_STATES = ["LAUNCHED"]
DRS_JOB_SERVERS_COMPLETE_FAILURE_STATES = ["FAILED", "TERMINATED"]
DRS_JOB_SERVERS_WAIT_STATES = ["PENDING", "IN_PROGRESS"]


class DecimalEncoder(json.JSONEncoder):
    """
    JSON encoder for DynamoDB Decimal types.

    DynamoDB returns numeric values as Decimal objects which aren't JSON serializable.
    This encoder converts Decimals to int (if whole number) or float (if fractional).
    """

    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Main entry point for Step Functions orchestration.

    Routes requests to appropriate handlers based on action parameter.
    All handlers follow state ownership pattern - they return complete state objects.

    Supported Actions:
    - begin: Initialize wave plan execution
    - store_task_token: Store callback token for pause/resume
    - pause: Handle execution pause with task token
    - resume_wave: Resume execution after manual approval
    - poll_wave_status: Poll wave status via query-handler

    Args:
        event: Step Functions event containing action and state
        context: Lambda context (unused)

    Returns:
        Complete state object for Step Functions to persist

    Raises:
        ValueError: If action is unknown
    """
    print(f"Event: {json.dumps(event, cls=DecimalEncoder)}")

    action = event.get("action")

    # Log account context for multi-account operations
    account_context = event.get("accountContext", {})
    account_id = account_context.get("accountId")
    if account_id:
        print(f"Operating in account context: {account_id}")

    if action == "begin":
        return begin_wave_plan(event)
    elif action == "store_task_token":
        return store_task_token(event)
    elif action == "pause":
        return handle_execution_pause(event, context)
    elif action == "resume_wave":
        return resume_wave(event)
    elif action == "poll_wave_status":
        return poll_wave_status(event)
    else:
        raise ValueError(f"Unknown action: {action}")


def begin_wave_plan(event: Dict) -> Dict:
    """
    Initialize wave plan execution and start first wave.

    Creates complete state object with all tracking fields for Step Functions.
    Supports up to 1-year execution duration for long-running DR scenarios.

    State Object Structure:
    - Core identifiers: plan_id, execution_id, is_drill, accountContext
    - Wave tracking: waves, total_waves, current_wave_number, completed_waves
    - Completion flags: all_waves_completed, wave_completed (for Step Functions Choice states)
    - Polling config: update intervals and max wait times
    - Status: running/paused/completed/failed/cancelled (for parent orchestrator)
    - Results: wave_results, recovery_instance_ids, recovery_instance_ips
    - Current wave: job_id, region, server_ids
    - Error handling: error, error_code
    - Pause/Resume: paused_before_wave, task token (stored in DynamoDB)
    - Timing: start_time, end_time, duration_seconds (for SLA tracking)

    Args:
        event: Step Functions event with plan, execution, isDrill, accountContext

    Returns:
        Complete state object with first wave started (state ownership pattern)
    """
    plan = event.get("plan", {})
    execution_id = event.get("execution", "")
    is_drill = event.get("isDrill", True)
    account_context = event.get("accountContext", {})

    plan_id = plan.get("planId", "")
    waves = plan.get("waves", [])

    print(f"Beginning wave plan for execution {execution_id}, plan {plan_id}")
    print(f"Total waves: {len(waves)}, isDrill: {is_drill}")

    # Initialize state object at root level (state ownership pattern)
    start_time = int(time.time())
    state = {
        # Core identifiers
        "plan_id": plan_id,
        "plan_name": plan.get("planName", ""),
        "execution_id": execution_id,
        "is_drill": is_drill,
        "accountContext": account_context,  # Step Functions expects camelCase
        # Wave tracking
        "waves": waves,
        "total_waves": len(waves),
        "current_wave_number": 0,
        "completed_waves": 0,
        "failed_waves": 0,
        # Completion flags for Step Functions Choice states
        "all_waves_completed": False,
        "wave_completed": False,
        # Polling configuration - supports up to 1 year for long-term pauses
        "current_wave_update_time": 30,
        "current_wave_total_wait_time": 0,
        "current_wave_max_wait_time": 31536000,  # 1 year (365 * 24 * 60 * 60)
        # Status for parent orchestrator branching
        "status": "running",  # running/paused/completed/failed/cancelled
        "status_reason": None,
        # Results for downstream processing
        "wave_results": [],
        "recovery_instance_ids": [],  # EC2 instance IDs
        "recovery_instance_ips": [],  # Private IPs
        # Current wave details
        "job_id": None,
        "region": None,
        "server_ids": [],
        # Error handling
        "error": None,
        "error_code": None,
        # Pause/Resume
        "paused_before_wave": None,
        # Step Functions pause check support
        "pauseBeforeExecution": False,
        # Timing for SLA tracking
        "start_time": start_time,
        "end_time": None,
        "duration_seconds": None,
    }

    # Update DynamoDB execution status
    try:
        get_execution_history_table().update_item(
            Key={"executionId": execution_id, "planId": plan_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": "RUNNING"},
        )
    except Exception as e:
        print(f"Error updating execution status: {e}")

    # Start first wave via execution-handler
    if len(waves) > 0:
        try:
            execution_handler_arn = os.environ.get("EXECUTION_HANDLER_ARN")
            if not execution_handler_arn:
                raise ValueError("EXECUTION_HANDLER_ARN environment variable not set")

            print(f"Invoking execution-handler: {execution_handler_arn}")
            lambda_client = boto3.client("lambda")
            response = lambda_client.invoke(
                FunctionName=execution_handler_arn,
                InvocationType="RequestResponse",
                Payload=json.dumps(
                    {
                        "action": "start_wave_recovery",
                        "state": state,
                        "wave_number": 0,
                    },
                    cls=DecimalEncoder,
                ),
            )

            # Read payload once and store
            payload_bytes = response["Payload"].read()
            print(f"DEBUG: Lambda response StatusCode={response.get('StatusCode')}")
            print(f"DEBUG: Lambda response FunctionError={response.get('FunctionError')}")
            print(f"DEBUG: Lambda response payload length={len(payload_bytes)}")

            # Check for function error
            if response.get("FunctionError"):
                error_detail = payload_bytes.decode("utf-8") if payload_bytes else "No payload"
                raise Exception(f"Handler error: {response.get('FunctionError')} - {error_detail}")

            # Parse response
            result = json.loads(payload_bytes)
            print(f"DEBUG: Parsed result keys={list(result.keys()) if isinstance(result, dict) else type(result)}")

            # Check if result contains error
            if isinstance(result, dict) and result.get("error"):
                print(f"DEBUG: Handler returned error: {result.get('error')}")

            state.update(result)
            print(
                f"DEBUG: After start_wave_recovery - job_id={state.get('job_id')}, "
                f"region={state.get('region')}, server_ids={state.get('server_ids')}"
            )

            # Notify: execution started successfully
            try:
                publish_recovery_plan_notification(
                    plan_id=plan_id,
                    event_type="start",
                    details={
                        "executionId": execution_id,
                        "planId": plan_id,
                        "planName": plan.get(
                            "planName", ""
                        ),
                        "accountId": account_context.get(
                            "accountId", ""
                        ),
                        "waveCount": len(waves),
                        "isDrill": is_drill,
                        "timestamp": time.strftime(
                            "%Y-%m-%dT%H:%M:%SZ",
                            time.gmtime(),
                        ),
                    },
                )
            except Exception as notif_err:
                logger.error(
                    "Notification failed (start): %s",
                    notif_err,
                )

        except Exception as e:
            logger.error(f"Error invoking execution-handler: {e}")
            import traceback

            traceback.print_exc()
            state["wave_completed"] = True
            state["status"] = "failed"
            state["error"] = str(e)

            # Notify: execution failed to start
            try:
                publish_recovery_plan_notification(
                    plan_id=plan_id,
                    event_type="fail",
                    details={
                        "executionId": execution_id,
                        "planId": plan_id,
                        "planName": plan.get(
                            "planName", ""
                        ),
                        "accountId": account_context.get(
                            "accountId", ""
                        ),
                        "errorMessage": str(e),
                        "timestamp": time.strftime(
                            "%Y-%m-%dT%H:%M:%SZ",
                            time.gmtime(),
                        ),
                    },
                )
            except Exception as notif_err:
                logger.error(
                    "Notification failed (fail): %s",
                    notif_err,
                )
    else:
        print("No waves to execute")
        state["all_waves_completed"] = True
        state["status"] = "completed"

        # Notify: execution completed (no waves)
        try:
            publish_recovery_plan_notification(
                plan_id=plan_id,
                event_type="complete",
                details={
                    "executionId": execution_id,
                    "planId": plan_id,
                    "planName": plan.get(
                        "planName", ""
                    ),
                    "accountId": account_context.get(
                        "accountId", ""
                    ),
                    "waveCount": 0,
                    "timestamp": time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ",
                        time.gmtime(),
                    ),
                },
            )
        except Exception as notif_err:
            logger.error(
                "Notification failed (complete): %s",
                notif_err,
            )

    print(
        f"DEBUG: Returning state with job_id={state.get('job_id')}, wave_completed={state.get('wave_completed')}, status={state.get('status')}"  # noqa: E501
    )
    return state


def store_task_token(event: Dict) -> Dict:
    """
    Store task token for callback pattern (manual pause/resume workflow).

    Task tokens enable Step Functions to pause execution and wait for external
    approval before continuing. The token is stored in DynamoDB and used later
    with SendTaskSuccess to resume execution.

    State Ownership Pattern: Returns complete state object with paused_before_wave set
    so resume knows which wave to start.

    Args:
        event: Contains state (application) and taskToken from Step Functions

    Returns:
        Complete state object with pause metadata

    Raises:
        ValueError: If task token is missing
    """
    # State passed directly (state ownership pattern)
    state = event.get("application", event)
    task_token = event.get("taskToken")
    execution_id = state.get("execution_id")
    plan_id = state.get("plan_id")
    paused_before_wave = state.get("paused_before_wave", state.get("current_wave_number", 0) + 1)

    print(f"⏸️ Storing task token for execution {execution_id}, paused before wave {paused_before_wave}")

    if not task_token:
        print("ERROR: No task token provided")
        raise ValueError("No task token provided for callback")

    # Store task token in DynamoDB for later resume
    try:
        get_execution_history_table().update_item(
            Key={"executionId": execution_id, "planId": plan_id},
            UpdateExpression="SET #status = :status, taskToken = :token, pausedBeforeWave = :wave",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "PAUSED",
                ":token": task_token,
                ":wave": paused_before_wave,
            },
        )
        print(f"✅ Task token stored for execution {execution_id}")
    except Exception as e:
        print(f"ERROR storing task token: {e}")
        raise

    # State Ownership pattern: Return complete state for SendTaskSuccess
    state["paused_before_wave"] = paused_before_wave
    return state


def _notify_execution_start(state: Dict) -> None:
    """
    Publish notification for execution start event.

    Wraps publish_recovery_plan_notification with start-specific
    details. Failures are logged but never block execution.

    Args:
        state: Execution state dictionary.
    """
    try:
        account_ctx = state.get("accountContext", {})
        publish_recovery_plan_notification(
            plan_id=state.get("plan_id", ""),
            event_type="start",
            details={
                "executionId": state.get(
                    "execution_id", ""
                ),
                "planName": state.get("plan_name", ""),
                "waveCount": state.get("total_waves", 0),
                "isDrill": state.get("is_drill", False),
                "accountId": account_ctx.get(
                    "accountId", ""
                ),
                "consoleLink": os.environ.get(
                    "API_GATEWAY_URL", ""
                ),
                "timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                ),
            },
        )
    except Exception as exc:
        logger.error(
            "Notification failed (start): %s", exc
        )


def _notify_execution_complete(state: Dict) -> None:
    """
    Publish notification for execution complete event.

    Wraps publish_recovery_plan_notification with completion
    details. Failures are logged but never block execution.

    Args:
        state: Execution state dictionary.
    """
    try:
        wave_results = state.get("wave_results", [])
        success_count = sum(
            1
            for w in wave_results
            if w.get("status") == "success"
        )
        failure_count = sum(
            1
            for w in wave_results
            if w.get("status") == "failed"
        )
        account_ctx = state.get("accountContext", {})
        publish_recovery_plan_notification(
            plan_id=state.get("plan_id", ""),
            event_type="complete",
            details={
                "executionId": state.get(
                    "execution_id", ""
                ),
                "planName": state.get("plan_name", ""),
                "successCount": success_count,
                "failureCount": failure_count,
                "durationSeconds": state.get(
                    "duration_seconds", 0
                ),
                "accountId": account_ctx.get(
                    "accountId", ""
                ),
                "timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                ),
            },
        )
    except Exception as exc:
        logger.error(
            "Notification failed (complete): %s", exc
        )


def _notify_execution_failure(state: Dict) -> None:
    """
    Publish notification for execution failure event.

    Wraps publish_recovery_plan_notification with failure
    details. Failures are logged but never block execution.

    Args:
        state: Execution state dictionary.
    """
    try:
        account_ctx = state.get("accountContext", {})
        publish_recovery_plan_notification(
            plan_id=state.get("plan_id", ""),
            event_type="fail",
            details={
                "executionId": state.get(
                    "execution_id", ""
                ),
                "planName": state.get("plan_name", ""),
                "errorMessage": state.get("error", ""),
                "errorCode": state.get(
                    "error_code", ""
                ),
                "accountId": account_ctx.get(
                    "accountId", ""
                ),
                "timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                ),
            },
        )
    except Exception as exc:
        logger.error(
            "Notification failed (failure): %s", exc
        )


def handle_execution_pause(
    event: Dict, context
) -> Dict:
    """
    Handle execution pause with task token for resume/cancel.

    Called by Step Functions when the state machine routes to
    PauseForApproval using the waitForTaskToken integration.
    This handler is ONLY invoked for pause-enabled executions
    and does NOT affect the normal (non-pause) execution flow.

    Workflow:
    1. Extract state and taskToken from the event
    2. Store task token in DynamoDB (marks execution PAUSED)
    3. Publish pause notification with resume/cancel URLs
    4. Return state with pause metadata for Step Functions

    Args:
        event: Step Functions event with application state
            and taskToken from waitForTaskToken
        context: Lambda context (unused)

    Returns:
        Complete state object with pause metadata

    Raises:
        ValueError: If task token is missing
    """
    state = event.get("application", event)
    task_token = event.get("taskToken")
    execution_id = state.get("execution_id", "")
    plan_id = state.get("plan_id", "")
    plan_name = state.get("plan_name", "")
    pause_reason = state.get(
        "pause_reason", "Manual approval required"
    )

    logger.info(
        "Pause requested for execution %s, plan %s",
        execution_id,
        plan_id,
    )

    if not task_token:
        raise ValueError(
            "taskToken is required for pause handler. "
            "This handler must be invoked via "
            "waitForTaskToken integration."
        )

    # Store task token and mark execution as PAUSED
    paused_before_wave = state.get(
        "paused_before_wave",
        state.get("current_wave_number", 0) + 1,
    )
    try:
        get_execution_history_table().update_item(
            Key={
                "executionId": execution_id,
                "planId": plan_id,
            },
            UpdateExpression=(
                "SET #status = :status, "
                "taskToken = :token, "
                "pausedBeforeWave = :wave"
            ),
            ExpressionAttributeNames={
                "#status": "status"
            },
            ExpressionAttributeValues={
                ":status": "PAUSED",
                ":token": task_token,
                ":wave": paused_before_wave,
            },
        )
        logger.info(
            "Task token stored for execution %s",
            execution_id,
        )
    except Exception as exc:
        logger.error(
            "Failed to store task token: %s", exc
        )
        raise

    # Update state with pause metadata
    state["status"] = "paused"
    state["paused_before_wave"] = paused_before_wave

    # Build callback URLs for email action links
    api_url = os.environ.get("API_GATEWAY_URL", "")
    resume_url = (
        f"{api_url}/execution-callback"
        f"?action=resume&taskToken={task_token}"
    )
    cancel_url = (
        f"{api_url}/execution-callback"
        f"?action=cancel&taskToken={task_token}"
    )

    # Publish pause notification (never blocks execution)
    account_ctx = get_account_context(state)
    try:
        publish_recovery_plan_notification(
            plan_id=plan_id,
            event_type="pause",
            details={
                "executionId": execution_id,
                "planId": plan_id,
                "planName": plan_name,
                "accountId": account_ctx.get(
                    "accountId", ""
                ),
                "pauseReason": pause_reason,
                "pausedBeforeWave": paused_before_wave,
                "taskToken": task_token,
                "resumeUrl": resume_url,
                "cancelUrl": cancel_url,
                "timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ",
                    time.gmtime(),
                ),
            },
        )
    except Exception as notif_err:
        logger.error(
            "Notification failed (pause): %s",
            notif_err,
        )

    return state



def resume_wave(event: Dict) -> Dict:
    """
    Resume execution by starting the paused wave.

    Called after SendTaskSuccess provides the callback token. Resets execution
    status to running and starts the wave that was paused.

    State Ownership Pattern: State passed directly, returns complete state object.

    Args:
        event: Contains state (application) with paused_before_wave

    Returns:
        Complete state object with wave started
    """
    # State passed directly (state ownership pattern)
    state = event.get("application", event)
    execution_id = state.get("execution_id")
    plan_id = state.get("plan_id")
    paused_before_wave = state.get("paused_before_wave", 0)

    # DynamoDB returns Decimal, convert to int
    if isinstance(paused_before_wave, Decimal):
        paused_before_wave = int(paused_before_wave)

    print(f"⏯️ Resuming execution {execution_id}, starting wave {paused_before_wave}")

    # Reset status to running
    state["status"] = "running"
    state["wave_completed"] = False
    state["paused_before_wave"] = None

    # Update DynamoDB - remove task token and pause metadata
    try:
        get_execution_history_table().update_item(
            Key={"executionId": execution_id, "planId": plan_id},
            UpdateExpression="SET #status = :status REMOVE taskToken, pausedBeforeWave",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": "RUNNING"},
        )
    except Exception as e:
        print(f"Error updating execution status: {e}")

    # Start the paused wave via execution-handler
    try:
        lambda_client = boto3.client("lambda")
        response = lambda_client.invoke(
            FunctionName=os.environ["EXECUTION_HANDLER_ARN"],
            InvocationType="RequestResponse",
            Payload=json.dumps(
                {
                    "action": "start_wave_recovery",
                    "state": state,
                    "wave_number": paused_before_wave,
                }
            ),
        )

        # Check for function error
        if response.get("FunctionError"):
            raise Exception(f"Handler error: {response}")

        result = json.loads(response["Payload"].read())
        state.update(result)

    except Exception as e:
        logger.error(f"Error invoking execution-handler: {e}")
        state["wave_completed"] = True
        state["status"] = "failed"
        state["error"] = str(e)

    return state


def poll_wave_status(event: Dict) -> Dict:
    """
    Poll wave status by invoking query-handler.

    This function delegates wave status polling to the query-handler
    Lambda, which tracks DRS job progress and server launch status.

    Args:
        event: Step Functions event with state

    Returns:
        Updated state object from query-handler

    Raises:
        Exception: If query-handler invocation fails
    """
    state = event.get("application", event)

    try:
        lambda_client = boto3.client("lambda")
        response = lambda_client.invoke(
            FunctionName=os.environ["QUERY_HANDLER_ARN"],
            InvocationType="RequestResponse",
            Payload=json.dumps({"action": "poll_wave_status", "state": state}),
        )

        # Check for function error
        if response.get("FunctionError"):
            raise Exception(f"Handler error: {response}")

        result = json.loads(response["Payload"].read())

        # Notify on execution completion or failure
        _notify_on_status_change(state, result)

        return result

    except Exception as e:
        logger.error(f"Error invoking query-handler: {e}")
        state["wave_completed"] = True
        state["status"] = "failed"
        state["error"] = str(e)

        # Notify: polling failure
        try:
            publish_recovery_plan_notification(
                plan_id=state.get("plan_id", ""),
                event_type="fail",
                details={
                    "executionId": state.get(
                        "execution_id", ""
                    ),
                    "planId": state.get("plan_id", ""),
                    "planName": state.get(
                        "plan_name", ""
                    ),
                    "accountId": get_account_context(
                        state
                    ).get("accountId", ""),
                    "errorMessage": str(e),
                    "timestamp": time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ",
                        time.gmtime(),
                    ),
                },
            )
        except Exception as notif_err:
            logger.error(
                "Notification failed (fail): %s",
                notif_err,
            )

        return state


def _notify_on_status_change(
    old_state: Dict, new_state: Dict
) -> None:
    """
    Publish notification when execution status changes.

    Checks the query-handler result for completion or failure
    and sends the appropriate notification. Failures in
    notification publishing are logged but never raised.

    Args:
        old_state: State before polling
        new_state: State returned by query-handler
    """
    new_status = new_state.get("status", "")
    all_done = new_state.get("all_waves_completed", False)
    plan_id = new_state.get("plan_id", "")

    if not plan_id:
        return

    account_ctx = get_account_context(new_state)
    base_details = {
        "executionId": new_state.get("execution_id", ""),
        "planId": plan_id,
        "planName": new_state.get("plan_name", ""),
        "accountId": account_ctx.get("accountId", ""),
        "timestamp": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
        ),
    }

    try:
        if all_done and new_status == "completed":
            base_details["completedWaves"] = new_state.get(
                "completed_waves", 0
            )
            base_details["totalWaves"] = new_state.get(
                "total_waves", 0
            )
            start_ts = new_state.get("start_time")
            if start_ts:
                base_details["durationSeconds"] = (
                    int(time.time()) - int(start_ts)
                )
            publish_recovery_plan_notification(
                plan_id=plan_id,
                event_type="complete",
                details=base_details,
            )
        elif new_status == "failed":
            base_details["errorMessage"] = new_state.get(
                "error", "Unknown error"
            )
            base_details["failedWaves"] = new_state.get(
                "failed_waves", 0
            )
            publish_recovery_plan_notification(
                plan_id=plan_id,
                event_type="fail",
                details=base_details,
            )
    except Exception as notif_err:
        logger.error(
            "Notification failed (status change): %s",
            notif_err,
        )
