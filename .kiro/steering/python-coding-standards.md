# Python Coding Standards

## CRITICAL: Always Follow PEP 8 Standards

**NEVER deviate from PEP 8 Python coding standards. This ensures consistent, readable, and maintainable code across the entire AWS DRS Orchestration project.**

## Code Formatting Rules (MANDATORY)

### 1. Line Length and Indentation
```python
# ALWAYS use 79 characters maximum line length (strict PEP 8)
# ALWAYS use 4 spaces per indentation level (NO TABS)
def example_function(parameter_one, parameter_two, parameter_three):
    """Function with proper indentation and line length."""
    if (parameter_one and parameter_two and 
        parameter_three):  # Line continuation with proper alignment
        return True
    return False
```

### 2. Import Organization (MANDATORY)
```python
# ALWAYS organize imports in this exact order with blank lines between groups:

# 1. Standard library imports
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# 2. Third-party imports
import boto3
import requests
from botocore.exceptions import ClientError

# 3. Local application imports
from lambda.utils import format_response
from lambda.exceptions import ValidationError
```

### 3. String Formatting (STANDARDIZED)
```python
# ALWAYS use double quotes for strings
message = "This is the standard string format"

# ALWAYS use f-strings for string formatting (Python 3.6+)
user_id = "12345"
region = "us-east-1"
result = f"User {user_id} in region {region} completed successfully"

# NEVER use old-style formatting
# BAD: "User %s in region %s" % (user_id, region)
# BAD: "User {} in region {}".format(user_id, region)
```

### 4. Whitespace and Spacing (CONSISTENT)
```python
# ALWAYS use proper spacing around operators
result = value_one + value_two
condition = (status == "active" and count > 0)

# ALWAYS use proper spacing in function calls
function_call(arg1, arg2, keyword_arg=value)

# ALWAYS use proper spacing in lists and dictionaries
my_list = [item1, item2, item3]
my_dict = {"key1": "value1", "key2": "value2"}

# NEVER use extra spaces
# BAD: result = value_one+value_two
# BAD: function_call( arg1 , arg2 )

# Whitespace in expressions and statements
# ALWAYS avoid extraneous whitespace
spam(ham[1], {eggs: 2})  # GOOD
# spam( ham[ 1 ], { eggs: 2 } )  # BAD

# ALWAYS use whitespace around assignment operators
x = 1
y = 2
long_variable = 3

# NEVER align assignment operators
# BAD:
# x             = 1
# y             = 2
# long_variable = 3

# Function annotations - use spaces around -> and :
def munge(input: AnyStr) -> AnyStr:
    pass

# Variable annotations - use spaces around :
code: int
class Point:
    coords: Tuple[int, int]
    label: str = '<unknown>'
```

### 5. Blank Lines (PEP 8 STANDARD)
```python
# ALWAYS use 2 blank lines around top-level function and class definitions
import os


class MyClass:
    """Example class."""
    pass


def top_level_function():
    """Example function."""
    pass


# ALWAYS use 1 blank line around method definitions inside classes
class MyClass:
    """Example class with methods."""
    
    def method_one(self):
        """First method."""
        pass
    
    def method_two(self):
        """Second method."""
        pass

# Use blank lines sparingly inside functions to indicate logical sections
def complex_function():
    """Function with logical sections."""
    # Setup phase
    data = initialize_data()
    config = load_config()
    
    # Processing phase
    processed_data = process(data, config)
    
    # Cleanup phase
    cleanup_resources()
    return processed_data
```

### 6. Source File Encoding (UTF-8)
```python
# ALWAYS use UTF-8 encoding for Python source files
# Files using ASCII (in Python 2) or UTF-8 (in Python 3) should not have an encoding declaration

# ONLY add encoding declaration if non-UTF-8 encoding is required (rare)
# -*- coding: utf-8 -*-

# For Python 3.x (our standard), UTF-8 is default - no declaration needed
```

## Naming Convention Rules (MANDATORY)

### 1. Function and Variable Names
```python
# ALWAYS use snake_case for functions and variables
def process_drs_servers():
    server_count = 0
    protection_group_id = "pg-12345"
    return server_count

# NEVER use camelCase or PascalCase for functions/variables
# BAD: def processDrsServers():
# BAD: serverCount = 0
```

### 2. Class Names
```python
# ALWAYS use PascalCase for class names
class ProtectionGroupManager:
    """Manages DRS protection groups."""
    
    def __init__(self):
        self.group_count = 0

class DRSOrchestrationError(Exception):
    """Custom exception for DRS orchestration errors."""
    pass
```

