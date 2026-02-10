"""
Unit Tests: Data Management Handler New Operations

Tests for new operations implemented in Phase 4:
- update_server_launch_config (Task 5.1)
- delete_server_launch_config (Task 5.2)
- bulk_update_server_configs (Task 5.3)
- validate_static_ip (Task 5.4)
- add_target_account (Task 5.5)
- update_target_account (Task 5.6)
- delete_target_account (Task 5.7)
- add_staging_account (Task 5.8)
- remove_staging_account (Task 5.9)
- trigger_tag_sync (Task 5.10)
- update_tag_sync_settings (Task 5.11)
- sync_extended_source_servers (Task 5.12)
- import_configuration (Task 5.13)

Requirements: 6.4, 6.5, 6.6, 6.11-6.19
"""

import json
import os
import sys
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timezone
from pathlib import Path
import importlib.util

import boto3
import pytest
from moto import mock_aws

# Set environment variables before importing handler
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
os.environ["TAG_SYNC_CONFIG_TABLE"] = "test-tag-sync-config"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Import from data-management-handler
spec = importlib.util.spec_from_file_location(
    "data_management_handler",
    Path(__file__).parent.parent.parent / "lambda" / "data-management-handler" / "index.py"
)
data_management_handler = importlib.util.module_from_spec(spec)
sys.modules['data_management_handler'] = data_management_handler
spec.loader.exec_module(data_management_handler)

# Import handler functions
update_server_launch_config = data_management_handler.update_server_launch_config
delete_server_launch_config = data_management_handler.delete_server_launch_config
bulk_update_server_launch_config = data_management_handler.bulk_update_server_launch_config
validate_server_static_ip = data_management_handler.validate_server_static_ip
create_target_account = data_management_handler.create_target_account
update_target_account = data_management_handler.update_target_account
delete_target_account = data_management_handler.delete_target_account
handle_add_staging_account = data_management_handler.handle_add_staging_account
handle_remove_staging_account = data_management_handler.handle_remove_staging_account
handle_sync_single_account = data_management_handler.handle_sync_single_account
handle_drs_tag_sync = data_management_handler.handle_drs_tag_sync
update_tag_sync_settings = data_management_handler.update_tag_sync_settings
import_configuration = data_management_handler.import_configuration
handle_direct_invocation = data_management_handler.handle_direct_invocation


