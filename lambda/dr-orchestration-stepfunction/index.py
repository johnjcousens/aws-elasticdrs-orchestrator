"""
DR Orchestration Step Functions Lambda

Orchestrates multi-wave disaster recovery operations using AWS DRS (Elastic Disaster Recovery).
Manages wave-based execution, cross-account operations, and pause/resume workflows.

ENTERPRISE INTEGRATION CONTEXT:
This Lambda implements the DRS adapter for enterprise DR orchestration platforms.
The wave-based orchestration pattern demonstrated here serves as the reference implementation
for other technology adapters (Aurora, ECS, Lambda, Route53) that will follow the same
4-phase lifecycle: INSTANTIATE → ACTIVATE → CLEANUP → REPLICATE.

The DRS adapter focuses on EC2 instance recovery using AWS Elastic Disaster Recovery Service,
while future adapters will handle database failover, container orchestration, serverless
functions, and DNS management using the same wave execution model.

DIRECT INVOCATION SUPPORT:
This Lambda supports both API Gateway invocation (current standalone mode) and direct
Lambda invocation (future enterprise integration mode). In enterprise mode, this function is called
directly by the orchestration Step Functions without API Gateway or Cognito,
enabling unified multi-technology DR orchestration across the enterprise platform.

Architecture Pattern: Archive Pattern
- Lambda owns ALL state via Step Functions OutputPath
- State exists at root level ($), not nested under $.application
- All functions return the COMPLETE state object for Step Functions to persist
- State modifications happen in-place to maintain consistency

Security Model:
- Authentication/authorization handled at API Gateway layer (Cognito) in standalone mode
- In enterprise mode, authentication handled by enterprise platform (no Cognito)
- This Lambda receives pre-validated data from Step Functions
- Input sanitization intentionally omitted to preserve archive pattern integrity

Key Capabilities:
- Multi-wave recovery execution with dependency management (AWSM-1103)
- Cross-account DRS operations via IAM role assumption
- Tag-based server discovery and resolution at execution time
- Pause/resume support with callback tokens for manual approval gates
- Real-time DRS job polling and server launch status tracking
- Protection Group launch configuration application before recovery

Wave Execution Model (AWSM-1103):
- Sequential waves: Wave N+1 starts only after Wave N completes
- Parallel within wave: All resources in a wave recover simultaneously
- Failure tolerance: Wave continues even if individual resources fail
- Timeout support: Configurable max wait time (default 1 year for long-term pauses)
- Cancellation: User-initiated cancellation checked at each poll cycle

Technology Adapter Pattern:
Each technology adapter (DRS, Aurora, ECS, Lambda, Route53) implements:
1. INSTANTIATE phase: Launch recovery resources (EC2, RDS, ECS tasks, Lambda functions)
2. ACTIVATE phase: Configure and validate services (DNS, health checks, connections)
3. CLEANUP phase: Remove temporary resources and configurations
4. REPLICATE phase: Re-establish replication to primary region (for failback)

The DRS adapter demonstrates this pattern for EC2 instance recovery, providing the
blueprint for other adapters to follow in broader enterprise platforms.

Reference: docs/user-stories/AWSM-1088/AWSM-1103/IMPLEMTATION.md
"""

import json
import os
import time
from decimal import Decimal
from typing import Dict, List

import boto3

# Import shared utilities
try:
    from shared.account_utils import construct_role_arn
    from shared.cross_account import create_drs_client
except ImportError:
    # Fallback for local testing
    def construct_role_arn(account_id: str) -> str:
        """Construct standardized role ARN from account ID."""
        if not account_id or len(account_id) != 12 or not account_id.isdigit():
            raise ValueError(f"Invalid account ID: {account_id}. Must be 12 digits.")
        return f"arn:aws:iam::{account_id}:role/DRSOrchestrationRole"

    # Fallback create_drs_client for local testing
    def create_drs_client(region: str, account_context: Dict = None):
        """Fallback DRS client creation for local testing."""
        return boto3.client("drs", region_name=region)


# Environment variables
PROTECTION_GROUPS_TABLE = os.environ.get("PROTECTION_GROUPS_TABLE")
RECOVERY_PLANS_TABLE = os.environ.get("RECOVERY_PLANS_TABLE")
EXECUTION_HISTORY_TABLE = os.environ.get("EXECUTION_HISTORY_TABLE")

# AWS clients
dynamodb = boto3.resource("dynamodb")

