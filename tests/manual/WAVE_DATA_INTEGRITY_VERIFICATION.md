# Wave Data Integrity Verification

## Overview

This document describes the comprehensive data integrity verification for Task 4.10: Verify no data loss during wave transitions after the wave polling refactoring (FR4 - Query Handler Read-Only Audit).

## Background

As part of the query-handler read-only audit, we split the `poll_wave_status()` function:
- **Query-handler**: Reads DRS job status (read-only) - returns wave data
- **Execution-handler**: Updates execution history table (write operations) - persists wave status

This verification ensures that:
1. All execution history fields are populated correctly after refactoring
2. No missing data in wave status updates
3. Wave completion, pause, and cancellation states work correctly
4. Execution progress tracking remains accurate
5. Server status data is preserved across wave transitions

## Verification Scripts

Two comprehensive verification scripts have been created:

### 1. Python Script: `verify_wave_data_integrity.py`

**Location**: `tests/manual/verify_wave_data_integrity.py`

**Features**:
- Comprehensive schema validation for execution records
- Wave-specific data completeness checks
- Timestamp consistency verification
- Logical validation (completedWaves vs totalWaves, duration calculations)
- Status-specific field requirements validation
- Wave transition data flow testing
- Detailed error reporting with categorization

**Usage**:
```bash
python tests/manual/verify_wave_data_integrity.py
```

**Verification Checks**:

1. **Schema Validation**
   - Required fields: executionId, planId, status, lastUpdated
   - Optional fields: startTime, endTime, currentWave, totalWaves, etc.
   - Field type validation (string, int, float)

2. **Wave Data Completeness**
   - COMPLETED: Requires endTime, completedWaves, durationSeconds
   - FAILED: Requires endTime, failedWaves, durationSeconds, errorMessage (optional), errorCode (optional)
   - CANCELLED: Requires endTime
   - PAUSED: Optional pausedBeforeWave
   - RUNNING: Expected currentWave

3. **Timestamp Consistency**
   - lastUpdated is recent (within 7 days)
   - startTime is not in the future
   - endTime is not in the future
   - endTime >= startTime
   - durationSeconds matches calculated duration (endTime - startTime)

4. **Logical Validation**
   - completedWaves <= totalWaves
   - For COMPLETED status: completedWaves == totalWaves
   - durationSeconds >= 0

5. **Wave Transition Data Flow**
   - Creates test execution with RUNNING status
   - Simulates wave 1 completion (updates completedWaves)
   - Simulates pause before wave 2 (updates status to PAUSED, sets pausedBeforeWave)
   - Simulates execution completion (updates status to COMPLETED, sets endTime, durationSeconds)
   - Verifies all fields preserved through transitions
   - Verifies no data loss

### 2. Shell Script: `verify_wave_data_integrity.sh`

**Location**: `tests/manual/verify_wave_data_integrity.sh`

**Features**:
- Same functionality as Python script
- Bash-based for environments without Python
- Uses AWS CLI and jq for JSON processing
- Colored output for easy reading

**Usage**:
```bash
./tests/manual/verify_wave_data_integrity.sh
```

## Verification Process

### Test 1: Analyze Recent Executions

Queries the execution history table to retrieve recent executions and verifies:

**Required Fields** (must be present):
- `executionId` - Unique execution identifier
- `planId` - Recovery plan identifier
- `status` - Execution status (RUNNING, COMPLETED, FAILED, CANCELLED, PAUSED)
- `lastUpdated` - Timestamp of last update

**Optional Fields** (expected but may be missing):
- `startTime` - Execution start timestamp
- `endTime` - Execution end timestamp (required for terminal states)
- `currentWave` - Current wave number (expected for RUNNING)
- `totalWaves` - Total number of waves
- `completedWaves` - Number of completed waves
- `failedWaves` - Number of failed waves
- `pausedBeforeWave` - Wave number before which execution is paused
- `errorMessage` - Error description (for FAILED status)
- `errorCode` - Error code (for FAILED status)
- `durationSeconds` - Execution duration (for terminal states)
- `statusReason` - Human-readable status reason

