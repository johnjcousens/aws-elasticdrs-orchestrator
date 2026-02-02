"""
Pytest configuration for test suite.

This file sets up the Python path to allow tests to import from Lambda handlers
and shared modules.
"""

import sys
from pathlib import Path
import pytest
from moto import mock_aws

# Add Lambda root to sys.path so 'shared' can be imported as a module
lambda_root = Path(__file__).parent.parent / "lambda"
if str(lambda_root) not in sys.path:
    sys.path.insert(0, str(lambda_root))

# Note: Each test should add its specific handler path (query-handler, 
# data-management-handler, etc.) to avoid conflicts between handlers that 
# all have an index.py file.


@pytest.fixture(scope="function", autouse=True)
def clear_index_module():
    """
    Clear the 'index' module from sys.modules before each test.
    
    This prevents conflicts when different tests import 'index' from
    different Lambda handlers (query-handler, data-management-handler, etc.).
    """
    if "index" in sys.modules:
        del sys.modules["index"]
    yield
    # Clean up after test
    if "index" in sys.modules:
        del sys.modules["index"]


@pytest.fixture(scope="function", autouse=True)
def aws_credentials(monkeypatch):
    """Mocked AWS Credentials for moto."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture(scope="function", autouse=True)
def reset_moto():
    """Reset moto state between tests to prevent state leakage."""
    # This fixture runs before and after each test
    yield
    # Cleanup happens automatically when mock_aws decorator exits
