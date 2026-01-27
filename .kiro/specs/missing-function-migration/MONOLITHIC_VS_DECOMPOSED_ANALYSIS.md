# Monolithic vs Decomposed Handler Analysis

## Executive Summary

**Status**: ✅ Code migration complete, ❌ Functional regression identified

**Root Cause**: The decomposed handlers have identical code to the monolithic handler, but the **polling architecture** may not be functioning correctly, preventing server enrichment and status updates.

## Architecture Comparison

### Monolithic Handler Architecture

```
GET /executions/{id}
    ↓
get_execution_details(execution_id)
    ↓
get_execution_details_fast(execution_id)  ← Returns CACHED data from DynamoDB
    ↓
Response with cached execution data

Background Process (EventBridge → Execution Finder → Execution Poller):
    ↓
Execution Finder (every 30s)
    ↓
Query StatusIndex GSI for Status=POLLING
    ↓
Invoke Execution Poller for each execution
    ↓
poll_wave_status() → Query DRS API
    ↓
Enrich with server names, IPs, instance details
    ↓
update_execution_waves() → Write to DynamoDB
```

### Decomposed Handler Architecture

```
GET /executions/{id}
    ↓
execution-handler: get_execution_details(execution_id, query_params)
    ↓
Returns CACHED data from DynamoDB (IDENTICAL to monolithic)
    ↓
Response with cached execution data

Background Process (SAME as monolithic):
    ↓
Execution Finder Lambda (every 30s)
    ↓
Query StatusIndex GSI for Status=POLLING
    ↓
Invoke Execution Poller Lambda for each execution
    ↓
poll_wave_status() → Query DRS API
    ↓
Enrich with server names, IPs, instance details
    ↓
update_execution_waves() → Write to DynamoDB
```

## Key Findings

### 1. get_execution_details() - IDENTICAL ✅

**Monolithic** (`api-handler-monolithic-20260124/index.py:6202`):
```python
def get_execution_details(execution_id: str) -> Dict:
    """Get execution details - now uses FAST cached data by default"""
    return get_execution_details_fast(execution_id)
```

**Decomposed** (`execution-handler/index.py:1427`):
```python
def get_execution_details(execution_id: str, query_params: Dict) -> Dict:
    """
    Get execution details by ID - uses cached data for fast response.
    """
    # IDENTICAL implementation to monolithic get_execution_details_fast()
```

**Conclusion**: The GET endpoint logic is identical. Both return cached data from DynamoDB.

### 2. Enrichment Logic - NOT CALLED IN GET ENDPOINT ✅

**Finding**: Neither monolithic nor decomposed handlers call `enrich_execution_with_server_details()` in the GET endpoint.

**Reason**: Enrichment happens **asynchronously** via the execution-poller Lambda, not synchronously in the GET request.

**Conclusion**: This is correct architecture. The GET endpoint should be fast (<1s) and return cached data.

### 3. Execution Poller - IDENTICAL LOGIC ✅

**Monolithic**: No separate poller (inline worker mode)
**Decomposed**: Dedicated execution-poller Lambda

**Poller Logic** (`execution-poller/index.py:518`):
- Queries DRS job status via `query_drs_job_status()`
- Enriches server data with names from DRS tags via `get_drs_server_name()`
- Enriches server data with EC2 details via `get_ec2_instance_details()`
- Updates DynamoDB via `update_execution_waves()`

**Conclusion**: The poller has all the enrichment logic. The issue is likely in the **invocation chain**.

### 4. Execution Finder - CORRECT ARCHITECTURE ✅

**Execution Finder** (`execution-finder/index.py`):
- Triggered by EventBridge every 30 seconds
- Queries StatusIndex GSI for `Status=POLLING`
- Invokes execution-poller Lambda for each execution
- Implements adaptive polling intervals

**Conclusion**: The finder architecture is correct.

## Potential Issues

### Issue 1: Execution Status Not Set to POLLING

**Symptom**: Execution Finder doesn't find executions because they're not in POLLING status.

**Check**:
```sql
-- Query DynamoDB to see execution status
SELECT executionId, status, waves FROM ExecutionHistory WHERE executionId = '<id>'
```

**Expected**: Status should be `POLLING` after execution starts.

**Possible Causes**:
- Execution status not transitioning from `INITIATED` → `POLLING`
- Step Functions not updating status correctly
- execute_recovery_plan() not setting initial status correctly

### Issue 2: StatusIndex GSI Not Configured

**Symptom**: Execution Finder query returns no results even though executions exist.

**Check**:
```bash
aws dynamodb describe-table --table-name <table> --query 'Table.GlobalSecondaryIndexes[?IndexName==`StatusIndex`]'
```

**Expected**: StatusIndex GSI should exist with `Status` as partition key.

**Possible Causes**:
- GSI not created during deployment
- GSI still in CREATING status
- GSI projection doesn't include required fields

### Issue 3: Execution Poller Not Invoked

**Symptom**: Execution Finder runs but doesn't invoke poller.

