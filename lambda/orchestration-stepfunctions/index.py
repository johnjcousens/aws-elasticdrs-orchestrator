"""
Step Functions Orchestration Lambda
Archive pattern: Lambda owns ALL state via OutputPath

State is at root level ($), not nested under $.application
All functions return the COMPLETE state object

NOTE: Security validation is handled at the API layer (Cognito + API Gateway).
This Lambda receives trusted data from Step Functions internal flow.
Do NOT add sanitization here - it breaks the archive pattern where state
must be modified in place.
"""

import json
import os
import time
from decimal import Decimal
from typing import Dict, List

import boto3

# Environment variables
PROTECTION_GROUPS_TABLE = os.environ.get("PROTECTION_GROUPS_TABLE")
RECOVERY_PLANS_TABLE = os.environ.get("RECOVERY_PLANS_TABLE")
EXECUTION_HISTORY_TABLE = os.environ.get("EXECUTION_HISTORY_TABLE")

# AWS clients
dynamodb = boto3.resource("dynamodb")

# DynamoDB tables (lazy init)
_protection_groups_table = None
_recovery_plans_table = None
_execution_history_table = None


def get_protection_groups_table():
    global _protection_groups_table
    if _protection_groups_table is None:
        _protection_groups_table = dynamodb.Table(PROTECTION_GROUPS_TABLE)
    return _protection_groups_table


def get_recovery_plans_table():
    global _recovery_plans_table
    if _recovery_plans_table is None:
        _recovery_plans_table = dynamodb.Table(RECOVERY_PLANS_TABLE)
    return _recovery_plans_table


def get_execution_history_table():
    global _execution_history_table
    if _execution_history_table is None:
        _execution_history_table = dynamodb.Table(EXECUTION_HISTORY_TABLE)
    return _execution_history_table


def get_account_context(state: Dict) -> Dict:
    """
    Get account context from state, handling both camelCase and snake_case.

    Initial execution uses camelCase (accountContext) from Step Functions input.
    Resume uses snake_case (account_context) from SendTaskSuccess output.
    """
    return state.get("accountContext") or state.get("account_context", {})


def create_drs_client(region: str, account_context: Dict = None):
    """
    Create DRS client with optional cross-account access

    Args:
        region: AWS region for DRS operations
        account_context: Dict containing accountId and assumeRoleName for cross-account access

    Returns:
        boto3 DRS client
    """
    # Check if cross-account access is needed - only if accountId is provided, not empty, and not current account
    if (account_context and 
        account_context.get("accountId") and 
        account_context.get("accountId").strip() and  # Not empty string
        not account_context.get("isCurrentAccount", False)):  # Not current account
        
        account_id = account_context["accountId"]
        role_name = account_context.get(
            "assumeRoleName", "drs-orchestration-cross-account-role"
        )

        print(
            f"Creating cross-account DRS client for account {account_id} in region {region}"
        )

        # Assume role in target account
        sts_client = boto3.client("sts", region_name=region)
        session_name = f"drs-orchestration-{int(time.time())}"

        try:
            assumed_role = sts_client.assume_role(
                RoleArn=f"arn:aws:iam::{account_id}:role/{role_name}",  # noqa: E231
                RoleSessionName=session_name,
            )

            credentials = assumed_role["Credentials"]
            print(
                f"Successfully assumed role {role_name} in account {account_id}"
            )

            return boto3.client(
                "drs",
                region_name=region,
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
            )
        except Exception as e:
            print(
                f"Failed to assume role {role_name} in account {account_id}: {e}"
            )
            raise

    # Default: use current account credentials
    print(f"Creating DRS client for current account in region {region}")
    return boto3.client("drs", region_name=region)


