# IDE Troubleshooting FAQ

Common issues and solutions for IDE integration with Python coding standards in the AWS DRS Orchestration project.

## VS Code Issues

### Black Formatter Not Working

**Problem**: Black doesn't format code on save or shows "command not found" error.

**Solutions**:
1. **Check Black Installation**
   ```bash
   source venv/bin/activate
   pip list | grep black
   ```
   If not installed: `pip install black`

2. **Verify VS Code Extension**
   - Install "Black Formatter" extension (ms-python.black-formatter)
   - Restart VS Code after installation

3. **Check Settings Configuration**
   - Verify `.vscode/settings.json` has correct formatter settings
   - Ensure `python.defaultInterpreterPath` points to virtual environment

4. **Manual Test**
   ```bash
   source venv/bin/activate
   black --version
   black lambda/index.py --diff
   ```

### Flake8 Linting Not Showing

**Problem**: PEP 8 violations not highlighted in editor.

**Solutions**:
1. **Install Flake8 Extension**
   - Install "Flake8" extension (ms-python.flake8)
   - Reload VS Code window

2. **Check Flake8 Installation**
   ```bash
   source venv/bin/activate
   flake8 --version
   ```

3. **Verify Configuration**
   - Check `.flake8` file exists in project root
   - Verify VS Code settings enable flake8

4. **Test Manually**
   ```bash
   source venv/bin/activate
   flake8 lambda/index.py
   ```

### Import Sorting Not Working

**Problem**: isort doesn't organize imports on save.

**Solutions**:
1. **Install isort Extension**
   - Install "isort" extension (ms-python.isort)
   - Enable "source.organizeImports" in settings

2. **Check isort Installation**
   ```bash
   source venv/bin/activate
   isort --version
   ```

3. **Verify Configuration**
   - Check `pyproject.toml` has isort configuration
   - Ensure profile is set to "black"

4. **Manual Test**
   ```bash
   source venv/bin/activate
   isort lambda/index.py --diff
   ```

### Python Interpreter Not Found

**Problem**: VS Code can't find Python interpreter or shows wrong version.

**Solutions**:
1. **Select Correct Interpreter**
   - Press `Ctrl+Shift+P` (Cmd+Shift+P on macOS)
   - Type "Python: Select Interpreter"
   - Choose `./venv/bin/python`

2. **Check Virtual Environment**
   ```bash
   source venv/bin/activate
   which python
   python --version
   ```

3. **Reload VS Code**
   - Press `Ctrl+Shift+P` → "Developer: Reload Window"

### Code Completion Not Working

**Problem**: IntelliSense doesn't work for project modules.

**Solutions**:
1. **Check PYTHONPATH**
   - Verify `.vscode/settings.json` includes correct paths
   - Should include `./lambda` and `./scripts`

2. **Verify Source Roots**
   - Check `python.analysis.extraPaths` in settings
   - Reload window after changes

3. **Clear Cache**
   - Press `Ctrl+Shift+P` → "Python: Clear Cache and Reload Window"

## PyCharm Issues

### Black Plugin Not Working

**Problem**: Black plugin installed but not formatting code.

**Solutions**:
1. **Check Plugin Configuration**
   - Go to `Tools` → `Black`
   - Verify executable path: `./venv/bin/black`
   - Check "Trigger when saving changed files"

2. **Test Black Manually**
   ```bash
   source venv/bin/activate
   black --version
   ```

3. **Restart PyCharm**
   - Sometimes plugin needs restart to work properly

### Project Interpreter Issues

**Problem**: PyCharm doesn't recognize virtual environment or shows import errors.

**Solutions**:
1. **Configure Interpreter**
   - Go to `File` → `Settings` → `Project` → `Python Interpreter`
   - Click gear icon → `Add` → `Existing environment`
   - Select `./venv/bin/python`

2. **Mark Source Roots**
   - Right-click `lambda` folder → `Mark Directory as` → `Sources Root`
   - Right-click `scripts` folder → `Mark Directory as` → `Sources Root`

3. **Invalidate Caches**
   - Go to `File` → `Invalidate Caches and Restart`

### External Tools Not Working

**Problem**: Flake8 or isort external tools show "command not found".

**Solutions**:
1. **Check Tool Paths**
   - Go to `Tools` → `External Tools`
   - Verify program paths point to virtual environment
   - Use absolute paths: `/full/path/to/venv/bin/flake8`

2. **Test Tools Manually**
   ```bash
   source venv/bin/activate
   which flake8
   which isort
   ```

3. **Update Working Directory**
   - Set working directory to `$ProjectFileDir$`

## General Python Issues

### Virtual Environment Problems

**Problem**: Virtual environment not activating or packages not found.

