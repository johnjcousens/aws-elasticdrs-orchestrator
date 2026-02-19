# Requirements Document: DynamoDB Mock Structure Fix

## Spec Status: ❌ CANCELLED - Wrong Root Cause

**Cancellation Date**: February 18, 2025

**Reason for Cancellation**: Investigation revealed the 3 test failures are NOT DynamoDB mock structure issues. They are cross-file test isolation issues in `test_error_handling_query_handler.py`.

**Evidence**:
- All tests in `test_launch_config_service_unit.py` pass: 59 passed, 5 skipped, 0 failures
- The 3 failures are in `test_error_handling_query_handler.py`:
  - `test_retryable_errors_include_retry_guidance`
  - `test_dynamodb_resource_not_found`
  - `test_dynamodb_throttling_error`
- These tests PASS when run individually or in their own file
- These tests FAIL only when run as part of the full test suite
- This is the definition of cross-file test isolation failure

**Correct Action**: These 3 failures should be addressed in the cross-file-test-isolation-fix spec, not a new DynamoDB mock structure spec.

**Work Completed**:
1. Fixed pytest-asyncio deprecation warning in pyproject.toml
2. Verified all tests in test_launch_config_service_unit.py pass
3. Identified the real root cause (cross-file isolation, not mock structure)

---

## Introduction

The test suite has 10 failing tests in `test_launch_config_service_unit.py` that fail due to incorrect DynamoDB Table mock structure. These tests attempt to mock DynamoDB operations but the mock structure doesn't properly simulate how boto3's DynamoDB Table resource works.

**Current Test Results**: 1,053 passed, 12 skipped, 10 failures

**Failing Test Classes**:
1. `TestEnvironmentVariableHandling` - 1 failure (missing PROTECTION_GROUPS_TABLE env var)
2. `TestGetConfigStatus` - 5 failures (DynamoDB query mock structure issues)
3. `TestPersistConfigStatus` - 4 failures (DynamoDB update mock structure issues)

**Root Cause**: The tests mock `_get_protection_groups_table()` to return a MagicMock, but don't properly configure the mock to simulate boto3 Table behavior:
- `get_item()` should return `{"Item": {...}}` format
- `update_item()` should accept specific parameters
- Environment variable `PROTECTION_GROUPS_TABLE` must be set

## Glossary

- **DynamoDB_Table**: boto3 resource representing a DynamoDB table with methods like `get_item()`, `put_item()`, `update_item()`
- **Mock_Structure**: The configuration of a MagicMock object to simulate real API behavior
- **Response_Format**: The dictionary structure returned by DynamoDB operations (e.g., `{"Item": {...}}`)
- **Table_Resource**: boto3 DynamoDB Table resource accessed via `dynamodb.Table(table_name)`
- **Environment_Variable**: OS environment variable like `PROTECTION_GROUPS_TABLE` that specifies table name

## Requirements

### Requirement 1: Fix TestEnvironmentVariableHandling Failures

**User Story:** As a developer, I want the environment variable handling tests to pass, so that I can verify the code properly validates required environment variables.

#### Acceptance Criteria

1. WHEN running `test_missing_table_name_env_var_raises_error`, THE Test SHALL pass by properly setting up the environment and mock structure
2. WHEN the test checks for missing `PROTECTION_GROUPS_TABLE` env var, THE Code SHALL raise `LaunchConfigApplicationError` with appropriate message
3. WHEN the test mocks `_get_dynamodb_resource`, THE Mock SHALL be configured to simulate boto3 DynamoDB resource behavior
4. THE Test SHALL verify that missing environment variable is detected before attempting to create table resource
5. THE Test SHALL reset module-level `_protection_groups_table` variable to None before execution

**Failing Test**:
- `test_missing_table_name_env_var_raises_error`

### Requirement 2: Fix TestGetConfigStatus Failures

**User Story:** As a developer, I want the get_config_status tests to pass, so that I can verify configuration status retrieval works correctly.

#### Acceptance Criteria

