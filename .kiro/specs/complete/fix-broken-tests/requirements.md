# Fix Broken Tests - Requirements

## Overview
Fix all 68 failing tests in the `/tests/unit` directory that are preventing successful deployment via `deploy.sh`.

## Problem Statement
The deploy script runs pytest tests as part of Stage 3 (Tests), and currently 68 tests are failing. These failures block deployment and need to be resolved.

## User Stories

### 1. Test Execution Success
**As a** developer  
**I want** all unit tests to pass  
**So that** I can deploy code changes without test failures blocking the pipeline

**Acceptance Criteria:**
- All tests in `tests/unit/` pass when run via pytest
- Tests pass both individually and when run as a suite
- No test isolation issues remain
- Deploy script Stage 3 (Tests) completes successfully

### 2. Test Categories Fixed

#### 2.1 Query Handler Tests (27 failures)
**Tests affected:**
- `test_query_handler_get_server_config_history.py` (11 failures)
- `test_query_handler_get_server_launch_config.py` (8 failures)
- `test_query_handler_new_operations.py` (8 errors - AttributeError: 'target_accounts_table')
- `test_query_handler_new_operations_property.py` (8 failures)
- `test_error_handling_query_handler.py` (3 failures)

**Root cause:** Missing or incorrectly mocked attributes in query handler

#### 2.2 Data Management Tests (13 failures)
**Tests affected:**
- `test_data_management_new_operations.py` (7 failures)
- `test_error_handling_data_management_handler.py` (5 failures)
- `test_data_management_response_format.py` (1 failure)

**Root cause:** API changes or missing mocks in data management handler

#### 2.3 Combined Capacity Tests (5 failures)
**Tests affected:**
- `test_handle_get_combined_capacity.py` (5 failures)

**Root cause:** Staging accounts handling logic changes

#### 2.4 Property-Based Tests (2 failures)
**Tests affected:**
- `test_empty_staging_accounts_default_property.py` (2 failures)

**Root cause:** Property test assumptions about default values

#### 2.5 IAM Audit Logging (1 failure)
**Tests affected:**
- `test_iam_audit_logging_property.py` (1 failure)

**Root cause:** Audit log field requirements changed

## Technical Requirements

### 3. Test Infrastructure
**Requirements:**
- Tests must use proper mocking for AWS services
- Tests must not depend on external resources
- Tests must be isolated and repeatable
- Tests must run in both fast mode (skip property tests) and full mode

### 4. Mock Patterns
**Requirements:**
- Use `@patch` decorators for external dependencies
- Mock DynamoDB tables correctly
- Mock boto3 clients appropriately
- Ensure mocks match actual Lambda handler structure

### 5. Test Execution Modes
**Requirements:**
- Fast mode: `pytest tests/unit/ -m "not property"` (default in deploy.sh)
- Full mode: `pytest tests/unit/` (with --full-tests or --validate-only)
- Both modes must pass all applicable tests

## Constraints

1. **No Breaking Changes**: Fixes must not break existing functionality
2. **Maintain Test Coverage**: All test scenarios must remain covered
3. **Follow PEP 8**: All Python code must follow coding standards
4. **Preserve Test Intent**: Fix implementation, not test expectations (unless tests are wrong)

## Success Criteria

1. ✅ All 682 tests pass when run via pytest
2. ✅ Deploy script Stage 3 (Tests) completes without failures
3. ✅ Tests pass in both fast mode and full mode
4. ✅ No test isolation issues (tests pass individually and as suite)
5. ✅ All mocks correctly reflect Lambda handler structure

## Out of Scope

- Adding new test coverage (only fixing existing tests)
- Refactoring test structure (maintain current organization)
- Performance optimization of tests
- Integration or E2E tests (only unit tests)

## Dependencies

- Python 3.12
- pytest with hypothesis plugin
- Virtual environment (.venv) with all dependencies
- Lambda handler code in `/lambda` directory

## References

- Deploy script: `scripts/deploy.sh`
- Test directory: `tests/unit/`
- Lambda handlers: `lambda/*/index.py`
- Test configuration: `pyproject.toml`
