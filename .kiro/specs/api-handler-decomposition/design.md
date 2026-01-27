# Design Document: API Handler Decomposition

## Executive Summary

This document specifies the design for decomposing the monolithic DR Orchestration API Handler Lambda function (11,558 lines) into three focused Lambda functions. The decomposition improves deployment safety, performance optimization, code organization, and enables direct Lambda invocation for future HRP integration.

**Decomposition Strategy**: Split by operational domain into three handlers:
1. **Data Management Handler** (~4,500 lines): Protection Groups + Recovery Plans CRUD
2. **Execution Handler** (~4,500 lines): DR execution operations and lifecycle management
3. **Query Handler** (~2,000 lines): Read-only DRS and EC2 infrastructure queries

**Key Design Principles**:
- Zero downtime migration with phased rollout
- 100% API compatibility (no frontend changes required)
- Support both API Gateway invocation AND direct Lambda invocation
- Extract shared utilities to Lambda Layer for code reuse
- Independent deployment and scaling per handler

## Architecture Overview

### Current Architecture (Monolithic)

```
API Gateway (48 endpoints)
    ↓
API Handler Lambda (11,558 lines)
    ├── Protection Groups CRUD
    ├── Recovery Plans CRUD
    ├── Execution Operations
    ├── DRS Infrastructure Queries
    ├── EC2 Resource Queries
    ├── Configuration Management
    └── User Permissions
    ↓
DynamoDB Tables + DRS API + Step Functions
```

### Target Architecture (Decomposed)

```
API Gateway (48 endpoints)
    ├── /protection-groups/* → Data Management Handler
    ├── /recovery-plans/*    → Data Management Handler
    ├── /executions/*        → Execution Handler
    ├── /drs/*              → Execution Handler (operations)
    ├── /drs/source-servers → Query Handler
    ├── /drs/quotas         → Query Handler
    ├── /ec2/*              → Query Handler
    ├── /accounts/*         → Query Handler
    ├── /config/*           → Query Handler
    └── /user/permissions   → Query Handler

Each Handler
    ↓
Lambda Layer (Shared Utilities)
    ├── Conflict Detection
    ├── DRS Service Limits
    ├── Cross-Account IAM
    ├── RBAC Middleware
    └── Response Utilities
    ↓
DynamoDB Tables + DRS API + Step Functions
```


## Handler Specifications

### 1. Data Management Handler

**Purpose**: Manage Protection Groups and Recovery Plans with CRUD operations, tag resolution, and launch configuration management.

**Responsibilities**:
- Protection Groups: Create, read, update, delete, resolve tags
- Recovery Plans: Create, read, update, delete, execute validation
- Launch Configuration: Apply DRS launch settings to servers
- Conflict Detection: Check for active executions before modifications
- Tag-based Discovery: Query DRS servers matching selection tags
- Tag Synchronization: Sync EC2 tags to DRS source servers, manage EventBridge schedule
- Configuration Management: Import configuration from JSON

**Size**: ~5,000 lines (43% of current handler)

**Memory**: 512 MB (moderate complexity, DRS API calls)

**Timeout**: 120 seconds (tag resolution can be slow)

**API Endpoints** (16 endpoints):
- `POST /protection-groups` - Create Protection Group
- `GET /protection-groups` - List Protection Groups
- `GET /protection-groups/{id}` - Get Protection Group
- `PUT /protection-groups/{id}` - Update Protection Group
- `DELETE /protection-groups/{id}` - Delete Protection Group
- `POST /protection-groups/resolve` - Resolve tag-based server selection
- `POST /recovery-plans` - Create Recovery Plan
- `GET /recovery-plans` - List Recovery Plans
- `GET /recovery-plans/{id}` - Get Recovery Plan
- `PUT /recovery-plans/{id}` - Update Recovery Plan
- `DELETE /recovery-plans/{id}` - Delete Recovery Plan
- `POST /recovery-plans/{id}/check-instances` - Check for existing instances
- `POST /drs/tag-sync` - Trigger manual tag synchronization
- `GET /config/tag-sync` - Get tag sync schedule settings
- `PUT /config/tag-sync` - Update tag sync schedule settings
- `POST /config/import` - Import configuration from JSON

**Key Functions**:
- `create_protection_group()` - Validate name uniqueness, tag conflicts, server conflicts
- `update_protection_group()` - Optimistic locking, block if in active execution
- `delete_protection_group()` - Check for active executions, remove from plans
- `resolve_protection_group_tags()` - Query DRS API with tag filters
- `query_drs_servers_by_tags()` - AND logic for tag matching
- `create_recovery_plan()` - Validate wave sizes against DRS limits
- `update_recovery_plan()` - Version conflict detection
- `delete_recovery_plan()` - Check for active executions
- `apply_launch_config_to_servers()` - Update DRS launch configuration
- `handle_drs_tag_sync()` - Sync EC2 tags to DRS source servers across all regions
- `get_tag_sync_settings()` - Get EventBridge schedule configuration
- `update_tag_sync_settings()` - Update schedule (enable/disable, interval)
- `import_configuration()` - Import and validate configuration from JSON

**Direct Invocation Payload**:
```json
{
  "operation": "create_protection_group",
  "body": {
    "groupName": "Production-Database-Servers",
    "region": "us-east-1",
    "serverSelectionTags": {
      "DR-Application": "Database",
      "DR-Tier": "Production"
    }
  }
}
```


### 2. Execution Handler

**Purpose**: Execute and manage DR operations including recovery plan execution, instance termination, pause/resume, and DRS job management.

**Responsibilities**:
- Recovery Plan Execution: Start Step Functions, validate servers, check conflicts
- Execution Lifecycle: Cancel, pause, resume, terminate operations
- DRS Operations: Start recovery, terminate instances, disconnect instances
- Failback Operations: Reverse replication, start/stop failback
- Job Management: Query DRS jobs, get job logs, check termination status
- Conflict Detection: Validate server availability across executions and DRS jobs

**Size**: ~4,500 lines (39% of current handler)

**Memory**: 512 MB (DRS API operations, Step Functions integration)

**Timeout**: 300 seconds (DRS operations can be slow, async execution pattern)

**API Endpoints** (23 endpoints):
- `POST /recovery-plans/{id}/execute` - Validate and execute Recovery Plan
- `GET /executions` - List executions
- `DELETE /executions` - Bulk delete executions
- `GET /executions/{id}` - Get execution details
- `POST /executions/{id}/cancel` - Cancel execution
- `POST /executions/{id}/pause` - Pause execution
- `POST /executions/{id}/resume` - Resume execution
- `POST /executions/{id}/terminate` - Terminate recovery instances
- `GET /executions/{id}/recovery-instances` - Get recovery instance details
- `GET /executions/{id}/job-logs` - Get DRS job logs
- `GET /executions/{id}/termination-status` - Check termination progress
- `POST /drs/failover` - Execute failover operation
- `POST /drs/start-recovery` - Start DRS recovery
- `POST /drs/terminate-recovery-instances` - Terminate instances
- `POST /drs/disconnect-recovery-instance` - Disconnect instance
- `POST /drs/failback` - Execute failback operation
- `POST /drs/reverse-replication` - Reverse replication direction
- `POST /drs/start-failback` - Start failback process
- `POST /drs/stop-failback` - Stop failback process
- `GET /drs/failback-configuration` - Get failback config
- `GET /drs/jobs` - List DRS jobs
- `GET /drs/jobs/{id}` - Get DRS job details
- `GET /drs/jobs/{id}/logs` - Get DRS job logs

**Key Functions**:
- `execute_recovery_plan()` - Validate, check conflicts, start Step Functions
- `cancel_execution()` - Stop Step Functions, update DynamoDB status
- `pause_execution()` - Set pause flag, notify Step Functions
- `resume_execution()` - Clear pause flag, send task token
- `terminate_recovery_instances()` - Call DRS API, update execution
- `check_server_conflicts()` - Query DynamoDB + live DRS jobs
- `get_servers_in_active_executions()` - Resolve from execution waves + Protection Groups
- `get_servers_in_active_drs_jobs()` - Query DRS API for active LAUNCH jobs
- `validate_wave_sizes()` - Enforce 100 servers per job limit
- `validate_concurrent_jobs()` - Check 20 concurrent jobs limit
- `validate_servers_in_all_jobs()` - Check 500 servers across all jobs limit

**Direct Invocation Payload**:
```json
{
  "operation": "execute_recovery_plan",
  "body": {
    "planId": "plan-uuid",
    "isDrill": true,
    "pauseBeforeWave": 2
  }
}
```


### 3. Query Handler

**Purpose**: Provide read-only queries for DRS infrastructure, EC2 resources, account information, and configuration export.

**Responsibilities**:
- DRS Infrastructure: Query source servers, quotas, capacity, accounts
- EC2 Resources: Query subnets, security groups, instance types, instance profiles
- Account Information: Get current account ID and region
- Configuration Export: Export Protection Groups and Recovery Plans
- User Permissions: Return RBAC permissions (Cognito-based)
- Tag Synchronization: Trigger DRS tag sync operations

**Size**: ~1,500 lines (13% of current handler)

**Memory**: 256 MB (read-only operations, smaller footprint)

**Timeout**: 60 seconds (queries should be fast)

**API Endpoints** (9 endpoints):
- `GET /drs/source-servers` - Query DRS source servers
- `GET /drs/quotas` - Get DRS service quotas and capacity
- `GET /drs/accounts` - List registered target accounts
- `GET /ec2/subnets` - Query EC2 subnets
- `GET /ec2/security-groups` - Query security groups
- `GET /ec2/instance-profiles` - Query IAM instance profiles
- `GET /ec2/instance-types` - Query available instance types
- `GET /accounts/current` - Get current account ID and region
- `GET /config/export` - Export configuration as JSON
- `GET /user/permissions` - Get user RBAC permissions

**Key Functions**:
- `get_drs_source_servers()` - Query DRS API across all regions
- `get_drs_account_capacity()` - Check replicating server count vs 300 limit
- `get_drs_account_capacity_all_regions()` - Aggregate capacity across regions
- `get_drs_regional_capacity()` - Get capacity for specific region
- `get_target_accounts()` - List registered cross-account configurations
- `get_ec2_subnets()` - Query subnets with cross-account support
- `get_ec2_security_groups()` - Query security groups
- `get_ec2_instance_profiles()` - Query IAM instance profiles
- `get_ec2_instance_types()` - Query available instance types
- `get_current_account_id()` - Return account ID from STS
- `export_configuration()` - Serialize Protection Groups + Recovery Plans
- `get_user_permissions()` - Return RBAC permissions from Cognito

**Direct Invocation Payload**:
```json
{
  "operation": "get_drs_source_servers",
  "queryParams": {
    "region": "us-east-1",
    "accountId": "123456789012"
  }
}
```


## Lambda Layer: Shared Utilities

