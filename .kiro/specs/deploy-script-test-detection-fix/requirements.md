# Deploy Script Test Detection Fix - Requirements

## Overview
Fix the deploy script to properly detect and fail on test failures, and resolve the remaining 5 test isolation issues that cause tests to pass individually but fail in batch execution.

## Problem Statement

### Issue 1: Deploy Script Bug - CONFIRMED
The deploy script (`scripts/deploy.sh`) has a critical bug in Stage 3 (Tests) at lines 620-660 where it incorrectly handles test failures. When pytest reports failures, the script checks if the output contains both "passed" and "failed" strings, and if so, assumes these are test isolation issues and continues deployment anyway.

**Current Behavior (WRONG) - Lines 643-649:**
```bash
if ! $PYTEST_CMD tests/unit/ -q --tb=no 2>&1 | tee /tmp/pytest_output.txt; then
    # Check if failures are only test isolation issues
    if grep -q "passed" /tmp/pytest_output.txt && grep -q "failed" /tmp/pytest_output.txt; then
        echo -e "${YELLOW}  ⚠ Some tests failed (may be test isolation issues)${NC}"
        echo -e "${YELLOW}  Continuing deployment (tests pass individually)${NC}"
    else
        TEST_FAILED=true
    fi
fi
```

**Root Cause Analysis:**
The script uses `if ! $PYTEST_CMD` which captures the exit code, but then IGNORES it and instead checks for string patterns in the output. This logic is fundamentally flawed because:
1. The `if !` condition catches the non-zero exit code from pytest
2. But then the nested `if grep -q` checks override this by looking for "passed" AND "failed" strings
3. If both strings exist (which is common when some tests pass and some fail), it assumes "test isolation issues" and continues
4. This means ANY test failure that has at least one passing test will be ignored

**Impact:**
- ❌ Deployment continues even when tests fail
- ❌ No indication that tests actually failed
- ❌ False sense of security that everything is working
- ❌ Broken code gets deployed to AWS

**Expected Behavior:**
- ✅ Deploy script should check pytest exit code directly
- ✅ Non-zero exit code = test failure = stop deployment immediately
- ✅ Clear error message indicating which tests failed
- ✅ Show failure count and test names

### Issue 2: Remaining Test Isolation Issues - TO BE INVESTIGATED
After completing the test-isolation-refactoring spec, 5 tests still fail when run as part of the full test suite but pass when run individually:

1. `test_data_management_response_format.py::TestDirectInvocationResponseFormat::test_create_protection_group_direct_format`
2. `test_error_handling_query_handler.py::TestDynamoDBErrors::test_dynamodb_throttling_error`
3. `test_error_handling_query_handler.py::TestDynamoDBErrors::test_dynamodb_resource_not_found`
4. `test_error_handling_query_handler.py::TestErrorResponseStructure::test_retryable_errors_include_retry_guidance`
5. `test_iam_audit_logging_property.py::test_audit_log_always_contains_required_fields`

**Test Directory Structure:**
- Total unit tests: 56 test files in `tests/unit/`
- Test discovery pattern: `test_*.py` or `*_test.py`
- Shared fixtures: `tests/unit/conftest.py`
- Property-based tests: Marked with `@pytest.mark.property`

**Hypothesis:**
These tests are likely affected by:
- Global state not being reset between tests
- Cached boto3 clients from previous tests
- Mock configurations leaking between tests
- Test execution order dependencies
- Environment variables not being reset
- Logger state persisting across tests

## User Stories

### 1. Reliable Deployment Gate
**As a** developer  
**I want** the deploy script to fail when tests fail  
**So that** broken code never gets deployed to AWS

