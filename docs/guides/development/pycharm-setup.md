# PyCharm IDE Setup for Python Coding Standards

This guide walks you through configuring PyCharm (Community or Professional) for the AWS DRS Orchestration project with automatic PEP 8 compliance.

## Prerequisites

- **PyCharm Community Edition** (FREE) or PyCharm Professional 2023.3 or later
- Python 3.12 installed
- Project virtual environment created (`python -m venv venv`)

## PyCharm Editions Comparison

### PyCharm Community Edition (FREE) ✅ Recommended
- **Cost**: Completely free
- **Python Support**: Full Python development support
- **Code Quality**: Black, Flake8, isort integration ✅
- **Debugging**: Full debugging capabilities ✅
- **Git Integration**: Complete version control ✅
- **Limitations**: No web development frameworks, no database tools, no remote development

### PyCharm Professional (Paid)
- **Cost**: $199/year (free for students/open source)
- **Additional Features**: Web frameworks, database tools, remote development, profiler
- **For This Project**: Professional features not needed for Python backend development

**Recommendation**: Use PyCharm Community Edition - it has everything needed for this project.

## Step 1: Project Interpreter Setup

1. **Open Project Settings**
   - Go to `File` → `Settings` (Windows/Linux) or `PyCharm` → `Preferences` (macOS)
   - Navigate to `Project: aws-drs-orchestration` → `Python Interpreter`

2. **Configure Virtual Environment**
   - Click the gear icon → `Add...`
   - Select `Existing environment`
   - Set interpreter path to: `./venv/bin/python` (macOS/Linux) or `.\venv\Scripts\python.exe` (Windows)
   - Click `OK`

## Step 2: Code Style Configuration

### Black Formatter Setup

1. **Install Black Plugin**
   - Go to `File` → `Settings` → `Plugins`
   - Search for "Black" and install the official Black plugin
   - Restart PyCharm when prompted

2. **Configure Black**
   - Go to `Tools` → `Black`
   - Set Black executable path: `./venv/bin/black` (or `.\venv\Scripts\black.exe` on Windows)
   - Arguments: `--line-length=79 --target-version=py312`
   - Check "Trigger when saving changed files"
   - Check "Trigger on code reformat"

### Python Code Style

1. **Navigate to Code Style Settings**
   - Go to `Editor` → `Code Style` → `Python`

2. **Configure Tabs and Indents**
   - Tab size: `4`
   - Indent: `4`
   - Continuation indent: `4`
   - Check "Use tab character": `No`

3. **Configure Wrapping and Braces**
   - Right margin (columns): `79`
   - Check "Wrap when typing reaches right margin"

4. **Configure Imports**
   - Go to `Editor` → `Code Style` → `Python` → `Imports`
   - Structure of "from" imports: `Leave as is`
   - Sort imports: `Alphabetically`
   - Check "Use 'from' imports for packages"

## Step 3: Linting Configuration

### Flake8 Setup

1. **Install Flake8 Plugin**
   - Go to `File` → `Settings` → `Plugins`
   - Search for "Flake8" and install
   - Restart PyCharm

2. **Configure Flake8**
   - Go to `Tools` → `External Tools`
   - Click `+` to add new tool
   - Name: `Flake8`
   - Program: `./venv/bin/flake8` (or `.\venv\Scripts\flake8.exe`)
   - Arguments: `$FilePath$`
   - Working directory: `$ProjectFileDir$`

### Built-in Inspections

1. **Configure Python Inspections**
   - Go to `Editor` → `Inspections`
   - Expand `Python`
   - Enable these inspections:
     - `PEP 8 coding style violation`
     - `PEP 8 naming convention violation`
     - `Unused import statement`
     - `Unused local variable`
     - `Function is too complex`

2. **Set Inspection Severity**
   - Set PEP 8 violations to `Warning` or `Error` as preferred
   - Set unused imports to `Warning`

## Step 4: Import Organization

### isort Integration

1. **Configure isort as External Tool**
   - Go to `Tools` → `External Tools`
   - Click `+` to add new tool
   - Name: `isort`
   - Program: `./venv/bin/isort` (or `.\venv\Scripts\isort.exe`)
   - Arguments: `--profile=black --line-length=79 $FilePath$`
   - Working directory: `$ProjectFileDir$`

2. **Create Keyboard Shortcut**
   - Go to `Keymap`
   - Search for "isort" in External Tools
   - Assign shortcut (e.g., `Ctrl+Alt+I`)

## Step 5: File Templates

### Python File Template

1. **Navigate to File Templates**
   - Go to `Editor` → `File and Code Templates`
   - Select `Python Script`

2. **Set Template Content**
```python
#!/usr/bin/env python3
"""
${NAME}.py

Description: Brief description of the module.

Author: ${USER}
Created: ${DATE}
"""

def main():
    """Main function."""
    pass


if __name__ == "__main__":
    main()
```

## Step 6: Run Configurations

