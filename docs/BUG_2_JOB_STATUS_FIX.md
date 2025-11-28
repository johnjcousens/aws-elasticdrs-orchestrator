# Bug #2 Fix - Job Status Checking

**Bug Discovered**: November 28, 2025, 5:11 PM ET  
**Bug Fixed**: November 28, 2025, 5:20 PM ET  
**Severity**: CRITICAL - System showed COMPLETED when jobs FAILED

## Executive Summary

During Test Scenario 1.1 validation, discovered that DRS recovery jobs failed but our system marked executions as COMPLETED. Investigation revealed ExecutionPoller was checking DRS job `status` field (COMPLETED) instead of verifying actual server launch success/failure.

## Bug Details

### Root Cause

**Location**: `lambda/poller/execution_poller.py` - `poll_wave_status()` function (line 253)

**Problem Code**:
```python
# Line 253 - PROBLEM: Copies DRS status directly
wave['Status'] = job_status.get('Status', wave.get('Status', 'UNKNOWN'))

# Lines 269-276 - Only sets COMPLETED, doesn't detect FAILED
if execution_type == 'DRILL':
    if all(s.get('Status') == 'LAUNCHED' for s in wave.get('Servers', [])):
        wave['Status'] = 'COMPLETED'
```

**Why This Failed**:
1. DRS job `status` field indicates job execution state: PENDING → STARTED → COMPLETED
2. Status='COMPLETED' means job finished running, NOT that it succeeded
3. Jobs can have status='COMPLETED' even when all servers FAILED to launch
4. Original code only checked for success (LAUNCHED), never checked for failure
5. Result: Failed jobs showed as COMPLETED in our system ❌

### Impact

**User Experience**:
- System shows "Execution COMPLETED" when servers actually failed to launch
- No distinction between successful and failed executions
- Users think recovery succeeded when it actually failed
- Misleading status undermines trust in the orchestration system

**Operational Impact**:
- Impossible to detect launch failures programmatically
- Automated testing cannot distinguish success from failure
- Alerting and monitoring ineffective
- Production readiness compromised

## The Fix

### Solution Design

Instead of copying DRS job status directly, check actual server launch statuses:

**Success Criteria**:
- ALL servers reach 'LAUNCHED' status → Wave Status = 'COMPLETED' ✅

**Failure Criteria**:
- ANY server has 'LAUNCH_FAILED', 'FAILED', or 'TERMINATED' → Wave Status = 'FAILED' ✅

**In-Progress**:
- DRS job status is 'PENDING' or 'STARTED' → Wave Status = 'LAUNCHING' 🔄

### Implementation

**Updated Code** (lines 250-337):
```python
def poll_wave_status(wave: Dict[str, Any], execution_type: str) -> Dict[str, Any]:
    # ... get job status from DRS ...
    
    # Get DRS job status and message
    drs_status = job_status.get('Status', 'UNKNOWN')
    wave['StatusMessage'] = job_status.get('StatusMessage', '')
    
    # Update server statuses from DRS
    # ... update servers ...
    
    # Determine wave status based on server launch results
    servers = wave.get('Servers', [])
    
    if execution_type == 'DRILL':
        if servers:
            # Check if ALL servers launched successfully
            all_launched = all(s.get('Status') == 'LAUNCHED' for s in servers)
            # Check if ANY servers failed to launch
            any_failed = any(s.get('Status') in ['LAUNCH_FAILED', 'FAILED', 'TERMINATED'] for s in servers)
            
            if all_launched:
                wave['Status'] = 'COMPLETED'
                logger.info(f"Wave {wave.get('WaveId')} completed - all servers LAUNCHED")
            elif any_failed:
                wave['Status'] = 'FAILED'
                failed_servers = [s.get('SourceServerID') for s in servers 
                                 if s.get('Status') in ['LAUNCH_FAILED', 'FAILED', 'TERMINATED']]
                logger.warning(f"Wave {wave.get('WaveId')} failed - servers {failed_servers} failed to launch")
            elif drs_status in ['PENDING', 'STARTED']:
                wave['Status'] = 'LAUNCHING'
            else:
                wave['Status'] = drs_status  # Fallback
        else:
            wave['Status'] = drs_status  # No servers yet
```

### Key Changes

