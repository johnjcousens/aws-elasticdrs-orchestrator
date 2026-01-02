# IDE Integration Testing Guide

This guide provides step-by-step tests to verify that your IDE is properly configured for Python coding standards in the AWS DRS Orchestration project.

## Pre-Test Setup

### Environment Verification
```bash
# Activate virtual environment
source venv/bin/activate

# Verify tools are installed
black --version
flake8 --version
isort --version
pytest --version
```

### Create Test Directory
```bash
mkdir -p /tmp/ide-test
cd /tmp/ide-test
```

## Test 1: Black Formatter Integration

### Create Test File
Create `test_black.py` with intentionally poor formatting:

```python
# Poorly formatted Python code
import os,sys,json
def badly_formatted_function(param1,param2,param3):
    if param1=='test'and param2>10:
        result={'key1':param1,'key2':param2,'key3':param3}
        return result
    else:return None

class PoorlyFormattedClass:
    def __init__(self,name,value):
        self.name=name
        self.value=value
    def get_info(self):return f"{self.name}: {self.value}"
```

### VS Code Test
1. **Open file in VS Code**
2. **Save file** (`Ctrl+S` / `Cmd+S`)
3. **Expected Result**: File should be automatically formatted by Black

### PyCharm Test
1. **Open file in PyCharm**
2. **Reformat code** (`Ctrl+Alt+L` / `Cmd+Option+L`)
3. **Expected Result**: File should be formatted by Black

### Expected Output
After formatting, the file should look like:
```python
# Properly formatted Python code
import json
import os
import sys


def badly_formatted_function(param1, param2, param3):
    if param1 == "test" and param2 > 10:
        result = {"key1": param1, "key2": param2, "key3": param3}
        return result
    else:
        return None


class PoorlyFormattedClass:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def get_info(self):
        return f"{self.name}: {self.value}"
```

### Manual Verification
```bash
# Test Black manually
black test_black.py --diff
# Should show no changes if IDE formatting worked
```

## Test 2: Flake8 Linting Integration

### Create Test File
Create `test_flake8.py` with PEP 8 violations:

```python
import os
import sys
import unused_module  # F401: unused import

def function_with_violations():
    x=1+2  # E225: missing whitespace around operator
    if x==3:  # E225: missing whitespace around operator
        print("test")
    unused_variable = "test"  # F841: unused variable
    
def overly_long_function_name_that_exceeds_reasonable_length_and_should_trigger_warnings():  # E501: line too long
    pass

class badClassName:  # N801: class name should use CapWords convention
    pass

try:
    risky_operation()
except:  # E722: bare except clause
    pass
```

### IDE Test
1. **Open file in IDE**
2. **Expected Result**: IDE should highlight violations with squiggly underlines
3. **Check Problems Panel**: Should show list of violations

### Manual Verification
```bash
# Test Flake8 manually
flake8 test_flake8.py
# Should show violations like:
# test_flake8.py:3:1: F401 'unused_module' imported but unused
# test_flake8.py:6:6: E225 missing whitespace around operator
```

## Test 3: Import Sorting Integration

### Create Test File
Create `test_isort.py` with messy imports:

```python
from lambda.index import handler
import json
from datetime import datetime
import os
import boto3
from typing import Dict, List
import sys
from lambda.orchestration_stepfunctions import start_execution
import logging
from scripts.add_current_account import main
```

### VS Code Test
1. **Open file in VS Code**
2. **Save file** (`Ctrl+S` / `Cmd+S`)
3. **Expected Result**: Imports should be automatically organized

### PyCharm Test
1. **Open file in PyCharm**
2. **Optimize imports** (`Ctrl+Alt+O` / `Cmd+Option+O`)
3. **Expected Result**: Imports should be organized

### Expected Output
After import sorting:
```python
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List

import boto3

from lambda.index import handler
from lambda.orchestration_stepfunctions import start_execution
from scripts.add_current_account import main
```

### Manual Verification
```bash
# Test isort manually
isort test_isort.py --diff
# Should show no changes if IDE sorting worked
```

## Test 4: Code Completion and IntelliSense

### Create Test File
Create `test_completion.py`:

```python
import boto3
from lambda.index import handler

def test_completion():
    # Test AWS SDK completion
    client = boto3.client('drs')
    # Type 'client.' and check for method completion
    
    # Test local module completion
    # Type 'handler.' and check for completion
    
    # Test standard library completion
    import json
    # Type 'json.' and check for method completion
```

### IDE Test
1. **Open file in IDE**
2. **Type `client.`** after the boto3 client line
3. **Expected Result**: Should show DRS client methods (describe_jobs, start_recovery, etc.)
4. **Type `json.`** after import
5. **Expected Result**: Should show JSON methods (loads, dumps, etc.)

## Test 5: Debugging Configuration

### Create Test File
Create `test_debug.py`:

```python
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_function(param1, param2):
    """Test function for debugging."""
    logger.info(f"Testing with {param1} and {param2}")
    
    result = {
        'param1': param1,
        'param2': param2,
        'sum': param1 + param2
    }
    
    return result

def main():
    """Main function for testing."""
    result1 = test_function(5, 10)
    result2 = test_function(20, 30)
    
    print(json.dumps(result1, indent=2))
    print(json.dumps(result2, indent=2))

if __name__ == "__main__":
    main()
```

### IDE Test
1. **Set breakpoint** on line with `result = {`
2. **Start debugging** (F5 or debug button)
3. **Expected Result**: 
   - Debugger should stop at breakpoint
   - Variables panel should show `param1` and `param2` values
   - Can step through code and inspect variables

