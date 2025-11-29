# Bug 11: DRS Job Completes Without Launching Instance

**Status**: INVESTIGATING  
**Severity**: CRITICAL  
**Discovered**: November 28, 2025 10:28 PM EST

## Summary

DRS job creates successfully but never attempts to launch recovery instance. Job status shows "COMPLETED" but launchStatus shows "FAILED" with no actual launch attempt.

## Symptoms

```
Job Status: COMPLETED
Launch Status: FAILED
Job Log: START → SNAPSHOT → END (no launch phase)
Recovery Instance: None created
```

## Investigation Results

### 1. Job Details
```
Job ID: drsjob-308515d95a29790bc
Status: COMPLETED
Type: LAUNCH
Initiated By: START_DRILL
Duration: ~1 second
Participating Servers: 1
Launch Status: FAILED (but never attempted)
```

### 2. Job Log Events
```
- JOB_START
- SNAPSHOT_START (server: s-3d75cdc0d9a28a725)
- SNAPSHOT_END (server: s-3d75cdc0d9a28a725)
- JOB_END
```

**CRITICAL: No launch-related events at all!**

### 3. Server Status
```
Source Server: s-3d75cdc0d9a28a725
Replication State: CONTINUOUS (healthy)
Lag Duration: 0 (ready)
Last Launch: DRILL (has drilled before)
Launch Config: Valid (launchDisposition: STARTED)
```

### 4. Code Comparison

**Standalone Script (WORKS):**
```python
source_server_config = {
    'sourceServerID': source_server_id
}
if recovery_snapshot:
    source_server_config['recoverySnapshotID'] = snapshot['snapshotID']

drs_client.start_recovery(
    sourceServers=[source_server_config],
    isDrill=True,
    tags={...}
)
```

**Lambda Code (IDENTICAL):**
```python
source_servers = []
for server_id in server_ids:
    # Get snapshots
    snapshots = get_sorted_snapshots(server_id)
    
    # Build config
    server_config = {'sourceServerID': server_id}
    if snapshots:
        server_config['recoverySnapshotID'] = snapshots[0]['snapshotID']
    
    source_servers.append(server_config)

drs_client.start_recovery(
    sourceServers=source_servers,
    isDrill=is_drill,
    tags=job_tags
)
```

**FINDING: The code is IDENTICAL. Both use same DRS API pattern.**

## Key Questions

1. **Why does DRS create job but skip launch?**
   - Snapshots taken successfully
   - Job marked as "COMPLETED" 
   - But no launch phase occurs

2. **What's different between standalone and Lambda?**
   - Same API calls
   - Same parameters
   - Same snapshot selection logic
   - Different execution context (Lambda vs local)

3. **Is this an IAM permission issue?**
   - CloudWatch showed: `AccessDeniedException` on `GetLaunchConfiguration`
   - But job still created (permission error non-blocking?)
   - Does DRS silently fail launch when can't read config?

4. **Is this a DRS service state issue?**
   - Server last launched: DRILL
   - Is previous drill cleanup blocking new drill?
   - Does DRS require cleanup between drills?

## Hypotheses

### Hypothesis 1: Permission Issue (LIKELY)
```
Error in logs: AccessDeniedException - drs:GetLaunchConfiguration
Impact: DRS may require this permission to launch instances
Result: Job creates, snapshots succeed, but launch silently skipped
```

**Test**: Add `drs:GetLaunchConfiguration` permission to Lambda role

### Hypothesis 2: Previous Drill Cleanup Required
```
Server state: Last launch was DRILL
Issue: Previous drill instance may not be terminated
Impact: DRS blocks new drill until cleanup
```

**Test**: Check for existing drill instances, terminate if found

### Hypothesis 3: DRS Service Configuration
```
Issue: Some DRS service setting preventing drill launches
Examples: Account limits, service quotas, region restrictions
```

**Test**: Check DRS service limits and quotas

## Next Steps

1. **Check IAM Permissions** (HIGHEST PRIORITY)
   - Review Lambda role permissions
   - Add `drs:GetLaunchConfiguration` if missing
   - Redeploy and test

2. **Check for Existing Drill Instances**
   - Query for recovery instances in DRILL mode
   - Terminate any existing drill instances
   - Retry drill

3. **Compare Full Job Details**
   - Get complete job JSON from both scenarios
   - Compare all fields and metadata
   - Look for subtle differences

4. **Enable DRS Debug Logging**
   - Check if DRS has verbose logging options
   - Look for additional error details

## CloudWatch Log Evidence

```
2025-11-29T03:24:38 [Launch Config] ERROR for s-3d75cdc0d9a28a725: 
  An error occurred (AccessDeniedException) when calling the 
  GetLaunchConfiguration operation: User: 
  arn:aws:sts::438465159935:assumed-role/drs-orchestration-test-LambdaStack-1-ApiHandlerRole-g3ncRmCgVFUo/drs-orchestration-api-handler-test 
  is not authorized to perform: drs:GetLaunchConfiguration 
  on resource: arn:aws:drs:us-east-1:438465159935:source-server/s-3d75cdc0d9a28a725
```

**This permission error occurs BEFORE the start_recovery() call!**

## Timeline

- 03:24:38 - Permission error on GetLaunchConfiguration
- 03:24:38 - start_recovery() called successfully
- 03:24:38 - Job created (drsjob-308515d95a29790bc)
- 03:24:38 - Snapshots taken
- 03:24:39 - Job marked COMPLETED
- 03:24:39 - **NO LAUNCH ATTEMPT**

## Impact

- ALL drill operations broken
- ALL recovery operations likely broken
- User cannot test failover
- System appears to work but doesn't

## Related Issues

- Bug 8: Launch config enhancement (attempted to read configs)
- Bug 9: Removed invalid parameter from start_recovery()
- Bug 10: Snapshot sorting (FIXED - working)