def setup_dynamodb_tables():
    """Set up mock DynamoDB tables"""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Protection Groups table
    pg_table = dynamodb.create_table(
        TableName="test-protection-groups",
        KeySchema=[{"AttributeName": "groupId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "groupId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Target Accounts table
    ta_table = dynamodb.create_table(
        TableName="test-target-accounts",
        KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "accountId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Tag Sync Config table
    ts_table = dynamodb.create_table(
        TableName="test-tag-sync-config",
        KeySchema=[{"AttributeName": "configId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "configId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    return pg_table, ta_table, ts_table



# ============================================================================
# Tests for update_server_launch_config (Task 5.1)
# ============================================================================


@mock_aws
def test_update_server_launch_config_success():
    """Test updating server launch configuration successfully"""
    pg_table, _, _ = setup_dynamodb_tables()

    # Create test protection group
    pg_table.put_item(
        Item={
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-111", "s-222"],
            "servers": [],
        }
    )

    # Update server launch config
    body = {
        "instanceType": "t3.large",
        "targetSubnet": "subnet-abc123",
        "securityGroups": ["sg-111", "sg-222"],
    }

    result = update_server_launch_config("pg-123", "s-111", body)

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["serverId"] == "s-111"
    assert response_body["launchConfig"]["instanceType"] == "t3.large"


@mock_aws
def test_update_server_launch_config_protection_group_not_found():
    """Test updating server config when protection group doesn't exist"""
    setup_dynamodb_tables()

    body = {"instanceType": "t3.large"}

    result = update_server_launch_config("pg-nonexistent", "s-111", body)

    assert result["statusCode"] == 404
    response_body = json.loads(result["body"])
    assert "error" in response_body


@mock_aws
def test_update_server_launch_config_server_not_in_group():
    """Test updating config for server not in protection group"""
    pg_table, _, _ = setup_dynamodb_tables()

    pg_table.put_item(
        Item={
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-111"],
            "servers": [],
        }
    )

    body = {"instanceType": "t3.large"}

    result = update_server_launch_config("pg-123", "s-999", body)

    assert result["statusCode"] == 400
    response_body = json.loads(result["body"])
    assert "error" in response_body



# ============================================================================
# Tests for delete_server_launch_config (Task 5.2)
# ============================================================================


@mock_aws
def test_delete_server_launch_config_success():
    """Test deleting server launch configuration successfully"""
    pg_table, _, _ = setup_dynamodb_tables()

    # Create protection group with server config
    pg_table.put_item(
        Item={
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-111"],
            "servers": [
                {
                    "serverId": "s-111",
                    "launchConfig": {
                        "instanceType": "t3.large",
                        "targetSubnet": "subnet-abc123",
                    },
                }
            ],
        }
    )

    result = delete_server_launch_config("pg-123", "s-111")

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["message"] == "Server launch configuration deleted"


@mock_aws
def test_delete_server_launch_config_not_found():
    """Test deleting config when server has no custom config"""
    pg_table, _, _ = setup_dynamodb_tables()

    pg_table.put_item(
        Item={
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-111"],
            "servers": [],
        }
    )

    result = delete_server_launch_config("pg-123", "s-111")

    assert result["statusCode"] == 404
    response_body = json.loads(result["body"])
    assert "error" in response_body


# ============================================================================
# Tests for bulk_update_server_configs (Task 5.3)
# ============================================================================


@mock_aws
def test_bulk_update_server_configs_success():
    """Test bulk updating multiple server configurations"""
    pg_table, _, _ = setup_dynamodb_tables()

    pg_table.put_item(
        Item={
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-111", "s-222", "s-333"],
            "servers": [],
        }
    )

    body = {
        "servers": [
            {
                "serverId": "s-111",
                "launchConfig": {"instanceType": "t3.large"},
            },
            {
                "serverId": "s-222",
                "launchConfig": {"instanceType": "t3.xlarge"},
            },
        ]
    }

    result = bulk_update_server_launch_config("pg-123", body)

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["successCount"] == 2
    assert response_body["failureCount"] == 0


@mock_aws
def test_bulk_update_server_configs_partial_failure():
    """Test bulk update with some servers not in group"""
    pg_table, _, _ = setup_dynamodb_tables()

    pg_table.put_item(
        Item={
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-111"],
            "servers": [],
        }
    )

    body = {
        "servers": [
            {
                "serverId": "s-111",
                "launchConfig": {"instanceType": "t3.large"},
            },
            {
                "serverId": "s-999",  # Not in group
                "launchConfig": {"instanceType": "t3.xlarge"},
            },
        ]
    }

    result = bulk_update_server_launch_config("pg-123", body)

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["successCount"] == 1
    assert response_body["failureCount"] == 1



# ============================================================================
# Tests for validate_static_ip (Task 5.4)
# ============================================================================


@mock_aws
@patch("data_management_handler.index.create_ec2_client")
def test_validate_static_ip_success(mock_ec2_client):
    """Test validating static IP successfully"""
    pg_table, _, _ = setup_dynamodb_tables()

    pg_table.put_item(
        Item={
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-111"],
            "region": "us-east-1",
            "accountId": "123456789012",
        }
    )

    # Mock EC2 client
    mock_ec2 = MagicMock()
    mock_ec2.describe_subnets.return_value = {
        "Subnets": [{"CidrBlock": "10.0.1.0/24"}]
    }
    mock_ec2.describe_network_interfaces.return_value = {
        "NetworkInterfaces": []
    }
    mock_ec2_client.return_value = mock_ec2

    body = {
        "privateIpAddress": "10.0.1.50",
        "targetSubnet": "subnet-abc123",
    }

    result = validate_server_static_ip("pg-123", "s-111", body)

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["valid"] is True


@mock_aws
@patch("data_management_handler.index.create_ec2_client")
def test_validate_static_ip_already_in_use(mock_ec2_client):
    """Test validating IP that's already in use"""
    pg_table, _, _ = setup_dynamodb_tables()

    pg_table.put_item(
        Item={
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-111"],
            "region": "us-east-1",
            "accountId": "123456789012",
        }
    )

    # Mock EC2 client - IP already in use
    mock_ec2 = MagicMock()
    mock_ec2.describe_subnets.return_value = {
        "Subnets": [{"CidrBlock": "10.0.1.0/24"}]
    }
    mock_ec2.describe_network_interfaces.return_value = {
        "NetworkInterfaces": [{"PrivateIpAddress": "10.0.1.50"}]
    }
    mock_ec2_client.return_value = mock_ec2

    body = {
        "privateIpAddress": "10.0.1.50",
        "targetSubnet": "subnet-abc123",
    }

    result = validate_server_static_ip("pg-123", "s-111", body)

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["valid"] is False
    assert "already in use" in response_body["reason"]


# ============================================================================
# Tests for target account operations (Tasks 5.5-5.7)
# ============================================================================


@mock_aws
def test_create_target_account_success():
    """Test creating target account successfully"""
    _, ta_table, _ = setup_dynamodb_tables()

    body = {
        "accountId": "123456789012",
        "accountName": "Production Account",
        "roleArn": "arn:aws:iam::123456789012:role/DRSRole",
        "externalId": "external-123",
        "regions": ["us-east-1", "us-west-2"],
    }

    result = create_target_account(body)

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["accountId"] == "123456789012"
    assert response_body["accountName"] == "Production Account"


@mock_aws
def test_create_target_account_duplicate():
    """Test creating duplicate target account"""
    _, ta_table, _ = setup_dynamodb_tables()

    ta_table.put_item(
        Item={
            "accountId": "123456789012",
            "accountName": "Existing Account",
        }
    )

    body = {
        "accountId": "123456789012",
        "accountName": "Production Account",
        "roleArn": "arn:aws:iam::123456789012:role/DRSRole",
        "externalId": "external-123",
    }

    result = create_target_account(body)

    assert result["statusCode"] == 409
    response_body = json.loads(result["body"])
    assert "error" in response_body


@mock_aws
def test_update_target_account_success():
    """Test updating target account successfully"""
    _, ta_table, _ = setup_dynamodb_tables()

    ta_table.put_item(
        Item={
            "accountId": "123456789012",
            "accountName": "Old Name",
            "roleArn": "arn:aws:iam::123456789012:role/OldRole",
        }
    )

    body = {
        "accountName": "New Name",
        "roleArn": "arn:aws:iam::123456789012:role/NewRole",
    }

    result = update_target_account("123456789012", body)

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["accountName"] == "New Name"


@mock_aws
def test_delete_target_account_success():
    """Test deleting target account successfully"""
    _, ta_table, _ = setup_dynamodb_tables()

    ta_table.put_item(
        Item={
            "accountId": "123456789012",
            "accountName": "Test Account",
        }
    )

    result = delete_target_account("123456789012")

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert "deleted" in response_body["message"].lower()



# ============================================================================
# Tests for staging account operations (Tasks 5.8-5.9)
# ============================================================================


@mock_aws
def test_add_staging_account_success():
    """Test adding staging account successfully"""
    _, ta_table, _ = setup_dynamodb_tables()

    ta_table.put_item(
        Item={
            "accountId": "123456789012",
            "accountName": "Target Account",
            "stagingAccounts": [],
        }
    )

    body = {
        "targetAccountId": "123456789012",
        "stagingAccount": {
            "accountId": "444455556666",
            "accountName": "Staging Account",
            "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
            "externalId": "staging-123",
        },
    }

    result = handle_add_staging_account(body)

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert len(response_body["stagingAccounts"]) == 1


@mock_aws
def test_remove_staging_account_success():
    """Test removing staging account successfully"""
    _, ta_table, _ = setup_dynamodb_tables()

    ta_table.put_item(
        Item={
            "accountId": "123456789012",
            "accountName": "Target Account",
            "stagingAccounts": [
                {
                    "accountId": "444455556666",
                    "accountName": "Staging Account",
                }
            ],
        }
    )

    body = {
        "targetAccountId": "123456789012",
        "stagingAccountId": "444455556666",
    }

    result = handle_remove_staging_account(body)

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert len(response_body["stagingAccounts"]) == 0


# ============================================================================
# Tests for tag sync operations (Tasks 5.10-5.11)
# ============================================================================


@mock_aws
@patch("data_management_handler.index.create_drs_client")
@patch("data_management_handler.index.create_ec2_client")
def test_trigger_tag_sync_success(mock_ec2_client, mock_drs_client):
    """Test triggering tag sync successfully"""
    _, ta_table, ts_table = setup_dynamodb_tables()

    # Setup tag sync config
    ts_table.put_item(
        Item={
            "configId": "default",
            "enabled": True,
            "tagMappings": [{"ec2Tag": "Name", "drsTag": "Name"}],
        }
    )

    # Mock DRS and EC2 clients
    mock_drs = MagicMock()
    mock_drs.describe_source_servers.return_value = {
        "items": [{"sourceServerID": "s-111"}]
    }
    mock_drs_client.return_value = mock_drs

    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-111",
                        "Tags": [{"Key": "Name", "Value": "TestServer"}],
                    }
                ]
            }
        ]
    }
    mock_ec2_client.return_value = mock_ec2

    result = handle_drs_tag_sync({})

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert "syncedServers" in response_body


@mock_aws
def test_update_tag_sync_settings_success():
    """Test updating tag sync settings successfully"""
    _, _, ts_table = setup_dynamodb_tables()

    ts_table.put_item(
        Item={
            "configId": "default",
            "enabled": False,
        }
    )

    body = {
        "enabled": True,
        "tagMappings": [
            {"ec2Tag": "Name", "drsTag": "Name"},
            {"ec2Tag": "Environment", "drsTag": "Environment"},
        ],
    }

    result = update_tag_sync_settings(body)

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["enabled"] is True
    assert len(response_body["tagMappings"]) == 2



# ============================================================================
# Tests for sync_extended_source_servers (Task 5.12)
# ============================================================================


@mock_aws
@patch("data_management_handler.index.create_drs_client")
def test_sync_extended_source_servers_success(mock_drs_client):
    """Test syncing extended source servers successfully"""
    _, ta_table, _ = setup_dynamodb_tables()

    ta_table.put_item(
        Item={
            "accountId": "123456789012",
            "accountName": "Target Account",
            "stagingAccounts": [
                {
                    "accountId": "444455556666",
                    "accountName": "Staging Account",
                    "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
                }
            ],
        }
    )

    # Mock DRS client
    mock_drs = MagicMock()
    mock_drs.describe_source_servers.return_value = {
        "items": [
            {"sourceServerID": "s-111", "hostname": "server1"},
            {"sourceServerID": "s-222", "hostname": "server2"},
        ]
    }
    mock_drs_client.return_value = mock_drs

    result = handle_sync_single_account("123456789012")

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert "extendedSourceServers" in response_body


# ============================================================================
# Tests for import_configuration (Task 5.13)
# ============================================================================


@mock_aws
def test_import_configuration_success():
    """Test importing configuration successfully"""
    pg_table, _, _ = setup_dynamodb_tables()

    body = {
        "protectionGroups": [
            {
                "groupName": "Imported Group",
                "sourceServerIds": ["s-111", "s-222"],
                "region": "us-east-1",
                "accountId": "123456789012",
            }
        ],
        "recoveryPlans": [],
    }

    result = import_configuration(body)

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["importedProtectionGroups"] == 1


@mock_aws
def test_import_configuration_validation_error():
    """Test import with validation errors"""
    setup_dynamodb_tables()

    body = {
        "protectionGroups": [
            {
                # Missing required fields
                "groupName": "Invalid Group",
            }
        ],
    }

    result = import_configuration(body)

    assert result["statusCode"] == 400
    response_body = json.loads(result["body"])
    assert "error" in response_body


# ============================================================================
# Tests for direct invocation routing
# ============================================================================


@mock_aws
def test_direct_invocation_update_server_launch_config():
    """Test direct invocation of update_server_launch_config"""
    pg_table, _, _ = setup_dynamodb_tables()

    pg_table.put_item(
        Item={
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-111"],
            "servers": [],
        }
    )

    event = {
        "operation": "update_server_launch_config",
        "body": {
            "groupId": "pg-123",
            "serverId": "s-111",
            "instanceType": "t3.large",
        },
    }

    # Mock context
    context = MagicMock()
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"

    with patch("data_management_handler.index.validate_iam_authorization", return_value=True):
        with patch("data_management_handler.index.extract_iam_principal", return_value="test-role"):
            result = handle_direct_invocation(event, context)

    assert "error" not in result or result.get("statusCode") == 200


@mock_aws
def test_direct_invocation_delete_server_launch_config():
    """Test direct invocation of delete_server_launch_config"""
    pg_table, _, _ = setup_dynamodb_tables()

    pg_table.put_item(
        Item={
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-111"],
            "servers": [
                {
                    "serverId": "s-111",
                    "launchConfig": {"instanceType": "t3.large"},
                }
            ],
        }
    )

    event = {
        "operation": "delete_server_launch_config",
        "body": {
            "groupId": "pg-123",
            "serverId": "s-111",
        },
    }

    context = MagicMock()
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"

    with patch("data_management_handler.index.validate_iam_authorization", return_value=True):
        with patch("data_management_handler.index.extract_iam_principal", return_value="test-role"):
            result = handle_direct_invocation(event, context)

    assert "error" not in result or result.get("statusCode") == 200



@mock_aws
def test_direct_invocation_bulk_update_server_configs():
    """Test direct invocation of bulk_update_server_configs"""
    pg_table, _, _ = setup_dynamodb_tables()

    pg_table.put_item(
        Item={
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-111", "s-222"],
            "servers": [],
        }
    )

    event = {
        "operation": "bulk_update_server_configs",
        "body": {
            "groupId": "pg-123",
            "servers": [
                {
                    "serverId": "s-111",
                    "launchConfig": {"instanceType": "t3.large"},
                },
                {
                    "serverId": "s-222",
                    "launchConfig": {"instanceType": "t3.xlarge"},
                },
            ],
        },
    }

    context = MagicMock()
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"

    with patch("data_management_handler.index.validate_iam_authorization", return_value=True):
        with patch("data_management_handler.index.extract_iam_principal", return_value="test-role"):
            result = handle_direct_invocation(event, context)

    assert "error" not in result or result.get("statusCode") == 200


@mock_aws
def test_direct_invocation_add_target_account():
    """Test direct invocation of add_target_account"""
    setup_dynamodb_tables()

    event = {
        "operation": "add_target_account",
        "body": {
            "accountId": "123456789012",
            "accountName": "Test Account",
            "roleArn": "arn:aws:iam::123456789012:role/DRSRole",
            "externalId": "test-123",
        },
    }

    context = MagicMock()
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"

    with patch("data_management_handler.index.validate_iam_authorization", return_value=True):
        with patch("data_management_handler.index.extract_iam_principal", return_value="test-role"):
            result = handle_direct_invocation(event, context)

    assert "error" not in result or result.get("statusCode") == 200


@mock_aws
def test_direct_invocation_trigger_tag_sync():
    """Test direct invocation of trigger_tag_sync"""
    _, _, ts_table = setup_dynamodb_tables()

    ts_table.put_item(
        Item={
            "configId": "default",
            "enabled": True,
            "tagMappings": [],
        }
    )

    event = {
        "operation": "trigger_tag_sync",
        "body": {},
    }

    context = MagicMock()
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"

    with patch("data_management_handler.index.create_drs_client"):
        with patch("data_management_handler.index.create_ec2_client"):
            with patch("data_management_handler.index.validate_iam_authorization", return_value=True):
                with patch("data_management_handler.index.extract_iam_principal", return_value="test-role"):
                    result = handle_direct_invocation(event, context)

    assert "error" not in result or result.get("statusCode") == 200


@mock_aws
def test_direct_invocation_invalid_operation():
    """Test direct invocation with invalid operation"""
    setup_dynamodb_tables()

    event = {
        "operation": "invalid_operation",
        "body": {},
    }

    context = MagicMock()
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"

    with patch("data_management_handler.index.validate_iam_authorization", return_value=True):
        with patch("data_management_handler.index.extract_iam_principal", return_value="test-role"):
            result = handle_direct_invocation(event, context)

    assert "error" in result
    assert result["error"] == "UNKNOWN_OPERATION"


# ============================================================================
# Tests for parameter validation
# ============================================================================


@mock_aws
def test_update_server_launch_config_missing_parameters():
    """Test update with missing required parameters"""
    setup_dynamodb_tables()

    body = {}  # Missing all parameters

    result = update_server_launch_config("pg-123", "s-111", body)

    assert result["statusCode"] == 400
    response_body = json.loads(result["body"])
    assert "error" in response_body


@mock_aws
def test_bulk_update_missing_servers_array():
    """Test bulk update with missing servers array"""
    pg_table, _, _ = setup_dynamodb_tables()

    pg_table.put_item(
        Item={
            "groupId": "pg-123",
            "groupName": "Test Group",
            "sourceServerIds": ["s-111"],
        }
    )

    body = {}  # Missing servers array

    result = bulk_update_server_launch_config("pg-123", body)

    assert result["statusCode"] == 400
    response_body = json.loads(result["body"])
    assert "error" in response_body


@mock_aws
def test_create_target_account_missing_required_fields():
    """Test creating target account with missing required fields"""
    setup_dynamodb_tables()

    body = {
        "accountId": "123456789012",
        # Missing accountName, roleArn, externalId
    }

    result = create_target_account(body)

    assert result["statusCode"] == 400
    response_body = json.loads(result["body"])
    assert "error" in response_body


# ============================================================================
# Tests for error handling
# ============================================================================


@mock_aws
def test_update_server_launch_config_dynamodb_error():
    """Test handling DynamoDB errors"""
    setup_dynamodb_tables()

    body = {"instanceType": "t3.large"}

    with patch("data_management_handler.index.protection_groups_table") as mock_table:
        mock_table.get_item.side_effect = Exception("DynamoDB error")

        result = update_server_launch_config("pg-123", "s-111", body)

        assert result["statusCode"] == 500
        response_body = json.loads(result["body"])
        assert "error" in response_body


@mock_aws
def test_delete_target_account_not_found():
    """Test deleting non-existent target account"""
    setup_dynamodb_tables()

    result = delete_target_account("999999999999")

    assert result["statusCode"] == 404
    response_body = json.loads(result["body"])
    assert "error" in response_body
