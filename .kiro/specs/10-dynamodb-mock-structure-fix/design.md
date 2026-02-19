# Design Document: DynamoDB Mock Structure Fix

## Overview

This design addresses 10 test failures in `test_launch_config_service_unit.py` caused by incorrect DynamoDB Table mock structure. The tests attempt to mock boto3 DynamoDB Table resources but don't properly configure the mocks to simulate the actual boto3 API behavior.

The solution implements proper DynamoDB Table mock patterns that correctly simulate:
- `get_item()` returning `{"Item": {...}}` format
- `update_item()` accepting standard parameters
- Environment variable handling for table names
- ClientError exception raising for error cases

## Architecture

### Current State Analysis

**Existing Mock Pattern (Incorrect)**:
```python
@patch("shared.launch_config_service._get_protection_groups_table")
def test_get_existing_status_returns_status(self, mock_get_table):
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    # ❌ WRONG: Doesn't configure get_item() return format
    mock_table.get_item.return_value = {
        "Item": {"groupId": "pg-123", "launchConfigStatus": {...}}
    }
    
    # Test calls get_config_status() which does:
    # response = table.get_item(Key={"groupId": group_id})
    # item = response.get("Item")  # ❌ Fails because mock doesn't return proper structure
```

**Problem**: The mock returns a dictionary directly, but boto3 Table.get_item() returns a response dictionary with "Item" key. The test doesn't properly configure the mock's return value structure.

**Root Causes**:
1. **Incorrect Response Format**: Mocks don't return `{"Item": {...}}` structure
2. **Missing Environment Variables**: Tests don't set `PROTECTION_GROUPS_TABLE` env var
3. **Incomplete Mock Configuration**: Mocks don't handle all boto3 Table method signatures
4. **Missing Error Simulation**: Mocks don't properly raise ClientError exceptions

### Correct Mock Pattern

**Pattern 1: Successful get_item() Response**:
```python
@patch("shared.launch_config_service._get_protection_groups_table")
def test_get_existing_status_returns_status(self, mock_get_table):
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    # ✅ CORRECT: Configure get_item() to return proper boto3 response format
    expected_status = {
        "status": "ready",
        "lastApplied": "2025-02-16T10:30:00Z",
        "appliedBy": "user@example.com",
        "serverConfigs": {},
        "errors": [],
    }
    
    mock_table.get_item.return_value = {
        "Item": {
            "groupId": "pg-123",
            "launchConfigStatus": expected_status
        }
    }
    
    result = get_config_status("pg-123")
    
    # Verify mock was called correctly
    mock_table.get_item.assert_called_once_with(Key={"groupId": "pg-123"})
    assert result == expected_status
```

**Pattern 2: Item Not Found (Empty Response)**:
```python
@patch("shared.launch_config_service._get_protection_groups_table")
def test_get_status_group_not_found_raises_error(self, mock_get_table):
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    # ✅ CORRECT: Empty dict when item doesn't exist
    mock_table.get_item.return_value = {}
    
    with pytest.raises(
        LaunchConfigApplicationError,
        match="Protection group pg-123 not found",
    ):
        get_config_status("pg-123")
```

**Pattern 3: Item Without launchConfigStatus Field**:
```python
@patch("shared.launch_config_service._get_protection_groups_table")
def test_get_status_without_launch_config_returns_default(self, mock_get_table):
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    # ✅ CORRECT: Item exists but doesn't have launchConfigStatus field
    mock_table.get_item.return_value = {
        "Item": {
            "groupId": "pg-123",
            "groupName": "Test Group"
            # No launchConfigStatus field
        }
    }
    
    result = get_config_status("pg-123")
    
    # Should return default status
    assert result["status"] == "not_configured"
    assert result["lastApplied"] is None
```

**Pattern 4: DynamoDB ClientError**:
```python
@patch("shared.launch_config_service._get_protection_groups_table")
def test_get_status_dynamodb_client_error_raises_application_error(self, mock_get_table):
    from botocore.exceptions import ClientError
    
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    # ✅ CORRECT: Configure get_item() to raise ClientError
    mock_table.get_item.side_effect = ClientError(
        {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Table not found"
            }
        },
        "GetItem",
    )
    
    with pytest.raises(
        LaunchConfigApplicationError,
        match="DynamoDB query failed"
    ):
        get_config_status("pg-123")
```

