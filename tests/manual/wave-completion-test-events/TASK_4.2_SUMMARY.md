# Task 4.2 Summary: Wave Completion Status Update Testing

## What Was Done

### 1. Added Action Routing to Lambda Handler

Updated `lambda/execution-handler/index.py` to handle the `update_wave_completion_status` action:

```python
elif action == "update_wave_completion_status":
    # Extract parameters from event
    execution_id = event.get("execution_id")
    plan_id = event.get("plan_id")
    status = event.get("status")
    wave_data = event.get("wave_data")

    # Validate required parameters
    if not execution_id or not plan_id or not status:
        return response(
            400,
            {
                "error": "MISSING_PARAMETERS",
                "message": "execution_id, plan_id, and status are required",
            },
        )

    # Call update function
    return update_wave_completion_status(
        execution_id=execution_id,
        plan_id=plan_id,
        status=status,
        wave_data=wave_data,
    )
```

### 2. Created Test Events

Created 4 test event files for each status type:

1. **test-cancelled.json** - Tests CANCELLED status update
2. **test-paused.json** - Tests PAUSED status update with pausedBeforeWave
3. **test-completed.json** - Tests COMPLETED status update with wave data
4. **test-failed.json** - Tests FAILED status update with error details

### 3. Created Test Automation Script

Created `run-tests.sh` that:
- Creates a test execution record in DynamoDB
- Invokes the Lambda function with each test event
- Verifies the DynamoDB updates
- Displays the results
- Cleans up test data

## Test Event Format

All test events follow this structure:

```json
{
  "action": "update_wave_completion_status",
  "execution_id": "test-exec-001",
  "plan_id": "test-plan-001",
  "status": "CANCELLED|PAUSED|COMPLETED|FAILED",
  "wave_data": {
    // Status-specific data
  }
}
```

## Running the Tests

### Prerequisites

1. **AWS Authentication**: Ensure you're authenticated to AWS account 438465159935
   ```bash
   aws sts get-caller-identity --region us-east-1
   ```

2. **Lambda Function**: Execution-handler must be deployed
   ```bash
   aws lambda get-function \
     --function-name aws-drs-orchestration-execution-handler-qa \
     --region us-east-1
   ```

3. **DynamoDB Table**: Execution history table must exist
   ```bash
   aws dynamodb describe-table \
     --table-name aws-drs-orchestration-execution-history-qa \
     --region us-east-1
   ```

### Option 1: Run All Tests (Recommended)

```bash
cd tests/manual/wave-completion-test-events
./run-tests.sh
```

This will:
1. Create test execution record
2. Run all 4 tests sequentially
3. Verify each DynamoDB update
4. Clean up test data

### Option 2: Run Individual Tests

```bash
# Test CANCELLED status
aws lambda invoke \
  --function-name aws-drs-orchestration-execution-handler-qa \
  --region us-east-1 \
  --payload file://tests/manual/wave-completion-test-events/test-cancelled.json \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json | jq .
```

## Expected Results

### Test 1: CANCELLED Status
```json
{
  "statusCode": 200,
  "message": "Execution test-exec-001 status updated to CANCELLED"
}
```

DynamoDB record should have:
- `status` = "CANCELLED"
- `endTime` = current timestamp
- `lastUpdated` = current timestamp

### Test 2: PAUSED Status
```json
{
  "statusCode": 200,
  "message": "Execution test-exec-001 status updated to PAUSED"
}
```

DynamoDB record should have:
- `status` = "PAUSED"
- `pausedBeforeWave` = 2
- `lastUpdated` = current timestamp

### Test 3: COMPLETED Status
```json
{
  "statusCode": 200,
  "message": "Execution test-exec-001 status updated to COMPLETED"
}
```

DynamoDB record should have:
- `status` = "COMPLETED"
- `endTime` = current timestamp
- `completedWaves` = 3
- `durationSeconds` = calculated duration
- `lastUpdated` = current timestamp

### Test 4: FAILED Status
```json
{
  "statusCode": 200,
  "message": "Execution test-exec-001 status updated to FAILED"
}
```

DynamoDB record should have:
- `status` = "FAILED"
- `endTime` = current timestamp
- `failedWaves` = 2
- `errorMessage` = "DRS job failed: LAUNCH_FAILED"
- `errorCode` = "LAUNCH_FAILED"
- `durationSeconds` = calculated duration
- `lastUpdated` = current timestamp

## Verification

After running tests, verify the DynamoDB updates:

```bash
aws dynamodb get-item \
  --table-name aws-drs-orchestration-execution-history-qa \
  --region us-east-1 \
  --key '{"executionId": {"S": "test-exec-001"}, "planId": {"S": "test-plan-001"}}' \
  --output json | jq '.Item'
```

## Next Steps

Once tests pass:

1. **Deploy to QA**: Deploy the updated execution-handler
   ```bash
   ./scripts/deploy.sh qa --lambda-only
   ```

2. **Proceed to Task 4.3**: Refactor `poll_wave_status()` in query-handler to remove DynamoDB writes

3. **Update Step Functions**: Add UpdateWaveStatus state to call this function

## Troubleshooting

### Lambda Invocation Fails

Check Lambda logs:
```bash
aws logs tail /aws/lambda/aws-drs-orchestration-execution-handler-qa \
  --region us-east-1 \
  --since 5m \
  --follow
```

### DynamoDB Update Fails

Check if execution record exists:
```bash
aws dynamodb get-item \
  --table-name aws-drs-orchestration-execution-history-qa \
  --region us-east-1 \
  --key '{"executionId": {"S": "test-exec-001"}, "planId": {"S": "test-plan-001"}}'
```

### Authentication Expired

Re-authenticate:
```bash
aws login
```

## Files Created

- `tests/manual/wave-completion-test-events/README.md` - Detailed testing instructions
- `tests/manual/wave-completion-test-events/test-cancelled.json` - CANCELLED test event
- `tests/manual/wave-completion-test-events/test-paused.json` - PAUSED test event
- `tests/manual/wave-completion-test-events/test-completed.json` - COMPLETED test event
- `tests/manual/wave-completion-test-events/test-failed.json` - FAILED test event
- `tests/manual/wave-completion-test-events/run-tests.sh` - Automated test script
- `tests/manual/wave-completion-test-events/TASK_4.2_SUMMARY.md` - This file

## Implementation Details

The `update_wave_completion_status()` function (created in task 4.1) handles:

1. **Status Normalization**: Converts status to uppercase
2. **Timestamp Management**: Adds lastUpdated and endTime timestamps
3. **Status-Specific Logic**:
   - CANCELLED: Sets endTime
   - PAUSED: Sets pausedBeforeWave if provided
   - COMPLETED: Sets endTime, completedWaves, durationSeconds
   - FAILED: Sets endTime, failedWaves, errorMessage, errorCode, durationSeconds
4. **DynamoDB Update**: Uses conditional update to ensure execution exists
5. **Error Handling**: Returns 404 if execution not found, propagates other errors

## Success Criteria

✅ Lambda handler routes `update_wave_completion_status` action correctly
✅ All 4 status types update DynamoDB successfully
✅ Timestamps are set correctly
✅ Status-specific fields are populated
✅ Error handling works (404 for missing execution)
✅ Test automation script works end-to-end
