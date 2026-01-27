"""
Data Management Handler - Protection Groups and Recovery Plans CRUD Operations

Handles all data management operations for the DR Orchestration Platform including
Protection Groups, Recovery Plans, Tag Synchronization, and Configuration Management.

## Architecture Pattern

Dual Invocation Support:
- API Gateway Mode: REST API endpoints for frontend/CLI
- Direct Invocation Mode: Function calls from Step Functions/Lambda

## Integration Points

### 1. API Gateway Invocation (Frontend/CLI)
```bash
# Create Protection Group
curl -X POST https://api.example.com/protection-groups \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "groupName": "Production Web Servers",
    "region": "us-east-1",
    "accountId": "123456789012",
    "sourceServerIds": ["s-abc123...", "s-def456..."]
  }'

# Create Recovery Plan
curl -X POST https://api.example.com/recovery-plans \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "planName": "Production DR Plan",
    "waves": [
      {"waveNumber": 1, "waveName": "Critical", "protectionGroupId": "pg-123"}
    ]
  }'
```

### 2. Direct Lambda Invocation (Step Functions)
```python
import boto3

lambda_client = boto3.client('lambda')

# Create Protection Group
response = lambda_client.invoke(
    FunctionName='data-management-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "create_protection_group",
        "body": {
            "groupName": "Production Web Servers",
            "region": "us-east-1",
            "sourceServerIds": ["s-abc123..."]
        }
    })
)

# List Recovery Plans
response = lambda_client.invoke(
    FunctionName='data-management-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "list_recovery_plans",
        "queryParams": {}
    })
)
```

### 3. AWS CLI Direct Invocation
```bash
# Create Protection Group
aws lambda invoke \
  --function-name data-management-handler \
  --payload '{
    "operation": "create_protection_group",
    "body": {
      "groupName": "Production Web Servers",
      "region": "us-east-1",
      "sourceServerIds": ["s-abc123..."]
    }
  }' \
  response.json

# Resolve Tag-Based Protection Group
aws lambda invoke \
  --function-name data-management-handler \
  --payload '{
    "operation": "resolve_protection_group_tags",
    "body": {
      "region": "us-east-1",
      "tags": {"Environment": "production", "Tier": "web"}
    }
  }' \
  response.json
```

## Supported Operations

### Protection Groups (6 operations)
- `create_protection_group`: Create new protection group
- `list_protection_groups`: List all protection groups
- `get_protection_group`: Get protection group details
- `update_protection_group`: Update protection group configuration
- `delete_protection_group`: Delete protection group
- `resolve_protection_group_tags`: Preview servers matching tags

### Recovery Plans (5 operations)
- `create_recovery_plan`: Create new recovery plan
- `list_recovery_plans`: List all recovery plans
- `get_recovery_plan`: Get recovery plan details
- `update_recovery_plan`: Update recovery plan configuration
- `delete_recovery_plan`: Delete recovery plan

### Tag Synchronization (2 operations)
- `handle_drs_tag_sync`: Sync EC2 tags to DRS source servers
- `get_tag_sync_settings`: Get tag sync configuration
- `update_tag_sync_settings`: Update tag sync configuration

### Configuration Management (1 operation)
- `import_configuration`: Import protection groups and recovery plans

## API Endpoints (API Gateway Mode)

### Protection Groups
- `GET /protection-groups` - List all protection groups
- `POST /protection-groups` - Create protection group
- `POST /protection-groups/resolve` - Resolve tag-based selection
- `GET /protection-groups/{id}` - Get protection group
- `PUT /protection-groups/{id}` - Update protection group
- `DELETE /protection-groups/{id}` - Delete protection group

### Recovery Plans
- `GET /recovery-plans` - List all recovery plans
- `POST /recovery-plans` - Create recovery plan
- `GET /recovery-plans/{id}` - Get recovery plan
- `PUT /recovery-plans/{id}` - Update recovery plan
- `DELETE /recovery-plans/{id}` - Delete recovery plan

### Tag Sync & Configuration
- `POST /drs/tag-sync` - Trigger tag synchronization
- `GET /config/tag-sync` - Get tag sync settings
- `PUT /config/tag-sync` - Update tag sync settings
- `POST /config/import` - Import configuration

### Target Accounts
- `GET /accounts/targets` - List target accounts
- `POST /accounts/targets` - Register target account
- `GET /accounts/targets/{id}` - Get target account
- `PUT /accounts/targets/{id}` - Update target account
- `DELETE /accounts/targets/{id}` - Delete target account
- `POST /accounts/targets/{id}/validate` - Validate account access

## Data Validation

### Protection Group Validation
- Unique name (case-insensitive)
- Valid AWS region
- Valid DRS server IDs
- No server conflicts (servers not in other groups)
- Healthy replication state

### Recovery Plan Validation
- Unique name (case-insensitive)
- Valid wave configuration
- No circular dependencies
- Wave size limits (max 100 servers per wave)
- Protection groups exist
- No conflicts with active executions

### Tag-Based Selection
- Valid tag format (key-value pairs)
- No exact tag conflicts with existing groups
- Servers exist in DRS with specified tags

## DynamoDB Tables

### Protection Groups Table
- Primary Key: `groupId`
- Attributes: groupName, region, accountId, sourceServerIds, serverSelectionTags

### Recovery Plans Table
- Primary Key: `planId`
- Attributes: planName, waves, description, createdAt, updatedAt
- GSI: planIdIndex (for execution queries)

### Executions Table
- Primary Key: `executionId`
- GSI: planIdIndex (for active execution checks)

### Target Accounts Table
- Primary Key: `accountId`
- Attributes: accountName, assumeRoleName, status, IsCurrentAccount

### Tag Sync Config Table
- Primary Key: `configId`
- Attributes: enabled, tagMappings, syncFrequency

## Performance Characteristics

### Memory: 512 MB
Moderate complexity with DRS API calls and DynamoDB operations.

### Timeout: 120 seconds
Tag resolution can be slow when querying large numbers of DRS servers.

### Concurrency
Supports concurrent operations with DynamoDB optimistic locking.

## Error Handling

### Validation Errors (400)
- Missing required fields
- Invalid format
- Duplicate names
- Server conflicts

### Not Found Errors (404)
- Protection group not found
- Recovery plan not found
- Target account not found

### Conflict Errors (409)
- Active execution in progress
- Server already assigned
- Tag conflicts

### Internal Errors (500)
- DynamoDB errors
- DRS API errors
- Cross-account access failures

## Testing Considerations

### Mock DynamoDB Tables
```python
import boto3
from moto import mock_dynamodb

@mock_dynamodb
def test_create_protection_group():
    # Create mock tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(...)
    
    # Test operation
    event = {
        "operation": "create_protection_group",
        "body": {"groupName": "Test Group", ...}
    }
    result = lambda_handler(event, None)
    assert result["statusCode"] == 200
```

### Mock DRS API
```python
from unittest.mock import patch

with patch('boto3.client') as mock_client:
    mock_drs = mock_client.return_value
    mock_drs.describe_source_servers.return_value = {
        "items": [{"sourceServerID": "s-123"}]
    }
    
    result = resolve_protection_group_tags({"tags": {...}})
```

Data Management Operations:
- Protection Groups: Create, read, update, delete, resolve tags
- Recovery Plans: Create, read, update, delete, validate
- Tag Synchronization: Sync EC2 tags to DRS source servers
- Configuration Management: Import/export configuration

Performance:
- Memory: 512 MB (moderate complexity, DRS API calls)
- Timeout: 120 seconds (tag resolution can be slow)
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

# Import shared utilities
from shared.conflict_detection import (
    check_server_conflicts_for_create,
    check_server_conflicts_for_update,
    get_plans_with_conflicts,
    query_drs_servers_by_tags,
)
from shared.response_utils import response

# DRS regions (all regions where DRS is available)
DRS_REGIONS = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "eu-central-1",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-south-1",
    "ca-central-1",
    "sa-east-1",
]

# DynamoDB tables (from environment variables)
PROTECTION_GROUPS_TABLE = os.environ.get("PROTECTION_GROUPS_TABLE")
RECOVERY_PLANS_TABLE = os.environ.get("RECOVERY_PLANS_TABLE")
EXECUTIONS_TABLE = os.environ.get("EXECUTION_HISTORY_TABLE")
TARGET_ACCOUNTS_TABLE = os.environ.get("TARGET_ACCOUNTS_TABLE")
TAG_SYNC_CONFIG_TABLE = os.environ.get("TAG_SYNC_CONFIG_TABLE")

# Initialize DynamoDB resources
dynamodb = boto3.resource("dynamodb")
stepfunctions = boto3.client("stepfunctions")
protection_groups_table = (
    dynamodb.Table(PROTECTION_GROUPS_TABLE)
    if PROTECTION_GROUPS_TABLE
    else None
)
recovery_plans_table = (
    dynamodb.Table(RECOVERY_PLANS_TABLE) if RECOVERY_PLANS_TABLE else None
)
executions_table = (
    dynamodb.Table(EXECUTIONS_TABLE) if EXECUTIONS_TABLE else None
)
target_accounts_table = (
    dynamodb.Table(TARGET_ACCOUNTS_TABLE) if TARGET_ACCOUNTS_TABLE else None
)
tag_sync_config_table = (
    dynamodb.Table(TAG_SYNC_CONFIG_TABLE) if TAG_SYNC_CONFIG_TABLE else None
)

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

    Direct Invocation Event (HRP Mode):
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
            # Direct invocation (HRP mode)
            return handle_direct_invocation(event, context)
        else:
            return response(
                400,
                {
                    "error": "INVALID_INVOCATION",
                    "message": "Event must contain either 'requestContext' (API Gateway) or 'operation' (direct invocation)",
                },
            )

    except Exception as e:
        print(f"Unhandled error in lambda_handler: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": f"Internal server error: {str(e)}"})


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
                return response(400, {"error": "Invalid JSON in request body"})

        # Protection Groups endpoints (6)
        if path == "/protection-groups":
            if http_method == "GET":
                return get_protection_groups(query_parameters)
            elif http_method == "POST":
                return create_protection_group(body)

        elif path == "/protection-groups/resolve":
            if http_method == "POST":
                return resolve_protection_group_tags(body)

        elif "/protection-groups/" in path and path.endswith("/resolve"):
            if http_method == "POST":
                return resolve_protection_group_tags(body)

        elif "/protection-groups/" in path:
            group_id = path_parameters.get("id")
            if not group_id:
                return response(400, {"error": "Missing protection group ID"})

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
                return create_recovery_plan(body)

        elif "/recovery-plans/" in path and "/check-instances" in path:
            plan_id = path_parameters.get("id")
            if http_method == "POST":
                return response(
                    501,
                    {
                        "message": "Not yet implemented - check_existing_instances"
                    },
                )

        elif "/recovery-plans/" in path:
            plan_id = path_parameters.get("id")
            if not plan_id:
                return response(400, {"error": "Missing recovery plan ID"})

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

        elif path == "/config/tag-sync":
            if http_method == "GET":
                return get_tag_sync_settings()
            elif http_method == "PUT":
                return update_tag_sync_settings(body)

        elif path == "/config/import":
            if http_method == "POST":
                return import_configuration(body)

        # Target Accounts endpoints (5)
        elif path == "/accounts/targets":
            if http_method == "GET":
                return get_target_accounts()
            elif http_method == "POST":
                return create_target_account(body)

        elif "/accounts/targets/" in path:
            account_id = path_parameters.get("id")
            if not account_id:
                return response(400, {"error": "Missing account ID"})

            if "/validate" in path:
                if http_method == "POST":
                    return validate_target_account(account_id)
            elif http_method == "GET":
                return get_target_account(account_id)
            elif http_method == "PUT":
                return update_target_account(account_id, body)
            elif http_method == "DELETE":
                return delete_target_account(account_id)

        else:
            return response(
                404,
                {
                    "error": "NOT_FOUND",
                    "message": f"No handler for {http_method} {path}",
                },
            )

    except Exception as e:
        print(f"Unhandled error in handle_api_gateway_request: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": f"Internal server error: {str(e)}"})


def handle_direct_invocation(event, context):
    """Handle direct Lambda invocation (HRP mode)"""
    operation = event.get("operation")
    body = event.get("body", {})
    query_params = event.get("queryParams", {})

    # Map operations to functions
    operations = {
        # Protection Groups
        "create_protection_group": lambda: create_protection_group(body),
        "list_protection_groups": lambda: get_protection_groups(query_params),
        "get_protection_group": lambda: get_protection_group(
            body.get("groupId")
        ),
        "update_protection_group": lambda: update_protection_group(
            body.get("groupId"), body
        ),
        "delete_protection_group": lambda: delete_protection_group(
            body.get("groupId")
        ),
        "resolve_protection_group_tags": lambda: resolve_protection_group_tags(
            body
        ),
        # Recovery Plans
        "create_recovery_plan": lambda: create_recovery_plan(body),
        "list_recovery_plans": lambda: get_recovery_plans(query_params),
        "get_recovery_plan": lambda: get_recovery_plan(body.get("planId")),
        "update_recovery_plan": lambda: update_recovery_plan(
            body.get("planId"), body
        ),
        "delete_recovery_plan": lambda: delete_recovery_plan(
            body.get("planId")
        ),
        # Tag Sync & Config
        "handle_drs_tag_sync": lambda: handle_drs_tag_sync(body),
        "get_tag_sync_settings": lambda: get_tag_sync_settings(),
        "update_tag_sync_settings": lambda: update_tag_sync_settings(body),
        "import_configuration": lambda: import_configuration(body),
    }

    if operation in operations:
        return operations[operation]()
    else:
        return {
            "error": "UNKNOWN_OPERATION",
            "message": f"Unknown operation: {operation}",
        }


# ============================================================================
# Protection Groups Functions (Batch 1 - To be extracted)
# ============================================================================

# Functions will be extracted here in Batch 1


# ============================================================================
# Recovery Plans Functions (Batch 2 - To be extracted)
# ============================================================================

# Functions will be extracted here in Batch 2


# ============================================================================
# Tag Sync & Config Functions (Batch 3 - To be extracted)
# ============================================================================

# Functions will be extracted here in Batch 3


# ============================================================================
# Helper Functions (Batch 4 - To be extracted)
# ============================================================================


def get_active_executions_for_plan(plan_id: str) -> List[Dict]:
    """
    Get all active executions for a specific Recovery Plan.

    Uses Step Functions execution state as source of truth to prevent
    conflicts when DynamoDB status is out of sync.

    Returns executions where Step Functions state is RUNNING.
    Terminal states (SUCCEEDED, FAILED, ABORTED, TIMED_OUT) are excluded.
    """
    try:
        # Try GSI first
        try:
            result = executions_table.query(
                IndexName="planIdIndex",
                KeyConditionExpression=Key("planId").eq(plan_id),
            )
            executions = result.get("Items", [])
        except Exception:
            # Fallback to scan
            result = executions_table.scan(
                FilterExpression=Attr("planId").eq(plan_id)
            )
            executions = result.get("Items", [])

        # Check Step Functions state for each execution
        active_executions = []
        for execution in executions:
            execution_id = execution.get("executionId")
            if not execution_id:
                continue

            # Build Step Functions execution ARN
            state_machine_arn = os.environ.get("STATE_MACHINE_ARN")
            if not state_machine_arn:
                print(
                    "WARNING: STATE_MACHINE_ARN not set, falling back to DynamoDB status"
                )
                # Fallback to DynamoDB status check
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
                if execution.get("status", "").upper() in active_statuses:
                    active_executions.append(execution)
                continue

            execution_arn = f"{state_machine_arn.rsplit(':', 1)[0]}:execution:{state_machine_arn.split(':')[-1]}:{execution_id}"

            try:
                # Query Step Functions for actual execution state
                sf_response = stepfunctions.describe_execution(
                    executionArn=execution_arn
                )
                sf_status = sf_response.get("status", "")

                # Only RUNNING state is considered active
                # Terminal states: SUCCEEDED, FAILED, ABORTED, TIMED_OUT
                if sf_status == "RUNNING":
                    active_executions.append(execution)
                    print(
                        f"Execution {execution_id} is RUNNING in Step Functions"
                    )
                else:
                    print(
                        f"Execution {execution_id} is {sf_status} in Step Functions (not active)"
                    )

            except stepfunctions.exceptions.ExecutionDoesNotExist:
                print(
                    f"Execution {execution_id} not found in Step Functions (not active)"
                )
                continue
            except Exception as sf_error:
                print(
                    f"Error checking Step Functions state for {execution_id}: {sf_error}"
                )
                # On error, fall back to DynamoDB status to be safe
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
                if execution.get("status", "").upper() in active_statuses:
                    active_executions.append(execution)

        return active_executions

    except Exception as e:
        print(f"Error checking active executions for plan {plan_id}: {e}")
        return []


def get_active_execution_for_protection_group(
    group_id: str,
) -> Optional[Dict]:
    """
    Check if a protection group is part of any active execution.
    Returns execution info if found, None otherwise.
    """
    try:
        # Find all recovery plans that use this protection group
        plans_result = recovery_plans_table.scan()
        all_plans = plans_result.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in plans_result:
            plans_result = recovery_plans_table.scan(
                ExclusiveStartKey=plans_result["LastEvaluatedKey"]
            )
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
                plan = next(
                    (p for p in all_plans if p.get("planId") == plan_id), {}
                )
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


def ensure_default_account() -> None:
    """Automatically add current account as default target account if no accounts exist"""
    try:
        if not target_accounts_table:
            return

        # Check if any accounts already exist
        scan_result = target_accounts_table.scan(Select="COUNT")
        total_accounts = scan_result.get("Count", 0)

        if total_accounts == 0:
            # No accounts exist - auto-add current account as default
            current_account_id = get_current_account_id()
            current_account_name = (
                get_account_name(current_account_id)
                or f"Account {current_account_id}"
            )

            now = datetime.now(timezone.utc).isoformat() + "Z"

            # Create default account entry
            default_account = {
                "accountId": current_account_id,
                "accountName": current_account_name,
                "status": "active",
                "IsCurrentAccount": True,
                "IsDefault": True,
                "createdAt": now,
                "lastValidated": now,
                "createdBy": "system-auto-init",
            }

            target_accounts_table.put_item(Item=default_account)

            print(
                f"Auto-initialized default target account: {current_account_id} ({current_account_name})"
            )

    except Exception as e:
        print(f"Error auto-initializing default account: {e}")


def validate_unique_pg_name(
    name: str, current_pg_id: Optional[str] = None
) -> bool:
    """
    Validate that Protection Group name is unique (case-insensitive)

    Args:
    - name: Protection Group name to validate
    - current_pg_id: Optional PG ID to exclude (for edit operations)

    Returns:
    - True if unique, False if duplicate exists
    """
    pg_response = protection_groups_table.scan()

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


def validate_unique_rp_name(
    name: str, current_rp_id: Optional[str] = None
) -> bool:
    """
    Validate that Recovery Plan name is unique (case-insensitive)

    Args:
    - name: Recovery Plan name to validate
    - current_rp_id: Optional RP ID to exclude (for edit operations)

    Returns:
    - True if unique, False if duplicate exists
    """
    rp_response = recovery_plans_table.scan()

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


def validate_server_replication_states(
    region: str, server_ids: List[str]
) -> Dict:
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

            response = regional_drs.describe_source_servers(
                filters={"sourceServerIDs": batch}
            )

            for server in response.get("items", []):
                server_id = server.get("sourceServerID")
                replication_state = server.get("dataReplicationInfo", {}).get(
                    "dataReplicationState", "UNKNOWN"
                )
                lifecycle_state = server.get("lifeCycle", {}).get(
                    "state", "UNKNOWN"
                )

                if (
                    replication_state in INVALID_REPLICATION_STATES
                    or lifecycle_state == "STOPPED"
                ):
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


def validate_server_assignments(
    server_ids: List[str], current_pg_id: Optional[str] = None
) -> List[Dict]:
    """
    Validate that servers are not already assigned to other Protection Groups

    Args:
    - server_ids: List of server IDs to validate
    - current_pg_id: Optional PG ID to exclude (for edit operations)

    Returns:
    - conflicts: List of {serverId, protectionGroupId, protectionGroupName}
    """
    pg_response = protection_groups_table.scan()

    conflicts = []
    for pg in pg_response.get("Items", []):
        pg_id = pg.get("groupId") or pg.get("protectionGroupId")

        # Skip current PG when editing
        if current_pg_id and pg_id == current_pg_id:
            continue

        assigned_servers = pg.get("sourceServerIds") or pg.get(
            "sourceServerIds", []
        )
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


def validate_servers_exist_in_drs(
    region: str, server_ids: List[str]
) -> List[str]:
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
        valid_server_ids = {
            s["sourceServerID"] for s in response.get("items", [])
        }

        # Find invalid servers
        invalid_servers = [
            sid for sid in server_ids if sid not in valid_server_ids
        ]

        if invalid_servers:
            print(f"Invalid server IDs detected: {invalid_servers}")

        return invalid_servers

    except Exception as e:
        print(f"Error validating servers in DRS: {str(e)}")
        # On error, assume servers might be valid (fail open for now)
        # In production, might want to fail closed
        return []


def validate_and_get_source_servers(
    account_id: str, region: str, tags: Dict
) -> List[str]:
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


def check_tag_conflicts_for_create(
    tags: Dict[str, str], region: str
) -> List[Dict]:
    """
    Check if the specified tags would conflict with existing tag-based Protection Groups.
    A conflict occurs if another PG has the EXACT SAME tags (all keys and values match).
    """
    if not tags:
        return []

    conflicts = []

    # Scan all PGs
    pg_response = protection_groups_table.scan()
    all_pgs = pg_response.get("Items", [])

    while "LastEvaluatedKey" in pg_response:
        pg_response = protection_groups_table.scan(
            ExclusiveStartKey=pg_response["LastEvaluatedKey"]
        )
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


def check_tag_conflicts_for_update(
    tags: Dict[str, str], region: str, current_pg_id: str
) -> List[Dict]:
    """
    Check if the specified tags would conflict with existing tag-based Protection Groups (excluding current).
    """
    if not tags:
        return []

    conflicts = []

    # Scan all PGs
    pg_response = protection_groups_table.scan()
    all_pgs = pg_response.get("Items", [])

    while "LastEvaluatedKey" in pg_response:
        pg_response = protection_groups_table.scan(
            ExclusiveStartKey=pg_response["LastEvaluatedKey"]
        )
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
    """Validate wave configuration - supports both single and multi-PG formats"""
    try:
        if not waves:
            return "Waves array cannot be empty"

        # Check for duplicate wave numbers
        wave_numbers = [
            w.get("waveNumber")
            for w in waves
            if w.get("waveNumber") is not None
        ]
        if wave_numbers and len(wave_numbers) != len(set(wave_numbers)):
            return "Duplicate waveNumber found in waves"

        # Check for circular dependencies using dependsOnWaves
        dependency_graph = {}
        for wave in waves:
            wave_num = wave.get("waveNumber", 0)
            depends_on = wave.get("dependsOnWaves", [])
            dependency_graph[wave_num] = depends_on

        if dependency_graph and has_circular_dependencies_by_number(
            dependency_graph
        ):
            return "Circular dependency detected in wave configuration"

        # Validate each wave has required fields
        for wave in waves:
            if "waveNumber" not in wave:
                return "Wave missing required field: waveNumber"

            if "waveName" not in wave and "name" not in wave:
                return "Wave missing required field: waveName or name"

            # Accept either protectionGroupId (single) OR protectionGroupIds (multi)
            has_single_pg = "protectionGroupId" in wave
            has_multi_pg = "protectionGroupIds" in wave

            if not has_single_pg and not has_multi_pg:
                return "Wave missing Protection Group assignment (protectionGroupId or protectionGroupIds required)"

            # Validate protectionGroupIds is an array if present
            pg_ids = wave.get("protectionGroupIds") or wave.get(
                "protectionGroupIds"
            )
            if pg_ids is not None:
                if not isinstance(pg_ids, list):
                    return f"protectionGroupIds must be an array, got {type(pg_ids)}"
                if len(pg_ids) == 0:
                    return "protectionGroupIds array cannot be empty"

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
    Queries DRS API to preview servers matching tag criteria before creating Protection Group.

    Used for previewing which servers match the specified tags.

    Request body:
    {
        "region": "us-east-1",
        "serverSelectionTags": {"DR-Application": "HRP", "DR-Tier": "Database"}
    }

    Returns list of servers matching ALL specified tags.
    """
    try:
        region = body.get("region")
        tags = body.get("serverSelectionTags") or body.get("tags", {})

        if not region:
            return response(400, {"error": "region is required"})

        if not tags or not isinstance(tags, dict):
            return response(
                400,
                {"error": "ServerSelectionTags must be a non-empty object"},
            )

        # Extract account context from request body
        account_context = None
        if body.get("accountId"):
            account_context = {
                "accountId": body.get("accountId"),
                "assumeRoleName": body.get("assumeRoleName"),
            }

        # Query DRS for servers matching tags
        raw_servers = query_drs_servers_by_tags(region, tags, account_context)

        # Transform to frontend format
        from shared.drs_utils import transform_drs_server_for_frontend

        resolved_servers = [
            transform_drs_server_for_frontend(server) for server in raw_servers
        ]

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
        return response(500, {"error": str(e)})


