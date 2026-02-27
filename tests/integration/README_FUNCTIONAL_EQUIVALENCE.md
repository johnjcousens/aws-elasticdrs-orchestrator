# Functional Equivalence Testing Guide

## Overview

This guide explains how to execute functional equivalence tests for the function-specific IAM roles implementation. The tests verify that all Lambda functions work identically with both unified and function-specific role configurations.

## Test Environment

- **Environment**: `qa`
- **Region**: `us-east-2`
- **Account**: `438465159935`
- **Stack**: `aws-drs-orchestration-qa`

## Prerequisites

### 1. AWS Credentials

Configure AWS credentials for account `438465159935`:

```bash
# Option 1: AWS CLI profile
export AWS_PROFILE=qa-account

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_SESSION_TOKEN=your_session_token  # If using temporary credentials
```

### 2. Test Data Setup

Run the test infrastructure setup script to create test data:

```bash
python tests/integration/setup_test_infrastructure.py
```

This creates:
- 2 test protection groups (`test-pg-001`, `test-pg-002`)
- 2 test recovery plans (`test-plan-001`, `test-plan-002`)
- 3 test target accounts
- 1 test execution history record

### 3. Verify QA Stack Configuration

Ensure the QA stack is deployed with `UseFunctionSpecificRoles=false` (unified role):

```bash
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-qa \
  --region us-east-2 \
  --query 'Stacks[0].Parameters[?ParameterKey==`UseFunctionSpecificRoles`].ParameterValue' \
  --output text
```

Expected output: `false`

## Test Execution

### Step 1: Execute Baseline Tests (Unified Role)

Run functional equivalence tests with the unified role configuration:

```bash
python tests/integration/test_functional_equivalence_unified.py
```

This script:
1. Verifies the QA environment configuration
2. Tests all 5 Lambda functions:
   - Query Handler (read operations)
   - Data Management Handler (CRUD operations)
   - Execution Handler (orchestration)
   - Orchestration Function (DRS operations)
   - Frontend Deployer (S3/CloudFront operations)
3. Records execution times and results
4. Checks CloudWatch Logs for AccessDenied errors
5. Saves results to `tests/integration/functional_equivalence_unified_results.json`

### Step 2: Review Results

Check the results file:

```bash
cat tests/integration/functional_equivalence_unified_results.json | jq .
```

Expected output structure:
```json
{
  "query_handler": {
    "function_name": "aws-drs-orchestration-query-handler-qa",
    "tests": [...],
    "access_denied_errors": [],
    "summary": {
      "total_tests": 2,
      "successful": 2,
      "failed": 0,
      "access_denied_count": 0
    }
  },
  "overall_summary": {
    "total_tests": 10,
    "successful": 10,
    "failed": 0,
    "total_access_denied_errors": 0
  }
}
```

### Step 3: Verify No AccessDenied Errors

Check CloudWatch Logs for all Lambda functions:

```bash
# Query Handler
AWS_PAGER="" aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-drs-orchestration-query-handler-qa \
  --region us-east-2 \
  --filter-pattern "AccessDenied" \
  --start-time $(date -u -d '5 minutes ago' +%s)000

# Data Management Handler
AWS_PAGER="" aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-drs-orchestration-data-management-handler-qa \
  --region us-east-2 \
  --filter-pattern "AccessDenied" \
  --start-time $(date -u -d '5 minutes ago' +%s)000

# Execution Handler
AWS_PAGER="" aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-drs-orchestration-execution-handler-qa \
  --region us-east-2 \
  --filter-pattern "AccessDenied" \
  --start-time $(date -u -d '5 minutes ago' +%s)000

# Orchestration Function
AWS_PAGER="" aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-drs-orchestration-dr-orch-sf-qa \
  --region us-east-2 \
  --filter-pattern "AccessDenied" \
  --start-time $(date -u -d '5 minutes ago' +%s)000

# Frontend Deployer
AWS_PAGER="" aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-drs-orchestration-frontend-deployer-qa \
  --region us-east-2 \
  --filter-pattern "AccessDenied" \
  --start-time $(date -u -d '5 minutes ago' +%s)000
```

Expected: No events found (empty results)

## Test Coverage

### Query Handler Tests

1. **List Protection Groups** (DynamoDB read)
   - Payload: `GET /protection-groups`
   - Expected: 200 OK with list of protection groups
   - Verifies: DynamoDB GetItem, Query, Scan permissions

2. **Get Protection Group Details** (DynamoDB read)
   - Payload: `GET /protection-groups/test-pg-001`
   - Expected: 200 OK with protection group details
   - Verifies: DynamoDB GetItem permission

### Data Management Handler Tests

1. **Create Protection Group** (DynamoDB write)
   - Payload: `POST /protection-groups`
   - Expected: 201 Created with new groupId
   - Verifies: DynamoDB PutItem permission

2. **Update Protection Group** (DynamoDB write)
   - Payload: `PUT /protection-groups/{groupId}`
   - Expected: 200 OK with updated group
   - Verifies: DynamoDB UpdateItem permission

3. **Delete Protection Group** (DynamoDB write)
   - Payload: `DELETE /protection-groups/{groupId}`
   - Expected: 204 No Content
   - Verifies: DynamoDB DeleteItem permission

### Execution Handler Tests

1. **Find Pending Executions** (DynamoDB read + Step Functions)
   - Payload: `{"operation": "find"}`
   - Expected: Success with list of pending executions
   - Verifies: DynamoDB Query, Step Functions DescribeExecution permissions

### Orchestration Function Tests

1. **Validate DRS Permissions** (DRS read)
   - Payload: `{"operation": "validate_permissions"}`
   - Expected: Success with permission validation results
   - Verifies: DRS Describe* permissions

### Frontend Deployer Tests

1. **Validate S3 Permissions** (S3 read)
   - Payload: `{"operation": "validate_permissions"}`
   - Expected: Success with permission validation results
   - Verifies: S3 ListBucket, GetObject permissions

## Success Criteria

For task 18.4 to be complete:

- ✅ All Lambda functions execute successfully
- ✅ All tests pass (no failures)
- ✅ No AccessDenied errors in CloudWatch Logs
- ✅ Execution times recorded for baseline comparison
- ✅ Results saved to JSON file

## Troubleshooting

### Issue: "Unable to locate credentials"

**Solution**: Configure AWS credentials as described in Prerequisites section.

### Issue: "Function not found"

**Solution**: Verify QA stack is deployed:
```bash
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-qa \
  --region us-east-2 \
  --query 'Stacks[0].StackStatus'
```

### Issue: "Table not found"

**Solution**: Run test infrastructure setup:
```bash
python tests/integration/setup_test_infrastructure.py
```

### Issue: AccessDenied errors during tests

**Solution**: This indicates IAM permission issues. Check:
1. Lambda function role ARN
2. IAM policy statements
3. Resource ARN patterns

## Next Steps

After completing task 18.4:

1. **Task 18.5**: Deploy stack update with `UseFunctionSpecificRoles=true`
2. **Task 18.6**: Execute functional equivalence tests with function-specific roles
3. **Task 18.7**: Execute negative security tests
4. **Task 18.8**: Test rollback capability

## Cleanup

After all testing is complete, clean up test data:

```bash
python tests/integration/setup_test_infrastructure.py --cleanup
```

This removes:
- Test protection groups
- Test recovery plans
- Test target accounts
- Test execution history
