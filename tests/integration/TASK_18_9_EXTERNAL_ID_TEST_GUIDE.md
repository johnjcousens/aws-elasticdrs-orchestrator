# Task 18.9: Cross-Account ExternalId Validation Test Guide

## Overview

This guide explains how to execute integration tests for cross-account ExternalId validation (Task 18.9).

## Test Files Created

1. **`test_external_id_validation.py`** - Integration tests for ExternalId validation
   - Tests that target accounts have externalId configured
   - Tests ExternalId format matches `{ProjectName}-{Environment}`
   - Tests AssumeRole succeeds with correct ExternalId
   - Tests AssumeRole fails with incorrect ExternalId (AccessDenied)
   - Tests AssumeRole fails without ExternalId (AccessDenied)

2. **`test_external_id_property.py`** - Property-based tests for Property 18
   - Property 18: Cross-Account ExternalId Validation
   - Generates various ExternalId values (correct, incorrect, malformed)
   - Verifies success only when ExternalId matches expected format
   - Verifies AccessDenied for all other cases

## Requirements Validated

- **Requirement 10.2**: ExternalId required for STS AssumeRole operations
- **Requirement 10.3**: ExternalId must match `{ProjectName}-{Environment}`
- **Requirement 10.4**: AssumeRole fails with AccessDenied when ExternalId is incorrect

## Test Environment

- **Stack**: `aws-drs-orchestration-qa`
- **Region**: `us-east-2`
- **Account**: `438465159935`
- **Target Accounts Table**: `aws-drs-orchestration-target-accounts-qa`
- **Expected ExternalId**: `aws-drs-orchestration-qa`

## Prerequisites

### 1. AWS Credentials

You must have valid AWS credentials configured for the QA account (438465159935):

```bash
# Option 1: AWS CLI profile
export AWS_PROFILE=qa-profile

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_SESSION_TOKEN=your-session-token  # If using temporary credentials

# Option 3: AWS SSO
aws sso login --profile qa-profile
export AWS_PROFILE=qa-profile
```

### 2. IAM Permissions Required

Your AWS credentials must have the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:Scan",
        "dynamodb:GetItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-target-accounts-qa"
    },
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::*:role/DRSOrchestrationRole"
    }
  ]
}
```

### 3. Target Account Configuration

Target accounts must have:
- `roleArn` configured in DynamoDB table
- `externalId` configured in DynamoDB table (value: `aws-drs-orchestration-qa`)
- Trust policy in target account role requiring ExternalId

Example target account trust policy:

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

## Running the Tests

### Integration Tests

```bash
# Run all ExternalId validation tests
AWS_PAGER="" python -m pytest tests/integration/test_external_id_validation.py -v -s

# Run specific test
AWS_PAGER="" python -m pytest tests/integration/test_external_id_validation.py::test_assume_role_succeeds_with_correct_external_id -v -s
```

### Property-Based Tests

```bash
# Run Property 18 tests
AWS_PAGER="" python -m pytest tests/integration/test_external_id_property.py -v -s

# Run with more examples (default is 20)
AWS_PAGER="" python -m pytest tests/integration/test_external_id_property.py -v -s --hypothesis-max-examples=50
```

## Expected Test Results

### Successful Test Run

```
tests/integration/test_external_id_validation.py::test_target_accounts_have_external_id PASSED
tests/integration/test_external_id_validation.py::test_external_id_format_matches_project_environment PASSED
tests/integration/test_external_id_validation.py::test_assume_role_succeeds_with_correct_external_id PASSED
tests/integration/test_external_id_validation.py::test_assume_role_fails_with_incorrect_external_id PASSED
tests/integration/test_external_id_validation.py::test_assume_role_fails_without_external_id PASSED

5 passed in X.XXs
```

### Test Output Details

Each test provides detailed output:

```
Testing AssumeRole with correct ExternalId:
  Account: 160885257264 (DEMO_TARGET)
  Role ARN: arn:aws:iam::160885257264:role/DRSOrchestrationRole
  ExternalId: aws-drs-orchestration-qa
✓ AssumeRole succeeded with correct ExternalId
  Session: [ASSUMED_ROLE_ID]:test-external-id-validation

Testing AssumeRole with incorrect ExternalId:
  Account: 160885257264 (DEMO_TARGET)
  Role ARN: arn:aws:iam::160885257264:role/DRSOrchestrationRole
  Incorrect ExternalId: incorrect-external-id-12345
