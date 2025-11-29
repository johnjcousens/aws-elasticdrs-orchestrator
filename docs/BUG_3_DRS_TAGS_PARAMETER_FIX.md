# Bug #3 Fix - Invalid DRS Tags Parameter

**Bug Discovered**: November 28, 2025, 6:15 PM ET  
**Bug Fixed**: November 28, 2025, 6:23 PM ET  
**Severity**: CRITICAL - All drill executions failing immediately

## Executive Summary

After deploying Bug #2 fix, discovered that all drill executions were failing immediately with ValidationException from DRS API. Investigation revealed Lambda code was passing an invalid `tags` parameter to `start_recovery()` API calls. DRS API does not accept tags parameter - only sourceServers, isDrill, and optionally recoverySnapshotID.

## Bug Details

### Root Cause

**Locations**: 
- `lambda/index.py` - `start_drs_recovery_for_wave()` function (line ~990)
- `lambda/index.py` - `start_drs_recovery()` function (line ~1070)

**Problem Code**:
```python
# PROBLEM: Passing tags parameter to DRS API
response = drs_client.start_recovery(
    sourceServers=source_servers,
    isDrill=is_drill,
    tags={'ExecutionId': execution_id}  # ❌ DRS API doesn't accept this
)
```

**DRS API Error**:
```
An error occurred (ValidationException) when calling the StartRecovery 
operation: Invalid request provided: Tags
```

**Why This Failed**:
1. AWS DRS `start_recovery()` API has specific parameters
2. Valid parameters: sourceServers, isDrill, recoverySnapshotID (optional)
3. `tags` is NOT a valid parameter for this API
4. Code attempted to tag jobs with ExecutionId for tracking
5. Result: 100% of drill executions fail at launch ❌

### Impact

**User Experience**:
- All drill executions fail immediately
- Error shows in wave server status
- No EC2 instances launch
- System completely unusable for drills

**Operational Impact**:
- MVP testing blocked
- Cannot validate DRS integration
- Cannot complete Test Scenario 1.1
- Production readiness blocked

## The Fix

### Solution Design

**Remove tags parameter** from both DRS API call functions:

1. `start_drs_recovery_for_wave()` - Wave-level launches (multiple servers)
2. `start_drs_recovery()` - Individual server launches (legacy path)

**ExecutionId Tracking Alternative**:
- JobId is already stored in wave data in DynamoDB
- ExecutionPoller uses JobId to track job status
- No need to tag DRS jobs directly with ExecutionId

### Implementation

**Fixed Code** (`start_drs_recovery_for_wave` line ~990):
```python
response = drs_client.start_recovery(
    sourceServers=source_servers,
    isDrill=is_drill
    # Removed: tags={'ExecutionId': execution_id}
)
```

**Fixed Code** (`start_drs_recovery` line ~1070):
```python
response = drs_client.start_recovery(
    sourceServers=[{
        'sourceServerID': server_id
    }],
    isDrill=is_drill
    # Removed: tags={'ExecutionId': execution_id, 'ExecutionType': execution_type}
)
```

### Key Changes

1. **Removed tags parameter** from both functions
2. **Preserved all valid parameters** - sourceServers, isDrill
3. **Added DRS API documentation** in code comments
4. **Enhanced logging** - Shows what parameters are being sent
5. **Maintained tracking** - JobId storage in DynamoDB unchanged

## Deployment

**Deployment Time**: 6:23 PM ET, November 28, 2025

**Steps Taken**:
1. Modified `lambda/index.py` - Removed tags from both functions
2. Syntax validated - Python compilation successful ✅
3. Packaged Lambda code - Created deployment zip (11.09 MB)
4. Deployed to Lambda - Updated `drs-orchestration-api-handler-test`
5. Verified deployment - LastModified: 2025-11-28T23:23:19.000+0000
6. Git commit - 390e2e9

**Deployment Details**:
- Function: drs-orchestration-api-handler-test
- Runtime: python3.12
- Code Size: 11,632,130 bytes
- Last Modified: 2025-11-28T23:23:19.000+0000
- Status: Active

**Git Commit**: 390e2e9
```
fix(lambda): Remove invalid tags parameter from DRS API calls

CRITICAL BUG FIX - DRS start_recovery() API calls were failing with:
'An error occurred (ValidationException) when calling the StartRecovery 
operation: Invalid request provided: Tags'
```

## Testing Plan

### Validation Steps

1. **Create new drill execution** via UI
2. **Monitor CloudWatch logs** for Lambda errors
3. **Check DRS console** - Jobs should be created
4. **Verify EC2 instances launch** - Should see instances in EC2 console
5. **Check ExecutionPoller logs** - Should track job status successfully
6. **Verify execution completes** - Should reach COMPLETED status

### Expected Behavior

**Before Fix** (100% failure):
```
DRS API Call: FAILED
Error: ValidationException - Invalid request provided: Tags
Wave Status: FAILED
No EC2 instances launched
```

**After Fix** (should succeed):
```
DRS API Call: SUCCESS
DRS Job Created: drsjob-xxxxx
EC2 Instances: Launching
Wave Status: LAUNCHING → COMPLETED
```

## Related Issues

### Bug #1: Multiple JobIds Per Wave (FIXED - Commit 30321bb)
- Created `start_drs_recovery_for_wave()` function
- ONE JobId per wave for ExecutionPoller tracking

### Bug #2: Job Status Checking (FIXED - Commit earlier today)
- ExecutionPoller now checks server launch statuses
- Distinguishes COMPLETED from FAILED properly

### Current Status
- Bug #1: ✅ FIXED
- Bug #2: ✅ FIXED
- Bug #3: ✅ FIXED
- Ready for end-to-end testing

## Success Criteria

✅ **Fix Applied Successfully**:
- Code modified and deployed
- Syntax validated
- Lambda function updated
- Git commit created

⏳ **Pending Validation**:
- Run new test execution
- Verify DRS jobs create successfully
- Verify EC2 instances launch
- Verify execution completes end-to-end

## Next Steps

1. **Execute drill test** - Create new execution via UI
2. **Monitor execution** - Watch logs and DRS console
3. **Validate EC2 launches** - Check instances appear
4. **Complete Test Scenario 1.1** - End-to-end validation
5. **Document results** - Update test documentation

## AWS DRS API Reference

**Valid Parameters** for `start_recovery()`:
- `sourceServers` (required) - List of source servers to recover
- `isDrill` (required) - True for drill, False for actual recovery
- `recoverySnapshotID` (optional) - Specific snapshot to use

**Invalid Parameters**:
- ❌ `tags` - Not supported by this API
- ❌ Any other custom parameters

**Documentation**: AWS DRS API Reference - StartRecovery operation

## Files Modified

**Git Commit**: 390e2e9

**Files Changed**:
- `lambda/index.py` - Updated `start_drs_recovery_for_wave()` and `start_drs_recovery()` functions

**Lines of Code**:
- Removed: 2 lines (tags parameters)
- Added: ~57 lines (enhanced logging and documentation)
- Total: ~59 lines of code changes

---

**Bug Discovered By**: CloudWatch logs analysis during testing  
**Bug Fixed By**: Cline AI Assistant  
**Documentation Created**: November 28, 2025, 6:23 PM ET  
**Status**: DEPLOYED - Ready for Testing
