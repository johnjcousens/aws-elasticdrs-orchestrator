"""
Shared pytest fixtures for unit tests.

This module provides fixtures that ensure test isolation across all unit tests.
"""

import os
import pytest


@pytest.fixture(autouse=True)
def reset_launch_config_globals():
    """
    Reset launch config service global variables before each test.
    
    This fixture ensures test isolation by resetting the module-level
    DynamoDB resource and table references that are cached globally in
    the launch_config_service module.
    
    This is an autouse fixture that runs before every test automatically.
    """
    # Only reset if the module has been imported
    import sys
    if "shared.launch_config_service" in sys.modules:
        import shared.launch_config_service as lcs
        lcs._dynamodb = None
        lcs._protection_groups_table = None
    
    yield
    
    # Clean up after test
    if "shared.launch_config_service" in sys.modules:
        import shared.launch_config_service as lcs
        lcs._dynamodb = None
        lcs._protection_groups_table = None


@pytest.fixture(autouse=True)
def set_launch_config_env_vars():
    """
    Set required environment variables for launch config tests.
    
    This fixture ensures the PROTECTION_GROUPS_TABLE environment variable
    is set for tests that use the launch_config_service module.
    
    This is an autouse fixture that runs before every test automatically.
    """
    # Save original value if it exists
    original_value = os.environ.get("PROTECTION_GROUPS_TABLE")
    
    # Set test value
    os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups-table"
    
    yield
    
    # Restore original value or remove if it didn't exist
    if original_value is not None:
        os.environ["PROTECTION_GROUPS_TABLE"] = original_value
    elif "PROTECTION_GROUPS_TABLE" in os.environ:
        del os.environ["PROTECTION_GROUPS_TABLE"]


# ============================================================================
# Test Isolation Fixtures
# Added: 2024-02-11
# Purpose: Prevent global state leakage between tests
# ============================================================================

import os
import logging
import pytest


@pytest.fixture(autouse=True)
def reset_environment_variables():
    """
    Reset environment variables before and after each test.
    
    This prevents environment variable leakage between tests.
    """
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def reset_logger_state():
    """
    Reset logger state before each test.
    
    This prevents logger configuration and handlers from leaking between tests.
    """
    # Get root logger
    root_logger = logging.getLogger()
    
    # Store original state
    original_level = root_logger.level
    original_handlers = root_logger.handlers.copy()
    
    yield
    
    # Reset to original state
    root_logger.setLevel(original_level)
    root_logger.handlers = original_handlers


@pytest.fixture(autouse=True)
def reset_module_caches():
    """
    Reset module-level caches before each test.
    
    This prevents cached boto3 clients and DynamoDB tables from leaking between tests.
    """
    # Import modules that have global state
    import sys
    
    # Add lambda directory to path if not already there
    lambda_path = os.path.join(os.path.dirname(__file__), "../../lambda")
    if lambda_path not in sys.path:
        sys.path.insert(0, lambda_path)
    
    try:
        import shared.conflict_detection as conflict_detection
        # Reset conflict_detection global tables
        conflict_detection._protection_groups_table = None
        conflict_detection._recovery_plans_table = None
        conflict_detection._execution_history_table = None
    except ImportError:
        pass
    
    try:
        import sys
        # Reset data-management-handler if loaded
        if 'data-management-handler.index' in sys.modules:
            handler = sys.modules['data-management-handler.index']
            if hasattr(handler, '_target_accounts_table'):
                handler._target_accounts_table = None
            if hasattr(handler, '_tag_sync_config_table'):
                handler._tag_sync_config_table = None
    except (ImportError, AttributeError):
        pass
    
    yield


@pytest.fixture(autouse=True)
def reset_mock_state():
    """
    Reset mock call history before each test.
    
    This prevents mock call history from leaking between tests.
    """
    yield
    # Cleanup happens automatically with pytest's mock cleanup


@pytest.fixture(autouse=True)
def isolate_test_execution(monkeypatch):
    """
    Ensure complete test isolation by resetting all global state.
    
    This is a catch-all fixture that runs before every test to ensure
    no state leaks from previous tests.
    """
    # Set consistent test environment
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    
    # Ensure we're not using real AWS credentials
    monkeypatch.delenv('AWS_ACCESS_KEY_ID', raising=False)
    monkeypatch.delenv('AWS_SECRET_ACCESS_KEY', raising=False)
    monkeypatch.delenv('AWS_SESSION_TOKEN', raising=False)
    
    yield
