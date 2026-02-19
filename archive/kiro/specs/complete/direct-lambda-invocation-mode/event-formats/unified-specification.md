# Unified Direct Invocation Event Format Specification

**Purpose**: Comprehensive specification of direct Lambda invocation patterns across all handlers  
**Date**: January 31, 2026  
**Version**: 1.0

## Overview

The DR Orchestration Platform supports **direct Lambda invocation** as an alternative to API Gateway for internal operations, Step Functions orchestration, and CLI/SDK access. This document provides a unified specification of event formats, invocation patterns, and response structures across all three Lambda handlers.

## Handler Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Invocation Sources                            │
├─────────────────────────────────────────────────────────────────────┤
│  API Gateway  │  Step Functions  │  EventBridge  │  Direct (CLI/SDK) │
└─────────────────────────────────────────────────────────────────────┘
         │              │                  │                │
         ▼              ▼                  ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Lambda Handlers                               │
├───────────────────┬───────────────────┬─────────────────────────────┤
│ query-handler     │ data-management   │ execution-handler           │
│                   │ handler           │                             │
├───────────────────┼───────────────────┼─────────────────────────────┤
│ Read Operations:  │ CRUD Operations:  │ Execution Control:          │
│ - DRS servers     │ - Protection Grps │ - Start recovery            │
│ - EC2 resources   │ - Recovery Plans  │ - Pause/Resume              │
│ - Capacity data   │ - Target Accounts │ - Cancel execution          │
│ - Config export   │ - Tag sync        │ - Poll DRS jobs             │
└───────────────────┴───────────────────┴─────────────────────────────┘
```

## Invocation Mode Detection

Each handler detects invocation mode using this priority order:

### query-handler Detection

```python
def lambda_handler(event, context):
    # 1. API Gateway invocation
    if event.get("httpMethod") and event.get("path"):
        return handle_api_gateway_request(event, context)
    
    # 2. Direct invocation
    if event.get("operation"):
        return handle_direct_invocation(event, context)
    
    # 3. Unknown invocation
    return {"error": "Unknown invocation pattern"}
```

### data-management-handler Detection

```python
def lambda_handler(event, context):
    # 1. API Gateway invocation
    if event.get("httpMethod") and event.get("path"):
        return handle_api_gateway_request(event, context)
    
    # 2. Direct invocation
    if event.get("operation"):
        return handle_direct_invocation(event, context)
    
    # 3. Unknown invocation
    return {"error": "Unknown invocation pattern"}
```

### execution-handler Detection

```python
def lambda_handler(event, context):
    # 1. Worker pattern (async background execution)
    if event.get("worker"):
        execute_recovery_plan_worker(event)
        return {"statusCode": 200, "body": "Worker completed"}
    
    # 2. Action-based invocation (Step Functions)
    if event.get("action"):
        return handle_action_invocation(event)
    
    # 3. Operation-based invocation (EventBridge + direct)
    if event.get("operation"):
        return handle_operation(event, context)
    
    # 4. EventBridge scheduled trigger
    if event.get("source") == "aws.events":
        return handle_find_operation(event, context)
    
    # 5. API Gateway invocation (default)
    return handle_api_gateway_request(event, context)
