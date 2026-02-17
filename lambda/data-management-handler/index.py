"""
Data Management Handler Lambda

Manages Protection Groups, Recovery Plans, Target Accounts, and Configuration for the
DR Orchestration Platform. Provides CRUD operations via API Gateway and direct invocation.

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
    │ handler (this)    │ │                   │ │                   │
    ├───────────────────┤ ├───────────────────┤ ├───────────────────┤
    │ CRUD Operations:  │ │ Recovery Actions: │ │ Read Operations:  │
    │ - Protection Grps │ │ - Start recovery  │ │ - List executions │
    │ - Recovery Plans  │ │ - Cancel exec     │ │ - Poll DRS jobs   │
    │ - Target Accounts │ │ - Terminate inst  │ │ - Server status   │
    │ - Tag sync        │ │ - Apply configs   │ │ - Dashboard data  │
    │ - Launch configs  │ └───────────────────┘ └───────────────────┘
    └───────────────────┘

HANDLER RESPONSIBILITIES:
- data-management-handler (this): CRUD for Protection Groups, Recovery Plans, Target
  Accounts, Tag Sync, Launch Configs (API Gateway + Direct Invocation)
- execution-handler: Start/cancel recovery, terminate instances, apply launch configs
- query-handler: Poll DRS jobs, list executions, dashboard metrics, server status
- dr-orchestration-stepfunction: Wave orchestration, state management, handler coordination

DUAL INVOCATION SUPPORT:
This Lambda supports two invocation patterns:

1. API Gateway Mode (Frontend/CLI):
   - REST API endpoints with Cognito authentication
   - Request/response via HTTP methods (GET, POST, PUT, DELETE)
   - Path parameters and query strings for resource identification

2. Direct Invocation Mode (Step Functions/Lambda/CLI):
   - Function calls with operation parameter
   - Bypasses API Gateway for internal operations
   - Used by Step Functions for configuration lookups

SECURITY MODEL:
- API Gateway mode: Authentication via Cognito JWT tokens
- Direct invocation mode: IAM role-based access control
- Cross-account DRS operations: IAM role assumption to target accounts
- Input validation: All inputs validated before processing

KEY CAPABILITIES:
- Protection Group management with tag-based or explicit server selection
- Recovery Plan management with multi-wave configuration
- Target Account registration and cross-account role validation
- Tag synchronization from EC2 to DRS source servers
- Per-server launch configuration overrides
- Configuration import/export for disaster recovery

PROTECTION GROUP FEATURES:
- Tag-based server selection: Dynamic resolution at execution time
- Explicit server selection: Static list of DRS source server IDs
- Per-server launch configs: Override instance type, subnet, security groups
- Server conflict detection: Prevents servers in multiple groups
- Replication state validation: Ensures servers are ready for recovery

RECOVERY PLAN FEATURES:
- Multi-wave execution: Sequential waves with dependency management
- Pause gates: Manual approval points between waves
- Wave dependencies: dependsOnWaves for complex orchestration
- DRS quota validation: Max 100 servers per wave (DRS limit)
- Active execution detection: Prevents conflicting operations

DYNAMODB DATA FLOW:
The platform uses 5 DynamoDB tables for configuration and state management:

    +-------------------------+     +----------------------------+
    |   protection-groups     |     |     recovery-plans         |
    +-------------------------+     +----------------------------+
    | PK: groupId             |     | PK: planId                 |
    |                         |     |                            |
    | - groupName             |<----| - waves[].protectionGroupId|
    | - sourceServerIds[]     |     | - waves[].waveNumber       |
    | - serverSelectionTags{} |     | - waves[].pauseBeforeWave  |
    | - launchConfig{}        |     | - waves[].dependsOnWaves[] |
    | - servers[] (per-srv)   |     | - planName                 |
    | - region                |     | - description              |
    | - accountId             |     +----------------------------+
    +-------------------------+
              │
              │  Referenced by
              ▼
    +-------------------------------------------------------------------+
    |                      execution-history                            |
    +-------------------------------------------------------------------+
    | PK: executionId                                                   |
    | SK: planId (GSI for querying executions by plan)                  |
    |                                                                   |
    | - status: RUNNING | PAUSED | COMPLETED | FAILED | CANCELLED       |
    | - currentWave, waveStatuses[], serverExecutions[]                 |
    +-------------------------------------------------------------------+

    +-------------------------+     +----------------------------+
    |    target-accounts      |     |    tag-sync-config         |
    +-------------------------+     +----------------------------+
    | PK: accountId           |     | PK: configId               |
    |                         |     |                            |
    | - accountName           |     | - enabled                  |
    | - assumeRoleName        |     | - tagMappings[]            |
    | - externalId            |     | - syncFrequency            |
    | - regions[]             |     | - lastSyncTime             |
    | - stagingAccounts[]     |     +----------------------------+
    | - IsCurrentAccount      |
    +-------------------------+

DATA VALIDATION RULES:
- Protection Group names: Unique (case-insensitive), valid region, valid server IDs
- Recovery Plan names: Unique (case-insensitive), valid wave config, no circular deps
- Server assignments: No server in multiple Protection Groups
- Wave size: Max 100 servers per wave (DRS StartRecovery API limit)
- Replication state: Servers must have healthy replication for recovery

API ENDPOINTS (API Gateway Mode):
Protection Groups:
- GET/POST /protection-groups - List/Create
- GET/PUT/DELETE /protection-groups/{id} - Read/Update/Delete
- POST /protection-groups/resolve - Preview tag-based selection

Recovery Plans:
- GET/POST /recovery-plans - List/Create
- GET/PUT/DELETE /recovery-plans/{id} - Read/Update/Delete

Target Accounts:
- GET/POST /accounts/targets - List/Register
- GET/PUT/DELETE /accounts/targets/{id} - Read/Update/Delete
- POST /accounts/targets/{id}/validate - Validate cross-account access

Configuration:
- POST /drs/tag-sync - Trigger tag synchronization
- GET/PUT /config/tag-sync - Get/Update tag sync settings
- POST /config/import - Import configuration

DIRECT INVOCATION OPERATIONS:
Protection Groups: create_protection_group, list_protection_groups, get_protection_group,
                   update_protection_group, delete_protection_group, resolve_protection_group_tags
Recovery Plans: create_recovery_plan, list_recovery_plans, get_recovery_plan,
                update_recovery_plan, delete_recovery_plan
Tag Sync: handle_drs_tag_sync, get_tag_sync_settings, update_tag_sync_settings
Config: import_configuration

SHARED UTILITIES (lambda/shared/):
Common modules used by this Lambda for cross-account and validation operations:

    +---------------------------+------------------------------------------------+
    | Module                    | Purpose                                        |
    +---------------------------+------------------------------------------------+
    | account_utils.py          | get_account_name(), get_target_accounts()      |
    | conflict_detection.py     | check_server_conflicts_*(), get_shared_pgs()   |
    | cross_account.py          | create_drs_client(), create_ec2_client()       |
    | config_merge.py           | get_effective_launch_config() for overrides    |
    | response_utils.py         | response() for standardized API responses      |
    | drs_utils.py              | transform_drs_server_for_frontend()            |
    +---------------------------+------------------------------------------------+

PERFORMANCE CHARACTERISTICS:
- Memory: 512 MB (moderate complexity with DRS API calls)
- Timeout: 120 seconds (tag resolution can query many servers)
- Concurrency: Supports concurrent operations with DynamoDB optimistic locking

ERROR HANDLING:
- 400 Bad Request: Validation errors, missing fields, duplicate names, server conflicts
- 404 Not Found: Protection group, recovery plan, or target account not found
- 409 Conflict: Active execution in progress, server already assigned
- 500 Internal Error: DynamoDB errors, DRS API errors, cross-account failures
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import uuid

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Import shared utilities
from shared.account_utils import (
    get_account_name,
    get_target_accounts,
    validate_target_account,
    validate_account_context_for_invocation,
)
from shared.security_utils import (
    sanitize_string,
    validate_email,
    InputValidationError,
)
from shared.notifications import (
    manage_recovery_plan_subscription,
)
from shared.conflict_detection import (
    check_server_conflicts_for_create,
    check_server_conflicts_for_update,
    get_active_executions_for_plan,
    get_inventory_table,
    get_plans_with_conflicts,
    get_shared_protection_groups,
    query_drs_servers_by_tags,
)
from shared.config_merge import get_effective_launch_config
from shared.cross_account import (
    get_current_account_id,
    create_drs_client,
    create_ec2_client,
)
from shared.response_utils import (
    response,
    error_response,
    ERROR_MISSING_PARAMETER,
    ERROR_INVALID_PARAMETER,
    ERROR_NOT_FOUND,
    ERROR_DYNAMODB_ERROR,
    ERROR_INTERNAL_ERROR,
)

from shared.drs_regions import DRS_REGIONS
from shared.launch_config_service import (
    apply_launch_configs_to_group,
    persist_config_status,
    LaunchConfigApplicationError,
    LaunchConfigTimeoutError,
)

# DynamoDB tables (from environment variables)
PROTECTION_GROUPS_TABLE = os.environ.get("PROTECTION_GROUPS_TABLE")
RECOVERY_PLANS_TABLE = os.environ.get("RECOVERY_PLANS_TABLE")
EXECUTIONS_TABLE = os.environ.get("EXECUTION_HISTORY_TABLE")
TARGET_ACCOUNTS_TABLE = os.environ.get("TARGET_ACCOUNTS_TABLE")
TAG_SYNC_CONFIG_TABLE = os.environ.get("TAG_SYNC_CONFIG_TABLE")
INVENTORY_TABLE = os.environ.get("SOURCE_SERVER_INVENTORY_TABLE")

# Initialize DynamoDB resources - lazy initialization for test mocking
dynamodb = boto3.resource("dynamodb")
stepfunctions = boto3.client("stepfunctions")

# Module-level table variables - lazy initialization
_protection_groups_table = None
_recovery_plans_table = None
_executions_table = None
_target_accounts_table = None
_tag_sync_config_table = None
_inventory_table = None


def get_protection_groups_table():
    """Lazy-load Protection Groups table for test mocking"""
    global _protection_groups_table
    if _protection_groups_table is None and PROTECTION_GROUPS_TABLE:
        _protection_groups_table = dynamodb.Table(PROTECTION_GROUPS_TABLE)
    return _protection_groups_table


def get_recovery_plans_table():
    """Lazy-load Recovery Plans table for test mocking"""
    global _recovery_plans_table
    if _recovery_plans_table is None and RECOVERY_PLANS_TABLE:
        _recovery_plans_table = dynamodb.Table(RECOVERY_PLANS_TABLE)
    return _recovery_plans_table


def get_executions_table():
    """Lazy-load Executions table for test mocking"""
    global _executions_table
    if _executions_table is None and EXECUTIONS_TABLE:
        _executions_table = dynamodb.Table(EXECUTIONS_TABLE)
    return _executions_table


def get_target_accounts_table():
    """Lazy-load Target Accounts table for test mocking"""
    global _target_accounts_table
    if _target_accounts_table is None and TARGET_ACCOUNTS_TABLE:
        _target_accounts_table = dynamodb.Table(TARGET_ACCOUNTS_TABLE)
    return _target_accounts_table


def get_tag_sync_config_table():
    """Lazy-load Tag Sync Config table for test mocking"""
    global _tag_sync_config_table
    if _tag_sync_config_table is None and TAG_SYNC_CONFIG_TABLE:
        _tag_sync_config_table = dynamodb.Table(TAG_SYNC_CONFIG_TABLE)
    return _tag_sync_config_table


# Invalid replication states that block DR operations
INVALID_REPLICATION_STATES = [
    "DISCONNECTED",
    "STOPPED",
    "STALLED",
    "NOT_STARTED",
]


# ============================================================================
# Lambda Handler Entry Point
# ============================================================================


def lambda_handler(event, context):
    """
    Unified entry point supporting both API Gateway and direct invocation.

    API Gateway Event (Standalone Mode):
    {
        "requestContext": {...},
        "httpMethod": "POST",
        "path": "/protection-groups",
        "body": "{...}"
    }

    Direct Invocation Event (CLI/SDK Mode):
    {
        "operation": "create_protection_group",
        "body": {...}
    }
    """
    try:
        # Detect invocation pattern
        if "requestContext" in event:
            # API Gateway invocation (standalone mode)
            return handle_api_gateway_request(event, context)
        elif "operation" in event:
            # Direct invocation (CLI/SDK mode)
            return handle_direct_invocation(event, context)
        elif "synch_tags" in event or "synch_instance_type" in event:
            # EventBridge scheduled tag sync trigger
            # Payload: {"synch_tags": true, "synch_instance_type": true}
            print(f"EventBridge tag sync trigger received: {event}")
            return handle_drs_tag_sync(event)
        else:
            return response(
                400,
                error_response(
                    "INVALID_INVOCATION",
                    "Event must contain either 'requestContext' (API Gateway) or 'operation' (direct invocation)",
                ),
            )

    except Exception as e:
        print(f"Unhandled error in lambda_handler: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(500, error_response("INTERNAL_ERROR", str(e)))


def handle_api_gateway_request(event, context):
    """Route API Gateway requests to appropriate handler functions"""
    try:
        http_method = event.get("httpMethod")
        path = event.get("path", "")
        path_parameters = event.get("pathParameters") or {}
        query_parameters = event.get("queryStringParameters") or {}
        body = event.get("body", "{}")

        # Parse body if it's a string
        if isinstance(body, str):
            try:
                body = json.loads(body) if body else {}
            except json.JSONDecodeError:
                return response(
                    400,
                    error_response(
                        ERROR_INVALID_PARAMETER,
                        "Invalid parameter value",
                        details={
                            "parameter": "body",
                            "value": body,
                            "expected": "valid JSON",
                        },
                    ),
                )

        # Protection Groups endpoints (6)
        if path == "/protection-groups":
            if http_method == "GET":
                return get_protection_groups(query_parameters)
            elif http_method == "POST":
                return create_protection_group(event, body)

        elif path == "/protection-groups/resolve":
            if http_method == "POST":
                return resolve_protection_group_tags(body)

        elif "/protection-groups/" in path and path.endswith("/resolve"):
            if http_method == "POST":
                return resolve_protection_group_tags(body)

        elif "/protection-groups/" in path:
            group_id = path_parameters.get("id")
            if not group_id:
                return response(
                    400,
                    error_response(
                        ERROR_MISSING_PARAMETER,
                        "Missing required parameter",
                        details={"parameter": "id"},
                    ),
                )

            # Apply launch configurations endpoint
            if "/apply-launch-configs" in path:
                if http_method == "POST":
                    return apply_launch_configs(group_id, body)

            # Get launch configuration status endpoint
            elif "/launch-config-status" in path:
                if http_method == "GET":
                    return get_launch_config_status(group_id)

            # Bulk server configuration endpoint
            elif "/servers/bulk-launch-config" in path:
                if http_method == "POST":
                    return bulk_update_server_launch_config(group_id, body)

            # Per-server launch config endpoints
            elif "/servers/" in path and "/launch-config" in path:
                server_id = path_parameters.get("serverId")
                if not server_id:
                    return response(
                        400,
                        error_response(
                            ERROR_MISSING_PARAMETER,
                            "Missing required parameter",
                            details={"parameter": "serverId"},
                        ),
                    )

                if http_method == "GET":
                    return get_server_launch_config(group_id, server_id)
                elif http_method == "PUT":
                    return update_server_launch_config(group_id, server_id, body)
                elif http_method == "DELETE":
                    return delete_server_launch_config(group_id, server_id)

            # Per-server IP validation endpoint
            elif "/servers/" in path and "/validate-ip" in path:
                server_id = path_parameters.get("serverId")
                if not server_id:
                    return response(
                        400,
                        error_response(
                            ERROR_MISSING_PARAMETER,
                            "Missing required parameter",
                            details={"parameter": "serverId"},
                        ),
                    )

                if http_method == "POST":
                    return validate_server_static_ip(group_id, server_id, body)

            # Protection group CRUD endpoints
            if http_method == "GET":
                return get_protection_group(group_id)
            elif http_method == "PUT":
                return update_protection_group(group_id, body)
            elif http_method == "DELETE":
                return delete_protection_group(group_id)

        # Recovery Plans endpoints (6)
        elif path == "/recovery-plans":
            if http_method == "GET":
                return get_recovery_plans(query_parameters)
            elif http_method == "POST":
                return create_recovery_plan(event, body)

        elif "/recovery-plans/" in path and "/check-existing-instances" in path:
            plan_id = path_parameters.get("id")
            if not plan_id:
                return response(
                    400,
                    error_response(
                        ERROR_MISSING_PARAMETER,
                        "Missing required parameter",
                        details={"parameter": "id"},
                    ),
                )
            if http_method == "GET":
                return check_existing_recovery_instances(plan_id)

        elif "/recovery-plans/" in path:
            plan_id = path_parameters.get("id")
            if not plan_id:
                return response(
                    400,
                    error_response(
                        ERROR_MISSING_PARAMETER,
                        "Missing required parameter",
                        details={"parameter": "id"},
                    ),
                )

            if http_method == "GET":
                return get_recovery_plan(plan_id)
            elif http_method == "PUT":
                return update_recovery_plan(plan_id, body)
            elif http_method == "DELETE":
                return delete_recovery_plan(plan_id)

        # Tag Sync & Config endpoints (4)
        elif path == "/drs/tag-sync":
            if http_method == "POST":
                return handle_drs_tag_sync(body)
            elif http_method == "GET":
                return get_last_tag_sync_status()

        elif path == "/config/tag-sync":
            if http_method == "GET":
                return get_tag_sync_settings()
            elif http_method == "PUT":
                return update_tag_sync_settings(body)

        elif path == "/config/import":
            if http_method == "POST":
                return import_configuration(body)

        elif path == "/config/validate-manifest":
            if http_method == "POST":
                # Validate manifest without importing
                manifest = body.get("manifest", body)
                correlation_id = body.get("correlationId")
                report = generate_manifest_validation_report(manifest, correlation_id)
                return response(200, report)

        # Target Accounts endpoints (5)
        elif path == "/accounts/targets":
            if http_method == "GET":
                return get_target_accounts()
            elif http_method == "POST":
                return create_target_account(body)

        elif "/accounts/targets/" in path:
            account_id = path_parameters.get("id")
            if not account_id:
                return response(
                    400,
                    error_response(
                        ERROR_MISSING_PARAMETER,
                        "Missing required parameter",
                        details={"parameter": "id"},
                    ),
                )

            # Staging accounts endpoints
            if "/staging-accounts" in path:
                if path.endswith("/staging-accounts"):
                    # POST /accounts/{id}/staging-accounts - Add staging
                    # account
                    if http_method == "POST":
                        body["targetAccountId"] = account_id
                        return handle_add_staging_account(body)
                elif path.endswith("/staging-accounts/sync"):
                    # POST /accounts/{id}/staging-accounts/sync - Sync staging
                    # accounts
                    if http_method == "POST":
                        return handle_sync_single_account(account_id)
                else:
                    # DELETE /accounts/{id}/staging-accounts/{stagingId}
                    staging_id = path_parameters.get("stagingId")
                    if not staging_id:
                        return response(
                            400,
                            error_response(
                                ERROR_MISSING_PARAMETER,
                                "Missing required parameter",
                                details={"parameter": "stagingId"},
                            ),
                        )
                    if http_method == "DELETE":
                        return handle_remove_staging_account(
                            {
                                "targetAccountId": account_id,
                                "stagingAccountId": staging_id,
                            }
                        )

            # Target account validation endpoint
            elif "/validate" in path:
                if http_method == "POST":
                    return validate_target_account(account_id)
            # Target account CRUD endpoints
            elif http_method == "GET":
                return get_target_account(account_id)
            elif http_method == "PUT":
                return update_target_account(account_id, body)
            elif http_method == "DELETE":
                return delete_target_account(account_id)

        else:
            return response(
                404,
                error_response(
                    "NOT_FOUND",
                    f"No handler for {http_method} {path}",
                ),
            )

    except Exception as e:
        print(f"Unhandled error in handle_api_gateway_request: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(500, error_response("INTERNAL_ERROR", str(e)))


def handle_direct_invocation(event, context):
    """
    Handle direct Lambda invocation (CLI/SDK mode).

    Returns raw data (not API Gateway wrapped) for direct invocations.
    Operation functions return response(statusCode, body) format, which
    we unwrap to return just the body data.
    """
    # Import IAM utilities
    from shared.iam_utils import (
        extract_iam_principal,
        validate_iam_authorization,
        log_direct_invocation,
        create_authorization_error_response,
        validate_direct_invocation_event,
    )

    # Validate event format
    if not validate_direct_invocation_event(event):
        error_result = {
            "error": "INVALID_EVENT_FORMAT",
            "message": "Event must contain 'operation' field",
        }
        log_direct_invocation(
            principal="unknown",
            operation="invalid",
            params={},
            result=error_result,
            success=False,
            context=context,
        )
        return error_result

    # Extract IAM principal from context
    principal = extract_iam_principal(context)

    # Validate authorization
    if not validate_iam_authorization(principal):
        error_result = create_authorization_error_response()
        log_direct_invocation(
            principal=principal,
            operation=event.get("operation"),
            params=event.get("body", {}),
            result=error_result,
            success=False,
            context=context,
        )
        return error_result

    operation = event.get("operation")
    body = event.get("body", {})
    query_params = event.get("queryParams", {})

    # Map operations to functions
    operations = {
        # Protection Groups
        "create_protection_group": lambda: create_protection_group(event, body),
        "list_protection_groups": lambda: get_protection_groups(query_params),
        "get_protection_group": lambda: get_protection_group(body.get("groupId")),
        "update_protection_group": lambda: update_protection_group(body.get("groupId"), body),
        "delete_protection_group": lambda: delete_protection_group(body.get("groupId")),
        "resolve_protection_group_tags": lambda: resolve_protection_group_tags(body),
        # Recovery Plans
        "create_recovery_plan": lambda: create_recovery_plan(event, body),
        "list_recovery_plans": lambda: get_recovery_plans(query_params),
        "get_recovery_plan": lambda: get_recovery_plan(body.get("planId")),
        "update_recovery_plan": lambda: update_recovery_plan(body.get("planId"), body),
        "delete_recovery_plan": lambda: delete_recovery_plan(body.get("planId")),
        # Server Launch Configs (Phase 4: Tasks 5.1-5.4)
        "update_server_launch_config": lambda: update_server_launch_config(
            body.get("groupId"), body.get("serverId"), body
        ),
        "delete_server_launch_config": lambda: delete_server_launch_config(body.get("groupId"), body.get("serverId")),
        "bulk_update_server_configs": lambda: bulk_update_server_launch_config(body.get("groupId"), body),
        "validate_static_ip": lambda: validate_server_static_ip(body.get("groupId"), body.get("serverId"), body),
        # Launch Config Pre-Application (Task 8)
        "apply_launch_configs": lambda: apply_launch_configs(body.get("groupId"), body),
        "get_launch_config_status": lambda: get_launch_config_status(body.get("groupId")),
        # Target Accounts (Phase 4: Tasks 5.5-5.7)
        "add_target_account": lambda: create_target_account(body),
        "update_target_account": lambda: update_target_account(body.get("accountId"), body),
        "delete_target_account": lambda: delete_target_account(body.get("accountId")),
        # Tag Sync & Config
        "handle_drs_tag_sync": lambda: handle_drs_tag_sync(body),
        "trigger_tag_sync": lambda: handle_drs_tag_sync(body),  # Alias for handle_drs_tag_sync
        "get_tag_sync_settings": lambda: get_tag_sync_settings(),
        "update_tag_sync_settings": lambda: update_tag_sync_settings(body),
        "import_configuration": lambda: import_configuration(body),
        "export_configuration": lambda: export_configuration({}),
        # Staging Accounts (Phase 4: Tasks 5.8-5.9, 5.12)
        "add_staging_account": lambda: handle_add_staging_account(body),
        "remove_staging_account": lambda: handle_remove_staging_account(body),
        "sync_staging_accounts": lambda: handle_sync_single_account(body.get("targetAccountId")),
        "sync_extended_source_servers": lambda: handle_sync_single_account(body.get("targetAccountId")),  # Alias
    }

    if operation in operations:
        try:
            result = operations[operation]()

            # Unwrap API Gateway response format for direct invocations
            # Operation functions return response(statusCode, body) which wraps
            # the data in API Gateway format. For direct invocations, we need
            # to extract just the body data.
            if isinstance(result, dict) and "statusCode" in result:
                # Extract body from API Gateway response format
                body_data = result.get("body")
                if isinstance(body_data, str):
                    # Body is JSON string, parse it
                    body_data = json.loads(body_data)

                # Log successful invocation with unwrapped data
                log_direct_invocation(
                    principal=principal,
                    operation=operation,
                    params={"body": body, "queryParams": query_params},
                    result=body_data,
                    success=True,
                    context=context,
                )
                return body_data
            else:
                # Result is already in raw format (shouldn't happen with current code)
                log_direct_invocation(
                    principal=principal,
                    operation=operation,
                    params={"body": body, "queryParams": query_params},
                    result=result,
                    success=True,
                    context=context,
                )
                return result

        except Exception as e:
            error_result = {
                "error": "OPERATION_FAILED",
                "message": str(e),
                "operation": operation,
            }
            log_direct_invocation(
                principal=principal,
                operation=operation,
                params={"body": body, "queryParams": query_params},
                result=error_result,
                success=False,
                context=context,
            )
            return error_result
    else:
        error_result = {
            "error": "INVALID_OPERATION",
            "message": f"Unknown operation: {operation}",
            "details": {
                "operation": operation,
            },
        }
        log_direct_invocation(
            principal=principal,
            operation=operation,
            params={"body": body, "queryParams": query_params},
            result=error_result,
            success=False,
            context=context,
        )
        return error_result


# ============================================================================
# Protection Groups Functions
# ============================================================================


# ============================================================================
# Recovery Plans Functions
# ============================================================================


# ============================================================================
# Tag Sync & Config Functions
# ============================================================================


# ============================================================================
# Helper Functions
# ============================================================================


def get_active_execution_for_protection_group(
    group_id: str,
) -> Optional[Dict]:
    """
    Check if a protection group is part of any active execution.
    Returns execution info if found, None otherwise.
    """
    try:
        # Find all recovery plans that use this protection group
        plans_result = get_recovery_plans_table().scan()
        all_plans = plans_result.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in plans_result:
            plans_result = get_recovery_plans_table().scan(ExclusiveStartKey=plans_result["LastEvaluatedKey"])
            all_plans.extend(plans_result.get("Items", []))

        # Find plan IDs that reference this protection group
        plan_ids_with_pg = []
        for plan in all_plans:
            for wave in plan.get("waves", []):
                pg_id_in_wave = wave.get("protectionGroupId")
                if pg_id_in_wave == group_id:
                    plan_ids_with_pg.append(plan.get("planId"))
                    break

        if not plan_ids_with_pg:
            return None

        # Check if any of these plans have active executions
        for plan_id in plan_ids_with_pg:
            active_executions = get_active_executions_for_plan(plan_id)
            if active_executions:
                exec_info = active_executions[0]
                # Get plan name
                plan = next((p for p in all_plans if p.get("planId") == plan_id), {})
                return {
                    "executionId": exec_info.get("executionId"),
                    "planId": plan_id,
                    "planName": plan.get("planName", "Unknown"),
                    "status": exec_info.get("status"),
                }

        return None
    except Exception as e:
        print(f"Error checking active execution for protection group: {e}")
        return None


def validate_unique_pg_name(name: str, current_pg_id: Optional[str] = None) -> bool:
    """
    Validate that Protection Group name is unique (case-insensitive)

    Args:
    - name: Protection Group name to validate
    - current_pg_id: Optional PG ID to exclude (for edit operations)

    Returns:
    - True if unique, False if duplicate exists
    """
    pg_response = get_protection_groups_table().scan()

    name_lower = name.lower()
    for pg in pg_response.get("Items", []):
        pg_id = pg.get("groupId") or pg.get("protectionGroupId")

        # Skip current PG when editing
        if current_pg_id and pg_id == current_pg_id:
            continue

        existing_name = pg.get("groupName") or pg.get("name", "")
        if existing_name.lower() == name_lower:
            return False

    return True


def validate_unique_rp_name(name: str, current_rp_id: Optional[str] = None) -> bool:
    """
    Validate that Recovery Plan name is unique (case-insensitive)

    Args:
    - name: Recovery Plan name to validate
    - current_rp_id: Optional RP ID to exclude (for edit operations)

    Returns:
    - True if unique, False if duplicate exists
    """
    rp_response = get_recovery_plans_table().scan()

    name_lower = name.lower()
    for rp in rp_response.get("Items", []):
        rp_id = rp.get("planId")

        # Skip current RP when editing
        if current_rp_id and rp_id == current_rp_id:
            continue

        existing_name = rp.get("planName", "")
        if existing_name.lower() == name_lower:
            return False

    return True


def validate_server_replication_states(region: str, server_ids: List[str]) -> Dict:
    """
    Validate that all servers have healthy replication state for recovery.
    Returns validation result with unhealthy servers list.
    """
    if not server_ids:
        return {
            "valid": True,
            "healthyCount": 0,
            "unhealthyCount": 0,
            "unhealthyServers": [],
        }

    try:
        regional_drs = boto3.client("drs", region_name=region)

        unhealthy_servers = []
        healthy_servers = []

        # Batch describe servers (max 200 per call)
        for i in range(0, len(server_ids), 200):
            batch = server_ids[i : i + 200]

            response = regional_drs.describe_source_servers(filters={"sourceServerIDs": batch})

            for server in response.get("items", []):
                server_id = server.get("sourceServerID")
                replication_state = server.get("dataReplicationInfo", {}).get("dataReplicationState", "UNKNOWN")
                lifecycle_state = server.get("lifeCycle", {}).get("state", "UNKNOWN")

                if replication_state in INVALID_REPLICATION_STATES or lifecycle_state == "STOPPED":
                    unhealthy_servers.append(
                        {
                            "serverId": server_id,
                            "hostname": server.get("sourceProperties", {})
                            .get("identificationHints", {})
                            .get("hostname", "Unknown"),
                            "replicationState": replication_state,
                            "lifecycleState": lifecycle_state,
                            "reason": f"Replication: {replication_state}, Lifecycle: {lifecycle_state}",
                        }
                    )
                else:
                    healthy_servers.append(server_id)

        return {
            "valid": len(unhealthy_servers) == 0,
            "healthyCount": len(healthy_servers),
            "unhealthyCount": len(unhealthy_servers),
            "unhealthyServers": unhealthy_servers,
            "message": (
                f"All {len(healthy_servers)} servers have healthy replication"
                if len(unhealthy_servers) == 0
                else f"{len(unhealthy_servers)} server(s) have unhealthy replication state"
            ),
        }

    except Exception as e:
        print(f"Error checking server replication states: {e}")
        return {
            "valid": True,
            "warning": f"Could not verify server replication states: {str(e)}",
            "unhealthyServers": [],
        }


def validate_server_assignments(server_ids: List[str], current_pg_id: Optional[str] = None) -> List[Dict]:
    """
    Validate that servers are not already assigned to other Protection Groups

    Args:
    - server_ids: List of server IDs to validate
    - current_pg_id: Optional PG ID to exclude (for edit operations)

    Returns:
    - conflicts: List of {serverId, protectionGroupId, protectionGroupName}
    """
    pg_response = get_protection_groups_table().scan()

    conflicts = []
    for pg in pg_response.get("Items", []):
        pg_id = pg.get("groupId") or pg.get("protectionGroupId")

        # Skip current PG when editing
        if current_pg_id and pg_id == current_pg_id:
            continue

        assigned_servers = pg.get("sourceServerIds") or pg.get("sourceServerIds", [])
        for server_id in server_ids:
            if server_id in assigned_servers:
                pg_name = pg.get("groupName") or pg.get("name")
                conflicts.append(
                    {
                        "serverId": server_id,
                        "protectionGroupId": pg_id,
                        "protectionGroupName": pg_name,
                    }
                )

    return conflicts


def validate_servers_exist_in_drs(region: str, server_ids: List[str]) -> List[str]:
    """
    Validate that server IDs actually exist in DRS

    Args:
    - region: AWS region to check
    - server_ids: List of server IDs to validate

    Returns:
    - List of invalid server IDs (empty list if all valid)
    """
    try:
        drs_client = boto3.client("drs", region_name=region)

        # Get all source servers in the region
        response = drs_client.describe_source_servers(maxResults=200)
        valid_server_ids = {s["sourceServerID"] for s in response.get("items", [])}

        # Find invalid servers
        invalid_servers = [sid for sid in server_ids if sid not in valid_server_ids]

        if invalid_servers:
            print(f"Invalid server IDs detected: {invalid_servers}")

        return invalid_servers

    except Exception as e:
        print(f"Error validating servers in DRS: {str(e)}")
        # On error, assume servers might be valid (fail open for now)
        # In production, might want to fail closed
        return []


def validate_and_get_source_servers(account_id: str, region: str, tags: Dict) -> List[str]:
    """Validate source servers exist with specified tags and return their IDs"""
    try:
        # For now, use current account credentials
        # In production, would assume cross-account role
        drs_client = boto3.client("drs", region_name=region)

        # Get all source servers
        servers_response = drs_client.describe_source_servers()
        servers = servers_response.get("items", [])

        # Filter by tags
        matching_servers = []
        key_name = tags.get("KeyName", "")
        key_value = tags.get("KeyValue", "")

        for server in servers:
            server_tags = server.get("tags", {})
            if key_name in server_tags and server_tags[key_name] == key_value:
                matching_servers.append(server["sourceServerID"])

        return matching_servers

    except Exception as e:
        print(f"Error validating source servers: {str(e)}")
        raise


def check_tag_conflicts_for_create(tags: Dict[str, str], region: str) -> List[Dict]:
    """
    Check if the specified tags would conflict with existing tag-based Protection Groups.
    A conflict occurs if another PG has the EXACT SAME tags (all keys and values match).
    """
    if not tags:
        return []

    conflicts = []

    # Scan all PGs
    pg_response = get_protection_groups_table().scan()
    all_pgs = pg_response.get("Items", [])

    while "LastEvaluatedKey" in pg_response:
        pg_response = get_protection_groups_table().scan(ExclusiveStartKey=pg_response["LastEvaluatedKey"])
        all_pgs.extend(pg_response.get("Items", []))

    for pg in all_pgs:
        existing_tags = pg.get("serverSelectionTags", {})
        if not existing_tags:
            continue

        # Check if tags are identical (exact match)
        if existing_tags == tags:
            conflicts.append(
                {
                    "protectionGroupId": pg.get("groupId"),
                    "protectionGroupName": pg.get("groupName"),
                    "conflictingTags": existing_tags,
                    "conflictType": "exact_match",
                }
            )

    return conflicts


def check_tag_conflicts_for_update(tags: Dict[str, str], region: str, current_pg_id: str) -> List[Dict]:
    """
    Check if the specified tags would conflict with existing tag-based Protection Groups (excluding current).
    """
    if not tags:
        return []

    conflicts = []

    # Scan all PGs
    pg_response = get_protection_groups_table().scan()
    all_pgs = pg_response.get("Items", [])

    while "LastEvaluatedKey" in pg_response:
        pg_response = get_protection_groups_table().scan(ExclusiveStartKey=pg_response["LastEvaluatedKey"])
        all_pgs.extend(pg_response.get("Items", []))

    for pg in all_pgs:
        # Skip current PG
        if pg.get("groupId") == current_pg_id:
            continue

        existing_tags = pg.get("serverSelectionTags", {})
        if not existing_tags:
            continue

        # Check if tags are identical (exact match)
        if existing_tags == tags:
            conflicts.append(
                {
                    "protectionGroupId": pg.get("groupId"),
                    "protectionGroupName": pg.get("groupName"),
                    "conflictingTags": existing_tags,
                    "conflictType": "exact_match",
                }
            )

    return conflicts


def validate_waves(waves: List[Dict]) -> Optional[str]:
    """Validate wave configuration - supports both single and multi-PG formats

    Includes DRS quota validation:
    - Max 100 servers per wave (DRS job limit)
    """
    try:
        if not waves:
            return "Waves array cannot be empty"

        # Check for duplicate wave numbers
        wave_numbers = [w.get("waveNumber") for w in waves if w.get("waveNumber") is not None]
        if wave_numbers and len(wave_numbers) != len(set(wave_numbers)):
            return "Duplicate waveNumber found in waves"

        # Check for circular dependencies using dependsOnWaves
        dependency_graph = {}
        for wave in waves:
            wave_num = wave.get("waveNumber", 0)
            depends_on = wave.get("dependsOnWaves", [])
            dependency_graph[wave_num] = depends_on

        if dependency_graph and has_circular_dependencies_by_number(dependency_graph):
            return "Circular dependency detected in wave configuration"

        # Validate each wave has required fields
        for wave in waves:
            if "waveNumber" not in wave:
                return "Wave missing required field: waveNumber"

            if "waveName" not in wave and "name" not in wave:
                return "Wave missing required field: waveName or name"

            # Accept either protectionGroupId (single) OR protectionGroupIds
            # (multi)
            has_single_pg = "protectionGroupId" in wave
            has_multi_pg = "protectionGroupIds" in wave

            if not has_single_pg and not has_multi_pg:
                return "Wave missing Protection Group assignment (protectionGroupId or protectionGroupIds required)"

            # Validate protectionGroupIds is an array if present
            pg_ids = wave.get("protectionGroupIds") or wave.get("protectionGroupIds")
            if pg_ids is not None:
                if not isinstance(pg_ids, list):
                    return f"protectionGroupIds must be an array, got {type(pg_ids)}"
                if len(pg_ids) == 0:
                    return "protectionGroupIds array cannot be empty"

        # QUOTA VALIDATION: Check each wave doesn't exceed 100 servers per job
        from shared.conflict_detection import (
            resolve_pg_servers_for_conflict_check,
        )

        pg_cache = {}
        for wave in waves:
            wave_name = wave.get("waveName") or wave.get("name", f"Wave {wave.get('waveNumber', '?')}")
            pg_id = wave.get("protectionGroupId") or (wave.get("protectionGroupIds", []) or [None])[0]

            if pg_id:
                try:
                    # Resolve servers from Protection Group
                    server_ids = resolve_pg_servers_for_conflict_check(pg_id, pg_cache)
                    server_count = len(server_ids)

                    # Check 100 servers per job limit
                    if server_count > 100:
                        return f"QUOTA_EXCEEDED: Wave '{wave_name}' contains {server_count} servers (max 100 per job). DRS Service Quota: Max 100 servers per job (not adjustable). Split this wave into multiple waves or reduce Protection Group size."  # noqa: E501

                except Exception as e:
                    print(f"Warning: Could not validate server count for wave '{wave_name}': {e}")
                    # Continue validation - don't block on PG resolution errors

        return None  # No errors

    except Exception as e:
        return f"Error validating waves: {str(e)}"


def has_circular_dependencies_by_number(graph: Dict[int, List[int]]) -> bool:
    """Check for circular dependencies using wave numbers"""
    visited = set()
    rec_stack = set()

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            if dfs(node):
                return True
    return False


def resolve_protection_group_tags(body: Dict) -> Dict:
    """
    Resolve tag-based server selection to actual DRS source servers.

    EXTRACTION TARGET: Data Management Handler (Phase 3)
    Queries inventory database to preview servers matching tag criteria.

    Supports TWO invocation modes:
    1. Frontend/API Gateway: accountId provided in request body (from account dropdown)
    2. Direct Lambda: accountId optional, uses protectionGroupId to lookup account

    Request body (Frontend):
    {
        "region": "us-east-1",
        "tags": {"dr:wave": "1"},
        "accountId": "851725249649"  # From account dropdown
    }

    Request body (Direct Lambda):
    {
        "region": "us-east-1",
        "tags": {"dr:wave": "1"},
        "protectionGroupId": "pg-123"  # Lookup accountId from PG
    }

    Returns list of servers matching ALL specified tags.
    """
    try:
        print(f"DEBUG: resolve_protection_group_tags called with body: {json.dumps(body, indent=2, default=str)}")

        region = body.get("region")
        tags = body.get("serverSelectionTags") or body.get("tags", {})

        print(f"DEBUG: Extracted region={region}, tags={tags}")

        if not region:
            return response(
                400,
                error_response(
                    ERROR_MISSING_PARAMETER,
                    "Missing required parameter",
                    details={"parameter": "region"},
                ),
            )

        if not tags or not isinstance(tags, dict):
            return response(
                400,
                error_response(
                    ERROR_INVALID_PARAMETER,
                    "serverSelectionTags must be a non-empty object",
                    details={
                        "parameter": "serverSelectionTags",
                        "value": tags,
                    },
                ),
            )

        # Determine accountId from request body OR protection group
        account_id = body.get("accountId")
        protection_group_id = body.get("protectionGroupId")

        if not account_id and protection_group_id:
            # Direct Lambda invocation - lookup accountId from protection group
            print(f"DEBUG: No accountId provided, looking up from protectionGroupId={protection_group_id}")
            pg_table = get_protection_groups_table()
            pg_result = pg_table.get_item(Key={"protectionGroupId": protection_group_id})
            if "Item" not in pg_result:
                return response(
                    404,
                    error_response(
                        ERROR_NOT_FOUND,
                        "Protection Group not found",
                        details={"protectionGroupId": protection_group_id},
                    ),
                )
            account_id = pg_result["Item"].get("accountId")
            print(f"DEBUG: Found accountId={account_id} from protection group")

        if not account_id:
            return response(
                400,
                error_response(
                    ERROR_MISSING_PARAMETER,
                    "Missing required parameter: accountId or protectionGroupId",
                    details={
                        "provided": {
                            "accountId": account_id,
                            "protectionGroupId": protection_group_id,
                        }
                    },
                ),
            )

        # Query inventory database for servers matching tags
        print(f"DEBUG: Querying inventory for accountId={account_id}, region={region}, tags={tags}")
        inventory_table = get_inventory_table()

        # Query using SourceAccountIndex GSI (same as server selector)
        result = inventory_table.query(
            IndexName="SourceAccountIndex",
            KeyConditionExpression="sourceAccountId = :said",
            ExpressionAttributeValues={":said": account_id},
        )
        all_servers = result.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in result:
            result = inventory_table.query(
                IndexName="SourceAccountIndex",
                KeyConditionExpression="sourceAccountId = :said",
                ExpressionAttributeValues={":said": account_id},
                ExclusiveStartKey=result["LastEvaluatedKey"],
            )
            all_servers.extend(result.get("Items", []))

        print(f"DEBUG: Found {len(all_servers)} total servers in account {account_id}")

        # Filter by region (use replicationRegion, same as server selector)
        if region:
            all_servers = [s for s in all_servers if s.get("replicationRegion") == region]
            print(f"DEBUG: After region filter: {len(all_servers)} servers")

        # Filter by tags - server must have ALL specified tags
        matching_servers = []
        for server in all_servers:
            server_tags = server.get("sourceTags", {})
            matches_all_tags = all(server_tags.get(tag_key) == tag_value for tag_key, tag_value in tags.items())
            if matches_all_tags:
                matching_servers.append(server)

        print(f"DEBUG: After tag filter: {len(matching_servers)} servers matching all tags")

        # Transform to frontend-compatible format (same as server selector)
        resolved_servers = []
        for item in matching_servers:
            network = item.get("networkConfig", {})
            tags_dict = item.get("sourceTags", {})
            ram_bytes = int(item.get("ramBytes", 0))
            storage_bytes = int(item.get("totalStorageBytes", 0))
            server = {
                "sourceServerID": item.get("sourceServerID", ""),
                "arn": item.get("sourceServerArn", ""),
                "hostname": item.get("hostname", ""),
                "fqdn": item.get("fqdn", ""),
                "nameTag": tags_dict.get("Name", item.get("hostname", "")),
                "sourceInstanceId": item.get("instanceId", ""),
                "sourceIp": item.get("primaryIp", network.get("privateIp", "")),
                "sourceMac": item.get("macAddress", ""),
                "sourceRegion": item.get("sourceRegion", ""),
                "sourceAccount": item.get("sourceAccountId", ""),
                "os": item.get("osName", ""),
                "state": ("READY_FOR_RECOVERY" if item.get("replicationState") == "CONTINUOUS" else "NOT_READY"),
                "replicationState": item.get("replicationState", "UNKNOWN"),
                "lagDuration": item.get("lagDuration", ""),
                "lastSeen": item.get("lastSeen", item.get("lastUpdated", "")),
                "lastSnapshot": item.get("lastSnapshot", ""),
                "region": item.get("replicationRegion", ""),
                "instanceId": item.get("instanceId", ""),
                "agentVersion": item.get("agentVersion", ""),
                "stagingAccountId": item.get("stagingAccountId", ""),
                "sourceAccountId": item.get("sourceAccountId", ""),
                "hardware": {
                    "cpus": (
                        [
                            {
                                "modelName": item.get("cpuModel", ""),
                                "cores": int(item.get("cpuCores", 0)),
                            }
                        ]
                        if item.get("cpuModel")
                        else []
                    ),
                    "totalCores": int(item.get("cpuCores", 0)),
                    "ramBytes": ram_bytes,
                    "ramGiB": (round(ram_bytes / (1024**3), 1) if ram_bytes else 0),
                    "disks": [
                        {
                            "deviceName": d.get("deviceName", ""),
                            "bytes": int(d.get("bytes", 0)),
                            "sizeGiB": round(int(d.get("bytes", 0)) / (1024**3), 1),
                        }
                        for d in item.get("disks", [])
                    ],
                    "totalDiskGiB": (round(storage_bytes / (1024**3), 1) if storage_bytes else 0),
                },
                "networkInterfaces": (
                    [
                        {
                            "ips": [item.get("primaryIp", network.get("privateIp", ""))],
                            "macAddress": item.get("macAddress", ""),
                            "isPrimary": True,
                        }
                    ]
                    if item.get("primaryIp") or network.get("privateIp")
                    else []
                ),
                "vpcId": network.get("vpcId", ""),
                "subnetId": network.get("subnetId", ""),
                "privateIp": network.get("privateIp", item.get("primaryIp", "")),
                "securityGroups": network.get("securityGroups", []),
                "instanceProfile": network.get("instanceProfile", ""),
                "drsTags": tags_dict,
                "tags": tags_dict,
                "name": tags_dict.get("Name", item.get("hostname", "")),
                "assignedToProtectionGroup": None,
                "selectable": True,
                "dataSource": "inventory",
            }
            resolved_servers.append(server)

        return response(
            200,
            {
                "region": region,
                "tags": tags,
                "serverSelectionTags": tags,  # Backward compatibility
                "resolvedServers": resolved_servers,
                "sourceServers": resolved_servers,  # Backward compatibility
                "serverCount": len(resolved_servers),
                "resolvedAt": int(time.time()),
            },
        )

    except Exception as e:
        print(f"Error resolving protection group tags: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def create_protection_group(event: Dict, body: Dict) -> Dict:
    """
    Create a new Protection Group - supports both tag-based and explicit server selection.

    EXTRACTION TARGET: Data Management Handler (Phase 3)
    Validates name uniqueness, checks for server conflicts, and stores in DynamoDB.

    Args:
        event: Lambda event object (for invocation source detection)
        body: Request body with Protection Group configuration

    Returns:
        API Gateway response dict with statusCode and body
    """
    try:
        # FORCE DEPLOYMENT: camelCase migration complete - v1.3.1-hotfix
        print("DEBUG: create_protection_group v1.3.1-hotfix - camelCase validation active")
        print(f"DEBUG: create_protection_group called with body keys: {list(body.keys())}")
        print(f"DEBUG: body content: {json.dumps(body, indent=2, default=str)}")

        # Debug: Check specific fields
        print(f"DEBUG: serverSelectionTags present: {'serverSelectionTags' in body}")
        print(f"DEBUG: sourceServerIds present: {'sourceServerIds' in body}")
        if "serverSelectionTags" in body:
            print(f"DEBUG: serverSelectionTags value: {body['serverSelectionTags']}")
        if "sourceServerIds" in body:
            print(f"DEBUG: sourceServerIds value: {body['sourceServerIds']}")
        if "launchConfig" in body:
            print(f"DEBUG: launchConfig present with keys: {list(body['launchConfig'].keys())}")

        print("DEBUG: Starting validation checks...")
        print("DEBUG: About to validate groupName field")

        # Validate required fields - FIXED: camelCase field validation
        if "groupName" not in body:
            print("DEBUG: groupName not found in body, returning camelCase error")
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "groupName is required",
                    "field": "groupName",
                },
            )

        if "region" not in body:
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "region is required",
                    "field": "region",
                },
            )

        # Validate and extract account context (handles both
        # API Gateway and direct invocation modes)
        account_context = validate_account_context_for_invocation(event, body)

        # Sanitize user inputs
        name = sanitize_string(body["groupName"], max_length=64)
        description = sanitize_string(body.get("description", ""), max_length=1000)
        region = body["region"]

        # Validate name is not empty or whitespace-only
        if not name or not name.strip():
            return response(
                400,
                {
                    "error": "INVALID_NAME",
                    "message": ("groupName cannot be empty or " "whitespace-only"),
                    "field": "groupName",
                },
            )

        # Validate name length (1-64 characters)
        if len(name.strip()) > 64:
            return response(
                400,
                {
                    "error": "INVALID_NAME",
                    "message": ("groupName must be 64 characters or fewer"),
                    "field": "groupName",
                    "maxLength": 64,
                    "actualLength": len(name.strip()),
                },
            )

        # Use trimmed name
        name = name.strip()

        # Support both selection modes
        selection_tags = body.get("serverSelectionTags", {})
        source_server_ids = body.get("sourceServerIds", [])

        # Must have at least one selection method
        has_tags = isinstance(selection_tags, dict) and len(selection_tags) > 0
        has_servers = isinstance(source_server_ids, list) and len(source_server_ids) > 0

        if not has_tags and not has_servers:
            return response(
                400,
                error_response(
                    ERROR_INVALID_PARAMETER,
                    "At least one selection method required: serverSelectionTags or sourceServerIds",
                    details={"parameter": "serverSelectionTags or sourceServerIds"},
                ),
            )

        # Validate unique name (case-insensitive, global across all users)
        if not validate_unique_pg_name(name):
            return response(
                409,
                {
                    "error": "PG_NAME_EXISTS",
                    "message": f'A Protection Group named "{name}" already exists',
                    "existingName": name,
                },
            )

        # If using tags, check for tag conflicts with other PGs
        if has_tags:
            tag_conflicts = check_tag_conflicts_for_create(selection_tags, region)
            if tag_conflicts:
                return response(
                    409,
                    {
                        "error": "TAG_CONFLICT",
                        "message": "Another Protection Group already uses these exact tags",
                        "conflicts": tag_conflicts,
                    },
                )

        # If using explicit server IDs, validate they exist and aren't assigned
        # elsewhere
        if has_servers:
            print(f"DEBUG: Validating {len(source_server_ids)} explicit server IDs")

            # Create DRS account context for cross-account access
            drs_account_context = None
            if account_context.get("accountId"):
                current_account_id = get_current_account_id()
                target_account_id = account_context["accountId"]
                drs_account_context = {
                    "accountId": target_account_id,
                    "assumeRoleName": account_context.get("assumeRoleName"),
                    "isCurrentAccount": (current_account_id == target_account_id),
                    "externalId": ("drs-orchestration-cross-account"),
                }

            # Use cross-account DRS client
            regional_drs = create_drs_client(region, drs_account_context)
            print(f"DEBUG: Created DRS client for region {region} with account context")
            try:
                drs_response = regional_drs.describe_source_servers(filters={"sourceServerIDs": source_server_ids})
                found_ids = {s["sourceServerID"] for s in drs_response.get("items", [])}
                missing = set(source_server_ids) - found_ids
                if missing:
                    return response(
                        400,
                        error_response(
                            ERROR_INVALID_PARAMETER,
                            "Invalid DRS source server IDs",
                            details={
                                "parameter": "sourceServerIds",
                                "invalid_ids": list(missing),
                            },
                        ),
                    )
            except Exception as e:
                print(f"Error validating servers: {e}")
                # Continue anyway - servers might be valid

            # Check for server conflicts with other PGs
            conflicts = check_server_conflicts_for_create(source_server_ids)
            if conflicts:
                return response(
                    409,
                    {
                        "error": "SERVER_CONFLICT",
                        "message": "One or more servers are already assigned to another Protection Group",
                        "conflicts": conflicts,
                    },
                )

            # QUOTA VALIDATION: Check 100 servers per job limit
            if len(source_server_ids) > 100:
                return response(
                    400,
                    {
                        "error": "QUOTA_EXCEEDED",
                        "quotaType": "servers_per_job",
                        "message": "Protection Group cannot contain more than 100 servers",
                        "serverCount": len(source_server_ids),
                        "maxServers": 100,
                        "limit": "DRS Service Quota: Max 100 servers per job (not adjustable)",
                        "documentation": "https://docs.aws.amazon.com/general/latest/gr/drs.html",
                    },
                )

        # QUOTA VALIDATION: For tag-based selection, resolve and count servers
        if has_tags:
            # Use validated account context for cross-account access
            tag_account_context = None
            if account_context.get("accountId"):
                tag_account_context = {
                    "accountId": account_context["accountId"],
                    "assumeRoleName": account_context.get("assumeRoleName"),
                }

            # Resolve servers matching tags
            resolved = query_drs_servers_by_tags(region, selection_tags, tag_account_context)
            server_count = len(resolved)

            # Check 100 servers per job limit
            if server_count > 100:
                return response(
                    400,
                    {
                        "error": "QUOTA_EXCEEDED",
                        "quotaType": "servers_per_job",
                        "message": f"Tag selection matches {server_count} servers (max 100 per job)",
                        "serverCount": server_count,
                        "maxServers": 100,
                        "matchingServers": [s.get("sourceServerID") for s in resolved],
                        "limit": "DRS Service Quota: Max 100 servers per job (not adjustable)",
                        "documentation": "https://docs.aws.amazon.com/general/latest/gr/drs.html",
                        "recommendation": "Refine your tag selection to match fewer servers or split into multiple Protection Groups",  # noqa: E501
                    },
                )

        # Generate UUID for GroupId
        group_id = str(uuid.uuid4())
        timestamp = int(time.time())

        if timestamp <= 0:
            timestamp = int(time.time())
            if timestamp <= 0:
                raise Exception("Failed to generate valid timestamp")

        item = {
            "groupId": group_id,  # DynamoDB key (camelCase)
            "groupName": name,
            "description": description,
            "region": region,
            "accountId": account_context["accountId"],
            "assumeRoleName": account_context.get("assumeRoleName", ""),
            "owner": sanitize_string(body.get("owner", ""), max_length=255),
            "createdDate": timestamp,  # FIXED: camelCase
            "lastModifiedDate": timestamp,  # FIXED: camelCase
            "version": 1,  # FIXED: camelCase - Optimistic locking starts at version 1
            "launchConfigStatus": {
                "status": "not_configured",
                "lastApplied": None,
                "appliedBy": None,
                "serverConfigs": {},
                "errors": [],
            },
        }

        # Store the appropriate selection method (MUTUALLY EXCLUSIVE)
        # Tags take precedence if both are somehow provided
        if has_tags:
            item["serverSelectionTags"] = selection_tags
            # Resolve servers from tags and store the actual server IDs
            # This allows launch configs to be pre-applied to the resolved servers
            print("DEBUG: Resolving servers from tags for protection group creation")
            tag_account_context = None
            if account_context.get("accountId"):
                current_account_id = get_current_account_id()
                tag_account_context = {
                    "accountId": account_context["accountId"],
                    "assumeRoleName": account_context.get("assumeRoleName"),
                    "isCurrentAccount": account_context["accountId"] == current_account_id,
                }
            resolved_servers = query_drs_servers_by_tags(region, selection_tags, tag_account_context)
            resolved_server_ids = [s.get("sourceServerID") for s in resolved_servers if s.get("sourceServerID")]
            item["sourceServerIds"] = resolved_server_ids  # Store resolved IDs
            print(f"DEBUG: Resolved {len(resolved_server_ids)} servers from tags: {resolved_server_ids}")
        elif has_servers:
            item["sourceServerIds"] = source_server_ids
            item["serverSelectionTags"] = {}  # Ensure empty

        # Handle launchConfig if provided
        if "launchConfig" in body:
            launch_config = body["launchConfig"]

            # Validate launchConfig structure
            if not isinstance(launch_config, dict):
                return response(
                    400,
                    {
                        "error": "launchConfig must be an object",
                        "code": "INVALID_LAUNCH_CONFIG",
                    },
                )

            # Validate securityGroupIds is array if present
            if "securityGroupIds" in launch_config:
                if not isinstance(launch_config["securityGroupIds"], list):
                    return response(
                        400,
                        {
                            "error": "securityGroupIds must be an array",
                            "code": "INVALID_SECURITY_GROUPS",
                        },
                    )

            # Store launchConfig in item
            item["launchConfig"] = launch_config

        print(f"Creating Protection Group: {group_id}")

        # Store in DynamoDB
        get_protection_groups_table().put_item(Item=item)

        # Apply launch configurations after group creation (if provided)
        if "launchConfig" in body:
            launch_config = body["launchConfig"]

            # Get server IDs to apply settings to - use the already-resolved IDs from item
            server_ids_to_apply = item.get("sourceServerIds", [])
            print(f"DEBUG: Using {len(server_ids_to_apply)} server IDs for launch config application")

            # Apply launch configs if we have servers
            if server_ids_to_apply:
                try:
                    print(f"Applying launch configs to {len(server_ids_to_apply)} servers")

                    # Build launch_configs dict (same config for all servers)
                    launch_configs = {server_id: launch_config for server_id in server_ids_to_apply}

                    # Prepare account context for cross-account operations
                    lc_account_context = None
                    if account_context.get("accountId"):
                        current_account_id = get_current_account_id()
                        target_account_id = account_context["accountId"]
                        if current_account_id != target_account_id:
                            lc_account_context = {
                                "accountId": target_account_id,
                                "roleName": account_context.get("assumeRoleName", "OrchestrationRole"),
                            }

                    # Apply configurations with timeout (allow group creation to succeed even if this times out)
                    apply_result = apply_launch_configs_to_group(
                        group_id=group_id,
                        region=region,
                        server_ids=server_ids_to_apply,
                        launch_configs=launch_configs,
                        account_context=lc_account_context,
                        timeout_seconds=60,  # 60 second timeout for group creation
                    )

                    print(f"Launch config application result: {apply_result}")

                    # Update launchConfigStatus in DynamoDB
                    config_status = {
                        "status": apply_result["status"],
                        "lastApplied": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "appliedBy": None,  # TODO: Extract from event context
                        "serverConfigs": apply_result["serverConfigs"],
                        "errors": apply_result["errors"],
                    }

                    persist_config_status(group_id, config_status)

                    # Update item with latest status for response
                    item["launchConfigStatus"] = config_status

                    print(f"Launch config status persisted: {config_status['status']}")

                except LaunchConfigTimeoutError as e:
                    # Timeout is acceptable - group creation succeeds, configs marked as pending
                    print(f"Launch config application timed out: {e}")
                    config_status = {
                        "status": "pending",
                        "lastApplied": None,
                        "appliedBy": None,
                        "serverConfigs": {},
                        "errors": [str(e)],
                    }
                    persist_config_status(group_id, config_status)
                    item["launchConfigStatus"] = config_status

                except LaunchConfigApplicationError as e:
                    # Application error - group creation succeeds, configs marked as failed
                    print(f"Launch config application failed: {e}")
                    config_status = {
                        "status": "failed",
                        "lastApplied": None,
                        "appliedBy": None,
                        "serverConfigs": {},
                        "errors": [str(e)],
                    }
                    persist_config_status(group_id, config_status)
                    item["launchConfigStatus"] = config_status

                except Exception as e:
                    # Unexpected error - log but don't fail group creation
                    print(f"Unexpected error applying launch configs: {e}")
                    import traceback

                    traceback.print_exc()
                    config_status = {
                        "status": "failed",
                        "lastApplied": None,
                        "appliedBy": None,
                        "serverConfigs": {},
                        "errors": [f"Unexpected error: {str(e)}"],
                    }
                    persist_config_status(group_id, config_status)
                    item["launchConfigStatus"] = config_status
            else:
                print("WARNING: launchConfig provided but no servers to apply to")

        # Return raw camelCase database fields directly - no transformation
        # needed
        item["protectionGroupId"] = item["groupId"]  # Only add this alias for compatibility
        return response(201, item)

    except InputValidationError as e:
        print(f"Validation error creating Protection Group: {e}")
        return response(
            400,
            {
                "error": "VALIDATION_ERROR",
                "message": str(e),
            },
        )

    except Exception as e:
        print(f"Error creating Protection Group: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def get_protection_groups(query_params: Dict = None) -> Dict:
    """List all Protection Groups with optional account filtering"""
    try:
        query_params = query_params or {}
        account_id = query_params.get("accountId")

        result = get_protection_groups_table().scan()
        groups = result.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in result:
            result = get_protection_groups_table().scan(ExclusiveStartKey=result["LastEvaluatedKey"])
            groups.extend(result.get("Items", []))

        # Filter by account if specified
        if account_id:
            filtered_groups = []
            for group in groups:
                # Only include groups that explicitly match the requested
                # account
                group_account = group.get("accountId")
                if group_account == account_id:
                    filtered_groups.append(group)
            groups = filtered_groups

        # Return raw camelCase database fields directly - no transformation
        # needed
        for group in groups:
            group["protectionGroupId"] = group["groupId"]  # Add alias for compatibility
        return response(200, {"groups": groups, "count": len(groups)})

    except Exception as e:
        print(f"Error listing Protection Groups: {str(e)}")
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def get_protection_group(group_id: str) -> Dict:
    """Get a single Protection Group by ID"""
    try:
        result = get_protection_groups_table().get_item(Key={"groupId": group_id})

        if "Item" not in result:
            return response(
                404,
                error_response(
                    ERROR_NOT_FOUND,
                    "Protection Group not found",
                    details={"Protection Group": group_id},
                ),
            )

        group = result["Item"]

        # Return raw camelCase database fields directly - no transformation
        # needed
        group["protectionGroupId"] = group["groupId"]  # Add alias for compatibility
        return response(200, group)

    except Exception as e:
        print(f"Error getting Protection Group: {str(e)}")
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def update_protection_group(group_id: str, body: Dict) -> Dict:
    """Update an existing Protection Group with validation and optimistic locking"""
    try:
        # Check if group exists
        result = get_protection_groups_table().get_item(Key={"groupId": group_id})
        if "Item" not in result:
            return response(
                404,
                error_response(
                    ERROR_NOT_FOUND,
                    "Protection Group not found",
                    details={"Protection Group": group_id},
                ),
            )

        existing_group = result["Item"]
        current_version = existing_group.get("version", 1)  # FIXED: camelCase - Default to 1 for legacy items

        # Optimistic locking: Check if client provided expected version
        client_version = body.get("version") or body.get("Version")
        if client_version is not None:
            # Convert to int for comparison (handles Decimal from DynamoDB)
            client_version = int(client_version)
            if client_version != int(current_version):
                return response(
                    409,
                    {
                        "error": "VERSION_CONFLICT",
                        "message": "Resource was modified by another user. Please refresh and try again.",
                        "expectedVersion": client_version,
                        "currentVersion": int(current_version),
                        "resourceId": group_id,
                    },
                )

        # BLOCK: Cannot update protection group if it's part of a RUNNING execution
        # Note: PAUSED executions allow edits - only block when actively
        # running
        active_exec_info = get_active_execution_for_protection_group(group_id)
        if active_exec_info:
            exec_status = active_exec_info.get("status", "").upper()
            # Only block if execution is actively running (not paused)
            running_statuses = [
                "PENDING",
                "POLLING",
                "INITIATED",
                "LAUNCHING",
                "STARTED",
                "IN_PROGRESS",
                "RUNNING",
                "CANCELLING",
            ]
            if exec_status in running_statuses:
                return response(
                    409,
                    {
                        "error": "PG_IN_ACTIVE_EXECUTION",
                        "message": "Cannot modify Protection Group while it is part of a running execution",
                        "activeExecution": active_exec_info,
                    },
                )

        # Prevent region changes
        if "region" in body and body["region"] != existing_group.get("region"):
            return response(
                400,
                error_response(
                    ERROR_INVALID_PARAMETER,
                    "Invalid parameter value",
                    details={
                        "parameter": "region",
                        "value": body.get("region"),
                        "expected": "cannot be changed after creation",
                    },
                ),
            )

        # Validate name if provided
        if "groupName" in body:
            name = body["groupName"]

            # Validate name is not empty or whitespace-only
            if not name or not name.strip():
                return response(
                    400,
                    {
                        "error": "INVALID_NAME",
                        "message": "groupName cannot be empty or whitespace-only",
                        "field": "groupName",
                    },
                )

            # Validate name length (1-64 characters)
            if len(name.strip()) > 64:
                return response(
                    400,
                    {
                        "error": "INVALID_NAME",
                        "message": "groupName must be 64 characters or fewer",
                        "field": "groupName",
                        "maxLength": 64,
                        "actualLength": len(name.strip()),
                    },
                )

            # Trim the name
            body["groupName"] = name.strip()

            # Validate unique name if changing
            if body["groupName"] != existing_group.get("groupName"):
                if not validate_unique_pg_name(body["groupName"], group_id):
                    return response(
                        409,
                        {
                            "error": "PG_NAME_EXISTS",
                            "message": f'A Protection Group named "{body["groupName"]}" already exists',
                            "existingName": body["groupName"],
                        },
                    )

        # Validate tags if provided
        if "serverSelectionTags" in body:
            selection_tags = body["serverSelectionTags"]
            if not isinstance(selection_tags, dict) or len(selection_tags) == 0:
                return response(
                    400,
                    {
                        "error": "INVALID_TAGS",
                        "message": "serverSelectionTags must be a non-empty object with tag key-value pairs",
                    },
                )

            # Check for tag conflicts with other PGs (excluding this one)
            region = existing_group.get("region", "")
            tag_conflicts = check_tag_conflicts_for_update(selection_tags, region, group_id)
            if tag_conflicts:
                return response(
                    409,
                    {
                        "error": "TAG_CONFLICT",
                        "message": "Another Protection Group already uses these exact tags",
                        "conflicts": tag_conflicts,
                    },
                )

        # Validate server IDs if provided
        if "sourceServerIds" in body:
            source_server_ids = body["sourceServerIds"]
            if not isinstance(source_server_ids, list) or len(source_server_ids) == 0:
                return response(
                    400,
                    {
                        "error": "INVALID_SERVERS",
                        "message": "SourceServerIds must be a non-empty array",
                    },
                )

            # Check for conflicts with other PGs (excluding this one)
            conflicts = check_server_conflicts_for_update(source_server_ids, group_id)
            if conflicts:
                return response(
                    409,
                    {
                        "error": "SERVER_CONFLICT",
                        "message": "One or more servers are already assigned to another Protection Group",
                        "conflicts": conflicts,
                    },
                )

        # Build update expression with version increment (optimistic locking)
        # Use v1.3.0 working pattern: simple string concatenation with
        # camelCase fields
        new_version = int(current_version) + 1
        update_expression = "SET lastModifiedDate = :timestamp, version = :new_version"
        expression_values = {
            ":timestamp": int(time.time()),
            ":new_version": new_version,
            ":current_version": int(current_version),
        }
        expression_names = {}

        if "groupName" in body:
            update_expression += ", groupName = :name"
            expression_values[":name"] = body["groupName"]

        if "description" in body:
            update_expression += ", #desc = :desc"
            expression_values[":desc"] = body["description"]
            expression_names["#desc"] = "description"
            print(f"DEBUG: Adding description to update: {body['description']}")

        # MUTUALLY EXCLUSIVE: Tags OR Servers, not both
        # When one is set, clear the other AND remove old PascalCase fields if
        # they exist

        if "serverSelectionTags" in body:
            update_expression += ", serverSelectionTags = :tags"
            expression_values[":tags"] = body["serverSelectionTags"]

            # Resolve servers from tags and store the actual server IDs
            print("DEBUG: Resolving servers from tags for protection group update")
            tag_account_context = None
            if existing_group.get("accountId"):
                current_account_id = get_current_account_id()
                tag_account_context = {
                    "accountId": existing_group["accountId"],
                    "assumeRoleName": existing_group.get("assumeRoleName"),
                    "isCurrentAccount": existing_group["accountId"] == current_account_id,
                }
            resolved_servers = query_drs_servers_by_tags(
                existing_group.get("region"), body["serverSelectionTags"], tag_account_context
            )
            resolved_server_ids = [s.get("sourceServerID") for s in resolved_servers if s.get("sourceServerID")]
            update_expression += ", sourceServerIds = :resolved_servers"
            expression_values[":resolved_servers"] = resolved_server_ids
            print(f"DEBUG: Resolved {len(resolved_server_ids)} servers from tags: {resolved_server_ids}")

            # Remove old PascalCase fields only if they exist
            if "ServerSelectionTags" in existing_group:
                update_expression += " REMOVE ServerSelectionTags"
            if "SourceServerIds" in existing_group:
                update_expression += " REMOVE SourceServerIds"

        if "sourceServerIds" in body:
            update_expression += ", sourceServerIds = :servers"
            expression_values[":servers"] = body["sourceServerIds"]
            # Clear serverSelectionTags when using explicit servers
            update_expression += ", serverSelectionTags = :empty_tags"
            expression_values[":empty_tags"] = {}
            # Remove old PascalCase fields only if they exist
            if "ServerSelectionTags" in existing_group:
                update_expression += " REMOVE ServerSelectionTags"
            if "SourceServerIds" in existing_group:
                update_expression += " REMOVE SourceServerIds"

        # Handle launchConfig - EC2 launch settings for recovery instances
        # Detect if servers or configs changed to determine if re-apply needed
        servers_changed = False
        configs_changed = False

        if "sourceServerIds" in body:
            old_servers = set(existing_group.get("sourceServerIds", []))
            new_servers = set(body["sourceServerIds"])
            servers_changed = old_servers != new_servers

        if "serverSelectionTags" in body:
            old_tags = existing_group.get("serverSelectionTags", {})
            new_tags = body["serverSelectionTags"]
            servers_changed = old_tags != new_tags

        if "launchConfig" in body:
            old_config = existing_group.get("launchConfig", {})
            new_config = body["launchConfig"]
            configs_changed = old_config != new_config

        # Apply launch configs if servers or configs changed
        if "launchConfig" in body and (servers_changed or configs_changed):
            launch_config = body["launchConfig"]

            # Validate launchConfig structure
            if not isinstance(launch_config, dict):
                return response(
                    400,
                    {
                        "error": "launchConfig must be an object",
                        "code": "INVALID_LAUNCH_CONFIG",
                    },
                )

            # Validate securityGroupIds is array if present
            if "securityGroupIds" in launch_config:
                if not isinstance(launch_config["securityGroupIds"], list):
                    return response(
                        400,
                        {
                            "error": "securityGroupIds must be an array",
                            "code": "INVALID_SECURITY_GROUPS",
                        },
                    )

            # Get server IDs to apply settings to
            region = existing_group.get("region")
            server_ids = body.get("sourceServerIds", existing_group.get("sourceServerIds", []))

            # If using tags, resolve servers first
            if not server_ids and (body.get("serverSelectionTags") or existing_group.get("serverSelectionTags")):
                tags = body.get(
                    "serverSelectionTags",
                    existing_group.get("serverSelectionTags", {}),
                )
                # Extract account context from existing group
                account_context = None
                if existing_group.get("accountId"):
                    account_context = {
                        "accountId": existing_group.get("accountId"),
                        "assumeRoleName": existing_group.get("assumeRoleName"),
                    }
                resolved = query_drs_servers_by_tags(
                    region,
                    tags,
                    account_context,
                )
                server_ids = [s.get("sourceServerID") for s in resolved if s.get("sourceServerID")]

            # Apply launch configs using new service
            if server_ids:
                try:
                    print(f"Applying launch configs to " f"{len(server_ids)} servers (update)")

                    # Build launch_configs dict
                    launch_configs = {server_id: launch_config for server_id in server_ids}

                    # Prepare account context for cross-account
                    lc_account_context = None
                    if existing_group.get("accountId"):
                        current_account_id = get_current_account_id()
                        target_account_id = existing_group["accountId"]
                        if current_account_id != target_account_id:
                            lc_account_context = {
                                "accountId": target_account_id,
                                "roleName": existing_group.get("assumeRoleName", "OrchestrationRole"),
                            }

                    # Apply with timeout (allow update to succeed)
                    apply_result = apply_launch_configs_to_group(
                        group_id=group_id,
                        region=region,
                        server_ids=server_ids,
                        launch_configs=launch_configs,
                        account_context=lc_account_context,
                        timeout_seconds=60,
                    )

                    print(f"Launch config result: {apply_result}")

                    # Update launchConfigStatus in DynamoDB
                    config_status = {
                        "status": apply_result["status"],
                        "lastApplied": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "appliedBy": None,
                        "serverConfigs": apply_result["serverConfigs"],
                        "errors": apply_result["errors"],
                    }

                    persist_config_status(group_id, config_status)

                    # Add to update expression
                    update_expression += ", launchConfigStatus = :launchConfigStatus"
                    expression_values[":launchConfigStatus"] = config_status

                    print(f"Launch config status: " f"{config_status['status']}")

                except LaunchConfigTimeoutError as e:
                    # Timeout OK - update succeeds, configs pending
                    print(f"Launch config timed out: {e}")
                    config_status = {
                        "status": "pending",
                        "lastApplied": None,
                        "appliedBy": None,
                        "serverConfigs": {},
                        "errors": [str(e)],
                    }
                    persist_config_status(group_id, config_status)
                    update_expression += ", launchConfigStatus = :launchConfigStatus"
                    expression_values[":launchConfigStatus"] = config_status

                except LaunchConfigApplicationError as e:
                    # Application error - update succeeds, configs failed
                    print(f"Launch config failed: {e}")
                    config_status = {
                        "status": "failed",
                        "lastApplied": None,
                        "appliedBy": None,
                        "serverConfigs": {},
                        "errors": [str(e)],
                    }
                    persist_config_status(group_id, config_status)
                    update_expression += ", launchConfigStatus = :launchConfigStatus"
                    expression_values[":launchConfigStatus"] = config_status

                except Exception as e:
                    # Unexpected error - log but don't fail update
                    print(f"Unexpected error applying configs: {e}")
                    import traceback

                    traceback.print_exc()
                    config_status = {
                        "status": "failed",
                        "lastApplied": None,
                        "appliedBy": None,
                        "serverConfigs": {},
                        "errors": [f"Unexpected error: {str(e)}"],
                    }
                    persist_config_status(group_id, config_status)
                    update_expression += ", launchConfigStatus = :launchConfigStatus"
                    expression_values[":launchConfigStatus"] = config_status

            # Store launchConfig in DynamoDB
            update_expression += ", launchConfig = :launchConfig"
            expression_values[":launchConfig"] = launch_config
        elif "launchConfig" in body:
            # Config provided but no changes - just store it
            update_expression += ", launchConfig = :launchConfig"
            expression_values[":launchConfig"] = body["launchConfig"]

        # Handle servers array - per-server launch template configurations
        servers_apply_results = None
        if "servers" in body:
            servers = body["servers"]

            # Validate servers structure
            if not isinstance(servers, list):
                return response(
                    400,
                    {
                        "error": "servers must be an array",
                        "code": "INVALID_SERVERS",
                    },
                )

            # Apply per-server launch configs to AWS DRS/EC2
            region = existing_group.get("region")
            if servers and region:
                # Build updated protection group dict for config merge
                updated_pg = dict(existing_group)
                updated_pg["servers"] = servers
                # Include updated launchConfig if provided
                if "launchConfig" in body:
                    updated_pg["launchConfig"] = body["launchConfig"]

                # Extract server IDs from servers array
                server_ids = [s.get("sourceServerId") for s in servers if s.get("sourceServerId")]

                # Get group name (use updated name if provided, else existing)
                pg_name = body.get("groupName", existing_group.get("groupName", ""))
                pg_id = group_id

                # Apply launch configs to AWS (uses config_merge to get
                # effective configs)
                servers_apply_results = apply_launch_config_to_servers(
                    server_ids,
                    updated_pg.get("launchConfig", {}),
                    region,
                    protection_group=updated_pg,  # Pass full PG for per-server overrides
                    protection_group_id=pg_id,
                    protection_group_name=pg_name,
                )

                # If any failed, return error (don't save partial state)
                if servers_apply_results.get("failed", 0) > 0:
                    failed_servers = [
                        d for d in servers_apply_results.get("details", []) if d.get("status") == "failed"
                    ]
                    return response(
                        400,
                        {
                            "error": "Failed to apply per-server launch settings",
                            "code": "SERVERS_CONFIG_APPLY_FAILED",
                            "failedServers": failed_servers,
                            "applyResults": servers_apply_results,
                        },
                    )

            # Store servers array in DynamoDB
            update_expression += ", servers = :servers_array"
            expression_values[":servers_array"] = servers

        print(f"DEBUG: Final update expression: {update_expression}")
        print(f"DEBUG: Expression values: {expression_values}")

        # Update item with conditional write (optimistic locking)
        # Only succeeds if version hasn't changed since we read it
        update_args = {
            "Key": {"groupId": group_id},
            "UpdateExpression": update_expression,
            # FIXED: camelCase
            "ConditionExpression": "version = :current_version OR attribute_not_exists(version)",
            "ExpressionAttributeValues": expression_values,
            "ReturnValues": "ALL_NEW",
        }

        if expression_names:
            update_args["ExpressionAttributeNames"] = expression_names

        try:
            result = get_protection_groups_table().update_item(**update_args)
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            # Another process updated the item between our read and write
            return response(
                409,
                {
                    "error": "VERSION_CONFLICT",
                    "message": "Resource was modified by another user. Please refresh and try again.",
                    "resourceId": group_id,
                },
            )

        # Transform to camelCase for frontend
        response_item = result["Attributes"]

        print(f"Updated Protection Group: {group_id}")
        return response(200, response_item)

    except Exception as e:
        print(f"Error updating Protection Group: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def delete_protection_group(group_id: str) -> Dict:
    """Delete a Protection Group - blocked if used in ANY recovery plan"""
    try:
        # Check if group is referenced in ANY Recovery Plans (not just active ones)
        # Scan all plans and check if any wave references this PG
        plans_result = get_recovery_plans_table().scan()
        all_plans = plans_result.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in plans_result:
            plans_result = get_recovery_plans_table().scan(ExclusiveStartKey=plans_result["LastEvaluatedKey"])
            all_plans.extend(plans_result.get("Items", []))

        # Find plans that reference this protection group
        referencing_plans = []
        for plan in all_plans:
            for wave in plan.get("waves", []):
                if wave.get("protectionGroupId") == group_id:
                    referencing_plans.append(
                        {
                            "planId": plan.get("planId"),
                            "planName": plan.get("planName"),
                            "waveName": wave.get("waveName"),
                        }
                    )
                    break  # Only need to find one wave per plan

        if referencing_plans:
            plan_names = list(set([p["planName"] for p in referencing_plans]))
            return response(
                409,
                {
                    "error": "PG_IN_USE",
                    "message": f"Cannot delete Protection Group - it is used in {len(plan_names)} Recovery Plan(s)",
                    "plans": plan_names,
                    "details": referencing_plans,
                },
            )

        # Delete the group
        get_protection_groups_table().delete_item(Key={"groupId": group_id})

        print(f"Deleted Protection Group: {group_id}")
        return response(200, {"message": "Protection Group deleted successfully"})

    except Exception as e:
        print(f"Error deleting Protection Group: {str(e)}")
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def get_server_launch_config(group_id: str, server_id: str) -> Dict:
    """
    Get per-server launch configuration with effective config preview.

    Returns the server-specific configuration along with the effective
    configuration that results from merging group defaults with server
    overrides.

    Args:
        group_id: Protection group ID
        server_id: Source server ID

    Returns:
        Response with server configuration and effective config:
        {
            "sourceServerId": "s-xxx",
            "instanceId": "i-xxx",
            "instanceName": "web-server-01",
            "useGroupDefaults": false,
            "launchTemplate": {
                "staticPrivateIp": "10.0.1.100",
                "instanceType": "c6a.xlarge"
            },
            "effectiveConfig": {
                "subnetId": "subnet-xxx",
                "securityGroupIds": ["sg-xxx"],
                "instanceType": "c6a.xlarge",
                "staticPrivateIp": "10.0.1.100"
            }
        }

    Requirements: 2.1, 2.4
    """
    try:
        # Get protection group
        result = get_protection_groups_table().get_item(Key={"groupId": group_id})

        if "Item" not in result:
            return response(
                404,
                error_response(
                    ERROR_NOT_FOUND,
                    "Protection Group not found",
                    details={"Protection Group": group_id},
                ),
            )

        protection_group = result["Item"]

        # Find server in protection group's servers array
        servers = protection_group.get("servers", [])
        server_config = next(
            (s for s in servers if s.get("sourceServerId") == server_id),
            None,
        )

        # If server not found in servers array, return default config
        if not server_config:
            # Server exists in sourceServerIds but has no custom config
            source_server_ids = protection_group.get("sourceServerIds", [])
            if server_id not in source_server_ids:
                return response(
                    404,
                    {
                        "error": "Server not found in protection group",
                        "serverId": server_id,
                        "groupId": group_id,
                    },
                )

            # Return default configuration (no custom overrides)
            group_defaults = protection_group.get("launchConfig", {})
            return response(
                200,
                {
                    "sourceServerId": server_id,
                    "useGroupDefaults": True,
                    "launchTemplate": {},
                    "effectiveConfig": group_defaults,
                },
            )

        # Get effective configuration (group defaults + server overrides)
        effective_config = get_effective_launch_config(protection_group, server_id)

        # Build response with camelCase fields for frontend
        response_data = {
            "sourceServerId": server_config.get("sourceServerId"),
            "instanceId": server_config.get("instanceId"),
            "instanceName": server_config.get("instanceName"),
            "tags": server_config.get("tags", {}),
            "useGroupDefaults": server_config.get("useGroupDefaults", True),
            "launchTemplate": server_config.get("launchTemplate", {}),
            "effectiveConfig": effective_config,
        }

        return response(200, response_data)

    except Exception as e:
        print(f"Error getting server launch config: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def update_server_launch_config(group_id: str, server_id: str, body: Dict) -> Dict:
    """
    Update per-server launch configuration.

    Validates all fields, updates DynamoDB, applies configuration to DRS/EC2,
    and records audit trail entry.

    Args:
        group_id: Protection group ID
        server_id: Source server ID
        body: Request body with useGroupDefaults and launchTemplate

    Request Body:
        {
            "useGroupDefaults": false,
            "launchTemplate": {
                "staticPrivateIp": "10.0.1.100",
                "instanceType": "c6a.xlarge",
                "securityGroupIds": ["sg-xxx"],
                "subnetId": "subnet-xxx",
                "instanceProfileName": "demo-ec2-profile"
            }
        }

    Returns:
        Response with updated configuration:
        {
            "sourceServerId": "s-xxx",
            "instanceId": "i-xxx",
            "useGroupDefaults": false,
            "launchTemplate": {...},
            "effectiveConfig": {...},
            "auditTrail": {
                "timestamp": "2026-01-27T23:00:00Z",
                "user": "admin@example.com",
                "changedFields": ["staticPrivateIp", "instanceType"]
            }
        }

    Requirements: 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 8.1
    """
    try:
        # Import validation functions
        from shared.launch_config_validation import (
            validate_static_ip,
            validate_aws_approved_fields,
            validate_security_groups,
            validate_instance_type,
            validate_iam_profile,
            validate_subnet,
        )

        # Get protection group
        result = get_protection_groups_table().get_item(Key={"groupId": group_id})

        if "Item" not in result:
            return response(
                404,
                error_response(
                    ERROR_NOT_FOUND,
                    "Protection Group not found",
                    details={"Protection Group": group_id},
                ),
            )

        protection_group = result["Item"]
        region = protection_group.get("region")

        # Verify server exists in protection group
        source_server_ids = protection_group.get("sourceServerIds", [])
        if server_id not in source_server_ids:
            return response(
                404,
                {
                    "error": "Server not found in protection group",
                    "serverId": server_id,
                    "groupId": group_id,
                },
            )

        # Parse request body
        use_group_defaults = body.get("useGroupDefaults", True)
        launch_template = body.get("launchTemplate", {})

        # Validate AWS-approved fields only
        field_validation = validate_aws_approved_fields(launch_template)
        if not field_validation.get("valid"):
            return response(400, field_validation)

        # Validate individual fields
        validation_errors = []

        # Validate static private IP
        if launch_template.get("staticPrivateIp"):
            static_ip = launch_template["staticPrivateIp"]
            # Get subnet ID (from launch template or group defaults)
            subnet_id = launch_template.get("subnetId") or protection_group.get("launchConfig", {}).get("subnetId")

            if not subnet_id:
                validation_errors.append(
                    {
                        "field": "subnetId",
                        "error": "MISSING_SUBNET",
                        "message": "subnetId is required when setting " "staticPrivateIp",
                    }
                )
            else:
                ip_validation = validate_static_ip(static_ip, subnet_id, region)
                if not ip_validation.get("valid"):
                    validation_errors.append(ip_validation)

                # Check for duplicate IPs across servers in same subnet
                from shared.launch_config_validation import (
                    validate_no_duplicate_ips,
                )

                duplicate_check = validate_no_duplicate_ips(protection_group, server_id, static_ip, subnet_id)
                if not duplicate_check.get("valid"):
                    validation_errors.append(duplicate_check)

        # Validate security groups
        if launch_template.get("securityGroupIds"):
            sg_ids = launch_template["securityGroupIds"]
            # Get VPC ID from subnet
            subnet_id = launch_template.get("subnetId") or protection_group.get("launchConfig", {}).get("subnetId")

            if subnet_id:
                # Get VPC ID from subnet
                subnet_validation = validate_subnet(subnet_id, region)
                if subnet_validation.get("valid"):
                    vpc_id = subnet_validation["details"]["vpcId"]
                    sg_validation = validate_security_groups(sg_ids, vpc_id, region)
                    if not sg_validation.get("valid"):
                        validation_errors.append(sg_validation)
                else:
                    validation_errors.append(subnet_validation)

        # Validate instance type
        if launch_template.get("instanceType"):
            instance_type = launch_template["instanceType"]
            type_validation = validate_instance_type(instance_type, region)
            if not type_validation.get("valid"):
                validation_errors.append(type_validation)

        # Validate IAM instance profile
        if launch_template.get("instanceProfileName"):
            profile_name = launch_template["instanceProfileName"]
            profile_validation = validate_iam_profile(profile_name, region)
            if not profile_validation.get("valid"):
                validation_errors.append(profile_validation)

        # Validate subnet
        if launch_template.get("subnetId"):
            subnet_id = launch_template["subnetId"]
            subnet_validation = validate_subnet(subnet_id, region)
            if not subnet_validation.get("valid"):
                validation_errors.append(subnet_validation)

        # Return validation errors if any
        if validation_errors:
            return response(
                400,
                {
                    "error": "VALIDATION_FAILED",
                    "message": "One or more fields failed validation",
                    "validationErrors": validation_errors,
                },
            )

        # Get existing server config to track changes
        servers = protection_group.get("servers", [])
        existing_server_config = next(
            (s for s in servers if s.get("sourceServerId") == server_id),
            None,
        )

        # Track changed fields for audit trail
        changed_fields = []
        if existing_server_config:
            old_template = existing_server_config.get("launchTemplate", {})
            for key, value in launch_template.items():
                if old_template.get(key) != value:
                    changed_fields.append(key)
            # Check if useGroupDefaults changed
            if existing_server_config.get("useGroupDefaults", True) != use_group_defaults:
                changed_fields.append("useGroupDefaults")
        else:
            # New server config - all fields are changes
            changed_fields = list(launch_template.keys())
            if not use_group_defaults:
                changed_fields.append("useGroupDefaults")

        # Build new server configuration
        new_server_config = {
            "sourceServerId": server_id,
            "useGroupDefaults": use_group_defaults,
            "launchTemplate": launch_template,
        }

        # Add instance metadata if available
        try:
            regional_drs = boto3.client("drs", region_name=region)
            drs_response = regional_drs.describe_source_servers(filters={"sourceServerIDs": [server_id]})
            if drs_response.get("items"):
                server_info = drs_response["items"][0]
                source_props = server_info.get("sourceProperties", {})
                new_server_config["instanceId"] = source_props.get("lastUpdatedDateTime")
                identification = source_props.get("identificationHints", {})
                new_server_config["instanceName"] = identification.get("hostname", "")
                new_server_config["tags"] = server_info.get("tags", {})
        except Exception as e:
            print(f"Warning: Could not fetch server metadata: {e}")

        # Update or add server config in protection group
        if existing_server_config:
            # Update existing config
            for i, s in enumerate(servers):
                if s.get("sourceServerId") == server_id:
                    servers[i] = new_server_config
                    break
        else:
            # Add new server config
            servers.append(new_server_config)

        # If useGroupDefaults is true and no custom fields, remove from array
        if use_group_defaults and not launch_template:
            servers = [s for s in servers if s.get("sourceServerId") != server_id]

        # Update protection group in DynamoDB
        from datetime import datetime, timezone

        timestamp = datetime.now(timezone.utc).isoformat()

        get_protection_groups_table().update_item(
            Key={"groupId": group_id},
            UpdateExpression="SET servers = :servers, updatedAt = :updated",
            ExpressionAttributeValues={
                ":servers": servers,
                ":updated": timestamp,
            },
        )

        # Apply configuration to DRS/EC2
        apply_result = apply_launch_config_to_servers(
            server_ids=[server_id],
            launch_config=protection_group.get("launchConfig", {}),
            region=region,
            protection_group={
                **protection_group,
                "servers": servers,
            },
            protection_group_id=group_id,
            protection_group_name=protection_group.get("groupName"),
        )

        # Get effective configuration for response
        updated_protection_group = {**protection_group, "servers": servers}
        effective_config = get_effective_launch_config(updated_protection_group, server_id)

        # Build audit trail entry
        audit_entry = {
            "timestamp": timestamp,
            "user": protection_group.get("owner", "unknown"),
            "changedFields": changed_fields,
            "applyResult": apply_result,
        }

        # Build response
        response_data = {
            "sourceServerId": server_id,
            "instanceId": new_server_config.get("instanceId"),
            "instanceName": new_server_config.get("instanceName"),
            "tags": new_server_config.get("tags", {}),
            "useGroupDefaults": use_group_defaults,
            "launchTemplate": launch_template,
            "effectiveConfig": effective_config,
            "auditTrail": audit_entry,
        }

        return response(200, response_data)

    except ClientError as e:
        print(f"DynamoDB error updating server launch config: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_DYNAMODB_ERROR,
                "DynamoDB operation failed",
                details={"operation": "update", "error": str(e)},
            ),
        )
    except Exception as e:
        print(f"Error updating server launch config: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def delete_server_launch_config(group_id: str, server_id: str) -> Dict:
    """
    Delete per-server launch configuration and revert to group defaults.

    Removes the server from the servers array in the protection group
    document. After removal, the server will use group defaults. Applies
    the group defaults to DRS/EC2 and records an audit trail entry.

    Args:
        group_id: Protection group ID
        server_id: Source server ID

    Returns:
        Response with confirmation and effective config:
        {
            "sourceServerId": "s-xxx",
            "message": "Server configuration deleted, reverted to group "
                       "defaults",
            "effectiveConfig": {
                "subnetId": "subnet-xxx",
                "securityGroupIds": ["sg-xxx"],
                "instanceType": "t3.medium"
            },
            "auditTrail": {
                "timestamp": "2026-01-27T23:00:00Z",
                "user": "admin@example.com",
                "action": "deleted_server_config"
            }
        }

    Requirements: 6.5
    """
    try:
        # Get protection group
        result = get_protection_groups_table().get_item(Key={"groupId": group_id})

        if "Item" not in result:
            return response(
                404,
                error_response(
                    ERROR_NOT_FOUND,
                    "Protection Group not found",
                    details={"Protection Group": group_id},
                ),
            )

        protection_group = result["Item"]
        region = protection_group.get("region")

        # Verify server exists in protection group
        source_server_ids = protection_group.get("sourceServerIds", [])
        if server_id not in source_server_ids:
            return response(
                404,
                {
                    "error": "Server not found in protection group",
                    "serverId": server_id,
                    "groupId": group_id,
                },
            )

        # Remove server from servers array
        servers = protection_group.get("servers", [])
        original_count = len(servers)
        servers = [s for s in servers if s.get("sourceServerId") != server_id]

        # Check if server had custom config
        had_custom_config = len(servers) < original_count

        # Update protection group in DynamoDB
        from datetime import datetime, timezone

        timestamp = datetime.now(timezone.utc).isoformat()

        get_protection_groups_table().update_item(
            Key={"groupId": group_id},
            UpdateExpression="SET servers = :servers, updatedAt = :updated",
            ExpressionAttributeValues={
                ":servers": servers,
                ":updated": timestamp,
            },
        )

        # Apply group defaults to DRS/EC2
        group_defaults = protection_group.get("launchConfig", {})
        apply_result = apply_launch_config_to_servers(
            server_ids=[server_id],
            launch_config=group_defaults,
            region=region,
            protection_group={
                **protection_group,
                "servers": servers,
            },
            protection_group_id=group_id,
            protection_group_name=protection_group.get("groupName"),
        )

        # Build audit trail entry
        audit_entry = {
            "timestamp": timestamp,
            "user": protection_group.get("owner", "unknown"),
            "action": "deleted_server_config",
            "applyResult": apply_result,
        }

        # Build response with camelCase fields for frontend
        response_data = {
            "sourceServerId": server_id,
            "message": "Server configuration deleted, reverted to group " "defaults",
            "effectiveConfig": group_defaults,
            "auditTrail": audit_entry,
        }

        # Add note if server had no custom config
        if not had_custom_config:
            response_data["message"] = "Server had no custom configuration, " "already using group defaults"

        return response(200, response_data)

    except ClientError as e:
        print(f"DynamoDB error deleting server launch config: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_DYNAMODB_ERROR,
                "DynamoDB operation failed",
                details={"operation": "update", "error": str(e)},
            ),
        )
    except Exception as e:
        print(f"Error deleting server launch config: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def validate_server_static_ip(group_id: str, server_id: str, body: Dict) -> Dict:
    """
    Validate static private IP address for a server.

    Performs comprehensive validation:
    - IPv4 format validation
    - IP within subnet CIDR range
    - IP not in reserved range (first 4, last 1 addresses)
    - IP availability check via AWS API

    Args:
        group_id: Protection group ID
        server_id: Source server ID
        body: Request body with staticPrivateIp and subnetId

    Request Body:
        {
            "staticPrivateIp": "10.0.1.100",
            "subnetId": "subnet-xxx"
        }

    Returns:
        Response with validation result:

        Valid IP:
        {
            "valid": true,
            "ip": "10.0.1.100",
            "subnetId": "subnet-xxx",
            "details": {
                "inCidrRange": true,
                "notReserved": true,
                "available": true,
                "subnetCidr": "10.0.1.0/24"
            }
        }

        Invalid IP:
        {
            "valid": false,
            "error": "IP_IN_USE",
            "message": "IP address 10.0.1.100 is already in use by
                       network interface eni-xxx",
            "ip": "10.0.1.100",
            "subnetId": "subnet-xxx"
        }

    Requirements: 3.1, 3.2, 4.1.5, 9.1
    """
    try:
        # Import validation function
        from shared.launch_config_validation import validate_static_ip

        # Get protection group
        result = get_protection_groups_table().get_item(Key={"groupId": group_id})

        if "Item" not in result:
            return response(
                404,
                error_response(
                    ERROR_NOT_FOUND,
                    "Protection Group not found",
                    details={"Protection Group": group_id},
                ),
            )

        protection_group = result["Item"]
        region = protection_group.get("region")

        # Verify server exists in protection group
        source_server_ids = protection_group.get("sourceServerIds", [])
        if server_id not in source_server_ids:
            return response(
                404,
                {
                    "error": "Server not found in protection group",
                    "serverId": server_id,
                    "groupId": group_id,
                },
            )

        # Parse request body (camelCase from frontend)
        static_ip = body.get("staticPrivateIp")
        subnet_id = body.get("subnetId")

        # Validate required fields
        if not static_ip:
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "staticPrivateIp is required",
                    "field": "staticPrivateIp",
                },
            )

        if not subnet_id:
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "subnetId is required",
                    "field": "subnetId",
                },
            )

        # Perform validation
        validation_result = validate_static_ip(static_ip, subnet_id, region)

        # If validation passed, build success response with details
        if validation_result.get("valid"):
            # Get subnet CIDR from validation (if available)
            subnet_cidr = validation_result.get("subnetCidr")

            response_data = {
                "valid": True,
                "ip": static_ip,
                "subnetId": subnet_id,
                "details": {
                    "inCidrRange": True,
                    "notReserved": True,
                    "available": True,
                },
            }

            # Add subnet CIDR if available
            if subnet_cidr:
                response_data["details"]["subnetCidr"] = subnet_cidr

            return response(200, response_data)

        # Validation failed - return error details
        validation_error = {
            "valid": False,
            "ip": static_ip,
            "subnetId": subnet_id,
        }

        # Add error details from validation result
        if validation_result.get("error"):
            validation_error["error"] = validation_result["error"]

        if validation_result.get("message"):
            validation_error["message"] = validation_result["message"]

        if validation_result.get("conflictingResource"):
            validation_error["conflictingResource"] = validation_result["conflictingResource"]

        # Return 400 for validation errors
        return response(400, validation_error)

    except Exception as e:
        print(f"Error validating static IP: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def bulk_update_server_launch_config(group_id: str, body: Dict) -> Dict:
    """
    Bulk update launch configurations for multiple servers.

    Validates all configurations before applying any changes (fail fast).
    Applies configurations sequentially with error handling. Returns
    detailed summary of applied and failed servers.

    Args:
        group_id: Protection group ID
        body: Request body with servers array

    Request Body:
        {
            "servers": [
                {
                    "sourceServerId": "s-xxx",
                    "useGroupDefaults": false,
                    "launchTemplate": {
                        "staticPrivateIp": "10.0.1.100",
                        "instanceType": "c6a.xlarge"
                    }
                },
                {
                    "sourceServerId": "s-yyy",
                    "useGroupDefaults": false,
                    "launchTemplate": {
                        "staticPrivateIp": "10.0.1.101"
                    }
                }
            ]
        }

    Returns:
        Response with summary and detailed results:
        {
            "summary": {
                "total": 2,
                "applied": 1,
                "failed": 1
            },
            "results": [
                {
                    "sourceServerId": "s-xxx",
                    "status": "applied",
                    "effectiveConfig": {...}
                },
                {
                    "sourceServerId": "s-yyy",
                    "status": "failed",
                    "error": "IP_IN_USE",
                    "message": "IP address 10.0.1.101 is already in use"
                }
            ]
        }

    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
    """
    try:
        # Import validation functions
        from shared.launch_config_validation import (
            validate_static_ip,
            validate_aws_approved_fields,
            validate_security_groups,
            validate_instance_type,
            validate_iam_profile,
            validate_subnet,
        )

        # Get protection group
        result = get_protection_groups_table().get_item(Key={"groupId": group_id})

        if "Item" not in result:
            return response(
                404,
                error_response(
                    ERROR_NOT_FOUND,
                    "Protection Group not found",
                    details={"Protection Group": group_id},
                ),
            )

        protection_group = result["Item"]
        region = protection_group.get("region")
        source_server_ids = protection_group.get("sourceServerIds", [])

        # Parse request body
        servers_config = body.get("servers", [])

        if not servers_config:
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "servers array is required",
                    "field": "servers",
                },
            )

        if not isinstance(servers_config, list):
            return response(
                400,
                {
                    "error": "INVALID_TYPE",
                    "message": "servers must be an array",
                    "field": "servers",
                },
            )

        # Phase 1: Validate ALL configurations before applying any
        validation_errors = []

        # First, check for duplicate IPs within the batch itself
        ip_to_server_map = {}  # Maps (subnet_id, ip) -> server_id
        for idx, server_config in enumerate(servers_config):
            server_id = server_config.get("sourceServerId")
            launch_template = server_config.get("launchTemplate", {})
            static_ip = launch_template.get("staticPrivateIp")

            if static_ip:
                # Get subnet ID (from launch template or group defaults)
                subnet_id = launch_template.get("subnetId") or protection_group.get("launchConfig", {}).get("subnetId")

                if subnet_id:
                    key = (subnet_id, static_ip)
                    if key in ip_to_server_map:
                        # Duplicate IP within batch
                        validation_errors.append(
                            {
                                "index": idx,
                                "sourceServerId": server_id,
                                "error": "DUPLICATE_IP_IN_BATCH",
                                "message": f"IP {static_ip} is assigned to "
                                f"multiple servers in this batch: "
                                f"{ip_to_server_map[key]} and {server_id}",
                                "field": "staticPrivateIp",
                                "conflictingServer": {
                                    "sourceServerId": ip_to_server_map[key],
                                    "staticPrivateIp": static_ip,
                                    "subnetId": subnet_id,
                                },
                            }
                        )
                    else:
                        ip_to_server_map[key] = server_id

        # Continue with per-server validation
        for idx, server_config in enumerate(servers_config):
            server_id = server_config.get("sourceServerId")
            launch_template = server_config.get("launchTemplate", {})

            # Validate server ID present
            if not server_id:
                validation_errors.append(
                    {
                        "index": idx,
                        "error": "MISSING_SERVER_ID",
                        "message": "sourceServerId is required for each " "server",
                    }
                )
                continue

            # Validate server exists in protection group
            if server_id not in source_server_ids:
                validation_errors.append(
                    {
                        "index": idx,
                        "sourceServerId": server_id,
                        "error": "SERVER_NOT_FOUND",
                        "message": f"Server {server_id} not found in " "protection group",
                    }
                )
                continue

            # Validate AWS-approved fields only
            field_validation = validate_aws_approved_fields(launch_template)
            if not field_validation.get("valid"):
                validation_errors.append(
                    {
                        "index": idx,
                        "sourceServerId": server_id,
                        **field_validation,
                    }
                )
                continue

            # Validate static private IP
            if launch_template.get("staticPrivateIp"):
                static_ip = launch_template["staticPrivateIp"]
                subnet_id = launch_template.get("subnetId") or protection_group.get("launchConfig", {}).get("subnetId")

                if not subnet_id:
                    validation_errors.append(
                        {
                            "index": idx,
                            "sourceServerId": server_id,
                            "field": "subnetId",
                            "error": "MISSING_SUBNET",
                            "message": "subnetId is required when setting " "staticPrivateIp",
                        }
                    )
                    continue

                ip_validation = validate_static_ip(static_ip, subnet_id, region)
                if not ip_validation.get("valid"):
                    validation_errors.append(
                        {
                            "index": idx,
                            "sourceServerId": server_id,
                            **ip_validation,
                        }
                    )
                    continue

                # Check for duplicate IPs across servers in same subnet
                from shared.launch_config_validation import (
                    validate_no_duplicate_ips,
                )

                duplicate_check = validate_no_duplicate_ips(protection_group, server_id, static_ip, subnet_id)
                if not duplicate_check.get("valid"):
                    validation_errors.append(
                        {
                            "index": idx,
                            "sourceServerId": server_id,
                            **duplicate_check,
                        }
                    )
                    continue

            # Validate security groups
            if launch_template.get("securityGroupIds"):
                sg_ids = launch_template["securityGroupIds"]
                subnet_id = launch_template.get("subnetId") or protection_group.get("launchConfig", {}).get("subnetId")

                if subnet_id:
                    subnet_validation = validate_subnet(subnet_id, region)
                    if subnet_validation.get("valid"):
                        vpc_id = subnet_validation["details"]["vpcId"]
                        sg_validation = validate_security_groups(sg_ids, vpc_id, region)
                        if not sg_validation.get("valid"):
                            validation_errors.append(
                                {
                                    "index": idx,
                                    "sourceServerId": server_id,
                                    **sg_validation,
                                }
                            )
                            continue

            # Validate instance type
            if launch_template.get("instanceType"):
                instance_type = launch_template["instanceType"]
                type_validation = validate_instance_type(instance_type, region)
                if not type_validation.get("valid"):
                    validation_errors.append(
                        {
                            "index": idx,
                            "sourceServerId": server_id,
                            **type_validation,
                        }
                    )
                    continue

            # Validate IAM instance profile
            if launch_template.get("instanceProfileName"):
                profile_name = launch_template["instanceProfileName"]
                profile_validation = validate_iam_profile(profile_name, region)
                if not profile_validation.get("valid"):
                    validation_errors.append(
                        {
                            "index": idx,
                            "sourceServerId": server_id,
                            **profile_validation,
                        }
                    )
                    continue

        # If any validation errors, fail fast and return all errors
        if validation_errors:
            return response(
                400,
                {
                    "error": "VALIDATION_FAILED",
                    "message": f"{len(validation_errors)} server " f"configuration(s) failed validation",
                    "validationErrors": validation_errors,
                },
            )

        # Phase 2: Apply configurations with error handling
        results = []
        applied_count = 0
        failed_count = 0

        # Get existing servers array
        servers = protection_group.get("servers", [])

        for server_config in servers_config:
            server_id = server_config.get("sourceServerId")
            use_group_defaults = server_config.get("useGroupDefaults", True)
            launch_template = server_config.get("launchTemplate", {})

            try:
                # Build new server configuration
                new_server_config = {
                    "sourceServerId": server_id,
                    "useGroupDefaults": use_group_defaults,
                    "launchTemplate": launch_template,
                }

                # Add instance metadata if available
                try:
                    regional_drs = boto3.client("drs", region_name=region)
                    drs_response = regional_drs.describe_source_servers(filters={"sourceServerIDs": [server_id]})
                    if drs_response.get("items"):
                        server_info = drs_response["items"][0]
                        source_props = server_info.get("sourceProperties", {})
                        new_server_config["instanceId"] = source_props.get("lastUpdatedDateTime")
                        identification = source_props.get("identificationHints", {})
                        new_server_config["instanceName"] = identification.get("hostname", "")
                        new_server_config["tags"] = server_info.get("tags", {})
                except Exception as e:
                    print(f"Warning: Could not fetch metadata for " f"{server_id}: {e}")

                # Update or add server config in array
                existing_idx = next(
                    (i for i, s in enumerate(servers) if s.get("sourceServerId") == server_id),
                    None,
                )

                if existing_idx is not None:
                    servers[existing_idx] = new_server_config
                else:
                    servers.append(new_server_config)

                # Get effective configuration for response
                updated_protection_group = {
                    **protection_group,
                    "servers": servers,
                }
                effective_config = get_effective_launch_config(updated_protection_group, server_id)

                # Add success result
                results.append(
                    {
                        "sourceServerId": server_id,
                        "status": "applied",
                        "effectiveConfig": effective_config,
                    }
                )
                applied_count += 1

            except Exception as e:
                # Add failure result
                print(f"Error applying config for {server_id}: {str(e)}")
                results.append(
                    {
                        "sourceServerId": server_id,
                        "status": "failed",
                        "error": "APPLICATION_ERROR",
                        "message": str(e),
                    }
                )
                failed_count += 1

        # Phase 3: Update DynamoDB with all changes
        from datetime import datetime, timezone

        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            get_protection_groups_table().update_item(
                Key={"groupId": group_id},
                UpdateExpression="SET servers = :servers, " "updatedAt = :updated",
                ExpressionAttributeValues={
                    ":servers": servers,
                    ":updated": timestamp,
                },
            )
        except Exception as e:
            print(f"Error updating DynamoDB: {str(e)}")
            return response(
                500,
                {
                    "error": "DATABASE_ERROR",
                    "message": f"Failed to save configurations: {str(e)}",
                },
            )

        # Phase 4: Apply configurations to DRS/EC2
        # Get list of successfully configured server IDs
        applied_server_ids = [r["sourceServerId"] for r in results if r.get("status") == "applied"]

        if applied_server_ids:
            try:
                apply_launch_config_to_servers(
                    server_ids=applied_server_ids,
                    launch_config=protection_group.get("launchConfig", {}),
                    region=region,
                    protection_group={
                        **protection_group,
                        "servers": servers,
                    },
                    protection_group_id=group_id,
                    protection_group_name=protection_group.get("groupName"),
                )
            except Exception as e:
                print(f"Warning: Error applying configs to DRS/EC2: {e}")
                # Don't fail the entire operation if DRS/EC2 update fails
                # Configs are saved in DynamoDB and can be retried

        # Build response
        response_data = {
            "summary": {
                "total": len(servers_config),
                "applied": applied_count,
                "failed": failed_count,
            },
            "results": results,
        }

        return response(200, response_data)

    except ClientError as e:
        print(f"DynamoDB error in bulk update: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_DYNAMODB_ERROR,
                "DynamoDB operation failed",
                details={"operation": "update", "error": str(e)},
            ),
        )
    except Exception as e:
        print(f"Error in bulk update: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


# ============================================================================
# Recovery Plans Handlers
# ============================================================================


def create_recovery_plan(event: Dict, body: Dict) -> Dict:
    """
    Create a new Recovery Plan with account context and
    optional notification email.

    Validates wave sizes against DRS limits, ensures all
    Protection Groups belong to the same account, and
    stores plan in DynamoDB. Optionally creates an SNS
    subscription for execution notifications.

    Args:
        event: Lambda event object (for invocation source
            detection)
        body: Request body with Recovery Plan configuration

    Returns:
        API Gateway response dict with statusCode and body
    """
    try:
        # Validate and extract account context (handles both
        # API Gateway and direct invocation modes)
        account_context = validate_account_context_for_invocation(event, body)

        # Validate required fields - accept both frontend
        # (name) and legacy (PlanName) formats
        plan_name = body.get("name") or body.get("planName")
        if not plan_name:
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "name is required",
                    "field": "name",
                },
            )

        waves = body.get("waves")
        if not waves:
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "At least one wave is required",
                    "field": "waves",
                },
            )

        # Validate name is not empty or whitespace-only
        if not plan_name or not plan_name.strip():
            return response(
                400,
                {
                    "error": "INVALID_NAME",
                    "message": ("name cannot be empty or " "whitespace-only"),
                    "field": "name",
                },
            )

        # Validate name length (1-64 characters)
        if len(plan_name.strip()) > 64:
            return response(
                400,
                {
                    "error": "INVALID_NAME",
                    "message": ("name must be 64 characters or fewer"),
                    "field": "name",
                    "maxLength": 64,
                    "actualLength": len(plan_name.strip()),
                },
            )

        # Use trimmed name
        plan_name = plan_name.strip()

        # Validate notification email format if provided
        notification_email = body.get("notificationEmail")
        if notification_email:
            notification_email = notification_email.strip()
            if not validate_email(notification_email):
                return response(
                    400,
                    {
                        "error": "INVALID_EMAIL",
                        "message": (f"Invalid email format: " f"{notification_email}"),
                        "field": "notificationEmail",
                    },
                )

        # Validate unique name (case-insensitive)
        if not validate_unique_rp_name(plan_name):
            return response(
                409,
                {
                    "error": "RP_NAME_EXISTS",
                    "message": (f"A Recovery Plan named " f'"{plan_name}" already exists'),
                    "existingName": plan_name,
                },
            )

        # Generate UUID for PlanId
        plan_id = str(uuid.uuid4())

        # Create Recovery Plan item with account context
        timestamp = int(time.time())
        item = {
            "planId": plan_id,
            "planName": plan_name,
            "description": body.get("description", ""),
            "accountId": account_context["accountId"],
            "assumeRoleName": account_context.get("assumeRoleName", ""),
            "notificationEmail": notification_email or "",
            "snsSubscriptionArn": "",
            "waves": waves,
            "createdDate": timestamp,
            "lastModifiedDate": timestamp,
            "version": 1,
        }

        # Validate waves if provided
        if waves:
            # CamelCase migration - store waves in exact format frontend expects
            # KEEP IT SIMPLE: Same field names in database, API, and frontend
            camelcase_waves = []
            for idx, wave in enumerate(waves):
                camelcase_wave = {
                    "waveNumber": idx,
                    "waveName": wave.get("waveName", wave.get("name", f"Wave {idx + 1}")),
                    "waveDescription": wave.get("waveDescription", wave.get("description", "")),
                    "protectionGroupId": wave.get("protectionGroupId", ""),
                    "serverIds": wave.get("serverIds", []),
                    "pauseBeforeWave": wave.get("pauseBeforeWave", False),
                    "dependsOnWaves": wave.get("dependsOnWaves", []),
                }
                # Only include protectionGroupIds if provided and non-empty
                if wave.get("protectionGroupIds"):
                    camelcase_wave["protectionGroupIds"] = wave.get("protectionGroupIds")
                camelcase_waves.append(camelcase_wave)

            # Store in camelCase format
            item["waves"] = camelcase_waves

            # Validate all Protection Groups belong to the
            # same account as this Recovery Plan
            plan_account_id = account_context["accountId"]
            for wave in camelcase_waves:
                pg_id = wave.get("protectionGroupId") or (wave.get("protectionGroupIds", []) or [None])[0]
                if pg_id:
                    try:
                        pg_result = get_protection_groups_table().get_item(Key={"groupId": pg_id})
                        pg = pg_result.get("Item")
                        if not pg:
                            return response(
                                400,
                                {
                                    "error": "PG_NOT_FOUND",
                                    "message": (f"Protection Group " f"{pg_id} not found"),
                                    "field": "waves",
                                },
                            )
                        pg_account = pg.get("accountId", "")
                        if pg_account and pg_account != plan_account_id:
                            return response(
                                400,
                                {
                                    "error": ("ACCOUNT_MISMATCH"),
                                    "message": (
                                        f"Protection Group "
                                        f"{pg_id} belongs to "
                                        f"account "
                                        f"{pg_account}, but "
                                        f"Recovery Plan is "
                                        f"for account "
                                        f"{plan_account_id}"
                                    ),
                                    "field": "waves",
                                },
                            )
                    except ClientError as e:
                        print(f"Warning: Could not validate " f"PG {pg_id} account: {e}")

            validation_error = validate_waves(camelcase_waves)
            if validation_error:
                return response(
                    400,
                    error_response(
                        ERROR_INVALID_PARAMETER,
                        validation_error,
                        details={"parameter": "waves"},
                    ),
                )

            # QUOTA VALIDATION: Check total servers across all waves doesn't
            # exceed 500
            from shared.conflict_detection import (
                resolve_pg_servers_for_conflict_check,
            )

            pg_cache = {}
            total_servers = 0
            wave_server_counts = []

            for wave in camelcase_waves:
                wave_name = wave.get("waveName", f"Wave {wave.get('waveNumber', '?')}")
                pg_id = wave.get("protectionGroupId") or (wave.get("protectionGroupIds", []) or [None])[0]

                if pg_id:
                    try:
                        server_ids = resolve_pg_servers_for_conflict_check(pg_id, pg_cache)
                        wave_count = len(server_ids)
                        total_servers += wave_count
                        wave_server_counts.append({"waveName": wave_name, "serverCount": wave_count})
                    except Exception as e:
                        print(f"Warning: Could not count servers for wave '{wave_name}': {e}")

            # Check 500 total servers limit
            if total_servers > 500:
                return response(
                    400,
                    {
                        "error": "QUOTA_EXCEEDED",
                        "quotaType": "total_servers_in_jobs",
                        "message": f"Recovery Plan would launch {total_servers} servers (max 500 across all jobs)",
                        "totalServers": total_servers,
                        "maxServers": 500,
                        "waveBreakdown": wave_server_counts,
                        "limit": "DRS Service Quota: Max 500 servers across all concurrent jobs (not adjustable)",
                        "documentation": "https://docs.aws.amazon.com/general/latest/gr/drs.html",
                        "recommendation": "Split this Recovery Plan into multiple plans or reduce the number of servers per wave",  # noqa: E501
                    },
                )

            # OPTIONAL WARNING: Check concurrent jobs limit and server conflicts
            # Get region from first wave's Protection Group
            first_wave = camelcase_waves[0] if camelcase_waves else {}
            pg_id = first_wave.get("protectionGroupId") or (first_wave.get("protectionGroupIds", []) or [None])[0]

            warnings = []

            if pg_id:
                try:
                    pg_result = get_protection_groups_table().get_item(Key={"groupId": pg_id})
                    pg = pg_result.get("Item", {})
                    region = pg.get("region", "us-east-1")

                    # Check concurrent jobs limit
                    from shared.conflict_detection import (
                        check_concurrent_jobs_limit,
                    )

                    jobs_check = check_concurrent_jobs_limit(region)
                    if not jobs_check["canStartJob"]:
                        warnings.append(
                            {
                                "type": "CONCURRENT_JOBS_AT_LIMIT",
                                "severity": "warning",
                                "message": f"Region {region} currently has {jobs_check['currentJobs']}/20 concurrent jobs active",
                                "recommendation": "Wait for active jobs to complete before executing this plan",
                                "currentJobs": jobs_check["currentJobs"],
                                "maxJobs": jobs_check["maxJobs"],
                                "canExecuteNow": False,
                            }
                        )

                    # Check for server conflicts
                    from shared.conflict_detection import (
                        check_server_conflicts,
                    )

                    conflict_check_plan = {
                        "planId": plan_id,
                        "planName": plan_name,
                        "waves": camelcase_waves,
                    }

                    conflicts = check_server_conflicts(conflict_check_plan)
                    if conflicts:
                        conflict_summary = {
                            "execution_conflicts": len(
                                [c for c in conflicts if c.get("conflictSource") == "execution"]
                            ),
                            "drs_job_conflicts": len([c for c in conflicts if c.get("conflictSource") == "drs_job"]),
                            "quota_violations": len(
                                [c for c in conflicts if c.get("conflictSource") == "quota_violation"]
                            ),
                        }

                        warnings.append(
                            {
                                "type": "SERVER_CONFLICTS_DETECTED",
                                "severity": "warning",
                                "message": "Some servers are currently in use by other operations",
                                "recommendation": "Wait for active operations to complete before executing this plan",
                                "conflicts": conflict_summary,
                                "canExecuteNow": False,
                            }
                        )

                except Exception as e:
                    print(f"Warning: Could not check concurrent jobs/conflicts: {e}")

            # Add warnings to response if any
            if warnings:
                item["warnings"] = warnings

        # Store in DynamoDB
        get_recovery_plans_table().put_item(Item=item)

        print(f"Created Recovery Plan: {plan_id}")

        # Create SNS subscription if notification email provided
        if notification_email:
            try:
                subscription_arn = manage_recovery_plan_subscription(
                    plan_id=plan_id,
                    email=notification_email,
                    action="create",
                )
                if subscription_arn:
                    # Update item with subscription ARN
                    get_recovery_plans_table().update_item(
                        Key={"planId": plan_id},
                        UpdateExpression=("SET snsSubscriptionArn = :arn"),
                        ExpressionAttributeValues={":arn": subscription_arn},
                    )
                    item["snsSubscriptionArn"] = subscription_arn
                    print(f"Created SNS subscription for " f"plan {plan_id}: " f"{subscription_arn}")
            except Exception as sub_err:
                # Don't fail plan creation if subscription
                # creation fails
                print(f"Warning: Failed to create SNS " f"subscription for plan {plan_id}: " f"{sub_err}")

        # Data is already in camelCase - return directly
        return response(201, item)

    except InputValidationError as e:
        print(f"Validation error creating Recovery Plan: {e}")
        return response(
            400,
            error_response(
                ERROR_INVALID_PARAMETER,
                str(e),
            ),
        )
    except Exception as e:
        print(f"Error creating Recovery Plan: {str(e)}")
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def get_recovery_plans(query_params: Dict = None) -> Dict:
    """List all Recovery Plans with latest execution history and conflict info

    Query Parameters:
        accountId: Filter by target account ID
        name: Filter by plan name (case-insensitive partial match)
        nameExact: Filter by exact plan name (case-insensitive)
        tag: Filter by tag key=value (plans with protection groups having this tag)
        hasConflict: Filter by conflict status (true/false)
        status: Filter by last execution status
    """
    try:
        query_params = query_params or {}

        result = get_recovery_plans_table().scan()
        plans = result.get("Items", [])

        # Apply filters
        account_id = query_params.get("accountId")
        name_filter = query_params.get("name", "").lower()
        name_exact_filter = query_params.get("nameExact", "").lower()
        tag_filter = query_params.get("tag", "")  # Format: key=value
        has_conflict_filter = query_params.get("hasConflict")
        status_filter = query_params.get("status", "").lower()

        # Parse tag filter
        tag_key, tag_value = None, None
        if tag_filter and "=" in tag_filter:
            tag_key, tag_value = tag_filter.split("=", 1)

        # Build protection group tag lookup if tag filter is specified
        pg_tags_map = {}
        if tag_key:
            try:
                pg_result = get_protection_groups_table().scan()
                for pg in pg_result.get("Items", []):
                    pg_id = pg.get("groupId")
                    pg_tags = pg.get("serverSelectionTags", {})
                    pg_tags_map[pg_id] = pg_tags
            except Exception as e:
                print(f"Error loading PG tags for filter: {e}")

        # Get conflict info for all plans (for graying out Drill/Recovery
        # buttons)
        plans_with_conflicts = get_plans_with_conflicts()

        # Get shared Protection Group warnings (informational, not blocking)
        shared_pgs = get_shared_protection_groups()

        # Enrich each plan with latest execution data and conflict info
        for plan in plans:
            plan_id = plan.get("planId")

            # Add conflict info if this plan has conflicts with other active
            # executions
            if plan_id in plans_with_conflicts:
                conflict_info = plans_with_conflicts[plan_id]
                plan["hasServerConflict"] = True
                plan["conflictInfo"] = conflict_info
            else:
                plan["hasServerConflict"] = False
                plan["conflictInfo"] = None

            # Add shared PG warnings (informational)
            plan_shared_warnings = []
            for pg_id, pg_info in shared_pgs.items():
                if any(p["planId"] == plan_id for p in pg_info["usedByPlans"]):
                    other_plans = [p for p in pg_info["usedByPlans"] if p["planId"] != plan_id]
                    if other_plans:
                        plan_shared_warnings.append(
                            {
                                "protectionGroupId": pg_id,
                                "protectionGroupName": pg_info["protectionGroupName"],
                                "sharedWithPlans": other_plans,
                            }
                        )
            plan["sharedProtectionGroups"] = plan_shared_warnings if plan_shared_warnings else None

            # Query ExecutionHistoryTable for latest execution
            # Note: planIdIndex has no sort key, so we query all and sort by startTime
            try:
                execution_result = get_executions_table().query(
                    IndexName="planIdIndex",
                    KeyConditionExpression=Key("planId").eq(plan_id),
                )

                if execution_result.get("Items"):
                    # Sort by startTime descending to get the latest execution
                    executions = sorted(
                        execution_result["Items"],
                        key=lambda x: int(x.get("startTime", 0)),
                        reverse=True,
                    )
                    latest_execution = executions[0]
                    plan["lastExecutionStatus"] = latest_execution.get("status")
                    plan["lastStartTime"] = latest_execution.get("startTime")
                    plan["lastEndTime"] = latest_execution.get("endTime")
                else:
                    # No executions found for this plan
                    plan["lastExecutionStatus"] = None
                    plan["lastStartTime"] = None
                    plan["lastEndTime"] = None

            except Exception as e:
                print(f"Error querying execution history for plan {plan_id}: {str(e)}")
                # Set null values on error
                plan["lastExecutionStatus"] = None
                plan["lastStartTime"] = None
                plan["lastEndTime"] = None

            # Add wave count before transformation
            plan["waveCount"] = len(plan.get("waves", []))

        # Apply filters to plans
        filtered_plans = []
        for plan in plans:
            # Account filter - derive account from protection groups in waves
            if account_id:
                # Recovery plans don't store accountId directly - they derive it
                # from their protection groups. Check if ANY wave's protection
                # group matches the requested account.
                plan_matches_account = False
                waves = plan.get("waves", [])

                for wave in waves:
                    pg_id = wave.get("protectionGroupId")
                    if pg_id:
                        try:
                            pg_result = get_protection_groups_table().get_item(Key={"groupId": pg_id})
                            if "Item" in pg_result:
                                pg = pg_result["Item"]
                                pg_account = pg.get("accountId")
                                if pg_account == account_id:
                                    plan_matches_account = True
                                    break
                        except Exception as e:
                            print(f"Error checking PG {pg_id} account: {e}")
                            continue

                # Skip plan if no waves match the requested account
                if not plan_matches_account:
                    continue

            # Name filter (partial match, case-insensitive)
            if name_filter:
                plan_name = plan.get("planName", "").lower()
                if name_filter not in plan_name:
                    continue

            # Exact name filter (case-insensitive)
            if name_exact_filter:
                plan_name = plan.get("planName", "").lower()
                if name_exact_filter != plan_name:
                    continue

            # Conflict filter
            if has_conflict_filter is not None:
                has_conflict = plan.get("hasServerConflict", False)
                if has_conflict_filter.lower() == "true" and not has_conflict:
                    continue
                if has_conflict_filter.lower() == "false" and has_conflict:
                    continue

            # Status filter (last execution status)
            if status_filter:
                last_status = (plan.get("lastExecutionStatus") or "").lower()
                if status_filter != last_status:
                    continue

            # Tag filter - check if any protection group in plan has matching
            # tag
            if tag_key:
                plan_waves = plan.get("waves", [])
                has_matching_tag = False
                for wave in plan_waves:
                    pg_id = wave.get("protectionGroupId")
                    if pg_id and pg_id in pg_tags_map:
                        pg_tags = pg_tags_map[pg_id]
                        if tag_key in pg_tags and pg_tags[tag_key] == tag_value:
                            has_matching_tag = True
                            break
                if not has_matching_tag:
                    continue

            filtered_plans.append(plan)

        # Return raw database fields - database is already camelCase
        return response(
            200,
            {"recoveryPlans": filtered_plans, "count": len(filtered_plans)},
        )

    except Exception as e:
        print(f"Error listing Recovery Plans: {str(e)}")
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def get_recovery_plan(plan_id: str) -> Dict:
    """Get a single Recovery Plan by ID"""
    try:
        result = get_recovery_plans_table().get_item(Key={"planId": plan_id})

        if "Item" not in result:
            return response(
                404,
                error_response(
                    ERROR_NOT_FOUND,
                    "Recovery Plan not found",
                    details={"Recovery Plan": plan_id},
                ),
            )

        plan = result["Item"]
        plan["waveCount"] = len(plan.get("waves", []))

        # Return raw database fields - database is already camelCase
        return response(200, plan)

    except Exception as e:
        print(f"Error getting Recovery Plan: {str(e)}")
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def check_existing_recovery_instances(plan_id: str) -> Dict:
    """Check if servers in this plan have existing recovery instances.

    Returns info about any recovery instances that haven't been terminated yet.
    Used by frontend to prompt user before starting a new drill.
    """
    print(f"XDEBUG: check_existing_recovery_instances called for plan {plan_id}")
    try:
        # Get the recovery plan
        plan_result = get_recovery_plans_table().get_item(Key={"planId": plan_id})
        print(f"XDEBUG: Retrieved plan, has Item: {'Item' in plan_result}")
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
        account_context = None  # Track account context for cross-account DRS queries

        for wave in plan.get("waves", []):
            pg_id = wave.get("protectionGroupId")
            print(f"DEBUG: Processing wave with PG ID: {pg_id}")
            if not pg_id:
                print("DEBUG: No PG ID in wave, skipping")
                continue

            pg_result = get_protection_groups_table().get_item(Key={"groupId": pg_id})
            pg = pg_result.get("Item", {})
            print(f"DEBUG: Retrieved PG: {pg_id}, has Item: {'Item' in pg_result}")
            if not pg:
                print(f"DEBUG: No PG data for {pg_id}, skipping")
                continue

            # Get region from protection group
            pg_region = pg.get("region", "us-east-1")
            if pg_region:
                region = pg_region
            print(f"DEBUG: PG {pg_id} region: {pg_region}")

            # Extract account context from Protection Group (for cross-account)
            pg_account_id = pg.get("accountId")
            print(f"DEBUG: PG {pg_id} - accountId from PG: {pg_account_id}, current account_context: {account_context}")
            if pg.get("accountId") and not account_context:
                from shared.cross_account import get_current_account_id

                current_account_id = get_current_account_id()
                pg_account_id = pg.get("accountId")

                print(
                    f"DEBUG: Checking account context - PG account: {pg_account_id}, Current account: {current_account_id}"
                )

                if pg_account_id != current_account_id:
                    # Look up target account configuration to get externalId
                    assume_role_name = pg.get("assumeRoleName", "DRSOrchestrationRole")
                    external_id = None

                    try:
                        account_result = get_target_accounts_table().get_item(Key={"accountId": pg_account_id})
                        if "Item" in account_result:
                            account_config = account_result["Item"]
                            external_id = account_config.get("externalId")
                            # Use role name from target account config if available
                            if account_config.get("assumeRoleName"):
                                assume_role_name = account_config["assumeRoleName"]
                            print(f"DEBUG: Retrieved externalId from target accounts table: {external_id}")
                    except Exception as e:
                        print(f"DEBUG: Error looking up target account config: {e}")

                    account_context = {
                        "accountId": pg_account_id,
                        "assumeRoleName": assume_role_name,
                        "externalId": external_id,
                        "isCurrentAccount": False,
                    }
                    print(f"Using cross-account context: {account_context}")
                else:
                    print(f"Protection group is in current account {current_account_id}, no cross-account needed")

            # Check for explicit server IDs first
            explicit_servers = pg.get("sourceServerIds", [])
            if explicit_servers:
                print(f"PG {pg_id} has explicit servers: {explicit_servers}")
                for server_id in explicit_servers:
                    all_server_ids.add(server_id)
            else:
                # Resolve servers from tags
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
                    except Exception as e:
                        print(f"Error resolving tags for PG {pg_id}: {e}")

        print(f"Total servers to check for recovery instances: " f"{len(all_server_ids)}: {all_server_ids}")

        if not all_server_ids:
            return response(
                200,
                {
                    "hasExistingInstances": False,
                    "existingInstances": [],
                    "instanceCount": 0,
                    "planId": plan_id,
                },
            )

        # Query DRS for recovery instances (with cross-account support)
        drs_client = create_drs_client(region, account_context)

        existing_instances = []
        try:
            # Get all recovery instances in the region
            paginator = drs_client.get_paginator("describe_recovery_instances")
            for page in paginator.paginate():
                for ri in page.get("items", []):
                    source_server_id = ri.get("sourceServerID")
                    ec2_state = ri.get("ec2InstanceState")
                    print(
                        f"Recovery instance: source={source_server_id}, "
                        f"state={ec2_state}, in_list={source_server_id in all_server_ids}"
                    )
                    if source_server_id in all_server_ids:
                        ec2_instance_id = ri.get("ec2InstanceID")
                        recovery_instance_id = ri.get("recoveryInstanceID")

                        # Find which execution created this instance
                        source_execution = None
                        source_plan_name = None

                        # Search execution history for this recovery instance
                        try:
                            exec_scan = get_executions_table().scan(
                                FilterExpression="attribute_exists(waves)",
                                Limit=100,
                            )

                            exec_items = sorted(
                                exec_scan.get("Items", []),
                                key=lambda x: x.get("startTime", 0),
                                reverse=True,
                            )

                            for exec_item in exec_items:
                                exec_waves = exec_item.get("waves", [])
                                found = False
                                for wave_data in exec_waves:
                                    for server in wave_data.get("serverStatuses", []):
                                        if server.get("sourceServerId") == source_server_id:
                                            source_execution = exec_item.get("executionId")
                                            exec_plan_id = exec_item.get("planId")
                                            if exec_plan_id:
                                                plan_lookup = get_recovery_plans_table().get_item(
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

        # Enrich with source server names from DRS
        if existing_instances:
            try:
                source_ids = [inst["sourceServerId"] for inst in existing_instances]
                # Query DRS for source server details
                servers_response = drs_client.describe_source_servers(filters={"sourceServerIDs": source_ids})
                server_names = {}
                for server in servers_response.get("items", []):
                    server_id = server.get("sourceServerID")
                    # Get Name tag from DRS tags
                    tags = server.get("tags", {})
                    name_tag = tags.get("Name") or tags.get("name")
                    # Fallback to hostname if no Name tag
                    if not name_tag:
                        source_props = server.get("sourceProperties", {})
                        name_tag = source_props.get("identificationHints", {}).get("hostname")
                    server_names[server_id] = name_tag
                # Add source server name to each instance
                for inst in existing_instances:
                    source_id = inst.get("sourceServerId")
                    if source_id in server_names:
                        inst["sourceServerName"] = server_names[source_id]
            except Exception as e:
                print(f"Error fetching source server names: {e}")

        # Enrich with EC2 instance details (Name tag, IP, launch time)
        if existing_instances:
            try:
                ec2_client = create_ec2_client(region, account_context)
                ec2_ids = [inst["ec2InstanceId"] for inst in existing_instances if inst.get("ec2InstanceId")]
                if ec2_ids:
                    ec2_response = ec2_client.describe_instances(InstanceIds=ec2_ids)
                    ec2_details = {}
                    for reservation in ec2_response.get("Reservations", []):
                        for instance in reservation.get("Instances", []):
                            inst_id = instance.get("InstanceId")
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


def update_recovery_plan(plan_id: str, body: Dict) -> Dict:
    """Update an existing Recovery Plan - blocked if execution in progress, with optimistic locking"""
    try:
        # Check if plan exists
        result = get_recovery_plans_table().get_item(Key={"planId": plan_id})
        if "Item" not in result:
            return response(
                404,
                error_response(
                    ERROR_NOT_FOUND,
                    "Recovery Plan not found",
                    details={"Recovery Plan": plan_id},
                ),
            )

        existing_plan = result["Item"]
        current_version = existing_plan.get("version", 1)  # FIXED: camelCase - Default to 1 for legacy items

        # Optimistic locking: Check if client provided expected version
        client_version = body.get("version") or body.get("Version")
        if client_version is not None:
            # Convert to int for comparison (handles Decimal from DynamoDB)
            client_version = int(client_version)
            if client_version != int(current_version):
                return response(
                    409,
                    {
                        "error": "VERSION_CONFLICT",
                        "message": "Resource was modified by another user. Please refresh and try again.",
                        "expectedVersion": client_version,
                        "currentVersion": int(current_version),
                        "resourceId": plan_id,
                    },
                )

        # BLOCK: Cannot update plan with active execution
        active_executions = get_active_executions_for_plan(plan_id)
        if active_executions:
            exec_ids = [e.get("executionId") for e in active_executions]
            return response(
                409,
                {
                    "error": "PLAN_HAS_ACTIVE_EXECUTION",
                    "message": "Cannot modify Recovery Plan while an execution is in progress",
                    "activeExecutions": exec_ids,
                    "planId": plan_id,
                },
            )

        # Validate name if provided - accept both frontend (name) and legacy
        # (PlanName) formats
        plan_name = body.get("name") or body.get("planName")
        if plan_name is not None:
            # Validate name is not empty or whitespace-only
            if not plan_name or not plan_name.strip():
                return response(
                    400,
                    {
                        "error": "INVALID_NAME",
                        "message": "name cannot be empty or whitespace-only",
                        "field": "name",
                    },
                )

            # Validate name length (1-64 characters)
            if len(plan_name.strip()) > 64:
                return response(
                    400,
                    {
                        "error": "INVALID_NAME",
                        "message": "name must be 64 characters or fewer",
                        "field": "name",
                        "maxLength": 64,
                        "actualLength": len(plan_name.strip()),
                    },
                )

            # Trim the name and store in both formats for compatibility
            trimmed_name = plan_name.strip()
            body["planName"] = trimmed_name  # For DynamoDB storage
            if "name" in body:
                body["name"] = trimmed_name  # Update frontend field too

            # Validate unique name if changing
            if trimmed_name != existing_plan.get("planName"):
                if not validate_unique_rp_name(trimmed_name, plan_id):
                    return response(
                        409,
                        {
                            "error": "RP_NAME_EXISTS",
                            "message": f'A Recovery Plan named "{trimmed_name}" already exists',
                            "existingName": trimmed_name,
                        },
                    )

        # Handle notificationEmail changes
        new_email = body.get("notificationEmail")
        old_email = existing_plan.get("notificationEmail", "")
        old_sub_arn = existing_plan.get("snsSubscriptionArn", "")
        email_changed = "notificationEmail" in body and new_email != old_email
        # Also trigger if email exists but subscription is missing
        email_to_subscribe = new_email if new_email else old_email
        needs_subscription = bool(email_to_subscribe and not old_sub_arn)

        print(
            f"[Notification] plan={plan_id} "
            f"new_email={new_email!r} old_email={old_email!r} "
            f"old_sub_arn={old_sub_arn!r} "
            f"email_changed={email_changed} "
            f"needs_subscription={needs_subscription} "
            f"'notificationEmail' in body={'notificationEmail' in body}"
        )

        if email_changed or needs_subscription:
            # Use the right email for subscription
            effective_email = new_email if email_changed else email_to_subscribe
            # Validate new email format if non-empty
            if effective_email and not validate_email(effective_email):
                return response(
                    400,
                    error_response(
                        ERROR_INVALID_PARAMETER,
                        f"Invalid email format: {effective_email}",
                        details={"parameter": "notificationEmail"},
                    ),
                )

            # Delete old subscription if one exists and email changed
            old_sub_arn = existing_plan.get("snsSubscriptionArn", "")
            if email_changed and old_email and old_sub_arn:
                try:
                    manage_recovery_plan_subscription(
                        plan_id=plan_id,
                        email=old_email,
                        action="delete",
                    )
                except Exception as sub_err:
                    print(f"Failed to delete old subscription " f"for plan {plan_id}: {sub_err}")

            # Create subscription for the effective email
            if effective_email:
                try:
                    new_sub_arn = manage_recovery_plan_subscription(
                        plan_id=plan_id,
                        email=effective_email,
                        action="create",
                    )
                    body["snsSubscriptionArn"] = new_sub_arn or ""
                except Exception as sub_err:
                    print(f"Failed to create subscription " f"for plan {plan_id}: {sub_err}")
                    body["snsSubscriptionArn"] = ""
            else:
                # Email removed — clear subscription ARN
                body["snsSubscriptionArn"] = ""

        # NEW: Pre-write validation for Waves - waves field is camelCase
        waves = body.get("waves")
        if waves is not None:
            print(f"Updating plan {plan_id} with {len(waves)} waves")

            # CamelCase migration - store waves in exact format frontend expects
            # KEEP IT SIMPLE: Same field names in database, API, and frontend
            camelcase_waves = []
            for idx, wave in enumerate(waves):
                camelcase_wave = {
                    "waveNumber": idx,
                    "waveName": wave.get("waveName", wave.get("name", f"Wave {idx + 1}")),
                    "waveDescription": wave.get("waveDescription", wave.get("description", "")),
                    "protectionGroupId": wave.get("protectionGroupId", ""),
                    "serverIds": wave.get("serverIds", []),
                    "pauseBeforeWave": wave.get("pauseBeforeWave", False),
                    "dependsOnWaves": wave.get("dependsOnWaves", []),
                }
                # Only include protectionGroupIds if provided and non-empty
                if wave.get("protectionGroupIds"):
                    camelcase_wave["protectionGroupIds"] = wave.get("protectionGroupIds")
                camelcase_waves.append(camelcase_wave)

            # Store in camelCase format
            body["waves"] = camelcase_waves

            # DEFENSIVE: Validate ServerIds in each wave
            for idx, wave in enumerate(camelcase_waves):
                server_ids = wave.get("serverIds", [])
                if not isinstance(server_ids, list):
                    print(f"ERROR: Wave {idx} ServerIds is not a list: {type(server_ids)}")
                    return response(
                        400,
                        {
                            "error": "INVALID_WAVE_DATA",
                            "message": f"Wave {idx} has invalid ServerIds format (must be array)",
                            "waveIndex": idx,
                        },
                    )
                print(f"Wave {idx}: {wave.get('waveName')} - {len(server_ids)} servers")

            validation_error = validate_waves(body["waves"])
            if validation_error:
                return response(
                    400,
                    error_response(
                        ERROR_INVALID_PARAMETER,
                        validation_error,
                        details={"parameter": "waves"},
                    ),
                )

        # Build update expression with version increment (optimistic locking)
        # FIXED: Use camelCase field names consistently
        new_version = int(current_version) + 1
        update_expression = "SET lastModifiedDate = :timestamp, version = :new_version"
        expression_values = {
            ":timestamp": int(time.time()),
            ":new_version": new_version,
            ":current_version": int(current_version),
        }
        expression_names = {}

        updatable_fields = [
            "planName",
            "description",
            "rpo",
            "rto",
            "waves",
            "notificationEmail",
            "snsSubscriptionArn",
        ]
        for field in updatable_fields:
            if field in body:
                if field == "description":
                    # FIXED: Use camelCase 'description' not PascalCase
                    # 'Description'
                    update_expression += ", description = :desc"
                    expression_values[":desc"] = body["description"]
                elif field == "planName":
                    # FIXED: Use camelCase 'planName' not PascalCase 'PlanName'
                    update_expression += ", planName = :planname"
                    expression_values[":planname"] = body["planName"]
                else:
                    update_expression += f", {field} = :{field.lower()}"
                    expression_values[f":{field.lower()}"] = body[field]

        # Update item with conditional write (optimistic locking)
        update_args = {
            "Key": {"planId": plan_id},
            "UpdateExpression": update_expression,
            # FIXED: camelCase
            "ConditionExpression": "version = :current_version OR attribute_not_exists(version)",
            "ExpressionAttributeValues": expression_values,
            "ReturnValues": "ALL_NEW",
        }

        if expression_names:
            update_args["ExpressionAttributeNames"] = expression_names

        try:
            result = get_recovery_plans_table().update_item(**update_args)
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            # Another process updated the item between our read and write
            return response(
                409,
                {
                    "error": "VERSION_CONFLICT",
                    "message": "Resource was modified by another user. Please refresh and try again.",
                    "resourceId": plan_id,
                },
            )

        print(f"Updated Recovery Plan: {plan_id}")
        # Transform to camelCase for frontend consistency
        updated_plan = result["Attributes"]
        updated_plan["waveCount"] = len(updated_plan.get("waves", []))
        # Data is already in camelCase - return directly
        return response(200, updated_plan)

    except Exception as e:
        print(f"Error updating Recovery Plan: {str(e)}")
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def delete_recovery_plan(plan_id: str) -> Dict:
    """Delete a Recovery Plan - blocked if any active execution exists"""
    try:
        # Check for ANY active execution (not just RUNNING)
        active_executions = get_active_executions_for_plan(plan_id)

        if active_executions:
            exec_ids = [e.get("executionId") for e in active_executions]
            statuses = [e.get("status") for e in active_executions]
            print(f"Cannot delete plan {plan_id}: {len(active_executions)} active execution(s)")
            return response(
                409,
                {
                    "error": "PLAN_HAS_ACTIVE_EXECUTION",
                    "message": f"Cannot delete Recovery Plan while {len(active_executions)} execution(s) are in progress",
                    "activeExecutions": exec_ids,
                    "activeStatuses": statuses,
                    "planId": plan_id,
                },
            )

        # No active executions, safe to delete
        # Clean up SNS subscription before deletion
        try:
            plan_result = get_recovery_plans_table().get_item(Key={"planId": plan_id})
            plan_item = plan_result.get("Item", {})
            plan_email = plan_item.get("notificationEmail")
            plan_sub_arn = plan_item.get("snsSubscriptionArn")

            if plan_email and plan_sub_arn:
                try:
                    manage_recovery_plan_subscription(
                        plan_id=plan_id,
                        email=plan_email,
                        action="delete",
                    )
                    print(f"Deleted SNS subscription for" f" plan {plan_id}")
                except Exception as sub_err:
                    print(f"Warning: Failed to delete SNS" f" subscription for plan" f" {plan_id}: {str(sub_err)}")
        except Exception as fetch_err:
            print(f"Warning: Failed to fetch plan for" f" subscription cleanup: {str(fetch_err)}")

        print(f"Deleting Recovery Plan: {plan_id}")
        get_recovery_plans_table().delete_item(Key={"planId": plan_id})

        print(f"Successfully deleted Recovery Plan: {plan_id}")
        return response(
            200,
            {
                "message": "Recovery Plan deleted successfully",
                "planId": plan_id,
            },
        )

    except Exception as e:
        print(f"Error deleting Recovery Plan {plan_id}: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            {
                "error": "DELETE_FAILED",
                "message": f"Failed to delete Recovery Plan: {str(e)}",
                "planId": plan_id,
            },
        )


# ============================================================================
# Tag Sync & Config Functions (Batch 3)
# ============================================================================


def handle_drs_tag_sync(body: Dict = None) -> Dict:
    """
    Sync EC2 instance tags to DRS source servers across all DRS-enabled regions.

    Synchronizes tags from source EC2 instances to their corresponding DRS source servers,
    enabling consistent tagging across disaster recovery infrastructure. Automatically
    enables copyTags in DRS launch configuration to preserve tags during recovery.

    ## Use Cases

    ### 1. Maintain Tag Consistency
    Ensures DR servers have same tags as source servers for:
    - Cost allocation tracking
    - Compliance reporting
    - Resource organization
    - Automated discovery

    ### 2. Enable Tag-Based Protection Groups
    Synced tags allow Protection Groups to use tag-based server selection:
    ```python
    protection_group = {
        "groupName": "Production Web Servers",
        "serverSelectionTags": {
            "Environment": "production",
            "Tier": "web"
        }
    }
    ```

    ### 3. Scheduled Synchronization
    Can be triggered by EventBridge for periodic sync:
    ```json
    {
      "schedule": "rate(1 hour)",
      "target": "data-management-handler",
      "operation": "handle_drs_tag_sync"
    }
    ```

    ## Integration Points

    ### API Gateway Invocation
    ```bash
    curl -X POST https://api.example.com/drs/tag-sync \
      -H "Authorization: Bearer $TOKEN" \
      -d '{"accountId": "123456789012"}'
    ```

    ### Direct Lambda Invocation
    ```python
    lambda_client.invoke(
        FunctionName='data-management-handler',
        Payload=json.dumps({
            "operation": "handle_drs_tag_sync",
            "body": {"accountId": "123456789012"}
        })
    )
    ```

    ### EventBridge Scheduled Trigger
    ```json
    {
      "source": "aws.events",
      "detail-type": "Scheduled Event",
      "detail": {
        "operation": "handle_drs_tag_sync"
      }
    }
    ```

    ## Behavior

    ### Tag Synchronization Process
    1. Query all DRS source servers across all DRS-enabled regions
    2. For each server, retrieve source EC2 instance ID
    3. Query EC2 tags from source instance (in source region)
    4. Filter out AWS-managed tags (aws:*)
    5. Apply tags to DRS source server ARN
    6. Enable copyTags in DRS launch configuration

    ### Region Handling
    - Processes all 15 DRS-enabled regions concurrently
    - Skips regions with no DRS servers (no error)
    - Continues on region failures (logs error, processes remaining regions)
    - Handles cross-region scenarios (EC2 in us-east-1, DRS in us-west-2)

    ### Server Filtering
    - Skips servers without EC2 instance ID
    - Skips DISCONNECTED servers (no active replication)
    - Skips deleted/inaccessible EC2 instances
    - Skips servers with no tags

    ### Error Handling
    - Non-blocking: Region failures don't stop entire sync
    - Graceful degradation: Server failures don't stop region sync
    - Detailed logging: All errors logged with context

    ## Args

    body: Optional request body with:
        - accountId (str): AWS account ID to sync (default: current account)

    ## Returns

    Dict with sync results:
        - accountId: Account ID synced
        - accountName: Account name
        - total_regions: Total DRS regions checked (15)
        - regions_with_servers: Regions containing DRS servers
        - total_servers: Total DRS servers found
        - total_synced: Servers successfully synced
        - total_failed: Servers that failed to sync
        - regions: List of region names with servers

    ## Example Response

    ```json
    {
      "accountId": "123456789012",
      "accountName": "Production Account",
      "total_regions": 15,
      "regions_with_servers": 3,
      "total_servers": 125,
      "total_synced": 123,
      "total_failed": 2,
      "regions": ["us-east-1", "us-west-2", "eu-west-1"]
    }
    ```

    ## Performance

    ### Execution Time
    - Small deployment (< 50 servers): 10-30 seconds
    - Medium deployment (50-200 servers): 30-90 seconds
    - Large deployment (200-500 servers): 90-180 seconds

    ### API Calls
    - DRS DescribeSourceServers: 1 per region (paginated)
    - EC2 DescribeInstances: 1 per server
    - DRS TagResource: 1 per server
    - DRS UpdateLaunchConfiguration: 1 per server

    ### Throttling Considerations
    - DRS API: 10 TPS per region
    - EC2 API: 100 TPS per region
    - Automatic retry with exponential backoff

    ## Limitations

    ### Current Account Only
    Multi-account support planned but not implemented. Returns 400 error if
    accountId differs from current account.

    ### Synchronous Execution
    Runs synchronously - may timeout for very large deployments (500+ servers).
    Consider async execution via Step Functions for large-scale operations.

    ### Tag Limits
    - DRS supports 50 tags per resource
    - Tag key max length: 128 characters
    - Tag value max length: 256 characters

    ## Related Functions

    - `sync_tags_in_region()`: Single-region tag sync implementation
    - `get_tag_sync_settings()`: Get tag sync configuration
    - `update_tag_sync_settings()`: Update tag sync configuration

    Runs asynchronously when called via API Gateway to avoid timeout.
    Supports cross-account operations for target accounts.
    """
    try:
        # Get parameters from request body
        target_account_id = None
        region = None
        assume_role_name = None
        is_async_execution = False
        use_async = False  # Only use async for API Gateway calls
        sync_source = "manual"

        # Detect EventBridge trigger
        if body and isinstance(body, dict):
            if body.get("synch_tags") or body.get("synch_instance_type"):
                sync_source = "eventbridge"
            target_account_id = body.get("accountId")
            region = body.get("region")
            assume_role_name = body.get("assumeRoleName")
            is_async_execution = body.get("_async_execution", False)
            use_async = body.get("async", False)  # API Gateway passes this
            if body.get("_sync_source"):
                sync_source = body.get("_sync_source")

        # If this is an async execution (self-invoked), run the actual sync
        if is_async_execution:
            print(
                f"Running async tag sync execution - target_account_id: {target_account_id}, region: {region}, source: {sync_source}"
            )
            try:
                if not target_account_id:
                    print("Starting tag sync for ALL target accounts...")
                    result = _sync_tags_all_target_accounts(region, sync_source)
                else:
                    print(f"Starting tag sync for single account: {target_account_id}")
                    result = _sync_tags_for_account(target_account_id, region, assume_role_name)
                # Clear lock on completion
                _clear_tag_sync_lock()
                print("Async tag sync completed successfully")
                return result
            except Exception as e:
                print(f"Async tag sync failed with error: {e}")
                _clear_tag_sync_lock()
                raise

        # For API Gateway calls with async=true, invoke self asynchronously
        # This avoids the 29-second API Gateway timeout
        if use_async:
            # Check if sync is already running
            if _is_tag_sync_running():
                return response(
                    409,
                    {
                        "message": "Tag sync already in progress",
                        "status": "ALREADY_RUNNING",
                        "details": "Please wait for the current sync to complete.",
                    },
                )

            function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
            if function_name:
                # Set lock before starting
                _set_tag_sync_lock()

                print("Triggering async tag sync via self-invocation")
                lambda_client = boto3.client("lambda")

                async_payload = {
                    "operation": "handle_drs_tag_sync",
                    "body": {
                        "accountId": target_account_id,
                        "region": region,
                        "assumeRoleName": assume_role_name,
                        "_async_execution": True,
                        "_sync_source": sync_source,
                    },
                }

                lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType="Event",  # Async invocation
                    Payload=json.dumps(async_payload),
                )

                return response(
                    202,
                    {
                        "message": "Tag sync started",
                        "status": "STARTED",
                        "details": "Tag synchronization is running in the background. "
                        "Check CloudWatch logs for progress.",
                    },
                )

        # Synchronous execution (direct invocation, EventBridge, or async not requested)
        if not target_account_id:
            return _sync_tags_all_target_accounts(region, sync_source)
        else:
            return _sync_tags_for_account(target_account_id, region, assume_role_name)

    except Exception as e:
        print(f"Error in tag sync: {e}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


# Lock timeout in seconds (15 minutes max for tag sync)
TAG_SYNC_LOCK_TTL = 900


def _is_tag_sync_running() -> bool:
    """Check if a tag sync is currently running."""
    try:
        tag_sync_config_table = get_tag_sync_config_table()

        if not tag_sync_config_table:
            return False
        result = get_tag_sync_config_table().get_item(Key={"accountId": "_tag_sync_lock"})
        if "Item" not in result:
            return False
        lock = result["Item"]
        # Check if lock is expired
        started_at = lock.get("startedAt", 0)
        if time.time() - started_at > TAG_SYNC_LOCK_TTL:
            return False
        return lock.get("status") == "IN_PROGRESS"
    except Exception as e:
        print(f"Error checking tag sync lock: {e}")
        return False


def _set_tag_sync_lock() -> None:
    """Set the tag sync lock."""
    try:
        tag_sync_config_table = get_tag_sync_config_table()

        if not tag_sync_config_table:
            return
        get_tag_sync_config_table().put_item(
            Item={
                "accountId": "_tag_sync_lock",
                "status": "IN_PROGRESS",
                "startedAt": int(time.time()),
            }
        )
    except Exception as e:
        print(f"Error setting tag sync lock: {e}")


def _clear_tag_sync_lock() -> None:
    """Clear the tag sync lock."""
    try:
        tag_sync_config_table = get_tag_sync_config_table()

        if not tag_sync_config_table:
            return
        get_tag_sync_config_table().put_item(
            Item={
                "accountId": "_tag_sync_lock",
                "status": "COMPLETED",
                "completedAt": int(time.time()),
            }
        )
    except Exception as e:
        print(f"Error clearing tag sync lock: {e}")


def _save_tag_sync_result(result: Dict, source: str = "manual") -> None:
    """Save tag sync result for dashboard display."""
    try:
        tag_sync_config_table = get_tag_sync_config_table()

        if not tag_sync_config_table:
            return
        get_tag_sync_config_table().put_item(
            Item={
                "accountId": "_last_tag_sync",
                "timestamp": int(time.time()),
                "source": source,  # "manual", "eventbridge", "settings_update"
                "totalAccounts": result.get("total_accounts", 1),
                "totalSynced": result.get("total_synced", 0),
                "totalFailed": result.get("total_failed", 0),
                "totalServers": result.get("total_servers", 0),
                "status": ("SUCCESS" if result.get("total_failed", 0) == 0 else "PARTIAL"),
            }
        )
    except Exception as e:
        print(f"Error saving tag sync result: {e}")


def get_last_tag_sync_status() -> Dict:
    """Get the last tag sync status for dashboard display."""
    try:
        tag_sync_config_table = get_tag_sync_config_table()

        if not tag_sync_config_table:
            return response(200, {"message": "No sync history available"})

        from datetime import datetime

        # First check if a sync is currently running
        if _is_tag_sync_running():
            # Get the lock to show when it started
            lock_result = get_tag_sync_config_table().get_item(Key={"accountId": "_tag_sync_lock"})
            started_at = 0
            if "Item" in lock_result:
                started_at = lock_result["Item"].get("startedAt", 0)
            iso_started = datetime.utcfromtimestamp(started_at).isoformat() + "Z" if started_at else None

            return response(
                200,
                {
                    "lastSync": iso_started,
                    "source": "manual",
                    "totalAccounts": 0,
                    "totalSynced": 0,
                    "totalFailed": 0,
                    "totalServers": 0,
                    "status": "IN_PROGRESS",
                },
            )

        # No sync running, return last completed sync
        result = get_tag_sync_config_table().get_item(Key={"accountId": "_last_tag_sync"})
        if "Item" not in result:
            return response(200, {"message": "No sync history available"})

        item = result["Item"]
        # Convert timestamp to ISO format
        timestamp = item.get("timestamp", 0)
        iso_time = datetime.utcfromtimestamp(timestamp).isoformat() + "Z" if timestamp else None

        return response(
            200,
            {
                "lastSync": iso_time,
                "source": item.get("source", "unknown"),
                "totalAccounts": item.get("totalAccounts", 0),
                "totalSynced": item.get("totalSynced", 0),
                "totalFailed": item.get("totalFailed", 0),
                "totalServers": item.get("totalServers", 0),
                "status": item.get("status", "UNKNOWN"),
            },
        )
    except Exception as e:
        print(f"Error getting last tag sync status: {e}")
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def _sync_tags_for_account(target_account_id: str, region: str = None, assume_role_name: str = None) -> Dict:
    """Sync tags for a specific account."""
    try:
        account_name = get_account_name(target_account_id)
        current_account_id = get_current_account_id()
        is_current_account = target_account_id == current_account_id

        # Build account context
        account_context = {
            "accountId": target_account_id,
            "accountName": account_name,
            "isCurrentAccount": is_current_account,
            "externalId": "drs-orchestration-cross-account",
        }

        if not is_current_account:
            # Get role from target accounts table or use provided/default
            if assume_role_name:
                account_context["assumeRoleName"] = assume_role_name
            else:
                role = _get_target_account_role(target_account_id)
                account_context["assumeRoleName"] = role or "DRSOrchestrationRole"

        return _sync_tags_single_account(account_context, region)

    except Exception as e:
        print(f"Error syncing tags for account {target_account_id}: {e}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def _get_target_account_role(account_id: str) -> str:
    """Get the cross-account role name for a target account."""
    try:
        target_accounts_table = get_target_accounts_table()
        if not target_accounts_table:
            return None
        result = target_accounts_table.get_item(Key={"accountId": account_id})
        if "Item" in result:
            return result["Item"].get("assumeRoleName", "DRSOrchestrationRole")
        return None
    except Exception as e:
        print(f"Error getting role for account {account_id}: {e}")
        return None


def _sync_tags_all_target_accounts(region: str = None, source: str = "manual") -> Dict:
    """
    Sync tags for ALL registered target accounts.

    Called by EventBridge scheduled trigger. Iterates over all target accounts
    in DynamoDB and syncs EC2 tags to DRS source servers in each.
    """
    print(f"Starting tag sync for all target accounts (source: {source})")

    all_results = []
    total_accounts = 0
    total_synced = 0
    total_failed = 0

    try:
        target_accounts_table = get_target_accounts_table()
        if not target_accounts_table:
            return response(
                500,
                error_response(
                    ERROR_INTERNAL_ERROR,
                    "Internal error occurred",
                    details={"error": "Target accounts table not configured"},
                ),
            )

        # Get all target accounts
        scan_result = target_accounts_table.scan()
        target_accounts = scan_result.get("Items", [])

        while "LastEvaluatedKey" in scan_result:
            scan_result = target_accounts_table.scan(ExclusiveStartKey=scan_result["LastEvaluatedKey"])
            target_accounts.extend(scan_result.get("Items", []))

        if not target_accounts:
            print("No target accounts configured")
            return response(200, {"message": "No target accounts configured"})

        current_account_id = get_current_account_id()

        for account in target_accounts:
            account_id = account.get("accountId")
            account_name = account.get("accountName", account_id)
            assume_role = account.get("assumeRoleName", "DRSOrchestrationRole")
            is_current = account_id == current_account_id

            print(f"Syncing tags for target account: {account_id} ({account_name})")

            account_context = {
                "accountId": account_id,
                "accountName": account_name,
                "isCurrentAccount": is_current,
                "externalId": "drs-orchestration-cross-account",
            }

            if not is_current:
                account_context["assumeRoleName"] = assume_role

            try:
                result = _sync_tags_single_account(account_context, region)
                result_body = json.loads(result.get("body", "{}"))
                all_results.append({"accountId": account_id, "result": result_body})
                total_accounts += 1
                total_synced += result_body.get("total_synced", 0)
                total_failed += result_body.get("total_failed", 0)
            except Exception as e:
                print(f"Error syncing account {account_id}: {e}")
                all_results.append({"accountId": account_id, "error": str(e)})

    except Exception as e:
        print(f"Error scanning target accounts: {e}")
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )

    summary = {
        "message": "Tag sync complete for all target accounts",
        "total_accounts": total_accounts,
        "total_synced": total_synced,
        "total_failed": total_failed,
        "accounts": all_results,
    }

    # Save result for dashboard
    _save_tag_sync_result(summary, source=source)

    print(f"Tag sync complete: {total_synced} synced, {total_failed} failed " f"across {total_accounts} accounts")

    return response(200, summary)


def _get_initialized_drs_regions(account_context: Dict) -> List[str]:
    """
    Quickly detect which regions have DRS initialized by checking for source servers.

    This is much faster than iterating all 30 DRS regions - it only makes one API call
    per region to check if DRS is initialized (has any source servers).

    Uses concurrent execution to check multiple regions in parallel.
    """
    import concurrent.futures

    account_id = account_context.get("accountId")
    is_current_account = account_context.get("isCurrentAccount", True)

    def check_region(region: str) -> str:
        """Check if a region has DRS source servers. Returns region name or None."""
        try:
            if is_current_account:
                drs_client = boto3.client("drs", region_name=region)
            else:
                # Cross-account: assume role
                assume_role_name = account_context.get("assumeRoleName", "DRSOrchestrationRole")
                external_id = account_context.get("externalId", "drs-orchestration-cross-account")
                sts_client = boto3.client("sts")
                role_arn = f"arn:aws:iam::{account_id}:role/{assume_role_name}"
                assumed = sts_client.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName="drs-region-check",
                    ExternalId=external_id,
                )
                creds = assumed["Credentials"]
                drs_client = boto3.client(
                    "drs",
                    region_name=region,
                    aws_access_key_id=creds["AccessKeyId"],
                    aws_secret_access_key=creds["SecretAccessKey"],
                    aws_session_token=creds["SessionToken"],
                )

            # Quick check - just get 1 server to see if DRS is initialized
            resp = drs_client.describe_source_servers(maxResults=1)
            if resp.get("items"):
                return region
            return None
        except Exception:
            # Region not initialized or access denied - skip it
            return None

    initialized_regions = []

    # Check regions in parallel (max 10 concurrent)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_region = {executor.submit(check_region, r): r for r in DRS_REGIONS}
        for future in concurrent.futures.as_completed(future_to_region):
            result = future.result()
            if result:
                initialized_regions.append(result)

    print(f"Found {len(initialized_regions)} initialized DRS regions: {initialized_regions}")
    return initialized_regions


def _sync_tags_single_account(account_context: Dict, region: str = None) -> Dict:
    """Sync tags for a single account across DRS regions."""
    account_id = account_context.get("accountId")
    account_name = account_context.get("accountName", account_id)

    total_synced = 0
    total_servers = 0
    total_failed = 0
    regions_with_servers = []

    print(f"Starting tag sync for account {account_id} ({account_name or 'Unknown'})")

    # Optimize: Only sync regions that have DRS initialized
    if region:
        regions_to_sync = [region]
    else:
        # First, quickly detect which regions have DRS servers
        print("Detecting initialized DRS regions...")
        regions_to_sync = _get_initialized_drs_regions(account_context)
        if not regions_to_sync:
            print("No initialized DRS regions found - nothing to sync")
            return response(
                200,
                {
                    "message": f"No DRS servers found in account {account_id}",
                    "accountId": account_id,
                    "accountName": account_name,
                    "total_regions": len(DRS_REGIONS),
                    "regions_with_servers": 0,
                    "total_servers": 0,
                    "total_synced": 0,
                    "total_failed": 0,
                    "regions": [],
                },
            )
        print(f"Will sync {len(regions_to_sync)} regions: {regions_to_sync}")

    for sync_region in regions_to_sync:
        try:
            result = sync_tags_in_region(sync_region, account_context)
            if result["total"] > 0:
                regions_with_servers.append(sync_region)
                total_servers += result["total"]
                total_synced += result["synced"]
                total_failed += result["failed"]
                print(f"Tag sync {sync_region}: {result['synced']}/{result['total']} synced")
        except Exception as e:
            print(f"Tag sync {sync_region}: skipped - {e}")

    summary = {
        "message": f"Tag sync complete for account {account_id}",
        "accountId": account_id,
        "accountName": account_name,
        "total_regions": len(DRS_REGIONS),
        "regions_with_servers": len(regions_with_servers),
        "total_servers": total_servers,
        "total_synced": total_synced,
        "total_failed": total_failed,
        "regions": regions_with_servers,
    }

    print(
        f"Tag sync complete: {total_synced}/{total_servers} servers synced "
        f"across {len(regions_with_servers)} regions"
    )

    return response(200, summary)


def sync_tags_in_region(drs_region: str, account_context: dict = None) -> dict:
    """
    Sync EC2 instance tags to DRS source servers in a single region.

    Core implementation for tag synchronization. Queries all DRS source servers in the
    specified region, retrieves tags from their source EC2 instances, and applies those
    tags to the DRS server ARNs. Automatically enables copyTags in DRS launch configuration
    to preserve tags during recovery operations.

    Supports cross-account tag syncing for extended source servers.

    ## Use Cases

    ### 1. Regional Tag Sync
    Synchronize tags for all DRS servers in a specific region:
    ```python
    result = sync_tags_in_region("us-east-1")
    # Returns: {"total": 50, "synced": 48, "failed": 2, "region": "us-east-1"}
    ```

    ### 2. Cross-Region Tag Sync
    Handles servers where EC2 instance is in different region than DRS:
    ```python
    # EC2 instance in us-east-1, DRS replication in us-west-2
    result = sync_tags_in_region("us-west-2")
    # Automatically queries EC2 tags from us-east-1
    ```

    ### 3. Cross-Account Tag Sync
    Sync tags for extended source servers in target account:
    ```python
    account_context = {
        "accountId": "111122223333",
        "accountName": "DEMO_TARGET",
        "isCurrentAccount": False,
        "assumeRoleName": "DRSOrchestrationRole",
        "externalId": "drs-orchestration-cross-account"
    }
    result = sync_tags_in_region("us-west-2", account_context)
    ```

    ### 4. Scheduled Regional Sync
    Can be called from EventBridge for periodic regional sync:
    ```python
    for region in ["us-east-1", "us-west-2", "eu-west-1"]:
        sync_tags_in_region(region)
    ```

    ## Behavior

    ### Tag Synchronization Process
    1. Query all DRS source servers in specified region (paginated)
    2. For each server:
       - Extract EC2 instance ID from sourceProperties
       - Determine source region from sourceCloudProperties
       - Query EC2 tags from source instance
       - Filter out AWS-managed tags (aws:*)
       - Apply tags to DRS source server ARN
       - Enable copyTags in DRS launch configuration

    ### Server Filtering
    - Skips servers without EC2 instance ID
    - Skips DISCONNECTED servers (no active replication)
    - Skips deleted/inaccessible EC2 instances
    - Skips servers with no tags

    ### Error Handling
    - Non-blocking: Server failures don't stop region sync
    - Graceful degradation: Continues processing remaining servers
    - Detailed logging: All errors logged with server context

    ## Args

    drs_region: AWS region containing DRS source servers
    account_id: AWS account ID (reserved for future multi-account support)

    ## Returns

    Dict with regional sync results:
        - total: Total DRS servers found in region
        - synced: Servers successfully synced
        - failed: Servers that failed to sync
        - region: Region name

    ## Example Response

    ```json
    {
      "total": 50,
      "synced": 48,
      "failed": 2,
      "region": "us-east-1"
    }
    ```

    ## Performance

    ### Execution Time
    - Small region (< 20 servers): 5-15 seconds
    - Medium region (20-100 servers): 15-60 seconds
    - Large region (100-200 servers): 60-120 seconds

    ### API Calls
    - DRS DescribeSourceServers: 1 call (paginated, 200 per page)
    - EC2 DescribeInstances: 1 per server
    - DRS TagResource: 1 per server with tags
    - DRS UpdateLaunchConfiguration: 1 per server

    ### Throttling
    - DRS API: 10 TPS per region
    - EC2 API: 100 TPS per region
    - Automatic retry with exponential backoff

    ## Related Functions

    - `handle_drs_tag_sync()`: Multi-region tag sync orchestrator
    - `get_tag_sync_settings()`: Get tag sync configuration
    - `update_tag_sync_settings()`: Update tag sync configuration

    Args:
        drs_region: AWS region to sync tags in
        account_context: Account context dict with accountId, isCurrentAccount, assumeRoleName, externalId
    """
    # Use account context if provided, otherwise default to current account
    if account_context is None:
        account_context = {
            "accountId": get_current_account_id(),
            "isCurrentAccount": True,
        }

    # Create DRS client with cross-account support
    drs_client = create_drs_client(drs_region, account_context)
    ec2_clients = {}

    # Get all DRS source servers
    source_servers = []
    paginator = drs_client.get_paginator("describe_source_servers")
    for page in paginator.paginate(filters={}, maxResults=200):
        source_servers.extend(page.get("items", []))

    print(f"Tag sync: Found {len(source_servers)} DRS source servers in {drs_region}")

    synced = 0
    failed = 0
    skipped_no_instance = 0
    skipped_disconnected = 0
    skipped_no_tags = 0

    for server in source_servers:
        try:
            instance_id = server.get("sourceProperties", {}).get("identificationHints", {}).get("awsInstanceID")
            source_server_id = server["sourceServerID"]
            server_arn = server["arn"]
            source_region = server.get("sourceCloudProperties", {}).get("originRegion", drs_region)

            if not instance_id:
                skipped_no_instance += 1
                continue

            # Skip disconnected servers
            replication_state = server.get("dataReplicationInfo", {}).get("dataReplicationState", "")
            if replication_state == "DISCONNECTED":
                skipped_disconnected += 1
                continue

            # Get or create EC2 client for source region
            # EC2 instances are in the target account (same account as DRS servers)
            # Staging account is only used for replication infrastructure
            ec2_client_key = f"{source_region}"
            if ec2_client_key not in ec2_clients:
                ec2_clients[ec2_client_key] = create_ec2_client(source_region, account_context)
            ec2_client = ec2_clients[ec2_client_key]

            # Get EC2 instance tags
            try:
                ec2_response = ec2_client.describe_instances(InstanceIds=[instance_id])
                if not ec2_response["Reservations"]:
                    print(f"Warning: Instance {instance_id} not found in account {account_context.get('accountId')}")
                    failed += 1
                    continue
                instance = ec2_response["Reservations"][0]["Instances"][0]
                ec2_tags = {
                    tag["Key"]: tag["Value"] for tag in instance.get("Tags", []) if not tag["Key"].startswith("aws:")
                }
            except Exception as e:
                # Skip instances that cannot be described (permissions, deleted, etc.)
                print(
                    f"Warning: Could not describe instance {instance_id} in account {account_context.get('accountId')}: {e}"
                )
                failed += 1
                continue

            if not ec2_tags:
                skipped_no_tags += 1
                continue

            # Sync tags to DRS source server
            drs_client.tag_resource(resourceArn=server_arn, tags=ec2_tags)

            # Enable copyTags in launch configuration
            try:
                drs_client.update_launch_configuration(sourceServerID=source_server_id, copyTags=True)
            except ClientError as e:
                error_code = e.response.get("error", {}).get("Code", "")
                if error_code in [
                    "ValidationException",
                    "ResourceNotFoundException",
                ]:
                    print(f"Cannot update launch config for server {source_server_id}: {error_code}")
                else:
                    print(f"DRS error updating launch config for {source_server_id}: {e}")
            except Exception as e:
                print(f"Unexpected error updating launch config for {source_server_id}: {e}")

            synced += 1

        except Exception as e:
            failed += 1
            print(f"Failed to sync server {server.get('sourceServerID', 'unknown')}: {e}")

    print(
        f"Tag sync {drs_region} complete: {synced} synced, {failed} failed, "
        f"skipped: {skipped_no_instance} no instance, {skipped_disconnected} disconnected, "
        f"{skipped_no_tags} no tags"
    )

    return {
        "total": len(source_servers),
        "synced": synced,
        "failed": failed,
        "region": drs_region,
        "skipped": {
            "noInstanceId": skipped_no_instance,
            "disconnected": skipped_disconnected,
            "noTags": skipped_no_tags,
        },
    }


def get_tag_sync_settings() -> Dict:
    """
    Get current tag sync configuration from EventBridge scheduled rule.

    Retrieves the configuration for automated tag synchronization, including whether
    it's enabled and the sync interval. Tag sync is implemented as an EventBridge
    scheduled rule that triggers the data-management-handler Lambda function.

    ## Use Cases

    ### 1. Check Current Configuration
    ```bash
    curl -X GET https://api.example.com/drs/tag-sync/settings \
      -H "Authorization: Bearer $TOKEN"
    ```

    ### 2. Verify Sync Schedule
    ```python
    settings = get_tag_sync_settings()
    if settings["enabled"]:
        print(f"Tag sync runs every {settings['intervalHours']} hours")
    ```

    ### 3. Troubleshoot Sync Issues
    ```python
    settings = get_tag_sync_settings()
    if not settings["enabled"]:
        print("Tag sync is disabled - enable it to start automatic sync")
    ```

    ## Integration Points

    ### API Gateway Invocation
    ```bash
    curl -X GET https://api.example.com/drs/tag-sync/settings \
      -H "Authorization: Bearer $TOKEN"
    ```

    ### Direct Lambda Invocation
    ```python
    lambda_client.invoke(
        FunctionName='data-management-handler',
        Payload=json.dumps({
            "operation": "get_tag_sync_settings"
        })
    )
    ```

    ## Behavior

    ### EventBridge Rule Lookup
    1. Constructs rule name from environment variables:
       - Pattern: `{PROJECT_NAME}-tag-sync-schedule-{ENVIRONMENT}`
       - Example: `drs-orchestration-tag-sync-schedule-dev`
    2. Queries EventBridge for rule details
    3. Parses schedule expression to extract interval
    4. Returns configuration with enabled state

    ### Default Behavior
    If EventBridge rule doesn't exist:
    - Returns default settings (disabled, 4-hour interval)
    - Does not create the rule automatically
    - Includes message indicating rule not found

    ## Returns

    Dict with tag sync configuration:
        - enabled: Whether tag sync is enabled (bool)
        - intervalHours: Sync interval in hours (int)
        - scheduleExpression: EventBridge schedule expression (str)
        - ruleName: EventBridge rule name (str)
        - lastModified: Last modification timestamp (ISO 8601 string)
        - message: Optional message if rule not found

    ## Example Response

    ```json
    {
      "enabled": true,
      "intervalHours": 4,
      "scheduleExpression": "rate(4 hours)",
      "ruleName": "drs-orchestration-tag-sync-schedule-dev",
      "lastModified": "2026-01-25T10:30:00Z"
    }
    ```

    ## Error Handling

    ### Rule Not Found (200 OK)
    Returns default settings with message:
    ```json
    {
      "enabled": false,
      "intervalHours": 4,
      "scheduleExpression": "rate(4 hours)",
      "ruleName": "drs-orchestration-tag-sync-schedule-dev",
      "lastModified": null,
      "message": "Tag sync rule not found - using defaults"
    }
    ```

    ### Access Denied (500 Error)
    Returns error if insufficient EventBridge permissions:
    ```json
    {
      "error": "Failed to get tag sync settings: AccessDeniedException"
    }
    ```

    ## Related Functions

    - `update_tag_sync_settings()`: Update tag sync configuration
    - `handle_drs_tag_sync()`: Execute tag sync operation
    - `sync_tags_in_region()`: Regional tag sync implementation

    Get current tag sync configuration settings
    """
    try:
        import boto3

        # Get EventBridge client
        events_client = boto3.client("events")

        # Get environment variables for current settings
        project_name = os.environ.get("PROJECT_NAME", "drs-orchestration")
        environment = os.environ.get("ENVIRONMENT", "prod")

        # Construct rule name based on naming convention
        rule_name = f"{project_name}-tag-sync-schedule-{environment}"

        try:
            # Get the EventBridge rule
            rule_response = events_client.describe_rule(Name=rule_name)

            # Parse schedule expression to get interval
            schedule_expression = rule_response.get("ScheduleExpression", "")
            interval_hours = parse_schedule_expression(schedule_expression)

            settings = {
                "enabled": rule_response.get("State") == "ENABLED",
                "intervalHours": interval_hours,
                "scheduleExpression": schedule_expression,
                "ruleName": rule_name,
                "lastModified": (
                    rule_response.get("ModifiedDate", "").isoformat() if rule_response.get("ModifiedDate") else None
                ),
            }

            return response(200, settings)

        except events_client.exceptions.ResourceNotFoundException:
            # Rule doesn't exist - return default settings
            return response(
                200,
                {
                    "enabled": False,
                    "intervalHours": 4,
                    "scheduleExpression": "rate(4 hours)",
                    "ruleName": rule_name,
                    "lastModified": None,
                    "message": "Tag sync rule not found - using defaults",
                },
            )

    except Exception as e:
        print(f"Error getting tag sync settings: {e}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": f"Failed to get tag sync settings: {str(e)}"},
            ),
        )


def update_tag_sync_settings(body: Dict) -> Dict:
    """
    Update tag sync configuration in EventBridge scheduled rule.

    Modifies the automated tag synchronization configuration, including enabling/disabling
    the sync and changing the sync interval. When enabled, automatically triggers an
    immediate manual sync to apply changes right away.

    ## Use Cases

    ### 1. Enable Tag Sync
    ```bash
    curl -X PUT https://api.example.com/drs/tag-sync/settings \
      -H "Authorization: Bearer $TOKEN" \
      -d '{"enabled": true, "intervalHours": 4}'
    ```

    ### 2. Disable Tag Sync
    ```bash
    curl -X PUT https://api.example.com/drs/tag-sync/settings \
      -H "Authorization: Bearer $TOKEN" \
      -d '{"enabled": false}'
    ```

    ### 3. Change Sync Interval
    ```bash
    curl -X PUT https://api.example.com/drs/tag-sync/settings \
      -H "Authorization: Bearer $TOKEN" \
      -d '{"enabled": true, "intervalHours": 2}'
    ```

    ## Integration Points

    ### API Gateway Invocation
    ```bash
    curl -X PUT https://api.example.com/drs/tag-sync/settings \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"enabled": true, "intervalHours": 4}'
    ```

    ### Direct Lambda Invocation
    ```python
    lambda_client.invoke(
        FunctionName='data-management-handler',
        Payload=json.dumps({
            "operation": "update_tag_sync_settings",
            "body": {
                "enabled": True,
                "intervalHours": 4
            }
        })
    )
    ```

    ## Behavior

    ### Update Process
    1. Validates request body (enabled required, intervalHours optional)
    2. Checks if EventBridge rule exists
    3. Updates rule state (ENABLED/DISABLED)
    4. Updates schedule expression if intervalHours provided
    5. Triggers immediate manual sync if enabled (async)
    6. Returns updated configuration

    ### Immediate Sync Trigger
    When tag sync is enabled or settings changed:
    - Triggers async manual sync (doesn't wait for completion)
    - Ensures tags are synced immediately after configuration change
    - Sync runs in background (doesn't block settings update)

    ### Rule Creation
    Does NOT create EventBridge rule if it doesn't exist. Rule must be created
    during CloudFormation deployment with EnableTagSync=true parameter.

    ## Args

    body: Request body with:
        - enabled (bool, required): Enable or disable tag sync
        - intervalHours (int, optional): Sync interval (1-24 hours)

    ## Returns

    Dict with updated configuration:
        - message: Success message
        - enabled: Whether tag sync is enabled (bool)
        - intervalHours: Sync interval in hours (int)
        - scheduleExpression: EventBridge schedule expression (str)
        - ruleName: EventBridge rule name (str)
        - lastModified: Last modification timestamp (ISO 8601 string)
        - syncTriggered: Whether immediate sync was triggered (bool)
        - syncResult: Result of immediate sync trigger (dict or null)

    ## Example Response

    ```json
    {
      "message": "Tag sync settings updated successfully",
      "enabled": true,
      "intervalHours": 4,
      "scheduleExpression": "rate(4 hours)",
      "ruleName": "drs-orchestration-tag-sync-schedule-dev",
      "lastModified": "2026-01-25T10:35:00Z",
      "syncTriggered": true,
      "syncResult": {
        "message": "Manual sync triggered asynchronously"
      }
    }
    ```

    ## Error Handling

    ### Invalid Request (400 Bad Request)
    ```json
    {
      "error": "enabled field is required"
    }
    ```

    ### Rule Not Found (400 Bad Request)
    ```json
    {
      "error": "Tag sync rule not found. Please redeploy the CloudFormation stack with EnableTagSync=true to create the rule.",  # noqa: E501
      "code": "RULE_NOT_FOUND"
    }
    ```

    ### Invalid Interval (400 Bad Request)
    ```json
    {
      "error": "intervalHours must be a number between 1 and 24"
    }
    ```

    ### Access Denied (500 Error)
    ```json
    {
      "error": "Failed to update tag sync settings: AccessDeniedException"
    }
    ```

    ## Validation Rules

    ### enabled Field
    - Required: Yes
    - Type: Boolean
    - Values: true or false

    ### intervalHours Field
    - Required: No (optional)
    - Type: Integer
    - Range: 1-24 hours
    - Default: Current schedule (if not provided)

    ## Performance

    ### Execution Time
    - Settings update: < 1 second
    - Immediate sync trigger: Async (doesn't block)

    ### API Calls
    - EventBridge DescribeRule: 1 call
    - EventBridge EnableRule or DisableRule: 1 call
    - EventBridge PutRule: 1 call (if interval changed)
    - Lambda Invoke: 1 call (if enabled, async)

    ## Related Functions

    - `get_tag_sync_settings()`: Get current tag sync configuration
    - `handle_drs_tag_sync()`: Execute tag sync operation
    - `sync_tags_in_region()`: Regional tag sync implementation

    Update tag sync configuration settings
    """
    try:
        import json

        import boto3

        # Validate input
        if not isinstance(body, dict):
            return response(
                400,
                error_response(
                    ERROR_INVALID_PARAMETER,
                    "Invalid parameter value",
                    details={
                        "parameter": "body",
                        "value": body,
                        "expected": "JSON object",
                    },
                ),
            )

        enabled = body.get("enabled")
        interval_hours = body.get("intervalHours")

        if enabled is None:
            return response(
                400,
                error_response(
                    ERROR_MISSING_PARAMETER,
                    "Missing required parameter",
                    details={"parameter": "enabled"},
                ),
            )

        if not isinstance(enabled, bool):
            return response(
                400,
                error_response(
                    ERROR_INVALID_PARAMETER,
                    "Invalid parameter value",
                    details={
                        "parameter": "enabled",
                        "value": enabled,
                        "expected": "boolean",
                    },
                ),
            )

        if interval_hours is not None:
            if not isinstance(interval_hours, (int, float)) or interval_hours < 1 or interval_hours > 24:
                return response(
                    400,
                    {"error": "intervalHours must be a number between 1 and 24"},
                )
            interval_hours = int(interval_hours)

        # Get EventBridge client
        events_client = boto3.client("events")

        # Get environment variables
        project_name = os.environ.get("PROJECT_NAME", "drs-orchestration")
        environment = os.environ.get("ENVIRONMENT", "prod")

        # Construct rule name
        rule_name = f"{project_name}-tag-sync-schedule-{environment}"

        try:
            # Get current rule to check if it exists
            current_rule = events_client.describe_rule(Name=rule_name)
            rule_exists = True
        except events_client.exceptions.ResourceNotFoundException:
            rule_exists = False
            current_rule = {}

        # If rule doesn't exist and we're trying to enable, return error
        if not rule_exists and enabled:
            return response(
                400,
                {
                    "error": "Tag sync rule not found. Please redeploy the CloudFormation stack with EnableTagSync=true to create the rule.",  # noqa: E501
                    "code": "RULE_NOT_FOUND",
                },
            )

        # If rule doesn't exist and we're disabling, that's fine
        if not rule_exists and not enabled:
            return response(
                200,
                {
                    "message": "Tag sync is already disabled (rule does not exist)",
                    "enabled": False,
                    "intervalHours": interval_hours or 4,
                },
            )

        # Update rule state
        if enabled:
            # Enable the rule
            events_client.enable_rule(Name=rule_name)

            # Update schedule if interval_hours provided
            if interval_hours is not None:
                # Use correct singular/plural form for EventBridge schedule
                # expression
                time_unit = "hour" if interval_hours == 1 else "hours"
                new_schedule = f"rate({interval_hours} {time_unit})"
                events_client.put_rule(
                    Name=rule_name,
                    ScheduleExpression=new_schedule,
                    State="ENABLED",
                    Description=f"Scheduled DRS tag synchronization every {interval_hours} {time_unit}",
                )
            else:
                # Just enable with current schedule
                events_client.enable_rule(Name=rule_name)
                interval_hours = parse_schedule_expression(current_rule.get("ScheduleExpression", "rate(4 hours)"))
        else:
            # Disable the rule
            events_client.disable_rule(Name=rule_name)
            interval_hours = interval_hours or parse_schedule_expression(
                current_rule.get("ScheduleExpression", "rate(4 hours)")
            )

        # Get updated rule info
        updated_rule = events_client.describe_rule(Name=rule_name)

        # Trigger immediate manual sync when settings are changed or enabled
        sync_triggered = False
        sync_result = None

        if enabled:
            try:
                print("Settings updated - triggering immediate manual tag sync asynchronously")

                # Trigger async manual sync by invoking this same Lambda
                # function
                lambda_client = boto3.client("lambda")
                function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")

                if function_name:
                    # Create async payload for manual sync using direct invocation
                    async_payload = {
                        "operation": "handle_drs_tag_sync",
                        "body": {
                            "async": False,  # Run synchronously in background
                            "_sync_source": "settings_update",
                        },
                    }

                    # Invoke async (don't wait for response)
                    lambda_client.invoke(
                        FunctionName=function_name,
                        InvocationType="Event",  # Async invocation
                        Payload=json.dumps(async_payload),
                    )

                    sync_triggered = True
                    sync_result = {"message": "Manual sync triggered asynchronously"}
                    print("Async manual sync triggered successfully")
                else:
                    print("Warning: Could not determine Lambda function name for async sync")

            except Exception as sync_error:
                print(f"Warning: Failed to trigger async manual sync after settings update: {sync_error}")
                # Don't fail the settings update if sync fails
                sync_triggered = False

        result = {
            "message": "Tag sync settings updated successfully",
            "enabled": updated_rule.get("State") == "ENABLED",
            "intervalHours": interval_hours,
            "scheduleExpression": updated_rule.get("ScheduleExpression"),
            "ruleName": rule_name,
            "lastModified": (
                updated_rule.get("ModifiedDate", "").isoformat() if updated_rule.get("ModifiedDate") else None
            ),
            "syncTriggered": sync_triggered,
            "syncResult": sync_result if sync_triggered else None,
        }

        return response(200, result)

    except Exception as e:
        print(f"Error updating tag sync settings: {e}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": f"Failed to update tag sync settings: {str(e)}"},
            ),
        )


def parse_schedule_expression(schedule_expression: str) -> int:
    """Parse EventBridge schedule expression to extract interval hours"""
    try:
        # Handle rate expressions like "rate(4 hours)"
        if schedule_expression.startswith("rate(") and schedule_expression.endswith(")"):
            rate_part = schedule_expression[5:-1]  # Remove "rate(" and ")"

            if "hour" in rate_part:
                # Extract number from "4 hours" or "1 hour"
                import re

                match = re.search(r"(\d+)\s+hours?", rate_part)
                if match:
                    return int(match.group(1))
            elif "minute" in rate_part:
                # Convert minutes to hours
                match = re.search(r"(\d+)\s+minutes?", rate_part)
                if match:
                    minutes = int(match.group(1))
                    return max(1, minutes // 60)  # At least 1 hour

        # Default fallback
        return 4

    except Exception as e:
        print(f"Error parsing schedule expression '{schedule_expression}': {e}")
        return 4


# ============================================================================
# Helper Functions (Batch 4)
# ============================================================================


def apply_launch_config_to_servers(
    server_ids: List[str],
    launch_config: Dict,
    region: str,
    protection_group: Dict = None,
    protection_group_id: str = None,
    protection_group_name: str = None,
) -> Dict:
    """Apply launchConfig to all servers' EC2 launch templates and DRS settings.

    Called immediately when Protection Group is saved.
    Returns summary of results for each server.

    Supports per-server configuration overrides via protection_group parameter.
    When protection_group is provided, merges group defaults with server-specific
    overrides using get_effective_launch_config().

    For extended source servers (servers from staging accounts), launch settings
    are applied in the target account where recovery happens, not the staging account.

    Args:
        server_ids: List of DRS source server IDs
        launch_config: Dict with SubnetId, SecurityGroupIds, InstanceProfileName, etc.
        region: AWS region
        protection_group: Optional full PG dict with servers array for per-server configs
        protection_group_id: Optional PG ID for version tracking
        protection_group_name: Optional PG name for version tracking

    Returns:
        Dict with applied, skipped, failed counts and details array
    """
    if not launch_config or not server_ids:
        return {"applied": 0, "skipped": 0, "failed": 0, "details": []}

    # Import config merge utility for per-server overrides
    from shared.config_merge import get_effective_launch_config
    from shared.cross_account import create_drs_client

    # Determine target account context from protection group
    account_context = None
    if protection_group:
        account_id = protection_group.get("accountId")
        assume_role_name = protection_group.get("assumeRoleName")

        # If accountId is provided, use it for cross-account access
        if account_id and account_id.strip():
            account_context = {
                "accountId": account_id,
                "assumeRoleName": assume_role_name,
                "isCurrentAccount": False,
                "externalId": "drs-orchestration-cross-account",
            }
            print(f"Using target account {account_id} for launch config application")
        else:
            # No accountId specified - query first server to detect if extended source servers
            # For extended source servers, we need to apply settings in the target account
            print("No accountId specified, checking if servers are extended source servers")
            try:
                temp_drs = boto3.client("drs", region_name=region)
                first_server_response = temp_drs.describe_source_servers(filters={"sourceServerIDs": [server_ids[0]]})
                if first_server_response.get("items"):
                    first_server = first_server_response["items"][0]
                    staging_area = first_server.get("stagingArea", {})
                    staging_account_id = staging_area.get("stagingAccountID", "")

                    # Get current account ID
                    from shared.cross_account import get_current_account_id

                    current_account_id = get_current_account_id()

                    # If server is in current account but has different staging account,
                    # it's an extended source server - we're already in the target account
                    if staging_account_id and staging_account_id != current_account_id:
                        print(
                            f"Detected extended source server from staging account "
                            f"{staging_account_id}, already in target account {current_account_id}"
                        )
                        # No cross-account needed, we're already in the target account
                    else:
                        print(f"Server is native to current account {current_account_id}")
            except Exception as e:
                print(f"Warning: Could not detect server account context: {e}")
                # Continue with current account credentials

    # Create DRS client with proper account context
    regional_drs = create_drs_client(region, account_context)

    # Create EC2 client with same account context
    if account_context and not account_context.get("isCurrentAccount", True):
        from shared.cross_account import get_cross_account_session

        account_id = account_context["accountId"]
        assume_role_name = account_context.get("assumeRoleName")
        if assume_role_name:
            role_arn = f"arn:aws:iam::{account_id}:role/{assume_role_name}"
            external_id = account_context.get("externalId")
            session = get_cross_account_session(role_arn, external_id)
            ec2 = session.client("ec2", region_name=region)
            print(f"Created cross-account EC2 client for account {account_id}")
        else:
            ec2 = boto3.client("ec2", region_name=region)
    else:
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
            # so we must call it before our EC2 template updates to avoid being
            # overwritten
            drs_update = {"sourceServerID": server_id}

            # If static IP is specified, disable copyPrivateIp to prevent DRS
            # from overriding it
            if effective_config.get("staticPrivateIp"):
                drs_update["copyPrivateIp"] = False
            elif "copyPrivateIp" in effective_config:
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
                    config_details.append("CopyTags")
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


def apply_launch_configs(group_id: str, body: Dict) -> Dict:
    """
    Manually apply launch configurations to a protection group.

    Supports three invocation methods:
    - Frontend: Via API Gateway with Cognito auth
    - API: Via API Gateway with IAM auth
    - Direct: Lambda invocation with operation parameter

    Args:
        group_id: Protection group ID
        body: {"force": bool}  # Force re-apply even if status is ready

    Returns:
        {
            "groupId": "pg-xxx",
            "status": "ready",
            "appliedServers": 10,
            "failedServers": 0,
            "errors": []
        }
    """
    from shared.launch_config_service import (
        apply_launch_configs_to_group,
        get_config_status,
    )

    try:
        # Get protection group
        table = get_protection_groups_table()
        pg_response = table.get_item(Key={"groupId": group_id})

        if "Item" not in pg_response:
            return response(
                404,
                error_response(
                    ERROR_NOT_FOUND,
                    f"Protection group {group_id} not found",
                ),
            )

        protection_group = pg_response["Item"]

        # Check force flag
        force = body.get("force", False)

        # If not forcing, check current status
        if not force:
            current_status = get_config_status(group_id)
            if current_status.get("status") == "ready":
                return response(
                    200,
                    {
                        "groupId": group_id,
                        "status": "ready",
                        "appliedServers": len(current_status.get("serverConfigs", {})),
                        "failedServers": 0,
                        "message": ("Configuration already applied. " "Use force=true to re-apply."),
                        "errors": [],
                    },
                )

        # Get server IDs and launch configs
        server_ids = protection_group.get("sourceServerIds", [])
        if not server_ids:
            return response(
                400,
                error_response(
                    ERROR_INVALID_PARAMETER,
                    "Protection group has no servers",
                ),
            )

        # Build launch configs dict (group defaults + per-server overrides)
        launch_configs = {}

        for server_id in server_ids:
            # Get effective config (merge group defaults with server overrides)
            effective_config = get_effective_launch_config(protection_group, server_id)
            launch_configs[server_id] = effective_config

        # Get account context for cross-account operations
        account_context = None
        account_id = protection_group.get("accountId")
        assume_role_name = protection_group.get("assumeRoleName")

        if account_id and account_id.strip():
            account_context = {
                "accountId": account_id,
                "assumeRoleName": assume_role_name,
                "isCurrentAccount": False,
                "externalId": "drs-orchestration-cross-account",
            }

        # Apply configurations
        region = protection_group.get("region")
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs,
            account_context=account_context,
            timeout_seconds=300,
        )

        # Return result
        return response(
            200,
            {
                "groupId": group_id,
                "status": result.get("status"),
                "appliedServers": result.get("appliedServers", 0),
                "failedServers": result.get("failedServers", 0),
                "serverConfigs": result.get("serverConfigs", {}),
                "errors": result.get("errors", []),
            },
        )

    except Exception as e:
        print(f"Error applying launch configs to group {group_id}: {e}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(ERROR_INTERNAL_ERROR, str(e)),
        )


def get_launch_config_status(group_id: str) -> Dict:
    """
    Get launch configuration status for a protection group.

    Supports three invocation methods.

    Args:
        group_id: Protection group ID

    Returns:
        Configuration status dictionary
    """
    from shared.launch_config_service import get_config_status

    try:
        # Verify protection group exists
        table = get_protection_groups_table()
        pg_response = table.get_item(Key={"groupId": group_id})

        if "Item" not in pg_response:
            return response(
                404,
                error_response(
                    ERROR_NOT_FOUND,
                    f"Protection group {group_id} not found",
                ),
            )

        # Get configuration status
        config_status = get_config_status(group_id)

        return response(200, config_status)

    except Exception as e:
        print(f"Error getting launch config status for group {group_id}: {e}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(ERROR_INTERNAL_ERROR, str(e)),
        )


# ============================================================================
# Target Account Management Functions
# ============================================================================


def get_target_account(account_id: str) -> Dict:
    """Get a specific target account by ID"""
    try:
        target_accounts_table = get_target_accounts_table()
        if not target_accounts_table:
            return response(
                500,
                error_response(
                    ERROR_INTERNAL_ERROR,
                    "Internal error occurred",
                    details={"error": "Target accounts table not configured"},
                ),
            )

        result = target_accounts_table.get_item(Key={"accountId": account_id})
        if "Item" not in result:
            return response(
                404,
                {
                    "error": "NOT_FOUND",
                    "message": f"Target account {account_id} not found",
                },
            )

        return response(200, result["Item"])

    except Exception as e:
        print(f"Error getting target account: {e}")
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def create_target_account(body: Dict) -> Dict:
    """Create a new target account configuration"""
    try:
        target_accounts_table = get_target_accounts_table()
        if not target_accounts_table:
            return response(
                500,
                error_response(
                    ERROR_INTERNAL_ERROR,
                    "Internal error occurred",
                    details={"error": "Target accounts table not configured"},
                ),
            )

        if not body:
            return response(
                400,
                {
                    "error": "MISSING_BODY",
                    "message": "Request body is required",
                },
            )

        account_id = body.get("accountId")
        if not account_id:
            return response(
                400,
                {"error": "MISSING_FIELD", "message": "accountId is required"},
            )

        # Validate account ID format
        if not re.match(r"^\d{12}$", account_id):
            return response(
                400,
                {
                    "error": "INVALID_FORMAT",
                    "message": "accountId must be 12 digits",
                },
            )

        # Check if account already exists
        try:
            existing = target_accounts_table.get_item(Key={"accountId": account_id})
            if "Item" in existing:
                return response(
                    400,
                    {
                        "error": "ACCOUNT_EXISTS",
                        "message": f"Target account {account_id} already exists",
                    },
                )
        except Exception as e:
            print(f"Error checking existing account: {e}")

        # Get current account info
        current_account_id = get_current_account_id()
        account_name = body.get("accountName", "")
        role_arn = body.get("roleArn", "")

        # Determine if this is the same account as the solution
        is_current_account = account_id == current_account_id

        # Wizard validation logic
        if is_current_account:
            # Same account - cross-account role should NOT be provided
            if role_arn:
                return response(
                    400,
                    {
                        "error": "SAME_ACCOUNT_NO_ROLE_NEEDED",
                        "message": "Cross-account role is not needed when adding the same account where this solution is deployed. Please leave the role field empty.",  # noqa: E501
                    },
                )
            print(f"Same account deployment detected for {account_id} - no cross-account role required")
        else:
            # Different account - construct role ARN if not provided
            if not role_arn:
                # Import account utilities for standardized role naming
                from shared.account_utils import construct_role_arn

                role_arn = construct_role_arn(account_id)
                print(f"Constructed standardized role ARN for {account_id}: {role_arn}")
            else:
                # Validate provided role ARN format
                if not role_arn.startswith("arn:aws:iam::"):
                    return response(
                        400,
                        {
                            "error": "INVALID_ROLE_ARN",
                            "message": "Cross-account role ARN must be a valid IAM role ARN (arn:aws:iam::account:role/role-name)",  # noqa: E501
                        },
                    )
                print(f"Using provided role ARN for {account_id}: {role_arn}")

        # If no name provided, try to get account name
        if not account_name:
            if is_current_account:
                account_name = get_account_name(account_id) or f"Account {account_id}"
            else:
                account_name = f"Account {account_id}"

        # Check if this is the first account (for default setting)
        is_first_account = False
        try:
            scan_result = get_target_accounts_table().scan(Select="COUNT")
            total_accounts = scan_result.get("Count", 0)
            is_first_account = total_accounts == 0
        except Exception as e:
            print(f"Error checking account count: {e}")

        now = datetime.now(timezone.utc).isoformat() + "Z"
        account_item = {
            "accountId": account_id,
            "accountName": account_name,
            "status": "active",
            "isCurrentAccount": is_current_account,
            "createdAt": now,
            "lastValidated": now,
            "createdBy": "user",
        }

        # Add role ARN if provided
        if role_arn:
            account_item["roleArn"] = role_arn

        # Add external ID for cross-account role assumption
        external_id = body.get("externalId", "drs-orchestration-cross-account")
        if not is_current_account:
            account_item["externalId"] = external_id

        # Store in DynamoDB
        get_target_accounts_table().put_item(Item=account_item)

        success_message = f"Target account {account_id} added successfully"
        if is_current_account:
            success_message += " (same account - no cross-account role needed)"
        if is_first_account:
            success_message += " and set as default account"

        print(f"Created target account: {account_id} " f"(isCurrentAccount: {is_current_account})")

        # Note: Automatic staging account discovery was removed in refactor.
        # Staging accounts are now discovered via the query-handler's
        # handle_discover_staging_accounts function which uses extended source servers.

        response_data = {
            **account_item,
            "message": success_message,
        }

        return response(201, response_data)

    except Exception as e:
        print(f"Error creating target account: {e}")
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def update_target_account(account_id: str, body: Dict) -> Dict:
    """Update target account configuration"""
    try:
        target_accounts_table = get_target_accounts_table()
        if not target_accounts_table:
            return response(
                500,
                error_response(
                    ERROR_INTERNAL_ERROR,
                    "Internal error occurred",
                    details={"error": "Target accounts table not configured"},
                ),
            )

        if not body:
            return response(
                400,
                {
                    "error": "MISSING_BODY",
                    "message": "Request body is required",
                },
            )

        # Check if account exists
        result = target_accounts_table.get_item(Key={"accountId": account_id})
        if "Item" not in result:
            return response(
                404,
                {
                    "error": "NOT_FOUND",
                    "message": f"Target account {account_id} not found",
                },
            )

        # Build update expression
        set_clauses = ["lastValidated = :lastValidated"]
        remove_clauses = []
        expression_values = {":lastValidated": datetime.now(timezone.utc).isoformat() + "Z"}
        expression_names = {}

        # Update account name if provided
        if "accountName" in body:
            account_name = body["accountName"]
            if account_name:
                set_clauses.append("accountName = :accountName")
                expression_values[":accountName"] = account_name
            else:
                remove_clauses.append("accountName")

        # Update status if provided
        if "status" in body and body["status"] in ["active", "inactive"]:
            set_clauses.append("#status = :status")
            expression_values[":status"] = body["status"]
            expression_names["#status"] = "status"

        # Update role ARN if provided
        if "roleArn" in body:
            role_arn = body["roleArn"]
            if role_arn:
                set_clauses.append("roleArn = :roleArn")
                expression_values[":roleArn"] = role_arn
            else:
                remove_clauses.append("roleArn")

        # Build the final update expression
        update_expression = "SET " + ", ".join(set_clauses)
        if remove_clauses:
            update_expression += " REMOVE " + ", ".join(remove_clauses)

        # Perform update
        update_args = {
            "Key": {"accountId": account_id},
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_values,
            "ReturnValues": "ALL_NEW",
        }

        if expression_names:
            update_args["ExpressionAttributeNames"] = expression_names

        result = get_target_accounts_table().update_item(**update_args)
        updated_account = result["Attributes"]

        print(f"Updated target account: {account_id}")
        return response(200, updated_account)

    except Exception as e:
        print(f"Error updating target account: {e}")
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def delete_target_account(account_id: str) -> Dict:
    """Delete target account configuration"""
    try:
        target_accounts_table = get_target_accounts_table()
        if not target_accounts_table:
            return response(
                500,
                error_response(
                    ERROR_INTERNAL_ERROR,
                    "Internal error occurred",
                    details={"error": "Target accounts table not configured"},
                ),
            )

        # Check if account exists
        result = target_accounts_table.get_item(Key={"accountId": account_id})
        if "Item" not in result:
            return response(
                404,
                {
                    "error": "NOT_FOUND",
                    "message": f"Target account {account_id} not found",
                },
            )

        # Delete the account
        get_target_accounts_table().delete_item(Key={"accountId": account_id})

        current_account_id = get_current_account_id()
        is_current = account_id == current_account_id
        account_type = "current account" if is_current else "target account"

        print(f"Deleted {account_type}: {account_id}")
        return response(
            200,
            {"message": f"Target account {account_id} deleted successfully"},
        )

    except Exception as e:
        print(f"Error deleting target account: {e}")
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


# ============================================================================
# Staging Account Management Functions
# ============================================================================


def handle_add_staging_account(body: Dict) -> Dict:
    """
    Add staging account to target account configuration.

    Validates staging account structure, checks for duplicates, and updates
    the Target Accounts table with the new staging account.

    Input:
    {
        "targetAccountId": "111122223333",
        "stagingAccount": {
            "accountId": "444455556666",
            "accountName": "STAGING_01",
            "roleArn": "arn:aws:iam::444455556666:role/DRSOrchestrationRole-test",
            "externalId": "drs-orchestration-test-444455556666"
        }
    }

    Output:
    {
        "success": true,
        "message": "Added staging account STAGING_01",
        "stagingAccounts": [...]
    }

    Requirements: 1.6, 7.1
    """
    try:
        # Import staging account models
        from shared.staging_account_models import add_staging_account

        if not body:
            return response(
                400,
                {
                    "error": "MISSING_BODY",
                    "message": "Request body is required",
                },
            )

        target_account_id = body.get("targetAccountId")
        staging_account = body.get("stagingAccount")

        # Validate required fields
        if not target_account_id:
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "targetAccountId is required",
                },
            )

        if not staging_account:
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "stagingAccount is required",
                },
            )

        # Validate target account ID format
        if not re.match(r"^\d{12}$", target_account_id):
            return response(
                400,
                {
                    "error": "INVALID_FORMAT",
                    "message": "targetAccountId must be 12 digits",
                },
            )

        # Add staging account using shared module
        result = add_staging_account(target_account_id, staging_account, added_by="user")

        print(f"Added staging account {staging_account.get('accountId')} " f"to target account {target_account_id}")

        return response(200, result)

    except ValueError as e:
        # Validation errors from staging_account_models
        error_msg = str(e)
        if "not found" in error_msg.lower():
            return response(
                404,
                {
                    "error": "TARGET_ACCOUNT_NOT_FOUND",
                    "message": error_msg,
                },
            )
        elif "already exists" in error_msg.lower():
            return response(
                409,
                {
                    "error": "STAGING_ACCOUNT_EXISTS",
                    "message": error_msg,
                },
            )
        else:
            return response(
                400,
                {
                    "error": "VALIDATION_ERROR",
                    "message": error_msg,
                },
            )

    except Exception as e:
        print(f"Error adding staging account: {e}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def handle_remove_staging_account(body: Dict) -> Dict:
    """
    Remove staging account from target account configuration.

    Input:
    {
        "targetAccountId": "111122223333",
        "stagingAccountId": "444455556666"
    }

    Output:
    {
        "success": true,
        "message": "Removed staging account 444455556666",
        "stagingAccounts": [...]
    }

    Requirements: 2.2, 7.2
    """
    try:
        # Import staging account models
        from shared.staging_account_models import remove_staging_account

        if not body:
            return response(
                400,
                {
                    "error": "MISSING_BODY",
                    "message": "Request body is required",
                },
            )

        target_account_id = body.get("targetAccountId")
        staging_account_id = body.get("stagingAccountId")

        # Validate required fields
        if not target_account_id:
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "targetAccountId is required",
                },
            )

        if not staging_account_id:
            return response(
                400,
                {
                    "error": "MISSING_FIELD",
                    "message": "stagingAccountId is required",
                },
            )

        # Validate account ID formats
        if not re.match(r"^\d{12}$", target_account_id):
            return response(
                400,
                {
                    "error": "INVALID_FORMAT",
                    "message": "targetAccountId must be 12 digits",
                },
            )

        if not re.match(r"^\d{12}$", staging_account_id):
            return response(
                400,
                {
                    "error": "INVALID_FORMAT",
                    "message": "stagingAccountId must be 12 digits",
                },
            )

        # Remove staging account using shared module
        result = remove_staging_account(target_account_id, staging_account_id)

        print(f"Removed staging account {staging_account_id} " f"from target account {target_account_id}")

        return response(200, result)

    except ValueError as e:
        # Validation errors from staging_account_models
        error_msg = str(e)
        if "not found" in error_msg.lower():
            return response(
                404,
                {
                    "error": "NOT_FOUND",
                    "message": error_msg,
                },
            )
        else:
            return response(
                400,
                {
                    "error": "VALIDATION_ERROR",
                    "message": error_msg,
                },
            )

    except Exception as e:
        print(f"Error removing staging account: {e}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


def handle_sync_single_account(target_account_id: str) -> Dict:
    """
    Sync staging accounts for a single target account (on-demand).

    This is the same operation that runs automatically every 5 minutes via EventBridge,
    but triggered on-demand by the user clicking the refresh button in the dashboard.

    Workflow:
    1. Get target account from DynamoDB
    2. Discover staging accounts from DRS extended source servers
    3. Compare with current staging accounts
    4. Update DynamoDB if changes detected
    5. Return sync result

    Input:
    - target_account_id: Target account ID (from path parameter)

    Output:
    {
        "success": true,
        "message": "Staging accounts synced successfully",
        "targetAccountId": "111122223333",
        "stagingAccounts": [...],
        "changes": {
            "added": ["777788889999"],
            "removed": ["444455556666"]
        }
    }

    Requirements: 7.3

    NOTE: Automatic staging account discovery was removed in refactoring.
    Staging accounts must now be added manually via the API.
    """
    try:
        # Validate account ID format
        if not re.match(r"^\d{12}$", target_account_id):
            return response(
                400,
                {
                    "error": "INVALID_FORMAT",
                    "message": "targetAccountId must be 12 digits",
                },
            )

        # Get target account from DynamoDB
        account_response = get_target_accounts_table().get_item(Key={"accountId": target_account_id})

        if "Item" not in account_response:
            return response(
                404,
                {
                    "error": "TARGET_ACCOUNT_NOT_FOUND",
                    "message": f"Target account {target_account_id} not found",
                },
            )

        account = account_response["Item"]

        # Return current staging accounts (no auto-discovery)
        current_staging = account.get("stagingAccounts", [])

        return response(
            200,
            {
                "success": True,
                "message": "Staging accounts retrieved (auto-discovery disabled)",
                "targetAccountId": target_account_id,
                "stagingAccounts": current_staging,
            },
        )

    except Exception as e:
        print(f"Error getting staging accounts for {target_account_id}: {e}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": str(e)},
            ),
        )


# ============================================================================
# Configuration Import/Export Functions
# ============================================================================

# Schema version for configuration import/export
SCHEMA_VERSION = "1.1"
SUPPORTED_SCHEMA_VERSIONS = ["1.0", "1.1"]


def export_configuration(query_params: Dict) -> Dict:
    """
    Export all Protection Groups and Recovery Plans to JSON format.

    Creates portable JSON backup of entire DR orchestration configuration including
    Protection Groups, Recovery Plans, and metadata. Resolves Protection Group IDs
    to names for portability across environments. Supports backup, migration, and
    disaster recovery of DR configuration itself.

    ## Use Cases

    ### 1. Configuration Backup
    ```bash
    curl -X GET https://api.example.com/configuration/export \
      -H "Authorization: Bearer $TOKEN" \
      > dr-config-backup-2026-01-25.json
    ```

    ### 2. Environment Migration
    ```bash
    # Export from dev
    curl -X GET https://api-dev.example.com/configuration/export \
      > dev-config.json

    # Import to prod (after review)
    curl -X POST https://api-prod.example.com/configuration/import \
      -d @dev-config.json
    ```

    ### 3. Disaster Recovery of DR Config
    ```python
    # Regular automated backup
    config = export_configuration({})
    s3_client.put_object(
        Bucket='dr-config-backups',
        Key=f'backup-{date}.json',
        Body=json.dumps(config)
    )
    ```

    ## Integration Points

    ### API Gateway Invocation
    ```bash
    curl -X GET https://api.example.com/configuration/export \
      -H "Authorization: Bearer $TOKEN"
    ```

    ### Direct Lambda Invocation
    ```python
    lambda_client.invoke(
        FunctionName='data-management-handler',
        Payload=json.dumps({
            "operation": "export_configuration"
        })
    )
    ```

    ## Behavior

    ### Export Process
    1. Scan all Protection Groups from DynamoDB
    2. Scan all Recovery Plans from DynamoDB
    3. Build PG ID → Name mapping
    4. Transform Protection Groups (remove internal fields)
    5. Transform Recovery Plans (resolve PG IDs to names)
    6. Add metadata (schema version, timestamp, source region)
    7. Return complete configuration as JSON

    ### Protection Group Transformation
    - Removes internal fields (groupId, createdTime, updatedTime)
    - Preserves: groupName, description, region, accountId, owner
    - Includes server selection (sourceServerIds OR serverSelectionTags)
    - Includes launchConfig if present
    - Includes per-server configurations (schema v1.1+):
      - sourceServerId: DRS source server ID
      - instanceId: EC2 instance ID (optional)
      - instanceName: Server name (optional)
      - tags: Server tags (optional)
      - useGroupDefaults: Whether server uses group defaults
      - launchTemplate: Per-server launch template overrides

    ### Recovery Plan Transformation
    - Resolves protectionGroupId → protectionGroupName in waves
    - Removes protectionGroupId (uses name for portability)
    - Preserves: planName, description, waves
    - Warns about orphaned PG references

    ### Portability Features
    - Uses names instead of IDs for cross-environment compatibility
    - Includes schema version for compatibility checking
    - Includes source region for reference
    - Timestamp for backup tracking

    ## Returns

    Dict with complete configuration:
        - metadata: Export metadata (schemaVersion, exportedAt, sourceRegion)
        - protectionGroups: List of Protection Groups
        - recoveryPlans: List of Recovery Plans

    ## Example Response

    ```json
    {
      "metadata": {
        "schemaVersion": "1.1",
        "exportedAt": "2026-01-27T22:42:00Z",
        "sourceRegion": "us-east-1",
        "exportedBy": "api",
        "protectionGroupCount": 1,
        "recoveryPlanCount": 1,
        "serverCount": 2,
        "serversWithCustomConfig": 1,
        "orphanedReferences": 0
      },
      "protectionGroups": [
        {
          "groupName": "Production Web Servers",
          "description": "Web tier servers",
          "region": "us-east-1",
          "accountId": "123456789012",
          "owner": "user@example.com",
          "serverSelectionTags": {
            "Environment": "production",
            "Tier": "web"
          },
          "launchConfig": {
            "subnetId": "subnet-abc123",
            "securityGroupIds": ["sg-xyz789"],
            "instanceType": "c6a.large"
          },
          "servers": [
            {
              "sourceServerId": "s-57eae3bdae1f0179b",
              "instanceId": "i-0123456789abcdef0",
              "instanceName": "web-server-01",
              "useGroupDefaults": false,
              "launchTemplate": {
                "staticPrivateIp": "10.0.1.100",
                "instanceType": "c6a.xlarge"
              }
            },
            {
              "sourceServerId": "s-5d4ac077408e03d02",
              "instanceId": "i-0123456789abcdef1",
              "instanceName": "web-server-02",
              "useGroupDefaults": true,
              "launchTemplate": {
                "staticPrivateIp": "10.0.1.101"
              }
            }
          ]
        }
      ],
      "recoveryPlans": [
        {
          "planName": "Production DR Plan",
          "description": "Full production failover",
          "waves": [
            {
              "waveName": "Database Wave",
              "waveNumber": 0,
              "protectionGroupName": "Production Database Servers",
              "pauseBeforeWave": false
            },
            {
              "waveName": "Application Wave",
              "waveNumber": 1,
              "protectionGroupName": "Production App Servers",
              "pauseBeforeWave": true
            }
          ]
        }
      ]
    }
    ```

    ## Performance

    ### Execution Time
    - Small deployment (< 10 PGs, < 5 RPs): 1-3 seconds
    - Medium deployment (10-50 PGs, 5-20 RPs): 3-10 seconds
    - Large deployment (50+ PGs, 20+ RPs): 10-30 seconds

    ### API Calls
    - DynamoDB Scan: 1 for Protection Groups (paginated)
    - DynamoDB Scan: 1 for Recovery Plans (paginated)

    ## Error Handling

    ### Orphaned Protection Group References
    If Recovery Plan references non-existent Protection Group:
    - Logs warning with PG ID
    - Keeps PG ID in export (instead of name)
    - Continues export (non-blocking)
    - Includes orphaned count in logs

    ### Export Failure (500)
    ```json
    {
      "error": "Failed to export configuration",
      "details": "DynamoDB scan failed: ..."
    }
    ```

    ## Schema Version

    Current: `1.1`

    Schema includes:
    - Protection Group structure
    - Recovery Plan structure
    - Wave structure with PG name references
    - Per-server launch template configurations (v1.1+)

    ### Schema v1.1 Changes
    - Added `servers` array to Protection Groups
    - Added metadata counts: protectionGroupCount, recoveryPlanCount,
      serverCount, serversWithCustomConfig, orphanedReferences
    - Per-server fields: sourceServerId, instanceId, instanceName, tags,
      useGroupDefaults, launchTemplate
    - Backward compatible with v1.0 (servers array is optional)

    ## Related Functions

    - `import_configuration()`: Import configuration from JSON
    - `get_protection_groups()`: Get Protection Groups
    - `get_recovery_plans()`: Get Recovery Plans

    Export all Protection Groups and Recovery Plans to JSON format.

    Returns complete configuration with metadata for backup/migration.
    """
    try:
        import datetime

        # Get source region from environment or default
        source_region = os.environ.get("AWS_REGION", "us-east-1")

        # Scan all Protection Groups
        pg_result = get_protection_groups_table().scan()
        protection_groups = pg_result.get("Items", [])
        while "LastEvaluatedKey" in pg_result:
            pg_result = get_protection_groups_table().scan(ExclusiveStartKey=pg_result["LastEvaluatedKey"])
            protection_groups.extend(pg_result.get("Items", []))

        # Scan all Recovery Plans
        rp_result = get_recovery_plans_table().scan()
        recovery_plans = rp_result.get("Items", [])
        while "LastEvaluatedKey" in rp_result:
            rp_result = get_recovery_plans_table().scan(ExclusiveStartKey=rp_result["LastEvaluatedKey"])
            recovery_plans.extend(rp_result.get("Items", []))

        # Build PG ID -> Name mapping for wave export
        pg_id_to_name = {pg.get("groupId", ""): pg.get("groupName", "") for pg in protection_groups}

        # Transform Protection Groups for export (exclude internal fields)
        exported_pgs = []
        servers_with_custom_config = 0
        total_server_count = 0

        for pg in protection_groups:
            exported_pg = {
                "groupName": pg.get("groupName", ""),
                "description": pg.get("description", ""),
                "region": pg.get("region", ""),
                "accountId": pg.get("accountId", ""),
                "assumeRoleName": pg.get("assumeRoleName", ""),
            }
            # Include server selection method (mutually exclusive)
            if pg.get("sourceServerIds"):
                exported_pg["sourceServerIds"] = pg["sourceServerIds"]
            if pg.get("serverSelectionTags"):
                exported_pg["serverSelectionTags"] = pg["serverSelectionTags"]
            # Include launchConfig if present
            if pg.get("launchConfig"):
                exported_pg["launchConfig"] = pg["launchConfig"]

            # Include per-server configurations (schema v1.1)
            if pg.get("servers"):
                exported_servers = []
                for server in pg["servers"]:
                    exported_server = {
                        "sourceServerId": server.get("sourceServerId", ""),
                        "useGroupDefaults": server.get("useGroupDefaults", True),
                    }
                    # Include optional fields if present
                    if server.get("instanceId"):
                        exported_server["instanceId"] = server["instanceId"]
                    if server.get("instanceName"):
                        exported_server["instanceName"] = server["instanceName"]
                    if server.get("tags"):
                        exported_server["tags"] = server["tags"]
                    if server.get("launchTemplate"):
                        exported_server["launchTemplate"] = server["launchTemplate"]

                    exported_servers.append(exported_server)
                    total_server_count += 1

                    # Count servers with custom configurations
                    if not server.get("useGroupDefaults", True) or (
                        server.get("launchTemplate") and any(v is not None for v in server["launchTemplate"].values())
                    ):
                        servers_with_custom_config += 1

                exported_pg["servers"] = exported_servers

            exported_pgs.append(exported_pg)

        # Transform Recovery Plans for export (resolve PG IDs to names)
        exported_rps = []
        orphaned_pg_ids = []
        for rp in recovery_plans:
            # Transform waves to include ProtectionGroupName
            exported_waves = []
            for wave in rp.get("waves", []):
                exported_wave = dict(wave)
                pg_id = wave.get("protectionGroupId", "")
                if pg_id:
                    if pg_id in pg_id_to_name:
                        exported_wave["protectionGroupName"] = pg_id_to_name[pg_id]
                        # Remove ID - use name only for portability
                        exported_wave.pop("protectionGroupId", None)
                    else:
                        # Keep ID if name can't be resolved (orphaned
                        # reference)
                        orphaned_pg_ids.append(pg_id)
                        print(f"Warning: PG ID '{pg_id}' not found - keeping ID in export")
                # Remove internal ID arrays — export uses names only
                exported_wave.pop("protectionGroupIds", None)
                exported_waves.append(exported_wave)

            exported_rp = {
                "planName": rp.get("planName", ""),
                "description": rp.get("description", ""),
                "accountId": rp.get("accountId", ""),
                "assumeRoleName": rp.get("assumeRoleName", ""),
                "notificationEmail": rp.get("notificationEmail", ""),
                "waves": exported_waves,
            }
            exported_rps.append(exported_rp)

        if orphaned_pg_ids:
            print(f"Export contains {len(orphaned_pg_ids)} orphaned PG references")

        # Build export payload — clean, customer-facing format
        export_data = {
            "exportedAt": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
            "sourceRegion": source_region,
            "protectionGroups": exported_pgs,
            "recoveryPlans": exported_rps,
        }

        return response(200, export_data)

    except Exception as e:
        print(f"Error exporting configuration: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": f"Failed to export configuration: {str(e)}"},
            ),
        )


def import_configuration(body: Dict) -> Dict:
    """
    Import Protection Groups and Recovery Plans from JSON configuration.

    ## Purpose

    Restores DR configuration from exported JSON, enabling:
    - Disaster recovery of orchestration configuration
    - Migration between environments (dev → test → prod)
    - Configuration version control and rollback
    - Multi-region deployment synchronization

    ## Use Cases

    ### Disaster Recovery
    Restore orchestration configuration after control plane failure:
    ```bash
    # Export configuration before disaster
    aws lambda invoke --function-name data-management-handler \
      --payload '{"action":"export_configuration"}' \
      response.json

    # After disaster, restore configuration
    aws lambda invoke --function-name data-management-handler \
      --payload file://backup-config.json \
      response.json
    ```

    ### Environment Migration
    Promote configuration from dev to production:
    ```bash
    # Export from dev
    curl -X POST https://api-dev.example.com/configuration/export \
      -H "Authorization: Bearer $TOKEN" > dev-config.json

    # Import to prod (with dry run first)
    curl -X POST https://api-prod.example.com/configuration/import \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"dryRun": true, "config": '$(cat dev-config.json)'}'

    # Apply if validation passes
    curl -X POST https://api-prod.example.com/configuration/import \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d @dev-config.json
    ```

    ### Configuration Rollback
    Revert to previous configuration version:
    ```bash
    # Import historical backup
    aws lambda invoke --function-name data-management-handler \
      --payload file://config-backup-2026-01-20.json \
      response.json
    ```

    ## Integration Points

    ### API Gateway
    - **Endpoint**: `POST /configuration/import`
    - **Method**: `import_configuration`
    - **Auth**: Cognito User Pool (admin role required)

    ### Direct Lambda Invocation
    ```bash
    aws lambda invoke \
      --function-name data-management-handler \
      --payload '{
        "action": "import_configuration",
        "dryRun": false,
        "config": {
          "metadata": {
            "schemaVersion": "1.0",
            "exportedAt": "2026-01-25T10:00:00Z",
            "sourceRegion": "us-east-1"
          },
          "protectionGroups": [...],
          "recoveryPlans": [...]
        }
      }' \
      response.json
    ```

    ### EventBridge Integration
    Automated configuration sync across regions:
    ```json
    {
      "source": "dr.orchestration",
      "detail-type": "Configuration Export Complete",
      "detail": {
        "exportData": {...},
        "targetRegions": ["us-west-2", "eu-west-1"]
      }
    }
    ```

    ## Behavior

    ### Non-Destructive Import
    Import is **additive-only** and never modifies or deletes existing resources:

    1. **Conflict Detection**: Checks for name collisions with existing resources
    2. **Skip Existing**: Resources with matching names are skipped (not updated)
    3. **Create New**: Only creates resources that don't exist
    4. **Preserve State**: Never modifies existing Protection Groups or Recovery Plans

    ### Validation Steps

    1. **Schema Version Check**: Validates `schemaVersion` matches supported versions
    2. **Protection Group Validation**:
       - Name uniqueness (case-insensitive)
       - Server ID existence in DRS
       - Server availability (not in active executions)
       - Server assignment conflicts (not in other PGs)
    3. **Recovery Plan Validation**:
       - Name uniqueness (case-insensitive)
       - Protection Group references exist
       - Wave number uniqueness within plan

    ### Dependency Resolution

    Protection Groups are imported before Recovery Plans to satisfy dependencies:

    ```
    Import Order:
    1. Protection Groups → DynamoDB
    2. Build PG name→ID mapping
    3. Recovery Plans → Resolve PG names to IDs → DynamoDB
    ```

    ### Dry Run Mode

    Set `dryRun: true` to validate without creating resources:
    - Performs all validation checks
    - Simulates import process
    - Returns detailed results without database writes
    - Use before production imports to verify configuration

    ## Request Format

    ### Standard Format
    ```json
    {
      "action": "import_configuration",
      "dryRun": false,
      "config": {
        "metadata": {
          "schemaVersion": "1.0",
          "exportedAt": "2026-01-25T10:00:00Z",
          "sourceRegion": "us-east-1"
        },
        "protectionGroups": [
          {
            "groupName": "Production Database Servers",
            "description": "Critical database tier",
            "region": "us-east-1",
            "accountId": "123456789012",
            "owner": "dba-team",
            "sourceServerIds": ["s-1234567890abcdef0", "s-abcdef1234567890"],
            "launchConfig": {
              "launchDisposition": "STARTED",
              "targetInstanceTypeRightSizingMethod": "BASIC"
            }
          }
        ],
        "recoveryPlans": [
          {
            "planName": "Production DR Plan",
            "description": "Full production failover",
            "waves": [
              {
                "waveName": "Database Wave",
                "waveNumber": 0,
                "protectionGroupName": "Production Database Servers",
                "pauseBeforeWave": false
              }
            ]
          }
        ]
      }
    }
    ```

    ### Direct Format (config at root)
    ```json
    {
      "dryRun": true,
      "metadata": {...},
      "protectionGroups": [...],
      "recoveryPlans": [...]
    }
    ```

    ## Response Format

    ### Success (200)
    ```json
    {
      "success": true,
      "dryRun": false,
      "correlationId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "summary": {
        "protectionGroups": {
          "created": 2,
          "skipped": 1,
          "failed": 0
        },
        "recoveryPlans": {
          "created": 1,
          "skipped": 0,
          "failed": 0
        }
      },
      "created": [
        {
          "type": "ProtectionGroup",
          "name": "Production Database Servers",
          "status": "created",
          "details": {
            "groupId": "pg-abc123",
            "serverCount": 2
          }
        }
      ],
      "skipped": [
        {
          "type": "ProtectionGroup",
          "name": "Existing Group",
          "status": "skipped",
          "reason": "Protection Group already exists"
        }
      ],
      "failed": []
    }
    ```

    ### Validation Failure (400)
    ```json
    {
      "error": "Unsupported schema version: 2.0",
      "supportedVersions": ["1.0"]
    }
    ```

    ### Import Failure (500)
    ```json
    {
      "error": "Failed to import configuration",
      "details": "DynamoDB PutItem failed: ..."
    }
    ```

    ## Performance

    ### Execution Time
    - Small import (< 10 PGs, < 5 RPs): 2-5 seconds
    - Medium import (10-50 PGs, 5-20 RPs): 5-15 seconds
    - Large import (50+ PGs, 20+ RPs): 15-45 seconds
    - Dry run: 50% faster (no database writes)

    ### API Calls
    - DynamoDB Scan: 2 (Protection Groups, Recovery Plans)
    - DynamoDB Query: 8 (active executions by status)
    - DynamoDB PutItem: 1 per created resource
    - DRS DescribeSourceServers: 1 per Protection Group (server validation)

    ### Throttling
    - DynamoDB: 1000 WCU per table (burst to 3000)
    - DRS API: 10 TPS (shared across all DRS operations)
    - Batch imports: Use exponential backoff for retries

    ## Error Handling

    ### Schema Version Mismatch (400)
    ```json
    {
      "error": "Unsupported schema version: 2.0",
      "supportedVersions": ["1.0"]
    }
    ```
    **Resolution**: Export configuration again with current version

    ### Protection Group Name Conflict (200 with skip)
    ```json
    {
      "skipped": [{
        "type": "ProtectionGroup",
        "name": "Duplicate Name",
        "reason": "Protection Group already exists"
      }]
    }
    ```
    **Resolution**: Rename conflicting resource or delete existing resource

    ### Server Not Found (200 with failure)
    ```json
    {
      "failed": [{
        "type": "ProtectionGroup",
        "name": "Invalid Servers",
        "reason": "Server s-invalid123 not found in DRS"
      }]
    }
    ```
    **Resolution**: Verify server IDs exist in target region

    ### Server In Active Execution (200 with failure)
    ```json
    {
      "failed": [{
        "type": "ProtectionGroup",
        "name": "Locked Servers",
        "reason": "Server s-abc123 in active execution exec-xyz789"
      }]
    }
    ```
    **Resolution**: Wait for execution to complete or cancel execution

    ### Recovery Plan Missing Protection Group (200 with failure)
    ```json
    {
      "failed": [{
        "type": "RecoveryPlan",
        "name": "Incomplete Plan",
        "reason": "Protection Group 'Missing PG' not found"
      }]
    }
    ```
    **Resolution**: Import Protection Group first or fix reference

    ## Schema Version

    Current: `1.0`

    Supported versions: `["1.0"]`

    Schema includes:
    - Protection Group structure with server selection
    - Recovery Plan structure with wave dependencies
    - Launch configuration settings
    - Metadata for tracking and validation

    ## Related Functions

    - `export_configuration()`: Export configuration to JSON
    - `create_protection_group()`: Create individual Protection Group
    - `create_recovery_plan()`: Create individual Recovery Plan
    - `get_protection_groups()`: List Protection Groups
    - `get_recovery_plans()`: List Recovery Plans

    Non-destructive, additive-only operation:
    - Skips resources that already exist (by name)
    - Validates server existence and conflicts
    - Supports dry_run mode for validation without changes

    Returns detailed results with created, skipped, and failed resources.
    """
    try:
        correlation_id = str(uuid.uuid4())
        print(f"[{correlation_id}] Starting configuration import")

        # Extract parameters
        dry_run = body.get("dryRun", False)
        config = body.get("config", body)  # Support both wrapped and direct format

        # Get import data
        import_pgs = config.get("protectionGroups", [])
        import_rps = config.get("recoveryPlans", [])

        # Load existing data for conflict detection
        existing_pgs = _get_existing_protection_groups()
        existing_rps = _get_existing_recovery_plans()
        active_execution_servers = _get_active_execution_servers()

        # Track results
        results = {
            "success": True,
            "dryRun": dry_run,
            "correlationId": correlation_id,
            "summary": {
                "protectionGroups": {"created": 0, "skipped": 0, "failed": 0},
                "recoveryPlans": {"created": 0, "skipped": 0, "failed": 0},
            },
            "created": [],
            "skipped": [],
            "failed": [],
        }

        # Track which PGs were successfully created/exist for RP dependency
        # resolution
        available_pg_names = set(existing_pgs.keys())
        failed_pg_names = set()

        # Build name->ID mapping from existing PGs (case-insensitive keys)
        pg_name_to_id = {name.lower(): pg.get("groupId", "") for name, pg in existing_pgs.items()}

        # Process Protection Groups first (RPs depend on them)
        for pg in import_pgs:
            pg_result = _process_protection_group_import(
                pg,
                existing_pgs,
                active_execution_servers,
                dry_run,
                correlation_id,
            )

            if pg_result["status"] == "created":
                results["created"].append(pg_result)
                results["summary"]["protectionGroups"]["created"] += 1
                pg_name = pg.get("groupName", "")
                available_pg_names.add(pg_name)
                # Add newly created PG to name->ID mapping
                new_pg_id = pg_result.get("details", {}).get("groupId", "")
                if new_pg_id:
                    pg_name_to_id[pg_name.lower()] = new_pg_id
            elif pg_result["status"] == "skipped":
                results["skipped"].append(pg_result)
                results["summary"]["protectionGroups"]["skipped"] += 1
            else:  # failed
                results["failed"].append(pg_result)
                results["summary"]["protectionGroups"]["failed"] += 1
                failed_pg_names.add(pg.get("groupName", ""))
                results["success"] = False

        # Process Recovery Plans (with name->ID resolution)
        for rp in import_rps:
            rp_result = _process_recovery_plan_import(
                rp,
                existing_rps,
                available_pg_names,
                failed_pg_names,
                pg_name_to_id,
                dry_run,
                correlation_id,
            )

            if rp_result["status"] == "created":
                results["created"].append(rp_result)
                results["summary"]["recoveryPlans"]["created"] += 1
            elif rp_result["status"] == "skipped":
                results["skipped"].append(rp_result)
                results["summary"]["recoveryPlans"]["skipped"] += 1
            else:  # failed
                results["failed"].append(rp_result)
                results["summary"]["recoveryPlans"]["failed"] += 1
                results["success"] = False

        print(f"[{correlation_id}] Import complete: {results['summary']}")
        return response(200, results)

    except Exception as e:
        print(f"Error importing configuration: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            error_response(
                ERROR_INTERNAL_ERROR,
                "Internal error occurred",
                details={"error": f"Failed to import configuration: {str(e)}"},
            ),
        )


def _get_existing_protection_groups() -> Dict[str, Dict]:
    """Get all existing Protection Groups indexed by name (case-insensitive)"""
    result = get_protection_groups_table().scan()
    pgs = result.get("Items", [])
    while "LastEvaluatedKey" in result:
        result = get_protection_groups_table().scan(ExclusiveStartKey=result["LastEvaluatedKey"])
        pgs.extend(result.get("Items", []))
    return {pg.get("groupName", "").lower(): pg for pg in pgs}


def _get_existing_recovery_plans() -> Dict[str, Dict]:
    """Get all existing Recovery Plans indexed by name (case-insensitive)"""
    result = get_recovery_plans_table().scan()
    rps = result.get("Items", [])
    while "LastEvaluatedKey" in result:
        result = get_recovery_plans_table().scan(ExclusiveStartKey=result["LastEvaluatedKey"])
        rps.extend(result.get("Items", []))
    return {rp.get("planName", "").lower(): rp for rp in rps}


def _get_active_execution_servers() -> Dict[str, Dict]:
    """Get servers involved in active executions with execution details"""
    # Query executions with active statuses
    active_statuses = [
        "PENDING",
        "POLLING",
        "INITIATED",
        "LAUNCHING",
        "STARTED",
        "IN_PROGRESS",
        "RUNNING",
        "PAUSED",
    ]

    servers = {}
    for status in active_statuses:
        try:
            result = get_executions_table().query(
                IndexName="StatusIndex",
                KeyConditionExpression="#s = :status",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":status": status},
            )
            for exec_item in result.get("Items", []):
                exec_id = exec_item.get("executionId", "")
                plan_name = exec_item.get("planName", "")
                exec_status = exec_item.get("status", "")
                # Get servers from waves
                for wave in exec_item.get("waves", []):
                    for server in wave.get("servers", []):
                        server_id = server.get("sourceServerId", "")
                        if server_id:
                            servers[server_id] = {
                                "executionId": exec_id,
                                "planName": plan_name,
                                "status": exec_status,
                            }
        except Exception as e:
            print(f"Warning: Could not query executions for status {status}: {e}")

    return servers


def _get_all_assigned_servers() -> Dict[str, str]:
    """Get all servers assigned to any Protection Group"""
    result = get_protection_groups_table().scan()
    pgs = result.get("Items", [])
    while "LastEvaluatedKey" in result:
        result = get_protection_groups_table().scan(ExclusiveStartKey=result["LastEvaluatedKey"])
        pgs.extend(result.get("Items", []))

    assigned = {}
    for pg in pgs:
        pg_name = pg.get("groupName", "")
        for server_id in pg.get("sourceServerIds", []):
            assigned[server_id] = pg_name
    return assigned


def _validate_and_resolve_server_configs(
    servers_config: list,
    source_server_ids: list,
    region: str,
    group_launch_config: Dict,
    correlation_id: str,
) -> Dict[str, Any]:
    """
    Validate and resolve per-server configurations for import.

    This function performs comprehensive validation:
    1. Resolves EC2 instance IDs to DRS source server IDs
    2. Validates AWS-approved fields only
    3. Validates static IP addresses
    4. Checks for duplicate IPs within same subnet
    5. Supports partial import (skips invalid entries with warnings)

    Args:
        servers_config: List of server configurations from manifest
        source_server_ids: List of source server IDs from protection group
        region: AWS region for validation
        group_launch_config: Group-level launch config for defaults
        correlation_id: Correlation ID for logging

    Returns:
        Dict with validation result:
        {
            "valid": bool,
            "resolvedServers": list (validated server configs),
            "warnings": list (skipped servers with reasons),
            "error": str (if validation failed),
            "details": dict (error details)
        }

    Validates: Requirements 10.2, 10.3, 10.4, 10.5, 10.5.2, 10.5.3
    """
    from shared.launch_config_validation import (
        validate_aws_approved_fields,
        validate_static_ip,
    )

    resolved_servers = []
    warnings = []
    seen_ips = {}  # Track IPs per subnet for duplicate detection

    # Create DRS client for instance ID resolution
    try:
        drs_client = boto3.client("drs", region_name=region)
    except Exception as e:
        return {
            "valid": False,
            "error": "DRS_CLIENT_ERROR",
            "message": f"Failed to create DRS client: {str(e)}",
            "details": {"region": region},
        }

    for idx, server in enumerate(servers_config):
        server_id = server.get("sourceServerId")
        instance_id = server.get("instanceId")
        instance_name = server.get("instanceName", "")

        # Step 1: Resolve EC2 instance ID to DRS source server ID
        if not server_id and instance_id:
            print(f"[{correlation_id}] Resolving instance ID {instance_id} " f"to DRS source server ID")
            try:
                # Query DRS for source servers
                drs_response = drs_client.describe_source_servers()
                found = False

                for drs_server in drs_response.get("items", []):
                    # Check if source properties match instance ID
                    source_props = drs_server.get("sourceProperties", {})
                    if source_props.get("lastUpdatedDateTime"):
                        # Get identification hints
                        identification = source_props.get("identificationHints", {})
                        aws_instance_id = identification.get("awsInstanceID")

                        if aws_instance_id == instance_id:
                            server_id = drs_server.get("sourceServerID")
                            found = True
                            print(f"[{correlation_id}] Resolved {instance_id} " f"to {server_id}")
                            break

                if not found:
                    warnings.append(
                        {
                            "serverIndex": idx,
                            "instanceId": instance_id,
                            "instanceName": instance_name,
                            "reason": "INSTANCE_NOT_IN_DRS",
                            "message": f"EC2 instance {instance_id} not " f"found in DRS. Server will be skipped.",
                        }
                    )
                    print(f"[{correlation_id}] Warning: Instance " f"{instance_id} not found in DRS, skipping")
                    continue

            except Exception as e:
                warnings.append(
                    {
                        "serverIndex": idx,
                        "instanceId": instance_id,
                        "instanceName": instance_name,
                        "reason": "DRS_QUERY_ERROR",
                        "message": f"Failed to resolve instance ID: " f"{str(e)}",
                    }
                )
                print(f"[{correlation_id}] Warning: Failed to resolve " f"{instance_id}: {e}")
                continue

        # Validate server_id is present
        if not server_id:
            warnings.append(
                {
                    "serverIndex": idx,
                    "instanceName": instance_name,
                    "reason": "MISSING_SERVER_ID",
                    "message": "Neither sourceServerId nor instanceId " "provided. Server will be skipped.",
                }
            )
            continue

        # Validate server_id is in protection group's source server list
        if source_server_ids and server_id not in source_server_ids:
            warnings.append(
                {
                    "serverIndex": idx,
                    "sourceServerId": server_id,
                    "instanceName": instance_name,
                    "reason": "SERVER_NOT_IN_GROUP",
                    "message": f"Server {server_id} is not in protection "
                    f"group's sourceServerIds list. Server will be "
                    "skipped.",
                }
            )
            continue

        # Step 2: Validate launch template configuration
        launch_template = server.get("launchTemplate", {})

        if launch_template:
            # Validate AWS-approved fields only
            field_validation = validate_aws_approved_fields(launch_template)

            if not field_validation["valid"]:
                warnings.append(
                    {
                        "serverIndex": idx,
                        "sourceServerId": server_id,
                        "instanceName": instance_name,
                        "reason": field_validation.get("error"),
                        "message": field_validation.get("message"),
                        "blockedFields": field_validation.get("blockedFields", []),
                    }
                )
                print(f"[{correlation_id}] Warning: Server {server_id} has " f"invalid fields, skipping")
                continue

            # Step 3: Validate static IP if present
            static_ip = launch_template.get("staticPrivateIp")

            if static_ip:
                # Determine effective subnet
                subnet_id = launch_template.get("subnetId") or group_launch_config.get("subnetId")

                if not subnet_id:
                    warnings.append(
                        {
                            "serverIndex": idx,
                            "sourceServerId": server_id,
                            "instanceName": instance_name,
                            "reason": "MISSING_SUBNET",
                            "message": "Static IP configured but no subnet "
                            "specified in server config or group defaults. "
                            "Server will be skipped.",
                        }
                    )
                    continue

                # Validate static IP
                ip_validation = validate_static_ip(static_ip, subnet_id, region)

                if not ip_validation["valid"]:
                    warnings.append(
                        {
                            "serverIndex": idx,
                            "sourceServerId": server_id,
                            "instanceName": instance_name,
                            "staticPrivateIp": static_ip,
                            "subnetId": subnet_id,
                            "reason": ip_validation.get("error"),
                            "message": ip_validation.get("message"),
                        }
                    )
                    print(f"[{correlation_id}] Warning: Server {server_id} " f"has invalid IP {static_ip}, skipping")
                    continue

                # Step 4: Check for duplicate IPs in same subnet
                subnet_key = subnet_id
                if subnet_key not in seen_ips:
                    seen_ips[subnet_key] = {}

                if static_ip in seen_ips[subnet_key]:
                    conflict_server = seen_ips[subnet_key][static_ip]
                    warnings.append(
                        {
                            "serverIndex": idx,
                            "sourceServerId": server_id,
                            "instanceName": instance_name,
                            "staticPrivateIp": static_ip,
                            "subnetId": subnet_id,
                            "reason": "DUPLICATE_IP",
                            "message": f"IP {static_ip} is already "
                            f"configured for server "
                            f"{conflict_server['sourceServerId']} in "
                            f"subnet {subnet_id}. Server will be skipped.",
                            "conflictingServer": conflict_server,
                        }
                    )
                    print(f"[{correlation_id}] Warning: Duplicate IP " f"{static_ip} for server {server_id}, skipping")
                    continue

                # Track this IP
                seen_ips[subnet_key][static_ip] = {
                    "sourceServerId": server_id,
                    "instanceName": instance_name,
                }

        # Server passed all validations - add to resolved list
        resolved_server = {
            "sourceServerId": server_id,
            "useGroupDefaults": server.get("useGroupDefaults", True),
        }

        # Include optional fields if present
        if instance_id:
            resolved_server["instanceId"] = instance_id
        if instance_name:
            resolved_server["instanceName"] = instance_name
        if server.get("tags"):
            resolved_server["tags"] = server["tags"]
        if launch_template:
            resolved_server["launchTemplate"] = launch_template

        resolved_servers.append(resolved_server)
        print(f"[{correlation_id}] Validated server config for {server_id}")

    # Return validation result
    return {
        "valid": True,
        "resolvedServers": resolved_servers,
        "warnings": warnings,
        "message": f"Validated {len(resolved_servers)} server " f"configurations, {len(warnings)} skipped",
    }


def generate_manifest_validation_report(manifest: Dict, correlation_id: str = None) -> Dict[str, Any]:
    """
    Generate comprehensive validation report for JSON manifest.

    This function performs complete manifest validation and generates a
    detailed report covering:
    1. Schema structure validation
    2. Protection group validation (servers, launch configs)
    3. Per-server configuration validation (static IPs, AWS resources)
    4. Recovery plan validation
    5. Cross-reference validation (PG references in RPs)

    Args:
        manifest: JSON manifest to validate
        correlation_id: Optional correlation ID for logging

    Returns:
        Dict containing validation report:
        {
            "valid": bool,
            "summary": {
                "totalProtectionGroups": int,
                "totalRecoveryPlans": int,
                "totalServers": int,
                "serversWithCustomConfig": int,
                "validationErrors": int,
                "validationWarnings": int
            },
            "schemaValidation": {...},
            "protectionGroupValidation": [...],
            "recoveryPlanValidation": [...],
            "errors": [...],
            "warnings": [...]
        }

    Validates: Requirements 10.2, 10.5
    """

    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    print(f"[{correlation_id}] Starting manifest validation")

    report = {
        "valid": True,
        "correlationId": correlation_id,
        "summary": {
            "totalProtectionGroups": 0,
            "totalRecoveryPlans": 0,
            "totalServers": 0,
            "serversWithCustomConfig": 0,
            "validationErrors": 0,
            "validationWarnings": 0,
        },
        "schemaValidation": {"valid": True, "errors": []},
        "protectionGroupValidation": [],
        "recoveryPlanValidation": [],
        "errors": [],
        "warnings": [],
    }

    # Step 1: Validate schema structure
    schema_errors = []

    # Check required fields
    if "metadata" not in manifest:
        schema_errors.append(
            {
                "field": "metadata",
                "error": "MISSING_REQUIRED_FIELD",
                "message": "Manifest must contain 'metadata' field",
            }
        )

    metadata = manifest.get("metadata", {})
    schema_version = metadata.get("schemaVersion")

    if not schema_version:
        schema_errors.append(
            {
                "field": "metadata.schemaVersion",
                "error": "MISSING_SCHEMA_VERSION",
                "message": "Manifest metadata must contain schemaVersion",
            }
        )
    elif schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        schema_errors.append(
            {
                "field": "metadata.schemaVersion",
                "error": "UNSUPPORTED_SCHEMA_VERSION",
                "message": f"Schema version {schema_version} not "
                f"supported. Supported versions: "
                f"{', '.join(SUPPORTED_SCHEMA_VERSIONS)}",
                "value": schema_version,
            }
        )

    if "protectionGroups" not in manifest:
        schema_errors.append(
            {
                "field": "protectionGroups",
                "error": "MISSING_REQUIRED_FIELD",
                "message": "Manifest must contain 'protectionGroups' array",
            }
        )

    if schema_errors:
        report["schemaValidation"]["valid"] = False
        report["schemaValidation"]["errors"] = schema_errors
        report["valid"] = False
        report["summary"]["validationErrors"] += len(schema_errors)
        report["errors"].extend(schema_errors)
        # Cannot continue validation without valid schema
        return report

    # Step 2: Validate protection groups
    protection_groups = manifest.get("protectionGroups", [])
    report["summary"]["totalProtectionGroups"] = len(protection_groups)

    for pg_idx, pg in enumerate(protection_groups):
        pg_validation = _validate_protection_group_manifest(pg, pg_idx, correlation_id)

        report["protectionGroupValidation"].append(pg_validation)

        # Update summary counts
        report["summary"]["totalServers"] += pg_validation.get("serverCount", 0)
        report["summary"]["serversWithCustomConfig"] += pg_validation.get("serversWithCustomConfig", 0)

        # Collect errors and warnings
        if not pg_validation["valid"]:
            report["valid"] = False
            report["summary"]["validationErrors"] += len(pg_validation.get("errors", []))
            report["errors"].extend(pg_validation.get("errors", []))

        report["summary"]["validationWarnings"] += len(pg_validation.get("warnings", []))
        report["warnings"].extend(pg_validation.get("warnings", []))

    # Step 3: Validate recovery plans
    recovery_plans = manifest.get("recoveryPlans", [])
    report["summary"]["totalRecoveryPlans"] = len(recovery_plans)

    # Build PG name set for cross-reference validation
    pg_names = {pg.get("groupName") for pg in protection_groups}

    for rp_idx, rp in enumerate(recovery_plans):
        rp_validation = _validate_recovery_plan_manifest(rp, rp_idx, pg_names, correlation_id)

        report["recoveryPlanValidation"].append(rp_validation)

        # Collect errors and warnings
        if not rp_validation["valid"]:
            report["valid"] = False
            report["summary"]["validationErrors"] += len(rp_validation.get("errors", []))
            report["errors"].extend(rp_validation.get("errors", []))

        report["summary"]["validationWarnings"] += len(rp_validation.get("warnings", []))
        report["warnings"].extend(rp_validation.get("warnings", []))

    print(
        f"[{correlation_id}] Manifest validation complete: "
        f"valid={report['valid']}, "
        f"errors={report['summary']['validationErrors']}, "
        f"warnings={report['summary']['validationWarnings']}"
    )

    return report


def _validate_protection_group_manifest(pg: Dict, pg_idx: int, correlation_id: str) -> Dict[str, Any]:
    """
    Validate a single protection group from manifest.

    Validates:
    - Required fields (groupName, region)
    - Server configurations (if present)
    - Static IP addresses
    - AWS-approved fields
    - Duplicate IP detection

    Args:
        pg: Protection group dict from manifest
        pg_idx: Index in manifest array
        correlation_id: Correlation ID for logging

    Returns:
        Dict with validation result for this protection group
    """

    validation = {
        "valid": True,
        "protectionGroupIndex": pg_idx,
        "groupName": pg.get("groupName", f"<unnamed-{pg_idx}>"),
        "serverCount": 0,
        "serversWithCustomConfig": 0,
        "errors": [],
        "warnings": [],
    }

    # Validate required fields
    if not pg.get("groupName"):
        validation["valid"] = False
        validation["errors"].append(
            {
                "field": f"protectionGroups[{pg_idx}].groupName",
                "error": "MISSING_REQUIRED_FIELD",
                "message": "Protection group must have a groupName",
            }
        )

    if not pg.get("region"):
        validation["valid"] = False
        validation["errors"].append(
            {
                "field": f"protectionGroups[{pg_idx}].region",
                "error": "MISSING_REQUIRED_FIELD",
                "message": "Protection group must have a region",
            }
        )

    # Validate per-server configurations (schema v1.1)
    servers = pg.get("servers", [])
    validation["serverCount"] = len(servers)

    if servers:
        # Track IPs per subnet for duplicate detection
        seen_ips = {}

        for server_idx, server in enumerate(servers):
            server_validation = _validate_server_config_manifest(
                server,
                server_idx,
                pg.get("launchConfig", {}),
                pg.get("region", ""),
                seen_ips,
                correlation_id,
            )

            # Count servers with custom config
            if server.get("launchTemplate"):
                validation["serversWithCustomConfig"] += 1

            # Collect errors and warnings
            if not server_validation["valid"]:
                validation["valid"] = False
                validation["errors"].extend(server_validation.get("errors", []))

            validation["warnings"].extend(server_validation.get("warnings", []))

    return validation


def _validate_server_config_manifest(
    server: Dict,
    server_idx: int,
    group_launch_config: Dict,
    region: str,
    seen_ips: Dict,
    correlation_id: str,
) -> Dict[str, Any]:
    """
    Validate a single server configuration from manifest.

    Validates:
    - Server identification (sourceServerId or instanceId)
    - Launch template configuration
    - AWS-approved fields
    - Static IP format and CIDR range
    - Duplicate IP detection

    Args:
        server: Server dict from manifest
        server_idx: Index in servers array
        group_launch_config: Group-level launch config for defaults
        region: AWS region
        seen_ips: Dict tracking IPs per subnet
        correlation_id: Correlation ID for logging

    Returns:
        Dict with validation result for this server
    """
    from shared.launch_config_validation import (
        validate_aws_approved_fields,
        _validate_ip_format,
    )

    validation = {
        "valid": True,
        "serverIndex": server_idx,
        "sourceServerId": server.get("sourceServerId"),
        "instanceId": server.get("instanceId"),
        "errors": [],
        "warnings": [],
    }

    # Validate server identification
    if not server.get("sourceServerId") and not server.get("instanceId"):
        validation["valid"] = False
        validation["errors"].append(
            {
                "field": f"servers[{server_idx}]",
                "error": "MISSING_SERVER_IDENTIFICATION",
                "message": "Server must have either sourceServerId or " "instanceId",
            }
        )
        return validation

    # Validate launch template configuration
    launch_template = server.get("launchTemplate", {})

    if not launch_template:
        # No custom config - valid
        return validation

    # Validate AWS-approved fields
    field_validation = validate_aws_approved_fields(launch_template)

    if not field_validation["valid"]:
        validation["valid"] = False
        validation["errors"].append(
            {
                "field": f"servers[{server_idx}].launchTemplate",
                "error": field_validation.get("error"),
                "message": field_validation.get("message"),
                "blockedFields": field_validation.get("blockedFields", []),
            }
        )
        return validation

    # Validate static IP if present
    static_ip = launch_template.get("staticPrivateIp")

    if static_ip:
        # Determine effective subnet
        subnet_id = launch_template.get("subnetId") or group_launch_config.get("subnetId")

        if not subnet_id:
            validation["warnings"].append(
                {
                    "field": f"servers[{server_idx}].launchTemplate." "staticPrivateIp",
                    "warning": "MISSING_SUBNET",
                    "message": "Static IP configured but no subnet " "specified. Cannot validate IP without subnet.",
                }
            )
        else:
            # Validate IP format
            format_result = _validate_ip_format(static_ip)

            if not format_result["valid"]:
                validation["valid"] = False
                validation["errors"].append(
                    {
                        "field": f"servers[{server_idx}].launchTemplate." "staticPrivateIp",
                        "error": format_result.get("error"),
                        "message": format_result.get("message"),
                        "value": static_ip,
                    }
                )
            else:
                # Note: We cannot validate CIDR range or availability
                # without AWS API calls. This is a schema-level validation.
                # Full validation happens during import with AWS API access.

                # Check for duplicate IPs in manifest
                subnet_key = subnet_id
                if subnet_key not in seen_ips:
                    seen_ips[subnet_key] = {}

                if static_ip in seen_ips[subnet_key]:
                    conflict_server = seen_ips[subnet_key][static_ip]
                    validation["valid"] = False
                    validation["errors"].append(
                        {
                            "field": f"servers[{server_idx}].launchTemplate." "staticPrivateIp",
                            "error": "DUPLICATE_IP_IN_MANIFEST",
                            "message": f"IP {static_ip} is already "
                            f"configured for server at index "
                            f"{conflict_server['serverIndex']} in "
                            f"subnet {subnet_id}",
                            "conflictingServer": conflict_server,
                        }
                    )
                else:
                    # Track this IP
                    seen_ips[subnet_key][static_ip] = {
                        "serverIndex": server_idx,
                        "sourceServerId": server.get("sourceServerId"),
                        "instanceId": server.get("instanceId"),
                    }

    return validation


def _validate_recovery_plan_manifest(rp: Dict, rp_idx: int, pg_names: set, correlation_id: str) -> Dict[str, Any]:
    """
    Validate a single recovery plan from manifest.

    Validates:
    - Required fields (planName)
    - Wave structure
    - Protection group references

    Args:
        rp: Recovery plan dict from manifest
        rp_idx: Index in manifest array
        pg_names: Set of protection group names for cross-reference
        correlation_id: Correlation ID for logging

    Returns:
        Dict with validation result for this recovery plan
    """
    validation = {
        "valid": True,
        "recoveryPlanIndex": rp_idx,
        "planName": rp.get("planName", f"<unnamed-{rp_idx}>"),
        "errors": [],
        "warnings": [],
    }

    # Validate required fields
    if not rp.get("planName"):
        validation["valid"] = False
        validation["errors"].append(
            {
                "field": f"recoveryPlans[{rp_idx}].planName",
                "error": "MISSING_REQUIRED_FIELD",
                "message": "Recovery plan must have a planName",
            }
        )

    # Validate waves
    waves = rp.get("waves", [])

    if not waves:
        validation["warnings"].append(
            {
                "field": f"recoveryPlans[{rp_idx}].waves",
                "warning": "EMPTY_WAVES",
                "message": "Recovery plan has no waves defined",
            }
        )

    for wave_idx, wave in enumerate(waves):
        # Validate protection group reference
        pg_name = wave.get("protectionGroupName")

        if not pg_name:
            validation["valid"] = False
            validation["errors"].append(
                {
                    "field": f"recoveryPlans[{rp_idx}].waves[{wave_idx}]." "protectionGroupName",
                    "error": "MISSING_REQUIRED_FIELD",
                    "message": "Wave must reference a protectionGroupName",
                }
            )
        elif pg_name not in pg_names:
            validation["valid"] = False
            validation["errors"].append(
                {
                    "field": f"recoveryPlans[{rp_idx}].waves[{wave_idx}]." "protectionGroupName",
                    "error": "PROTECTION_GROUP_NOT_FOUND",
                    "message": f"Protection group '{pg_name}' referenced " "in wave but not found in manifest",
                    "value": pg_name,
                }
            )

    return validation


def _process_protection_group_import(
    pg: Dict,
    existing_pgs: Dict[str, Dict],
    active_execution_servers: Dict[str, Dict],
    dry_run: bool,
    correlation_id: str,
) -> Dict:
    """
    Process a single Protection Group import with per-server config support.

    Supports schema v1.0 (group-level only) and v1.1 (per-server configs).
    Validates per-server configurations including:
    - EC2 instance ID resolution to DRS source server IDs
    - Static IP validation
    - AWS-approved fields enforcement
    - Duplicate IP detection

    Validates: Requirements 10.2, 10.3, 10.4, 10.5, 10.5.2, 10.5.3
    """
    pg_name = pg.get("groupName", "")
    region = pg.get("region", "")

    result = {
        "type": "ProtectionGroup",
        "name": pg_name,
        "status": "failed",
        "reason": "",
        "details": {},
    }

    # Check if already exists
    if pg_name.lower() in existing_pgs:
        result["status"] = "skipped"
        result["reason"] = "ALREADY_EXISTS"
        result["details"] = {"existingGroupId": existing_pgs[pg_name.lower()].get("groupId", "")}
        print(f"[{correlation_id}] Skipping PG '{pg_name}': already exists")
        return result

    # Get server IDs to validate
    source_server_ids = pg.get("sourceServerIds", [])
    server_selection_tags = pg.get("serverSelectionTags", {})

    # NEW: Get per-server configurations (schema v1.1)
    servers_config = pg.get("servers", [])

    # NEW: Validate and resolve per-server configurations
    if servers_config:
        validation_result = _validate_and_resolve_server_configs(
            servers_config,
            source_server_ids,
            region,
            pg.get("launchConfig", {}),
            correlation_id,
        )

        if not validation_result["valid"]:
            result["reason"] = validation_result["error"]
            result["details"] = validation_result.get("details", {})
            print(
                f"[{correlation_id}] Failed PG '{pg_name}': "
                f"per-server config validation failed - "
                f"{validation_result.get('message', '')}"
            )
            return result

        # Update servers_config with resolved source server IDs
        servers_config = validation_result["resolvedServers"]
        result["details"]["perServerConfigCount"] = len(servers_config)
        result["details"]["perServerValidationWarnings"] = validation_result.get("warnings", [])

    # Validate explicit servers
    if source_server_ids:
        # Check servers exist in DRS
        try:
            regional_drs = boto3.client("drs", region_name=region)
            drs_response = regional_drs.describe_source_servers(filters={"sourceServerIDs": source_server_ids})
            found_ids = {s["sourceServerID"] for s in drs_response.get("items", [])}
            missing = set(source_server_ids) - found_ids

            if missing:
                result["reason"] = "SERVER_NOT_FOUND"
                result["details"] = {
                    "missingServerIds": list(missing),
                    "region": region,
                }
                print(f"[{correlation_id}] Failed PG '{pg_name}': missing servers {missing}")
                return result
        except Exception as e:
            if "UninitializedAccountException" in str(e):
                result["reason"] = "DRS_NOT_INITIALIZED"
                result["details"] = {"region": region, "error": str(e)}
            else:
                result["reason"] = "DRS_VALIDATION_ERROR"
                result["details"] = {"region": region, "error": str(e)}
            print(f"[{correlation_id}] Failed PG '{pg_name}': DRS error {e}")
            return result

        # Check for server conflicts with existing PGs
        assigned_servers = _get_all_assigned_servers()
        conflicts = []
        for server_id in source_server_ids:
            if server_id in assigned_servers:
                conflicts.append(
                    {
                        "serverId": server_id,
                        "assignedTo": assigned_servers[server_id],
                    }
                )

        if conflicts:
            result["reason"] = "SERVER_CONFLICT"
            result["details"] = {"conflicts": conflicts}
            print(f"[{correlation_id}] Failed PG '{pg_name}': server conflicts {conflicts}")
            return result

        # Check for conflicts with active executions
        exec_conflicts = []
        for server_id in source_server_ids:
            if server_id in active_execution_servers:
                exec_conflicts.append(
                    {
                        "serverId": server_id,
                        **active_execution_servers[server_id],
                    }
                )

        if exec_conflicts:
            result["reason"] = "ACTIVE_EXECUTION_CONFLICT"
            result["details"] = {"executionConflicts": exec_conflicts}
            print(f"[{correlation_id}] Failed PG '{pg_name}': active execution conflicts")
            return result

    # Validate tag-based selection
    elif server_selection_tags:
        try:
            # Extract account context from protection group data if available
            account_context = None
            if pg.get("accountId"):
                account_context = {
                    "accountId": pg.get("accountId"),
                    "assumeRoleName": pg.get("assumeRoleName"),
                }
            resolved = query_drs_servers_by_tags(region, server_selection_tags, account_context)
            if not resolved:
                result["reason"] = "NO_TAG_MATCHES"
                result["details"] = {
                    "tags": server_selection_tags,
                    "region": region,
                    "matchCount": 0,
                }
                print(f"[{correlation_id}] Failed PG '{pg_name}': no servers match tags")
                return result
        except Exception as e:
            result["reason"] = "TAG_RESOLUTION_ERROR"
            result["details"] = {
                "tags": server_selection_tags,
                "region": region,
                "error": str(e),
            }
            print(f"[{correlation_id}] Failed PG '{pg_name}': tag resolution error {e}")
            return result
    else:
        result["reason"] = "NO_SELECTION_METHOD"
        result["details"] = {"message": "Either SourceServerIds or ServerSelectionTags required"}
        return result

    # Create the Protection Group (unless dry run)
    if not dry_run:
        try:
            group_id = str(uuid.uuid4())
            timestamp = int(time.time())

            item = {
                "groupId": group_id,
                "groupName": pg_name,
                "description": pg.get("description", ""),
                "region": region,
                "accountId": pg.get("accountId", ""),
                "assumeRoleName": pg.get("assumeRoleName", ""),
                "externalId": pg.get("externalId", ""),
                "owner": pg.get("owner", ""),  # FIXED: camelCase
                "createdDate": timestamp,  # FIXED: camelCase
                "lastModifiedDate": timestamp,  # FIXED: camelCase
                "version": 1,  # FIXED: camelCase
            }

            if source_server_ids:
                item["sourceServerIds"] = source_server_ids
                item["serverSelectionTags"] = {}
            elif server_selection_tags:
                item["serverSelectionTags"] = server_selection_tags
                item["sourceServerIds"] = []

            launch_config = pg.get("launchConfig")
            if launch_config:
                item["launchConfig"] = launch_config

            # NEW: Include per-server configurations (schema v1.1)
            if servers_config:
                item["servers"] = servers_config

            get_protection_groups_table().put_item(Item=item)
            result["details"] = {"groupId": group_id}
            print(f"[{correlation_id}] Created PG '{pg_name}' with ID {group_id}")

            # NEW: Log per-server config count
            if servers_config:
                print(f"[{correlation_id}] Imported {len(servers_config)} " f"per-server configurations")

            # Apply launchConfig to DRS servers (same as create/update)
            # NEW: Pass full protection group for per-server config support
            if launch_config or servers_config:
                server_ids_to_apply = []
                if source_server_ids:
                    server_ids_to_apply = source_server_ids
                elif server_selection_tags:
                    # Extract account context from protection group data if
                    # available
                    account_context = None
                    if pg.get("accountId"):
                        account_context = {
                            "accountId": pg.get("accountId"),
                            "assumeRoleName": pg.get("assumeRoleName"),
                        }
                    resolved = query_drs_servers_by_tags(region, server_selection_tags, account_context)
                    server_ids_to_apply = [s.get("sourceServerId") for s in resolved if s.get("sourceServerId")]

                if server_ids_to_apply:
                    try:
                        # Build full protection group dict for per-server config
                        full_pg = {
                            "groupId": group_id,
                            "groupName": pg_name,
                            "accountId": pg.get("accountId", ""),
                            "assumeRoleName": pg.get("assumeRoleName", ""),
                            "region": region,
                            "launchConfig": launch_config or {},
                            "servers": servers_config,
                        }

                        apply_results = apply_launch_config_to_servers(
                            server_ids_to_apply,
                            launch_config or {},
                            region,
                            protection_group=full_pg,
                            protection_group_id=group_id,
                            protection_group_name=pg_name,
                        )
                        # Extract counts safely without referencing sensitive
                        # object methods
                        applied_count = 0
                        failed_count = 0
                        if apply_results and "applied" in apply_results:
                            applied_count = apply_results["applied"]
                        if apply_results and "failed" in apply_results:
                            failed_count = apply_results["failed"]

                        result["details"]["launchConfigApplied"] = applied_count
                        result["details"]["launchConfigFailed"] = failed_count
                        # launchConfig applied successfully - no logging to
                        # prevent sensitive data exposure
                    except Exception as lc_err:
                        print(f"Warning: Failed to apply launchConfig: {type(lc_err).__name__}")
        except Exception as e:
            result["reason"] = "CREATE_ERROR"
            result["details"] = {"error": str(e)}
            print(f"Failed to create PG '{pg_name}': {type(e).__name__}")
            return result
    else:
        result["details"] = {"wouldCreate": True}
        # Warn if account context is missing
        if not pg.get("accountId"):
            result["details"]["accountContextWarning"] = (
                "No accountId in imported data. " "Account context should be set after import."
            )
        print(f"[{correlation_id}] [DRY RUN] Would create PG '{pg_name}'")

    result["status"] = "created"
    result["reason"] = ""
    return result


def _process_recovery_plan_import(
    rp: Dict,
    existing_rps: Dict[str, Dict],
    available_pg_names: set,
    failed_pg_names: set,
    pg_name_to_id: Dict[str, str],
    dry_run: bool,
    correlation_id: str,
) -> Dict:
    """Process a single Recovery Plan import

    Supports both ProtectionGroupId and ProtectionGroupName in waves.
    If ProtectionGroupName is provided, resolves it to ProtectionGroupId.
    """
    plan_name = rp.get("planName", "")
    waves = rp.get("waves", [])

    result = {
        "type": "RecoveryPlan",
        "name": plan_name,
        "status": "failed",
        "reason": "",
        "details": {},
    }

    # Check if already exists
    if plan_name.lower() in existing_rps:
        result["status"] = "skipped"
        result["reason"] = "ALREADY_EXISTS"
        result["details"] = {"existingPlanId": existing_rps[plan_name.lower()].get("planId", "")}
        print(f"[{correlation_id}] Skipping RP '{plan_name}': already exists")
        return result

    # Validate and resolve Protection Group references in waves
    missing_pgs = []
    cascade_failed_pgs = []
    resolved_waves = []

    for wave in waves:
        wave_copy = dict(wave)  # Don't modify original
        pg_id = wave.get("protectionGroupId", "")
        pg_name = wave.get("protectionGroupName", "")

        # Try to resolve ProtectionGroupId
        resolved_pg_id = None
        resolved_pg_name = None

        # Case 1: ProtectionGroupId provided - validate it exists
        if pg_id:
            # Check if this ID maps to a known PG name
            for name, gid in pg_name_to_id.items():
                if gid == pg_id:
                    resolved_pg_id = pg_id
                    resolved_pg_name = name
                    break

            # If ID not found in mapping, it might be an old/invalid ID
            # Try to resolve via protectionGroupName if provided
            if not resolved_pg_id and pg_name:
                pg_name_lower = pg_name.lower()
                if pg_name_lower in pg_name_to_id:
                    resolved_pg_id = pg_name_to_id[pg_name_lower]
                    resolved_pg_name = pg_name
                    print(f"[{correlation_id}] Resolved PG '{pg_name}' from name (ID was stale)")

            # If still not resolved, the ID is invalid
            if not resolved_pg_id:
                # Check if we have a protectionGroupName to fall back to
                if not pg_name:
                    missing_pgs.append(f"ID:{pg_id}")
                    continue

        # Case 2: Only protectionGroupName provided - resolve to ID
        if not resolved_pg_id and pg_name:
            pg_name_lower = pg_name.lower()
            print(f"[{correlation_id}] Resolving PG name '{pg_name}' (lower: '{pg_name_lower}')")
            print(f"[{correlation_id}] Available PG names in mapping: {list(pg_name_to_id.keys())}")

            # Check if PG failed import (cascade failure)
            if pg_name in failed_pg_names:
                cascade_failed_pgs.append(pg_name)
                continue

            # Check if PG exists and get its ID
            if pg_name_lower in pg_name_to_id:
                resolved_pg_id = pg_name_to_id[pg_name_lower]
                resolved_pg_name = pg_name
                print(f"[{correlation_id}] Resolved '{pg_name}' -> ID '{resolved_pg_id}'")
            else:
                print(f"[{correlation_id}] PG name '{pg_name_lower}' NOT FOUND in mapping")
                missing_pgs.append(pg_name)
                continue

        # Case 3: Neither provided
        if not resolved_pg_id and not pg_name and not pg_id:
            # Wave without PG reference - might be valid for some use cases
            resolved_waves.append(wave_copy)
            continue

        # Update wave with resolved ID
        if resolved_pg_id:
            wave_copy["protectionGroupId"] = resolved_pg_id
            if resolved_pg_name:
                wave_copy["protectionGroupName"] = resolved_pg_name
            resolved_waves.append(wave_copy)

    if cascade_failed_pgs:
        result["reason"] = "CASCADE_FAILURE"
        result["details"] = {
            "failedProtectionGroups": list(set(cascade_failed_pgs)),
            "message": "Referenced Protection Groups failed to import",
        }
        print(f"[{correlation_id}] Failed RP '{plan_name}': cascade failure from PGs {cascade_failed_pgs}")
        return result

    if missing_pgs:
        result["reason"] = "MISSING_PROTECTION_GROUP"
        result["details"] = {
            "missingProtectionGroups": list(set(missing_pgs)),
            "message": "Referenced Protection Groups do not exist",
        }
        print(f"[{correlation_id}] Failed RP '{plan_name}': missing PGs {missing_pgs}")
        return result

    # Create the Recovery Plan (unless dry run)
    if not dry_run:
        try:
            plan_id = str(uuid.uuid4())
            timestamp = int(time.time())

            # Validate account context (warn if missing, don't block)
            account_id = rp.get("accountId", "")
            assume_role_name = rp.get("assumeRoleName", "")

            if not account_id:
                print(
                    f"[{correlation_id}] Warning: Recovery Plan "
                    f"'{plan_name}' has no accountId - "
                    f"backward compatible import"
                )
                result["details"]["accountContextWarning"] = (
                    "No accountId in imported data. " "Account context should be set after import."
                )

            item = {
                "planId": plan_id,
                "planName": plan_name,
                "description": rp.get("description", ""),
                "accountId": account_id,
                "assumeRoleName": assume_role_name,
                "waves": resolved_waves,  # Use resolved waves with correct IDs
                "createdDate": timestamp,  # FIXED: camelCase
                "lastModifiedDate": timestamp,  # FIXED: camelCase
                "version": 1,  # FIXED: camelCase
            }

            get_recovery_plans_table().put_item(Item=item)
            result["details"] = {"planId": plan_id}
            print(f"[{correlation_id}] Created RP '{plan_name}' with ID {plan_id}")
        except Exception as e:
            result["reason"] = "CREATE_ERROR"
            result["details"] = {"error": str(e)}
            print(f"[{correlation_id}] Failed to create RP '{plan_name}': {e}")
            return result
    else:
        # Validate account context in dry run too
        account_id = rp.get("accountId", "")
        if not account_id:
            result["details"]["accountContextWarning"] = (
                "No accountId in imported data. " "Account context should be set after import."
            )

        result["details"]["wouldCreate"] = True
        result["details"]["resolvedWaves"] = len(resolved_waves)
        print(f"[{correlation_id}] [DRY RUN] Would create RP '{plan_name}'")

    result["status"] = "created"
    result["reason"] = ""
    return result