**Purpose**: Extract common code used by all three handlers to eliminate duplication and ensure consistent behavior.

**Size**: ~500 lines (4% of current handler)

**Layer Structure**:
```
lambda/shared/
├── __init__.py
├── conflict_detection.py      # Conflict checking logic (always used)
├── drs_limits.py              # DRS service limit validation (always used)
├── cross_account.py           # IAM role assumption utilities (always used)
├── execution_utils.py         # Execution termination logic (always used)
├── response_utils.py          # DecimalEncoder (always used), response() (API Gateway only)
└── rbac_middleware.py         # User permission checks (API Gateway + Cognito only)
```

**Deployment Modes**:
- **Standalone Mode** (API Gateway + Cognito): All utilities used
- **HRP Mode** (direct invocation): rbac_middleware.py and response() not used

### conflict_detection.py

**Functions**:
- `get_servers_in_active_executions()` - Query DynamoDB for servers in active executions
- `get_servers_in_active_drs_jobs()` - Query DRS API for servers in active jobs
- `check_server_conflicts()` - Comprehensive conflict detection (DynamoDB + DRS API)
- `get_plans_with_conflicts()` - Get all plans with conflicts (for frontend)
- `resolve_pg_servers_for_conflict_check()` - Resolve Protection Group to server IDs

**Why Shared**: All three handlers need conflict detection:
- Data Management: Check before deleting Protection Groups
- Execution: Validate before starting executions
- Query: Return conflict status for frontend

### drs_limits.py

**Functions**:
- `validate_wave_sizes()` - Enforce 100 servers per job limit
- `validate_concurrent_jobs()` - Check 20 concurrent jobs limit
- `validate_servers_in_all_jobs()` - Check 500 servers across all jobs limit
- `validate_server_replication_states()` - Verify healthy replication

**Constants**:
```python
DRS_LIMITS = {
    "MAX_SERVERS_PER_JOB": 100,
    "MAX_CONCURRENT_JOBS": 20,
    "MAX_SERVERS_IN_ALL_JOBS": 500,
    "MAX_REPLICATING_SERVERS": 300,
    "WARNING_REPLICATING_THRESHOLD": 250,
    "CRITICAL_REPLICATING_THRESHOLD": 280,
}
```

**Why Shared**: DRS limits enforced by multiple handlers:
- Data Management: Validate Recovery Plan wave sizes
- Execution: Check capacity before starting operations
- Query: Report current capacity metrics

### cross_account.py

**Functions**:
- `determine_target_account_context()` - Resolve target account from Protection Groups
- `create_drs_client()` - Create DRS client with optional cross-account role assumption

**Why Shared**: All handlers perform cross-account operations:
- Data Management: Resolve tags in target accounts
- Execution: Execute recovery in target accounts
- Query: Query DRS infrastructure in target accounts

### rbac_middleware.py (Optional - API Gateway mode only)

**Functions**:
- `get_user_permissions()` - Extract permissions from Cognito user attributes
- `get_user_roles()` - Get user roles from Cognito groups

**When Used**: Only when deployed with API Gateway + Cognito
- Standalone mode: RBAC enforced via Cognito authorizer
- HRP mode: Not used (no API Gateway, no Cognito)

**Why Optional**: 
- HRP integration uses direct Lambda invocation (no Cognito context)
- Audit logging uses IAM role context instead of Cognito user
- Reduces Lambda package size in HRP deployment mode

### execution_utils.py

**Functions**:
- `can_terminate_execution()` - Check if execution can be terminated

**Why Shared**: Multiple handlers check termination eligibility:
- Execution: Validate before terminating
- Query: Return termination status

### response_utils.py (Partially optional)

**Functions**:
- `response()` - Generate API Gateway response with CORS and security headers (optional)
- `DecimalEncoder` - JSON encoder for DynamoDB Decimal types (always needed)

**When Used**:
- `response()`: Only when deployed with API Gateway (standalone mode)
- `DecimalEncoder`: Always needed for DynamoDB Decimal serialization

**Why Partially Optional**:
- API Gateway response formatting not needed in HRP mode (direct invocation)
- DecimalEncoder always required for DynamoDB data serialization
- Reduces unnecessary code execution in HRP deployment mode


## API Gateway Routing

### Current Routing (Monolithic)

All 48 endpoints route to single API Handler Lambda:

```yaml
ApiHandlerIntegration:
  Type: AWS::ApiGateway::Integration
  Properties:
    IntegrationHttpMethod: POST
    Type: AWS_PROXY
    Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ApiHandlerFunctionArn}/invocations"
```

### Target Routing (Decomposed)

Endpoints route to three different handlers based on path prefix:

| Path Pattern | Handler | Endpoints |
|--------------|---------|-----------|
| `/protection-groups*` | Data Management | 6 endpoints |
| `/recovery-plans*` | Data Management | 6 endpoints |
| `/recovery-plans/{id}/execute` | Execution | 1 endpoint |
| `/executions*` | Execution | 10 endpoints |
| `/drs/failover` | Execution | 1 endpoint |
| `/drs/start-recovery` | Execution | 1 endpoint |
| `/drs/terminate-recovery-instances` | Execution | 1 endpoint |
| `/drs/disconnect-recovery-instance` | Execution | 1 endpoint |
| `/drs/failback*` | Execution | 4 endpoints |
| `/drs/reverse-replication` | Execution | 1 endpoint |
| `/drs/jobs*` | Execution | 3 endpoints |
| `/drs/source-servers` | Query | 1 endpoint |
| `/drs/quotas` | Query | 1 endpoint |
| `/drs/accounts` | Query | 1 endpoint |
| `/drs/tag-sync` | Data Management | 1 endpoint |
| `/ec2/*` | Query | 4 endpoints |
| `/accounts/current` | Query | 1 endpoint |
| `/config/export` | Query | 1 endpoint |
| `/config/import` | Data Management | 1 endpoint |
| `/config/tag-sync` | Data Management | 2 endpoints |
| `/user/permissions` | Query | 1 endpoint |

**Total: 48 endpoints** (16 Data Management + 23 Execution + 9 Query)

### CloudFormation Changes

**api-gateway-core-methods-stack.yaml** (Protection Groups, Recovery Plans, Tag Sync, Config Import):
```yaml
ProtectionGroupsMethod:
  Properties:
    Integration:
      Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${DataManagementHandlerArn}/invocations"
```

**api-gateway-operations-methods-stack.yaml** (Executions, DRS Operations, Recovery Plan Execute):
```yaml
ExecutionsMethod:
  Properties:
    Integration:
      Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ExecutionHandlerArn}/invocations"
```

**api-gateway-infrastructure-methods-stack.yaml** (DRS Infrastructure, EC2, Config Export):
```yaml
DrsSourceServersMethod:
  Properties:
    Integration:
      Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${QueryHandlerArn}/invocations"
```

### Lambda Permissions

Each handler needs permission for API Gateway to invoke it:

```yaml
DataManagementHandlerApiPermission:
  Type: AWS::Lambda::Permission
  Properties:
    FunctionName: !Ref DataManagementHandlerFunction
    Action: lambda:InvokeFunction
    Principal: apigateway.amazonaws.com
    SourceArn: !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${RestApiId}/*"

ExecutionHandlerApiPermission:
  Type: AWS::Lambda::Permission
  Properties:
    FunctionName: !Ref ExecutionHandlerFunction
    Action: lambda:InvokeFunction
    Principal: apigateway.amazonaws.com
    SourceArn: !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${RestApiId}/*"

QueryHandlerApiPermission:
  Type: AWS::Lambda::Permission
  Properties:
    FunctionName: !Ref QueryHandlerFunction
    Action: lambda:InvokeFunction
    Principal: apigateway.amazonaws.com
    SourceArn: !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${RestApiId}/*"
```


## Direct Lambda Invocation Support

### Invocation Patterns

Each handler supports TWO invocation patterns:

1. **API Gateway Invocation** (Current):
   - Event contains `requestContext`, `httpMethod`, `path`, `body`
   - Returns API Gateway response format with `statusCode`, `headers`, `body`

2. **Direct Invocation** (Future HRP Integration):
   - Event contains `operation` and operation-specific parameters
   - Returns operation result directly (no API Gateway wrapper)

### Handler Entry Point Pattern

```python
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
    # Detect invocation pattern
    if "requestContext" in event:
        # API Gateway invocation (standalone mode)
        # Uses: RBAC middleware, response() utility
        return handle_api_gateway_request(event, context)
    elif "operation" in event:
        # Direct invocation (HRP mode)
        # Skips: RBAC middleware, response() utility
        return handle_direct_invocation(event, context)
    else:
        return {
            "error": "Invalid invocation format",
            "message": "Event must contain either 'requestContext' (API Gateway) or 'operation' (direct invocation)"
        }
```

### API Gateway Routing Logic

Each handler must route requests based on HTTP method and path. Here's the routing implementation for each handler:

#### Data Management Handler Routing (13 endpoints)

```python
def handle_api_gateway_request(event, context):
    """Route API Gateway requests to appropriate handler functions"""
    method = event["httpMethod"]
    path = event["path"]
    path_params = event.get("pathParameters", {})
    
    # Protection Groups endpoints (6)
    if path == "/protection-groups":
        if method == "GET":
            return list_protection_groups(event)
        elif method == "POST":
            return create_protection_group(event)
    
    elif path == "/protection-groups/{id}":
        group_id = path_params.get("id")
        if method == "GET":
            return get_protection_group(event, group_id)
        elif method == "PUT":
            return update_protection_group(event, group_id)
        elif method == "DELETE":
            return delete_protection_group(event, group_id)
    
    elif path == "/protection-groups/resolve":
        if method == "POST":
            return resolve_protection_group_tags(event)
    
    # Recovery Plans endpoints (7)
    elif path == "/recovery-plans":
        if method == "GET":
            return list_recovery_plans(event)
        elif method == "POST":
            return create_recovery_plan(event)
    
    elif path == "/recovery-plans/{id}":
        plan_id = path_params.get("id")
        if method == "GET":
            return get_recovery_plan(event, plan_id)
        elif method == "PUT":
            return update_recovery_plan(event, plan_id)
        elif method == "DELETE":
            return delete_recovery_plan(event, plan_id)
    
    elif path == "/recovery-plans/{id}/execute":
        plan_id = path_params.get("id")
        if method == "POST":
            return execute_recovery_plan(event, plan_id)
    
    elif path == "/recovery-plans/{id}/check-instances":
        plan_id = path_params.get("id")
        if method == "POST":
            return check_existing_instances(event, plan_id)
    
    else:
        return response(404, {"error": "Not Found", "message": f"Path {path} not found"})
```

#### Execution Handler Routing (22 endpoints)

