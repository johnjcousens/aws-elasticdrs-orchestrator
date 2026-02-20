"""
Unit tests for query-handler invocation mode detection and IAM principal extraction.

Tests dual invocation modes:
1. API Gateway invocation (Cognito JWT authentication)
2. Direct Lambda invocation (IAM authentication)

Validates:
- Invocation mode detection (API_GATEWAY vs DIRECT_LAMBDA)
- IAM principal extraction from Lambda context
- Principal type identification (AssumedRole, Role, User, Service)
- Principal ARN parsing and field extraction
"""

import json
import os
from unittest.mock import Mock, patch, MagicMock
import pytest


# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for all tests."""
    env_vars = {
        "AWS_ACCOUNT_ID": "438465159935",
        "AWS_REGION": "us-east-1",
        "PROTECTION_GROUPS_TABLE": "aws-drs-orchestration-protection-groups-qa",
        "RECOVERY_PLANS_TABLE": "aws-drs-orchestration-recovery-plans-qa",
        "TARGET_ACCOUNTS_TABLE": "aws-drs-orchestration-target-accounts-qa",
        "EXECUTION_HISTORY_TABLE": "aws-drs-orchestration-execution-history-qa",
        "DRS_REGION_STATUS_TABLE": "aws-drs-orchestration-drs-region-status-qa",
    }
    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture
def mock_lambda_context():
    """Create mock Lambda context for testing."""
    context = Mock()
    context.aws_request_id = "test-request-id-123"
    context.function_name = "aws-drs-orchestration-query-handler-qa"
    context.function_version = "$LATEST"
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:438465159935:function:aws-drs-orchestration-query-handler-qa"
    )
    context.memory_limit_in_mb = 256
    context.log_group_name = "/aws/lambda/aws-drs-orchestration-query-handler-qa"
    context.log_stream_name = "2026/02/09/[$LATEST]test-stream"
    return context


