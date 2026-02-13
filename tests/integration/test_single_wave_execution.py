"""
Integration test for single-wave execution lifecycle.

Tests the complete flow of a single-wave DR execution from creation
through polling to finalization, verifying that execution status
transitions correctly and server data is enriched.
"""

import json
import os
import sys
import time
from decimal import Decimal
from unittest.mock import Mock, patch

import boto3
import pytest
from moto import mock_aws

# Add lambda directory to path
lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
sys.path.insert(0, os.path.join(lambda_dir, "execution-handler"))
sys.path.insert(0, lambda_dir)


@pytest.fixture(scope="function", autouse=False)
def mock_shared_modules():
    """Mock shared modules for handler import, but NOT launch_config_validation."""
    # Save original modules
    original_modules = {}
    mock_modules = [
        "shared.account_utils",
        "shared.config_merge",
        "shared.conflict_detection",
        "shared.cross_account",
        "shared.drs_limits",
        "shared.drs_utils",
        "shared.execution_utils",
        "shared.rbac_middleware",
        "shared.response_utils",
        "shared.security_utils",
    ]

    for module_name in mock_modules:
        if module_name in sys.modules:
            original_modules[module_name] = sys.modules[module_name]

    # Mock the modules (will be set up by each test file's specific mocks)
    yield

    # Restore original modules
    for module_name in mock_modules:
        if module_name in original_modules:
            sys.modules[module_name] = original_modules[module_name]
        else:
            sys.modules.pop(module_name, None)


# NOTE: Module-level mocking removed to prevent pytest collection conflicts
# Tests that need mocking should use fixtures or patch decorators within the test function
#
# # Mock shared modules
# sys.modules['shared'] = Mock()
# sys.modules['shared.config_merge'] = Mock()
# sys.modules['shared.conflict_detection'] = Mock()
# sys.modules['shared.cross_account'] = Mock()
# sys.modules['shared.drs_limits'] = Mock()
# sys.modules['shared.execution_utils'] = Mock()
# sys.modules['shared.drs_utils'] = Mock()
#
# # Mock response_utils with proper response function
# mock_response_utils = Mock()
#
# # Create a proper DecimalEncoder class
# class MockDecimalEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, Decimal):
#             return int(obj) if obj % 1 == 0 else float(obj)
#         return super().default(obj)
#
# def mock_response(status_code, body, headers=None):
#     """Mock response function that returns proper API Gateway response"""
#     return {
#         "statusCode": status_code,
#         "headers": {
#             "Content-Type": "application/json",
#             "Access-Control-Allow-Origin": "*",
#         },
#         "body": json.dumps(body, cls=MockDecimalEncoder)
#     }
# mock_response_utils.response = mock_response
# mock_response_utils.DecimalEncoder = MockDecimalEncoder
# sys.modules['shared.response_utils'] = mock_response_utils


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for moto"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def dynamodb_table(aws_credentials):
    """Create mock DynamoDB table for executions"""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Create execution history table
        table = dynamodb.create_table(
            TableName="test-execution-table",
            KeySchema=[
                {"AttributeName": "executionId", "KeyType": "HASH"},
                {"AttributeName": "planId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "executionId", "AttributeType": "S"},
                {"AttributeName": "planId", "AttributeType": "S"},
                {"AttributeName": "status", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "StatusIndex",
                    "KeySchema": [{"AttributeName": "status", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
                }
            ],
            BillingMode="PROVISIONED",
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        yield table


@pytest.fixture
def mock_env_vars():
    """Set up environment variables"""
    with patch.dict(
        os.environ,
        {
            "EXECUTION_HISTORY_TABLE": "test-execution-table",
            "PROTECTION_GROUPS_TABLE": "test-pg-table",
            "RECOVERY_PLANS_TABLE": "test-plans-table",
            "TARGET_ACCOUNTS_TABLE": "test-accounts-table",
            "PROJECT_NAME": "test-project",
            "ENVIRONMENT": "test",
            "STATE_MACHINE_ARN": "arn:aws:states:us-east-1:123456789012:stateMachine:test",
        },
    ):
        yield


@pytest.fixture
def mock_drs_api():
    """Mock DRS API responses"""
    with patch("boto3.client") as mock_client:
        drs_client = Mock()

        # Mock describe_jobs response
        drs_client.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "job-123",
                    "status": "COMPLETED",
                    "type": "LAUNCH",
                    "initiatedBy": "USER",
                    "creationDateTime": "2026-01-25T12:00:00Z",
                    "endDateTime": "2026-01-25T12:15:00Z",
                    "participatingServers": [
                        {"sourceServerID": "s-abc123", "launchStatus": "LAUNCHED", "recoveryInstanceID": "i-xyz789"}
                    ],
                }
            ]
        }

        # Mock describe_recovery_instances response
        drs_client.describe_recovery_instances.return_value = {
            "items": [
                {
                    "recoveryInstanceID": "i-xyz789",
                    "sourceServerID": "s-abc123",
                    "ec2InstanceID": "i-xyz789",
                    "ec2InstanceState": "running",
                }
            ]
        }

        mock_client.return_value = drs_client
        yield drs_client


@pytest.fixture
def mock_ec2_api():
    """Mock EC2 API responses"""
    with patch("boto3.client") as mock_client:
        ec2_client = Mock()

        # Mock describe_instances response
        ec2_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-xyz789",
                            "InstanceType": "t3.medium",
                            "PrivateIpAddress": "10.0.1.50",
                            "PrivateDnsName": "ip-10-0-1-50.ec2.internal",
                            "State": {"Name": "running"},
                            "LaunchTime": "2026-01-25T12:10:00Z",
                        }
                    ]
                }
            ]
        }

        mock_client.return_value = ec2_client
        yield ec2_client