**Solutions**:
1. **Recreate Virtual Environment**
   ```bash
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements-dev.txt
   ```

2. **Check Python Version**
   ```bash
   python3 --version  # Should be 3.12+
   ```

3. **Verify Activation**
   ```bash
   source venv/bin/activate
   which python  # Should show venv path
   ```

### Package Installation Issues

**Problem**: pip install fails or packages not found.

**Solutions**:
1. **Upgrade pip**
   ```bash
   source venv/bin/activate
   pip install --upgrade pip
   ```

2. **Check Network/Proxy**
   - If behind corporate firewall, configure pip proxy
   - Try: `pip install --trusted-host pypi.org --trusted-host pypi.python.org package-name`

3. **Use Requirements File**
   ```bash
   pip install -r requirements-dev.txt
   ```

### Import Errors in IDE

**Problem**: IDE shows import errors but code runs fine.

**Solutions**:
1. **Check PYTHONPATH**
   - Ensure lambda and scripts directories are in path
   - Add to IDE settings or environment variables

2. **Verify File Structure**
   - Check `__init__.py` files exist where needed
   - Verify relative imports are correct

3. **Restart Language Server**
   - VS Code: `Ctrl+Shift+P` → "Python: Restart Language Server"
   - PyCharm: Invalidate caches and restart

## Configuration Issues

### Settings Not Loading

**Problem**: IDE doesn't use project settings from `.vscode/settings.json`.

**Solutions**:
1. **Check File Location**
   - Ensure `.vscode/settings.json` is in project root
   - Verify JSON syntax is valid

2. **Reload Configuration**
   - VS Code: `Ctrl+Shift+P` → "Developer: Reload Window"
   - Check for syntax errors in settings file

3. **User vs Workspace Settings**
   - Workspace settings override user settings
   - Check both levels for conflicts

### Extension Conflicts

**Problem**: Multiple formatters or linters causing conflicts.

**Solutions**:
1. **Disable Conflicting Extensions**
   - Disable autopep8, yapf if using Black
   - Use only one formatter per language

2. **Check Extension Priority**
   - Verify `editor.defaultFormatter` is set correctly
   - Use extension-specific settings

3. **Clean Extension Install**
   - Uninstall all Python extensions
   - Restart IDE
   - Install only required extensions

## Performance Issues

### Slow IDE Performance

**Problem**: IDE is slow when working with Python files.

**Solutions**:
1. **Exclude Large Directories**
   - Add `venv`, `__pycache__`, `.pytest_cache` to exclusions
   - Update `.vscode/settings.json` or PyCharm exclusions

2. **Increase Memory**
   - PyCharm: `Help` → `Change Memory Settings` → 2048MB
   - VS Code: Usually handles memory automatically

3. **Disable Unused Features**
   - Turn off unused language servers
   - Disable unnecessary extensions

### Large File Issues

**Problem**: IDE struggles with large Python files.

**Solutions**:
1. **Split Large Files**
   - Refactor large modules into smaller ones
   - Follow single responsibility principle

2. **Adjust IDE Settings**
   - Increase file size limits
   - Disable real-time analysis for large files

## Testing Integration Issues

### pytest Not Working in IDE

**Problem**: Tests don't run from IDE or show import errors.

**Solutions**:
1. **Configure Test Runner**
   - VS Code: Set `python.testing.pytestEnabled` to true
   - PyCharm: Configure pytest as test runner

2. **Check Test Discovery**
   - Verify test files follow naming convention (`test_*.py`)
   - Check `__init__.py` files in test directories

3. **Set Working Directory**
   - Tests should run from project root
   - Configure test runner working directory

### Debug Configuration Issues

**Problem**: Debugging doesn't work or shows import errors.

**Solutions**:
1. **Check Launch Configuration**
   - Verify `.vscode/launch.json` has correct paths
   - Set PYTHONPATH in environment variables

2. **Test Debug Setup**
   - Set breakpoint in simple function
   - Run debug configuration
   - Check console for errors

## Getting Additional Help

### Log Files and Diagnostics

**VS Code**:
- View logs: `Help` → `Toggle Developer Tools` → Console
- Python extension logs: Output panel → Python

**PyCharm**:
- View logs: `Help` → `Show Log in Finder/Explorer`
- Check `idea.log` for errors

### Community Resources

- [VS Code Python Documentation](https://code.visualstudio.com/docs/python/python-tutorial)
- [PyCharm Python Documentation](https://www.jetbrains.com/help/pycharm/python.html)
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)

### Team Support

If issues persist:
1. Check with team members for similar experiences
2. Document the issue and solution for future reference
3. Update this FAQ with new solutions
4. Consider team-wide IDE configuration standardization

---

**Last Updated**: January 2026

**Contributing**: Please add new issues and solutions as you encounter them to help the team.