"""
Unit tests for query-handler get_server_config_history operation.

Tests the get_server_config_history_direct function which retrieves
configuration change audit history for a specific server within a
protection group.

Test Coverage:
- Success case: Valid groupId and serverId
- Error case: Missing groupId parameter
- Error case: Missing serverId parameter
- Error case: Missing both parameters
- Error case: Protection group not found
- Error case: Server not found in protection group
- Edge case: Server in sourceServerIds but not in servers array
- Edge case: Server in servers array with custom config
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Set environment variables before importing
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups-table"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans-table"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts-table"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history-table"
os.environ["EXECUTION_HANDLER_ARN"] = (
    "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
)

# Clear any existing index module to avoid conflicts
if "index" in sys.modules:
    del sys.modules["index"]

# Add lambda paths for imports - query-handler FIRST
query_handler_dir = (
    Path(__file__).parent.parent.parent / "lambda" / "query-handler"
)
shared_dir = Path(__file__).parent.parent.parent / "lambda" / "shared"

sys.path.insert(0, str(query_handler_dir))
sys.path.insert(1, str(shared_dir))


@pytest.fixture
def lambda_context():
    """Mock Lambda context"""
    context = MagicMock()
    context.function_name = "query-handler"
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
    )
    return context


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table"""
    with patch("index.protection_groups_table") as mock_table:
        yield mock_table


@pytest.fixture
def sample_protection_group():
    """Sample protection group with servers"""
    return {
        "groupId": "pg-abc123",
        "name": "Test Protection Group",
        "sourceServerIds": [
            "s-1234567890abcdef0",
            "s-1234567890abcdef1",
        ],
        "servers": [
            {
                "sourceServerId": "s-1234567890abcdef0",
                "instanceName": "web-server-01",
                "useGroupDefaults": False,
                "launchTemplate": {
                    "instanceType": "t3.medium",
                    "subnetId": "subnet-123",
                    "securityGroupIds": ["sg-123"],
                },
            }
        ],
        "launchConfig": {
            "instanceType": "t3.small",
            "subnetId": "subnet-default",
            "securityGroupIds": ["sg-default"],
        },
    }


def test_get_server_config_history_success(
    lambda_context, mock_dynamodb_table, sample_protection_group
):
    """Test successful retrieval of server config history"""
    from index import lambda_handler

    # Mock DynamoDB to return protection group
    mock_dynamodb_table.get_item.return_value = {"Item": sample_protection_group}

    event = {
        "operation": "get_server_config_history",
        "groupId": "pg-abc123",
        "serverId": "s-1234567890abcdef0",
    }

    # Act
    result = lambda_handler(event, lambda_context)

    # Assert
    assert "error" not in result
    assert result["serverId"] == "s-1234567890abcdef0"
    assert result["groupId"] == "pg-abc123"
    assert "history" in result
    assert isinstance(result["history"], list)
    assert len(result["history"]) == 0  # Empty until feature implemented
    assert "note" in result
    assert "not yet implemented" in result["note"]

    # Verify DynamoDB was called correctly
    mock_dynamodb_table.get_item.assert_called_once_with(
        Key={"groupId": "pg-abc123"}
    )


def test_get_server_config_history_missing_group_id(
    lambda_context, mock_dynamodb_table
):
    """Test error when groupId is missing"""
    from index import lambda_handler

    event = {
        "operation": "get_server_config_history",
        "serverId": "s-1234567890abcdef0",
    }

    # Act
    result = lambda_handler(event, lambda_context)

    # Assert
    assert result["error"] == "MISSING_PARAMETER"
    assert "groupId and serverId are required" in result["message"]

    # Verify DynamoDB was not called
    mock_dynamodb_table.get_item.assert_not_called()


def test_get_server_config_history_missing_server_id(
    lambda_context, mock_dynamodb_table
):
    """Test error when serverId is missing"""
    from index import lambda_handler

    event = {
        "operation": "get_server_config_history",
        "groupId": "pg-abc123",
    }

    # Act
    result = lambda_handler(event, lambda_context)

    # Assert
    assert result["error"] == "MISSING_PARAMETER"
    assert "groupId and serverId are required" in result["message"]

    # Verify DynamoDB was not called
    mock_dynamodb_table.get_item.assert_not_called()


def test_get_server_config_history_missing_both_parameters(
    lambda_context, mock_dynamodb_table
):
    """Test error when both parameters are missing"""
    from index import lambda_handler

    event = {
        "operation": "get_server_config_history",
    }

    # Act
    result = lambda_handler(event, lambda_context)

    # Assert
    assert result["error"] == "MISSING_PARAMETER"
    assert "groupId and serverId are required" in result["message"]

    # Verify DynamoDB was not called
    mock_dynamodb_table.get_item.assert_not_called()


