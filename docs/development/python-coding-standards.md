# Python Coding Standards Guide

## Overview

This guide provides comprehensive Python coding standards for the AWS DRS Orchestration project, based on PEP 8 guidelines with project-specific configurations and best practices.

## Quick Reference

### Code Formatting
- **Line Length**: 79 characters maximum
- **Indentation**: 4 spaces (no tabs)
- **String Quotes**: Double quotes preferred for consistency
- **Trailing Commas**: Required in multi-line structures

### Import Organization
```python
# Standard library imports
import json
import time
from datetime import datetime

# Third-party imports
import boto3
import requests

# Local application imports
from lambda.utils import sanitize_input
from lambda.constants import DRS_LIMITS
```

### Function Documentation
```python
def create_protection_group(group_data: Dict) -> Dict:
    """
    Create a new protection group with validation.
    
    Args:
        group_data: Dictionary containing group configuration
        
    Returns:
        Dict: Created protection group with generated ID
        
    Raises:
        ValidationError: If group_data is invalid
        DynamoDBError: If database operation fails
    """
```

## Tool Configuration

### Black Formatter
Configuration in `pyproject.toml`:
```toml
[tool.black]
line-length = 79
target-version = ['py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # Exclude auto-generated files
  \.eggs
  | \.git
  | \.venv
  | venv
  | build
  | dist
)/
'''
```

### Flake8 Linter
Configuration in `.flake8`:
```ini
[flake8]
max-line-length = 79
max-complexity = 12
select = E,W,F,C,N
ignore = 
    E203,  # Whitespace before ':' (conflicts with Black)
    W503,  # Line break before binary operator (outdated)
exclude = 
    .git,
    __pycache__,
    .venv,
    venv,
    build,
    dist,
    *.egg-info
```

### isort Import Sorter
Configuration in `pyproject.toml`:
```toml
[tool.isort]
profile = "black"
line_length = 79
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

## Common Patterns

### Error Handling
```python
# Good: Specific exception handling
try:
    response = drs_client.describe_source_servers()
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'UnauthorizedOperation':
        logger.error(f"DRS access denied: {e}")
        raise DRSPermissionError("Insufficient DRS permissions") from e
    else:
        logger.error(f"DRS API error: {e}")
        raise DRSServiceError(f"DRS operation failed: {error_code}") from e
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise

# Bad: Bare except clause
try:
    response = drs_client.describe_source_servers()
except:  # Never use bare except
    pass
```

### Logging
```python
# Good: Structured logging with context
logger.info(
    "Starting recovery execution",
    extra={
        "execution_id": execution_id,
        "plan_id": plan_id,
        "wave_count": len(waves)
    }
)

# Good: F-string formatting
logger.error(f"Failed to start recovery for plan {plan_id}: {error}")

# Bad: String concatenation
logger.error("Failed to start recovery for plan " + plan_id + ": " + str(error))
```

### Type Hints
```python
from typing import Dict, List, Optional, Union

def process_recovery_plan(
    plan_data: Dict[str, Any],
    execution_type: str,
    dry_run: bool = False
) -> Dict[str, Union[str, List[Dict]]]:
    """Process recovery plan with proper type hints."""
    pass
```

### Constants
```python
# Good: Use constants for magic numbers and strings
DRS_LIMITS = {
    "MAX_SOURCE_SERVERS": 1000,
    "MAX_REPLICATING_SERVERS": 300,
}

EXECUTION_STATUSES = {
    "PENDING": "pending",
    "IN_PROGRESS": "in_progress", 
    "COMPLETED": "completed",
    "FAILED": "failed",
}

# Bad: Magic numbers in code
if server_count > 300:  # What is 300?
    raise ValueError("Too many servers")
```

## AWS-Specific Patterns

### DRS Client Usage
```python
def create_drs_client(region: str, account_id: str = None) -> boto3.client:
    """Create DRS client with optional cross-account access."""
    if account_id:
        # Cross-account access
        sts_client = boto3.client("sts", region_name=region)
        role_arn = f"arn:aws:iam::{account_id}:role/DRSOrchestrationRole"  # noqa: E231
        
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"drs-orchestration-{int(time.time())}"
        )
        
        credentials = assumed_role["Credentials"]
        return boto3.client(
            "drs",
            region_name=region,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"]
        )
    else:
        # Same account access
        return boto3.client("drs", region_name=region)