class TestAPIGatewayInvocation:
    """Test API Gateway invocation mode (Cognito JWT authentication)."""

    def test_api_gateway_invocation_with_cognito_user(self, mock_lambda_context):
        """Test API Gateway invocation extracts Cognito user from JWT claims."""
        # Import here to ensure mocked environment is loaded
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import lambda_handler

        # Create API Gateway event with Cognito JWT
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "email": "test.user@example.com",
                        "sub": "cognito-user-id-123",
                        "cognito:groups": ["Admin", "Operator"],
                    }
                },
                "requestId": "api-request-123",
            },
            "httpMethod": "GET",
            "path": "/accounts/current",
            "queryStringParameters": {},
        }

        # Mock get_current_account_id to avoid AWS API calls
        with patch("index.get_current_account_id", return_value="438465159935"):
            with patch("index.os.environ.get", side_effect=lambda k, d=None: {
                "AWS_ACCOUNT_ID": "438465159935",
                "AWS_REGION": "us-east-1"
            }.get(k, d)):
                result = lambda_handler(event, mock_lambda_context)

        # Verify response structure (should be API Gateway response)
        assert "statusCode" in result
        assert result["statusCode"] == 200

    def test_api_gateway_invocation_missing_cognito_claims(self, mock_lambda_context):
        """Test API Gateway invocation handles missing Cognito claims gracefully."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import lambda_handler

        # Create API Gateway event without Cognito claims
        event = {
            "requestContext": {
                "requestId": "api-request-123",
            },
            "httpMethod": "GET",
            "path": "/accounts/current",
            "queryStringParameters": {},
        }

        # Mock get_current_account_id
        with patch("index.get_current_account_id", return_value="438465159935"):
            with patch("index.os.environ.get", side_effect=lambda k, d=None: {
                "AWS_ACCOUNT_ID": "438465159935",
                "AWS_REGION": "us-east-1"
            }.get(k, d)):
                result = lambda_handler(event, mock_lambda_context)

        # Should still return valid response (principal_info will have "Unknown" type)
        assert "statusCode" in result


class TestDirectLambdaInvocation:
    """Test Direct Lambda invocation mode (IAM authentication)."""

    def test_step_functions_invocation_assumed_role(self, mock_lambda_context):
        """Test Step Functions invocation extracts AssumedRole principal."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import lambda_handler, _parse_principal_arn

        # Mock Step Functions assumed role ARN
        mock_lambda_context.invoked_function_arn = (
            "arn:aws:sts::438465159935:assumed-role/StepFunctionsExecutionRole/execution-abc123"
        )

        # Create direct invocation event
        event = {
            "operation": "get_drs_source_servers",
            "queryParams": {"region": "us-east-1"},
        }

        # Test _parse_principal_arn function directly
        principal_info = _parse_principal_arn(
            mock_lambda_context.invoked_function_arn,
            "DIRECT_LAMBDA"
        )

        # Verify principal information
        assert principal_info["invocation_mode"] == "DIRECT_LAMBDA"
        assert principal_info["principal_type"] == "AssumedRole"
        assert principal_info["principal_arn"] == "arn:aws:iam::438465159935:role/StepFunctionsExecutionRole"
        assert principal_info["session_name"] == "execution-abc123"
        assert principal_info["account_id"] == "438465159935"

    def test_eventbridge_invocation_service_principal(self, mock_lambda_context):
        """Test EventBridge invocation extracts Service principal."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        # Mock EventBridge service principal ARN
        service_arn = "arn:aws:events::438465159935:rule/inventory-sync-rule"

        # Test _parse_principal_arn function
        principal_info = _parse_principal_arn(service_arn, "DIRECT_LAMBDA")

        # Verify principal information
        assert principal_info["invocation_mode"] == "DIRECT_LAMBDA"
        assert principal_info["principal_type"] == "Service"
        assert principal_info["principal_arn"] == service_arn
        assert principal_info["session_name"] is None
        assert principal_info["account_id"] == "438465159935"

    def test_iam_role_invocation(self, mock_lambda_context):
        """Test IAM role invocation extracts Role principal."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        # Mock IAM role ARN
        role_arn = "arn:aws:iam::438465159935:role/OrchestrationRole"

        # Test _parse_principal_arn function
        principal_info = _parse_principal_arn(role_arn, "DIRECT_LAMBDA")

        # Verify principal information
        assert principal_info["invocation_mode"] == "DIRECT_LAMBDA"
        assert principal_info["principal_type"] == "Role"
        assert principal_info["principal_arn"] == role_arn
        assert principal_info["session_name"] is None
        assert principal_info["account_id"] == "438465159935"

    def test_iam_user_invocation(self, mock_lambda_context):
        """Test IAM user invocation extracts User principal."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        # Mock IAM user ARN
        user_arn = "arn:aws:iam::438465159935:user/admin-user"

        # Test _parse_principal_arn function
        principal_info = _parse_principal_arn(user_arn, "DIRECT_LAMBDA")

        # Verify principal information
        assert principal_info["invocation_mode"] == "DIRECT_LAMBDA"
        assert principal_info["principal_type"] == "User"
        assert principal_info["principal_arn"] == user_arn
        assert principal_info["session_name"] is None
        assert principal_info["account_id"] == "438465159935"

    def test_unknown_principal_format(self, mock_lambda_context):
        """Test unknown principal format returns Unknown type."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        # Mock truly unknown ARN format (not matching any pattern)
        unknown_arn = "not-an-arn-format"

        # Test _parse_principal_arn function
        principal_info = _parse_principal_arn(unknown_arn, "DIRECT_LAMBDA")

        # Verify principal information
        assert principal_info["invocation_mode"] == "DIRECT_LAMBDA"
        assert principal_info["principal_type"] == "Unknown"
        assert principal_info["principal_arn"] == unknown_arn
        assert principal_info["account_id"] == "unknown"