**Pattern 5: Successful update_item()**:
```python
@patch("shared.launch_config_service._get_protection_groups_table")
def test_persist_valid_status_succeeds(self, mock_get_table):
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    config_status = {
        "status": "ready",
        "serverConfigs": {},
        "errors": [],
    }
    
    persist_config_status("pg-123", config_status)
    
    # ✅ CORRECT: Verify update_item() was called with proper parameters
    mock_table.update_item.assert_called_once()
    call_args = mock_table.update_item.call_args
    
    # Verify Key parameter
    assert call_args[1]["Key"] == {"groupId": "pg-123"}
    
    # Verify UpdateExpression
    assert "UpdateExpression" in call_args[1]
    assert "SET launchConfigStatus" in call_args[1]["UpdateExpression"]
    
    # Verify ExpressionAttributeValues
    assert "ExpressionAttributeValues" in call_args[1]
    assert ":status" in call_args[1]["ExpressionAttributeValues"]
```

**Pattern 6: Environment Variable Handling**:
```python
@patch.dict(os.environ, {}, clear=True)
@patch("shared.launch_config_service._get_dynamodb_resource")
def test_missing_table_name_env_var_raises_error(self, mock_get_resource):
    # Reset global variables
    import shared.launch_config_service as service
    service._protection_groups_table = None
    
    mock_dynamodb = MagicMock()
    mock_get_resource.return_value = mock_dynamodb
    
    # ✅ CORRECT: Test with empty environment
    with pytest.raises(
        LaunchConfigApplicationError,
        match="PROTECTION_GROUPS_TABLE environment variable not set",
    ):
        service._get_protection_groups_table()
```

## Components and Interfaces

### Component 1: DynamoDB Table Mock Factory

**Purpose**: Provide reusable function to create properly configured DynamoDB Table mocks.

**Interface**:
```python
def create_dynamodb_table_mock(
    get_item_response=None,
    get_item_side_effect=None,
    update_item_response=None,
    update_item_side_effect=None,
):
    """
    Create a properly configured DynamoDB Table mock.
    
    Args:
        get_item_response: Response dict for get_item() calls
        get_item_side_effect: Exception or list for get_item() side_effect
        update_item_response: Response dict for update_item() calls
        update_item_side_effect: Exception or list for update_item() side_effect
        
    Returns:
        MagicMock configured to simulate boto3 Table behavior
    """
    mock_table = MagicMock()
    
    if get_item_response is not None:
        mock_table.get_item.return_value = get_item_response
    if get_item_side_effect is not None:
        mock_table.get_item.side_effect = get_item_side_effect
        
    if update_item_response is not None:
        mock_table.update_item.return_value = update_item_response
    if update_item_side_effect is not None:
        mock_table.update_item.side_effect = update_item_side_effect
        
    return mock_table
```

**Usage Example**:
```python
@patch("shared.launch_config_service._get_protection_groups_table")
def test_example(self, mock_get_table):
    # Create mock with successful get_item response
    mock_table = create_dynamodb_table_mock(
        get_item_response={
            "Item": {
                "groupId": "pg-123",
                "launchConfigStatus": {"status": "ready"}
            }
        }
    )
    mock_get_table.return_value = mock_table
    
    result = get_config_status("pg-123")
    assert result["status"] == "ready"
```

### Component 2: Test Fixture for Environment Variables

**Purpose**: Provide reusable fixture to set up environment variables for tests.

**Interface**:
```python
@pytest.fixture
def dynamodb_env_vars():
    """Set up DynamoDB environment variables for tests."""
    with patch.dict(
        os.environ,
        {"PROTECTION_GROUPS_TABLE": "test-protection-groups"},
        clear=False
    ):
        yield
```

**Usage Example**:
```python
def test_with_env_vars(dynamodb_env_vars):
    # Environment variables are set
    assert os.environ["PROTECTION_GROUPS_TABLE"] == "test-protection-groups"
```

### Component 3: Module State Reset Helper

**Purpose**: Reset module-level variables before tests that check initialization.

**Interface**:
```python
def reset_launch_config_service_state():
    """Reset module-level state in launch_config_service."""
    import shared.launch_config_service as service
    service._protection_groups_table = None
    service._dynamodb = None
```

**Usage Example**:
```python
@patch.dict(os.environ, {}, clear=True)
@patch("shared.launch_config_service._get_dynamodb_resource")
def test_missing_env_var(self, mock_get_resource):
    reset_launch_config_service_state()
    
    with pytest.raises(LaunchConfigApplicationError):
        service._get_protection_groups_table()
```