def apply_launch_config_before_recovery(
    drs_client,
    server_ids: List[str],
    launch_config: Dict,
    region: str
) -> None:
    """
    Apply Protection Group launch config to DRS servers before starting recovery.
    
    This ensures the DRS launch templates have the correct subnet, security groups,
    instance type, etc. from the Protection Group configuration.
    """
    ec2_client = boto3.client("ec2", region_name=region)
    
    for server_id in server_ids:
        try:
            # Get current DRS launch configuration to find the EC2 launch template
            current_config = drs_client.get_launch_configuration(
                sourceServerID=server_id
            )
            template_id = current_config.get("ec2LaunchTemplateID")
            
            if not template_id:
                print(f"No launch template found for {server_id}, skipping")
                continue
            
            # Update DRS launch configuration settings
            drs_update = {"sourceServerID": server_id}
            if "copyPrivateIp" in launch_config:
                drs_update["copyPrivateIp"] = launch_config["copyPrivateIp"]
            if "copyTags" in launch_config:
                drs_update["copyTags"] = launch_config["copyTags"]
            if "licensing" in launch_config:
                drs_update["licensing"] = launch_config["licensing"]
            if "targetInstanceTypeRightSizingMethod" in launch_config:
                drs_update["targetInstanceTypeRightSizingMethod"] = (
                    launch_config["targetInstanceTypeRightSizingMethod"]
                )
            if "launchDisposition" in launch_config:
                drs_update["launchDisposition"] = launch_config["launchDisposition"]
            
            if len(drs_update) > 1:
                drs_client.update_launch_configuration(**drs_update)
                print(f"Updated DRS launch config for {server_id}")
            
            # Update EC2 launch template with network/instance settings
            template_data = {}
            
            if launch_config.get("instanceType"):
                template_data["InstanceType"] = launch_config["instanceType"]
            
            if launch_config.get("subnetId") or launch_config.get("securityGroupIds"):
                network_interface = {"DeviceIndex": 0}
                if launch_config.get("subnetId"):
                    network_interface["SubnetId"] = launch_config["subnetId"]
                if launch_config.get("securityGroupIds"):
                    network_interface["Groups"] = launch_config["securityGroupIds"]
                template_data["NetworkInterfaces"] = [network_interface]
            
            if launch_config.get("instanceProfileName"):
                template_data["IamInstanceProfile"] = {
                    "Name": launch_config["instanceProfileName"]
                }
            
            if template_data:
                ec2_client.create_launch_template_version(
                    LaunchTemplateId=template_id,
                    LaunchTemplateData=template_data,
                    VersionDescription="DRS Orchestration pre-recovery update",
                )
                ec2_client.modify_launch_template(
                    LaunchTemplateId=template_id,
                    DefaultVersion="$Latest"
                )
                print(f"Updated EC2 launch template {template_id} for {server_id}")
                
        except Exception as e:
            print(f"Warning: Failed to apply launch config to {server_id}: {e}")
            # Continue with other servers - don't fail the whole recovery


# DRS job status constants
DRS_JOB_STATUS_COMPLETE_STATES = ["COMPLETED"]
DRS_JOB_STATUS_WAIT_STATES = ["PENDING", "STARTED"]

