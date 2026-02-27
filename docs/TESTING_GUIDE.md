# Testing Guide

## Overview

This guide documents the comprehensive testing strategy for the DR Orchestration Platform, including unit tests, property-based tests, integration tests, and negative security tests. The platform uses a dual testing approach to ensure correctness and security.

## Testing Philosophy

### Dual Testing Approach

1. **Unit Tests**: Validate specific examples, edge cases, and error conditions
   - Test specific inputs and expected outputs
   - Test error handling and edge cases
   - Test CloudFormation template syntax and structure
   - Fast execution (seconds)

2. **Property-Based Tests**: Validate universal properties across all inputs
   - Test properties that should hold for ALL valid inputs
   - Use Hypothesis framework to generate random test cases
   - Minimum 100 iterations per property test
   - Discover edge cases automatically

### Testing Pyramid

```
        /\
       /  \
      / E2E \          End-to-End Tests (integration tests in QA)
     /______\
    /        \
   / Property \        Property-Based Tests (universal properties)
  /___________\
 /             \
/   Unit Tests  \     Unit Tests (specific examples and edge cases)
/_________________\
```

## Test Directory Structure

```
tests/
├── unit/                              # Unit tests
│   ├── test_account_utils_unit.py    # Account utilities unit tests
│   ├── test_account_utils_property.py # Account utilities property tests
│   └── ...
├── deployment/                        # Deployment architecture tests
│   ├── conftest.py                   # Shared fixtures
│   ├── test_iam_roles_stack.py       # IAM roles stack validation
│   ├── test_lambda_functions_stack.py # Lambda functions stack validation
│   ├── test_nested_stacks.py         # Nested stack orchestration
│   ├── test_conditional_logic.py     # UseFunctionSpecificRoles parameter
│   ├── test_backward_compatibility.py # Unified vs function-specific roles
│   └── test_deploy_main_stack.py     # deploy-main-stack.sh script
├── integration/                       # Integration tests (run in QA)
│   ├── test_functional_equivalence_function_specific.py
│   ├── test_negative_security_function_specific.py
│   ├── test_rollback_capability.py
│   └── test_alarm_trigger.py
└── conftest.py                        # Global fixtures
```

## Running Tests Locally

### Prerequisites

1. **Python Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```

2. **Required Tools**:
   - pytest (unit testing)
   - hypothesis (property-based testing)
   - cfn-lint (CloudFormation validation)
   - flake8 (Python linting)
   - black (Python formatting)
   - bandit (Python security)
   - detect-secrets (credential scanning)

### Running Unit Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_account_utils_unit.py -v

# Run with coverage
pytest --cov=lambda --cov-report=term tests/unit/

# Run with coverage report
pytest --cov=lambda --cov-report=html tests/unit/
open htmlcov/index.html
```

### Running Property-Based Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all property-based tests
pytest tests/unit/test_account_utils_property.py -v --hypothesis-show-statistics

# Run with increased iterations (default: 100)
pytest tests/unit/test_account_utils_property.py -v --hypothesis-show-statistics \
  --hypothesis-max-examples=1000

# Run with verbose output
pytest tests/unit/test_account_utils_property.py -v --hypothesis-verbosity=verbose
```

### Running Deployment Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all deployment tests
pytest tests/deployment/ -v

# Run specific deployment test
pytest tests/deployment/test_iam_roles_stack.py -v

# Run with CloudFormation validation
pytest tests/deployment/ -v --cfn-lint
```

### Running Integration Tests

**CRITICAL**: Integration tests run against live AWS resources in the QA environment.

```bash
# Activate virtual environment
source .venv/bin/activate

# Set AWS credentials for QA environment
export AWS_PROFILE=qa
export AWS_REGION=us-east-2

# Run all integration tests
pytest tests/integration/ -v

# Run specific integration test
pytest tests/integration/test_functional_equivalence_function_specific.py -v

# Run with detailed output
pytest tests/integration/ -v -s
```

## Running Tests in CI/CD Pipeline

The deployment script (`./scripts/deploy-main-stack.sh`) runs all tests automatically:

### Stage 1: Validation

```bash
# CloudFormation validation
cfn-lint cfn/**/*.yaml

# Python linting
flake8 lambda/ --max-line-length=120 --ignore=E203,W503,E501

# Python formatting
black --check lambda/

# TypeScript type checking
cd frontend && npm run type-check
```

### Stage 2: Security Scanning