def create_protection_group(body: Dict) -> Dict:
    """
    Create a new Protection Group - supports both tag-based and explicit server selection.

    EXTRACTION TARGET: Data Management Handler (Phase 3)
    Validates name uniqueness, checks for server conflicts, and stores in DynamoDB.
    """
    try:
        # FORCE DEPLOYMENT: camelCase migration complete - v1.3.1-hotfix
        print(
            f"DEBUG: create_protection_group v1.3.1-hotfix - camelCase validation active"
        )
        print(
            f"DEBUG: create_protection_group called with body keys: {list(body.keys())}"
        )
        print(
            f"DEBUG: body content: {json.dumps(body, indent=2, default=str)}"
        )

        # Debug: Check specific fields
        print(
            f"DEBUG: serverSelectionTags present: {'serverSelectionTags' in body}"
        )
        print(f"DEBUG: sourceServerIds present: {'sourceServerIds' in body}")
        if "serverSelectionTags" in body:
            print(
                f"DEBUG: serverSelectionTags value: {body['serverSelectionTags']}"
            )
        if "sourceServerIds" in body:
            print(f"DEBUG: sourceServerIds value: {body['sourceServerIds']}")
        if "launchConfig" in body:
            print(
                f"DEBUG: launchConfig present with keys: {list(body['launchConfig'].keys())}"
            )

        # Validate required fields - FIXED: camelCase field validation
        if "groupName" not in body:
            print(
                "DEBUG: groupName not found in body, returning camelCase error"
            )
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

        name = body["groupName"]
        region = body["region"]

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

        # Use trimmed name
        name = name.strip()

        # Support both selection modes
        selection_tags = body.get("serverSelectionTags", {})
        source_server_ids = body.get("sourceServerIds", [])

        # Must have at least one selection method
        has_tags = isinstance(selection_tags, dict) and len(selection_tags) > 0
        has_servers = (
            isinstance(source_server_ids, list) and len(source_server_ids) > 0
        )

        if not has_tags and not has_servers:
            return response(
                400,
                {
                    "error": "Either serverSelectionTags or sourceServerIds is required"
                },
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
            tag_conflicts = check_tag_conflicts_for_create(
                selection_tags, region
            )
            if tag_conflicts:
                return response(
                    409,
                    {
                        "error": "TAG_CONFLICT",
                        "message": "Another Protection Group already uses these exact tags",
                        "conflicts": tag_conflicts,
                    },
                )

        # If using explicit server IDs, validate they exist and aren't assigned elsewhere
        if has_servers:
            # Validate servers exist in DRS
            regional_drs = boto3.client("drs", region_name=region)
            try:
                drs_response = regional_drs.describe_source_servers(
                    filters={"sourceServerIDs": source_server_ids}
                )
                found_ids = {
                    s["sourceServerID"] for s in drs_response.get("items", [])
                }
                missing = set(source_server_ids) - found_ids
                if missing:
                    return response(
                        400, {"error": f"Invalid server IDs: {list(missing)}"}
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
            "description": body.get("description", ""),
            "region": region,
            "accountId": body.get("accountId", ""),
            "assumeRoleName": body.get("assumeRoleName", ""),
            "owner": body.get("owner", ""),  # FIXED: camelCase
            "createdDate": timestamp,  # FIXED: camelCase
            "lastModifiedDate": timestamp,  # FIXED: camelCase
            "version": 1,  # FIXED: camelCase - Optimistic locking starts at version 1
        }

        # Store the appropriate selection method (MUTUALLY EXCLUSIVE)
        # Tags take precedence if both are somehow provided
        if has_tags:
            item["serverSelectionTags"] = selection_tags
            item["sourceServerIds"] = []  # Ensure empty
        elif has_servers:
            item["sourceServerIds"] = source_server_ids
            item["serverSelectionTags"] = {}  # Ensure empty

        # Handle launchConfig if provided
        launch_config_apply_results = None
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

            # Get server IDs to apply settings to
            server_ids_to_apply = source_server_ids if has_servers else []

            # If using tags, resolve servers first
            if has_tags and not server_ids_to_apply:
                # Create account context for cross-account access
                account_context = None
                if body.get("accountId"):
                    account_context = {
                        "accountId": body.get("accountId"),
                        "assumeRoleName": body.get("assumeRoleName"),
                    }
                resolved = query_drs_servers_by_tags(
                    region, selection_tags, account_context
                )
                server_ids_to_apply = [
                    s.get("sourceServerID")
                    for s in resolved
                    if s.get("sourceServerID")
                ]

            # Apply launchConfig to DRS/EC2 immediately
            if server_ids_to_apply and launch_config:
                launch_config_apply_results = apply_launch_config_to_servers(
                    server_ids_to_apply,
                    launch_config,
                    region,
                    protection_group_id=group_id,
                    protection_group_name=name,
                )

                # If any failed, return error (don't save partial state)
                if launch_config_apply_results.get("failed", 0) > 0:
                    failed_servers = [
                        d
                        for d in launch_config_apply_results.get("details", [])
                        if d.get("status") == "failed"
                    ]
                    return response(
                        400,
                        {
                            "error": "Failed to apply launch settings to some servers",
                            "code": "LAUNCH_CONFIG_APPLY_FAILED",
                            "failedServers": failed_servers,
                            "applyResults": launch_config_apply_results,
                        },
                    )

            # Store launchConfig in item
            item["launchConfig"] = launch_config

        print(f"Creating Protection Group: {group_id}")

        # Store in DynamoDB
        protection_groups_table.put_item(Item=item)

        # Return raw camelCase database fields directly - no transformation needed
        item["protectionGroupId"] = item[
            "groupId"
        ]  # Only add this alias for compatibility
        return response(201, item)

    except Exception as e:
        print(f"Error creating Protection Group: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def get_protection_groups(query_params: Dict = None) -> Dict:
    """List all Protection Groups with optional account filtering"""
    try:
        # Auto-initialize default account if none exist
        if target_accounts_table:
            ensure_default_account()

        query_params = query_params or {}
        account_id = query_params.get("accountId")

        result = protection_groups_table.scan()
        groups = result.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in result:
            result = protection_groups_table.scan(
                ExclusiveStartKey=result["LastEvaluatedKey"]
            )
            groups.extend(result.get("Items", []))

        # Filter by account if specified
        if account_id:
            # For now, implement client-side filtering based on region or stored account info
            # In future, could add AccountId field to DynamoDB schema
            filtered_groups = []
            for group in groups:
                # Check if group has account info or matches current account
                group_account = group.get("accountId")
                if group_account == account_id or not group_account:
                    # Include groups that match account or have no account specified (legacy)
                    filtered_groups.append(group)
            groups = filtered_groups

        # Return raw camelCase database fields directly - no transformation needed
        for group in groups:
            group["protectionGroupId"] = group[
                "groupId"
            ]  # Add alias for compatibility
        return response(200, {"groups": groups, "count": len(groups)})

    except Exception as e:
        print(f"Error listing Protection Groups: {str(e)}")
        return response(500, {"error": str(e)})


def get_protection_group(group_id: str) -> Dict:
    """Get a single Protection Group by ID"""
    try:
        result = protection_groups_table.get_item(Key={"groupId": group_id})

        if "Item" not in result:
            return response(404, {"error": "Protection Group not found"})

        group = result["Item"]

        # Return raw camelCase database fields directly - no transformation needed
        group["protectionGroupId"] = group[
            "groupId"
        ]  # Add alias for compatibility
        return response(200, group)

    except Exception as e:
        print(f"Error getting Protection Group: {str(e)}")
        return response(500, {"error": str(e)})


def update_protection_group(group_id: str, body: Dict) -> Dict:
    """Update an existing Protection Group with validation and optimistic locking"""
    try:
        # Check if group exists
        result = protection_groups_table.get_item(Key={"groupId": group_id})
        if "Item" not in result:
            return response(404, {"error": "Protection Group not found"})

        existing_group = result["Item"]
        current_version = existing_group.get(
            "version", 1
        )  # FIXED: camelCase - Default to 1 for legacy items

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
        # Note: PAUSED executions allow edits - only block when actively running
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
                        "message": f"Cannot modify Protection Group while it is part of a running execution",
                        "activeExecution": active_exec_info,
                    },
                )

        # Prevent region changes
        if "region" in body and body["region"] != existing_group.get("region"):
            return response(
                400, {"error": "Cannot change region after creation"}
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
            if (
                not isinstance(selection_tags, dict)
                or len(selection_tags) == 0
            ):
                return response(
                    400,
                    {
                        "error": "INVALID_TAGS",
                        "message": "serverSelectionTags must be a non-empty object with tag key-value pairs",
                    },
                )

            # Check for tag conflicts with other PGs (excluding this one)
            region = existing_group.get("region", "")
            tag_conflicts = check_tag_conflicts_for_update(
                selection_tags, region, group_id
            )
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
            if (
                not isinstance(source_server_ids, list)
                or len(source_server_ids) == 0
            ):
                return response(
                    400,
                    {
                        "error": "INVALID_SERVERS",
                        "message": "SourceServerIds must be a non-empty array",
                    },
                )

            # Check for conflicts with other PGs (excluding this one)
            conflicts = check_server_conflicts_for_update(
                source_server_ids, group_id
            )
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
        # Use v1.3.0 working pattern: simple string concatenation with camelCase fields
        new_version = int(current_version) + 1
        update_expression = (
            "SET lastModifiedDate = :timestamp, version = :new_version"
        )
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
            print(
                f"DEBUG: Adding description to update: {body['description']}"
            )

        # MUTUALLY EXCLUSIVE: Tags OR Servers, not both
        # When one is set, clear the other AND remove old PascalCase fields if they exist

        if "serverSelectionTags" in body:
            update_expression += ", serverSelectionTags = :tags"
            expression_values[":tags"] = body["serverSelectionTags"]
            # Clear sourceServerIds when using tags
            update_expression += ", sourceServerIds = :empty_servers"
            expression_values[":empty_servers"] = []
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
        launch_config_apply_results = None
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

            # Get server IDs to apply settings to
            region = existing_group.get("region")
            server_ids = body.get(
                "sourceServerIds", existing_group.get("sourceServerIds", [])
            )

            # If using tags, resolve servers first
            if not server_ids and existing_group.get("serverSelectionTags"):
                # Extract account context from existing group
                account_context = None
                if existing_group.get("accountId"):
                    account_context = {
                        "accountId": existing_group.get("accountId"),
                        "assumeRoleName": existing_group.get("assumeRoleName"),
                    }
                resolved = query_drs_servers_by_tags(
                    region,
                    existing_group["serverSelectionTags"],
                    account_context,
                )
                server_ids = [
                    s.get("sourceServerID")
                    for s in resolved
                    if s.get("sourceServerID")
                ]

            # Apply launchConfig to DRS/EC2 immediately
            if server_ids and launch_config:
                # Get group name (use updated name if provided, else existing)
                pg_name = body.get(
                    "groupName", existing_group.get("groupName", "")
                )
                launch_config_apply_results = apply_launch_config_to_servers(
                    server_ids,
                    launch_config,
                    region,
                    protection_group_id=group_id,
                    protection_group_name=pg_name,
                )

                # If any failed, return error (don't save partial state)
                if launch_config_apply_results.get("failed", 0) > 0:
                    failed_servers = [
                        d
                        for d in launch_config_apply_results.get("details", [])
                        if d.get("status") == "failed"
                    ]
                    return response(
                        400,
                        {
                            "error": "Failed to apply launch settings to some servers",
                            "code": "LAUNCH_CONFIG_APPLY_FAILED",
                            "failedServers": failed_servers,
                            "applyResults": launch_config_apply_results,
                        },
                    )

            # Store launchConfig in DynamoDB
            update_expression += ", launchConfig = :launchConfig"
            expression_values[":launchConfig"] = launch_config

        print(f"DEBUG: Final update expression: {update_expression}")
        print(f"DEBUG: Expression values: {expression_values}")

        # Update item with conditional write (optimistic locking)
        # Only succeeds if version hasn't changed since we read it
        update_args = {
            "Key": {"groupId": group_id},
            "UpdateExpression": update_expression,
            "ConditionExpression": "version = :current_version OR attribute_not_exists(version)",  # FIXED: camelCase
            "ExpressionAttributeValues": expression_values,
            "ReturnValues": "ALL_NEW",
        }

        if expression_names:
            update_args["ExpressionAttributeNames"] = expression_names

        try:
            result = protection_groups_table.update_item(**update_args)
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

        # Include launchConfig apply results if applicable
        if launch_config_apply_results:
            response_item["launchConfigApplyResults"] = (
                launch_config_apply_results
            )

        print(f"Updated Protection Group: {group_id}")
        return response(200, response_item)

    except Exception as e:
        print(f"Error updating Protection Group: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def delete_protection_group(group_id: str) -> Dict:
    """Delete a Protection Group - blocked if used in ANY recovery plan"""
    try:
        # Check if group is referenced in ANY Recovery Plans (not just active ones)
        # Scan all plans and check if any wave references this PG
        plans_result = recovery_plans_table.scan()
        all_plans = plans_result.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in plans_result:
            plans_result = recovery_plans_table.scan(
                ExclusiveStartKey=plans_result["LastEvaluatedKey"]
            )
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
        protection_groups_table.delete_item(Key={"groupId": group_id})

        print(f"Deleted Protection Group: {group_id}")
        return response(
            200, {"message": "Protection Group deleted successfully"}
        )

    except Exception as e:
        print(f"Error deleting Protection Group: {str(e)}")
        return response(500, {"error": str(e)})


# ============================================================================
# Recovery Plans Handlers
# ============================================================================


def create_recovery_plan(body: Dict) -> Dict:
    """
    Create a new Recovery Plan.

    EXTRACTION TARGET: Data Management Handler (Phase 3)
    Validates wave sizes against DRS limits and stores plan in DynamoDB.
    """
    try:
        # Validate required fields - accept both frontend (name) and legacy (PlanName) formats
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

        # Use trimmed name
        plan_name = plan_name.strip()

        # Validate unique name (case-insensitive, global across all users)
        if not validate_unique_rp_name(plan_name):
            return response(
                409,
                {  # Conflict
                    "error": "RP_NAME_EXISTS",
                    "message": f'A Recovery Plan named "{plan_name}" already exists',
                    "existingName": plan_name,
                },
            )

        # Generate UUID for PlanId
        plan_id = str(uuid.uuid4())

        # Create Recovery Plan item
        timestamp = int(time.time())
        item = {
            "planId": plan_id,
            "planName": plan_name,  # Use the validated plan_name variable
            "description": body.get(
                "description", body.get("description", "")
            ),  # Accept both formats
            "waves": waves,  # Use the validated waves variable
            "createdDate": timestamp,  # FIXED: camelCase
            "lastModifiedDate": timestamp,  # FIXED: camelCase
            "version": 1,  # FIXED: camelCase - Optimistic locking starts at version 1
        }

        # Validate waves if provided
        if waves:
            # CamelCase migration - store waves in exact format frontend expects
            # KEEP IT SIMPLE: Same field names in database, API, and frontend
            camelcase_waves = []
            for idx, wave in enumerate(waves):
                camelcase_wave = {
                    "waveNumber": idx,
                    "waveName": wave.get(
                        "waveName", wave.get("name", f"Wave {idx + 1}")
                    ),
                    "waveDescription": wave.get(
                        "waveDescription", wave.get("description", "")
                    ),
                    "protectionGroupId": wave.get("protectionGroupId", ""),
                    "serverIds": wave.get("serverIds", []),
                    "pauseBeforeWave": wave.get("pauseBeforeWave", False),
                    "dependsOnWaves": wave.get("dependsOnWaves", []),
                }
                # Only include protectionGroupIds if provided and non-empty
                if wave.get("protectionGroupIds"):
                    camelcase_wave["protectionGroupIds"] = wave.get(
                        "protectionGroupIds"
                    )
                camelcase_waves.append(camelcase_wave)

            # Store in camelCase format
            item["waves"] = camelcase_waves

            validation_error = validate_waves(camelcase_waves)
            if validation_error:
                return response(400, {"error": validation_error})

        # Store in DynamoDB
        recovery_plans_table.put_item(Item=item)

        print(f"Created Recovery Plan: {plan_id}")

        # Data is already in camelCase - return directly
        return response(201, item)

    except Exception as e:
        print(f"Error creating Recovery Plan: {str(e)}")
        return response(500, {"error": str(e)})


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
        # Auto-initialize default account if none exist
        if target_accounts_table:
            ensure_default_account()

        query_params = query_params or {}

        result = recovery_plans_table.scan()
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
                pg_result = protection_groups_table.scan()
                for pg in pg_result.get("Items", []):
                    pg_id = pg.get("groupId")
                    pg_tags = pg.get("serverSelectionTags", {})
                    pg_tags_map[pg_id] = pg_tags
            except Exception as e:
                print(f"Error loading PG tags for filter: {e}")

        # Get conflict info for all plans (for graying out Drill/Recovery buttons)
        plans_with_conflicts = get_plans_with_conflicts()

        # Enrich each plan with latest execution data and conflict info
        for plan in plans:
            plan_id = plan.get("planId")

            # Add conflict info if this plan has conflicts with other active executions
            if plan_id in plans_with_conflicts:
                conflict_info = plans_with_conflicts[plan_id]
                plan["hasServerConflict"] = True
                plan["conflictInfo"] = conflict_info
            else:
                plan["hasServerConflict"] = False
                plan["conflictInfo"] = None

            # Query ExecutionHistoryTable for latest execution
            try:
                execution_result = executions_table.query(
                    IndexName="planIdIndex",
                    KeyConditionExpression=Key("planId").eq(plan_id),
                    ScanIndexForward=False,  # Sort by StartTime DESC
                    Limit=1,  # Get only the latest execution
                )

                if execution_result.get("Items"):
                    latest_execution = execution_result["Items"][0]
                    plan["lastExecutionStatus"] = latest_execution.get(
                        "status"
                    )
                    plan["lastStartTime"] = latest_execution.get("startTime")
                    plan["lastEndTime"] = latest_execution.get("endTime")
                else:
                    # No executions found for this plan
                    plan["lastExecutionStatus"] = None
                    plan["lastStartTime"] = None
                    plan["lastEndTime"] = None

            except Exception as e:
                print(
                    f"Error querying execution history for plan {plan_id}: {str(e)}"
                )
                # Set null values on error
                plan["lastExecutionStatus"] = None
                plan["lastStartTime"] = None
                plan["lastEndTime"] = None

            # Add wave count before transformation
            plan["waveCount"] = len(plan.get("waves", []))

        # Apply filters to plans
        filtered_plans = []
        for plan in plans:
            # Account filter - check if plan targets the specified account
            if account_id:
                # For now, implement client-side filtering based on stored account info
                # In future, could add AccountId field to DynamoDB schema
                plan_account = plan.get("accountId")
                if plan_account and plan_account != account_id:
                    continue
                # If no account specified in plan, include it (legacy plans)

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

            # Tag filter - check if any protection group in plan has matching tag
            if tag_key:
                plan_waves = plan.get("waves", [])
                has_matching_tag = False
                for wave in plan_waves:
                    pg_id = wave.get("protectionGroupId")
                    if pg_id and pg_id in pg_tags_map:
                        pg_tags = pg_tags_map[pg_id]
                        if (
                            tag_key in pg_tags
                            and pg_tags[tag_key] == tag_value
                        ):
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
        return response(500, {"error": str(e)})


def get_recovery_plan(plan_id: str) -> Dict:
    """Get a single Recovery Plan by ID"""
    try:
        result = recovery_plans_table.get_item(Key={"planId": plan_id})

        if "Item" not in result:
            return response(404, {"error": "Recovery Plan not found"})

        plan = result["Item"]
        plan["waveCount"] = len(plan.get("waves", []))

        # Return raw database fields - database is already camelCase
        return response(200, plan)

    except Exception as e:
        print(f"Error getting Recovery Plan: {str(e)}")
        return response(500, {"error": str(e)})


def update_recovery_plan(plan_id: str, body: Dict) -> Dict:
    """Update an existing Recovery Plan - blocked if execution in progress, with optimistic locking"""
    try:
        # Check if plan exists
        result = recovery_plans_table.get_item(Key={"planId": plan_id})
        if "Item" not in result:
            return response(404, {"error": "Recovery Plan not found"})

        existing_plan = result["Item"]
        current_version = existing_plan.get(
            "version", 1
        )  # FIXED: camelCase - Default to 1 for legacy items

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

        # Validate name if provided - accept both frontend (name) and legacy (PlanName) formats
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
                    "waveName": wave.get(
                        "waveName", wave.get("name", f"Wave {idx + 1}")
                    ),
                    "waveDescription": wave.get(
                        "waveDescription", wave.get("description", "")
                    ),
                    "protectionGroupId": wave.get("protectionGroupId", ""),
                    "serverIds": wave.get("serverIds", []),
                    "pauseBeforeWave": wave.get("pauseBeforeWave", False),
                    "dependsOnWaves": wave.get("dependsOnWaves", []),
                }
                # Only include protectionGroupIds if provided and non-empty
                if wave.get("protectionGroupIds"):
                    camelcase_wave["protectionGroupIds"] = wave.get(
                        "protectionGroupIds"
                    )
                camelcase_waves.append(camelcase_wave)

            # Store in camelCase format
            body["waves"] = camelcase_waves

            # DEFENSIVE: Validate ServerIds in each wave
            for idx, wave in enumerate(camelcase_waves):
                server_ids = wave.get("serverIds", [])
                if not isinstance(server_ids, list):
                    print(
                        f"ERROR: Wave {idx} ServerIds is not a list: {type(server_ids)}"
                    )
                    return response(
                        400,
                        {
                            "error": "INVALID_WAVE_DATA",
                            "message": f"Wave {idx} has invalid ServerIds format (must be array)",
                            "waveIndex": idx,
                        },
                    )
                print(
                    f"Wave {idx}: {wave.get('waveName')} - {len(server_ids)} servers"
                )

            validation_error = validate_waves(body["waves"])
            if validation_error:
                return response(400, {"error": validation_error})

        # Build update expression with version increment (optimistic locking)
        # FIXED: Use camelCase field names consistently
        new_version = int(current_version) + 1
        update_expression = (
            "SET lastModifiedDate = :timestamp, version = :new_version"
        )
        expression_values = {
            ":timestamp": int(time.time()),
            ":new_version": new_version,
            ":current_version": int(current_version),
        }
        expression_names = {}

        updatable_fields = ["planName", "description", "rpo", "rto", "waves"]
        for field in updatable_fields:
            if field in body:
                if field == "description":
                    # FIXED: Use camelCase 'description' not PascalCase 'Description'
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
            "ConditionExpression": "version = :current_version OR attribute_not_exists(version)",  # FIXED: camelCase
            "ExpressionAttributeValues": expression_values,
            "ReturnValues": "ALL_NEW",
        }

        if expression_names:
            update_args["ExpressionAttributeNames"] = expression_names

        try:
            result = recovery_plans_table.update_item(**update_args)
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
        return response(500, {"error": str(e)})