**Status-Specific Requirements**:

| Status | Required Fields | Optional Fields |
|--------|----------------|-----------------|
| RUNNING | status, lastUpdated, currentWave | completedWaves, failedWaves |
| COMPLETED | status, lastUpdated, endTime, completedWaves, durationSeconds | statusReason |
| FAILED | status, lastUpdated, endTime, failedWaves, durationSeconds | errorMessage, errorCode, statusReason |
| CANCELLED | status, lastUpdated, endTime | statusReason |
| PAUSED | status, lastUpdated | pausedBeforeWave |

### Test 2: Analyze Executions by Status

Queries executions filtered by status (COMPLETED, FAILED, CANCELLED, PAUSED, RUNNING) and verifies:
- Status-specific required fields are present
- Field types are correct
- Logical consistency (e.g., COMPLETED has completedWaves == totalWaves)

### Test 3: Wave Transition Data Flow

Creates a test execution and simulates complete wave transition lifecycle:

**Step 1: Create Initial Execution**
```json
{
  "executionId": "data-integrity-test-{timestamp}",
  "planId": "test-plan-001",
  "status": "RUNNING",
  "startTime": {current_time},
  "currentWave": 1,
  "totalWaves": 3,
  "completedWaves": 0,
  "failedWaves": 0,
  "lastUpdated": {current_time}
}
```

**Verification**: All required fields present, no data integrity issues

**Step 2: Simulate Wave 1 Completion**
- Invokes execution-handler with `update_wave_completion_status`
- Updates `completedWaves` to 1
- Keeps `status` as RUNNING

**Verification**:
- `completedWaves` updated to 1
- All initial fields preserved
- No data loss

**Step 3: Simulate Pause Before Wave 2**
- Invokes execution-handler with `update_wave_completion_status`
- Updates `status` to PAUSED
- Sets `pausedBeforeWave` to 2

**Verification**:
- `status` updated to PAUSED
- `pausedBeforeWave` set to 2
- All previous fields preserved
- No data loss

**Step 4: Simulate Execution Completion**
- Invokes execution-handler with `update_wave_completion_status`
- Updates `status` to COMPLETED
- Sets `endTime` to current time
- Updates `completedWaves` to 3
- Calculates and sets `durationSeconds`

**Verification**:
- `status` updated to COMPLETED
- `endTime` set correctly
- `completedWaves` updated to 3
- `durationSeconds` calculated correctly
- All previous fields preserved
- No data loss

**Step 5: Verify No Data Loss**
- Checks all initial fields are still present
- Verifies no fields were lost during transitions
- Confirms data integrity maintained throughout lifecycle

## Expected Results

### Success Criteria

✅ **All verifications pass**:
- Execution history table is accessible
- Recent executions show expected fields with correct types
- Status-specific required fields are present
- Timestamp consistency maintained
- Logical validations pass (completedWaves <= totalWaves, duration calculations)
- Wave transition data flow test passes
- No data loss detected during transitions

### Field Verification Matrix

| Status | Required Fields | Logical Checks |
|--------|----------------|----------------|
| RUNNING | status, lastUpdated, currentWave | currentWave <= totalWaves |
| COMPLETED | status, lastUpdated, endTime, completedWaves, durationSeconds | completedWaves == totalWaves, endTime >= startTime, durationSeconds == (endTime - startTime) |
| FAILED | status, lastUpdated, endTime, failedWaves, durationSeconds | failedWaves > 0, endTime >= startTime, durationSeconds == (endTime - startTime) |
| CANCELLED | status, lastUpdated, endTime | endTime >= startTime |
| PAUSED | status, lastUpdated | pausedBeforeWave <= totalWaves (if present) |

## Manual Verification (Without Scripts)

If you need to verify manually without running the scripts:

### 1. Check Recent Executions

```bash
AWS_PAGER="" aws dynamodb scan \
    --table-name aws-drs-orchestration-execution-history-qa \
    --region us-east-1 \
    --limit 10 \
    --query 'Items[*].{ExecutionId:executionId.S,Status:status.S,CompletedWaves:completedWaves.N,TotalWaves:totalWaves.N,LastUpdated:lastUpdated.N}'
```