**Acceptance Criteria:**
- Deploy script checks pytest exit code
- Non-zero exit code stops deployment immediately
- Clear error message shows which tests failed
- No false positives (passing tests don't trigger failure)

### 2. Consistent Test Execution
**As a** developer  
**I want** all tests to pass in both individual and batch execution modes  
**So that** I can trust the test suite results regardless of how tests are run

**Acceptance Criteria:**
- All 5 affected tests pass when run individually
- All 5 affected tests pass when run as part of the full test suite
- No test isolation issues remain
- Test execution is consistent and repeatable

### 3. Clear Test Failure Reporting
**As a** developer  
**I want** clear error messages when tests fail  
**So that** I can quickly identify and fix the issue

**Acceptance Criteria:**
- Deploy script shows which tests failed
- Deploy script shows test failure count
- Deploy script provides guidance on how to debug
- Test output is preserved for review

## Technical Requirements

### 4. Deploy Script Fix
**File:** `scripts/deploy.sh` (lines 620-670)

**Current problematic code (lines 643-649):**
```bash
if ! $PYTEST_CMD tests/unit/ -q --tb=no 2>&1 | tee /tmp/pytest_output.txt; then
    # Check if failures are only test isolation issues
    if grep -q "passed" /tmp/pytest_output.txt && grep -q "failed" /tmp/pytest_output.txt; then
        echo -e "${YELLOW}  ⚠ Some tests failed (may be test isolation issues)${NC}"
        echo -e "${YELLOW}  Continuing deployment (tests pass individually)${NC}"
    else
        TEST_FAILED=true
    fi
fi
```

**Also affects (lines 655-662):**
The same flawed logic is duplicated for the fast test mode:
```bash
if ! $PYTEST_CMD tests/unit/ -m "not property" -q --tb=no 2>&1 | tee /tmp/pytest_output.txt; then
    # Check if failures are only test isolation issues
    if grep -q "passed" /tmp/pytest_output.txt && grep -q "failed" /tmp/pytest_output.txt; then
        echo -e "${YELLOW}  ⚠ Some tests failed (may be test isolation issues)${NC}"
        echo -e "${YELLOW}  Continuing deployment (tests pass individually)${NC}"
    else
        TEST_FAILED=true
    fi
fi
```

**Required fix:**
Replace BOTH occurrences with proper exit code checking:

```bash
# For full test mode (lines 643-649)
set +e
$PYTEST_CMD tests/unit/ -v --tb=short 2>&1 | tee /tmp/pytest_output.txt
PYTEST_EXIT_CODE=$?
set -e

if [ $PYTEST_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}  ✗ Unit tests failed (exit code: $PYTEST_EXIT_CODE)${NC}"
    
    # Show failure summary
    FAILED_COUNT=$(grep -c "FAILED" /tmp/pytest_output.txt || echo "0")
    echo -e "${RED}  Failed tests: $FAILED_COUNT${NC}"
    
    # Show which tests failed
    echo -e "${YELLOW}  Failed test details:${NC}"
    grep "FAILED" /tmp/pytest_output.txt || true
    
    TEST_FAILED=true
else
    PASSED_COUNT=$(grep -c "PASSED" /tmp/pytest_output.txt || echo "0")
    echo -e "${GREEN}  ✓ Unit tests passed ($PASSED_COUNT tests)${NC}"
fi
```

```bash
# For fast test mode (lines 655-662)
set +e
$PYTEST_CMD tests/unit/ -m "not property" -v --tb=short 2>&1 | tee /tmp/pytest_output.txt
PYTEST_EXIT_CODE=$?
set -e

if [ $PYTEST_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}  ✗ Unit tests failed (exit code: $PYTEST_EXIT_CODE)${NC}"
    
    # Show failure summary
    FAILED_COUNT=$(grep -c "FAILED" /tmp/pytest_output.txt || echo "0")
    echo -e "${RED}  Failed tests: $FAILED_COUNT${NC}"
    
    # Show which tests failed
    echo -e "${YELLOW}  Failed test details:${NC}"
    grep "FAILED" /tmp/pytest_output.txt || true
    
    TEST_FAILED=true
else
    PASSED_COUNT=$(grep -c "PASSED" /tmp/pytest_output.txt || echo "0")
    echo -e "${GREEN}  ✓ Unit tests passed ($PASSED_COUNT tests)${NC}"
fi
```

**Key changes:**
- Capture pytest exit code explicitly with `set +e` / `set -e` wrapper
- Check exit code instead of output strings
- Show clear failure summary with count
- List which tests failed
- Remove the "test isolation issues" workaround completely
- Apply fix to BOTH test modes (full and fast)

### 5. Test Isolation Fixes

**Affected test files:**
1. `tests/unit/test_data_management_response_format.py`
2. `tests/unit/test_error_handling_query_handler.py`
3. `tests/unit/test_iam_audit_logging_property.py`

**Investigation steps:**
1. Run each test individually to confirm it passes
2. Run full test suite to confirm it fails
3. Identify which tests run before the failing test
4. Check for global state that isn't being reset
5. Add appropriate fixtures to reset state

**Common patterns to check:**
- Global variables in Lambda handler modules
- Cached boto3 clients
- Mock configurations not being cleaned up
- Environment variables not being reset
- Logger state not being reset

### 6. Fixture Enhancement
**File:** `tests/unit/conftest.py`

May need to add additional fixtures:
- Reset environment variables
- Reset logger state
- Reset any module-level caches
- Clear mock call history

**Example fixture:**
```python
@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
```

## Constraints

1. **No Functional Changes**: Fixes must not change test behavior or expectations
2. **Maintain Test Coverage**: All test scenarios must remain covered
3. **Follow PEP 8**: All Python code must follow coding standards
4. **Preserve Deploy Script Functionality**: Only fix test detection, don't break other features

## Success Criteria

1. ✅ Deploy script properly detects test failures (checks exit code)
2. ✅ Deploy script stops deployment when tests fail
3. ✅ Deploy script shows clear error messages with test names
4. ✅ All 5 affected tests pass when run individually
5. ✅ All 5 affected tests pass when run as part of the full test suite
6. ✅ Full test suite passes: `pytest tests/unit/ -v` shows 0 failures
7. ✅ Deploy script Stage 3 (Tests) completes successfully with passing tests
8. ✅ Deploy script Stage 3 (Tests) fails correctly with failing tests

## Out of Scope

- Adding new test coverage (only fixing existing tests)
- Refactoring tests that already work correctly
- Performance optimization of tests
- Integration or E2E tests (only unit tests)
- Changing deploy script behavior beyond test detection

## Dependencies

- Python 3.12
- pytest with hypothesis plugin
- Virtual environment (.venv) with all dependencies
- Deploy script: `scripts/deploy.sh`
- Test files in `tests/unit/`
- Shared fixtures in `tests/unit/conftest.py`

## References

- Deploy script: `scripts/deploy.sh` (lines 620-660)
- Failing tests:
  - `tests/unit/test_data_management_response_format.py`
  - `tests/unit/test_error_handling_query_handler.py`
  - `tests/unit/test_iam_audit_logging_property.py`
- Shared fixtures: `tests/unit/conftest.py`
- Previous spec: `.kiro/specs/test-isolation-refactoring/` (completed)

## Related Issues

This spec addresses:
1. Critical bug in deploy script that allows broken code to be deployed
2. Remaining test isolation issues discovered during deployment
3. Need for better test failure reporting and debugging

## Testing Strategy

### Deploy Script Testing
1. Create a test that intentionally fails
2. Run deploy script and verify it stops deployment
3. Verify error message shows the failing test
4. Fix the test and verify deployment continues

### Test Isolation Testing
1. Run each affected test individually: `pytest tests/unit/test_file.py::test_name -v`
2. Run full test suite: `pytest tests/unit/ -v`
3. Compare results and identify differences
4. Add debugging output to identify state leakage
5. Implement fixes and verify both modes pass

## Risk Assessment

**High Risk:**
- Deploy script changes could break deployment pipeline
- Test fixes could introduce new failures

**Mitigation:**
- Test deploy script changes thoroughly before committing
- Run full test suite after each fix
- Keep changes minimal and focused
- Document all changes clearly

**Low Risk:**
- Test isolation fixes are localized to specific test files
- Deploy script fix is straightforward (check exit code)