```python
def handle_api_gateway_request(event, context):
    """Route API Gateway requests to appropriate handler functions"""
    method = event["httpMethod"]
    path = event["path"]
    path_params = event.get("pathParameters", {})
    
    # Executions endpoints (10)
    if path == "/executions":
        if method == "GET":
            return list_executions(event)
        elif method == "DELETE":
            return bulk_delete_executions(event)
    
    elif path == "/executions/{id}":
        execution_id = path_params.get("id")
        if method == "GET":
            return get_execution(event, execution_id)
    
    elif path == "/executions/{id}/cancel":
        execution_id = path_params.get("id")
        if method == "POST":
            return cancel_execution(event, execution_id)
    
    elif path == "/executions/{id}/pause":
        execution_id = path_params.get("id")
        if method == "POST":
            return pause_execution(event, execution_id)
    
    elif path == "/executions/{id}/resume":
        execution_id = path_params.get("id")
        if method == "POST":
            return resume_execution(event, execution_id)
    
    elif path == "/executions/{id}/terminate":
        execution_id = path_params.get("id")
        if method == "POST":
            return terminate_recovery_instances(event, execution_id)
    
    elif path == "/executions/{id}/recovery-instances":
        execution_id = path_params.get("id")
        if method == "GET":
            return get_recovery_instances(event, execution_id)
    
    elif path == "/executions/{id}/job-logs":
        execution_id = path_params.get("id")
        if method == "GET":
            return get_job_logs(event, execution_id)
    
    elif path == "/executions/{id}/termination-status":
        execution_id = path_params.get("id")
        if method == "GET":
            return get_termination_status(event, execution_id)
    
    # DRS Operations endpoints (12)
    elif path == "/drs/failover":
        if method == "POST":
            return execute_failover(event)
    
    elif path == "/drs/start-recovery":
        if method == "POST":
            return start_recovery(event)
    
    elif path == "/drs/terminate-recovery-instances":
        if method == "POST":
            return terminate_drs_instances(event)
    
    elif path == "/drs/disconnect-recovery-instance":
        if method == "POST":
            return disconnect_recovery_instance(event)
    
    elif path == "/drs/failback":
        if method == "POST":
            return execute_failback(event)
    
    elif path == "/drs/reverse-replication":
        if method == "POST":
            return reverse_replication(event)
    
    elif path == "/drs/start-failback":
        if method == "POST":
            return start_failback(event)
    
    elif path == "/drs/stop-failback":
        if method == "POST":
            return stop_failback(event)
    
    elif path == "/drs/failback-configuration":
        if method == "GET":
            return get_failback_configuration(event)
    
    elif path == "/drs/jobs":
        if method == "GET":
            return list_drs_jobs(event)
    
    elif path == "/drs/jobs/{id}":
        job_id = path_params.get("id")
        if method == "GET":
            return get_drs_job(event, job_id)
    
    elif path == "/drs/jobs/{id}/logs":
        job_id = path_params.get("id")
        if method == "GET":
            return get_drs_job_logs(event, job_id)
    
    else:
        return response(404, {"error": "Not Found", "message": f"Path {path} not found"})
```

#### Query Handler Routing (13 endpoints)

```python
def handle_api_gateway_request(event, context):
    """Route API Gateway requests to appropriate handler functions"""
    method = event["httpMethod"]
    path = event["path"]
    query_params = event.get("queryStringParameters", {})
    
    # DRS Infrastructure endpoints (4)
    if path == "/drs/source-servers":
        if method == "GET":
            return get_drs_source_servers(event)
    
    elif path == "/drs/quotas":
        if method == "GET":
            return get_drs_quotas(event)
    
    elif path == "/drs/accounts":
        if method == "GET":
            return get_target_accounts(event)
    
    elif path == "/drs/tag-sync":
        if method == "POST":
            return trigger_tag_sync(event)
    
    # EC2 Resources endpoints (4)
    elif path == "/ec2/subnets":
        if method == "GET":
            return get_ec2_subnets(event)
    
    elif path == "/ec2/security-groups":
        if method == "GET":
            return get_ec2_security_groups(event)
    
    elif path == "/ec2/instance-profiles":
        if method == "GET":
            return get_ec2_instance_profiles(event)
    
    elif path == "/ec2/instance-types":
        if method == "GET":
            return get_ec2_instance_types(event)
    
    # Account & Config endpoints (4)
    elif path == "/accounts/current":
        if method == "GET":
            return get_current_account(event)
    
    elif path == "/config/export":
        if method == "GET":
            return export_configuration(event)
    
    elif path == "/config/import":
        if method == "POST":
            return import_configuration(event)
    
    elif path == "/config/tag-sync":
        if method == "POST":
            return trigger_config_tag_sync(event)
    
    # User permissions endpoint (1)
    elif path == "/user/permissions":
        if method == "GET":
            return get_user_permissions(event)
    
    else:
        return response(404, {"error": "Not Found", "message": f"Path {path} not found"})
```

### Routing Validation

**Testing Strategy**:
```python
# Test all 48 endpoints route correctly
def test_handler_routing():
    test_cases = [
        # Data Management Handler (13 endpoints)
        ("GET", "/protection-groups", "list_protection_groups"),
        ("POST", "/protection-groups", "create_protection_group"),
        ("GET", "/protection-groups/{id}", "get_protection_group"),
        ("PUT", "/protection-groups/{id}", "update_protection_group"),
        ("DELETE", "/protection-groups/{id}", "delete_protection_group"),
        ("POST", "/protection-groups/resolve", "resolve_protection_group_tags"),
        ("GET", "/recovery-plans", "list_recovery_plans"),
        ("POST", "/recovery-plans", "create_recovery_plan"),
        ("GET", "/recovery-plans/{id}", "get_recovery_plan"),
        ("PUT", "/recovery-plans/{id}", "update_recovery_plan"),
        ("DELETE", "/recovery-plans/{id}", "delete_recovery_plan"),
        ("POST", "/recovery-plans/{id}/execute", "execute_recovery_plan"),
        ("POST", "/recovery-plans/{id}/check-instances", "check_existing_instances"),
        
        # Execution Handler (22 endpoints)
        ("GET", "/executions", "list_executions"),
        ("DELETE", "/executions", "bulk_delete_executions"),
        # ... all 22 endpoints
        
        # Query Handler (13 endpoints)
        ("GET", "/drs/source-servers", "get_drs_source_servers"),
        ("GET", "/drs/quotas", "get_drs_quotas"),
        # ... all 13 endpoints
    ]
    
    for method, path, expected_function in test_cases:
        event = create_api_gateway_event(method, path)
        # Verify correct function is called
        assert routes_to_function(event, expected_function)
```

### Direct Invocation Payload Formats

**Data Management Handler**:
```python
# Create Protection Group
{
    "operation": "create_protection_group",
    "body": {
        "groupName": "Production-Database-Servers",
        "region": "us-east-1",
        "serverSelectionTags": {"DR-Application": "Database"}
    }
}

# Update Protection Group
{
    "operation": "update_protection_group",
    "groupId": "pg-uuid",
    "body": {
        "description": "Updated description",
        "version": 2
    }
}

# Resolve Protection Group Tags
{
    "operation": "resolve_protection_group_tags",
    "body": {
        "region": "us-east-1",
        "serverSelectionTags": {"DR-Tier": "Production"}
    }
}

# Create Recovery Plan
{
    "operation": "create_recovery_plan",
    "body": {
        "planName": "Production-Failover",
        "waves": [
            {"waveName": "Wave 1", "protectionGroupId": "pg-uuid"}
        ]
    }
}
```

**Execution Handler**:
```python
# Execute Recovery Plan
{
    "operation": "execute_recovery_plan",
    "body": {
        "planId": "plan-uuid",
        "isDrill": true,
        "pauseBeforeWave": 2
    }
}

# Cancel Execution
{
    "operation": "cancel_execution",
    "executionId": "exec-uuid"
}

# Pause Execution
{
    "operation": "pause_execution",
    "executionId": "exec-uuid"
}

# Resume Execution
{
    "operation": "resume_execution",
    "executionId": "exec-uuid"
}

# Terminate Recovery Instances
{
    "operation": "terminate_recovery_instances",
    "executionId": "exec-uuid"
}
```

**Query Handler**:
```python
# Get DRS Source Servers
{
    "operation": "get_drs_source_servers",
    "queryParams": {
        "region": "us-east-1",
        "accountId": "123456789012"
    }
}

# Get DRS Quotas
{
    "operation": "get_drs_quotas",
    "queryParams": {
        "region": "us-east-1"
    }
}

# Get EC2 Subnets
{
    "operation": "get_ec2_subnets",
    "queryParams": {
        "region": "us-east-1",
        "vpcId": "vpc-12345"
    }
}

# Export Configuration
{
    "operation": "export_configuration"
}
```

### Response Format Differences

**API Gateway Response** (wrapped):
```json
{
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    },
    "body": "{\"groupId\":\"pg-uuid\",\"groupName\":\"Production-Database-Servers\"}"
}
```

**Direct Invocation Response** (unwrapped):
```json
{
    "groupId": "pg-uuid",
    "groupName": "Production-Database-Servers",
    "region": "us-east-1",
    "createdDate": 1705449600
}
```


## IAM Permissions

### Unified IAM Role Approach

All three handlers use a **single unified IAM execution role** (`UnifiedOrchestrationRole`) with full permissions. This approach:
- Simplifies IAM management (one role instead of three)
- Enables seamless HRP integration (HRP orchestration role controls all functions)
- Reduces operational complexity (no per-handler permission troubleshooting)
- Maintains security through application-level access control (RBAC via Cognito)

**UnifiedOrchestrationRole** (used by all handlers):
```yaml
UnifiedOrchestrationRole:
  Policies:
    - DynamoDB: GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan
      Tables: ProtectionGroups, RecoveryPlans, ExecutionHistory, TargetAccounts
    - Step Functions: StartExecution, DescribeExecution, SendTaskSuccess, SendTaskFailure
    - DRS: Full access (StartRecovery, TerminateRecoveryInstances, DisconnectRecoveryInstance, 
           ReverseReplication, StartFailbackLaunch, StopFailback, Describe*)
    - EC2: Describe*, CreateLaunchTemplateVersion
    - IAM: PassRole (for DRS and EC2 operations)
    - STS: AssumeRole (cross-account operations)
    - Lambda: InvokeFunction (for async operations and handler invocation)
    - SNS: Publish (execution notifications)
    - CloudWatch: PutMetricData (custom metrics)
```

### Benefits of Unified Role

**Operational Simplicity**:
- Single IAM role to manage and audit
- No permission boundary issues between handlers
- Simplified troubleshooting (no "which handler needs which permission?" questions)

**HRP Integration Ready**:
- HRP orchestration uses single IAM role for all technology adapters
- Direct Lambda invocation works seamlessly (same role across all functions)
- No cross-role permission issues when HRP calls DRS handlers