```

## Common Event Structure Patterns

### Pattern 1: Operation-Based (query-handler, data-management-handler)

**Structure**:
```json
{
  "operation": "operation_name",
  "body": {...},
  "queryParams": {...}
}
```

**Fields**:
- `operation` (string, required): Operation identifier
- `body` (object, optional): Request body for create/update operations
- `queryParams` (object, optional): Query parameters for list/filter operations

**Used By**:
- query-handler: All 16 operations
- data-management-handler: All 18 operations

---

### Pattern 2: Action-Based (execution-handler only)

**Structure**:
```json
{
  "action": "action_name",
  "state": {...},
  "wave_number": 1
}
```

**Fields**:
- `action` (string, required): Action identifier (currently only `start_wave_recovery`)
- `state` (object, required): Step Functions state object
- `wave_number` (number, required): Wave to execute

**Used By**:
- execution-handler: Step Functions orchestration

---

### Pattern 3: Operation-Based (execution-handler)

**Structure**:
```json
{
  "operation": "operation_name",
  "executionId": "uuid",
  "planId": "uuid",
  "queryParams": {...}
}
```

**Fields**:
- `operation` (string, required): Operation identifier
- `executionId` (string, optional): Execution ID
- `planId` (string, optional): Recovery plan ID
- `queryParams` (object, optional): Additional parameters

**Used By**:
- execution-handler: Background polling, lifecycle management, direct invocation

---

## Response Format Standards

### Success Response (query-handler)

Direct invocation returns **raw data** without API Gateway wrapping:

```json
{
  "servers": [...],
  "totalCount": 25
}
```

**No `statusCode` or `body` wrapping** - returns data directly.

---

### Success Response (data-management-handler)

Returns **API Gateway format** even for direct invocation:

```json
{
  "statusCode": 200,
  "body": {
    "groupId": "pg-123",
    "message": "Protection group created successfully"
  }
}
```

**Always includes `statusCode` and `body` fields**.

---

### Success Response (execution-handler)

**Action-based**: Returns modified `state` object directly:

```json
{
  "executionId": "exec-123",
  "planId": "rp-456",
  "drsJobId": "drsjob-abc",
  "status": "STARTED",
  ...
}
```

**Operation-based**: Returns API Gateway format:

```json
{
  "statusCode": 200,
  "executionId": "exec-123",
  "status": "RUNNING",
  ...
}
```

---

### Error Response (All Handlers)

**query-handler**:
```json
{
  "error": "Unknown operation",
  "operation": "invalid_operation_name"
}
```

**data-management-handler**:
```json
{
  "statusCode": 400,
  "body": {
    "error": "UNKNOWN_OPERATION",
    "message": "Unknown operation: invalid_operation"
  }
}
```

**execution-handler**:
```json
{
  "statusCode": 400,
  "error": "UNKNOWN_OPERATION",
  "message": "Unknown operation: invalid_operation"
}
```

---

## Parameter Naming Conventions

### Resource Identifiers

| Resource | Parameter Name | Format | Example |
|----------|---------------|--------|---------|
| Protection Group | `groupId` | UUID | `pg-a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Recovery Plan | `planId` | UUID | `rp-b2c3d4e5-f6a7-8901-bcde-f12345678901` |
| Execution | `executionId` | UUID | `exec-c3d4e5f6-a7b8-9012-cdef-123456789012` |
| DRS Source Server | `serverId` or `sourceServerId` | DRS format | `s-1234567890abcdef0` |
| DRS Job | `drsJobId` | DRS format | `drsjob-1234567890abcdef0` |
| AWS Account | `accountId` | 12-digit | `123456789012` |
| AWS Region | `region` | Region code | `us-east-1` |

### Common Parameters

| Parameter | Type | Description | Used By |
|-----------|------|-------------|---------|
| `operation` | string | Operation identifier | All handlers (direct invocation) |
| `action` | string | Action identifier | execution-handler (Step Functions) |
| `body` | object | Request body | data-management-handler |
| `queryParams` | object | Query parameters | query-handler, execution-handler |
| `accountContext` | object | Cross-account context | All handlers |
| `region` | string | AWS region | All handlers |
| `accountId` | string | AWS account ID | All handlers |

---

## Cross-Account Context Structure

All handlers support cross-account operations using this standard structure:

```json
{
  "accountContext": {
    "accountId": "123456789012",
    "region": "us-east-1",
    "roleName": "DRSOrchestrationRole",
    "externalId": "unique-external-id"
  }
}
```

**Fields**:
- `accountId` (string, required): Target AWS account ID
- `region` (string, required): Target AWS region
- `roleName` (string, required): IAM role name for cross-account access
- `externalId` (string, optional): External ID for role assumption

**Usage**:
- query-handler: `get_drs_source_servers`, `get_drs_account_capacity_all_regions`
- data-management-handler: All protection group and recovery plan operations
- execution-handler: All execution operations

---

## AWS CLI Invocation Patterns

### Basic Invocation

```bash
aws lambda invoke \
  --function-name <handler-name> \
  --payload '<json-payload>' \
  response.json
```

### With Output Parsing

```bash
aws lambda invoke \
  --function-name <handler-name> \
  --payload '<json-payload>' \
  response.json && cat response.json | jq .
```

### From File

```bash
aws lambda invoke \
  --function-name <handler-name> \
  --payload file://event.json \
  response.json
```

### Async Invocation

```bash
aws lambda invoke \
  --function-name <handler-name> \
  --invocation-type Event \
  --payload '<json-payload>' \
  response.json
```

---

## Python boto3 Invocation Patterns

### Synchronous Invocation

```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='handler-name',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "operation_name",
        "queryParams": {...}
    })
)

result = json.loads(response['Payload'].read())
```

