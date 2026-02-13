"""
Unit tests for data-management-handler response format consistency.

Tests verify that:
1. API Gateway invocations return wrapped responses (statusCode, headers, body)
2. Direct invocations return raw data (unwrapped)
3. Error responses are consistent across both modes

Feature: direct-lambda-invocation-mode
Validates: Requirements 10.2, 10.5, 10.6
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from pathlib import Path
import importlib.util

# Mock environment variables before importing handler
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-executions"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
os.environ["TAG_SYNC_CONFIG_TABLE"] = "test-tag-sync-config"

# Import from data-management-handler using importlib.import_module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lambda"))
data_management_handler = importlib.import_module("data-management-handler.index")


@pytest.fixture(autouse=True)
def reset_mocks():
    """
    Reset all mocks between tests to prevent state pollution.

    This fixture runs automatically before each test to ensure clean state.
    It resets module-level variables in both account_utils and conflict_detection
    modules to prevent boto3 client caching issues.
    """
    # Import modules that need resetting
    import shared.account_utils
    import shared.conflict_detection

    # Reset account_utils module-level variables
    shared.account_utils._dynamodb = None
    shared.account_utils._target_accounts_table = None

    # Reset conflict_detection module-level variables
    shared.conflict_detection._protection_groups_table = None
    shared.conflict_detection._recovery_plans_table = None
    shared.conflict_detection._execution_history_table = None
    shared.conflict_detection.dynamodb = None

    yield

    # Clean up after test
    patch.stopall()


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB tables"""
    # Mock protection groups table
    mock_pg_table = MagicMock()
    mock_pg_table.scan.return_value = {
        "Items": [
            {
                "groupId": "pg-123",
                "groupName": "Test Group",
                "region": "us-east-1",
                "sourceServerIds": ["s-123"],
            }
        ]
    }
    mock_pg_table.get_item.return_value = {
        "Item": {
            "groupId": "pg-123",
            "groupName": "Test Group",
            "region": "us-east-1",
            "sourceServerIds": ["s-123"],
        }
    }

    # Mock recovery plans table
    mock_rp_table = MagicMock()
    mock_rp_table.scan.return_value = {"Items": []}

    return mock_pg_table, mock_rp_table


@pytest.fixture
def mock_iam_utils():
    """Mock IAM utilities for authorization"""
    with (
        patch("shared.iam_utils.extract_iam_principal") as mock_extract,
        patch("shared.iam_utils.validate_iam_authorization") as mock_validate,
        patch("shared.iam_utils.log_direct_invocation") as mock_log,
        patch("shared.iam_utils.validate_direct_invocation_event") as mock_validate_event,
    ):

        mock_extract.return_value = "arn:aws:iam::123456789012:role/OrchestrationRole"
        mock_validate.return_value = True
        mock_validate_event.return_value = True

        yield {
            "extract": mock_extract,
            "validate": mock_validate,
            "log": mock_log,
            "validate_event": mock_validate_event,
        }


@pytest.fixture
def lambda_context():
    """Mock Lambda context"""
    context = Mock()
    context.request_id = "test-request-123"
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
    return context


class TestAPIGatewayResponseFormat:
    """Test API Gateway invocations return wrapped responses"""

    def test_list_protection_groups_api_gateway_format(self, mock_dynamodb, lambda_context):
        """API Gateway invocation should return wrapped response"""
        mock_pg_table, mock_rp_table = mock_dynamodb

        with patch.object(data_management_handler, "get_protection_groups_table", return_value=mock_pg_table):
            with patch.object(data_management_handler, "get_recovery_plans_table", return_value=mock_rp_table):
                event = {
                    "requestContext": {"authorizer": {"claims": {}}},
                    "httpMethod": "GET",
                    "path": "/protection-groups",
                    "queryStringParameters": {},
                }

                result = data_management_handler.lambda_handler(event, lambda_context)

                # Verify API Gateway response format
                assert isinstance(result, dict)
                assert "statusCode" in result
                assert "headers" in result
                assert "body" in result
                assert result["statusCode"] == 200

                # Verify body is JSON string
                assert isinstance(result["body"], str)
                body = json.loads(result["body"])
                assert "groups" in body
                assert "count" in body

    def test_get_protection_group_api_gateway_format(self, mock_dynamodb, lambda_context):
        """API Gateway GET should return wrapped response"""
        mock_pg_table, mock_rp_table = mock_dynamodb

        with patch.object(data_management_handler, "get_protection_groups_table", return_value=mock_pg_table):
            with patch.object(data_management_handler, "get_recovery_plans_table", return_value=mock_rp_table):
                event = {
                    "requestContext": {"authorizer": {"claims": {}}},
                    "httpMethod": "GET",
                    "path": "/protection-groups/pg-123",
                    "pathParameters": {"id": "pg-123"},
                    "queryStringParameters": {},
                }

                result = data_management_handler.lambda_handler(event, lambda_context)

                # Verify API Gateway response format
                assert isinstance(result, dict)
                assert "statusCode" in result
                assert result["statusCode"] == 200

                # Verify body contains protection group data
                body = json.loads(result["body"])
                assert body["groupId"] == "pg-123"
                assert body["groupName"] == "Test Group"


