# Complete DRS IAM Requirements Analysis

## Root Cause Found

**Error**: `UnauthorizedOperation` when calling `CreateLaunchTemplateVersion`

**The Problem**: When our Lambda calls `drs:StartRecovery`, DRS service needs to:
1. Create snapshots
2. Launch conversion server
3. **Create/modify launch templates** ← FAILING HERE
4. Launch recovery instances

## DRS Recovery Flow & Required Permissions

### Phase 1: Snapshot Creation
**DRS Service Role Needs**:
- `ec2:CreateSnapshot` (on volumes with DRS tag)
- `ec2:CreateTags` (to tag snapshots)
- `ec2:DescribeVolumes`
- `ec2:DescribeSnapshots`

### Phase 2: Conversion Server Launch
**DRS Service Role Needs**:
- `ec2:RunInstances` (with DRS tag requirement)
- `ec2:CreateNetworkInterface`
- `ec2:DescribeSubnets`
- `ec2:DescribeSecurityGroups`
- `iam:PassRole` (for AWSElasticDisasterRecoveryConversionServerRole)

### Phase 3: Launch Template Management ← **FAILING HERE**
**DRS Service Role Needs**:
- `ec2:CreateLaunchTemplate` (with DRS tag)
- `ec2:CreateLaunchTemplateVersion` ← **MISSING**
- `ec2:ModifyLaunchTemplate` (with DRS tag condition)
- `ec2:DescribeLaunchTemplates`
- `ec2:DescribeLaunchTemplateVersions`

### Phase 4: Recovery Instance Launch
**DRS Service Role Needs**:
- `ec2:RunInstances` (with DRS tag)
- `ec2:StartInstances` (with DRS tag condition)
- `ec2:CreateVolume` (from DRS snapshots)
- `ec2:AttachVolume` (with DRS tag)
- `iam:PassRole` (for AWSElasticDisasterRecoveryRecoveryInstanceRole)

## The Issue: Who Calls CreateLaunchTemplateVersion?

### Scenario 1: DRS Service-Linked Role (Normal Flow)
When DRS runs as a service:
- Uses: `AWSServiceRoleForElasticDisasterRecovery`
- Has: `AWSElasticDisasterRecoveryServiceRolePolicy` (v8)
- **Includes**: `ec2:CreateLaunchTemplateVersion` with DRS tag condition

### Scenario 2: User/Lambda Calls start_recovery (Our Case)
When Lambda calls `drs:StartRecovery`:
- Lambda uses: `OrchestrationRole` 
- Lambda has: `drs:StartRecovery` permission ✓
- **BUT**: DRS service still needs to perform EC2 operations
- **Problem**: DRS tries to use the calling role's permissions?

## AWS Service Role vs Calling Role

### Key Question: Who performs the EC2 operations?

**Option A: DRS Service-Linked Role** (Expected)
- DRS should use `AWSServiceRoleForElasticDisasterRecovery`
- This role has all necessary EC2 permissions
- Should work regardless of who calls `start_recovery`

