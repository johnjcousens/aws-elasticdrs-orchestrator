# Step Functions Removal Plan

## Problem
The orchestration Lambda (`drs-orchestration-orchestration-test`) is misconfigured:
- CloudFormation expects handler: `drs_orchestrator.lambda_handler`
- Deployed code has: `index.py` with `lambda_handler` (API handler code)
- **Step Functions is NOT being used** - polling solution handles everything

## Current Working Architecture
```
User Request
    ↓
API Gateway → API Handler Lambda (index.py)
    ↓
execute_recovery_plan() → Creates PENDING execution in DynamoDB
    ↓
Async worker invocation → execute_recovery_plan_worker()
    ↓
initiate_wave() → Calls DRS start_recovery() API
    ↓
Status: POLLING
    ↓
EventBridge (every 60s) → ExecutionFinder Lambda
    ↓
Finds PENDING/POLLING executions via StatusIndex GSI
    ↓
Invokes ExecutionPoller Lambda for each active execution
    ↓
Polls DRS DescribeJobs API → Updates execution status
    ↓
Status: COMPLETED/FAILED
```

## Step Functions State Machine (UNUSED)
- Exists in CloudFormation: `drs-orchestration-orchestration-test`
- Has 3 states: InitializeExecution, ProcessWaves, FinalizeExecution
- Calls orchestration Lambda with `action` parameter
- **Never invoked** - API handler uses async worker pattern instead

## Solution: Remove Step Functions Dependency

### Option 1: Minimal Fix (Recommended)
**Keep Step Functions infrastructure but fix the Lambda**
- Update `orchestration.zip` to contain a stub that returns success
- Prevents CloudFormation errors if Step Functions is accidentally invoked
- No infrastructure changes needed
- Fast deployment

### Option 2: Complete Removal
**Remove Step Functions from CloudFormation**
- Delete Step Functions state machine from `api-stack.yaml`
- Delete orchestration Lambda from `lambda-stack.yaml`
- Update API handler to remove STATE_MACHINE_ARN reference
- Requires full stack update

## Recommendation: Option 1

**Why:**
- Polling solution is working perfectly (20s detection, 0% error rate)
- No need to touch working infrastructure
- Step Functions might be useful for future Phase 3 enhancements
- Minimal risk, fast fix

**Implementation:**
1. Create stub `drs_orchestrator.py` that returns success
2. Package as `orchestration.zip`
3. Upload to S3 bucket
4. Update Lambda function code
5. Test that it doesn't break anything

## Files to Modify

### 1. Create `lambda/drs_orchestrator.py` (stub)
```python
"""
AWS DRS Orchestration - Orchestration Lambda (Stub)
NOTE: This Lambda is not currently used. The polling solution handles all orchestration.
"""

def lambda_handler(event, context):
    """Stub handler - returns success"""
    print(f"Orchestration Lambda invoked (stub): {event}")
    return {
        'statusCode': 200,
        'message': 'Orchestration Lambda is not used - polling solution handles execution'
    }
```

### 2. Update `lambda/orchestration.zip`
- Package `drs_orchestrator.py` into zip
- Upload to `s3://aws-drs-orchestration/lambda/orchestration.zip`

### 3. Update Lambda function
```bash
aws lambda update-function-code \
  --function-name drs-orchestration-orchestration-test \
  --s3-bucket aws-drs-orchestration \
  --s3-key lambda/orchestration.zip \
  --region us-east-1
```

## Testing
1. Verify Lambda function updates successfully
2. Check CloudWatch Logs for any errors
3. Test drill execution end-to-end
4. Confirm polling solution continues working

## Future Considerations (Phase 3)
If we want to use Step Functions in the future:
- Implement proper state machine orchestration
- Add wave dependency handling in Step Functions
- Use Step Functions for complex workflows (pause/resume)
- Keep polling as fallback mechanism
