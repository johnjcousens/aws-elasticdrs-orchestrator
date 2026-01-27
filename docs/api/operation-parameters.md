# Execution Handler Operation Parameters

API reference for execution-handler Lambda operation-based invocation.

## Overview

The execution-handler supports operation-based routing for internal system operations. EventBridge and Step Functions use this pattern for execution lifecycle management.

## Operation Types

### find

**Purpose**: Discover active executions that need polling  
**Trigger**: EventBridge (1-minute schedule)  
**Behavior**: Queries DynamoDB for POLLING/CANCELLING executions, invokes poll for each

**Parameters**:
```json
{
  "operation": "find"
}
```

**Returns**:
```json
{
  "statusCode": 200,
  "executionsFound": 3,
  "executionsPolled": 3,
  "results": [
    {"executionId": "uuid", "success": true, "status": "POLLING"}
  ]
}
```

**Usage**:
```bash
aws lambda invoke \
  --function-name execution-handler \
  --payload '{"operation":"find"}' \
  response.json
```

---

### poll

**Purpose**: Update wave status and enrich server data  
**Trigger**: Self-invoked by find operation  
**Behavior**: Queries DRS job status, enriches with EC2 data, updates DynamoDB

**Critical**: Never changes execution status or calls finalize

**Parameters**:
```json
{
  "operation": "poll",
  "executionId": "uuid",
  "planId": "uuid"
}
```

**Returns**:
```json
{
  "statusCode": 200,
  "executionId": "uuid",
  "status": "POLLING",
  "allWavesComplete": false,
  "waves": [
    {
      "waveNumber": 0,
      "status": "COMPLETED",
      "serverStatuses": [
        {
          "sourceServerId": "s-123",
          "launchStatus": "LAUNCHED",
          "instanceId": "i-abc",
          "privateIp": "10.0.1.50",
          "instanceType": "t3.medium"
        }
      ]
    }
  ]
}
```

**Data Enrichment**:
- DRS API: sourceServerId, launchStatus, recoveryInstanceId
- EC2 API: instanceId, privateIp, hostname, instanceType
- Normalized to camelCase

**Usage**:
```bash
aws lambda invoke \
  --function-name execution-handler \
  --payload '{"operation":"poll","executionId":"uuid","planId":"uuid"}' \
  response.json
```

---

### finalize

**Purpose**: Mark execution complete after all waves finish  
**Trigger**: Step Functions only  
**Behavior**: Validates all waves complete, updates status to COMPLETED

**Critical**: Idempotent, uses conditional writes

**Parameters**:
```json
{
  "operation": "finalize",
  "executionId": "uuid",
  "planId": "uuid"
}
```

**Returns**:
```json
{
  "statusCode": 200,
  "executionId": "uuid",
  "status": "COMPLETED",
  "totalWaves": 3,
  "alreadyFinalized": false
}
```

**Validation**: Returns 400 if any wave status is not COMPLETED

**Usage**:
```bash
aws lambda invoke \
  --function-name execution-handler \
  --payload '{"operation":"finalize","executionId":"uuid","planId":"uuid"}' \
  response.json
```

---

### pause

**Purpose**: Pause execution between waves  
**Trigger**: API Gateway or Step Functions  
**Behavior**: Changes execution status to PAUSED

**Parameters**:
```json
{
  "operation": "pause",
  "executionId": "uuid",
  "planId": "uuid"
}
```

**Returns**:
```json
{
  "statusCode": 200,
  "executionId": "uuid",
  "status": "PAUSED"
}
```

---

### resume

**Purpose**: Resume paused execution  
**Trigger**: API Gateway  
**Behavior**: Changes status to POLLING, resumes Step Functions

**Parameters**:
```json
{
  "operation": "resume",
  "executionId": "uuid",
  "planId": "uuid"
}
```

**Returns**:
```json
{
  "statusCode": 200,
  "executionId": "uuid",
  "status": "POLLING"
}
```

## Architecture Pattern

```
EventBridge (1-minute schedule)
  ↓
execution-handler (operation: "find")
  ↓
Query DynamoDB (status: POLLING/CANCELLING)
  ↓
For each execution:
  execution-handler (operation: "poll")
    ↓
  Query DRS job status
    ↓
  Query EC2 instance details
    ↓
  Update DynamoDB (waves, serverStatuses)
    ↓
  Return allWavesComplete flag
    ↓
Step Functions checks flag
  ↓
If all complete:
  execution-handler (operation: "finalize")
```

## Error Handling

All operations return standard error responses:

```json
{
  "statusCode": 400|404|500,
  "error": "ERROR_CODE",
  "message": "Human-readable description"
}
```

**Common Errors**:
- 400: Missing parameters, invalid state
- 404: Execution not found
- 500: Internal error (DRS/EC2 API failures)

## Related Documentation

- [Multi-Wave Execution Fix Requirements](../../.kiro/specs/multi-wave-execution-fix/requirements.md)
- [Multi-Wave Execution Fix Design](../../.kiro/specs/multi-wave-execution-fix/design.md)
- [DRS Utils](../../lambda/shared/drs_utils.py)
