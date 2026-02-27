# Task 18.8: Rollback Capability Test Guide

## Overview

This guide documents the execution of Task 18.8, which tests the rollback capability from function-specific IAM roles (UseFunctionSpecificRoles=true) to the unified IAM role (UseFunctionSpecificRoles=false).

## Test Objective

Verify that rolling back from function-specific roles to unified role:
1. Preserves all DynamoDB data (no item loss)
2. Does not interrupt running Step Functions executions
3. Successfully switches all Lambda functions to unified role
4. Updates CloudFormation parameter to UseFunctionSpecificRoles=false

## Environment

- **Stack**: `aws-drs-orchestration-qa`
- **Region**: `us-east-2`
- **Account**: `438465159935`
- **Current State**: UseFunctionSpecificRoles=true (function-specific roles active)
- **Target State**: UseFunctionSpecificRoles=false (unified role active)

## Test Components

### 1. Rollback Capability Test (`test_rollback_capability.py`)

Main test script that:
- Captures pre-rollback state (DynamoDB counts, Lambda roles, Step Functions executions)
- Executes rollback deployment via `./scripts/deploy-main-stack.sh qa`
- Captures post-rollback state
- Verifies rollback results
- Saves detailed results to `rollback_capability_results.json`

### 2. Property 17 Test (`test_property_17_rollback.py`)

Property-based test that validates:
- **Property 17a**: DynamoDB data preserved
- **Property 17b**: Lambda functions use unified role
- **Property 17c**: Step Functions executions not interrupted
- **Property 17d**: CloudFormation parameter updated
- **Property 17**: Overall rollback success

## Execution Steps

### Prerequisites

1. **Verify QA stack is deployed with function-specific roles**:
   ```bash
   AWS_PAGER="" aws cloudformation describe-stacks \
     --stack-name aws-drs-orchestration-qa \
     --region us-east-2 \
     --query 'Stacks[0].Parameters[?ParameterKey==`UseFunctionSpecificRoles`].ParameterValue' \
     --output text
   ```
   Expected output: `true`

2. **Verify Lambda functions are using function-specific roles**:
   ```bash
   AWS_PAGER="" aws lambda get-function \
     --function-name aws-drs-orchestration-query-handler-qa \
     --region us-east-2 \
     --query 'Configuration.Role'
   ```
   Expected: Role ARN should contain `query-handler-role`

3. **Activate Python virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

### Step 1: Execute Rollback Capability Test

```bash
# Run the rollback test
.venv/bin/python tests/integration/test_rollback_capability.py
```

**What this does**:
1. Verifies environment (correct account, region, stack exists)
2. Captures pre-rollback state:
   - DynamoDB table item counts
   - Lambda function role ARNs
   - Active Step Functions executions
   - CloudFormation parameters
3. Executes rollback deployment:
   - Runs `./scripts/deploy-main-stack.sh qa`
   - Waits for CloudFormation stack update to complete
4. Captures post-rollback state (same metrics as pre-rollback)
5. Verifies rollback results:
   - DynamoDB item counts match
   - Lambda functions use unified role
   - Step Functions executions not interrupted
   - CloudFormation parameter updated to 'false'
6. Saves results to `tests/integration/rollback_capability_results.json`

**Expected Duration**: 15-30 minutes (CloudFormation stack update)

**Expected Output**:
```
================================================================================
ROLLBACK TEST SUMMARY
================================================================================
✓ PASS: dynamodb_data_preserved
✓ PASS: lambda_functions_use_unified_role
✓ PASS: stepfunctions_executions_not_interrupted
✓ PASS: cloudformation_parameter_updated
================================================================================
✓ Rollback test PASSED - All checks successful!
```

### Step 2: Run Property 17 Tests

```bash
# Run property-based tests
.venv/bin/pytest tests/integration/test_property_17_rollback.py -v
```

**What this does**:
1. Loads results from `rollback_capability_results.json`
2. Runs 5 property tests:
   - `test_property_17_dynamodb_data_preserved`
   - `test_property_17_lambda_functions_use_unified_role`
   - `test_property_17_stepfunctions_executions_not_interrupted`
   - `test_property_17_cloudformation_parameter_updated`
   - `test_property_17_overall_rollback_success`
3. Each test verifies a specific aspect of Property 17

**Expected Output**:
```
tests/integration/test_property_17_rollback.py::test_property_17_dynamodb_data_preserved PASSED
tests/integration/test_property_17_rollback.py::test_property_17_lambda_functions_use_unified_role PASSED
tests/integration/test_property_17_rollback.py::test_property_17_stepfunctions_executions_not_interrupted PASSED
tests/integration/test_property_17_rollback.py::test_property_17_cloudformation_parameter_updated PASSED
tests/integration/test_property_17_rollback.py::test_property_17_overall_rollback_success PASSED

============================== 5 passed in 0.50s ===============================
```

### Step 3: Re-run Functional Equivalence Tests

```bash
# Run functional equivalence tests with unified role
.venv/bin/python tests/integration/test_functional_equivalence_function_specific.py
```

