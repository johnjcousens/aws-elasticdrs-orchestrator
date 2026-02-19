# Fix Broken Tests - Tasks

## Phase 1: Diagnostic Analysis

- [x] 1. Run full test suite and capture detailed failure output
  - Run: `pytest tests/unit/ -v --tb=short > test_failures.txt 2>&1`
  - Analyze each failure category
  - Document root causes

## Phase 2: Fix AttributeError Issues (Priority 1)

- [x] 2. Fix query handler target_accounts_table AttributeError
  - Examine `lambda/query-handler/index.py` for correct attribute name
  - Update `tests/unit/test_query_handler_new_operations.py` fixture
  - Fix mock path in `mock_target_accounts_table` fixture
  - Verify 8 tests now pass

## Phase 3: Fix Query Handler Tests

- [x] 3. Fix get_server_config_history tests (11 failures)
  - Review `lambda/query-handler/index.py` implementation
  - Update test mocks in `test_query_handler_get_server_config_history.py`
  - Fix response format expectations
  - Verify all 11 tests pass

- [x] 4. Fix get_server_launch_config tests (8 failures)
  - Review launch config implementation
  - Update test mocks in `test_query_handler_get_server_launch_config.py`
  - Fix protection group structure expectations
  - Verify all 8 tests pass

- [x] 5. Fix query handler property tests (8 failures)
  - Review `test_query_handler_new_operations_property.py`
  - Update property test assumptions
  - Fix generators if needed
  - Verify all 8 property tests pass

- [x] 6. Fix query handler error handling tests (3 failures)
  - Review `test_error_handling_query_handler.py`
  - Update error response expectations
  - Fix DynamoDB error mocks
  - Verify all 3 tests pass

## Phase 4: Fix Data Management Tests

- [x] 7. Fix data management operations tests (7 failures)
  - Review `lambda/data-management-handler/index.py`
  - Update test mocks in `test_data_management_new_operations.py`
  - Fix direct invocation expectations
  - Fix tag sync and target account operations
  - Verify all 7 tests pass

- [x] 8. Fix data management error handling tests (5 failures)
  - Review `test_error_handling_data_management_handler.py`
  - Update authorization error expectations
  - Fix DRS API error mocks
  - Verify all 5 tests pass

- [x] 9. Fix data management response format test (1 failure)
  - Review `test_data_management_response_format.py`
  - Update direct invocation format expectations
  - Verify test passes

## Phase 5: Fix Combined Capacity Tests

- [x] 10. Fix combined capacity tests (5 failures)
  - Review `lambda/query-handler/index.py` capacity logic
  - Update test mocks in `test_handle_get_combined_capacity.py`
  - Fix staging accounts handling
  - Verify all 5 tests pass

## Phase 6: Fix Property-Based Tests

- [x] 11. Fix empty staging accounts property tests (2 failures)
  - Review `test_empty_staging_accounts_default_property.py`
  - Update default value assumptions
  - Verify both property tests pass

## Phase 7: Fix Miscellaneous Tests

- [x] 12. Fix IAM audit logging property test (1 failure)
  - Review `test_iam_audit_logging_property.py`
  - Update audit log field requirements
  - Verify test passes

## Phase 8: Verification

- [x] 13. Run full test suite in fast mode
  - Run: `pytest tests/unit/ -m "not property" -v`
  - Verify all non-property tests pass
  - Check for test isolation issues

- [x] 14. Run full test suite in full mode
  - Run: `pytest tests/unit/ -v`
  - Verify all 682 tests pass
  - Check execution time

- [x] 15. Test deploy script Stage 3
  - Run: `./scripts/deploy.sh test --validate-only`
  - Verify Stage 3 (Tests) completes successfully
  - Verify no test failures block deployment

## Phase 9: Documentation

- [x] 16. Update test documentation
  - Document any test pattern changes
  - Update mock patterns if needed
  - Add comments for complex fixes

- [x] 17. Create summary of fixes
  - List all tests fixed
  - Document root causes
  - Note any remaining issues

## Success Criteria

All tasks complete when:
- ✅ All 682 tests pass in both fast and full modes
- ✅ Deploy script Stage 3 (Tests) succeeds
- ✅ No test isolation issues remain
- ✅ All mocks accurately reflect Lambda handler structure