**Security Through Application Logic**:
- RBAC enforced at application level via Cognito user attributes
- Audit logging tracks which user performed which operation
- CloudTrail logs all IAM role actions with full context

### Handler Responsibilities (Application-Level)

While all handlers share the same IAM role, they maintain distinct responsibilities at the application level:

| Handler | Primary Operations | Secondary Operations |
|---------|-------------------|---------------------|
| Data Management | Protection Groups, Recovery Plans CRUD | Tag resolution, conflict detection |
| Execution | DR operations, Step Functions orchestration | DRS API calls, instance termination |
| Query | Read-only queries | DRS infrastructure, EC2 resources |

**Note**: The decomposition provides operational benefits (independent deployment, performance optimization, code organization) without requiring IAM role separation.


## Migration Strategy

### Phased Rollout Approach

**Phase 1: Query Handler** (Lowest Risk)
- Deploy Query Handler with read-only operations
- Route query endpoints to new handler
- Keep Data Management and Execution in monolithic handler
- Validate: No data modifications, fastest cold starts
- Rollback: Simple - revert API Gateway routing

**Phase 2: Execution Handler** (Highest Value)
- Deploy Execution Handler with DR operations
- Route execution endpoints to new handler
- Keep Data Management in monolithic handler
- Validate: Executions work correctly, conflict detection accurate
- Rollback: Revert API Gateway routing, no data loss

**Phase 3: Data Management Handler** (Complete Migration)
- Deploy Data Management Handler
- Route remaining endpoints to new handler
- Decommission monolithic API Handler
- Validate: Full system operational
- Rollback: Redeploy monolithic handler if needed

### Phase 1: Query Handler Deployment

**Step 1: Create Lambda Layer**
```bash
# Package shared utilities
cd lambda/shared
zip -r ../../build/shared-layer.zip .

# Upload to S3
aws s3 cp build/shared-layer.zip s3://deployment-bucket/lambda/shared-layer.zip
```

**Step 2: Deploy Query Handler**
```yaml
# Add to lambda-stack.yaml
QueryHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub "${ProjectName}-query-handler-${Environment}"
    Runtime: python3.12
    Handler: index.lambda_handler
    Role: !Ref QueryHandlerRoleArn
    Code:
      S3Bucket: !Ref SourceBucket
      S3Key: "lambda/query-handler.zip"
    Layers:
      - !Ref SharedUtilitiesLayer
    Timeout: 60
    MemorySize: 256
    Environment:
      Variables:
        PROTECTION_GROUPS_TABLE: !Ref ProtectionGroupsTableName
        RECOVERY_PLANS_TABLE: !Ref RecoveryPlansTableName
        EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTableName
        TARGET_ACCOUNTS_TABLE: !Ref TargetAccountsTableName
```

**Step 3: Update API Gateway Routing**
```yaml
# Update api-gateway-infrastructure-methods-stack.yaml
DrsSourceServersMethod:
  Properties:
    Integration:
      Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${QueryHandlerArn}/invocations"
```

**Step 4: Validation**
```bash
# Test query endpoints
curl -X GET https://api.example.com/drs/source-servers?region=us-east-1
curl -X GET https://api.example.com/drs/quotas?region=us-east-1
curl -X GET https://api.example.com/ec2/subnets?region=us-east-1

# Verify no errors in CloudWatch Logs
aws logs tail /aws/lambda/query-handler --follow
```

**Step 5: Monitor**
- CloudWatch metrics: Invocation count, duration, errors
- API Gateway metrics: 4xx/5xx errors, latency
- Frontend: No user-reported issues

**Rollback Plan**:
```bash
# Revert API Gateway routing to monolithic handler
aws cloudformation update-stack \
  --stack-name api-gateway-infrastructure-methods \
  --use-previous-template \
  --parameters ParameterKey=QueryHandlerArn,ParameterValue=${MonolithicHandlerArn}
```

### Phase 2: Execution Handler Deployment

**Step 1: Deploy Execution Handler**
```yaml
ExecutionHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub "${ProjectName}-execution-handler-${Environment}"
    Runtime: python3.12
    Handler: index.lambda_handler
    Role: !Ref ExecutionHandlerRoleArn
    Code:
      S3Bucket: !Ref SourceBucket
      S3Key: "lambda/execution-handler.zip"
    Layers:
      - !Ref SharedUtilitiesLayer
    Timeout: 300
    MemorySize: 512
    Environment:
      Variables:
        PROTECTION_GROUPS_TABLE: !Ref ProtectionGroupsTableName
        RECOVERY_PLANS_TABLE: !Ref RecoveryPlansTableName
        EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTableName
        STATE_MACHINE_ARN: !Ref StateMachineArn
```

**Step 2: Update API Gateway Routing**
```yaml
# Update api-gateway-operations-methods-stack.yaml
ExecutionsMethod:
  Properties:
    Integration:
      Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ExecutionHandlerArn}/invocations"
```

**Step 3: Validation**
```bash
# Test execution endpoints (non-destructive)
curl -X GET https://api.example.com/executions
curl -X GET https://api.example.com/executions/{id}

# Test DRS operations (drill mode)
curl -X POST https://api.example.com/recovery-plans/{id}/execute \
  -d '{"isDrill": true}'

# Verify conflict detection
curl -X POST https://api.example.com/recovery-plans/{id}/execute \
  -d '{"isDrill": false}' # Should fail if conflicts exist
```

**Step 4: Monitor**
- Step Functions executions: Success rate, duration
- DRS operations: Job success rate, server launch status
- Conflict detection: False positives/negatives

**Rollback Plan**:
```bash
# Revert API Gateway routing
aws cloudformation update-stack \
  --stack-name api-gateway-operations-methods \
  --use-previous-template \
  --parameters ParameterKey=ExecutionHandlerArn,ParameterValue=${MonolithicHandlerArn}
```

### Phase 3: Data Management Handler Deployment

**Step 1: Deploy Data Management Handler**
```yaml
DataManagementHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub "${ProjectName}-data-management-handler-${Environment}"
    Runtime: python3.12
    Handler: index.lambda_handler
    Role: !Ref DataManagementHandlerRoleArn
    Code:
      S3Bucket: !Ref SourceBucket
      S3Key: "lambda/data-management-handler.zip"
    Layers:
      - !Ref SharedUtilitiesLayer
    Timeout: 120
    MemorySize: 512
    Environment:
      Variables:
        PROTECTION_GROUPS_TABLE: !Ref ProtectionGroupsTableName
        RECOVERY_PLANS_TABLE: !Ref RecoveryPlansTableName
        EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTableName
```

**Step 2: Update API Gateway Routing**
```yaml
# Update api-gateway-core-methods-stack.yaml
ProtectionGroupsMethod:
  Properties:
    Integration:
      Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${DataManagementHandlerArn}/invocations"
```

**Step 3: Validation**
```bash
# Test Protection Groups CRUD
curl -X POST https://api.example.com/protection-groups \
  -d '{"groupName": "Test-PG", "region": "us-east-1"}'
curl -X GET https://api.example.com/protection-groups
curl -X PUT https://api.example.com/protection-groups/{id} \
  -d '{"description": "Updated"}'
curl -X DELETE https://api.example.com/protection-groups/{id}

# Test Recovery Plans CRUD
curl -X POST https://api.example.com/recovery-plans \
  -d '{"planName": "Test-Plan", "waves": [...]}'
curl -X GET https://api.example.com/recovery-plans
```

**Step 4: Decommission Monolithic Handler**
```bash
# Remove monolithic API Handler from lambda-stack.yaml
# Deploy updated stack
aws cloudformation update-stack --stack-name lambda-stack
```

**Step 5: Monitor**
- Protection Group operations: Create/update/delete success
- Recovery Plan operations: Wave validation, conflict detection
- Tag resolution: Server discovery accuracy

**Rollback Plan**:
```bash
# Redeploy monolithic handler
aws cloudformation update-stack \
  --stack-name lambda-stack \
  --use-previous-template \
  --parameters ParameterKey=DeployMonolithicHandler,ParameterValue=true

# Revert all API Gateway routing
aws cloudformation update-stack --stack-name api-gateway-core-methods
aws cloudformation update-stack --stack-name api-gateway-operations-methods
aws cloudformation update-stack --stack-name api-gateway-infrastructure-methods
```

### Zero Downtime Deployment

**Blue/Green Deployment Pattern**:
1. Deploy new handler versions alongside existing monolithic handler
2. Update API Gateway routing to new handlers (atomic operation)
3. Monitor for errors (5-10 minutes)
4. If errors detected, revert routing (atomic rollback)
5. If successful, decommission old handler

**API Gateway Deployment**:
```bash
# Create new deployment after routing changes
aws apigateway create-deployment \
  --rest-api-id ${API_ID} \
  --stage-name ${ENVIRONMENT}
```

**Lambda Alias Strategy** (Optional):
```yaml
# Use Lambda aliases for instant rollback
DataManagementHandlerAlias:
  Type: AWS::Lambda::Alias
  Properties:
    FunctionName: !Ref DataManagementHandlerFunction
    FunctionVersion: !GetAtt DataManagementHandlerVersion.Version
    Name: live

# API Gateway points to alias, not function
Integration:
  Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${DataManagementHandlerAlias}/invocations"
```


## Testing Strategy

### Unit Testing

**Test Coverage Requirements**:
- Lambda Layer utilities: 90%+ coverage
- Handler functions: 80%+ coverage
- Integration points: 100% coverage (API Gateway, DynamoDB, DRS API)

**Test Structure**:
```
tests/
├── unit/
│   ├── test_conflict_detection.py
│   ├── test_drs_limits.py
│   ├── test_cross_account.py
│   ├── test_rbac_middleware.py
│   ├── test_execution_utils.py
│   └── test_response_utils.py
├── integration/
│   ├── test_data_management_handler.py
│   ├── test_execution_handler.py
│   └── test_query_handler.py
└── e2e/
    ├── test_protection_group_lifecycle.py
    ├── test_recovery_plan_lifecycle.py
    └── test_execution_lifecycle.py
```

**Example Unit Test** (conflict_detection.py):
```python
import pytest
from moto import mock_dynamodb, mock_drs
from shared.conflict_detection import check_server_conflicts

@mock_dynamodb
@mock_drs
def test_check_server_conflicts_detects_active_execution():
    # Setup: Create active execution in DynamoDB
    execution_table.put_item(Item={
        "executionId": "exec-1",
        "status": "RUNNING",
        "waves": [{
            "serverStatuses": [{"sourceServerId": "s-12345"}]
        }]
    })
    
    # Test: Check conflicts for plan with same server
    plan = {
        "waves": [{
            "protectionGroupId": "pg-1"  # Resolves to s-12345
        }]
    }
    
    conflicts = check_server_conflicts(plan)
    
    # Assert: Conflict detected
    assert len(conflicts) == 1
    assert conflicts[0]["serverId"] == "s-12345"
    assert conflicts[0]["conflictSource"] == "execution"
```