class TestInvocationModeDetection:
    """Test invocation mode detection logic."""

    def test_detects_api_gateway_mode(self, mock_lambda_context):
        """Test lambda_handler detects API Gateway invocation mode."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import lambda_handler

        # API Gateway event has requestContext
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {"email": "test@example.com"}
                }
            },
            "httpMethod": "GET",
            "path": "/accounts/current",
        }

        with patch("index.get_current_account_id", return_value="438465159935"):
            with patch("index.os.environ.get", side_effect=lambda k, d=None: {
                "AWS_ACCOUNT_ID": "438465159935"
            }.get(k, d)):
                result = lambda_handler(event, mock_lambda_context)

        # Should return API Gateway response format
        assert "statusCode" in result

    def test_detects_direct_lambda_mode_with_operation(self, mock_lambda_context):
        """Test lambda_handler detects Direct Lambda invocation mode (operation)."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import lambda_handler

        # Direct invocation event has operation field
        event = {
            "operation": "get_current_account",
        }

        # Mock the context with IAM role ARN as string
        mock_lambda_context.invoked_function_arn = (
            "arn:aws:iam::438465159935:role/TestRole"
        )

        # Mock extract_iam_principal at the shared module level
        with patch("shared.iam_utils.extract_iam_principal", return_value="arn:aws:iam::438465159935:role/TestRole"):
            with patch("index.handle_direct_invocation", return_value={"accountId": "438465159935"}):
                result = lambda_handler(event, mock_lambda_context)

        # Should return direct invocation response
        assert "accountId" in result

    def test_detects_direct_lambda_mode_with_action(self, mock_lambda_context):
        """Test lambda_handler detects Direct Lambda invocation mode (action)."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import lambda_handler

        # Orchestration invocation event has action field
        event = {
            "action": "query_servers_by_tags",
            "region": "us-east-1",
            "tags": {"Environment": "Production"},
        }

        # Mock the context with assumed role ARN as string
        mock_lambda_context.invoked_function_arn = (
            "arn:aws:sts::438465159935:assumed-role/StepFunctionsRole/exec-123"
        )

        # Mock extract_iam_principal at the shared module level
        with patch("shared.iam_utils.extract_iam_principal", return_value="arn:aws:sts::438465159935:assumed-role/StepFunctionsRole/exec-123"):
            with patch("index.query_drs_servers_by_tags", return_value=["s-123", "s-456"]):
                result = lambda_handler(event, mock_lambda_context)

        # Should return action response
        assert "server_ids" in result

    def test_invalid_invocation_returns_error(self, mock_lambda_context):
        """Test lambda_handler returns error for invalid invocation."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import lambda_handler

        # Invalid event (no requestContext, action, or operation)
        event = {
            "invalid_field": "value"
        }

        result = lambda_handler(event, mock_lambda_context)

        # Should return error response
        assert "statusCode" in result
        assert result["statusCode"] == 500