## Data Models

### DynamoDB get_item() Response Format

**Successful Response with Item**:
```python
{
    "Item": {
        "groupId": "pg-123",  # Primary key
        "groupName": "Test Group",
        "launchConfigStatus": {
            "status": "ready",
            "lastApplied": "2025-02-16T10:30:00Z",
            "appliedBy": "user@example.com",
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": "2025-02-16T10:30:00Z",
                    "configHash": "sha256:abc123",
                    "errors": []
                }
            },
            "errors": []
        }
    },
    "ResponseMetadata": {
        "RequestId": "...",
        "HTTPStatusCode": 200
    }
}
```

**Response When Item Not Found**:
```python
{
    "ResponseMetadata": {
        "RequestId": "...",
        "HTTPStatusCode": 200
    }
    # No "Item" key
}
```

**Response When Item Exists Without launchConfigStatus**:
```python
{
    "Item": {
        "groupId": "pg-123",
        "groupName": "Test Group"
        # No launchConfigStatus field
    },
    "ResponseMetadata": {
        "RequestId": "...",
        "HTTPStatusCode": 200
    }
}
```

### DynamoDB update_item() Parameters

**Standard update_item() Call**:
```python
table.update_item(
    Key={"groupId": "pg-123"},
    UpdateExpression="SET launchConfigStatus = :status",
    ExpressionAttributeValues={
        ":status": {
            "status": "ready",
            "lastApplied": "2025-02-16T10:30:00Z",
            "appliedBy": "user@example.com",
            "serverConfigs": {},
            "errors": []
        }
    }
)
```

**Response Format**:
```python
{
    "Attributes": {
        # Updated item attributes (if ReturnValues specified)
    },
    "ResponseMetadata": {
        "RequestId": "...",
        "HTTPStatusCode": 200
    }
}
```

## Error Handling

### Error Scenario 1: Missing Environment Variable

**Situation**: `PROTECTION_GROUPS_TABLE` environment variable not set.

**Handling**:
- Check for environment variable before creating table resource
- Raise `LaunchConfigApplicationError` with clear message
- Test verifies error is raised with correct message

**Test Pattern**:
```python
@patch.dict(os.environ, {}, clear=True)
@patch("shared.launch_config_service._get_dynamodb_resource")
def test_missing_table_name_env_var_raises_error(self, mock_get_resource):
    reset_launch_config_service_state()
    
    mock_dynamodb = MagicMock()
    mock_get_resource.return_value = mock_dynamodb
    
    with pytest.raises(
        LaunchConfigApplicationError,
        match="PROTECTION_GROUPS_TABLE environment variable not set",
    ):
        service._get_protection_groups_table()
```

### Error Scenario 2: DynamoDB ClientError on get_item()

**Situation**: DynamoDB get_item() raises ClientError.

**Handling**:
- Catch ClientError exception
- Wrap in `LaunchConfigApplicationError` with context
- Test verifies proper error wrapping

**Test Pattern**:
```python
@patch("shared.launch_config_service._get_protection_groups_table")
def test_get_status_dynamodb_client_error(self, mock_get_table):
    from botocore.exceptions import ClientError
    
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    mock_table.get_item.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "Not found"}},
        "GetItem",
    )
    
    with pytest.raises(
        LaunchConfigApplicationError,
        match="DynamoDB query failed"
    ):
        get_config_status("pg-123")
```

### Error Scenario 3: DynamoDB ClientError on update_item()

**Situation**: DynamoDB update_item() raises ClientError.

**Handling**:
- Catch ClientError exception
- Wrap in `LaunchConfigApplicationError` with context
- Test verifies proper error wrapping

**Test Pattern**:
```python
@patch("shared.launch_config_service._get_protection_groups_table")
def test_persist_dynamodb_client_error(self, mock_get_table):
    from botocore.exceptions import ClientError
    
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    mock_table.update_item.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "Invalid"}},
        "UpdateItem",
    )
    
    config_status = {"status": "ready", "serverConfigs": {}, "errors": []}
    
    with pytest.raises(
        LaunchConfigApplicationError,
        match="DynamoDB update failed"
    ):
        persist_config_status("pg-123", config_status)
```

### Error Scenario 4: Item Not Found

**Situation**: get_item() returns empty response (no "Item" key).