### Integration Testing

**API Gateway Integration Tests**:
```python
import boto3
import requests

def test_query_handler_api_gateway_integration():
    # Invoke via API Gateway
    response = requests.get(
        "https://api.example.com/drs/source-servers",
        params={"region": "us-east-1"},
        headers={"Authorization": f"Bearer {cognito_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "servers" in data
    assert isinstance(data["servers"], list)
```

**Direct Invocation Tests**:
```python
def test_query_handler_direct_invocation():
    lambda_client = boto3.client("lambda")
    
    # Invoke directly
    response = lambda_client.invoke(
        FunctionName="query-handler",
        Payload=json.dumps({
            "operation": "get_drs_source_servers",
            "queryParams": {"region": "us-east-1"}
        })
    )
    
    result = json.loads(response["Payload"].read())
    assert "servers" in result
    assert isinstance(result["servers"], list)
```

### End-to-End Testing

**Protection Group Lifecycle Test**:
```python
def test_protection_group_full_lifecycle():
    # Create Protection Group
    pg = create_protection_group({
        "groupName": "E2E-Test-PG",
        "region": "us-east-1",
        "serverSelectionTags": {"DR-Test": "true"}
    })
    assert pg["groupId"]
    
    # Resolve tags
    resolved = resolve_protection_group_tags({
        "region": "us-east-1",
        "serverSelectionTags": {"DR-Test": "true"}
    })
    assert len(resolved["resolvedServers"]) > 0
    
    # Update Protection Group
    updated = update_protection_group(pg["groupId"], {
        "description": "Updated description",
        "version": 1
    })
    assert updated["version"] == 2
    
    # Delete Protection Group
    delete_protection_group(pg["groupId"])
    
    # Verify deleted
    with pytest.raises(Exception, match="not found"):
        get_protection_group(pg["groupId"])
```

**Recovery Plan Execution Test**:
```python
def test_recovery_plan_execution_lifecycle():
    # Create Protection Group
    pg = create_protection_group({
        "groupName": "E2E-Exec-Test-PG",
        "region": "us-east-1",
        "sourceServerIds": ["s-test-1", "s-test-2"]
    })
    
    # Create Recovery Plan
    plan = create_recovery_plan({
        "planName": "E2E-Exec-Test-Plan",
        "waves": [{
            "waveName": "Wave 1",
            "protectionGroupId": pg["groupId"]
        }]
    })
    
    # Execute (drill mode)
    execution = execute_recovery_plan({
        "planId": plan["planId"],
        "isDrill": true
    })
    assert execution["executionId"]
    assert execution["status"] == "PENDING"
    
    # Poll execution status
    import time
    for _ in range(30):  # 30 seconds max
        status = get_execution(execution["executionId"])
        if status["status"] in ["COMPLETED", "FAILED"]:
            break
        time.sleep(1)
    
    # Verify execution completed
    assert status["status"] == "COMPLETED"
    
    # Cleanup
    delete_recovery_plan(plan["planId"])
    delete_protection_group(pg["groupId"])
```

### Performance Testing

**Cold Start Benchmarks**:
```python
def test_handler_cold_start_times():
    results = {}
    
    for handler in ["data-management", "execution", "query"]:
        # Force cold start by updating environment variable
        lambda_client.update_function_configuration(
            FunctionName=handler,
            Environment={"Variables": {"FORCE_COLD_START": str(time.time())}}
        )
        
        # Wait for update to complete
        time.sleep(5)
        
        # Measure cold start
        start = time.time()
        lambda_client.invoke(FunctionName=handler, Payload="{}")
        cold_start_ms = (time.time() - start) * 1000
        
        results[handler] = cold_start_ms
    
    # Assert cold start targets
    assert results["query"] < 2000  # Query handler: <2s
    assert results["data-management"] < 3000  # Data Management: <3s
    assert results["execution"] < 3000  # Execution: <3s
```

**Concurrent Execution Test**:
```python
import concurrent.futures

def test_concurrent_query_handler_invocations():
    # Simulate 100 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [
            executor.submit(
                lambda_client.invoke,
                FunctionName="query-handler",
                Payload=json.dumps({
                    "operation": "get_drs_source_servers",
                    "queryParams": {"region": "us-east-1"}
                })
            )
            for _ in range(100)
        ]
        
        results = [f.result() for f in futures]
    
    # Assert all succeeded
    assert all(r["StatusCode"] == 200 for r in results)
    
    # Assert p95 latency < 500ms
    durations = [r["ExecutedVersion"] for r in results]
    p95 = sorted(durations)[94]  # 95th percentile
    assert p95 < 500
```

### Regression Testing

**API Compatibility Test Suite**:
```python
def test_api_compatibility_after_decomposition():
    """
    Verify all 28 API endpoints return identical responses
    before and after decomposition.
    """
    endpoints = [
        ("GET", "/protection-groups"),
        ("POST", "/protection-groups"),
        ("GET", "/protection-groups/{id}"),
        ("PUT", "/protection-groups/{id}"),
        ("DELETE", "/protection-groups/{id}"),
        # ... all 48 endpoints
    ]
    
    for method, path in endpoints:
        # Test with monolithic handler
        monolithic_response = call_api(method, path, use_monolithic=True)
        
        # Test with decomposed handlers
        decomposed_response = call_api(method, path, use_monolithic=False)
        
        # Assert identical responses
        assert monolithic_response.status_code == decomposed_response.status_code
        assert monolithic_response.json() == decomposed_response.json()
```

### Test Automation

**CI/CD Pipeline Integration**:
```yaml
# .github/workflows/test.yml
name: Test API Handler Decomposition

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run unit tests
        run: |
          pip install -r requirements-dev.txt
          pytest tests/unit/ --cov=lambda --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
  
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy test stack
        run: ./scripts/deploy.sh test --quick
      - name: Run integration tests
        run: pytest tests/integration/
      - name: Cleanup
        run: ./scripts/cleanup.sh test
  
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy test stack
        run: ./scripts/deploy.sh test
      - name: Run E2E tests
        run: pytest tests/e2e/
      - name: Cleanup
        run: ./scripts/cleanup.sh test
```


## CloudFormation Refactoring Requirements

### Overview

The API handler decomposition requires significant CloudFormation template changes across multiple stacks. This section documents the required refactoring for each template.

### Affected Templates

1. **lambda-stack.yaml** - Add 3 new handler functions + Lambda Layer
2. **master-template.yaml** - Pass handler ARNs to nested API Gateway stacks
3. **api-gateway-core-methods-stack.yaml** - Route Protection Groups/Recovery Plans to Data Management Handler
4. **api-gateway-operations-methods-stack.yaml** - Route Executions/DRS operations to Execution Handler
5. **api-gateway-infrastructure-methods-stack.yaml** - Route queries to Query Handler

### Migration Strategy

**Phase 1: Add New Handlers (Backward Compatible)**
- Deploy new handlers alongside existing monolithic handler
- Keep existing API Gateway routing to monolithic handler
- Validate new handlers work via direct invocation
- Zero risk - no user-facing changes

**Phase 2: Update API Gateway Routing (Phased Cutover)**
- Update routing one handler at a time (Query → Execution → Data Management)
- Each phase is independently rollbackable
- Monitor for errors after each phase

**Phase 3: Cleanup (Remove Monolithic Handler)**
- Remove monolithic API Handler function
- Remove unused parameters and outputs
- Final cleanup after all phases validated

### lambda-stack.yaml Refactoring

**Current State**:
- Single `ApiHandlerFunction` resource
- Single `ApiHandlerFunctionArn` output
- Parameters: `OrchestrationRoleArn`, `SourceBucket`, `ProjectName`, `Environment`

**Target State**:
- Add `SharedUtilitiesLayer` resource
- Add `DataManagementHandlerFunction` resource
- Add `ExecutionHandlerFunction` resource
- Add `QueryHandlerFunction` resource
- Keep `ApiHandlerFunction` during migration (remove in Phase 3)
- Add 4 new outputs (handler ARNs + layer ARN)

**Key Changes**:
```yaml
# NEW: Lambda Layer
SharedUtilitiesLayer:
  Type: AWS::Lambda::LayerVersion
  Properties:
    LayerName: !Sub "${ProjectName}-shared-utilities-${Environment}"
    Content:
      S3Bucket: !Ref SourceBucket
      S3Key: "lambda/shared-layer.zip"
    CompatibleRuntimes:
      - python3.12

# NEW: Data Management Handler
DataManagementHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub "${ProjectName}-data-management-handler-${Environment}"
    Role: !Ref OrchestrationRoleArn
    Layers:
      - !Ref SharedUtilitiesLayer
    Timeout: 120
    MemorySize: 512

# NEW: Execution Handler
ExecutionHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub "${ProjectName}-execution-handler-${Environment}"
    Role: !Ref OrchestrationRoleArn
    Layers:
      - !Ref SharedUtilitiesLayer
    Timeout: 300
    MemorySize: 512

# NEW: Query Handler
QueryHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub "${ProjectName}-query-handler-${Environment}"
    Role: !Ref OrchestrationRoleArn
    Layers:
      - !Ref SharedUtilitiesLayer
    Timeout: 60
    MemorySize: 256

# NEW: Outputs
Outputs:
  DataManagementHandlerArn:
    Value: !GetAtt DataManagementHandlerFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-DataManagementHandlerArn"
  
  ExecutionHandlerArn:
    Value: !GetAtt ExecutionHandlerFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-ExecutionHandlerArn"
  
  QueryHandlerArn:
    Value: !GetAtt QueryHandlerFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-QueryHandlerArn"
  
  SharedUtilitiesLayerArn:
    Value: !Ref SharedUtilitiesLayer
    Export:
      Name: !Sub "${AWS::StackName}-SharedUtilitiesLayerArn"
```

### master-template.yaml Refactoring

**Current State**:
- Passes `ApiHandlerFunctionArn` to all API Gateway nested stacks
- Single parameter for Lambda function ARN

**Target State**:
- Pass 3 handler ARNs to appropriate API Gateway stacks
- Route each stack to correct handler

