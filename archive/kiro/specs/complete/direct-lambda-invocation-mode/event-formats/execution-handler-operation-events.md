# Execution Handler Operation-Based Event Formats

**Handler**: `lambda/execution-handler/index.py`  
**Invocation Pattern**: Operation-Based (EventBridge, Direct Invocation)  
**Purpose**: Background polling, lifecycle management, and direct execution control

## Overview

The execution-handler supports **operation-based invocation** for:
1. **EventBridge Scheduled Polling**: Periodic status updates (30s schedule)
2. **Self-Invocation**: Async polling of DRS job status
3. **Direct Invocation**: Execution lifecycle operations (start, pause, resume, etc.)

## Detection Logic

Operation-based invocation is detected when the event contains an `operation` field:

```python
if event.get("operation"):
    # Route to operation-based handler
    return handle_operation(event, context)
```

## Event Structure

```json
{
  "operation": "operation_name",
  "executionId": "uuid",
  "planId": "uuid",
  "queryParams": {...}
}
```

**Required Fields**:
- `operation` (string): Operation name

**Optional Fields**:
- `executionId` (string): Execution ID (required for most operations)
- `planId` (string): Recovery plan ID (required for some operations)
- `queryParams` (object): Additional parameters

## Supported Operations (7 total)

### 1. Background Polling Operations

#### 1.1 find

Find active executions that need status polling.

**Invoked By**: EventBridge (30 second schedule)

**Event**:
```json
{
  "operation": "find"
}
```

**Parameters**: None

**Response**:
```json
{
  "statusCode": 200,
  "executionsFound": 3,
  "executionsPolled": 3,
  "results": [
    {
      "executionId": "exec-123",
      "planId": "rp-456",
      "status": "POLLING_INITIATED"
    }
  ]
}
```

**Behavior**:
1. Queries DynamoDB for executions with status `RUNNING`
2. For each execution, self-invokes with `operation=poll`
3. Returns summary of polling operations initiated

**EventBridge Rule**:
```json
{
  "source": ["aws.events"],
  "detail-type": ["Scheduled Event"],
  "resources": ["arn:aws:events:us-east-1:123456789012:rule/drs-execution-polling"]
}
```

---

#### 1.2 poll

Poll DRS job status and update execution record.

**Invoked By**: Self-invocation from `find` operation

**Event**:
```json
{
  "operation": "poll",
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901"
}
```

**Parameters**:
- `executionId` (string, required): Execution ID to poll
- `planId` (string, required): Recovery plan ID

**Response**:
```json
{
  "statusCode": 200,
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "currentWave": 1,
  "waveStatus": "IN_PROGRESS",
  "drsJobStatus": "RUNNING",
  "serversLaunched": 5,
  "serversCompleted": 3,
  "serversFailed": 0,
  "lastPolled": "2025-01-31T15:35:00Z"
}
```

**Behavior**:
1. Retrieves execution record from DynamoDB
2. Gets current wave's DRS job ID
3. Calls DRS `DescribeJobs` API to get job status
4. Updates execution record with latest status
5. If wave complete, triggers next wave or marks execution complete

**DRS Job Status Mapping**:
- `PENDING` → `IN_PROGRESS`
- `STARTED` → `IN_PROGRESS`
- `COMPLETED` → `COMPLETED`
- `FAILED` → `FAILED`

---

### 2. Lifecycle Management Operations

#### 2.1 finalize

Mark execution as COMPLETED after all waves finish.

**Invoked By**: Step Functions (final state)

**Event**:
```json
{
  "operation": "finalize",
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901"
}
```

**Parameters**:
- `executionId` (string, required): Execution ID
- `planId` (string, required): Recovery plan ID

**Response**:
```json
{
  "statusCode": 200,
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "COMPLETED",
  "totalWaves": 3,
  "completedWaves": 3,
  "totalServers": 25,
  "successfulServers": 25,
  "failedServers": 0,
  "startTime": "2025-01-31T15:30:00Z",
  "endTime": "2025-01-31T16:15:00Z",
  "duration": "45m"
}
```

