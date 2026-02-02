"""
Query Handler - Read-Only DRS and EC2 Infrastructure Queries

Handles all read-only query operations for the DR Orchestration Platform including
DRS source servers, EC2 resources, account information, and configuration exports.

## Architecture Pattern

Dual Invocation Support:
- API Gateway Mode: REST API endpoints for frontend/CLI
- Direct Invocation Mode: Function calls from Step Functions/Lambda

## Integration Points

### 1. API Gateway Invocation (Frontend/CLI)
```bash
# Query DRS Source Servers
curl -X GET "https://api.example.com/drs/source-servers?region=us-east-1" \
  -H "Authorization: Bearer $TOKEN"

# Query EC2 Subnets
curl -X GET "https://api.example.com/ec2/subnets?region=us-east-1&vpcId=vpc-123" \
  -H "Authorization: Bearer $TOKEN"

# Get DRS Service Limits
curl -X GET "https://api.example.com/drs/service-limits?region=us-east-1" \
  -H "Authorization: Bearer $TOKEN"

# Export Configuration
curl -X GET "https://api.example.com/config/export" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Direct Lambda Invocation (Step Functions)
```python
import boto3

lambda_client = boto3.client('lambda')

# Query DRS Source Servers
response = lambda_client.invoke(
    FunctionName='query-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_drs_source_servers",
        "queryParams": {"region": "us-east-1"}
    })
)

# Query EC2 Security Groups
response = lambda_client.invoke(
    FunctionName='query-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_ec2_security_groups",
        "queryParams": {"region": "us-east-1", "vpcId": "vpc-123"}
    })
)
```

### 3. AWS CLI Direct Invocation
```bash
# Query DRS Source Servers
aws lambda invoke \
  --function-name query-handler \
  --payload '{
    "operation": "get_drs_source_servers",
    "queryParams": {"region": "us-east-1"}
  }' \
  response.json

# Get Current Account Info
aws lambda invoke \
  --function-name query-handler \
  --payload '{
    "operation": "get_current_account"
  }' \
  response.json

# Export Configuration
aws lambda invoke \
  --function-name query-handler \
  --payload '{
    "operation": "export_configuration"
  }' \
  response.json
```

## Supported Operations

### DRS Infrastructure Queries (4 operations)
- `get_drs_source_servers`: List DRS source servers in region
- `get_drs_quotas`: Get DRS service quotas (deprecated - use service_limits)
- `get_drs_service_limits`: Get DRS service limits and current usage
- `get_drs_accounts`: List DRS-enabled accounts

### EC2 Resource Queries (4 operations)
- `get_ec2_subnets`: List EC2 subnets in VPC
- `get_ec2_security_groups`: List EC2 security groups in VPC
- `get_ec2_instance_types`: List available EC2 instance types
- `get_ec2_instance_profiles`: List IAM instance profiles

### Account Information (1 operation)
- `get_current_account`: Get current AWS account ID and region

### Configuration Export (1 operation)
- `export_configuration`: Export all protection groups and recovery plans

### User Permissions (1 operation - API Gateway only)
- `get_user_permissions`: Get RBAC permissions for authenticated user

## API Endpoints (API Gateway Mode)

### DRS Infrastructure
- `GET /drs/source-servers?region={region}` - List DRS source servers
- `GET /drs/quotas?region={region}` - Get DRS quotas (deprecated)
- `GET /drs/service-limits?region={region}` - Get DRS service limits
- `GET /drs/accounts` - List DRS-enabled accounts

### EC2 Resources
- `GET /ec2/subnets?region={region}&vpcId={vpcId}` - List subnets
- `GET /ec2/security-groups?region={region}&vpcId={vpcId}` - List security groups
- `GET /ec2/instance-types?region={region}` - List instance types
- `GET /ec2/instance-profiles?region={region}` - List instance profiles

### Account & Configuration
- `GET /accounts/current` - Get current account info
- `GET /config/export` - Export configuration
- `GET /user/permissions` - Get user RBAC permissions

## Query Parameters

### Common Parameters
- `region`: AWS region (required for most operations)
- `vpcId`: VPC ID (required for subnet/security group queries)
- `accountId`: Target account ID (optional, defaults to current account)

### DRS Source Servers Filters
- `tags`: Filter by tags (JSON object)
- `replicationState`: Filter by replication state
- `lifecycleState`: Filter by lifecycle state

### EC2 Filters
- `availabilityZone`: Filter subnets by AZ
- `instanceFamily`: Filter instance types by family (e.g., "t3", "m5")

## Response Format

### DRS Source Servers
```json
{
  "servers": [
    {
      "sourceServerID": "s-abc123...",
      "hostname": "web-server-01",
      "replicationState": "CONTINUOUS",
      "lifecycleState": "READY_FOR_LAUNCH",
      "tags": {"Environment": "production"}
    }
  ],
  "totalCount": 25
}
```

### DRS Service Limits
```json
{
  "limits": {
    "maxServersPerJob": 100,
    "maxConcurrentJobs": 20,
    "maxServersInAllJobs": 500
  },
  "currentUsage": {
    "activeJobs": 2,
    "serversInJobs": 45
  }
}
```

### EC2 Subnets
```json
{
  "subnets": [
    {
      "subnetId": "subnet-123",
      "subnetName": "Private Subnet 1A",
      "availabilityZone": "us-east-1a",
      "cidrBlock": "10.0.1.0/24",
      "vpcId": "vpc-123"
    }
  ]
}
```

### Configuration Export
```json
{
  "protectionGroups": [...],
  "recoveryPlans": [...],
  "exportedAt": "2026-01-25T12:00:00Z",
  "version": "1.0"
}
```

## Cross-Account Support

### Hub-and-Spoke Model
Query handler supports cross-account queries via IAM role assumption:

```python
# Query DRS servers in target account
response = lambda_client.invoke(
    FunctionName='query-handler',
    Payload=json.dumps({
        "operation": "get_drs_source_servers",
        "queryParams": {
            "region": "us-east-1",
            "accountId": "123456789012"  # Target account
        }
    })
)
```

### IAM Role Assumption
- Hub account assumes `DRSOrchestrationCrossAccountRole` in spoke accounts
- Role ARN configured in Target Accounts table
- Automatic credential management via STS

## Performance Characteristics

### Memory: 256 MB
Read-only operations with minimal processing.

### Timeout: 60 seconds
Sufficient for DRS/EC2 API calls with pagination.

### Cold Start: < 2 seconds
Lightweight function with minimal dependencies.

### Caching
No caching - always returns fresh data from AWS APIs.

## Error Handling

### Not Found Errors (404)
- Region not supported
- VPC not found
- No DRS servers in region

### Access Denied Errors (403)
- Insufficient IAM permissions
- Cross-account role assumption failed
- DRS not enabled in region

### Internal Errors (500)
- AWS API errors
- DynamoDB errors
- Timeout errors

## Testing Considerations

### Mock AWS APIs
```python
from unittest.mock import patch

with patch('boto3.client') as mock_client:
    mock_drs = mock_client.return_value
    mock_drs.describe_source_servers.return_value = {
        "items": [{"sourceServerID": "s-123"}]
    }
    
    result = lambda_handler({
        "operation": "get_drs_source_servers",
        "queryParams": {"region": "us-east-1"}
    }, None)
    
    assert result["statusCode"] == 200
```

### Mock DynamoDB
```python
from moto import mock_dynamodb

@mock_dynamodb
def test_export_configuration():
    # Create mock tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(...)
    
    result = lambda_handler({
        "operation": "export_configuration"
    }, None)
    
    assert "protectionGroups" in json.loads(result["body"])
```

Query Operations:
- DRS Infrastructure: Source servers, quotas, capacity, accounts
- EC2 Resources: Subnets, security groups, instance types, instance profiles
- Account Information: Current account ID and region
- Configuration Export: Export Protection Groups and Recovery Plans
- User Permissions: RBAC permissions (API Gateway mode only)

Performance:
- Memory: 256 MB (read-only operations)
- Timeout: 60 seconds
- Cold start target: < 2 seconds
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.exceptions import ClientError

# Import shared utilities
from shared.account_utils import (
    get_account_name,
    get_target_accounts,
    validate_target_account,
)
from shared.conflict_detection import query_drs_servers_by_tags
from shared.cross_account import (
    create_drs_client,
    get_cross_account_session,
    get_current_account_id,
)
from shared.drs_limits import DRS_LIMITS
from shared.drs_utils import map_replication_state_to_display
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
TARGET_ACCOUNTS_TABLE = os.environ.get("TARGET_ACCOUNTS_TABLE")

# Initialize DynamoDB resources
dynamodb = boto3.resource("dynamodb")
protection_groups_table = (
    dynamodb.Table(PROTECTION_GROUPS_TABLE)
    if PROTECTION_GROUPS_TABLE
    else None
)
recovery_plans_table = (
    dynamodb.Table(RECOVERY_PLANS_TABLE) if RECOVERY_PLANS_TABLE else None
)
target_accounts_table = (
    dynamodb.Table(TARGET_ACCOUNTS_TABLE) if TARGET_ACCOUNTS_TABLE else None
)


# ============================================================================
# Lambda Handler Entry Point
# ============================================================================


def lambda_handler(event, context):
    """
    Unified entry point supporting both API Gateway and direct invocation.

    API Gateway Event (Standalone Mode):
    {
        "requestContext": {...},
        "httpMethod": "GET",
        "path": "/drs/source-servers",
        "queryStringParameters": {"region": "us-east-1"}
    }

    Direct Invocation Event (Direct Lambda Mode):
    {
        "operation": "get_drs_source_servers",
        "queryParams": {"region": "us-east-1"}
    }
    """
    try:
        # Detect invocation pattern
        if "requestContext" in event:
            # API Gateway invocation (standalone mode)
            return handle_api_gateway_request(event, context)
        elif "operation" in event:
            # Direct invocation (direct Lambda mode)
            return handle_direct_invocation(event, context)
        else:
            return {
                "error": "Invalid invocation format",
                "message": "Event must contain either 'requestContext' (API Gateway) or 'operation' (direct invocation)",
            }
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def handle_api_gateway_request(event, context):
    """Route API Gateway requests to appropriate handler functions"""
    method = event["httpMethod"]
    path = event["path"]
    query_params = event.get("queryStringParameters") or {}

    # DRS Infrastructure endpoints
    if path == "/drs/source-servers" and method == "GET":
        return get_drs_source_servers(query_params)

    elif path == "/drs/quotas" and method == "GET":
        account_id = query_params.get("accountId")

        # Default to current account if not specified
        if not account_id:
            account_id = get_current_account_id()

        # Build account context for cross-account access
        current_account_id = get_current_account_id()
        account_context = None
        if account_id != current_account_id:
            account_context = {"accountId": account_id}

        # Get account-wide capacity across all regions
        return get_drs_account_capacity_all_regions_response(account_context)

    elif path == "/drs/accounts" and method == "GET":
        return get_target_accounts()

    # EC2 Resources endpoints
    elif path == "/ec2/subnets" and method == "GET":
        return get_ec2_subnets(query_params)

    elif path == "/ec2/security-groups" and method == "GET":
        return get_ec2_security_groups(query_params)

    elif path == "/ec2/instance-profiles" and method == "GET":
        return get_ec2_instance_profiles(query_params)

    elif path == "/ec2/instance-types" and method == "GET":
        return get_ec2_instance_types(query_params)

    # Account & Config endpoints
    elif path == "/accounts/current" and method == "GET":
        return get_current_account_info()

    elif path == "/config/export" and method == "GET":
        return export_configuration(query_params)

    # User permissions endpoint
    elif path == "/user/permissions" and method == "GET":
        return handle_user_permissions(event)

    # User profile endpoint
    elif path == "/user/profile" and method == "GET":
        return handle_user_profile(event)

    # User roles endpoint
    elif path == "/user/roles" and method == "GET":
        return handle_user_roles(event)

    # Staging account validation endpoint
    elif path == "/staging-accounts/validate" and method == "POST":
        # Extract body from API Gateway event
        body = json.loads(event.get("body", "{}"))
        return handle_validate_staging_account(body)

    # Combined capacity endpoint
    # Supports both:
    # - /accounts/{targetAccountId}/capacity
    # - /accounts/targets/{targetAccountId}/capacity
    elif (
        path.startswith("/accounts/")
        and path.endswith("/capacity")
        and method == "GET"
    ):
        # Extract target account ID from path
        path_parts = path.split("/")

        # Handle /accounts/targets/{id}/capacity
        if len(path_parts) >= 5 and path_parts[2] == "targets":
            target_account_id = path_parts[3]
            return handle_get_combined_capacity(
                {"targetAccountId": target_account_id}
            )
        # Handle /accounts/{id}/capacity
        elif len(path_parts) >= 4:
            target_account_id = path_parts[2]
            return handle_get_combined_capacity(
                {"targetAccountId": target_account_id}
            )
        else:
            return response(400, {"error": "Invalid path format"})

    # Discover staging accounts endpoint
    # Supports both:
    # - /accounts/targets/{id}/staging-accounts/discover
    # - /accounts/{targetAccountId}/staging-accounts/discover
    elif (
        path.startswith("/accounts/")
        and path.endswith("/staging-accounts/discover")
        and method == "GET"
    ):
        # Extract target account ID from path
        path_parts = path.split("/")

        # Handle /accounts/targets/{id}/staging-accounts/discover
        if len(path_parts) >= 5 and path_parts[2] == "targets":
            target_account_id = path_parts[3]
            return handle_discover_staging_accounts(
                {"targetAccountId": target_account_id}
            )
        # Handle /accounts/{id}/staging-accounts/discover
        elif len(path_parts) >= 4:
            target_account_id = path_parts[2]
            return handle_discover_staging_accounts(
                {"targetAccountId": target_account_id}
            )
        else:
            return response(400, {"error": "Invalid path format"})

    else:
        return response(
            404, {"error": "Not Found", "message": f"Path {path} not found"}
        )


def handle_direct_invocation(event, context):
    """Handle direct Lambda invocation (direct Lambda mode)"""
    operation = event.get("operation")
    query_params = event.get("queryParams", {})

    # Map operation to function
    operations = {
        "get_drs_source_servers": lambda: get_drs_source_servers(query_params),
        "get_drs_account_capacity": lambda: get_drs_account_capacity(
            query_params.get("region"), query_params.get("accountId")
        ),
        "get_drs_account_capacity_all_regions": lambda: get_drs_account_capacity_all_regions(
            query_params.get("account_context")
        ),
        "get_drs_regional_capacity": lambda: get_drs_regional_capacity(
            query_params.get("region")
        ),
        "get_target_accounts": lambda: get_target_accounts(),
        "get_ec2_subnets": lambda: get_ec2_subnets(query_params),
        "get_ec2_security_groups": lambda: get_ec2_security_groups(
            query_params
        ),
        "get_ec2_instance_profiles": lambda: get_ec2_instance_profiles(
            query_params
        ),
        "get_ec2_instance_types": lambda: get_ec2_instance_types(query_params),
        "get_current_account_id": lambda: {
            "accountId": get_current_account_id()
        },
        "export_configuration": lambda: export_configuration(query_params),
        "get_user_permissions": lambda: {
            "error": "User permissions not available in direct invocation mode"
        },
        "validate_staging_account": lambda: handle_validate_staging_account(
            query_params
        ),
        "discover_staging_accounts": lambda: handle_discover_staging_accounts(
            query_params
        ),
        "get_combined_capacity": lambda: handle_get_combined_capacity(
            query_params
        ),
    }

    if operation in operations:
        result = operations[operation]()
        # Return raw result (not API Gateway response format)
        if isinstance(result, dict) and "statusCode" in result:
            # Extract body from API Gateway response format
            return json.loads(result.get("body", "{}"))
        return result
    else:
        return {"error": "Unknown operation", "operation": operation}


# ============================================================================
# Helper Functions
# ============================================================================


def _count_drs_servers(regional_drs, account_id: str) -> Dict:
    """
    Count DRS source servers and replicating servers.

    IMPORTANT: Distinguishes between:
    - Replicating servers: Servers actively replicating TO this account (for 300 limit)
    - Extended source servers: Servers from staging accounts (don't count toward 300 limit)
    - Total source servers: All servers including extended (for 4,000 recovery limit)

    Extended source servers are identified by checking stagingArea.stagingAccountID field.
    If this field exists and differs from the target account_id, the server is extended
    from a staging account and should NOT count toward the 300 replicating limit.

    Args:
        regional_drs: DRS client for the region
        account_id: AWS account ID to identify extended source servers

    Returns:
        Dict with:
        - totalServers: All servers including extended (for recovery capacity)
        - replicatingServers: Only servers replicating TO this account (for 300 limit)
    """
    total_servers = 0
    replicating_servers = 0
    extended_count = 0

    paginator = regional_drs.get_paginator("describe_source_servers")

    for page in paginator.paginate():
        for server in page.get("items", []):
            total_servers += 1
            server_id = server.get("sourceServerID", "unknown")

            # Check if this is an extended source server from a staging account
            # Extended source servers have stagingArea.stagingAccountID != target account
            staging_area = server.get("stagingArea", {})
            staging_account_id = staging_area.get("stagingAccountID", "")

            # Debug: log staging area info for first few servers
            if total_servers <= 3:
                print(
                    f"DEBUG Server {server_id}: "
                    f"stagingArea={staging_area}, "
                    f"stagingAccountID={staging_account_id}, "
                    f"targetAccountID={account_id}"
                )

            is_extended = (
                staging_account_id and staging_account_id != account_id
            )

            if is_extended:
                extended_count += 1
                print(
                    f"Extended source server detected: "
                    f"serverID={server_id}, "
                    f"stagingAccountID={staging_account_id}, "
                    f"targetAccountID={account_id}"
                )

            # Only count replicating servers that are NOT extended source servers
            if not is_extended:
                replication_state = server.get("dataReplicationInfo", {}).get(
                    "dataReplicationState", ""
                )
                if replication_state in [
                    "CONTINUOUS",
                    "INITIAL_SYNC",
                    "RESCAN",
                    "INITIATING",
                    "CREATING_SNAPSHOT",
                    "BACKLOG",
                ]:
                    replicating_servers += 1

    print(
        f"Server count summary for account {account_id}: "
        f"total={total_servers}, replicating={replicating_servers}, "
        f"extended={extended_count}"
    )

    return {
        "totalServers": total_servers,  # All servers (for 4,000 recovery limit)
        "replicatingServers": replicating_servers,  # Only direct replicating (for 300 limit)
    }


# ============================================================================
# DRS Infrastructure Query Functions
# ============================================================================


def _transform_drs_server(server: Dict) -> Dict:
    """Transform raw DRS API response to frontend format"""
    source_props = server.get("sourceProperties", {})
    identification = source_props.get("identificationHints", {})
    hardware = source_props.get("cpus", [])
    disks = source_props.get("disks", [])
    nics = source_props.get("networkInterfaces", [])

    # Calculate hardware totals
    total_cores = sum(cpu.get("cores", 0) for cpu in hardware)
    ram_bytes = source_props.get("ramBytes", 0)
    ram_gib = round(ram_bytes / (1024**3), 2) if ram_bytes else 0

    disk_list = []
    total_disk_gib = 0
    for disk in disks:
        disk_bytes = disk.get("bytes", 0)
        disk_gib = round(disk_bytes / (1024**3), 2) if disk_bytes else 0
        total_disk_gib += disk_gib
        disk_list.append(
            {
                "deviceName": disk.get("deviceName", ""),
                "bytes": disk_bytes,
                "sizeGiB": disk_gib,
            }
        )

    # Extract primary IP
    primary_ip = None
    for nic in nics:
        if nic.get("isPrimary"):
            ips = nic.get("ips", [])
            if ips:
                primary_ip = ips[0]
            break

    # Extract replication state from DRS API response
    data_replication_info = server.get("dataReplicationInfo", {})
    raw_replication_state = data_replication_info.get(
        "dataReplicationState", "UNKNOWN"
    )

    # Debug log to see what DRS is actually returning
    server_id = server.get("sourceServerID", "unknown")
    print(
        f"DEBUG: Server {server_id} raw dataReplicationState: {raw_replication_state}"
    )
    print(f"DEBUG: Full dataReplicationInfo: {data_replication_info}")

    return {
        "sourceServerID": server.get("sourceServerID", ""),
        "hostname": identification.get("hostname", ""),
        "fqdn": identification.get("fqdn", ""),
        "nameTag": server.get("tags", {}).get("Name", ""),
        "sourceInstanceId": identification.get("awsInstanceID", ""),
        "sourceIp": primary_ip or "",
        "sourceRegion": server.get("sourceProperties", {}).get(
            "lastUpdatedDateTime", ""
        ),
        "os": source_props.get("os", {}).get("fullString", ""),
        # Map dataReplicationState to display state for UI
        "state": map_replication_state_to_display(raw_replication_state),
        "replicationState": raw_replication_state,
        "lagDuration": data_replication_info.get("lagDuration", ""),
        "lastSeen": server.get("lifeCycle", {}).get(
            "lastSeenByServiceDateTime", ""
        ),
        "hardware": {
            "cpus": [
                {
                    "modelName": cpu.get("modelName", ""),
                    "cores": cpu.get("cores", 0),
                }
                for cpu in hardware
            ],
            "totalCores": total_cores,
            "ramBytes": ram_bytes,
            "ramGiB": ram_gib,
            "disks": disk_list,
            "totalDiskGiB": round(total_disk_gib, 2),
        },
        "networkInterfaces": [
            {
                "ips": nic.get("ips", []),
                "macAddress": nic.get("macAddress", ""),
                "isPrimary": nic.get("isPrimary", False),
            }
            for nic in nics
        ],
        "drsTags": server.get("tags", {}),
        "assignedToProtectionGroup": None,
        "selectable": True,
    }


def get_drs_source_servers(query_params: Dict) -> Dict:
    """Query DRS source servers with optional filtering"""
    region = query_params.get("region")
    account_id = query_params.get("accountId")
    current_pg_id = query_params.get("currentProtectionGroupId")

    if not region:
        return response(400, {"error": "region is required"})

    try:
        # Determine account context for cross-account queries
        account_context = None
        if account_id:
            # Look up target account details to get assumeRoleName
            if target_accounts_table:
                try:
                    account_result = target_accounts_table.get_item(
                        Key={"accountId": account_id}
                    )
                    if "Item" in account_result:
                        account = account_result["Item"]

                        # Extract role name from roleArn if assumeRoleName not present
                        assume_role_name = account.get("assumeRoleName")
                        if not assume_role_name:
                            role_arn = account.get("roleArn")
                            if role_arn:
                                # Extract role name from ARN: arn:aws:iam::123456789012:role/RoleName
                                assume_role_name = role_arn.split("/")[-1]

                        # Get External ID if present
                        external_id = account.get("externalId")

                        account_context = {
                            "accountId": account_id,
                            "assumeRoleName": assume_role_name,
                            "externalId": external_id,
                            "isCurrentAccount": False,
                        }
                        print(
                            f"Found target account {account_id} with role {assume_role_name}"
                        )
                    else:
                        print(
                            f"WARNING: Account {account_id} not found in target accounts table"
                        )
                        # Still try with just accountId (will use current account)
                        account_context = {"accountId": account_id}
                except Exception as e:
                    print(f"Error looking up target account: {e}")
                    account_context = {"accountId": account_id}
            else:
                # No target accounts table, use just accountId
                account_context = {"accountId": account_id}

        regional_drs = create_drs_client(region, account_context)

        # Query DRS for source servers with proper error handling
        try:
            raw_servers = []
            paginator = regional_drs.get_paginator("describe_source_servers")

            for page in paginator.paginate():
                raw_servers.extend(page.get("items", []))

        except regional_drs.exceptions.UninitializedAccountException:
            print(f"DRS not initialized in {region}")
            return response(
                400,
                {
                    "error": "DRS_NOT_INITIALIZED",
                    "message": f"AWS Elastic Disaster Recovery (DRS) is not initialized in {region}. Go to the DRS Console in {region} and complete the initialization wizard before creating Protection Groups.",
                    "region": region,
                    "initialized": False,
                },
            )
        except Exception as drs_error:
            error_str = str(drs_error)
            print(f"Error querying DRS: {error_str}")

            # Check if it's an uninitialized error
            if (
                "UninitializedAccountException" in error_str
                or "not initialized" in error_str.lower()
            ):
                return response(
                    400,
                    {
                        "error": "DRS_NOT_INITIALIZED",
                        "message": f"AWS Elastic Disaster Recovery (DRS) is not initialized in {region}. Go to the DRS Console in {region} and complete the initialization wizard before creating Protection Groups.",
                        "region": region,
                        "initialized": False,
                    },
                )

            # Check if it's an opt-in region not enabled
            if (
                "UnrecognizedClientException" in error_str
                or "security token" in error_str.lower()
            ):
                print(f"Region not enabled: {region}")
                return response(
                    400,
                    {
                        "error": "REGION_NOT_ENABLED",
                        "message": f"Region {region} is not enabled in your AWS account. This is an opt-in region that requires explicit enablement. Go to AWS Account Settings to enable this region, then initialize DRS.",
                        "region": region,
                        "initialized": False,
                    },
                )

            # Re-raise other errors
            raise

        # Transform servers to frontend format
        servers = [_transform_drs_server(s) for s in raw_servers]

        print(
            f"DEBUG: About to check PG assignments, protection_groups_table={protection_groups_table}"
        )

        # Check Protection Group assignments for all servers
        if protection_groups_table:
            try:
                # Scan all Protection Groups to build server assignment map
                pg_scan = protection_groups_table.scan()
                server_assignments = {}

                print(
                    f"DEBUG: Checking PG assignments - found {len(pg_scan.get('Items', []))} PGs"
                )

                for pg in pg_scan.get("Items", []):
                    pg_id = pg.get("groupId") or pg.get("protectionGroupId")
                    pg_name = pg.get("groupName") or pg.get("name")
                    pg_region = pg.get("region")
                    pg_account = pg.get("accountId")

                    print(
                        f"DEBUG: PG '{pg_name}' - region={pg_region}, account={pg_account}, target_region={region}, target_account={account_id}"
                    )

                    # Skip if this is the current PG being edited
                    if current_pg_id and pg_id == current_pg_id:
                        print(f"DEBUG: Skipping current PG: {pg_id}")
                        continue

                    # Only check PGs in the same region
                    if pg_region != region:
                        print(f"DEBUG: Skipping PG in different region")
                        continue

                    # Only check PGs in the same account (if account filtering is enabled)
                    if account_id and pg_account != account_id:
                        print(
                            f"DEBUG: Skipping PG in different account (PG account: {pg_account}, target: {account_id})"
                        )
                        continue

                    # Check manual server selection (sourceServerIds)
                    server_ids = pg.get("sourceServerIds", [])
                    print(
                        f"DEBUG: PG '{pg_name}' has {len(server_ids)} manual serverIds"
                    )
                    for server_id in server_ids:
                        server_assignments[server_id] = {
                            "protectionGroupId": pg_id,
                            "protectionGroupName": pg_name,
                        }

                    # Check tag-based selection (serverSelectionTags)
                    selection_tags = pg.get("serverSelectionTags", {})
                    print(
                        f"DEBUG: PG '{pg_name}' selection_tags={selection_tags}"
                    )

                    if selection_tags:
                        matched = 0
                        # Match servers against tag criteria (AND logic)
                        for server in servers:
                            server_id = server["sourceServerID"]
                            server_tags = server.get("drsTags", {})

                            # Check if server matches ALL selection tags
                            matches_all_tags = all(
                                server_tags.get(tag_key) == tag_value
                                for tag_key, tag_value in selection_tags.items()
                            )

                            if matches_all_tags:
                                matched += 1
                                print(
                                    f"DEBUG: Server {server_id} matches PG '{pg_name}'"
                                )
                                server_assignments[server_id] = {
                                    "protectionGroupId": pg_id,
                                    "protectionGroupName": pg_name,
                                }
                        print(
                            f"DEBUG: PG '{pg_name}' matched {matched} servers"
                        )

                print(f"DEBUG: Total assignments: {len(server_assignments)}")

                # Mark servers with their assignments
                for server in servers:
                    server_id = server["sourceServerID"]
                    if server_id in server_assignments:
                        server["assignedToProtectionGroup"] = (
                            server_assignments[server_id]
                        )
                        server["selectable"] = False
                    else:
                        server["assignedToProtectionGroup"] = None
                        server["selectable"] = True

            except Exception as e:
                print(f"Warning: Could not check PG assignments: {e}")
                import traceback

                traceback.print_exc()
                # Continue without assignment info

        return response(
            200,
            {
                "servers": servers,
                "sourceServers": raw_servers,
                "region": region,
                "serverCount": len(servers),
            },
        )

    except Exception as e:
        print(f"Error getting DRS source servers: {e}")
        return response(500, {"error": str(e)})


def get_drs_regional_capacity(region: str) -> Dict:
    """
    Get DRS capacity metrics for a specific region.

    Queries DRS source servers in a single region and returns capacity metrics including
    total servers and replicating servers. Used for regional capacity monitoring and
    planning.

    ## Use Cases

    ### 1. Regional Capacity Check
    ```python
    capacity = get_drs_regional_capacity("us-east-1")
    print(f"Region has {capacity['replicatingServers']} replicating servers")
    ```

    ### 2. Multi-Region Capacity Aggregation
    ```python
    for region in DRS_REGIONS:
        capacity = get_drs_regional_capacity(region)
        if capacity['status'] == 'OK':
            total += capacity['totalSourceServers']
    ```

    ## Behavior

    ### Capacity Calculation
    1. Queries all DRS source servers in region (paginated)
    2. Counts total servers and replicating servers
    3. Determines status based on server counts
    4. Returns capacity metrics with status

    ### Status Values
    - OK: Region has servers and is operational
    - NOT_INITIALIZED: DRS not initialized in region
    - ACCESS_DENIED: Insufficient permissions
    - ERROR: Other errors occurred

    ## Args

    region: AWS region to check capacity

    ## Returns

    Dict with regional capacity:
        - region: Region name
        - totalSourceServers: Total DRS servers in region
        - replicatingServers: Servers actively replicating
        - status: Region status (OK/NOT_INITIALIZED/ACCESS_DENIED/ERROR)
        - error: Error message (if status is ERROR)

    ## Example Response

    ```json
    {
      "region": "us-east-1",
      "totalSourceServers": 125,
      "replicatingServers": 120,
      "status": "OK"
    }
    ```

    ## Related Functions

    - `get_drs_account_capacity_all_regions()`: Account-wide capacity across all regions
    - `get_drs_account_capacity()`: Single-region capacity with API Gateway wrapper

    Get DRS capacity metrics for a specific region
    """
    try:
        regional_drs = boto3.client("drs", region_name=region)
        # Get current account ID for filtering extended source servers
        account_id = get_current_account_id()
        counts = _count_drs_servers(regional_drs, account_id)

        return {
            "region": region,
            "totalSourceServers": counts["totalServers"],
            "replicatingServers": counts["replicatingServers"],
            "status": "OK",
        }

    except Exception as e:
        error_str = str(e)
        print(f"Error getting regional capacity for {region}: {e}")

        # Check for common uninitialized/access errors
        if (
            "UninitializedAccountException" in error_str
            or "not initialized" in error_str.lower()
            or "UnrecognizedClientException" in error_str
        ):
            return {
                "region": region,
                "totalSourceServers": 0,
                "replicatingServers": 0,
                "status": "NOT_INITIALIZED",
            }
        elif (
            "AccessDeniedException" in error_str
            or "not authorized" in error_str.lower()
        ):
            return {
                "region": region,
                "totalSourceServers": None,
                "replicatingServers": None,
                "status": "ACCESS_DENIED",
            }

        return {"region": region, "error": error_str, "status": "ERROR"}


def get_drs_account_capacity_all_regions(
    account_context: Optional[Dict] = None,
) -> Dict:
    """
    Get DRS account capacity aggregated across all regions.

    Queries all 15 DRS-enabled regions concurrently and aggregates capacity metrics
    to provide account-wide view. Compares replicating server count against the
    300-server hard limit to determine capacity status.

    ## Use Cases

    ### 1. Account-Wide Capacity Monitoring
    ```python
    capacity = get_drs_account_capacity_all_regions()
    if capacity['status'] == 'CRITICAL':
        alert("DRS at capacity limit!")
    ```

    ### 2. Capacity Planning
    ```python
    capacity = get_drs_account_capacity_all_regions()
    available = capacity['availableReplicatingSlots']
    print(f"Can add {available} more replicating servers")
    ```

    ### 3. Regional Breakdown Analysis
    ```python
    capacity = get_drs_account_capacity_all_regions()
    for region_data in capacity['regionalBreakdown']:
        print(f"{region_data['region']}: {region_data['replicatingServers']} servers")
    ```

    ## Integration Points

    ### Direct Invocation
    ```python
    capacity = get_drs_account_capacity_all_regions()
    ```

    ### Cross-Account Query
    ```python
    capacity = get_drs_account_capacity_all_regions(
        account_context={"accountId": "123456789012"}
    )
    ```

    ## Behavior

    ### Concurrent Regional Queries
    1. Queries all 15 DRS regions concurrently (max 10 threads)
    2. Priority regions queried first (us-east-1, us-east-2, us-west-1, us-west-2)
    3. Skips uninitialized regions silently (no error)
    4. Aggregates results across all regions
    5. Determines account-wide capacity status

    ### Capacity Status Determination
    - CRITICAL: >= 300 replicating servers (at hard limit)
    - WARNING: >= 270 replicating servers (90% of limit)
    - INFO: >= 240 replicating servers (80% of limit)
    - OK: < 240 replicating servers

    ### Error Handling
    - Non-blocking: Region failures don't stop aggregation
    - Graceful degradation: Failed regions tracked separately
    - Uninitialized regions: Counted as 0 servers (no error)

    ## Args

    account_context: Optional cross-account context with:
        - accountId: AWS account ID to query

    ## Returns

    Dict with account-wide capacity:
        - totalSourceServers: Total DRS servers across all regions
        - replicatingServers: Total replicating servers across all regions
        - maxReplicatingServers: Hard limit (300)
        - maxSourceServers: Soft limit (1000)
        - availableReplicatingSlots: Remaining capacity
        - status: Capacity status (OK/INFO/WARNING/CRITICAL)
        - message: Human-readable status message
        - regionalBreakdown: List of regions with servers
        - failedRegions: List of regions that failed to query

    ## Example Response

    ```json
    {
      "totalSourceServers": 325,
      "replicatingServers": 285,
      "maxReplicatingServers": 300,
      "maxSourceServers": 1000,
      "availableReplicatingSlots": 15,
      "status": "WARNING",
      "message": "Approaching hard limit: 285/300 replicating servers across all regions",
      "regionalBreakdown": [
        {"region": "us-east-1", "totalServers": 125, "replicatingServers": 120},
        {"region": "us-west-2", "totalServers": 100, "replicatingServers": 95},
        {"region": "eu-west-1", "totalServers": 100, "replicatingServers": 70}
      ],
      "failedRegions": []
    }
    ```

    ## Performance

    ### Execution Time
    - Small deployment (< 100 servers): 2-5 seconds
    - Medium deployment (100-300 servers): 5-10 seconds
    - Large deployment (300+ servers): 10-15 seconds

    ### Concurrency
    - Max 10 concurrent region queries
    - Priority regions queried first for faster response
    - Uninitialized regions skipped immediately

    ### API Calls
    - DRS DescribeSourceServers: 1 per region (paginated)
    - Total: Up to 15 API calls (one per region)

    ## Related Functions

    - `get_drs_account_capacity_all_regions_response()`: API Gateway wrapper
    - `get_drs_regional_capacity()`: Single-region capacity
    - `get_drs_account_capacity()`: Single-region with API wrapper

    Get DRS account capacity aggregated across all regions.
    Queries all regions concurrently for fast response.
    """
    # Priority regions to check first
    priority_regions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]
    other_regions = [r for r in DRS_REGIONS if r not in priority_regions]
    all_regions_ordered = priority_regions + other_regions

    total_servers = 0
    replicating_servers = 0
    regional_breakdown = []
    failed_regions = []

    def query_region(region: str) -> Dict:
        """Query a single region and return results"""
        try:
            regional_drs = create_drs_client(region, account_context)
            # Get account ID from context or current account
            account_id = (
                account_context.get("accountId")
                if account_context
                else get_current_account_id()
            )
            counts = _count_drs_servers(regional_drs, account_id)
            return {
                "success": True,
                "region": region,
                "totalServers": counts["totalServers"],
                "replicatingServers": counts["replicatingServers"],
            }
        except Exception as e:
            error_str = str(e)
            # Skip uninitialized regions and opt-in regions silently
            if (
                "UninitializedAccountException" in error_str
                or "not initialized" in error_str.lower()
                or "UnrecognizedClientException" in error_str
                or "security token" in error_str.lower()
            ):
                return {
                    "success": True,
                    "region": region,
                    "totalServers": 0,
                    "replicatingServers": 0,
                }

            print(f"ERROR: Failed to query DRS in {region}: {e}")
            return {"success": False, "region": region, "error": str(e)}

    # Query all regions concurrently (max 10 threads to avoid overwhelming API)
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_region = {
            executor.submit(query_region, region): region
            for region in all_regions_ordered
        }

        for future in as_completed(future_to_region):
            result = future.result()

            if result["success"]:
                if result["totalServers"] > 0:
                    regional_breakdown.append(
                        {
                            "region": result["region"],
                            "totalServers": result["totalServers"],
                            "replicatingServers": result["replicatingServers"],
                        }
                    )

                total_servers += result["totalServers"]
                replicating_servers += result["replicatingServers"]
            else:
                failed_regions.append(result["region"])

    # Determine capacity status based on account-wide limits
    if replicating_servers >= DRS_LIMITS["MAX_REPLICATING_SERVERS"]:
        status = "CRITICAL"
        message = f"Account at hard limit: {replicating_servers}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} replicating servers across all regions"
    elif replicating_servers >= DRS_LIMITS["CRITICAL_REPLICATING_THRESHOLD"]:
        status = "WARNING"
        message = f"Approaching hard limit: {replicating_servers}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} replicating servers across all regions"
    elif replicating_servers >= DRS_LIMITS["WARNING_REPLICATING_THRESHOLD"]:
        status = "INFO"
        message = f"Monitor capacity: {replicating_servers}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} replicating servers across all regions"
    else:
        status = "OK"
        message = f"Capacity OK: {replicating_servers}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} replicating servers across all regions"

    # Add warning if some regions failed
    if failed_regions:
        message += f" (Warning: {len(failed_regions)} regions failed to query)"

    return {
        "totalSourceServers": total_servers,
        "replicatingServers": replicating_servers,
        "maxReplicatingServers": DRS_LIMITS["MAX_REPLICATING_SERVERS"],
        "maxSourceServers": DRS_LIMITS["MAX_SOURCE_SERVERS"],
        "availableReplicatingSlots": max(
            0, DRS_LIMITS["MAX_REPLICATING_SERVERS"] - replicating_servers
        ),
        "status": status,
        "message": message,
        "regionalBreakdown": regional_breakdown,
        "failedRegions": failed_regions,
    }


def get_drs_account_capacity_all_regions_response(
    account_context: Optional[Dict] = None,
) -> Dict:
    """
    API Gateway wrapper for account-wide DRS capacity query.
    
    Returns account-wide DRS capacity in the format expected by the frontend,
    including capacity metrics, concurrent jobs info, and servers in jobs count.
    Combines data from multiple sources into a unified response.
    
    ## Use Cases
    
    ### 1. Frontend Dashboard
    ```bash
    curl -X GET https://api.example.com/drs/capacity \
      -H "Authorization: Bearer $TOKEN"
    ```
    
    ### 2. Capacity Monitoring
    ```python
    response = get_drs_account_capacity_all_regions_response()
    capacity = response['capacity']
    if capacity['status'] == 'CRITICAL':
        send_alert("DRS at capacity limit")
    ```
    
    ## Integration Points
    
    ### API Gateway Invocation
    ```bash
    curl -X GET https://api.example.com/drs/capacity \
      -H "Authorization: Bearer $TOKEN"
    ```
    
    ### Direct Lambda Invocation
    ```python
    lambda_client.invoke(
        FunctionName='query-handler',
        Payload=json.dumps({
            "operation": "get_drs_account_capacity_all_regions_response"
        })
    )
    ```
    
    ## Behavior
    
    ### Data Aggregation
    1. Gets account ID and name
    2. Queries account-wide DRS capacity across all regions
    3. Queries concurrent jobs info (from us-east-1 by default)
    4. Queries servers in active jobs (from us-east-1 by default)
    5. Combines all data into unified response
    
    ### Regional vs Account-Wide Data
    - Capacity: Account-wide across all 15 regions
    - Concurrent jobs: Regional (us-east-1 by default)
    - Servers in jobs: Regional (us-east-1 by default)
    
    ## Args
    
    account_context: Optional cross-account context with:
        - accountId: AWS account ID to query
    
    ## Returns
    
    Dict with comprehensive capacity data:
        - accountId: AWS account ID
        - accountName: Account name
        - region: Region queried for jobs info (us-east-1)
        - limits: DRS hard limits (dict)
        - capacity: Account-wide capacity metrics (dict)
        - concurrentJobs: Current/max concurrent jobs (dict)
        - serversInJobs: Current/max servers in jobs (dict)
    
    ## Example Response
    
    ```json
    {
      "accountId": "123456789012",
      "accountName": "Production Account",
      "region": "us-east-1",
      "limits": {
        "MAX_REPLICATING_SERVERS": 300,
        "MAX_SOURCE_SERVERS": 1000,
        "MAX_CONCURRENT_JOBS": 20,
        "MAX_SERVERS_IN_ALL_JOBS": 500
      },
      "capacity": {
        "totalSourceServers": 325,
        "replicatingServers": 285,
        "maxReplicatingServers": 300,
        "availableReplicatingSlots": 15,
        "status": "WARNING",
        "message": "Approaching hard limit: 285/300 replicating servers",
        "regionalBreakdown": [...]
      },
      "concurrentJobs": {
        "current": 3,
        "max": 20,
        "available": 17
      },
      "serversInJobs": {
        "current": 45,
        "max": 500
      }
    }
    ```
    
    ## Performance
    
    ### Execution Time
    - Small deployment: 2-5 seconds
    - Medium deployment: 5-10 seconds
    - Large deployment: 10-15 seconds
    
    ### API Calls
    - DRS DescribeSourceServers: 1 per region (15 total)
    - DRS DescribeJobs: 1 call (us-east-1)
    - Total: ~16 API calls
    
    ## Related Functions
    
    - `get_drs_account_capacity_all_regions()`: Core capacity aggregation
    - `validate_concurrent_jobs()`: Concurrent jobs validation
    - `validate_servers_in_all_jobs()`: Servers in jobs validation
    
    API Gateway wrapper for get_drs_account_capacity_all_regions.
    Returns account-wide DRS capacity in the format expected by the frontend.
    Matches the exact response structure from the old API Handler.
    """
    try:
        # Get account ID
        if account_context and "accountId" in account_context:
            account_id = account_context["accountId"]
        else:
            account_id = get_current_account_id()

        # Get account name
        account_name = get_account_name(account_id)

        # Get account-wide capacity
        capacity = get_drs_account_capacity_all_regions(account_context)

        # Use us-east-1 as default region for jobs info (matches old API Handler)
        region = os.environ.get("AWS_REGION", "us-east-1")

        # Get concurrent jobs info (regional)
        jobs_info = validate_concurrent_jobs(region)

        # Get servers in active jobs (regional)
        servers_in_jobs = validate_servers_in_all_jobs(region, 0)

        # Return in the exact format expected by frontend (matching old API Handler)
        return response(
            200,
            {
                "accountId": account_id,
                "accountName": account_name or f"Account {account_id}",
                "region": region,  # Region queried for jobs info
                "limits": DRS_LIMITS,
                "capacity": capacity,  # Account-wide DRS capacity across all regions
                "concurrentJobs": {
                    "current": jobs_info.get("currentJobs"),
                    "max": jobs_info.get("maxJobs"),
                    "available": jobs_info.get("availableSlots"),
                },
                "serversInJobs": {
                    "current": servers_in_jobs.get("currentServersInJobs"),
                    "max": servers_in_jobs.get("maxServers"),
                },
            },
        )
    except Exception as e:
        print(f"Error getting account-wide capacity: {e}")
        return response(500, {"error": str(e)})


def validate_concurrent_jobs(region: str) -> Dict:
    """
    Check current DRS job count against the 20 concurrent jobs limit.
    Returns validation result with current count and availability.
    """
    try:
        regional_drs = boto3.client("drs", region_name=region)

        # Get active jobs (PENDING or STARTED status)
        active_jobs = []
        paginator = regional_drs.get_paginator("describe_jobs")

        for page in paginator.paginate():
            for job in page.get("items", []):
                if job.get("status") in ["PENDING", "STARTED"]:
                    active_jobs.append(
                        {
                            "jobId": job.get("jobID"),
                            "status": job.get("status"),
                            "type": job.get("type"),
                            "serverCount": len(
                                job.get("participatingServers", [])
                            ),
                        }
                    )

        current_count = len(active_jobs)
        available_slots = DRS_LIMITS["MAX_CONCURRENT_JOBS"] - current_count

        return {
            "valid": current_count < DRS_LIMITS["MAX_CONCURRENT_JOBS"],
            "currentJobs": current_count,
            "maxJobs": DRS_LIMITS["MAX_CONCURRENT_JOBS"],
            "availableSlots": available_slots,
            "activeJobs": active_jobs,
            "message": (
                f"DRS has {current_count}/{DRS_LIMITS['MAX_CONCURRENT_JOBS']} active jobs"
                if current_count < DRS_LIMITS["MAX_CONCURRENT_JOBS"]
                else f"DRS concurrent job limit reached ({current_count}/{DRS_LIMITS['MAX_CONCURRENT_JOBS']})"
            ),
        }

    except Exception as e:
        error_str = str(e)
        print(f"Error checking concurrent jobs: {e}")

        # Check for uninitialized region errors
        if any(
            x in error_str
            for x in [
                "UninitializedAccountException",
                "UnrecognizedClientException",
                "security token",
            ]
        ):
            return {
                "valid": True,
                "currentJobs": 0,
                "maxJobs": DRS_LIMITS["MAX_CONCURRENT_JOBS"],
                "availableSlots": DRS_LIMITS["MAX_CONCURRENT_JOBS"],
                "notInitialized": True,
            }

        return {
            "valid": True,
            "warning": f"Could not verify concurrent jobs: {error_str}",
            "currentJobs": None,
            "maxJobs": DRS_LIMITS["MAX_CONCURRENT_JOBS"],
        }


def validate_servers_in_all_jobs(region: str, new_server_count: int) -> Dict:
    """
    Check if adding new servers would exceed the 500 servers in all jobs limit.
    Returns validation result.
    """
    try:
        regional_drs = boto3.client("drs", region_name=region)

        # Count servers in active jobs
        servers_in_jobs = 0
        paginator = regional_drs.get_paginator("describe_jobs")

        for page in paginator.paginate():
            for job in page.get("items", []):
                if job.get("status") in ["PENDING", "STARTED"]:
                    servers_in_jobs += len(job.get("participatingServers", []))

        total_after_new = servers_in_jobs + new_server_count

        return {
            "valid": total_after_new <= DRS_LIMITS["MAX_SERVERS_IN_ALL_JOBS"],
            "currentServersInJobs": servers_in_jobs,
            "newServerCount": new_server_count,
            "totalAfterNew": total_after_new,
            "maxServers": DRS_LIMITS["MAX_SERVERS_IN_ALL_JOBS"],
            "message": (
                f"Would have {total_after_new}/{DRS_LIMITS['MAX_SERVERS_IN_ALL_JOBS']} servers in active jobs"
                if total_after_new <= DRS_LIMITS["MAX_SERVERS_IN_ALL_JOBS"]
                else f"Would exceed max servers in all jobs ({total_after_new}/{DRS_LIMITS['MAX_SERVERS_IN_ALL_JOBS']})"
            ),
        }

    except Exception as e:
        error_str = str(e)
        print(f"Error checking servers in all jobs: {e}")

        # Check for uninitialized region errors
        if any(
            x in error_str
            for x in [
                "UninitializedAccountException",
                "UnrecognizedClientException",
                "security token",
            ]
        ):
            return {
                "valid": True,
                "currentServersInJobs": 0,
                "maxServers": DRS_LIMITS["MAX_SERVERS_IN_ALL_JOBS"],
                "notInitialized": True,
            }

        return {
            "valid": True,
            "warning": f"Could not verify servers in all jobs: {error_str}",
            "currentServersInJobs": None,
            "maxServers": DRS_LIMITS["MAX_SERVERS_IN_ALL_JOBS"],
        }


def validate_max_servers_per_job(
    region: str, account_context: Optional[Dict] = None
) -> Dict:
    """
    Check the maximum number of servers in any single active job.
    DRS limit: 100 servers per recovery job.

    Args:
        region: AWS region to check
        account_context: Optional cross-account context with accountId,
                        assumeRoleName, externalId

    Returns:
        Dict with:
        - maxServersInSingleJob: Highest server count in any active job
        - maxAllowed: 100 (DRS limit)
        - jobId: ID of job with most servers (if any)
        - status: OK, WARNING, or CRITICAL
        - message: Status message
    """
    try:
        # Get DRS client (cross-account if needed)
        if account_context and account_context.get("accountId"):
            session = get_cross_account_session(
                account_context["accountId"],
                account_context.get("assumeRoleName"),
                account_context.get("externalId"),
            )
            regional_drs = session.client("drs", region_name=region)
        else:
            regional_drs = boto3.client("drs", region_name=region)

        # Find job with most servers
        max_servers = 0
        max_job_id = None
        paginator = regional_drs.get_paginator("describe_jobs")

        for page in paginator.paginate():
            for job in page.get("items", []):
                if job.get("status") in ["PENDING", "STARTED"]:
                    server_count = len(job.get("participatingServers", []))
                    if server_count > max_servers:
                        max_servers = server_count
                        max_job_id = job.get("jobID")

        # Determine status
        max_allowed = DRS_LIMITS["MAX_SERVERS_PER_JOB"]

        if max_servers >= max_allowed:
            status = "CRITICAL"
            message = f"Job {max_job_id} has {max_servers} servers (at limit)"
        elif max_servers >= max_allowed * 0.9:  # 90 servers
            status = "WARNING"
            message = (
                f"Job {max_job_id} has {max_servers} servers (90% of limit)"
            )
        elif max_servers >= max_allowed * 0.8:  # 80 servers
            status = "INFO"
            message = (
                f"Job {max_job_id} has {max_servers} servers (80% of limit)"
            )
        else:
            status = "OK"
            message = (
                f"Largest job has {max_servers} servers"
                if max_servers > 0
                else "No active jobs"
            )

        return {
            "maxServersInSingleJob": max_servers,
            "maxAllowed": max_allowed,
            "availableSlots": max_allowed - max_servers,
            "jobId": max_job_id,
            "status": status,
            "message": message,
        }

    except Exception as e:
        error_str = str(e)
        print(f"Error checking max servers per job: {e}")

        # Check for uninitialized region errors
        if any(
            x in error_str
            for x in [
                "UninitializedAccountException",
                "UnrecognizedClientException",
                "security token",
            ]
        ):
            return {
                "maxServersInSingleJob": 0,
                "maxAllowed": DRS_LIMITS["MAX_SERVERS_PER_JOB"],
                "availableSlots": DRS_LIMITS["MAX_SERVERS_PER_JOB"],
                "status": "OK",
                "message": "DRS not initialized in region",
                "notInitialized": True,
            }

        return {
            "maxServersInSingleJob": 0,
            "maxAllowed": DRS_LIMITS["MAX_SERVERS_PER_JOB"],
            "availableSlots": DRS_LIMITS["MAX_SERVERS_PER_JOB"],
            "status": "OK",
            "message": f"Could not check per-job limits: {error_str}",
            "warning": error_str,
        }


def get_drs_account_capacity(
    region: str, account_id: Optional[str] = None
) -> Dict:
    """
    Get DRS account capacity metrics for a specific region with API Gateway wrapper.
    
    Returns capacity info including replicating server count compared against the
    300-server hard limit. Provides detailed status messages for capacity planning.
    
    ## Use Cases
    
    ### 1. Regional Capacity Check
    ```bash
    curl -X GET https://api.example.com/drs/capacity/us-east-1 \
      -H "Authorization: Bearer $TOKEN"
    ```
    
    ### 2. Pre-Launch Validation
    ```python
    capacity = get_drs_account_capacity("us-east-1")
    if capacity['availableReplicatingSlots'] < 10:
        print("Warning: Low capacity in region")
    ```
    
    ### 3. Cross-Account Capacity Query
    ```python
    capacity = get_drs_account_capacity(
        region="us-east-1",
        account_id="123456789012"
    )
    ```
    
    ## Integration Points
    
    ### API Gateway Invocation
    ```bash
    curl -X GET https://api.example.com/drs/capacity/us-east-1 \
      -H "Authorization: Bearer $TOKEN"
    ```
    
    ### Direct Lambda Invocation
    ```python
    lambda_client.invoke(
        FunctionName='query-handler',
        Payload=json.dumps({
            "operation": "get_drs_account_capacity",
            "region": "us-east-1"
        })
    )
    ```
    
    ## Behavior
    
    ### Capacity Calculation
    1. Queries all DRS source servers in region
    2. Counts total servers and replicating servers
    3. Compares against 300-server hard limit
    4. Determines capacity status
    5. Returns metrics with status message
    
    ### Status Determination
    - CRITICAL: >= 300 replicating servers (at hard limit)
    - WARNING: >= 270 replicating servers (90% of limit)
    - INFO: >= 240 replicating servers (80% of limit)
    - OK: < 240 replicating servers
    - NOT_INITIALIZED: DRS not initialized in region
    
    ### Cross-Account Support
    If account_id provided and differs from current account:
    - Assumes cross-account role
    - Queries DRS in target account
    - Returns capacity for target account
    
    ## Args
    
    region: AWS region to check capacity
    account_id: Optional account ID for cross-account queries
    
    ## Returns
    
    Dict with regional capacity (200 OK):
        - totalSourceServers: Total DRS servers in region
        - replicatingServers: Servers actively replicating
        - maxReplicatingServers: Hard limit (300)
        - maxSourceServers: Soft limit (1000)
        - availableReplicatingSlots: Remaining capacity
        - status: Capacity status
        - message: Human-readable status message
    
    ## Example Response
    
    ```json
    {
      "totalSourceServers": 125,
      "replicatingServers": 120,
      "maxReplicatingServers": 300,
      "maxSourceServers": 1000,
      "availableReplicatingSlots": 180,
      "status": "OK",
      "message": "Capacity OK: 120/300 replicating servers in us-east-1"
    }
    ```
    
    ## Error Handling
    
    ### DRS Not Initialized (200 OK)
    ```json
    {
      "totalSourceServers": 0,
      "replicatingServers": 0,
      "maxReplicatingServers": 300,
      "maxSourceServers": 1000,
      "availableReplicatingSlots": 300,
      "status": "NOT_INITIALIZED",
      "message": "DRS not initialized in us-east-1. Initialize DRS in the AWS Console to use this region."
    }
    ```
    
    ### Access Denied (403 Forbidden)
    ```json
    {
      "totalSourceServers": null,
      "replicatingServers": null,
      "status": "ACCESS_DENIED",
      "message": "Access denied to DRS in us-east-1. Check IAM permissions."
    }
    ```
    
    ## Performance
    
    ### Execution Time
    - Small region (< 50 servers): 1-2 seconds
    - Medium region (50-200 servers): 2-5 seconds
    - Large region (200+ servers): 5-10 seconds
    
    ### API Calls
    - DRS DescribeSourceServers: 1 call (paginated)
    
    ## Related Functions
    
    - `get_drs_account_capacity_all_regions()`: Account-wide capacity
    - `get_drs_regional_capacity()`: Regional capacity without wrapper
    - `validate_concurrent_jobs()`: Concurrent jobs validation
    
    Get current DRS account capacity metrics for a specific region.
    Returns capacity info including replicating server count vs 300 hard limit.
    """
    try:
        # Determine account context for cross-account queries
        account_context = None
        if account_id:
            current_account_id = get_current_account_id()
            if account_id != current_account_id:
                account_context = {"accountId": account_id}

        regional_drs = create_drs_client(region, account_context)
        # Get account ID for filtering extended source servers
        target_account_id = (
            account_id if account_id else get_current_account_id()
        )
        counts = _count_drs_servers(regional_drs, target_account_id)
        total_servers = counts["totalServers"]
        replicating_servers = counts["replicatingServers"]

        # Determine capacity status
        if replicating_servers >= DRS_LIMITS["MAX_REPLICATING_SERVERS"]:
            status = "CRITICAL"
            message = f"Account at hard limit: {replicating_servers}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} replicating servers in {region}"
        elif (
            replicating_servers >= DRS_LIMITS["CRITICAL_REPLICATING_THRESHOLD"]
        ):
            status = "WARNING"
            message = f"Approaching hard limit: {replicating_servers}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} replicating servers in {region}"
        elif (
            replicating_servers >= DRS_LIMITS["WARNING_REPLICATING_THRESHOLD"]
        ):
            status = "INFO"
            message = f"Monitor capacity: {replicating_servers}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} replicating servers in {region}"
        else:
            status = "OK"
            message = f"Capacity OK: {replicating_servers}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} replicating servers in {region}"

        return response(
            200,
            {
                "totalSourceServers": total_servers,
                "replicatingServers": replicating_servers,
                "maxReplicatingServers": DRS_LIMITS["MAX_REPLICATING_SERVERS"],
                "maxSourceServers": DRS_LIMITS["MAX_SOURCE_SERVERS"],
                "availableReplicatingSlots": max(
                    0,
                    DRS_LIMITS["MAX_REPLICATING_SERVERS"]
                    - replicating_servers,
                ),
                "status": status,
                "message": message,
            },
        )

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "UninitializedAccountException":
            return response(
                200,
                {
                    "totalSourceServers": 0,
                    "replicatingServers": 0,
                    "maxReplicatingServers": DRS_LIMITS[
                        "MAX_REPLICATING_SERVERS"
                    ],
                    "maxSourceServers": DRS_LIMITS["MAX_SOURCE_SERVERS"],
                    "availableReplicatingSlots": DRS_LIMITS[
                        "MAX_REPLICATING_SERVERS"
                    ],
                    "status": "NOT_INITIALIZED",
                    "message": f"DRS not initialized in {region}. Initialize DRS in the AWS Console to use this region.",
                },
            )
        raise

    except Exception as e:
        error_str = str(e)
        print(f"Error getting account capacity: {e}")

        # Check for common uninitialized/access errors
        if (
            "UninitializedAccountException" in error_str
            or "not initialized" in error_str.lower()
            or "UnrecognizedClientException" in error_str
            or "security token" in error_str.lower()
        ):
            return response(
                200,
                {
                    "totalSourceServers": 0,
                    "replicatingServers": 0,
                    "maxReplicatingServers": DRS_LIMITS[
                        "MAX_REPLICATING_SERVERS"
                    ],
                    "maxSourceServers": DRS_LIMITS["MAX_SOURCE_SERVERS"],
                    "availableReplicatingSlots": DRS_LIMITS[
                        "MAX_REPLICATING_SERVERS"
                    ],
                    "status": "NOT_INITIALIZED",
                    "message": f"DRS not initialized in {region}. Initialize DRS in the AWS Console to use this region.",
                },
            )
        elif (
            "AccessDeniedException" in error_str
            or "not authorized" in error_str.lower()
        ):
            return response(
                403,
                {
                    "totalSourceServers": None,
                    "replicatingServers": None,
                    "status": "ACCESS_DENIED",
                    "message": f"Access denied to DRS in {region}. Check IAM permissions.",
                },
            )

        return response(
            500,
            {
                "error": error_str,
                "status": "UNKNOWN",
                "message": f"Failed to get DRS capacity in {region}",
            },
        )


# ============================================================================
# EC2 Resource Query Functions
# ============================================================================


def get_ec2_subnets(query_params: Dict) -> Dict:
    """Get VPC subnets for dropdown selection"""
    region = query_params.get("region")

    if not region:
        return response(
            400, {"error": "region is required", "code": "MISSING_REGION"}
        )

    try:
        ec2 = boto3.client("ec2", region_name=region)
        result = ec2.describe_subnets()

        subnets = []
        for subnet in result["Subnets"]:
            name = next(
                (
                    t["Value"]
                    for t in subnet.get("Tags", [])
                    if t["Key"] == "Name"
                ),
                None,
            )
            label = f"{subnet['SubnetId']}"
            if name:
                label = f"{name} ({subnet['SubnetId']})"
            label += f" - {subnet['CidrBlock']} - {subnet['AvailabilityZone']}"

            subnets.append(
                {
                    "value": subnet["SubnetId"],
                    "label": label,
                    "vpcId": subnet["VpcId"],
                    "az": subnet["AvailabilityZone"],
                    "cidr": subnet["CidrBlock"],
                }
            )

        subnets.sort(key=lambda x: x["label"])
        return response(200, {"subnets": subnets})
    except Exception as e:
        print(f"Error getting subnets: {e}")
        return response(500, {"error": str(e)})


def get_ec2_security_groups(query_params: Dict) -> Dict:
    """Get security groups for dropdown selection"""
    region = query_params.get("region")
    vpc_id = query_params.get("vpcId")  # Optional filter

    if not region:
        return response(
            400, {"error": "region is required", "code": "MISSING_REGION"}
        )

    try:
        ec2 = boto3.client("ec2", region_name=region)
        filters = [{"Name": "vpc-id", "Values": [vpc_id]}] if vpc_id else []
        result = (
            ec2.describe_security_groups(Filters=filters)
            if filters
            else ec2.describe_security_groups()
        )

        groups = []
        for sg in result["SecurityGroups"]:
            label = f"{sg['GroupName']} ({sg['GroupId']})"
            groups.append(
                {
                    "value": sg["GroupId"],
                    "label": label,
                    "name": sg["GroupName"],
                    "vpcId": sg["VpcId"],
                    "description": sg.get("Description", "")[:100],
                }
            )

        groups.sort(key=lambda x: x["name"])
        return response(200, {"securityGroups": groups})
    except Exception as e:
        print(f"Error getting security groups: {e}")
        return response(500, {"error": str(e)})


def get_ec2_instance_profiles(query_params: Dict) -> Dict:
    """Get IAM instance profiles for dropdown selection"""
    region = query_params.get("region")

    if not region:
        return response(
            400, {"error": "region is required", "code": "MISSING_REGION"}
        )

    try:
        # IAM is global but we accept region for consistency
        iam = boto3.client("iam")
        profiles = []
        paginator = iam.get_paginator("list_instance_profiles")

        for page in paginator.paginate():
            for profile in page["InstanceProfiles"]:
                profiles.append(
                    {
                        "value": profile["InstanceProfileName"],
                        "label": profile["InstanceProfileName"],
                        "arn": profile["Arn"],
                    }
                )

        profiles.sort(key=lambda x: x["label"])
        return response(200, {"instanceProfiles": profiles})
    except Exception as e:
        print(f"Error getting instance profiles: {e}")
        return response(500, {"error": str(e)})


def get_ec2_instance_types(query_params: Dict) -> Dict:
    """Get ALL EC2 instance types available in the specified region for DRS launch settings"""
    region = query_params.get("region")

    if not region:
        return response(
            400, {"error": "region is required", "code": "MISSING_REGION"}
        )

    try:
        ec2 = boto3.client("ec2", region_name=region)

        types = []
        paginator = ec2.get_paginator("describe_instance_types")

        # Get ALL instance types available in the region (no filtering)
        for page in paginator.paginate():
            for it in page["InstanceTypes"]:
                instance_type = it["InstanceType"]
                vcpus = it["VCpuInfo"]["DefaultVCpus"]
                mem_gb = round(it["MemoryInfo"]["SizeInMiB"] / 1024)

                # Skip bare metal instances as they're typically not used for DRS recovery
                if ".metal" in instance_type:
                    continue

                types.append(
                    {
                        "value": instance_type,
                        "label": f"{instance_type} ({vcpus} vCPU, {mem_gb} GB)",
                        "vcpus": vcpus,
                        "memoryGb": mem_gb,
                    }
                )

        # Sort by family then by vcpus for better organization
        types.sort(key=lambda x: (x["value"].split(".")[0], x["vcpus"]))

        print(f"Retrieved {len(types)} instance types for region {region}")
        return response(200, {"instanceTypes": types})

    except Exception as e:
        print(f"Error getting instance types for region {region}: {e}")
        return response(500, {"error": str(e)})


# ============================================================================
# Account & Configuration Functions
# ============================================================================


def get_current_account_info() -> Dict:
    """Get current account information for setup wizard"""
    try:
        current_account_id = get_current_account_id()
        current_account_name = get_account_name(current_account_id)

        return response(
            200,
            {
                "accountId": current_account_id,
                "accountName": current_account_name
                or f"Account {current_account_id}",
                "isCurrentAccount": True,
            },
        )

    except Exception as e:
        print(f"Error getting current account info: {e}")
        return response(500, {"error": str(e)})


def export_configuration(query_params: Dict) -> Dict:
    """
    Export all Protection Groups and Recovery Plans to JSON format.
    Returns complete configuration with metadata for backup/migration.

    Schema v1.1: Includes per-server launch template configurations.
    """
    try:
        if not protection_groups_table or not recovery_plans_table:
            return response(500, {"error": "DynamoDB tables not configured"})

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
        servers_with_custom_config = 0
        total_server_count = 0

        for pg in protection_groups:
            exported_pg = {
                "groupName": pg.get("groupName", ""),
                "description": pg.get("description", ""),
                "region": pg.get("region", ""),
                "accountId": pg.get("accountId", ""),
                "owner": pg.get("owner", ""),
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
                        "useGroupDefaults": server.get(
                            "useGroupDefaults", True
                        ),
                    }
                    # Include optional fields if present
                    if server.get("instanceId"):
                        exported_server["instanceId"] = server["instanceId"]
                    if server.get("instanceName"):
                        exported_server["instanceName"] = server[
                            "instanceName"
                        ]
                    if server.get("tags"):
                        exported_server["tags"] = server["tags"]
                    if server.get("launchTemplate"):
                        exported_server["launchTemplate"] = server[
                            "launchTemplate"
                        ]

                    exported_servers.append(exported_server)
                    total_server_count += 1

                    # Count servers with custom configurations
                    if not server.get("useGroupDefaults", True) or (
                        server.get("launchTemplate")
                        and any(
                            v is not None
                            for v in server["launchTemplate"].values()
                        )
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

        # Build export payload with schema v1.1 metadata
        export_data = {
            "schemaVersion": "1.1",
            "exportedAt": datetime.now(timezone.utc).isoformat() + "Z",
            "sourceRegion": source_region,
            "sourceAccount": get_current_account_id(),
            "protectionGroups": exported_pgs,
            "recoveryPlans": exported_rps,
            "metadata": {
                "protectionGroupCount": len(exported_pgs),
                "recoveryPlanCount": len(exported_rps),
                "serverCount": total_server_count,
                "serversWithCustomConfig": servers_with_custom_config,
                "orphanedReferences": len(orphaned_pg_ids),
            },
        }

        return response(200, export_data)

    except Exception as e:
        print(f"Error exporting configuration: {e}")
        import traceback

        traceback.print_exc()
        return response(500, {"error": str(e)})


def handle_user_permissions(event: Dict) -> Dict:
    """Return user roles and permissions based on Cognito groups"""
    try:
        print("🔍 Processing user permissions request")

        # Import RBAC middleware (only available in API Gateway mode)
        try:
            from shared.rbac_middleware import (
                get_user_from_event,
                get_user_roles,
                get_user_permissions as get_perms,
            )

            print("✅ RBAC middleware imported successfully")
        except ImportError as ie:
            print(f"❌ Import error: {ie}")
            return response(
                500,
                {
                    "error": "Import Error",
                    "message": f"Failed to import RBAC middleware: {str(ie)}",
                },
            )

        # Extract user information from the event
        user = get_user_from_event(event)
        print(f"🔍 User extracted: {user}")

        # Get user roles and permissions
        user_roles = get_user_roles(user)
        user_permissions = get_perms(user)

        print(f"🔐 User roles: {[role.value for role in user_roles]}")
        print(
            f"🔑 User permissions: {[perm.value for perm in user_permissions]}"
        )

        return response(
            200,
            {
                "user": {
                    "email": user.get("email"),
                    "userId": user.get("userId"),
                    "username": user.get("username"),
                    "groups": user.get("groups", []),
                },
                "roles": [role.value for role in user_roles],
                "permissions": [perm.value for perm in user_permissions],
            },
        )

    except Exception as e:
        print(f"Error in handle_user_permissions: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            {
                "error": "Internal Server Error",
                "message": f"Failed to get user permissions: {str(e)}",
            },
        )


def handle_user_profile(event: Dict) -> Dict:
    """Return user profile information from Cognito claims"""
    try:
        print("🔍 Processing user profile request")

        # Import RBAC middleware (only available in API Gateway mode)
        try:
            from shared.rbac_middleware import get_user_from_event

            print("✅ RBAC middleware imported successfully")
        except ImportError as ie:
            print(f"❌ Import error: {ie}")
            return response(
                500,
                {
                    "error": "Import Error",
                    "message": f"Failed to import RBAC middleware: {str(ie)}",
                },
            )

        # Extract user information from the event
        user = get_user_from_event(event)
        print(f"🔍 User profile extracted: {user}")

        return response(
            200,
            {
                "email": user.get("email"),
                "userId": user.get("userId"),
                "username": user.get("username"),
                "groups": user.get("groups", []),
                "emailVerified": user.get("emailVerified", False),
                "name": user.get("name"),
                "givenName": user.get("givenName"),
                "familyName": user.get("familyName"),
            },
        )

    except Exception as e:
        print(f"Error in handle_user_profile: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            {
                "error": "Internal Server Error",
                "message": f"Failed to get user profile: {str(e)}",
            },
        )


def handle_user_roles(event: Dict) -> Dict:
    """Return user roles based on Cognito groups"""
    try:
        print("🔍 Processing user roles request")

        # Import RBAC middleware (only available in API Gateway mode)
        try:
            from shared.rbac_middleware import (
                get_user_from_event,
                get_user_roles,
            )

            print("✅ RBAC middleware imported successfully")
        except ImportError as ie:
            print(f"❌ Import error: {ie}")
            return response(
                500,
                {
                    "error": "Import Error",
                    "message": f"Failed to import RBAC middleware: {str(ie)}",
                },
            )

        # Extract user information from the event
        user = get_user_from_event(event)
        print(f"🔍 User extracted: {user}")

        # Get user roles
        user_roles = get_user_roles(user)

        print(f"🔐 User roles: {[role.value for role in user_roles]}")

        return response(
            200,
            {
                "user": {
                    "email": user.get("email"),
                    "userId": user.get("userId"),
                    "username": user.get("username"),
                    "groups": user.get("groups", []),
                },
                "roles": [role.value for role in user_roles],
            },
        )

    except Exception as e:
        print(f"Error in handle_user_roles: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            {
                "error": "Internal Server Error",
                "message": f"Failed to get user roles: {str(e)}",
            },
        )


# ============================================================================
# Query Functions (Batch 7 Migration)
# ============================================================================


def get_protection_group_servers(pg_id: str, region: str) -> Dict:
    """
    Get servers that belong to a specific Protection Group.

    For tag-based Protection Groups, this resolves the tags to actual servers.

    Args:
    - pg_id: Protection Group ID
    - region: AWS region

    Returns:
    - Response with servers from the Protection Group (resolved from tags)
    """
    print(f"Getting servers for Protection Group: {pg_id}")

    try:
        # 1. Get the Protection Group
        result = protection_groups_table.get_item(Key={"groupId": pg_id})

        if "Item" not in result:
            return response(
                404,
                {
                    "error": "PROTECTION_GROUP_NOT_FOUND",
                    "message": f"Protection Group {pg_id} not found",
                },
            )

        pg = result["Item"]
        selection_tags = pg.get("serverSelectionTags", {})

        if not selection_tags:
            return response(
                200,
                {
                    "region": region,
                    "protectionGroupId": pg_id,
                    "protectionGroupName": pg.get("groupName"),
                    "initialized": True,
                    "servers": [],
                    "totalCount": 0,
                    "message": "No server selection tags defined",
                },
            )

        # 2. Resolve servers by tags
        # Extract account context from Protection Group
        account_context = None
        if pg.get("accountId"):
            account_context = {
                "accountId": pg.get("accountId"),
                "assumeRoleName": pg.get("assumeRoleName"),
            }
        resolved_servers = query_drs_servers_by_tags(
            region, selection_tags, account_context
        )

        if not resolved_servers:
            return response(
                200,
                {
                    "region": region,
                    "protectionGroupId": pg_id,
                    "protectionGroupName": pg.get("groupName"),
                    "initialized": True,
                    "servers": [],
                    "totalCount": 0,
                    "tags": selection_tags,
                    "message": "No servers match the specified tags",
                },
            )

        # Return resolved servers
        return response(
            200,
            {
                "region": region,
                "protectionGroupId": pg_id,
                "protectionGroupName": pg.get("groupName"),
                "initialized": True,
                "servers": resolved_servers,
                "totalCount": len(resolved_servers),
                "tags": selection_tags,
                "resolvedAt": int(time.time()),
            },
        )

    except Exception as e:
        print(f"Error getting Protection Group servers: {str(e)}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            {
                "error": "INTERNAL_ERROR",
                "message": f"Failed to get Protection Group servers: {str(e)}",
            },
        )


def get_drs_source_server_details(
    account_id: str, region: str, server_ids: List[str]
) -> List[Dict]:
    """Get detailed information about DRS source servers"""
    try:
        drs_client = boto3.client("drs", region_name=region)

        servers_response = drs_client.describe_source_servers()
        all_servers = servers_response.get("items", [])

        # Filter to requested servers
        details = []
        for server in all_servers:
            if server["sourceServerID"] in server_ids:
                details.append(
                    {
                        "sourceServerId": server["sourceServerID"],
                        "Hostname": server.get("sourceProperties", {})
                        .get("identificationHints", {})
                        .get("hostname", "Unknown"),
                        "ReplicationStatus": server.get(
                            "dataReplicationInfo", {}
                        ).get("dataReplicationState", "Unknown"),
                        "LastSeenTime": server.get("sourceProperties", {}).get(
                            "lastUpdatedDateTime", ""
                        ),
                        "LifeCycleState": server.get("lifeCycle", {}).get(
                            "state", "Unknown"
                        ),
                    }
                )

        return details

    except Exception as e:
        print(f"Error getting server details: {str(e)}")
        return []


# ============================================================================
# Staging Account Validation Functions
# ============================================================================


def handle_validate_staging_account(query_params: Dict) -> Dict:
    """
    Validate staging account access and DRS status.

    Validates that:
    1. Role can be assumed in staging account
    2. DRS is initialized in the specified region
    3. Current server counts can be retrieved

    Args:
        query_params: Dict with:
            - accountId: Staging account ID (12-digit string)
            - roleArn: IAM role ARN for cross-account access
            - externalId: External ID for role assumption
            - region: AWS region to validate

    Returns:
        Dict with validation results:
        {
            "valid": bool,
            "roleAccessible": bool,
            "drsInitialized": bool,
            "currentServers": int,
            "replicatingServers": int,
            "totalAfter": int,  # Projected combined capacity
            "error": str  # Only present if validation fails
        }

    Requirements: 3.1, 3.2, 3.3, 3.4, 7.3
    """
    try:
        # Extract and validate required parameters
        account_id = query_params.get("accountId")
        role_arn = query_params.get("roleArn")
        external_id = query_params.get("externalId")
        region = query_params.get("region")

        # Validate required fields
        if not account_id:
            return response(
                400,
                {"valid": False, "error": "Missing required field: accountId"},
            )

        # Construct roleArn if not provided
        if not role_arn:
            from shared.account_utils import construct_role_arn

            role_arn = construct_role_arn(account_id)
            print(
                f"Constructed standardized role ARN for validation: {role_arn}"
            )
        else:
            print(f"Using provided role ARN for validation: {role_arn}")

        if not external_id:
            return response(
                400,
                {
                    "valid": False,
                    "error": "Missing required field: externalId",
                },
            )

        if not region:
            return response(
                400,
                {"valid": False, "error": "Missing required field: region"},
            )

        # Validate account ID format (12 digits)
        if not account_id.isdigit() or len(account_id) != 12:
            return response(
                400,
                {
                    "valid": False,
                    "error": f"Invalid account ID format: {account_id}. Must be 12-digit string.",
                },
            )

        # Step 1: Attempt to assume role in staging account
        print(f"Validating staging account {account_id} in region {region}")
        print(f"Attempting to assume role: {role_arn}")

        try:
            sts_client = boto3.client("sts")
            assumed_role = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName="drs-orchestration-staging-validation",
                ExternalId=external_id,
                DurationSeconds=900,  # 15 minutes
            )

            credentials = assumed_role["Credentials"]
            print(f"Successfully assumed role in account {account_id}")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            print(f"Failed to assume role: {error_code} - {error_message}")

            if error_code == "AccessDenied":
                return response(
                    200,
                    {
                        "valid": False,
                        "roleAccessible": False,
                        "error": "Unable to assume role: Access Denied. Verify role trust policy includes this account and external ID is correct.",
                    },
                )
            elif error_code == "InvalidClientTokenId":
                return response(
                    200,
                    {
                        "valid": False,
                        "roleAccessible": False,
                        "error": "Invalid credentials. Verify role ARN is correct.",
                    },
                )
            else:
                return response(
                    200,
                    {
                        "valid": False,
                        "roleAccessible": False,
                        "error": f"Role assumption failed: {error_message}",
                    },
                )

        # Step 2: Create DRS client with assumed credentials
        drs_client = boto3.client(
            "drs",
            region_name=region,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
        )

        # Step 3: Check DRS initialization and count servers
        try:
            print(f"Checking DRS initialization in {region}")

            # Count servers using the helper function
            server_counts = _count_drs_servers(drs_client, account_id)

            total_servers = server_counts["totalServers"]
            replicating_servers = server_counts["replicatingServers"]

            print(
                f"DRS initialized. Total servers: {total_servers}, Replicating: {replicating_servers}"
            )

            # Calculate projected combined capacity
            # Note: This is a simplified calculation. In production, you'd query
            # the target account's current capacity and add this staging account's capacity.
            # For validation purposes, we just return the staging account's current count.
            total_after = replicating_servers  # Simplified - would add target account count

            return response(
                200,
                {
                    "valid": True,
                    "roleAccessible": True,
                    "drsInitialized": True,
                    "currentServers": total_servers,
                    "replicatingServers": replicating_servers,
                    "totalAfter": total_after,
                },
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            print(f"DRS error: {error_code} - {error_message}")

            if (
                error_code == "UninitializedAccountException"
                or "not initialized" in error_message.lower()
            ):
                return response(
                    200,
                    {
                        "valid": False,
                        "roleAccessible": True,
                        "drsInitialized": False,
                        "error": f"DRS is not initialized in region {region}. Initialize DRS in the staging account before adding it.",
                    },
                )
            else:
                return response(
                    200,
                    {
                        "valid": False,
                        "roleAccessible": True,
                        "drsInitialized": False,
                        "error": f"DRS query failed: {error_message}",
                    },
                )

    except Exception as e:
        print(f"Unexpected error validating staging account: {e}")
        import traceback

        traceback.print_exc()

        return response(
            500, {"valid": False, "error": f"Internal error: {str(e)}"}
        )


# ============================================================================
# Multi-Account Capacity Query Functions
# ============================================================================


def query_account_capacity(account_config: Dict) -> Dict:
    """
    Query DRS capacity for a single account across all regions.

    This function:
    1. Assumes role in the account (if not the current account)
    2. Queries all DRS-enabled regions concurrently
    3. Handles uninitialized regions gracefully (returns zero servers)
    4. Aggregates regional results

    Args:
        account_config: Dict with:
            - accountId: Account ID (12-digit string)
            - accountName: Human-readable account name
            - accountType: 'target' or 'staging'
            - roleArn: IAM role ARN (optional, not needed for current account)
            - externalId: External ID (optional, not needed for current account)

    Returns:
        Dict with account capacity:
        {
            "accountId": str,
            "accountName": str,
            "accountType": str,
            "replicatingServers": int,
            "totalServers": int,
            "regionalBreakdown": [
                {
                    "region": str,
                    "totalServers": int,
                    "replicatingServers": int
                }
            ],
            "accessible": bool,
            "error": str  # Only present if query fails
        }

    Requirements: 9.2, 9.3, 9.4
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    account_id = account_config.get("accountId")
    account_name = account_config.get("accountName", "Unknown")
    account_type = account_config.get("accountType", "staging")
    role_arn = account_config.get("roleArn")
    external_id = account_config.get("externalId")

    # Construct roleArn if not present (for cross-account access)
    if not role_arn and external_id:
        from shared.account_utils import construct_role_arn

        role_arn = construct_role_arn(account_id)
        print(
            f"Constructed standardized role ARN for account {account_id}: {role_arn}"
        )
    elif role_arn:
        print(f"Using provided role ARN for account {account_id}: {role_arn}")

    print(f"Querying capacity for account {account_id} ({account_name})")

    try:
        # Step 1: Get credentials for the account
        if role_arn and external_id:
            # Cross-account access - assume role
            print(f"Assuming role {role_arn} in account {account_id}")

            try:
                sts_client = boto3.client("sts")
                assumed_role = sts_client.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName="drs-orchestration-capacity-query",
                    ExternalId=external_id,
                    DurationSeconds=900,  # 15 minutes
                )

                credentials = assumed_role["Credentials"]
                print(f"Successfully assumed role in account {account_id}")

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                error_message = e.response["Error"]["Message"]

                print(
                    f"Failed to assume role in account {account_id}: {error_code} - {error_message}"
                )

                return {
                    "accountId": account_id,
                    "accountName": account_name,
                    "accountType": account_type,
                    "replicatingServers": 0,
                    "totalServers": 0,
                    "regionalBreakdown": [],
                    "accessible": False,
                    "error": f"Role assumption failed: {error_message}",
                }
        else:
            # Current account - use default credentials
            credentials = None
            print(f"Using default credentials for account {account_id}")

        # Step 2: Query all DRS regions concurrently
        def query_region(region: str) -> Dict:
            """Query a single region for DRS capacity."""
            try:
                # Create DRS client for this region
                if credentials:
                    drs_client = boto3.client(
                        "drs",
                        region_name=region,
                        aws_access_key_id=credentials["AccessKeyId"],
                        aws_secret_access_key=credentials["SecretAccessKey"],
                        aws_session_token=credentials["SessionToken"],
                    )
                else:
                    drs_client = boto3.client("drs", region_name=region)

                # Count servers in this region
                server_counts = _count_drs_servers(drs_client, account_id)

                return {
                    "region": region,
                    "totalServers": server_counts["totalServers"],
                    "replicatingServers": server_counts["replicatingServers"],
                    "error": None,
                }

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                error_message = e.response["Error"]["Message"]

                # Handle uninitialized regions gracefully
                if (
                    error_code == "UninitializedAccountException"
                    or "not initialized" in error_message.lower()
                ):
                    print(
                        f"DRS not initialized in {region} for account {account_id} - treating as zero servers"
                    )
                    return {
                        "region": region,
                        "totalServers": 0,
                        "replicatingServers": 0,
                        "error": None,
                    }
                else:
                    print(
                        f"Error querying {region} for account {account_id}: {error_code} - {error_message}"
                    )
                    return {
                        "region": region,
                        "totalServers": 0,
                        "replicatingServers": 0,
                        "error": error_message,
                    }

            except Exception as e:
                print(
                    f"Unexpected error querying {region} for account {account_id}: {e}"
                )
                return {
                    "region": region,
                    "totalServers": 0,
                    "replicatingServers": 0,
                    "error": str(e),
                }

        # Query all regions in parallel
        regional_results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(query_region, region): region
                for region in DRS_REGIONS
            }

            for future in as_completed(futures):
                region = futures[future]
                try:
                    result = future.result()
                    regional_results.append(result)
                except Exception as e:
                    print(f"Failed to get result for region {region}: {e}")
                    regional_results.append(
                        {
                            "region": region,
                            "totalServers": 0,
                            "replicatingServers": 0,
                            "error": str(e),
                        }
                    )

        # Step 3: Aggregate results
        total_servers = sum(r["totalServers"] for r in regional_results)
        replicating_servers = sum(
            r["replicatingServers"] for r in regional_results
        )

        # Filter out regions with no servers for cleaner output
        regional_breakdown = [
            r for r in regional_results if r["totalServers"] > 0 or r["error"]
        ]

        print(
            f"Account {account_id} capacity: {replicating_servers} replicating, {total_servers} total"
        )

        return {
            "accountId": account_id,
            "accountName": account_name,
            "accountType": account_type,
            "replicatingServers": replicating_servers,
            "totalServers": total_servers,
            "regionalBreakdown": regional_breakdown,
            "accessible": True,
        }

    except Exception as e:
        print(f"Unexpected error querying account {account_id}: {e}")
        import traceback

        traceback.print_exc()

        return {
            "accountId": account_id,
            "accountName": account_name,
            "accountType": account_type,
            "replicatingServers": 0,
            "totalServers": 0,
            "regionalBreakdown": [],
            "accessible": False,
            "error": f"Internal error: {str(e)}",
        }


