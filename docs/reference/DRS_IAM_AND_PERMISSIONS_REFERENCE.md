# DRS IAM and Permissions Reference

**Version**: 2.2 (January 26, 2026)  
**Purpose**: Comprehensive IAM permissions analysis for AWS DRS operations  
**Scope**: Service roles, cross-account setup, and troubleshooting

---

## Overview

AWS Elastic Disaster Recovery (DRS) requires specific IAM permissions to perform recovery operations. This document consolidates all IAM analysis including service role permissions, complete IAM requirements, and cross-account configurations.

## Lambda Handler Architecture

The orchestration platform uses **6 Lambda functions** with the unified orchestration role:

- **data-management-handler**: Protection groups, recovery plans, configuration management
- **execution-handler**: Recovery execution control, pause/resume, termination
- **query-handler**: Read-only queries, DRS status, EC2 resource discovery
- **frontend-deployer**: Frontend build and deployment operations
- **orch-sf**: Step Functions orchestration logic
- **notification-formatter**: SNS notification routing and formatting

All handlers share the **UnifiedOrchestrationRole** with comprehensive permissions.

## Service Role Permissions Analysis

### AWSElasticDisasterRecoveryServiceRolePolicy

**Policy ARN**: `arn:aws:iam::aws:policy/aws-service-role/AWSElasticDisasterRecoveryServiceRolePolicy`  
**Version**: v8  
**Purpose**: Allows DRS service to manage AWS resources on your behalf

#### Critical Finding: ec2:StartInstances Permission

**Statement 12 (DRSServiceRolePolicy12)**:
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

**Critical Condition**: The service role CAN start instances, BUT only if they have the `AWSElasticDisasterRecoveryManaged` tag.

This explains recovery failures:
- ✅ Tagged instances launch successfully
- ❌ Untagged instances fail with UnauthorizedOperation

#### Policy Structure (33 Statements Total)

**DRS-Specific Actions** (Statements 1-3):
- `drs:ListTagsForResource` - List tags on DRS resources
- `drs:TagResource` - Tag recovery instances and source servers
- `drs:CreateRecoveryInstanceForDrs` - Create recovery instances

**EC2 Read Permissions** (Statement 6):
- Extensive describe permissions for EC2 resources
- No conditions - allows DRS to inspect infrastructure

## Complete DRS Recovery Flow & Required Permissions

### Root Cause: UnauthorizedOperation on CreateLaunchTemplateVersion

When Lambda calls `drs:StartRecovery`, DRS service performs these phases:

#### Phase 1: Snapshot Creation
**DRS Service Role Needs**:
- `ec2:CreateSnapshot` (on volumes with DRS tag)
- `ec2:CreateTags` (to tag snapshots)
- `ec2:DescribeVolumes`
- `ec2:DescribeSnapshots`

#### Phase 2: Conversion Server Launch
**DRS Service Role Needs**:
- `ec2:RunInstances` (with DRS tag requirement)
- `ec2:CreateNetworkInterface`
- `ec2:DescribeSubnets`
- `ec2:DescribeSecurityGroups`
- `iam:PassRole` (for AWSElasticDisasterRecoveryConversionServerRole)

#### Phase 3: Launch Template Management ← **COMMON FAILURE POINT**
**DRS Service Role Needs**:
- `ec2:CreateLaunchTemplate` (with DRS tag)
- `ec2:CreateLaunchTemplateVersion` ← **OFTEN MISSING**
- `ec2:ModifyLaunchTemplate` (with DRS tag condition)
- `ec2:DescribeLaunchTemplates`
- `ec2:DescribeLaunchTemplateVersions`

#### Phase 4: Recovery Instance Launch
**DRS Service Role Needs**:
- `ec2:RunInstances` (with DRS tag)
- `ec2:StartInstances` (with DRS tag condition)
- `ec2:CreateVolume` (from DRS snapshots)
- `ec2:AttachVolume` (with DRS tag)
- `iam:PassRole` (for AWSElasticDisasterRecoveryRecoveryInstanceRole)

### Lambda Function IAM Requirements

For orchestration Lambda functions calling DRS APIs:

**Functions**: `data-management-handler`, `execution-handler`, `query-handler`, `frontend-deployer`, `orch-sf`, `notification-formatter`

```yaml
# DRS Permissions (CRITICAL)
- drs:DescribeSourceServers
- drs:StartRecovery
- drs:DescribeJobs
- drs:CreateRecoveryInstanceForDrs  # Often missing - causes failures

# EC2 Permissions (required by DRS during recovery)
- ec2:RunInstances
- ec2:CreateLaunchTemplate
- ec2:CreateLaunchTemplateVersion
- ec2:CreateVolume
- ec2:CreateTags

# DynamoDB Permissions (for orchestration state)
- dynamodb:GetItem
- dynamodb:PutItem
- dynamodb:UpdateItem
- dynamodb:Query
- dynamodb:Scan

# Step Functions (for orchestration)
- states:SendTaskSuccess
- states:SendTaskFailure
- states:SendTaskHeartbeat
```

## Cross-Account IAM Configuration

### Architecture Overview

Cross-account DRS enables source servers in one AWS account to replicate and recover to a different AWS account, providing additional isolation and security.

#### Supported Scenarios
- Cross-account within same region
- Cross-account cross-region
- Hybrid (on-premises to AWS cross-account)
- AWS to AWS cross-account

### Cross-Account Role Setup

#### 1. Source Account Configuration