### 3. Constants
```python
# ALWAYS use UPPER_CASE with underscores for constants
MAX_RETRY_ATTEMPTS = 3
DEFAULT_REGION = "us-east-1"
DRS_SERVICE_NAME = "drs"
API_VERSION = "2020-02-26"
```

### 4. Avoid Problematic Names
```python
# NEVER use single-character names that are visually confusing
# BAD: l = []  # Looks like 1
# BAD: O = {}  # Looks like 0
# BAD: I = 1   # Looks like l

# GOOD: Use descriptive names
server_list = []
options_dict = {}
index = 1
```

### 5. Module and Package Names
```python
# ALWAYS use short, all-lowercase names for modules
# Underscores can be used if it improves readability
import mymodule
import my_module  # If needed for readability

# Package names should be short, all-lowercase, preferably without underscores
# mypackage/
#   __init__.py
#   submodule.py
```

### 6. Method Names and Instance Variables
```python
class ExampleClass:
    """Example class demonstrating naming conventions."""
    
    def __init__(self):
        # Public instance variables (use sparingly)
        self.public_attribute = "value"
        
        # Non-public instance variables (single leading underscore)
        self._internal_attribute = "internal"
        
        # Name mangling (double leading underscore, avoid unless necessary)
        self.__private_attribute = "private"
    
    def public_method(self):
        """Public method - snake_case."""
        pass
    
    def _internal_method(self):
        """Non-public method - single leading underscore."""
        pass
    
    @property
    def computed_property(self):
        """Property method - snake_case."""
        return self._internal_attribute
```

### 7. Function and Variable Annotations
```python
# ALWAYS use type hints for function parameters and return values
from typing import Dict, List, Optional, Union

def process_servers(
    server_ids: List[str], 
    region: str, 
    timeout: Optional[int] = None
) -> Dict[str, Union[str, int]]:
    """Process DRS servers with proper type annotations."""
    result: Dict[str, Union[str, int]] = {
        "processed_count": len(server_ids),
        "region": region
    }
    return result

# Variable annotations (when type is not obvious)
servers: List[Dict[str, str]] = []
config: Optional[Dict[str, Any]] = None
```

## Comments and Documentation Standards (PEP 8 + PEP 257)

### 1. Comments Best Practices
```python
# Comments should be complete sentences with proper capitalization and punctuation
# Use inline comments sparingly and ensure they're necessary

# GOOD - explains why, not what
# Compensate for network latency in DRS operations
timeout = base_timeout * 1.5

# BAD - explains obvious code
# Set timeout to base_timeout times 1.5
timeout = base_timeout * 1.5

# Block comments - use for complex logic explanation
# The following algorithm implements wave-based recovery orchestration.
# Each wave must complete successfully before the next wave begins.
# This ensures proper dependency management between application tiers.
for wave in recovery_plan.waves:
    execute_wave(wave)
    wait_for_completion(wave)

# Inline comments - use sparingly, separate with at least 2 spaces
x = x + 1  # Increment counter
```

### 2. Docstring Standards (PEP 257)
```python
def short_function():
    """Do something and return result."""
    pass

def complex_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Perform complex operation with detailed documentation.
    
    This function demonstrates the proper format for multi-line docstrings.
    The summary line should be concise and end with a period.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Dictionary containing operation results with keys:
        - status: Operation status string
        - data: Processed data
        
    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is not an integer
        
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result["status"])
        success
    """
    pass

class ExampleClass:
    """
    Example class demonstrating docstring conventions.
    
    Classes should have docstrings describing their purpose,
    public methods, and instance variables.
    
    Attributes:
        public_attr: Description of public attribute
    """
    
    def __init__(self, value: str):
        """Initialize with given value."""
        self.public_attr = value
    
    def public_method(self) -> str:
        """Return processed value."""
        return self.public_attr.upper()
```

## Programming Recommendations (PEP 8 BEST PRACTICES)

### 1. Comparisons and Boolean Operations
```python
# ALWAYS use 'is' and 'is not' for singleton comparisons
if value is None:
    pass

if value is not None:
    pass

# NEVER use == or != with None
# BAD: if value == None:
# BAD: if value != None:

# Use 'is not' rather than 'not ... is'
if foo is not None:  # GOOD
    pass
# if not foo is None:  # BAD

# Boolean comparisons - don't compare to True/False
if greeting:  # GOOD
    pass
# if greeting == True:  # BAD
# if greeting is True:  # BAD (unless specifically checking for True)

# Use startswith() and endswith() instead of string slicing
if filename.endswith('.py'):  # GOOD
    pass
# if filename[-3:] == '.py':  # BAD
```

