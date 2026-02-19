# Fix All Failing Tests - Design

## Approach

Systematically fix each failing test by:
1. Identifying the root cause
2. Applying the appropriate fix pattern
3. Verifying the fix works

## Common Fix Patterns

### Pattern 1: DynamoDB Mock Structure
```python
# Create mock table
mock_table = MagicMock()
mock_table.get_item.return_value = {"Item": {...}}

# Patch getter function
with patch("module.index.get_table_name", return_value=mock_table):
    # Test code
```

### Pattern 2: Environment Variables
```python
@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    monkeypatch.setenv("TABLE_NAME", "test-table")
```

### Pattern 3: Property Test Constraints
```python
@given(value=text(min_size=1, max_size=100))
def test_property(value):
    # Constrain inputs to valid range
```

## Implementation Strategy

1. Run tests to identify failures
2. Fix one test file at a time
3. Verify fixes don't break other tests
4. Move to next failing test

## Testing

After each fix:
```bash
pytest tests/unit/test_file.py -v
pytest tests/unit/ -v  # Verify no regressions
```