### Asynchronous Invocation

```python
response = lambda_client.invoke(
    FunctionName='handler-name',
    InvocationType='Event',
    Payload=json.dumps({
        "operation": "operation_name"
    })
)
```

### With Error Handling

```python
try:
    response = lambda_client.invoke(
        FunctionName='handler-name',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    
    result = json.loads(response['Payload'].read())
    
    if 'error' in result or result.get('statusCode', 200) >= 400:
        print(f"Error: {result.get('error') or result.get('body', {}).get('error')}")
    else:
        print(f"Success: {result}")
        
except Exception as e:
    print(f"Invocation failed: {e}")
```

---

## Operation Inventory Summary

### query-handler (16 operations)

| Category | Operations | Count |
|----------|-----------|-------|
| DRS Infrastructure | get_drs_source_servers, get_drs_account_capacity, get_drs_account_capacity_all_regions, get_drs_regional_capacity | 4 |
| Account Management | get_target_accounts | 1 |
| EC2 Resources | get_ec2_subnets, get_ec2_security_groups, get_ec2_instance_profiles, get_ec2_instance_types | 4 |
| Account Info | get_current_account_id | 1 |
| Config Export | export_configuration | 1 |
| User Permissions | get_user_permissions | 1 |
| Staging Accounts | validate_staging_account, discover_staging_accounts, get_combined_capacity | 3 |
| Synchronization | sync_staging_accounts | 1 |

### data-management-handler (18 operations)

| Category | Operations | Count |
|----------|-----------|-------|
| Protection Groups | create_protection_group, list_protection_groups, get_protection_group, update_protection_group, delete_protection_group, resolve_protection_group_tags | 6 |
| Recovery Plans | create_recovery_plan, list_recovery_plans, get_recovery_plan, update_recovery_plan, delete_recovery_plan | 5 |
| Tag Sync & Config | handle_drs_tag_sync, get_tag_sync_settings, update_tag_sync_settings, import_configuration | 4 |
| Staging Accounts | add_staging_account, remove_staging_account, sync_staging_accounts | 3 |

### execution-handler (7 operations)

| Category | Operations | Count |
|----------|-----------|-------|
| Background Polling | find, poll | 2 |
| Lifecycle Management | finalize, pause, resume | 3 |
| Direct Invocation | start_execution, get_execution_details | 2 |

**Total Operations**: 41 across all handlers

---

## Validation Rules

### Common Validations

All handlers perform these validations:

1. **Operation Exists**: Operation name must be in supported operations list
2. **Required Parameters**: All required parameters must be present
3. **Parameter Types**: Parameters must match expected types
4. **Resource Existence**: Referenced resources must exist (groupId, planId, etc.)
5. **State Validation**: Operations must be valid for current resource state

### Handler-Specific Validations

**query-handler**:
- Valid AWS region codes
- Valid VPC IDs for EC2 queries
- Valid account IDs for cross-account queries

**data-management-handler**:
- Unique names (protection groups, recovery plans)
- No active executions when updating/deleting
- No server conflicts across protection groups
- Valid wave dependencies (no circular dependencies)
- DRS limits (max 100 servers per wave)

**execution-handler**:
- Valid execution states for pause/resume
- No conflicting active executions
- Valid Step Functions task tokens
- Valid DRS job IDs

---

## Security Considerations

### IAM Permissions

**Direct Invocation Requires**:
```json
{
  "Effect": "Allow",
  "Action": "lambda:InvokeFunction",
  "Resource": [
    "arn:aws:lambda:*:*:function:query-handler",
    "arn:aws:lambda:*:*:function:data-management-handler",
    "arn:aws:lambda:*:*:function:execution-handler"
  ]
}
```

### Cross-Account Access

