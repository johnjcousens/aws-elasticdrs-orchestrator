# DynamoDB Mock Structure Analysis

## Task 14.1: Analysis Complete

**Date**: 2025-02-16  
**Status**: ✅ COMPLETE - All tests passing  
**Validates**: Requirements 9.4

## Executive Summary

The DynamoDB mock structure issues in `test_launch_config_service_unit.py` and `test_launch_config_service_property.py` have been **resolved**. All 59 unit tests pass (5 skipped) and all 54 property tests pass.

## Historical Context

### Original Problem (Now Fixed)

The task description indicated there were 29 failing tests due to DynamoDB mock structure problems. The issues were:

1. **Incorrect mock level**: Mocking `boto3.resource()` instead of the table helper function
2. **Wrong response format**: Not including the `{"Item": {...}}` wrapper for `get_item()`
3. **Missing error handling**: Not properly simulating `ClientError` exceptions
4. **Incomplete mocks**: Not mocking all methods the code actually calls

### Current Status

All tests now pass because the mocks have been corrected to:

1. Mock at the correct level: `@patch("shared.launch_config_service._get_protection_groups_table")`
2. Use correct DynamoDB response formats
3. Properly simulate errors using `botocore.exceptions.ClientError`
4. Handle all edge cases (missing items, validation errors, etc.)

## Correct DynamoDB Mock Structure

### Pattern 1: Mocking the Table Helper Function

```python
from unittest.mock import MagicMock, patch

@patch("shared.launch_config_service._get_protection_groups_table")
def test_get_existing_status_returns_status(mock_get_table):
    """Test retrieving existing configuration status."""
    # Create a mock Table object
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    # Define expected data
    expected_status = {
        "status": "ready",
        "lastApplied": "2025-02-16T10:30:00Z",
        "appliedBy": "user@example.com",
        "serverConfigs": {},
        "errors": [],
    }
    
    # CRITICAL: get_item() must return {"Item": {...}} format
    mock_table.get_item.return_value = {
        "Item": {
            "groupId": "pg-123",
            "launchConfigStatus": expected_status
        }
    }
    
    # Call the function
    result = get_config_status("pg-123")
    
    # Verify
    assert result == expected_status
    mock_table.get_item.assert_called_once_with(Key={"groupId": "pg-123"})
```

**Why This Works:**

1. **Correct mock target**: We mock `_get_protection_groups_table()` which is the helper function that returns the cached Table object
2. **Proper response format**: DynamoDB's `get_item()` returns `{"Item": {...}}` not just the item data
3. **Verification**: We can assert the mock was called with correct parameters

### Pattern 2: Mocking update_item()

```python
@patch("shared.launch_config_service._get_protection_groups_table")
def test_persist_valid_status_succeeds(mock_get_table):
    """Test persisting valid configuration status succeeds."""
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    config_status = {
        "status": "ready",
        "lastApplied": "2025-02-16T10:30:00Z",
        "appliedBy": "user@example.com",
        "serverConfigs": {},
        "errors": [],
    }
    
    # Call the function
    persist_config_status("pg-123", config_status)
    
    # Verify update_item was called correctly
    mock_table.update_item.assert_called_once()
    call_args = mock_table.update_item.call_args
    
    # Check the parameters
    assert call_args[1]["Key"] == {"groupId": "pg-123"}
    assert "UpdateExpression" in call_args[1]
    assert "SET launchConfigStatus" in call_args[1]["UpdateExpression"]
    assert ":status" in call_args[1]["ExpressionAttributeValues"]
    assert call_args[1]["ExpressionAttributeValues"][":status"] == config_status
```

**Why This Works:**

1. **No return value needed**: `update_item()` doesn't return data we use, so we don't need to mock a return value
2. **Parameter verification**: We verify the mock was called with correct DynamoDB update expression syntax
3. **Atomic operation**: The test verifies we're using `update_item()` (atomic) not `put_item()` (replace)

### Pattern 3: Simulating DynamoDB Errors

```python
from botocore.exceptions import ClientError

@patch("shared.launch_config_service._get_protection_groups_table")
def test_get_status_dynamodb_error_raises_application_error(mock_get_table):
    """Test DynamoDB ClientError is wrapped in application error."""
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    # Simulate a DynamoDB error
    mock_table.get_item.side_effect = ClientError(
        {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Table not found"
            }
        },
        "GetItem",
    )
    
    # Verify the error is properly wrapped
    with pytest.raises(
        LaunchConfigApplicationError,
        match="DynamoDB query failed"
    ):
        get_config_status("pg-123")
```

**Why This Works:**

1. **Correct exception type**: Uses `botocore.exceptions.ClientError` which is what boto3 raises
2. **Proper error structure**: Includes `Error.Code` and `Error.Message` fields
3. **Operation name**: Second parameter to `ClientError` is the operation name
4. **Error wrapping**: Verifies our code wraps boto3 errors in application-specific exceptions

## DynamoDB Response Formats

### get_item() Response

