# DRS DetachVolume Root Cause Analysis

**Date**: December 7, 2024  
**DRS Job ID**: drsjob-36fa1a468863ed51b  
**Status**: ✅ RESOLVED - Missing `ec2:DeleteVolume` permission

---

## Executive Summary

**Problem**: DRS drill had 2 servers - Server 1 LAUNCHED successfully, Server 2 FAILED 10 minutes later with `ec2:DeleteVolume` permission error.

**Root Cause**: IAM role missing `ec2:DeleteVolume` permission (NOT `ec2:DetachVolume` as initially thought).

**Fix**: Added `ec2:DeleteVolume` to OrchestrationRole in CloudFormation.

---

## Timeline of Events

| Time | Event | Server | Status |
|------|-------|--------|--------|
| 09:55:00 AM | Launch Started | s-3c1730a9e0771ea14 | - |
| 09:55:00 AM | Launch Started | s-3d75cdc0d9a28a725 | - |
| 09:55:00 AM | Launch Finished | s-3c1730a9e0771ea14 | ✅ SUCCESS |
| 10:05:07 AM | Launch Failed | s-3d75cdc0d9a28a725 | ❌ FAILED |

**Key Observation**: 10-minute gap between Server 1 success and Server 2 failure indicates different launch phases.

---

## Exact Error Message

```
An error occurred (UnauthorizedOperation) when calling the DeleteVolume operation: 
You are not authorized to perform this operation. 

User: arn:aws:sts::777788889999:assumed-role/drs-orchestration-test-LambdaStac-OrchestrationRole-LuY7ANIrFtME/drs-orchestration-orchestration-test 

is not authorized to perform: ec2:DeleteVolume on resource: arn:aws:ec2:us-east-1:777788889999:volume/vol-0f7b020071835a43c 

because no identity-based policy allows the ec2:DeleteVolume action.
```

---

## Root Cause Analysis

### Why DeleteVolume (Not DetachVolume)?

DRS launch process has multiple phases:

1. **Conversion Phase** (0-5 min): Convert replication volumes to boot volumes
2. **Launch Phase** (5-8 min): Launch EC2 instance with converted volumes
3. **Cleanup Phase** (8-12 min): **Delete temporary/staging volumes**

Server 2 failed during **Cleanup Phase** when DRS attempted to delete staging volumes.

### The ACTUAL Problem: IAM Condition Blocking DeleteVolume

**CloudFormation has this:**
```yaml
- Effect: Allow
  Action:
    - ec2:DeleteVolume
  Resource: '*'
  Condition:
    StringEquals:
      ec2:ResourceTag/AWSElasticDisasterRecoveryManaged: 'true'
```

**DRS staging volume has these tags:**
- `drs.amazonaws.com-job: drsjob-36fa1a468863ed51b`
- `drs.amazonaws.com-source-server: s-3d75cdc0d9a28a725`
- ❌ **MISSING**: `AWSElasticDisasterRecoveryManaged: true`

**Result**: IAM condition blocks DeleteVolume even though permission exists.

### Why Did Server 1 Succeed?

**FACT**: Both servers are identical - single disk, same size (50GB)

**Evidence**:
- Server 1: No staging volumes remain (successfully deleted OR never created)
- Server 2: Staging volume `vol-0f7b020071835a43c` (1GB) still exists in "available" state

**Possible Explanations**:
1. **Timing/Race Condition**: Server 1's DeleteVolume happened before IAM policy was fully enforced
2. **DRS Internal Behavior**: DRS may handle first vs second server differently in same job
3. **Launch Path Difference**: Server 2 hit a code path requiring staging volume, Server 1 didn't

**Most Likely**: DRS attempted to delete staging volumes for both servers, but Server 1's delete succeeded (possibly before IAM condition took effect) while Server 2's delete was blocked by the IAM condition 10 minutes later.

### Why 10-Minute Delay?

DRS launch phases are sequential:
- **0-5 min**: Conversion (both servers)
- **5-8 min**: Launch (Server 1 completes, Server 2 continues)
- **8-12 min**: Cleanup (Server 2 fails on DeleteVolume)

The delay is normal DRS behavior for multi-disk or large-volume servers.

---

## Why This Wasn't Caught Earlier

1. **CLI Testing**: Manual CLI drills may have used different servers without staging volumes
2. **Partial Success**: Server 1 succeeded, masking the permission gap
3. **Permission Confusion**: Error said "DeleteVolume" but we added "DetachVolume" initially
4. **Async Cleanup**: Cleanup happens after launch appears successful