**Behavior**:
1. Updates execution status to `COMPLETED`
2. Records end time
3. Calculates execution duration
4. Sends SNS notification (if configured)
5. Returns final execution summary

---

#### 2.2 pause

Pause execution at next wave boundary.

**Invoked By**: Direct invocation (API Gateway or CLI)

**Event**:
```json
{
  "operation": "pause",
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901"
}
```

**Parameters**:
- `executionId` (string, required): Execution ID
- `planId` (string, required): Recovery plan ID

**Response**:
```json
{
  "statusCode": 200,
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PAUSED",
  "currentWave": 1,
  "nextWave": 2,
  "pausedAt": "2025-01-31T15:45:00Z",
  "message": "Execution will pause after wave 1 completes"
}
```

**Behavior**:
1. Validates execution is in `RUNNING` state
2. Sets pause flag in execution record
3. Execution will pause after current wave completes
4. Step Functions stores task token for resume

**AWS CLI**:
```bash
aws lambda invoke \
  --function-name execution-handler \
  --payload '{
    "operation": "pause",
    "executionId": "exec-123",
    "planId": "rp-456"
  }' \
  response.json
```

---

#### 2.3 resume

Resume paused execution.

**Invoked By**: Direct invocation (API Gateway or CLI)

**Event**:
```json
{
  "operation": "resume",
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901"
}
```

**Parameters**:
- `executionId` (string, required): Execution ID
- `planId` (string, required): Recovery plan ID

**Response**:
```json
{
  "statusCode": 200,
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "RUNNING",
  "currentWave": 2,
  "resumedAt": "2025-01-31T16:00:00Z",
  "message": "Execution resumed, starting wave 2"
}
```

**Behavior**:
1. Validates execution is in `PAUSED` state
2. Retrieves Step Functions task token
3. Calls `SendTaskSuccess` to resume Step Functions
4. Updates execution status to `RUNNING`
5. Step Functions continues with next wave

**AWS CLI**:
```bash
aws lambda invoke \
  --function-name execution-handler \
  --payload '{
    "operation": "resume",
    "executionId": "exec-123",
    "planId": "rp-456"
  }' \
  response.json
```

---

### 3. Direct Invocation Operations

#### 3.1 start_execution

Start a new recovery plan execution.

**Invoked By**: Direct invocation (bypasses API Gateway)

**Event**:
```json
{
  "operation": "start_execution",
  "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "executionType": "DRILL",
  "initiatedBy": "user@example.com",
  "accountContext": {
    "accountId": "123456789012",
    "region": "us-east-1",
    "roleName": "DRSOrchestrationRole"
  }
}
```

**Parameters**:
- `planId` (string, required): Recovery plan ID
- `executionType` (string, required): `DRILL` or `RECOVERY`
- `initiatedBy` (string, required): User identifier
- `accountContext` (object, optional): Cross-account context

**Response**:
```json
{
  "statusCode": 200,
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "status": "RUNNING",
  "executionType": "DRILL",
  "stepFunctionArn": "arn:aws:states:us-east-1:123456789012:execution:dr-orchestration:exec-123",
  "startTime": "2025-01-31T15:30:00Z",
  "totalWaves": 3,
  "totalServers": 25
}
```

**Behavior**:
1. Validates recovery plan exists
2. Checks for conflicting active executions
3. Creates execution record in DynamoDB
4. Starts Step Functions state machine
5. Returns execution details

**AWS CLI**:
```bash
aws lambda invoke \
  --function-name execution-handler \
  --payload '{
    "operation": "start_execution",
    "planId": "rp-456",
    "executionType": "DRILL",
    "initiatedBy": "admin@example.com"
  }' \
  response.json
```