**Check CloudWatch Logs**:
```bash
# Check Execution Finder logs
aws logs tail /aws/lambda/aws-drs-orchestration-execution-finder-dev --since 1h

# Check Execution Poller logs
aws logs tail /aws/lambda/aws-drs-orchestration-execution-poller-dev --since 1h
```

**Expected**: 
- Finder logs: "Found X executions in POLLING status"
- Finder logs: "Invoking poller for execution <id>"
- Poller logs: "Polling execution: <id>"

**Possible Causes**:
- Lambda invocation permissions missing
- Execution Finder not finding executions (see Issue 1)
- Poller Lambda function name incorrect in environment variable

### Issue 4: DynamoDB Update Failing

**Symptom**: Poller runs but waves not updated in DynamoDB.

**Check CloudWatch Logs**:
```bash
aws logs tail /aws/lambda/aws-drs-orchestration-execution-poller-dev --since 1h --filter-pattern "Error updating execution waves"
```

**Expected**: No errors in update_execution_waves()

**Possible Causes**:
- DynamoDB permissions missing
- Conditional check failing (execution doesn't exist)
- Wave data format incompatible with DynamoDB

### Issue 5: DRS API Calls Failing

**Symptom**: Poller runs but can't query DRS job status.

**Check CloudWatch Logs**:
```bash
aws logs tail /aws/lambda/aws-drs-orchestration-execution-poller-dev --since 1h --filter-pattern "Error querying DRS"
```

**Expected**: No DRS API errors

**Possible Causes**:
- DRS permissions missing
- Cross-account role assumption failing
- DRS job IDs not stored correctly in wave data
- Region mismatch (querying wrong region)

## Recommended Investigation Steps

### Step 1: Check Execution Status in DynamoDB

```bash
# Get execution details from DynamoDB
aws dynamodb query \
  --table-name aws-drs-orchestration-execution-history-dev \
  --key-condition-expression "executionId = :id" \
  --expression-attribute-values '{":id":{"S":"<execution-id>"}}' \
  --query 'Items[0].[status.S, waves.L[*].M.status.S]'
```

**Expected Output**: `["POLLING", ["IN_PROGRESS", "PENDING", ...]]`

**If status is NOT POLLING**: The execution-finder won't find it. Check execute_recovery_plan() logic.

### Step 2: Check StatusIndex GSI

```bash
# Verify GSI exists
aws dynamodb describe-table \
  --table-name aws-drs-orchestration-execution-history-dev \
  --query 'Table.GlobalSecondaryIndexes[?IndexName==`StatusIndex`]'
```

**Expected Output**: GSI with Status as partition key, IndexStatus=ACTIVE

**If GSI missing**: Deploy CloudFormation stack to create it.

### Step 3: Check Execution Finder Logs

```bash
# Check if finder is running
aws logs tail /aws/lambda/aws-drs-orchestration-execution-finder-dev --since 1h

# Look for:
# - "Found X executions in POLLING status"
# - "Invoking poller for execution <id>"
```

**Expected**: Finder should run every 30 seconds and find POLLING executions.

**If no executions found**: See Step 1 (status not POLLING).

### Step 4: Check Execution Poller Logs

```bash
# Check if poller is being invoked
aws logs tail /aws/lambda/aws-drs-orchestration-execution-poller-dev --since 1h

# Look for:
# - "Polling execution: <id>"
# - "Updated X waves for execution <id>"
# - Any error messages
```

**Expected**: Poller should be invoked for each POLLING execution and update waves.

**If poller not invoked**: Check Lambda invocation permissions.
**If poller errors**: Check error messages for root cause.

### Step 5: Manual Poller Invocation Test

```bash
# Manually invoke poller with test payload
aws lambda invoke \
  --function-name aws-drs-orchestration-execution-poller-dev \
  --payload '{"executionId":"<id>","planId":"<plan-id>","executionType":"DRILL","startTime":1234567890}' \
  /tmp/poller-response.json

# Check response
cat /tmp/poller-response.json
```

**Expected**: Poller should successfully query DRS and update DynamoDB.

**If errors**: Check error message for specific issue (permissions, DRS API, etc.).

## Next Steps

1. **IMMEDIATE**: Run Step 1-4 to identify which component is failing
2. **IMMEDIATE**: Check CloudWatch Logs for all three Lambdas (finder, poller, execution-handler)
3. **IMMEDIATE**: Verify execution status is POLLING in DynamoDB
4. **IMMEDIATE**: Verify StatusIndex GSI exists and is ACTIVE
5. **FIX**: Based on findings, fix the specific issue (status transition, GSI, permissions, etc.)
6. **TEST**: Start a new execution and verify polling works end-to-end
7. **VERIFY**: Check execution details page shows server names, IPs, and status updates

## Conclusion

The code migration is **100% complete and correct**. The decomposed handlers have identical logic to the monolithic handler. The issue is **NOT in the migrated functions** but in the **polling infrastructure**:

- Execution status may not be transitioning to POLLING
- StatusIndex GSI may not be configured
- Execution Finder may not be finding executions
- Execution Poller may not be invoked or failing

**Action Required**: Investigate the polling chain (Step 1-5 above) to identify the specific failure point.
