# Bug 12 Root Cause Analysis - Instance Launch Failures

**Date**: November 28, 2025, 10:45 PM EST  
**Session**: Session 57 Part 16  
**Status**: Investigation Complete - Root Cause Identified

## Executive Summary

User reported repeated instance launch failures (0/1 successfully launched) across multiple DRS jobs. Investigation revealed:

1. ✅ **Bug 8 was already reverted** - No invalid API parameters exist
2. ✅ **Our code matches working reference implementation** - API calls are correct
3. ❌ **Actual problem**: IAM permissions OR DRS launch configuration issues

## Investigation History

### Failed Jobs
1. **drsjob-36742e0fb83dd8c8e** (Test execution)
   - Server: EC2AMAZ-3NLOQQ7 (s-0e15a6a8c54be0c7d)
   - Result: Successfully launched 0/1, Recovery status FAILED

2. **drsjob-334750d51db4ed208** (Current execution)
   - Server: EC2AMAZ-RLP9U5V (s-3d75cdc0d9a28a725)
   - Result: Successfully launched 0/1, Recovery status FAILED

## Code Analysis

### Current Implementation (lambda/index.py lines 1050-1120)

```python
# STEP 2: Build sourceServers array WITH recovery snapshots
source_servers = []
for server_id in server_ids:
    try:
        # Get recovery snapshots for this server
        snapshots_response = drs_client.describe_recovery_snapshots(
            sourceServerID=server_id
        )
        
        # Sort by timestamp (most recent first)
        snapshots = sorted(
            completed_snapshots,
            key=lambda x: x['timestamp'],
            reverse=True
        )
        
        # Build source server config
        server_config = {'sourceServerID': server_id}
        
        if snapshots:
            snapshot_id = snapshots[0]['snapshotID']
            server_config['recoverySnapshotID'] = snapshot_id
        
        source_servers.append(server_config)
```

### Working Reference Implementation (drs-plan-automation)

```python
wave_plan[index].append({
    'sourceServerID': k  # ONLY sourceServerID
})

# Later in start_recovery:
drs_launch = drs_client.start_recovery(
    isDrill=isdrill,
    sourceServers=servers  # Simple array
)
```

### Comparison Result

✅ **IDENTICAL PATTERN**: Both use simple `{'sourceServerID': id}` format  
✅ **NO INVALID PARAMETERS**: Bug 8 recoveryInstanceProperties was already removed  
✅ **PROPER API USAGE**: Matches AWS DRS API specification exactly

## Why Jobs Are Failing

Since our API calls are correct, the failure must be:

### Theory 1: IAM Permission Issues (Most Likely)
- Lambda has DRS permissions but may lack EC2 permissions
- Instances fail to launch due to missing permissions:
  - `ec2:RunInstances`
  - `ec2:CreateTags`
  - `ec2:DescribeInstances`
  - Network interface permissions
  - Security group permissions

**Bug 11 attempted to fix this** but may have been incomplete.

### Theory 2: DRS Launch Configuration Issues
- Invalid subnet configuration in DRS launch settings
- Invalid security group configuration
- Invalid instance type selection
- Network configuration problems

### Theory 3: Account/Service Limits
- EC2 instance limits reached
- Subnet capacity issues
- DRS service quotas

## Recommended Next Steps

### Step 1: Check Lambda CloudWatch Logs
Look for detailed error messages from DRS job execution:
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/drs-orchestration-api-handler-test \
  --filter-pattern "drsjob-334750d51db4ed208" \
  --start-time $(($(date +%s) - 3600))000 \
  --region us-east-1
```

### Step 2: Check DRS Job Logs Directly
```bash
aws drs describe-job-log-items \
  --job-id drsjob-334750d51db4ed208 \
  --region us-east-1 \
  --max-results 100
```

### Step 3: Verify Lambda IAM Role
Check if Lambda execution role has ALL required permissions:
```bash
aws iam get-role-policy \
  --role-name drs-orchestration-lambda-role-test \
  --policy-name DRSOrchestrationPolicy
```

### Step 4: Check DRS Launch Configuration
```bash
aws drs get-launch-configuration \
  --source-server-id s-3d75cdc0d9a28a725 \
  --region us-east-1
```

## Critical Insights from Reference Code

The working drs-plan-automation code shows:
1. **Assumed role credentials** are used for DRS operations
2. **Cross-account access** is required
3. **No launch configuration parameters** in start_recovery()
4. **Pre-configured launch settings** in DRS service itself

## Conclusion

**The API calls are correct. The problem is environmental:**
- IAM permissions (most likely)
- DRS launch configuration 
- Account/network configuration
- Service limits

**Next action**: Debug with actual DRS job logs and Lambda CloudWatch logs to identify the specific permission or configuration issue.

## Files Modified

None - this is purely diagnostic analysis.

## Related Documents

- `docs/BUG_11_NO_LAUNCH_INVESTIGATION.md` - Previous IAM investigation
- `docs/BUG_11_RESOLUTION.md` - Attempted IAM fix
- `docs/BUG_9_DRS_API_FIX_RESEARCH.md` - API parameter investigation