```bash
# Python security
bandit -r lambda/ -ll

# Frontend vulnerabilities
cd frontend && npm audit --audit-level=high

# CloudFormation security
cfn_nag_scan --input-path cfn/

# Credential scanning
detect-secrets scan --baseline .secrets.baseline

# Shell script security
shellcheck scripts/*.sh

# Infrastructure security
checkov -d cfn/ --framework cloudformation
```

### Stage 3: Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Property-based tests
pytest tests/unit/ -v --hypothesis-show-statistics

# Deployment tests
pytest tests/deployment/ -v

# Frontend tests
cd frontend && npm test
```

### Stage 4: Git Push

```bash
# Push to remote
git push origin main
```

### Stage 5: Deploy

```bash
# Sync templates to S3
aws s3 sync cfn/ s3://aws-drs-orchestration-438465159935-qa/cfn/ --region us-east-2

# Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file cfn/main-stack.yaml \
  --stack-name aws-drs-orchestration-qa \
  --region us-east-2 \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=qa \
    DeploymentBucket=aws-drs-orchestration-438465159935-qa \
    AdminEmail=jocousen@amazon.com \
    UseFunctionSpecificRoles=true
```

## Test Environment Setup

### QA Environment

The QA environment is used for integration testing:

- **Stack Name**: `aws-drs-orchestration-qa`
- **Region**: `us-east-2`
- **Account ID**: `438465159935`
- **Deployment Bucket**: `aws-drs-orchestration-438465159935-qa`
- **API Endpoint**: `https://434getjyia.execute-api.us-east-2.amazonaws.com/qa`
- **CloudFront**: `https://d2hwh0tbw91md5.cloudfront.net`
- **UseFunctionSpecificRoles**: `true`
- **AdminEmail**: `jocousen@amazon.com`

### Test Data Setup

Integration tests require test data in DynamoDB:

```python
# tests/integration/conftest.py
import boto3
import pytest

@pytest.fixture(scope="session")
def dynamodb_client():
    return boto3.client("dynamodb", region_name="us-east-2")

@pytest.fixture(scope="session")
def setup_test_data(dynamodb_client):
    # Create test protection group
    dynamodb_client.put_item(
        TableName="aws-drs-orchestration-protection-groups-qa",
        Item={
            "groupId": {"S": "test-group-1"},
            "groupName": {"S": "Test Protection Group"},
            "description": {"S": "Test group for integration tests"},
            "serverIds": {"L": [{"S": "s-1234567890abcdef0"}]},
            "createdAt": {"S": "2025-01-01T00:00:00Z"},
            "updatedAt": {"S": "2025-01-01T00:00:00Z"}
        }
    )
    
    yield
    
    # Cleanup test data
    dynamodb_client.delete_item(
        TableName="aws-drs-orchestration-protection-groups-qa",
        Key={"groupId": {"S": "test-group-1"}}
    )
```

### AWS Credentials

Integration tests require AWS credentials with permissions to:

- Invoke Lambda functions
- Read/write DynamoDB tables
- Read CloudWatch Logs
- Describe CloudFormation stacks
- Describe IAM roles

```bash
# Set AWS credentials
export AWS_PROFILE=qa
export AWS_REGION=us-east-2

# Verify credentials
aws sts get-caller-identity
```

## Negative Testing Patterns

Negative tests verify that unauthorized operations fail with AccessDenied errors.

### Query Handler Negative Tests

```python
def test_query_handler_cannot_write_dynamodb():
    """Query Handler should NOT be able to write to DynamoDB."""
    lambda_client = boto3.client("lambda", region_name="us-east-2")
    
    # Attempt to write to DynamoDB (should fail)
    response = lambda_client.invoke(
        FunctionName="aws-drs-orchestration-query-handler-qa",
        InvocationType="RequestResponse",
        Payload=json.dumps({
            "operation": "create_protection_group",
            "groupName": "Unauthorized Group",
            "description": "This should fail"
        })
    )
    
    result = json.loads(response["Payload"].read())
    
    # Verify AccessDenied error
    assert response["StatusCode"] == 200
    assert "errorMessage" in result
    assert "AccessDenied" in result["errorMessage"]

def test_query_handler_cannot_start_recovery():
    """Query Handler should NOT be able to start DRS recovery."""
    lambda_client = boto3.client("lambda", region_name="us-east-2")
    
    # Attempt to start recovery (should fail)
    response = lambda_client.invoke(
        FunctionName="aws-drs-orchestration-query-handler-qa",
        InvocationType="RequestResponse",
        Payload=json.dumps({
            "operation": "start_recovery",
            "sourceServerIds": ["s-1234567890abcdef0"]
        })
    )
    
    result = json.loads(response["Payload"].read())
    
    # Verify AccessDenied error
    assert response["StatusCode"] == 200
    assert "errorMessage" in result
    assert "AccessDenied" in result["errorMessage"]
```

