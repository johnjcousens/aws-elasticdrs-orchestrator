# Multi-Wave Execution Bug Analysis

## Critical Finding

**Execution**: `0754e970-3f18-4cc4-9091-3bed3983d56f`
**Issue**: Execution marked as COMPLETED in DynamoDB after wave 1, but Step Functions still RUNNING with 2 more waves pending

## Root Cause

The execution-poller's `finalize_execution()` function marks the execution as COMPLETED when all waves in the DynamoDB record are complete. However, it doesn't know that Step Functions is managing a multi-wave execution with more waves to come.

### Architecture Flow

1. **Step Functions** starts execution with all 3 waves in its state
2. **Step Functions** creates wave 1 in DynamoDB and starts DRS job
3. **Execution-Finder** finds execution in POLLING status
4. **Execution-Poller** polls wave 1 status from DRS
5. **Execution-Poller** sees wave 1 COMPLETED
6. **Execution-Poller** calls `finalize_execution()` because all waves in DynamoDB are complete
7. **BUG**: Execution marked COMPLETED in DynamoDB
8. **Step Functions** still RUNNING, waiting to create wave 2

### Step Functions State

```json
{
  "status": "RUNNING",
  "waves": [
    {"waveName": "DBWave1", "waveNumber": 0, "pauseBeforeWave": false},
    {"waveName": "AppWave2", "waveNumber": 1, "pauseBeforeWave": true},
    {"waveName": "WebWave3", "waveNumber": 2, "pauseBeforeWave": true}
  ],
  "current_wave_number": 0,
  "completed_waves": 0,
  "all_waves_completed": false
}
```

### DynamoDB State (After Bug)

```json
{
  "executionId": "0754e970-3f18-4cc4-9091-3bed3983d56f",
  "status": "COMPLETED",  // ← BUG: Should be POLLING or PAUSED
  "waves": [
    {"waveName": "DBWave1", "waveNumber": 0, "status": "COMPLETED"}
  ],
  "totalWaves": 3  // ← Knows there should be 3 waves
}
```

## The Problem

The execution-poller doesn't have visibility into the Step Functions state. It only sees what's in DynamoDB:
- Wave 1 is complete
- No other waves exist in DynamoDB yet
- Conclusion: Execution must be complete

But the Step Functions knows:
- Wave 1 is complete
- Wave 2 needs to be created (paused before execution)
- Wave 3 needs to be created (paused before execution)
- Execution is NOT complete

## Solution Options

### Option 1: Don't Finalize in Poller (RECOMMENDED)
- Execution-poller should NEVER call `finalize_execution()`
- Only Step Functions should finalize the execution
- Poller only updates wave status
- Step Functions checks if all waves complete and finalizes

### Option 2: Check totalWaves Field
- Poller checks `totalWaves` field in execution record
- Only finalize if `len(waves) == totalWaves` AND all complete
- Still risky - race conditions possible

### Option 3: Add Step Functions Status Check
- Poller queries Step Functions execution status
- Only finalize if Step Functions execution is also complete
- Adds complexity and API calls

## Recommended Fix

Remove `finalize_execution()` logic from execution-poller. The poller should only:
1. Poll DRS job status for active waves
2. Update wave status in DynamoDB
3. Update `lastPolledTime` for adaptive polling

The Step Functions state machine should:
1. Create waves as needed
2. Monitor wave completion
3. Create next wave or pause
4. Finalize execution when all waves truly complete

## Impact

**Current State**:
- Single-wave executions work correctly
- Multi-wave executions break - only first wave executes
- Pause/resume functionality doesn't work
- Frontend shows execution as COMPLETED prematurely

**After Fix**:
- Multi-wave executions work correctly
- Pause/resume between waves works
- Frontend shows correct execution status
- Step Functions controls execution lifecycle

## Files to Modify

1. `lambda/execution-poller/index.py`
   - Remove `finalize_execution()` call from `lambda_handler()`
   - Keep wave status updates only

2. `lambda/orchestration-stepfunctions/index.py` (if exists)
   - Add execution finalization logic
   - Check all waves complete before finalizing

## Testing Plan

1. Start execution with 3-wave recovery plan
2. Verify wave 1 completes
3. Verify execution status remains POLLING or PAUSED
4. Verify Step Functions creates wave 2
5. Resume wave 2 execution
6. Verify wave 2 completes
7. Verify execution finalizes only after wave 3 completes

## Related Issues

- Normalization bug (FIXED) - separate issue
- This is the CORE functionality bug blocking multi-wave DR orchestration