### 2. Exception Handling Best Practices
```python
# ALWAYS derive exceptions from Exception, not BaseException
class CustomError(Exception):
    """Custom exception for application errors."""
    pass

# Use exception chaining for context
try:
    risky_operation()
except SomeError as e:
    raise CustomError("Operation failed") from e

# Be specific about exception types in except clauses
try:
    value = int(user_input)
except ValueError:
    print("Invalid number")
except (TypeError, AttributeError):
    print("Invalid input type")

# Use finally for cleanup that must happen
try:
    file = open('data.txt')
    process_file(file)
finally:
    file.close()

# Better: use context managers
with open('data.txt') as file:
    process_file(file)
```

### 3. Return Statements
```python
# Be consistent in return statements
def get_server_status(server_id: str) -> Optional[str]:
    """Get server status, return None if not found."""
    if server_id in active_servers:
        return active_servers[server_id]
    return None  # Explicit None return

# Don't use return value from functions that don't return anything
def process_data(data):
    """Process data in place."""
    data.sort()
    data.reverse()
    # No return statement needed

# result = process_data(my_data)  # BAD - process_data returns None
process_data(my_data)  # GOOD
```

### 4. String Methods vs String Module
```python
# ALWAYS use string methods instead of string module
name = "john doe"
formatted_name = name.title()  # GOOD

# import string
# formatted_name = string.capwords(name)  # BAD - avoid string module
```

### 5. Sequence Operations
```python
# Use ''.join() for string concatenation in loops
items = ['apple', 'banana', 'cherry']
result = ', '.join(items)  # GOOD

# BAD - inefficient string concatenation
# result = ''
# for item in items:
#     result += item + ', '

# Use enumerate() when you need both index and value
for i, item in enumerate(items):
    print(f"{i}: {item}")

# Use zip() for parallel iteration
names = ['Alice', 'Bob', 'Charlie']
ages = [25, 30, 35]
for name, age in zip(names, ages):
    print(f"{name} is {age} years old")
```

### 6. Lambda Functions
```python
# Keep lambda functions simple - prefer def for complex logic
# GOOD - simple lambda
squares = list(map(lambda x: x**2, range(10)))

# BAD - complex lambda
# process = lambda x: x.strip().lower().replace(' ', '_') if x else ''

# GOOD - use def for complex logic
def normalize_name(name: str) -> str:
    """Normalize name by stripping, lowercasing, and replacing spaces."""
    return name.strip().lower().replace(' ', '_') if name else ''

normalized_names = [normalize_name(name) for name in raw_names]
```

### 7. Default Mutable Arguments
```python
# NEVER use mutable objects as default arguments
def add_server(server_id: str, server_list: Optional[List[str]] = None) -> List[str]:
    """Add server to list, creating new list if none provided."""
    if server_list is None:
        server_list = []
    server_list.append(server_id)
    return server_list

# BAD - mutable default argument
# def add_server(server_id: str, server_list: List[str] = []) -> List[str]:
#     server_list.append(server_id)
#     return server_list
```

### 1. Lambda Handler Pattern
```python
import json
import logging
from typing import Any, Dict

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for DRS orchestration operations.
    
    Args:
        event: Lambda event containing request data
        context: Lambda context object
        
    Returns:
        Dict containing statusCode, body, and headers
        
    Raises:
        ValidationError: When input validation fails
        DRSServiceError: When DRS API calls fail
    """
    try:
        # Log incoming request
        logger.info(f"Processing request: {event.get('httpMethod')} {event.get('path')}")
        
        # Process request
        result = process_request(event)
        
        return {
            "statusCode": 200,
            "body": json.dumps(result),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
            "headers": {"Content-Type": "application/json"}
        }
```

### 2. DRS Integration Patterns
```python
import boto3
from botocore.exceptions import ClientError

def get_drs_client(region: str) -> boto3.client:
    """Get DRS client for specified region."""
    return boto3.client("drs", region_name=region)

def describe_source_servers(region: str) -> List[Dict[str, Any]]:
    """
    Describe DRS source servers in specified region.
    
    Args:
        region: AWS region name
        
    Returns:
        List of source server dictionaries
        
    Raises:
        DRSServiceError: When DRS API call fails
    """
    try:
        drs_client = get_drs_client(region)
        response = drs_client.describe_source_servers()
        return response.get("items", [])
        
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        raise DRSServiceError(f"DRS API error {error_code}: {error_message}")
```