## Test 6: Project-Specific Integration

### Test Lambda Function Editing
1. **Open `lambda/index.py`** in IDE
2. **Check syntax highlighting** for AWS SDK imports
3. **Test code completion** for boto3 methods
4. **Verify no import errors** for local modules

### Test Script Editing
1. **Open `scripts/add-current-account.py`** in IDE
2. **Check for linting violations** (should be minimal after fixes)
3. **Test code completion** for argparse and other modules

### Test Configuration Files
1. **Open `pyproject.toml`** in IDE
2. **Verify TOML syntax highlighting**
3. **Check for configuration errors**

## Test 7: Quality Tools Integration

### Run All Quality Checks
Create `test_quality.py`:

```python
"""Test file for quality checks."""

import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class QualityTestClass:
    """Test class for quality checks."""
    
    def __init__(self, name: str, config: Dict[str, str]) -> None:
        """Initialize test class."""
        self.name = name
        self.config = config
    
    def process_data(self, data: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Process data with proper type hints."""
        if not data:
            return None
        
        result = {
            'processed_count': len(data),
            'processor': self.name,
            'config': json.dumps(self.config)
        }
        
        logger.info(f"Processed {len(data)} items")
        return result


def main() -> None:
    """Main function with proper type hints."""
    processor = QualityTestClass(
        name="test_processor",
        config={"mode": "test", "debug": "true"}
    )
    
    test_data = [
        {"id": "1", "value": "test1"},
        {"id": "2", "value": "test2"}
    ]
    
    result = processor.process_data(test_data)
    if result:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

### IDE Integration Test
1. **Open file in IDE**
2. **Save file** - should auto-format with Black
3. **Check for linting issues** - should show none
4. **Verify import organization** - should be properly sorted

### Manual Quality Check
```bash
# Run all quality tools
black test_quality.py --check
isort test_quality.py --check-only
flake8 test_quality.py
# All should pass without issues
```

## Test 8: Error Handling and Recovery

### Create File with Errors
Create `test_errors.py`:

```python
# File with intentional errors for testing error handling
import nonexistent_module  # Import error

def function_with_syntax_error()
    print("Missing colon")  # Syntax error

def function_with_undefined_variable():
    return undefined_variable  # Name error

class TestClass:
    def method_with_indentation_error(self):
    print("Wrong indentation")  # Indentation error
```

### IDE Test
1. **Open file in IDE**
2. **Expected Results**:
   - Syntax errors should be highlighted immediately
   - Import errors should be shown
   - Undefined variables should be flagged
   - Indentation errors should be marked

### Error Recovery Test
1. **Fix each error one by one**
2. **Verify IDE updates** error highlighting in real-time
3. **Save file** and confirm no errors remain

## Test Results Checklist

### Black Formatter ✓
- [ ] Automatically formats code on save
- [ ] Respects 79-character line length
- [ ] Properly formats imports, functions, and classes
- [ ] Works with both VS Code and PyCharm

### Flake8 Linting ✓
- [ ] Shows PEP 8 violations in real-time
- [ ] Highlights unused imports and variables
- [ ] Flags overly complex functions
- [ ] Respects .flake8 configuration

### Import Sorting ✓
- [ ] Organizes imports automatically
- [ ] Groups standard library, third-party, and local imports
- [ ] Compatible with Black formatting
- [ ] Works on save or manual trigger

### Code Completion ✓
- [ ] AWS SDK methods and properties
- [ ] Local project modules and functions
- [ ] Standard library completions
- [ ] Type hints and documentation

### Debugging ✓
- [ ] Breakpoints work correctly
- [ ] Variable inspection available
- [ ] Step-through debugging functional
- [ ] Console output visible

### Project Integration ✓
- [ ] Lambda functions load without import errors
- [ ] Scripts and utilities accessible
- [ ] Configuration files properly highlighted
- [ ] Virtual environment recognized

## Troubleshooting Failed Tests

### If Black Formatting Fails
1. Check Black extension installation
2. Verify virtual environment activation
3. Check settings.json configuration
4. Test Black manually in terminal

### If Flake8 Linting Fails
1. Verify Flake8 extension installation
2. Check .flake8 configuration file
3. Test Flake8 manually in terminal
4. Check IDE Python interpreter setting

### If Import Sorting Fails
1. Check isort extension installation
2. Verify pyproject.toml configuration
3. Test isort manually in terminal
4. Check "organize imports on save" setting

### If Code Completion Fails
1. Check Python interpreter configuration
2. Verify PYTHONPATH includes project directories
3. Clear IDE caches and restart
4. Check for conflicting extensions

## Performance Verification

### Startup Time Test
1. **Close IDE completely**
2. **Open project** and time startup
3. **Expected**: Should open within 30 seconds
4. **If slow**: Check excluded directories and memory settings

### Real-time Analysis Test
1. **Make changes to large Python file**
2. **Check responsiveness** of syntax highlighting and linting
3. **Expected**: Updates should appear within 2-3 seconds
4. **If slow**: Consider excluding large directories or files

## Conclusion

After completing all tests successfully:

1. **Document any issues** encountered and solutions found
2. **Update IDE configuration** if needed
3. **Share results** with team members
4. **Update troubleshooting FAQ** with new solutions

Your IDE is properly configured when all tests pass and you can efficiently develop Python code with automatic formatting, linting, and intelligent code completion.

---

**Test Duration**: Approximately 30-45 minutes for complete verification

**Last Updated**: January 2026

**Next Review**: Update tests when new tools or IDE versions are adopted