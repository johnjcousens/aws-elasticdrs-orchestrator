# Task 18.7: Negative Security Tests Execution Guide

## Overview

Task 18.7 implements **Property 16: Security Validation Through Negative Testing** using property-based testing with Hypothesis. The test suite verifies that function-specific IAM roles properly deny unauthorized operations.

**Status**: Test implementation complete, awaiting AWS credentials for execution

**Test File**: `tests/integration/test_negative_security_property.py`

**Requirements Validated**: 9.14, 9.15, 9.16, 9.17, 9.18, 9.19

## Test Implementation Summary

### Property-Based Tests (10 tests, 100 iterations each)

#### Query Handler Restrictions (3 tests)
1. **test_property_query_handler_cannot_write_dynamodb**
   - Validates: Requirement 9.14
   - Tests: DynamoDB PutItem operations fail with AccessDenied
   - Iterations: 100 with generated table names and items

2. **test_property_query_handler_cannot_start_recovery**
   - Validates: Requirement 9.15
   - Tests: DRS StartRecovery operations fail with AccessDenied
   - Iterations: 100 with generated source server IDs

3. **test_property_query_handler_cannot_invoke_unauthorized_functions**
   - Validates: Requirement 9.14
   - Tests: Lambda InvokeFunction fails for unauthorized functions
   - Iterations: 100 with generated function names (excluding execution-handler)

#### Data Management Handler Restrictions (3 tests)
4. **test_property_data_management_cannot_start_recovery**
   - Validates: Requirement 9.16
   - Tests: DRS StartRecovery operations fail with AccessDenied
   - Iterations: 100 with generated source server IDs

5. **test_property_data_management_cannot_terminate_recovery_instances**
   - Validates: Requirement 9.16
   - Tests: DRS TerminateRecoveryInstances fails with AccessDenied
   - Iterations: 100 with generated recovery instance IDs

6. **test_property_data_management_cannot_start_step_functions**
   - Validates: Requirement 9.16
   - Tests: Step Functions StartExecution fails with AccessDenied
   - Iterations: 100 with generated state machine ARNs

#### Frontend Deployer Restrictions (3 tests)
7. **test_property_frontend_deployer_cannot_access_dynamodb**
   - Validates: Requirement 9.18
   - Tests: DynamoDB GetItem operations fail with AccessDenied
   - Iterations: 100 with generated table names

8. **test_property_frontend_deployer_cannot_access_drs**
   - Validates: Requirement 9.17
   - Tests: DRS DescribeSourceServers fails with AccessDenied
   - Iterations: 100 with generated max results parameters

9. **test_property_frontend_deployer_cannot_invoke_lambda**
   - Validates: Requirement 9.18
   - Tests: Lambda InvokeFunction fails with AccessDenied
   - Iterations: 100 with generated function names

#### Resource Pattern Restrictions (1 test)
10. **test_property_functions_cannot_access_non_project_resources**
    - Validates: Requirement 9.19
    - Tests: All functions cannot access resources outside {ProjectName}-* pattern
    - Iterations: 100 with generated non-project table names

### CloudWatch Monitoring Tests (2 tests)

11. **test_cloudwatch_alarms_configured_for_access_denied**
    - Validates: Requirements 10.1, 10.2, 10.3
    - Verifies: CloudWatch Alarm exists with correct configuration
    - Checks: Threshold=5, Period=300s, SNS actions configured

12. **test_cloudwatch_metric_filters_exist_for_access_denied**
    - Validates: Requirement 10.4
    - Verifies: Metric filters exist for all Lambda function log groups
    - Checks: Filter patterns include "AccessDenied" or "AccessDeniedException"

## Test Execution Requirements

### Prerequisites

1. **AWS Credentials**: Valid AWS credentials for account 438465159935
   ```bash
   aws sts get-caller-identity --region us-east-2
   ```

2. **IAM Permissions**: Ability to assume the following roles:
   - `aws-drs-orchestration-query-handler-role-qa`
   - `aws-drs-orchestration-data-management-role-qa`
   - `aws-drs-orchestration-frontend-deployer-role-qa`