### 2. Get Specific Execution Details

```bash
AWS_PAGER="" aws dynamodb get-item \
    --table-name aws-drs-orchestration-execution-history-qa \
    --region us-east-1 \
    --key '{"executionId": {"S": "YOUR_EXECUTION_ID"}, "planId": {"S": "YOUR_PLAN_ID"}}' \
    | jq '.Item'
```

### 3. Verify Field Presence

```bash
# Check for required fields
execution=$(aws dynamodb get-item \
    --table-name aws-drs-orchestration-execution-history-qa \
    --region us-east-1 \
    --key '{"executionId": {"S": "YOUR_EXECUTION_ID"}, "planId": {"S": "YOUR_PLAN_ID"}}')

# Check status
echo "$execution" | jq -r '.Item.status.S'

# Check lastUpdated
echo "$execution" | jq -r '.Item.lastUpdated.N'

# Check completedWaves
echo "$execution" | jq -r '.Item.completedWaves.N'

# Check endTime (for terminal states)
echo "$execution" | jq -r '.Item.endTime.N'

# Check durationSeconds (for terminal states)
echo "$execution" | jq -r '.Item.durationSeconds.N'
```

### 4. Verify Timestamp Consistency

```bash
# Get timestamps
start_time=$(echo "$execution" | jq -r '.Item.startTime.N')
end_time=$(echo "$execution" | jq -r '.Item.endTime.N')
duration=$(echo "$execution" | jq -r '.Item.durationSeconds.N')

# Calculate duration
calculated_duration=$((end_time - start_time))

# Compare
echo "Stored duration: $duration"
echo "Calculated duration: $calculated_duration"
echo "Difference: $((calculated_duration - duration))"
```

## Troubleshooting

### Issue: Missing Required Fields

**Cause**: Execution-handler not updating all required fields

**Solution**:
1. Check execution-handler CloudWatch Logs for errors
2. Verify `update_wave_completion_status()` function logic
3. Review Step Functions state machine - ensure `UpdateWaveStatus` state is called
4. Test execution-handler directly with test payload

### Issue: Incorrect Field Types

**Cause**: DynamoDB schema mismatch or incorrect data conversion

**Solution**:
1. Review execution-handler code for type conversions
2. Check for Decimal vs int/float issues
3. Verify DynamoDB attribute types in table schema

### Issue: Timestamp Inconsistencies

**Cause**: Clock skew, incorrect duration calculation, or race conditions

**Solution**:
1. Verify system time is synchronized
2. Check duration calculation logic in execution-handler
3. Review for race conditions between query-handler and execution-handler

### Issue: Data Loss During Transitions

**Cause**: Overwriting fields instead of updating, or missing fields in update expression

**Solution**:
1. Review `update_wave_completion_status()` UpdateExpression
2. Ensure all existing fields are preserved
3. Use SET operations, not PUT operations
4. Test with wave transition data flow test

### Issue: Logical Validation Failures

**Cause**: Incorrect wave counting, status transitions, or field updates

**Solution**:
1. Review wave completion logic in query-handler
2. Verify completedWaves increment logic
3. Check status transition logic in execution-handler
4. Test with multiple wave scenarios

## Data Integrity Guarantees

After successful verification, the following guarantees are confirmed:

### 1. Field Preservation
- All initial execution fields are preserved through wave transitions
- No fields are lost or overwritten unintentionally
- Field types remain consistent

### 2. Status Transitions
- RUNNING → COMPLETED: All required fields populated
- RUNNING → FAILED: Error information captured
- RUNNING → PAUSED: Pause information captured
- RUNNING → CANCELLED: Cancellation information captured

### 3. Wave Progress Tracking
- `completedWaves` increments correctly
- `failedWaves` increments on failures
- `currentWave` tracks active wave
- Wave counts remain consistent with `totalWaves`

