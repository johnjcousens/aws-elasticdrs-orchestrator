# ExternalId Standardization - Complete

**Date**: February 4, 2026  
**Status**: ✅ Complete

## Problem

The cross-account role ExternalId was dynamically generated per account using the format `drs-orchestration-{TargetAccountId}`, which meant:
- Each target/staging account had a different ExternalId
- Backend Lambda needed to look up ExternalId from DynamoDB for each account
- Added complexity and potential for configuration errors

## Solution

Standardized ExternalId to a single hardcoded value across all accounts:
- **ExternalId**: `drs-orchestration-cross-account` (same for all accounts)
- **Role Name**: `DRSOrchestrationRole` (already standardized)

This makes the ExternalId predictable for the backend without requiring DynamoDB lookups.

## Changes Made

### 1. CloudFormation Template (`cfn/cross-account-role-stack.yaml`)

**Before:**
```yaml
ExternalId:
  Default: 'USE_AUTO_GENERATED'

# Generated as: ${ProjectName}-${AWS::AccountId}
# Result: drs-orchestration-111122223333 (varies per account)
```

**After:**
```yaml
ExternalId:
  Default: 'drs-orchestration-cross-account'

# Hardcoded value, same for all accounts
```

### 2. Lambda Code (`lambda/data-management-handler/index.py`)

**Before:**
```python
account_context = {
    "accountId": target_account_id,
    "assumeRoleName": body.get("assumeRoleName"),
    "isCurrentAccount": (current_account_id == target_account_id),
    "externalId": f"drs-orchestration-{current_account_id}",  # Dynamic
}
```

**After:**
```python
account_context = {
    "accountId": target_account_id,
    "assumeRoleName": body.get("assumeRoleName"),
    "isCurrentAccount": (current_account_id == target_account_id),
    "externalId": "drs-orchestration-cross-account",  # Hardcoded
}
```

### 3. Stack Deployments

Updated cross-account role stacks in both accounts:

**Target Account (111122223333):**
```bash
aws cloudformation deploy \
  --template-file cfn/cross-account-role-stack.yaml \
  --stack-name drs-cross-account-role \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    OrchestrationAccountId=777788889999 \
    ExternalId=drs-orchestration-cross-account \
  --region us-east-1
```

**Orchestration/Staging Account (777788889999):**
```bash
aws cloudformation deploy \
  --template-file cfn/cross-account-role-stack.yaml \
  --stack-name drs-orchestration-cross-account-role-self \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    OrchestrationAccountId=777788889999 \
    ExternalId=drs-orchestration-cross-account \
  --region us-east-1
```

### 4. Lambda Deployment

```bash
./scripts/deploy.sh test --lambda-only
```

## Verification

### Cross-Account Role in Target Account (111122223333)
```bash
$ aws cloudformation describe-stacks \
    --stack-name drs-cross-account-role \
    --query 'Stacks[0].Outputs[?OutputKey==`ExternalId`].OutputValue' \
    --output text

drs-orchestration-cross-account ✅
```

### Cross-Account Role in Orchestration Account (777788889999)
```bash
$ aws cloudformation describe-stacks \
    --stack-name drs-orchestration-cross-account-role-self \
    --query 'Stacks[0].Outputs[?OutputKey==`ExternalId`].OutputValue' \
    --output text

drs-orchestration-cross-account ✅
```

## Benefits

1. **Predictable**: Backend always knows the ExternalId without lookups
2. **Simple**: No dynamic generation or per-account configuration
3. **Consistent**: Same value across all target and staging accounts
4. **Maintainable**: Easy to understand and document

## Architecture

```
Orchestration Account (777788889999)
├── Lambda: data-management-handler
│   └── Uses: externalId = "drs-orchestration-cross-account"
│
├── Cross-Account Role: DRSOrchestrationRole
│   └── ExternalId: "drs-orchestration-cross-account"
│
└── Assumes roles in target accounts ↓

Target Account (111122223333)
└── Cross-Account Role: DRSOrchestrationRole
    └── ExternalId: "drs-orchestration-cross-account"
    └── Trust Policy: Allows 777788889999 with ExternalId
```

## Next Steps

1. ✅ Cross-account roles updated in both accounts
2. ✅ Lambda code deployed with hardcoded ExternalId
3. ⏳ Test protection group creation via UI with cross-account servers
4. ⏳ Verify Lambda logs show successful role assumption

## Testing

To test the fix:

1. Navigate to CloudFront URL: https://d1kqe40a9vwn47.cloudfront.net
2. Create a protection group with servers from target account (111122223333)
3. Verify in Lambda logs that role assumption succeeds
4. Check for successful server validation

Expected log output:
```
Assuming role: arn:aws:iam::111122223333:role/DRSOrchestrationRole
Using External ID for role assumption
Successfully created cross-account DRS client for account 111122223333
```

## Related Documentation

- [Cross-Account Assume Role Fix](CROSS_ACCOUNT_ASSUME_ROLE_FIX.md)
- [Protection Group Creation Debug](PROTECTION_GROUP_CREATION_DEBUG.md)
- [Cross-Account Role Stack](../../cfn/cross-account-role-stack.yaml)

## Git Commit

```
commit 365a1d84
fix: standardize ExternalId to hardcoded value for all cross-account roles

- Changed ExternalId from dynamic (per-account) to hardcoded: drs-orchestration-cross-account
- Updated cfn/cross-account-role-stack.yaml to use fixed ExternalId
- Updated Lambda data-management-handler to use hardcoded ExternalId
- This makes ExternalId predictable for backend without DynamoDB lookup
- Role name remains standardized: DRSOrchestrationRole
```
