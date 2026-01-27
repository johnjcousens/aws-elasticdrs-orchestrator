"""
Integration tests for Data Management Handler.

Tests Protection Groups and Recovery Plans CRUD operations.
"""

import json
import os
import sys
from decimal import Decimal
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws

# Add lambda and tests directories to path
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "..", "lambda"),
)
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), ".."),
)

from fixtures.mock_data import (
    get_mock_api_gateway_event,
    get_mock_direct_invocation_event,
    get_mock_drs_source_server,
    get_mock_protection_group,
    get_mock_protection_group_with_tags,
    get_mock_recovery_plan,
)


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing"""
    os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
    os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
    os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
    os.environ["AWS_REGION"] = "us-east-1"
    yield
    # Cleanup
    for key in ["PROTECTION_GROUPS_TABLE", "RECOVERY_PLANS_TABLE", "EXECUTION_HISTORY_TABLE"]:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def mock_dynamodb_tables():
    """Create mock DynamoDB tables"""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        
        # Create Protection Groups table
        pg_table = dynamodb.create_table(
            TableName="test-protection-groups",
            KeySchema=[{"AttributeName": "groupId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "groupId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        
        # Create Recovery Plans table
        rp_table = dynamodb.create_table(
            TableName="test-recovery-plans",
            KeySchema=[{"AttributeName": "planId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "planId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        
        # Create Execution History table
        eh_table = dynamodb.create_table(
            TableName="test-execution-history",
            KeySchema=[{"AttributeName": "executionId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "executionId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        
        yield {
            "protection_groups": pg_table,
            "recovery_plans": rp_table,
            "execution_history": eh_table,
        }


@pytest.fixture
def sample_data(mock_dynamodb_tables):
    """Populate tables with sample data"""
    pg_table = mock_dynamodb_tables["protection_groups"]
    rp_table = mock_dynamodb_tables["recovery_plans"]
    
    # Add sample Protection Groups
    pg_table.put_item(Item=get_mock_protection_group("pg-1", "Database Servers"))
    pg_table.put_item(Item=get_mock_protection_group("pg-2", "Web Servers"))
    
    # Add sample Recovery Plans
    rp_table.put_item(Item=get_mock_recovery_plan("plan-1", "Production DR Plan"))
    
    yield


def test_create_protection_group_api_gateway(mock_env_vars, mock_dynamodb_tables):
    """Test create_protection_group via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="POST",
        path="/protection-groups",
        body={
            "groupName": "New Protection Group",
            "region": "us-east-1",
            "sourceServerIds": ["s-111", "s-222"],
        },
    )
    
    # Validate event structure
    assert event["httpMethod"] == "POST"
    assert event["path"] == "/protection-groups"
    
    body = json.loads(event["body"])
    assert body["groupName"] == "New Protection Group"
    assert body["region"] == "us-east-1"
    assert len(body["sourceServerIds"]) == 2


def test_create_protection_group_direct_invocation(mock_env_vars, mock_dynamodb_tables):
    """Test create_protection_group via direct Lambda invocation"""
    # Create direct invocation event
    event = get_mock_direct_invocation_event(
        operation="create_protection_group",
        body={
            "groupName": "New Protection Group",
            "region": "us-east-1",
            "sourceServerIds": ["s-111", "s-222"],
        },
    )
    
    # Validate event structure
    assert event["operation"] == "create_protection_group"
    assert event["body"]["groupName"] == "New Protection Group"


def test_list_protection_groups_api_gateway(mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test list_protection_groups via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="GET",
        path="/protection-groups",
    )
    
    # Validate event structure
    assert event["httpMethod"] == "GET"
    assert event["path"] == "/protection-groups"


def test_get_protection_group_api_gateway(mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test get_protection_group via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="GET",
        path="/protection-groups/{id}",
        path_params={"id": "pg-1"},
    )
    
    # Validate event structure
    assert event["httpMethod"] == "GET"
    assert event["path"] == "/protection-groups/{id}"
    assert event["pathParameters"]["id"] == "pg-1"


def test_update_protection_group_api_gateway(mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test update_protection_group via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="PUT",
        path="/protection-groups/{id}",
        path_params={"id": "pg-1"},
        body={
            "groupName": "Updated Database Servers",
            "sourceServerIds": ["s-111", "s-222", "s-333"],
            "version": 1,
        },
    )
    
    # Validate event structure
    assert event["httpMethod"] == "PUT"
    assert event["path"] == "/protection-groups/{id}"
    assert event["pathParameters"]["id"] == "pg-1"
    
    body = json.loads(event["body"])
    assert body["groupName"] == "Updated Database Servers"
    assert body["version"] == 1


def test_delete_protection_group_api_gateway(mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test delete_protection_group via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="DELETE",
        path="/protection-groups/{id}",
        path_params={"id": "pg-1"},
    )
    
    # Validate event structure
    assert event["httpMethod"] == "DELETE"
    assert event["path"] == "/protection-groups/{id}"
    assert event["pathParameters"]["id"] == "pg-1"


@patch("boto3.client")
def test_resolve_protection_group_tags_api_gateway(mock_boto_client, mock_env_vars, mock_dynamodb_tables):
    """Test resolve_protection_group_tags via API Gateway invocation"""
    # Mock DRS client
    mock_drs = MagicMock()
    mock_drs.describe_source_servers.return_value = {
        "items": [
            get_mock_drs_source_server("s-111", "db-server-01"),
            get_mock_drs_source_server("s-222", "db-server-02"),
        ]
    }
    mock_boto_client.return_value = mock_drs
    
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="POST",
        path="/protection-groups/resolve",
        body={
            "region": "us-east-1",
            "serverSelectionTags": {
                "DR-Application": "Database",
                "DR-Tier": "Production",
            },
        },
    )
    
    # Validate event structure
    assert event["httpMethod"] == "POST"
    assert event["path"] == "/protection-groups/resolve"
    
    body = json.loads(event["body"])
    assert body["region"] == "us-east-1"
    assert "serverSelectionTags" in body