**Handling**:
- Check if "Item" key exists in response
- Raise `LaunchConfigApplicationError` if not found
- Test verifies proper error message

**Test Pattern**:
```python
@patch("shared.launch_config_service._get_protection_groups_table")
def test_get_status_group_not_found_raises_error(self, mock_get_table):
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    # Empty response (no "Item" key)
    mock_table.get_item.return_value = {}
    
    with pytest.raises(
        LaunchConfigApplicationError,
        match="Protection group pg-123 not found",
    ):
        get_config_status("pg-123")
```

## Testing Strategy

### Unit Test Fixes

**Fix Category 1: TestEnvironmentVariableHandling (1 test)**
- Fix `test_missing_table_name_env_var_raises_error`
- Use `@patch.dict(os.environ, {}, clear=True)` to clear environment
- Reset module state before test
- Verify proper error is raised

**Fix Category 2: TestGetConfigStatus (5 tests)**
- Fix all get_item() mock return values to use `{"Item": {...}}` format
- Fix empty response case to return `{}`
- Fix ClientError case to properly raise exception
- Verify all assertions match expected behavior

**Fix Category 3: TestPersistConfigStatus (4 tests)**
- Fix update_item() mock to accept proper parameters
- Verify Key, UpdateExpression, ExpressionAttributeValues
- Fix ClientError case to properly raise exception
- Verify all assertions match expected behavior

### Verification Tests

**Test 1: Run Individual Test File**
```bash
pytest tests/unit/test_launch_config_service_unit.py -v
```
Expected: 59 passed, 5 skipped, 0 failures

**Test 2: Run Full Test Suite**
```bash
pytest tests/unit/ -v
```
Expected: 1,063 passed, 12 skipped, 0 failures

**Test 3: Run Multiple Times for Consistency**
```bash
for i in {1..5}; do pytest tests/unit/test_launch_config_service_unit.py -v; done
```
Expected: Consistent results across all runs

## Implementation Notes

### Mock Configuration Best Practices

1. **Always use proper response format**: `{"Item": {...}}` for get_item()
2. **Configure side_effect for errors**: Use ClientError exceptions
3. **Verify mock calls**: Use `assert_called_once_with()` to verify parameters
4. **Reset module state**: Reset global variables before environment variable tests
5. **Use patch.dict for environment**: Properly isolate environment variable changes

### Common Mistakes to Avoid

1. ❌ **Don't return Item directly**: `mock_table.get_item.return_value = {"groupId": "pg-123"}`
2. ✅ **Do wrap in response dict**: `mock_table.get_item.return_value = {"Item": {"groupId": "pg-123"}}`

3. ❌ **Don't forget to reset state**: Tests that check initialization need clean state
4. ✅ **Do reset module variables**: `service._protection_groups_table = None`

5. ❌ **Don't use generic exceptions**: `mock_table.get_item.side_effect = Exception("Error")`
6. ✅ **Do use ClientError**: `mock_table.get_item.side_effect = ClientError(...)`

### Documentation Updates

After fixing tests, document the correct mock pattern in test file:

```python
"""
DynamoDB Table Mock Pattern
===========================

When mocking DynamoDB Table resources, use this pattern:

1. Successful get_item():
   mock_table.get_item.return_value = {"Item": {...}}

2. Item not found:
   mock_table.get_item.return_value = {}

3. ClientError:
   from botocore.exceptions import ClientError
   mock_table.get_item.side_effect = ClientError(
       {"Error": {"Code": "...", "Message": "..."}},
       "GetItem"
   )

4. Successful update_item():
   mock_table.update_item.return_value = {}
   # Verify call:
   mock_table.update_item.assert_called_once_with(
       Key={"groupId": "..."},
       UpdateExpression="...",
       ExpressionAttributeValues={...}
   )
"""
```

## Performance Considerations

- Mock configuration is fast (no performance impact)
- Tests should run in <1 second each
- Full test file should complete in <30 seconds
- No network calls (all mocked)

## Success Metrics

- All 10 failing tests pass
- Test execution time remains consistent
- No regression in other tests
- Mock pattern is clear and reusable
- Documentation is complete

## Related Documentation

- boto3 DynamoDB Table documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#table
- unittest.mock documentation: https://docs.python.org/3/library/unittest.mock.html
- pytest fixtures: https://docs.pytest.org/en/stable/fixture.html