def create_single_wave_execution(table, execution_id="test-exec-1", plan_id="test-plan-1"):
    """Helper to create a single-wave execution in DynamoDB"""
    execution = {
        "executionId": execution_id,
        "planId": plan_id,
        "status": "POLLING",
        "executionType": "DRILL",
        "waves": [
            {
                "waveNumber": Decimal("0"),
                "waveName": "Wave1",
                "status": "IN_PROGRESS",
                "jobId": "job-123",
                "region": "us-east-1",
                "serverStatuses": [],
            }
        ],
        "createdTime": Decimal(str(int(time.time()))),
        "lastPolledTime": Decimal(str(int(time.time()))),
    }

    table.put_item(Item=execution)
    return execution


class TestSingleWaveExecution:
    """Integration tests for single-wave execution lifecycle"""

    def test_single_wave_execution_complete_flow(self, dynamodb_table, mock_env_vars):
        """
        Test complete single-wave execution flow:
        1. Create execution with one wave
        2. Poll wave status (enriches with DRS + EC2 data)
        3. Wave completes
        4. Finalize execution
        """
        from index import lambda_handler

        # Step 1: Create execution
        execution = create_single_wave_execution(dynamodb_table, execution_id="exec-single-1", plan_id="plan-1")

        # Mock boto3.client to return DRS and EC2 clients
        with patch("boto3.client") as mock_boto_client:
            # Create mock DRS client
            mock_drs = Mock()
            mock_drs.describe_jobs.return_value = {
                "items": [
                    {
                        "jobID": "job-123",
                        "status": "COMPLETED",
                        "participatingServers": [
                            {"sourceServerID": "s-abc123", "launchStatus": "LAUNCHED", "recoveryInstanceID": "i-xyz789"}
                        ],
                    }
                ]
            }

            # Create mock EC2 client
            mock_ec2 = Mock()
            mock_ec2.describe_instances.return_value = {
                "Reservations": [
                    {
                        "Instances": [
                            {
                                "InstanceId": "i-xyz789",
                                "InstanceType": "t3.medium",
                                "PrivateIpAddress": "10.0.1.50",
                                "PrivateDnsName": "ip-10-0-1-50.ec2.internal",
                                "State": {"Name": "running"},
                            }
                        ]
                    }
                ]
            }

            # Return appropriate client based on service name
            def get_client(service, **kwargs):
                if service == "drs":
                    return mock_drs
                elif service == "ec2":
                    return mock_ec2
                return Mock()

            mock_boto_client.side_effect = get_client

            # Mock enrich_server_data to return enriched data
            with patch("shared.drs_utils.enrich_server_data") as mock_enrich:
                mock_enrich.return_value = [
                    {
                        "sourceServerId": "s-abc123",
                        "launchStatus": "LAUNCHED",
                        "instanceId": "i-xyz789",
                        "privateIp": "10.0.1.50",
                        "hostname": "ip-10-0-1-50.ec2.internal",
                        "instanceType": "t3.medium",
                        "instanceState": "running",
                    }
                ]

                # Step 2: Poll execution (should enrich server data)
                poll_event = {"operation": "poll", "executionId": "exec-single-1", "planId": "plan-1"}

                with patch("index.execution_history_table", dynamodb_table):
                    poll_result = lambda_handler(poll_event, Mock())

                # Verify polling result
                assert poll_result["statusCode"] == 200
                assert poll_result["executionId"] == "exec-single-1"
                assert poll_result["status"] == "POLLING"  # Status unchanged
                assert poll_result["allWavesComplete"] is True  # Wave completed
                assert len(poll_result["waves"]) == 1
                assert poll_result["waves"][0]["status"] == "COMPLETED"

                # Verify server data enriched
                server_statuses = poll_result["waves"][0]["serverStatuses"]
                assert len(server_statuses) == 1
                assert server_statuses[0]["privateIp"] == "10.0.1.50"
                assert server_statuses[0]["instanceType"] == "t3.medium"

        # Step 3: Finalize execution
        finalize_event = {"operation": "finalize", "executionId": "exec-single-1", "planId": "plan-1"}

        with patch("index.execution_history_table", dynamodb_table):
            finalize_result = lambda_handler(finalize_event, Mock())

        # Verify finalization
        assert finalize_result["statusCode"] == 200
        assert finalize_result["status"] == "COMPLETED"
        assert finalize_result["executionId"] == "exec-single-1"

        # Step 4: Verify final state in DynamoDB
        response = dynamodb_table.get_item(Key={"executionId": "exec-single-1", "planId": "plan-1"})

        final_execution = response["Item"]
        assert final_execution["status"] == "COMPLETED"
        assert "endTime" in final_execution  # Finalization sets endTime
        assert len(final_execution["waves"]) == 1
        assert final_execution["waves"][0]["status"] == "COMPLETED"

    def test_polling_never_changes_execution_status(self, dynamodb_table, mock_env_vars, mock_drs_api):
        """
        Test that polling updates wave status but NEVER changes execution status.
        This is the critical fix for the multi-wave bug.
        """
        from index import lambda_handler

        # Create execution
        execution = create_single_wave_execution(dynamodb_table, execution_id="exec-status-test", plan_id="plan-1")

        # Mock enrich_server_data
        with patch("shared.drs_utils.enrich_server_data") as mock_enrich:
            mock_enrich.return_value = [{"sourceServerId": "s-abc123", "launchStatus": "LAUNCHED"}]

            # Poll execution multiple times
            poll_event = {"operation": "poll", "executionId": "exec-status-test", "planId": "plan-1"}

            with patch("index.execution_history_table", dynamodb_table):
                # First poll
                result1 = lambda_handler(poll_event, Mock())
                assert result1["status"] == "POLLING"

                # Second poll
                result2 = lambda_handler(poll_event, Mock())
                assert result2["status"] == "POLLING"

                # Third poll
                result3 = lambda_handler(poll_event, Mock())
                assert result3["status"] == "POLLING"

        # Verify execution status in DynamoDB still POLLING
        response = dynamodb_table.get_item(Key={"executionId": "exec-status-test", "planId": "plan-1"})

        assert response["Item"]["status"] == "POLLING"

    def test_finalization_requires_all_waves_complete(self, dynamodb_table, mock_env_vars):
        """
        Test that finalization fails if wave is not complete.
        """
        from index import lambda_handler

        # Create execution with incomplete wave
        execution = {
            "executionId": "exec-incomplete",
            "planId": "plan-1",
            "status": "POLLING",
            "executionType": "DRILL",
            "waves": [
                {
                    "waveNumber": Decimal("0"),
                    "waveName": "Wave1",
                    "status": "IN_PROGRESS",  # Not complete
                    "jobId": "job-123",
                    "region": "us-east-1",
                }
            ],
        }

        dynamodb_table.put_item(Item=execution)

        # Try to finalize
        finalize_event = {"operation": "finalize", "executionId": "exec-incomplete", "planId": "plan-1"}

        with patch("index.execution_history_table", dynamodb_table):
            result = lambda_handler(finalize_event, Mock())

        # Should fail
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "WAVES_NOT_COMPLETE" in body["error"]

        # Verify execution status unchanged
        response = dynamodb_table.get_item(Key={"executionId": "exec-incomplete", "planId": "plan-1"})
        assert response["Item"]["status"] == "POLLING"

    def test_finalization_is_idempotent(self, dynamodb_table, mock_env_vars):
        """
        Test that finalization can be called multiple times safely.
        """
        from index import lambda_handler

        # Create completed execution
        execution = {
            "executionId": "exec-idempotent",
            "planId": "plan-1",
            "status": "POLLING",
            "executionType": "DRILL",
            "waves": [
                {
                    "waveNumber": Decimal("0"),
                    "waveName": "Wave1",
                    "status": "COMPLETED",
                    "jobId": "job-123",
                    "region": "us-east-1",
                }
            ],
        }

        dynamodb_table.put_item(Item=execution)

        finalize_event = {"operation": "finalize", "executionId": "exec-idempotent", "planId": "plan-1"}

        with patch("index.execution_history_table", dynamodb_table):
            # First finalization
            result1 = lambda_handler(finalize_event, Mock())
            assert result1["statusCode"] == 200
            assert result1["status"] == "COMPLETED"

            # Second finalization (should succeed)
            result2 = lambda_handler(finalize_event, Mock())
            assert result2["statusCode"] == 200
            assert result2["status"] == "COMPLETED"
            assert result2.get("alreadyFinalized") is True

    def test_server_data_enrichment_with_ec2_details(self, dynamodb_table, mock_env_vars):
        """
        Test that server data is enriched with EC2 instance details during polling.
        """
        from index import lambda_handler

        # Create execution
        execution = create_single_wave_execution(dynamodb_table, execution_id="exec-enrichment", plan_id="plan-1")

        # Mock boto3.client to return DRS and EC2 clients
        with patch("boto3.client") as mock_boto_client:
            # Create mock DRS client
            mock_drs = Mock()
            mock_drs.describe_jobs.return_value = {
                "items": [
                    {
                        "jobID": "job-123",
                        "status": "COMPLETED",
                        "participatingServers": [
                            {"sourceServerID": "s-abc123", "launchStatus": "LAUNCHED", "recoveryInstanceID": "i-xyz789"}
                        ],
                    }
                ]
            }

            # Create mock EC2 client
            mock_ec2 = Mock()
            mock_ec2.describe_instances.return_value = {
                "Reservations": [
                    {
                        "Instances": [
                            {
                                "InstanceId": "i-xyz789",
                                "InstanceType": "t3.medium",
                                "PrivateIpAddress": "10.0.1.50",
                                "PrivateDnsName": "ip-10-0-1-50.ec2.internal",
                                "State": {"Name": "running"},
                            }
                        ]
                    }
                ]
            }

            # Return appropriate client based on service name
            def get_client(service, **kwargs):
                if service == "drs":
                    return mock_drs
                elif service == "ec2":
                    return mock_ec2
                return Mock()

            mock_boto_client.side_effect = get_client

            # Mock enrich_server_data with full EC2 details
            with patch("shared.drs_utils.enrich_server_data") as mock_enrich:
                mock_enrich.return_value = [
                    {
                        "sourceServerId": "s-abc123",
                        "serverName": "web-server-01",
                        "launchStatus": "LAUNCHED",
                        "launchTime": 1737806400,
                        "instanceId": "i-xyz789",
                        "privateIp": "10.0.1.50",
                        "hostname": "ip-10-0-1-50.ec2.internal",
                        "instanceType": "t3.medium",
                        "instanceState": "running",
                    }
                ]

                # Poll execution
                poll_event = {"operation": "poll", "executionId": "exec-enrichment", "planId": "plan-1"}

                with patch("index.execution_history_table", dynamodb_table):
                    result = lambda_handler(poll_event, Mock())

                # Verify enriched data
                server_statuses = result["waves"][0]["serverStatuses"]
                assert len(server_statuses) == 1

                server = server_statuses[0]
                assert server["sourceServerId"] == "s-abc123"
                assert server["serverName"] == "web-server-01"
                assert server["launchStatus"] == "LAUNCHED"
                assert server["instanceId"] == "i-xyz789"
                assert server["privateIp"] == "10.0.1.50"
                assert server["hostname"] == "ip-10-0-1-50.ec2.internal"
                assert server["instanceType"] == "t3.medium"
                assert server["instanceState"] == "running"