**Python boto3**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='execution-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "start_execution",
        "planId": "rp-456",
        "executionType": "DRILL",
        "initiatedBy": "admin@example.com",
        "accountContext": {
            "accountId": "123456789012",
            "region": "us-east-1",
            "roleName": "DRSOrchestrationRole"
        }
    })
)

result = json.loads(response['Payload'].read())
print(f"Started execution: {result['executionId']}")
print(f"Step Functions ARN: {result['stepFunctionArn']}")
```

---

#### 3.2 get_execution_details

Get detailed execution information.

**Invoked By**: Direct invocation (bypasses API Gateway)

**Event**:
```json
{
  "operation": "get_execution_details",
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "queryParams": {
    "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901"
  }
}
```

**Parameters**:
- `executionId` (string, required): Execution ID
- `queryParams.planId` (string, optional): Recovery plan ID

**Response**:
```json
{
  "statusCode": 200,
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "planName": "Production DR Plan",
  "status": "RUNNING",
  "executionType": "DRILL",
  "initiatedBy": "user@example.com",
  "startTime": "2025-01-31T15:30:00Z",
  "currentWave": 2,
  "totalWaves": 3,
  "waveStatuses": [
    {
      "waveNumber": 1,
      "waveName": "Database Tier",
      "status": "COMPLETED",
      "drsJobId": "drsjob-wave1",
      "serversLaunched": 5,
      "serversCompleted": 5,
      "serversFailed": 0,
      "startTime": "2025-01-31T15:30:00Z",
      "endTime": "2025-01-31T15:40:00Z"
    },
    {
      "waveNumber": 2,
      "waveName": "Application Tier",
      "status": "IN_PROGRESS",
      "drsJobId": "drsjob-wave2",
      "serversLaunched": 10,
      "serversCompleted": 7,
      "serversFailed": 0,
      "startTime": "2025-01-31T15:45:00Z"
    }
  ],
  "serverExecutions": [
    {
      "serverId": "s-abc",
      "hostname": "db-primary",
      "waveNumber": 1,
      "status": "COMPLETED",
      "recoveryInstanceId": "i-0123456789abcdef0",
      "launchTime": "2025-01-31T15:32:00Z"
    }
  ]
}
```

**AWS CLI**:
```bash
aws lambda invoke \
  --function-name execution-handler \
  --payload '{
    "operation": "get_execution_details",
    "executionId": "exec-123",
    "queryParams": {"planId": "rp-456"}
  }' \
  response.json && cat response.json | jq .
```

---

## EventBridge Integration

### Scheduled Polling Rule

**Rule Configuration**:
```json
{
  "Name": "drs-execution-polling",
  "Description": "Poll active DRS executions every 30 seconds",
  "ScheduleExpression": "rate(30 seconds)",
  "State": "ENABLED",
  "Targets": [
    {
      "Arn": "arn:aws:lambda:us-east-1:123456789012:function:execution-handler",
      "Input": "{\"operation\": \"find\"}"
    }
  ]
}
```

**Event Payload**:
```json
{
  "version": "0",
  "id": "12345678-1234-1234-1234-123456789012",
  "detail-type": "Scheduled Event",
  "source": "aws.events",
  "account": "123456789012",
  "time": "2025-01-31T15:30:00Z",
  "region": "us-east-1",
  "resources": [
    "arn:aws:events:us-east-1:123456789012:rule/drs-execution-polling"
  ],
  "detail": {}
}
```

**Handler Detection**:
```python
if event.get("source") == "aws.events":
    # EventBridge scheduled event
    return handle_find_operation(event, context)
```

---

## Self-Invocation Pattern

### Find → Poll Flow

```
┌─────────────────────────────────────────────────────────────┐
│              EventBridge (30s schedule)                      │
│              {"operation": "find"}                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         Lambda: execution-handler (find operation)           │
├─────────────────────────────────────────────────────────────┤
│ 1. Query DynamoDB for RUNNING executions                    │
│ 2. For each execution, self-invoke with poll operation      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├──────────────┬──────────────┐
                            ▼              ▼              ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Lambda: poll     │ │ Lambda: poll     │ │ Lambda: poll     │