**Option B: Calling Role** (What's Happening?)
- DRS tries to use the Lambda's `OrchestrationRole`
- This role is MISSING `ec2:CreateLaunchTemplateVersion`
- **This explains the UnauthorizedOperation error**

## Complete EC2 Permissions Needed

Based on `AWSElasticDisasterRecoveryServiceRolePolicy` v8:

### Read Permissions (No Conditions)
```json
{
  "Action": [
    "ec2:DescribeAccountAttributes",
    "ec2:DescribeAvailabilityZones",
    "ec2:DescribeImages",
    "ec2:DescribeInstances",
    "ec2:DescribeInstanceTypes",
    "ec2:DescribeInstanceAttribute",
    "ec2:DescribeInstanceStatus",
    "ec2:DescribeLaunchTemplateVersions",
    "ec2:DescribeLaunchTemplates",
    "ec2:DescribeSecurityGroups",
    "ec2:DescribeSnapshots",
    "ec2:DescribeSubnets",
    "ec2:DescribeVolumes",
    "ec2:DescribeVolumeAttribute",
    "ec2:DescribeVpcs",
    "ec2:DescribeNetworkInterfaces",
    "ec2:GetEbsDefaultKmsKeyId",
    "ec2:GetEbsEncryptionByDefault"
  ],
  "Resource": "*"
}
```

### Write Permissions (With DRS Tag Conditions)
```json
{
  "Action": [
    "ec2:CreateLaunchTemplate",
    "ec2:CreateLaunchTemplateVersion",
    "ec2:ModifyLaunchTemplate",
    "ec2:DeleteLaunchTemplate",
    "ec2:DeleteLaunchTemplateVersions",
    "ec2:CreateVolume",
    "ec2:DeleteVolume",
    "ec2:ModifyVolume",
    "ec2:CreateSnapshot",
    "ec2:DeleteSnapshot",
    "ec2:CreateSecurityGroup",
    "ec2:CreateNetworkInterface",
    "ec2:DeleteNetworkInterface",
    "ec2:ModifyNetworkInterfaceAttribute",
    "ec2:RunInstances",
    "ec2:StartInstances",
    "ec2:StopInstances",
    "ec2:TerminateInstances",
    "ec2:AttachVolume",
    "ec2:DetachVolume",
    "ec2:CreateTags",
    "ec2:RegisterImage",
    "ec2:DeregisterImage"
  ],
  "Resource": "*",
  "Condition": {
    "Null": {
      "aws:ResourceTag/AWSElasticDisasterRecoveryManaged": "false"
    }
  }
}
```

## The Fix

### Option 1: Add Missing Permission to OrchestrationRole (Quick Fix)
Add to `cfn/lambda-stack.yaml`:
```yaml
- ec2:CreateLaunchTemplateVersion
- ec2:ModifyLaunchTemplate
- ec2:DeleteLaunchTemplateVersions
```

### Option 2: Add ALL DRS-Required EC2 Permissions (Complete Fix)
Add complete set of EC2 permissions that DRS needs:
```yaml
- ec2:CreateLaunchTemplate
- ec2:CreateLaunchTemplateVersion
- ec2:ModifyLaunchTemplate
- ec2:DeleteLaunchTemplate
- ec2:DeleteLaunchTemplateVersions
- ec2:CreateVolume
- ec2:AttachVolume
- ec2:DetachVolume
- ec2:CreateSnapshot
- ec2:CreateNetworkInterface
- ec2:DeleteNetworkInterface
- ec2:ModifyNetworkInterfaceAttribute
- ec2:RunInstances
- ec2:RegisterImage
- ec2:DeregisterImage
```

### Option 3: Use Service-Linked Role (Architectural Fix)
**Problem**: We can't force DRS to use its service-linked role when we call the API.

## Why This Happens

### AWS Service Behavior Pattern
Some AWS services inherit the calling principal's permissions:
- **CloudFormation**: Uses calling role for resource operations
- **Step Functions**: Can use calling role or execution role
- **DRS**: Appears to use calling role for EC2 operations

### The Confusion
- DRS has a service-linked role with full permissions
- But when called via API, it uses the **caller's permissions**
- This is why CLI works (user has admin) but Lambda fails (limited role)

## Complete Required Permissions for OrchestrationRole

```yaml
EC2Access:
  Effect: Allow
  Action:
    # Read permissions
    - ec2:DescribeInstances
    - ec2:DescribeInstanceStatus
    - ec2:DescribeTags
    - ec2:DescribeLaunchTemplates
    - ec2:DescribeLaunchTemplateVersions
    - ec2:DescribeVolumes
    - ec2:DescribeSnapshots
    - ec2:DescribeSecurityGroups
    - ec2:DescribeSubnets
    - ec2:DescribeNetworkInterfaces
    
    # Launch template operations (MISSING - CRITICAL)
    - ec2:CreateLaunchTemplate
    - ec2:CreateLaunchTemplateVersion
    - ec2:ModifyLaunchTemplate
    - ec2:DeleteLaunchTemplateVersions
    
    # Instance operations
    - ec2:RunInstances
    - ec2:StartInstances
    - ec2:StopInstances
    - ec2:TerminateInstances
    
    # Volume operations
    - ec2:CreateVolume
    - ec2:AttachVolume
    - ec2:DetachVolume
    - ec2:DeleteVolume
    
    # Snapshot operations
    - ec2:CreateSnapshot
    - ec2:DeleteSnapshot
    
    # Network operations
    - ec2:CreateNetworkInterface
    - ec2:DeleteNetworkInterface
    - ec2:ModifyNetworkInterfaceAttribute
    
    # Image operations
    - ec2:RegisterImage
    - ec2:DeregisterImage
    
    # Tagging
    - ec2:CreateTags
    
  Resource: '*'
```

## Verification Command

After adding permissions, verify:
```bash
aws iam get-role-policy \
  --role-name drs-orchestration-dev-LambdaStack-OrchestrationRole-DUHcjjfdjIDD \
  --policy-name EC2Access \
  --query 'PolicyDocument.Statement[0].Action' \
  | grep CreateLaunchTemplateVersion
```

Should return: `ec2:CreateLaunchTemplateVersion`

## Summary

**Root Cause**: DRS service uses the **calling role's permissions** when performing EC2 operations, not its own service-linked role.

**Missing Permission**: `ec2:CreateLaunchTemplateVersion` (and likely others)

**Fix**: Add complete set of EC2 permissions to OrchestrationRole that mirror what DRS service-linked role has.

**Why Previous Fix Worked**: Adding `ec2:StartInstances` allowed ONE operation, but DRS needs MANY more EC2 permissions throughout the recovery process.
