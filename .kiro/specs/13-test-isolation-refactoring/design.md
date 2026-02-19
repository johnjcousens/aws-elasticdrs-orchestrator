# Test Isolation Refactoring - Design

## Overview
This design document outlines the approach for refactoring 15 tests from using moto's `@mock_aws` decorator to explicit mocking patterns, resolving test isolation issues in batch test execution.

## Architecture

### Current Architecture (Problematic)

```
Test Execution Flow (Batch Mode):
┌─────────────────────────────────────────────────────────────┐
│ Test 1-661: Explicit Mocking                                │
│ - Use patch() to mock getter functions                      │
│ - boto3 clients cached in memory                            │
│ - Tests pass ✅                                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Test 662-676: @mock_aws Decorator                           │
│ - Decorator tries to create mock AWS environment            │
│ - Conflicts with cached boto3 clients from earlier tests    │
│ - UnrecognizedClientException: Unknown service 'dynamodb'   │
│ - Tests fail ❌                                              │
└─────────────────────────────────────────────────────────────┘
```

### Target Architecture (Solution)

```
Test Execution Flow (Batch Mode):
┌─────────────────────────────────────────────────────────────┐
│ All Tests: Explicit Mocking                                 │
│ - Use patch() to mock getter functions                      │
│ - Create mock DynamoDB tables with MagicMock()              │
│ - Consistent mocking pattern across all tests               │
│ - No decorator conflicts                                    │
│ - All tests pass ✅                                          │
└─────────────────────────────────────────────────────────────┘
```

## Design Decisions

### 1. Explicit Mocking Over Decorators

**Decision:** Use explicit `patch()` mocking instead of `@mock_aws` decorator

**Rationale:**
- 661 existing tests already use explicit mocking successfully
- Explicit mocking provides better test isolation
- No conflicts with cached boto3 clients
- More maintainable and easier to debug
- Follows established codebase patterns

**Alternatives Considered:**
1. ❌ Fix `@mock_aws` decorator issues - Would require modifying conftest.py and potentially breaking other tests
2. ❌ Clear boto3 cache between tests - Attempted but failed, adds complexity
3. ✅ Refactor to explicit mocking - Proven pattern, aligns with existing tests

### 2. Patch Getter Functions, Not Module Variables

**Decision:** Patch getter functions like `get_target_accounts_table()` instead of module-level variables

**Rationale:**
- Lambda handler uses lazy-loaded getter functions (lines 242-280 in `lambda/data-management-handler/index.py`)
- No module-level table variables exist to patch
- Getter functions are the correct abstraction layer
- Matches reference implementation in `test_conflict_detection_comprehensive.py`

**Example:**
```python
# ❌ WRONG - Module variable doesn't exist
patch.object(data_management_handler, "target_accounts_table", mock_table)

# ✅ CORRECT - Patch getter function
patch("data-management-handler.index.get_target_accounts_table", return_value=mock_table)
```

### 3. Use MagicMock for DynamoDB Tables

**Decision:** Create mock DynamoDB tables using `MagicMock()` with configured return values

**Rationale:**
- Provides full control over mock behavior
- Can configure specific return values for each test
- Matches pattern used in 661 passing tests
- No dependency on moto's mock AWS environment

**Example:**
```python
mock_table = MagicMock()
mock_table.put_item.return_value = {}
mock_table.get_item.return_value = {"Item": {...}}
mock_table.scan.return_value = {"Items": [...]}
```

## Implementation Strategy

### Phase 1: Analyze Test Structure

For each of the 15 tests:
1. Identify which DynamoDB tables are accessed
2. Identify which getter functions need to be patched
3. Determine required mock return values
4. Document test dependencies

### Phase 2: Create Refactoring Template

Develop a standard template for refactoring:

