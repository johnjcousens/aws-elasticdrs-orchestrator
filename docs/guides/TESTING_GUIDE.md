# Testing Guide: Function-Specific IAM Roles

## Overview

This guide documents the comprehensive testing approach for the function-specific IAM roles implementation. The testing strategy uses a dual approach combining traditional unit tests with property-based tests using the Hypothesis framework to ensure correctness, security, and functional equivalence across role configurations.

## Testing Philosophy

### Dual Testing Approach

The implementation uses two complementary testing methodologies:

1. **Unit Tests**: Verify specific examples and edge cases work correctly
   - Test known scenarios with concrete inputs
   - Validate expected behavior for specific use cases
   - Provide clear, readable test cases that document functionality

2. **Property-Based Tests**: Verify universal properties hold across all inputs
   - Generate hundreds of random test cases automatically
   - Discover edge cases that humans might miss
   - Validate invariants that should always be true
   - Use Hypothesis framework for intelligent test generation

**Why Both?**
- Unit tests provide clear documentation of expected behavior
- Property-based tests provide comprehensive coverage across input space
- Together they catch both known issues and unexpected edge cases

## Test Environment Setup

### Prerequisites

**Python Virtual Environment (.venv)**

All Python testing tools run inside a virtual environment to ensure consistent dependencies:

```bash
# Create virtual environment (first time only)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt
```

**Required Tools in .venv:**
- pytest (unit test framework)
- hypothesis (property-based testing)
- boto3 (AWS SDK)
- moto (AWS service mocking for unit tests)

**AWS Credentials**

Integration tests require valid AWS credentials for the QA environment:

```bash
# Configure AWS credentials
aws configure --profile qa

# Verify credentials
aws sts get-caller-identity --profile qa
```

**QA Environment Details:**
- Account: `438465159935`
- Region: `us-east-2`
- Stack: `aws-drs-orchestration-qa`
- Deployment Bucket: `aws-drs-orchestration-438465159935-qa`

### Directory Structure

```
tests/
├── unit/                           # Unit tests (fast, no AWS calls)
│   ├── test_account_utils_unit.py
│   ├── test_account_utils_property.py
│   └── ...
├── integration/                    # Integration tests (real AWS calls)
│   ├── conftest.py                # Shared fixtures
│   ├── test_query_handler_integration.py
│   ├── test_data_management_handler_integration.py
│   ├── test_execution_handler_integration.py
│   ├── test_functional_equivalence_unified.py
│   ├── test_functional_equivalence_function_specific.py
│   ├── test_negative_security_function_specific.py
│   ├── test_negative_security_property.py
│   ├── test_external_id_property.py
│   ├── test_property_17_rollback.py
│   └── test_monitoring_infrastructure.py
└── requirements-dev.txt           # Test dependencies
```

## Running Tests Locally

### Quick Reference

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run all unit tests (fast)
.venv/bin/pytest tests/unit/ -v

# Run specific test file
.venv/bin/pytest tests/unit/test_account_utils_unit.py -v

# Run property-based tests with statistics
.venv/bin/pytest tests/unit/test_account_utils_property.py -v --hypothesis-show-statistics

# Run integration tests (requires AWS credentials)
.venv/bin/pytest tests/integration/test_query_handler_integration.py -v

# Run with coverage
.venv/bin/pytest --cov=lambda --cov-report=term tests/unit/

# Run specific test by name
.venv/bin/pytest tests/unit/test_account_utils_unit.py::test_validate_account_id_valid -v
```

### Unit Tests

Unit tests run quickly without AWS API calls:

```bash
# Run all unit tests
.venv/bin/pytest tests/unit/ -v

# Run with coverage report
.venv/bin/pytest tests/unit/ --cov=lambda --cov-report=html

# Open coverage report
open htmlcov/index.html
```

**Unit Test Characteristics:**
- Fast execution (< 1 second per test)
- No AWS credentials required
- Use moto for AWS service mocking
- Test specific examples and edge cases

### Property-Based Tests

Property-based tests use Hypothesis to generate test cases:

```bash
# Run property tests with statistics
.venv/bin/pytest tests/unit/test_account_utils_property.py -v --hypothesis-show-statistics