1. **Added failure detection** - Checks for LAUNCH_FAILED, FAILED, TERMINATED statuses
2. **Verified success condition** - Only sets COMPLETED when ALL servers LAUNCHED
3. **Added LAUNCHING status** - Shows in-progress state clearly
4. **Enhanced logging** - Logs which servers failed and why
5. **Same logic for RECOVERY** - Also checks post-launch actions completion

## Deployment

**Deployment Time**: 5:20 PM ET, November 28, 2025

**Steps Taken**:
1. Modified `execution_poller.py` - Updated `poll_wave_status()` function
2. Syntax validated - Python compilation successful ✅
3. Packaged poller code - Created Lambda deployment zip (112 KB)
4. Deployed to Lambda - Updated `drs-orchestration-execution-poller-test`
5. Verified deployment - LastModified: 2025-11-28T22:20:19.000+0000

**Deployment Details**:
- Function: drs-orchestration-execution-poller-test
- Runtime: python3.12
- Code Size: 112,290 bytes
- Last Modified: 2025-11-28T22:20:19.000+0000
- Status: Active (InProgress → Active)

## Testing Plan

### Validation Steps

1. **Create new drill execution** via UI
2. **Monitor execution progress** - Should see:
   - PENDING → POLLING → LAUNCHING → [COMPLETED or FAILED]
3. **Check wave statuses** in DynamoDB:
   - Successful launches: Wave Status = 'COMPLETED'
   - Failed launches: Wave Status = 'FAILED'
4. **Verify execution status** - Overall:
   - All waves succeed: Execution Status = 'COMPLETED'
   - Any wave fails: Execution Status = 'FAILED'
5. **Check CloudWatch logs** - Should see detailed logging:
   - Success: "Wave X completed - all servers LAUNCHED"
   - Failure: "Wave X failed - servers [IDs] failed to launch"

### Expected Behavior

**Scenario 1: Successful Launch**
```
DRS Job Status: COMPLETED
Server Statuses: All LAUNCHED
Wave Status: COMPLETED ✅
Execution Status: COMPLETED ✅
```

**Scenario 2: Failed Launch** (Previously broken, now fixed)
```
DRS Job Status: COMPLETED
Server Statuses: Some LAUNCH_FAILED
Wave Status: FAILED ✅ (was incorrectly COMPLETED)
Execution Status: FAILED ✅ (was incorrectly COMPLETED)
```

**Scenario 3: In Progress**
```
DRS Job Status: STARTED
Server Statuses: Mixed (some LAUNCHING, none failed yet)
Wave Status: LAUNCHING ✅ (new status)
Execution Status: POLLING ✅
```

## Related Issues

### Bug #1: Multiple JobIds Per Wave (FIXED)
- Fixed in commit 30321bb
- Created `start_drs_recovery_for_wave()` function
- Now creates ONE JobId per wave (not per server)
- ExecutionPoller can properly track jobs

### DRS Job Failures (To Investigate)
- Test execution showed all DRS jobs failed
- Need to investigate root cause:
  - IAM permissions?
  - Security group configuration?
  - Source server readiness?
  - Replication status?
- Will investigate once Bug #2 fix is validated

## Success Criteria

✅ **Fix Applied Successfully**:
- Code modified and deployed
- Syntax validated
- Lambda function updated

⏳ **Pending Validation**:
- Run new test execution
- Verify failed jobs show as FAILED
- Verify successful jobs show as COMPLETED
- CloudWatch logs show detailed status messages

## Next Steps

1. **Investigate DRS job failures** - Why did all jobs fail?
2. **Fix underlying DRS issues** - Permissions, configuration, etc.
3. **Re-run Test Scenario 1.1** - With working DRS + corrected status checking
4. **Build test automation** - End-to-end validation framework
5. **Complete MVP testing** - All test scenarios with fixed system

## Files Modified

**Git Commit**: (Pending - will commit after validation)

**Files Changed**:
- `lambda/poller/execution_poller.py` - Updated `poll_wave_status()` function (~60 lines modified)

**Lines of Code**:
- Added: ~40 lines (failure detection, enhanced logging)
- Modified: ~20 lines (status logic)
- Total: ~60 lines of code changes

---

**Bug Discovered By**: User feedback during Test Scenario 1.1  
**Bug Fixed By**: Cline AI Assistant  
**Documentation Created**: November 28, 2025, 5:20 PM ET  
**Status**: DEPLOYED - Awaiting Validation