**DRS Service Role** (Source Account):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "drs.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

**Required Permissions**:
- Standard DRS service role permissions
- `sts:AssumeRole` to target account role

#### 2. Target Account Configuration

**Cross-Account DRS Role** (Target Account):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::SOURCE-ACCOUNT-ID:role/service-role/AWSElasticDisasterRecoveryServiceRole"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "sts:ExternalId": "unique-external-id"
                }
            }
        }
    ]
}
```

**Required Permissions**:
- All EC2 launch and management permissions
- VPC and networking permissions
- KMS permissions for encrypted volumes

#### 3. KMS Key Requirements for Cross-Account

**Source Account KMS Policy**:
```json
{
    "Sid": "AllowCrossAccountDRSAccess",
    "Effect": "Allow",
    "Principal": {
        "AWS": "arn:aws:iam::TARGET-ACCOUNT-ID:role/DRSCrossAccountRole"
    },
    "Action": [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey"
    ],
    "Resource": "*"
}
```

**Target Account KMS Policy**:
```json
{
    "Sid": "AllowDRSServiceAccess",
    "Effect": "Allow",
    "Principal": {
        "Service": "drs.amazonaws.com"
    },
    "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
    ],
    "Resource": "*"
}
```

### Network Requirements

#### VPC Peering or Transit Gateway
- Source and target VPCs must have connectivity
- DRS replication traffic flows between accounts
- Staging area subnets in target account

#### Security Group Rules
```yaml
# Source Account Security Group
Outbound:
  - Protocol: TCP
    Port: 443
    Destination: 0.0.0.0/0  # HTTPS to DRS service
  - Protocol: TCP  
    Port: 1500
    Destination: TARGET-VPC-CIDR  # DRS replication traffic

# Target Account Security Group  
Inbound:
  - Protocol: TCP
    Port: 1500
    Source: SOURCE-VPC-CIDR  # DRS replication traffic
```

## Common IAM Issues and Troubleshooting

### 1. UnauthorizedOperation on CreateLaunchTemplateVersion

**Symptoms**:
- DRS job fails during launch template creation
- Error: "User is not authorized to perform: ec2:CreateLaunchTemplateVersion"

**Root Cause**:
- Missing `ec2:CreateLaunchTemplateVersion` permission in DRS service role
- Launch template not tagged with `AWSElasticDisasterRecoveryManaged`

**Solution**:
```yaml
# Add to DRS service role policy
- ec2:CreateLaunchTemplateVersion
- ec2:ModifyLaunchTemplate
```

### 2. AccessDeniedException on CreateRecoveryInstanceForDrs

**Symptoms**:
- Recovery job fails at instance launch
- Error: "Access denied for CreateRecoveryInstanceForDrs"

**Root Cause**:
- Missing `drs:CreateRecoveryInstanceForDrs` permission
- Often missing from Lambda execution roles

**Solution**:
```yaml
# Add to Lambda execution role
- drs:CreateRecoveryInstanceForDrs
```

### 3. Cross-Account Role Assumption Failures

**Symptoms**:
- Cross-account recovery fails
- Error: "Cannot assume role in target account"

**Root Cause**:
- Incorrect trust relationship
- Missing external ID
- KMS key permissions

**Solution**:
1. Verify trust relationship includes source account DRS role
2. Ensure external ID matches configuration
3. Update KMS key policies for cross-account access

### 4. Instance Launch Failures

**Symptoms**:
- Recovery instances fail to launch
- Error: "LAUNCH_FAILED with No Recovery Instances"

**Root Cause**:
- Missing `AWSElasticDisasterRecoveryManaged` tag
- Insufficient EC2 permissions
- Network connectivity issues

**Solution**:
1. Verify DRS tags on launch templates
2. Check EC2 service limits
3. Validate VPC and subnet configuration
4. Review CloudTrail for detailed error messages

## Security Best Practices

### 1. Least Privilege Access
- Use condition-based policies with DRS tags
- Limit cross-account access to specific resources
- Regular audit of IAM permissions

### 2. External ID Usage
- Always use external IDs for cross-account roles
- Generate unique, unpredictable external IDs
- Rotate external IDs periodically

### 3. KMS Key Management
- Use customer-managed KMS keys
- Implement key rotation policies
- Separate keys for source and target accounts

### 4. Monitoring and Auditing
- Enable CloudTrail for all DRS API calls
- Monitor cross-account role assumptions
- Set up alerts for permission failures

## Validation Commands

### Check DRS Service Role Permissions
```bash
# Get DRS service role policy
AWS_PAGER="" aws iam get-role-policy \
  --role-name AWSElasticDisasterRecoveryServiceRole \
  --policy-name AWSElasticDisasterRecoveryServiceRolePolicy

# List attached policies
AWS_PAGER="" aws iam list-attached-role-policies \
  --role-name AWSElasticDisasterRecoveryServiceRole
```

### Test Cross-Account Role Assumption
```bash
# Assume cross-account role
AWS_PAGER="" aws sts assume-role \
  --role-arn arn:aws:iam::TARGET-ACCOUNT:role/DRSCrossAccountRole \
  --role-session-name test-session \
  --external-id unique-external-id
```

### Verify KMS Key Permissions
```bash
# Check KMS key policy
AWS_PAGER="" aws kms get-key-policy \
  --key-id arn:aws:kms:region:account:key/key-id \
  --policy-name default
```

This comprehensive reference consolidates all DRS IAM knowledge for troubleshooting and configuration management.