**Key Changes**:
```yaml
# Update ApiGatewayCoreMethodsStack (Protection Groups, Recovery Plans)
ApiGatewayCoreMethodsStack:
  Type: AWS::CloudFormation::Stack
  Properties:
    Parameters:
      # OLD: ApiHandlerFunctionArn: !GetAtt LambdaStack.Outputs.ApiHandlerFunctionArn
      # NEW:
      DataManagementHandlerArn: !GetAtt LambdaStack.Outputs.DataManagementHandlerArn
      RestApiId: !GetAtt ApiGatewayCoreStack.Outputs.RestApiId
      # ... other parameters

# Update ApiGatewayOperationsMethodsStack (Executions, DRS Operations)
ApiGatewayOperationsMethodsStack:
  Type: AWS::CloudFormation::Stack
  Properties:
    Parameters:
      # OLD: ApiHandlerFunctionArn: !GetAtt LambdaStack.Outputs.ApiHandlerFunctionArn
      # NEW:
      ExecutionHandlerArn: !GetAtt LambdaStack.Outputs.ExecutionHandlerArn
      RestApiId: !GetAtt ApiGatewayCoreStack.Outputs.RestApiId
      # ... other parameters

# Update ApiGatewayInfrastructureMethodsStack (DRS Infrastructure, EC2, Config)
ApiGatewayInfrastructureMethodsStack:
  Type: AWS::CloudFormation::Stack
  Properties:
    Parameters:
      # OLD: ApiHandlerFunctionArn: !GetAtt LambdaStack.Outputs.ApiHandlerFunctionArn
      # NEW:
      QueryHandlerArn: !GetAtt LambdaStack.Outputs.QueryHandlerArn
      RestApiId: !GetAtt ApiGatewayCoreStack.Outputs.RestApiId
      # ... other parameters
```

### api-gateway-core-methods-stack.yaml Refactoring

**Current State**:
- Parameter: `ApiHandlerFunctionArn`
- All methods route to single handler

**Target State**:
- Parameter: `DataManagementHandlerArn`
- All methods route to Data Management Handler
- Add Lambda permission for new handler

**Key Changes**:
```yaml
Parameters:
  # OLD: ApiHandlerFunctionArn
  # NEW:
  DataManagementHandlerArn:
    Type: String
    Description: "ARN of Data Management Handler Lambda"

Resources:
  # Update ALL method integrations (Protection Groups, Recovery Plans)
  ProtectionGroupsGetMethod:
    Properties:
      Integration:
        Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${DataManagementHandlerArn}/invocations"
  
  ProtectionGroupsPostMethod:
    Properties:
      Integration:
        Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${DataManagementHandlerArn}/invocations"
  
  # ... repeat for all 13 methods in this stack
  
  # NEW: Lambda permission
  DataManagementHandlerApiPermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref DataManagementHandlerArn
      Action: lambda:InvokeFunction
      Principal: apigateway.amazonaws.com
      SourceArn: !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${RestApiId}/*"
```

**Methods to Update** (13 total):
- ProtectionGroupsGetMethod, ProtectionGroupsPostMethod
- ProtectionGroupsByIdGetMethod, ProtectionGroupsByIdPutMethod, ProtectionGroupsByIdDeleteMethod
- ProtectionGroupsResolvePostMethod
- RecoveryPlansGetMethod, RecoveryPlansPostMethod
- RecoveryPlansByIdGetMethod, RecoveryPlansByIdPutMethod, RecoveryPlansByIdDeleteMethod
- RecoveryPlansExecutePostMethod, RecoveryPlansCheckInstancesPostMethod

### api-gateway-operations-methods-stack.yaml Refactoring

**Current State**:
- Parameter: `ApiHandlerFunctionArn`
- All methods route to single handler

**Target State**:
- Parameter: `ExecutionHandlerArn`
- All methods route to Execution Handler
- Add Lambda permission for new handler

**Methods to Update** (22 total):
- ExecutionsGetMethod, ExecutionsDeleteMethod
- ExecutionsByIdGetMethod, ExecutionsCancelPostMethod, ExecutionsPausePostMethod, ExecutionsResumePostMethod, ExecutionsTerminatePostMethod
- ExecutionsRecoveryInstancesGetMethod, ExecutionsJobLogsGetMethod, ExecutionsTerminationStatusGetMethod
- DrsFailoverPostMethod, DrsStartRecoveryPostMethod, DrsTerminateRecoveryInstancesPostMethod, DrsDisconnectRecoveryInstancePostMethod
- DrsFailbackPostMethod, DrsReverseReplicationPostMethod, DrsStartFailbackPostMethod, DrsStopFailbackPostMethod, DrsFailbackConfigurationGetMethod
- DrsJobsGetMethod, DrsJobsByIdGetMethod, DrsJobsLogsGetMethod

### api-gateway-infrastructure-methods-stack.yaml Refactoring

**Current State**:
- Parameter: `ApiHandlerFunctionArn`
- All methods route to single handler

**Target State**:
- Parameter: `QueryHandlerArn`
- All methods route to Query Handler
- Add Lambda permission for new handler

**Methods to Update** (13 total):
- DrsSourceServersGetMethod, DrsQuotasGetMethod, DrsAccountsGetMethod, DrsTagSyncPostMethod
- Ec2SubnetsGetMethod, Ec2SecurityGroupsGetMethod, Ec2InstanceProfilesGetMethod, Ec2InstanceTypesGetMethod
- AccountsCurrentGetMethod
- ConfigExportGetMethod, ConfigImportPostMethod, ConfigTagSyncPostMethod
- UserPermissionsGetMethod

### Refactoring Checklist

**lambda-stack.yaml**:
- [ ] Add SharedUtilitiesLayer resource
- [ ] Add DataManagementHandlerFunction resource
- [ ] Add ExecutionHandlerFunction resource
- [ ] Add QueryHandlerFunction resource
- [ ] Add 4 new outputs (handler ARNs + layer ARN)
- [ ] Keep ApiHandlerFunction during migration
- [ ] Update all environment variables for new handlers

**master-template.yaml**:
- [ ] Update ApiGatewayCoreMethodsStack parameters (DataManagementHandlerArn)
- [ ] Update ApiGatewayOperationsMethodsStack parameters (ExecutionHandlerArn)
- [ ] Update ApiGatewayInfrastructureMethodsStack parameters (QueryHandlerArn)
- [ ] Keep backward compatibility during migration

**api-gateway-core-methods-stack.yaml**:
- [ ] Change parameter from ApiHandlerFunctionArn to DataManagementHandlerArn
- [ ] Update 13 method integrations to use DataManagementHandlerArn
- [ ] Add DataManagementHandlerApiPermission resource

**api-gateway-operations-methods-stack.yaml**:
- [ ] Change parameter from ApiHandlerFunctionArn to ExecutionHandlerArn
- [ ] Update 22 method integrations to use ExecutionHandlerArn
- [ ] Add ExecutionHandlerApiPermission resource

**api-gateway-infrastructure-methods-stack.yaml**:
- [ ] Change parameter from ApiHandlerFunctionArn to QueryHandlerArn
- [ ] Update 13 method integrations to use QueryHandlerArn
- [ ] Add QueryHandlerApiPermission resource

### Deployment Order

1. **Deploy lambda-stack.yaml** (adds new handlers, keeps old handler)
2. **Deploy master-template.yaml** (passes new handler ARNs to nested stacks)
3. **Deploy api-gateway-*-methods-stack.yaml** (updates routing, one at a time)
4. **Validate each phase** (test endpoints, check CloudWatch Logs)
5. **Deploy API Gateway deployment** (activate new routing)
6. **Monitor for errors** (5-10 minutes per phase)
7. **Rollback if needed** (revert to previous stack version)

### Rollback Strategy

**Per-Stack Rollback**:
```bash
# Rollback specific API Gateway stack
aws cloudformation update-stack \
  --stack-name api-gateway-infrastructure-methods-dev \
  --use-previous-template \
  --parameters ParameterKey=QueryHandlerArn,UsePreviousValue=true

# Rollback Lambda stack
aws cloudformation update-stack \
  --stack-name lambda-dev \
  --use-previous-template
```

**Complete Rollback**:
```bash
# Revert all stacks to previous version
./scripts/rollback-decomposition.sh dev
```


## CloudFormation Changes

### lambda-stack.yaml Updates

**Add Lambda Layer**:
```yaml
SharedUtilitiesLayer:
  Type: AWS::Lambda::LayerVersion
  Properties:
    LayerName: !Sub "${ProjectName}-shared-utilities-${Environment}"
    Description: "Shared utilities for DRS orchestration handlers"
    Content:
      S3Bucket: !Ref SourceBucket
      S3Key: "lambda/shared-layer.zip"
    CompatibleRuntimes:
      - python3.12
```

**Add Three Handler Functions** (all using unified IAM role):
```yaml
DataManagementHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub "${ProjectName}-data-management-handler-${Environment}"
    Runtime: python3.12
    Handler: index.lambda_handler
    Role: !Ref UnifiedOrchestrationRoleArn  # Shared role across all handlers
    Code:
      S3Bucket: !Ref SourceBucket
      S3Key: "lambda/data-management-handler.zip"
    Layers:
      - !Ref SharedUtilitiesLayer
    Timeout: 120
    MemorySize: 512
    Environment:
      Variables:
        PROTECTION_GROUPS_TABLE: !Ref ProtectionGroupsTableName
        RECOVERY_PLANS_TABLE: !Ref RecoveryPlansTableName
        EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTableName

ExecutionHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub "${ProjectName}-execution-handler-${Environment}"
    Runtime: python3.12
    Handler: index.lambda_handler
    Role: !Ref UnifiedOrchestrationRoleArn  # Shared role across all handlers
    Code:
      S3Bucket: !Ref SourceBucket
      S3Key: "lambda/execution-handler.zip"
    Layers:
      - !Ref SharedUtilitiesLayer
    Timeout: 300
    MemorySize: 512
    Environment:
      Variables:
        PROTECTION_GROUPS_TABLE: !Ref ProtectionGroupsTableName
        RECOVERY_PLANS_TABLE: !Ref RecoveryPlansTableName
        EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTableName
        STATE_MACHINE_ARN: !Sub "arn:${AWS::Partition}:states:${AWS::Region}:${AWS::AccountId}:stateMachine:${ProjectName}-orchestration-${Environment}"

QueryHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub "${ProjectName}-query-handler-${Environment}"
    Runtime: python3.12
    Handler: index.lambda_handler
    Role: !Ref UnifiedOrchestrationRoleArn  # Shared role across all handlers
    Code:
      S3Bucket: !Ref SourceBucket
      S3Key: "lambda/query-handler.zip"
    Layers:
      - !Ref SharedUtilitiesLayer
    Timeout: 60
    MemorySize: 256
    Environment:
      Variables:
        PROTECTION_GROUPS_TABLE: !Ref ProtectionGroupsTableName
        RECOVERY_PLANS_TABLE: !Ref RecoveryPlansTableName
        EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTableName
        TARGET_ACCOUNTS_TABLE: !Ref TargetAccountsTableName
```

**Add Outputs**:
```yaml
Outputs:
  DataManagementHandlerArn:
    Value: !GetAtt DataManagementHandlerFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-DataManagementHandlerArn"
  
  ExecutionHandlerArn:
    Value: !GetAtt ExecutionHandlerFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-ExecutionHandlerArn"
  
  QueryHandlerArn:
    Value: !GetAtt QueryHandlerFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-QueryHandlerArn"
  
  SharedUtilitiesLayerArn:
    Value: !Ref SharedUtilitiesLayer
    Export:
      Name: !Sub "${AWS::StackName}-SharedUtilitiesLayerArn"
```

