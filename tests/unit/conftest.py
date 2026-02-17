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
