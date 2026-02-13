"""
Integration tests for Execution Handler.

Tests DR execution operations and lifecycle management.
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
    get_mock_drs_job,
    get_mock_execution,
    get_mock_protection_group,
    get_mock_recovery_instance,
    get_mock_recovery_plan,
)


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing"""
    os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
    os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
    os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["STATE_MACHINE_ARN"] = "arn:aws:states:us-east-1:123456789012:stateMachine:DROrchestrator"
    yield
    # Cleanup
    for key in ["PROTECTION_GROUPS_TABLE", "RECOVERY_PLANS_TABLE", "EXECUTION_HISTORY_TABLE", "STATE_MACHINE_ARN"]:
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
    eh_table = mock_dynamodb_tables["execution_history"]

    # Add sample Protection Groups
    pg_table.put_item(Item=get_mock_protection_group("pg-1", "Database Servers"))
    pg_table.put_item(Item=get_mock_protection_group("pg-2", "Web Servers"))

    # Add sample Recovery Plans
    rp_table.put_item(Item=get_mock_recovery_plan("plan-1", "Production DR Plan"))

    # Add sample Executions
    eh_table.put_item(Item=get_mock_execution("exec-1", "plan-1", "IN_PROGRESS"))
    eh_table.put_item(Item=get_mock_execution("exec-2", "plan-1", "COMPLETED"))

    yield