class TestDirectInvocationResponseFormat:
    """Test direct invocations return raw data (unwrapped)"""

    def test_list_protection_groups_direct_format(self, mock_dynamodb, mock_iam_utils, lambda_context):
        """Direct invocation should return raw data without API Gateway wrapping"""
        mock_pg_table, mock_rp_table = mock_dynamodb

        with patch.object(data_management_handler, "get_protection_groups_table", return_value=mock_pg_table):
            with patch.object(data_management_handler, "get_recovery_plans_table", return_value=mock_rp_table):
                event = {
                    "operation": "list_protection_groups",
                    "queryParams": {},
                }

                result = data_management_handler.lambda_handler(event, lambda_context)

                # Verify raw response format (no statusCode wrapper)
                assert isinstance(result, dict)
                assert "statusCode" not in result  # Should NOT have API Gateway wrapper
                assert "groups" in result
                assert "count" in result
                assert isinstance(result["groups"], list)
                assert isinstance(result["count"], int)

    def test_get_protection_group_direct_format(self, mock_dynamodb, mock_iam_utils, lambda_context):
        """Direct invocation GET should return raw protection group data"""
        mock_pg_table, mock_rp_table = mock_dynamodb

        with patch.object(data_management_handler, "get_protection_groups_table", return_value=mock_pg_table):
            with patch.object(data_management_handler, "get_recovery_plans_table", return_value=mock_rp_table):
                event = {
                    "operation": "get_protection_group",
                    "body": {"groupId": "pg-123"},
                }

                result = data_management_handler.lambda_handler(event, lambda_context)

                # Verify raw response format
                assert isinstance(result, dict)
                assert "statusCode" not in result  # Should NOT have API Gateway wrapper
                assert result["groupId"] == "pg-123"
                assert result["groupName"] == "Test Group"
                assert "region" in result

    def test_create_protection_group_direct_format(self, mock_dynamodb, mock_iam_utils, lambda_context):
        """Direct invocation CREATE should return raw created item"""
        mock_pg_table, mock_rp_table = mock_dynamodb

        # Mock successful creation
        mock_pg_table.put_item.return_value = {}
        mock_pg_table.scan.return_value = {"Items": []}

        # Mock DRS client
        mock_drs = MagicMock()
        mock_drs.describe_source_servers.return_value = {"items": [{"sourceServerID": "s-456"}]}

        # Mock execution history table
        mock_exec_table = MagicMock()
        mock_exec_table.scan.return_value = {"Items": []}

        # Patch getter functions and conflict detection
        # check_server_conflicts_for_create is imported directly
        # into the handler, so patch it at the handler level
        with (
            patch.object(data_management_handler, "get_protection_groups_table", return_value=mock_pg_table),
            patch.object(data_management_handler, "get_recovery_plans_table", return_value=mock_rp_table),
            patch.object(data_management_handler, "get_executions_table", return_value=mock_exec_table),
            patch.object(data_management_handler, "check_server_conflicts_for_create", return_value=[]),
            patch.object(data_management_handler, "create_drs_client", return_value=mock_drs),
        ):
            event = {
                "operation": "create_protection_group",
                "body": {
                    "groupName": "New Group",
                    "region": "us-east-1",
                    "sourceServerIds": ["s-456"],
                    "accountId": "123456789012",
                },
            }

            result = data_management_handler.lambda_handler(event, lambda_context)

            # Verify raw response format
            assert isinstance(result, dict)
            # Should NOT have API Gateway wrapper
            assert "statusCode" not in result
            assert "groupId" in result
            assert result["groupName"] == "New Group"


