# Terminate Instances Feature - TODO

## Current Status

The terminate instances dialog shows "No Recovery Instances Found" even when instances exist.

## Root Cause

The `/executions/{id}/recovery-instances` endpoint exists but returns empty results because:
1. Data structure mismatch between DynamoDB storage and API expectations
2. Field name inconsistency (PascalCase vs camelCase)
3. Wave data may use `serverStatuses` or `servers` field inconsistently

## Quick Fix (Immediate)

Check the `get_recovery_instances()` function in `lambda/execution-handler/index.py` around line 3303:
- It looks for `serverStatuses` or `servers` in waves
- It needs `sourceServerId` from each server
- It queries DRS API for recovery instances

**Debug Steps**:
1. Check CloudWatch logs for the Lambda when dialog opens
2. Verify wave data structure in DynamoDB for execution `920312ed-b7dc-4d43-b651-9b0fffcb6859`
3. Confirm `serverStatuses` field exists and has `sourceServerId` populated

## Comprehensive Fix (Follow Plan)

See `docs/analysis/TERMINATE_BUTTON_FIX_PLAN.md` for the complete 3-day implementation plan that addresses all 19 historical breakages.

### Phase 1 Priorities:
1. Add `can_terminate_execution()` helper in `lambda/shared/execution_utils.py`
2. Normalize field names at API boundary in `lambda/shared/drs_utils.py`
3. Add backend validation and metadata to execution responses
4. Simplify frontend logic to trust backend flags

## Test Execution Data

**Execution ID**: `920312ed-b7dc-4d43-b651-9b0fffcb6859`
**Plan ID**: `3c8e5f4a-8b9d-4e2f-a1c3-7d6e9f2b4a8c`
**Status**: In Progress (Polling)
**Waves**: 3 waves
**Region**: us-west-2

Use this execution to test the fix.

## Related Files

- `lambda/execution-handler/index.py` - get_recovery_instances() function
- `lambda/shared/drs_utils.py` - Field normalization
- `frontend/src/components/TerminateInstancesDialog.tsx` - Dialog component
- `frontend/src/services/api.ts` - API client
- `docs/analysis/TERMINATE_BUTTON_FIX_PLAN.md` - Comprehensive fix plan
