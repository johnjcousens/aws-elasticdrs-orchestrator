# Orchestration Fix Plan

## Key Finding
✅ **The orchestration Lambda logic is identical** between working archive and current implementation.
❌ **The issue is in the integration layer** - Step Functions, EventBridge, or DRS permissions.

## Root Cause Analysis

Based on local testing, both implementations produce identical state objects:
- Same function signatures
- Same state management logic  
- Same error handling patterns
- Same DRS integration code

**Conclusion**: The problem is NOT in the Lambda code itself.

## Most Likely Issues (In Priority Order)

### 1. Step Functions State Machine Issues
- **Symptom**: Execution stuck in "Polling" with "Unknown" wave status
- **Cause**: Step Functions may not be transitioning states correctly
- **Check**: CloudWatch Logs for Step Functions execution history
- **Fix**: Verify state machine definition matches working archive exactly

### 2. DRS API Permissions
- **Symptom**: DRS jobs not being created or failing silently
- **Cause**: Lambda execution role missing DRS permissions
- **Check**: CloudWatch Logs for DRS API errors
- **Fix**: Ensure orchestration role has all required DRS permissions

### 3. EventBridge Polling Not Working
- **Symptom**: Executions never progress beyond initial state
- **Cause**: execution-finder not running or execution-poller not being invoked
- **Check**: EventBridge rule status and Lambda invocation logs
- **Fix**: Verify EventBridge rules are enabled and targeting correct functions

### 4. Environment Variable Mismatch
- **Symptom**: Lambda functions can't access DynamoDB tables
- **Cause**: Table names or ARNs not matching between stacks
- **Check**: Lambda environment variables vs actual table names
- **Fix**: Ensure all environment variables are correctly passed from CloudFormation

## Immediate Action Plan

### Phase 1: Verify Integration (No Code Changes)
1. **Check Step Functions Execution**:
   ```bash
   # Look for the stuck execution in Step Functions console
   # Check execution history and state transitions
   # Verify if update_wave_status is being called
   ```

2. **Check DRS Permissions**:
   ```bash
   # Test DRS API access from orchestration Lambda role
   # Verify all required DRS permissions are granted
   # Check for any permission denied errors in logs
   ```

3. **Check EventBridge Rules**:
   ```bash
   # Verify execution-finder rule is enabled
   # Check if execution-poller is being invoked
   # Look for any EventBridge errors
   ```

### Phase 2: Deploy and Test (If Integration Issues Found)
1. **Deploy Current Code** (since logic is identical):
   ```bash
   ./scripts/check-deployment-scope.sh
   ./scripts/safe-push.sh
   ```

2. **Test with Simple Execution**:
   - Create a new execution with the same recovery plan
   - Monitor Step Functions execution in real-time
   - Check CloudWatch Logs for all components

3. **Compare with Working Archive Deployment**:
   - If still failing, compare deployed resources with working archive
   - Check for any missing IAM permissions or environment variables

## Testing Strategy

### Local Testing (Already Done ✅)
- Confirmed orchestration logic is identical
- Both implementations handle state the same way
- No code-level differences found

### Integration Testing (Next Step)
- Focus on Step Functions state transitions
- Verify DRS API connectivity and permissions
- Test EventBridge polling mechanism

### End-to-End Testing
- Deploy and test with the same recovery plan that worked on Jan 7th
- Monitor all components in real-time
- Identify exactly where the execution gets stuck

## Success Criteria

1. **Step Functions Execution**: Should progress through all states without getting stuck
2. **DRS Job Creation**: Should successfully create DRS jobs and get job IDs
3. **Wave Status Updates**: Should transition from "Polling" to "Launching" to "Completed"
4. **Recovery Instances**: Should successfully launch EC2 instances

## Rollback Plan

If the current implementation still fails after fixing integration issues:
1. Keep the refactored Lambda structure (it's better organized)
2. Copy the exact working logic from archive (though it should be identical)
3. Focus on CloudFormation template differences
4. Compare IAM roles and permissions exactly

## Next Steps

1. **Deploy current code** (since orchestration logic is correct)
2. **Monitor Step Functions execution** in real-time
3. **Check CloudWatch Logs** for all Lambda functions
4. **Verify DRS permissions** and API connectivity
5. **Test with the same recovery plan** that worked on Jan 7th

The refactored structure should work - we just need to ensure the integration layer is properly configured.