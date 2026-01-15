# Recovery Instances Endpoint Fix

## Issue
The "Terminate Recovery Instances" dialog was showing "No Recovery Instances Found" even when instances existed.

## Root Cause
The `/executions/{id}/recovery-instances` endpoint was removed during performance optimizations (commit `793b706a` - "perf: remove expensive recovery instance calls from list executions").

The endpoint existed in multiple previous commits:
- `076b8578` - emergency: fix terminate instances dialog API integration
- `ff1c019b` - fix: add missing ExecutionRecoveryInstancesResourceId parameter
- `4bc502a7` - fix(rbac): add missing recovery-instances endpoint permission
- `13981f59` - Original implementation

## Solution
Restored the `get_recovery_instances()` function with camelCase field names to match current database schema:

### Changes Made

1. **Added `get_recovery_instances()` function** (lambda/api-handler/index.py ~line 6188)
   - Returns recovery instance details without terminating them
   - Uses camelCase field names: `executionId`, `planId`, `waves`, `waveNumber`, etc.
   - Supports cross-account executions via account context
   - Two-phase lookup strategy:
     - Primary: Query DRS jobs for participating servers
     - Fallback: Query recovery instances by source server IDs

2. **Added route handler** (lambda/api-handler/index.py ~line 3599)
   ```python
   elif execution_id and "/recovery-instances" in full_path:
       return get_recovery_instances(execution_id)
   ```

### API Response Format
```json
{
  "executionId": "string",
  "instances": [
    {
      "instanceId": "i-xxxxx",
      "recoveryInstanceId": "ri-xxxxx",
      "sourceServerId": "s-xxxxx",
      "region": "us-east-1",
      "waveName": "Wave 1",
      "waveNumber": 0,
      "jobId": "drsjob-xxxxx",
      "status": "running",
      "hostname": "server-hostname",
      "serverName": "Server Name"
    }
  ],
  "totalInstances": 1,
  "message": "Found 1 recovery instances"
}
```

## Testing
After deployment completes:
1. Navigate to Execution Details page
2. Click "Terminate Recovery Instances" button
3. Dialog should now display list of recovery instances with details
4. Verify instance count matches actual launched instances

## Related Issues
- This fix also addresses the field name mismatch issue where old executions used `instanceId` but new code expects `recoveredInstanceId`
- The function handles both old and new field name formats for backward compatibility

## Deployment
- Commit: `2309bdaf`
- Deployed via GitHub Actions CI/CD pipeline
- Target environment: test stack (aws-elasticdrs-orchestrator-test)
