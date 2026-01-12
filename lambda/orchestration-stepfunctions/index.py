"""
Step Functions Orchestration Lambda
Archive pattern: Lambda owns ALL state via OutputPath

State is at root level ($), not nested under $.application
All functions return the COMPLETE state object
"""

import json
import os
import re
import time
from decimal import Decimal
from typing import Dict, List

import boto3

# Import security utilities (mandatory - no fallback)
from shared.security_utils import (
    log_security_event,
    safe_aws_client_call,
    sanitize_dynamodb_input,
    sanitize_string_input,
    validate_dynamodb_input,
    validate_drs_server_id,
)

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
    Get account context from state, handling both PascalCase and snake_case.

    Initial execution uses PascalCase (AccountContext) from Step Functions input.
    Resume uses snake_case (account_context) from SendTaskSuccess output.
    """
    return state.get("AccountContext") or state.get("account_context", {})


def create_drs_client(region: str, account_context: Dict = None):
    """
    Create DRS client with optional cross-account access

    Args:
        region: AWS region for DRS operations
        account_context: Dict containing accountId and assumeRoleName for cross-account access

    Returns:
        boto3 DRS client
    """
    # Security validation for inputs
    region = sanitize_string_input(region)
    
    # Validate region format
    if not re.match(r'^[a-z]{2}-[a-z]+-\d{1}$', region):
        raise ValueError(f"Invalid AWS region format: {region}")
    
    log_security_event("drs_client_creation", {
        "region": region,
        "cross_account": bool(account_context)
    })
    
    if account_context and account_context.get("accountId"):
        account_id = sanitize_string_input(account_context["accountId"])
        role_name = sanitize_string_input(account_context.get(
            "assumeRoleName", "drs-orchestration-cross-account-role"
        ))

        # Validate account ID format
        if not re.match(r'^\d{12}$', account_id):
            raise ValueError(f"Invalid AWS account ID format: {account_id}")

        print(
            f"Creating cross-account DRS client for account {account_id} in region {region}"
        )

        # Assume role in target account with safe AWS call
        def assume_role_call():
            sts_client = boto3.client("sts", region_name=region)
            session_name = f"drs-orchestration-{int(time.time())}"
            return sts_client.assume_role(
                RoleArn=f"arn:aws:iam::{account_id}:role/{role_name}",
                RoleSessionName=session_name,
            )

        assumed_role = safe_aws_client_call(assume_role_call)

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
    return boto3.client("drs", region_name=region)


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
    Step Functions orchestration handler with security - Archive pattern

    All actions return COMPLETE state object (Lambda owns state)
    """
    try:
        # Enhanced security logging
        log_security_event(
            "stepfunctions_orchestration_invoked",
            {
                "function_name": context.function_name,
                "request_id": context.aws_request_id,
                "action": event.get("action", "unknown"),
                "execution_id": event.get("execution", "unknown"),
            },
        )

        print(f"Event: {json.dumps(event, cls=DecimalEncoder)}")

        # Input validation
        action = event.get("action")
        if not action or not isinstance(action, str):
            log_security_event("invalid_stepfunctions_action", {"action": action})
            raise ValueError("Invalid or missing action parameter")

        # Sanitize the entire event
        sanitized_event = sanitize_dynamodb_input(event)
        
        # Extract account context for multi-account support
        account_context = sanitized_event.get("AccountContext", {})
        account_id = account_context.get("accountId")
        if account_id:
            print(f"Operating in account context: {account_id}")

        if action == "begin":
            return begin_wave_plan(sanitized_event)
        elif action == "update_wave_status":
            return update_wave_status(sanitized_event)
        elif action == "store_task_token":
            return store_task_token(sanitized_event)
        elif action == "resume_wave":
            return resume_wave(sanitized_event)
        else:
            log_security_event("unknown_stepfunctions_action", {"action": action})
            raise ValueError(f"Unknown action: {action}")

    except Exception as e:
        log_security_event(
            "stepfunctions_orchestration_error",
            {
                "error": str(e),
                "action": event.get("action", "unknown"),
                "execution_id": event.get("execution", "unknown"),
            },
            "ERROR"
        )
        raise


