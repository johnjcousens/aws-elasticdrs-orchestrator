# Test Fixes Summary

**Date**: February 2, 2026  
**Status**: In Progress  
**Tests Passing**: 232 / 259 (89.6%)  
**Tests Failing**: 27 / 259 (10.4%)

## Problem

After implementing per-region quota tracking in `lambda/query-handler/index.py`, 29 tests were failing with the error:
```
NoCredentialsError: Unable to locate credentials
```

The root cause was that `index.py` creates boto3 DynamoDB resources at module import time (lines ~300-310), which happens BEFORE the `@mock_aws` decorator is active in tests.

## Solution

The fix requires a specific pattern for tests that use `handle_get_combined_capacity` and other functions that access DynamoDB:

### Pattern: Reload Module Inside @mock_aws Context

```python
from moto import mock_aws

@mock_aws
@settings(max_examples=100, deadline=2000)
@given(...)
def test_function(...):
    # Import boto3 INSIDE the test
    import boto3
    
    # Clear and reload index module to use mocked AWS
    if "index" in sys.modules:
        del sys.modules["index"]
    import index
    from index import handle_get_combined_capacity
    
    # Create mock DynamoDB table using moto
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    
    # Delete existing table if it exists (avoid ResourceInUseException)
    try:
        existing_table = dynamodb.Table("test-target-accounts-table")
        existing_table.delete()
        existing_table.wait_until_not_exists()
    except:
        pass
    
    # Create fresh table
    table = dynamodb.create_table(
        TableName="test-target-accounts-table",
        KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "accountId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    
    # Put test data
    table.put_item(Item=target_account)
    
    # Patch the module's table reference
    with patch.object(index, "target_accounts_table", table), \
         patch.object(index, "query_all_accounts_parallel", mock_function):
        # Call the function
        result = handle_get_combined_capacity(...)
```

### Key Points

1. **Import boto3 inside test**: Ensures moto mocking is active
2. **Reload index module**: Forces module to use mocked boto3
3. **Delete existing tables**: Prevents ResourceInUseException on reruns
4. **Use patch.object**: Patches the module's table reference, not the global

## Changes Made

### 1. conftest.py
Added environment variables to `aws_credentials` fixture:
```python
monkeypatch.setenv("TARGET_ACCOUNTS_TABLE", "test-target-accounts-table")
monkeypatch.setenv("STAGING_ACCOUNTS_TABLE", "test-staging-accounts-table")
monkeypatch.setenv("PROTECTION_GROUPS_TABLE", "test-protection-groups-table")
monkeypatch.setenv("RECOVERY_PLANS_TABLE", "test-recovery-plans-table")
```

### 2. Test Files Updated

Added `@mock_aws` decorator and module reload pattern to:
- ✅ `test_account_breakdown_completeness_property.py` (FIXED - 1 test passing)
- ⚠️ `test_empty_staging_accounts_default_property.py` (2 tests failing)
- ⚠️ `test_failed_account_resilience_property.py` (5 tests failing)
- ⚠️ `test_handle_get_combined_capacity.py` (5 tests failing)
- ⚠️ `test_multi_account_query_parallelism_property.py` (6 tests failing)
- ⚠️ `test_query_handler_role_arn.py` (6 tests failing)
- ⚠️ `test_uninitialized_region_handling_property.py` (3 tests failing)

## Test Results

### Before Fix
```
200 tests passing
29 tests failing
```

### After Fix
```
232 tests passing (+32)
27 tests failing (-2)
```

### Fixed Tests
1. `test_property_12_account_breakdown_completeness` ✅

### Remaining Failures (27 tests)

All have the same root cause - need module reload pattern applied:

**test_empty_staging_accounts_default_property.py** (2 failures):
- test_property_13_empty_staging_accounts_default
- test_property_13_missing_staging_accounts_attribute

**test_failed_account_resilience_property.py** (5 failures):
- test_property_failed_account_resilience
- test_property_partial_failure_continues_query
- test_property_all_staging_accounts_fail_target_succeeds
- test_edge_case_target_fails_all_staging_succeed
- test_edge_case_different_error_types

