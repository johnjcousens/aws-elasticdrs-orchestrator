# Session 61 Validation Guide

## Overview
Validate custom tags (9 tags) and Cognito user attribution deployed in Session 61.

## Pre-Validation Checklist ✅
- [x] Lambda deployed: 2025-11-30T21:07:42Z
- [x] Function: drs-orchestration-api-handler-test
- [x] All 8 implementation steps complete
- [x] Launch configuration validation included

## Validation Workflow

### Step 1: Execute Test Drill via UI

1. Open frontend: https://d3l68i7nq9o48k.cloudfront.net
2. Navigate to Recovery Plans
3. Select a plan with configured servers
4. Click "Execute Drill"
5. Note the Execution ID (will be used for verification)

### Step 2: Monitor CloudWatch Logs

```bash
# Get latest log stream
aws logs describe-log-streams \
  --log-group-name /aws/lambda/drs-orchestration-api-handler-test \
  --order-by LastEventTime \
  --descending \
  --max-items 1 \
  --profile ***REMOVED***_AdministratorAccess

# View logs (replace STREAM_NAME)
aws logs get-log-events \
  --log-group-name /aws/lambda/drs-orchestration-api-handler-test \
  --log-stream-name "STREAM_NAME" \
  --profile ***REMOVED***_AdministratorAccess
```

**Look for:**
- ✅ `[Launch Config]` validation messages
- ✅ `[DRS API] Built custom tags:` showing 9 tags
- ✅ `Initiated by: user@amazon.com` showing Cognito email
- ✅ Job ID creation success

### Step 3: Verify EC2 Instance Tags

```bash
# List drill instances (replace EXECUTION_ID)
aws ec2 describe-instances \
  --filters "Name=tag:DRS:ExecutionId,Values=EXECUTION_ID" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,Tags]' \
  --profile ***REMOVED***_AdministratorAccess \
  --region us-east-1 \
  --output json | jq '.'

# Verify specific tag (replace EXECUTION_ID)
aws ec2 describe-tags \
  --filters "Name=resource-type,Values=instance" \
            "Name=tag:DRS:ExecutionId,Values=EXECUTION_ID" \
  --profile ***REMOVED***_AdministratorAccess \
  --region us-east-1 \
  --output table
```

### Step 4: Verify All 9 Tags Present

**Expected Tags:**
1. ✅ DRS:ExecutionId = "uuid-format"
2. ✅ DRS:ExecutionType = "DRILL"
3. ✅ DRS:PlanName = "Your-Plan-Name"
4. ✅ DRS:WaveName = "Wave 1"
5. ✅ DRS:WaveNumber = "1"
6. ✅ DRS:InitiatedBy = "user@amazon.com" ← **KEY VALIDATION**
7. ✅ DRS:UserId = "cognito-sub-uuid"
8. ✅ DRS:DrillId = "uuid-format"
9. ✅ DRS:Timestamp = "unix-timestamp"

### Step 5: Alternative - Use execute_drill.py Script

```bash
# Execute drill programmatically
python scripts/execute_drill.py \
  --plan-id "PLAN_UUID" \
  --execution-type DRILL \
  --initiated-by "test-validation"
```

Then follow Steps 2-4 to verify tags.

## Validation Checklist

### CloudWatch Logs Verification
- [ ] Launch config validation ran (no empty configs)
- [ ] Custom tags built (9 tags shown in logs)
- [ ] Cognito email extracted correctly
- [ ] DRS job created successfully

### EC2 Instance Verification
- [ ] Instances launched with DRS:ExecutionId tag
- [ ] All 9 tags present on instances
- [ ] DRS:InitiatedBy shows actual user email (not "system")
- [ ] Tag values match execution metadata

### Functional Verification
- [ ] Drill executed without launch config errors
- [ ] Tags enable drill instance tracking
- [ ] User attribution working correctly
- [ ] Launch validation prevents empty config failures

## Success Criteria

✅ **PASS** if:
- Drill completes successfully
- All 9 tags present on EC2 instances
- DRS:InitiatedBy shows user email (from Cognito)
- CloudWatch logs confirm tag application
- No launch configuration errors

❌ **FAIL** if:
- Launch configuration errors occur
- Tags missing or incomplete
- DRS:InitiatedBy shows "system" instead of email
- Drill fails to launch instances

## Troubleshooting

### If launch config error occurs:
- Check CloudWatch logs for `[Launch Config]` messages
- Verify server launch configs manually:
  ```bash
  aws drs get-launch-configuration --source-server-id s-xxxxx
  ```

### If tags missing:
- Verify Lambda deployment timestamp matches latest
- Check CloudWatch logs for tag building step
- Confirm DRS API call succeeded

### If wrong user attribution:
- Verify Cognito token in API Gateway request
- Check `get_cognito_user_from_event()` extraction
- Confirm authorizer claims present

## Next Steps After Validation

1. Document validation results
2. Update SESSION_61_VALIDATION_RESULTS.md
3. Mark Session 61 as fully validated ✅
4. Proceed with operational use

