# Test Isolation Refactoring - Tasks

## Phase 1: Verification and Analysis

- [x] 1. Verify current test failures
  - Run full test suite: `source .venv/bin/activate && pytest tests/unit/ -v`
  - Confirm 15 tests fail in batch mode
  - Verify tests pass individually
  - Document actual failure count and patterns

- [x] 2. Analyze test dependencies
  - Review each of the 15 tests in `test_data_management_new_operations.py`
  - Identify which DynamoDB tables each test accesses
  - Identify which getter functions need patching
  - Document mock return values needed for each test

## Phase 2: Refactor Target Account Operations (4 tests)

- [x] 3. Refactor test_create_target_account_success (lines 485-520)
  - Remove `@mock_aws` decorator
  - Create mock `target_accounts_table` using `MagicMock()`
  - Patch `get_target_accounts_table()` getter function
  - Configure mock return values for `put_item()` and `scan()`
  - Verify test passes individually and in batch

- [x] 4. Refactor test_create_target_account_duplicate (lines 523-547)
  - Remove `@mock_aws` decorator
  - Create mock `target_accounts_table` using `MagicMock()`
  - Patch `get_target_accounts_table()` getter function
  - Configure mock to return existing account in `scan()`
  - Verify test passes individually and in batch

- [x] 5. Refactor test_update_target_account_success (lines 550-577)
  - Remove `@mock_aws` decorator
  - Create mock `target_accounts_table` using `MagicMock()`
  - Patch `get_target_accounts_table()` getter function
  - Configure mock return values for `update_item()` and `get_item()`
  - Verify test passes individually and in batch

- [x] 6. Refactor test_delete_target_account_success (lines 580-599)
  - Remove `@mock_aws` decorator
  - Create mock `target_accounts_table` using `MagicMock()`
  - Patch `get_target_accounts_table()` getter function
  - Configure mock return values for `delete_item()` and `get_item()`
  - Verify test passes individually and in batch

## Phase 3: Refactor Tag Sync Operations (1 test)

- [x] 7. Refactor test_trigger_tag_sync_success (lines 704-738)
  - Remove `@mock_aws` decorator
  - Create mock `tag_sync_config_table` using `MagicMock()`
  - Create mock `protection_groups_table` using `MagicMock()`
  - Patch `get_tag_sync_config_table()` getter function
  - Patch `get_protection_groups_table()` getter function
  - Configure mock return values for both tables
  - Verify test passes individually and in batch

## Phase 4: Refactor Extended Source Servers (1 test)

- [x] 8. Refactor test_sync_extended_source_servers_success (lines 826-854)
  - Remove `@mock_aws` decorator
  - Create mock `protection_groups_table` using `MagicMock()`
  - Patch `get_protection_groups_table()` getter function
  - Configure mock return values for `scan()` and `update_item()`
  - Verify test passes individually and in batch

## Phase 5: Refactor Direct Invocation Tests (2 tests)

- [x] 9. Refactor test_direct_invocation_add_target_account (lines 987-1015)
  - Remove `@mock_aws` decorator
  - Create mock `target_accounts_table` using `MagicMock()`
  - Patch `get_target_accounts_table()` getter function
  - Configure mock return values for direct invocation mode
  - Verify test passes individually and in batch

- [x] 10. Refactor test_direct_invocation_trigger_tag_sync (lines 1018-1062)
  - Remove `@mock_aws` decorator
  - Create mock `tag_sync_config_table` using `MagicMock()`
  - Create mock `protection_groups_table` using `MagicMock()`
  - Patch `get_tag_sync_config_table()` getter function
  - Patch `get_protection_groups_table()` getter function
  - Configure mock return values for direct invocation mode
  - Verify test passes individually and in batch

## Phase 6: Refactor Error Case Tests (2 tests)

- [x] 11. Refactor test_create_target_account_missing_required_fields (lines 1127-1149)
  - Remove `@mock_aws` decorator
  - Create mock `target_accounts_table` using `MagicMock()`
  - Patch `get_target_accounts_table()` getter function
  - Configure mock for validation error scenario
  - Verify test passes individually and in batch

- [x] 12. Refactor test_delete_target_account_not_found (lines 1172-1183)
  - Remove `@mock_aws` decorator
  - Create mock `target_accounts_table` using `MagicMock()`
  - Patch `get_target_accounts_table()` getter function
  - Configure mock to return empty result for `get_item()`
  - Verify test passes individually and in batch

## Phase 7: Comprehensive Verification

- [x] 13. Run full test suite verification
  - Run: `source .venv/bin/activate && pytest tests/unit/ -v`
  - Verify all 15 refactored tests pass
  - Verify no new test failures introduced
  - Verify total test count remains the same
  - Check for any `UnrecognizedClientException` errors

- [x] 14. Run individual test verification
  - Run each refactored test individually
  - Verify all pass in isolation
  - Document any edge cases or issues

- [x] 15. Run deploy script test stage
  - Run: `./scripts/deploy.sh test --validate-only`
  - Verify Stage 3 (Tests) completes successfully
  - Verify no test failures block deployment
  - Check test execution time

## Phase 8: Documentation and Cleanup

- [x] 16. Update test file documentation
  - Add header comment explaining mocking pattern
  - Reference this spec in test file
  - Document any complex mock configurations
  - Add inline comments where helpful

- [x] 17. Create refactoring summary
  - Document all 15 tests refactored
  - List getter functions patched
  - Note any challenges or edge cases
  - Verify success criteria met

## Success Criteria

All tasks complete when:
- ✅ All 15 tests pass when run individually
- ✅ All 15 tests pass when run as part of full test suite
- ✅ No `UnrecognizedClientException` errors occur
- ✅ Full test suite shows 0 failures
- ✅ Deploy script Stage 3 (Tests) succeeds
- ✅ All tests use consistent explicit mocking pattern
- ✅ Mocking pattern matches reference implementation

## Notes

- Use `tests/unit/test_conflict_detection_comprehensive.py` as reference for mocking pattern
- Patch getter functions from `lambda/data-management-handler/index.py` (lines 242-280)
- Use correct patch path: `"data-management-handler.index.get_<table_name>_table"`
- Create mocks using `MagicMock()` with configured return values
- Verify each test after refactoring before moving to next test