```python
def test_example():
    # 1. Create mock tables
    mock_target_accounts = MagicMock()
    mock_target_accounts.put_item.return_value = {}
    
    mock_tag_sync = MagicMock()
    mock_tag_sync.get_item.return_value = {"Item": {...}}
    
    # 2. Patch getter functions
    with patch("data-management-handler.index.get_target_accounts_table", 
               return_value=mock_target_accounts):
        with patch("data-management-handler.index.get_tag_sync_config_table",
                   return_value=mock_tag_sync):
            # 3. Test logic (unchanged)
            result = lambda_handler(event, context)
            assert result["statusCode"] == 200
```

### Phase 3: Refactor Tests Systematically

Refactor tests in groups based on functionality:

**Group 1: Target Account Operations (4 tests)**
- `test_create_target_account_success`
- `test_create_target_account_duplicate`
- `test_update_target_account_success`
- `test_delete_target_account_success`

**Group 2: Tag Sync Operations (1 test)**
- `test_trigger_tag_sync_success`

**Group 3: Extended Source Servers (1 test)**
- `test_sync_extended_source_servers_success`

**Group 4: Direct Invocation (2 tests)**
- `test_direct_invocation_add_target_account`
- `test_direct_invocation_trigger_tag_sync`

**Group 5: Error Cases (2 tests)**
- `test_create_target_account_missing_required_fields`
- `test_delete_target_account_not_found`

### Phase 4: Verification

After each refactoring:
1. Run individual test: `pytest tests/unit/test_data_management_new_operations.py::test_name -v`
2. Run full suite: `pytest tests/unit/ -v`
3. Verify no new failures introduced

## Detailed Refactoring Examples

### Example 1: Target Account Creation

**Before:**
```python
@mock_aws
def test_create_target_account_success():
    # Create DynamoDB table using moto
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.create_table(...)
    
    # Test logic
    event = {...}
    result = lambda_handler(event, context)
    assert result["statusCode"] == 200
```

**After:**
```python
def test_create_target_account_success():
    # Create mock table
    mock_table = MagicMock()
    mock_table.put_item.return_value = {}
    mock_table.scan.return_value = {"Items": []}
    
    # Patch getter function
    with patch("data-management-handler.index.get_target_accounts_table",
               return_value=mock_table):
        # Test logic (unchanged)
        event = {...}
        result = lambda_handler(event, context)
        assert result["statusCode"] == 200
        
        # Verify mock was called correctly
        mock_table.put_item.assert_called_once()
```

### Example 2: Tag Sync with Multiple Tables

**Before:**
```python
@mock_aws
def test_trigger_tag_sync_success():
    # Create multiple DynamoDB tables using moto
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    tag_sync_table = dynamodb.create_table(...)
    pg_table = dynamodb.create_table(...)
    
    # Test logic
    event = {...}
    result = lambda_handler(event, context)
    assert result["statusCode"] == 200
```

**After:**
```python
def test_trigger_tag_sync_success():
    # Create mock tables
    mock_tag_sync = MagicMock()
    mock_tag_sync.get_item.return_value = {
        "Item": {"ConfigId": "test", "Enabled": True}
    }
    
    mock_pg_table = MagicMock()
    mock_pg_table.scan.return_value = {"Items": [...]}
    
    # Patch getter functions
    with patch("data-management-handler.index.get_tag_sync_config_table",
               return_value=mock_tag_sync):
        with patch("data-management-handler.index.get_protection_groups_table",
                   return_value=mock_pg_table):
            # Test logic (unchanged)
            event = {...}
            result = lambda_handler(event, context)
            assert result["statusCode"] == 200
```

## Getter Functions Reference

From `lambda/data-management-handler/index.py` (lines 242-280):

