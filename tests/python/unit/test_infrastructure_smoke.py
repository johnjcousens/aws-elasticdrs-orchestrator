"""
Smoke test to verify test infrastructure is working correctly.
"""
import pytest
from hypothesis import given, strategies as st


@pytest.mark.unit
def test_pytest_working():
    """Verify pytest is working."""
    assert True


@pytest.mark.unit
def test_fixtures_available(dynamodb_mock):
    """Verify pytest fixtures are available."""
    assert dynamodb_mock is not None


@pytest.mark.unit
def test_dynamodb_table_creation(protection_groups_table):
    """Verify DynamoDB table fixtures work."""
    assert protection_groups_table.table_name == "protection-groups-test"


@pytest.mark.property
@given(x=st.integers())
def test_hypothesis_working(x):
    """Verify Hypothesis property-based testing works."""
    assert isinstance(x, int)


@pytest.mark.unit
def test_moto_mocking():
    """Verify moto AWS mocking works."""
    import boto3
    from moto import mock_dynamodb
    
    with mock_dynamodb():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-table",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        assert table.table_name == "test-table"
