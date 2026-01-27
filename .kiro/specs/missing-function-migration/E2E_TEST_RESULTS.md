# E2E Test Results - Phase 4

## Test Execution Details

**Date**: 2026-01-26  
**Environment**: dev  
**Execution ID**: e8aa91db-ce8b-4884-bc12-e7b9f66e9498  
**Recovery Plan**: 3TierRecoveryPlan (3 waves, 39 servers total)

## E2E Test 1: Server Enrichment & Execution Details

**Status**: ❌ FAILED

### Test Steps Executed

1. ✅ Started DR execution via API
   - Execution ID: e8aa91db-ce8b-4884-bc12-e7b9f66e9498
   - Plan: 3TierRecoveryPlan
   - Type: DRILL
   - Initiated by: integration-test@drs-orch.example.com

2. ✅ Execution created in DynamoDB
   - Table: aws-drs-orchestration-execution-history-dev
   - Status: POLLING
   - Waves: 1 started (DBWave1)
   - Servers: 2 in first wave

3. ✅ Step Functions execution started
   - ARN: arn:aws:states:us-east-1:777788889999:execution:aws-drs-orchestration-orchestration-dev:e8aa91db-ce8b-4884-bc12-e7b9f66e9498
   - DRS Job ID: drsjob-5bb659579a7bbed62
   - Region: us-west-2

4. ❌ Server enrichment NOT working
   - Server names: NULL (expected: EC2 Name tags)
   - IP addresses: NULL (expected: private IPs)
   - Only sourceServerId and launchStatus present

### DynamoDB Data Analysis

```json
{
  "sourceServerId": "s-51b12197c9ad51796",
  "launchStatus": "PENDING",
  "serverName": null,
  "ipAddress": null
}
```

**Expected**:
```json
{
  "sourceServerId": "s-51b12197c9ad51796",
  "launchStatus": "PENDING",
  "serverName": "WINDBSRV02",
  "ipAddress": "10.0.1.123"
}
```

### CloudWatch Logs Analysis

**Polling logs**:
- ✅ Polling triggered every minute
- ✅ "Polling complete" messages present
- ❌ NO enrichment function calls logged
- ❌ NO EC2 DescribeInstances calls logged
- ❌ NO server name/IP population logged

### Root Cause

**CRITICAL REGRESSION: Server enrichment only works for recovery instances, not source servers.**

The `enrich_server_data()` function in `shared/drs_utils.py` only enriches servers that have `recoveryInstanceID`:

```python
# Current implementation (BROKEN)
instance_ids = [
    s.get("recoveryInstanceID")  # Only gets recovery instances
    for s in participating_servers
    if s.get("recoveryInstanceID")
]
```

**Problem**: During PENDING/LAUNCHING status, servers have NO recovery instances yet, so enrichment returns empty data.

**What's Missing**:
1. Query DRS source servers by `sourceServerId` to get EC2 instance IDs
2. Query EC2 for source instance Name tags and IP addresses
3. Populate `serverName` and `ipAddress` from SOURCE servers, not recovery instances

**Historical execution worked** because it had a different enrichment implementation that queried source servers.

### Impact

**CRITICAL**: Frontend will display incomplete data:
- ❌ No server names (users see only source server IDs)
- ❌ No IP addresses
- ❌ Difficult to identify which servers are being recovered
- ❌ Poor user experience

### Comparison with Historical Data

**Historical execution** (0754e970-3f18-4cc4-9091-3bed3983d56f):
- ✅ Server names populated: "WINDBSRV02", "WINDBSRV01"
- ✅ DRS job info present
- ✅ Launch status tracked

**Current execution** (e8aa91db-ce8b-4884-bc12-e7b9f66e9498):
- ❌ Server names: NULL
- ✅ DRS job info present
- ✅ Launch status tracked

## Conclusion

**Phase 2 was marked complete based on historical data analysis, but live testing reveals server enrichment is NOT working in the current code.**

The polling operation is running, but it's not enriching server data with EC2 Name tags and IP addresses.

## Next Steps

1. **IMMEDIATE**: Fix `enrich_server_data()` to query source servers
   - Add DRS `describe_source_servers()` call
   - Extract EC2 instance IDs from source servers
   - Query EC2 for Name tags and IP addresses
   - Populate serverName and ipAddress fields

2. Add logging to track enrichment execution
3. Re-deploy with fixes
4. Re-test with new execution
5. Verify server names and IPs display in frontend

## Code Fix Required

**File**: `infra/orchestration/drs-orchestration/lambda/shared/drs_utils.py`

**Function**: `enrich_server_data()`

**Changes Needed**:
```python
def enrich_server_data(participating_servers, drs_client, ec2_client):
    # 1. Extract source server IDs
    source_server_ids = [s.get("sourceServerID") for s in participating_servers]
    
    # 2. Query DRS for source server details
    source_servers = drs_client.describe_source_servers(
        filters={"sourceServerIDs": source_server_ids}
    )
    
    # 3. Extract EC2 instance IDs from source servers
    source_instance_ids = [
        s["sourceProperties"]["identificationHints"]["awsInstanceID"]
        for s in source_servers["items"]
        if "sourceProperties" in s
    ]
    
    # 4. Query EC2 for Name tags and IPs
    ec2_instances = batch_describe_ec2_instances(source_instance_ids, ec2_client)
    
    # 5. Map source server ID -> EC2 instance data
    # 6. Enrich participating_servers with serverName and ipAddress
```

## Files to Investigate

- `infra/orchestration/drs-orchestration/lambda/execution-handler/index.py` - Poll operation
- `infra/orchestration/drs-orchestration/lambda/shared/drs_utils.py` - Enrichment functions
- CloudWatch Logs: `/aws/lambda/aws-drs-orchestration-execution-handler-dev`

## Test Environment

- API Endpoint: https://g0ojnzzfh1.execute-api.us-east-1.amazonaws.com/dev
- CloudFront URL: https://d1ksi7eif6291h.cloudfront.net
- DynamoDB Table: aws-drs-orchestration-execution-history-dev
- Lambda Function: aws-drs-orchestration-execution-handler-dev