# Run with more examples (default is 100)
.venv/bin/pytest tests/unit/ -v --hypothesis-profile=dev

# Run with fewer examples for quick feedback
.venv/bin/pytest tests/unit/ -v --hypothesis-profile=ci
```

**Hypothesis Configuration (pytest.ini):**

```ini
[pytest]
markers =
    property: Property-based tests using Hypothesis

[tool:pytest]
hypothesis_profile = default

[hypothesis]
default:
    max_examples = 100
    deadline = None

ci:
    max_examples = 50
    deadline = 5000

dev:
    max_examples = 200
    deadline = None
```

**Property Test Characteristics:**
- Generate 100+ random test cases automatically
- Discover edge cases through intelligent fuzzing
- Shrink failing examples to minimal reproducible cases
- Validate invariants across input space

### Integration Tests

Integration tests make real AWS API calls:

```bash
# Set AWS profile
export AWS_PROFILE=qa

# Run all integration tests
.venv/bin/pytest tests/integration/ -v

# Run specific integration test
.venv/bin/pytest tests/integration/test_query_handler_integration.py -v

# Run functional equivalence tests
.venv/bin/pytest tests/integration/test_functional_equivalence_unified.py -v
.venv/bin/pytest tests/integration/test_functional_equivalence_function_specific.py -v

# Run negative security tests
.venv/bin/pytest tests/integration/test_negative_security_function_specific.py -v
```

**Integration Test Characteristics:**
- Require valid AWS credentials
- Make real API calls to QA environment
- Test actual IAM permissions and resource access
- Slower execution (seconds to minutes per test)

## CI/CD Pipeline Integration

### Deploy Script Integration

The `./scripts/deploy.sh` script runs all tests as part of the deployment pipeline:

```bash
# Full deployment with all quality gates
./scripts/deploy.sh qa

# Stages executed:
# [1/5] Validation - cfn-lint, flake8, black, TypeScript checks
# [2/5] Security - bandit, npm audit, cfn_nag, detect-secrets
# [3/5] Tests - pytest unit tests, pytest property tests, vitest
# [4/5] Git Push - commit and push changes
# [5/5] Deploy - CloudFormation stack update
```

### Test Execution in CI/CD

**Stage 3: Tests**

The deploy script executes tests in this order:

1. **Python Unit Tests** (fast, no AWS calls)
   ```bash
   .venv/bin/pytest tests/unit/ -v --forked
   ```

2. **Python Property-Based Tests** (comprehensive)
   ```bash
   .venv/bin/pytest tests/unit/ -v --forked --hypothesis-show-statistics
   ```

3. **Frontend Unit Tests** (TypeScript)
   ```bash
   npm test
   ```

**Test Isolation:**

The `--forked` flag runs each test in a separate process to prevent state leakage:

```bash
# Install pytest-forked
pip install pytest-forked

# Run with process isolation
.venv/bin/pytest tests/unit/ --forked
```

### Validate-Only Mode

Run all quality gates without deploying:

```bash
# Run validation, security, and tests without deployment
./scripts/deploy.sh qa --validate-only

# Useful for:
# - Pre-commit validation
# - Pull request checks
# - Local development verification
```

## Test Categories

### 1. Functional Equivalence Tests

**Purpose**: Verify Lambda functions work identically with unified and function-specific roles.

**Test Files:**
- `tests/integration/test_functional_equivalence_unified.py`
- `tests/integration/test_functional_equivalence_function_specific.py`

**What They Test:**
- Query Handler returns identical results for read operations
- Data Management Handler performs identical DynamoDB operations
- Execution Handler orchestrates identical Step Functions workflows
- Response times are within 10% variance
- Cross-account operations work identically

**Example Test:**

```python
def test_query_handler_list_servers_equivalence():
    """Verify Query Handler returns identical server lists under both role configs."""
    # Deploy with unified role
    deploy_stack(use_function_specific_roles=False)
    unified_result = invoke_query_handler({"operation": "list_servers"})
    
    # Deploy with function-specific roles
    deploy_stack(use_function_specific_roles=True)
    function_specific_result = invoke_query_handler({"operation": "list_servers"})
    
    # Compare results
    assert unified_result["servers"] == function_specific_result["servers"]
    assert abs(unified_result["duration"] - function_specific_result["duration"]) < 0.1 * unified_result["duration"]