### Data Management Handler Negative Tests

```python
def test_data_management_cannot_start_recovery():
    """Data Management Handler should NOT be able to start DRS recovery."""
    lambda_client = boto3.client("lambda", region_name="us-east-2")
    
    # Attempt to start recovery (should fail)
    response = lambda_client.invoke(
        FunctionName="aws-drs-orchestration-data-management-handler-qa",
        InvocationType="RequestResponse",
        Payload=json.dumps({
            "operation": "start_recovery",
            "sourceServerIds": ["s-1234567890abcdef0"]
        })
    )
    
    result = json.loads(response["Payload"].read())
    
    # Verify AccessDenied error
    assert response["StatusCode"] == 200
    assert "errorMessage" in result
    assert "AccessDenied" in result["errorMessage"]
```

### Frontend Deployer Negative Tests

```python
def test_frontend_deployer_cannot_access_drs():
    """Frontend Deployer should NOT be able to access DRS."""
    lambda_client = boto3.client("lambda", region_name="us-east-2")
    
    # Attempt to describe source servers (should fail)
    response = lambda_client.invoke(
        FunctionName="aws-drs-orchestration-frontend-deployer-qa",
        InvocationType="RequestResponse",
        Payload=json.dumps({
            "operation": "describe_source_servers"
        })
    )
    
    result = json.loads(response["Payload"].read())
    
    # Verify AccessDenied error
    assert response["StatusCode"] == 200
    assert "errorMessage" in result
    assert "AccessDenied" in result["errorMessage"]

def test_frontend_deployer_cannot_access_dynamodb():
    """Frontend Deployer should NOT be able to access DynamoDB."""
    lambda_client = boto3.client("lambda", region_name="us-east-2")
    
    # Attempt to read from DynamoDB (should fail)
    response = lambda_client.invoke(
        FunctionName="aws-drs-orchestration-frontend-deployer-qa",
        InvocationType="RequestResponse",
        Payload=json.dumps({
            "operation": "list_protection_groups"
        })
    )
    
    result = json.loads(response["Payload"].read())
    
    # Verify AccessDenied error
    assert response["StatusCode"] == 200
    assert "errorMessage" in result
    assert "AccessDenied" in result["errorMessage"]
```

## Property-Based Testing with Hypothesis

### What is Property-Based Testing?

Property-based testing validates universal properties that should hold for ALL valid inputs, not just specific examples.

**Example**: Instead of testing `add(2, 3) == 5`, test the property `add(a, b) == add(b, a)` for all integers a and b.

### Writing Property Tests

```python
from hypothesis import given, strategies as st
import pytest

@given(
    project_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    environment=st.sampled_from(["dev", "test", "qa", "staging", "prod"])
)
def test_iam_role_naming_convention(project_name, environment):
    """IAM role names should follow the pattern {ProjectName}-{function}-role-{Environment}."""
    role_types = ["query-handler", "data-management", "execution-handler", "orchestration", "frontend-deployer"]
    
    for role_type in role_types:
        role_name = f"{project_name}-{role_type}-role-{environment}"
        
        # Verify naming convention
        assert role_name.startswith(project_name)
        assert role_name.endswith(environment)
        assert role_type in role_name
        assert role_name.count("-") >= 3  # At least 3 hyphens
```

### Hypothesis Strategies

Hypothesis provides strategies for generating test data:

```python
from hypothesis import strategies as st

# Text strategies
st.text()                              # Any text
st.text(min_size=1, max_size=100)     # Text with length constraints
st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll")))  # Letters only

# Numeric strategies
st.integers()                          # Any integer
st.integers(min_value=1, max_value=100)  # Integers in range
st.floats()                            # Any float

# Collection strategies
st.lists(st.integers())                # Lists of integers
st.lists(st.text(), min_size=1, max_size=10)  # Lists with size constraints
st.dictionaries(keys=st.text(), values=st.integers())  # Dictionaries

# Choice strategies
st.sampled_from(["dev", "test", "qa"])  # Choose from list
st.one_of(st.integers(), st.text())     # Choose from multiple strategies

# Composite strategies
st.tuples(st.text(), st.integers())     # Tuples of (text, integer)
```

