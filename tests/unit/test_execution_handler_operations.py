"""
Unit tests for execution-handler operation routing.

Tests the consolidated execution-handler Lambda function that replaced
execution-finder and execution-poller with operation-based routing.
"""

import json  # noqa: F401
import os  # noqa: E402
import sys  # noqa: E402
import importlib.util  # noqa: F401
from unittest.mock import MagicMock, Mock, patch  # noqa: F401  # noqa: F401  # noqa: F401

import pytest  # noqa: F401
from botocore.exceptions import ClientError  # noqa: F401


# Module-level setup to load execution-handler index
lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
execution_handler_dir = os.path.join(lambda_dir, "execution-handler")


@pytest.fixture(scope="function", autouse=True)
def setup_execution_handler_import():
    """Ensure execution-handler index is imported correctly for each test"""
    # Save original sys.path and modules
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    # Remove any existing 'index' module
    if "index" in sys.modules:
        del sys.modules["index"]

    # Add execution-handler to front of path
    sys.path.insert(0, execution_handler_dir)
    sys.path.insert(0, lambda_dir)

    yield

    # Restore original state
    sys.path = original_path
    if "index" in sys.modules:
        del sys.modules["index"]
    if original_index is not None:
        sys.modules["index"] = original_index


@pytest.fixture(scope="function", autouse=False)
def mock_shared_modules():
    """Mock shared modules for handler import, but NOT launch_config_validation."""
    # Save original modules
    original_modules = {}
    mock_modules = [
        "shared.account_utils",
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
# # Mock shared modules before importing index
# sys.modules['shared'] = Mock()
# sys.modules['shared.conflict_detection'] = Mock()
# sys.modules['shared.cross_account'] = Mock()
# sys.modules['shared.drs_limits'] = Mock()
# sys.modules['shared.execution_utils'] = Mock()
# sys.modules['shared.drs_utils'] = Mock()
#
# # Mock response_utils with a proper response function
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
def mock_env_vars():
    """Set up environment variables for tests"""
    with patch.dict(
        os.environ,
        {
            "EXECUTION_HISTORY_TABLE": "test-execution-table",
            "PROTECTION_GROUPS_TABLE": "test-pg-table",
            "RECOVERY_PLANS_TABLE": "test-plans-table",
            "TARGET_ACCOUNTS_TABLE": "test-target-accounts-table",
            "PROJECT_NAME": "test-project",
            "ENVIRONMENT": "test",
            "STATE_MACHINE_ARN": "arn:aws:states:us-east-1:123456789012:stateMachine:test",
        },
    ):
        yield


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table"""
    table = Mock()  # noqa: F841
    table.query = Mock()
    table.get_item = Mock()
    table.update_item = Mock()
    return table


@pytest.fixture
def mock_drs_client():
    """Mock DRS client"""
    client = Mock()  # noqa: F841
    client.describe_jobs = Mock()
    return client


@pytest.fixture
def mock_ec2_client():
    """Mock EC2 client"""
    client = Mock()  # noqa: F841
    client.describe_instances = Mock()
    return client


class TestOperationRouting:
    """Test operation-based routing in lambda_handler"""

    def test_operation_find_routes_correctly(self, mock_env_vars):  # noqa: F811
        """Test that operation='find' routes to handle_find_operation"""
        from index import lambda_handler  # noqa: F401

        event = {"operation": "find"}
        context = Mock()
        context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"

        with patch("shared.iam_utils.validate_iam_authorization") as mock_validate:
            mock_validate.return_value = True

            with patch("index.handle_find_operation") as mock_find:
                mock_find.return_value = {"statusCode": 200, "executionsFound": 0}

                result = lambda_handler(event, context)  # noqa: F841

                mock_find.assert_called_once_with(event, context)
                assert result["statusCode"] == 200

    def test_operation_poll_routes_correctly(self, mock_env_vars):  # noqa: F811
        """Test that operation='poll' routes to handle_poll_operation"""
        from index import lambda_handler  # noqa: F401

        event = {"operation": "poll", "executionId": "test-123", "planId": "plan-456"}
        context = Mock()
        context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"

        with patch("shared.iam_utils.validate_iam_authorization") as mock_validate:
            mock_validate.return_value = True

            with patch("index.handle_poll_operation") as mock_poll:
                mock_poll.return_value = {"statusCode": 200, "executionId": "test-123"}

                result = lambda_handler(event, context)  # noqa: F841

                mock_poll.assert_called_once_with(event, context)
                assert result["statusCode"] == 200

    def test_operation_finalize_routes_correctly(self, mock_env_vars):  # noqa: F811
        """Test that operation='finalize' routes to handle_finalize_operation"""
        from index import lambda_handler  # noqa: F401

        event = {"operation": "finalize", "executionId": "test-123", "planId": "plan-456"}
        context = Mock()
        context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"

        with patch("shared.iam_utils.validate_iam_authorization") as mock_validate:
            mock_validate.return_value = True

            with patch("index.handle_finalize_operation") as mock_finalize:
                mock_finalize.return_value = {"statusCode": 200, "status": "COMPLETED"}

                result = lambda_handler(event, context)  # noqa: F841

                mock_finalize.assert_called_once_with(event, context)
                assert result["statusCode"] == 200

    def test_unknown_operation_returns_error(self, mock_env_vars):  # noqa: F811
        """Test that unknown operation returns error (raw dict format for direct invocation)"""
        from index import lambda_handler  # noqa: F401

        event = {"operation": "invalid_operation"}
        context = Mock()
        context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"

        with patch("shared.iam_utils.validate_iam_authorization") as mock_validate:
            mock_validate.return_value = True

            result = lambda_handler(event, context)  # noqa: F841

            # Direct invocation returns raw dict, not API Gateway format
            assert "error" in result
            assert result["error"] == "INVALID_OPERATION"
            assert "invalid_operation" in result["message"]
            assert "validOperations" in result["details"]

    def test_eventbridge_invocation_routes_to_find(self, mock_env_vars):  # noqa: F811
        """Test that EventBridge scheduled invocation routes to find operation"""
        from index import lambda_handler  # noqa: F401

        event = {"source": "aws.events"}
        context = Mock()
        context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"

        with patch("index.handle_find_operation") as mock_find:
            mock_find.return_value = {"statusCode": 200, "executionsFound": 0}

            result = lambda_handler(event, context)  # noqa: F841

            mock_find.assert_called_once_with(event, context)


class TestHandleFindOperation:
    """Test handle_find_operation function"""

    @patch("shared.iam_utils.validate_iam_authorization")
    def test_finds_polling_executions(self, mock_validate, mock_env_vars, mock_dynamodb_table):  # noqa: F811
        """Test finding executions in POLLING status"""
        from index import handle_find_operation  # noqa: F401

        mock_validate.return_value = True

        # Mock DynamoDB responses
        mock_dynamodb_table.query.side_effect = [
            {
                "Items": [
                    {"executionId": "exec-1", "planId": "plan-1", "status": "POLLING"},
                    {"executionId": "exec-2", "planId": "plan-2", "status": "POLLING"},
                ]
            },
            {"Items": []},  # No CANCELLING executions
            {"Items": []},  # No COMPLETED executions
        ]

        event = {"operation": "find"}
        context = Mock()
        context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"

        with patch("index.execution_history_table", mock_dynamodb_table):
            with patch("index.handle_poll_operation") as mock_poll:
                mock_poll.return_value = {"statusCode": 200}

                result = handle_find_operation(event, context)  # noqa: F841

                assert result["executionsFound"] == 2
                assert result["executionsPolled"] == 2
                assert mock_poll.call_count == 2

    @patch("shared.iam_utils.validate_iam_authorization")
    def test_finds_cancelling_executions(self, mock_validate, mock_env_vars, mock_dynamodb_table):  # noqa: F811
        """Test finding executions in CANCELLING status"""
        from index import handle_find_operation  # noqa: F401

        mock_validate.return_value = True

        mock_dynamodb_table.query.side_effect = [
            {"Items": []},  # No POLLING executions
            {"Items": [{"executionId": "exec-3", "planId": "plan-3", "status": "CANCELLING"}]},
            {"Items": []},  # No COMPLETED executions
        ]

        event = {"operation": "find"}
        context = Mock()
        context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"

        with patch("index.execution_history_table", mock_dynamodb_table):
            with patch("index.handle_poll_operation") as mock_poll:
                mock_poll.return_value = {"statusCode": 200}

                result = handle_find_operation(event, context)  # noqa: F841

                assert result["executionsFound"] == 1
                assert mock_poll.call_count == 1

    @patch("shared.iam_utils.validate_iam_authorization")
    def test_skips_executions_with_missing_ids(self, mock_validate, mock_env_vars, mock_dynamodb_table):  # noqa: F811
        """Test that executions with missing IDs are skipped"""
        from index import handle_find_operation  # noqa: F401

        mock_validate.return_value = True

        mock_dynamodb_table.query.side_effect = [
            {
                "Items": [
                    {"executionId": "exec-1"},  # Missing planId
                    {"planId": "plan-2"},  # Missing executionId
                    {"executionId": "exec-3", "planId": "plan-3"},  # Valid
                ]
            },
            {"Items": []},
            {"Items": []},  # No COMPLETED executions
        ]

        event = {"operation": "find"}
        context = Mock()
        context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"

        with patch("index.execution_history_table", mock_dynamodb_table):
            with patch("index.handle_poll_operation") as mock_poll:
                mock_poll.return_value = {"statusCode": 200}

                result = handle_find_operation(event, context)  # noqa: F841

                assert result["executionsFound"] == 3
                assert result["executionsPolled"] == 1  # Only valid one polled


class TestHandlePollOperation:
    """Test handle_poll_operation function"""

    def test_poll_updates_wave_status_without_changing_execution_status(  # noqa: F811
        self, mock_env_vars, mock_dynamodb_table
    ):
        """Test polling updates wave status but NOT execution status"""
        from index import handle_poll_operation  # noqa: F401

        # Mock execution with one wave
        execution = {
            "executionId": "exec-1",
            "planId": "plan-1",
            "status": "POLLING",
            "executionType": "DRILL",
            "waves": [
                {
                    "waveNumber": 0,
                    "waveName": "Wave1",
                    "status": "IN_PROGRESS",
                    "jobId": "job-123",
                    "region": "us-east-1",
                }
            ],
        }

        mock_dynamodb_table.get_item.return_value = {"Item": execution}

        event = {"operation": "poll", "executionId": "exec-1", "planId": "plan-1"}
        context = Mock()

        with patch("index.execution_history_table", mock_dynamodb_table):
            with patch("index.poll_wave_with_enrichment") as mock_poll_wave:
                mock_poll_wave.return_value = {
                    "waveNumber": 0,
                    "waveName": "Wave1",
                    "status": "COMPLETED",
                    "jobId": "job-123",
                }

                result = handle_poll_operation(event, context)  # noqa: F841

                # Verify execution status unchanged
                assert result["status"] == "POLLING"
                assert result["executionId"] == "exec-1"

                # Verify DynamoDB update called with waves but NOT status
                mock_dynamodb_table.update_item.assert_called_once()
                call_args = mock_dynamodb_table.update_item.call_args
                assert "waves" in call_args[1]["UpdateExpression"]
                assert "lastPolledTime" in call_args[1]["UpdateExpression"]
                assert "#status" not in call_args[1].get("UpdateExpression", "")

    def test_poll_skips_completed_executions(self, mock_env_vars, mock_dynamodb_table):  # noqa: F811
        """Test polling skips executions that are already completed"""
        from index import handle_poll_operation  # noqa: F401

        execution = {"executionId": "exec-1", "planId": "plan-1", "status": "COMPLETED", "waves": []}

        mock_dynamodb_table.get_item.return_value = {"Item": execution}

        event = {"operation": "poll", "executionId": "exec-1", "planId": "plan-1"}
        context = Mock()

        with patch("index.execution_history_table", mock_dynamodb_table):
            result = handle_poll_operation(event, context)  # noqa: F841

            assert result["status"] == "COMPLETED"
            assert result["allWavesComplete"] is True
            # Should not update DynamoDB
            mock_dynamodb_table.update_item.assert_not_called()

    def test_poll_returns_all_waves_complete_flag(self, mock_env_vars, mock_dynamodb_table):  # noqa: F811
        """Test polling returns allWavesComplete flag for Step Functions"""
        from index import handle_poll_operation  # noqa: F401

        execution = {
            "executionId": "exec-1",
            "planId": "plan-1",
            "status": "POLLING",
            "executionType": "DRILL",
            "waves": [
                {"waveNumber": 0, "status": "COMPLETED", "jobId": "job-1"},
                {"waveNumber": 1, "status": "COMPLETED", "jobId": "job-2"},
            ],
        }

        mock_dynamodb_table.get_item.return_value = {"Item": execution}

        event = {"operation": "poll", "executionId": "exec-1", "planId": "plan-1"}
        context = Mock()

        with patch("index.execution_history_table", mock_dynamodb_table):
            result = handle_poll_operation(event, context)  # noqa: F841

            assert result["allWavesComplete"] is True
            assert result["status"] == "POLLING"  # Status unchanged

    def test_poll_missing_execution_returns_404(self, mock_env_vars, mock_dynamodb_table):  # noqa: F811
        """Test polling non-existent execution returns 404"""
        from index import handle_poll_operation  # noqa: F401

        mock_dynamodb_table.get_item.return_value = {}  # No Item

        event = {"operation": "poll", "executionId": "nonexistent", "planId": "plan-1"}
        context = Mock()

        with patch("index.execution_history_table", mock_dynamodb_table):
            result = handle_poll_operation(event, context)  # noqa: F841

            assert result["statusCode"] == 404


class TestHandleFinalizeOperation:
    """Test handle_finalize_operation function"""

    def test_finalize_requires_all_waves_complete(self, mock_env_vars, mock_dynamodb_table):  # noqa: F811
        """Test finalization fails if not all waves complete"""
        from index import handle_finalize_operation  # noqa: F401

        execution = {
            "executionId": "exec-1",
            "planId": "plan-1",
            "status": "POLLING",
            "waves": [
                {"waveNumber": 0, "status": "COMPLETED"},
                {"waveNumber": 1, "status": "IN_PROGRESS"},  # Not complete
            ],
        }

        mock_dynamodb_table.get_item.return_value = {"Item": execution}

        event = {"operation": "finalize", "executionId": "exec-1", "planId": "plan-1"}
        context = Mock()

        with patch("index.execution_history_table", mock_dynamodb_table):
            result = handle_finalize_operation(event, context)  # noqa: F841

            assert result["statusCode"] == 400
            body = json.loads(result["body"])
            assert body["error"] == "INVALID_STATE"
            assert "not all waves complete" in body["message"]

    def test_finalize_is_idempotent(self, mock_env_vars, mock_dynamodb_table):  # noqa: F811
        """Test finalization is idempotent - safe to call multiple times"""
        from index import handle_finalize_operation  # noqa: F401

        execution = {
            "executionId": "exec-1",
            "planId": "plan-1",
            "status": "COMPLETED",  # Already finalized
            "waves": [{"waveNumber": 0, "status": "COMPLETED"}],
        }

        mock_dynamodb_table.get_item.return_value = {"Item": execution}

        event = {"operation": "finalize", "executionId": "exec-1", "planId": "plan-1"}
        context = Mock()

        with patch("index.execution_history_table", mock_dynamodb_table):
            result = handle_finalize_operation(event, context)  # noqa: F841

            assert result["statusCode"] == 200
            assert result["status"] == "COMPLETED"
            assert result["alreadyFinalized"] is True
            # Should not update DynamoDB
            mock_dynamodb_table.update_item.assert_not_called()

    def test_finalize_uses_conditional_write(self, mock_env_vars, mock_dynamodb_table):  # noqa: F811
        """Test finalization uses conditional write for idempotency"""
        from index import handle_finalize_operation  # noqa: F401

        execution = {
            "executionId": "exec-1",
            "planId": "plan-1",
            "status": "POLLING",
            "waves": [{"waveNumber": 0, "status": "COMPLETED"}],
        }

        mock_dynamodb_table.get_item.return_value = {"Item": execution}

        event = {"operation": "finalize", "executionId": "exec-1", "planId": "plan-1"}
        context = Mock()

        with patch("index.execution_history_table", mock_dynamodb_table):
            result = handle_finalize_operation(event, context)  # noqa: F841

            # Verify conditional write used
            mock_dynamodb_table.update_item.assert_called_once()
            call_args = mock_dynamodb_table.update_item.call_args
            assert "ConditionExpression" in call_args[1]
            assert result["statusCode"] == 200

    def test_finalize_handles_concurrent_calls(self, mock_env_vars, mock_dynamodb_table):  # noqa: F811
        """Test finalization handles concurrent calls gracefully"""
        from index import handle_finalize_operation  # noqa: F401

        execution = {
            "executionId": "exec-1",
            "planId": "plan-1",
            "status": "POLLING",
            "waves": [{"waveNumber": 0, "status": "COMPLETED"}],
        }

        mock_dynamodb_table.get_item.return_value = {"Item": execution}

        # Simulate conditional check failure (already finalized by another call)
        mock_dynamodb_table.update_item.side_effect = ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException"}}, "UpdateItem"
        )

        event = {"operation": "finalize", "executionId": "exec-1", "planId": "plan-1"}
        context = Mock()

        with patch("index.execution_history_table", mock_dynamodb_table):
            result = handle_finalize_operation(event, context)  # noqa: F841

            assert result["statusCode"] == 200
            assert result["alreadyFinalized"] is True


class TestPollWaveWithEnrichment:
    """Test poll_wave_with_enrichment function"""

    def test_enriches_server_data_with_ec2_details(self, mock_env_vars, mock_drs_client, mock_ec2_client):  # noqa: F811
        """Test wave polling enriches server data with EC2 details"""
        from index import poll_wave_with_enrichment  # noqa: F401

        wave = {"waveNumber": 0, "waveName": "Wave1", "jobId": "job-123", "region": "us-east-1"}

        # Mock DRS response
        mock_drs_client.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "job-123",
                    "status": "COMPLETED",
                    "participatingServers": [
                        {"sourceServerID": "s-123", "launchStatus": "LAUNCHED", "recoveryInstanceID": "i-abc123"}
                    ],
                }
            ]
        }

        with patch("boto3.client") as mock_boto_client:
            mock_boto_client.side_effect = lambda service, **kwargs: (
                mock_drs_client if service == "drs" else mock_ec2_client
            )

            # Mock the enrich_server_data function from shared.drs_utils
            with patch("shared.drs_utils.enrich_server_data") as mock_enrich:
                mock_enrich.return_value = [
                    {
                        "sourceServerId": "s-123",
                        "launchStatus": "LAUNCHED",
                        "instanceId": "i-abc123",
                        "privateIp": "10.0.1.50",
                        "hostname": "server1.example.com",
                    }
                ]

                result = poll_wave_with_enrichment(wave, "DRILL")  # noqa: F841

                assert result["status"] == "COMPLETED"
                assert "serverStatuses" in result
                assert len(result["serverStatuses"]) == 1
                assert result["serverStatuses"][0]["privateIp"] == "10.0.1.50"

    def test_handles_missing_job_gracefully(self, mock_env_vars):  # noqa: F811
        """Test wave polling handles missing DRS job gracefully"""
        from index import poll_wave_with_enrichment  # noqa: F401

        wave = {"waveNumber": 0, "waveName": "Wave1", "jobId": None, "region": "us-east-1"}  # No job ID

        result = poll_wave_with_enrichment(wave, "DRILL")  # noqa: F841

        # Should return wave unchanged
        assert result == wave  # noqa: F841