```

**Running Functional Equivalence Tests:**

```bash
# Test unified role configuration
.venv/bin/pytest tests/integration/test_functional_equivalence_unified.py -v

# Test function-specific role configuration
.venv/bin/pytest tests/integration/test_functional_equivalence_function_specific.py -v

# Compare results
diff tests/integration/functional_equivalence_unified_results.json \
     tests/integration/functional_equivalence_function_specific_results.json
```

### 2. Negative Security Tests

**Purpose**: Verify functions CANNOT perform operations they shouldn't have permission for.

**Test Files:**
- `tests/integration/test_negative_security_function_specific.py`
- `tests/integration/test_negative_security_property.py`

**What They Test:**
- Query Handler CANNOT execute write operations (DynamoDB PutItem → AccessDenied)
- Query Handler CANNOT execute DRS recovery (StartRecovery → AccessDenied)
- Data Management Handler CANNOT execute DRS recovery (StartRecovery → AccessDenied)
- Frontend Deployer CANNOT access DRS (DescribeSourceServers → AccessDenied)
- Frontend Deployer CANNOT access DynamoDB (GetItem → AccessDenied)
- All functions CANNOT access resources outside `{ProjectName}-*` pattern

**Example Test:**

```python
def test_query_handler_cannot_write_dynamodb():
    """Verify Query Handler cannot execute DynamoDB write operations."""
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    
    # Attempt DynamoDB PutItem operation
    response = lambda_client.invoke(
        FunctionName='aws-drs-orchestration-query-handler-qa',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            "operation": "put_item",
            "table": "aws-drs-orchestration-protection-groups-qa",
            "item": {"groupId": "test-group"}
        })
    )
    
    result = json.loads(response['Payload'].read())
    
    # Expect AccessDenied error
    assert result['statusCode'] == 403
    assert 'AccessDenied' in result['body'] or 'not authorized' in result['body']
```

**Property-Based Negative Test:**

```python
from hypothesis import given, strategies as st

@given(
    operation=st.sampled_from(['PutItem', 'UpdateItem', 'DeleteItem', 'BatchWriteItem']),
    table_name=st.text(min_size=1, max_size=50)
)
def test_query_handler_cannot_write_any_dynamodb_operation(operation, table_name):
    """Property: Query Handler cannot execute ANY DynamoDB write operation."""
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    
    response = lambda_client.invoke(
        FunctionName='aws-drs-orchestration-query-handler-qa',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            "operation": operation.lower(),
            "table": table_name
        })
    )
    
    result = json.loads(response['Payload'].read())
    
    # Property: ALL write operations should fail with AccessDenied
    assert result['statusCode'] == 403
```

**Running Negative Security Tests:**

```bash
# Run all negative security tests
.venv/bin/pytest tests/integration/test_negative_security_function_specific.py -v

# Run property-based negative tests
.venv/bin/pytest tests/integration/test_negative_security_property.py -v --hypothesis-show-statistics
```

### 3. External ID Validation Tests

**Purpose**: Verify cross-account role assumptions require correct ExternalId.

**Test Files:**
- `tests/integration/test_external_id_property.py`
- `tests/integration/test_external_id_validation.py`

**What They Test:**
- AssumeRole succeeds with correct ExternalId (`{ProjectName}-{Environment}`)
- AssumeRole fails with incorrect ExternalId (AccessDenied)
- AssumeRole fails with missing ExternalId (AccessDenied)
- All functions enforce ExternalId validation consistently

**Example Property Test:**

```python
from hypothesis import given, strategies as st