### Property Test Examples

#### Property 1: Query Handler Read-Only Access

```python
from hypothesis import given, strategies as st
import pytest

@given(
    operation=st.sampled_from(["GetItem", "PutItem", "UpdateItem", "DeleteItem"]),
    table_name=st.text(min_size=1, max_size=100)
)
def test_query_handler_read_only_access(operation, table_name):
    """Query Handler should succeed on read operations and fail on write operations."""
    # Parse IAM policy from CloudFormation template
    policy = parse_iam_policy("cfn/iam/roles-stack.yaml", "QueryHandlerRole")
    
    # Check if operation is allowed
    is_allowed = check_iam_permission(policy, "dynamodb", operation, f"arn:aws:dynamodb:*:*:table/{table_name}")
    
    # Verify read operations are allowed, write operations are denied
    if operation == "GetItem":
        assert is_allowed, f"Query Handler should allow {operation}"
    else:
        assert not is_allowed, f"Query Handler should deny {operation}"
```

#### Property 2: Resource-Level Restrictions

```python
from hypothesis import given, strategies as st
import pytest

@given(
    project_name=st.text(min_size=1, max_size=50),
    table_name=st.text(min_size=1, max_size=100)
)
def test_query_handler_resource_restrictions(project_name, table_name):
    """Query Handler should only access tables matching {ProjectName}-* pattern."""
    # Parse IAM policy from CloudFormation template
    policy = parse_iam_policy("cfn/iam/roles-stack.yaml", "QueryHandlerRole")
    
    # Check if table access is allowed
    table_arn = f"arn:aws:dynamodb:us-east-2:123456789012:table/{table_name}"
    is_allowed = check_iam_permission(policy, "dynamodb", "GetItem", table_arn)
    
    # Verify only project tables are allowed
    if table_name.startswith(f"{project_name}-"):
        assert is_allowed, f"Query Handler should allow access to {table_name}"
    else:
        assert not is_allowed, f"Query Handler should deny access to {table_name}"
```

### Running Property Tests with Statistics

```bash
# Run with statistics
pytest tests/unit/test_account_utils_property.py -v --hypothesis-show-statistics

# Output:
# test_iam_role_naming_convention:
#   - 100 passing examples, 0 failing examples, 0 invalid examples
#   - Typical runtimes: 0-1ms, ~ 50% in data generation
#   - Stopped because settings.max_examples=100
```

## Test Coverage

### Measuring Coverage

```bash
# Run tests with coverage
pytest --cov=lambda --cov-report=term tests/unit/

# Generate HTML coverage report
pytest --cov=lambda --cov-report=html tests/unit/
open htmlcov/index.html
```

### Coverage Goals

- **Unit Tests**: 80% code coverage minimum
- **Property Tests**: 100% IAM policy coverage
- **Integration Tests**: 100% Lambda function coverage
- **Negative Tests**: 100% unauthorized operation coverage

### Coverage Report Example

```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
lambda/query-handler/index.py            150     15    90%
lambda/data-management-handler/index.py  200     20    90%
lambda/execution-handler/index.py        180     18    90%
lambda/orchestration/index.py            250     25    90%
lambda/frontend-deployer/index.py        100     10    90%
lambda/utils/account_utils.py             50      5    90%
-----------------------------------------------------------
TOTAL                                    930     93    90%
```

## Troubleshooting Tests

### Test Failures

**Symptom**: Test fails with unexpected error

**Diagnosis**:
```bash
# Run test with verbose output
pytest tests/unit/test_account_utils_unit.py::test_function_name -v -s

# Run test with pdb debugger
pytest tests/unit/test_account_utils_unit.py::test_function_name --pdb
```

### Property Test Failures

**Symptom**: Property test fails with counterexample

**Diagnosis**:
```bash
# Run property test with verbose output
pytest tests/unit/test_account_utils_property.py::test_property_name -v --hypothesis-verbosity=verbose

# Hypothesis will show the failing example:
# Falsifying example: test_property_name(
#     project_name='aws-drs',
#     environment='test'
# )
```

**Resolution**:
- Fix the code to handle the counterexample
- Or update the property test to exclude invalid inputs

### Integration Test Failures

**Symptom**: Integration test fails with AWS error

**Diagnosis**:
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check Lambda function logs
aws logs tail /aws/lambda/aws-drs-orchestration-query-handler-qa --since 5m

