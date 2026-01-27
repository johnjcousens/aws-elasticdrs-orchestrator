# Known Issues

## ✅ RESOLVED ISSUES

### CANCELLING Status Display and Conflict Detection

**Status**: ✅ Resolved (January 26, 2026)  
**Severity**: High (was blocking concurrent executions)  
**Resolution**: See `docs/fixes/CANCELLING_STATUS_AND_CONFLICT_FIX.md`

**Issues Fixed**:
1. **CANCELLING executions appeared in History instead of Active Executions**
   - Root Cause: `hasActiveDrsJobs` hardcoded to `false`
   - Solution: Calculate dynamically from wave status
   - Impact: Executions now stay in Active until all waves complete

2. **Plans blocked by CANCELLED waves**
   - Root Cause: Conflict detection checked all waves without verifying status
   - Solution: Skip CANCELLED waves in conflict detection
   - Impact: Plans can run immediately when conflicting waves are cancelled

### Dashboard Status Color Coding

**Status**: ✅ Resolved (January 26, 2026)  
**Severity**: Medium (UI display issue)  
**Resolution**: See `docs/fixes/DASHBOARD_AND_ACCOUNT_FIXES.md`

**Issues Fixed**:
1. **Execution Status pie chart showed gray instead of green for COMPLETED**
   - Root Cause: Frontend used lowercase keys, backend returned uppercase
   - Solution: Updated STATUS_COLORS to use uppercase keys
   - Impact: Dashboard now correctly displays execution status colors

2. **Success rate displayed 0% even with completed executions**
   - Root Cause: Key mismatch between statusCounts and color mapping
   - Solution: Fixed key references to use uppercase
   - Impact: Success rate metric now calculates properly

### Account Management Simplification

**Status**: ✅ Resolved (January 26, 2026)  
**Severity**: Low (UX improvement)  
**Resolution**: See `docs/fixes/DASHBOARD_AND_ACCOUNT_FIXES.md`

**Issue Fixed**:
- **Add Target Account modal included unnecessary staging account fields**
  - Root Cause: Staging accounts already configured in DRS with trust relationships
  - Solution: Removed stagingAccountId and stagingAccountName fields
  - Impact: Simplified UI focused on essential target account configuration

### Termination Progress Bar

**Status**: ✅ Resolved (January 26, 2026)  
**Severity**: Medium (monitoring visibility)  
**Resolution**: See `docs/fixes/TERMINATION_PROGRESS_FIX.md`

**Issue Fixed**:
- **Termination progress bar stuck at 0% and never updated**
  - Root Cause: Backend set `instancesTerminated=True` immediately, frontend stopped polling
  - Solution: Defer setting flag until DRS jobs actually complete
  - Impact: Progress bar now updates correctly (10% → 50% → 100%)

---

## 🔴 OPEN ISSUES

## Backend Polling Not Enriching Server Data

**Status**: Open  
**Severity**: Medium  
**Affects**: Execution details UI display

### Description

The execution-handler's polling mechanism is not properly enriching server data with recovery instance details after DRS job completion.

### Symptoms

1. Server `launchStatus` not updated to `LAUNCHED` when job completes
2. Wave `status` remains `STARTED` instead of `COMPLETED`
3. Missing instance data in UI:
   - Instance ID
   - Instance Type
   - Launch Time

### Evidence

**DynamoDB Data** (execution-history table):
```
Wave Status: STARTED (should be COMPLETED)
Server hrp-core-db01-az1:
  - launchStatus: IN_PROGRESS (should be LAUNCHED)
  - instanceId: N/A (should be i-01e37dc27f549149a)
  - instanceType: N/A
  - launchTime: N/A
```

**DRS API Data** (describe-recovery-instances):
```
Source Server: s-51b12197c9ad51796
  Recovery Instance ID: i-01e37dc27f549149a
  State: STOPPED
  Job ID: drsjob-5f84731a3946c9582
```

**Job Logs** (describe-job-log-items):
```
Events: JOB_START, SNAPSHOT_START/END, CONVERSION_START/END, LAUNCH_START/END, JOB_END
Status: All events completed successfully
```

### Root Cause

The polling logic in execution-handler Lambda should:
1. Query DRS `describe-recovery-instances` for launched instances
2. Extract instance ID, type, state, and launch time
3. Update server statuses in DynamoDB execution record
4. Mark servers as `LAUNCHED` when instances exist (regardless of RUNNING/STOPPED state)
5. Mark wave as `COMPLETED` when all servers launched

Current behavior: Polling updates are not happening or failing silently.

**Note**: Instances are STOPPED by design per protection group launch settings, not due to drill mode.

### Workaround

Frontend now uses job logs to determine completion status:
- Checks for `JOB_END` and `LAUNCH_END` events
- Shows correct status badges (✓) even if backend data is stale
- Progress calculation uses job log data as authoritative source

### Impact

- **UI Display**: Status badges now correct (fixed in frontend)
- **Progress Bar**: Now shows correct percentage (fixed in frontend)
- **Instance Details**: Still missing (requires backend fix)
- **Functionality**: Does not affect DR operations, only monitoring

### Fix Required

Update execution-handler polling logic to:
1. Call `describe-recovery-instances` after job completion
2. Enrich server data with instance details
3. Update DynamoDB execution record
4. Handle drill vs recovery scenarios (STOPPED vs RUNNING instances)

### Related Files

- `lambda/execution-handler/index.py` - Polling logic
- `lambda/shared/drs_utils.py` - DRS API utilities
- `frontend/src/components/WaveProgress.tsx` - Frontend workaround

### Test Case

**Execution ID**: `920312ed-b7dc-4d43-b651-9b0fffcb6859`  
**Job ID**: `drsjob-5f84731a3946c9582`  
**Region**: us-west-2  
**Type**: DRILL

Expected after job completion:
- Wave status: `COMPLETED`
- Both servers: `launchStatus: LAUNCHED`
- Instance IDs populated
- Instance types populated
- Launch times populated
