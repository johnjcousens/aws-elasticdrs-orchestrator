# Tasks Document: DynamoDB Mock Structure Fix

## Task Status Legend
- [ ] Not started
- [~] In progress
- [x] Complete
- [N/A] Not applicable

---

## SPEC COMPLETION SUMMARY

**Status**: ✅ COMPLETE (No work needed)

**Discovery**: All tests in `test_launch_config_service_unit.py` are already passing:
- 59 passed, 5 skipped, 0 failures
- The 10 "failures" mentioned in the cross-file-test-isolation-fix spec were from an earlier test run
- Current state shows no DynamoDB mock structure issues

**Work Completed**:
1. Created comprehensive requirements.md documenting expected failures
2. Created detailed design.md with correct mock patterns
3. Created tasks.md with implementation plan
4. Verified all tests pass (59 passed, 5 skipped, 0 failures)
5. Fixed pytest-asyncio deprecation warning in pyproject.toml

**Conclusion**: This spec was created based on outdated test results. All tests are currently passing and no fixes are needed.

---

## Task 1: Fix TestEnvironmentVariableHandling (1 test)

**Status**: [N/A] - Test already passes

**Description**: Fix the single failing test in TestEnvironmentVariableHandling class that checks for missing PROTECTION_GROUPS_TABLE environment variable.

**Failing Test**:
- `test_missing_table_name_env_var_raises_error`

**Implementation Steps**:

1.1. [ ] Read the current test implementation to understand the failure
   - File: `tests/unit/test_launch_config_service_unit.py`
   - Class: `TestEnvironmentVariableHandling`
   - Method: `test_missing_table_name_env_var_raises_error`

1.2. [ ] Update test to properly clear environment variables
   - Use `@patch.dict(os.environ, {}, clear=True)` decorator
   - Ensure PROTECTION_GROUPS_TABLE is not set

1.3. [ ] Add module state reset before test execution
   - Import `shared.launch_config_service as service`
   - Set `service._protection_groups_table = None`
   - Set `service._dynamodb = None` if needed

1.4. [ ] Configure mock for `_get_dynamodb_resource`
   - Mock should return a MagicMock representing DynamoDB resource
   - Mock doesn't need specific configuration for this test

1.5. [ ] Verify test expects correct exception
   - Should raise `LaunchConfigApplicationError`
   - Error message should mention "PROTECTION_GROUPS_TABLE environment variable not set"

1.6. [ ] Run test to verify fix
   ```bash
   pytest tests/unit/test_launch_config_service_unit.py::TestEnvironmentVariableHandling::test_missing_table_name_env_var_raises_error -v
   ```

**Expected Result**: 1 passed, 0 failures

**Acceptance Criteria**:
- Test passes consistently
- Error message is correct
- Module state is properly reset

---

## Task 2: Fix TestGetConfigStatus (5 tests)

**Status**: [ ]

**Description**: Fix all 5 failing tests in TestGetConfigStatus class by correcting DynamoDB Table mock structure to return proper boto3 response format.

**Failing Tests**:
- `test_get_existing_status_returns_status`
- `test_get_status_without_launch_config_returns_default`
- `test_get_status_group_not_found_raises_error`
- `test_get_status_dynamodb_client_error_raises_application_error`
- `test_get_status_with_server_configs`

**Implementation Steps**:

2.1. [ ] Fix `test_get_existing_status_returns_status`
   - Update mock to return: `{"Item": {"groupId": "pg-123", "launchConfigStatus": {...}}}`
   - Verify mock_table.get_item is called with `Key={"groupId": "pg-123"}`
   - Verify result matches expected status

2.2. [ ] Fix `test_get_status_without_launch_config_returns_default`
   - Update mock to return: `{"Item": {"groupId": "pg-123", "groupName": "Test Group"}}`
   - Item should NOT have `launchConfigStatus` field
   - Verify result returns default status structure

2.3. [ ] Fix `test_get_status_group_not_found_raises_error`
   - Update mock to return: `{}` (empty dict, no "Item" key)
   - Verify raises `LaunchConfigApplicationError`
   - Verify error message mentions "not found"

