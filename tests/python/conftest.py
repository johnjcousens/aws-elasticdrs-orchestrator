"""
Pytest configuration and shared fixtures for execution engine tests.
"""
import os
import pytest
import boto3
from moto import mock_dynamodb, mock_stepfunctions, mock_sts, mock_ec2
from typing import Generator


# ============================================================================
# Environment Setup
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    
    # DynamoDB table names for testing
    os.environ["PROTECTION_GROUPS_TABLE"] = "protection-groups-test"
    os.environ["RECOVERY_PLANS_TABLE"] = "recovery-plans-test"
    os.environ["EXECUTION_HISTORY_TABLE"] = "execution-history-test"
    os.environ["STATE_MACHINE_ARN"] = "arn:aws:states:us-east-1:123456789012:stateMachine:test-state-machine"


# ============================================================================
# AWS Service Mocks
# ============================================================================

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture
def dynamodb_mock(aws_credentials) -> Generator:
    """Mock DynamoDB service."""
    with mock_dynamodb():
        yield boto3.resource("dynamodb", region_name="us-east-1")


@pytest.fixture
def stepfunctions_mock(aws_credentials) -> Generator:
    """Mock Step Functions service."""
    with mock_stepfunctions():
        yield boto3.client("stepfunctions", region_name="us-east-1")


@pytest.fixture
def sts_mock(aws_credentials) -> Generator:
    """Mock STS service for cross-account testing."""
    with mock_sts():
        yield boto3.client("sts", region_name="us-east-1")


@pytest.fixture
def ec2_mock(aws_credentials) -> Generator:
    """Mock EC2 service for health checks."""
    with mock_ec2():
        yield boto3.client("ec2", region_name="us-east-1")


# ============================================================================
# DynamoDB Table Fixtures
# ============================================================================

@pytest.fixture
def protection_groups_table(dynamodb_mock):
    """Create mock Protection Groups DynamoDB table."""
    table = dynamodb_mock.create_table(
        TableName="protection-groups-test",
        KeySchema=[{"AttributeName": "GroupId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "GroupId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST"
    )
    return table


@pytest.fixture
def recovery_plans_table(dynamodb_mock):
    """Create mock Recovery Plans DynamoDB table."""
    table = dynamodb_mock.create_table(
        TableName="recovery-plans-test",
        KeySchema=[{"AttributeName": "PlanId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "PlanId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST"
    )
    return table


@pytest.fixture
def execution_history_table(dynamodb_mock):
    """Create mock Execution History DynamoDB table."""
    table = dynamodb_mock.create_table(
        TableName="execution-history-test",
        KeySchema=[{"AttributeName": "ExecutionId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "ExecutionId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST"
    )
    return table


# ============================================================================
# Test Data Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup test data after each test."""
    yield
    # Cleanup happens automatically with moto mocks
    # For integration tests, add explicit cleanup here