**Target Account Role**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ORCHESTRATOR_ACCOUNT:role/LambdaExecutionRole"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-external-id"
        }
      }
    }
  ]
}
```

### Input Validation

All handlers validate:
- Parameter types and formats
- Resource identifier formats (UUIDs, AWS IDs)
- Enum values (executionType, status, etc.)
- Cross-account context structure
- No SQL injection or command injection vectors

---

## Performance Considerations

### Invocation Latency

| Handler | Typical Latency | Notes |
|---------|----------------|-------|
| query-handler | 100-500ms | DRS API calls add latency |
| data-management-handler | 50-200ms | DynamoDB operations |
| execution-handler | 200-1000ms | Step Functions + DRS API |

### Concurrency Limits

- **Reserved Concurrency**: 10 per handler (configurable)
- **Burst Concurrency**: 1000 (account-level)
- **Throttling**: Exponential backoff recommended

### Optimization Tips

1. **Batch Operations**: Use list operations instead of multiple get operations
2. **Async Invocation**: Use `InvocationType='Event'` for non-critical operations
3. **Caching**: Cache DRS source server lists (5-minute TTL)
4. **Pagination**: Use pagination for large result sets

---

## Monitoring and Logging

### CloudWatch Metrics

All handlers emit:
- `Invocations`: Total invocation count
- `Errors`: Error count
- `Duration`: Execution duration
- `Throttles`: Throttle count

### Custom Metrics

- `DirectInvocations`: Count of direct invocations (vs API Gateway)
- `OperationLatency`: Per-operation latency
- `CrossAccountCalls`: Cross-account operation count

### Logging Format

```json
{
  "timestamp": "2025-01-31T15:30:00Z",
  "level": "INFO",
  "handler": "query-handler",
  "operation": "get_drs_source_servers",
  "invocationType": "direct",
  "duration": 250,
  "statusCode": 200
}
```

---

## Testing Direct Invocation

### Unit Test Example

```python
import json
from lambda.query_handler import index

def test_direct_invocation():
    event = {
        "operation": "get_drs_source_servers",
        "queryParams": {
            "region": "us-east-1"
        }
    }
    
    context = MockContext()
    response = index.lambda_handler(event, context)
    
    assert "servers" in response
    assert response["totalCount"] >= 0
```

### Integration Test Example

```python
import boto3
import json

def test_direct_invocation_integration():
    lambda_client = boto3.client('lambda')
    
    response = lambda_client.invoke(
        FunctionName='query-handler',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            "operation": "get_target_accounts"
        })
    )
    
    result = json.loads(response['Payload'].read())
    assert "accounts" in result
    assert result["count"] >= 0
```

---

## Migration from API Gateway

### API Gateway Request

```json
{
  "httpMethod": "GET",
  "path": "/drs/source-servers",
  "queryStringParameters": {
    "region": "us-east-1"
  },
  "headers": {
    "Authorization": "Bearer <token>"
  }
}
```

### Direct Invocation Equivalent

```json
{
  "operation": "get_drs_source_servers",
  "queryParams": {
    "region": "us-east-1"
  }
}
```

### Key Differences

| Aspect | API Gateway | Direct Invocation |
|--------|-------------|-------------------|
| Authentication | Cognito JWT | IAM permissions |
| Request Format | HTTP request | JSON event |
| Response Format | HTTP response | JSON object |
| Latency | +50-100ms | Baseline |
| Cost | $3.50/million | $0.20/million |

---

## Best Practices

### DO

✅ Use direct invocation for:
- Internal service-to-service communication
- Step Functions orchestration
- EventBridge scheduled tasks
- CLI/SDK automation scripts
- High-volume operations (cost optimization)

✅ Validate all inputs before processing

✅ Use consistent parameter naming across handlers

✅ Return structured error responses

✅ Log all invocations with operation name

### DON'T

❌ Use direct invocation for:
- Frontend user requests (use API Gateway)
- Operations requiring user authentication (use API Gateway + Cognito)

❌ Bypass validation for "trusted" callers

❌ Return sensitive data without authorization checks

❌ Use hardcoded resource identifiers

❌ Ignore error responses

---

## Future Enhancements

### Planned Improvements

1. **Standardized Error Codes**: Unified error code taxonomy across all handlers
2. **Request Validation Schema**: JSON Schema validation for all operations
3. **Operation Discovery**: `list_operations` operation for each handler
4. **Batch Operations**: Support for batching multiple operations in single invocation
5. **Async Response Pattern**: Long-running operations with callback support
6. **Versioning**: API versioning for backward compatibility

### Under Consideration

- GraphQL-style query language for complex queries
- WebSocket support for real-time updates
- gRPC support for high-performance invocations
- OpenAPI specification generation

---

## Related Documentation

- [Query Handler Events](query-handler-events.md) - Complete query-handler operation reference
- [Data Management Handler Events](data-management-handler-events.md) - Complete data-management-handler operation reference
- [Execution Handler Action Events](execution-handler-action-events.md) - Step Functions action-based invocation
- [Execution Handler Operation Events](execution-handler-operation-events.md) - EventBridge and direct invocation operations
- [API Reference](../api-reference.md) - Complete API documentation
- [Design Document](../design.md) - Architecture and design decisions