2.4. [ ] Fix `test_get_status_dynamodb_client_error_raises_application_error`
   - Import: `from botocore.exceptions import ClientError`
   - Configure mock: `mock_table.get_item.side_effect = ClientError(...)`
   - Use proper ClientError structure:
     ```python
     ClientError(
         {"Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}},
         "GetItem"
     )
     ```
   - Verify raises `LaunchConfigApplicationError`
   - Verify error message mentions "DynamoDB query failed"

2.5. [ ] Fix `test_get_status_with_server_configs`
   - Update mock to return: `{"Item": {"groupId": "pg-123", "launchConfigStatus": {...}}}`
   - Include serverConfigs in launchConfigStatus
   - Verify result includes server configurations

2.6. [ ] Run all TestGetConfigStatus tests
   ```bash
   pytest tests/unit/test_launch_config_service_unit.py::TestGetConfigStatus -v
   ```

**Expected Result**: 5 passed, 0 failures

**Acceptance Criteria**:
- All 5 tests pass consistently
- Mock structure matches boto3 Table.get_item() response format
- Error cases properly raise ClientError
- Assertions verify correct behavior

---

## Task 3: Fix TestPersistConfigStatus (4 tests)

**Status**: [ ]

**Description**: Fix all 4 failing tests in TestPersistConfigStatus class by ensuring DynamoDB Table mock accepts proper update_item() parameters.

**Failing Tests**:
- `test_persist_valid_status_succeeds`
- `test_persist_with_server_configs`
- `test_persist_with_errors`
- `test_persist_dynamodb_client_error_raises_application_error`

**Implementation Steps**:

3.1. [ ] Fix `test_persist_valid_status_succeeds`
   - Configure mock_table.update_item to accept calls
   - Verify update_item is called with:
     - `Key={"groupId": "pg-123"}`
     - `UpdateExpression` containing "SET launchConfigStatus"
     - `ExpressionAttributeValues` containing `:status`
   - Use `mock_table.update_item.assert_called_once()` to verify call
   - Extract call_args to verify parameters

3.2. [ ] Fix `test_persist_with_server_configs`
   - Configure mock_table.update_item to accept calls
   - Verify serverConfigs are included in persisted status
   - Verify update_item is called with proper parameters

3.3. [ ] Fix `test_persist_with_errors`
   - Configure mock_table.update_item to accept calls
   - Verify errors array is included in persisted status
   - Verify update_item is called with proper parameters

3.4. [ ] Fix `test_persist_dynamodb_client_error_raises_application_error`
   - Import: `from botocore.exceptions import ClientError`
   - Configure mock: `mock_table.update_item.side_effect = ClientError(...)`
   - Use proper ClientError structure:
     ```python
     ClientError(
         {"Error": {"Code": "ValidationException", "Message": "Invalid update"}},
         "UpdateItem"
     )
     ```
   - Verify raises `LaunchConfigApplicationError`
   - Verify error message mentions "DynamoDB update failed"

3.5. [ ] Run all TestPersistConfigStatus tests
   ```bash
   pytest tests/unit/test_launch_config_service_unit.py::TestPersistConfigStatus -v
   ```

**Expected Result**: 4 passed, 0 failures

**Acceptance Criteria**:
- All 4 tests pass consistently
- Mock accepts proper update_item() parameters
- Error cases properly raise ClientError
- Assertions verify correct behavior

---

## Task 4: Document Correct Mock Pattern

**Status**: [ ]

**Description**: Add comprehensive documentation to the test file explaining the correct DynamoDB Table mock pattern for future reference.

**Implementation Steps**:

4.1. [ ] Add module-level docstring section for DynamoDB mocking
   - Location: Near top of `test_launch_config_service_unit.py`
   - After existing imports and before test classes

4.2. [ ] Document Pattern 1: Successful get_item()
   ```python
   """
   DynamoDB Table Mock Patterns
   =============================
   
   Pattern 1: Successful get_item() with Item
   ------------------------------------------
   mock_table.get_item.return_value = {
       "Item": {
           "groupId": "pg-123",
           "launchConfigStatus": {...}
       }
   }
   """
   ```

4.3. [ ] Document Pattern 2: Item not found
   ```python
   """
   Pattern 2: Item Not Found
   -------------------------
   mock_table.get_item.return_value = {}
   """
   ```

4.4. [ ] Document Pattern 3: ClientError
   ```python
   """
   Pattern 3: DynamoDB ClientError
   -------------------------------
   from botocore.exceptions import ClientError
   
   mock_table.get_item.side_effect = ClientError(
       {"Error": {"Code": "ResourceNotFoundException", "Message": "Not found"}},
       "GetItem"
   )
   """
   ```

