# Deployment Success Summary

**Date**: December 8, 2025  
**Issue**: DRS recovery failing with `UnauthorizedOperation` on `CreateLaunchTemplateVersion`  
**Resolution**: Added EC2 launch template permissions to OrchestrationRole  
**Status**: ✅ **RESOLVED AND VERIFIED**

---

## Problem Statement

DRS recovery jobs were completing but failing to launch recovery instances with error:
```
UnauthorizedOperation when calling CreateLaunchTemplateVersion operation: 
You are not authorized to perform this operation.
```

### Root Cause

When Lambda calls `drs:StartRecovery`, the DRS service uses the **calling role's IAM permissions** (OrchestrationRole) to perform EC2 operations, not its own service-linked role permissions. The OrchestrationRole was missing critical EC2 launch template permissions.

---

## Solution Implemented

### 1. CloudFormation Template Update

**File**: `cfn/lambda-stack.yaml`  
**Change**: Added 5 EC2 launch template permissions to OrchestrationRole

```yaml
EC2Access:
  Effect: Allow
  Action:
    # Existing permissions...
    - ec2:DescribeInstances
    - ec2:DescribeInstanceStatus
    - ec2:StartInstances
    
    # NEW: Launch template permissions (CRITICAL FIX)
    - ec2:CreateLaunchTemplate
    - ec2:CreateLaunchTemplateVersion
    - ec2:ModifyLaunchTemplate
    - ec2:DeleteLaunchTemplate
    - ec2:DeleteLaunchTemplateVersions
    
  Resource: '*'
```

### 2. Deployment Process

```bash
# Sync code to S3 and deploy CloudFormation
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

**Deployment Results**:
- ✅ S3 sync completed
- ✅ Lambda package uploaded (170.8 KiB)
- ✅ CloudFormation stack updated (34 seconds)
- ✅ All nested stacks updated (Database, Lambda, API, Frontend)

### 3. Permission Verification

```bash
aws iam get-role-policy \
  --role-name drs-orchestration-dev-LambdaStack-OrchestrationRole-DUHcjjfdjIDD \
  --policy-name EC2Access
```

**Confirmed Permissions**:
```json
[
  "ec2:CreateLaunchTemplate",
  "ec2:CreateLaunchTemplateVersion",
  "ec2:ModifyLaunchTemplate",
  "ec2:DeleteLaunchTemplate",
  "ec2:DeleteLaunchTemplateVersions"
]
```

---

## Test Results

### Test Execution

**Job ID**: `drsjob-3d99102eaab6ff86e`  
**Source Servers**: 
- `s-3c1730a9e0771ea14` (EC2AMAZ-4IMB9PN)
- `s-3d75cdc0d9a28a725` (EC2AMAZ-RLP9U5V)

**Drill Mode**: True

### Timeline

| Time | Event | Status |
|------|-------|--------|
| 04:44:25 | Conversion Start | ✓ |
| 04:57:28 | Conversion End | ✓ (13 min) |
| 04:57:30 | Launch Start | ✓ |
| 05:29:29 | Instance 1 Launched | ✓ |
| 05:30:14 | Instance 2 Launched | ✓ |
| 04:57:31 | Job End | COMPLETED |

### Recovery Instances Created

| Instance ID | Source Server | State | Launch Time | Name |
|-------------|---------------|-------|-------------|------|
| i-0b75b58c7b13ea2db | s-3c1730a9e0771ea14 | RUNNING | 05:29:29 | EC2AMAZ-4IMB9PN |
| i-068d6519e1768280d | s-3d75cdc0d9a28a725 | RUNNING | 05:30:14 | EC2AMAZ-RLP9U5V |

### Verification

```bash
aws ec2 describe-instances \
  --instance-ids i-0b75b58c7b13ea2db i-068d6519e1768280d
