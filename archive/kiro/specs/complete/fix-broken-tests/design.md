# Fix Broken Tests - Design

## Overview
This design outlines the systematic approach to fixing all 68 failing unit tests, organized by failure category and root cause.

## Failure Analysis

### Category 1: Query Handler AttributeError (8 errors)
**Files:** `test_query_handler_new_operations.py`

**Error:**
```
AttributeError: <module 'index'> does not have the attribute 'target_accounts_table'
```

**Root Cause:**
The test fixture `mock_target_accounts_table` is trying to patch `index.target_accounts_table`, but this attribute doesn't exist in the query handler's index.py module.

**Fix Strategy:**
1. Examine `lambda/query-handler/index.py` to find correct attribute name
2. Update mock path in test fixture
3. Verify all 8 tests using this fixture

### Category 2: Query Handler Server Config Tests (11 failures)
**Files:** `test_query_handler_get_server_config_history.py`

**Likely Causes:**
- API response format changes
- Missing mock setup
- Changed function signatures

**Fix Strategy:**
1. Review actual implementation in query handler
2. Update test expectations to match current API
3. Ensure mocks match actual DynamoDB structure

### Category 3: Query Handler Launch Config Tests (8 failures)
**Files:** `test_query_handler_get_server_launch_config.py`

**Likely Causes:**
- Similar to server config tests
- Launch configuration structure changes

**Fix Strategy:**
1. Verify current launch config implementation
2. Update test mocks and assertions
3. Ensure protection group structure is correct

### Category 4: Data Management Operations (7 failures)
**Files:** `test_data_management_new_operations.py`

**Likely Causes:**
- Direct invocation mode changes
- Tag sync implementation updates
- Target account operations modified

**Fix Strategy:**
1. Review data management handler implementation
2. Update test mocks for new operation signatures
3. Verify response format expectations

### Category 5: Combined Capacity Tests (5 failures)
**Files:** `test_handle_get_combined_capacity.py`

**Likely Causes:**
- Staging accounts handling changed
- Capacity aggregation logic updated

**Fix Strategy:**
1. Review combined capacity implementation
2. Update staging account mocks
3. Verify capacity calculation logic

### Category 6: Error Handling Tests (8 failures)
**Files:** 
- `test_error_handling_data_management_handler.py` (5)
- `test_error_handling_query_handler.py` (3)

**Likely Causes:**
- Error response format changes
- Authorization logic updates
- DRS API error handling modified

**Fix Strategy:**
1. Review current error handling patterns
2. Update error response expectations
3. Verify authorization flow

### Category 7: Property-Based Tests (10 failures)
**Files:**
- `test_empty_staging_accounts_default_property.py` (2)
- `test_query_handler_new_operations_property.py` (8)

**Likely Causes:**
- Property assumptions about defaults
- API contract changes

**Fix Strategy:**
1. Review property test assumptions
2. Update generators if needed
3. Verify properties still hold

### Category 8: Miscellaneous (2 failures)
**Files:**
- `test_data_management_response_format.py` (1)
- `test_iam_audit_logging_property.py` (1)

**Fix Strategy:**
1. Review specific test failures
2. Update expectations to match implementation

## Implementation Approach

### Phase 1: Diagnostic Analysis
For each failing test:
1. Run test individually to see full error
2. Examine actual Lambda handler code
3. Identify mismatch between test and implementation
4. Document required fix

### Phase 2: Fix by Category
Fix tests in order of dependency:
1. **AttributeError fixes first** (blocking 8 tests)
2. **Mock setup fixes** (query handler tests)
3. **API contract fixes** (data management tests)
4. **Logic fixes** (capacity and error handling)
5. **Property test fixes** (adjust assumptions)

### Phase 3: Verification
1. Run each fixed test individually
2. Run full test suite to check for isolation issues
3. Run in both fast and full modes
4. Verify deploy script Stage 3 passes

## Mock Patterns

### DynamoDB Table Mocking
```python
@pytest.fixture
def mock_dynamodb_table():
    with patch("lambda.query_handler.index.dynamodb") as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        yield mock_table
```

### Boto3 Client Mocking
```python
@pytest.fixture
def mock_drs_client():
    with patch("boto3.client") as mock_client:
        mock_drs = MagicMock()
        mock_client.return_value = mock_drs
        yield mock_drs
```

### Lambda Handler Mocking
```python
@pytest.fixture
def mock_handler_dependencies():
    with patch.multiple(
        "index",
        protection_groups_table=MagicMock(),
        target_accounts_table=MagicMock(),
        drs_client=MagicMock()
    ):
        yield
```

## Testing Strategy

### Fast Mode (Default)
- Skip property-based tests marked with `@pytest.mark.property`
- Run only unit tests with specific examples
- Faster feedback for development

### Full Mode (--full-tests or --validate-only)
- Run all tests including property-based tests
- Complete validation before deployment
- Slower but comprehensive

## Correctness Properties

### Property 1: Test Isolation
**Statement:** Each test must pass when run individually and as part of the suite

**Validation:** Run tests both ways and verify no failures

### Property 2: Mock Accuracy
**Statement:** All mocks must accurately reflect the actual Lambda handler structure

**Validation:** Compare mock paths with actual module attributes

### Property 3: API Contract Consistency
**Statement:** Test expectations must match actual API responses

**Validation:** Review handler code and update test assertions

## Risk Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation:** Only fix tests, don't modify Lambda handler code unless absolutely necessary

### Risk 2: Test Isolation Issues
**Mitigation:** Use proper fixtures and cleanup, avoid global state

### Risk 3: Incomplete Fixes
**Mitigation:** Run full test suite after each category of fixes

## Success Metrics

1. **Test Pass Rate:** 100% (682/682 tests passing)
2. **Deploy Script Success:** Stage 3 (Tests) completes without errors
3. **Execution Time:** Fast mode < 30s, Full mode < 2min
4. **No Regressions:** All previously passing tests still pass

## Implementation Notes

### Common Patterns to Fix

1. **AttributeError on mock paths:**
   - Find actual attribute name in Lambda handler
   - Update patch path in test

2. **Assertion failures on response format:**
   - Review actual handler response
   - Update test expectations

3. **Missing mock setup:**
   - Add required fixtures
   - Ensure proper mock return values

4. **Property test failures:**
   - Review property assumptions
   - Update generators or properties as needed

### Testing Checklist

For each fixed test:
- [ ] Test passes individually
- [ ] Test passes in suite
- [ ] Mock paths are correct
- [ ] Assertions match implementation
- [ ] No side effects on other tests
- [ ] Follows PEP 8 standards
