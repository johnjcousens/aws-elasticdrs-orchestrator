# Test Patterns and Mock Guidelines

## Purpose
This document describes the test patterns, mock strategies, and common fixes applied to the AWS DRS Orchestration test suite. It serves as a reference for maintaining and writing new tests.

## Table of Contents
1. [Mock Pattern Changes](#mock-pattern-changes)
2. [Common Syntax Fixes](#common-syntax-fixes)
3. [DynamoDB Table Mocking](#dynamodb-table-mocking)
4. [AWS Client Mocking](#aws-client-mocking)
5. [Property-Based Testing Patterns](#property-based-testing-patterns)
6. [Test Isolation Fixtures](#test-isolation-fixtures)
7. [Cross-File Test Isolation](#cross-file-test-isolation)
8. [Best Practices](#best-practices)

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

## Test Isolation Fixtures

### Overview

All tests automatically use isolation fixtures from `tests/unit/conftest.py` to prevent global state leakage between tests. These fixtures ensure each test runs in a clean, isolated environment.

The test suite uses a comprehensive set of cleanup fixtures that work together at different scopes (session, module, function) to prevent state pollution between tests. This multi-layered approach ensures complete test isolation.

### Overview

All tests automatically use isolation fixtures from `tests/unit/conftest.py` to prevent global state leakage between tests. These fixtures ensure each test runs in a clean, isolated environment.

The test suite uses a comprehensive set of cleanup fixtures that work together at different scopes (session, module, function) to prevent state pollution between tests. This multi-layered approach ensures complete test isolation.

### Fixture Hierarchy and Execution Order

The cleanup fixtures are organized in a three-tier hierarchy based on pytest scopes:

```
Session Scope (once per test run)
├── capture_original_state - Captures baseline state at session start
└── reset_all_module_state_session - Initial cleanup before any tests

Module Scope (once per test file)
├── cleanup_sys_modules_per_file - Removes modules added by test file
├── cleanup_mocks_per_file - Stops all active mock patches
├── reset_environment_per_file - Restores environment variables
├── reset_sys_path_per_file - Restores Python import paths
└── reset_all_module_state_per_file - Resets module-level variables

Function Scope (before each test)
├── reset_environment_variables - Resets env vars per test
├── reset_launch_config_globals - Resets launch config state
├── set_launch_config_env_vars - Sets required env vars
├── reset_logger_state - Resets logging configuration
├── reset_data_management_handler_state - Resets handler tables
├── reset_orchestration_handler_state - Resets handler tables
├── reset_execution_handler_state - Resets handler tables
├── reset_query_handler_state - Resets handler tables
├── reset_mock_state - Cleans up mock history
└── isolate_test_execution - Ensures AWS isolation
```

### Session-Scoped Fixtures (Once Per Test Run)

#### capture_original_state

**Purpose**: Captures the baseline state at the start of the test session for later restoration.

**What it captures**:
- `sys.path` - Python import paths (list of directory paths)
- `os.environ` - Environment variables (dictionary)
- `sys.modules` - Loaded Python modules (set of module names)

**Why it's needed**: Other fixtures need to know the original state to restore it between test files. This provides a clean baseline that represents the system state before any tests run.

**Scope**: `session` (runs once at test session start)

**Autouse**: `True` (runs automatically)

**Example captured state**:
```python
original_state = {
    "sys_path": ['/project', '/usr/lib/python3.12', '/usr/lib/python3.12/lib-dynload'],
    "environ": {'HOME': '/home/user', 'PATH': '/usr/bin:/bin', 'AWS_REGION': 'us-east-1'},
    "sys_modules": {'sys', 'os', 'pytest', 'boto3', 'moto', ...}
}
```

**Debug output**:
```
[SESSION] Capturing original state
  Captured sys.path with 15 entries
  Captured 42 environment variables
  Captured 127 loaded modules
```

#### reset_all_module_state_session

**Purpose**: Performs initial cleanup before any tests run to ensure a clean slate.

**What it resets**:
- All Lambda handler module-level table variables (6 handlers × 3-6 tables each)
- All shared module DynamoDB resources (6 shared modules)
- Uses `MODULE_STATE_REGISTRY` to systematically reset all known state

**Why it's needed**: Ensures the test session starts with completely clean state, preventing any residual state from previous test runs or development work.

**Scope**: `session` (runs once before any tests)

**Autouse**: `True` (runs automatically)

**Example**:
```python
# Before session starts:
shared.launch_config_service._dynamodb = None
shared.launch_config_service._protection_groups_table = None
lambda.data_management_handler.index._protection_groups_table = None
# ... (all 30+ module-level variables reset to None)
```

### Module-Scoped Fixtures (Once Per Test File)

#### cleanup_sys_modules_per_file

**Purpose**: Removes modules that were added during test file execution.

**What it cleans up**:
- Modules imported during test execution
- Modules deleted by tests (e.g., `del sys.modules["index"]` to force reimport)
- Modules added to `sys.modules` that weren't present at session start

**Why it's needed**: Some tests delete modules from `sys.modules` to force reimport with different mocks. Without cleanup, these deletions affect subsequent test files, causing import errors or stale module references.

**Scope**: `module` (runs after each test file completes)

**Autouse**: `True` (runs automatically)

**Example**:
```python
# Test file adds these modules:
sys.modules["lambda.data_management_handler.index"] = <module>
sys.modules["shared.launch_config_service"] = <module>

# Test file deletes this module to force reimport:
del sys.modules["index"]

# After test file completes, fixture:
# 1. Removes added modules not in original_modules
# 2. Ensures sys.modules consistency for next test file
```

#### cleanup_mocks_per_file

**Purpose**: Stops all active mock patches after each test file completes.

**What it cleans up**:
- Active `@patch` decorators that weren't properly stopped
- `unittest.mock.patch` context managers that leaked
- Mock call history and state

**Why it's needed**: Prevents mock pollution from affecting subsequent test files. If a test file creates a patch and doesn't clean it up, the mock persists and affects the next test file.

**Scope**: `module` (runs after each test file completes)

**Autouse**: `True` (runs automatically)

**Example**:
```python
# Test file creates patches:
@patch('boto3.resource')
def test_something(mock_resource):
    pass

# Or module-level patch (bad practice):
mock_patch = patch('boto3.resource')
mock_patch.start()

# After test file completes, fixture stops all patches:
for patch_obj in _patch._active_patches:
    patch_obj.stop()
```

#### reset_environment_per_file

**Purpose**: Restores environment variables to original session state after each test file.

**What it resets**:
- All environment variables to session start values
- Removes variables added by test file
- Restores variables modified by test file

**Why it's needed**: Prevents environment variable pollution between test files. Tests often set environment variables like `AWS_REGION`, `DYNAMODB_TABLE_NAME`, etc. Without cleanup, these persist and affect subsequent test files.

**Scope**: `module` (runs after each test file completes)

**Autouse**: `True` (runs automatically)

**Example**:
```python
# Test file sets:
os.environ["PROTECTION_GROUPS_TABLE"] = "test-table"
os.environ["AWS_REGION"] = "us-west-2"
os.environ["NEW_TEST_VAR"] = "value"

# After test file completes, fixture restores:
os.environ.clear()
os.environ.update(original_environ)  # From capture_original_state

# Result:
# - NEW_TEST_VAR removed
# - PROTECTION_GROUPS_TABLE restored to original value (or removed if didn't exist)
# - AWS_REGION restored to original value
```

#### reset_sys_path_per_file

**Purpose**: Restores `sys.path` to original session state after each test file.

**What it resets**:
- Python import paths to session start values
- Removes paths added by test file (e.g., Lambda handler directories)

**Why it's needed**: Prevents import-time side effects from affecting subsequent test files. Tests often add Lambda handler directories to `sys.path` to import handler code. Without cleanup, these paths persist and can cause import conflicts.

**Scope**: `module` (runs after each test file completes)

**Autouse**: `True` (runs automatically)

**Example**:
```python
# Test file adds:
sys.path.insert(0, '/project/lambda/data-management-handler')
sys.path.insert(0, '/project/lambda/query-handler')

# After test file completes, fixture restores:
sys.path[:] = original_sys_path  # From capture_original_state

# Result:
sys.path = ['/project', '/usr/lib/python3.12', ...]  # Original paths only
```

#### reset_all_module_state_per_file

**Purpose**: Resets all module-level state before each test file runs.

**What it resets**:
- All Lambda handler table variables (30+ variables across 4 handlers)
- All shared module DynamoDB resources (10+ variables across 6 modules)
- Uses `MODULE_STATE_REGISTRY` to track what to reset

**Why it's needed**: **Critical for preventing cross-file test contamination**. This is the primary defense against module-level state pollution. Without this, cached DynamoDB tables and clients persist between test files, causing tests to share state.

**Scope**: `module` (runs before each test file starts)

**Autouse**: `True` (runs automatically)

**Debug output**:
```
======================================================================
[MODULE FIXTURE] Starting: tests.unit.test_query_handler_get_server_config_history
======================================================================
  Before reset - launch_config_service:
    _dynamodb: <boto3.resources.factory.dynamodb.ServiceResource>
    _protection_groups_table: <boto3.resources.factory.dynamodb.Table>
  
  Resetting all module state...
  
  After reset - launch_config_service:
    _dynamodb: None
    _protection_groups_table: None
======================================================================
```

**Example**:
```python
# Before test file:
shared.launch_config_service._dynamodb = None
shared.launch_config_service._protection_groups_table = None
lambda.data_management_handler.index._protection_groups_table = None
lambda.data_management_handler.index._recovery_plans_table = None
# ... (all 30+ variables reset)

# Test file runs and sets:
shared.launch_config_service._dynamodb = <boto3.resource>
shared.launch_config_service._protection_groups_table = <Table>

# Before next test file:
# Fixture resets everything back to None
```

### Function-Scoped Fixtures (Before Each Test)

#### reset_environment_variables

**Purpose**: Resets environment variables before and after each individual test.

**What it resets**:
- All environment variables to pre-test values
- Captures state before test, restores after test

**Why it's needed**: Prevents environment variable leakage between individual tests within the same file. Provides finer-grained isolation than module-scoped fixture.

**Scope**: `function` (runs before/after each test)

**Autouse**: `True` (runs automatically)

**Example**:
```python
# Before test_1:
original_env = os.environ.copy()

# test_1 runs and sets:
os.environ["TEST_VAR"] = "value1"

# After test_1:
os.environ.clear()
os.environ.update(original_env)  # TEST_VAR removed

# Before test_2:
# Clean environment, no TEST_VAR
```

#### reset_launch_config_globals

**Purpose**: Resets launch config service module-level variables before and after each test.

**What it resets**:
```python
shared.launch_config_service._dynamodb = None
shared.launch_config_service._protection_groups_table = None
```

**Why it's needed**: The launch config service caches DynamoDB resources globally. Without reset, tests share the same resource instance, causing state pollution and test interdependencies.

**Scope**: `function` (runs before/after each test)

**Autouse**: `True` (runs automatically)

**Example**:
```python
# Test 1 creates:
_dynamodb = boto3.resource('dynamodb')
_protection_groups_table = _dynamodb.Table('test-table')

# Without fixture, Test 2 would reuse these (BAD)
# With fixture, Test 2 starts with None and creates fresh resources (GOOD)
```

#### set_launch_config_env_vars

**Purpose**: Sets required environment variables for launch config tests.

**What it sets**:
```python
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups-table"
```

**Why it's needed**: Launch config service requires this environment variable to function. This fixture ensures it's always set for tests that need it, and properly restored afterward.

**Scope**: `function` (runs before/after each test)

**Autouse**: `True` (runs automatically)

**Example**:
```python
# Before test:
original_value = os.environ.get("PROTECTION_GROUPS_TABLE")  # Save original
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups-table"

# Test runs with required env var set

# After test:
if original_value is not None:
    os.environ["PROTECTION_GROUPS_TABLE"] = original_value  # Restore
else:
    del os.environ["PROTECTION_GROUPS_TABLE"]  # Remove if didn't exist
```

#### reset_logger_state

**Purpose**: Resets logging configuration before and after each test.

**What it resets**:
- Logger level (e.g., DEBUG, INFO, WARNING)
- Logger handlers (console, file, custom handlers)

**Why it's needed**: Prevents logger configuration from leaking between tests. Tests may configure logging for debugging, and this configuration should not affect other tests.

**Scope**: `function` (runs before/after each test)

**Autouse**: `True` (runs automatically)

**Example**:
```python
# Test 1 configures:
logger.setLevel(logging.DEBUG)
logger.addHandler(custom_handler)

# Without fixture, Test 2 inherits this configuration (BAD)
# With fixture, Test 2 starts with original logger state (GOOD)

# After test:
root_logger.setLevel(original_level)  # Restore level
root_logger.handlers = original_handlers  # Restore handlers
```

#### reset_data_management_handler_state

**Purpose**: Resets data-management-handler module-level table variables.

**What it resets** (6 tables):
```python
lambda.data_management_handler.index._protection_groups_table = None
lambda.data_management_handler.index._recovery_plans_table = None
lambda.data_management_handler.index._executions_table = None
lambda.data_management_handler.index._target_accounts_table = None
lambda.data_management_handler.index._tag_sync_config_table = None
lambda.data_management_handler.index._inventory_table = None
```

**Why it's needed**: This handler caches 6 DynamoDB tables at module level (lines 238-280 in handler code). Without reset, tests share table instances.

**Scope**: `function` (runs before/after each test)

**Autouse**: `True` (runs automatically)

#### reset_orchestration_handler_state

**Purpose**: Resets dr-orchestration-stepfunction module-level table variables.

**What it resets** (3 tables):
```python
lambda.dr_orchestration_stepfunction.index._protection_groups_table = None
lambda.dr_orchestration_stepfunction.index._recovery_plans_table = None
lambda.dr_orchestration_stepfunction.index._execution_history_table = None
```

**Why it's needed**: This handler caches 3 DynamoDB tables at module level (lines 213-253 in handler code).

**Scope**: `function` (runs before/after each test)

**Autouse**: `True` (runs automatically)

#### reset_execution_handler_state

**Purpose**: Resets execution-handler module-level table variables.

**What it resets** (4 tables, note: no underscore prefix):
```python
lambda.execution_handler.index.protection_groups_table = None
lambda.execution_handler.index.recovery_plans_table = None
lambda.execution_handler.index.execution_history_table = None
lambda.execution_handler.index.target_accounts_table = None
```

**Why it's needed**: This handler caches 4 DynamoDB tables at module level (lines 155-170 in handler code). **Note**: This handler uses direct initialization without underscore prefix, unlike other handlers.

**Scope**: `function` (runs before/after each test)

**Autouse**: `True` (runs automatically)

#### reset_query_handler_state

**Purpose**: Resets query-handler module-level table variables.

**What it resets** (6 tables):
```python
lambda.query_handler.index._protection_groups_table = None
lambda.query_handler.index._recovery_plans_table = None
lambda.query_handler.index._target_accounts_table = None
lambda.query_handler.index._execution_history_table = None
lambda.query_handler.index._region_status_table = None
lambda.query_handler.index._inventory_table = None
```

**Why it's needed**: This handler caches 6 DynamoDB tables at module level (lines 361-435 in handler code).

**Scope**: `function` (runs before/after each test)

**Autouse**: `True` (runs automatically)

#### reset_mock_state

**Purpose**: Resets mock call history before each test.

**What it resets**:
- Mock call counts (`mock.call_count`)
- Mock call arguments (`mock.call_args`, `mock.call_args_list`)

**Why it's needed**: Prevents mock call history from leaking between tests. Tests often assert on mock calls, and stale call history causes false positives/negatives.

**Scope**: `function` (runs before/after each test)

**Autouse**: `True` (runs automatically)

**Note**: Cleanup happens automatically with pytest's mock cleanup mechanism.

#### isolate_test_execution

**Purpose**: Ensures complete test isolation with consistent AWS environment.

**What it sets**:
```python
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_REGION'] = 'us-east-1'
```

**What it removes**:
```python
del os.environ['AWS_ACCESS_KEY_ID']  # Prevent real AWS calls
del os.environ['AWS_SECRET_ACCESS_KEY']
del os.environ['AWS_SESSION_TOKEN']
```

**Why it's needed**: Ensures tests don't accidentally use real AWS credentials and have consistent region settings. This is a critical safety measure.

**Scope**: `function` (runs before each test)

**Autouse**: `True` (runs automatically)

**Example**:
```python
# Before test:
# - AWS credentials removed (prevents real API calls)
# - AWS region set to us-east-1 (consistent test environment)

# Test runs safely without real AWS access

# After test:
# - Environment restored by reset_environment_variables fixture
```

### How Fixtures Work Together

#### Complete Test File Execution Flow

```python
# 1. Session Start (once per test run)
capture_original_state()  # Captures baseline: sys.path, environ, sys.modules
reset_all_module_state_session()  # Initial cleanup: all module variables → None

# 2. Before test_file_1.py starts
reset_all_module_state_per_file()  # Reset all module variables → None
reset_sys_path_per_file()  # Restore sys.path to original
reset_environment_per_file()  # Restore environment to original

# 3. Before test_file_1::test_1 runs
reset_environment_variables()  # Capture current env
reset_launch_config_globals()  # Reset launch config → None
set_launch_config_env_vars()  # Set PROTECTION_GROUPS_TABLE
reset_logger_state()  # Reset logging config
reset_data_management_handler_state()  # Reset handler tables → None
reset_orchestration_handler_state()  # Reset handler tables → None
reset_execution_handler_state()  # Reset handler tables → None
reset_query_handler_state()  # Reset handler tables → None
reset_mock_state()  # Reset mock history
isolate_test_execution()  # Set AWS env, remove credentials

# 4. Run test_file_1::test_1
# ... test executes with clean state ...

# 5. After test_file_1::test_1 completes
# All function-scoped fixtures cleanup (restore state)

# 6. Before test_file_1::test_2 runs
# All function-scoped fixtures run again (fresh state)

# 7. After test_file_1.py completes (all tests done)
cleanup_sys_modules_per_file()  # Remove modules added by test file
cleanup_mocks_per_file()  # Stop all active patches
reset_environment_per_file()  # Restore environment to original
reset_sys_path_per_file()  # Restore sys.path to original

# 8. Before test_file_2.py starts
# Module-scoped fixtures run again (fresh start for new file)
reset_all_module_state_per_file()  # Reset all module variables → None
# ... (repeat cycle for test_file_2.py)

# 9. Session End (after all test files complete)
# Session-scoped fixtures cleanup
```

#### Fixture Interaction Example

```python
# Session Start
capture_original_state()
# → Captures: sys.path=['/project', ...], environ={'HOME': '/home/user', ...}

# Before test_file_1.py
reset_all_module_state_per_file()
# → Sets: shared.launch_config_service._dynamodb = None

# Before test_file_1::test_1
reset_launch_config_globals()
# → Confirms: shared.launch_config_service._dynamodb = None
set_launch_config_env_vars()
# → Sets: os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups-table"
isolate_test_execution()
# → Sets: os.environ["AWS_REGION"] = "us-east-1"
# → Removes: os.environ["AWS_ACCESS_KEY_ID"]

# test_file_1::test_1 runs
# → Creates: shared.launch_config_service._dynamodb = <boto3.resource>

# After test_file_1::test_1
reset_launch_config_globals()
# → Resets: shared.launch_config_service._dynamodb = None

# Before test_file_1::test_2
# → Fresh state again, no pollution from test_1

# After test_file_1.py completes
reset_environment_per_file()
# → Restores: os.environ to original (removes PROTECTION_GROUPS_TABLE)
reset_sys_path_per_file()
# → Restores: sys.path to original

# Before test_file_2.py
# → Completely fresh state, no pollution from test_file_1.py
```

### MODULE_STATE_REGISTRY

The registry is the central source of truth for all module-level state that needs cleanup:

```python
MODULE_STATE_REGISTRY = {
    # Shared modules (6 modules, 10+ variables)
    "shared.launch_config_service": [
        "_dynamodb",
        "_protection_groups_table"
    ],
    "shared.staging_account_models": [
        "_dynamodb",
        "_target_accounts_table"
    ],
    "shared.notifications": [
        "_dynamodb_resource"
    ],
    "shared.account_utils": [
        "_dynamodb",
        "_target_accounts_table"
    ],
    "shared.conflict_detection": [
        "_protection_groups_table",
        "_recovery_plans_table",
        "_execution_history_table",
        "_inventory_table"
    ],
    "shared.cross_account": [
        "_dynamodb",
        "_protection_groups_table",
        "_target_accounts_table"
    ],
    
    # Lambda handlers (4 handlers, 20+ variables)
    "lambda.data_management_handler.index": [
        "_protection_groups_table",
        "_recovery_plans_table",
        "_executions_table",
        "_target_accounts_table",
        "_tag_sync_config_table",
        "_inventory_table"
    ],
    "lambda.dr_orchestration_stepfunction.index": [
        "_protection_groups_table",
        "_recovery_plans_table",
        "_execution_history_table"
    ],
    "lambda.execution_handler.index": [
        "protection_groups_table",  # Note: No underscore prefix
        "recovery_plans_table",
        "execution_history_table",
        "target_accounts_table"
    ],
    "lambda.query_handler.index": [
        "_protection_groups_table",
        "_recovery_plans_table",
        "_target_accounts_table",
        "_execution_history_table",
        "_region_status_table",
        "_inventory_table"
    ]
}
```

**How it's used**:
```python
def reset_module_variables(module, variable_names):
    """Reset specific module-level variables to None."""
    for var_name in variable_names:
        if hasattr(module, var_name):
            setattr(module, var_name, None)

def reset_shared_module_state():
    """Reset module-level state in shared modules."""
    shared_modules = [
        "shared.launch_config_service",
        "shared.staging_account_models",
        "shared.notifications",
        "shared.account_utils",
        "shared.conflict_detection",
        "shared.cross_account",
    ]
    
    for module_name in shared_modules:
        if module_name in sys.modules:
            module = sys.modules[module_name]
            variable_names = MODULE_STATE_REGISTRY.get(module_name, [])
            reset_module_variables(module, variable_names)
```

**Benefits**:
1. **Single source of truth**: All module state tracked in one place
2. **Easy maintenance**: Add new modules/variables to registry
3. **Systematic cleanup**: Ensures no state is missed
4. **Documentation**: Registry serves as documentation of module state

### Best Practices for Using Fixtures

#### 1. Trust the Autouse Fixtures

Most tests don't need to explicitly reference fixtures:

```python
# ✅ CORRECT - Fixtures run automatically
def test_something():
    """Standard test - isolation fixtures run automatically"""
    mock_table = MagicMock()
    with patch.object(index, "get_table", return_value=mock_table):
        result = index.lambda_handler(event, context)
        assert result["statusCode"] == 200
```

#### 2. Explicit Fixtures for Property-Based Tests

Hypothesis requires explicit fixture parameters:

```python
# ✅ CORRECT - Explicit fixtures for property tests
from hypothesis import given, strategies as st, settings, HealthCheck

@given(value=st.integers())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property(
    value,
    reset_environment_variables,
    reset_logger_state,
    reset_data_management_handler_state
):
    """Property test with explicit isolation fixtures"""
    assert validate_value(value) is not None
```

**Why explicit fixtures are needed**:
- Hypothesis generates multiple test cases from one test function
- Function-scoped fixtures normally run once per test function
- Explicit parameters ensure fixtures run for each generated case
- Health check suppression tells Hypothesis this is intentional

#### 3. Custom Fixtures Can Depend on Isolation Fixtures

```python
# ✅ CORRECT - Custom fixture depends on isolation
@pytest.fixture
def mock_dynamodb_with_clean_state(reset_data_management_handler_state):
    """Custom fixture that depends on state reset"""
    # This fixture needs clean state before setting up mocks
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": {...}}
    
    with patch.object(index, "get_table", return_value=mock_table):
        yield mock_table

def test_with_custom_fixture(mock_dynamodb_with_clean_state):
    """Test using custom fixture that depends on isolation"""
    result = index.lambda_handler(event, context)
    assert result["statusCode"] == 200
```

#### 4. Verify Fixture Behavior in Tests

```python
# ✅ CORRECT - Test that verifies fixture works
def test_environment_variables_are_reset(reset_environment_variables):
    """Verify environment variables are properly reset"""
    import os
    
    # Set a test variable
    os.environ["TEST_VAR"] = "test_value"
    
    # Fixture should reset environment after test
    # This test verifies the fixture works correctly
```

### Benefits of Multi-Layered Isolation

1. **Prevents Flaky Tests**: Each test starts with completely clean state
2. **Improves Test Reliability**: No hidden dependencies between tests
3. **Easier Debugging**: Test failures are isolated to the test itself
4. **Parallel Test Execution**: Tests can run in parallel safely
5. **Consistent Results**: Tests produce same results regardless of execution order
6. **Cross-File Isolation**: Test files don't pollute each other
7. **Performance**: Module-scoped fixtures reduce overhead vs function-scoped

### Troubleshooting Isolation Issues

#### Symptom: Test passes individually but fails with others

```bash
# Passes alone
pytest tests/unit/test_file.py::test_something -v  # ✅ PASSED

# Fails with others
pytest tests/unit/ -v  # ❌ FAILED
```

**Diagnosis**:
1. Check for module-level state not in `MODULE_STATE_REGISTRY`
2. Verify mock cleanup is working
3. Look for environment variable pollution
4. Check sys.path modifications

**Solution**: Add missing state to registry or create new cleanup fixture

#### Symptom: AttributeError: 'NoneType' object has no attribute

```python
AttributeError: 'NoneType' object has no attribute 'query'
```

**Diagnosis**: Module-level variable was reset to None but code is using cached reference

**Solution**: Ensure getter functions are mocked, not direct attributes:
```python
# ✅ CORRECT
with patch.object(index, "get_table", return_value=mock_table):
    pass

# ❌ WRONG
with patch.object(index, "table", mock_table):
    pass
```

#### Symptom: Tests fail in random order

```bash
pytest tests/unit/ -v --random-order
```

**Diagnosis**: Tests have hidden dependencies on execution order

**Solution**: Verify all fixtures are working, check for shared state

### Verification Commands

```bash
# Run tests in random order to verify isolation
pytest tests/unit/ -v --random-order

# Run specific test file multiple times
pytest tests/unit/test_file.py -v --count=10

# Run tests in parallel to verify no shared state
pytest tests/unit/ -v -n auto

# All tests should pass consistently regardless of order or parallelization
```

1. **`reset_environment_variables`**: Resets environment variables to a clean state
   - Clears all environment variables
   - Sets consistent test environment variables
   - Prevents environment pollution between tests

2. **`reset_logger_state`**: Resets logger configuration
   - Clears all logger handlers
   - Resets logger levels
   - Prevents log message interference between tests

3. **`reset_data_management_handler_state`**: Resets data-management-handler global tables
   - Clears `target_accounts_table` global variable
   - Clears `protection_groups_table` global variable
   - Clears `recovery_plans_table` global variable
   - Clears `tag_sync_config_table` global variable
   - Prevents table reference leakage between tests

4. **`reset_orchestration_handler_state`**: Resets dr-orchestration-stepfunction global tables
   - Clears `executions_table` global variable
   - Clears `protection_groups_table` global variable
   - Prevents table reference leakage between tests

5. **`reset_execution_handler_state`**: Resets execution-handler global tables
   - Clears `executions_table` global variable
   - Clears `protection_groups_table` global variable
   - Prevents table reference leakage between tests

6. **`reset_query_handler_state`**: Resets query-handler global tables
   - Clears `target_accounts_table` global variable
   - Clears `protection_groups_table` global variable
   - Clears `recovery_plans_table` global variable
   - Prevents table reference leakage between tests

7. **`reset_mock_state`**: Resets mock call history
   - Clears all mock call counts
   - Resets mock return values
   - Prevents mock state leakage between tests

8. **`isolate_test_execution`**: Sets consistent test environment
   - Combines all isolation fixtures
   - Ensures complete test isolation
   - Runs before every test automatically

### When to Use Explicit Fixtures

Most tests don't need to explicitly reference these fixtures since they use `autouse=True`. However, you may need to explicitly add them as parameters in these cases:

#### 1. Property-Based Tests with Hypothesis

Hypothesis requires explicit fixture parameters and suppression of the `function_scoped_fixture` health check:

```python
from hypothesis import given, strategies as st, settings, HealthCheck

@given(value=st.integers())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_with_property_based_testing(
    value,
    reset_environment_variables,
    reset_logger_state,
    reset_data_management_handler_state
):
    """Property test with explicit isolation fixtures"""
    # Test implementation
    assert validate_value(value) is not None
```

**Why This Is Needed**:
- Hypothesis generates multiple test cases from a single test function
- Function-scoped fixtures normally run once per test function
- Explicit parameters ensure fixtures run for each generated test case
- The health check suppression tells Hypothesis this is intentional

#### 2. Tests That Verify Fixture Behavior

When testing the fixtures themselves or verifying isolation behavior:

```python
def test_environment_variables_are_reset(reset_environment_variables):
    """Verify environment variables are properly reset"""
    import os
    
    # Set a test variable
    os.environ["TEST_VAR"] = "test_value"
    
    # Fixture should have already reset environment
    # This test verifies the fixture works correctly
    assert "TEST_VAR" not in os.environ or os.environ["TEST_VAR"] != "test_value"
```

#### 3. Tests with Custom Fixture Dependencies

When your custom fixture depends on an isolation fixture:

```python
@pytest.fixture
def mock_dynamodb_with_clean_state(reset_data_management_handler_state):
    """Custom fixture that depends on state reset"""
    # This fixture needs clean state before setting up mocks
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": {...}}
    
    with patch.object(index, "get_target_accounts_table", return_value=mock_table):
        yield mock_table

def test_with_custom_fixture(mock_dynamodb_with_clean_state):
    """Test using custom fixture that depends on isolation"""
    result = index.lambda_handler(event, context)
    assert result["statusCode"] == 200
```

### Example: Standard Test (No Explicit Fixtures)

```python
def test_create_protection_group_success():
    """Standard test - isolation fixtures run automatically"""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {}
    mock_table.put_item.return_value = {}
    
    with patch.object(index, "get_protection_groups_table", return_value=mock_table):
        event = {
            "body": json.dumps({
                "groupName": "test-group",
                "sourceServerIds": ["s-1234567890abcdef0"]
            })
        }
        
        result = index.lambda_handler(event, context)
        assert result["statusCode"] == 200
```

### Example: Property-Based Test (Explicit Fixtures)

```python
from hypothesis import given, strategies as st, settings, HealthCheck

@given(
    group_name=st.text(min_size=1, max_size=50),
    server_count=st.integers(min_value=1, max_value=10)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_protection_group_creation(
    group_name,
    server_count,
    reset_environment_variables,
    reset_logger_state,
    reset_data_management_handler_state
):
    """Property test with explicit isolation fixtures"""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {}
    mock_table.put_item.return_value = {}
    
    with patch.object(index, "get_protection_groups_table", return_value=mock_table):
        server_ids = [f"s-{i:017x}" for i in range(server_count)]
        
        event = {
            "body": json.dumps({
                "groupName": group_name,
                "sourceServerIds": server_ids
            })
        }
        
        result = index.lambda_handler(event, context)
        assert result["statusCode"] == 200
        mock_table.put_item.assert_called_once()
```

### Benefits of Test Isolation

1. **Prevents Flaky Tests**: Each test starts with a clean slate
2. **Improves Test Reliability**: No hidden dependencies between tests
3. **Easier Debugging**: Test failures are isolated to the test itself
4. **Parallel Test Execution**: Tests can run in parallel safely
5. **Consistent Results**: Tests produce the same results regardless of execution order

### Troubleshooting

If you encounter issues with test isolation:

1. **Check for Global State**: Look for module-level variables that aren't being reset
2. **Verify Mock Cleanup**: Ensure mocks are properly cleaned up after each test
3. **Review Fixture Order**: Fixtures run in dependency order, check for conflicts
4. **Add Explicit Fixtures**: For property-based tests, add fixtures as parameters
5. **Check Environment Variables**: Verify environment variables are being reset

---

## Cross-File Test Isolation

### Overview

Cross-file test pollution occurs when tests in one file affect tests in another file, causing failures that only appear when tests run together. This section documents the problem, solution, and best practices for maintaining proper test isolation.

### The Problem: Cross-File Pollution

#### What Is Cross-File Pollution?

Cross-file pollution happens when:
1. **Test File A** runs and modifies global state (mocks, environment variables, module imports)
2. **Test File B** runs next and inherits the polluted state from Test File A
3. **Test File B** fails because it expects clean state but gets polluted state

**Key Characteristic**: Tests pass when run individually but fail when run together with other tests.

#### Common Sources of Pollution

**1. Mock Pollution**
```python
# File: test_file_a.py
def test_something():
    with patch("module.function") as mock_func:
        mock_func.return_value = "test_value"
        # Test code
    # Mock is cleaned up here

# But if the mock was created at module level...
mock_func = patch("module.function")
mock_func.start()  # ❌ This persists across test files!

def test_something():
    # Test code
    pass
# Mock is NEVER cleaned up - pollutes other test files
```

**2. sys.path Pollution**
```python
# File: test_file_a.py
import sys
sys.path.insert(0, "/path/to/lambda/handler")  # ❌ Persists across files

def test_something():
    import index  # Imports from modified sys.path
    # Test code
```

**3. Environment Variable Pollution**
```python
# File: test_file_a.py
import os
os.environ["AWS_REGION"] = "us-west-2"  # ❌ Persists across files

def test_something():
    # Test code that uses AWS_REGION
```

**4. Module-Level Global State**
```python
# File: lambda/handler/index.py
target_accounts_table = None  # Global variable

def get_target_accounts_table():
    global target_accounts_table
    if target_accounts_table is None:
        target_accounts_table = boto3.resource("dynamodb").Table("accounts")
    return target_accounts_table

# File: test_file_a.py
def test_something():
    mock_table = MagicMock()
    with patch.object(index, "get_target_accounts_table", return_value=mock_table):
        # Test code
    # But index.target_accounts_table is still set to mock_table!
    # This pollutes test_file_b.py
```

#### Real-World Example: The Failing Test

**Symptom**:
```bash
# Test passes individually
pytest tests/unit/test_query_handler_get_server_config_history.py -v
# ✅ PASSED

# Test fails when run with other tests
pytest tests/unit/ -v
# ❌ FAILED - AttributeError: 'NoneType' object has no attribute 'query'
```

**Root Cause**:
1. `test_file_a.py` patches `get_target_accounts_table()` and sets `index.target_accounts_table = mock_table`
2. `test_file_a.py` finishes, mock is cleaned up, but `index.target_accounts_table` is still set
3. `test_file_b.py` runs and calls `get_target_accounts_table()`
4. Function returns the cached `index.target_accounts_table` (which is now `None` or invalid)
5. Test fails with `AttributeError` because it's using a stale reference

### The Solution: Module-Scoped Cleanup Fixtures

#### Why Module-Scoped?

**Function-scoped fixtures** (`scope="function"`) run before/after each test function:
- ✅ Good for test-specific setup/teardown
- ❌ Don't prevent pollution between test files
- ❌ Run too frequently (performance overhead)

**Module-scoped fixtures** (`scope="module"`) run once per test file:
- ✅ Clean up state after entire test file completes
- ✅ Prevent pollution from affecting next test file
- ✅ Better performance (run once per file, not per test)
- ✅ Perfect for cleaning up global state

#### Implementation Pattern

**Location**: `tests/unit/conftest.py` (shared across all test files)

```python
import pytest
import sys
import os
from unittest.mock import patch

@pytest.fixture(scope="module", autouse=True)
def cleanup_module_state():
    """
    Module-scoped fixture that cleans up global state after each test file.
    
    Runs automatically (autouse=True) after all tests in a file complete.
    Prevents pollution from affecting subsequent test files.
    """
    # Setup: runs before test file
    yield
    
    # Teardown: runs after all tests in file complete
    
    # 1. Clean up sys.path modifications
    original_paths = [
        "/path/to/lambda/data-management-handler",
        "/path/to/lambda/query-handler",
        "/path/to/lambda/execution-handler",
        "/path/to/lambda/dr-orchestration-stepfunction"
    ]
    for path in original_paths:
        while path in sys.path:
            sys.path.remove(path)
    
    # 2. Reset module-level global variables
    try:
        import lambda.data_management_handler.index as dm_index
        dm_index.target_accounts_table = None
        dm_index.protection_groups_table = None
        dm_index.recovery_plans_table = None
        dm_index.tag_sync_config_table = None
    except (ImportError, AttributeError):
        pass
    
    try:
        import lambda.query_handler.index as query_index
        query_index.target_accounts_table = None
        query_index.protection_groups_table = None
        query_index.recovery_plans_table = None
    except (ImportError, AttributeError):
        pass
    
    # 3. Clean up environment variables
    test_env_vars = [
        "AWS_REGION",
        "DYNAMODB_TABLE_NAME",
        "TEST_MODE"
    ]
    for var in test_env_vars:
        os.environ.pop(var, None)
    
    # 4. Stop any lingering mocks
    patch.stopall()
```

#### Key Features

**1. `scope="module"`**: Runs once per test file
```python
@pytest.fixture(scope="module", autouse=True)
def cleanup_module_state():
    yield  # All tests in file run here
    # Cleanup runs after all tests complete
```

**2. `autouse=True`**: Runs automatically without explicit reference
```python
# No need to add fixture as parameter
def test_something():
    # cleanup_module_state runs automatically
    pass
```

**3. `yield` Pattern**: Setup before, cleanup after
```python
def cleanup_module_state():
    # Setup code (if needed)
    yield  # Tests run here
    # Cleanup code (always runs)
```

**4. Exception Handling**: Graceful handling of missing modules
```python
try:
    import module
    module.global_var = None
except (ImportError, AttributeError):
    pass  # Module not imported in this test file
```

### Fixture Scope Comparison

| Scope | Runs | Use Case | Example |
|-------|------|----------|---------|
| `function` | Before/after each test | Test-specific setup | Mock for single test |
| `class` | Before/after each test class | Shared setup for test class | Database connection |
| `module` | Before/after each test file | **Cross-file isolation** | **Global state cleanup** |
| `session` | Once per test session | Expensive one-time setup | Test database creation |

### When to Use Each Scope

#### Use Function Scope When:
- Setup is test-specific and not shared
- Cleanup must happen immediately after test
- State should not persist between tests in same file

```python
@pytest.fixture(scope="function")
def mock_dynamodb_table():
    """Function-scoped: fresh mock for each test"""
    mock_table = MagicMock()
    yield mock_table
    # Cleanup happens after each test
```

#### Use Module Scope When:
- Cleaning up global state that persists across tests
- Preventing pollution between test files
- Expensive setup that can be shared within a file

```python
@pytest.fixture(scope="module", autouse=True)
def cleanup_global_state():
    """Module-scoped: cleanup after entire file"""
    yield
    # Cleanup happens after all tests in file
    reset_global_variables()
```

#### Use Session Scope When:
- One-time expensive setup for entire test run
- Shared resources across all test files
- Database initialization, test data loading

```python
@pytest.fixture(scope="session")
def test_database():
    """Session-scoped: created once for all tests"""
    db = create_test_database()
    yield db
    db.cleanup()
```

### Best Practices for Test Isolation

#### 1. Always Clean Up Global State

**DO**:
```python
@pytest.fixture(scope="module", autouse=True)
def cleanup_module_state():
    """Clean up after test file completes"""
    yield
    
    # Reset all global variables
    import module
    module.global_var = None
    module.cached_client = None
```

**DON'T**:
```python
# ❌ No cleanup - pollutes other test files
def test_something():
    import module
    module.global_var = "test_value"
    # Test code
    # global_var persists after test!
```

#### 2. Use Context Managers for Temporary Changes

**DO**:
```python
def test_with_environment_variable():
    """Use context manager for temporary changes"""
    with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}):
        # Test code
        pass
    # Environment variable automatically cleaned up
```

**DON'T**:
```python
def test_with_environment_variable():
    """Direct modification persists"""
    os.environ["AWS_REGION"] = "us-west-2"  # ❌ Persists!
    # Test code
    # Need manual cleanup
```

#### 3. Avoid Module-Level Mocks

**DO**:
```python
def test_with_mock():
    """Create mock inside test function"""
    with patch("module.function") as mock_func:
        mock_func.return_value = "test"
        # Test code
    # Mock automatically cleaned up
```

**DON'T**:
```python
# ❌ Module-level mock persists across files
mock_func = patch("module.function")
mock_func.start()

def test_with_mock():
    # Test code
    pass
# Mock never cleaned up!
```

#### 4. Reset sys.path Modifications

**DO**:
```python
@pytest.fixture(scope="module", autouse=True)
def cleanup_sys_path():
    """Clean up sys.path after test file"""
    yield
    
    paths_to_remove = ["/path/to/lambda/handler"]
    for path in paths_to_remove:
        while path in sys.path:
            sys.path.remove(path)
```

**DON'T**:
```python
# ❌ sys.path modification persists
import sys
sys.path.insert(0, "/path/to/lambda/handler")

def test_something():
    import index  # Uses modified sys.path
    # Test code
# sys.path still modified!
```

#### 5. Use Explicit Imports in Tests

**DO**:
```python
def test_something():
    """Import inside test function"""
    import lambda.handler.index as index
    
    mock_table = MagicMock()
    with patch.object(index, "get_table", return_value=mock_table):
        result = index.lambda_handler(event, context)
```

**DON'T**:
```python
# ❌ Module-level import can cache polluted state
import lambda.handler.index as index

def test_something():
    # index module may have polluted state from previous test file
    result = index.lambda_handler(event, context)
```

### Debugging Cross-File Pollution

#### Step 1: Identify the Problem

**Symptoms**:
- Test passes individually: `pytest tests/unit/test_file.py -v` ✅
- Test fails with others: `pytest tests/unit/ -v` ❌
- Error mentions `None`, `AttributeError`, or unexpected values

**Diagnosis**:
```bash
# Run tests in different orders to isolate culprit
pytest tests/unit/test_file_a.py tests/unit/test_file_b.py -v
pytest tests/unit/test_file_b.py tests/unit/test_file_a.py -v

# If results differ, you have cross-file pollution
```

#### Step 2: Find the Source

**Check for**:
1. Module-level mocks or patches
2. Global variable modifications
3. sys.path modifications
4. Environment variable changes
5. Cached module imports

**Inspection**:
```python
# Add debug output to conftest.py
@pytest.fixture(scope="module", autouse=True)
def cleanup_module_state():
    yield
    
    # Debug: print state before cleanup
    import sys
    print(f"sys.path: {sys.path}")
    
    import module
    print(f"module.global_var: {module.global_var}")
    
    # Cleanup code
```

#### Step 3: Add Cleanup Fixture

**Solution**:
```python
@pytest.fixture(scope="module", autouse=True)
def cleanup_module_state():
    """Clean up the specific pollution source"""
    yield
    
    # Clean up the identified pollution
    import module
    module.global_var = None
    
    # Remove sys.path modifications
    while "/polluting/path" in sys.path:
        sys.path.remove("/polluting/path")
```

#### Step 4: Verify Fix

```bash
# Run tests together multiple times
pytest tests/unit/ -v
pytest tests/unit/ -v --random-order

# All tests should pass consistently
```

### Common Patterns and Solutions

#### Pattern 1: DynamoDB Table Caching

**Problem**:
```python
# lambda/handler/index.py
target_accounts_table = None  # Cached globally

def get_target_accounts_table():
    global target_accounts_table
    if target_accounts_table is None:
        target_accounts_table = boto3.resource("dynamodb").Table("accounts")
    return target_accounts_table
```

**Solution**:
```python
@pytest.fixture(scope="module", autouse=True)
def cleanup_dynamodb_cache():
    """Reset DynamoDB table cache after test file"""
    yield
    
    import lambda.handler.index as index
    index.target_accounts_table = None
```

#### Pattern 2: AWS Client Caching

**Problem**:
```python
# lambda/handler/index.py
drs_client = None  # Cached globally

def get_drs_client():
    global drs_client
    if drs_client is None:
        drs_client = boto3.client("drs")
    return drs_client
```

**Solution**:
```python
@pytest.fixture(scope="module", autouse=True)
def cleanup_aws_clients():
    """Reset AWS client cache after test file"""
    yield
    
    import lambda.handler.index as index
    index.drs_client = None
```

#### Pattern 3: Logger Configuration

**Problem**:
```python
# test_file_a.py
import logging
logging.basicConfig(level=logging.DEBUG)  # Persists!

def test_something():
    # Test code
```

**Solution**:
```python
@pytest.fixture(scope="module", autouse=True)
def cleanup_logger():
    """Reset logger configuration after test file"""
    yield
    
    import logging
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(logging.WARNING)
```

### Testing the Isolation

#### Verify Cleanup Works

```python
def test_isolation_verification():
    """Verify cleanup fixtures work correctly"""
    import lambda.handler.index as index
    
    # Set global state
    index.target_accounts_table = "test_value"
    
    # After test file completes, cleanup fixture should reset this
    # Next test file should see None, not "test_value"
```

#### Run Tests in Random Order

```bash
# Install pytest-random-order
pip install pytest-random-order

# Run tests in random order
pytest tests/unit/ -v --random-order

# Tests should pass regardless of order
```

### Summary

**Key Takeaways**:
1. **Cross-file pollution** occurs when global state persists between test files
2. **Module-scoped fixtures** (`scope="module"`) clean up after each test file
3. **`autouse=True`** makes fixtures run automatically without explicit reference
4. **Always clean up**: mocks, global variables, sys.path, environment variables
5. **Test isolation** prevents flaky tests and enables parallel execution

**Quick Checklist**:
- [ ] Module-scoped cleanup fixtures in `conftest.py`
- [ ] Reset all global variables after test file
- [ ] Clean up sys.path modifications
- [ ] Reset environment variables
- [ ] Stop all lingering mocks
- [ ] Use context managers for temporary changes
- [ ] Avoid module-level mocks
- [ ] Test with `--random-order` to verify isolation

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

## Debugging Test Isolation Issues

### Overview

This section provides practical debugging techniques for identifying and resolving test isolation issues. Use these techniques when tests pass individually but fail when run together, or when tests exhibit inconsistent behavior.

### How to Identify Mock Pollution

**Symptom**: Tests fail with unexpected mock behavior or mock calls from previous tests.

#### Detection Techniques

**1. Check Mock Call History**

```python
# Add debug output to see mock state
def test_something(mock_table):
    print(f"Mock call count at start: {mock_table.get_item.call_count}")
    print(f"Mock call history: {mock_table.get_item.call_args_list}")
    
    # Your test code
    result = index.lambda_handler(event, context)
    
    print(f"Mock call count at end: {mock_table.get_item.call_count}")
```

**2. Verify Mock Cleanup**

```python
# Add to conftest.py to verify mocks are cleaned up
@pytest.fixture(scope="module", autouse=True)
def debug_mock_state():
    """Debug fixture to verify mock cleanup"""
    yield
    
    # Check for active patches
    from unittest.mock import _patch
    active_patches = len(_patch._active_patches)
    if active_patches > 0:
        print(f"WARNING: {active_patches} active patches after test file!")
        for patch_obj in _patch._active_patches:
            print(f"  - {patch_obj}")
```

**3. Run Tests with Mock Debugging**

```bash
# Run tests with verbose mock output
pytest tests/unit/test_file.py -v -s

# Look for:
# - Unexpected mock calls
# - Mock call counts > 1 at test start
# - Mock return values from previous tests
```

#### Common Mock Pollution Patterns

**Pattern 1: Module-Level Mock**

```python
# ❌ WRONG - Mock persists across test files
mock_client = patch("boto3.client")
mock_client.start()

def test_something():
    # Test code
    pass
# Mock never stopped!
```

**Fix**:
```python
# ✅ CORRECT - Mock cleaned up automatically
def test_something():
    with patch("boto3.client") as mock_client:
        # Test code
        pass
    # Mock automatically stopped
```

**Pattern 2: Fixture Without Cleanup**

```python
# ❌ WRONG - Fixture doesn't clean up mock
@pytest.fixture
def mock_drs_client():
    mock_client = MagicMock()
    patch_obj = patch("boto3.client", return_value=mock_client)
    patch_obj.start()
    return mock_client
    # patch_obj never stopped!
```

**Fix**:
```python
# ✅ CORRECT - Fixture cleans up mock
@pytest.fixture
def mock_drs_client():
    mock_client = MagicMock()
    with patch("boto3.client", return_value=mock_client):
        yield mock_client
    # Mock automatically stopped after yield
```

**Pattern 3: Shared Mock State**

```python
# ❌ WRONG - Mock state shared between tests
mock_table = MagicMock()

def test_first():
    mock_table.get_item.return_value = {"Item": {"id": "1"}}
    # Test code

def test_second():
    # mock_table still has return_value from test_first!
    # This causes unexpected behavior
```

**Fix**:
```python
# ✅ CORRECT - Fresh mock for each test
@pytest.fixture
def mock_table():
    """Fresh mock for each test"""
    return MagicMock()

def test_first(mock_table):
    mock_table.get_item.return_value = {"Item": {"id": "1"}}
    # Test code

def test_second(mock_table):
    # Fresh mock, no pollution from test_first
    mock_table.get_item.return_value = {"Item": {"id": "2"}}
    # Test code
```

### How to Identify sys.path Pollution

**Symptom**: Import errors, wrong modules imported, or tests fail with "module not found" errors.

#### Detection Techniques

**1. Print sys.path State**

```python
# Add to conftest.py to track sys.path changes
@pytest.fixture(scope="module", autouse=True)
def debug_sys_path():
    """Debug fixture to track sys.path changes"""
    import sys
    original_paths = sys.path.copy()
    
    print(f"\n[DEBUG] sys.path at module start ({len(original_paths)} entries):")
    for i, path in enumerate(original_paths):
        print(f"  [{i}] {path}")
    
    yield
    
    current_paths = sys.path.copy()
    added_paths = [p for p in current_paths if p not in original_paths]
    removed_paths = [p for p in original_paths if p not in current_paths]
    
    if added_paths:
        print(f"\n[DEBUG] Paths ADDED during test file:")
        for path in added_paths:
            print(f"  + {path}")
    
    if removed_paths:
        print(f"\n[DEBUG] Paths REMOVED during test file:")
        for path in removed_paths:
            print(f"  - {path}")
```

**2. Check for Lambda Handler Paths**

```python
# Common Lambda handler paths that cause pollution
lambda_paths = [
    "/project/lambda/data-management-handler",
    "/project/lambda/query-handler",
    "/project/lambda/execution-handler",
    "/project/lambda/dr-orchestration-stepfunction"
]

import sys
for path in lambda_paths:
    if path in sys.path:
        print(f"WARNING: Lambda path in sys.path: {path}")
```

**3. Run Tests with Path Debugging**

```bash
# Run single test and check sys.path
pytest tests/unit/test_file.py::test_something -v -s

# Run multiple tests and compare sys.path
pytest tests/unit/test_file_a.py tests/unit/test_file_b.py -v -s
```

#### Common sys.path Pollution Patterns

**Pattern 1: Direct sys.path Modification**

```python
# ❌ WRONG - Modification persists across test files
import sys
sys.path.insert(0, "/path/to/lambda/handler")

def test_something():
    import index  # Uses modified sys.path
    # Test code
# sys.path still modified!
```

**Fix**:
```python
# ✅ CORRECT - Use fixture to clean up
@pytest.fixture
def lambda_handler_path():
    """Add Lambda handler to sys.path temporarily"""
    import sys
    path = "/path/to/lambda/handler"
    sys.path.insert(0, path)
    yield
    sys.path.remove(path)

def test_something(lambda_handler_path):
    import index  # Uses modified sys.path
    # Test code
    # sys.path automatically restored
```

**Pattern 2: Module-Level Path Addition**

```python
# ❌ WRONG - Module-level modification persists
import sys
import os

# This runs when test file is imported
handler_path = os.path.join(os.getcwd(), "lambda", "handler")
sys.path.insert(0, handler_path)

def test_something():
    # Test code
```

**Fix**:
```python
# ✅ CORRECT - Add path in fixture or test function
def test_something():
    import sys
    import os
    
    handler_path = os.path.join(os.getcwd(), "lambda", "handler")
    sys.path.insert(0, handler_path)
    
    try:
        import index
        # Test code
    finally:
        sys.path.remove(handler_path)
```

### How to Identify Environment Variable Pollution

**Symptom**: Tests fail with wrong AWS region, missing environment variables, or unexpected configuration values.

#### Detection Techniques

**1. Print Environment State**

```python
# Add to conftest.py to track environment changes
@pytest.fixture(scope="module", autouse=True)
def debug_environment():
    """Debug fixture to track environment variable changes"""
    import os
    original_env = os.environ.copy()
    
    print(f"\n[DEBUG] Environment at module start ({len(original_env)} variables)")
    
    # Print AWS-related variables
    aws_vars = {k: v for k, v in original_env.items() if k.startswith("AWS_")}
    if aws_vars:
        print("[DEBUG] AWS environment variables:")
        for key, value in aws_vars.items():
            print(f"  {key}={value}")
    
    yield
    
    current_env = os.environ.copy()
    added_vars = {k: v for k, v in current_env.items() if k not in original_env}
    changed_vars = {k: (original_env[k], current_env[k]) 
                    for k in original_env 
                    if k in current_env and original_env[k] != current_env[k]}
    removed_vars = {k: v for k, v in original_env.items() if k not in current_env}
    
    if added_vars:
        print(f"\n[DEBUG] Environment variables ADDED:")
        for key, value in added_vars.items():
            print(f"  + {key}={value}")
    
    if changed_vars:
        print(f"\n[DEBUG] Environment variables CHANGED:")
        for key, (old, new) in changed_vars.items():
            print(f"  ~ {key}: {old} → {new}")
    
    if removed_vars:
        print(f"\n[DEBUG] Environment variables REMOVED:")
        for key, value in removed_vars.items():
            print(f"  - {key}={value}")
```

**2. Check Specific Variables**

```python
# Check for common test environment variables
import os

test_vars = [
    "AWS_REGION",
    "AWS_DEFAULT_REGION",
    "PROTECTION_GROUPS_TABLE",
    "TARGET_ACCOUNTS_TABLE",
    "DYNAMODB_TABLE_NAME"
]

for var in test_vars:
    value = os.environ.get(var)
    if value:
        print(f"{var}={value}")
    else:
        print(f"{var} not set")
```

**3. Run Tests with Environment Debugging**

```bash
# Run test and print environment
pytest tests/unit/test_file.py -v -s

# Check for unexpected AWS_REGION
pytest tests/unit/ -v -s | grep "AWS_REGION"
```

#### Common Environment Variable Pollution Patterns

**Pattern 1: Direct Environment Modification**

```python
# ❌ WRONG - Modification persists across test files
import os
os.environ["AWS_REGION"] = "us-west-2"

def test_something():
    # Test code that uses AWS_REGION
# AWS_REGION still set to us-west-2!
```

**Fix**:
```python
# ✅ CORRECT - Use context manager
def test_something():
    with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}):
        # Test code that uses AWS_REGION
        pass
    # AWS_REGION automatically restored
```

**Pattern 2: Module-Level Environment Setup**

```python
# ❌ WRONG - Module-level modification persists
import os

# This runs when test file is imported
os.environ["PROTECTION_GROUPS_TABLE"] = "test-table"
os.environ["AWS_REGION"] = "us-east-1"

def test_something():
    # Test code
```

**Fix**:
```python
# ✅ CORRECT - Use fixture
@pytest.fixture
def test_environment():
    """Set test environment variables"""
    with patch.dict(os.environ, {
        "PROTECTION_GROUPS_TABLE": "test-table",
        "AWS_REGION": "us-east-1"
    }):
        yield

def test_something(test_environment):
    # Test code
    # Environment automatically restored
```

### How to Use Debug Logging in Fixtures

#### Enable Debug Output

**1. Add Debug Logging to conftest.py**

```python
# tests/unit/conftest.py
import logging

# Enable debug logging for fixtures
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)

@pytest.fixture(scope="module", autouse=True)
def reset_all_module_state_per_file():
    """Reset all module state before each test file"""
    logger.debug("=" * 70)
    logger.debug(f"Starting test file: {pytest.current_test_module}")
    logger.debug("=" * 70)
    
    # Reset module state
    reset_shared_module_state()
    reset_lambda_handler_state()
    
    logger.debug("Module state reset complete")
    
    yield
    
    logger.debug("Test file complete, cleaning up")
```

**2. Add Debug Output to Specific Fixtures**

```python
@pytest.fixture(scope="function", autouse=True)
def reset_data_management_handler_state():
    """Reset data-management-handler state before each test"""
    logger.debug("Resetting data-management-handler state")
    
    try:
        import lambda.data_management_handler.index as index
        
        # Log current state
        logger.debug(f"  Before: _protection_groups_table = {index._protection_groups_table}")
        logger.debug(f"  Before: _target_accounts_table = {index._target_accounts_table}")
        
        # Reset state
        index._protection_groups_table = None
        index._target_accounts_table = None
        
        # Log new state
        logger.debug(f"  After: _protection_groups_table = {index._protection_groups_table}")
        logger.debug(f"  After: _target_accounts_table = {index._target_accounts_table}")
        
    except (ImportError, AttributeError) as e:
        logger.debug(f"  Could not reset: {e}")
    
    yield
```

**3. Run Tests with Debug Output**

```bash
# Run tests with debug logging
pytest tests/unit/test_file.py -v -s --log-cli-level=DEBUG

# Filter debug output
pytest tests/unit/ -v -s --log-cli-level=DEBUG 2>&1 | grep "DEBUG"

# Save debug output to file
pytest tests/unit/ -v -s --log-cli-level=DEBUG > debug.log 2>&1
```

#### Debug Logging Best Practices

**DO**:
```python
# ✅ Log state before and after changes
logger.debug(f"Before reset: table = {module.table}")
module.table = None
logger.debug(f"After reset: table = {module.table}")

# ✅ Log fixture execution
logger.debug(f"Fixture {fixture_name} starting")
# Fixture code
logger.debug(f"Fixture {fixture_name} complete")

# ✅ Log exceptions
try:
    # Code that might fail
    pass
except Exception as e:
    logger.debug(f"Exception in fixture: {e}", exc_info=True)
```

**DON'T**:
```python
# ❌ Don't log sensitive data
logger.debug(f"AWS credentials: {os.environ['AWS_SECRET_ACCESS_KEY']}")

# ❌ Don't log too much
logger.debug(f"Full environment: {os.environ}")  # Too verbose

# ❌ Don't use print() instead of logging
print("Debug output")  # Use logger.debug() instead
```

### How to Test Individual Files vs Full Suite

#### Testing Individual Files

**1. Run Single Test File**

```bash
# Run one test file
pytest tests/unit/test_file.py -v

# Run with debug output
pytest tests/unit/test_file.py -v -s

# Run specific test
pytest tests/unit/test_file.py::test_something -v
```

**2. Run Multiple Specific Files**

```bash
# Run two files in order
pytest tests/unit/test_file_a.py tests/unit/test_file_b.py -v

# Run in reverse order to check for pollution
pytest tests/unit/test_file_b.py tests/unit/test_file_a.py -v

# If results differ, you have cross-file pollution
```

**3. Run File Multiple Times**

```bash
# Install pytest-repeat
pip install pytest-repeat

# Run file 10 times to check for flakiness
pytest tests/unit/test_file.py -v --count=10

# All runs should pass consistently
```

#### Testing Full Suite

**1. Run All Tests**

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ -v --cov=lambda --cov-report=term

# Run in parallel
pytest tests/unit/ -v -n auto
```

**2. Run Tests in Random Order**

```bash
# Install pytest-randomly
pip install pytest-randomly

# Run tests in random order
pytest tests/unit/ -v --randomly-seed=12345

# Run multiple times with different seeds
pytest tests/unit/ -v --randomly-seed=1
pytest tests/unit/ -v --randomly-seed=2
pytest tests/unit/ -v --randomly-seed=3

# All runs should pass consistently
```

**3. Compare Individual vs Suite Results**

```bash
# Run individual file
pytest tests/unit/test_file.py -v > individual.log 2>&1

# Run full suite
pytest tests/unit/ -v > suite.log 2>&1

# Compare results
diff individual.log suite.log

# Look for:
# - Tests that pass individually but fail in suite
# - Different error messages
# - Different mock call counts
```

### How to Use pytest-randomly to Find Order Dependencies

#### Installation and Basic Usage

```bash
# Install pytest-randomly
pip install pytest-randomly

# Run tests in random order
pytest tests/unit/ -v

# Run with specific seed for reproducibility
pytest tests/unit/ -v --randomly-seed=12345

# Disable random order (useful for debugging)
pytest tests/unit/ -v -p no:randomly
```

#### Finding Order-Dependent Tests

**1. Run Tests Multiple Times with Different Seeds**

```bash
# Create script to run tests with different seeds
#!/bin/bash
for seed in {1..10}; do
    echo "Running with seed $seed"
    pytest tests/unit/ -v --randomly-seed=$seed
    if [ $? -ne 0 ]; then
        echo "FAILED with seed $seed"
        exit 1
    fi
done
echo "All seeds passed!"
```

**2. Identify Failing Seed**

```bash
# When a test fails, note the seed
pytest tests/unit/ -v --randomly-seed=42
# FAILED tests/unit/test_file.py::test_something

# Reproduce failure with same seed
pytest tests/unit/ -v --randomly-seed=42

# Run without random order to verify it's order-dependent
pytest tests/unit/ -v -p no:randomly
```

**3. Bisect to Find Problematic Test Pair**

```bash
# Run failing test with different subsets
pytest tests/unit/test_file_a.py tests/unit/test_file_b.py -v --randomly-seed=42

# Try different combinations
pytest tests/unit/test_file_a.py tests/unit/test_file_c.py -v --randomly-seed=42
pytest tests/unit/test_file_b.py tests/unit/test_file_c.py -v --randomly-seed=42

# Identify which pair causes failure
```

#### Debugging Order Dependencies

**1. Add Fixture Debugging**

```python
# Add to conftest.py
@pytest.fixture(scope="module", autouse=True)
def debug_test_order():
    """Debug fixture to track test execution order"""
    import pytest
    test_file = pytest.current_test_module
    print(f"\n[ORDER] Starting test file: {test_file}")
    yield
    print(f"[ORDER] Finished test file: {test_file}")
```

**2. Check for Shared State**

```python
# Add debug output to check for pollution
def test_something():
    import lambda.handler.index as index
    
    # Check for polluted state
    if index.target_accounts_table is not None:
        print(f"WARNING: table already set to {index.target_accounts_table}")
    
    # Test code
```

**3. Verify Cleanup Fixtures**

```bash
# Run with fixture debugging
pytest tests/unit/ -v --setup-show --randomly-seed=42

# Look for:
# - Fixtures that don't run
# - Fixtures that run in wrong order
# - Missing cleanup fixtures
```

### Quick Debugging Checklist

When encountering test isolation issues, follow this checklist:

- [ ] **Run test individually**: `pytest tests/unit/test_file.py::test_name -v`
- [ ] **Run test with full suite**: `pytest tests/unit/ -v`
- [ ] **Compare results**: Do they differ?
- [ ] **Check for mock pollution**: Add debug output to see mock state
- [ ] **Check for sys.path pollution**: Print sys.path before/after test
- [ ] **Check for environment pollution**: Print os.environ before/after test
- [ ] **Run with random order**: `pytest tests/unit/ -v --randomly-seed=12345`
- [ ] **Run multiple times**: `pytest tests/unit/test_file.py -v --count=10`
- [ ] **Enable debug logging**: `pytest tests/unit/ -v -s --log-cli-level=DEBUG`
- [ ] **Check fixture execution**: `pytest tests/unit/ -v --setup-show`
- [ ] **Verify cleanup fixtures**: Ensure module-scoped fixtures run
- [ ] **Add debug fixtures**: Add temporary debug output to conftest.py
- [ ] **Bisect test order**: Find which test pair causes failure

### Common Debugging Commands

```bash
# Run single test with full debug output
pytest tests/unit/test_file.py::test_name -v -s --log-cli-level=DEBUG --setup-show

# Run tests in random order with seed
pytest tests/unit/ -v --randomly-seed=12345

# Run tests multiple times to check for flakiness
pytest tests/unit/test_file.py -v --count=10

# Run tests in parallel to check for shared state
pytest tests/unit/ -v -n auto

# Run with coverage to see what code is executed
pytest tests/unit/ -v --cov=lambda --cov-report=term-missing

# Run with fixture debugging
pytest tests/unit/ -v --setup-show

# Save output to file for analysis
pytest tests/unit/ -v -s --log-cli-level=DEBUG > debug.log 2>&1
```

---

## Version History

- **v1.0** (2025-02-01): Initial documentation of test patterns and fixes
  - Documented mock pattern changes (target_accounts_table → get_target_accounts_table())
  - Documented syntax fixes (return_value, → return_value=)
  - Added DynamoDB and AWS client mocking patterns
  - Added property-based testing guidelines
  - Documented remaining test failures

- **v1.1** (2025-02-02): Added comprehensive debugging guide
  - Added techniques for identifying mock pollution
  - Added techniques for identifying sys.path pollution
  - Added techniques for identifying environment variable pollution
  - Added debug logging patterns for fixtures
  - Added guidance for testing individual files vs full suite
  - Added pytest-randomly usage for finding order dependencies
  - Added quick debugging checklist and common commands


- **v1.2** (2025-02-18): Added pytest-asyncio configuration documentation
  - Documented asyncio_default_fixture_loop_scope configuration
  - Explained how it prevents event loop sharing between tests
  - Added configuration location and deprecation warning elimination

---

## pytest-asyncio Configuration

### Overview

The project uses pytest-asyncio for testing asynchronous code. To ensure proper test isolation and prevent event loop sharing between tests, we configure the default fixture loop scope.

### Configuration

**Location**: `pyproject.toml` (line 52)

```toml
[tool.pytest.ini_options]
asyncio_default_fixture_loop_scope = "function"
```

### What This Does

The `asyncio_default_fixture_loop_scope = "function"` configuration:

1. **Sets the default event loop scope** for async fixtures to `function` level
2. **Creates a fresh event loop** for each test function
3. **Prevents event loop sharing** between tests
4. **Eliminates deprecation warnings** from pytest-asyncio

### Why It's Needed

**Without this configuration**:
- pytest-asyncio would use the default `session` scope for event loops
- Event loops would be shared across multiple test functions
- Tests could interfere with each other through shared event loop state
- Deprecation warnings would appear: `DeprecationWarning: The event_loop fixture provided by pytest-asyncio has been redefined`

**With this configuration**:
- Each test function gets its own isolated event loop
- Tests cannot interfere with each other through event loop state
- No deprecation warnings
- Consistent with our function-scoped isolation strategy

### How It Works

```python
# Example async test - automatically gets function-scoped event loop
async def test_async_operation():
    """Test with isolated event loop"""
    result = await some_async_function()
    assert result == expected_value
    # Event loop is cleaned up after this test

async def test_another_async_operation():
    """Test with fresh event loop"""
    result = await another_async_function()
    assert result == expected_value
    # Fresh event loop, no pollution from previous test
```

### Verification

To verify the configuration is working:

```bash
# Run async tests - should see no deprecation warnings
pytest tests/unit/ -v -W default

# Check for event loop isolation
pytest tests/unit/test_async_file.py -v -s
```

### Related Configuration

This configuration works together with our other isolation fixtures:

- **Function-scoped fixtures**: Reset state before each test
- **Module-scoped fixtures**: Clean up after each test file
- **Event loop isolation**: Prevents async state pollution

### Best Practices

1. **Always use function scope** for async fixtures unless you have a specific reason to share event loops
2. **Don't manually create event loops** in tests - let pytest-asyncio handle it
3. **Clean up async resources** properly using `async with` or `try/finally`
4. **Test async code in isolation** - don't rely on event loop state from previous tests

### Troubleshooting

**If you see deprecation warnings**:
```
DeprecationWarning: The event_loop fixture provided by pytest-asyncio has been redefined
```

**Solution**: Verify `asyncio_default_fixture_loop_scope = "function"` is set in `pyproject.toml`

**If async tests fail with event loop errors**:
```
RuntimeError: Event loop is closed
```

**Solution**: Ensure you're not manually closing event loops in tests - let pytest-asyncio manage them

### References

- pytest-asyncio documentation: https://pytest-asyncio.readthedocs.io/
- PEP 492 (Coroutines with async and await syntax): https://www.python.org/dev/peps/pep-0492/
- asyncio documentation: https://docs.python.org/3/library/asyncio.html