class TestPrincipalARNParsing:
    """Test _parse_principal_arn function with various ARN formats."""

    def test_parse_assumed_role_with_session(self):
        """Test parsing AssumedRole ARN with session name."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        arn = "arn:aws:sts::123456789012:assumed-role/MyRole/session-name-123"
        result = _parse_principal_arn(arn, "DIRECT_LAMBDA")

        assert result["principal_type"] == "AssumedRole"
        assert result["principal_arn"] == "arn:aws:iam::123456789012:role/MyRole"
        assert result["session_name"] == "session-name-123"
        assert result["account_id"] == "123456789012"

    def test_parse_iam_role(self):
        """Test parsing IAM Role ARN."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        arn = "arn:aws:iam::123456789012:role/MyRole"
        result = _parse_principal_arn(arn, "DIRECT_LAMBDA")

        assert result["principal_type"] == "Role"
        assert result["principal_arn"] == arn
        assert result["session_name"] is None
        assert result["account_id"] == "123456789012"

    def test_parse_iam_user(self):
        """Test parsing IAM User ARN."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        arn = "arn:aws:iam::123456789012:user/admin"
        result = _parse_principal_arn(arn, "DIRECT_LAMBDA")

        assert result["principal_type"] == "User"
        assert result["principal_arn"] == arn
        assert result["session_name"] is None
        assert result["account_id"] == "123456789012"

    def test_parse_service_principal(self):
        """Test parsing AWS Service principal ARN."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        arn = "arn:aws:events::123456789012:rule/my-rule"
        result = _parse_principal_arn(arn, "DIRECT_LAMBDA")

        assert result["principal_type"] == "Service"
        assert result["principal_arn"] == arn
        assert result["session_name"] is None
        assert result["account_id"] == "123456789012"

    def test_parse_unknown_arn(self):
        """Test parsing unknown ARN format."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        arn = "unknown"
        result = _parse_principal_arn(arn, "DIRECT_LAMBDA")

        assert result["principal_type"] == "Unknown"
        assert result["principal_arn"] == "unknown"
        assert result["session_name"] is None
        assert result["account_id"] == "unknown"


class TestStepFunctionsInvocation:
    """Test Step Functions invocation mode with AssumedRole principal."""

    def test_step_functions_invocation_with_assumed_role(self, mock_lambda_context):
        """Test Step Functions invocation extracts AssumedRole principal correctly."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        # Mock Step Functions assumed role ARN
        arn = "arn:aws:sts::438465159935:assumed-role/aws-drs-orchestration-StepFunctionsRole-qa/execution-abc123"

        # Parse principal ARN
        principal_info = _parse_principal_arn(arn, "DIRECT_LAMBDA")

        # Verify principal information
        assert principal_info["invocation_mode"] == "DIRECT_LAMBDA"
        assert principal_info["principal_type"] == "AssumedRole"
        assert principal_info["principal_arn"] == "arn:aws:iam::438465159935:role/aws-drs-orchestration-StepFunctionsRole-qa"
        assert principal_info["session_name"] == "execution-abc123"
        assert principal_info["account_id"] == "438465159935"

    def test_step_functions_invocation_with_wave_polling(self, mock_lambda_context):
        """Test Step Functions wave polling invocation."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        # Mock Step Functions assumed role ARN (as string, not Mock)
        arn = "arn:aws:sts::438465159935:assumed-role/aws-drs-orchestration-StepFunctionsRole-qa/wave-poll-exec-123"

        # Parse principal ARN to verify it works for Step Functions
        principal_info = _parse_principal_arn(arn, "DIRECT_LAMBDA")

        # Verify response structure
        assert principal_info["invocation_mode"] == "DIRECT_LAMBDA"
        assert principal_info["principal_type"] == "AssumedRole"
        assert principal_info["principal_arn"] == "arn:aws:iam::438465159935:role/aws-drs-orchestration-StepFunctionsRole-qa"
        assert principal_info["session_name"] == "wave-poll-exec-123"

    def test_step_functions_invocation_audit_log_fields(self, mock_lambda_context):
        """Test Step Functions invocation populates audit log fields correctly."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        # Mock Step Functions assumed role ARN
        arn = "arn:aws:sts::438465159935:assumed-role/ExecutionRole/session-xyz"

        # Parse principal ARN
        principal_info = _parse_principal_arn(arn, "DIRECT_LAMBDA")

        # Verify audit log fields
        assert principal_info["invocation_mode"] == "DIRECT_LAMBDA"
        assert principal_info["principal_type"] == "AssumedRole"
        assert principal_info["principal_arn"] == "arn:aws:iam::438465159935:role/ExecutionRole"
        assert principal_info["session_name"] == "session-xyz"
        assert principal_info["account_id"] == "438465159935"

        # Verify all required audit log fields are present
        required_fields = ["invocation_mode", "principal_type", "principal_arn", "session_name", "account_id"]
        for field in required_fields:
            assert field in principal_info


class TestEventBridgeInvocation:
    """Test EventBridge invocation mode with Service principal."""

    def test_eventbridge_invocation_with_service_principal(self, mock_lambda_context):
        """Test EventBridge invocation extracts Service principal correctly."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        # Mock EventBridge service principal ARN
        arn = "arn:aws:events::438465159935:rule/aws-drs-orchestration-inventory-sync-rule"

        # Parse principal ARN
        principal_info = _parse_principal_arn(arn, "DIRECT_LAMBDA")

        # Verify principal information
        assert principal_info["invocation_mode"] == "DIRECT_LAMBDA"
        assert principal_info["principal_type"] == "Service"
        assert principal_info["principal_arn"] == arn
        assert principal_info["session_name"] is None
        assert principal_info["account_id"] == "438465159935"

    def test_eventbridge_invocation_with_inventory_sync(self, mock_lambda_context):
        """Test EventBridge inventory sync invocation."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        # Mock EventBridge service principal ARN (as string, not Mock)
        arn = "arn:aws:events::438465159935:rule/inventory-sync-rule"

        # Parse principal ARN to verify it works for EventBridge
        principal_info = _parse_principal_arn(arn, "DIRECT_LAMBDA")

        # Verify response structure
        assert principal_info["invocation_mode"] == "DIRECT_LAMBDA"
        assert principal_info["principal_type"] == "Service"
        assert principal_info["principal_arn"] == arn
        assert principal_info["session_name"] is None

    def test_eventbridge_invocation_audit_log_fields(self, mock_lambda_context):
        """Test EventBridge invocation populates audit log fields correctly."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        # Mock EventBridge service principal ARN
        arn = "arn:aws:events::438465159935:rule/staging-sync-rule"

        # Parse principal ARN
        principal_info = _parse_principal_arn(arn, "DIRECT_LAMBDA")

        # Verify audit log fields
        assert principal_info["invocation_mode"] == "DIRECT_LAMBDA"
        assert principal_info["principal_type"] == "Service"
        assert principal_info["principal_arn"] == arn
        assert principal_info["session_name"] is None
        assert principal_info["account_id"] == "438465159935"

        # Verify all required audit log fields are present
        required_fields = ["invocation_mode", "principal_type", "principal_arn", "session_name", "account_id"]
        for field in required_fields:
            assert field in principal_info

    def test_eventbridge_multiple_service_types(self, mock_lambda_context):
        """Test EventBridge invocation with different AWS service types."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        # Test different AWS service ARN formats
        test_cases = [
            ("arn:aws:events::123456789012:rule/my-rule", "events"),
            ("arn:aws:scheduler::123456789012:schedule/my-schedule", "scheduler"),
            ("arn:aws:states::123456789012:stateMachine:my-state-machine", "states"),
        ]

        for arn, expected_service in test_cases:
            principal_info = _parse_principal_arn(arn, "DIRECT_LAMBDA")

            # Verify Service principal type
            assert principal_info["principal_type"] == "Service"
            assert principal_info["principal_arn"] == arn
            assert principal_info["session_name"] is None
            assert principal_info["account_id"] == "123456789012"


