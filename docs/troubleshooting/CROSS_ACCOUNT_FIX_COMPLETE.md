# Cross-Account Role Assumption Fix - Complete

**Date**: February 4, 2026  
**Status**: ✅ COMPLETE AND TESTED

## Problem Summary

Lambda functions were failing to assume cross-account roles when creating protection groups with servers in target accounts. The error was:
```
User: arn:aws:sts::777788889999:assumed-role/aws-drs-orchestration-orchestration-role-test/aws-drs-orchestration-data-management-handler-test 
is not authorized to perform: sts:AssumeRole on resource: arn:aws:iam::111122223333:role/DRSOrchestrationRole
```

## Root Causes

1. **ExternalId was dynamic per account** instead of standardized
2. **Missing externalId in account_context** in `apply_launch_config_to_servers` function
3. **DynamoDB had old ExternalId values** from before standardization

## Solution Implemented

### 1. Standardized ExternalId (Commit 365a1d84)

**Changed from**: `drs-orchestration-{TargetAccountId}` (varies per account)  
**Changed to**: `drs-orchestration-cross-account` (same for all accounts)

**Files Modified**:
- `cfn/cross-account-role-stack.yaml` - Hardcoded ExternalId parameter default
- `lambda/data-management-handler/index.py` - Line 1310: Added hardcoded externalId to account_context

### 2. Fixed Missing ExternalId in Launch Config Function (Commit 929b0848)

**Problem**: The `apply_launch_config_to_servers` function created `account_context` without `externalId`

**Fix**: Added `externalId: "drs-orchestration-cross-account"` to account_context at line 4857

**Why This Matters**: Protection group creation involves TWO role assumptions:
1. **Server Validation** (line 1310) - Had externalId ✓
2. **Launch Config Application** (line 4857) - Missing externalId ✗ (now fixed ✓)

### 3. Updated Cross-Account Role Stacks

**Target Account (111122223333)**:
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

**Orchestration Account (777788889999)**:
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

### 4. Updated DynamoDB Target Accounts Table

```bash
aws dynamodb update-item \
  --table-name aws-drs-orchestration-target-accounts-test \
  --key '{"accountId": {"S": "111122223333"}}' \
  --update-expression "SET externalId = :newExternalId" \
  --expression-attribute-values '{":newExternalId": {"S": "drs-orchestration-cross-account"}}'
```

## Testing

### Test Scenario
- **Target Account**: 111122223333 (DEMO_TARGET)
- **Staging Account**: 777788889999 (DEMO_ONPREM - also orchestration account)
- **Region**: us-west-2
- **Servers**: 8 total
  - 2 native to target account
  - 6 extended source servers from staging account

### Test Method: Direct Lambda Invocation

```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload file://test-create-pg-cross-account.json \
  response-pg-create.json
```

**Test Payload**:
```json
{
  "operation": "create_protection_group",
  "body": {
    "groupName": "Test Cross-Account PG",
    "region": "us-west-2",
    "accountId": "111122223333",
    "assumeRoleName": "DRSOrchestrationRole",
    "sourceServerIds": [
      "s-5d4817d71be01af24",
      "s-53badf746d9e8e5e7",
      "s-5eb9be9ac40cc72ef",
      "s-5b4011e505ce3384d",
      "s-513e8dd2d3858552e",
      "s-53cf17a60f22e0510",
      "s-5e80aa027512a4768",
      "s-52aa730dc1b57e5bb"
    ]
  }
}
```

### Test Results

✅ **SUCCESS** - Status Code: 201 Created

**Lambda Logs**:
```
Creating cross-account DRS client for account 111122223333 using role DRSOrchestrationRole
Assuming role: arn:aws:iam::111122223333:role/DRSOrchestrationRole
Using External ID for role assumption
Successfully created cross-account DRS client for account 111122223333
Creating Protection Group: f364d248-d1bf-4039-9f32-7a2b033e5ecd
```

**DynamoDB Verification**:
```json
{
  "groupId": "f364d248-d1bf-4039-9f32-7a2b033e5ecd",
  "groupName": "Test Cross-Account PG",
  "region": "us-west-2",
  "accountId": "111122223333",
  "serverCount": 8
}
```

## Architecture

```
Orchestration Account (777788889999)
├── Lambda: data-management-handler
│   ├── Server Validation (line 1310)
│   │   └── externalId: "drs-orchestration-cross-account" ✓
│   └── Launch Config Application (line 4857)
│       └── externalId: "drs-orchestration-cross-account" ✓
│
├── Cross-Account Role: DRSOrchestrationRole
│   └── ExternalId: "drs-orchestration-cross-account"
│
└── Assumes role in target account ↓

Target Account (111122223333)
├── Cross-Account Role: DRSOrchestrationRole
│   ├── ExternalId: "drs-orchestration-cross-account"
│   └── Trust Policy: Allows 777788889999:root with ExternalId
│
└── DRS Source Servers (8 total)
    ├── Native: 2 servers
    └── Extended: 6 servers from staging account
```

## Key Learnings

1. **ExternalId must be consistent**: Using a hardcoded value simplifies configuration and eliminates per-account lookups

2. **Multiple role assumptions in one operation**: Protection group creation involves multiple cross-account calls - all must have externalId

3. **Extended source servers**: Launch configurations are applied in the target account where recovery happens, not the staging account where servers originate

4. **Testing approach**: Direct Lambda invocation tests the actual customer use case better than UI testing

## Files Modified

1. `cfn/cross-account-role-stack.yaml` - ExternalId standardization
2. `lambda/data-management-handler/index.py` - Two locations:
   - Line 1310: Server validation account_context
   - Line 4857: Launch config application account_context
3. `lambda/shared/cross_account.py` - Already had proper ExternalId handling

## Deployment Commands

```bash
# 1. Deploy Lambda changes
./scripts/deploy.sh test --lambda-only

# 2. Update cross-account roles (already done)
# 3. Update DynamoDB (already done)
```

## Verification Steps

1. ✅ Cross-account role trust policies verified
2. ✅ DynamoDB Target Accounts table updated
3. ✅ Lambda code deployed with externalId in both locations
4. ✅ Direct Lambda invocation test passed
5. ✅ Protection group created successfully with 8 servers

## Related Documentation

- [ExternalId Standardization Complete](EXTERNAL_ID_STANDARDIZATION_COMPLETE.md)
- [Cross-Account Assume Role Fix](CROSS_ACCOUNT_ASSUME_ROLE_FIX.md)
- [Protection Group Creation Debug](PROTECTION_GROUP_CREATION_DEBUG.md)

## Customer Impact

This fix enables customers to:
- Create protection groups with servers in target accounts via direct Lambda invocation
- Use the orchestration role to manage cross-account DRS operations
- Support extended source servers from staging accounts
- Apply launch configurations to servers in target accounts

The solution works as designed for customer deployments using direct Lambda invocation patterns.
