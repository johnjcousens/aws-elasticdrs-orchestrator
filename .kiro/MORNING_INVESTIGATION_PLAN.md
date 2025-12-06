# Morning Investigation Plan - Lambda Drill Mystery

**Date**: December 1, 2025 (Morning)
**Prepared**: November 30, 2025 (Night)
**Status**: Ready to Execute

---

## 🎯 The Mystery

**Problem**: Lambda-triggered drills don't create EC2 recovery instances, but CLI script does

**What We Know**:
- ✅ Both use `isDrill=True`
- ✅ Both use identical API call structure
- ✅ Both jobs reach COMPLETED/LAUNCHED status
- ✅ Code is identical (verified)
- ❓ Why different behavior?

---

## 📋 Investigation Checklist

### Step 1: Get Job IDs ⏱️ 5 minutes

**Lambda Job** (from recent execution):
```bash
# Check CloudWatch logs for recent job ID
aws logs tail /aws/lambda/drs-orchestration-api-handler-test \
  --since 24h --format short --region us-east-1 | grep "jobID"
```

**CLI Job** (user should provide or run new drill):
```bash
# Run CLI drill to get fresh job ID
cd scripts
python3 execute_drill.py
# Note the job ID from output
```

### Step 2: Compare Job Details ⏱️ 10 minutes

**Get Lambda Job Details**:
```bash
aws drs describe-jobs \
  --filters jobIDs=<lambda-job-id> \
  --region us-east-1 \
  --output json > lambda-job.json
```

**Get CLI Job Details**:
```bash
aws drs describe-jobs \
  --filters jobIDs=<cli-job-id> \
  --region us-east-1 \
  --output json > cli-job.json
```

**Compare Side-by-Side**:
```bash
# Check for differences
diff lambda-job.json cli-job.json
```

**Key Fields to Check**:
- [ ] `status` - Should both be COMPLETED
- [ ] `participatingServers[].launchStatus` - Should both be LAUNCHED
- [ ] `participatingServers[].recoveryInstanceID` - **CRITICAL**: Does Lambda have this?
- [ ] `type` - Should both be LAUNCH
- [ ] `initiatedBy` - Different but shouldn't matter
- [ ] `tags` - Lambda has 9, CLI has 5

### Step 3: Check Recovery Instances ⏱️ 5 minutes

**List All Recovery Instances**:
```bash
aws drs describe-recovery-instances \
  --region us-east-1 \
  --output json > recovery-instances.json
```

**Filter by Test Server**:
```bash
aws drs describe-recovery-instances \
  --filters sourceServerIDs=s-3c63bb8be30d7d071 \
  --region us-east-1 \
  --output json
```

**Check**:
- [ ] Does CLI job have recovery instances?
- [ ] Does Lambda job have recovery instances?
- [ ] What's the `isDrill` flag for each?
- [ ] What's the `ec2InstanceState` for each?

### Step 4: Verify Launch Configuration ⏱️ 5 minutes

**Get Launch Configuration**:
```bash
aws drs get-launch-configuration \
  --source-server-id s-3c63bb8be30d7d071 \
  --region us-east-1 \
  --output json > launch-config.json
```

**Check**:
- [ ] Is `launchIntoInstanceProperties` empty? (Session 61 should have fixed)
- [ ] What's the `launchDisposition`? (Should be STARTED)
- [ ] What's the `targetInstanceTypeRightSizingMethod`?
- [ ] Any other configuration issues?

### Step 5: Check Source Server State ⏱️ 5 minutes

**Get Server Details**:
```bash
aws drs describe-source-servers \
  --filters sourceServerIDs=s-3c63bb8be30d7d071 \
  --region us-east-1 \
  --output json > source-server.json
```

**Check**:
- [ ] `dataReplicationInfo.dataReplicationState` - Should be CONTINUOUS
- [ ] `lifeCycle.state` - Should be READY_FOR_RECOVERY
- [ ] `dataReplicationInfo.lagDuration` - Should be reasonable
- [ ] Any warnings or issues?

### Step 6: Compare IAM Permissions ⏱️ 10 minutes

**Get Lambda Role**:
```bash
# Find the role name
aws lambda get-function \
  --function-name drs-orchestration-api-handler-test \
  --region us-east-1 \
  --query 'Configuration.Role' \
  --output text

# Get role policies
aws iam get-role --role-name <role-name> --output json > lambda-role.json
aws iam list-attached-role-policies --role-name <role-name> --output json
aws iam list-role-policies --role-name <role-name> --output json
```

**Get CLI Credentials**:
```bash
# Check what credentials CLI is using
aws sts get-caller-identity --output json
```

**Compare**:
- [ ] Does Lambda have all EC2 permissions? (Session 58 added 14)
- [ ] Does Lambda have DRS permissions?
- [ ] Any permission gaps?

### Step 7: Check for Active Operations ⏱️ 5 minutes

**Check for Conflicts**:
```bash
# Get recent jobs (last 24 hours)
aws drs describe-jobs \
  --filters fromDate=$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ) \
  --region us-east-1 \
  --output json > recent-jobs.json
```

**Check**:
- [ ] Any PENDING or STARTED jobs when Lambda ran?
- [ ] Could ConflictException have occurred?
- [ ] Any pattern of failures?