1. WHEN mocking DynamoDB Table, THE Mock SHALL return responses in correct boto3 format: `{"Item": {...}}`
2. WHEN `get_item()` is called, THE Mock SHALL return dictionary with "Item" key containing the DynamoDB item
3. WHEN item doesn't exist, THE Mock SHALL return empty dictionary `{}`
4. WHEN item exists without `launchConfigStatus` field, THE Mock SHALL return item with only basic fields
5. WHEN DynamoDB ClientError occurs, THE Mock SHALL raise proper boto3 ClientError exception
6. THE Mock SHALL properly simulate `Table.get_item(Key={"groupId": "..."})` call signature
7. ALL 5 failing tests in TestGetConfigStatus SHALL pass

**Failing Tests**:
- `test_get_existing_status_returns_status`
- `test_get_status_without_launch_config_returns_default`
- `test_get_status_group_not_found_raises_error`
- `test_get_status_dynamodb_client_error_raises_application_error`
- `test_get_status_with_server_configs`

### Requirement 3: Fix TestPersistConfigStatus Failures

**User Story:** As a developer, I want the persist_config_status tests to pass, so that I can verify configuration status persistence works correctly.

#### Acceptance Criteria

1. WHEN mocking DynamoDB Table, THE Mock SHALL accept `update_item()` calls with proper parameters
2. WHEN `update_item()` is called, THE Mock SHALL accept parameters: `Key`, `UpdateExpression`, `ExpressionAttributeValues`
3. WHEN DynamoDB ClientError occurs, THE Mock SHALL raise proper boto3 ClientError exception
4. THE Mock SHALL properly simulate `Table.update_item(Key=..., UpdateExpression=..., ExpressionAttributeValues=...)` call signature
5. ALL 4 failing tests in TestPersistConfigStatus SHALL pass

**Failing Tests**:
- `test_persist_valid_status_succeeds`
- `test_persist_with_server_configs`
- `test_persist_with_errors`
- `test_persist_dynamodb_client_error_raises_application_error`

### Requirement 4: Ensure Proper Mock Structure Pattern

**User Story:** As a developer, I want a reusable pattern for mocking DynamoDB Table resources, so that future tests can use the same correct structure.

#### Acceptance Criteria

1. WHEN creating a DynamoDB Table mock, THE Pattern SHALL configure `get_item()` to return `{"Item": {...}}` format
2. WHEN creating a DynamoDB Table mock, THE Pattern SHALL configure `update_item()` to accept standard parameters
3. WHEN creating a DynamoDB Table mock, THE Pattern SHALL configure `put_item()` to accept standard parameters
4. THE Pattern SHALL be documented in test file comments for future reference
5. THE Pattern SHALL handle both success and error cases (ClientError exceptions)

### Requirement 5: Verify All Tests Pass

**User Story:** As a developer, I want all tests in test_launch_config_service_unit.py to pass, so that I have confidence in the launch config service implementation.

#### Acceptance Criteria

1. WHEN running `pytest tests/unit/test_launch_config_service_unit.py -v`, THE Test Suite SHALL show 0 failures
2. WHEN running the full test suite, THE Total Pass Count SHALL be 1,063 (1,053 + 10 fixed)
3. WHEN running tests multiple times, THE Results SHALL be consistent
4. THE Test Suite SHALL maintain 12 skipped tests (5 tests with wrong mocks that need complete rewrite)
5. THE Overall Test Suite SHALL achieve >99% pass rate

## Success Criteria

- All 10 failing tests in `test_launch_config_service_unit.py` pass
- Test suite shows: 1,063 passed, 12 skipped, 0 failures
- DynamoDB mock structure properly simulates boto3 Table behavior
- Pattern is documented for future test development
- No regression in other passing tests

## Out of Scope

- Rewriting the 5 skipped tests that mock wrong methods (separate work)
- Modifying the actual launch_config_service implementation code
- Adding new test cases beyond fixing existing failures
- Performance optimization of test execution
- Refactoring test structure or organization

## Related Documentation

- Cross-file test isolation spec: `.kiro/specs/cross-file-test-isolation-fix/`
- Test patterns documentation: `docs/TEST_PATTERNS.md`
- Launch config service implementation: `lambda/shared/launch_config_service.py`
