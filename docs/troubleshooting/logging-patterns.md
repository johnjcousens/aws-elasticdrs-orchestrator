# Logging Patterns and Troubleshooting

CloudWatch Logs patterns for DR Orchestration execution-handler.

## Log Structure

**Format**: Structured JSON with contextual fields  
**Location**: `/aws/lambda/{EnvironmentName}-execution-handler`  
**Retention**: 30 days

## Operation Patterns

### Find Operation (EventBridge Trigger)

**Success Pattern**:
```
Finding executions that need polling
Found 3 executions needing polling
✅ Polling complete for {executionId} - waves updated, execution status unchanged
```

**No Active Executions**:
```
Finding executions that need polling
Found 0 executions needing polling
```

**Query**:
```
fields @timestamp, @message
| filter @message like /Finding executions/
| sort @timestamp desc
| limit 20
```

---

### Poll Operation (Wave Status Update)

**Success Pattern**:
```
Polling execution {executionId}
[DRS API] Querying job status for {jobId}
[EC2 API] Enriching {count} servers with instance details
✅ Polling complete for {executionId} - waves updated, execution status unchanged
```

**Wave Complete**:
```
Polling execution {executionId}
Wave {waveNumber} status: COMPLETED
✅ Polling complete for {executionId} - waves updated, execution status unchanged
```

**All Waves Complete**:
```
Polling execution {executionId}
All waves complete - allWavesComplete=true
✅ Polling complete for {executionId} - waves updated, execution status unchanged
```

**Query**:
```
fields @timestamp, @message
| filter @message like /Polling execution/
| sort @timestamp desc
| limit 50
```

---

### Finalize Operation (Execution Complete)

**Success Pattern**:
```
Finalizing execution {executionId}
All waves validated as COMPLETED
Execution {executionId} marked as COMPLETED
```

**Already Finalized**:
```
Finalizing execution {executionId}
Execution already finalized - idempotent operation
```

**Validation Failure**:
```
Finalizing execution {executionId}
❌ Cannot finalize: wave {waveNumber} status is {status}
```

**Query**:
```
fields @timestamp, @message
| filter @message like /Finalizing execution/
| sort @timestamp desc
| limit 20
```

---

## Error Patterns

### DRS API Errors

**Throttling**:
```
❌ DRS API throttled - will retry
ThrottlingException: Rate exceeded
```

**Job Not Found**:
```
❌ No DRS job found for {jobId}
Wave {waveNumber} has no jobId
```

**Query**:
```
fields @timestamp, @message
| filter @message like /DRS API/ and @message like /❌/
| sort @timestamp desc
| limit 50
```

---

### EC2 API Errors

**Instance Not Found**:
```
[EC2 API] Some instances not found yet - returning partial results
InvalidInstanceID.NotFound: {instanceId}
```

**Throttling**:
```
❌ EC2 API throttled
RequestLimitExceeded
```

**Query**:
```
fields @timestamp, @message
| filter @message like /EC2 API/ and (@message like /❌/ or @message like /not found/)
| sort @timestamp desc
| limit 50
```

---

### DynamoDB Errors

**Conditional Check Failed**:
```
❌ Conditional check failed - execution already finalized
ConditionalCheckFailedException
```

**Item Not Found**:
```
❌ Execution not found: {executionId}
```

**Query**:
```
fields @timestamp, @message
| filter @message like /DynamoDB/ or @message like /ConditionalCheckFailed/
| sort @timestamp desc
| limit 50
```

---

## Performance Monitoring

### Polling Duration

**Query**:
```
fields @timestamp, @duration
| filter @message like /Polling complete/
| stats avg(@duration), max(@duration), p95(@duration) by bin(5m)
```

**Thresholds**:
- Normal: < 2 seconds
- Warning: 2-4 seconds
- Critical: > 4 seconds

---

### API Call Counts

**Query**:
```
fields @timestamp
| filter @message like /DRS API/ or @message like /EC2 API/
| stats count() by bin(5m)
```

**Expected**:
- DRS API: 1-5 calls per poll
- EC2 API: 1-2 calls per poll (batch queries)

---

### Enrichment Success Rate

**Query**:
```
fields @timestamp, @message
| filter @message like /Enriching/ or @message like /enriched/
| stats count() by bin(5m)
```

---

## Troubleshooting Scenarios

### Scenario 1: Execution Stuck in POLLING

**Symptoms**:
- Execution status remains POLLING for > 30 minutes
- No wave status updates in DynamoDB
- No polling logs in CloudWatch

**Investigation**:
```
fields @timestamp, @message
| filter @message like /{executionId}/
| sort @timestamp desc
| limit 100
```

**Common Causes**:
1. EventBridge rule disabled
2. Lambda function errors
3. DRS job stuck in IN_PROGRESS

**Resolution**:
1. Check EventBridge rule status
2. Review Lambda error logs
3. Query DRS job status directly

---

### Scenario 2: Premature Finalization

**Symptoms**:
- Execution marked COMPLETED with incomplete waves
- Step Functions still RUNNING
- Missing waves in DynamoDB

**Investigation**:
```
fields @timestamp, @message
| filter @message like /Finalizing/ and @message like /{executionId}/
| sort @timestamp desc
```

**Expected**: Should NOT see finalization logs during polling

**Resolution**: This bug was fixed - polling never calls finalize

---

### Scenario 3: Missing Server Data

**Symptoms**:
- serverStatuses field empty or incomplete
- No EC2 instance details
- Missing privateIp, instanceType fields

**Investigation**:
```
fields @timestamp, @message
| filter @message like /Enriching/ and @message like /{executionId}/
| sort @timestamp desc
```

**Common Causes**:
1. EC2 instances not yet launched
2. EC2 API throttling
3. Invalid instance IDs

**Resolution**:
1. Wait for DRS launch to complete
2. Check EC2 API error logs
3. Verify DRS job status

---

### Scenario 4: High Polling Duration

**Symptoms**:
- Polling takes > 5 seconds
- Lambda timeout warnings
- Incomplete wave updates

**Investigation**:
```
fields @timestamp, @duration, @message
| filter @message like /Polling execution/
| sort @duration desc
| limit 20
```

**Common Causes**:
1. Large wave sizes (> 50 servers)
2. EC2 API latency
3. DynamoDB throttling

**Resolution**:
1. Increase Lambda timeout (300s → 600s)
2. Implement EC2 result caching
3. Increase DynamoDB capacity

---

## Useful Queries

### Execution Timeline

```
fields @timestamp, @message
| filter @message like /{executionId}/
| sort @timestamp asc
```

### Error Summary (Last Hour)

```
fields @timestamp, @message
| filter @message like /❌/ or @message like /Error/
| stats count() by @message
| sort count desc
```

### Polling Performance (Last 24 Hours)

```
fields @timestamp, @duration
| filter @message like /Polling complete/
| stats avg(@duration) as avg_duration, max(@duration) as max_duration, p95(@duration) as p95_duration by bin(1h)
```

### API Call Distribution

```
fields @timestamp
| filter @message like /API/
| parse @message /\[(?<api>\w+ API)\]/
| stats count() by api, bin(5m)
```

## Related Documentation

- [Lambda Configuration](../deployment/lambda-configuration.md)
- [Operation Parameters](../api/operation-parameters.md)
- [Multi-Wave Bug Analysis](../../../.kiro/specs/missing-function-migration/MULTI_WAVE_BUG_ANALYSIS.md)