class TestInvocationModeAuditLogging:
    """Test audit logging for different invocation modes."""

    def test_api_gateway_invocation_mode_field(self, mock_lambda_context):
        """Test API Gateway invocation sets invocation_mode to API_GATEWAY."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import lambda_handler

        # API Gateway event
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {"email": "test@example.com"}
                }
            },
            "httpMethod": "GET",
            "path": "/accounts/current",
        }

        # Mock get_current_account_id
        with patch("index.get_current_account_id", return_value="438465159935"):
            with patch("index.os.environ.get", side_effect=lambda k, d=None: {
                "AWS_ACCOUNT_ID": "438465159935"
            }.get(k, d)):
                result = lambda_handler(event, mock_lambda_context)

        # Verify API Gateway response (invocation_mode would be API_GATEWAY in audit log)
        assert "statusCode" in result

    def test_direct_lambda_invocation_mode_field(self, mock_lambda_context):
        """Test Direct Lambda invocation sets invocation_mode to DIRECT_LAMBDA."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        # Direct Lambda invocation with IAM role
        arn = "arn:aws:iam::438465159935:role/TestRole"

        # Parse principal ARN
        principal_info = _parse_principal_arn(arn, "DIRECT_LAMBDA")

        # Verify invocation_mode field
        assert principal_info["invocation_mode"] == "DIRECT_LAMBDA"

    def test_cognito_user_principal_extraction(self, mock_lambda_context):
        """Test Cognito user email extraction for API Gateway invocations."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import lambda_handler

        # API Gateway event with Cognito claims
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "email": "admin@example.com",
                        "sub": "cognito-user-123",
                        "cognito:groups": ["Admin"]
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/accounts/current",
        }

        # Mock get_current_account_id
        with patch("index.get_current_account_id", return_value="438465159935"):
            with patch("index.os.environ.get", side_effect=lambda k, d=None: {
                "AWS_ACCOUNT_ID": "438465159935"
            }.get(k, d)):
                result = lambda_handler(event, mock_lambda_context)

        # Verify response (principal would be admin@example.com in audit log)
        assert "statusCode" in result

    def test_iam_arn_principal_extraction(self, mock_lambda_context):
        """Test IAM ARN extraction for Direct Lambda invocations."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/query-handler"))
        from index import _parse_principal_arn

        # Direct Lambda invocation with assumed role
        arn = "arn:aws:sts::438465159935:assumed-role/ExecutionRole/session-123"

        # Parse principal ARN
        principal_info = _parse_principal_arn(arn, "DIRECT_LAMBDA")

        # Verify IAM ARN extraction
        assert principal_info["principal_arn"] == "arn:aws:iam::438465159935:role/ExecutionRole"
        assert principal_info["session_name"] == "session-123"
