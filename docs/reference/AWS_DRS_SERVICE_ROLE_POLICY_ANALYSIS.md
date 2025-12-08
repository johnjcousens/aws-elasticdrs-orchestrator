# AWS DRS Service Role Policy Analysis

**Policy**: `AWSElasticDisasterRecoveryServiceRolePolicy`  
**ARN**: `arn:aws:iam::aws:policy/aws-service-role/AWSElasticDisasterRecoveryServiceRolePolicy`  
**Version**: v8  
**Purpose**: Allows Elastic Disaster Recovery service to manage AWS resources on your behalf

## Key Finding: ec2:StartInstances Permission

### Statement 12 (DRSServiceRolePolicy12)
```json
{
    "Sid": "DRSServiceRolePolicy12",
    "Effect": "Allow",
    "Action": [
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:TerminateInstances",
        "ec2:ModifyInstanceAttribute",
        "ec2:GetConsoleOutput",
        "ec2:GetConsoleScreenshot"
    ],
    "Resource": "arn:aws:ec2:*:*:instance/*",
    "Condition": {
        "Null": {
            "aws:ResourceTag/AWSElasticDisasterRecoveryManaged": "false"
        }
    }
}
```

### Critical Condition
**The service role CAN start instances, BUT only if they have the `AWSElasticDisasterRecoveryManaged` tag.**

This explains why:
- ✅ Server 1 (EC2AMAZ-4IMB9PN) launched - had the tag
- ❌ Server 2 (EC2AMAZ-RLP9U5V) failed - missing the tag

## Policy Structure Overview

### 33 Statements Total

**DRS-Specific Actions** (Statements 1-3):
- `drs:ListTagsForResource` - List tags on DRS resources
- `drs:TagResource` - Tag recovery instances and source servers
- `drs:CreateRecoveryInstanceForDrs` - Create recovery instances

**EC2 Read Permissions** (Statement 6):
- Extensive describe permissions for EC2 resources
- No conditions - allows DRS to inspect infrastructure

**EC2 Write Permissions with Tag Conditions** (Statements 8-13, 18-22):
All destructive/modification actions require `AWSElasticDisasterRecoveryManaged` tag:
- `ec2:StartInstances` ⚠️ **REQUIRES TAG**
- `ec2:StopInstances` - Requires tag
- `ec2:TerminateInstances` - Requires tag
- `ec2:DeleteVolume` - Requires tag
- `ec2:DeleteSnapshot` - Requires tag
- `ec2:DetachVolume` - Requires tag (on instance)
- `ec2:AttachVolume` - Requires tag

**EC2 Create Permissions** (Statements 14-19, 23-24, 30-31):
Resource creation requires `AWSElasticDisasterRecoveryManaged` tag on REQUEST:
- `ec2:CreateVolume` - Tag required on request
- `ec2:CreateSecurityGroup` - Tag required on request
- `ec2:CreateLaunchTemplate` - Tag required on request
- `ec2:CreateSnapshot` - Tag required on request
- `ec2:RunInstances` - Tag required on request
- `ec2:CreateNetworkInterface` - Tag required on request

**IAM PassRole** (Statement 25):
Limited to DRS service roles:
- `AWSElasticDisasterRecoveryReplicationServerRole`
- `AWSElasticDisasterRecoveryConversionServerRole`
- `AWSElasticDisasterRecoveryRecoveryInstanceRole`

**Tagging** (Statements 26-27):
- Can tag resources during creation
- Can tag AMIs with DRS managed tag

**CloudWatch** (Statement 28):
- `cloudwatch:GetMetricData` - Monitor instance metrics

## Tag-Based Security Model

### The Tag: `AWSElasticDisasterRecoveryManaged`

**Purpose**: Ensures DRS service role can only manage resources it created or explicitly tagged.

**Condition Types**:

1. **Resource Tag Condition** (`aws:ResourceTag/...`):
   - Applied to existing resources
   - Checks if resource HAS the tag
   - Used for: Start, Stop, Terminate, Delete, Modify

2. **Request Tag Condition** (`aws:RequestTag/...`):
   - Applied during resource creation
   - Checks if tag is being ADDED
   - Used for: Create operations

### Security Benefits

✅ **Prevents accidental modification** of non-DRS resources  
✅ **Isolates DRS operations** from other EC2 workloads  
✅ **Enables safe multi-tenant** DRS deployments  
✅ **Audit trail** via tag presence

### Security Risks

⚠️ **If tag is missing** on recovery instances, DRS cannot manage them  
⚠️ **Manual tag removal** breaks DRS automation  
⚠️ **Launch template must include tag** for successful recovery

## Comparison with Our Fix (Commit 242b696c)

### DRS Service Role (This Policy)
```json
{
    "Action": "ec2:StartInstances",
    "Resource": "arn:aws:ec2:*:*:instance/*",
    "Condition": {
        "Null": {
            "aws:ResourceTag/AWSElasticDisasterRecoveryManaged": "false"
        }
    }
}
```
**Limitation**: Can only start instances WITH the tag.

### Our Orchestration Role (Our Fix)
```yaml
- Effect: Allow
  Action:
    - ec2:StartInstances
  Resource: '*'
```
**Advantage**: Can start ANY instance, regardless of tags.

## Why Our Fix Was Necessary

### The Problem
1. DRS service role creates recovery instances
2. Launch template for Server 2 was missing `AWSElasticDisasterRecoveryManaged` tag
3. DRS service role could NOT start the instance (condition failed)
4. Recovery failed for Server 2

### The Solution
1. Our orchestration Lambda has its own IAM role
2. We added unconditional `ec2:StartInstances` permission
3. Our Lambda can start instances even without the tag
4. Both servers now launch successfully

## Best Practices

### For DRS Deployments

1. **Always include tag in launch templates**:
```yaml
Tags:
  - Key: AWSElasticDisasterRecoveryManaged
    Value: "true"
```

2. **Verify tag on source servers**:
```bash
aws ec2 describe-instances \
  --instance-ids i-xxxxx \
  --query 'Reservations[].Instances[].Tags[?Key==`AWSElasticDisasterRecoveryManaged`]'
```

3. **Monitor tag compliance**:
- Use AWS Config rules
- Alert on missing tags
- Automated remediation

### For Orchestration

1. **Use service-specific roles** with appropriate permissions
2. **Add unconditional permissions** when needed for orchestration
3. **Document why** permissions bypass tag conditions
4. **Audit orchestration actions** separately from DRS service actions

## Related Policies

### AWSElasticDisasterRecoveryConsoleFullAccess_v2
- User-facing console policy
- Also has tag-based conditions
- Allows users to manage DRS resources

### Service-Linked Roles
- `AWSElasticDisasterRecoveryReplicationServerRole` - Replication servers
- `AWSElasticDisasterRecoveryConversionServerRole` - Conversion servers
- `AWSElasticDisasterRecoveryRecoveryInstanceRole` - Recovery instances

## Conclusion

The `AWSElasticDisasterRecoveryServiceRolePolicy` implements a **tag-based security model** that:

✅ Protects non-DRS resources from accidental modification  
✅ Enables safe DRS operations in shared AWS accounts  
⚠️ Requires proper tagging for successful recovery operations

Our orchestration fix (commit 242b696c) was necessary because:
- Launch template was missing the required tag
- DRS service role couldn't start the instance
- Our orchestration role bypasses the tag requirement
- Enables recovery even with misconfigured launch templates

**Recommendation**: Fix launch templates to include the tag, but keep our orchestration permission as a safety net.