def begin_wave_plan(event: Dict) -> Dict:
    """
    Initialize wave plan execution with security validation
    Returns COMPLETE state object (archive pattern)
    """
    # Security validation and sanitization
    plan = sanitize_dynamodb_input(event.get("plan", {}))
    execution_id = sanitize_string_input(event.get("execution", ""))
    is_drill = event.get("isDrill", True)
    account_context = sanitize_dynamodb_input(event.get("AccountContext", {}))

    # Validate required parameters
    if not execution_id:
        raise ValueError("Missing required execution parameter")
    
    validate_dynamodb_input("executionId", execution_id)

    plan_id = sanitize_string_input(plan.get("planId", ""))
    if not plan_id:
        raise ValueError("Missing required planId in plan")
    
    validate_dynamodb_input("planId", plan_id)
    
    waves = plan.get("waves", [])

    log_security_event("wave_plan_begin", {
        "execution_id": execution_id,
        "plan_id": plan_id,
        "wave_count": len(waves),
        "is_drill": is_drill
    })

    print(f"Beginning wave plan for execution {execution_id}, plan {plan_id}")
    print(f"Total waves: {len(waves)}, isDrill: {is_drill}")

    # Initialize state object (at root level - archive pattern)
    # Enhanced for parent Step Function integration
    start_time = int(time.time())
    state = {
        # Core identifiers
        "plan_id": plan_id,
        "plan_name": sanitize_string_input(plan.get("planName", "")),
        "execution_id": execution_id,
        "is_drill": is_drill,
        "AccountContext": account_context,  # Step Functions expects uppercase
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
            ExpressionAttributeNames={"#status": "Status"},
            ExpressionAttributeValues={":status": "RUNNING"},
        )
    except Exception as e:
        print(f"Error updating execution status: {e}")

    # Start first wave
    if len(waves) > 0:
        start_wave_recovery(state, 0)
    else:
        print("No waves to execute")
        state["all_waves_completed"] = True
        state["status"] = "completed"

    return state


def store_task_token(event: Dict) -> Dict:
    """
    Store task token for callback pattern (pause/resume) with security validation

    ARCHIVE PATTERN: Returns COMPLETE state object
    The state includes paused_before_wave so resume knows which wave to start
    """
    # Security validation and sanitization
    sanitized_event = sanitize_dynamodb_input(event)
    
    # State is passed directly (archive pattern)
    state = sanitized_event.get("application", sanitized_event)
    task_token = sanitized_event.get("taskToken")
    
    # Validate required parameters
    execution_id = sanitize_string_input(state.get("execution_id", ""))
    plan_id = sanitize_string_input(state.get("plan_id", ""))
    
    if not execution_id or not plan_id:
        log_security_event("store_task_token_invalid_input", {
            "missing_execution_id": not execution_id,
            "missing_plan_id": not plan_id
        }, "ERROR")
        raise ValueError("Missing required execution_id or plan_id")
    
    validate_dynamodb_input("executionId", execution_id)
    validate_dynamodb_input("planId", plan_id)
    
    paused_before_wave = state.get(
        "paused_before_wave", state.get("current_wave_number", 0) + 1
    )

    log_security_event("store_task_token", {
        "execution_id": execution_id,
        "plan_id": plan_id,
        "paused_before_wave": paused_before_wave,
        "has_task_token": bool(task_token)
    })

    print(
        f"⏸️ Storing task token for execution {execution_id}, paused before wave {paused_before_wave}"
    )

    if not task_token:
        log_security_event("store_task_token_missing_token", {
            "execution_id": execution_id
        }, "ERROR")
        print("ERROR: No task token provided")
        raise ValueError("No task token provided for callback")

    # Sanitize task token
    task_token = sanitize_string_input(task_token, 4096)  # Task tokens can be long

    # Store task token in DynamoDB with safe operation
    try:
        def update_task_token():
            return get_execution_history_table().update_item(
                Key={"executionId": execution_id, "planId": plan_id},
                UpdateExpression="SET #status = :status, TaskToken = :token, PausedBeforeWave = :wave",
                ExpressionAttributeNames={"#status": "Status"},
                ExpressionAttributeValues={
                    ":status": "PAUSED",
                    ":token": task_token,
                    ":wave": paused_before_wave,
                },
            )
        
        safe_aws_client_call(update_task_token)
        print(f"✅ Task token stored for execution {execution_id}")
        
        log_security_event("store_task_token_success", {
            "execution_id": execution_id,
            "paused_before_wave": paused_before_wave
        })
    except Exception as e:
        log_security_event("store_task_token_error", {
            "execution_id": execution_id,
            "error": str(e)
        }, "ERROR")
        print(f"ERROR storing task token: {e}")
        raise

    # ARCHIVE PATTERN: Return COMPLETE state
    # This state will be passed to ResumeWavePlan after SendTaskSuccess
    state["paused_before_wave"] = paused_before_wave
    return state