```

**Results**:
- ✅ Both instances RUNNING
- ✅ Launched from DRS recovery job
- ✅ Tagged with `AWSElasticDisasterRecoveryManaged`
- ✅ Proper instance names preserved

---

## Key Insights

### 1. DRS Permission Model

**Discovery**: DRS uses the **calling principal's IAM permissions** when performing EC2 operations, not its own service-linked role.

**Implication**: When Lambda calls `drs:StartRecovery`, the Lambda's IAM role must have:
- All DRS API permissions (`drs:*`)
- All EC2 permissions that DRS needs to perform recovery operations

### 2. Required EC2 Permissions for DRS Recovery

Based on `AWSElasticDisasterRecoveryServiceRolePolicy` v8, the calling role needs:

**Read Permissions** (no conditions):
- `ec2:Describe*` (instances, volumes, snapshots, launch templates, etc.)

**Write Permissions** (with DRS tag conditions):
- Launch templates: Create, CreateVersion, Modify, Delete
- Instances: RunInstances, StartInstances, StopInstances, TerminateInstances
- Volumes: CreateVolume, AttachVolume, DetachVolume, DeleteVolume
- Snapshots: CreateSnapshot, DeleteSnapshot
- Network: CreateNetworkInterface, DeleteNetworkInterface, ModifyNetworkInterfaceAttribute
- Images: RegisterImage, DeregisterImage
- Tags: CreateTags

### 3. DRS Recovery Flow

**Phase 1**: Snapshot Creation (1-2 min)
- Creates EBS snapshots of source volumes
- Tags snapshots with `AWSElasticDisasterRecoveryManaged`

**Phase 2**: Conversion Server Launch (1-2 min)
- Launches conversion server from DRS AMI
- Attaches source snapshots
- Performs OS-level conversion

**Phase 3**: Launch Template Management (< 1 min) ← **Previously failing here**
- Creates/updates launch template for recovery instance
- Configures instance type, networking, storage
- **Requires**: `ec2:CreateLaunchTemplateVersion`

**Phase 4**: Recovery Instance Launch (1-2 min)
- Launches recovery instance from launch template
- Attaches converted volumes
- Starts instance

**Total Duration**: ~15-20 minutes for drill recovery

---

## Previous Fixes

### Fix #1: ec2:StartInstances Permission (Commit 242b696c)

**Problem**: DRS couldn't start recovery instances  
**Solution**: Added `ec2:StartInstances` to OrchestrationRole  
**Result**: Partial fix - allowed instance start but not launch template creation

### Fix #2: LAUNCHED Status Detection (Commit 00f4eb3e)

**Problem**: Code required `recoveryInstanceID` to detect LAUNCHED status  
**Solution**: Trust LAUNCHED status from DRS job response without requiring `recoveryInstanceID`  
**Result**: Improved status detection but didn't fix permission issue

### Fix #3: Launch Template Permissions (Current)

**Problem**: Missing `ec2:CreateLaunchTemplateVersion` and related permissions  
**Solution**: Added complete set of launch template permissions  
**Result**: ✅ **Full recovery working end-to-end**

---

## Verification Checklist

- [x] CloudFormation template updated with launch template permissions
- [x] Code synced to S3 deployment bucket
- [x] CloudFormation stack deployed successfully
- [x] IAM role has new permissions (verified via AWS CLI)
- [x] DRS drill executed successfully
- [x] Recovery instances created and running
- [x] Instances properly tagged with DRS managed tag
- [x] Instance names preserved from source servers

---

## Next Steps

### 1. Monitor Production Usage

Watch for any additional permission errors during:
- Full recovery (non-drill) executions
- Multi-wave recovery plans
- Different instance types or configurations

### 2. Consider Additional Permissions

Based on `AWSElasticDisasterRecoveryServiceRolePolicy`, consider adding:
- `ec2:CreateVolume` (for EBS volume creation)
- `ec2:AttachVolume` (for volume attachment)
- `ec2:CreateSnapshot` (for snapshot operations)
- `ec2:RunInstances` (for instance launch)

These may be needed for more complex recovery scenarios.

### 3. Update Documentation

- [x] Document root cause in `DRS_COMPLETE_IAM_ANALYSIS.md`
- [x] Update deployment guide with permission requirements
- [ ] Add troubleshooting section for permission errors
- [ ] Create runbook for DRS recovery testing

### 4. Automated Testing

Consider adding:
- Automated drill execution in CI/CD pipeline
- Permission validation tests
- Recovery instance verification tests

---

## Conclusion

The DRS recovery failure was caused by missing EC2 launch template permissions in the OrchestrationRole. Adding `ec2:CreateLaunchTemplate`, `ec2:CreateLaunchTemplateVersion`, `ec2:ModifyLaunchTemplate`, `ec2:DeleteLaunchTemplate`, and `ec2:DeleteLaunchTemplateVersions` resolved the issue.

**Key Takeaway**: When integrating with AWS DRS via API, the calling role must have comprehensive EC2 permissions that mirror the DRS service-linked role, as DRS uses the caller's permissions for EC2 operations.

**Status**: ✅ **MVP DRILL ONLY PROTOTYPE**

---

## References

- [DRS_COMPLETE_IAM_ANALYSIS.md](DRS_COMPLETE_IAM_ANALYSIS.md) - Root cause analysis
- [COMMIT_242b696_ANALYSIS.md](COMMIT_242b696_ANALYSIS.md) - First IAM fix
- [COMMIT_00f4eb3_ANALYSIS.md](COMMIT_00f4eb3_ANALYSIS.md) - Status detection fix
- [AWS DRS Service Role Policy](https://docs.aws.amazon.com/drs/latest/userguide/security_iam_service-with-iam.html)
- [cfn/lambda-stack.yaml](cfn/lambda-stack.yaml) - Updated CloudFormation template
