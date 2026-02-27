# Task 18.7 Status Report: Negative Security Tests

**Date**: 2025-02-26  
**Task**: 18.7 Execute negative security tests  
**Status**: BLOCKED - Requires IAM trust policy updates  
**Test File**: `tests/integration/test_negative_security_property.py`

## Executive Summary

The negative security test implementation is **complete and ready**, but execution is **blocked** because the IAM roles' trust policies only allow `lambda.amazonaws.com` to assume them, not test users/roles. The tests require the ability to assume each function's IAM role to verify that unauthorized operations are properly denied.

## Test Results Summary

**Total Tests**: 12  
**Passed**: 1 (8%)  
**Skipped**: 9 (75%) - Cannot assume IAM roles  
**Failed**: 2 (17%) - Credential issues  

### Detailed Results

#### ✅ Passed (1 test)
- `test_property_functions_cannot_access_non_project_resources` - Tests resource pattern restrictions without requiring role assumption

#### ⏸️ Skipped (9 tests) - Cannot Assume IAM Roles
All property-based tests that require assuming function-specific roles:

**Query Handler Tests (3 skipped)**:
1. `test_property_query_handler_cannot_write_dynamodb` - Validates Requirement 9.14
2. `test_property_query_handler_cannot_start_recovery` - Validates Requirement 9.15
3. `test_property_query_handler_cannot_invoke_unauthorized_functions` - Validates Requirement 9.14

**Data Management Handler Tests (3 skipped)**:
4. `test_property_data_management_cannot_start_recovery` - Validates Requirement 9.16
5. `test_property_data_management_cannot_terminate_recovery_instances` - Validates Requirement 9.16
6. `test_property_data_management_cannot_start_step_functions` - Validates Requirement 9.16

**Frontend Deployer Tests (3 skipped)**:
7. `test_property_frontend_deployer_cannot_access_dynamodb` - Validates Requirement 9.18
8. `test_property_frontend_deployer_cannot_access_drs` - Validates Requirement 9.17
9. `test_property_frontend_deployer_cannot_invoke_lambda` - Validates Requirement 9.18

#### ❌ Failed (2 tests) - Credential Issues
10. `test_cloudwatch_alarms_configured_for_access_denied` - InvalidClientTokenId error
11. `test_cloudwatch_metric_filters_exist_for_access_denied` - UnrecognizedClientException error

## Root Cause Analysis

### Issue 1: IAM Role Trust Policies (9 skipped tests)

**Current Trust Policy** (all function-specific roles):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

**Problem**: The trust policy only allows Lambda service to assume the role, not test users/roles.

**Impact**: Tests cannot use `sts:AssumeRole` to get temporary credentials for each function's IAM role, which is required to verify that unauthorized operations are properly denied.

**Affected Roles**:
- `aws-drs-orchestration-query-handler-role-qa`
- `aws-drs-orchestration-data-management-role-qa`
- `aws-drs-orchestration-frontend-deployer-role-qa`

### Issue 2: Boto3 Credential Caching (2 failed tests)

**Error Messages**:
- `InvalidClientTokenId: The security token included in the request is invalid`
- `UnrecognizedClientException: The security token included in the request is invalid`

**Problem**: Boto3 clients may be caching expired credentials even though AWS CLI shows valid credentials.

**Impact**: CloudWatch alarm and metric filter verification tests fail despite valid AWS credentials being available.

## Solutions

### Solution 1: Update IAM Trust Policies (Recommended for Testing)

Add the current user/role to the trust policy **temporarily** for testing:

```bash
# Get current user ARN
CURRENT_ARN=$(aws sts get-caller-identity --query 'Arn' --output text --region us-east-2)

# Update trust policy for each role
for ROLE in query-handler data-management frontend-deployer; do
    ROLE_NAME="aws-drs-orchestration-${ROLE}-role-qa"
    
    # Create updated trust policy
    cat > /tmp/trust-policy-${ROLE}.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        },
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "${CURRENT_ARN}"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "sts:ExternalId": "test-negative-security-pbt"
                }
            }
        }
    ]
}
EOF
    
    # Update role trust policy
    aws iam update-assume-role-policy \
        --role-name ${ROLE_NAME} \
        --policy-document file:///tmp/trust-policy-${ROLE}.json \
        --region us-east-2
done
```

**Important**: This is a **temporary** change for testing only. After tests complete, revert the trust policies to production configuration (Lambda service only).

### Solution 2: Alternative Testing Approach (Production-Safe)

Instead of assuming roles directly, invoke the Lambda functions with test payloads that attempt unauthorized operations:

```python
def test_query_handler_cannot_write_via_lambda_invocation():
    """Test by invoking Lambda function directly."""
    lambda_client = boto3.client("lambda", region_name="us-east-2")
    
    # Invoke Query Handler with payload that attempts DynamoDB write
    response = lambda_client.invoke(
        FunctionName="aws-drs-orchestration-query-handler-qa",
        InvocationType="RequestResponse",
        Payload=json.dumps({
            "operation": "test_unauthorized_write",
            "table_name": "aws-drs-orchestration-protection-groups-qa",
            "item": {"id": "test"}
        })
    )
    
    # Verify AccessDenied error in response
    result = json.loads(response["Payload"].read())
    assert "AccessDeniedException" in str(result)
```

**Pros**: No trust policy changes required, tests production configuration  
**Cons**: Requires Lambda function code changes to support test operations

### Solution 3: Fix Boto3 Credential Caching

The CloudWatch tests can be fixed by ensuring boto3 uses fresh credentials:

```python
import boto3
from botocore.session import Session

def get_cloudwatch_client():
    """Get CloudWatch client with fresh credentials."""
    session = Session()
    session.get_credentials()  # Force credential refresh
    return boto3.client("cloudwatch", region_name="us-east-2")
```

## Recommendations

### Immediate Actions

1. **For Development/QA Testing**: Use Solution 1 (update trust policies temporarily)
   - Allows comprehensive property-based testing with 100 iterations per test
   - Validates IAM permissions directly without Lambda function modifications
   - Can be reverted after testing completes

2. **Fix CloudWatch Tests**: Implement Solution 3 (force credential refresh)
   - Simple code change to ensure fresh credentials
   - No infrastructure changes required

### Long-Term Strategy

1. **Production Deployment**: Use Solution 2 (Lambda invocation testing)
   - No trust policy changes required
   - Tests actual production configuration
   - Requires Lambda function code to support test operations

2. **CI/CD Integration**: Create dedicated test IAM role
   - Trust policy allows CI/CD service principal
   - Used only in automated test environments
   - Never deployed to production

## Next Steps

### Option A: Proceed with Trust Policy Updates (Fastest)

1. Run the trust policy update commands above
2. Re-run tests: `.venv/bin/pytest tests/integration/test_negative_security_property.py -v`
3. Verify all 12 tests pass
4. Revert trust policies to production configuration
5. Mark task 18.7 as complete

**Estimated Time**: 15 minutes

### Option B: Implement Lambda Invocation Testing (Production-Safe)

1. Add test operation handlers to Lambda functions
2. Rewrite tests to use Lambda invocation instead of role assumption
3. Deploy updated Lambda functions to QA
4. Run tests
5. Mark task 18.7 as complete

**Estimated Time**: 2-3 hours

### Option C: User Decision Required

Ask the user which approach they prefer:
- **Fast but requires temporary trust policy changes** (Option A)
- **Slower but production-safe** (Option B)
- **Alternative approach** (user suggests)

## Test Execution Commands

Once trust policies are updated:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all negative security tests
.venv/bin/pytest tests/integration/test_negative_security_property.py -v --tb=short

# Run with Hypothesis statistics
.venv/bin/pytest tests/integration/test_negative_security_property.py -v --hypothesis-show-statistics

# Run specific test categories
.venv/bin/pytest tests/integration/test_negative_security_property.py::test_property_query_handler_cannot_write_dynamodb -v
```

## Success Criteria

Task 18.7 is complete when:
- ✅ Test implementation complete (DONE)
- ⏳ All 12 tests pass (BLOCKED - awaiting trust policy updates or alternative approach)
- ⏳ CloudWatch alarms verified (BLOCKED - credential issues)
- ⏳ Property 16 validated across 1000+ test iterations (BLOCKED)
- ⏳ Task status updated to complete (BLOCKED)

## Files Modified

- `tests/integration/test_negative_security_property.py` - Fixed boto3 client creation to use lazy initialization
- `tests/integration/TASK_18_7_STATUS_REPORT.md` - This status report

## References

- **Requirements**: `.kiro/specs/function-specific-iam-roles/requirements.md` (Requirements 9.14-9.19, 10.1-10.4)
- **Design**: `.kiro/specs/function-specific-iam-roles/design.md` (Property 16)
- **Execution Guide**: `tests/integration/TASK_18_7_EXECUTION_GUIDE.md`
- **IAM Roles**: `cfn/iam/roles-stack.yaml`
- **Monitoring**: `cfn/monitoring/alarms-stack.yaml`