```

### DynamoDB Operations
```python
def update_execution_status(
    execution_id: str, 
    status: str, 
    details: Optional[Dict] = None
) -> None:
    """Update execution status in DynamoDB."""
    update_expression = "SET #status = :status, #updated = :updated"
    expression_values = {
        ":status": status,
        ":updated": datetime.utcnow().isoformat()
    }
    expression_names = {
        "#status": "status",
        "#updated": "lastUpdated"
    }
    
    if details:
        update_expression += ", #details = :details"
        expression_values[":details"] = details
        expression_names["#details"] = "details"
    
    try:
        dynamodb.update_item(
            TableName="execution-history",
            Key={"executionId": {"S": execution_id}},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names
        )
    except ClientError as e:
        logger.error(f"Failed to update execution {execution_id}: {e}")
        raise
```

## Violation Handling

### noqa Comments
Use `# noqa: CODE` comments for legitimate exceptions:

```python
# AWS ARN colons trigger false E231 violations
role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"  # noqa: E231

# Complex functions that cannot be easily simplified
def lambda_handler(event: Dict, context: Any) -> Dict:  # noqa: C901
    """Main Lambda handler with multiple operation types."""
    pass

# F-string false positives with emoji or special formatting
logger.info(f"✅ Operation completed successfully")  # noqa: F541
```

### Common False Positives
- **E231**: Missing whitespace after ':' in AWS ARNs and f-strings
- **E713**: "not in" detection in error messages containing "not found"
- **F541**: F-string missing placeholders in logging with emoji
- **C901**: Function complexity in Lambda handlers and main functions

## Development Workflow

### Pre-commit Checks
```bash
# Format code
black .

# Sort imports  
isort .

# Check for violations
flake8

# Run tests
pytest tests/python/ -v
```

### IDE Integration
Configure your IDE to run these tools automatically:
- **Format on Save**: Enable Black formatting
- **Lint on Type**: Enable Flake8 real-time checking
- **Import Organization**: Enable isort on save

### Quality Gates
All code must pass these checks before merge:
1. **Black**: No formatting violations
2. **isort**: Imports properly organized
3. **Flake8**: No new violations above baseline
4. **Tests**: All tests passing

## Common Violations and Fixes

### Import Issues
```python
# Bad: Unused import
import json  # F401 if not used

# Bad: Import not at top
def some_function():
    import boto3  # E402

# Good: Proper import organization
import json
import boto3
```

### Whitespace Issues
```python
# Bad: Missing whitespace
x=1+2  # E225, E226

# Bad: Trailing whitespace
name = "test"   # W291

# Good: Proper spacing
x = 1 + 2
name = "test"
```

### Line Length
```python
# Bad: Line too long
very_long_variable_name = some_function_with_many_parameters(param1, param2, param3, param4)  # E501

# Good: Proper line breaking
very_long_variable_name = some_function_with_many_parameters(
    param1, param2, param3, param4
)
```

### Function Complexity
```python
# Bad: Too complex (C901)
def complex_function():
    if condition1:
        if condition2:
            if condition3:
                # ... many nested conditions

# Good: Simplified with early returns
def simplified_function():
    if not condition1:
        return early_result
    
    if not condition2:
        return another_result
        
    # Main logic here
```

## Testing Standards

### Test Structure
```python
import pytest
from unittest.mock import Mock, patch

class TestProtectionGroups:
    """Test suite for protection group operations."""
    
    def test_create_protection_group_success(self):
        """Test successful protection group creation."""
        # Arrange
        group_data = {
            "name": "Test Group",
            "region": "us-east-1",
            "serverIds": ["s-123456789"]
        }
        
        # Act
        with patch('lambda.index.dynamodb') as mock_db:
            mock_db.put_item.return_value = {}
            result = create_protection_group(group_data)
        
        # Assert
        assert result["name"] == "Test Group"
        assert "groupId" in result
        mock_db.put_item.assert_called_once()
```

### Mock Usage
```python
# Good: Specific mocking
@patch('lambda.index.boto3.client')
def test_drs_operation(mock_boto3):
    mock_drs = Mock()
    mock_boto3.return_value = mock_drs
    mock_drs.describe_source_servers.return_value = {"items": []}
    
    # Test code here

# Bad: Over-mocking
@patch('lambda.index.boto3')
@patch('lambda.index.json')
@patch('lambda.index.time')
def test_simple_function(mock_time, mock_json, mock_boto3):
    # Too many mocks for simple test
```

## Performance Guidelines

