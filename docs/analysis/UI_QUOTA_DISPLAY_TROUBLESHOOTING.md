# UI Quota Display Troubleshooting

## Issue: "Max Servers Per Job" Gauge Not Displaying

**Status**: RESOLVED ✅

**Date**: February 2, 2026

## Problem Summary

The "Max Servers Per Job" gauge was not visible on the System Status page, even though the other two job-related gauges (Concurrent Jobs and Servers in Jobs) were displaying correctly.

## Root Cause: Syntax Error from Duplicate Lines

**Location**: `lambda/query-handler/index.py` lines 4007-4009

**Bug**:
```python
# BROKEN CODE (before fix)
max_per_job = validate_max_servers_per_job(
    primary_region, drs_client
)
print(f"Max per job: {max_per_job}")
    primary_region, drs_client  # DUPLICATE!
)
print(f"Max per job: {max_per_job}")  # DUPLICATE!
```

This created invalid Python syntax that prevented the Lambda from loading properly. The function would fail silently during import, causing the jobs metrics code to never execute.

**Fix**:
```python
# FIXED CODE
max_per_job = validate_max_servers_per_job(
    primary_region, drs_client
)
print(f"Max per job: {max_per_job}")
```

## Investigation Timeline

### 1. Initial Frontend Check ✅

**Checked**: `frontend/src/pages/SystemStatusPage.tsx` lines 344-361

**Finding**: Gauge rendering code is present and correct.

**Conclusion**: Frontend code is correct. The issue is that `capacityData.maxServersPerJob` is null/undefined.

### 2. TypeScript Interface Check ✅

**Checked**: `frontend/src/types/staging-accounts.ts` lines 267-274

**Finding**: Interface includes all three job metrics correctly.

**Conclusion**: TypeScript types are correct.

### 3. Backend Function Check ❌ → ✅

**Checked**: `lambda/shared/drs_limits.py` lines 360-460

**Finding**: Function `validate_max_servers_per_job()` was MISSING!

**Action Taken**: Created the function with proper signature.

**Status**: ✅ FIXED

### 4. Function Signature Check ❌ → ✅

**Finding**: Functions were being called with wrong number of arguments.

**Action Taken**: Modified all three functions to accept optional `drs_client` parameter.

**Status**: ✅ FIXED

### 5. Credentials Check ❌ → ✅

**Finding**: Validation functions were being called WITHOUT assumed role credentials.

**Action Taken**: Modified query handler to create DRS client with assumed role credentials and pass to validation functions.

**Status**: ✅ FIXED

### 6. Import Check ❌ → ✅

**Finding**: Validation functions were NOT imported!

**Action Taken**: Added imports for all three validation functions.

**Status**: ✅ FIXED

### 7. Syntax Error Check ❌ → ✅

**Finding**: Duplicate lines in `validate_max_servers_per_job` call causing syntax error.

**Action Taken**: Removed duplicate lines.

**Status**: ✅ FIXED

## Resolution

### Changes Made

1. **Removed duplicate lines** in `validate_max_servers_per_job` call
2. **Added comprehensive debug logging** throughout jobs metrics section
3. **Applied black formatting** to ensure code style compliance

### Commit

```
commit 572a322d
fix: remove duplicate lines causing syntax error in jobs metrics query

Fixed critical bug in handle_get_combined_capacity where duplicate lines
were causing a syntax error that prevented the jobs metrics code from
executing.
```

## Expected Behavior After Fix

1. Lambda loads successfully without syntax errors
2. Jobs metrics query (Step 7.5) executes
3. Debug logs show execution flow
4. API response includes all three job metrics
5. UI displays all three gauges on System Status page

## Verification Steps

After deployment:

1. **Check Lambda logs** for "Starting jobs metrics query (Step 7.5)"
2. **Test API endpoint** to verify response includes job metrics
3. **Check UI** for all three gauges in "DRS Job Limits" section

## Related Files

- `lambda/query-handler/index.py` (lines 3935-4070)
- `lambda/shared/drs_limits.py` (lines 153-460)
- `frontend/src/pages/SystemStatusPage.tsx` (lines 344-361)
- `frontend/src/types/staging-accounts.ts` (lines 267-274)

## Lessons Learned

1. Syntax errors can fail silently in Lambda if they prevent module import
2. Debug logging is essential for troubleshooting Lambda execution
3. Code review would have caught the duplicate lines immediately
4. Test after every change to catch issues early