# DRS server launch status constants
DRS_JOB_SERVERS_COMPLETE_SUCCESS_STATES = ["LAUNCHED"]
DRS_JOB_SERVERS_COMPLETE_FAILURE_STATES = ["FAILED", "TERMINATED"]
DRS_JOB_SERVERS_WAIT_STATES = ["PENDING", "IN_PROGRESS"]


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types from DynamoDB"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Step Functions orchestration handler - Archive pattern

    All actions return COMPLETE state object (Lambda owns state)
    """
    print(f"Event: {json.dumps(event, cls=DecimalEncoder)}")

    action = event.get("action")

    # Extract account context for multi-account support
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
    Initialize wave plan execution
    Returns COMPLETE state object (archive pattern)
    """
    plan = event.get("plan", {})
    execution_id = event.get("execution", "")
    is_drill = event.get("isDrill", True)
    account_context = event.get("accountContext", {})

    plan_id = plan.get("planId", "")
    waves = plan.get("waves", [])

    print(f"Beginning wave plan for execution {execution_id}, plan {plan_id}")
    print(f"Total waves: {len(waves)}, isDrill: {is_drill}")

    # Initialize state object (at root level - archive pattern)
    # Enhanced for parent Step Function integration
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
        # Completion flags (for Step Functions Choice states)
        "all_waves_completed": False,
        "wave_completed": False,
        # Polling configuration
        "current_wave_update_time": 30,
        "current_wave_total_wait_time": 0,
        "current_wave_max_wait_time": 31536000,  # 1 year (Step Functions supports up to 1 year pauses)
        # Status for parent orchestrator branching
        # Values: 'running', 'paused', 'completed', 'failed', 'cancelled'
        "status": "running",
        "status_reason": None,
        # Results for downstream processing
        "wave_results": [],
        "recovery_instance_ids": [],  # EC2 instance IDs of recovered servers
        "recovery_instance_ips": [],  # Private IPs of recovered servers
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
        # DEBUG: Log state after start_wave_recovery to verify job_id is set
        print(f"DEBUG: After start_wave_recovery - job_id={state.get('job_id')}, region={state.get('region')}, server_ids={state.get('server_ids')}")
    else:
        print("No waves to execute")
        state["all_waves_completed"] = True
        state["status"] = "completed"

    # DEBUG: Log final state being returned
    print(f"DEBUG: Returning state with job_id={state.get('job_id')}, wave_completed={state.get('wave_completed')}, status={state.get('status')}")
    return state


def store_task_token(event: Dict) -> Dict:
    """
    Store task token for callback pattern (pause/resume)

    ARCHIVE PATTERN: Returns COMPLETE state object
    The state includes paused_before_wave so resume knows which wave to start
    """
    # State is passed directly (archive pattern)
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

    # Store task token in DynamoDB
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

    # ARCHIVE PATTERN: Return COMPLETE state
    # This state will be passed to ResumeWavePlan after SendTaskSuccess
    state["paused_before_wave"] = paused_before_wave
    return state


def resume_wave(event: Dict) -> Dict:
    """
    Resume execution by starting the paused wave

    ARCHIVE PATTERN: State is passed directly, returns COMPLETE state
    """
    # State is passed directly (archive pattern)
    state = event.get("application", event)
    execution_id = state.get("execution_id")
    plan_id = state.get("plan_id")
    paused_before_wave = state.get("paused_before_wave", 0)

    # Convert Decimal to int if needed (DynamoDB returns Decimal)
    if isinstance(paused_before_wave, Decimal):
        paused_before_wave = int(paused_before_wave)

    print(
        f"⏯️ Resuming execution {execution_id}, starting wave {paused_before_wave}"
    )

    # Reset status to running
    state["status"] = "running"
    state["wave_completed"] = False
    state["paused_before_wave"] = None

    # Update DynamoDB
    try:
        get_execution_history_table().update_item(
            Key={"executionId": execution_id, "planId": plan_id},
            UpdateExpression="SET #status = :status REMOVE taskToken, pausedBeforeWave",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": "RUNNING"},
        )
    except Exception as e:
        print(f"Error updating execution status: {e}")

    # Start the wave that was paused
    start_wave_recovery(state, paused_before_wave)

    return state