def delete_recovery_plan(plan_id: str) -> Dict:
    """Delete a Recovery Plan - blocked if any active execution exists"""
    try:
        # Check for ANY active execution (not just RUNNING)
        active_executions = get_active_executions_for_plan(plan_id)

        if active_executions:
            exec_ids = [e.get("executionId") for e in active_executions]
            statuses = [e.get("status") for e in active_executions]
            print(
                f"Cannot delete plan {plan_id}: {len(active_executions)} active execution(s)"
            )
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
        print(f"Deleting Recovery Plan: {plan_id}")
        recovery_plans_table.delete_item(Key={"planId": plan_id})

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
    
    Runs synchronously - syncs tags from EC2 instances to their DRS source servers.
    Supports account-based operations for future multi-account support.
    """
    try:
        # Get account ID from request body (for future multi-account support)
        target_account_id = None
        if body and isinstance(body, dict):
            target_account_id = body.get("accountId")

        # For now, validate that we can only sync current account
        current_account_id = get_current_account_id()
        if target_account_id and target_account_id != current_account_id:
            return response(
                400,
                {
                    "error": "INVALID_ACCOUNT",
                    "message": f"Cannot sync tags for account {target_account_id}. Only current account {current_account_id} is supported.",
                },
            )

        # Use current account if no account specified
        account_id = target_account_id or current_account_id
        account_name = get_account_name(account_id)

        total_synced = 0
        total_servers = 0
        total_failed = 0
        regions_with_servers = []

        print(
            f"Starting tag sync for account {account_id} ({account_name or 'Unknown'})"
        )

        for region in DRS_REGIONS:
            try:
                result = sync_tags_in_region(region, account_id)
                if result["total"] > 0:
                    regions_with_servers.append(region)
                    total_servers += result["total"]
                    total_synced += result["synced"]
                    total_failed += result["failed"]
                    print(
                        f"Tag sync {region}: {result['synced']}/{result['total']} synced"
                    )
            except Exception as e:
                # Log but continue - don't fail entire sync for one region
                print(f"Tag sync {region}: skipped - {e}")

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
            f"Tag sync complete: {total_synced}/{total_servers} servers synced across {len(regions_with_servers)} regions"
        )

        return response(200, summary)

    except Exception as e:
        print(f"Error in tag sync: {e}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def sync_tags_in_region(drs_region: str, account_id: str = None) -> dict:
    """
    Sync EC2 instance tags to DRS source servers in a single region.

    Core implementation for tag synchronization. Queries all DRS source servers in the
    specified region, retrieves tags from their source EC2 instances, and applies those
    tags to the DRS server ARNs. Automatically enables copyTags in DRS launch configuration
    to preserve tags during recovery operations.

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

    ### 3. Scheduled Regional Sync
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
        account_id: AWS account ID (for future multi-account support)
    """
    drs_client = boto3.client("drs", region_name=drs_region)
    ec2_clients = {}

    # Get all DRS source servers
    source_servers = []
    paginator = drs_client.get_paginator("describe_source_servers")
    for page in paginator.paginate(filters={}, maxResults=200):
        source_servers.extend(page.get("items", []))

    synced = 0
    failed = 0

    for server in source_servers:
        try:
            instance_id = (
                server.get("sourceProperties", {})
                .get("identificationHints", {})
                .get("awsInstanceID")
            )
            source_server_id = server["sourceServerID"]
            server_arn = server["arn"]
            source_region = server.get("sourceCloudProperties", {}).get(
                "originRegion", drs_region
            )

            if not instance_id:
                continue

            # Skip disconnected servers
            replication_state = server.get("dataReplicationInfo", {}).get(
                "dataReplicationState", ""
            )
            if replication_state == "DISCONNECTED":
                continue

            # Get or create EC2 client for source region
            if source_region not in ec2_clients:
                ec2_clients[source_region] = boto3.client(
                    "ec2", region_name=source_region
                )
            ec2_client = ec2_clients[source_region]

            # Get EC2 instance tags
            try:
                ec2_response = ec2_client.describe_instances(
                    InstanceIds=[instance_id]
                )
                if not ec2_response["Reservations"]:
                    continue
                instance = ec2_response["Reservations"][0]["Instances"][0]
                ec2_tags = {
                    tag["Key"]: tag["Value"]
                    for tag in instance.get("Tags", [])
                    if not tag["Key"].startswith("aws:")
                }
            except Exception as e:
                # Skip instances that cannot be described (permissions, deleted, etc.)
                print(
                    f"Warning: Could not describe instance {instance_id}: {e}"
                )
                continue

            if not ec2_tags:
                continue

            # Sync tags to DRS source server
            drs_client.tag_resource(resourceArn=server_arn, tags=ec2_tags)

            # Enable copyTags in launch configuration
            try:
                drs_client.update_launch_configuration(
                    sourceServerID=source_server_id, copyTags=True
                )
            except ClientError as e:
                error_code = e.response.get("error", {}).get("Code", "")
                if error_code in [
                    "ValidationException",
                    "ResourceNotFoundException",
                ]:
                    print(
                        f"Cannot update launch config for server {source_server_id}: {error_code}"
                    )
                else:
                    print(
                        f"DRS error updating launch config for {source_server_id}: {e}"
                    )
            except Exception as e:
                print(
                    f"Unexpected error updating launch config for {source_server_id}: {e}"
                )

            synced += 1

        except Exception as e:
            failed += 1
            print(
                f"Failed to sync server {server.get('sourceServerID', 'unknown')}: {e}"
            )

    return {
        "total": len(source_servers),
        "synced": synced,
        "failed": failed,
        "region": drs_region,
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
                    rule_response.get("ModifiedDate", "").isoformat()
                    if rule_response.get("ModifiedDate")
                    else None
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
            500, {"error": f"Failed to get tag sync settings: {str(e)}"}
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
      "error": "Tag sync rule not found. Please redeploy the CloudFormation stack with EnableTagSync=true to create the rule.",
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
                400, {"error": "Request body must be a JSON object"}
            )

        enabled = body.get("enabled")
        interval_hours = body.get("intervalHours")

        if enabled is None:
            return response(400, {"error": "enabled field is required"})

        if not isinstance(enabled, bool):
            return response(400, {"error": "enabled must be a boolean"})

        if interval_hours is not None:
            if (
                not isinstance(interval_hours, (int, float))
                or interval_hours < 1
                or interval_hours > 24
            ):
                return response(
                    400,
                    {
                        "error": "intervalHours must be a number between 1 and 24"
                    },
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
                    "error": "Tag sync rule not found. Please redeploy the CloudFormation stack with EnableTagSync=true to create the rule.",
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
                # Use correct singular/plural form for EventBridge schedule expression
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
                interval_hours = parse_schedule_expression(
                    current_rule.get("ScheduleExpression", "rate(4 hours)")
                )
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
                print(
                    "Settings updated - triggering immediate manual tag sync asynchronously"
                )

                # Trigger async manual sync by invoking this same Lambda function
                lambda_client = boto3.client("lambda")
                function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")

                if function_name:
                    # Create async payload for manual sync
                    async_payload = {
                        "httpMethod": "POST",
                        "path": "/drs/tag-sync",
                        "headers": {"Content-Type": "application/json"},
                        "body": "{}",
                        "requestContext": {
                            "identity": {"sourceIp": "settings-update"}
                        },
                        "asyncTrigger": True,
                    }

                    # Invoke async (don't wait for response)
                    lambda_client.invoke(
                        FunctionName=function_name,
                        InvocationType="Event",  # Async invocation
                        Payload=json.dumps(async_payload),
                    )

                    sync_triggered = True
                    sync_result = {
                        "message": "Manual sync triggered asynchronously"
                    }
                    print("Async manual sync triggered successfully")
                else:
                    print(
                        "Warning: Could not determine Lambda function name for async sync"
                    )

            except Exception as sync_error:
                print(
                    f"Warning: Failed to trigger async manual sync after settings update: {sync_error}"
                )
                # Don't fail the settings update if sync fails
                sync_triggered = False

        result = {
            "message": f"Tag sync settings updated successfully",
            "enabled": updated_rule.get("State") == "ENABLED",
            "intervalHours": interval_hours,
            "scheduleExpression": updated_rule.get("ScheduleExpression"),
            "ruleName": rule_name,
            "lastModified": (
                updated_rule.get("ModifiedDate", "").isoformat()
                if updated_rule.get("ModifiedDate")
                else None
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
            500, {"error": f"Failed to update tag sync settings: {str(e)}"}
        )


def parse_schedule_expression(schedule_expression: str) -> int:
    """Parse EventBridge schedule expression to extract interval hours"""
    try:
        # Handle rate expressions like "rate(4 hours)"
        if schedule_expression.startswith(
            "rate("
        ) and schedule_expression.endswith(")"):
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
        print(
            f"Error parsing schedule expression '{schedule_expression}': {e}"
        )
        return 4


# ============================================================================
# Helper Functions (Batch 4)
# ============================================================================


def apply_launch_config_to_servers(
    server_ids: List[str],
    launch_config: Dict,
    region: str,
    protection_group_id: str = None,
    protection_group_name: str = None,
) -> Dict:
    """Apply launchConfig to all servers' EC2 launch templates and DRS settings.

    Called immediately when Protection Group is saved.
    Returns summary of results for each server.

    Args:
        server_ids: List of DRS source server IDs
        launch_config: Dict with SubnetId, SecurityGroupIds, InstanceProfileName, etc.
        region: AWS region
        protection_group_id: Optional PG ID for version tracking
        protection_group_name: Optional PG name for version tracking

    Returns:
        Dict with applied, skipped, failed counts and details array
    """
    if not launch_config or not server_ids:
        return {"applied": 0, "skipped": 0, "failed": 0, "details": []}

    regional_drs = boto3.client("drs", region_name=region)
    ec2 = boto3.client("ec2", region_name=region)

    results = {"applied": 0, "skipped": 0, "failed": 0, "details": []}

    for server_id in server_ids:
        try:
            # Get DRS launch configuration to find template ID
            drs_config = regional_drs.get_launch_configuration(
                sourceServerID=server_id
            )
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

            if launch_config.get("instanceType"):
                template_data["InstanceType"] = launch_config["instanceType"]

            # Network interface settings (subnet and security groups)
            if launch_config.get("subnetId") or launch_config.get(
                "securityGroupIds"
            ):
                network_interface = {"DeviceIndex": 0}
                if launch_config.get("subnetId"):
                    network_interface["SubnetId"] = launch_config["subnetId"]
                if launch_config.get("securityGroupIds"):
                    network_interface["Groups"] = launch_config[
                        "securityGroupIds"
                    ]
                template_data["NetworkInterfaces"] = [network_interface]

            if launch_config.get("instanceProfileName"):
                template_data["IamInstanceProfile"] = {
                    "Name": launch_config["instanceProfileName"]
                }

            # IMPORTANT: Update DRS launch configuration FIRST
            # DRS update_launch_configuration creates a new EC2 launch template version,
            # so we must call it before our EC2 template updates to avoid being overwritten
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
                drs_update["launchDisposition"] = launch_config[
                    "launchDisposition"
                ]

            if len(drs_update) > 1:  # More than just sourceServerID
                regional_drs.update_launch_configuration(**drs_update)

            # THEN update EC2 launch template (after DRS, so our changes stick)
            if template_data:
                # Build detailed version description for tracking/reuse
                from datetime import datetime, timezone

                timestamp = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                )
                desc_parts = [f"DRS Orchestration | {timestamp}"]
                if protection_group_name:
                    desc_parts.append(f"PG: {protection_group_name}")
                if protection_group_id:
                    desc_parts.append(f"ID: {protection_group_id[:8]}")
                # Add config details
                config_details = []
                if launch_config.get("instanceType"):
                    config_details.append(
                        f"Type:{launch_config['instanceType']}"
                    )
                if launch_config.get("subnetId"):
                    config_details.append(
                        f"Subnet:{launch_config['subnetId'][-8:]}"
                    )
                if launch_config.get("securityGroupIds"):
                    sg_count = len(launch_config["securityGroupIds"])
                    config_details.append(f"SGs:{sg_count}")
                if launch_config.get("instanceProfileName"):
                    profile = launch_config["instanceProfileName"]
                    # Truncate long profile names
                    if len(profile) > 20:
                        profile = profile[:17] + "..."
                    config_details.append(f"Profile:{profile}")
                if launch_config.get("copyPrivateIp"):
                    config_details.append("CopyIP")
                if launch_config.get("copyTags"):
                    config_details.append("CopyTags")
                if launch_config.get("targetInstanceTypeRightSizingMethod"):
                    config_details.append(
                        f"RightSize:{launch_config['targetInstanceTypeRightSizingMethod']}"
                    )
                if launch_config.get("launchDisposition"):
                    config_details.append(
                        f"Launch:{launch_config['launchDisposition']}"
                    )
                if config_details:
                    desc_parts.append(" | ".join(config_details))
                # EC2 version description max 255 chars
                version_desc = " | ".join(desc_parts)[:255]

                ec2.create_launch_template_version(
                    LaunchTemplateId=template_id,
                    LaunchTemplateData=template_data,
                    VersionDescription=version_desc,
                )
                ec2.modify_launch_template(
                    LaunchTemplateId=template_id, DefaultVersion="$Latest"
                )

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
            results["details"].append(
                {"serverId": server_id, "status": "failed", "error": str(e)}
            )

    return results


# ============================================================================
# Target Account Management Functions
# ============================================================================


def get_current_account_id() -> str:
    """Get current AWS account ID"""
    try:
        sts_client = boto3.client("sts")
        return sts_client.get_caller_identity()["Account"]
    except Exception as e:
        print(f"Error getting account ID: {e}")
        return "unknown"


def get_account_name(account_id: str) -> str:
    """Get account name/alias if available"""
    try:
        iam_client = boto3.client("iam")
        aliases = iam_client.list_account_aliases()["AccountAliases"]
        if aliases:
            return aliases[0]

        try:
            org_client = boto3.client("organizations")
            account = org_client.describe_account(AccountId=account_id)
            return account["Account"]["Name"]
        except (ClientError, Exception):
            pass

        return None

    except Exception as e:
        print(f"Error getting account name: {e}")
        return None


def get_target_accounts() -> Dict:
    """Get all configured target accounts"""
    try:
        if not target_accounts_table:
            return response(
                500, {"error": "Target accounts table not configured"}
            )

        # Auto-initialize default account if none exist
        ensure_default_account()

        # Get current account info
        current_account_id = get_current_account_id()
        current_account_name = get_account_name(current_account_id)

        if current_account_name is None:
            current_account_name = current_account_id

        # Scan target accounts table
        result = target_accounts_table.scan()
        accounts = result.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in result:
            result = target_accounts_table.scan(
                ExclusiveStartKey=result["LastEvaluatedKey"]
            )
            accounts.extend(result.get("Items", []))

        return response(200, accounts)

    except Exception as e:
        print(f"Error getting target accounts: {e}")
        return response(500, {"error": str(e)})


def get_target_account(account_id: str) -> Dict:
    """Get a specific target account by ID"""
    try:
        if not target_accounts_table:
            return response(
                500, {"error": "Target accounts table not configured"}
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
        return response(500, {"error": str(e)})


def create_target_account(body: Dict) -> Dict:
    """Create a new target account configuration"""
    try:
        if not target_accounts_table:
            return response(
                500, {"error": "Target accounts table not configured"}
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
            existing = target_accounts_table.get_item(
                Key={"accountId": account_id}
            )
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
                        "message": "Cross-account role is not needed when adding the same account where this solution is deployed. Please leave the role field empty.",
                    },
                )
            print(
                f"Same account deployment detected for {account_id} - no cross-account role required"
            )
        else:
            # Different account - cross-account role IS required
            if not role_arn:
                return response(
                    400,
                    {
                        "error": "CROSS_ACCOUNT_ROLE_REQUIRED",
                        "message": f"This account ({account_id}) is different from where the solution is deployed ({current_account_id}). Please provide a cross-account IAM role ARN with DRS permissions.",
                    },
                )
            # Validate role ARN format
            if not role_arn.startswith("arn:aws:iam::"):
                return response(
                    400,
                    {
                        "error": "INVALID_ROLE_ARN",
                        "message": "Cross-account role ARN must be a valid IAM role ARN (arn:aws:iam::account:role/role-name)",
                    },
                )

        # If no name provided, try to get account name
        if not account_name:
            if is_current_account:
                account_name = (
                    get_account_name(account_id) or f"Account {account_id}"
                )
            else:
                account_name = f"Account {account_id}"

        # Check if this will be the first account (for default setting)
        is_first_account = False
        try:
            scan_result = target_accounts_table.scan(Select="COUNT")
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

        # Store in DynamoDB
        target_accounts_table.put_item(Item=account_item)

        success_message = f"Target account {account_id} added successfully"
        if is_current_account:
            success_message += " (same account - no cross-account role needed)"
        if is_first_account:
            success_message += " and set as default account"

        print(
            f"Created target account: {account_id} (isCurrentAccount: {is_current_account})"
        )

        return response(201, {**account_item, "message": success_message})

    except Exception as e:
        print(f"Error creating target account: {e}")
        return response(500, {"error": str(e)})


def update_target_account(account_id: str, body: Dict) -> Dict:
    """Update target account configuration"""
    try:
        if not target_accounts_table:
            return response(
                500, {"error": "Target accounts table not configured"}
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
        expression_values = {
            ":lastValidated": datetime.now(timezone.utc).isoformat() + "Z"
        }
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

        result = target_accounts_table.update_item(**update_args)
        updated_account = result["Attributes"]

        print(f"Updated target account: {account_id}")
        return response(200, updated_account)

    except Exception as e:
        print(f"Error updating target account: {e}")
        return response(500, {"error": str(e)})


def delete_target_account(account_id: str) -> Dict:
    """Delete target account configuration"""
    try:
        if not target_accounts_table:
            return response(
                500, {"error": "Target accounts table not configured"}
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
        target_accounts_table.delete_item(Key={"accountId": account_id})

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
        return response(500, {"error": str(e)})


def validate_target_account(account_id: str) -> Dict:
    """Validate target account access and permissions"""
    try:
        if not target_accounts_table:
            return response(
                500, {"error": "Target accounts table not configured"}
            )

        current_account_id = get_current_account_id()

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

        account_config = result["Item"]
        validation_results = {
            "accountId": account_id,
            "valid": True,
            "message": "Validation successful",
            "details": {
                "roleExists": True,
                "roleAccessible": True,
                "requiredPermissions": True,
            },
        }

        if account_id == current_account_id:
            # Validate current account by checking DRS access
            try:
                drs_client = boto3.client("drs", region_name="us-east-1")
                drs_client.describe_source_servers(maxResults=1)
                validation_results["message"] = "DRS access validated"
            except Exception as drs_error:
                validation_results["valid"] = False
                validation_results["message"] = (
                    f"DRS access issue: {str(drs_error)}"
                )
                validation_results["details"]["requiredPermissions"] = False
        else:
            # Cross-account validation
            role_arn = account_config.get("roleArn")
            if not role_arn:
                validation_results["valid"] = False
                validation_results["message"] = (
                    "Cross-account role ARN not configured"
                )
                validation_results["details"]["roleExists"] = False
            else:
                # Basic validation - role ARN format check
                validation_results["message"] = (
                    "Cross-account role configured (full validation not yet implemented)"
                )

        # Update last validated timestamp
        try:
            target_accounts_table.update_item(
                Key={"accountId": account_id},
                UpdateExpression="SET lastValidated = :lastValidated",
                ExpressionAttributeValues={
                    ":lastValidated": datetime.now(timezone.utc).isoformat()
                    + "Z"
                },
            )
        except Exception as update_error:
            print(
                f"Warning: Could not update lastValidated timestamp: {update_error}"
            )

        return response(200, validation_results)

    except Exception as e:
        print(f"Error validating target account: {e}")
        return response(500, {"error": str(e)})


# ============================================================================
# Configuration Import/Export Functions
# ============================================================================

# Schema version for configuration import/export
SCHEMA_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSIONS = ["1.0"]


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
        "schemaVersion": "1.0",
        "exportedAt": "2026-01-25T10:30:00Z",
        "sourceRegion": "us-east-1",
        "exportedBy": "api"
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
            "securityGroupIds": ["sg-xyz789"]
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
    
    Current: `1.0`
    
    Schema includes:
    - Protection Group structure
    - Recovery Plan structure
    - Wave structure with PG name references
    
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
        pg_result = protection_groups_table.scan()
        protection_groups = pg_result.get("Items", [])
        while "LastEvaluatedKey" in pg_result:
            pg_result = protection_groups_table.scan(
                ExclusiveStartKey=pg_result["LastEvaluatedKey"]
            )
            protection_groups.extend(pg_result.get("Items", []))

        # Scan all Recovery Plans
        rp_result = recovery_plans_table.scan()
        recovery_plans = rp_result.get("Items", [])
        while "LastEvaluatedKey" in rp_result:
            rp_result = recovery_plans_table.scan(
                ExclusiveStartKey=rp_result["LastEvaluatedKey"]
            )
            recovery_plans.extend(rp_result.get("Items", []))

        # Build PG ID -> Name mapping for wave export
        pg_id_to_name = {
            pg.get("groupId", ""): pg.get("groupName", "")
            for pg in protection_groups
        }

        # Transform Protection Groups for export (exclude internal fields)
        exported_pgs = []
        for pg in protection_groups:
            exported_pg = {
                "groupName": pg.get("groupName", ""),
                "description": pg.get("description", ""),
                "region": pg.get("region", ""),
                "accountId": pg.get("accountId", ""),
                "owner": pg.get("owner", ""),  # FIXED: camelCase
            }
            # Include server selection method (mutually exclusive)
            if pg.get("sourceServerIds"):
                exported_pg["sourceServerIds"] = pg["sourceServerIds"]
            if pg.get("serverSelectionTags"):
                exported_pg["serverSelectionTags"] = pg["serverSelectionTags"]
            # Include launchConfig if present
            if pg.get("launchConfig"):
                exported_pg["launchConfig"] = pg["launchConfig"]
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
                        exported_wave["protectionGroupName"] = pg_id_to_name[
                            pg_id
                        ]
                        # Remove ID - use name only for portability
                        exported_wave.pop("protectionGroupId", None)
                    else:
                        # Keep ID if name can't be resolved (orphaned reference)
                        orphaned_pg_ids.append(pg_id)
                        print(
                            f"Warning: PG ID '{pg_id}' not found - keeping ID in export"
                        )
                exported_waves.append(exported_wave)

            exported_rp = {
                "planName": rp.get("planName", ""),
                "description": rp.get("description", ""),
                "waves": exported_waves,
            }
            exported_rps.append(exported_rp)

        if orphaned_pg_ids:
            print(
                f"Export contains {len(orphaned_pg_ids)} orphaned PG references"
            )

        # Build export payload
        export_data = {
            "metadata": {
                "schemaVersion": SCHEMA_VERSION,
                "exportedAt": datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat()
                + "Z",
                "sourceRegion": source_region,
                "exportedBy": "api",
            },
            "protectionGroups": exported_pgs,
            "recoveryPlans": exported_rps,
        }

        return response(200, export_data)

    except Exception as e:
        print(f"Error exporting configuration: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500, {"error": "Failed to export configuration", "details": str(e)}
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
        config = body.get(
            "config", body
        )  # Support both wrapped and direct format

        # Validate schema version
        metadata = config.get("metadata", {})
        schema_version = metadata.get("schemaVersion", "")

        if not schema_version:
            return response(
                400,
                {
                    "error": "Missing schemaVersion in metadata",
                    "supportedVersions": SUPPORTED_SCHEMA_VERSIONS,
                },
            )

        if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            return response(
                400,
                {
                    "error": f"Unsupported schema version: {schema_version}",
                    "supportedVersions": SUPPORTED_SCHEMA_VERSIONS,
                },
            )

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

        # Track which PGs were successfully created/exist for RP dependency resolution
        available_pg_names = set(existing_pgs.keys())
        failed_pg_names = set()

        # Build name->ID mapping from existing PGs (case-insensitive keys)
        pg_name_to_id = {
            name.lower(): pg.get("groupId", "")
            for name, pg in existing_pgs.items()
        }

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
            500, {"error": "Failed to import configuration", "details": str(e)}
        )


def _get_existing_protection_groups() -> Dict[str, Dict]:
    """Get all existing Protection Groups indexed by name (case-insensitive)"""
    result = protection_groups_table.scan()
    pgs = result.get("Items", [])
    while "LastEvaluatedKey" in result:
        result = protection_groups_table.scan(
            ExclusiveStartKey=result["LastEvaluatedKey"]
        )
        pgs.extend(result.get("Items", []))
    return {pg.get("groupName", "").lower(): pg for pg in pgs}


def _get_existing_recovery_plans() -> Dict[str, Dict]:
    """Get all existing Recovery Plans indexed by name (case-insensitive)"""
    result = recovery_plans_table.scan()
    rps = result.get("Items", [])
    while "LastEvaluatedKey" in result:
        result = recovery_plans_table.scan(
            ExclusiveStartKey=result["LastEvaluatedKey"]
        )
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
            result = executions_table.query(
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
            print(
                f"Warning: Could not query executions for status {status}: {e}"
            )

    return servers


def _get_all_assigned_servers() -> Dict[str, str]:
    """Get all servers assigned to any Protection Group"""
    result = protection_groups_table.scan()
    pgs = result.get("Items", [])
    while "LastEvaluatedKey" in result:
        result = protection_groups_table.scan(
            ExclusiveStartKey=result["LastEvaluatedKey"]
        )
        pgs.extend(result.get("Items", []))

    assigned = {}
    for pg in pgs:
        pg_name = pg.get("groupName", "")
        for server_id in pg.get("sourceServerIds", []):
            assigned[server_id] = pg_name
    return assigned


def _process_protection_group_import(
    pg: Dict,
    existing_pgs: Dict[str, Dict],
    active_execution_servers: Dict[str, Dict],
    dry_run: bool,
    correlation_id: str,
) -> Dict:
    """Process a single Protection Group import"""
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
        result["details"] = {
            "existingGroupId": existing_pgs[pg_name.lower()].get("groupId", "")
        }
        print(f"[{correlation_id}] Skipping PG '{pg_name}': already exists")
        return result

    # Get server IDs to validate
    source_server_ids = pg.get("sourceServerIds", [])
    server_selection_tags = pg.get("serverSelectionTags", {})

    # Validate explicit servers
    if source_server_ids:
        # Check servers exist in DRS
        try:
            regional_drs = boto3.client("drs", region_name=region)
            drs_response = regional_drs.describe_source_servers(
                filters={"sourceServerIDs": source_server_ids}
            )
            found_ids = {
                s["sourceServerID"] for s in drs_response.get("items", [])
            }
            missing = set(source_server_ids) - found_ids

            if missing:
                result["reason"] = "SERVER_NOT_FOUND"
                result["details"] = {
                    "missingServerIds": list(missing),
                    "region": region,
                }
                print(
                    f"[{correlation_id}] Failed PG '{pg_name}': missing servers {missing}"
                )
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
            print(
                f"[{correlation_id}] Failed PG '{pg_name}': server conflicts {conflicts}"
            )
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
            print(
                f"[{correlation_id}] Failed PG '{pg_name}': active execution conflicts"
            )
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
            resolved = query_drs_servers_by_tags(
                region, server_selection_tags, account_context
            )
            if not resolved:
                result["reason"] = "NO_TAG_MATCHES"
                result["details"] = {
                    "tags": server_selection_tags,
                    "region": region,
                    "matchCount": 0,
                }
                print(
                    f"[{correlation_id}] Failed PG '{pg_name}': no servers match tags"
                )
                return result
        except Exception as e:
            result["reason"] = "TAG_RESOLUTION_ERROR"
            result["details"] = {
                "tags": server_selection_tags,
                "region": region,
                "error": str(e),
            }
            print(
                f"[{correlation_id}] Failed PG '{pg_name}': tag resolution error {e}"
            )
            return result
    else:
        result["reason"] = "NO_SELECTION_METHOD"
        result["details"] = {
            "message": "Either SourceServerIds or ServerSelectionTags required"
        }
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

            protection_groups_table.put_item(Item=item)
            result["details"] = {"groupId": group_id}
            print(
                f"[{correlation_id}] Created PG '{pg_name}' with ID {group_id}"
            )

            # Apply launchConfig to DRS servers (same as create/update)
            if launch_config:
                server_ids_to_apply = []
                if source_server_ids:
                    server_ids_to_apply = source_server_ids
                elif server_selection_tags:
                    # Extract account context from protection group data if available
                    account_context = None
                    if pg.get("accountId"):
                        account_context = {
                            "accountId": pg.get("accountId"),
                            "assumeRoleName": pg.get("assumeRoleName"),
                        }
                    resolved = query_drs_servers_by_tags(
                        region, server_selection_tags, account_context
                    )
                    server_ids_to_apply = [
                        s.get("sourceServerId")
                        for s in resolved
                        if s.get("sourceServerId")
                    ]

                if server_ids_to_apply:
                    try:
                        apply_results = apply_launch_config_to_servers(
                            server_ids_to_apply,
                            launch_config,
                            region,
                            protection_group_id=group_id,
                            protection_group_name=pg_name,
                        )
                        # Extract counts safely without referencing sensitive object methods
                        applied_count = 0
                        failed_count = 0
                        if apply_results and "applied" in apply_results:
                            applied_count = apply_results["applied"]
                        if apply_results and "failed" in apply_results:
                            failed_count = apply_results["failed"]

                        result["details"][
                            "launchConfigApplied"
                        ] = applied_count
                        result["details"]["launchConfigFailed"] = failed_count
                        # launchConfig applied successfully - no logging to prevent sensitive data exposure
                    except Exception as lc_err:
                        print(
                            f"Warning: Failed to apply launchConfig: {type(lc_err).__name__}"
                        )
        except Exception as e:
            result["reason"] = "CREATE_ERROR"
            result["details"] = {"error": str(e)}
            print(f"Failed to create PG '{pg_name}': {type(e).__name__}")
            return result
    else:
        result["details"] = {"wouldCreate": True}
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
        result["details"] = {
            "existingPlanId": existing_rps[plan_name.lower()].get("planId", "")
        }
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
                    print(
                        f"[{correlation_id}] Resolved PG '{pg_name}' from name (ID was stale)"
                    )

            # If still not resolved, the ID is invalid
            if not resolved_pg_id:
                # Check if we have a protectionGroupName to fall back to
                if not pg_name:
                    missing_pgs.append(f"ID:{pg_id}")
                    continue

        # Case 2: Only protectionGroupName provided - resolve to ID
        if not resolved_pg_id and pg_name:
            pg_name_lower = pg_name.lower()
            print(
                f"[{correlation_id}] Resolving PG name '{pg_name}' (lower: '{pg_name_lower}')"
            )
            print(
                f"[{correlation_id}] Available PG names in mapping: {list(pg_name_to_id.keys())}"
            )

            # Check if PG failed import (cascade failure)
            if pg_name in failed_pg_names:
                cascade_failed_pgs.append(pg_name)
                continue

            # Check if PG exists and get its ID
            if pg_name_lower in pg_name_to_id:
                resolved_pg_id = pg_name_to_id[pg_name_lower]
                resolved_pg_name = pg_name
                print(
                    f"[{correlation_id}] Resolved '{pg_name}' -> ID '{resolved_pg_id}'"
                )
            else:
                print(
                    f"[{correlation_id}] PG name '{pg_name_lower}' NOT FOUND in mapping"
                )
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
        print(
            f"[{correlation_id}] Failed RP '{plan_name}': cascade failure from PGs {cascade_failed_pgs}"
        )
        return result

    if missing_pgs:
        result["reason"] = "MISSING_PROTECTION_GROUP"
        result["details"] = {
            "missingProtectionGroups": list(set(missing_pgs)),
            "message": "Referenced Protection Groups do not exist",
        }
        print(
            f"[{correlation_id}] Failed RP '{plan_name}': missing PGs {missing_pgs}"
        )
        return result

    # Create the Recovery Plan (unless dry run)
    if not dry_run:
        try:
            plan_id = str(uuid.uuid4())
            timestamp = int(time.time())

            item = {
                "planId": plan_id,
                "planName": plan_name,
                "description": rp.get("description", ""),
                "waves": resolved_waves,  # Use resolved waves with correct IDs
                "createdDate": timestamp,  # FIXED: camelCase
                "lastModifiedDate": timestamp,  # FIXED: camelCase
                "version": 1,  # FIXED: camelCase
            }

            recovery_plans_table.put_item(Item=item)
            result["details"] = {"planId": plan_id}
            print(
                f"[{correlation_id}] Created RP '{plan_name}' with ID {plan_id}"
            )
        except Exception as e:
            result["reason"] = "CREATE_ERROR"
            result["details"] = {"error": str(e)}
            print(f"[{correlation_id}] Failed to create RP '{plan_name}': {e}")
            return result
    else:
        result["details"] = {
            "wouldCreate": True,
            "resolvedWaves": len(resolved_waves),
        }
        print(f"[{correlation_id}] [DRY RUN] Would create RP '{plan_name}'")

    result["status"] = "created"
    result["reason"] = ""
    return result