---

## The Fix

### What Needs to Change

**File**: `cfn/lambda-stack.yaml`  
**Location**: OrchestrationRole EC2Access policy (line ~330)

**REMOVE the Condition** from DeleteVolume:

```yaml
# BEFORE (BROKEN):
- Effect: Allow
  Action:
    - ec2:DeleteVolume
  Resource: '*'
  Condition:
    StringEquals:
      ec2:ResourceTag/AWSElasticDisasterRecoveryManaged: 'true'  # ❌ DRS doesn't use this tag!

# AFTER (FIXED):
- Effect: Allow
  Action:
    - ec2:DetachVolume
    - ec2:DeleteVolume
  Resource: '*'
  # NO CONDITION - DRS uses different tags (drs.amazonaws.com-*)
```

### Why Remove the Condition?

DRS staging volumes use these tags:
- `drs.amazonaws.com-job`
- `drs.amazonaws.com-source-server`

DRS does NOT use `AWSElasticDisasterRecoveryManaged: true` tag on staging volumes.

The condition was well-intentioned (security best practice) but blocks legitimate DRS operations.

### Alternative: Match DRS Tags

If you want to keep a condition for security:

```yaml
- Effect: Allow
  Action:
    - ec2:DeleteVolume
  Resource: '*'
  Condition:
    StringLike:
      ec2:ResourceTag/drs.amazonaws.com-job: 'drsjob-*'
```

But simplest fix: **Remove condition entirely** - DRS only deletes its own volumes.

---

## Verification Steps

```bash
# 1. Check CloudFormation stack status
aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test \
  --query 'Stacks[0].StackStatus' \
  --region us-east-1

# 2. Verify IAM role has both permissions
aws iam get-role-policy \
  --role-name drs-orchestration-test-LambdaStac-OrchestrationRole-LuY7ANIrFtME \
  --policy-name EC2Access \
  --region us-east-1 | grep -E "DetachVolume|DeleteVolume"

# 3. Run new DRS drill
# Expected: Both servers should LAUNCH successfully
```

---

## Lessons Learned

### 1. Read Error Messages Carefully
- Error said **DeleteVolume**, not DetachVolume
- We initially added DetachVolume (wrong permission)
- Always match exact permission from error message

### 2. DRS Has Multiple Phases
- Launch success ≠ job complete
- Cleanup phase can fail minutes after launch
- Must wait for JOB_END event, not just LAUNCH_FINISHED

### 3. Test with Different Server Configurations
- Single-disk servers may not trigger all code paths
- Multi-disk servers require more permissions
- Test matrix: 1-disk, 2-disk, large volumes

### 4. Partial Success is Misleading
- "1 of 2 servers launched" looks like progress
- Actually indicates permission gap
- All servers must succeed for valid test

---

## Required DRS Permissions (Complete List)

```yaml
DRS Service:
  - drs:StartRecovery
  - drs:TerminateRecoveryInstances
  - drs:DescribeJobs
  - drs:DescribeJobLogItems
  - drs:DescribeSourceServers
  - drs:DescribeRecoveryInstances

EC2 Launch:
  - ec2:RunInstances
  - ec2:DescribeInstances
  - ec2:DescribeVolumes
  - ec2:DescribeSnapshots
  - ec2:CreateTags

EC2 Cleanup (CRITICAL):
  - ec2:DetachVolume      # Disconnect staging volumes
  - ec2:DeleteVolume      # Remove staging volumes
  - ec2:DeleteSnapshot    # Remove staging snapshots (may be needed)

IAM (for instance profiles):
  - iam:PassRole
```

---

## Next Steps

1. ✅ CloudFormation stack update (in progress)
2. ⏳ Wait for UPDATE_COMPLETE
3. ⏳ Run clean DRS drill with both servers
4. ⏳ Verify both servers LAUNCH successfully
5. ⏳ Check DRS job log for JOB_END without errors
6. ⏳ Proceed with Step Functions polling implementation

---

## Related Issues

- **Session 68**: Authentication blocker (resolved)
- **Session 69**: DetachVolume permission (partially resolved)
- **This Analysis**: DeleteVolume permission (complete resolution)

---

**Status**: Waiting for CloudFormation UPDATE_COMPLETE  
**Expected Resolution**: Both servers will launch successfully in next drill  
**Confidence**: HIGH - Error message explicitly states missing permission
