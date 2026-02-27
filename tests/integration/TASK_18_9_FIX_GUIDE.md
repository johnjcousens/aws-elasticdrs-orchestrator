# Task 18.9: Fix ExternalId Mismatch

## Problem

The integration test `test_assume_role_succeeds_with_correct_external_id` is failing because:

1. **DynamoDB has correct ExternalId**: `aws-drs-orchestration-qa`
2. **Target account CloudFormation stack has default ExternalId**: `drs-orchestration-cross-account`

The CloudFormation template `cfn/drs-target-account-setup-stack.yaml` has a default value on line 32:

```yaml
ExternalId:
  Description: 'External ID for secure cross-account access'
  Type: String
  Default: 'drs-orchestration-cross-account'  # <-- This is the problem
```

When the stack was deployed in the target account, it used this default value instead of the QA-specific value.

## Solution

Update the CloudFormation stack in the target account (160885257264) with the correct ExternalId parameter.

### Option 1: Update Stack via AWS Console (Recommended)

1. Log into target account 160885257264
2. Navigate to CloudFormation console
3. Find the stack (likely named `drs-target-account-setup` or similar)
4. Click "Update"
5. Select "Use current template"
6. In Parameters section, change `ExternalId` from `drs-orchestration-cross-account` to `aws-drs-orchestration-qa`
7. Review and update the stack

### Option 2: Update Stack via AWS CLI

```bash
# In target account 160885257264
aws cloudformation update-stack \
  --stack-name <stack-name> \
  --use-previous-template \
  --parameters \
    ParameterKey=OrchestrationAccountId,UsePreviousValue=true \
    ParameterKey=ExternalId,ParameterValue=aws-drs-orchestration-qa \
    ParameterKey=ProjectName,UsePreviousValue=true \
    ParameterKey=Environment,UsePreviousValue=true \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-2
```

### Option 3: Update Staging Account Stack

The staging account (664418995426) also needs the same fix:

```bash
# In staging account 664418995426
aws cloudformation update-stack \
  --stack-name <stack-name> \
  --use-previous-template \
  --parameters \
    ParameterKey=OrchestrationAccountId,UsePreviousValue=true \
    ParameterKey=ExternalId,ParameterValue=aws-drs-orchestration-qa \
    ParameterKey=ProjectName,UsePreviousValue=true \
    ParameterKey=Environment,UsePreviousValue=true \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-2
```

## Verification

After updating the stack, verify the trust policy:

```bash
# In target account 160885257264
AWS_PAGER="" aws iam get-role \
  --role-name DRSOrchestrationRole \
  --query 'Role.AssumeRolePolicyDocument' \
  --region us-east-2
```

Expected output should show:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::438465159935:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "aws-drs-orchestration-qa"
        }
      }
    }
  ]
}
```

## Re-run Tests

After fixing the ExternalId in both accounts, re-run the integration tests:

```bash
source .venv/bin/activate
AWS_PROFILE=438465159935_AdministratorAccess AWS_PAGER="" python -m pytest tests/integration/test_external_id_validation.py -v -s
```

Expected result: All 5 tests should PASS.

## Current Status

**DynamoDB**: ✅ Correct
- Account 160885257264: `externalId: aws-drs-orchestration-qa`
- Account 664418995426: `externalId: aws-drs-orchestration-qa`

**CloudFormation Stacks**: ❌ Need Update
- Account 160885257264: Stack deployed with default `drs-orchestration-cross-account`
- Account 664418995426: Stack deployed with default `drs-orchestration-cross-account`

**Action Required**: Update both CloudFormation stacks with correct ExternalId parameter.
