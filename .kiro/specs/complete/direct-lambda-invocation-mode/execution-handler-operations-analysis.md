# Execution Handler Operations Analysis

## Overview

The execution-handler Lambda function currently supports **three distinct invocation patterns**:

1. **API Gateway Invocation** (HTTP REST API)
2. **Action-Based Invocation** (Step Functions orchestration)
3. **Operation-Based Invocation** (EventBridge + direct invocation)

## Current Invocation Patterns

### 1. API Gateway Invocation Pattern

**Detection**: Event contains `httpMethod` and `path` fields

**Supported HTTP Endpoints**:

| Method | Path | Handler Function | Purpose |
|--------|------|------------------|---------|
| POST | `/executions` | `execute_recovery_plan()` | Start new recovery execution |
| POST | `/recovery-plans/{id}/execute` | `execute_recovery_plan()` | Legacy endpoint for starting execution |
| GET | `/executions` | `list_executions()` | List all executions with filtering |
| GET | `/executions/{id}` | `get_execution_details()` | Get execution details |
| GET | `/executions/{id}/realtime` | `get_execution_details_realtime()` | Get real-time execution status |
| GET | `/executions/{id}/job-logs` | `get_job_log_items()` | Get DRS job logs |
| GET | `/executions/{id}/recovery-instances` | `get_recovery_instances()` | Get recovery instance details |
| POST | `/executions/{id}/cancel` | `cancel_execution()` | Cancel running execution |
| POST | `/executions/{id}/pause` | `pause_execution()` | Pause execution at wave boundary |
| POST | `/executions/{id}/resume` | `resume_execution()` | Resume paused execution |
| POST | `/executions/{id}/terminate-instances` | `terminate_recovery_instances()` | Terminate recovery instances |
| GET | `/executions/{id}/termination-status` | `get_termination_job_status()` | Get termination job status |
| DELETE | `/executions?ids=...` | `delete_executions_by_ids()` | Bulk delete executions |
| DELETE | `/executions/completed` | `delete_completed_executions()` | Delete all completed executions |

**Authentication**: Cognito User Pool via API Gateway authorizer

**Response Format**: API Gateway format with `statusCode`, `headers`, `body`

### 2. Action-Based Invocation Pattern

**Detection**: Event contains `action` field

**Supported Actions**:

| Action | Handler Function | Invoked By | Purpose |
|--------|------------------|------------|---------|
| `start_wave_recovery` | `start_wave_recovery()` | Step Functions | Initiate DRS StartRecovery for specific wave |

**Event Format**:
```json
{
  "action": "start_wave_recovery",
  "state": {
    "executionId": "uuid",
    "planId": "uuid",
    "accountContext": {...},
    "waves": [...]
  },
  "wave_number": 1
}
```

**Response Format**: Returns modified `state` dict directly (no API Gateway wrapping)

**Purpose**: Step Functions orchestration for wave-based recovery execution

### 3. Operation-Based Invocation Pattern

**Detection**: Event contains `operation` field

**Supported Operations**:

| Operation | Handler Function | Invoked By | Purpose |
|-----------|------------------|------------|---------|
| `find` | `handle_find_operation()` | EventBridge (30s schedule) | Find active executions needing polling |
| `poll` | `handle_poll_operation()` | Self-invocation from `find` | Poll DRS job status and update execution |
| `finalize` | `handle_finalize_operation()` | Step Functions | Mark execution as COMPLETED |
| `pause` | `handle_pause_operation()` | Direct invocation | Pause execution |
| `resume` | `handle_resume_operation()` | Direct invocation | Resume paused execution |
| `get_execution_details` | `get_execution_details()` | Direct invocation | Get execution details (no API Gateway) |
| `start_execution` | `execute_recovery_plan()` | Direct invocation | Start recovery execution (no API Gateway) |

**Event Format Examples**:

```json
// Find operation (EventBridge)
{
  "operation": "find"
}

// Poll operation (self-invocation)
{
  "operation": "poll",
  "executionId": "uuid",
  "planId": "uuid"
}

// Finalize operation (Step Functions)
{
  "operation": "finalize",
  "executionId": "uuid",
  "planId": "uuid"
}

// Start execution (direct invocation)
{
  "operation": "start_execution",
  "planId": "uuid",
  "executionType": "DRILL",
  "initiatedBy": "user@example.com",
  "accountContext": {...}
}

// Get execution details (direct invocation)
{
  "operation": "get_execution_details",
  "executionId": "uuid",
  "queryParams": {
    "planId": "uuid"
  }
}
```

**Response Format**: Returns dict with `statusCode` and operation-specific data

**Purpose**: Background polling, lifecycle management, and direct invocation support

### 4. Worker Pattern (Async Background Execution)

**Detection**: Event contains `worker: true` field

**Handler Function**: `execute_recovery_plan_worker()`

**Event Format**:
```json
{
  "worker": true,
  "executionId": "uuid",
  "planId": "uuid",
  "executionType": "DRILL",
  "initiatedBy": "user@example.com",
  "accountContext": {...}
}
```

**Purpose**: Async background execution of recovery plans to avoid API Gateway 30s timeout

**Invoked By**: Self-invocation from `execute_recovery_plan()` API handler

### 5. EventBridge Scheduled Invocation

**Detection**: Event contains `source: "aws.events"` field

**Handler Function**: `handle_find_operation()`

**Purpose**: Periodic polling trigger (30 second schedule)

**Event Format**:
```json
{
  "source": "aws.events",
  "detail-type": "Scheduled Event",
  ...
}
```

## Lambda Handler Routing Logic

The `lambda_handler()` function routes invocations in this priority order:

