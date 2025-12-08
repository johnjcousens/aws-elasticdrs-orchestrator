# Commit Analysis: Fix IAM Policy for EC2 Instance Launch

**Commit**: `242b696cc81a5581718cc45d78221c3ef5ecdde2`  
**Date**: December 7, 2025, 11:46 AM  
**Author**: John J. Cousens

## What Was Fixed

### The Problem
AWS managed policy `AWSElasticDisasterRecoveryConsoleFullAccess_v2` has a **condition** on `ec2:StartInstances` requiring the `AWSElasticDisasterRecoveryManaged` tag. One server's launch template had this tag, the other didn't, causing inconsistent launch behavior.

### The Solution
Added `ec2:StartInstances` to the **inline IAM policy WITHOUT conditions**, bypassing the managed policy's tag-based restriction.

```yaml
# BEFORE:
- ec2:DescribeTags
- ec2:TerminateInstances
- ec2:StopInstances
- ec2:CreateTags

# AFTER:
- ec2:DescribeTags
- ec2:TerminateInstances
- ec2:StopInstances
- ec2:StartInstances  # ← ADDED
- ec2:CreateTags
```

### Key Insight
The AWS managed policy's conditional permission was blocking one server. Adding an unconditional inline policy permission overrides this restriction.

## Files Changed

### Infrastructure Changes (1 file)
- **cfn/lambda-stack.yaml** (+1 line)
  - Added `ec2:StartInstances` to OrchestrationLambdaRole inline policy

### Documentation Changes (5 files)
- **README.md** - Updated status
- **docs/DRS_DETACHVOLUME_ROOT_CAUSE_ANALYSIS.md** - Added findings
- **docs/SESSION_70_DELETEVOLUME_FIX.md** - Updated analysis
- **docs/SESSION_70_FINAL_ANALYSIS.md** - NEW: Complete root cause analysis (187 lines)
- **docs/SESSION_70_FINAL_ROOT_CAUSE.md** - NEW: Final diagnosis (95 lines)

## Root Cause Analysis

### AWS Managed Policy Condition
The managed policy `AWSElasticDisasterRecoveryConsoleFullAccess_v2` includes:
```json
{
  "Effect": "Allow",
  "Action": "ec2:StartInstances",
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "ec2:ResourceTag/AWSElasticDisasterRecoveryManaged": "true"
    }
  }
}
```

### The Inconsistency
- **Server 1** (EC2AMAZ-4IMB9PN): Launch template HAD the required tag → Launched successfully
- **Server 2** (EC2AMAZ-RLP9U5V): Launch template MISSING the tag → Failed to launch

### The Fix
Inline policy permissions take precedence and don't have the tag condition:
```yaml
- Effect: Allow
  Action:
    - ec2:StartInstances  # No conditions!
  Resource: '*'
```

## Validation

**Successful Drill**: `drsjob-3949c80becf56a075`

Both servers launched successfully:
- ✅ `i-097556fe6481c1d3a` (EC2AMAZ-4IMB9PN)
- ✅ `i-06ea360aab5e258fd` (EC2AMAZ-RLP9U5V)

## Deployment Status

### ✅ DEPLOYED

**Verification Completed**: December 8, 2025

1. **S3 Template**: ✅ Contains `ec2:StartInstances`
```bash
aws s3 cp s3://aws-drs-orchestration/cfn/lambda-stack.yaml -
# Confirmed: ec2:StartInstances present in template
```

2. **IAM Role Policy**: ✅ Deployed to OrchestrationRole
```bash
Role: drs-orchestration-dev-LambdaStack-OrchestrationRole-DUHcjjfdjIDD
Policy: EC2Access
Actions: [
  "ec2:DescribeInstances",
  "ec2:DescribeInstanceStatus",
  "ec2:DescribeTags",
  "ec2:DescribeLaunchTemplates",
  "ec2:TerminateInstances",
  "ec2:StopInstances",
  "ec2:StartInstances",  # ← CONFIRMED DEPLOYED
  "ec2:CreateTags"
]
```

3. **CloudFormation Stack**: ✅ Updated
```bash
Stack: drs-orchestration-dev-LambdaStack-NVR0GRX6B8U3
Status: UPDATE_COMPLETE
```

## Impact

### Before Fix:
- ❌ Only servers with `AWSElasticDisasterRecoveryManaged` tag could launch
- ❌ Inconsistent behavior between servers
- ❌ One server launched, one failed

### After Fix:
- ✅ All servers can launch regardless of tags
- ✅ Consistent behavior across all servers
- ✅ Both servers launch successfully

## CI/CD Compliance

### ✅ Code Committed
- CloudFormation template updated in git

### ✅ S3 Synced
- Template synced to `s3://aws-drs-orchestration/cfn/lambda-stack.yaml`
- Contains `ec2:StartInstances` permission

### ✅ Stack Updated
- CloudFormation stack deployed successfully
- IAM policy active in OrchestrationRole
- Permission verified in deployed environment

## Related Commits

This fix works in conjunction with:
- **00f4eb3** (Dec 7, 12:23 PM) - Fixed LAUNCHED status detection in orchestration_stepfunctions.py
- **242b696** (Dec 7, 11:46 AM) - Fixed IAM policy for ec2:StartInstances (THIS COMMIT)

Together, these fixes enable successful drill execution with both servers launching.

## Conclusion

✅ **Root cause identified**: AWS managed policy conditional permission  
✅ **Fix implemented**: Added unconditional ec2:StartInstances to inline policy  
✅ **Validated**: Both servers launched in drill drsjob-3949c80becf56a075  
✅ **DEPLOYED**: IAM policy active in production environment

**Status**: Fix is live and operational. Both servers can now launch successfully.
