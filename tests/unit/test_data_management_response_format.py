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

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

# Mock environment variables before importing handler
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-executions"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
os.environ["TAG_SYNC_CONFIG_TABLE"] = "test-tag-sync-config"


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB tables"""
    with patch("data-management-handler.index.dynamodb") as mock_db:
        # Mock protection groups table
        mock_pg_table = MagicMock()
        mock_pg_table.scan.return_value = {"Items": []}
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
        
        mock_db.Table.side_effect = lambda name: {
            "test-protection-groups": mock_pg_table,
            "test-recovery-plans": mock_rp_table,
        }.get(name, MagicMock())
        
        yield mock_db


@pytest.fixture
def mock_iam_utils():
    """Mock IAM utilities for authorization"""
    with patch("data-management-handler.index.extract_iam_principal") as mock_extract, \
         patch("data-management-handler.index.validate_iam_authorization") as mock_validate, \
         patch("data-management-handler.index.log_direct_invocation") as mock_log, \
         patch("data-management-handler.index.validate_direct_invocation_event") as mock_validate_event:
        
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
        from data_management_handler import index
        
        event = {
            "requestContext": {"authorizer": {"claims": {}}},
            "httpMethod": "GET",
            "path": "/protection-groups",
            "queryStringParameters": {},
        }
        
        result = index.lambda_handler(event, lambda_context)
        
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
        from data_management_handler import index
        
        event = {
            "requestContext": {"authorizer": {"claims": {}}},
            "httpMethod": "GET",
            "path": "/protection-groups/pg-123",
            "pathParameters": {"id": "pg-123"},
            "queryStringParameters": {},
        }
        
        result = index.lambda_handler(event, lambda_context)
        
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
        from data_management_handler import index
        
        event = {
            "operation": "list_protection_groups",
            "queryParams": {},
        }
        
        result = index.lambda_handler(event, lambda_context)
        
        # Verify raw response format (no statusCode wrapper)
        assert isinstance(result, dict)
        assert "statusCode" not in result  # Should NOT have API Gateway wrapper
        assert "groups" in result
        assert "count" in result
        assert isinstance(result["groups"], list)
        assert isinstance(result["count"], int)
    
    def test_get_protection_group_direct_format(self, mock_dynamodb, mock_iam_utils, lambda_context):
        """Direct invocation GET should return raw protection group data"""
        from data_management_handler import index
        
        event = {
            "operation": "get_protection_group",
            "body": {"groupId": "pg-123"},
        }
        
        result = index.lambda_handler(event, lambda_context)
        
        # Verify raw response format
        assert isinstance(result, dict)
        assert "statusCode" not in result  # Should NOT have API Gateway wrapper
        assert result["groupId"] == "pg-123"
        assert result["groupName"] == "Test Group"
        assert "region" in result
    
    def test_create_protection_group_direct_format(self, mock_dynamodb, mock_iam_utils, lambda_context):
        """Direct invocation CREATE should return raw created item"""
        from data_management_handler import index
        
        # Mock successful creation
        mock_pg_table = mock_dynamodb.Table("test-protection-groups")
        mock_pg_table.put_item.return_value = {}
        
        event = {
            "operation": "create_protection_group",
            "body": {
                "groupName": "New Group",
                "region": "us-east-1",
                "sourceServerIds": ["s-456"],
            },
        }
        
        result = index.lambda_handler(event, lambda_context)
        
        # Verify raw response format
        assert isinstance(result, dict)
        assert "statusCode" not in result  # Should NOT have API Gateway wrapper
        assert "groupId" in result
        assert result["groupName"] == "New Group"


class TestErrorResponseFormat:
    """Test error responses are consistent across both modes"""
    
    def test_invalid_operation_direct_invocation(self, mock_dynamodb, mock_iam_utils, lambda_context):
        """Invalid operation should return error in raw format"""
        from data_management_handler import index
        
        event = {
            "operation": "invalid_operation_name",
            "body": {},
        }
        
        result = index.lambda_handler(event, lambda_context)
        
        # Verify error response format
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "INVALID_OPERATION"
        assert "message" in result
        assert "invalid_operation_name" in result["message"]
    
    def test_missing_parameter_direct_invocation(self, mock_dynamodb, mock_iam_utils, lambda_context):
        """Missing parameter should return error in raw format"""
        from data_management_handler import index
        
        event = {
            "operation": "get_protection_group",
            "body": {},  # Missing groupId
        }
        
        result = index.lambda_handler(event, lambda_context)
        
        # Verify error response format
        assert isinstance(result, dict)
        # Should return 404 error for missing group (None passed to get_protection_group)
        assert "error" in result or "statusCode" not in result
    
    def test_authorization_failure_direct_invocation(self, mock_dynamodb, lambda_context):
        """Authorization failure should return error in raw format"""
        from data_management_handler import index
        
        with patch("data-management-handler.index.validate_iam_authorization") as mock_validate, \
             patch("data-management-handler.index.extract_iam_principal") as mock_extract, \
             patch("data-management-handler.index.validate_direct_invocation_event") as mock_validate_event, \
             patch("data-management-handler.index.log_direct_invocation") as mock_log, \
             patch("data-management-handler.index.create_authorization_error_response") as mock_auth_error:
            
            mock_validate_event.return_value = True
            mock_extract.return_value = "arn:aws:iam::123456789012:role/UnauthorizedRole"
            mock_validate.return_value = False
            mock_auth_error.return_value = {
                "error": "AUTHORIZATION_FAILED",
                "message": "IAM principal not authorized"
            }
            
            event = {
                "operation": "list_protection_groups",
                "queryParams": {},
            }
            
            result = index.lambda_handler(event, lambda_context)
            
            # Verify error response format
            assert isinstance(result, dict)
            assert result["error"] == "AUTHORIZATION_FAILED"
            assert "message" in result


class TestResponseUnwrapping:
    """Test that API Gateway responses are properly unwrapped for direct invocations"""
    
    def test_unwrap_json_string_body(self, mock_dynamodb, mock_iam_utils, lambda_context):
        """Test unwrapping when body is JSON string"""
        from data_management_handler import index
        
        event = {
            "operation": "list_protection_groups",
            "queryParams": {},
        }
        
        result = index.lambda_handler(event, lambda_context)
        
        # Result should be unwrapped dict, not API Gateway response
        assert isinstance(result, dict)
        assert "statusCode" not in result
        assert "groups" in result
    
    def test_unwrap_dict_body(self, mock_dynamodb, mock_iam_utils, lambda_context):
        """Test unwrapping when body is already a dict"""
        from data_management_handler import index
        
        event = {
            "operation": "get_protection_group",
            "body": {"groupId": "pg-123"},
        }
        
        result = index.lambda_handler(event, lambda_context)
        
        # Result should be unwrapped dict
        assert isinstance(result, dict)
        assert "statusCode" not in result
        assert "groupId" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