# DynamoDB tables - lazy initialization for Lambda cold start optimization
#
# ADAPTER PATTERN NOTE:
# This Step Functions Lambda currently reads Protection Groups and Recovery Plans
# directly from DynamoDB. In broader enterprise platforms, this pattern will be replicated
# across all technology adapters (Aurora, ECS, Lambda, Route53).
#
# API Handler Decomposition Impact:
# The API handler is being decomposed into 3 focused handlers (Query, Execution, Data Management).
# This decomposition does NOT affect Step Functions operation because:
# - Step Functions reads from DynamoDB (not via API handler)
# - API handlers and Step Functions are parallel consumers of the same DynamoDB tables
# - Communication happens via DynamoDB state, not direct Lambda invocation
#
# Future Enterprise Integration:
# When integrated into enterprise platforms, this DRS adapter will be invoked by the
# orchestration Step Functions, which will pass Protection Group and Recovery Plan
# data as input parameters rather than requiring DynamoDB reads. Other technology
# adapters (Aurora, ECS, Lambda, Route53) will follow this same pattern.
#
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
    All handlers follow archive pattern - they return complete state objects.

    Supported Actions:
    - begin: Initialize wave plan execution
    - store_task_token: Store callback token for pause/resume
    - resume_wave: Resume execution after manual approval

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
    elif action == "resume_wave":
        return resume_wave(event)
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
        Complete state object with first wave started (archive pattern)
    """
    plan = event.get("plan", {})
    execution_id = event.get("execution", "")
    is_drill = event.get("isDrill", True)
    account_context = event.get("accountContext", {})

    plan_id = plan.get("planId", "")
    waves = plan.get("waves", [])

    print(f"Beginning wave plan for execution {execution_id}, plan {plan_id}")
    print(f"Total waves: {len(waves)}, isDrill: {is_drill}")

    # Initialize state object at root level (archive pattern)
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

    # Start first wave
    if len(waves) > 0:
        start_wave_recovery(state, 0)
        print(
            f"DEBUG: After start_wave_recovery - job_id={state.get('job_id')}, region={state.get('region')}, server_ids={state.get('server_ids')}"  # noqa: E501
        )
    else:
        print("No waves to execute")
        state["all_waves_completed"] = True
        state["status"] = "completed"

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

    Archive Pattern: Returns complete state object with paused_before_wave set
    so resume knows which wave to start.

    Args:
        event: Contains state (application) and taskToken from Step Functions

    Returns:
        Complete state object with pause metadata

    Raises:
        ValueError: If task token is missing
    """
    # State passed directly (archive pattern)
    state = event.get("application", event)
    task_token = event.get("taskToken")
    execution_id = state.get("execution_id")
    plan_id = state.get("plan_id")
    paused_before_wave = state.get("paused_before_wave", state.get("current_wave_number", 0) + 1)

    print(
        f"⏸️ Storing task token for execution {execution_id}, paused before wave {paused_before_wave}"
    )

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

    # Archive pattern: Return complete state for SendTaskSuccess
    state["paused_before_wave"] = paused_before_wave
    return state


def resume_wave(event: Dict) -> Dict:
    """
    Resume execution by starting the paused wave.

    Called after SendTaskSuccess provides the callback token. Resets execution
    status to running and starts the wave that was paused.

    Archive Pattern: State passed directly, returns complete state object.

    Args:
        event: Contains state (application) with paused_before_wave

    Returns:
        Complete state object with wave started
    """
    # State passed directly (archive pattern)
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

    # Start the paused wave
    start_wave_recovery(state, paused_before_wave)

    return state


def query_drs_servers_by_tags(  # noqa: C901
    region: str, tags: Dict[str, str], account_context: Dict = None
) -> List[str]:
    """
    Query DRS source servers matching ALL specified tags (AND logic).

    Tag-based discovery enables dynamic server resolution at execution time rather
    than static server lists. This supports auto-scaling and server changes without
    updating Protection Groups.

    Tag Matching Rules:
    - Server must have ALL specified tags to be included
    - Tag keys and values are case-insensitive
    - Whitespace is stripped from keys and values
    - Tags are read from DRS source server metadata, not EC2 instance tags

    Args:
        region: AWS region to query DRS servers
        tags: Dict of tag key-value pairs that servers must match
        account_context: Optional cross-account context for IAM role assumption

    Returns:
        List of DRS source server IDs matching all tags

    Example:
        tags = {"Environment": "production", "Customer": "acme"}
        # Returns only servers with BOTH tags matching
    """
    try:
        # Create DRS client with cross-account support
        regional_drs = create_drs_client(region, account_context)

        # Get all source servers in the region
        all_servers = []
        paginator = regional_drs.get_paginator("describe_source_servers")

        for page in paginator.paginate():
            all_servers.extend(page.get("items", []))

        if not all_servers:
            print("No DRS source servers found in region")
            return []

        # Filter servers matching ALL specified tags
        matching_server_ids = []

        for server in all_servers:
            server_id = server.get("sourceServerID", "")
            drs_tags = server.get("tags", {})

            # Check if server has ALL required tags with matching values
            matches_all = True
            for tag_key, tag_value in tags.items():
                # Normalize for case-insensitive comparison
                normalized_required_key = tag_key.strip()
                normalized_required_value = tag_value.strip().lower()

                # Check if any DRS tag matches
                found_match = False
                for drs_key, drs_value in drs_tags.items():
                    normalized_drs_key = drs_key.strip()
                    normalized_drs_value = str(drs_value).strip().lower()

                    if (
                        normalized_drs_key == normalized_required_key
                        and normalized_drs_value == normalized_required_value
                    ):
                        found_match = True
                        break

                if not found_match:
                    matches_all = False
                    print(
                        f"Server {server_id} missing tag {tag_key}={tag_value}. Available DRS tags: {list(drs_tags.keys())}"  # noqa: E501
                    )
                    break

            if matches_all:
                matching_server_ids.append(server_id)

        print("Tag matching results:")
        print(f"- Total DRS servers: {len(all_servers)}")
        print(f"- Servers matching tags {tags}: {len(matching_server_ids)}")

        return matching_server_ids

    except Exception as e:
        print(f"Error querying DRS servers by DRS tags: {str(e)}")
        raise