✓ AssumeRole correctly failed with AccessDenied
  Error: AccessDenied
  Message: User: arn:aws:sts::438465159935:assumed-role/... is not authorized to perform: sts:AssumeRole on resource: arn:aws:iam::160885257264:role/DRSOrchestrationRole
```

## Troubleshooting

### Error: UnrecognizedClientException

```
botocore.exceptions.ClientError: An error occurred (UnrecognizedClientException) when calling the Scan operation: The security token included in the request is invalid.
```

**Solution**: Configure valid AWS credentials (see Prerequisites section above).

### Error: AccessDenied on DynamoDB Scan

```
botocore.exceptions.ClientError: An error occurred (AccessDeniedException) when calling the Scan operation: User: ... is not authorized to perform: dynamodb:Scan on resource: ...
```

**Solution**: Ensure your IAM user/role has `dynamodb:Scan` permission on the target accounts table.

### Error: No target accounts found

```
AssertionError: No target accounts found in DynamoDB table
```

**Solution**: Verify target accounts are configured in the DynamoDB table with `roleArn` and `externalId` fields.

### Error: AssumeRole succeeded with incorrect ExternalId

```
AssertionError: AssumeRole succeeded with incorrect ExternalId: 'incorrect-external-id-12345'. Expected only 'aws-drs-orchestration-qa' to succeed. This indicates the target account trust policy is not enforcing ExternalId validation.
```

**Solution**: Update the target account role trust policy to require ExternalId in the Condition block (see example above).

### Error: AssumeRole failed with correct ExternalId

```
Failed: AssumeRole failed with correct ExternalId: 'aws-drs-orchestration-qa'
  Error: AccessDenied
  Message: User: ... is not authorized to perform: sts:AssumeRole on resource: ...
  This indicates the target account trust policy may not be configured correctly
```

**Solution**: Verify:
1. Target account role exists
2. Trust policy allows the QA account (438465159935) to assume the role
3. ExternalId in trust policy matches `aws-drs-orchestration-qa`
4. Your IAM user/role has `sts:AssumeRole` permission

## Implementation Details

### ExternalId Flow

1. **Storage**: ExternalId is stored in the target accounts DynamoDB table
2. **Retrieval**: `determine_target_account_context()` retrieves externalId from DynamoDB
3. **Usage**: `get_cross_account_session()` passes externalId to STS AssumeRole
4. **Validation**: Target account trust policy enforces ExternalId match

### Code References

- **Lambda Code**: `lambda/shared/cross_account.py`
  - `get_cross_account_session()` - Passes ExternalId to STS
  - `determine_target_account_context()` - Retrieves ExternalId from DynamoDB
  - `create_drs_client()` - Uses ExternalId for cross-account DRS operations

- **Account Utils**: `lambda/shared/account_utils.py`
  - Account management utilities
  - ExternalId format validation

### Property 18 Validation

**Property 18: Cross-Account ExternalId Validation**

For any STS AssumeRole operation and any ExternalId value, when a Lambda function attempts to assume a cross-account role, the operation should succeed if the ExternalId matches `{ProjectName}-{Environment}`, and the operation should fail with AccessDenied if the ExternalId does not match.

**Validates: Requirements 10.2, 10.3, 10.4**

## Test Coverage

### Integration Tests (test_external_id_validation.py)

1. ✅ Target accounts have externalId configured (Req 10.2)
2. ✅ ExternalId format matches `{ProjectName}-{Environment}` (Req 10.3)
3. ✅ AssumeRole succeeds with correct ExternalId (Req 10.2)
4. ✅ AssumeRole fails with incorrect ExternalId (Req 10.4)
5. ✅ AssumeRole fails without ExternalId (Req 10.2)

### Property-Based Tests (test_external_id_property.py)

1. ✅ Property 18: ExternalId validation across various inputs (Req 10.2, 10.3, 10.4)
2. ✅ ExternalId format generation and validation (Req 10.3)

## Next Steps

After successful test execution:

1. Mark Task 18.9 as complete
2. Update task status in `.kiro/specs/function-specific-iam-roles/tasks.md`
3. Document test results in task completion notes
4. Proceed to next task in the implementation plan

## Related Documentation

- **Design Document**: `.kiro/specs/function-specific-iam-roles/design.md` (Property 18)
- **Requirements**: `.kiro/specs/function-specific-iam-roles/requirements.md` (Req 10.2, 10.3, 10.4)
- **Tasks**: `.kiro/specs/function-specific-iam-roles/tasks.md` (Task 18.9)
- **Functional Equivalence Summary**: `tests/integration/TASK_18_6_FUNCTIONAL_EQUIVALENCE_SUMMARY.md`