def resume_wave(event: Dict) -> Dict:
    """
    Resume execution by starting the paused wave with security validation

    ARCHIVE PATTERN: State is passed directly, returns COMPLETE state
    """
    # Security validation and sanitization
    sanitized_event = sanitize_dynamodb_input(event)
    
    # State is passed directly (archive pattern)
    state = sanitized_event.get("application", sanitized_event)
    
    # Validate required parameters
    execution_id = sanitize_string_input(state.get("execution_id", ""))
    plan_id = sanitize_string_input(state.get("plan_id", ""))
    
    if not execution_id or not plan_id:
        log_security_event("resume_wave_invalid_input", {
            "missing_execution_id": not execution_id,
            "missing_plan_id": not plan_id
        }, "ERROR")
        raise ValueError("Missing required execution_id or plan_id")
    
    validate_dynamodb_input("executionId", execution_id)
    validate_dynamodb_input("planId", plan_id)
    
    paused_before_wave = state.get("paused_before_wave", 0)

    # Convert Decimal to int if needed (DynamoDB returns Decimal)
    if isinstance(paused_before_wave, Decimal):
        paused_before_wave = int(paused_before_wave)

    log_security_event("resume_wave", {
        "execution_id": execution_id,
        "plan_id": plan_id,
        "paused_before_wave": paused_before_wave
    })

    print(
        f"⏯️ Resuming execution {execution_id}, starting wave {paused_before_wave}"
    )

    # Reset status to running
    state["status"] = "running"
    state["wave_completed"] = False
    state["paused_before_wave"] = None

    # Update DynamoDB with safe operation
    try:
        def update_resume_status():
            return get_execution_history_table().update_item(
                Key={"executionId": execution_id, "planId": plan_id},
                UpdateExpression="SET #status = :status REMOVE TaskToken, PausedBeforeWave",
                ExpressionAttributeNames={"#status": "Status"},
                ExpressionAttributeValues={":status": "RUNNING"},
            )
        
        safe_aws_client_call(update_resume_status)
        
        log_security_event("resume_wave_success", {
            "execution_id": execution_id,
            "paused_before_wave": paused_before_wave
        })
    except Exception as e:
        log_security_event("resume_wave_error", {
            "execution_id": execution_id,
            "error": str(e)
        }, "ERROR")
        print(f"Error updating execution status: {e}")

    # Start the wave that was paused
    start_wave_recovery(state, paused_before_wave)

    return state