## Exception Handling Standards

### 1. Specific Exception Handling
```python
# ALWAYS catch specific exceptions, not bare except
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Invalid value provided: {e}")
    raise ValidationError("Invalid input data")
except KeyError as e:
    logger.error(f"Missing required key: {e}")
    raise ValidationError(f"Missing required field: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise

# NEVER use bare except (unless absolutely necessary with # noqa comment)
# BAD:
# try:
#     risky_operation()
# except:  # This catches everything, including system exits
#     pass
```

### 2. AWS Service Exception Patterns
```python
from botocore.exceptions import ClientError, NoCredentialsError

def handle_aws_service_call():
    """Handle AWS service calls with proper exception handling."""
    try:
        # AWS service call
        response = drs_client.describe_jobs()
        return response
        
    except NoCredentialsError:
        logger.error("AWS credentials not configured")
        raise AuthenticationError("AWS credentials required")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "UnauthorizedOperation":
            raise PermissionError("Insufficient DRS permissions")
        elif error_code == "ThrottlingException":
            raise RateLimitError("DRS API rate limit exceeded")
        else:
            raise DRSServiceError(f"DRS API error: {error_code}")
```

## Documentation Standards

### 1. Function Docstrings (PEP 257)
```python
def create_protection_group(name: str, region: str, server_ids: List[str]) -> Dict[str, Any]:
    """
    Create a new DRS protection group.
    
    Creates a protection group containing the specified DRS source servers
    for coordinated disaster recovery operations.
    
    Args:
        name: Unique name for the protection group
        region: AWS region where servers are located
        server_ids: List of DRS source server IDs to include
        
    Returns:
        Dictionary containing protection group details:
        - group_id: Unique identifier for the created group
        - name: Protection group name
        - server_count: Number of servers in the group
        - created_at: ISO timestamp of creation
        
    Raises:
        ValidationError: When input parameters are invalid
        ConflictError: When server is already in another group
        DRSServiceError: When DRS API calls fail
        
    Example:
        >>> group = create_protection_group(
        ...     name="Web Servers",
        ...     region="us-east-1", 
        ...     server_ids=["s-1234567890abcdef0"]
        ... )
        >>> print(group["group_id"])
        pg-abc123def456
    """
```

### 2. Class Docstrings
```python
class ProtectionGroupManager:
    """
    Manages DRS protection groups for disaster recovery orchestration.
    
    This class provides methods for creating, updating, and managing
    protection groups that organize DRS source servers for coordinated
    recovery operations.
    
    Attributes:
        region: AWS region for DRS operations
        dynamodb_table: DynamoDB table for persistence
        
    Example:
        >>> manager = ProtectionGroupManager("us-east-1")
        >>> group = manager.create_group("Web Servers", ["s-123"])
        >>> manager.list_groups()
        [{"group_id": "pg-123", "name": "Web Servers"}]
    """
    
    def __init__(self, region: str):
        """
        Initialize protection group manager.
        
        Args:
            region: AWS region for DRS operations
        """
        self.region = region
        self.dynamodb_table = self._get_dynamodb_table()
```

## Code Quality Tools Integration

### 1. Tool Configuration Files

**pyproject.toml (Black and isort configuration)**:
```toml
[tool.black]
line-length = 79
target-version = ['py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  \.eggs
  | \.git
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 79
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

**.flake8 (Linting configuration)**:
```ini
[flake8]
max-line-length = 79
max-complexity = 10
select = E,W,F,C
ignore = 
    E203,  # Whitespace before ':' (conflicts with Black)
    W503,  # Line break before binary operator (PEP 8 updated)
exclude = 
    .git,
    __pycache__,
    .venv,
    build,
    dist,
    *.egg-info
per-file-ignores =
    __init__.py:F401  # Allow unused imports in __init__.py
```

### 2. Handling Complex Code (noqa Comments)
```python
# Use # noqa comments sparingly for legitimate exceptions
def complex_drs_orchestration_logic(execution_data):  # noqa: C901
    """
    Complex DRS orchestration logic that exceeds complexity limits.
    
    This function handles intricate wave-based recovery orchestration
    with multiple conditional paths that are necessary for proper
    disaster recovery coordination.
    """
    # Complex but necessary logic here
    pass