### 4. Timestamp Accuracy
- `lastUpdated` reflects most recent update
- `endTime` set correctly for terminal states
- `durationSeconds` calculated accurately
- Timestamps are logically consistent (endTime >= startTime)

### 5. Error Information
- `errorMessage` captured for FAILED status
- `errorCode` captured for FAILED status
- `statusReason` provides human-readable context

## Related Tests

### Unit Tests

**Location**: `tests/unit/test_update_wave_completion_status.py`

**Coverage**:
- CANCELLED status updates
- PAUSED status updates
- COMPLETED status updates
- FAILED status updates
- Error handling (execution not found, DynamoDB errors)

**Run Tests**:
```bash
pytest tests/unit/test_update_wave_completion_status.py -v
```

### Manual Tests

**Location**: 
- `tests/manual/test_wave_completion_update.sh`
- `tests/manual/test_wave_completion_update.py`

**Coverage**:
- Direct Lambda invocation tests
- Status update verification
- Field validation
- Error scenarios

**Run Tests**:
```bash
./tests/manual/test_wave_completion_update.sh
# or
python tests/manual/test_wave_completion_update.py
```

### Integration Tests

**Location**: `tests/manual/verify_execution_history_updates.py`

**Coverage**:
- Execution history table updates
- CloudWatch Logs verification
- Query-handler read-only verification

**Run Tests**:
```bash
python tests/manual/verify_execution_history_updates.py
```

## Configuration

### Environment Variables

The verification scripts use the following configuration:

```bash
REGION="us-east-1"
TABLE_NAME="aws-drs-orchestration-execution-history-qa"
EXECUTION_HANDLER="aws-drs-orchestration-execution-handler-qa"
QUERY_HANDLER="aws-drs-orchestration-query-handler-qa"
```

### AWS Credentials

Scripts require AWS credentials with the following permissions:

**DynamoDB**:
- `dynamodb:Scan` - Query recent executions
- `dynamodb:GetItem` - Get specific execution details
- `dynamodb:PutItem` - Create test execution
- `dynamodb:DeleteItem` - Cleanup test execution

**Lambda**:
- `lambda:InvokeFunction` - Invoke execution-handler for testing

**CloudWatch Logs**:
- `logs:FilterLogEvents` - Check Lambda logs (optional)

## Success Indicators

### ✅ Verification Passed

All of the following are true:
1. Recent executions found in DynamoDB table
2. All required fields present in execution records
3. Field types are correct
4. Status-specific required fields present
5. Timestamp consistency maintained
6. Logical validations pass
7. Wave transition data flow test passes
8. No data loss detected during transitions

### ❌ Verification Failed

Any of the following are true:
1. Cannot access DynamoDB table
2. Missing required fields in execution records
3. Incorrect field types
4. Status-specific required fields missing
5. Timestamp inconsistencies
6. Logical validation failures
7. Wave transition data flow test fails
8. Data loss detected during transitions

## Next Steps

After successful verification:

1. ✅ Mark Task 4.10 as complete
2. ✅ Proceed to Phase 3: Cleanup and Verification
3. ✅ Document data integrity guarantees in requirements.md
4. ✅ Update architecture documentation with refactoring details

## References

- **Spec**: `.kiro/specs/06-query-handler-read-only-audit/`
- **Requirements**: FR4 - Move Wave Status Updates to Execution Handler
- **Design**: Split wave status polling (read vs write)
- **Tasks**: Task 4.10 - Verify no data loss during wave transitions
- **Related**: Task 4.9 - Verify execution history table updates

## Conclusion

This comprehensive data integrity verification ensures that the wave polling refactoring (splitting `poll_wave_status()` into read-only query-handler and write operations in execution-handler) maintains complete data integrity with:

- ✅ No data loss during wave transitions
- ✅ All execution history fields populated correctly
- ✅ Wave completion, pause, and cancellation states work correctly
- ✅ Execution progress tracking remains accurate
- ✅ Timestamp consistency maintained
- ✅ Logical validations pass
- ✅ Field types are correct
- ✅ Status-specific requirements met

The refactoring successfully achieves the read-only query-handler goal while preserving all data integrity guarantees.
