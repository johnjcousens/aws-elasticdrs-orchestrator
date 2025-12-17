# Drill Debugging Checklist

## Quick Validation Commands

### 1. Test Current Drill Status
```bash
# Check if API is responding
curl -H "Authorization: Bearer $TOKEN" \
  https://api-endpoint/health

# List current executions
curl -H "Authorization: Bearer $TOKEN" \
  https://api-endpoint/executions
```

### 2. Check Account Context
```bash
# Get target accounts
curl -H "Authorization: Bearer $TOKEN" \
  https://api-endpoint/accounts/targets

# Check current account detection
aws sts get-caller-identity
```

### 3. Validate DRS Setup
```bash
# Check DRS initialization
AWS_PAGER="" aws drs describe-source-servers --region us-east-1

# Check DRS quotas
curl -H "Authorization: Bearer $TOKEN" \
  "https://api-endpoint/drs/quotas?region=us-east-1"
```

### 4. Test Protection Group Resolution
```bash
# List protection groups
curl -H "Authorization: Bearer $TOKEN" \
  https://api-endpoint/protection-groups

# Test tag resolution (if using tag-based)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://api-endpoint/protection-groups/resolve-tags \
  -d '{"Region": "us-east-1", "SelectionTags": {"Environment": "test"}}'
```

### 5. Test Drill Execution
```bash
# Execute drill
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://api-endpoint/recovery-plans/{planId}/execute \
  -d '{"ExecutionType": "DRILL", "InitiatedBy": "debug-test"}'
```

## CloudWatch Logs Investigation

### API Handler Logs
```bash
# Get recent API logs
AWS_PAGER="" aws logs tail /aws/lambda/drs-orchestration-api-handler-test \
  --since 10m --region us-east-1
```

### Step Functions Logs
```bash
# Get orchestration logs
AWS_PAGER="" aws logs tail /aws/lambda/drs-orchestration-orchestration-stepfunctions-test \
  --since 10m --region us-east-1
```

### Step Functions Execution
```bash
# List recent executions
AWS_PAGER="" aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:account:stateMachine:drs-orchestration-test \
  --status-filter FAILED --max-results 5 --region us-east-1
```

## Common Issues and Fixes

### Issue 1: Account Context Blocking
**Symptom**: Drill buttons grayed out, "Account required" messages
**Check**:
```javascript
// In browser console on Recovery Plans page
console.log(localStorage.getItem('selectedAccountId'));
console.log(window.accountContext);
```
**Fix**: Ensure account is selected in top navigation dropdown

### Issue 2: Server Conflicts
**Symptom**: "SERVER_CONFLICT" error when starting drill
**Check**: Look for other active executions using same servers
**Fix**: Wait for other executions to complete or use different servers

### Issue 3: DRS Service Limits
**Symptom**: "CONCURRENT_JOBS_LIMIT_EXCEEDED" or similar quota errors
**Check**: 
```bash
# Check active DRS jobs
AWS_PAGER="" aws drs describe-jobs --region us-east-1
```
**Fix**: Wait for jobs to complete or increase quotas

### Issue 4: Tag Resolution Failure
**Symptom**: Tag-based Protection Groups show no servers
**Check**: Verify DRS source servers have the expected tags
**Fix**: Add tags to DRS source servers or use manual selection

### Issue 5: Step Functions Timeout
**Symptom**: Executions stuck in POLLING status
**Check**: Step Functions execution history
**Fix**: Check DRS job status and server launch progress

## Frontend Debugging

### Browser Console Checks
```javascript
// Check account context
console.log('Account Context:', window.accountContext);

// Check API responses
// Open Network tab and look for failed API calls

// Check for JavaScript errors
// Open Console tab and look for red error messages
```

### Local Storage Inspection
```javascript
// Check stored account
localStorage.getItem('selectedAccountId');

// Check auth tokens
localStorage.getItem('amplify-signin-with-hostedUI');
```

## Step-by-Step Drill Test

### 1. Create Test Protection Group
- Use manual server selection (not tags initially)
- Select 1-2 servers in CONTINUOUS replication state
- Verify servers are not in other active executions

### 2. Create Test Recovery Plan
- Single wave with the test Protection Group
- No pause before wave (for simplicity)
- Save and verify plan appears in list

### 3. Execute Drill
- Click "Run Drill" button
- Confirm any existing instance warnings
- Monitor execution status on Executions page

### 4. Monitor Progress
- Watch execution status change: PENDING → POLLING → LAUNCHING → COMPLETED
- Check Step Functions execution in AWS Console
- Verify DRS job creation and completion

### 5. Validate Results
- Confirm recovery instances are created
- Check instances are tagged as drill instances
- Verify instances can be terminated

## Error Code Reference

| Error Code | Meaning | Solution |
|------------|---------|----------|
| MISSING_FIELD | Required field missing | Check API request format |
| INVALID_EXECUTION_TYPE | Wrong execution type | Use "DRILL" or "RECOVERY" |
| RECOVERY_PLAN_NOT_FOUND | Plan doesn't exist | Verify plan ID |
| PLAN_HAS_NO_WAVES | Empty plan | Add waves to recovery plan |
| PLAN_ALREADY_EXECUTING | Duplicate execution | Wait for current execution to finish |
| SERVER_CONFLICT | Server in use | Use different servers or wait |
| WAVE_SIZE_LIMIT_EXCEEDED | Too many servers | Reduce servers per wave (max 100) |
| CONCURRENT_JOBS_LIMIT_EXCEEDED | Too many DRS jobs | Wait for jobs to complete |
| UNHEALTHY_SERVER_REPLICATION | Bad replication state | Fix server replication |

## Success Indicators

### ✅ Drill is Working When:
1. **UI**: Drill button is enabled and clickable
2. **API**: POST to execute endpoint returns 202 with execution ID
3. **Database**: Execution record created with PENDING status
4. **Step Functions**: State machine execution starts
5. **DRS**: Recovery job created with isDrill=true
6. **Instances**: EC2 recovery instances launch
7. **Status**: Execution status updates to COMPLETED
8. **Cleanup**: Instances can be terminated after drill

### ❌ Drill is Broken When:
1. **UI**: Buttons permanently grayed out
2. **API**: Execute endpoint returns 4xx/5xx errors
3. **Step Functions**: Executions fail immediately
4. **DRS**: No recovery jobs created
5. **Instances**: No recovery instances launch
6. **Status**: Executions stuck in PENDING/POLLING

## Emergency Rollback

If drill functionality is completely broken:

```bash
# 1. Identify last working commit
git log --oneline --grep="drill" --since="1 week ago"

# 2. Create rollback branch
git checkout -b emergency-drill-rollback

# 3. Revert problematic commits (example)
git revert --no-commit 905a682  # Multi-account changes
git revert --no-commit 5b0e6db  # EC2 instance type changes

# 4. Test rollback
# Deploy and test drill functionality

# 5. If working, create emergency deployment
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

## Contact Information

**For immediate assistance:**
- Check CloudWatch logs first
- Review Step Functions execution history
- Test with minimal configuration (1 server, 1 wave)
- Document exact error messages and steps to reproduce