# Check CloudFormation stack status
aws cloudformation describe-stacks --stack-name aws-drs-orchestration-qa --region us-east-2
```

### Hypothesis Timeout

**Symptom**: Property test times out

**Diagnosis**:
```bash
# Reduce max examples
pytest tests/unit/test_account_utils_property.py -v --hypothesis-max-examples=10

# Increase timeout
pytest tests/unit/test_account_utils_property.py -v --hypothesis-deadline=None
```

## Best Practices

### 1. Write Tests First (TDD)

Write tests before implementing features:

```python
# 1. Write failing test
def test_new_feature():
    result = new_feature()
    assert result == expected_value

# 2. Implement feature
def new_feature():
    return expected_value

# 3. Run test (should pass)
pytest tests/unit/test_new_feature.py -v
```

### 2. Test One Thing Per Test

Each test should verify a single behavior:

```python
# ❌ BAD: Testing multiple things
def test_query_handler():
    assert query_handler_can_read_dynamodb()
    assert query_handler_cannot_write_dynamodb()
    assert query_handler_can_describe_drs()

# ✅ GOOD: One test per behavior
def test_query_handler_can_read_dynamodb():
    assert query_handler_can_read_dynamodb()

def test_query_handler_cannot_write_dynamodb():
    assert query_handler_cannot_write_dynamodb()

def test_query_handler_can_describe_drs():
    assert query_handler_can_describe_drs()
```

### 3. Use Descriptive Test Names

Test names should describe what is being tested:

```python
# ❌ BAD: Unclear test name
def test_1():
    ...

# ✅ GOOD: Descriptive test name
def test_query_handler_returns_protection_groups_when_valid_request():
    ...
```

### 4. Use Fixtures for Setup

Use pytest fixtures to avoid code duplication:

```python
@pytest.fixture
def lambda_client():
    return boto3.client("lambda", region_name="us-east-2")

@pytest.fixture
def test_protection_group():
    return {
        "groupId": "test-group-1",
        "groupName": "Test Group",
        "description": "Test group for integration tests"
    }

def test_create_protection_group(lambda_client, test_protection_group):
    response = lambda_client.invoke(
        FunctionName="aws-drs-orchestration-data-management-handler-qa",
        Payload=json.dumps({
            "operation": "create_protection_group",
            **test_protection_group
        })
    )
    assert response["StatusCode"] == 200
```

### 5. Clean Up Test Data

Always clean up test data after tests:

```python
@pytest.fixture
def test_protection_group(dynamodb_client):
    # Setup: Create test data
    group_id = "test-group-1"
    dynamodb_client.put_item(
        TableName="aws-drs-orchestration-protection-groups-qa",
        Item={"groupId": {"S": group_id}, ...}
    )
    
    yield group_id
    
    # Teardown: Clean up test data
    dynamodb_client.delete_item(
        TableName="aws-drs-orchestration-protection-groups-qa",
        Key={"groupId": {"S": group_id}}
    )
```

### 6. Mock External Dependencies

Mock external dependencies to isolate tests:

```python
from unittest.mock import patch, MagicMock

@patch("boto3.client")
def test_query_handler_with_mock(mock_boto3_client):
    # Setup mock
    mock_drs = MagicMock()
    mock_drs.describe_source_servers.return_value = {
        "items": [{"sourceServerID": "s-1234567890abcdef0"}]
    }
    mock_boto3_client.return_value = mock_drs
    
    # Test function
    result = query_handler({"operation": "list_servers"})
    
    # Verify mock was called
    mock_drs.describe_source_servers.assert_called_once()
    assert len(result["servers"]) == 1
```

### 7. Test Error Handling

Test error conditions and edge cases:

```python
def test_query_handler_handles_invalid_operation():
    lambda_client = boto3.client("lambda", region_name="us-east-2")
    
    response = lambda_client.invoke(
        FunctionName="aws-drs-orchestration-query-handler-qa",
        Payload=json.dumps({"operation": "invalid_operation"})
    )
    
    result = json.loads(response["Payload"].read())
    assert "errorMessage" in result
    assert "Invalid operation" in result["errorMessage"]
```

## Related Documentation

- [IAM Role Reference](IAM_ROLE_REFERENCE.md) - IAM role permissions
- [CloudFormation Template Organization](CFN_TEMPLATE_ORGANIZATION.md) - Template structure
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) - Common issues
- [QA Deployment Configuration](QA_DEPLOYMENT_CONFIGURATION.md) - QA environment setup
