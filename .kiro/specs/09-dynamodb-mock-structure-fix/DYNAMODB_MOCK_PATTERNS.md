# DynamoDB Mock Patterns

## Purpose

This document explains the correct patterns for mocking DynamoDB Table objects in unit tests, based on analysis of the launch configuration service tests.

## Problem: Incorrect DynamoDB Mock Structure

### Common Mistakes

When mocking DynamoDB Table objects, developers often make these mistakes:

1. **Mocking the wrong object**: Mocking `boto3.resource()` instead of the Table object
2. **Incorrect return format**: Returning raw data instead of DynamoDB response format
3. **Missing response structure**: Not including the `Item` wrapper for `get_item()`
4. **Incomplete mocks**: Not mocking all methods the code calls

## Solution: Correct DynamoDB Mock Structure

### Pattern 1: Mocking `_get_protection_groups_table()`

The launch configuration service uses a helper function `_get_protection_groups_table()` that returns a boto3 Table object. This is the correct level to mock.

```python
from unittest.mock import MagicMock, patch

@patch("shared.launch_config_service._get_protection_groups_table")
def test_get_existing_status_returns_status(mock_get_table):
    """Test retrieving existing configuration status."""
    # Create a mock Table object
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    # Define the expected status
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
    
    # Verify the result
    assert result == expected_status
    mock_table.get_item.assert_called_once_with(Key={"groupId": "pg-123"})
```

### Pattern 2: Mocking `update_item()`

When testing functions that persist data to DynamoDB:

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
    
    # Verify update_item was called with correct parameters
    mock_table.update_item.assert_called_once()
    call_args = mock_table.update_item.call_args
    
    # Verify the Key parameter
    assert call_args[1]["Key"] == {"groupId": "pg-123"}
    
    # Verify the UpdateExpression
    assert "UpdateExpression" in call_args[1]
    assert "SET launchConfigStatus" in call_args[1]["UpdateExpression"]
    
    # Verify the ExpressionAttributeValues
    assert ":status" in call_args[1]["ExpressionAttributeValues"]
    assert call_args[1]["ExpressionAttributeValues"][":status"] == config_status
```

### Pattern 3: Simulating DynamoDB Errors

To test error handling, use `botocore.exceptions.ClientError`:

```python
from botocore.exceptions import ClientError

@patch("shared.launch_config_service._get_protection_groups_table")
def test_get_status_dynamodb_client_error_raises_application_error(mock_get_table):
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

## DynamoDB Response Formats

### `get_item()` Response

```python
{
    "Item": {
        "groupId": "pg-123",
        "groupName": "Test Group",
        "launchConfigStatus": {
            "status": "ready",
            "lastApplied": "2025-02-16T10:30:00Z",
            "serverConfigs": {},
            "errors": []
        }
    }
}
```

**Key Points:**
- Response is a dictionary with an `"Item"` key
- The `"Item"` value contains the DynamoDB item attributes
- If item not found, response is `{}` (empty dict, no `"Item"` key)

### `update_item()` Parameters

```python
table.update_item(
    Key={"groupId": "pg-123"},
    UpdateExpression="SET launchConfigStatus = :status",
    ExpressionAttributeValues={
        ":status": config_status
    }
)
```

**Key Points:**
- `Key` specifies the primary key of the item to update
- `UpdateExpression` uses DynamoDB update expression syntax
- `ExpressionAttributeValues` provides values for placeholders in the expression

### `put_item()` Parameters

```python
table.put_item(
    Item={
        "groupId": "pg-123",
        "groupName": "Test Group",
        "launchConfigStatus": {
            "status": "ready",
            "serverConfigs": {},
            "errors": []
        }
    }
)
```

**Key Points:**
- `Item` is a dictionary containing all attributes
- Replaces the entire item if it exists
- Creates a new item if it doesn't exist

## Common Pitfalls

### Pitfall 1: Mocking at the Wrong Level

