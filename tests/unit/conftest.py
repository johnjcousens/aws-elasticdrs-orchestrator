"""
Global test configuration for unit tests.

This conftest.py provides session-scoped fixtures that set up mocks
BEFORE any tests run, preventing test isolation issues when running
tests in batch.

The key issue being solved:
- When tests run individually, each test's reset_mocks fixture works fine
- When tests run in batch, fixtures from different test files can interfere
- Module-level variables in shared modules get reset by one test's fixture
  while another test is trying to use them
- This causes "UnrecognizedClientException" because real AWS calls are made

Solution:
- Session-scoped fixture patches boto3 globally before ANY tests run
- All tests inherit these mocks automatically
- Individual test fixtures can still customize behavior as needed
"""

import pytest
from unittest.mock import MagicMock, patch
import os

# CRITICAL: Set moto's fake AWS credentials BEFORE any imports
# This must happen at module import time, not in a fixture
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Set environment variables before any imports
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-executions"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
os.environ["TAG_SYNC_CONFIG_TABLE"] = "test-tag-sync-config"


@pytest.fixture(scope="session")
def global_aws_mocks(request):
    """
    Session-scoped fixture that patches boto3 globally before any tests run.
    
    This prevents real AWS API calls during test execution and ensures
    consistent mock behavior across all tests, even when running in batch.
    
    IMPORTANT: This fixture is NOT auto-used because it conflicts with @mock_aws.
    Tests that don't use @mock_aws should explicitly request this fixture.
    Tests using @mock_aws should NOT use this fixture.
    
    The fixture:
    1. Creates mock DynamoDB resource and tables
    2. Patches boto3.resource() and boto3.client() globally
    3. Runs once at the start of the test session
    """
    # Create mock DynamoDB resource
    mock_dynamodb_resource = MagicMock()
    
    # Create mock tables with default behavior
    mock_table = MagicMock()
    mock_table.scan.return_value = {"Items": []}
    mock_table.get_item.return_value = {"Item": {}}
    mock_table.put_item.return_value = {}
    mock_table.query.return_value = {"Items": []}
    
    def get_table(table_name):
        """Return mock table for any table name"""
        return mock_table
    
    mock_dynamodb_resource.Table.side_effect = get_table
    
    # Create mock STS client
    mock_sts = MagicMock()
    mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
    
    # Create mock IAM client
    mock_iam = MagicMock()
    mock_iam.list_account_aliases.return_value = {"AccountAliases": ["test-account"]}
    
    # Create mock DRS client
    mock_drs = MagicMock()
    mock_drs.describe_source_servers.return_value = {"items": []}
    mock_drs.describe_jobs.return_value = {"items": []}
    
    def mock_client(service_name, **kwargs):
        """Return appropriate mock client based on service name"""
        if service_name == "sts":
            return mock_sts
        elif service_name == "iam":
            return mock_iam
        elif service_name == "drs":
            return mock_drs
        return MagicMock()
    
    def mock_resource(service_name, **kwargs):
        """Return appropriate mock resource based on service name"""
        if service_name == "dynamodb":
            return mock_dynamodb_resource
        return MagicMock()
    
    # Patch boto3 globally for the entire test session
    with patch("boto3.client", side_effect=mock_client) as mock_boto3_client, \
         patch("boto3.resource", side_effect=mock_resource) as mock_boto3_resource:
        
        # Import shared modules AFTER patching boto3
        import shared.conflict_detection
        import shared.account_utils
        
        # Import data-management-handler module
        import importlib
        data_management_handler = importlib.import_module("data-management-handler.index")
        
        # Set module-level dynamodb resource to our mock in all modules
        shared.conflict_detection.dynamodb = mock_dynamodb_resource
        shared.account_utils.dynamodb = mock_dynamodb_resource
        data_management_handler.dynamodb = mock_dynamodb_resource
        
        # Reset module-level table variables to None to force lazy initialization
        shared.conflict_detection._protection_groups_table = None
        shared.conflict_detection._recovery_plans_table = None
        shared.conflict_detection._execution_history_table = None
        shared.account_utils._dynamodb = None
        shared.account_utils._target_accounts_table = None
        data_management_handler._protection_groups_table = None
        data_management_handler._recovery_plans_table = None
        data_management_handler._executions_table = None
        data_management_handler._target_accounts_table = None
        data_management_handler._tag_sync_config_table = None
        
        yield {
            "dynamodb_resource": mock_dynamodb_resource,
            "mock_table": mock_table,
            "mock_sts": mock_sts,
            "mock_iam": mock_iam,
            "mock_drs": mock_drs,
            "mock_client": mock_boto3_client,
            "mock_resource": mock_boto3_resource,
        }


@pytest.fixture(autouse=True)
def reset_module_state():
    """
    Function-scoped fixture that resets module-level state between tests.
    
    This ensures each test starts with a clean slate while still using
    the global boto3 mocks from the session-scoped fixture.
    """
    import boto3
    
    # Clear boto3's internal client cache to prevent cross-test pollution
    # This is critical for @mock_aws to work properly in batch test runs
    if hasattr(boto3, 'DEFAULT_SESSION') and boto3.DEFAULT_SESSION is not None:
        boto3.DEFAULT_SESSION = None
    
    yield
    
    # Clear boto3 session after test to prevent state leakage
    if hasattr(boto3, 'DEFAULT_SESSION') and boto3.DEFAULT_SESSION is not None:
        boto3.DEFAULT_SESSION = None
    
    # Cleanup module state after test
    try:
        import shared.conflict_detection
        import shared.account_utils
        import importlib
        data_management_handler = importlib.import_module("data-management-handler.index")
        
        shared.conflict_detection.dynamodb = None
        shared.conflict_detection._protection_groups_table = None
        shared.conflict_detection._recovery_plans_table = None
        shared.conflict_detection._execution_history_table = None
        shared.account_utils._dynamodb = None
        shared.account_utils._target_accounts_table = None
        data_management_handler.dynamodb = None
        data_management_handler._protection_groups_table = None
        data_management_handler._recovery_plans_table = None
        data_management_handler._executions_table = None
        data_management_handler._target_accounts_table = None
        data_management_handler._tag_sync_config_table = None
    except (ImportError, AttributeError):
        # Module not imported yet or attributes don't exist - that's fine
        pass