---

## 🔍 Expected Findings

### Scenario 1: Missing `recoveryInstanceID`

**If Lambda job has NO `recoveryInstanceID`**:
- ❌ Instance creation failed silently
- ✅ This explains why no EC2 instances
- 🔍 Need to find WHY it failed

**Possible Causes**:
1. Launch configuration still empty (Session 61 fix didn't work)
2. IAM permission missing (subtle one we didn't catch)
3. DRS quota/limit hit
4. ConflictException during launch phase

### Scenario 2: Different Job Types

**If jobs have different `type` or `initiatedBy`**:
- Could indicate Lambda is doing something different
- Check if Lambda is actually calling `start_recovery` correctly

### Scenario 3: Tag Impact

**If 9 tags vs 5 tags matters**:
- Test Lambda with only 5 tags
- Deploy and re-test

### Scenario 4: Timing Issue

**If Lambda runs too fast**:
- Server might not be in CONTINUOUS state
- Add pre-validation check

---

## 🛠️ Quick Fixes to Try

### Fix 1: Reduce Tags (5 minutes)

If tag count matters, modify Lambda to use only 5 tags:

```python
# In lambda/index.py, replace 9 tags with 5
tags = {
    'DRS:ExecutionId': execution_id,
    'DRS:ExecutionType': execution_type,
    'DRS:PlanName': plan_name or 'Unknown',
    'DRS:InitiatedBy': cognito_user.get('email', 'system') if cognito_user else 'system',
    'DRS:Timestamp': datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
}
```

Deploy with fast method:
```bash
./scripts/sync-to-deployment-bucket.sh --update-lambda-code
```

### Fix 2: Add Pre-Validation (10 minutes)

Add server state check before starting drill:

```python
# Before start_recovery call
servers = drs_client.describe_source_servers(
    filters={'sourceServerIDs': server_ids}
)

for server in servers['items']:
    rep_state = server['dataReplicationInfo']['dataReplicationState']
    life_state = server['lifeCycle']['state']
    
    if rep_state != 'CONTINUOUS':
        raise Exception(f"Server not ready: {rep_state}")
    if life_state != 'READY_FOR_RECOVERY':
        raise Exception(f"Server not ready: {life_state}")
```

### Fix 3: Check Launch Config (5 minutes)

Verify launch config is not empty:

```python
# Before start_recovery call
launch_config = drs_client.get_launch_configuration(
    sourceServerId=server_id
)

if not launch_config.get('launchIntoInstanceProperties'):
    # Update with minimal config
    drs_client.update_launch_configuration(
        sourceServerId=server_id,
        launchIntoInstanceProperties={}
    )
```

---

## 📊 Data Collection Commands

**Save all outputs for analysis**:

```bash
# Create investigation directory
mkdir -p investigation/$(date +%Y%m%d)
cd investigation/$(date +%Y%m%d)

# Collect all data
aws drs describe-jobs --filters fromDate=$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ) --region us-east-1 > jobs.json
aws drs describe-recovery-instances --region us-east-1 > instances.json
aws drs describe-source-servers --filters sourceServerIDs=s-3c63bb8be30d7d071 --region us-east-1 > server.json
aws drs get-launch-configuration --source-server-id s-3c63bb8be30d7d071 --region us-east-1 > launch-config.json
aws lambda get-function --function-name drs-orchestration-api-handler-test --region us-east-1 > lambda-function.json

# Get CloudWatch logs
aws logs tail /aws/lambda/drs-orchestration-api-handler-test --since 24h --format short --region us-east-1 > lambda-logs.txt
```

---

## 🎯 Success Criteria

**Investigation Complete When**:
1. ✅ Root cause identified
2. ✅ Clear explanation of difference
3. ✅ Fix implemented and tested
4. ✅ Documentation updated

**Possible Outcomes**:
1. **Lambda Fixed** - Drills now create instances like CLI
2. **Understanding Updated** - Drills aren't supposed to create instances (update CLI understanding)
3. **Workaround Documented** - Known limitation with mitigation strategy

---

## 📝 Documentation to Update

After investigation:
1. Update `docs/SESSION_63_HANDOFF_TO_KIRO.md` with findings
2. Update `docs/PROJECT_STATUS.md` with resolution
3. Create `docs/DRILL_MYSTERY_RESOLUTION.md` with technical details
4. Update `docs/AWS_DRS_OPERATIONAL_RULES_AND_CONSTRAINTS.md` if needed

---

## ⏰ Time Estimate

**Total Investigation**: 45-60 minutes
- Data collection: 20 minutes
- Analysis: 15 minutes
- Fix implementation: 10 minutes
- Testing: 10 minutes
- Documentation: 5 minutes

---

## 🚀 Ready to Start

**Prerequisites**:
- ✅ AWS credentials updated and working
- ✅ All documentation analyzed and understood
- ✅ Investigation plan prepared
- ✅ Fast deployment method available (5 seconds)
- ✅ Test server ID known: s-3c63bb8be30d7d071

**First Command to Run**:
```bash
# Get recent Lambda job ID
aws logs tail /aws/lambda/drs-orchestration-api-handler-test \
  --since 24h --format short --region us-east-1 | grep "jobID" | tail -5
```

**Let's solve this mystery!** 🔍