│ exec-123         │ │ exec-456         │ │ exec-789         │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│ 1. Get exec      │ │ 1. Get exec      │ │ 1. Get exec      │
│ 2. Call DRS API  │ │ 2. Call DRS API  │ │ 2. Call DRS API  │
│ 3. Update status │ │ 3. Update status │ │ 3. Update status │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

### Self-Invocation Code

```python
# In find operation
lambda_client = boto3.client('lambda')

for execution in active_executions:
    lambda_client.invoke(
        FunctionName=context.function_name,
        InvocationType='Event',  # Async invocation
        Payload=json.dumps({
            "operation": "poll",
            "executionId": execution['executionId'],
            "planId": execution['planId']
        })
    )
```

---

## Error Responses

### Unknown Operation

**Event**:
```json
{
  "operation": "invalid_operation"
}
```

**Response**:
```json
{
  "statusCode": 400,
  "error": "UNKNOWN_OPERATION",
  "message": "Unknown operation: invalid_operation",
  "supportedOperations": [
    "find",
    "poll",
    "finalize",
    "pause",
    "resume",
    "start_execution",
    "get_execution_details"
  ]
}
```

### Missing Parameters

**Event**:
```json
{
  "operation": "poll"
}
```

**Response**:
```json
{
  "statusCode": 400,
  "error": "MISSING_PARAMETERS",
  "message": "Missing required parameters: executionId, planId"
}
```

### Execution Not Found

**Event**:
```json
{
  "operation": "get_execution_details",
  "executionId": "exec-nonexistent"
}
```

**Response**:
```json
{
  "statusCode": 404,
  "error": "EXECUTION_NOT_FOUND",
  "message": "Execution not found: exec-nonexistent"
}
```

### Invalid State Transition

**Event**:
```json
{
  "operation": "resume",
  "executionId": "exec-123",
  "planId": "rp-456"
}
```

**Response** (if execution not paused):
```json
{
  "statusCode": 400,
  "error": "INVALID_STATE",
  "message": "Cannot resume execution in RUNNING state. Expected PAUSED state.",
  "currentStatus": "RUNNING"
}
```

---

## Complete Python boto3 Examples

### Start Execution and Poll Status
```python
import boto3
import json
import time

lambda_client = boto3.client('lambda')

# Start execution
response = lambda_client.invoke(
    FunctionName='execution-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "start_execution",
        "planId": "rp-456",
        "executionType": "DRILL",
        "initiatedBy": "admin@example.com"
    })
)

result = json.loads(response['Payload'].read())
execution_id = result['executionId']
print(f"Started execution: {execution_id}")

# Poll status every 30 seconds
while True:
    response = lambda_client.invoke(
        FunctionName='execution-handler',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            "operation": "get_execution_details",
            "executionId": execution_id,
            "queryParams": {"planId": "rp-456"}
        })
    )
    
    status = json.loads(response['Payload'].read())
    print(f"Status: {status['status']}, Wave: {status['currentWave']}/{status['totalWaves']}")
    
    if status['status'] in ['COMPLETED', 'FAILED', 'CANCELLED']:
        break
    
    time.sleep(30)

print(f"Execution finished: {status['status']}")
```

### Pause and Resume Execution
```python
# Pause execution
response = lambda_client.invoke(
    FunctionName='execution-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "pause",
        "executionId": "exec-123",
        "planId": "rp-456"
    })
)

result = json.loads(response['Payload'].read())
print(f"Paused: {result['message']}")

# Wait for manual approval
input("Press Enter to resume execution...")

# Resume execution
response = lambda_client.invoke(
    FunctionName='execution-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "resume",
        "executionId": "exec-123",
        "planId": "rp-456"
    })
)

result = json.loads(response['Payload'].read())
print(f"Resumed: {result['message']}")
```
