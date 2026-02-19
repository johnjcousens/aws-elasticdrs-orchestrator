"""
Unit tests for data-management-handler staging account sync routing.

Tests verify that:
1. sync_staging_accounts operation routes to handle_sync_staging_accounts()
2. Direct invocation returns raw data (unwrapped)
3. Function is called with correct parameters

Feature: active-region-filtering
Validates: Requirements 11.10
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
os.environ["SOURCE_SERVER_INVENTORY_TABLE"] = "test-inventory"

# Import from data-management-handler using importlib.import_module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lambda"))
data_management_handler = importlib.import_module("data-management-handler.index")


@pytest.fixture(autouse=True)
def reset_mocks():
    """
    Reset all mocks between tests to prevent state pollution.
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


class TestStagingSyncRouting:
    """Test sync_staging_accounts operation routing"""

    def test_sync_staging_accounts_routes_to_correct_function(self, mock_iam_utils, lambda_context):
        """
        Test that sync_staging_accounts operation calls handle_sync_staging_accounts()
        
        Validates: Requirements 11.10
        """
        # Mock the handle_sync_staging_accounts function
        mock_sync_result = {
            "message": "Staging account sync completed",
            "accountsProcessed": 2,
            "serversExtended": 5,
            "regionsProcessed": ["us-east-1", "us-west-2"],
        }

        with patch.object(
            data_management_handler,
            "handle_sync_staging_accounts",
            return_value=data_management_handler.response(200, mock_sync_result),
        ) as mock_sync:

            event = {
                "operation": "sync_staging_accounts",
                "body": {},
            }

            result = data_management_handler.lambda_handler(event, lambda_context)

            # Verify the function was called
            mock_sync.assert_called_once()

            # Verify result is unwrapped (no statusCode)
            assert isinstance(result, dict)
            assert "statusCode" not in result
            assert result["message"] == "Staging account sync completed"
            assert result["accountsProcessed"] == 2
            assert result["serversExtended"] == 5

    def test_sync_staging_accounts_returns_raw_data(self, mock_iam_utils, lambda_context):
        """
        Test that direct invocation returns raw data without API Gateway wrapping
        
        Validates: Requirements 11.10
        """
        mock_sync_result = {
            "message": "Sync completed",
            "accountsProcessed": 1,
            "serversExtended": 3,
        }

        with patch.object(
            data_management_handler,
            "handle_sync_staging_accounts",
            return_value=data_management_handler.response(200, mock_sync_result),
        ):

            event = {
                "operation": "sync_staging_accounts",
                "body": {},
            }

            result = data_management_handler.lambda_handler(event, lambda_context)

            # Verify raw response format (no API Gateway wrapper)
            assert isinstance(result, dict)
            assert "statusCode" not in result
            assert "message" in result
            assert "accountsProcessed" in result
            assert "serversExtended" in result

    def test_sync_staging_accounts_no_parameters_required(self, mock_iam_utils, lambda_context):
        """
        Test that sync_staging_accounts operation doesn't require parameters
        
        Validates: Requirements 11.10
        """
        mock_sync_result = {
            "message": "Sync completed",
            "accountsProcessed": 0,
        }

        with patch.object(
            data_management_handler,
            "handle_sync_staging_accounts",
            return_value=data_management_handler.response(200, mock_sync_result),
        ) as mock_sync:

            # Call with empty body
            event = {
                "operation": "sync_staging_accounts",
                "body": {},
            }

            result = data_management_handler.lambda_handler(event, lambda_context)

            # Verify function was called with no arguments
            mock_sync.assert_called_once_with()

            # Verify result
            assert isinstance(result, dict)
            assert "message" in result

    def test_sync_staging_accounts_error_handling(self, mock_iam_utils, lambda_context):
        """
        Test error handling for sync_staging_accounts operation
        
        Validates: Requirements 11.10
        """
        # Mock function to raise an error
        with patch.object(
            data_management_handler,
            "handle_sync_staging_accounts",
            side_effect=Exception("DynamoDB connection failed"),
        ):

            event = {
                "operation": "sync_staging_accounts",
                "body": {},
            }

            result = data_management_handler.lambda_handler(event, lambda_context)

            # Verify error response format
            assert isinstance(result, dict)
            assert "error" in result
            assert result["error"] == "OPERATION_FAILED"
            assert "DynamoDB connection failed" in result["message"]

    def test_sync_staging_accounts_maintains_backward_compatibility(self, mock_iam_utils, lambda_context):
        """
        Test that existing operations still work after adding sync_staging_accounts
        
        Validates: Requirements 11.10 (backward compatibility)
        """
        # Mock other operations to ensure they still work
        mock_accounts = [
            {"accountId": "123456789012", "accountName": "Test Account"},
        ]

        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": mock_accounts}

        with patch.object(data_management_handler, "get_target_accounts_table", return_value=mock_table):

            # Test that list_target_accounts still works
            event = {
                "operation": "list_target_accounts",
                "body": {},
            }

            result = data_management_handler.lambda_handler(event, lambda_context)

            # Verify existing operation still works
            assert isinstance(result, dict)
            # Should have accounts data (exact format depends on implementation)
            assert "statusCode" not in result  # Direct invocation returns raw data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