**What this does**:
1. Executes all Lambda functions with unified role configuration
2. Verifies operations succeed (same as Task 18.6)
3. Checks for AccessDenied errors in CloudWatch Logs
4. Saves results to `functional_equivalence_function_specific_results.json`

**Expected Output**:
```
================================================================================
OVERALL SUMMARY
================================================================================
Total Tests: 8
Successful: 8
Failed: 0
AccessDenied Errors: 0
================================================================================
✓ All tests passed with no AccessDenied errors!
```

## Verification Checklist

After completing all steps, verify:

- [ ] Rollback capability test passed all checks
- [ ] Property 17 tests all passed (5/5)
- [ ] Functional equivalence tests passed with unified role
- [ ] No DynamoDB data loss (item counts match)
- [ ] No Step Functions executions interrupted
- [ ] All Lambda functions use unified role
- [ ] CloudFormation parameter UseFunctionSpecificRoles=false
- [ ] No AccessDenied errors in CloudWatch Logs

## Post-Test Verification Commands

### Verify Unified Role in Use

```bash
# Check Query Handler role
AWS_PAGER="" aws lambda get-function \
  --function-name aws-drs-orchestration-query-handler-qa \
  --region us-east-2 \
  --query 'Configuration.Role'

# Expected: arn:aws:iam::438465159935:role/aws-drs-orchestration-unified-role-qa
```

### Verify CloudFormation Parameter

```bash
# Check stack parameters
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-qa \
  --region us-east-2 \
  --query 'Stacks[0].Parameters[?ParameterKey==`UseFunctionSpecificRoles`]'

# Expected: ParameterValue: "false"
```

### Verify DynamoDB Tables

```bash
# Check protection groups table
AWS_PAGER="" aws dynamodb scan \
  --table-name aws-drs-orchestration-protection-groups-qa \
  --region us-east-2 \
  --select COUNT

# Compare Count with pre-rollback state
```

### Check CloudWatch Logs for Errors

```bash
# Check for AccessDenied errors in last 30 minutes
AWS_PAGER="" aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-drs-orchestration-query-handler-qa \
  --region us-east-2 \
  --filter-pattern "AccessDenied" \
  --start-time $(($(date +%s) - 1800))000

# Expected: No events found
```

## Troubleshooting

### Rollback Deployment Fails

**Symptom**: `./scripts/deploy-main-stack.sh qa` fails

**Resolution**:
1. Check CloudFormation stack events:
   ```bash
   AWS_PAGER="" aws cloudformation describe-stack-events \
     --stack-name aws-drs-orchestration-qa \
     --region us-east-2 \
     --max-items 20
   ```
2. Look for CREATE_FAILED or UPDATE_FAILED events
3. Check nested stack failures
4. Review CloudWatch Logs for Lambda errors

### DynamoDB Data Loss Detected

**Symptom**: Pre-rollback and post-rollback item counts don't match

**Resolution**:
1. Verify no manual deletions occurred during rollback
2. Check DynamoDB table streams for delete events
3. Review CloudFormation stack events for table replacements
4. If data loss confirmed, restore from backup or rollback CloudFormation

### Lambda Functions Not Using Unified Role

**Symptom**: Lambda functions still reference function-specific roles

**Resolution**:
1. Verify CloudFormation stack update completed successfully
2. Check IAM stack nested stack status
3. Verify unified role exists:
   ```bash
   AWS_PAGER="" aws iam get-role \
     --role-name aws-drs-orchestration-unified-role-qa
   ```
4. If role doesn't exist, CloudFormation update may have failed

### Step Functions Executions Interrupted

**Symptom**: Running executions stopped during rollback

**Resolution**:
1. Check Step Functions execution history
2. Review CloudWatch Logs for execution errors
3. Verify state machine definition not modified
4. Check if executions failed due to Lambda errors (not rollback)

## Success Criteria

Task 18.8 is complete when:

1. ✅ Rollback capability test passes all checks
2. ✅ Property 17 tests pass (5/5)
3. ✅ Functional equivalence tests pass with unified role
4. ✅ No DynamoDB data loss
5. ✅ No Step Functions executions interrupted
6. ✅ All Lambda functions use unified role
7. ✅ CloudFormation parameter updated to 'false'
8. ✅ No AccessDenied errors in CloudWatch Logs

## Related Files

- `tests/integration/test_rollback_capability.py` - Main rollback test
- `tests/integration/test_property_17_rollback.py` - Property 17 tests
- `tests/integration/rollback_capability_results.json` - Test results (generated)
- `tests/integration/test_functional_equivalence_function_specific.py` - Functional equivalence tests
- `scripts/deploy-main-stack.sh` - Deployment script

## Requirements Validated

- **Requirement 11.2**: Rollback from function-specific to unified roles completes without data loss
- **Requirement 11.3**: DynamoDB data preserved during rollback
- **Requirement 11.4**: Step Functions executions not interrupted during rollback
- **Requirement 11.5**: Lambda functions immediately use unified role after rollback