def query_drs_servers_by_tags(  # noqa: C901
    region: str, tags: Dict[str, str], account_context: Dict = None
) -> List[str]:
    """
    Query DRS source servers that have ALL specified tags with security validation.
    Uses AND logic - DRS source server must have all tags to be included.

    This queries the DRS source server tags directly, not EC2 instance tags.
    Returns list of source server IDs for orchestration.
    """
    try:
        # Security validation and sanitization
        region = sanitize_string_input(region)
        
        # Validate region format
        if not re.match(r'^[a-z]{2}-[a-z]+-\d{1}$|^us-gov-[a-z]+-\d{1}$', region):
            log_security_event("invalid_region_format", {
                "region": region
            }, "ERROR")
            raise ValueError(f"Invalid AWS region format: {region}")
        
        # Sanitize tags dictionary
        if not isinstance(tags, dict):
            log_security_event("invalid_tags_format", {
                "tags_type": type(tags).__name__
            }, "ERROR")
            raise ValueError("Tags must be a dictionary")
        
        sanitized_tags = {}
        for key, value in tags.items():
            sanitized_key = sanitize_string_input(str(key), 128)
            sanitized_value = sanitize_string_input(str(value), 256)
            sanitized_tags[sanitized_key] = sanitized_value
        
        # Sanitize account context if provided
        if account_context:
            account_context = sanitize_dynamodb_input(account_context)
        
        log_security_event("query_drs_servers_by_tags", {
            "region": region,
            "tag_count": len(sanitized_tags),
            "cross_account": bool(account_context)
        })

        # Create DRS client with cross-account support
        regional_drs = create_drs_client(region, account_context)

        # Get all source servers in the region with safe AWS call
        def describe_source_servers():
            all_servers = []
            paginator = regional_drs.get_paginator("describe_source_servers")
            for page in paginator.paginate():
                all_servers.extend(page.get("items", []))
            return all_servers

        all_servers = safe_aws_client_call(describe_source_servers)

        if not all_servers:
            log_security_event("no_drs_servers_found", {
                "region": region,
                "tag_count": len(sanitized_tags)
            })
            print("No DRS source servers found in region")
            return []

        # Filter servers that match ALL specified tags
        matching_server_ids = []

        for server in all_servers:
            server_id = sanitize_string_input(server.get("sourceServerID", ""))
            
            # Validate server ID format if it looks like a DRS server ID
            if server_id.startswith("s-") and not validate_drs_server_id(server_id):
                log_security_event("invalid_drs_server_id", {
                    "server_id": server_id,
                    "region": region
                }, "WARN")
                continue

            # Get DRS source server tags directly from server object
            drs_tags = server.get("tags", {})

            # Check if DRS server has ALL required tags with matching values
            # Use case-insensitive matching and strip whitespace for robustness
            matches_all = True
            for tag_key, tag_value in sanitized_tags.items():
                # Normalize tag key and value (strip whitespace, case-insensitive)
                normalized_required_key = tag_key.strip()
                normalized_required_value = tag_value.strip().lower()

                # Check if any DRS tag matches (case-insensitive)
                found_match = False
                for drs_key, drs_value in drs_tags.items():
                    # Sanitize DRS tag values
                    normalized_drs_key = sanitize_string_input(str(drs_key)).strip()
                    normalized_drs_value = sanitize_string_input(str(drs_value)).strip().lower()

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

        log_security_event("drs_servers_query_complete", {
            "region": region,
            "total_servers": len(all_servers),
            "matching_servers": len(matching_server_ids),
            "tag_count": len(sanitized_tags)
        })

        print("Tag matching results:")
        print(f"- Total DRS servers: {len(all_servers)}")
        print(f"- Servers matching tags {sanitized_tags}: {len(matching_server_ids)}")

        return matching_server_ids

    except Exception as e:
        log_security_event("query_drs_servers_error", {
            "region": region,
            "error": str(e),
            "tag_count": len(tags) if isinstance(tags, dict) else 0
        }, "ERROR")
        print(f"Error querying DRS servers by DRS tags: {str(e)}")
        raise


