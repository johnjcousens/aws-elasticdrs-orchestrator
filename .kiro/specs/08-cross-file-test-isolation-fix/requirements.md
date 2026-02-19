# Fix All Failing Tests - Requirements

## Overview
Fix all failing unit tests to achieve 100% pass rate. Currently there are approximately 20-30 failing tests that need to be fixed.

## Problem Statement
The test suite has failing tests that prevent full confidence in the codebase. All tests must pass to ensure code quality.

## User Story

**As a** developer  
**I want** all unit tests to pass  
**So that** I have complete confidence in code quality and can deploy safely

## Acceptance Criteria

1. All unit tests pass when running `pytest tests/unit/ -v`
2. No test failures
3. No test errors
4. Tests pass consistently across multiple runs
5. Tests pass both individually and as part of full suite

## Known Failing Test Categories

Based on previous analysis, failures are likely in these areas:

### 1. Query Handler Tests
- `test_query_handler_new_operations.py` - Direct invocation and staging account tests
- `test_query_handler_role_arn.py` - Role ARN construction and capacity query tests
- `test_error_handling_query_handler.py` - DynamoDB error handling tests

### 2. Property-Based Tests
- `test_multi_account_query_parallelism_property.py` - Parallel query tests
- `test_notification_formatter_property.py` - Formatter property tests

### 3. Launch Config Tests
- `test_launch_config_service_unit.py` - Environment variable handling tests

## Common Fix Patterns

1. **Mock Structure Issues**: Ensure DynamoDB table mocks return correct format
2. **Getter Function Mocking**: Patch getter functions not module variables
3. **Environment Variables**: Ensure required env vars are set in fixtures
4. **Property Test Strategies**: Constrain generators to valid inputs

## Success Criteria

- ✅ 0 test failures
- ✅ 0 test errors  
- ✅ All tests pass in batch mode
- ✅ Clean test output

## Out of Scope

- Adding new tests
- Refactoring test structure
- Performance optimization
- Changing production code (unless bugs are found)