### Lambda Function Debug Configuration

1. **Create New Configuration**
   - Go to `Run` → `Edit Configurations`
   - Click `+` → `Python`
   - Name: `Lambda Function Debug`
   - Script path: `./lambda/index.py`
   - Environment variables:
     - `PYTHONPATH`: `./lambda:./scripts`
     - `AWS_DEFAULT_REGION`: `us-east-1`

### Test Runner Configuration

1. **Configure pytest**
   - Go to `Run` → `Edit Configurations`
   - Click `+` → `Python tests` → `pytest`
   - Name: `All Tests`
   - Target: `Custom`
   - Additional Arguments: `-v --tb=short`
   - Working directory: `$PROJECT_DIR$`

## Step 7: Project Structure

### Source Roots Configuration

1. **Mark Directories as Source Roots**
   - Right-click on `lambda` folder → `Mark Directory as` → `Sources Root`
   - Right-click on `scripts` folder → `Mark Directory as` → `Sources Root`
   - Right-click on `tests` folder → `Mark Directory as` → `Test Sources Root`

### Excluded Directories

1. **Exclude Build Artifacts**
   - Right-click on `venv` folder → `Mark Directory as` → `Excluded`
   - Right-click on `__pycache__` folders → `Mark Directory as` → `Excluded`
   - Right-click on `.pytest_cache` → `Mark Directory as` → `Excluded`

## Step 8: Version Control Integration

### Git Configuration

1. **Configure Git**
   - Go to `Version Control` → `Git`
   - Verify Git executable path
   - Check "Use credential helper"

2. **Configure Changelists**
   - Go to `Version Control` → `Changelists`
   - Enable "Show dialog on adding files to VCS"

## Step 9: Productivity Features

### Live Templates

1. **Create Custom Live Templates**
   - Go to `Editor` → `Live Templates`
   - Click `+` → `Template Group` → Name: `AWS DRS`
   - Add templates for common patterns:

**Lambda Handler Template** (abbreviation: `handler`)
```python
def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Args:
        event: Lambda event data
        context: Lambda context object
        
    Returns:
        dict: Response with statusCode and body
    """
    try:
        # Implementation here
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Success'})
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### Code Completion

1. **Configure Auto-completion**
   - Go to `Editor` → `General` → `Code Completion`
   - Check "Match case"
   - Set completion delay to `0ms`
   - Check "Show suggestions as you type"

## Step 10: Keyboard Shortcuts

### Essential Shortcuts for Code Quality

| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Reformat Code | `Ctrl+Alt+L` | `Cmd+Option+L` |
| Optimize Imports | `Ctrl+Alt+O` | `Cmd+Option+O` |
| Run Black (custom) | `Ctrl+Alt+B` | `Cmd+Option+B` |
| Run isort (custom) | `Ctrl+Alt+I` | `Cmd+Option+I` |
| Show Inspection Results | `Alt+6` | `Option+6` |
| Next Error | `F2` | `F2` |
| Previous Error | `Shift+F2` | `Shift+F2` |

## Troubleshooting

### Common Issues

**Black not working:**
- Verify Black is installed in virtual environment: `./venv/bin/pip list | grep black`
- Check Black plugin is enabled in PyCharm plugins
- Verify executable path in Black settings

**Flake8 not showing violations:**
- Install flake8 in virtual environment: `./venv/bin/pip install flake8`
- Check external tool configuration
- Verify project interpreter is set correctly

**Import organization not working:**
- Install isort in virtual environment: `./venv/bin/pip install isort`
- Check isort external tool configuration
- Verify arguments include `--profile=black`

**Code completion not working:**
- Verify source roots are marked correctly
- Check PYTHONPATH includes lambda and scripts directories
- Invalidate caches: `File` → `Invalidate Caches and Restart`

### Performance Optimization

**Speed up PyCharm:**
- Increase heap size: `Help` → `Change Memory Settings` → Set to 2048MB
- Exclude large directories (venv, node_modules, .git)
- Disable unused plugins
- Enable "Power Save Mode" when not actively coding

## Verification Checklist

After setup, verify everything works:

- [ ] Black formats code on save
- [ ] Flake8 shows PEP 8 violations
- [ ] isort organizes imports correctly
- [ ] Code completion works for project modules
- [ ] Debug configurations run successfully
- [ ] Tests can be run from IDE
- [ ] Git integration shows file changes
- [ ] Live templates expand correctly

## Next Steps

1. **Team Onboarding**: Share this guide with team members
2. **Custom Configurations**: Adapt settings for team preferences
3. **Plugin Exploration**: Consider additional plugins for AWS development
4. **Workflow Integration**: Integrate with CI/CD pipeline checks

For additional help, see the [Development Workflow Guide](../guides/DEVELOPMENT_WORKFLOW_GUIDE.md) and [Troubleshooting Guide](../guides/TROUBLESHOOTING_GUIDE.md).