### Efficient AWS Operations
```python
# Good: Batch operations
def batch_get_servers(server_ids: List[str]) -> List[Dict]:
    """Get multiple servers in batches."""
    batch_size = 100
    all_servers = []
    
    for i in range(0, len(server_ids), batch_size):
        batch = server_ids[i:i + batch_size]
        response = drs_client.describe_source_servers(
            filters={"sourceServerIDs": batch}
        )
        all_servers.extend(response.get("items", []))
    
    return all_servers

# Bad: Individual operations
def get_servers_individually(server_ids: List[str]) -> List[Dict]:
    """Inefficient individual server requests."""
    servers = []
    for server_id in server_ids:
        response = drs_client.describe_source_servers(
            filters={"sourceServerIDs": [server_id]}
        )
        servers.extend(response.get("items", []))
    return servers
```

### Memory Efficiency
```python
# Good: Generator for large datasets
def process_large_dataset(items: List[Dict]) -> Iterator[Dict]:
    """Process items one at a time to save memory."""
    for item in items:
        yield process_item(item)

# Bad: Loading everything into memory
def process_all_at_once(items: List[Dict]) -> List[Dict]:
    """Memory intensive for large datasets."""
    return [process_item(item) for item in items]
```

## Security Guidelines

### Input Validation
```python
import re

def validate_server_id(server_id: str) -> bool:
    """Validate DRS source server ID format."""
    pattern = r'^s-[a-f0-9]{17}$'
    return bool(re.match(pattern, server_id))

def sanitize_input(value: str) -> str:
    """Remove potentially dangerous characters."""
    if not isinstance(value, str):
        return str(value)
    
    # Remove HTML/script injection attempts
    dangerous_chars = ['<', '>', '"', "'", ';', '\\']
    for char in dangerous_chars:
        value = value.replace(char, '')
    
    return value.strip()
```

### Secrets Management
```python
# Good: Use AWS Secrets Manager
def get_api_credentials(secret_name: str) -> Dict:
    """Retrieve credentials from Secrets Manager."""
    secrets_client = boto3.client('secretsmanager')
    
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        raise

# Bad: Hardcoded secrets
API_KEY = "sk-1234567890abcdef"  # Never do this
```

## Troubleshooting

### Common Issues

#### Black and Flake8 Conflicts
```python
# Issue: Black formats this way, but Flake8 complains
my_list = [
    1, 2, 3,  # E231: missing whitespace after ','
]

# Solution: Add noqa comment for false positive
my_list = [
    1, 2, 3,  # noqa: E231
]
```

#### Import Order Issues
```python
# Issue: Wrong import order
from lambda.utils import helper
import boto3  # E402: module level import not at top

# Solution: Reorganize imports
import boto3
from lambda.utils import helper
```

#### Line Length in Strings
```python
# Issue: Long string exceeds line limit
error_msg = "This is a very long error message that exceeds the 79 character limit and causes E501"

# Solution: Use implicit string concatenation
error_msg = (
    "This is a very long error message that exceeds the 79 character "
    "limit and causes E501"
)
```

### Debugging Flake8 Issues
```bash
# Check specific file
flake8 lambda/index.py

# Check with verbose output
flake8 --verbose lambda/index.py

# Show only specific error types
flake8 --select=F401,F841 lambda/

# Ignore specific errors temporarily
flake8 --ignore=E231,E713 lambda/index.py
```

## Resources

### Documentation
- [PEP 8 Style Guide](https://pep8.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [isort Documentation](https://pycqa.github.io/isort/)

### Project-Specific
- [Development Workflow Guide](../guides/DEVELOPMENT_WORKFLOW_GUIDE.md)
- [PyCharm Setup Guide](pycharm-setup.md)
- [IDE Integration Testing](ide-integration-testing.md)

### Quality Tools
- [Quality Report Generator](../../scripts/generate_quality_report.py)
- [Violation Analysis Script](../../scripts/analyze_violations.py)
- [Pre-commit Configuration](../../.pre-commit-config.yaml)

## Summary

Following these Python coding standards ensures:
- **Consistency**: All code follows the same formatting and style rules
- **Readability**: Code is easy to read and understand by all team members
- **Maintainability**: Consistent patterns make code easier to modify and extend
- **Quality**: Automated tools catch common issues before they reach production
- **Collaboration**: Standardized code reduces friction in code reviews

The baseline of 248 violations represents legacy code that will be addressed incrementally. All new code must follow these standards without adding new violations.