```python
def lambda_handler(event, context):
    # 1. Worker pattern (async background execution)
    if event.get("worker"):
        execute_recovery_plan_worker(event)
        return {"statusCode": 200, "body": "Worker completed"}
    
    # 2. Action-based invocation (Step Functions)
    if event.get("action"):
        if action == "start_wave_recovery":
            return start_wave_recovery(state, wave_number)
        else:
            return error response
    
    # 3. Operation-based invocation (EventBridge + direct)
    if event.get("operation"):
        return handle_operation(event, context)
    
    # 4. EventBridge scheduled trigger
    if event.get("source") == "aws.events":
        return handle_find_operation(event, context)
    
    # 5. API Gateway invocation (default)
    # Route based on httpMethod + path
    ...
```

## Gap Analysis: Missing Direct Invocation Support

### Current State

The execution-handler **partially supports** direct invocation through:
- ✅ Operation-based pattern (`operation` field)
- ✅ Two operations already support direct invocation:
  - `start_execution` - Start recovery execution
  - `get_execution_details` - Get execution details

### Missing Standardization

❌ **No standardized `handle_direct_invocation()` function** like query-handler and data-management-handler

❌ **Inconsistent operation routing** - operations are handled in `handle_operation()` but not unified with a direct invocation interface

❌ **Missing operations** for complete direct invocation coverage:
- `cancel_execution` - Cancel running execution
- `pause_execution` - Pause execution at wave boundary
- `resume_execution` - Resume paused execution
- `terminate_instances` - Terminate recovery instances
- `get_recovery_instances` - Get recovery instance details
- `list_executions` - List all executions

### Recommended Approach

To standardize execution-handler with query-handler and data-management-handler:

1. **Create `handle_direct_invocation()` function** that routes operations to handlers
2. **Update `lambda_handler()` to detect direct invocation** via `operation` field
3. **Add missing operations** to `handle_direct_invocation()`:
   - `start_execution` (already exists in `handle_operation`)
   - `cancel_execution` (new)
   - `pause_execution` (new)
   - `resume_execution` (new)
   - `terminate_instances` (new)
   - `get_recovery_instances` (new)
   - `list_executions` (new)
   - `get_execution` (alias for `get_execution_details`)
4. **Maintain backward compatibility** with existing action-based and operation-based patterns
5. **Delegate to query-handler** for read-only operations (`list_executions`, `get_execution`)

## Operation Mapping

### Execution Lifecycle Operations

| Operation | Current Handler | Direct Invocation Support | Notes |
|-----------|----------------|---------------------------|-------|
| `start_execution` | `execute_recovery_plan()` | ✅ Exists in `handle_operation` | Already supports direct invocation |
| `cancel_execution` | `cancel_execution()` | ❌ Missing | Need to add to `handle_direct_invocation()` |
| `pause_execution` | `pause_execution()` | ❌ Missing | Need to add to `handle_direct_invocation()` |
| `resume_execution` | `resume_execution()` | ❌ Missing | Need to add to `handle_direct_invocation()` |
| `terminate_instances` | `terminate_recovery_instances()` | ❌ Missing | Need to add to `handle_direct_invocation()` |
| `get_recovery_instances` | `get_recovery_instances()` | ❌ Missing | Need to add to `handle_direct_invocation()` |

### Query Operations (Delegate to Query Handler)

| Operation | Current Handler | Direct Invocation Support | Notes |
|-----------|----------------|---------------------------|-------|
| `list_executions` | `list_executions()` | ❌ Missing | Should delegate to query-handler |
| `get_execution` | `get_execution_details()` | ✅ Exists as `get_execution_details` | Should also support `get_execution` alias |

### Background Operations (Keep Existing Pattern)

| Operation | Current Handler | Direct Invocation Support | Notes |
|-----------|----------------|---------------------------|-------|
| `find` | `handle_find_operation()` | ✅ Exists | EventBridge scheduled polling |
| `poll` | `handle_poll_operation()` | ✅ Exists | Self-invocation for status updates |
| `finalize` | `handle_finalize_operation()` | ✅ Exists | Step Functions callback |

## Backward Compatibility Requirements

### Must Preserve

1. **Action-based invocations** from Step Functions:
   - `action="start_wave_recovery"` must continue working
   - Returns modified `state` dict directly

2. **Operation-based invocations** from EventBridge:
   - `operation="find"` for scheduled polling
   - `operation="poll"` for self-invocation
   - `operation="finalize"` from Step Functions

3. **API Gateway invocations**:
   - All HTTP endpoints must continue working
   - Cognito authentication must continue working
   - Response format must remain unchanged

### Implementation Strategy

```python
def lambda_handler(event, context):
    # 1. Worker pattern (unchanged)
    if event.get("worker"):
        execute_recovery_plan_worker(event)
        return {"statusCode": 200, "body": "Worker completed"}
    
    # 2. Action-based invocation (unchanged)
    if event.get("action"):
        return handle_action_invocation(event)
    
    # 3. Direct invocation (NEW - standardized)
    if event.get("operation") and not event.get("httpMethod"):
        return handle_direct_invocation(event, context)
    
    # 4. EventBridge scheduled trigger (unchanged)
    if event.get("source") == "aws.events":
        return handle_find_operation(event, context)
    
    # 5. API Gateway invocation (unchanged)
    return handle_api_gateway_request(event, context)
```

## Conclusion

The execution-handler has **partial direct invocation support** through the operation-based pattern, but lacks:

1. **Standardized `handle_direct_invocation()` function** for consistency with other handlers
2. **Complete operation coverage** for all execution lifecycle operations
3. **Unified routing logic** that clearly separates direct invocation from other patterns

The recommended approach is to:
- Create `handle_direct_invocation()` function
- Add missing operations (cancel, pause, resume, terminate, get_recovery_instances)
- Delegate query operations to query-handler
- Maintain backward compatibility with existing action-based and operation-based patterns
