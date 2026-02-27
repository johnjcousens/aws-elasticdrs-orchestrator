# Staging Account Sync - IAM Requirements

## Overview

The staging account sync feature requires specific IAM permissions in **target accounts** (not just the orchestration account). This document explains the cross-account IAM configuration needed for staging account sync to work.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Orchestration Account (Hub)                    │
│                                                                 │
│  Lambda (data-management-handler)                              │
│    ↓ Assumes Role                                              │
│    ↓                                                            │
└────┼────────────────────────────────────────────────────────────┘
     │
     │ STS AssumeRole
     ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Target Account (Spoke)                       │
│                                                                 │
│  DRSOrchestrationRole (assumed by orchestration Lambda)        │
│    ↓ Calls DRS API                                             │
│    ↓                                                            │
│  DRS Service                                                    │
│    ↓ CreateExtendedSourceServer                                │
│    ↓                                                            │
│  Extended Source Servers (created in target account)           │
└─────────────────────────────────────────────────────────────────┘
```

## Required IAM Permissions

### Target Account: DRSOrchestrationRole

The cross-account role in **each target account** must have these DRS permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "drs:CreateExtendedSourceServer",
        "drs:DescribeSourceServers",
        "drs:ListExtensibleSourceServers",
        "drs:ListStagingAccounts",
        "drs:StartRecovery",
        "drs:TerminateRecoveryInstances",
        "drs:UpdateLaunchConfiguration",
        "drs:GetLaunchConfiguration",
        "drs:DescribeJobs",
        "drs:DescribeRecoveryInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

**Critical Permission**: `drs:CreateExtendedSourceServer` is required for staging account sync to work.

### Orchestration Account: Lambda Execution Role

The orchestration Lambda's role needs permission to **assume** the target account role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::*:role/DRSOrchestrationRole"
    }
  ]
}
```

This is already configured in `cfn/master-template.yaml` (STSAccess policy).

## Deployment

### Option 1: Using CloudFormation Template

Deploy the cross-account role stack in each target account:

```bash
aws cloudformation deploy \
  --template-file cfn/cross-account-role.yaml \
  --stack-name drs-orchestration-cross-account-role \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    OrchestrationAccountId=438465159935 \
    ExternalId=your-external-id
```

### Option 2: Manual IAM Policy Update

If you already have a `DRSOrchestrationRole` in your target accounts:

1. Navigate to IAM Console in the target account
2. Find the `DRSOrchestrationRole` role
3. Add the `drs:CreateExtendedSourceServer` permission to the policy
4. Verify the trust relationship allows the orchestration account to assume the role

## Verification

### Test Cross-Account Access

```bash
# From orchestration account, test assuming the target account role
aws sts assume-role \
  --role-arn arn:aws:iam::TARGET_ACCOUNT_ID:role/DRSOrchestrationRole \
  --role-session-name test-session \
  --external-id your-external-id
```

### Test DRS Permissions

```bash
# Using assumed role credentials, test CreateExtendedSourceServer permission
aws drs create-extended-source-server \
  --source-server-arn arn:aws:drs:us-east-1:STAGING_ACCOUNT:source-server/s-xxxxx \
  --region us-east-1
```

## Troubleshooting

### Error: AccessDeniedException on CreateExtendedSourceServer

**Symptom**: CloudWatch logs show:
```
Failed to extend server s-xxxxx: An error occurred (AccessDeniedException) 
when calling the CreateExtendedSourceServer operation: Error in Authorization
```

**Root Cause**: The target account's `DRSOrchestrationRole` is missing the `drs:CreateExtendedSourceServer` permission.

**Solution**: Add the permission to the target account's IAM role policy (see above).

### Error: AccessDenied on AssumeRole

**Symptom**: CloudWatch logs show:
```
Failed to assume role arn:aws:iam::TARGET_ACCOUNT:role/DRSOrchestrationRole: 
An error occurred (AccessDenied) when calling the AssumeRole operation
```

**Root Cause**: Trust relationship not configured correctly in target account.

**Solution**: Update the trust policy on `DRSOrchestrationRole` in the target account:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::438465159935:role/aws-drs-orchestration-orchestration-role-qa"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "your-external-id"
        }
      }
    }
  ]
}
```

## Related Documentation

- [Cross-Account Setup Guide](../README.md#cross-account-setup)
- [Staging Account Configuration](../README.md#staging-accounts)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