def start_wave_recovery(state: Dict, wave_number: int) -> None:
    """
    Start DRS recovery for a wave with comprehensive security validation
    Modifies state in place (archive pattern)

    Tag-based server resolution: Servers are resolved at execution time
    by querying DRS for servers matching the Protection Group's tags.
    """
    # Security validation
    if not isinstance(state, dict):
        log_security_event("start_wave_recovery_invalid_state", {
            "state_type": type(state).__name__
        }, "ERROR")
        raise ValueError("Invalid state object")
    
    if not isinstance(wave_number, int) or wave_number < 0:
        log_security_event("start_wave_recovery_invalid_wave", {
            "wave_number": wave_number,
            "wave_type": type(wave_number).__name__
        }, "ERROR")
        raise ValueError("Invalid wave number")
    
    # Sanitize state
    state = sanitize_dynamodb_input(state)
    
    waves = state.get("waves", [])
    if wave_number >= len(waves):
        log_security_event("start_wave_recovery_wave_not_found", {
            "wave_number": wave_number,
            "total_waves": len(waves)
        }, "ERROR")
        raise ValueError(f"Wave {wave_number} not found in plan")
    
    wave = waves[wave_number]
    is_drill = state.get("is_drill", True)
    execution_id = sanitize_string_input(state.get("execution_id", ""))
    
    if not execution_id:
        log_security_event("start_wave_recovery_missing_execution_id", {
            "wave_number": wave_number
        }, "ERROR")
        raise ValueError("Missing execution_id in state")
    
    validate_dynamodb_input("executionId", execution_id)

    wave_name = sanitize_string_input(wave.get("waveName", f"Wave {wave_number + 1}"))

    log_security_event("start_wave_recovery", {
        "execution_id": execution_id,
        "wave_number": wave_number,
        "wave_name": wave_name,
        "is_drill": is_drill
    })

    # Get Protection Group
    protection_group_id = sanitize_string_input(wave.get("protectionGroupId", ""))
    if not protection_group_id:
        log_security_event("start_wave_recovery_no_protection_group", {
            "wave_number": wave_number,
            "execution_id": execution_id
        }, "ERROR")
        print(f"Wave {wave_number} has no ProtectionGroupId")
        state["wave_completed"] = True
        state["status"] = "failed"
        state["error"] = "No ProtectionGroupId in wave"
        return

    validate_dynamodb_input("groupId", protection_group_id)

    try:
        # Safe DynamoDB operation to get protection group
        def get_protection_group():
            return get_protection_groups_table().get_item(
                Key={"groupId": protection_group_id}
            )
        
        pg_response = safe_aws_client_call(get_protection_group)
        
        if "Item" not in pg_response:
            log_security_event("start_wave_recovery_protection_group_not_found", {
                "protection_group_id": protection_group_id,
                "wave_number": wave_number,
                "execution_id": execution_id
            }, "ERROR")
            print(f"Protection Group {protection_group_id} not found")
            state["wave_completed"] = True
            state["status"] = "failed"
            state["error"] = (
                f"Protection Group {protection_group_id} not found"
            )
            return

        pg = pg_response["Item"]
        region = sanitize_string_input(pg.get("region", "us-east-1"))
        
        # Validate region
        if not re.match(r'^[a-z]{2}-[a-z]+-\d{1}$|^us-gov-[a-z]+-\d{1}$', region):
            log_security_event("start_wave_recovery_invalid_region", {
                "region": region,
                "protection_group_id": protection_group_id
            }, "ERROR")
            raise ValueError(f"Invalid region format: {region}")

        # TAG-BASED RESOLUTION: Resolve servers at execution time using tags
        selection_tags = pg.get("serverSelectionTags", {})

        if selection_tags:
            # Sanitize selection tags
            sanitized_selection_tags = {}
            for key, value in selection_tags.items():
                sanitized_key = sanitize_string_input(str(key), 128)
                sanitized_value = sanitize_string_input(str(value), 256)
                sanitized_selection_tags[sanitized_key] = sanitized_value
            
            # Resolve servers by tags at execution time
            print(
                f"Resolving servers for PG {protection_group_id} with tags: {sanitized_selection_tags}"
            )
            account_context = get_account_context(state)
            server_ids = query_drs_servers_by_tags(
                region, sanitized_selection_tags, account_context
            )
            print(f"Resolved {len(server_ids)} servers from tags")
        else:
            # Fallback: Check if wave has explicit ServerIds (legacy support)
            server_ids = wave.get("serverIds", [])
            # Sanitize server IDs
            sanitized_server_ids = []
            for server_id in server_ids:
                sanitized_id = sanitize_string_input(str(server_id))
                if sanitized_id.startswith("s-") and not validate_drs_server_id(sanitized_id):
                    log_security_event("start_wave_recovery_invalid_server_id", {
                        "server_id": sanitized_id,
                        "protection_group_id": protection_group_id
                    }, "WARN")
                    continue
                sanitized_server_ids.append(sanitized_id)
            server_ids = sanitized_server_ids
            print(
                f"Using explicit ServerIds from wave: {len(server_ids)} servers"
            )

        if not server_ids:
            log_security_event("start_wave_recovery_no_servers", {
                "wave_number": wave_number,
                "protection_group_id": protection_group_id,
                "has_selection_tags": bool(selection_tags)
            })
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
        source_servers = [{"sourceServerID": sid} for sid in server_ids]

        # Safe DRS operation to start recovery
        def start_drs_recovery():
            return drs_client.start_recovery(
                isDrill=is_drill, sourceServers=source_servers
            )

        response = safe_aws_client_call(start_drs_recovery)

        job_id = sanitize_string_input(response["job"]["jobID"])
        print(f"✅ DRS Job created: {job_id}")

        log_security_event("start_wave_recovery_success", {
            "execution_id": execution_id,
            "wave_number": wave_number,
            "job_id": job_id,
            "region": region,
            "server_count": len(server_ids),
            "is_drill": is_drill
        })

        # Update state
        state["current_wave_number"] = wave_number
        state["job_id"] = job_id
        state["region"] = region
        state["server_ids"] = server_ids
        state["wave_completed"] = False
        state["current_wave_total_wait_time"] = 0

        # Store wave result
        wave_result = {
            "waveNumber": wave_number,
            "waveName": wave_name,
            "status": "STARTED",
            "jobId": job_id,
            "startTime": int(time.time()),
            "serverIds": server_ids,
            "region": region,
        }
        state["wave_results"].append(wave_result)

        # Update DynamoDB with execution-level DRS job info and wave data
        try:
            def update_execution_wave():
                return get_execution_history_table().update_item(
                    Key={"executionId": execution_id, "planId": state["plan_id"]},
                    UpdateExpression="SET Waves = list_append(if_not_exists(Waves, :empty), :wave), DrsJobId = :job_id, DrsRegion = :region, #status = :status",
                    ExpressionAttributeNames={"#status": "Status"},
                    ExpressionAttributeValues={
                        ":empty": [],
                        ":wave": [wave_result],
                        ":job_id": job_id,
                        ":region": region,
                        ":status": "POLLING",
                    },
                    ConditionExpression="attribute_exists(ExecutionId)",
                )
            
            safe_aws_client_call(update_execution_wave)
        except Exception as e:
            log_security_event("start_wave_recovery_dynamodb_error", {
                "execution_id": execution_id,
                "wave_number": wave_number,
                "error": str(e)
            }, "ERROR")
            print(f"Error updating wave start in DynamoDB: {e}")

    except Exception as e:
        log_security_event("start_wave_recovery_error", {
            "execution_id": execution_id,
            "wave_number": wave_number,
            "error": str(e)
        }, "ERROR")
        print(f"Error starting DRS recovery: {e}")
        import traceback

        traceback.print_exc()
        state["wave_completed"] = True
        state["status"] = "failed"
        state["error"] = str(e)


