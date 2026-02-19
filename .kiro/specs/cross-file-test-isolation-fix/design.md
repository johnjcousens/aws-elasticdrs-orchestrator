# Design Document: Complete Test Suite Fix

## Overview

This design provides a systematic approach to fixing all 165 test failures, 13 errors, and 50 warnings in the test suite. The solution uses established mock patterns from TEST_PATTERNS.md and addresses six distinct problem categories in priority order.

## Architecture

### Test Isolation Architecture

The test suite uses a three-tier fixture hierarchy for complete isolation:

```
Session Scope (once per test run)
├── capture_original_state - Baseline state capture
└── reset_all_module_state_session - Initial cleanup

Module Scope (once per test file)
├── cleanup_sys_modules_per_file - Module cleanup
├── cleanup_mocks_per_file - Mock cleanup
├── reset_environment_per_file - Environment restoration
├── reset_sys_path_per_file - Import path restoration
└── reset_all_module_state_per_file - Module state reset

Function Scope (before each test)
├── reset_environment_variables - Per-test env reset
├── reset_launch_config_globals - Launch config reset
├── set_launch_config_env_vars - Required env vars
├── reset_logger_state - Logging reset
├── reset_data_management_handler_state - Handler tables reset
├── reset_orchestration_handler_state - Handler tables reset
├── reset_execution_handler_state - Handler tables reset
├── reset_query_handler_state - Handler tables reset
├── reset_mock_state - Mock history cleanup
└── isolate_test_execution - AWS isolation
```

### Mock Pattern Architecture

All Lambda handlers use getter functions for DynamoDB tables:

```python
# Handler pattern (production code)
_protection_groups_table = None

def get_protection_groups_table():
    global _protection_groups_table
    if _protection_groups_table is None:
        _protection_groups_table = boto3.resource('dynamodb').Table(os.environ['PROTECTION_GROUPS_TABLE'])
    return _protection_groups_table
```