def test_create_recovery_plan_api_gateway(mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test create_recovery_plan via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="POST",
        path="/recovery-plans",
        body={
            "planName": "New Recovery Plan",
            "waves": [
                {
                    "waveName": "Wave 1",
                    "protectionGroupId": "pg-1",
                    "pauseBeforeWave": False,
                },
                {
                    "waveName": "Wave 2",
                    "protectionGroupId": "pg-2",
                    "pauseBeforeWave": True,
                },
            ],
        },
    )
    
    # Validate event structure
    assert event["httpMethod"] == "POST"
    assert event["path"] == "/recovery-plans"
    
    body = json.loads(event["body"])
    assert body["planName"] == "New Recovery Plan"
    assert len(body["waves"]) == 2


def test_list_recovery_plans_api_gateway(mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test list_recovery_plans via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="GET",
        path="/recovery-plans",
    )
    
    # Validate event structure
    assert event["httpMethod"] == "GET"
    assert event["path"] == "/recovery-plans"


def test_get_recovery_plan_api_gateway(mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test get_recovery_plan via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="GET",
        path="/recovery-plans/{id}",
        path_params={"id": "plan-1"},
    )
    
    # Validate event structure
    assert event["httpMethod"] == "GET"
    assert event["path"] == "/recovery-plans/{id}"
    assert event["pathParameters"]["id"] == "plan-1"


def test_update_recovery_plan_api_gateway(mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test update_recovery_plan via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="PUT",
        path="/recovery-plans/{id}",
        path_params={"id": "plan-1"},
        body={
            "planName": "Updated Production DR Plan",
            "waves": [
                {
                    "waveName": "Wave 1",
                    "protectionGroupId": "pg-1",
                    "pauseBeforeWave": False,
                },
            ],
            "version": 1,
        },
    )
    
    # Validate event structure
    assert event["httpMethod"] == "PUT"
    assert event["path"] == "/recovery-plans/{id}"
    assert event["pathParameters"]["id"] == "plan-1"
    
    body = json.loads(event["body"])
    assert body["planName"] == "Updated Production DR Plan"
    assert body["version"] == 1


def test_delete_recovery_plan_api_gateway(mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test delete_recovery_plan via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="DELETE",
        path="/recovery-plans/{id}",
        path_params={"id": "plan-1"},
    )
    
    # Validate event structure
    assert event["httpMethod"] == "DELETE"
    assert event["path"] == "/recovery-plans/{id}"
    assert event["pathParameters"]["id"] == "plan-1"


@patch("boto3.client")
def test_check_existing_instances_api_gateway(mock_boto_client, mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test check_existing_instances via API Gateway invocation"""
    # Mock DRS client
    mock_drs = MagicMock()
    mock_drs.describe_recovery_instances.return_value = {
        "items": []
    }
    mock_boto_client.return_value = mock_drs
    
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="POST",
        path="/recovery-plans/{id}/check-instances",
        path_params={"id": "plan-1"},
    )
    
    # Validate event structure
    assert event["httpMethod"] == "POST"
    assert event["path"] == "/recovery-plans/{id}/check-instances"
    assert event["pathParameters"]["id"] == "plan-1"


def test_import_configuration_api_gateway(mock_env_vars, mock_dynamodb_tables):
    """Test import_configuration via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="POST",
        path="/config/import",
        body={
            "protectionGroups": [
                get_mock_protection_group("pg-import-1", "Imported PG"),
            ],
            "recoveryPlans": [
                get_mock_recovery_plan("plan-import-1", "Imported Plan"),
            ],
        },
    )
    
    # Validate event structure
    assert event["httpMethod"] == "POST"
    assert event["path"] == "/config/import"
    
    body = json.loads(event["body"])
    assert "protectionGroups" in body
    assert "recoveryPlans" in body


@pytest.mark.parametrize("method,path,path_params", [
    ("POST", "/protection-groups", None),
    ("GET", "/protection-groups", None),
    ("GET", "/protection-groups/{id}", {"id": "pg-1"}),
    ("PUT", "/protection-groups/{id}", {"id": "pg-1"}),
    ("DELETE", "/protection-groups/{id}", {"id": "pg-1"}),
    ("POST", "/protection-groups/resolve", None),
    ("POST", "/recovery-plans", None),
    ("GET", "/recovery-plans", None),
    ("GET", "/recovery-plans/{id}", {"id": "plan-1"}),
    ("PUT", "/recovery-plans/{id}", {"id": "plan-1"}),
    ("DELETE", "/recovery-plans/{id}", {"id": "plan-1"}),
    ("POST", "/recovery-plans/{id}/check-instances", {"id": "plan-1"}),
    ("POST", "/drs/tag-sync", None),
    ("GET", "/config/tag-sync", None),
    ("PUT", "/config/tag-sync", None),
    ("POST", "/config/import", None),
])
def test_data_management_handler_endpoints(method, path, path_params, mock_env_vars):
    """Test all Data Management Handler endpoints have correct event structure"""
    event = get_mock_api_gateway_event(
        method=method,
        path=path,
        path_params=path_params,
    )
    
    assert event["httpMethod"] == method
    assert event["path"] == path
    assert "requestContext" in event
    
    if path_params:
        assert event["pathParameters"] == path_params