def update_wave_status(event: Dict) -> Dict:  # noqa: C901
    """
    Poll DRS job status and check server launch status with security validation

    ARCHIVE PATTERN: State is passed directly, returns COMPLETE state
    """
    # Security validation and sanitization
    sanitized_event = sanitize_dynamodb_input(event)
    
    # State is passed directly (archive pattern)
    state = sanitized_event.get("application", sanitized_event)
    
    # Validate and sanitize required parameters
    job_id = sanitize_string_input(state.get("job_id", ""))
    wave_number = state.get("current_wave_number", 0)
    region = sanitize_string_input(state.get("region", "us-east-1"))
    execution_id = sanitize_string_input(state.get("execution_id", ""))
    plan_id = sanitize_string_input(state.get("plan_id", ""))
    
    # Validate inputs
    if not isinstance(wave_number, int) or wave_number < 0:
        log_security_event("update_wave_status_invalid_wave", {
            "wave_number": wave_number,
            "wave_type": type(wave_number).__name__
        }, "ERROR")
        raise ValueError("Invalid wave number")
    
    if not re.match(r'^[a-z]{2}-[a-z]+-\d{1}$|^us-gov-[a-z]+-\d{1}$', region):
        log_security_event("update_wave_status_invalid_region", {
            "region": region
        }, "ERROR")
        raise ValueError(f"Invalid region format: {region}")
    
    if execution_id:
        validate_dynamodb_input("executionId", execution_id)
    if plan_id:
        validate_dynamodb_input("planId", plan_id)

    log_security_event("update_wave_status", {
        "execution_id": execution_id,
        "wave_number": wave_number,
        "job_id": job_id,
        "region": region
    })

    # Early check for cancellation - check at start of every poll cycle
    if execution_id and plan_id:
        try:
            def check_execution_status():
                return get_execution_history_table().get_item(
                    Key={"executionId": execution_id, "planId": plan_id}
                )
            
            exec_check = safe_aws_client_call(check_execution_status)
            exec_status = exec_check.get("Item", {}).get("status", "")
            if exec_status == "CANCELLING":
                log_security_event("update_wave_status_cancelled", {
                    "execution_id": execution_id,
                    "wave_number": wave_number
                })
                print("⚠️ Execution cancelled (detected at poll start)")
                state["all_waves_completed"] = True
                state["wave_completed"] = True
                state["status"] = "cancelled"
                
                def update_cancelled_status():
                    return get_execution_history_table().update_item(
                        Key={"executionId": execution_id, "planId": plan_id},
                        UpdateExpression="SET #status = :status, EndTime = :end",
                        ExpressionAttributeNames={"#status": "Status"},
                        ExpressionAttributeValues={
                            ":status": "CANCELLED",
                            ":end": int(time.time()),
                        },
                        ConditionExpression="attribute_exists(ExecutionId)",
                    )
                
                safe_aws_client_call(update_cancelled_status)
                return state
        except Exception as e:
            log_security_event("update_wave_status_cancellation_check_error", {
                "execution_id": execution_id,
                "error": str(e)
            }, "ERROR")
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
                            ss["EC2InstanceId"] = ri.get("ec2InstanceID")
                            ss["recoveryInstanceId"] = ri.get(
                                "recoveryInstanceID"
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
                ec2_id = ss.get("EC2InstanceId")
                if ec2_id:
                    if ec2_id not in state.get("recovery_instance_ids", []):
                        state.setdefault("recovery_instance_ids", []).append(
                            ec2_id
                        )

            # Fetch private IPs from EC2
            try:
                ec2_ids = [
                    ss.get("EC2InstanceId")
                    for ss in server_statuses
                    if ss.get("EC2InstanceId")
                ]
                if ec2_ids:
                    ec2_client = boto3.client("ec2", region_name=region)
                    ec2_response = ec2_client.describe_instances(
                        InstanceIds=ec2_ids
                    )
                    for reservation in ec2_response.get("Reservations", []):
                        for instance in reservation.get("Instances", []):
                            private_ip = instance.get("PrivateIpAddress")
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
                        UpdateExpression="SET #status = :status, EndTime = :end",
                        ExpressionAttributeNames={"#status": "Status"},
                        ExpressionAttributeValues={
                            ":status": "CANCELLED",
                            ":end": int(time.time()),
                        },
                        ConditionExpression="attribute_exists(ExecutionId)",
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
                    get_execution_history_table().update_item(
                        Key={"executionId": execution_id, "planId": plan_id},
                        UpdateExpression="SET #status = :status, PausedBeforeWave = :wave",
                        ExpressionAttributeNames={"#status": "Status"},
                        ExpressionAttributeValues={
                            ":status": "PAUSED",
                            ":wave": next_wave,
                        },
                        ConditionExpression="attribute_exists(ExecutionId)",
                    )
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
                    UpdateExpression="SET #status = :status, EndTime = :end",
                    ExpressionAttributeNames={"#status": "Status"},
                    ExpressionAttributeValues={
                        ":status": "COMPLETED",
                        ":end": end_time,
                    },
                    ConditionExpression="attribute_exists(ExecutionId)",
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
    """Update wave status in DynamoDB with security validation"""
    try:
        # Security validation and sanitization
        execution_id = sanitize_string_input(execution_id)
        plan_id = sanitize_string_input(plan_id)
        status = sanitize_string_input(status, 32)
        
        # Validate inputs
        validate_dynamodb_input("executionId", execution_id)
        validate_dynamodb_input("planId", plan_id)
        validate_dynamodb_input("status", status)
        
        if not isinstance(wave_number, int) or wave_number < 0:
            log_security_event("update_wave_in_dynamodb_invalid_wave", {
                "wave_number": wave_number,
                "execution_id": execution_id
            }, "ERROR")
            raise ValueError("Invalid wave number")
        
        if not isinstance(server_statuses, list):
            log_security_event("update_wave_in_dynamodb_invalid_statuses", {
                "statuses_type": type(server_statuses).__name__,
                "execution_id": execution_id
            }, "ERROR")
            raise ValueError("Server statuses must be a list")
        
        # Sanitize server statuses
        sanitized_server_statuses = []
        for server_status in server_statuses:
            if isinstance(server_status, dict):
                sanitized_status = sanitize_dynamodb_input(server_status)
                sanitized_server_statuses.append(sanitized_status)
        
        log_security_event("update_wave_in_dynamodb", {
            "execution_id": execution_id,
            "wave_number": wave_number,
            "status": status,
            "server_count": len(sanitized_server_statuses)
        })

        # Safe DynamoDB operations
        def get_execution():
            return get_execution_history_table().get_item(
                Key={"executionId": execution_id, "planId": plan_id},
                ConditionExpression="attribute_exists(ExecutionId)",
            )
        
        exec_response = safe_aws_client_call(get_execution)

        if "Item" in exec_response:
            waves = exec_response["Item"].get("waves", [])
            for i, w in enumerate(waves):
                if w.get("waveNumber") == wave_number:
                    waves[i]["status"] = status
                    waves[i]["endTime"] = int(time.time())
                    waves[i]["serverStatuses"] = sanitized_server_statuses
                    break

            def update_waves():
                return get_execution_history_table().update_item(
                    Key={"executionId": execution_id, "planId": plan_id},
                    UpdateExpression="SET Waves = :waves",
                    ExpressionAttributeValues={":waves": waves},
                    ConditionExpression="attribute_exists(ExecutionId)",
                )
            
            safe_aws_client_call(update_waves)
            
            log_security_event("update_wave_in_dynamodb_success", {
                "execution_id": execution_id,
                "wave_number": wave_number,
                "status": status
            })
    except Exception as e:
        log_security_event("update_wave_in_dynamodb_error", {
            "execution_id": execution_id,
            "wave_number": wave_number,
            "error": str(e)
        }, "ERROR")
        print(f"Error updating wave in DynamoDB: {e}")