@given(
    external_id=st.text(min_size=1, max_size=100).filter(
        lambda x: x != "aws-drs-orchestration-qa"
    )
)
def test_assume_role_fails_with_incorrect_external_id(external_id):
    """Property: AssumeRole fails for ANY incorrect ExternalId."""
    sts_client = boto3.client('sts', region_name='us-east-2')
    
    with pytest.raises(ClientError) as exc_info:
        sts_client.assume_role(
            RoleArn='arn:aws:iam::123456789012:role/DRSOrchestrationRole',
            RoleSessionName='test-session',
            ExternalId=external_id
        )
    
    # Property: ALL incorrect ExternalIds should fail
    assert exc_info.value.response['Error']['Code'] == 'AccessDenied'
```

**Running External ID Tests:**

```bash
# Run external ID validation tests
.venv/bin/pytest tests/integration/test_external_id_validation.py -v

# Run property-based external ID tests
.venv/bin/pytest tests/integration/test_external_id_property.py -v --hypothesis-show-statistics
```

### 4. Rollback Capability Tests

**Purpose**: Verify switching from function-specific to unified roles works without data loss.

**Test Files:**
- `tests/integration/test_rollback_capability.py`
- `tests/integration/test_property_17_rollback.py`

**What They Test:**
- CloudFormation update completes within 5 minutes
- DynamoDB data remains unchanged after rollback
- Running Step Functions executions continue without interruption
- Lambda functions immediately use Unified Role after rollback
- Function-specific roles are deleted after rollback

**Example Test:**

```python
def test_rollback_preserves_dynamodb_data():
    """Verify rollback from function-specific to unified roles preserves DynamoDB data."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table('aws-drs-orchestration-protection-groups-qa')
    
    # Record data before rollback
    response_before = table.scan()
    items_before = response_before['Items']
    
    # Rollback to unified role
    deploy_stack(use_function_specific_roles=False)
    
    # Verify data after rollback
    response_after = table.scan()
    items_after = response_after['Items']
    
    # Data should be identical
    assert len(items_before) == len(items_after)
    assert items_before == items_after
```

**Running Rollback Tests:**

```bash
# Run rollback capability tests
.venv/bin/pytest tests/integration/test_rollback_capability.py -v

# Run property-based rollback tests
.venv/bin/pytest tests/integration/test_property_17_rollback.py -v
```

### 5. Monitoring Infrastructure Tests

**Purpose**: Verify CloudWatch alarms detect IAM permission issues.

**Test Files:**
- `tests/integration/test_monitoring_infrastructure.py`
- `tests/integration/test_alarm_trigger.py`

**What They Test:**
- CloudWatch alarm exists for access denied errors
- Alarm transitions to ALARM state when errors occur
- SNS notifications are sent when alarm triggers
- CloudWatch Insights queries identify AccessDenied errors by function

**Example Test:**

```python
def test_access_denied_alarm_triggers():
    """Verify CloudWatch alarm triggers when Lambda generates AccessDenied errors."""
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-2')
    
    # Trigger AccessDenied errors (5+ within 5 minutes)
    for _ in range(6):
        invoke_lambda_with_insufficient_permissions()
    
    # Wait for alarm evaluation
    time.sleep(60)
    
    # Check alarm state
    response = cloudwatch.describe_alarms(
        AlarmNames=['aws-drs-orchestration-access-denied-qa']
    )
    
    alarm = response['MetricAlarms'][0]
    assert alarm['StateValue'] == 'ALARM'
```

**Running Monitoring Tests:**

```bash
# Run monitoring infrastructure tests
.venv/bin/pytest tests/integration/test_monitoring_infrastructure.py -v

# Run alarm trigger tests
.venv/bin/pytest tests/integration/test_alarm_trigger.py -v
```

## Negative Testing Patterns

### What is Negative Testing?

Negative testing verifies that operations that SHOULD fail actually DO fail with the correct error. This is critical for security validation.

### Negative Testing Strategy

**For Each Function:**

1. **Identify Prohibited Operations**
   - List operations the function should NOT have permission for
   - Example: Query Handler should NOT have DynamoDB write permissions

2. **Attempt Prohibited Operations**
   - Invoke Lambda with operation that should fail
   - Example: Invoke Query Handler with PutItem operation

3. **Verify AccessDenied Error**
   - Check response status code is 403
   - Check error message contains "AccessDenied" or "not authorized"
   - Example: `assert result['statusCode'] == 403`

4. **Use Property-Based Testing**
   - Generate many variations of prohibited operations
   - Example: Test ALL DynamoDB write operations (PutItem, UpdateItem, DeleteItem, BatchWriteItem)

### Negative Test Examples

**Query Handler Negative Tests:**

```python
# Unit test: Specific example
def test_query_handler_cannot_start_recovery():
    """Verify Query Handler cannot execute DRS StartRecovery."""
    response = invoke_query_handler({
        "operation": "start_recovery",
        "sourceServerIds": ["s-1234567890abcdef0"]
    })
    
    assert response['statusCode'] == 403
    assert 'AccessDenied' in response['body']

# Property test: All DRS write operations
@given(
    operation=st.sampled_from([
        'StartRecovery',
        'TerminateRecoveryInstances',
        'CreateRecoveryInstanceForDrs',
        'DisconnectRecoveryInstance'
    ])
)
def test_query_handler_cannot_execute_any_drs_write_operation(operation):
    """Property: Query Handler cannot execute ANY DRS write operation."""
    response = invoke_query_handler({"operation": operation.lower()})
    
    # Property: ALL DRS write operations should fail
    assert response['statusCode'] == 403
```

**Data Management Handler Negative Tests:**

```python
# Unit test: Specific example
def test_data_management_cannot_start_recovery():
    """Verify Data Management Handler cannot execute DRS StartRecovery."""
    response = invoke_data_management_handler({
        "operation": "start_recovery",
        "sourceServerIds": ["s-1234567890abcdef0"]
    })
    
    assert response['statusCode'] == 403
    assert 'AccessDenied' in response['body']

# Property test: All DRS recovery operations
@given(
    operation=st.sampled_from([
        'StartRecovery',
        'TerminateRecoveryInstances',
        'CreateRecoveryInstanceForDrs'
    ])
)
def test_data_management_cannot_execute_any_drs_recovery_operation(operation):
    """Property: Data Management Handler cannot execute ANY DRS recovery operation."""
    response = invoke_data_management_handler({"operation": operation.lower()})
    
    # Property: ALL DRS recovery operations should fail
    assert response['statusCode'] == 403
```

**Frontend Deployer Negative Tests:**

```python
# Unit test: Specific example
def test_frontend_deployer_cannot_access_drs():
    """Verify Frontend Deployer cannot access DRS."""
    response = invoke_frontend_deployer({
        "operation": "describe_source_servers"
    })
    
    assert response['statusCode'] == 403
    assert 'AccessDenied' in response['body']

# Property test: All DRS operations
@given(
    operation=st.sampled_from([
        'DescribeSourceServers',
        'DescribeJobs',
        'StartRecovery',
        'TerminateRecoveryInstances'
    ])
)
def test_frontend_deployer_cannot_execute_any_drs_operation(operation):
    """Property: Frontend Deployer cannot execute ANY DRS operation."""
    response = invoke_frontend_deployer({"operation": operation.lower()})
    
    # Property: ALL DRS operations should fail
    assert response['statusCode'] == 403
```

### Resource Pattern Negative Tests

Verify functions cannot access resources outside `{ProjectName}-*` pattern:

```python
@given(
    table_name=st.text(min_size=1, max_size=50).filter(
        lambda x: not x.startswith('aws-drs-orchestration-')
    )
)
def test_query_handler_cannot_access_non_project_tables(table_name):
    """Property: Query Handler cannot access tables outside project pattern."""
    response = invoke_query_handler({
        "operation": "get_item",
        "table": table_name,
        "key": {"id": "test"}
    })
    
    # Property: ALL non-project tables should be denied
    assert response['statusCode'] == 403
```

## Test Execution Best Practices

### 1. Always Use Virtual Environment

```bash
# ❌ WRONG - May use wrong Python version or missing dependencies
pytest tests/unit/

# ✅ CORRECT - Always use .venv
source .venv/bin/activate
.venv/bin/pytest tests/unit/
```

### 2. Run Tests Before Committing

```bash
# Pre-commit checklist
source .venv/bin/activate
.venv/bin/pytest tests/unit/ -v
.venv/bin/pytest tests/unit/ -v --hypothesis-show-statistics
```

### 3. Use Validate-Only Mode

```bash
# Run all quality gates without deploying
./scripts/deploy.sh qa --validate-only
```

### 4. Monitor Test Execution Time

```bash
# Show test durations
.venv/bin/pytest tests/unit/ -v --durations=10

# Identify slow tests
.venv/bin/pytest tests/unit/ -v --durations=0
```

### 5. Use Markers for Test Selection

```bash
# Run only property-based tests
.venv/bin/pytest tests/unit/ -v -m property

# Run only integration tests
.venv/bin/pytest tests/integration/ -v -m integration

# Skip slow tests
.venv/bin/pytest tests/unit/ -v -m "not slow"
```

## Troubleshooting

### Common Issues

**Issue: pytest not found**

```bash
# Solution: Activate virtual environment
source .venv/bin/activate
```

**Issue: AWS credentials not configured**

```bash
# Solution: Configure AWS profile
aws configure --profile qa

# Verify credentials
aws sts get-caller-identity --profile qa
```

**Issue: Hypothesis generates too many examples**

```bash
# Solution: Use CI profile for faster execution
.venv/bin/pytest tests/unit/ -v --hypothesis-profile=ci
```

**Issue: Integration tests fail with AccessDenied**

```bash
# Solution: Verify you're using QA environment
export AWS_PROFILE=qa
aws sts get-caller-identity

# Verify stack is deployed with function-specific roles
aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-qa \
  --query 'Stacks[0].Parameters[?ParameterKey==`UseFunctionSpecificRoles`].ParameterValue' \
  --output text
```

**Issue: Property tests fail with shrinking errors**

```bash
# Solution: Run with verbose shrinking output
.venv/bin/pytest tests/unit/ -v --hypothesis-verbosity=verbose
```

## Test Coverage

### Measuring Coverage

```bash
# Run tests with coverage
.venv/bin/pytest tests/unit/ --cov=lambda --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Coverage Goals

- **Unit Tests**: Minimum 80% code coverage on new Python code
- **Integration Tests**: Cover all critical paths and error scenarios
- **Property Tests**: Cover all invariants and security properties

### Coverage Reports

Coverage reports show:
- Lines executed vs. total lines
- Branches taken vs. total branches
- Functions called vs. total functions
- Missing coverage highlighted in red

## Continuous Integration

### GitHub Actions Integration

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Create virtual environment
        run: python -m venv .venv
      
      - name: Install dependencies
        run: |
          source .venv/bin/activate
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: |
          source .venv/bin/activate
          .venv/bin/pytest tests/unit/ -v --forked
      
      - name: Run property tests
        run: |
          source .venv/bin/activate
          .venv/bin/pytest tests/unit/ -v --forked --hypothesis-show-statistics
      
      - name: Generate coverage report
        run: |
          source .venv/bin/activate
          .venv/bin/pytest tests/unit/ --cov=lambda --cov-report=xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v2
```

## Summary

This testing guide provides comprehensive documentation for:

1. **Dual Testing Approach**: Unit tests + property-based tests with Hypothesis
2. **Local Execution**: How to run tests locally with virtual environment
3. **CI/CD Integration**: How tests run in deploy.sh pipeline
4. **Test Environment Setup**: QA environment configuration and AWS credentials
5. **Negative Testing Patterns**: Verifying unauthorized operations fail correctly

**Key Takeaways:**

- Always activate `.venv` before running tests
- Use property-based tests to discover edge cases
- Run negative security tests to verify access controls
- Use `--validate-only` mode for pre-commit checks
- Monitor test coverage to ensure comprehensive validation

**Next Steps:**

1. Set up virtual environment: `python3 -m venv .venv`
2. Install dependencies: `pip install -r requirements-dev.txt`
3. Run unit tests: `.venv/bin/pytest tests/unit/ -v`
4. Run property tests: `.venv/bin/pytest tests/unit/ -v --hypothesis-show-statistics`
5. Run integration tests: `.venv/bin/pytest tests/integration/ -v`