def test_get_server_config_history_group_not_found(
    lambda_context, mock_dynamodb_table
):
    """Test error when protection group is not found"""
    from index import lambda_handler

    # Mock DynamoDB to return no item
    mock_dynamodb_table.get_item.return_value = {}

    event = {
        "operation": "get_server_config_history",
        "groupId": "pg-nonexistent",
        "serverId": "s-1234567890abcdef0",
    }

    # Act
    result = lambda_handler(event, lambda_context)

    # Assert
    assert result["error"] == "NOT_FOUND"
    assert "Protection group pg-nonexistent not found" in result["message"]

    # Verify DynamoDB was called
    mock_dynamodb_table.get_item.assert_called_once_with(
        Key={"groupId": "pg-nonexistent"}
    )


def test_get_server_config_history_server_not_found(
    lambda_context, mock_dynamodb_table, sample_protection_group
):
    """Test error when server is not found in protection group"""
    from index import lambda_handler

    # Mock DynamoDB to return protection group
    mock_dynamodb_table.get_item.return_value = {"Item": sample_protection_group}

    event = {
        "operation": "get_server_config_history",
        "groupId": "pg-abc123",
        "serverId": "s-nonexistent",
    }

    # Act
    result = lambda_handler(event, lambda_context)

    # Assert
    assert result["error"] == "NOT_FOUND"
    assert (
        "Server s-nonexistent not found in protection group pg-abc123"
        in result["message"]
    )


def test_get_server_config_history_server_in_source_server_ids_only(
    lambda_context, mock_dynamodb_table
):
    """Test success when server is in sourceServerIds but not in servers array"""
    from index import lambda_handler

    # Protection group with server in sourceServerIds only
    protection_group = {
        "groupId": "pg-abc123",
        "name": "Test Protection Group",
        "sourceServerIds": [
            "s-1234567890abcdef0",
            "s-1234567890abcdef1",
        ],
        "servers": [],  # Empty servers array
        "launchConfig": {
            "instanceType": "t3.small",
        },
    }

    mock_dynamodb_table.get_item.return_value = {"Item": protection_group}

    event = {
        "operation": "get_server_config_history",
        "groupId": "pg-abc123",
        "serverId": "s-1234567890abcdef1",
    }

    # Act
    result = lambda_handler(event, lambda_context)

    # Assert
    assert "error" not in result
    assert result["serverId"] == "s-1234567890abcdef1"
    assert result["groupId"] == "pg-abc123"
    assert "history" in result
    assert isinstance(result["history"], list)


def test_get_server_config_history_server_with_custom_config(
    lambda_context, mock_dynamodb_table, sample_protection_group
):
    """Test success when server has custom configuration"""
    from index import lambda_handler

    # Mock DynamoDB to return protection group
    mock_dynamodb_table.get_item.return_value = {"Item": sample_protection_group}

    event = {
        "operation": "get_server_config_history",
        "groupId": "pg-abc123",
        "serverId": "s-1234567890abcdef0",
    }

    # Act
    result = lambda_handler(event, lambda_context)

    # Assert
    assert "error" not in result
    assert result["serverId"] == "s-1234567890abcdef0"
    assert result["groupId"] == "pg-abc123"
    assert "history" in result


def test_get_server_config_history_empty_group_id(
    lambda_context, mock_dynamodb_table
):
    """Test error when groupId is empty string"""
    from index import lambda_handler

    event = {
        "operation": "get_server_config_history",
        "groupId": "",
        "serverId": "s-1234567890abcdef0",
    }

    # Act
    result = lambda_handler(event, lambda_context)

    # Assert
    assert result["error"] == "MISSING_PARAMETER"
    assert "groupId and serverId are required" in result["message"]


def test_get_server_config_history_empty_server_id(
    lambda_context, mock_dynamodb_table
):
    """Test error when serverId is empty string"""
    from index import lambda_handler

    event = {
        "operation": "get_server_config_history",
        "groupId": "pg-abc123",
        "serverId": "",
    }

    # Act
    result = lambda_handler(event, lambda_context)

    # Assert
    assert result["error"] == "MISSING_PARAMETER"
    assert "groupId and serverId are required" in result["message"]


def test_get_server_config_history_dynamodb_exception(
    lambda_context, mock_dynamodb_table
):
    """Test error handling when DynamoDB raises exception"""
    from index import lambda_handler

    # Mock DynamoDB to raise exception
    mock_dynamodb_table.get_item.side_effect = Exception(
        "DynamoDB connection error"
    )

    event = {
        "operation": "get_server_config_history",
        "groupId": "pg-abc123",
        "serverId": "s-1234567890abcdef0",
    }

    # Act
    result = lambda_handler(event, lambda_context)

    # Assert
    assert result["error"] == "INTERNAL_ERROR"
    assert "Failed to get server configuration history" in result["message"]
    assert "DynamoDB connection error" in result["message"]
