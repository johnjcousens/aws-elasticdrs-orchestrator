# Wave Completion Status Update Test Events

This directory contains test events for testing the `update_wave_completion_status()` function in execution-handler via direct Lambda invocation.

## Purpose

These test events verify that the wave completion status update functionality (created in task 4.1) works correctly for all 4 status types:
- CANCELLED
- PAUSED
- COMPLETED
- FAILED

## Prerequisites

1. AWS CLI configured with credentials for account 438465159935
2. Execution-handler Lambda function deployed: `aws-drs-orchestration-execution-handler-qa`
3. An existing execution record in DynamoDB table: `aws-drs-orchestration-execution-history-qa`

## Creating a Test Execution

If you need to create a test execution record for testing:

```bash
# Create a test execution record
aws dynamodb put-item \
  --table-name aws-drs-orchestration-execution-history-qa \
  --region us-east-1 \
  --item '{
    "executionId": {"S": "test-exec-001"},
    "planId": {"S": "test-plan-001"},
    "status": {"S": "RUNNING"},
    "startTime": {"N": "'"$(date +%s)"'"},
    "lastUpdated": {"N": "'"$(date +%s)"'"}
  }'
```

## Running Tests

### Test 1: CANCELLED Status

```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-execution-handler-qa \
  --region us-east-1 \
  --payload file://tests/manual/wave-completion-test-events/test-cancelled.json \
  --cli-binary-format raw-in-base64-out \
  response-cancelled.json

cat response-cancelled.json | jq .
```

### Test 2: PAUSED Status

```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-execution-handler-qa \
  --region us-east-1 \
  --payload file://tests/manual/wave-completion-test-events/test-paused.json \
  --cli-binary-format raw-in-base64-out \
  response-paused.json

cat response-paused.json | jq .
```

### Test 3: COMPLETED Status

```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-execution-handler-qa \
  --region us-east-1 \
  --payload file://tests/manual/wave-completion-test-events/test-completed.json \
  --cli-binary-format raw-in-base64-out \
  response-completed.json

cat response-completed.json | jq .
```

### Test 4: FAILED Status

```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-execution-handler-qa \
  --region us-east-1 \
  --payload file://tests/manual/wave-completion-test-events/test-failed.json \
  --cli-binary-format raw-in-base64-out \
  response-failed.json

cat response-failed.json | jq .
```

## Verifying Results

After each test, verify the DynamoDB update:

```bash
aws dynamodb get-item \
  --table-name aws-drs-orchestration-execution-history-qa \
  --region us-east-1 \
  --key '{"executionId": {"S": "test-exec-001"}, "planId": {"S": "test-plan-001"}}' \
  --query 'Item.[status.S, lastUpdated.N, endTime.N, pausedBeforeWave.N, completedWaves.N, failedWaves.N, errorMessage.S]' \
  --output table
```

## Expected Results

### CANCELLED Status
- `status` = "CANCELLED"
- `endTime` = current timestamp
- `lastUpdated` = current timestamp

### PAUSED Status
- `status` = "PAUSED"
- `pausedBeforeWave` = 2 (from test event)
- `lastUpdated` = current timestamp

### COMPLETED Status
- `status` = "COMPLETED"
- `endTime` = current timestamp
- `completedWaves` = 3 (from test event)
- `durationSeconds` = calculated duration
- `lastUpdated` = current timestamp

### FAILED Status
- `status` = "FAILED"
- `endTime` = current timestamp
- `failedWaves` = 2 (from test event)
- `errorMessage` = "DRS job failed: LAUNCH_FAILED"
- `errorCode` = "LAUNCH_FAILED"
- `durationSeconds` = calculated duration
- `lastUpdated` = current timestamp

## Cleanup

After testing, delete the test execution record:

```bash
aws dynamodb delete-item \
  --table-name aws-drs-orchestration-execution-history-qa \
  --region us-east-1 \
  --key '{"executionId": {"S": "test-exec-001"}, "planId": {"S": "test-plan-001"}}'
```