# Use specific noqa codes when possible
arn_pattern = "arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0"  # noqa: E501
```

## Performance and Security Guidelines

### 1. Efficient Code Patterns
```python
# Use list comprehensions for simple transformations
server_ids = [server["sourceServerID"] for server in servers if server["isArchived"] is False]

# Use generator expressions for memory efficiency with large datasets
total_size = sum(server["totalStorageBytes"] for server in servers)

# Use dict.get() with defaults instead of key checking
region = event.get("region", "us-east-1")
```

### 2. Security Best Practices
```python
import re

def sanitize_input(user_input: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';\\]', '', user_input.strip())
    return sanitized

def validate_server_id(server_id: str) -> bool:
    """Validate DRS source server ID format."""
    # DRS server IDs follow specific pattern
    pattern = r'^s-[a-f0-9]{17}$'
    return bool(re.match(pattern, server_id))
```

## Testing Standards

### 1. Unit Test Structure
```python
import pytest
from unittest.mock import Mock, patch
from lambda.protection_groups import create_protection_group

class TestProtectionGroups:
    """Test suite for protection group operations."""
    
    def test_create_protection_group_success(self):
        """Test successful protection group creation."""
        # Arrange
        name = "Test Group"
        region = "us-east-1"
        server_ids = ["s-1234567890abcdef0"]
        
        # Act
        with patch('lambda.protection_groups.dynamodb') as mock_db:
            mock_db.put_item.return_value = {}
            result = create_protection_group(name, region, server_ids)
        
        # Assert
        assert result["name"] == name
        assert result["region"] == region
        assert len(result["server_ids"]) == 1
        assert "group_id" in result
    
    def test_create_protection_group_invalid_server_id(self):
        """Test protection group creation with invalid server ID."""
        # Arrange
        name = "Test Group"
        region = "us-east-1"
        server_ids = ["invalid-server-id"]
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            create_protection_group(name, region, server_ids)
        
        assert "Invalid server ID format" in str(exc_info.value)
```

### 2. Integration Test Patterns
```python
import boto3
import pytest
from moto import mock_dynamodb, mock_drs

