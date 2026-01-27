# Batch 2 Extraction Checkpoint

**Date**: January 23, 2026  
**Status**: Ready to Extract  
**Progress**: 30% Complete (7/23 tasks) - Batch 1 Complete, Batch 2 Prepared

## Summary

Batch 1 (Core Execution Lifecycle) is complete with all 5 functions extracted and tested. Batch 2 (Instance Management) function list has been corrected and is ready for extraction.

## Batch 2 Functions (Instance Management)

### Corrected Function List

The original tasks.md listed incorrect function names. After analyzing `handle_executions()` routing logic, the actual Batch 2 functions are:

1. **resume_execution()** - POST /executions/{id}/resume
   - Lines: 6540-6770 (~230 lines)
   - Purpose: Send task token to Step Functions to resume paused execution
   - Status: ✅ Fully read and ready to extract

2. **get_execution_details_realtime()** - GET /executions/{id}/realtime
   - Lines: 6067-6210 (~143 lines)
   - Purpose: Get real-time execution data from DRS API (slow but current)
   - Status: ✅ Fully read and ready to extract

3. **get_recovery_instances()** - GET /executions/{id}/recovery-instances
   - Lines: 6880-7136 (~256 lines)
   - Purpose: Get recovery instance details for display before termination
   - Status: ✅ Fully read and ready to extract

4. **terminate_recovery_instances()** - POST /executions/{id}/terminate-instances
   - Lines: 7137-7665 (~528 lines)
   - Purpose: Terminate all recovery instances from an execution
   - Status: ⚠️ Partially read (need to complete)

5. **get_termination_job_status()** - GET /executions/{id}/termination-status
   - Lines: 7666-7830 (~164 lines)
   - Purpose: Check DRS termination job progress
   - Status: ✅ Fully read and ready to extract

**Total Code**: ~1,321 lines to extract

## Changes Made

### 1. Corrected Batch 2 Function List (Commit: pending)

**File**: `.kiro/specs/api-handler-decomposition/tasks.md`

**Changes**:
- Changed batch name from "Wave Management" to "Instance Management"
- Corrected function names to match actual API handler implementation:
  - ✅ `resume_execution` (correct)
  - ❌ `get_wave_status` → ✅ `get_execution_details_realtime`
  - ❌ `retry_wave` → ✅ `get_recovery_instances`
  - ❌ `skip_wave` → ✅ `get_termination_job_status`
  - ✅ `terminate_recovery_instances` (correct)

**Verification**: Functions verified against `handle_executions()` routing logic in API handler (lines 3990-4058)

### 2. Documentation Updates (Commit: 5c9ffa2)

**Files Updated**:
- `infra/orchestration/drs-orchestration/CHANGELOG.md` - Added Phase 2 Batch 1 section
- `infra/orchestration/drs-orchestration/README.md` - Updated progress to 30%

## Next Steps (Batch 2 Extraction)

### Step 1: Complete Reading Functions
- Read remaining portion of `terminate_recovery_instances()` (lines 7300-7665)
- Verify all 5 functions are complete

### Step 2: Append to Execution Handler
Add all 5 Batch 2 functions to `lambda/execution-handler/index.py`:
- Append after Batch 1 functions
- Maintain all comments and logic
- Preserve error handling

### Step 3: Update Routing Logic
Update `handle_execution_request()` in execution handler to route Batch 2 endpoints:
```python
elif execution_id and "/resume" in path:
    return resume_execution(execution_id)
elif execution_id and "/realtime" in path:
    return get_execution_details_realtime(execution_id)
elif execution_id and "/recovery-instances" in path:
    return get_recovery_instances(execution_id)
elif execution_id and "/terminate-instances" in path:
    return terminate_recovery_instances(execution_id)
elif execution_id and "/termination-status" in path:
    job_ids = query_params.get("jobIds", "")
    region = query_params.get("region", "us-west-2")
    return get_termination_job_status(execution_id, job_ids, region)
```

### Step 4: Test Extraction
```bash
# Syntax validation
python3 -m py_compile lambda/execution-handler/index.py

# Run tests
pytest tests/python/unit/ -v
pytest tests/integration/test_execution_handler.py -v
pytest tests/ -k "execution" -v
```

### Step 5: Commit Batch 2
```bash
git add lambda/execution-handler/index.py
git commit -m "feat: extract Batch 2 functions to execution handler (5/10)

- Added resume_execution() - Resume paused executions
- Added get_execution_details_realtime() - Real-time DRS data
- Added get_recovery_instances() - List recovery instances
- Added terminate_recovery_instances() - Terminate instances
- Added get_termination_job_status() - Check termination progress
- Updated routing logic for 5 new endpoints
- All tests passing"
```

## Dependencies

### Shared Modules Required
All Batch 2 functions depend on these shared modules (already available):
- `shared.response_utils` - response() function
- `shared.cross_account` - create_drs_client(), determine_target_account_context()
- `shared.execution_utils` - can_terminate_execution()
- `shared.decimal_encoder` - DecimalEncoder class

### DynamoDB Tables
- `execution_history_table` - Read execution data
- `recovery_plans_table` - Get plan details for account context

### AWS Clients
- `stepfunctions` - SendTaskSuccess for resume
- `drs` - DRS API calls for instances and jobs
- `boto3.client("drs")` - Regional DRS clients

## Testing Strategy

### Unit Tests
- Test each function with mocked DynamoDB and DRS responses
- Verify error handling for missing executions
- Test cross-account context handling

### Integration Tests
- Test resume with valid/invalid task tokens
- Test real-time data reconciliation
- Test instance discovery and termination
- Test termination status polling

### Expected Results
- All 720 existing tests continue passing
- New Batch 2 tests added (estimate: +15 tests)
- Total: ~735 tests passing

## Commits

### Completed
- `768a8b1` - Extract execute_recovery_plan (Batch 1 - 1/5)
- `fda597c` - Complete Batch 1 extraction (5/5)
- `a27d23c` - Fix: add validate_server_replication_states
- `5c9ffa2` - docs: update CHANGELOG and README with Phase 2 Batch 1 completion

### Pending
- Batch 2 function list correction (tasks.md)
- Batch 2 extraction (5 functions)
- Batch 2 testing and validation

## Progress Tracking

**Overall Progress**: 30% → 35% (after Batch 2)

**Phase 2 Progress**:
- Batch 1: ✅ COMPLETE (5/23 functions)
- Batch 2: 🔄 IN PROGRESS (5/23 functions)
- Batch 3: ⏳ PENDING (6/23 functions)
- Batch 4: ⏳ PENDING (5/23 functions)
- Batch 5: ⏳ PENDING (2/23 functions)

**Total Functions**:
- Extracted: 5/23 (22%)
- Remaining: 18/23 (78%)
