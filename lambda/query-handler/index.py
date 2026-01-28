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
    ensure_default_account,
    get_account_name,
    get_target_accounts,
    validate_target_account,
)
from shared.conflict_detection import query_drs_servers_by_tags
from shared.cross_account import create_drs_client, get_current_account_id
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

    Direct Invocation Event (HRP Mode):
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
            # Direct invocation (HRP mode)
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

    else:
        return response(
            404, {"error": "Not Found", "message": f"Path {path} not found"}
        )


def handle_direct_invocation(event, context):
    """Handle direct Lambda invocation (HRP mode)"""
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


def _count_drs_servers(regional_drs) -> Dict:
    """
    Count DRS source servers and replicating servers.
    Shared helper function to eliminate duplication.
    """
    total_servers = 0
    replicating_servers = 0

    paginator = regional_drs.get_paginator("describe_source_servers")

    for page in paginator.paginate():
        for server in page.get("items", []):
            total_servers += 1
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

    return {
        "totalServers": total_servers,
        "replicatingServers": replicating_servers,
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

                    print(
                        f"DEBUG: PG '{pg_name}' - region={pg_region}, target_region={region}"
                    )

                    # Skip if this is the current PG being edited
                    if current_pg_id and pg_id == current_pg_id:
                        print(f"DEBUG: Skipping current PG: {pg_id}")
                        continue

                    # Only check PGs in the same region
                    if pg_region != region:
                        print(f"DEBUG: Skipping PG in different region")
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
        counts = _count_drs_servers(regional_drs)

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
            counts = _count_drs_servers(regional_drs)
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
        counts = _count_drs_servers(regional_drs)
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