@mock_dynamodb
@mock_drs
class TestProtectionGroupsIntegration:
    """Integration tests for protection group operations."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create mock DynamoDB table
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table = self.dynamodb.create_table(
            TableName='protection-groups-test',
            KeySchema=[{'AttributeName': 'GroupId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'GroupId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
    
    def test_full_protection_group_lifecycle(self):
        """Test complete CRUD operations for protection groups."""
        # Test implementation here
        pass
```

## Common Violations and Fixes

### 1. Line Length Issues
```python
# BAD: Line too long
very_long_function_call_with_many_parameters(parameter_one, parameter_two, parameter_three, parameter_four, parameter_five)

# GOOD: Proper line breaking
very_long_function_call_with_many_parameters(
    parameter_one, parameter_two, parameter_three,
    parameter_four, parameter_five
)

# GOOD: Alternative formatting
result = very_long_function_call_with_many_parameters(
    parameter_one=value_one,
    parameter_two=value_two,
    parameter_three=value_three
)
```

### 2. Import Issues
```python
# BAD: Unused imports
import json
import os
import sys  # Not used in this file

# GOOD: Only import what you use
import json
import os

# BAD: Import order
import boto3
import json
import os

# GOOD: Proper import order
import json
import os

import boto3
```

### 3. Whitespace Issues
```python
# BAD: Trailing whitespace, inconsistent spacing
def function( arg1,arg2 ):    
    return arg1+arg2

# GOOD: Proper spacing, no trailing whitespace
def function(arg1, arg2):
    return arg1 + arg2
```

## Development Workflow Integration

### 1. Pre-commit Hooks (when available)
```bash
# Install pre-commit hooks (if not blocked by corporate policies)
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run black
pre-commit run flake8
```

### 2. Manual Quality Checks
```bash
# Format code with Black
black lambda/ scripts/ tests/

# Check with Flake8
flake8 lambda/ scripts/ tests/

# Sort imports with isort
isort lambda/ scripts/ tests/

# Run all checks together
black --check lambda/ && flake8 lambda/ && isort --check-only lambda/
```

### 3. IDE Integration
**VS Code settings.json**:
```json
{
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=79"],
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.flake8Args": ["--max-line-length=79"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

## NEVER DO These Things

### 1. Code Style Violations
- ❌ NEVER use tabs for indentation (always use 4 spaces)
- ❌ NEVER exceed 79 characters per line for code
- ❌ NEVER use bare except clauses without # noqa comment
- ❌ NEVER use single-character variable names l, O, I
- ❌ NEVER mix string quote styles in the same file

### 2. Import Violations
- ❌ NEVER import unused modules
- ❌ NEVER use wildcard imports (from module import *)
- ❌ NEVER mix import styles in the same file
- ❌ NEVER put imports in the middle of the file

### 3. Naming Violations
- ❌ NEVER use camelCase for functions or variables
- ❌ NEVER use snake_case for class names
- ❌ NEVER use lowercase for constants
- ❌ NEVER use reserved keywords as variable names
- ❌ NEVER use single-character names l, O, I (visually confusing)

### 4. Programming Violations
- ❌ NEVER use == or != with None (use 'is' and 'is not')
- ❌ NEVER use mutable objects as default function arguments
- ❌ NEVER derive exceptions from BaseException (use Exception)
- ❌ NEVER use string module methods (use string methods instead)
- ❌ NEVER use inefficient string concatenation in loops

## ALWAYS DO These Things

### 1. Follow Standards
- ✅ ALWAYS use 4 spaces for indentation
- ✅ ALWAYS keep lines under 79 characters
- ✅ ALWAYS use double quotes for strings
- ✅ ALWAYS use f-strings for string formatting
- ✅ ALWAYS organize imports properly

### 2. Write Quality Code
- ✅ ALWAYS include comprehensive docstrings
- ✅ ALWAYS handle exceptions specifically
- ✅ ALWAYS use type hints for function parameters and returns
- ✅ ALWAYS validate input parameters
- ✅ ALWAYS log important operations

### 3. Test Your Code
- ✅ ALWAYS write unit tests for new functions
- ✅ ALWAYS test error conditions
- ✅ ALWAYS verify functionality after formatting
- ✅ ALWAYS run quality checks before committing

### 4. Follow Programming Best Practices
- ✅ ALWAYS use 'is' and 'is not' for None comparisons
- ✅ ALWAYS use string methods instead of string module
- ✅ ALWAYS use ''.join() for string concatenation in loops
- ✅ ALWAYS use enumerate() when you need both index and value
- ✅ ALWAYS derive custom exceptions from Exception class
- ✅ ALWAYS use context managers (with statements) for resource management
- ✅ ALWAYS be explicit about return values (return None when appropriate)

## Quality Metrics Tracking

### Current Project Status (v1.2.2)
- **Total Violations Fixed**: 187 (from 435 to 248)
- **Critical Violations**: 0 (all F821 undefined names resolved)
- **Lambda Functions**: Fully compliant with minimal remaining violations
- **Scripts Directory**: Significantly improved with core functionality preserved
- **Compliance Rate**: 43% improvement achieved

### Ongoing Monitoring
- Run quality checks on every code change
- Track violation trends over time
- Maintain baseline violation reports
- Monitor compliance percentage improvements

## PEP 8 Compliance Verification

### Official PEP 8 Coverage Checklist
This steering document covers all major sections from the official PEP 8 specification:

- ✅ **Code Lay-out**: Indentation, line length, blank lines, source file encoding
- ✅ **String Quotes**: Consistent double-quote usage with f-string formatting
- ✅ **Whitespace in Expressions**: Proper spacing around operators, brackets, commas
- ✅ **Comments**: Block comments, inline comments, documentation strings
- ✅ **Naming Conventions**: Functions, variables, classes, constants, modules
- ✅ **Programming Recommendations**: Comparisons, exceptions, returns, sequences
- ✅ **Function Annotations**: Type hints for parameters and return values

### Verification Commands
```bash
# Verify PEP 8 compliance with automated tools
python -m flake8 --max-line-length=79 lambda/ scripts/ tests/
python -m black --check --line-length=79 lambda/ scripts/ tests/
python -m isort --check-only --profile=black lambda/ scripts/ tests/

# Fix violations automatically
python -m black --line-length=79 lambda/ scripts/ tests/
python -m isort --profile=black lambda/ scripts/ tests/
```

### Integration with Development Workflow
- All Python code MUST pass PEP 8 validation before commit
- Use automated tools (Black, Flake8, isort) for consistency
- Follow 79-character line length for maximum compatibility
- Maintain current project compliance rate of 43% improvement (v1.2.2)

This comprehensive Python coding standards guide ensures all code in the AWS DRS Orchestration project maintains enterprise-grade quality, readability, and consistency while following established PEP 8 conventions and AWS best practices.