3. **QA Stack Deployed**: Stack `aws-drs-orchestration-qa` with function-specific roles enabled
   ```bash
   aws cloudformation describe-stacks \
     --stack-name aws-drs-orchestration-qa \
     --region us-east-2 \
     --query 'Stacks[0].StackStatus'
   ```

### Execution Commands

#### Run All Negative Security Tests
```bash
# Activate virtual environment
source .venv/bin/activate

# Run all property-based tests (1000+ test cases)
.venv/bin/pytest tests/integration/test_negative_security_property.py -v --tb=short

# Run with Hypothesis statistics
.venv/bin/pytest tests/integration/test_negative_security_property.py -v --hypothesis-show-statistics
```

#### Run Specific Test Categories
```bash
# Query Handler tests only
.venv/bin/pytest tests/integration/test_negative_security_property.py::test_property_query_handler_cannot_write_dynamodb -v
.venv/bin/pytest tests/integration/test_negative_security_property.py::test_property_query_handler_cannot_start_recovery -v
.venv/bin/pytest tests/integration/test_negative_security_property.py::test_property_query_handler_cannot_invoke_unauthorized_functions -v

# Data Management Handler tests only
.venv/bin/pytest tests/integration/test_negative_security_property.py::test_property_data_management_cannot_start_recovery -v
.venv/bin/pytest tests/integration/test_negative_security_property.py::test_property_data_management_cannot_terminate_recovery_instances -v
.venv/bin/pytest tests/integration/test_negative_security_property.py::test_property_data_management_cannot_start_step_functions -v

# Frontend Deployer tests only
.venv/bin/pytest tests/integration/test_negative_security_property.py::test_property_frontend_deployer_cannot_access_dynamodb -v
.venv/bin/pytest tests/integration/test_negative_security_property.py::test_property_frontend_deployer_cannot_access_drs -v
.venv/bin/pytest tests/integration/test_negative_security_property.py::test_property_frontend_deployer_cannot_invoke_lambda -v

# CloudWatch monitoring tests only
.venv/bin/pytest tests/integration/test_negative_security_property.py::test_cloudwatch_alarms_configured_for_access_denied -v
.venv/bin/pytest tests/integration/test_negative_security_property.py::test_cloudwatch_metric_filters_exist_for_access_denied -v
```

## Expected Test Results

### Success Criteria

All 12 tests should **PASS** with the following outcomes:

1. **Property Tests (10 tests)**: Each test runs 100 iterations
   - All unauthorized operations return `AccessDeniedException` or `UnauthorizedOperation`
   - No operations succeed that should be denied
   - Hypothesis finds no counterexamples

2. **CloudWatch Alarm Test**: 
   - Alarm `aws-drs-orchestration-access-denied-qa` exists
   - Threshold: 5 errors
   - Period: 300 seconds (5 minutes)
   - SNS actions configured

3. **CloudWatch Metric Filter Tests**:
   - Metric filters exist for all 3 Lambda function log groups
   - Filter patterns include "AccessDenied" or "AccessDeniedException"

### Current Test Run Status

**Last Execution**: 2025-02-26 (local environment)

**Result**: Cannot execute - AWS credentials expired

**Output**:
```
9 skipped (Cannot assume IAM roles)
1 passed (test_property_functions_cannot_access_non_project_resources)
2 failed (CloudWatch tests - invalid credentials)
```

**Reason**: 
- Property tests require STS AssumeRole permission to get temporary credentials for each function's IAM role
- CloudWatch tests require valid AWS credentials to describe alarms and metric filters
- Local environment credentials expired

## Troubleshooting

### Issue: "Cannot assume role" errors

**Cause**: Current AWS credentials don't have `sts:AssumeRole` permission for the function-specific roles

**Solution**:
1. Ensure you're authenticated to account 438465159935
2. Verify your IAM user/role has permission to assume the test roles
3. Check trust policies on the function-specific roles allow your principal

