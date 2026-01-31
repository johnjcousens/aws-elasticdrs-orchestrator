"""
End-to-End Integration Tests for Complete DR Workflows.

Tests complete DR workflows across all three handlers:
- Query Handler: DRS infrastructure queries
- Data Management Handler: Protection Groups and Recovery Plans
- Execution Handler: DR execution lifecycle

Test Scenarios:
1. Complete DR workflow (query → create PG → create RP → execute → terminate)
2. Cross-account operations across all handlers
3. Conflict detection across handlers
4. Error handling and validation
5. API compatibility validation
"""

import importlib.util
import json
import os
import sys
from decimal import Decimal
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws

# Add lambda directory to path FIRST so patch decorators can import shared modules
lambda_dir = os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
lambda_dir = os.path.abspath(lambda_dir)
if lambda_dir not in sys.path:
    sys.path.insert(0, lambda_dir)

# Add tests directory to path for fixtures
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fixtures.mock_data import (
    get_mock_api_gateway_event,
    get_mock_drs_client,
    get_mock_drs_source_server,
    get_mock_execution,
    get_mock_protection_group,
    get_mock_recovery_plan,
)


def load_handler_module(handler_name):
    """Load a handler module dynamically"""
    # Lambda directory already added to sys.path at module level
    handler_path = os.path.join(lambda_dir, handler_name, "index.py")
    # Replace hyphens with underscores for valid Python module name
    module_name = handler_name.replace("-", "_") + "_index"
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing"""
    os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
    os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
    os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["STATE_MACHINE_ARN"] = "arn:aws:states:us-east-1:123456789012:stateMachine:DROrchestrator"
    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "test-execution-handler"
    yield
    # Cleanup
    for key in [
        "PROTECTION_GROUPS_TABLE",
        "RECOVERY_PLANS_TABLE",
        "EXECUTION_HISTORY_TABLE",
        "STATE_MACHINE_ARN",
        "AWS_LAMBDA_FUNCTION_NAME",
    ]:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def mock_dynamodb_tables():
    """Create mock DynamoDB tables"""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Create Protection Groups table
        dynamodb.create_table(
            TableName="test-protection-groups",
            KeySchema=[{"AttributeName": "groupId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "groupId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create Recovery Plans table
        dynamodb.create_table(
            TableName="test-recovery-plans",
            KeySchema=[{"AttributeName": "planId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "planId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create Execution History table
        dynamodb.create_table(
            TableName="test-execution-history",
            KeySchema=[{"AttributeName": "executionId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "executionId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Yield to keep mock_aws context active for the test
        # Don't yield table objects to avoid deepcopy recursion issues
        yield


class TestCompleteDRWorkflow:
    """Test complete DR workflow across all handlers"""

    @pytest.mark.skip(reason="Async Lambda invocation with moto causes deepcopy recursion - requires refactoring to mock Lambda invoke")
    def test_complete_workflow_query_to_execution(
        self,
        mock_env_vars,
        mock_dynamodb_tables,
    ):
        """
        Test complete DR workflow:
        1. Query DRS servers (Query Handler)
        2. Resolve tags (Data Management Handler)
        3. Create Protection Group (Data Management Handler)
        4. Create Recovery Plan (Data Management Handler)
        5. Execute Recovery Plan (Execution Handler)
        6. Check execution status (Execution Handler)
        """
        # Load handler modules
        query_handler = load_handler_module("query-handler")
        dm_handler = load_handler_module("data-management-handler")
        exec_handler = load_handler_module("execution-handler")

        # Mock DRS client with pre-configured responses
        mock_drs = get_mock_drs_client()
        
        # Mock Step Functions client
        mock_sfn = MagicMock()
        mock_sfn.start_execution.return_value = {
            "executionArn": "arn:aws:states:us-east-1:123456789012:execution:DROrchestrator:exec-1",
            "startDate": "2026-01-24T00:00:00Z",
        }
        mock_sfn.describe_execution.return_value = {
            "executionArn": "arn:aws:states:us-east-1:123456789012:execution:DROrchestrator:exec-1",
            "status": "RUNNING",
            "startDate": "2026-01-24T00:00:00Z",
        }
        
        # Mock Lambda client for async invocation
        mock_lambda = MagicMock()
        mock_lambda.invoke.return_value = {
            "StatusCode": 202,
            "Payload": MagicMock(),
        }

        def mock_client_factory(service, **kwargs):
            if service == "drs":
                return mock_drs
            elif service == "stepfunctions":
                return mock_sfn
            elif service == "lambda":
                return mock_lambda
            return MagicMock()

        # Patch boto3.client AND the module-level clients in execution-handler
        with patch("boto3.client", side_effect=mock_client_factory), \
             patch.object(exec_handler, "lambda_client", mock_lambda), \
             patch.object(exec_handler, "stepfunctions", mock_sfn):
            # Step 1: Query DRS servers
            query_event = get_mock_api_gateway_event("GET", "/drs/source-servers", query_params={"region": "us-east-1"})
            query_response = query_handler.lambda_handler(query_event, {})
            assert query_response["statusCode"] == 200
            query_body = json.loads(query_response["body"])
            assert len(query_body["sourceServers"]) == 2

            # Step 2: Resolve tags
            resolve_event = get_mock_api_gateway_event(
                "POST",
                "/protection-groups/resolve",
                body={"tags": {"Purpose": "Database"}, "region": "us-east-1"},
            )
            resolve_response = dm_handler.lambda_handler(resolve_event, {})
            assert resolve_response["statusCode"] == 200
            resolve_body = json.loads(resolve_response["body"])
            print(f"DEBUG resolve_body keys: {resolve_body.keys()}")
            assert len(resolve_body.get("sourceServers", resolve_body.get("resolvedServers", []))) == 2

            # Step 3: Create Protection Group
            create_pg_event = get_mock_api_gateway_event(
                "POST",
                "/protection-groups",
                body={
                    "groupName": "test-db-servers",
                    "description": "Database servers",
                    "serverSelectionTags": {"Purpose": "Database"},
                    "region": "us-east-1",
                },
            )
            create_pg_response = dm_handler.lambda_handler(create_pg_event, {})
            if create_pg_response["statusCode"] not in [200, 201]:
                print(f"DEBUG create_pg_response: {json.loads(create_pg_response['body'])}")
            assert create_pg_response["statusCode"] in [200, 201]
            pg_body = json.loads(create_pg_response["body"])
            pg_id = pg_body["protectionGroupId"]

            # Step 4: Create Recovery Plan
            create_rp_event = get_mock_api_gateway_event(
                "POST",
                "/recovery-plans",
                body={
                    "name": "test-recovery-plan",
                    "description": "Test recovery plan",
                    "protectionGroupId": pg_id,
                    "waves": [
                        {
                            "waveNumber": 1,
                            "name": "Wave 1",
                            "serverSelectionCriteria": {"tags": {"Purpose": "Database"}},
                        }
                    ],
                },
            )
            create_rp_response = dm_handler.lambda_handler(create_rp_event, {})
            assert create_rp_response["statusCode"] in [200, 201]
            rp_body = json.loads(create_rp_response["body"])
            plan_id = rp_body.get("recoveryPlanId") or rp_body.get("planId")

            # Step 5: Execute Recovery Plan
            execute_event = get_mock_api_gateway_event(
                "POST",
                f"/recovery-plans/{plan_id}/execute",
                body={"executionType": "DRILL", "initiatedBy": "test-user"},
                path_params={"id": plan_id},
            )
            execute_response = exec_handler.lambda_handler(execute_event, {})
            if execute_response["statusCode"] not in [200, 202]:
                print(f"DEBUG execute_response: {json.loads(execute_response['body'])}")
            assert execute_response["statusCode"] in [200, 202]
            exec_body = json.loads(execute_response["body"])
            execution_id = exec_body["executionId"]

            # Step 6: Check execution status
            status_event = get_mock_api_gateway_event(
                "GET",
                f"/executions/{execution_id}/status",
                path_params={"id": execution_id},
            )
            status_response = exec_handler.lambda_handler(status_event, {})
            assert status_response["statusCode"] == 200
            status_body = json.loads(status_response["body"])
            assert status_body["status"] in ["RUNNING", "PENDING"]


class TestCrossAccountOperations:
    """Test cross-account operations across all handlers"""

    @patch("shared.cross_account.create_drs_client")
    @patch("boto3.client")
    def test_cross_account_query_and_protection_group(
        self,
        mock_boto_client,
        mock_create_drs_client,
        mock_env_vars,
        mock_dynamodb_tables,
    ):
        """
        Test cross-account operations:
        1. Query DRS servers in target account (Query Handler)
        2. Create Protection Group with cross-account servers (Data Management Handler)
        """
        query_handler = load_handler_module("query-handler")
        dm_handler = load_handler_module("data-management-handler")

        # Mock STS client for role assumption
        mock_sts = MagicMock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "token",
            }
        }

        # Mock DRS client with pre-configured responses
        mock_drs = get_mock_drs_client()
        # Override with single server for cross-account test
        mock_drs.describe_source_servers.return_value = {
            "items": [
                get_mock_drs_source_server("s-1", "cross-account-server"),
            ]
        }
        # Also override paginator
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "items": [
                    get_mock_drs_source_server("s-1", "cross-account-server"),
                ]
            }
        ]
        mock_drs.get_paginator.return_value = mock_paginator
        mock_create_drs_client.return_value = mock_drs

        def mock_client_factory(service, **kwargs):
            if service == "sts":
                return mock_sts
            elif service == "drs":
                return mock_drs
            return MagicMock()

        mock_boto_client.side_effect = mock_client_factory

        # Query DRS servers in target account
        query_event = get_mock_api_gateway_event(
            "GET",
            "/drs/source-servers",
            query_params={"region": "us-east-1", "accountId": "123456789012"},
        )
        query_response = query_handler.lambda_handler(query_event, {})
        assert query_response["statusCode"] == 200
        query_body = json.loads(query_response["body"])
        assert len(query_body["sourceServers"]) == 1

        # Create Protection Group with cross-account servers
        create_pg_event = get_mock_api_gateway_event(
            "POST",
            "/protection-groups",
            body={
                "groupName": "cross-account-servers",
                "description": "Cross-account servers",
                "serverSelectionTags": {"Purpose": "Database"},
                "region": "us-east-1",
                "accountId": "123456789012",
            },
        )
        create_pg_response = dm_handler.lambda_handler(create_pg_event, {})
        assert create_pg_response["statusCode"] in [200, 201]


class TestConflictDetection:
    """Test conflict detection across handlers"""

    @patch("shared.cross_account.create_drs_client")
    @patch("boto3.client")
    @pytest.mark.skip(reason="Async Lambda invocation with moto causes deepcopy recursion - requires refactoring to mock Lambda invoke")
    def test_conflict_detection_active_execution(
        self,
        mock_boto_client,
        mock_create_drs_client,
        mock_env_vars,
        mock_dynamodb_tables,
    ):
        """
        Test conflict detection when servers are in active execution:
        1. Create Protection Group with servers
        2. Start execution with those servers
        3. Try to delete Protection Group (should fail due to conflict)
        4. Try to update Protection Group (should fail due to conflict)
        """
        dm_handler = load_handler_module("data-management-handler")
        exec_handler = load_handler_module("execution-handler")

        # Mock DRS client with pre-configured responses
        mock_drs = get_mock_drs_client()
        # Override with single server for conflict test
        mock_drs.describe_source_servers.return_value = {
            "items": [
                get_mock_drs_source_server("s-1", "server-1"),
            ]
        }
        mock_create_drs_client.return_value = mock_drs

        # Mock Step Functions client
        mock_sfn = MagicMock()
        mock_sfn.start_execution.return_value = {
            "executionArn": "arn:aws:states:us-east-1:123456789012:execution:DROrchestrator:exec-1",
            "startDate": "2026-01-24T00:00:00Z",
        }

        def mock_client_factory(service, **kwargs):
            if service == "drs":
                return mock_drs
            elif service == "stepfunctions":
                return mock_sfn
            return MagicMock()

        mock_boto_client.side_effect = mock_client_factory

        # Create Protection Group
        create_pg_event = get_mock_api_gateway_event(
            "POST",
            "/protection-groups",
            body={
                "groupName": "conflict-test-pg",
                "description": "Test conflict detection",
                "serverSelectionTags": {"Purpose": "Database"},
                "region": "us-east-1",
            },
        )
        create_pg_response = dm_handler.lambda_handler(create_pg_event, {})
        assert create_pg_response["statusCode"] in [200, 201]
        pg_body = json.loads(create_pg_response["body"])
        pg_id = pg_body["protectionGroupId"]

        # Create Recovery Plan
        create_rp_event = get_mock_api_gateway_event(
            "POST",
            "/recovery-plans",
            body={
                "name": "conflict-test-rp",
                "description": "Test conflict detection",
                "protectionGroupId": pg_id,
                "waves": [
                    {
                        "waveNumber": 1,
                        "name": "Wave 1",
                        "serverSelectionCriteria": {"tags": {"Purpose": "Database"}},
                    }
                ],
            },
        )
        create_rp_response = dm_handler.lambda_handler(create_rp_event, {})
        assert create_rp_response["statusCode"] in [200, 201]
        rp_body = json.loads(create_rp_response["body"])
        plan_id = rp_body.get("recoveryPlanId") or rp_body.get("planId")

        # Start execution (creates active execution with servers)
        execute_event = get_mock_api_gateway_event(
            "POST",
            f"/recovery-plans/{plan_id}/execute",
            body={"executionType": "DRILL", "initiatedBy": "test-user"},
            path_params={"id": plan_id},
        )
        execute_response = exec_handler.lambda_handler(execute_event, {})
        assert execute_response["statusCode"] in [200, 202]

        # Try to delete Protection Group (should fail due to active execution)
        delete_pg_event = get_mock_api_gateway_event("DELETE", f"/protection-groups/{pg_id}")
        delete_pg_response = dm_handler.lambda_handler(delete_pg_event, {})
        # Should return 409 Conflict or 400 Bad Request
        assert delete_pg_response["statusCode"] in [400, 409]
        delete_body = json.loads(delete_pg_response["body"])
        assert "conflict" in delete_body.get("error", "").lower() or "active" in delete_body.get("message", "").lower()


class TestErrorHandling:
    """Test error handling and validation across handlers"""

    def test_invalid_protection_group_id(self, mock_env_vars, mock_dynamodb_tables):
        """Test error handling for invalid Protection Group ID"""
        dm_handler = load_handler_module("data-management-handler")

        # Try to get non-existent Protection Group
        get_pg_event = get_mock_api_gateway_event("GET", "/protection-groups/invalid-id")
        get_pg_response = dm_handler.lambda_handler(get_pg_event, {})
        assert get_pg_response["statusCode"] == 400
        body = json.loads(get_pg_response["body"])
        assert "error" in body or "message" in body

    def test_invalid_recovery_plan_id(self, mock_env_vars, mock_dynamodb_tables):
        """Test error handling for invalid Recovery Plan ID"""
        dm_handler = load_handler_module("data-management-handler")

        # Try to get non-existent Recovery Plan
        get_rp_event = get_mock_api_gateway_event("GET", "/recovery-plans/invalid-id")
        get_rp_response = dm_handler.lambda_handler(get_rp_event, {})
        assert get_rp_response["statusCode"] == 400
        body = json.loads(get_rp_response["body"])
        assert "error" in body or "message" in body

    def test_invalid_execution_id(self, mock_env_vars, mock_dynamodb_tables):
        """Test error handling for invalid Execution ID"""
        exec_handler = load_handler_module("execution-handler")

        # Try to get non-existent execution
        get_exec_event = get_mock_api_gateway_event("GET", "/executions/invalid-id")
        get_exec_response = exec_handler.lambda_handler(get_exec_event, {})
        assert get_exec_response["statusCode"] == 400
        body = json.loads(get_exec_response["body"])
        assert "error" in body or "message" in body

    @patch("shared.cross_account.create_drs_client")
    @pytest.mark.skip(reason="Wave size validation happens at execution time, not recovery plan creation - test needs refactoring")
    def test_wave_size_validation(self, mock_create_drs_client, mock_env_vars, mock_dynamodb_tables):
        """Test DRS service limit validation (100 servers per wave)"""
        dm_handler = load_handler_module("data-management-handler")

        # Mock DRS client with 101 servers
        mock_drs = get_mock_drs_client()
        servers = [get_mock_drs_source_server(f"s-{i}", f"server-{i}") for i in range(101)]
        mock_drs.describe_source_servers.return_value = {"items": servers}
        mock_create_drs_client.return_value = mock_drs

        # Create Protection Group with 101 servers
        create_pg_event = get_mock_api_gateway_event(
            "POST",
            "/protection-groups",
            body={
                "groupName": "large-pg",
                "description": "Large protection group",
                "serverSelectionTags": {"Purpose": "Database"},
                "region": "us-east-1",
            },
        )
        create_pg_response = dm_handler.lambda_handler(create_pg_event, {})
        pg_body = json.loads(create_pg_response["body"])
        pg_id = pg_body["protectionGroupId"]

        # Try to create Recovery Plan with wave > 100 servers (should fail)
        create_rp_event = get_mock_api_gateway_event(
            "POST",
            "/recovery-plans",
            body={
                "name": "large-rp",
                "description": "Recovery plan with too many servers",
                "protectionGroupId": pg_id,
                "waves": [
                    {
                        "waveNumber": 1,
                        "name": "Wave 1",
                        "serverSelectionCriteria": {"tags": {"Purpose": "Database"}},
                    }
                ],
            },
        )
        create_rp_response = dm_handler.lambda_handler(create_rp_event, {})
        # Should return 400 Bad Request due to wave size limit
        assert create_rp_response["statusCode"] == 400
        body = json.loads(create_rp_response["body"])
        assert "100" in body.get("message", "") or "limit" in body.get("message", "").lower()


class TestAPICompatibility:
    """Test API compatibility - responses identical to monolithic handler"""

    @patch("shared.cross_account.create_drs_client")
    def test_query_handler_response_format(self, mock_create_drs_client, mock_env_vars, mock_dynamodb_tables):
        """Test Query Handler returns same response format as monolithic handler"""
        query_handler = load_handler_module("query-handler")

        # Mock DRS client with pre-configured responses
        mock_drs = get_mock_drs_client()
        # Override with single server for format test
        mock_drs.describe_source_servers.return_value = {
            "items": [
                get_mock_drs_source_server("s-1", "server-1"),
            ]
        }
        # Also override paginator
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "items": [
                    get_mock_drs_source_server("s-1", "server-1"),
                ]
            }
        ]
        mock_drs.get_paginator.return_value = mock_paginator
        mock_create_drs_client.return_value = mock_drs

        # Query DRS servers
        query_event = get_mock_api_gateway_event("GET", "/drs/source-servers", query_params={"region": "us-east-1"})
        query_response = query_handler.lambda_handler(query_event, {})

        # Validate response structure
        assert query_response["statusCode"] == 200
        assert "headers" in query_response
        assert "Access-Control-Allow-Origin" in query_response["headers"]
        assert "Content-Type" in query_response["headers"]

        body = json.loads(query_response["body"])
        assert "sourceServers" in body
        assert isinstance(body["sourceServers"], list)
        assert len(body["sourceServers"]) == 1
        assert "sourceServerID" in body["sourceServers"][0]

    @patch("shared.cross_account.create_drs_client")
    def test_data_management_handler_response_format(self, mock_create_drs_client, mock_env_vars, mock_dynamodb_tables):
        """Test Data Management Handler returns same response format as monolithic handler"""
        dm_handler = load_handler_module("data-management-handler")

        # Mock DRS client
        mock_drs = MagicMock()
        mock_drs.describe_source_servers.return_value = {
            "items": [
                get_mock_drs_source_server("s-1", "server-1"),
            ]
        }
        mock_create_drs_client.return_value = mock_drs

        # Create Protection Group
        create_pg_event = get_mock_api_gateway_event(
            "POST",
            "/protection-groups",
            body={
                "groupName": "test-pg",
                "description": "Test protection group",
                "serverSelectionTags": {"Purpose": "Database"},
                "region": "us-east-1",
            },
        )
        create_pg_response = dm_handler.lambda_handler(create_pg_event, {})

        # Validate response structure
        assert create_pg_response["statusCode"] in [200, 201]
        assert "headers" in create_pg_response
        assert "Access-Control-Allow-Origin" in create_pg_response["headers"]

        body = json.loads(create_pg_response["body"])
        assert "protectionGroupId" in body
        assert "groupName" in body
        assert "sourceServerIds" in body or "sourceServers" in body

    def test_execution_handler_response_format(self, mock_env_vars, mock_dynamodb_tables):
        """Test Execution Handler returns same response format as monolithic handler"""
        exec_handler = load_handler_module("execution-handler")

        # List executions
        list_event = get_mock_api_gateway_event("GET", "/executions")
        list_response = exec_handler.lambda_handler(list_event, {})

        # Validate response structure
        assert list_response["statusCode"] == 200
        assert "headers" in list_response
        assert "Access-Control-Allow-Origin" in list_response["headers"]

        body = json.loads(list_response["body"])
        # Accept both field names for compatibility
        assert "executions" in body or "items" in body
        items = body.get("executions") or body.get("items")
        assert isinstance(items, list)
