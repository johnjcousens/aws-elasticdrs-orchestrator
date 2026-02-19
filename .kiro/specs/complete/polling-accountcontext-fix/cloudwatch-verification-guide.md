# CloudWatch Log Verification Guide

## Current Situation

**Current AWS Account**: 160885257264 (Source account)  
**Target AWS Account**: 891376951562 (Test environment account)  
**Lambda Function**: `hrp-drs-tech-adapter-execution-handler-dev`  
**Log Group**: `/aws/lambda/hrp-drs-tech-adapter-execution-handler-dev`

## Account Switch Required

The CloudWatch logs for the test environment Lambda function are in account **891376951562**, but we're currently authenticated to account **160885257264**. You need to switch AWS accounts to view the logs.

## Option 1: Switch AWS Account (Recommended)

### Step 1: Switch to Account 891376951562

Use AWS SSO or your preferred method to switch to account 891376951562:

```bash
# If using AWS SSO
aws sso login --profile <profile-for-891376951562>

# Set the profile
export AWS_PROFILE=<profile-for-891376951562>

# Verify you're in the correct account
aws sts get-caller-identity
# Should show: "Account": "891376951562"
```

### Step 2: Tail CloudWatch Logs

Once authenticated to the correct account:

```bash
AWS_PAGER="" aws logs tail /aws/lambda/hrp-drs-tech-adapter-execution-handler-dev --follow
```

### Step 3: What to Look For

**✅ SUCCESS INDICATORS:**

1. **Account Context Usage**:
   ```
   Using account context for polling: accountId=160885257264, isCurrentAccount=False
   ```

2. **Cross-Account DRS Client Creation**:
   ```
   Created cross-account DRS client for region us-east-1
   ```

3. **Successful DRS Queries**:
   ```
   Reconciling wave status with real-time DRS data
   Successfully queried DRS job status
   ```

**❌ ERROR INDICATORS (Should NOT appear):**

1. **Role Assumption Failure**:
   ```
   Failed to assume role None: Parameter validation failed
   ```

2. **Missing Account Context**:
   ```
   Error polling wave: Parameter validation failed
   ```

## Option 2: Use AWS Console

If you prefer using the AWS Console:

1. **Switch to Account 891376951562** in the AWS Console
2. Navigate to **CloudWatch** → **Logs** → **Log groups**
3. Find log group: `/aws/lambda/hrp-drs-tech-adapter-execution-handler-dev`
4. Click on the most recent log stream
5. Enable **Auto-refresh** to see real-time logs
6. Look for the success/error indicators listed above

## Option 3: Trigger a Test Execution

To generate fresh logs for verification:

### Step 1: Start a Recovery Drill

Using the frontend or API, start a recovery drill with cross-account servers:

```bash
# Example: Start TargetAccountOnly drill
curl -X POST https://cbpdf7d52d.execute-api.us-east-2.amazonaws.com/dev/executions \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "planId": "c5621161-98af-41ed-8e06-652cd3f88152",
    "executionType": "DRILL"
  }'
```

### Step 2: Poll for Status

The frontend will automatically poll for status updates. Watch the CloudWatch logs during polling.

### Step 3: Verify Logs

Look for the success indicators mentioned above in the CloudWatch logs.

## Verification Checklist

- [ ] Switched to AWS account 891376951562
- [ ] Verified account with `aws sts get-caller-identity`
- [ ] Started tailing CloudWatch logs
- [ ] Triggered a recovery drill (or waited for existing execution to poll)
- [ ] Observed "Using account context for polling" message
- [ ] Confirmed no "Failed to assume role None" errors
- [ ] Verified DRS queries succeeded
- [ ] Checked that server statuses updated in the UI

## Expected Log Flow

When polling occurs, you should see this sequence:

```
1. GET /executions/{executionId}?realtime=true
2. Reconciling wave status with real-time DRS data
3. Using account context for polling: accountId=160885257264, isCurrentAccount=False
4. Created cross-account DRS client for region us-east-1
5. Querying DRS for job status: drsjob-xxxxx
6. Successfully retrieved DRS job status
7. Updated server status: PENDING → LAUNCHED
```

## Troubleshooting

### Can't Access Account 891376951562

If you don't have access to account 891376951562:
- Contact your AWS administrator to request access
- Or ask someone with access to verify the logs for you

### Logs Not Appearing

If logs aren't appearing:
- Verify the Lambda function exists: `aws lambda get-function --function-name hrp-drs-tech-adapter-execution-handler-dev`
- Check if there are any active executions
- Trigger a new recovery drill to generate fresh logs

### Still Seeing Errors

If you still see "Failed to assume role None" errors after the fix:
- Verify the Lambda code was deployed successfully
- Check the Lambda function's LastModified timestamp
- Review the code change in `lambda/execution-handler/index.py` line 3671
- Ensure the execution record has `accountContext` field

## Next Steps

After verifying the logs:

1. **Mark task 3.3 as complete** if verification is successful
2. **Document any issues** if errors are still present
3. **Proceed to task 4.2** (Post-deployment verification) if all looks good

## Related Documentation

- [AWS Stack Protection Rules](../../../.kiro/rules/aws-stack-protection.md)
- [Polling AccountContext Fix Design](design.md)
- [Polling AccountContext Fix Requirements](requirements.md)
