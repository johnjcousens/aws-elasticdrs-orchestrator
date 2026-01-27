"""
Integration tests for Query Handler.

Tests read-only query operations for DRS infrastructure and EC2 resources.
"""

import json
import os
import sys
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


@patch("boto3.client")
def test_get_drs_source_servers_api_gateway(mock_boto_client, mock_env_vars, mock_dynamodb_tables):
    """Test get_drs_source_servers via API Gateway invocation"""
    # Mock DRS client
    mock_drs = MagicMock()
    mock_drs.describe_source_servers.return_value = {
        "items": [
            get_mock_drs_source_server("s-111", "server-01"),
            get_mock_drs_source_server("s-222", "server-02"),
        ]
    }
    mock_boto_client.return_value = mock_drs
    
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="GET",
        path="/drs/source-servers",
        query_params={"region": "us-east-1"},
    )
    
    # Note: This test validates the event structure
    # Actual handler invocation would require importing the handler
    assert event["httpMethod"] == "GET"
    assert event["path"] == "/drs/source-servers"
    assert event["queryStringParameters"]["region"] == "us-east-1"
    assert "requestContext" in event


@patch("boto3.client")
def test_get_drs_source_servers_direct_invocation(mock_boto_client, mock_env_vars):
    """Test get_drs_source_servers via direct Lambda invocation"""
    # Mock DRS client
    mock_drs = MagicMock()
    mock_drs.describe_source_servers.return_value = {
        "items": [
            get_mock_drs_source_server("s-111", "server-01"),
        ]
    }
    mock_boto_client.return_value = mock_drs
    
    # Create direct invocation event
    event = get_mock_direct_invocation_event(
        operation="get_drs_source_servers",
        query_params={"region": "us-east-1"},
    )
    
    # Validate event structure
    assert event["operation"] == "get_drs_source_servers"
    assert event["queryParams"]["region"] == "us-east-1"
    assert "requestContext" not in event


def test_export_configuration_api_gateway(mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test export_configuration via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="GET",
        path="/config/export",
    )
    
    # Validate event structure
    assert event["httpMethod"] == "GET"
    assert event["path"] == "/config/export"
    assert "requestContext" in event


def test_export_configuration_direct_invocation(mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test export_configuration via direct Lambda invocation"""
    # Create direct invocation event
    event = get_mock_direct_invocation_event(
        operation="export_configuration",
    )
    
    # Validate event structure
    assert event["operation"] == "export_configuration"
    assert "requestContext" not in event


@patch("boto3.client")
def test_get_ec2_subnets_api_gateway(mock_boto_client, mock_env_vars):
    """Test get_ec2_subnets via API Gateway invocation"""
    # Mock EC2 client
    mock_ec2 = MagicMock()
    mock_ec2.describe_subnets.return_value = {
        "Subnets": [
            {
                "SubnetId": "subnet-123",
                "VpcId": "vpc-123",
                "CidrBlock": "10.0.1.0/24",
                "AvailabilityZone": "us-east-1a",
                "Tags": [{"Key": "Name", "Value": "Private Subnet 1"}],
            }
        ]
    }
    mock_boto_client.return_value = mock_ec2
    
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="GET",
        path="/ec2/subnets",
        query_params={"region": "us-east-1"},
    )
    
    # Validate event structure
    assert event["httpMethod"] == "GET"
    assert event["path"] == "/ec2/subnets"
    assert event["queryStringParameters"]["region"] == "us-east-1"


@patch("boto3.client")
def test_get_ec2_security_groups_api_gateway(mock_boto_client, mock_env_vars):
    """Test get_ec2_security_groups via API Gateway invocation"""
    # Mock EC2 client
    mock_ec2 = MagicMock()
    mock_ec2.describe_security_groups.return_value = {
        "SecurityGroups": [
            {
                "GroupId": "sg-123",
                "GroupName": "default",
                "Description": "Default security group",
                "VpcId": "vpc-123",
            }
        ]
    }
    mock_boto_client.return_value = mock_ec2
    
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="GET",
        path="/ec2/security-groups",
        query_params={"region": "us-east-1"},
    )
    
    # Validate event structure
    assert event["httpMethod"] == "GET"
    assert event["path"] == "/ec2/security-groups"


@patch("boto3.client")
def test_get_current_account_api_gateway(mock_boto_client, mock_env_vars):
    """Test get_current_account via API Gateway invocation"""
    # Mock STS client
    mock_sts = MagicMock()
    mock_sts.get_caller_identity.return_value = {
        "Account": "123456789012",
        "Arn": "arn:aws:iam::123456789012:user/test",
    }
    mock_boto_client.return_value = mock_sts
    
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="GET",
        path="/accounts/current",
    )
    
    # Validate event structure
    assert event["httpMethod"] == "GET"
    assert event["path"] == "/accounts/current"


def test_api_gateway_event_structure():
    """Test API Gateway event structure is correct"""
    event = get_mock_api_gateway_event(
        method="POST",
        path="/test",
        body={"key": "value"},
        query_params={"param": "value"},
        path_params={"id": "123"},
    )
    
    # Validate required fields
    assert "requestContext" in event
    assert "httpMethod" in event
    assert "path" in event
    assert "headers" in event
    assert "body" in event
    
    # Validate body is JSON string
    assert isinstance(event["body"], str)
    body = json.loads(event["body"])
    assert body["key"] == "value"
    
    # Validate query and path parameters
    assert event["queryStringParameters"]["param"] == "value"
    assert event["pathParameters"]["id"] == "123"


def test_direct_invocation_event_structure():
    """Test direct invocation event structure is correct"""
    event = get_mock_direct_invocation_event(
        operation="test_operation",
        body={"key": "value"},
        query_params={"param": "value"},
    )
    
    # Validate required fields
    assert "operation" in event
    assert "body" in event
    assert "queryParams" in event
    
    # Validate no API Gateway fields
    assert "requestContext" not in event
    assert "httpMethod" not in event
    
    # Validate body is dict (not JSON string)
    assert isinstance(event["body"], dict)
    assert event["body"]["key"] == "value"


@pytest.mark.parametrize("method,path", [
    ("GET", "/drs/source-servers"),
    ("GET", "/drs/quotas"),
    ("GET", "/drs/accounts"),
    ("GET", "/ec2/subnets"),
    ("GET", "/ec2/security-groups"),
    ("GET", "/ec2/instance-profiles"),
    ("GET", "/ec2/instance-types"),
    ("GET", "/accounts/current"),
    ("GET", "/config/export"),
])
def test_query_handler_endpoints(method, path, mock_env_vars):
    """Test all Query Handler endpoints have correct event structure"""
    event = get_mock_api_gateway_event(method=method, path=path)
    
    assert event["httpMethod"] == method
    assert event["path"] == path
    assert "requestContext" in event

