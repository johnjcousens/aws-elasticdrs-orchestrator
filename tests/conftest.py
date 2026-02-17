"""
Pytest configuration for test suite.

This file sets up the Python path to allow tests to import from Lambda handlers
and shared modules.
"""

import os
import sys
from pathlib import Path
import pytest
from moto import mock_aws
from hypothesis import settings, Verbosity

# Configure Hypothesis for faster test runs
# This applies to ALL property-based tests in the test suite
settings.register_profile(
    "ci",
    max_examples=15,  # Reduced from default 100
    deadline=5000,    # 5 second deadline per example
    verbosity=Verbosity.normal,
)
settings.register_profile(
    "dev",
    max_examples=10,  # Fast for development
    deadline=5000,
    verbosity=Verbosity.normal,
)
settings.register_profile(
    "debug",
    max_examples=5,   # Minimal for debugging
    deadline=None,    # No deadline for debugging
    verbosity=Verbosity.verbose,
)

# Use 'dev' profile by default for faster test runs
# Can be overridden with: pytest --hypothesis-profile=ci
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))

# CRITICAL: Set environment variables BEFORE any imports
# This ensures global variables in shared modules are initialized correctly
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SECURITY_TOKEN", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("TARGET_ACCOUNTS_TABLE", "test-target-accounts-table")
os.environ.setdefault("STAGING_ACCOUNTS_TABLE", "test-staging-accounts-table")
os.environ.setdefault("PROTECTION_GROUPS_TABLE", "test-protection-groups-table")
os.environ.setdefault("RECOVERY_PLANS_TABLE", "test-recovery-plans-table")
os.environ.setdefault("EXECUTION_HISTORY_TABLE", "test-execution-history-table")
os.environ.setdefault("TAG_SYNC_CONFIG_TABLE", "test-tag-sync-config-table")

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
    # Set DynamoDB table names for tests
    monkeypatch.setenv("TARGET_ACCOUNTS_TABLE", "test-target-accounts-table")
    monkeypatch.setenv("STAGING_ACCOUNTS_TABLE", "test-staging-accounts-table")
    monkeypatch.setenv("PROTECTION_GROUPS_TABLE", "test-protection-groups-table")
    monkeypatch.setenv("RECOVERY_PLANS_TABLE", "test-recovery-plans-table")


@pytest.fixture(scope="function", autouse=True)
def reset_moto():
    """Reset moto state between tests to prevent state leakage."""
    # This fixture runs before and after each test
    yield
    # Cleanup happens automatically when mock_aws decorator exits