def query_drs_servers_by_tags(  # noqa: C901
    region: str, tags: Dict[str, str], account_context: Dict = None
) -> List[str]:
    """
    Query DRS source servers that have ALL specified tags.
    Uses AND logic - DRS source server must have all tags to be included.

    This queries the DRS source server tags directly, not EC2 instance tags.
    Returns list of source server IDs for orchestration.
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

        # Filter servers that match ALL specified tags
        matching_server_ids = []

        for server in all_servers:
            server_id = server.get("sourceServerID", "")

            # Get DRS source server tags directly from server object
            drs_tags = server.get("tags", {})

            # Check if DRS server has ALL required tags with matching values
            # Use case-insensitive matching and strip whitespace for robustness
            matches_all = True
            for tag_key, tag_value in tags.items():
                # Normalize tag key and value (strip whitespace, case-insensitive)
                normalized_required_key = tag_key.strip()
                normalized_required_value = tag_value.strip().lower()

                # Check if any DRS tag matches (case-insensitive)
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


def get_drs_server_details(drs_client, server_ids: List[str]) -> Dict[str, Dict]:
    """
    Get DRS source server details (Name tag, hostname) for server information display.
    
    Uses data already available from DRS source servers - no extra EC2 API calls needed.
    
    Args:
        drs_client: Boto3 DRS client
        server_ids: List of DRS source server IDs
        
    Returns:
        Dict mapping server_id to {serverName, hostname}
    """
    server_details = {}
    
    if not server_ids:
        return server_details
    
    try:
        # Query DRS for source server details
        response = drs_client.describe_source_servers(
            filters={"sourceServerIDs": server_ids}
        )
        
        for server in response.get("items", []):
            server_id = server.get("sourceServerID", "")
            
            # Get Name tag from DRS source server tags
            name_tag = server.get("tags", {}).get("Name", "")
            
            # Get hostname from identification hints
            hostname = (
                server.get("sourceProperties", {})
                .get("identificationHints", {})
                .get("hostname", "")
            )
            
            server_details[server_id] = {
                "serverName": name_tag or hostname or server_id,
                "hostname": hostname,
            }
            
    except Exception as e:
        print(f"Warning: Could not get DRS server details: {e}")
        # Return empty details - frontend will show server IDs
        
    return server_details


def start_wave_recovery(state: Dict, wave_number: int) -> None:
    """
    Start DRS recovery for a wave
    Modifies state in place (archive pattern)

    Tag-based server resolution: Servers are resolved at execution time
    by querying DRS for servers matching the Protection Group's tags.
    """
    waves = state["waves"]
    wave = waves[wave_number]
    is_drill = state["is_drill"]
    execution_id = state["execution_id"]

    wave_name = wave.get("waveName", f"Wave {wave_number + 1}")

    # Get Protection Group
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

        # TAG-BASED RESOLUTION: Resolve servers at execution time using tags
        selection_tags = pg.get("serverSelectionTags", {})

        if selection_tags:
            # Resolve servers by tags at execution time
            print(
                f"Resolving servers for PG {protection_group_id} with tags: {selection_tags}"
            )
            account_context = get_account_context(state)
            server_ids = query_drs_servers_by_tags(
                region, selection_tags, account_context
            )
            print(f"Resolved {len(server_ids)} servers from tags")
        else:
            # Fallback: Check if wave has explicit serverIds (legacy support)
            server_ids = wave.get("serverIds", [])
            print(
                f"Using explicit serverIds from wave: {len(server_ids)} servers"
            )

        if not server_ids:
            print(
                f"Wave {wave_number} has no servers (no tags matched or no servers found), marking complete"
            )
            state["wave_completed"] = True
            return

        print(f"Starting DRS recovery for wave {wave_number} ({wave_name})")
        print(f"Region: {region}, Servers: {server_ids}, isDrill: {is_drill}")

        # Create DRS client with cross-account support
        account_context = get_account_context(state)
        drs_client = create_drs_client(region, account_context)

        # Apply Protection Group launch config to DRS before starting recovery
        launch_config = pg.get("launchConfig")
        if launch_config:
            print(f"Applying launchConfig to {len(server_ids)} servers before recovery")
            apply_launch_config_before_recovery(
                drs_client, server_ids, launch_config, region
            )

        source_servers = [{"sourceServerID": sid} for sid in server_ids]

        response = drs_client.start_recovery(
            isDrill=is_drill, sourceServers=source_servers
        )

        job_id = response["job"]["jobID"]
        print(f"✅ DRS Job created: {job_id}")

        # Get server details (Name tag, hostname) from DRS source servers
        server_details = get_drs_server_details(drs_client, server_ids)
        
        # Build serverStatuses with server details for frontend display
        server_statuses = []
        for server_id in server_ids:
            details = server_details.get(server_id, {})
            server_statuses.append({
                "sourceServerId": server_id,
                "serverName": details.get("serverName", server_id),
                "hostname": details.get("hostname", ""),
                "launchStatus": "PENDING",
                "instanceId": "",
                "privateIp": "",
                "launchTime": 0,
            })

        # Update state IN PLACE (archive pattern - critical!)
        state["current_wave_number"] = wave_number
        state["job_id"] = job_id
        state["region"] = region
        state["server_ids"] = server_ids
        state["wave_completed"] = False
        state["current_wave_total_wait_time"] = 0

        # Store wave result with serverStatuses for frontend display
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

        # Update DynamoDB with execution-level DRS job info and wave data
        try:
            get_execution_history_table().update_item(
                Key={"executionId": execution_id, "planId": state["plan_id"]},
                UpdateExpression="SET waves = list_append(if_not_exists(waves, :empty), :wave), drsJobId = :job_id, drsRegion = :region, #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":empty": [],
                    ":wave": [wave_result],
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
    Poll DRS job status and check server launch status

    ARCHIVE PATTERN: State is passed directly, returns COMPLETE state
    """
    # State is passed directly (archive pattern)
    state = event.get("application", event)
    job_id = state.get("job_id")
    wave_number = state.get("current_wave_number", 0)
    region = state.get("region", "us-east-1")
    execution_id = state.get("execution_id")
    plan_id = state.get("plan_id")

    # Early check for cancellation - check at start of every poll cycle
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

    # Update total wait time
    update_time = state.get("current_wave_update_time", 30)
    total_wait = state.get("current_wave_total_wait_time", 0) + update_time
    max_wait = state.get("current_wave_max_wait_time", 31536000)  # 1 year default
    state["current_wave_total_wait_time"] = total_wait

    print(
        f"Checking status for job {job_id}, wait time: {total_wait}s / {max_wait}s"
    )

    # Check for timeout
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

        # Check server launch status
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

            server_statuses.append(
                {
                    "sourceServerId": server_id,
                    "launchStatus": launch_status,
                    "recoveryInstanceId": recovery_instance_id,
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

        # Check server launch status
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

            server_statuses.append(
                {
                    "sourceServerId": server_id,
                    "launchStatus": launch_status,
                    "recoveryInstanceId": recovery_instance_id,
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

        # Determine current wave status based on phase and server statuses
        current_wave_status = current_phase

        if launched_count > 0 and launched_count < total_servers:
            current_wave_status = "IN_PROGRESS"

        # Update wave status in DynamoDB if it has changed from STARTED
        if current_wave_status != "STARTED":
            print(
                f"Updating wave {wave_number} status to {current_wave_status}"
            )
            update_wave_in_dynamodb(
                execution_id,
                plan_id,
                wave_number,
                current_wave_status,
                server_statuses,
            )

        # Check if job completed but no instances created
        if job_status == "COMPLETED" and launched_count == 0:
            print("❌ Job COMPLETED but no instances launched")
            state["wave_completed"] = True
            state["status"] = "failed"
            state["error"] = (
                "DRS job completed but no recovery instances created"
            )
            update_wave_in_dynamodb(
                execution_id, plan_id, wave_number, "FAILED", server_statuses
            )
            return state

        # All servers launched
        if launched_count == total_servers and failed_count == 0:
            print(
                f"✅ Wave {wave_number} COMPLETE - all {launched_count} servers launched"
            )

            # Get EC2 instance IDs
            try:
                source_server_ids = [
                    s.get("sourceServerId") for s in server_statuses
                ]
                ri_response = drs_client.describe_recovery_instances(
                    filters={"sourceServerIDs": source_server_ids}
                )
                for ri in ri_response.get("items", []):
                    source_id = ri.get("sourceServerID")
                    for ss in server_statuses:
                        if ss.get("sourceServerId") == source_id:
                            ss["instanceId"] = ri.get("ec2InstanceID", "")
                            ss["recoveryInstanceId"] = ri.get(
                                "recoveryInstanceID", ""
                            )
                            break
            except Exception as e:
                print(
                    f"Warning: Could not fetch recovery instance details: {e}"
                )

            state["wave_completed"] = True
            state["completed_waves"] = state.get("completed_waves", 0) + 1

            # Capture recovery instance IDs and IPs for parent orchestrator
            for ss in server_statuses:
                ec2_id = ss.get("instanceId")
                if ec2_id:
                    if ec2_id not in state.get("recovery_instance_ids", []):
                        state.setdefault("recovery_instance_ids", []).append(
                            ec2_id
                        )

            # Fetch private IPs from EC2 and update server_statuses
            try:
                ec2_ids = [
                    ss.get("instanceId")
                    for ss in server_statuses
                    if ss.get("instanceId")
                ]
                if ec2_ids:
                    ec2_client = boto3.client("ec2", region_name=region)
                    ec2_response = ec2_client.describe_instances(
                        InstanceIds=ec2_ids
                    )
                    # Build mapping of instance ID to details
                    instance_details = {}
                    for reservation in ec2_response.get("Reservations", []):
                        for instance in reservation.get("Instances", []):
                            instance_id = instance.get("InstanceId")
                            instance_details[instance_id] = {
                                "privateIp": instance.get("PrivateIpAddress", ""),
                                "instanceType": instance.get("InstanceType", ""),
                            }
                    
                    # Update server_statuses with EC2 details
                    for ss in server_statuses:
                        ec2_id = ss.get("instanceId")
                        if ec2_id and ec2_id in instance_details:
                            ss["privateIp"] = instance_details[ec2_id].get("privateIp", "")
                            ss["instanceType"] = instance_details[ec2_id].get("instanceType", "")
                            
                    # Also add to state-level list
                    for details in instance_details.values():
                        private_ip = details.get("privateIp")
                        if private_ip and private_ip not in state.get(
                            "recovery_instance_ips", []
                        ):
                            state.setdefault(
                                "recovery_instance_ips", []
                            ).append(private_ip)
            except Exception as e:
                print(f"Warning: Could not fetch EC2 IPs: {e}")

            # Update wave result
            for wr in state.get("wave_results", []):
                if wr.get("waveNumber") == wave_number:
                    wr["status"] = "COMPLETED"
                    wr["endTime"] = int(time.time())
                    wr["serverStatuses"] = server_statuses
                    break

            update_wave_in_dynamodb(
                execution_id,
                plan_id,
                wave_number,
                "COMPLETED",
                server_statuses,
            )

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
                            Key={"executionId": execution_id, "planId": plan_id},
                            UpdateExpression="SET #status = :status, pausedBeforeWave = :wave",
                            ExpressionAttributeNames={"#status": "status"},
                            ExpressionAttributeValues={
                                ":status": "PAUSED",
                                ":wave": next_wave,
                            },
                            ConditionExpression="attribute_exists(executionId)",
                        )
                        print(f"✅ Execution paused before wave {next_wave}, waiting for manual resume")
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
            update_wave_in_dynamodb(
                execution_id, plan_id, wave_number, "FAILED", server_statuses
            )

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


def update_wave_in_dynamodb(
    execution_id: str,
    plan_id: str,
    wave_number: int,
    status: str,
    server_statuses: List[Dict],
) -> None:
    """Update wave status in DynamoDB"""
    try:
        exec_response = get_execution_history_table().get_item(
            Key={"executionId": execution_id, "planId": plan_id}
        )

        if "Item" in exec_response:
            waves = exec_response["Item"].get("waves", [])
            for i, w in enumerate(waves):
                if w.get("waveNumber") == wave_number:
                    waves[i]["status"] = status
                    waves[i]["endTime"] = int(time.time())
                    waves[i]["serverStatuses"] = server_statuses
                    break

            get_execution_history_table().update_item(
                Key={"executionId": execution_id, "planId": plan_id},
                UpdateExpression="SET waves = :waves",
                ExpressionAttributeValues={":waves": waves},
                ConditionExpression="attribute_exists(executionId)",
            )
    except Exception as e:
        print(f"Error updating wave in DynamoDB: {e}")