### Issue: "InvalidClientTokenId" or "UnrecognizedClientException"

**Cause**: AWS credentials expired or invalid

**Solution**:
```bash
# Re-authenticate
aws login

# Verify credentials
aws sts get-caller-identity --region us-east-2
```

### Issue: Tests skip with "Cannot assume role"

**Cause**: IAM roles don't exist or trust policies don't allow assumption

**Solution**:
1. Verify QA stack is deployed with function-specific roles:
   ```bash
   aws cloudformation describe-stack-resources \
     --stack-name aws-drs-orchestration-qa \
     --region us-east-2 \
     --query 'StackResources[?ResourceType==`AWS::IAM::Role`].PhysicalResourceId'
   ```

2. Check role trust policies allow your principal:
   ```bash
   aws iam get-role \
     --role-name aws-drs-orchestration-query-handler-role-qa \
     --query 'Role.AssumeRolePolicyDocument'
   ```

## Test Implementation Details

### Hypothesis Strategies

The test suite uses custom Hypothesis strategies to generate realistic test data:

1. **dynamodb_table_names**: Generates project table names
   - Pattern: `{ProjectName}-{table-type}-{Environment}`
   - Types: protection-groups, recovery-plans, execution-history, target-accounts

2. **dynamodb_items**: Generates DynamoDB item structures
   - Keys: id (string), name (string)
   - Values: Alphanumeric characters

3. **drs_source_server_ids**: Generates DRS source server IDs
   - Pattern: `s-test-negative-{random}`

4. **lambda_function_names**: Generates Lambda function names
   - Pattern: `{ProjectName}-{function-type}-{Environment}`
   - Types: query-handler, data-management-handler, execution-handler, frontend-deployer

5. **step_function_arns**: Generates Step Functions ARNs
   - Pattern: `arn:aws:states:{Region}:{AccountId}:stateMachine:{ProjectName}-dr-orch-sf-{Environment}`

### Test Methodology

Each property test follows this pattern:

1. **Assume Role**: Get temporary credentials for the function's IAM role using STS AssumeRole
2. **Create Client**: Create boto3 client with the temporary credentials
3. **Attempt Operation**: Try to perform an unauthorized operation
4. **Verify Denial**: Assert that the operation fails with AccessDeniedException
5. **Repeat**: Hypothesis runs 100 iterations with different generated inputs

### Security Validation

The tests validate the following security properties:

- **Least Privilege**: Functions can only perform operations they need
- **Resource Restrictions**: Functions can only access project resources ({ProjectName}-*)
- **Service Boundaries**: Functions cannot access services they don't need
- **Write Protection**: Read-only functions cannot perform write operations
- **Recovery Protection**: Non-orchestration functions cannot trigger disaster recovery

## Next Steps

1. **Authenticate to AWS**: Run `aws login` to get valid credentials
2. **Verify QA Stack**: Ensure `aws-drs-orchestration-qa` is deployed with function-specific roles
3. **Run Tests**: Execute the test suite using the commands above
4. **Verify Results**: All 12 tests should pass
5. **Check CloudWatch**: Verify alarms trigger when AccessDenied errors occur
6. **Update Task Status**: Mark task 18.7 as complete when all tests pass

## Documentation References

- **Requirements**: `.kiro/specs/function-specific-iam-roles/requirements.md` (Requirements 9.14-9.19, 10.1-10.4)
- **Design**: `.kiro/specs/function-specific-iam-roles/design.md` (Property 16)
- **IAM Roles**: `cfn/iam/roles-stack.yaml`
- **Monitoring**: `cfn/monitoring/alarms-stack.yaml`

## Completion Criteria

Task 18.7 is complete when:

- ✅ Test implementation complete (test_negative_security_property.py exists)
- ⏳ All 12 tests pass with valid AWS credentials
- ⏳ CloudWatch alarms verified to trigger on AccessDenied errors
- ⏳ Property 16 validated across 1000+ test iterations
- ⏳ Task status updated to complete in tasks.md