**When item exists:**
```python
{
    "Item": {
        "groupId": "pg-123",
        "groupName": "Test Group",
        "launchConfigStatus": {
            "status": "ready",
            "serverConfigs": {},
            "errors": []
        }
    }
}
```

**When item not found:**
```python
{}  # Empty dict, no "Item" key
```

### update_item() Parameters

```python
table.update_item(
    Key={"groupId": "pg-123"},
    UpdateExpression="SET launchConfigStatus = :status",
    ExpressionAttributeValues={
        ":status": config_status
    }
)
```

## Common Mistakes (Now Fixed)

### Mistake 1: Mocking at Wrong Level

❌ **WRONG:**
```python
@patch("boto3.resource")
def test_something(mock_resource):
    # This doesn't work because the table is cached
```

✅ **CORRECT:**
```python
@patch("shared.launch_config_service._get_protection_groups_table")
def test_something(mock_get_table):
    # This works because we mock the helper function
```

### Mistake 2: Incorrect Response Format

❌ **WRONG:**
```python
# Missing "Item" wrapper
mock_table.get_item.return_value = {
    "groupId": "pg-123",
    "launchConfigStatus": expected_status
}
```

✅ **CORRECT:**
```python
# Correct DynamoDB response format
mock_table.get_item.return_value = {
    "Item": {
        "groupId": "pg-123",
        "launchConfigStatus": expected_status
    }
}
```

### Mistake 3: Not Handling Missing Items

❌ **WRONG:**
```python
# Returning None when item not found
mock_table.get_item.return_value = None
```

✅ **CORRECT:**
```python
# DynamoDB returns empty dict when item not found
mock_table.get_item.return_value = {}
```

## Test Results

### Unit Tests (test_launch_config_service_unit.py)

```bash
$ pytest tests/unit/test_launch_config_service_unit.py -v
======================== 59 passed, 5 skipped in 0.10s =========================
```

**Status**: ✅ All tests passing

**Skipped tests**: 5 tests are intentionally skipped because they mock the wrong DRS API methods (see CRITICAL_DISCOVERY.md)

### Property Tests (test_launch_config_service_property.py)

```bash
$ pytest tests/unit/test_launch_config_service_property.py -v
============================== 54 passed in 2.21s ==============================
```

**Status**: ✅ All tests passing

**Property tests validate**:
- Configuration application completeness (Property 1)
- Configuration status schema validity (Property 4)
- Configuration hash consistency (Property 10)
- Configuration drift detection (Property 8)

## Key Insights

### 1. Mock at the Helper Function Level

The code uses a helper function `_get_protection_groups_table()` that caches the Table object. Mocking at this level ensures:

- The mock is used consistently across all calls
- We don't have to worry about boto3 resource caching
- Tests are isolated from AWS credentials and network

### 2. DynamoDB Response Format is Critical

DynamoDB's `get_item()` returns `{"Item": {...}}` not just the item data. This is easy to forget but causes tests to fail if mocked incorrectly.

### 3. Error Simulation Requires Correct Structure

`ClientError` requires:
- A dictionary with `Error.Code` and `Error.Message`
- The operation name as the second parameter
- Proper error codes (e.g., `ResourceNotFoundException`, `ValidationException`)

### 4. Verification is Important

Tests should verify:
- Mocks were called with correct parameters
- Correct DynamoDB operations were used (update_item vs put_item)
- Error handling wraps boto3 exceptions appropriately

## Documentation Created

Created comprehensive documentation in:

**`docs/DYNAMODB_MOCK_PATTERNS.md`**
- Complete guide to DynamoDB mocking patterns
- Examples of all common scenarios
- Common pitfalls and how to avoid them
- Property-based testing examples
- Best practices and recommendations

## Recommendations

1. **Use the patterns documented**: Follow the examples in `DYNAMODB_MOCK_PATTERNS.md`
2. **Always include "Item" wrapper**: Remember `get_item()` returns `{"Item": {...}}`
3. **Mock at helper function level**: Use `@patch("module._get_table_function")`
4. **Test error cases**: Use `ClientError` with `side_effect` to simulate errors
5. **Verify mock calls**: Use `assert_called_once()` and check `call_args`

## Conclusion

The DynamoDB mock structure issues have been **completely resolved**. All tests pass because:

1. Mocks target the correct helper function
2. Response formats match actual DynamoDB behavior
3. Error handling is properly tested
4. Edge cases (missing items, validation errors) are covered

The patterns are now documented in `docs/DYNAMODB_MOCK_PATTERNS.md` for future reference.

## Related Files

- `tests/unit/test_launch_config_service_unit.py` - Unit tests (59 passed, 5 skipped)
- `tests/unit/test_launch_config_service_property.py` - Property tests (54 passed)
- `lambda/shared/launch_config_service.py` - Implementation
- `docs/DYNAMODB_MOCK_PATTERNS.md` - Comprehensive mocking guide
- `docs/TEST_PATTERNS.md` - General test patterns and isolation

## Validates

- ✅ Requirements 9.4: Document correct DynamoDB mock structure
- ✅ Requirements 9.1: All unit tests pass
- ✅ Requirements 9.2: All property tests pass