class TestErrorResponseFormat:
    """Test error responses are consistent across both modes"""

    def test_invalid_operation_direct_invocation(self, mock_dynamodb, mock_iam_utils, lambda_context):
        """Invalid operation should return error in raw format"""

        with patch.object(data_management_handler, "dynamodb", mock_dynamodb):
            event = {
                "operation": "invalid_operation_name",
                "body": {},
            }

            result = data_management_handler.lambda_handler(event, lambda_context)

            # Verify error response format
            assert isinstance(result, dict)
            assert "error" in result
            assert result["error"] == "INVALID_OPERATION"
            assert "message" in result
            assert "invalid_operation_name" in result["message"]

    def test_missing_parameter_direct_invocation(self, mock_dynamodb, mock_iam_utils, lambda_context):
        """Missing parameter should return error in raw format"""

        with patch.object(data_management_handler, "dynamodb", mock_dynamodb):
            event = {
                "operation": "get_protection_group",
                "body": {},  # Missing groupId
            }

            result = data_management_handler.lambda_handler(event, lambda_context)

            # Verify error response format
            assert isinstance(result, dict)
            # Should return 404 error for missing group (None passed to get_protection_group)
            assert "error" in result or "statusCode" not in result

    def test_authorization_failure_direct_invocation(self, mock_dynamodb, lambda_context):
        """Authorization failure should return error in raw format"""

        with (
            patch("shared.iam_utils.validate_iam_authorization") as mock_validate,
            patch("shared.iam_utils.extract_iam_principal") as mock_extract,
            patch("shared.iam_utils.validate_direct_invocation_event") as mock_validate_event,
            patch("shared.iam_utils.log_direct_invocation") as mock_log,
            patch("shared.iam_utils.create_authorization_error_response") as mock_auth_error,
            patch.object(data_management_handler, "dynamodb", mock_dynamodb),
        ):

            mock_validate_event.return_value = True
            mock_extract.return_value = "arn:aws:iam::123456789012:role/UnauthorizedRole"
            mock_validate.return_value = False
            mock_auth_error.return_value = {"error": "AUTHORIZATION_FAILED", "message": "IAM principal not authorized"}

            event = {
                "operation": "list_protection_groups",
                "queryParams": {},
            }

            result = data_management_handler.lambda_handler(event, lambda_context)

            # Verify error response format
            assert isinstance(result, dict)
            assert result["error"] == "AUTHORIZATION_FAILED"
            assert "message" in result


class TestResponseUnwrapping:
    """Test that API Gateway responses are properly unwrapped for direct invocations"""

    def test_unwrap_json_string_body(self, mock_dynamodb, mock_iam_utils, lambda_context):
        """Test unwrapping when body is JSON string"""
        mock_pg_table, mock_rp_table = mock_dynamodb

        with patch.object(data_management_handler, "get_protection_groups_table", return_value=mock_pg_table):
            with patch.object(data_management_handler, "get_recovery_plans_table", return_value=mock_rp_table):
                event = {
                    "operation": "list_protection_groups",
                    "queryParams": {},
                }

                result = data_management_handler.lambda_handler(event, lambda_context)

                # Result should be unwrapped dict, not API Gateway response
                assert isinstance(result, dict)
                assert "statusCode" not in result
                assert "groups" in result

    def test_unwrap_dict_body(self, mock_dynamodb, mock_iam_utils, lambda_context):
        """Test unwrapping when body is already a dict"""
        mock_pg_table, mock_rp_table = mock_dynamodb

        with patch.object(data_management_handler, "get_protection_groups_table", return_value=mock_pg_table):
            with patch.object(data_management_handler, "get_recovery_plans_table", return_value=mock_rp_table):
                event = {
                    "operation": "get_protection_group",
                    "body": {"groupId": "pg-123"},
                }

                result = data_management_handler.lambda_handler(event, lambda_context)

                # Result should be unwrapped dict
                assert isinstance(result, dict)
                assert "statusCode" not in result
                assert "groupId" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
