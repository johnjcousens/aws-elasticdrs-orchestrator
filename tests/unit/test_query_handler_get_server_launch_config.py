"""
Unit tests for query-handler get_server_launch_config operation.

Tests the direct invocation of get_server_launch_config operation
to retrieve individual server launch configurations from protection groups.
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


def test_get_server_launch_config_missing_group_id(
    lambda_context, mock_dynamodb_table
):
    """Test error when groupId is missing"""
    from index import lambda_handler

    # Create event without groupId
    event = {"operation": "get_server_launch_config", "serverId": "s-123"}

    # Invoke lambda_handler
    result = lambda_handler(event, lambda_context)

    # Verify error response
    assert "error" in result
    assert result["error"] == "MISSING_PARAMETER"
    assert "groupId and serverId are required" in result["message"]


def test_get_server_launch_config_missing_server_id(
    lambda_context, mock_dynamodb_table
):
    """Test error when serverId is missing"""
    from index import lambda_handler

    # Create event without serverId
    event = {"operation": "get_server_launch_config", "groupId": "pg-123"}

    # Invoke lambda_handler
    result = lambda_handler(event, lambda_context)

    # Verify error response
    assert "error" in result
    assert result["error"] == "MISSING_PARAMETER"
    assert "groupId and serverId are required" in result["message"]


def test_get_server_launch_config_protection_group_not_found(
    lambda_context, mock_dynamodb_table
):
    """Test error when protection group doesn't exist"""
    from index import lambda_handler

    # Mock DynamoDB to return no item
    mock_dynamodb_table.get_item.return_value = {}

    # Create event
    event = {
        "operation": "get_server_launch_config",
        "groupId": "pg-nonexistent",
        "serverId": "s-123",
    }

    # Invoke lambda_handler
    result = lambda_handler(event, lambda_context)

    # Verify error response
    assert "error" in result
    assert result["error"] == "NOT_FOUND"
    assert "Protection group pg-nonexistent not found" in result["message"]


def test_get_server_launch_config_server_not_found(
    lambda_context, mock_dynamodb_table
):
    """Test error when server is not in protection group"""
    from index import lambda_handler

    # Mock DynamoDB to return protection group without the server
    mock_dynamodb_table.get_item.return_value = {
        "Item": {
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-456", "s-789"],
            "servers": [],
        }
    }

    # Create event
    event = {
        "operation": "get_server_launch_config",
        "groupId": "pg-123",
        "serverId": "s-123",
    }

    # Invoke lambda_handler
    result = lambda_handler(event, lambda_context)

    # Verify error response
    assert "error" in result
    assert result["error"] == "NOT_FOUND"
    assert "Server s-123 not found in protection group pg-123" in result["message"]


def test_get_server_launch_config_server_uses_group_defaults(
    lambda_context, mock_dynamodb_table
):
    """Test server that exists but has no custom config (uses group defaults)"""
    from index import lambda_handler

    # Mock DynamoDB to return protection group with server in sourceServerIds
    # but not in servers array
    mock_dynamodb_table.get_item.return_value = {
        "Item": {
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-123", "s-456"],
            "servers": [],
            "launchConfig": {
                "instanceType": "t3.medium",
                "subnetId": "subnet-default",
            },
        }
    }

    # Create event
    event = {
        "operation": "get_server_launch_config",
        "groupId": "pg-123",
        "serverId": "s-123",
    }

    # Invoke lambda_handler
    result = lambda_handler(event, lambda_context)

    # Verify success response with group defaults
    assert "error" not in result
    assert result["serverId"] == "s-123"
    assert result["useGroupDefaults"] is True
    assert result["launchConfiguration"]["instanceType"] == "t3.medium"
    assert result["launchConfiguration"]["subnetId"] == "subnet-default"


def test_get_server_launch_config_server_with_custom_config(
    lambda_context, mock_dynamodb_table
):
    """Test server with custom launch configuration"""
    from index import lambda_handler

    # Mock DynamoDB to return protection group with server having custom config
    mock_dynamodb_table.get_item.return_value = {
        "Item": {
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-123", "s-456"],
            "servers": [
                {
                    "sourceServerId": "s-123",
                    "instanceId": "i-abc123",
                    "instanceName": "web-server-01",
                    "useGroupDefaults": False,
                    "launchTemplate": {
                        "instanceType": "c6a.xlarge",
                        "subnetId": "subnet-custom",
                        "securityGroupIds": ["sg-123", "sg-456"],
                        "staticPrivateIp": "10.0.1.100",
                    },
                    "tags": {"Environment": "production"},
                }
            ],
            "launchConfig": {
                "instanceType": "t3.medium",
                "subnetId": "subnet-default",
            },
        }
    }

    # Create event
    event = {
        "operation": "get_server_launch_config",
        "groupId": "pg-123",
        "serverId": "s-123",
    }

    # Invoke lambda_handler
    result = lambda_handler(event, lambda_context)

    # Verify success response with custom config
    assert "error" not in result
    assert result["serverId"] == "s-123"
    assert result["useGroupDefaults"] is False
    assert result["instanceId"] == "i-abc123"
    assert result["instanceName"] == "web-server-01"
    assert result["launchConfiguration"]["instanceType"] == "c6a.xlarge"
    assert result["launchConfiguration"]["subnetId"] == "subnet-custom"
    assert result["launchConfiguration"]["securityGroupIds"] == ["sg-123", "sg-456"]
    assert result["launchConfiguration"]["staticPrivateIp"] == "10.0.1.100"
    assert result["tags"]["Environment"] == "production"


def test_get_server_launch_config_minimal_custom_config(
    lambda_context, mock_dynamodb_table
):
    """Test server with minimal custom configuration"""
    from index import lambda_handler

    # Mock DynamoDB to return protection group with server having minimal config
    mock_dynamodb_table.get_item.return_value = {
        "Item": {
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-123"],
            "servers": [
                {
                    "sourceServerId": "s-123",
                    "useGroupDefaults": True,
                    "launchTemplate": {},
                }
            ],
        }
    }

    # Create event
    event = {
        "operation": "get_server_launch_config",
        "groupId": "pg-123",
        "serverId": "s-123",
    }

    # Invoke lambda_handler
    result = lambda_handler(event, lambda_context)

    # Verify success response
    assert "error" not in result
    assert result["serverId"] == "s-123"
    assert result["useGroupDefaults"] is True
    assert result["launchConfiguration"] == {}


def test_get_server_launch_config_dynamodb_error(
    lambda_context, mock_dynamodb_table
):
    """Test handling of DynamoDB errors"""
    from index import lambda_handler

    # Mock DynamoDB to raise an exception
    mock_dynamodb_table.get_item.side_effect = Exception("DynamoDB connection error")

    # Create event
    event = {
        "operation": "get_server_launch_config",
        "groupId": "pg-123",
        "serverId": "s-123",
    }

    # Invoke lambda_handler
    result = lambda_handler(event, lambda_context)

    # Verify error response
    assert "error" in result
    assert result["error"] == "INTERNAL_ERROR"
    assert "Failed to get server launch configuration" in result["message"]