def query_all_accounts_parallel(
    target_account: Dict, staging_accounts: List[Dict]
) -> List[Dict]:
    """
    Query DRS capacity for target account and all staging accounts in parallel.

    This function:
    1. Queries target account and all staging accounts concurrently
    2. Handles role assumption failures gracefully (marks as inaccessible)
    3. Continues querying remaining accounts on individual failures
    4. Returns list of account capacity results

    Args:
        target_account: Dict with target account configuration
        staging_accounts: List of staging account configurations

    Returns:
        List of account capacity results (one per account)

    Requirements: 9.1, 9.5, 9.6
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print(
        f"Querying capacity for {len(staging_accounts) + 1} accounts in parallel"
    )

    # Prepare account configurations
    all_accounts = []

    # Add target account
    target_config = {
        "accountId": target_account.get("accountId"),
        "accountName": target_account.get("accountName", "Target Account"),
        "accountType": "target",
        "roleArn": target_account.get("roleArn"),
        "externalId": target_account.get("externalId"),
    }
    all_accounts.append(target_config)

    # Add staging accounts
    for staging in staging_accounts:
        staging_config = {
            "accountId": staging.get("accountId"),
            "accountName": staging.get("accountName", "Unknown Staging"),
            "accountType": "staging",
            "roleArn": staging.get("roleArn"),
            "externalId": staging.get("externalId"),
        }
        all_accounts.append(staging_config)

    # Query all accounts in parallel
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(query_account_capacity, account): account
            for account in all_accounts
        }

        for future in as_completed(futures):
            account = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(
                    f"Failed to query account {account.get('accountId')}: {e}"
                )
                # Return error result for this account
                results.append(
                    {
                        "accountId": account.get("accountId"),
                        "accountName": account.get("accountName", "Unknown"),
                        "accountType": account.get("accountType", "staging"),
                        "replicatingServers": 0,
                        "totalServers": 0,
                        "regionalBreakdown": [],
                        "accessible": False,
                        "error": f"Query failed: {str(e)}",
                    }
                )

    print(f"Completed querying {len(results)} accounts")
    return results


def calculate_combined_metrics(account_results: List[Dict]) -> Dict:
    """
    Calculate combined capacity metrics from account query results.

    This function:
    1. Sums replicating servers across all accessible accounts
    2. Calculates maximum capacity (num_accounts × 300)
    3. Calculates percentage used
    4. Calculates available slots

    Args:
        account_results: List of account capacity results from query_all_accounts_parallel

    Returns:
        Dict with combined metrics:
        {
            "totalReplicating": int,
            "totalServers": int,
            "maxReplicating": int,
            "percentUsed": float,
            "availableSlots": int,
            "accessibleAccounts": int,
            "totalAccounts": int
        }

    Requirements: 4.2, 4.3, 9.6
    """
    # Count accessible accounts
    accessible_accounts = [
        a for a in account_results if a.get("accessible", False)
    ]
    total_accounts = len(account_results)

    # Sum servers across all accessible accounts
    total_replicating = sum(
        a.get("replicatingServers", 0) for a in accessible_accounts
    )

    total_servers = sum(a.get("totalServers", 0) for a in accessible_accounts)

    # Calculate maximum capacity
    # Each account can have 300 replicating servers (hard limit per account)
    max_replicating = len(accessible_accounts) * 300

    # Calculate percentage used
    percent_used = (
        (total_replicating / max_replicating * 100)
        if max_replicating > 0
        else 0.0
    )

    # Calculate available slots
    available_slots = max_replicating - total_replicating

    print(
        f"Combined metrics: {total_replicating}/{max_replicating} ({percent_used:.1f}%) "
        f"across {len(accessible_accounts)} account(s)"
    )

    return {
        "totalReplicating": total_replicating,
        "totalServers": total_servers,
        "maxReplicating": max_replicating,
        "percentUsed": round(percent_used, 2),
        "availableSlots": available_slots,
        "accessibleAccounts": len(accessible_accounts),
        "totalAccounts": total_accounts,
    }


def calculate_account_status(replicating_servers: int) -> str:
    """
    Calculate status for a single account based on server count.

    Status thresholds:
    - OK: 0-200 servers (0-67%)
    - INFO: 200-225 servers (67-75%)
    - WARNING: 225-250 servers (75-83%)
    - CRITICAL: 250-280 servers (83-93%)
    - HYPER-CRITICAL: 280-300 servers (93-100%)

    Args:
        replicating_servers: Number of replicating servers in account

    Returns:
        Status string: OK, INFO, WARNING, CRITICAL, or HYPER-CRITICAL

    Requirements: 5.3, 5.4, 5.5, 5.6
    """
    if replicating_servers < 200:
        return "OK"
    elif replicating_servers < 225:
        return "INFO"
    elif replicating_servers < 250:
        return "WARNING"
    elif replicating_servers < 280:
        return "CRITICAL"
    else:
        return "HYPER-CRITICAL"


def calculate_combined_status(
    total_replicating: int, num_accounts: int
) -> str:
    """
    Calculate combined status based on total replicating servers.

    Considers both operational capacity (250 per account) and hard
    capacity (300 per account).

    Args:
        total_replicating: Total replicating servers across all accounts
        num_accounts: Number of accessible accounts

    Returns:
        Status string: OK, INFO, WARNING, CRITICAL, or HYPER-CRITICAL

    Requirements: 4.4
    """
    if num_accounts == 0:
        return "OK"

    operational_capacity = num_accounts * 250
    hard_capacity = num_accounts * 300

    # Check against hard capacity first
    if total_replicating >= hard_capacity:
        return "HYPER-CRITICAL"
    elif total_replicating >= operational_capacity:
        return "CRITICAL"

    # Calculate percentage of operational capacity
    percent_of_operational = (total_replicating / operational_capacity) * 100

    if percent_of_operational >= 93:
        return "WARNING"
    elif percent_of_operational >= 83:
        return "INFO"
    else:
        return "OK"


def generate_warnings(
    account_results: List[Dict], combined_metrics: Dict
) -> List[str]:
    """
    Generate capacity warnings based on thresholds.

    Generates per-account warnings and combined capacity warnings with
    actionable guidance.

    Warning thresholds:
    - INFO: 200-225 servers (67-75%) - Monitor capacity
    - WARNING: 225-250 servers (75-83%) - Plan to add staging account
    - CRITICAL: 250-280 servers (83-93%) - Add staging account
      immediately
    - HYPER-CRITICAL: 280-300 servers (93-100%) - Immediate action
      required

    Args:
        account_results: List of account capacity results
        combined_metrics: Combined capacity metrics

    Returns:
        List of warning messages with actionable guidance

    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
    """
    warnings = []

    # Generate per-account warnings
    for account in account_results:
        if not account.get("accessible", False):
            continue

        account_id = account.get("accountId", "Unknown")
        account_name = account.get("accountName", "Unknown")
        replicating = account.get("replicatingServers", 0)
        status = calculate_account_status(replicating)

        if status == "INFO":
            warnings.append(
                f"INFO: Account {account_name} ({account_id}) has "
                f"{replicating} replicating servers (67-75% capacity). "
                f"Monitor capacity usage."
            )
        elif status == "WARNING":
            warnings.append(
                f"WARNING: Account {account_name} ({account_id}) has "
                f"{replicating} replicating servers (75-83% capacity). "
                f"Plan to add a staging account soon."
            )
        elif status == "CRITICAL":
            warnings.append(
                f"CRITICAL: Account {account_name} ({account_id}) has "
                f"{replicating} replicating servers (83-93% capacity). "
                f"Add a staging account immediately to avoid hitting "
                f"the 300-server limit."
            )
        elif status == "HYPER-CRITICAL":
            warnings.append(
                f"HYPER-CRITICAL: Account {account_name} ({account_id}) "
                f"has {replicating} replicating servers (93-100% "
                f"capacity). Immediate action required - you are "
                f"approaching the hard limit of 300 servers per account."
            )

    # Generate combined capacity warnings
    total_replicating = combined_metrics.get("totalReplicating", 0)
    num_accounts = combined_metrics.get("accessibleAccounts", 0)

    if num_accounts > 0:
        operational_capacity = num_accounts * 250
        hard_capacity = num_accounts * 300
        combined_status = calculate_combined_status(
            total_replicating, num_accounts
        )

        if combined_status == "INFO":
            warnings.append(
                f"INFO: Combined capacity at {total_replicating}/"
                f"{operational_capacity} servers (83%+ of operational "
                f"limit). Monitor overall capacity usage."
            )
        elif combined_status == "WARNING":
            warnings.append(
                f"WARNING: Combined capacity at {total_replicating}/"
                f"{operational_capacity} servers (93%+ of operational "
                f"limit). Consider adding another staging account."
            )
        elif combined_status == "CRITICAL":
            warnings.append(
                f"CRITICAL: Combined capacity at {total_replicating}/"
                f"{hard_capacity} servers. You have exceeded the "
                f"operational limit of {operational_capacity} servers. "
                f"Add staging accounts immediately."
            )
        elif combined_status == "HYPER-CRITICAL":
            warnings.append(
                f"HYPER-CRITICAL: Combined capacity at {total_replicating}"
                f"/{hard_capacity} servers. You are at or near the hard "
                f"limit. Immediate action required - add staging accounts "
                f"or reduce server count."
            )

    return warnings


def calculate_recovery_capacity(target_account_servers: int) -> Dict:
    """
    Calculate recovery capacity metrics for the target account.

    Recovery capacity is based only on the target account (not staging
    accounts) and measures against the 4,000 instance recovery limit.

    Status thresholds:
    - OK: < 3,200 servers (< 80% of 4,000)
    - WARNING: 3,200-3,600 servers (80-90%)
    - CRITICAL: > 3,600 servers (> 90%)

    Args:
        target_account_servers: Number of replicating servers in target
            account only

    Returns:
        Dictionary containing:
        - currentServers: Number of servers in target account
        - maxRecoveryInstances: Maximum recovery instances (4,000)
        - percentUsed: Percentage of recovery capacity used
        - availableSlots: Available recovery slots
        - status: OK, WARNING, or CRITICAL

    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
    """
    max_recovery_instances = 4000
    percent_used = (target_account_servers / max_recovery_instances) * 100
    available_slots = max_recovery_instances - target_account_servers

    # Determine status based on thresholds
    if percent_used < 80:
        status = "OK"
    elif percent_used < 90:
        status = "WARNING"
    else:
        status = "CRITICAL"

    return {
        "currentServers": target_account_servers,
        "maxRecoveryInstances": max_recovery_instances,
        "percentUsed": round(percent_used, 2),
        "availableSlots": available_slots,
        "status": status,
    }


def handle_discover_staging_accounts(query_params: Dict) -> Dict:
    """
    Discover staging accounts by querying DRS extended source servers.

    This operation:
    1. Queries DRS describe_source_servers in target account
    2. Extracts unique staging account IDs from extended source server ARNs
    3. For each staging account, queries its capacity
    4. Returns list of discovered staging accounts with their details

    Args:
        query_params: Dict with:
            - targetAccountId: Target account ID (12-digit string)

    Returns:
        Dict with discovered staging accounts:
        {
            "targetAccountId": str,
            "stagingAccounts": [
                {
                    "accountId": str,
                    "replicatingServers": int,
                    "totalServers": int,
                    "status": "discovered"
                }
            ]
        }
    """
    try:
        # Step 1: Validate required parameters
        target_account_id = query_params.get("targetAccountId")

        if not target_account_id:
            return response(
                400,
                {"error": "Missing required field: targetAccountId"},
            )

        # Validate account ID format (12 digits)
        if not target_account_id.isdigit() or len(target_account_id) != 12:
            return response(
                400,
                {"error": f"Invalid account ID format: {target_account_id}"},
            )

        print(
            f"Discovering staging accounts for target account {target_account_id}"
        )

        # Step 2: Get target account configuration for credentials
        if not target_accounts_table:
            return response(
                500,
                {"error": "Target accounts table not configured"},
            )

        account_result = target_accounts_table.get_item(
            Key={"accountId": target_account_id}
        )

        if "Item" not in account_result:
            return response(
                404,
                {"error": f"Target account {target_account_id} not found"},
            )

        target_account = account_result["Item"]

        # Step 3: Query DRS in all regions to find extended source servers
        discovered_staging_accounts = {}  # accountId -> server count

        for region in DRS_REGIONS:
            try:
                # Get DRS client for this region
                regional_drs = get_drs_client(
                    region,
                    target_account.get("roleArn"),
                    target_account.get("externalId"),
                )

                # Query source servers
                paginator = regional_drs.get_paginator(
                    "describe_source_servers"
                )

                for page in paginator.paginate():
                    for server in page.get("items", []):
                        # Extract account ID from ARN
                        # ARN format: arn:aws:drs:region:account:source-server/id
                        server_arn = server.get("arn", "")
                        if server_arn:
                            arn_parts = server_arn.split(":")
                            if len(arn_parts) >= 5:
                                server_account_id = arn_parts[4]

                                # If account ID differs from target, it's a staging account
                                if server_account_id != target_account_id:
                                    if (
                                        server_account_id
                                        not in discovered_staging_accounts
                                    ):
                                        discovered_staging_accounts[
                                            server_account_id
                                        ] = 0
                                    discovered_staging_accounts[
                                        server_account_id
                                    ] += 1

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "UninitializedAccountException":
                    # DRS not initialized in this region - skip
                    continue
                else:
                    print(f"Error querying DRS in {region}: {error_code}")
                    continue
            except Exception as e:
                print(f"Unexpected error querying {region}: {e}")
                continue

        # Step 4: Build response with discovered staging accounts
        staging_accounts_list = []
        for account_id, server_count in discovered_staging_accounts.items():
            staging_accounts_list.append(
                {
                    "accountId": account_id,
                    "accountName": f"Staging Account {account_id[-4:]}",
                    "replicatingServers": server_count,
                    "totalServers": server_count,
                    "status": "discovered",
                }
            )

        print(f"Discovered {len(staging_accounts_list)} staging accounts")

        return response(
            200,
            {
                "targetAccountId": target_account_id,
                "stagingAccounts": staging_accounts_list,
            },
        )

    except Exception as e:
        print(f"Error discovering staging accounts: {e}")
        import traceback

        traceback.print_exc()
        return response(
            500,
            {"error": f"Failed to discover staging accounts: {str(e)}"},
        )


def handle_get_combined_capacity(query_params: Dict) -> Dict:
    """
    Get combined capacity across target and staging accounts.

    This operation:
    1. Retrieves target account configuration from DynamoDB
    2. Extracts staging accounts list (defaults to empty list if not present)
    3. Queries all accounts in parallel (target + staging)
    4. Calculates combined metrics
    5. Calculates per-account status and warnings
    6. Calculates recovery capacity
    7. Returns complete CombinedCapacityData response

    Args:
        query_params: Dict with:
            - targetAccountId: Target account ID (12-digit string)

    Returns:
        Dict with combined capacity data:
        {
            "combined": {
                "totalReplicating": int,
                "maxReplicating": int,
                "percentUsed": float,
                "status": str,
                "message": str
            },
            "accounts": [
                {
                    "accountId": str,
                    "accountName": str,
                    "accountType": str,
                    "replicatingServers": int,
                    "totalServers": int,
                    "maxReplicating": int,
                    "percentUsed": float,
                    "availableSlots": int,
                    "status": str,
                    "regionalBreakdown": [...],
                    "warnings": [...]
                }
            ],
            "recoveryCapacity": {
                "currentServers": int,
                "maxRecoveryInstances": int,
                "percentUsed": float,
                "availableSlots": int,
                "status": str
            },
            "warnings": [...]
        }

    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 8.5, 10.1
    """
    try:
        # Step 1: Validate required parameters
        target_account_id = query_params.get("targetAccountId")

        if not target_account_id:
            return response(
                400,
                {"error": "Missing required field: targetAccountId"},
            )

        # Validate account ID format (12 digits)
        if not target_account_id.isdigit() or len(target_account_id) != 12:
            return response(
                400,
                {
                    "error": f"Invalid account ID format: {target_account_id}. Must be 12-digit string."
                },
            )

        print(
            f"Querying combined capacity for target account {target_account_id}"
        )

        # Step 2: Retrieve target account configuration from DynamoDB
        if not target_accounts_table:
            return response(
                500,
                {"error": "Target accounts table not configured"},
            )

        try:
            account_result = target_accounts_table.get_item(
                Key={"accountId": target_account_id}
            )

            if "Item" not in account_result:
                return response(
                    404,
                    {
                        "error": "TARGET_ACCOUNT_NOT_FOUND",
                        "message": f"Target account {target_account_id} not found",
                    },
                )

            target_account = account_result["Item"]
            print(f"Found target account: {target_account.get('accountName')}")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            print(f"DynamoDB error: {error_code} - {error_message}")

            return response(
                500,
                {
                    "error": "Failed to retrieve target account",
                    "message": error_message,
                },
            )

        # Step 3: Extract staging accounts list (default to empty list if not present)
        # Requirement 8.5: When stagingAccounts attribute does not exist, treat as empty list
        staging_accounts = target_account.get("stagingAccounts", [])

        print(
            f"Found {len(staging_accounts)} staging accounts for target {target_account_id}"
        )

        # Step 4: Query all accounts in parallel (target + staging)
        account_results = query_all_accounts_parallel(
            target_account, staging_accounts
        )

        print(f"Queried {len(account_results)} accounts")

        # Step 5: Calculate combined metrics
        combined_metrics = calculate_combined_metrics(account_results)

        # Step 6: Calculate per-account status and warnings
        # Add status, percentage, available slots, and warnings to each account
        # Each account has its own 300 server replication limit
        for account in account_results:
            replicating = account.get("replicatingServers", 0)
            account_type = account.get("accountType", "staging")

            # Each account (target or staging) has 300 server limit
            max_replicating = 300

            # Calculate status based on account's own replicating count
            account["status"] = calculate_account_status(replicating)

            # Calculate percentage and available slots for this account
            account["maxReplicating"] = max_replicating
            account["percentUsed"] = round(
                (
                    (replicating / max_replicating * 100)
                    if max_replicating > 0
                    else 0.0
                ),
                2,
            )
            account["availableSlots"] = max_replicating - replicating

            # Generate warnings based on account's own capacity
            account_warnings = []
            status = account["status"]

            if status == "INFO":
                account_warnings.append(
                    f"Monitor capacity - at {replicating} servers (67-75%)"
                )
            elif status == "WARNING":
                account_warnings.append(
                    f"Plan capacity - at {replicating} servers (75-83%)"
                )
            elif status == "CRITICAL":
                account_warnings.append(
                    f"Add capacity immediately - at {replicating} servers (83-93%)"
                )
            elif status == "HYPER-CRITICAL":
                account_warnings.append(
                    f"Immediate action required - at {replicating} servers (93-100%)"
                )

            account["warnings"] = account_warnings

        # Step 7: Calculate recovery capacity (target account only)
        # Find target account in results
        target_account_result = next(
            (a for a in account_results if a.get("accountType") == "target"),
            None,
        )

        if target_account_result:
            target_replicating = target_account_result.get(
                "replicatingServers", 0
            )
        else:
            target_replicating = 0

        recovery_capacity = calculate_recovery_capacity(target_replicating)

        # Step 7.5: Get concurrent jobs and servers in jobs metrics
        # Query DRS jobs in target account's primary region (us-west-2)
        try:
            # Get target account's primary region from regional breakdown
            primary_region = "us-west-2"  # Default
            if target_account_result and target_account_result.get(
                "regionalBreakdown"
            ):
                # Use region with most servers
                regional_breakdown = target_account_result.get(
                    "regionalBreakdown", []
                )
                if regional_breakdown:
                    primary_region = max(
                        regional_breakdown,
                        key=lambda r: r.get("replicatingServers", 0),
                    ).get("region", "us-west-2")

            # Create account context for target account
            account_context = {
                "accountId": target_account_id,
                "assumeRoleName": target_account.get("assumeRoleName"),
                "externalId": target_account.get("externalId"),
            }

            # Create DRS client with assumed role credentials
            drs_client = None
            role_arn = target_account.get("roleArn")
            external_id = target_account.get("externalId")

            if role_arn and external_id:
                try:
                    sts_client = boto3.client("sts")
                    assumed_role = sts_client.assume_role(
                        RoleArn=role_arn,
                        RoleSessionName="drs-orchestration-jobs-query",
                        ExternalId=external_id,
                        DurationSeconds=900,
                    )
                    credentials = assumed_role["Credentials"]

                    # Create DRS client with assumed role credentials
                    drs_client = boto3.client(
                        "drs",
                        region_name=primary_region,
                        aws_access_key_id=credentials["AccessKeyId"],
                        aws_secret_access_key=credentials["SecretAccessKey"],
                        aws_session_token=credentials["SessionToken"],
                    )
                except Exception as e:
                    print(
                        f"Warning: Could not assume role for jobs query: {e}"
                    )
                    drs_client = None

            # Get concurrent jobs info (pass DRS client)
            jobs_info = validate_concurrent_jobs(primary_region, drs_client)

            # Get servers in active jobs (pass DRS client)
            servers_in_jobs = validate_servers_in_all_jobs(
                primary_region, 0, drs_client
            )

            # Get max servers per job (pass DRS client)
            max_per_job = validate_max_servers_per_job(
                primary_region, drs_client
            )

            concurrent_jobs_data = {
                "current": jobs_info.get("currentJobs", 0),
                "max": jobs_info.get("maxJobs", 20),
                "available": jobs_info.get("availableSlots", 20),
            }

            servers_in_jobs_data = {
                "current": servers_in_jobs.get("currentServersInJobs", 0),
                "max": servers_in_jobs.get("maxServersInJobs", 500),
                "available": servers_in_jobs.get("availableSlots", 500),
            }

            max_per_job_data = {
                "current": max_per_job.get("maxServersInSingleJob", 0),
                "max": max_per_job.get("maxAllowed", 100),
                "available": max_per_job.get("availableSlots", 100),
                "jobId": max_per_job.get("jobId"),
                "status": max_per_job.get("status", "OK"),
                "message": max_per_job.get("message", ""),
            }

        except Exception as e:
            print(f"Warning: Could not fetch jobs metrics: {e}")
            # Default to 0 if we can't fetch jobs data
            concurrent_jobs_data = {
                "current": 0,
                "max": 20,
                "available": 20,
            }
            servers_in_jobs_data = {
                "current": 0,
                "max": 500,
                "available": 500,
            }
            max_per_job_data = {
                "current": 0,
                "max": 100,
                "available": 100,
                "status": "OK",
                "message": "Could not fetch per-job metrics",
            }

        # Step 8: Generate combined warnings
        warnings = generate_warnings(account_results, combined_metrics)

        # Step 9: Calculate combined status
        total_replicating = combined_metrics.get("totalReplicating", 0)
        num_accounts = combined_metrics.get("accessibleAccounts", 0)
        combined_status = calculate_combined_status(
            total_replicating, num_accounts
        )

        # Generate combined status message
        if combined_status == "OK":
            status_message = "Capacity OK"
        elif combined_status == "INFO":
            status_message = "Monitor capacity usage"
        elif combined_status == "WARNING":
            status_message = "Consider adding staging account"
        elif combined_status == "CRITICAL":
            status_message = "Add staging accounts immediately"
        else:  # HYPER-CRITICAL
            status_message = "Immediate action required"

        # Step 10: Build response
        total_replicating = combined_metrics.get("totalReplicating", 0)
        max_replicating = combined_metrics.get("maxReplicating", 0)
        available_slots = max_replicating - total_replicating

        response_data = {
            "combined": {
                "totalReplicating": total_replicating,
                "maxReplicating": max_replicating,
                "percentUsed": combined_metrics.get("percentUsed", 0.0),
                "availableSlots": available_slots,
                "status": combined_status,
                "message": status_message,
            },
            "accounts": account_results,
            "recoveryCapacity": recovery_capacity,
            "concurrentJobs": concurrent_jobs_data,
            "serversInJobs": servers_in_jobs_data,
            "maxServersPerJob": max_per_job_data,
            "warnings": warnings,
        }

        print(
            f"Combined capacity: {response_data['combined']['totalReplicating']}/"
            f"{response_data['combined']['maxReplicating']} "
            f"({response_data['combined']['percentUsed']}%)"
        )

        return response(200, response_data)

    except Exception as e:
        print(f"Error in handle_get_combined_capacity: {e}")
        import traceback

        traceback.print_exc()

        return response(
            500,
            {
                "error": "Internal error",
                "message": str(e),
            },
        )
