# Test Isolation Refactoring - Requirements

## Overview
Refactor 15 tests that use the `@mock_aws` decorator to use explicit mocking patterns, resolving test isolation issues that cause batch test failures.

## Problem Statement
After completing the fix-broken-tests spec, 15 tests in `test_data_management_new_operations.py` pass when run individually but fail when run as part of the full test suite. The root cause is that these tests use moto's `@mock_aws` decorator, which doesn't work properly when boto3 clients are cached from earlier tests in the batch run.

### Current Behavior
- **Individual test execution**: All 15 tests pass ✅
- **Batch test execution**: All 15 tests fail with `UnrecognizedClientException` ❌
- **Error pattern**: `botocore.exceptions.UnrecognizedClientException: Unknown service: 'dynamodb'`

### Root Cause
The `@mock_aws` decorator creates a mock AWS environment, but when tests run in batch mode, boto3 clients cached from previous tests (that used explicit mocking) conflict with the decorator's mock environment. The 661 passing tests use explicit mocking with `patch()`, which is more reliable and doesn't have this isolation issue.

## User Stories

### 1. Reliable Batch Test Execution
**As a** developer  
**I want** all tests to pass in both individual and batch execution modes  
**So that** I can trust the test suite results regardless of how tests are run

**Acceptance Criteria:**
- All 15 affected tests pass when run individually
- All 15 affected tests pass when run as part of the full test suite
- No `UnrecognizedClientException` errors occur
- Test execution is consistent and repeatable

### 2. Consistent Mocking Patterns
**As a** developer  
**I want** all tests to use the same explicit mocking pattern  
**So that** the codebase is maintainable and test isolation is guaranteed

**Acceptance Criteria:**
- All tests use explicit `patch()` mocking instead of `@mock_aws` decorator
- Mocking pattern matches the 661 passing tests
- Tests patch getter functions (e.g., `get_target_accounts_table()`) not module-level variables
- Mock DynamoDB tables are created using `MagicMock()`

### 3. Correct Patching Pattern
**As a** developer  
**I want** tests to patch the correct functions and paths  
**So that** mocks work reliably and match the actual Lambda handler implementation

**Acceptance Criteria:**
- Tests patch getter functions: `patch("data-management-handler.index.get_target_accounts_table", return_value=mock_table)`
- Tests do NOT patch non-existent module-level variables
- Patching pattern follows the reference implementation in `test_conflict_detection_comprehensive.py`
- All DynamoDB table getters are correctly patched

## Technical Requirements

### 4. Affected Tests
**Tests to refactor** (all in `test_data_management_new_operations.py`):

1. `test_create_target_account_success` (lines 485-520)
2. `test_create_target_account_duplicate` (lines 523-547)
3. `test_update_target_account_success` (lines 550-577)
4. `test_delete_target_account_success` (lines 580-599)
5. `test_trigger_tag_sync_success` (lines 704-738)
6. `test_sync_extended_source_servers_success` (lines 826-854)
7. `test_direct_invocation_add_target_account` (lines 987-1015)
8. `test_direct_invocation_trigger_tag_sync` (lines 1018-1062)
9. `test_create_target_account_missing_required_fields` (lines 1127-1149)
10. `test_delete_target_account_not_found` (lines 1172-1183)

### 5. Refactoring Pattern
**Requirements:**
- Remove `@mock_aws` decorator from each test
- Create mock DynamoDB tables using `MagicMock()`
- Patch getter functions with correct module path
- Use context managers (`with patch(...)`) for all patches
- Follow the pattern from `test_conflict_detection_comprehensive.py`

**Example transformation:**

❌ **BEFORE (using @mock_aws):**
```python
@mock_aws
def test_create_target_account_success():
    # Test uses @mock_aws decorator
    # Fails in batch mode
    pass
```

✅ **AFTER (using explicit mocking):**
```python
def test_create_target_account_success():
    # Create mock table
    mock_table = MagicMock()
    mock_table.put_item.return_value = {}
    
    # Patch getter function
    with patch("data-management-handler.index.get_target_accounts_table", return_value=mock_table):
        # Test logic
        pass
```

### 6. Getter Functions to Patch
**Lambda handler getter functions** (from `lambda/data-management-handler/index.py` lines 242-280):
- `get_protection_groups_table()`
- `get_recovery_plans_table()`
- `get_executions_table()`
- `get_target_accounts_table()`
- `get_tag_sync_config_table()`

**Correct patch paths:**
- `"data-management-handler.index.get_protection_groups_table"`
- `"data-management-handler.index.get_recovery_plans_table"`
- `"data-management-handler.index.get_executions_table"`
- `"data-management-handler.index.get_target_accounts_table"`
- `"data-management-handler.index.get_tag_sync_config_table"`

### 7. Reference Implementation
**Use as template:** `tests/unit/test_conflict_detection_comprehensive.py`

This file demonstrates the correct explicit mocking pattern:
```python
with patch("conflict_detection.get_protection_groups_table", return_value=pg_table):
    with patch("conflict_detection.get_recovery_plans_table", return_value=rp_table):
        # Test logic
        pass
```

## Constraints

1. **No Functional Changes**: Refactoring must not change test behavior or expectations
2. **Maintain Test Coverage**: All test scenarios must remain covered
3. **Follow PEP 8**: All Python code must follow coding standards
4. **Preserve Test Intent**: Only change mocking approach, not test logic

## Success Criteria

1. ✅ All 15 refactored tests pass when run individually
2. ✅ All 15 refactored tests pass when run as part of the full test suite
3. ✅ No `UnrecognizedClientException` errors occur
4. ✅ Full test suite passes: `pytest tests/unit/ -v` shows 0 failures
5. ✅ Deploy script Stage 3 (Tests) completes successfully
6. ✅ All tests use consistent explicit mocking pattern

## Out of Scope

- Adding new test coverage (only refactoring existing tests)
- Refactoring tests that already use explicit mocking (661 tests already work)
- Performance optimization of tests
- Integration or E2E tests (only unit tests)

## Dependencies

- Python 3.12
- pytest with hypothesis plugin
- Virtual environment (.venv) with all dependencies
- Lambda handler code in `/lambda/data-management-handler/index.py`
- Reference implementation in `tests/unit/test_conflict_detection_comprehensive.py`

## References

- Failing tests: `tests/unit/test_data_management_new_operations.py`
- Lambda handler: `lambda/data-management-handler/index.py` (lines 242-280 for getter functions)
- Reference pattern: `tests/unit/test_conflict_detection_comprehensive.py`
- Deploy script: `scripts/deploy.sh`
- Previous spec: `.kiro/specs/fix-broken-tests/` (completed, all 17 tasks done)

## Related Issues

This spec addresses the remaining test isolation issues discovered after completing the fix-broken-tests spec. The original spec successfully fixed 68 failing tests, but these 15 tests require a different approach due to their use of the `@mock_aws` decorator.
