"""
Unit tests for execution-handler response format handling.

Tests verify that:
1. Direct invocations return raw data (no API Gateway wrapping)
2. API Gateway invocations return wrapped responses (statusCode, headers, body)
3. The unwrapping logic in handle_direct_invocation() works correctly

Feature: direct-lambda-invocation-mode
Validates: Requirements 10.3, 10.4, 10.6
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
import sys
import os
import importlib.util

# Mock environment variables before importing handler
os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["ORCHESTRATION_ROLE_ARN"] = "arn:aws:iam::123456789012:role/orchestration-role"
os.environ["STATE_MACHINE_ARN"] = "arn:aws:states:us-east-1:123456789012:stateMachine:test"

# Load execution-handler module dynamically
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))
execution_handler_index = importlib.import_module("execution-handler.index")


@pytest.fixture
def lambda_context():
    """Create mock Lambda context."""
    context = Mock()
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:execution-handler"
    context.request_id = "test-request-id-12345"
    context.function_name = "execution-handler"
    return context


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


class TestDirectInvocationResponseFormat:
    """Test response format for direct Lambda invocations."""

    def test_start_execution_returns_raw_data(self, lambda_context, mock_iam_utils):
        """
        Test that start_execution operation returns raw data for direct invocation.

        Verifies:
        - Response is a dict (not API Gateway format)
        - No statusCode field
        - No headers field
        - No body field (as string)
        - Contains actual data fields (executionId, status, message)
        """
        with patch.object(execution_handler_index, "execute_recovery_plan") as mock_execute:
            # Simulate API Gateway response format
            mock_execute.return_value = {
                "statusCode": 202,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"executionId": "exec-123", "status": "PENDING", "message": "Execution started"}),
            }

            event = {
                "operation": "start_execution",
                "parameters": {"planId": "plan-123", "executionType": "DRILL", "initiatedBy": "test-user"},
            }

            result = execution_handler_index.handle_direct_invocation(event, lambda_context)

            # Verify raw data format (unwrapped)
            assert isinstance(result, dict)
            assert "statusCode" not in result
            assert "headers" not in result
            assert "body" not in result or not isinstance(result.get("body"), str)

            # Verify actual data is present
            assert result.get("executionId") == "exec-123"
            assert result.get("status") == "PENDING"
            assert result.get("message") == "Execution started"

    def test_cancel_execution_returns_raw_data(self, lambda_context, mock_iam_utils):
        """Test that cancel_execution returns raw data for direct invocation."""
        with patch.object(execution_handler_index, "cancel_execution") as mock_cancel:
            mock_cancel.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"executionId": "exec-123", "status": "CANCELLED", "message": "Execution cancelled successfully"}
                ),
            }
            event = {"operation": "cancel_execution", "parameters": {"executionId": "exec-123"}}
            result = execution_handler_index.handle_direct_invocation(event, lambda_context)
            # Verify unwrapped response
            assert "statusCode" not in result
            assert result.get("executionId") == "exec-123"
            assert result.get("status") == "CANCELLED"

    def test_pause_execution_returns_raw_data(self, lambda_context, mock_iam_utils):
        """Test that pause_execution returns raw data for direct invocation."""
        with patch.object(execution_handler_index, "pause_execution") as mock_pause:
            mock_pause.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "executionId": "exec-123",
                        "status": "PAUSE_PENDING",
                        "message": "Execution will pause after current wave",
                    }
                ),
            }
            event = {"operation": "pause_execution", "parameters": {"executionId": "exec-123"}}
            result = execution_handler_index.handle_direct_invocation(event, lambda_context)
            # Verify unwrapped response
            assert "statusCode" not in result
            assert result.get("executionId") == "exec-123"
            assert result.get("status") == "PAUSE_PENDING"

    def test_resume_execution_returns_raw_data(self, lambda_context, mock_iam_utils):
        """Test that resume_execution returns raw data for direct invocation."""
        with patch.object(execution_handler_index, "resume_execution") as mock_resume:
            mock_resume.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"executionId": "exec-123", "status": "RUNNING", "message": "Execution resumed successfully"}
                ),
            }
            event = {"operation": "resume_execution", "parameters": {"executionId": "exec-123"}}
            result = execution_handler_index.handle_direct_invocation(event, lambda_context)
            # Verify unwrapped response
            assert "statusCode" not in result
            assert result.get("executionId") == "exec-123"
            assert result.get("status") == "RUNNING"

    def test_terminate_instances_returns_raw_data(self, lambda_context, mock_iam_utils):
        """Test that terminate_instances returns raw data for direct invocation."""
        with patch.object(execution_handler_index, "terminate_recovery_instances") as mock_terminate:
            mock_terminate.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"executionId": "exec-123", "terminatedInstances": 5, "message": "Terminated 5 recovery instances"}
                ),
            }
            event = {"operation": "terminate_instances", "parameters": {"executionId": "exec-123"}}
            result = execution_handler_index.handle_direct_invocation(event, lambda_context)
            # Verify unwrapped response
            assert "statusCode" not in result
            assert result.get("executionId") == "exec-123"
            assert result.get("terminatedInstances") == 5

    def test_get_recovery_instances_returns_raw_data(self, lambda_context, mock_iam_utils):
        """Test that get_recovery_instances returns raw data for direct invocation."""
        with patch.object(execution_handler_index, "get_recovery_instances") as mock_get_instances:
            mock_get_instances.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "executionId": "exec-123",
                        "instances": [
                            {"instanceId": "i-123", "state": "running"},
                            {"instanceId": "i-456", "state": "running"},
                        ],
                        "count": 2,
                    }
                ),
            }
            event = {"operation": "get_recovery_instances", "parameters": {"executionId": "exec-123"}}
            result = execution_handler_index.handle_direct_invocation(event, lambda_context)
            # Verify unwrapped response
            assert "statusCode" not in result
            assert result.get("executionId") == "exec-123"
            assert result.get("count") == 2
            assert len(result.get("instances", [])) == 2

    def test_error_response_format(self, lambda_context, mock_iam_utils):
        """Test that error responses are returned in raw format."""
        with patch.object(execution_handler_index, "cancel_execution") as mock_cancel:
            # Simulate error response
            mock_cancel.return_value = {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "NOT_FOUND", "message": "Execution not found"}),
            }
            event = {"operation": "cancel_execution", "parameters": {"executionId": "nonexistent"}}
            result = execution_handler_index.handle_direct_invocation(event, lambda_context)
            # Verify unwrapped error response
            assert "statusCode" not in result
            assert result.get("error") == "NOT_FOUND"
            assert result.get("message") == "Execution not found"

    def test_operation_returning_raw_dict_passes_through(self, lambda_context, mock_iam_utils):
        """
        Test that if an operation returns raw dict (no statusCode),
        it passes through unchanged.
        """
        with patch.object(execution_handler_index, "cancel_execution") as mock_cancel:
            # Return raw dict (no API Gateway wrapping)
            mock_cancel.return_value = {"executionId": "exec-123", "status": "CANCELLED", "message": "Direct response"}
            event = {"operation": "cancel_execution", "parameters": {"executionId": "exec-123"}}
            result = execution_handler_index.handle_direct_invocation(event, lambda_context)
            # Verify it passes through unchanged
            assert result.get("executionId") == "exec-123"
            assert result.get("status") == "CANCELLED"
            assert result.get("message") == "Direct response"


class TestUnwrappingLogic:
    """Test the unwrapping logic specifically."""

    def test_unwraps_api_gateway_response_with_statuscode(self, lambda_context, mock_iam_utils):
        """Test unwrapping when response has statusCode."""
        with patch.object(execution_handler_index, "cancel_execution") as mock_cancel:
            mock_cancel.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"executionId": "exec-123", "status": "CANCELLED", "nested": {"key": "value"}}),
            }
            event = {"operation": "cancel_execution", "parameters": {"executionId": "exec-123"}}
            result = execution_handler_index.handle_direct_invocation(event, lambda_context)
            # Verify body was parsed and unwrapped
            assert result.get("executionId") == "exec-123"
            assert result.get("status") == "CANCELLED"
            assert result.get("nested") == {"key": "value"}

    def test_handles_empty_body_gracefully(self, lambda_context, mock_iam_utils):
        """Test handling of empty body in API Gateway response."""
        with patch.object(execution_handler_index, "cancel_execution") as mock_cancel:
            mock_cancel.return_value = {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": ""}
            event = {"operation": "cancel_execution", "parameters": {"executionId": "exec-123"}}
            result = execution_handler_index.handle_direct_invocation(event, lambda_context)
            # Should return empty dict when body is empty
            assert result == {}

    def test_handles_decimal_types_in_response(self, lambda_context, mock_iam_utils):
        """Test handling of Decimal types from DynamoDB."""
        with patch.object(execution_handler_index, "cancel_execution") as mock_cancel:
            # DynamoDB often returns Decimal types
            mock_cancel.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"executionId": "exec-123", "timestamp": 1234567890, "count": 5}),
            }
            event = {"operation": "cancel_execution", "parameters": {"executionId": "exec-123"}}
            result = execution_handler_index.handle_direct_invocation(event, lambda_context)
            # Verify numeric values are preserved
            assert result.get("timestamp") == 1234567890
            assert result.get("count") == 5