### API Gateway Stack Updates

**api-gateway-core-methods-stack.yaml** (Protection Groups, Recovery Plans):
```yaml
Parameters:
  DataManagementHandlerArn:
    Type: String
    Description: "ARN of Data Management Handler Lambda"

Resources:
  # Update all Protection Group methods
  ProtectionGroupsGetMethod:
    Properties:
      Integration:
        Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${DataManagementHandlerArn}/invocations"
  
  ProtectionGroupsPostMethod:
    Properties:
      Integration:
        Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${DataManagementHandlerArn}/invocations"
  
  # Update all Recovery Plan methods
  RecoveryPlansGetMethod:
    Properties:
      Integration:
        Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${DataManagementHandlerArn}/invocations"
  
  # Add Lambda permission
  DataManagementHandlerApiPermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref DataManagementHandlerArn
      Action: lambda:InvokeFunction
      Principal: apigateway.amazonaws.com
      SourceArn: !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${RestApiId}/*"
```

**api-gateway-operations-methods-stack.yaml** (Executions, DRS Operations):
```yaml
Parameters:
  ExecutionHandlerArn:
    Type: String
    Description: "ARN of Execution Handler Lambda"

Resources:
  # Update all Execution methods
  ExecutionsGetMethod:
    Properties:
      Integration:
        Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ExecutionHandlerArn}/invocations"
  
  # Update all DRS operation methods
  DrsFailoverPostMethod:
    Properties:
      Integration:
        Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ExecutionHandlerArn}/invocations"
  
  # Add Lambda permission
  ExecutionHandlerApiPermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref ExecutionHandlerArn
      Action: lambda:InvokeFunction
      Principal: apigateway.amazonaws.com
      SourceArn: !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${RestApiId}/*"
```

**api-gateway-infrastructure-methods-stack.yaml** (DRS Infrastructure, EC2, Config):
```yaml
Parameters:
  QueryHandlerArn:
    Type: String
    Description: "ARN of Query Handler Lambda"

Resources:
  # Update all DRS infrastructure methods
  DrsSourceServersGetMethod:
    Properties:
      Integration:
        Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${QueryHandlerArn}/invocations"
  
  # Update all EC2 methods
  Ec2SubnetsGetMethod:
    Properties:
      Integration:
        Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${QueryHandlerArn}/invocations"
  
  # Update all Config methods
  ConfigExportGetMethod:
    Properties:
      Integration:
        Uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${QueryHandlerArn}/invocations"
  
  # Add Lambda permission
  QueryHandlerApiPermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref QueryHandlerArn
      Action: lambda:InvokeFunction
      Principal: apigateway.amazonaws.com
      SourceArn: !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${RestApiId}/*"
```

### master-template.yaml Updates

**Pass Handler ARNs to API Gateway Stacks**:
```yaml
ApiGatewayCoreMethodsStack:
  Properties:
    Parameters:
      DataManagementHandlerArn: !GetAtt LambdaStack.Outputs.DataManagementHandlerArn

ApiGatewayOperationsMethodsStack:
  Properties:
    Parameters:
      ExecutionHandlerArn: !GetAtt LambdaStack.Outputs.ExecutionHandlerArn

ApiGatewayInfrastructureMethodsStack:
  Properties:
    Parameters:
      QueryHandlerArn: !GetAtt LambdaStack.Outputs.QueryHandlerArn
```


## Deployment Process

### Build and Package

**Step 1: Package Lambda Layer**
```bash
#!/bin/bash
# scripts/package-lambda-layer.sh

cd lambda/shared
mkdir -p python
cp -r *.py python/
zip -r ../../build/shared-layer.zip python/
rm -rf python

aws s3 cp ../../build/shared-layer.zip s3://${SOURCE_BUCKET}/lambda/shared-layer.zip
```

**Step 2: Package Handler Functions**
```bash
#!/bin/bash
# scripts/package-handlers.sh

for handler in data-management-handler execution-handler query-handler; do
    cd lambda/${handler}
    
    # Install dependencies
    pip install -r requirements.txt -t .
    
    # Package function
    zip -r ../../build/${handler}.zip . -x "*.pyc" -x "__pycache__/*"
    
    # Upload to S3
    aws s3 cp ../../build/${handler}.zip s3://${SOURCE_BUCKET}/lambda/${handler}.zip
    
    cd ../..
done
```

**Step 3: Deploy CloudFormation Stack**
```bash
#!/bin/bash
# scripts/deploy-decomposed-handlers.sh

# Deploy Lambda stack with new handlers
aws cloudformation update-stack \
  --stack-name ${PROJECT_NAME}-lambda-${ENVIRONMENT} \
  --template-body file://cfn/lambda-stack.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=${PROJECT_NAME} \
    ParameterKey=Environment,ParameterValue=${ENVIRONMENT} \
    ParameterKey=SourceBucket,ParameterValue=${SOURCE_BUCKET} \
  --capabilities CAPABILITY_IAM

# Wait for stack update
aws cloudformation wait stack-update-complete \
  --stack-name ${PROJECT_NAME}-lambda-${ENVIRONMENT}

# Deploy API Gateway stacks with new handler ARNs
for stack in core-methods operations-methods infrastructure-methods; do
    aws cloudformation update-stack \
      --stack-name ${PROJECT_NAME}-api-gateway-${stack}-${ENVIRONMENT} \
      --use-previous-template \
      --parameters \
        ParameterKey=DataManagementHandlerArn,UsePreviousValue=false,ParameterValue=$(aws cloudformation describe-stacks --stack-name ${PROJECT_NAME}-lambda-${ENVIRONMENT} --query 'Stacks[0].Outputs[?OutputKey==`DataManagementHandlerArn`].OutputValue' --output text) \
        ParameterKey=ExecutionHandlerArn,UsePreviousValue=false,ParameterValue=$(aws cloudformation describe-stacks --stack-name ${PROJECT_NAME}-lambda-${ENVIRONMENT} --query 'Stacks[0].Outputs[?OutputKey==`ExecutionHandlerArn`].OutputValue' --output text) \
        ParameterKey=QueryHandlerArn,UsePreviousValue=false,ParameterValue=$(aws cloudformation describe-stacks --stack-name ${PROJECT_NAME}-lambda-${ENVIRONMENT} --query 'Stacks[0].Outputs[?OutputKey==`QueryHandlerArn`].OutputValue' --output text)
    
    aws cloudformation wait stack-update-complete \
      --stack-name ${PROJECT_NAME}-api-gateway-${stack}-${ENVIRONMENT}
done

# Create new API Gateway deployment
API_ID=$(aws cloudformation describe-stacks \
  --stack-name ${PROJECT_NAME}-api-gateway-core-${ENVIRONMENT} \
  --query 'Stacks[0].Outputs[?OutputKey==`RestApiId`].OutputValue' \
  --output text)

aws apigateway create-deployment \
  --rest-api-id ${API_ID} \
  --stage-name ${ENVIRONMENT} \
  --description "Deploy decomposed handlers"
```

### Rollback Process

**Automated Rollback Script**:
```bash
#!/bin/bash
# scripts/rollback-decomposition.sh

# Revert API Gateway to monolithic handler
MONOLITHIC_HANDLER_ARN=$(aws cloudformation describe-stacks \
  --stack-name ${PROJECT_NAME}-lambda-${ENVIRONMENT} \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiHandlerFunctionArn`].OutputValue' \
  --output text)

for stack in core-methods operations-methods infrastructure-methods; do
    aws cloudformation update-stack \
      --stack-name ${PROJECT_NAME}-api-gateway-${stack}-${ENVIRONMENT} \
      --use-previous-template \
      --parameters \
        ParameterKey=ApiHandlerFunctionArn,ParameterValue=${MONOLITHIC_HANDLER_ARN}
    
    aws cloudformation wait stack-update-complete \
      --stack-name ${PROJECT_NAME}-api-gateway-${stack}-${ENVIRONMENT}
done

# Create new API Gateway deployment
API_ID=$(aws cloudformation describe-stacks \
  --stack-name ${PROJECT_NAME}-api-gateway-core-${ENVIRONMENT} \
  --query 'Stacks[0].Outputs[?OutputKey==`RestApiId`].OutputValue' \
  --output text)

aws apigateway create-deployment \
  --rest-api-id ${API_ID} \
  --stage-name ${ENVIRONMENT} \
  --description "Rollback to monolithic handler"

echo "Rollback complete. Monolithic handler restored."
```

### Monitoring and Validation

**Post-Deployment Validation**:
```bash
#!/bin/bash
# scripts/validate-decomposition.sh

API_URL="https://api.example.com"

# Test Query Handler
echo "Testing Query Handler..."
curl -s -X GET "${API_URL}/drs/source-servers?region=us-east-1" | jq .
curl -s -X GET "${API_URL}/drs/quotas?region=us-east-1" | jq .

# Test Data Management Handler
echo "Testing Data Management Handler..."
curl -s -X GET "${API_URL}/protection-groups" | jq .
curl -s -X GET "${API_URL}/recovery-plans" | jq .

# Test Execution Handler
echo "Testing Execution Handler..."
curl -s -X GET "${API_URL}/executions" | jq .

# Check CloudWatch Logs for errors
echo "Checking CloudWatch Logs..."
for handler in data-management-handler execution-handler query-handler; do
    echo "Checking ${handler}..."
    aws logs tail /aws/lambda/${PROJECT_NAME}-${handler}-${ENVIRONMENT} \
      --since 5m \
      --filter-pattern "ERROR" \
      --format short
done

# Check CloudWatch Metrics
echo "Checking CloudWatch Metrics..."
for handler in data-management-handler execution-handler query-handler; do
    echo "Metrics for ${handler}:"
    aws cloudwatch get-metric-statistics \
      --namespace AWS/Lambda \
      --metric-name Errors \
      --dimensions Name=FunctionName,Value=${PROJECT_NAME}-${handler}-${ENVIRONMENT} \
      --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
      --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
      --period 300 \
      --statistics Sum
done
```


## Performance Optimization

### Cold Start Reduction

**Handler Size Comparison**:
| Handler | Lines of Code | Package Size | Cold Start Target |
|---------|---------------|--------------|-------------------|
| Monolithic | 11,558 | ~15 MB | 3-5 seconds |
| Data Management | ~4,500 | ~6 MB | <3 seconds |
| Execution | ~4,500 | ~6 MB | <3 seconds |
| Query | ~2,000 | ~3 MB | <2 seconds |

**Cold Start Improvements**:
- Query Handler: 40% faster cold starts (smaller package)
- Reduced dependency loading per handler
- Lambda Layer caching across handlers

### Memory Optimization

**Handler Memory Allocation**:
```yaml
DataManagementHandler:
  MemorySize: 512 MB  # Tag resolution requires DRS API calls
  
