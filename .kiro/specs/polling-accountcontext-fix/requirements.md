# Polling AccountContext Fix - Requirements

## Overview

Fix the polling operation in `get_execution_details_realtime()` to properly pass `accountContext` to `reconcile_wave_status_with_drs()`, preventing role assumption failures during cross-account DRS job status queries.

## Problem Statement

When the frontend polls for execution status updates, the backend fails to query DRS job status in cross-account scenarios because `accountContext` is not passed to the reconciliation function.

**Error observed in CloudWatch logs:**
```
Failed to assume role None: Parameter validation failed:
Invalid type for parameter RoleArn, value: None, type: <class 'NoneType'>, valid types: <class 'str'>
Error polling wave: Parameter validation failed
```

**Root Cause:**
- Line 3671 in `lambda/execution-handler/index.py` calls `reconcile_wave_status_with_drs(execution)` without the `account_context` parameter
- The `accountContext` is stored in the execution record in DynamoDB (line 674) but not retrieved before calling the reconciliation function
- This causes `roleArn` to be `None` when trying to assume cross-account roles for DRS queries

## User Stories

### 1. Cross-Account Execution Polling
**As a** user monitoring a cross-account recovery drill  
**I want** the frontend to show real-time DRS job status updates  
**So that** I can see accurate progress of server launches in the target account

**Acceptance Criteria:**
- When polling an active execution with cross-account servers, the backend successfully queries DRS job status
- No "Failed to assume role None" errors appear in CloudWatch logs
- Server statuses update from PENDING to LAUNCHED in the UI as DRS jobs complete
- Recovery instance IDs are properly captured and displayed

### 2. Same-Account Execution Polling
**As a** user monitoring a same-account recovery drill  
**I want** polling to continue working without regression  
**So that** existing functionality is preserved

**Acceptance Criteria:**
- When polling an execution where all servers are in the current account, DRS queries work correctly
- No role assumption is attempted when `isCurrentAccount` is true
- Server statuses update correctly in the UI

## Technical Requirements

### 1. Retrieve AccountContext from Execution Record
- Extract `accountContext` from the execution record retrieved from DynamoDB
- Handle both presence and absence of `accountContext` field (backwards compatibility)
- Log the account context being used for debugging

### 2. Pass AccountContext to Reconciliation Function
- Pass the retrieved `accountContext` as the second parameter to `reconcile_wave_status_with_drs()`
- Ensure the parameter matches the function signature: `reconcile_wave_status_with_drs(execution: Dict, account_context: Optional[Dict] = None)`

### 3. Maintain Consistency with Other Callers
- Verify that other callers of `reconcile_wave_status_with_drs()` properly pass `account_context`
- Ensure consistent behavior across all code paths (direct invocation, Step Functions, polling)

## Data Flow

```
Frontend Poll Request
  ↓
get_execution_details_realtime()
  ↓
Query DynamoDB for execution record
  ↓
Extract accountContext from execution
  ↓
reconcile_wave_status_with_drs(execution, account_context)
  ↓
create_drs_client(region, account_context)
  ↓
Query DRS for job status (with cross-account credentials if needed)
  ↓
Return updated execution with real-time DRS data
```

## Non-Functional Requirements

### Performance
- No additional DynamoDB queries required (accountContext already in execution record)
- No impact on polling latency

### Reliability
- Must handle missing `accountContext` gracefully (backwards compatibility)
- Must not break existing same-account executions

### Observability
- Log when accountContext is retrieved and used
- Log when cross-account role assumption occurs
- Maintain existing error logging for DRS query failures

## Out of Scope

- Modifying the structure of `accountContext` storage
- Changing how `accountContext` is determined during execution creation
- Refactoring the `reconcile_wave_status_with_drs()` function logic
- Frontend changes (this is a backend-only fix)

## Success Criteria

1. **No Role Assumption Errors**: CloudWatch logs show no "Failed to assume role None" errors during polling
2. **Successful Cross-Account Queries**: DRS job status queries succeed for cross-account executions
3. **UI Updates Work**: Server statuses update from PENDING to LAUNCHED in the frontend
4. **No Regressions**: Same-account executions continue to work correctly
5. **Consistent Behavior**: All callers of `reconcile_wave_status_with_drs()` pass accountContext consistently

## Testing Strategy

### Unit Tests
- Test `get_execution_details_realtime()` with cross-account execution record
- Test `get_execution_details_realtime()` with same-account execution record
- Test `get_execution_details_realtime()` with missing accountContext (backwards compatibility)

### Integration Tests
1. Start ExtendedSourceServers recovery drill (cross-account)
2. Poll for execution status via frontend
3. Verify CloudWatch logs show successful DRS queries
4. Verify server statuses update in UI
5. Verify no role assumption errors

### Regression Tests
1. Start TargetAccountOnly recovery drill (same-account)
2. Poll for execution status via frontend
3. Verify DRS queries work without cross-account role assumption
4. Verify server statuses update in UI

## Related Context

- **Task 2** from context transfer: Monitor TargetAccountOnly recovery drill and verify DRS job tracking
- **Execution ID**: 394362de-b17f-426b-a301-433f265ad21f (TargetAccountOnly drill)
- **Error Timestamp**: 18:02:08 in CloudWatch logs
- **File**: `lambda/execution-handler/index.py`
- **Function**: `get_execution_details_realtime()` (lines 3600-3750)
- **Bug Location**: Line 3671
- **Related Function**: `reconcile_wave_status_with_drs()` (lines 6418-6728)