**test_handle_get_combined_capacity.py** (5 failures):
- test_combined_capacity_no_staging_accounts
- test_combined_capacity_multiple_staging_accounts
- test_combined_capacity_one_staging_account_inaccessible
- test_combined_capacity_all_staging_accounts_inaccessible
- test_combined_capacity_target_account_not_found

**test_multi_account_query_parallelism_property.py** (6 failures):
- test_property_multi_account_query_parallelism
- test_property_concurrent_region_queries_per_account
- test_property_parallel_execution_not_sequential
- test_edge_case_no_staging_accounts
- test_edge_case_many_staging_accounts
- test_edge_case_query_failure_continues

**test_query_handler_role_arn.py** (6 failures):
- test_combined_capacity_constructs_arn_when_not_in_db
- test_combined_capacity_uses_explicit_arn_from_db
- test_capacity_query_with_explicit_role_arn
- test_capacity_query_with_constructed_role_arn
- test_capacity_query_missing_account
- test_capacity_query_drs_api_mocked

**test_uninitialized_region_handling_property.py** (3 failures):
- test_property_uninitialized_region_handling
- test_property_mixed_region_initialization
- test_edge_case_alternating_initialization

## Next Steps

1. Apply the module reload pattern to the remaining 27 failing tests
2. Each test file needs:
   - Import boto3 inside test function
   - Reload index module inside @mock_aws context
   - Create moto DynamoDB tables
   - Use patch.object instead of patch for module references

3. Run full test suite to verify all tests pass

## Verification

Run tests:
```bash
source .venv/bin/activate
python -m pytest tests/unit/ -v
```

Check specific test:
```bash
python -m pytest tests/unit/test_account_breakdown_completeness_property.py -v
```

## Related Files

- `lambda/query-handler/index.py` - Module that creates boto3 resources at import time
- `tests/conftest.py` - Test configuration with environment variables
- `docs/analysis/PER_REGION_QUOTA_FIX.md` - Backend changes that triggered test failures

## Lessons Learned

1. **Module-level boto3 initialization is problematic for testing** - Consider lazy initialization
2. **@mock_aws must be active before module import** - Reload pattern is necessary
3. **Environment variables must be set before module import** - conftest.py handles this
4. **Moto tables persist between test runs** - Always delete before creating

## Commit

```
fix(tests): Fix test environment setup and module loading

Fixed test failures by properly configuring test environment and
implementing module reload pattern for @mock_aws compatibility.

Test results: 232 passing (+32), 27 failing (-2)
```


## Deploy Script Test Detection Fix (2024-02-11)

### Issue
Deploy script incorrectly handled test failures, allowing broken code to deploy. The script checked for both "passed" and "failed" strings in output, assumed "test isolation issues", and continued deployment despite failures.

### Root Cause
1. Script used string parsing instead of pytest exit code
2. Script assumed test failures were "cross-file isolation issues"
3. No actual test isolation fixtures existed to prevent state leakage
4. Tests were genuinely failing due to global state leakage

### Solution
1. **Deploy Script Fix**: Updated test detection to use pytest exit code instead of string parsing
2. **Test Isolation**: Added 5 autouse fixtures to reset global state between tests
3. **Test Fixes**: Updated 5 failing tests to use appropriate isolation fixtures

### Files Changed
- `scripts/deploy.sh` (lines 636-663): Fixed test detection in 3 locations
- `tests/unit/conftest.py`: Added 5 autouse fixtures
- `tests/unit/test_data_management_response_format.py`: Added reset_environment_variables fixture
- `tests/unit/test_error_handling_query_handler.py`: Added reset_module_caches fixture to 3 tests
- `tests/unit/test_iam_audit_logging_property.py`: Added reset_logger_state and reset_environment_variables fixtures

### Result
- All tests now pass consistently in both individual and batch execution
- Deploy script properly detects and reports test failures
- No more false "test isolation issues" warnings
- Deployment blocked when tests actually fail

### Lessons Learned
1. Always use exit codes for command success/failure detection
2. Never parse command output strings for error detection
3. Test isolation is critical for reliable test suites
4. Autouse fixtures provide consistent test isolation
5. Global state in Lambda handlers requires careful management
