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
            raise ValueError(
                f"Invalid account ID: {account_id}. Must be 12 digits."
            )
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


def apply_launch_config_before_recovery(
    drs_client,
    server_ids: List[str],
    launch_config: Dict,
    region: str,
    protection_group: Dict = None,
) -> None:
    """
    Apply Protection Group launch configuration to DRS servers before recovery.

    Updates both DRS launch settings and EC2 launch templates to ensure recovered
    instances use correct network, security, and instance configurations.

    Supports per-server configuration overrides:
    - If protection_group contains 'servers' array, applies per-server configs
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
        launch_config: Protection Group launch configuration dict (group defaults)
        region: AWS region for EC2 operations
        protection_group: Full protection group dict with per-server configs (optional)

    Note:
        Failures for individual servers are logged but don't stop recovery.
        This ensures partial success when some servers have configuration issues.
    """
    ec2_client = boto3.client("ec2", region_name=region)

    # Import config merge function for per-server overrides
    try:
        from shared.config_merge import get_effective_launch_config
    except ImportError:
        print(
            "Warning: config_merge module not found, per-server configs disabled"
        )
        get_effective_launch_config = None

    for server_id in server_ids:
        try:
            # Get effective config (group defaults + per-server overrides)
            if protection_group and get_effective_launch_config:
                effective_config = get_effective_launch_config(
                    protection_group, server_id
                )
            else:
                effective_config = launch_config

            # Get DRS launch configuration to find EC2 launch template
            current_config = drs_client.get_launch_configuration(
                sourceServerID=server_id
            )
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
                drs_update["targetInstanceTypeRightSizingMethod"] = (
                    effective_config["targetInstanceTypeRightSizingMethod"]
                )
            if "launchDisposition" in effective_config:
                drs_update["launchDisposition"] = effective_config[
                    "launchDisposition"
                ]

            if len(drs_update) > 1:
                drs_client.update_launch_configuration(**drs_update)
                print(f"Updated DRS launch config for {server_id}")

            # Update EC2 launch template with network/instance settings
            template_data = {}

            if effective_config.get("instanceType"):
                template_data["InstanceType"] = effective_config[
                    "instanceType"
                ]

            # Handle network interfaces with static IP support
            if (
                effective_config.get("subnetId")
                or effective_config.get("securityGroupIds")
                or effective_config.get("staticPrivateIp")
            ):
                network_interface = {"DeviceIndex": 0}

                # Static private IP takes precedence
                if effective_config.get("staticPrivateIp"):
                    network_interface["PrivateIpAddress"] = effective_config[
                        "staticPrivateIp"
                    ]
                    print(
                        f"Setting static IP {effective_config['staticPrivateIp']} for {server_id}"
                    )

                if effective_config.get("subnetId"):
                    network_interface["SubnetId"] = effective_config[
                        "subnetId"
                    ]
                if effective_config.get("securityGroupIds"):
                    network_interface["Groups"] = effective_config[
                        "securityGroupIds"
                    ]
                template_data["NetworkInterfaces"] = [network_interface]

            if effective_config.get("instanceProfileName"):
                template_data["IamInstanceProfile"] = {
                    "Name": effective_config["instanceProfileName"]
                }

            if template_data:
                ec2_client.create_launch_template_version(
                    LaunchTemplateId=template_id,
                    LaunchTemplateData=template_data,
                    VersionDescription="DRS Orchestration pre-recovery update",
                )
                ec2_client.modify_launch_template(
                    LaunchTemplateId=template_id, DefaultVersion="$Latest"
                )
                print(
                    f"Updated EC2 launch template {template_id} for {server_id}"
                )

        except Exception as e:
            print(
                f"Warning: Failed to apply launch config to {server_id}: {e}"
            )
            # Continue with other servers - partial success is acceptable


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
    - update_wave_status: Poll DRS job and check server launch status
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
    elif action == "update_wave_status":
        return update_wave_status(event)
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
            f"DEBUG: After start_wave_recovery - job_id={state.get('job_id')}, region={state.get('region')}, server_ids={state.get('server_ids')}"
        )
    else:
        print("No waves to execute")
        state["all_waves_completed"] = True
        state["status"] = "completed"

    print(
        f"DEBUG: Returning state with job_id={state.get('job_id')}, wave_completed={state.get('wave_completed')}, status={state.get('status')}"
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
    paused_before_wave = state.get(
        "paused_before_wave", state.get("current_wave_number", 0) + 1
    )

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

    print(
        f"⏯️ Resuming execution {execution_id}, starting wave {paused_before_wave}"
    )

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
                        f"Server {server_id} missing tag {tag_key}={tag_value}. Available DRS tags: {list(drs_tags.keys())}"
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


def start_wave_recovery(state: Dict, wave_number: int) -> None:
    """
    Start DRS recovery for a wave with tag-based server resolution.

    Modifies state in-place (archive pattern) to update current wave tracking,
    job details, and wave results.

    Workflow:
    1. Retrieve Protection Group configuration from DynamoDB
    2. Resolve servers using tag-based discovery (execution-time resolution)
    3. Apply Protection Group launch configuration to DRS servers
    4. Start DRS recovery job (drill or production)
    5. Update state with job details and initial server statuses
    6. Store wave result in DynamoDB for frontend display

    Tag-Based Resolution (AWSM-1103):
    Servers are resolved at execution time by querying DRS for servers matching
    the Protection Group's serverSelectionTags. This enables dynamic discovery
    without maintaining static server lists. The pattern supports:
    - Auto-scaling: New servers automatically included if tags match
    - Multi-tenant: Customer/Environment tags scope recovery operations
    - Priority-based waves: dr:priority maps to wave numbers (critical→1, high→2, etc.)

    Wave Execution (AWSM-1103):
    - Sequential waves: This wave must complete before next wave starts
    - Parallel within wave: All servers launched simultaneously via batch API
    - Failure tolerance: Individual server failures don't stop wave execution

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
        Failures set wave_completed=True and status='failed' to stop execution.
        Empty server lists (no tags matched) mark wave complete without error.

    HRP Platform Extension:
        Other technology adapters (Aurora, ECS, Lambda, Route53) will implement
        similar start_wave_recovery functions with service-specific APIs while
        maintaining the same wave execution pattern and state management.
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
        pg_response = get_protection_groups_table().get_item(
            Key={"groupId": protection_group_id}
        )
        if "Item" not in pg_response:
            print(f"Protection Group {protection_group_id} not found")
            state["wave_completed"] = True
            state["status"] = "failed"
            state["error"] = (
                f"Protection Group {protection_group_id} not found"
            )
            return

        pg = pg_response["Item"]
        region = pg.get("region", "us-east-1")

        # Tag-based server resolution at execution time (AWSM-1103)
        selection_tags = pg.get("serverSelectionTags", {})

        if selection_tags:
            print(
                f"Resolving servers for PG {protection_group_id} with tags: {selection_tags}"
            )
            account_context = get_account_context(state)
            server_ids = query_drs_servers_by_tags(
                region, selection_tags, account_context
            )
            print(f"Resolved {len(server_ids)} servers from tags")
        else:
            # Fallback: explicit serverIds from wave (legacy support)
            server_ids = wave.get("serverIds", [])
            print(
                f"Using explicit serverIds from wave: {len(server_ids)} servers"
            )

        if not server_ids:
            print(
                f"Wave {wave_number} has no servers (no tags matched), marking complete"
            )
            state["wave_completed"] = True
            return

        print(f"Starting DRS recovery for wave {wave_number} ({wave_name})")
        print(f"Region: {region}, Servers: {server_ids}, isDrill: {is_drill}")

        # Create DRS client with cross-account support
        account_context = get_account_context(state)
        drs_client = create_drs_client(region, account_context)

        # Apply Protection Group launch config before recovery
        launch_config = pg.get("launchConfig")
        if launch_config:
            print(
                f"Applying launchConfig to {len(server_ids)} servers before recovery"
            )
            apply_launch_config_before_recovery(
                drs_client, server_ids, launch_config, region, pg
            )

        source_servers = [{"sourceServerID": sid} for sid in server_ids]

        response = drs_client.start_recovery(
            isDrill=is_drill, sourceServers=source_servers
        )

        job_id = response["job"]["jobID"]
        print(f"✅ DRS Job created: {job_id}")

        # Build initial serverStatuses - execution-poller enriches with details
        server_statuses = []
        for server_id in server_ids:
            server_statuses.append(
                {
                    "sourceServerId": server_id,
                    "serverName": server_id,  # Poller updates with Name tag
                    "hostname": "",
                    "launchStatus": "PENDING",
                    "instanceId": "",
                    "privateIp": "",
                    "instanceType": "",
                    "launchTime": 0,
                }
            )

        # Update state in-place (archive pattern - AWSM-1103)
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

        # Update DynamoDB with wave data at specific index to preserve completed waves
        try:
            get_execution_history_table().update_item(
                Key={"executionId": execution_id, "planId": state["plan_id"]},
                UpdateExpression=f"SET waves[{wave_number}] = :wave, drsJobId = :job_id, drsRegion = :region, #status = :status",
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


def update_wave_status(event: Dict) -> Dict:  # noqa: C901
    """
    Poll DRS job status and track server launch progress.

    Called repeatedly by Step Functions Wait state until wave completes or times out.
    Checks for cancellation, tracks server launch status, and manages wave transitions.

    Polling Workflow:
    1. Check for execution cancellation (user-initiated)
    2. Verify job exists and get current status
    3. Track individual server launch status (PENDING → IN_PROGRESS → LAUNCHED/FAILED)
    4. Determine current phase (CONVERTING → LAUNCHING → LAUNCHED)
    5. Check completion conditions (all launched, any failed, timeout)
    6. Handle wave completion: start next wave or pause/complete execution

    Server Launch States:
    - PENDING: Initial state, may be converting snapshots
    - IN_PROGRESS: Actively launching EC2 instance
    - LAUNCHED: Successfully created recovery instance
    - FAILED/TERMINATED: Launch failed

    Wave Completion Conditions:
    - Success: All servers LAUNCHED
    - Failure: Any server FAILED or TERMINATED
    - Timeout: Exceeded current_wave_max_wait_time (default 1 year)
    - Cancellation: User cancelled execution

    Archive Pattern: State passed directly, returns complete state object.

    Args:
        event: Contains state (application) with job_id, region, wave tracking

    Returns:
        Complete state object with updated wave status and completion flags

    State Updates:
    - current_wave_total_wait_time: Incremented by update_time
    - wave_completed: Set to True when wave finishes (success/failure/timeout)
    - all_waves_completed: Set to True when all waves done or execution cancelled
    - status: Updated to completed/failed/cancelled/paused
    - wave_results: Updated with server statuses and completion time

    Note:
        DynamoDB updates for server details (instanceId, privateIp) are handled
        by execution-poller Lambda to avoid race conditions.
    """
    # State passed directly (archive pattern)
    state = event.get("application", event)
    job_id = state.get("job_id")
    wave_number = state.get("current_wave_number", 0)
    region = state.get("region", "us-east-1")
    execution_id = state.get("execution_id")
    plan_id = state.get("plan_id")

    # Check for cancellation at start of every poll cycle
    if execution_id and plan_id:
        try:
            exec_check = get_execution_history_table().get_item(
                Key={"executionId": execution_id, "planId": plan_id}
            )
            exec_status = exec_check.get("Item", {}).get("status", "")
            if exec_status == "CANCELLING":
                print("⚠️ Execution cancelled (detected at poll start)")
                state["all_waves_completed"] = True
                state["wave_completed"] = True
                state["status"] = "cancelled"
                get_execution_history_table().update_item(
                    Key={"executionId": execution_id, "planId": plan_id},
                    UpdateExpression="SET #status = :status, endTime = :end",
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={
                        ":status": "CANCELLED",
                        ":end": int(time.time()),
                    },
                    ConditionExpression="attribute_exists(executionId)",
                )
                return state
        except Exception as e:
            print(f"Error checking cancellation status: {e}")

    if not job_id:
        print("No job_id found, marking wave complete")
        state["wave_completed"] = True
        return state

    # Update total wait time and check for timeout
    update_time = state.get("current_wave_update_time", 30)
    total_wait = state.get("current_wave_total_wait_time", 0) + update_time
    max_wait = state.get("current_wave_max_wait_time", 31536000)
    state["current_wave_total_wait_time"] = total_wait

    print(
        f"Checking status for job {job_id}, wait time: {total_wait}s / {max_wait}s"
    )

    if total_wait >= max_wait:
        print(f"❌ Wave {wave_number} TIMEOUT")
        state["wave_completed"] = True
        state["status"] = "timeout"
        state["error"] = f"Wave timed out after {total_wait}s"
        return state

    try:
        # Create DRS client with cross-account support
        account_context = get_account_context(state)
        drs_client = create_drs_client(region, account_context)
        job_response = drs_client.describe_jobs(filters={"jobIDs": [job_id]})

        if not job_response.get("items"):
            print(f"Job {job_id} not found")
            state["wave_completed"] = True
            state["status"] = "failed"
            state["error"] = f"Job {job_id} not found"
            return state

        job = job_response["items"][0]
        job_status = job.get("status")
        participating_servers = job.get("participatingServers", [])

        print(
            f"Job {job_id} status: {job_status}, servers: {len(participating_servers)}"
        )

        if not participating_servers:
            if (
                job_status in DRS_JOB_STATUS_WAIT_STATES
                or job_status == "STARTED"
            ):
                print("Job still initializing")
                state["wave_completed"] = False
                return state
            elif job_status == "COMPLETED":
                print("❌ Job COMPLETED but no servers")
                state["wave_completed"] = True
                state["status"] = "failed"
                state["error"] = (
                    "DRS job completed but no participating servers"
                )
                return state
            else:
                state["wave_completed"] = False
                return state

        # Preserve existing server data (serverName, hostname) from state
        existing_statuses = {}
        for wr in state.get("wave_results", []):
            if wr.get("waveNumber") == wave_number:
                for ss in wr.get("serverStatuses", []):
                    existing_statuses[ss.get("sourceServerId")] = ss
                break

        # Track server launch progress
        launched_count = 0
        failed_count = 0
        launching_count = 0
        converting_count = 0
        server_statuses = []

        for server in participating_servers:
            server_id = server.get("sourceServerID")
            launch_status = server.get("launchStatus", "PENDING")
            recovery_instance_id = server.get("recoveryInstanceID")

            print(f"Server {server_id}: {launch_status}")

            # Preserve existing data and update with new status
            existing = existing_statuses.get(server_id, {})
            server_statuses.append(
                {
                    "sourceServerId": server_id,
                    "serverName": existing.get("serverName", server_id),
                    "hostname": existing.get("hostname", ""),
                    "launchStatus": launch_status,
                    "recoveryInstanceId": recovery_instance_id
                    or existing.get("recoveryInstanceId", ""),
                    "instanceId": existing.get("instanceId", ""),
                    "privateIp": existing.get("privateIp", ""),
                    "instanceType": existing.get("instanceType", ""),
                    "launchTime": existing.get("launchTime", 0),
                }
            )

            if launch_status in DRS_JOB_SERVERS_COMPLETE_SUCCESS_STATES:
                launched_count += 1
            elif launch_status in DRS_JOB_SERVERS_COMPLETE_FAILURE_STATES:
                failed_count += 1
            elif launch_status == "IN_PROGRESS":
                # Check if it's launching or converting phase
                # This is determined by looking at the job events or server state
                launching_count += 1
            elif launch_status == "PENDING":
                # Could be converting or initial phase
                converting_count += 1

        total_servers = len(participating_servers)
        print(
            f"Progress: {launched_count}/{total_servers} launched, {failed_count} failed, {launching_count} launching, {converting_count} converting"
        )

        # Get job events to determine current phase
        job_events = []
        try:
            events_response = drs_client.describe_job_log_items(jobID=job_id)
            job_events = events_response.get("items", [])
        except Exception as e:
            print(f"Warning: Could not fetch job events: {e}")

        # Determine current phase from recent job events
        current_phase = "STARTED"
        recent_events = sorted(
            job_events, key=lambda x: x.get("eventDateTime", ""), reverse=True
        )[:10]

        for event in recent_events:
            event_type = event.get("event", "").upper()
            if "LAUNCHING" in event_type or "LAUNCH" in event_type:
                current_phase = "LAUNCHING"
                break
            elif "CONVERSION" in event_type and "STARTED" in event_type:
                current_phase = "CONVERTING"
                break

        print(f"Current phase determined from events: {current_phase}")

        # Determine current wave status based on phase and server statuses
        current_wave_status = current_phase

        if launched_count > 0 and launched_count < total_servers:
            current_wave_status = "IN_PROGRESS"

        # NOTE: DynamoDB updates are handled by execution-poller Lambda
        # to avoid race conditions and data overwrites
        if current_wave_status != "STARTED":
            print(
                f"Wave {wave_number} status changed to {current_wave_status} "
                "(DynamoDB update handled by execution-poller)"
            )

        # Check if job completed but no instances created
        if job_status == "COMPLETED" and launched_count == 0:
            print("❌ Job COMPLETED but no instances launched")
            state["wave_completed"] = True
            state["status"] = "failed"
            state["error"] = (
                "DRS job completed but no recovery instances created"
            )
            return state

        # All servers launched
        if launched_count == total_servers and failed_count == 0:
            print(
                f"✅ Wave {wave_number} COMPLETE - all {launched_count} servers launched"
            )

            state["wave_completed"] = True
            state["completed_waves"] = state.get("completed_waves", 0) + 1

            # Update wave result in Step Functions state
            # EC2 instance details (instanceId, privateIp, instanceType) are
            # populated by execution-poller which is the single source of truth
            for wr in state.get("wave_results", []):
                if wr.get("waveNumber") == wave_number:
                    wr["status"] = "COMPLETED"
                    wr["endTime"] = int(time.time())
                    break

            # Check if cancelled or paused
            try:
                exec_check = get_execution_history_table().get_item(
                    Key={"executionId": execution_id, "planId": plan_id}
                )
                exec_status = exec_check.get("Item", {}).get("status", "")

                if exec_status == "CANCELLING":
                    print("⚠️ Execution cancelled")
                    end_time = int(time.time())
                    state["all_waves_completed"] = True
                    state["status"] = "cancelled"
                    state["status_reason"] = "Execution cancelled by user"
                    state["end_time"] = end_time
                    if state.get("start_time"):
                        state["duration_seconds"] = (
                            end_time - state["start_time"]
                        )
                    get_execution_history_table().update_item(
                        Key={"executionId": execution_id, "planId": plan_id},
                        UpdateExpression="SET #status = :status, endTime = :end",
                        ExpressionAttributeNames={"#status": "status"},
                        ExpressionAttributeValues={
                            ":status": "CANCELLED",
                            ":end": int(time.time()),
                        },
                        ConditionExpression="attribute_exists(executionId)",
                    )
                    return state
            except Exception as e:
                print(f"Error checking execution status: {e}")

            # Move to next wave
            next_wave = wave_number + 1
            waves_list = state.get("waves", [])

            if next_wave < len(waves_list):
                next_wave_config = waves_list[next_wave]
                pause_before = next_wave_config.get("pauseBeforeWave", False)

                if pause_before:
                    print(f"⏸️ Pausing before wave {next_wave}")
                    state["status"] = "paused"
                    state["paused_before_wave"] = next_wave

                    # Mark execution as PAUSED for manual resume
                    try:
                        get_execution_history_table().update_item(
                            Key={
                                "executionId": execution_id,
                                "planId": plan_id,
                            },
                            UpdateExpression="SET #status = :status, pausedBeforeWave = :wave",
                            ExpressionAttributeNames={"#status": "status"},
                            ExpressionAttributeValues={
                                ":status": "PAUSED",
                                ":wave": next_wave,
                            },
                            ConditionExpression="attribute_exists(executionId)",
                        )
                        print(
                            f"✅ Execution paused before wave {next_wave}, waiting for manual resume"
                        )
                    except Exception as e:
                        print(f"Error pausing execution: {e}")

                    # Return immediately when paused - don't continue to next wave
                    return state

                print(f"Starting next wave: {next_wave}")
                start_wave_recovery(state, next_wave)
            else:
                print("✅ ALL WAVES COMPLETE")
                end_time = int(time.time())
                state["all_waves_completed"] = True
                state["status"] = "completed"
                state["status_reason"] = "All waves completed successfully"
                state["end_time"] = end_time
                state["completed_waves"] = len(waves_list)
                if state.get("start_time"):
                    state["duration_seconds"] = end_time - state["start_time"]
                get_execution_history_table().update_item(
                    Key={"executionId": execution_id, "planId": plan_id},
                    UpdateExpression="SET #status = :status, endTime = :end",
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={
                        ":status": "COMPLETED",
                        ":end": end_time,
                    },
                    ConditionExpression="attribute_exists(executionId)",
                )

        elif failed_count > 0:
            print(
                f"❌ Wave {wave_number} FAILED - {failed_count} servers failed"
            )
            end_time = int(time.time())
            state["wave_completed"] = True
            state["status"] = "failed"
            state["status_reason"] = (
                f"Wave {wave_number} failed: {failed_count} servers failed to launch"
            )
            state["error"] = f"{failed_count} servers failed to launch"
            state["error_code"] = "WAVE_LAUNCH_FAILED"
            state["failed_waves"] = 1
            state["end_time"] = end_time
            if state.get("start_time"):
                state["duration_seconds"] = end_time - state["start_time"]
            # NOTE: DynamoDB update handled by execution-poller Lambda

        else:
            print(
                f"⏳ Wave {wave_number} in progress - {launched_count}/{total_servers}"
            )
            state["wave_completed"] = False

    except Exception as e:
        print(f"Error checking DRS job status: {e}")
        import traceback

        traceback.print_exc()
        state["wave_completed"] = True
        state["status"] = "failed"
        state["error"] = str(e)

    return state
