# Test Isolation Refactoring Spec

## Quick Summary

**Problem:** 15 tests pass individually but fail in batch mode due to `@mock_aws` decorator conflicts  
**Solution:** Refactor tests to use explicit mocking pattern (like the 661 passing tests)  
**Status:** Ready to start implementation

## Files

- `requirements.md` - User stories and acceptance criteria
- `design.md` - Technical design and refactoring approach
- `tasks.md` - 17 implementation tasks

## Key Points

1. **Root Cause:** `@mock_aws` decorator conflicts with cached boto3 clients from earlier tests
2. **Affected Tests:** 15 tests in `test_data_management_new_operations.py`
3. **Solution:** Use explicit `patch()` mocking instead of decorator
4. **Pattern:** Patch getter functions (e.g., `get_target_accounts_table()`) not module variables
5. **Reference:** `test_conflict_detection_comprehensive.py` shows correct pattern

## Quick Start

```bash
# 1. Verify current failures
source .venv/bin/activate
pytest tests/unit/ -v

# 2. Start with Task 1 (verification)
# 3. Follow tasks 3-12 to refactor each test
# 4. Verify with Task 13 (full suite)
```

## Success Criteria

- ✅ All 15 tests pass individually
- ✅ All 15 tests pass in batch mode
- ✅ No `UnrecognizedClientException` errors
- ✅ Consistent mocking pattern across all tests

## Related Specs

- **Previous:** `.kiro/specs/fix-broken-tests/` (completed - fixed 68 tests)
- **Current:** `.kiro/specs/test-isolation-refactoring/` (this spec)

## Context

This spec addresses remaining test isolation issues discovered after completing the fix-broken-tests spec. The original spec successfully fixed 68 failing tests, but these 15 tests require a different approach due to their use of the `@mock_aws` decorator.
