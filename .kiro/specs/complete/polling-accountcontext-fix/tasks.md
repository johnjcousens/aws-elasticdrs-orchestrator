# Implementation Plan: Polling AccountContext Fix

## Overview

This is a minimal, surgical bug fix to resolve cross-account DRS query failures during polling operations. The fix involves adding 5 lines of code to extract and pass `accountContext` to the reconciliation function.

**Bug Location**: `lambda/execution-handler/index.py`, line 3671  
**Root Cause**: Missing `account_context` parameter in `reconcile_wave_status_with_drs()` call  
**Impact**: Cross-account DRS job status queries fail with "Failed to assume role None" error

## Tasks

- [x] 1. Implement the accountContext fix
  - [x] 1.1 Add accountContext extraction in get_execution_details_realtime()
    - Extract `account_context` from execution record using `execution.get("accountContext")`
    - Add logging to show account context being used (accountId, isCurrentAccount)
    - Handle missing accountContext gracefully (backwards compatibility)
    - _Requirements: 1.1, 1.2_
  
  - [x] 1.2 Pass accountContext to reconcile_wave_status_with_drs()
    - Update line 3671 to pass `account_context` as second parameter
    - Ensure parameter matches function signature: `reconcile_wave_status_with_drs(execution, account_context)`
    - _Requirements: 1.2_
  
  - [x] 1.3 Write unit tests for the fix
    - Test with cross-account execution (isCurrentAccount=False)
    - Test with same-account execution (isCurrentAccount=True)
    - Test with missing accountContext (backwards compatibility)
    - Verify account_context is extracted and passed correctly
    - _Requirements: 1.1, 1.2, 2.1, 2.2_

- [x] 2. Verify consistency with other callers
  - [x] 2.1 Review get_execution_details() implementation
    - Verify line 2201 correctly passes account_context
    - Confirm both endpoints use consistent pattern
    - _Requirements: 1.3_
  
  - [x] 2.2 Document the fix
    - Add code comments explaining why account_context is needed
    - Update any relevant documentation
    - _Requirements: 1.1, 1.2_

- [x] 3. Integration testing
  - [x] 3.1 Test cross-account execution polling
    - Start ExtendedSourceServers recovery drill (cross-account)
    - Poll for execution status via frontend
    - Verify CloudWatch logs show "Using account context for polling"
    - Verify no "Failed to assume role None" errors
    - Verify server statuses update from PENDING to LAUNCHED
    - _Requirements: 1.1, 1.2_
  
  - [x] 3.2 Test same-account execution polling
    - Start TargetAccountOnly recovery drill (same-account)
    - Poll for execution status via frontend
    - Verify DRS queries work without cross-account role assumption
    - Verify server statuses update correctly
    - _Requirements: 2.1, 2.2_
  
  - [x] 3.3 Verify CloudWatch logs
    - Check for successful cross-account DRS client creation
    - Verify account context logging shows correct accountId
    - Confirm no role assumption errors during polling
    - _Requirements: 1.1, 1.2_

- [x] 4. Deployment and verification
  - [x] 4.1 Deploy Lambda code
    - Run: `./scripts/deploy.sh test --lambda-only`
    - Verify deployment completes successfully
    - Check Lambda function LastModified timestamp
    - _Requirements: All_
  
  - [x] 4.2 Post-deployment verification
    - Start a recovery drill with cross-account servers
    - Monitor CloudWatch logs for successful DRS queries
    - Verify frontend shows real-time status updates
    - Confirm no regression in same-account executions
    - _Requirements: All_
  
  - [x] 4.3 Final checkpoint
    - Ensure all tests pass
    - Verify no "Failed to assume role None" errors in CloudWatch
    - Confirm server statuses update correctly in UI
    - Document any issues or observations

## Success Criteria

1. **No Role Assumption Errors**: CloudWatch logs show zero "Failed to assume role None" errors during polling
2. **Successful Cross-Account Queries**: DRS job status queries succeed for cross-account executions
3. **UI Updates Work**: Server statuses update from PENDING to LAUNCHED in the frontend
4. **No Regressions**: Same-account executions continue to work correctly
5. **Consistent Logging**: All polling operations log account context usage appropriately

## Code Change Summary

**File**: `lambda/execution-handler/index.py`  
**Location**: Line 3671  
**Lines Changed**: 5 lines added

**Before**:
```python
execution = reconcile_wave_status_with_drs(execution)
```

**After**:
```python
# Get account context from execution record for cross-account DRS queries
account_context = execution.get("accountContext")
if account_context:
    print(f"Using account context for polling: accountId={account_context.get('accountId')}, "
          f"isCurrentAccount={account_context.get('isCurrentAccount')}")

execution = reconcile_wave_status_with_drs(execution, account_context)
```

## Rollback Plan

If issues arise after deployment:

1. Revert the 5-line code change
2. Redeploy: `./scripts/deploy.sh test --lambda-only`
3. Investigate root cause
4. Verify accountContext structure hasn't changed
5. Check cross-account role configuration

## Notes

- This is a minimal, surgical fix - only 5 lines of code
- No changes to data structures or function signatures
- Backwards compatible with executions that don't have accountContext
- Consistent with existing pattern used in get_execution_details() (line 2201)
- Tasks marked with `*` are optional and can be skipped for faster deployment