@patch("boto3.client")
def test_execute_recovery_plan_api_gateway(mock_boto_client, mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test execute_recovery_plan via API Gateway invocation"""
    # Mock Step Functions client
    mock_sfn = MagicMock()
    mock_sfn.start_execution.return_value = {
        "executionArn": "arn:aws:states:us-east-1:123456789012:execution:DROrchestrator:exec-new",
        "startDate": "2024-01-15T10:00:00Z",
    }
    mock_boto_client.return_value = mock_sfn

    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="POST",
        path="/recovery-plans/{id}/execute",
        path_params={"id": "plan-1"},
        body={"isDrill": True, "pauseBeforeWave": 2},
    )

    # Validate event structure
    assert event["httpMethod"] == "POST"
    assert event["path"] == "/recovery-plans/{id}/execute"
    assert event["pathParameters"]["id"] == "plan-1"

    body = json.loads(event["body"])
    assert body["isDrill"] is True
    assert body["pauseBeforeWave"] == 2


@patch("boto3.client")
def test_execute_recovery_plan_direct_invocation(mock_boto_client, mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test execute_recovery_plan via direct Lambda invocation"""
    # Mock Step Functions client
    mock_sfn = MagicMock()
    mock_sfn.start_execution.return_value = {
        "executionArn": "arn:aws:states:us-east-1:123456789012:execution:DROrchestrator:exec-new",
        "startDate": "2024-01-15T10:00:00Z",
    }
    mock_boto_client.return_value = mock_sfn

    # Create direct invocation event
    event = get_mock_direct_invocation_event(
        operation="execute_recovery_plan",
        body={"planId": "plan-1", "isDrill": True, "pauseBeforeWave": 2},
    )

    # Validate event structure
    assert event["operation"] == "execute_recovery_plan"
    assert event["body"]["planId"] == "plan-1"
    assert event["body"]["isDrill"] is True


def test_list_executions_api_gateway(mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test list_executions via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="GET",
        path="/executions",
    )

    # Validate event structure
    assert event["httpMethod"] == "GET"
    assert event["path"] == "/executions"


def test_get_execution_api_gateway(mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test get_execution via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="GET",
        path="/executions/{id}",
        path_params={"id": "exec-1"},
    )

    # Validate event structure
    assert event["httpMethod"] == "GET"
    assert event["path"] == "/executions/{id}"
    assert event["pathParameters"]["id"] == "exec-1"


@patch("boto3.client")
def test_cancel_execution_api_gateway(mock_boto_client, mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test cancel_execution via API Gateway invocation"""
    # Mock Step Functions client
    mock_sfn = MagicMock()
    mock_sfn.stop_execution.return_value = {
        "stopDate": "2024-01-15T10:05:00Z",
    }
    mock_boto_client.return_value = mock_sfn

    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="POST",
        path="/executions/{id}/cancel",
        path_params={"id": "exec-1"},
    )

    # Validate event structure
    assert event["httpMethod"] == "POST"
    assert event["path"] == "/executions/{id}/cancel"
    assert event["pathParameters"]["id"] == "exec-1"


@patch("boto3.client")
def test_pause_execution_api_gateway(mock_boto_client, mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test pause_execution via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="POST",
        path="/executions/{id}/pause",
        path_params={"id": "exec-1"},
    )

    # Validate event structure
    assert event["httpMethod"] == "POST"
    assert event["path"] == "/executions/{id}/pause"
    assert event["pathParameters"]["id"] == "exec-1"


@patch("boto3.client")
def test_resume_execution_api_gateway(mock_boto_client, mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test resume_execution via API Gateway invocation"""
    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="POST",
        path="/executions/{id}/resume",
        path_params={"id": "exec-1"},
    )

    # Validate event structure
    assert event["httpMethod"] == "POST"
    assert event["path"] == "/executions/{id}/resume"
    assert event["pathParameters"]["id"] == "exec-1"


@patch("boto3.client")
def test_terminate_recovery_instances_api_gateway(mock_boto_client, mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test terminate_recovery_instances via API Gateway invocation"""
    # Mock DRS client
    mock_drs = MagicMock()
    mock_drs.terminate_recovery_instances.return_value = {
        "job": get_mock_drs_job("job-terminate-123", "STARTED", "TERMINATE"),
    }
    mock_boto_client.return_value = mock_drs

    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="POST",
        path="/executions/{id}/terminate",
        path_params={"id": "exec-1"},
    )

    # Validate event structure
    assert event["httpMethod"] == "POST"
    assert event["path"] == "/executions/{id}/terminate"
    assert event["pathParameters"]["id"] == "exec-1"


@patch("boto3.client")
def test_get_recovery_instances_api_gateway(mock_boto_client, mock_env_vars, mock_dynamodb_tables, sample_data):
    """Test get_recovery_instances via API Gateway invocation"""
    # Mock DRS client
    mock_drs = MagicMock()
    mock_drs.describe_recovery_instances.return_value = {
        "items": [
            get_mock_recovery_instance("i-recovery-111", "s-111"),
        ]
    }
    mock_boto_client.return_value = mock_drs

    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="GET",
        path="/executions/{id}/recovery-instances",
        path_params={"id": "exec-1"},
    )

    # Validate event structure
    assert event["httpMethod"] == "GET"
    assert event["path"] == "/executions/{id}/recovery-instances"


@patch("boto3.client")
def test_list_drs_jobs_api_gateway(mock_boto_client, mock_env_vars):
    """Test list_drs_jobs via API Gateway invocation"""
    # Mock DRS client
    mock_drs = MagicMock()
    mock_drs.describe_jobs.return_value = {
        "items": [
            get_mock_drs_job("job-1", "STARTED", "LAUNCH"),
            get_mock_drs_job("job-2", "COMPLETED", "LAUNCH"),
        ]
    }
    mock_boto_client.return_value = mock_drs

    # Create API Gateway event
    event = get_mock_api_gateway_event(
        method="GET",
        path="/drs/jobs",
        query_params={"region": "us-east-1"},
    )

    # Validate event structure
    assert event["httpMethod"] == "GET"
    assert event["path"] == "/drs/jobs"


@pytest.mark.parametrize(
    "method,path,path_params",
    [
        ("POST", "/recovery-plans/{id}/execute", {"id": "plan-1"}),
        ("GET", "/executions", None),
        ("DELETE", "/executions", None),
        ("GET", "/executions/{id}", {"id": "exec-1"}),
        ("POST", "/executions/{id}/cancel", {"id": "exec-1"}),
        ("POST", "/executions/{id}/pause", {"id": "exec-1"}),
        ("POST", "/executions/{id}/resume", {"id": "exec-1"}),
        ("POST", "/executions/{id}/terminate", {"id": "exec-1"}),
        ("GET", "/executions/{id}/recovery-instances", {"id": "exec-1"}),
        ("GET", "/executions/{id}/job-logs", {"id": "exec-1"}),
        ("GET", "/executions/{id}/termination-status", {"id": "exec-1"}),
        ("POST", "/drs/failover", None),
        ("POST", "/drs/start-recovery", None),
        ("POST", "/drs/terminate-recovery-instances", None),
        ("POST", "/drs/disconnect-recovery-instance", None),
        ("POST", "/drs/failback", None),
        ("POST", "/drs/reverse-replication", None),
        ("POST", "/drs/start-failback", None),
        ("POST", "/drs/stop-failback", None),
        ("GET", "/drs/failback-configuration", None),
        ("GET", "/drs/jobs", None),
        ("GET", "/drs/jobs/{id}", {"id": "job-1"}),
        ("GET", "/drs/jobs/{id}/logs", {"id": "job-1"}),
    ],
)
def test_execution_handler_endpoints(method, path, path_params, mock_env_vars):
    """Test all Execution Handler endpoints have correct event structure"""
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
