# Test Patterns and Mock Guidelines

## Purpose
This document describes the test patterns, mock strategies, and common fixes applied to the AWS DRS Orchestration test suite. It serves as a reference for maintaining and writing new tests.

## Table of Contents
1. [Mock Pattern Changes](#mock-pattern-changes)
2. [Common Syntax Fixes](#common-syntax-fixes)
3. [DynamoDB Table Mocking](#dynamodb-table-mocking)
4. [AWS Client Mocking](#aws-client-mocking)
5. [Property-Based Testing Patterns](#property-based-testing-patterns)
6. [Best Practices](#best-practices)

---

## Mock Pattern Changes

### Pattern 1: DynamoDB Table Access Functions

**Problem**: Lambda handlers use getter functions to access DynamoDB tables, not direct module attributes.

**Incorrect Pattern** (Old):
```python
# ❌ WRONG - Assumes table is a module attribute
with patch("index.target_accounts_table") as mock_table:
    pass
```

**Correct Pattern** (New):
```python
# ✅ CORRECT - Mock the getter function
with patch.object(index, "get_target_accounts_table", return_value=mock_table):
    pass
```

**Why This Changed**:
- Lambda handlers use `get_target_accounts_table()` function to lazily initialize tables
- This pattern allows better control over table lifecycle and testing
- Prevents accidental AWS API calls during test initialization

**Affected Functions**:
- `get_target_accounts_table()` - Target accounts DynamoDB table
- `get_protection_groups_table()` - Protection groups DynamoDB table
- `get_recovery_plans_table()` - Recovery plans DynamoDB table
- `get_executions_table()` - Executions DynamoDB table
- `get_tag_sync_config_table()` - Tag sync configuration table

**Example Fix**:
```python
# Before
@pytest.fixture
def mock_target_accounts_table():
    with patch("index.target_accounts_table") as mock_table:
        yield mock_table

# After
@pytest.fixture
def mock_target_accounts_table():
    with patch("index.get_target_accounts_table") as mock_func:
        mock_table = MagicMock()
        mock_func.return_value = mock_table
        yield mock_table
```

---

## Common Syntax Fixes

### Fix 1: patch.object() Keyword Argument

**Problem**: Missing `=` in `return_value` keyword argument causes NameError.

**Incorrect Syntax**:
```python
# ❌ WRONG - Missing = after return_value
with patch.object(index, "get_protection_groups_table", return_value, mock_table):
    pass
```

**Correct Syntax**:
```python
# ✅ CORRECT - Use return_value= keyword argument
with patch.object(index, "get_protection_groups_table", return_value=mock_table):
    pass
```

**Error Message**:
```
NameError: name 'return_value' is not defined
```

**How to Fix**:
1. Search for pattern: `return_value,`
2. Replace with: `return_value=`
3. Verify no other positional arguments follow

**Files Fixed** (30 tests):
- `test_query_handler_get_server_config_history.py` (11 tests)
- `test_query_handler_get_server_launch_config.py` (8 tests)
- `test_handle_get_combined_capacity.py` (5 tests)
- `test_empty_staging_accounts_default_property.py` (2 tests)
- `test_error_handling_data_management_handler.py` (4 tests)

---

## DynamoDB Table Mocking

### Complete DynamoDB Mock Pattern

**Problem**: Tests making actual AWS API calls instead of using mocks.

**Complete Mock Setup**:
```python
import pytest
from unittest.mock import MagicMock, patch
from moto import mock_aws

@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table with common operations"""
    mock_table = MagicMock()
    
    # Mock get_item
    mock_table.get_item.return_value = {
        "Item": {
            "accountId": "123456789012",
            "accountName": "test-account",
            "stagingAccounts": ["111111111111", "222222222222"]
        }
    }
    
    # Mock put_item
    mock_table.put_item.return_value = {}
    
    # Mock delete_item
    mock_table.delete_item.return_value = {}
    
    # Mock scan
    mock_table.scan.return_value = {
        "Items": [
            {"accountId": "123456789012", "accountName": "account-1"},
            {"accountId": "987654321098", "accountName": "account-2"}
        ]
    }
    
    # Mock query
    mock_table.query.return_value = {
        "Items": [{"accountId": "123456789012"}]
    }
    
    return mock_table

def test_with_dynamodb_mock(mock_dynamodb_table):
    """Example test using DynamoDB mock"""
    with patch.object(index, "get_target_accounts_table", return_value=mock_dynamodb_table):
        result = index.lambda_handler(event, context)
        assert result["statusCode"] == 200
```

### Mocking DynamoDB Exceptions

```python
from botocore.exceptions import ClientError

def test_dynamodb_error_handling(mock_dynamodb_table):
    """Test DynamoDB error handling"""
    # Mock ClientError
    mock_dynamodb_table.get_item.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}},
        "GetItem"
    )
    
    with patch.object(index, "get_target_accounts_table", return_value=mock_dynamodb_table):
        result = index.lambda_handler(event, context)
        assert result["statusCode"] == 404
```

---

## AWS Client Mocking

### Pattern 1: Mock AWS Credentials

**Problem**: Tests fail with "Invalid security token" errors.

**Solution**: Mock AWS credentials before any AWS client creation.

```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_aws_credentials():
    """Mock AWS credentials to prevent actual AWS API calls"""
    with patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'testing',
        'AWS_SECRET_ACCESS_KEY': 'testing',
        'AWS_SECURITY_TOKEN': 'testing',
        'AWS_SESSION_TOKEN': 'testing',
        'AWS_DEFAULT_REGION': 'us-east-1'
    }):
        yield

def test_with_mocked_credentials(mock_aws_credentials):
    """Test that uses mocked AWS credentials"""
    # Test code here - won't make actual AWS API calls
    pass
```

### Pattern 2: Mock DRS Client

```python
@pytest.fixture
def mock_drs_client():
    """Mock DRS client for testing"""
    mock_client = MagicMock()
    
    # Mock describe_source_servers
    mock_client.describe_source_servers.return_value = {
        "items": [
            {
                "sourceServerID": "s-1234567890abcdef0",
                "arn": "arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0",
                "tags": {"Name": "test-server"}
            }
        ]
    }
    
    # Mock start_recovery
    mock_client.start_recovery.return_value = {
        "job": {
            "jobID": "drsjob-1234567890abcdef0",
            "status": "PENDING"
        }
    }
    
    return mock_client

def test_drs_operations(mock_drs_client):
    """Test DRS operations with mocked client"""
    with patch.object(index, "create_drs_client", return_value=mock_drs_client):
        result = index.start_recovery_operation(event, context)
        assert result["statusCode"] == 200
```

### Pattern 3: Mock STS Client for Cross-Account Access

```python
@pytest.fixture
def mock_sts_client():
    """Mock STS client for cross-account role assumption"""
    mock_client = MagicMock()
    
    mock_client.assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "ASIA...",
            "SecretAccessKey": "secret...",
            "SessionToken": "token...",
            "Expiration": "2025-12-31T23:59:59Z"
        }
    }
    
    return mock_client

def test_cross_account_access(mock_sts_client):
    """Test cross-account access with mocked STS"""
    with patch("boto3.client") as mock_boto_client:
        mock_boto_client.return_value = mock_sts_client
        
        result = index.assume_role_and_query(event, context)
        assert result["statusCode"] == 200
```

---

## Property-Based Testing Patterns

### Pattern 1: Valid Input Generation

**Problem**: Property tests fail with invalid inputs that real code would never receive.

**Solution**: Use constrained strategies to generate valid inputs only.

```python
from hypothesis import given, strategies as st

# ✅ CORRECT - Constrained strategy for valid account IDs
@given(
    account_id=st.text(
        alphabet=st.characters(whitelist_categories=("Nd",)),  # Digits only
        min_size=12,
        max_size=12
    )
)
def test_property_valid_account_id(account_id):
    """Property test with valid account ID format"""
    result = validate_account_id(account_id)
    assert result is True

# ✅ CORRECT - Constrained strategy for operation names
@given(
    operation=st.sampled_from([
        "create_protection_group",
        "update_protection_group",
        "delete_protection_group",
        "get_protection_groups"
    ])
)
def test_property_valid_operations(operation):
    """Property test with valid operation names"""
    result = handle_operation(operation)
    assert "statusCode" in result
```

### Pattern 2: Mocking in Property Tests

```python
from hypothesis import given, strategies as st
from unittest.mock import patch, MagicMock

@given(
    account_id=st.text(alphabet=st.characters(whitelist_categories=("Nd",)), min_size=12, max_size=12),
    account_name=st.text(min_size=1, max_size=50)
)
def test_property_account_creation(account_id, account_name):
    """Property test for account creation with mocking"""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {}  # Account doesn't exist
    mock_table.put_item.return_value = {}
    
    with patch.object(index, "get_target_accounts_table", return_value=mock_table):
        result = index.create_target_account({
            "accountId": account_id,
            "accountName": account_name
        })
        
        assert result["statusCode"] == 200
        mock_table.put_item.assert_called_once()
```

### Pattern 3: Handling Falsifying Examples

**Problem**: Property test fails with specific input that reveals edge case.

**Example Failure**:
```
Falsifying example: test_audit_log_always_contains_required_fields(
    operation='___',  # Three underscores
)
```

**Solution**: Either fix the code to handle edge case or constrain the strategy.

```python
# Option 1: Fix the code to handle edge case
def audit_log(operation, user, result):
    # Filter out invalid operation names
    if not operation or operation.strip("_") == "":
        operation = "unknown_operation"
    
    logger.info(f"Audit: {operation} by {user} - {result}")

# Option 2: Constrain the strategy to exclude edge case
@given(
    operation=st.text(
        alphabet=st.characters(blacklist_characters="_"),  # Exclude underscores
        min_size=1,
        max_size=50
    ).filter(lambda x: x.strip())  # Exclude whitespace-only strings
)
def test_audit_log_property(operation):
    """Property test with constrained operation names"""
    audit_log(operation, "test-user", "success")
    # Assertions here
```

---

## Best Practices

### 1. Always Mock External Dependencies

**DO**:
```python
# ✅ Mock all AWS services
with patch.object(index, "get_target_accounts_table", return_value=mock_table):
    with patch("boto3.client") as mock_boto:
        mock_boto.return_value = mock_drs_client
        result = index.lambda_handler(event, context)
```

**DON'T**:
```python
# ❌ Don't make actual AWS API calls in tests
result = index.lambda_handler(event, context)  # Will fail without mocks
```

### 2. Use Fixtures for Common Mocks

**DO**:
```python
# ✅ Create reusable fixtures
@pytest.fixture
def mock_dynamodb_setup():
    """Complete DynamoDB mock setup"""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": {...}}
    
    with patch.object(index, "get_target_accounts_table", return_value=mock_table):
        yield mock_table

def test_with_fixture(mock_dynamodb_setup):
    result = index.lambda_handler(event, context)
    assert result["statusCode"] == 200
```

**DON'T**:
```python
# ❌ Don't repeat mock setup in every test
def test_without_fixture():
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": {...}}
    with patch.object(index, "get_target_accounts_table", return_value=mock_table):
        result = index.lambda_handler(event, context)
```

### 3. Test Error Paths

**DO**:
```python
# ✅ Test both success and error cases
def test_success_case(mock_table):
    mock_table.get_item.return_value = {"Item": {...}}
    result = index.lambda_handler(event, context)
    assert result["statusCode"] == 200

def test_not_found_case(mock_table):
    mock_table.get_item.return_value = {}  # No Item key
    result = index.lambda_handler(event, context)
    assert result["statusCode"] == 404

def test_exception_case(mock_table):
    mock_table.get_item.side_effect = ClientError(...)
    result = index.lambda_handler(event, context)
    assert result["statusCode"] == 500
```

### 4. Use Descriptive Test Names

**DO**:
```python
# ✅ Clear test names describe what is being tested
def test_get_staging_accounts_returns_list_when_account_exists():
    pass

def test_get_staging_accounts_returns_404_when_account_not_found():
    pass

def test_get_staging_accounts_returns_500_on_dynamodb_error():
    pass
```

**DON'T**:
```python
# ❌ Vague test names don't explain what is tested
def test_staging_accounts():
    pass

def test_error():
    pass
```

### 5. Keep Tests Focused

**DO**:
```python
# ✅ Test one thing per test
def test_create_protection_group_validates_required_fields():
    """Test that required fields are validated"""
    event = {"body": json.dumps({})}  # Missing required fields
    result = index.lambda_handler(event, context)
    assert result["statusCode"] == 400
    assert "required" in result["body"].lower()

def test_create_protection_group_checks_for_duplicates():
    """Test that duplicate names are rejected"""
    # Setup mock to return existing group
    result = index.lambda_handler(event, context)
    assert result["statusCode"] == 409
```

**DON'T**:
```python
# ❌ Don't test multiple things in one test
def test_create_protection_group():
    """Test everything about creating protection groups"""
    # Test validation
    # Test duplicates
    # Test success case
    # Test error handling
    # Too much in one test!
```

---

## Remaining Test Failures

As of the last test run, there are **15 remaining test failures** that require investigation:

### Category 1: DynamoDB ResourceNotFoundException (10 failures)
**File**: `test_data_management_new_operations.py`

**Issue**: Tests are not properly mocking DynamoDB tables, causing actual AWS API calls.

**Tests Affected**:
1. test_create_target_account_success
2. test_create_target_account_duplicate
3. test_update_target_account_success
4. test_delete_target_account_success
5. test_trigger_tag_sync_success
6. test_sync_extended_source_servers_success
7. test_direct_invocation_add_target_account
8. test_direct_invocation_trigger_tag_sync
9. test_create_target_account_missing_required_fields
10. test_delete_target_account_not_found

**Fix Required**: Add proper DynamoDB table mocking using the patterns described above.

### Category 2: UnrecognizedClientException (4 failures)
**Files**: 
- `test_data_management_response_format.py` (1 failure)
- `test_error_handling_query_handler.py` (3 failures)

**Issue**: Tests are not properly mocking AWS credentials/clients.

**Tests Affected**:
1. test_create_protection_group_direct_format
2. test_dynamodb_throttling_error
3. test_dynamodb_resource_not_found
4. test_retryable_errors_include_retry_guidance

**Fix Required**: Add AWS credential mocking using the patterns described above.

### Category 3: IAM Audit Logging Property Test (1 failure)
**File**: `test_iam_audit_logging_property.py`

**Issue**: Logger mock is not being called as expected for certain operation names.

**Test Affected**:
1. test_audit_log_always_contains_required_fields

**Falsifying Example**: `operation='___'` (three underscores)

**Fix Required**: Either fix the audit logging function to handle edge cases or constrain the property test strategy.

---

## Quick Reference

### Common Mock Patterns

| What to Mock | Pattern |
|--------------|---------|
| DynamoDB Table | `patch.object(index, "get_target_accounts_table", return_value=mock_table)` |
| DRS Client | `patch.object(index, "create_drs_client", return_value=mock_drs)` |
| STS Client | `patch("boto3.client", return_value=mock_sts)` |
| AWS Credentials | `patch.dict('os.environ', {'AWS_ACCESS_KEY_ID': 'testing', ...})` |
| IAM Validation | `patch("shared.iam_utils.validate_iam_authorization", return_value=True)` |

### Common Assertions

```python
# Status code
assert result["statusCode"] == 200

# Response body structure
body = json.loads(result["body"])
assert "data" in body
assert isinstance(body["data"], list)

# Error message
assert "error" in body
assert "not found" in body["error"].lower()

# Mock call verification
mock_table.get_item.assert_called_once()
mock_table.put_item.assert_called_with(Item={...})
```

---

## Related Documentation

- [Test Failure Analysis](../test_failure_analysis.md) - Detailed analysis of test failures
- [Python Coding Standards](../.kiro/steering/python-coding-standards.md) - Python style guide
- [Development Principles](../.kiro/steering/development-principles.md) - Core development philosophy

---

## Version History

- **v1.0** (2025-02-01): Initial documentation of test patterns and fixes
  - Documented mock pattern changes (target_accounts_table → get_target_accounts_table())
  - Documented syntax fixes (return_value, → return_value=)
  - Added DynamoDB and AWS client mocking patterns
  - Added property-based testing guidelines
  - Documented remaining test failures