❌ **WRONG:**
```python
@patch("boto3.resource")
def test_something(mock_resource):
    mock_dynamodb = MagicMock()
    mock_resource.return_value = mock_dynamodb
    # This doesn't work because the code caches the table reference
```

✅ **CORRECT:**
```python
@patch("shared.launch_config_service._get_protection_groups_table")
def test_something(mock_get_table):
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    # This works because we mock the helper function
```

### Pitfall 2: Incorrect Response Format

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

### Pitfall 3: Not Handling Missing Items

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

## Testing with Property-Based Tests

When using Hypothesis for property-based testing with DynamoDB mocks:

```python
from hypothesis import given, strategies as st

@given(
    group_id=st.text(min_size=1, max_size=50),
    status=st.sampled_from(["ready", "pending", "failed"]),
)
@patch("shared.launch_config_service._get_protection_groups_table")
def test_property_status_field_validity(
    mock_table,
    group_id,
    status
):
    """Property test: status field must be valid."""
    from datetime import datetime, UTC
    
    # Create valid launchConfigStatus
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    launch_config_status = {
        "status": status,
        "lastApplied": timestamp,
        "appliedBy": "user@example.com",
        "serverConfigs": {},
        "errors": []
    }
    
    # Mock DynamoDB table
    mock_table_instance = MagicMock()
    mock_table.return_value = mock_table_instance
    
    # Mock get_item to return the status
    mock_table_instance.get_item.return_value = {
        "Item": {
            "groupId": group_id,
            "launchConfigStatus": launch_config_status
        }
    }
    
    # Retrieve status
    retrieved_status = get_config_status(group_id)
    
    # Property: Status must be one of valid values
    assert retrieved_status["status"] in [
        "ready", "pending", "failed", "not_configured"
    ]
```

## Best Practices

1. **Always mock at the helper function level** (`_get_protection_groups_table()`)
2. **Use correct DynamoDB response formats** (include `"Item"` wrapper for `get_item()`)
3. **Test error cases** using `ClientError` with appropriate error codes
4. **Verify mock calls** using `assert_called_once()` and `call_args`
5. **Handle missing items correctly** (return `{}` not `None`)
6. **Use MagicMock** for flexible mock objects
7. **Reset mocks between tests** using module-scoped fixtures (see TEST_PATTERNS.md)

## Related Documentation

- [TEST_PATTERNS.md](TEST_PATTERNS.md) - General test patterns and isolation
- [boto3 DynamoDB Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)

## Example: Complete Test Class

```python
class TestGetConfigStatus:
    """Tests for get_config_status function."""

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_get_existing_status_returns_status(self, mock_get_table):
        """Test retrieving existing configuration status."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

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

        assert result == expected_status
        mock_table.get_item.assert_called_once_with(Key={"groupId": "pg-123"})

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_get_status_group_not_found_raises_error(self, mock_get_table):
        """Test retrieving status for non-existent group raises error."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        # DynamoDB returns empty dict when item not found
        mock_table.get_item.return_value = {}

        with pytest.raises(
            LaunchConfigApplicationError,
            match="Protection group pg-123 not found",
        ):
            get_config_status("pg-123")

    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_get_status_dynamodb_error_raises_application_error(
        self, mock_get_table
    ):
        """Test DynamoDB ClientError is wrapped in application error."""
        from botocore.exceptions import ClientError

        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
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

## Summary

The key to successful DynamoDB mocking is:

1. **Mock at the right level**: Use `@patch("module._get_table_function")`
2. **Use correct response formats**: Include `{"Item": {...}}` for `get_item()`
3. **Handle all cases**: Success, not found (empty dict), and errors (ClientError)
4. **Verify calls**: Check that mocks were called with expected parameters
5. **Test error paths**: Use `side_effect` to simulate DynamoDB errors

Following these patterns ensures tests accurately reflect DynamoDB behavior and catch real issues in the code.