4.5. [ ] Document Pattern 4: Successful update_item()
   ```python
   """
   Pattern 4: Successful update_item()
   -----------------------------------
   mock_table.update_item.return_value = {}
   
   # Verify call:
   mock_table.update_item.assert_called_once_with(
       Key={"groupId": "pg-123"},
       UpdateExpression="SET launchConfigStatus = :status",
       ExpressionAttributeValues={":status": {...}}
   )
   """
   ```

4.6. [ ] Document Pattern 5: Environment variable handling
   ```python
   """
   Pattern 5: Environment Variable Testing
   ---------------------------------------
   @patch.dict(os.environ, {}, clear=True)
   @patch("shared.launch_config_service._get_dynamodb_resource")
   def test_missing_env_var(self, mock_get_resource):
       # Reset module state
       import shared.launch_config_service as service
       service._protection_groups_table = None
       
       # Test code here
   """
   ```

**Expected Result**: Clear documentation for future test development

**Acceptance Criteria**:
- Documentation is comprehensive and clear
- All 5 patterns are documented with examples
- Documentation is placed in logical location
- Examples are copy-paste ready

---

## Task 5: Run Full Verification

**Status**: [ ]

**Description**: Run comprehensive test verification to ensure all fixes work correctly and no regressions occurred.

**Implementation Steps**:

5.1. [ ] Run the specific test file
   ```bash
   pytest tests/unit/test_launch_config_service_unit.py -v
   ```
   - Expected: 59 passed, 5 skipped, 0 failures
   - Verify all 10 previously failing tests now pass

5.2. [ ] Run full unit test suite
   ```bash
   pytest tests/unit/ -v
   ```
   - Expected: 1,063 passed, 12 skipped, 0 failures
   - Verify no regressions in other test files

5.3. [ ] Run tests multiple times for consistency
   ```bash
   for i in {1..3}; do 
     echo "Run $i:"
     pytest tests/unit/test_launch_config_service_unit.py -v --tb=short
   done
   ```
   - Verify consistent results across all runs
   - No flaky test behavior

5.4. [ ] Run with coverage report
   ```bash
   pytest tests/unit/test_launch_config_service_unit.py --cov=lambda.shared.launch_config_service --cov-report=term
   ```
   - Verify coverage remains high
   - Check that fixed tests contribute to coverage

5.5. [ ] Document final test results
   - Update this tasks.md with final verification results
   - Update requirements.md with completion status
   - Update design.md if any patterns changed during implementation

**Expected Result**: All tests pass consistently with no regressions

**Acceptance Criteria**:
- 1,063 total tests pass
- 12 tests remain skipped (expected)
- 0 failures
- Consistent results across multiple runs
- No performance degradation

---

## Task 6: Update Spec Status

**Status**: [ ]

**Description**: Update spec documents to reflect completion status.

**Implementation Steps**:

6.1. [ ] Update requirements.md
   - Change "Spec Status: 🔨 IN PROGRESS" to "Spec Status: ✅ COMPLETE"
   - Add completion date
   - Add final test results summary

6.2. [ ] Update design.md
   - Add "Implementation Complete" section
   - Document any deviations from original design
   - Add lessons learned

6.3. [ ] Update tasks.md
   - Mark all tasks as [x] complete
   - Add final verification results
   - Document total time spent

6.4. [ ] Create completion summary
   - Total tests fixed: 10
   - Total test files modified: 1
   - Final test results: 1,063 passed, 12 skipped, 0 failures
   - Success rate: 100% (excluding intentionally skipped tests)

**Expected Result**: Spec documents reflect successful completion

**Acceptance Criteria**:
- All spec documents updated
- Completion status clearly marked
- Final results documented
- Lessons learned captured

---

## Summary

**Total Tasks**: 6
**Completed**: 0
**In Progress**: 0
**Not Started**: 6

**Estimated Time**: 2-3 hours
**Actual Time**: TBD

**Test Targets**:
- Fix 10 failing tests
- Maintain 1,053 passing tests
- Keep 12 skipped tests
- Achieve 0 failures

**Success Criteria**:
- All 10 tests pass
- No regressions
- Pattern documented
- Spec complete