```python
def get_protection_groups_table():
    """Get DynamoDB table for protection groups."""
    global protection_groups_table
    if protection_groups_table is None:
        protection_groups_table = dynamodb.Table(
            os.environ["PROTECTION_GROUPS_TABLE"]
        )
    return protection_groups_table

def get_recovery_plans_table():
    """Get DynamoDB table for recovery plans."""
    global recovery_plans_table
    if recovery_plans_table is None:
        recovery_plans_table = dynamodb.Table(
            os.environ["RECOVERY_PLANS_TABLE"]
        )
    return recovery_plans_table

def get_executions_table():
    """Get DynamoDB table for executions."""
    global executions_table
    if executions_table is None:
        executions_table = dynamodb.Table(os.environ["EXECUTIONS_TABLE"])
    return executions_table

def get_target_accounts_table():
    """Get DynamoDB table for target accounts."""
    global target_accounts_table
    if target_accounts_table is None:
        target_accounts_table = dynamodb.Table(
            os.environ["TARGET_ACCOUNTS_TABLE"]
        )
    return target_accounts_table

def get_tag_sync_config_table():
    """Get DynamoDB table for tag sync configuration."""
    global tag_sync_config_table
    if tag_sync_config_table is None:
        tag_sync_config_table = dynamodb.Table(
            os.environ["TAG_SYNC_CONFIG_TABLE"]
        )
    return tag_sync_config_table
```

## Patch Path Construction

**Pattern:** `"<module-name>.<submodule>.get_<table_name>_table"`

**Examples:**
- `"data-management-handler.index.get_target_accounts_table"`
- `"data-management-handler.index.get_tag_sync_config_table"`
- `"data-management-handler.index.get_protection_groups_table"`
- `"data-management-handler.index.get_recovery_plans_table"`
- `"data-management-handler.index.get_executions_table"`

## Testing Strategy

### Unit Test Verification

After refactoring each test:

```bash
# 1. Test individually
pytest tests/unit/test_data_management_new_operations.py::test_create_target_account_success -v

# 2. Test the entire file
pytest tests/unit/test_data_management_new_operations.py -v

# 3. Test full suite
pytest tests/unit/ -v
```

### Success Criteria

- Individual test passes ✅
- File-level tests pass ✅
- Full suite passes ✅
- No `UnrecognizedClientException` errors ✅

## Risk Mitigation

### Risk 1: Breaking Test Logic
**Mitigation:** 
- Only change mocking approach, not test logic
- Verify test assertions remain unchanged
- Run tests after each refactoring

### Risk 2: Incorrect Mock Configuration
**Mitigation:**
- Reference working tests for mock patterns
- Verify mock return values match expected data structures
- Use `assert_called_once()` to verify mock usage

### Risk 3: Missing Patches
**Mitigation:**
- Analyze each test to identify all table accesses
- Patch all required getter functions
- Test will fail if patches are missing (good feedback)

## Performance Considerations

**Expected Impact:** Neutral to slightly positive

- Explicit mocking is typically faster than `@mock_aws` decorator
- No overhead from moto's AWS environment simulation
- Test execution time should remain similar or improve slightly

## Maintenance Considerations

**Benefits:**
- Consistent mocking pattern across all tests
- Easier to understand and debug
- Follows established codebase conventions
- No special decorator knowledge required

**Documentation:**
- Add comments explaining mock setup where complex
- Reference this design doc in test file header
- Update test documentation if needed

## Rollback Plan

If refactoring causes issues:

1. **Immediate:** Revert specific test to `@mock_aws` version
2. **Short-term:** Investigate root cause of failure
3. **Long-term:** Fix issue and re-apply refactoring

Git history preserves original implementations for reference.

## Success Metrics

1. **Test Pass Rate:** 100% (all 15 tests pass in batch mode)
2. **Consistency:** All tests use explicit mocking pattern
3. **Maintainability:** Code follows established patterns
4. **Reliability:** No test isolation issues remain

## References

- **Reference Implementation:** `tests/unit/test_conflict_detection_comprehensive.py`
- **Lambda Handler:** `lambda/data-management-handler/index.py` (lines 242-280)
- **Failing Tests:** `tests/unit/test_data_management_new_operations.py` (lines 485-1183)
- **Mocking Documentation:** Python `unittest.mock` library
- **Previous Spec:** `.kiro/specs/fix-broken-tests/` (completed)
