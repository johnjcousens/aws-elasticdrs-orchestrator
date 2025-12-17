# Conflict Detection & Resume Fix Changelog

## Session: December 17, 2025

### Issue 1: Resume Not Starting Wave 2

**Problem**: After pausing at wave 2 and clicking Resume, wave 2 never started.

**Root Cause**: 
1. `resume_execution()` in `index.py` builds `resume_state` but didn't include `account_context`
2. Step Functions `ResumeWavePlan` state expects `$.account_context` 
3. `start_wave_recovery()` in orchestration Lambda needs `account_context` for DRS client
4. Case mismatch: Initial start uses `AccountContext` (PascalCase), resume used `account_context` (snake_case)

**Fix Applied**:

1. **lambda/index.py** - Store AccountContext when execution starts:
   - Line ~3020: Added `AccountContext` to `history_item` when creating execution
   - Line ~4365: Added `account_context` to `resume_state` from stored execution record

2. **lambda/orchestration_stepfunctions.py** - Handle both cases:
   - Added `get_account_context(state)` helper function (line ~55)
   - Updated 3 locations to use helper instead of `state.get('AccountContext', {})`
   - Lines: ~440, ~457, ~567

**Deployed**: 2025-12-17T12:38:14Z

---

### Issue 2: DRS Job Conflict Detection (Previous Session)

**Problem**: When a drill fails, DynamoDB shows FAILED but DRS job may still be running. New drills fail with "ConflictException".

**Status**: Partially implemented - `/recovery-plans` API returns conflict info, but `POST /executions` may not be blocking properly.

**Files Modified**:
- `lambda/index.py`:
  - Added `DRS_ACTIVE_JOB_STATUSES = ['PENDING', 'STARTED']`
  - Added `get_servers_in_active_drs_jobs()` function
  - Updated `get_plans_with_conflicts()` to check DRS jobs
  - Updated `check_server_conflicts()` to check DRS jobs

**Next Steps**:
- Test resume functionality with new fix
- Verify conflict detection blocks execution start