ExecutionHandler:
  MemorySize: 512 MB  # DRS operations and Step Functions integration
  
QueryHandler:
  MemorySize: 256 MB  # Read-only operations, minimal memory footprint
```

**Cost Savings**:
- Query Handler: 50% memory reduction (512 MB → 256 MB)
- Estimated monthly savings: $50-100 for high-traffic query endpoints

### Concurrent Execution

**Independent Scaling**:
- Query Handler: High concurrency (100+ concurrent executions)
- Data Management Handler: Medium concurrency (20-50 concurrent executions)
- Execution Handler: Low concurrency (5-10 concurrent executions)

**Reserved Concurrency** (Optional):
```yaml
QueryHandlerFunction:
  ReservedConcurrentExecutions: 100  # Prevent throttling on high-traffic queries

ExecutionHandlerFunction:
  ReservedConcurrentExecutions: 10  # Limit concurrent DR operations
```

## Security Considerations

### Unified IAM Role Approach

All handlers use a single `UnifiedOrchestrationRole` with full permissions. Security is enforced at the application level:

**Application-Level Security**:
- RBAC enforced via Cognito user attributes (standalone mode)
- Audit logging tracks which user performed which operation
- CloudTrail logs all IAM role actions with full context

**Benefits**:
- Simplified IAM management (one role instead of three)
- No permission boundary issues between handlers
- Seamless HRP integration (HRP orchestration role controls all functions)
- Easier troubleshooting (no "which handler needs which permission?" questions)

### Audit Logging

**CloudWatch Logs**:
```python
# Log all operations with user context
logger.info(
    "Operation executed",
    extra={
        "operation": "create_protection_group",
        "user": user_email,
        "userId": user_id,
        "groupId": group_id,
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

**CloudTrail Integration**:
- All Lambda invocations logged to CloudTrail
- API Gateway requests logged with Cognito user context
- DRS API calls logged with assumed role information

### Input Validation

**Request Validation**:
```python
def validate_protection_group_input(body: Dict) -> List[str]:
    """Validate Protection Group creation input"""
    errors = []
    
    if not body.get("groupName"):
        errors.append("groupName is required")
    elif len(body["groupName"]) > 64:
        errors.append("groupName must be 64 characters or fewer")
    
    if not body.get("region"):
        errors.append("region is required")
    elif body["region"] not in DRS_REGIONS:
        errors.append(f"Invalid region: {body['region']}")
    
    return errors
```

## Observability

### CloudWatch Metrics

**Custom Metrics**:
```python
cloudwatch = boto3.client("cloudwatch")

# Track handler-specific metrics
cloudwatch.put_metric_data(
    Namespace="DROrchestration",
    MetricData=[
        {
            "MetricName": "ProtectionGroupCreated",
            "Value": 1,
            "Unit": "Count",
            "Dimensions": [
                {"Name": "Handler", "Value": "DataManagement"},
                {"Name": "Environment", "Value": os.environ["ENVIRONMENT"]}
            ]
        }
    ]
)
```

**Key Metrics to Track**:
- Handler invocation count (per handler)
- Handler duration (per handler)
- Handler errors (per handler)
- DRS API call count (per operation)
- Conflict detection results (conflicts found vs. clean)
- Tag resolution performance (servers resolved per second)

### CloudWatch Dashboards

**Handler Performance Dashboard**:
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "Handler Invocations",
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum", "label": "Data Management"}],
          ["...", {"stat": "Sum", "label": "Execution"}],
          ["...", {"stat": "Sum", "label": "Query"}]
        ]
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Handler Duration (p95)",
        "metrics": [
          ["AWS/Lambda", "Duration", {"stat": "p95", "label": "Data Management"}],
          ["...", {"stat": "p95", "label": "Execution"}],
          ["...", {"stat": "p95", "label": "Query"}]
        ]
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Handler Errors",
        "metrics": [
          ["AWS/Lambda", "Errors", {"stat": "Sum", "label": "Data Management"}],
          ["...", {"stat": "Sum", "label": "Execution"}],
          ["...", {"stat": "Sum", "label": "Query"}]
        ]
      }
    }
  ]
}
```

### Alarms

**Critical Alarms**:
```yaml
ExecutionHandlerErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${ProjectName}-execution-handler-errors-${Environment}"
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 5
    ComparisonOperator: GreaterThanThreshold
    Dimensions:
      - Name: FunctionName
        Value: !Ref ExecutionHandlerFunction
    AlarmActions:
      - !Ref AlertTopic

QueryHandlerThrottleAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${ProjectName}-query-handler-throttles-${Environment}"
    MetricName: Throttles
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 60
    EvaluationPeriods: 2
    Threshold: 10
    ComparisonOperator: GreaterThanThreshold
    Dimensions:
      - Name: FunctionName
        Value: !Ref QueryHandlerFunction
    AlarmActions:
      - !Ref AlertTopic
```

## Success Criteria

### Functional Requirements

- [ ] All 28 API endpoints return identical responses before and after decomposition
- [ ] Frontend requires zero code changes
- [ ] Direct Lambda invocation works for all three handlers
- [ ] Conflict detection accuracy maintained (no false positives/negatives)
- [ ] DRS service limits enforced correctly
- [ ] Cross-account operations work identically

### Performance Requirements

- [ ] Query Handler cold start < 2 seconds
- [ ] Data Management Handler cold start < 3 seconds
- [ ] Execution Handler cold start < 3 seconds
- [ ] API response time p95 < 500ms (unchanged)
- [ ] No increase in DRS API throttling

### Operational Requirements

- [ ] Independent deployment of each handler
- [ ] Zero downtime migration
- [ ] Rollback capability at each phase
- [ ] CloudWatch metrics for all handlers
- [ ] CloudWatch alarms for critical errors
- [ ] Comprehensive test coverage (80%+ unit, 100% integration)

### Security Requirements

- [ ] All handlers use unified IAM role (UnifiedOrchestrationRole)
- [ ] RBAC enforced at application level via Cognito user attributes
- [ ] All operations logged with user context (user ID, operation, timestamp)
- [ ] CloudTrail integration maintained for IAM role actions
- [ ] Audit logging tracks which user performed which operation

## EventBridge Integration

### Tag Sync Automation

The Data Management Handler's tag sync functionality (`POST /drs/tag-sync`) is integrated with EventBridge for automated execution:

**EventBridge Rule**: `${ProjectName}-tag-sync-schedule-${Environment}`
- **Schedule**: `rate(1 hour)` - Triggers every hour
- **Target**: Data Management Handler Lambda
- **Input**: `{"synch_tags": true, "synch_instance_type": true}`
- **State**: ENABLED (controlled by `EnableTagSync` CloudFormation parameter)
- **Purpose**: Automatically sync EC2 tags and instance types to DRS source servers

**Implementation Notes**:
- EventBridge invokes the Data Management Handler directly (not via API Gateway)
- Handler must detect EventBridge invocation pattern and skip RBAC middleware
- Tag sync operations are idempotent (safe to run multiple times)
- Failures are logged to CloudWatch and published to DRS Alerts SNS topic

**CloudFormation Configuration** (eventbridge-stack.yaml):
```yaml
TagSyncScheduleRule:
  Type: AWS::Events::Rule
  Properties:
    Name: !Sub '${ProjectName}-tag-sync-schedule-${Environment}'
    ScheduleExpression: 'rate(1 hour)'
    State: ENABLED
    Targets:
      - Arn: !GetAtt DataManagementHandlerFunction.Arn
        Input: '{"synch_tags": true, "synch_instance_type": true}'
```

## Out-of-Scope Lambda Functions

The following Lambda functions are **NOT part of the API handler decomposition** and should remain as separate, independent functions:

### 1. execution-poller
- **Function**: `${ProjectName}-execution-poller-${Environment}`
- **Purpose**: Polls DRS job status and updates execution wave states in DynamoDB
- **Invocation**: Lambda-to-Lambda (invoked by execution-finder)
- **Timeout**: 120s
- **Memory**: 256 MB
- **Why Out of Scope**: Background job polling with different invocation pattern (not API Gateway)

### 2. execution-finder
- **Function**: `${ProjectName}-execution-finder-${Environment}`
- **Purpose**: Queries StatusIndex GSI for executions in POLLING status
- **Invocation**: EventBridge (every 1 minute)
- **Timeout**: 60s
- **Memory**: 256 MB
- **Why Out of Scope**: EventBridge-triggered discovery with different invocation pattern

### 3. notification-formatter
- **Function**: `${ProjectName}-notification-formatter-${Environment}`
- **Purpose**: Formats DRS orchestration events into user-friendly notifications
- **Invocation**: Event-driven (Step Functions, SNS)
- **Timeout**: 60s
- **Memory**: 256 MB
- **Why Out of Scope**: Event-driven notification formatting with different invocation pattern

### 4. frontend-deployer
- **Function**: `${ProjectName}-frontend-deployer-${Environment}`
- **Purpose**: Builds and deploys React frontend to S3/CloudFront
- **Invocation**: Manual or CI/CD pipeline
- **Timeout**: 900s
- **Memory**: 2048 MB
- **Why Out of Scope**: Frontend deployment automation, not part of API operations

### 5. orchestration-stepfunctions
- **Function**: `${ProjectName}-orch-sf-${Environment}`
- **Purpose**: Wave-based orchestration logic with tag-based discovery (AWSM-1103)
- **Invocation**: Step Functions state machine
- **Timeout**: 120s
- **Memory**: 512 MB
- **Why Out of Scope**: Step Functions orchestration logic, separate from API operations

**Key Principle**: The API handler decomposition focuses ONLY on the monolithic API handler Lambda function that serves the 48 REST API endpoints. All other Lambda functions with different invocation patterns (EventBridge, Lambda-to-Lambda, Step Functions) remain independent and unchanged.

## Next Steps

1. **Review and Approve Design** (1 day)
   - Stakeholder review of design document
   - Address feedback and questions
   - Finalize handler boundaries and API routing

2. **Create Implementation Tasks** (1 day)
   - Break down design into implementation tasks
   - Estimate effort for each task
   - Prioritize tasks by phase

3. **Phase 1: Query Handler** (1 week)
   - Extract shared utilities to Lambda Layer
   - Create Query Handler function
   - Update API Gateway routing
   - Deploy and validate

4. **Phase 2: Execution Handler** (1 week)
   - Create Execution Handler function
   - Update API Gateway routing
   - Deploy and validate

5. **Phase 3: Data Management Handler** (1 week)
   - Create Data Management Handler function
   - Update API Gateway routing
   - Decommission monolithic handler
   - Deploy and validate

**Total Estimated Duration**: 3-4 weeks

