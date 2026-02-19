"""
Integration tests for Launch Config API endpoints.

Tests the apply-launch-configs and get-launch-config-status endpoints
via both Frontend (API Gateway with Cognito) and API (API Gateway with IAM)
invocation methods.

Feature: launch-config-preapplication
Requirements: 5.3, 5.6

Note: These are integration tests that test the actual handler logic
with moto for AWS service mocking. They focus on testing the integration
between components rather than unit testing individual functions.
"""

import json
import os
import sys
import uuid
import importlib
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import boto3
from moto import mock_aws

# Add lambda directories to path
lambda_base = Path(__file__).parent.parent.parent / "lambda"
sys.path.insert(0, str(lambda_base))
sys.path.insert(0, str(lambda_base / "data-management-handler"))
sys.path.insert(0, str(lambda_base / "shared"))

# Set environment variables before importing
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
os.environ["TAG_SYNC_CONFIG_TABLE"] = "test-tag-sync-config"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_REGION"] = "us-east-1"

# Import handler after path setup
data_management_handler = importlib.import_module(
    "data-management-handler.index"
)
lambda_handler = data_management_handler.lambda_handler


def get_mock_context():
    """Create mock Lambda context."""
    context = Mock()
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:123456789012:function:data-management-handler"
    )
    context.request_id = "test-request-123"
    context.function_name = "data-management-handler"
    context.memory_limit_in_mb = 512
    context.aws_request_id = "test-request-123"
    return context


def get_mock_principal_arn():
    """Return a valid IAM principal ARN for testing."""
    return "arn:aws:iam::123456789012:role/OrchestrationRole"


def setup_dynamodb_tables():
    """Set up DynamoDB tables for testing."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create protection groups table
    table = dynamodb.create_table(
        TableName="test-protection-groups",
        KeySchema=[{"AttributeName": "groupId", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "groupId", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Reset module-level table cache to use mocked DynamoDB
    data_management_handler._protection_groups_table = None
    data_management_handler.dynamodb = dynamodb

    # Also reset launch_config_service module cache
    from shared import launch_config_service
    launch_config_service._protection_groups_table = None
    launch_config_service._dynamodb = None

    return table


def create_protection_group_item(group_id: str, with_status: bool = False):
    """Create a protection group item for DynamoDB."""
    item = {
        "groupId": group_id,
        "groupName": "Test Protection Group",
        "description": "Test description",
        "region": "us-east-1",
        "sourceServerIds": ["s-1234567890abcdef0", "s-abcdef1234567890a"],
        "serverSelectionTags": {"Environment": "Test"},
        "launchConfig": {
            "instanceType": "t3.medium",
            "subnetId": "subnet-12345678",
        },
        "servers": [],
        "version": 1,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "updatedAt": datetime.utcnow().isoformat() + "Z",
    }

    if with_status:
        item["launchConfigStatus"] = {
            "status": "ready",
            "lastApplied": datetime.utcnow().isoformat() + "Z",
            "appliedBy": "test@example.com",
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": datetime.utcnow().isoformat() + "Z",
                    "configHash": "sha256:abc123def456",
                    "errors": [],
                },
                "s-abcdef1234567890a": {
                    "status": "ready",
                    "lastApplied": datetime.utcnow().isoformat() + "Z",
                    "configHash": "sha256:def456abc123",
                    "errors": [],
                },
            },
            "errors": [],
        }

    return item


# ============================================================================
# Test: Apply Launch Configs - Frontend Invocation (API Gateway + Cognito)
# ============================================================================


class TestApplyLaunchConfigsFrontendInvocation:
    """
    Test apply-launch-configs endpoint via Frontend invocation.

    Frontend invocation uses API Gateway with Cognito authentication.
    Event structure includes requestContext with authorizer claims.

    Validates: Requirements 5.3, 5.6
    """

    @mock_aws
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    def test_apply_launch_configs_frontend_success(
        self,
        mock_apply_configs,
    ):
        """
        Test successful apply-launch-configs via Frontend invocation.

        Validates:
        - API Gateway event detection
        - Cognito user extraction
        - Correct routing to apply_launch_configs function
        - Response format with statusCode
        """
        table = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Add protection group without status (not_configured)
        table.put_item(Item=create_protection_group_item(group_id))

        # Mock apply_launch_configs_to_group
        mock_apply_configs.return_value = {
            "status": "ready",
            "appliedServers": 2,
            "failedServers": 0,
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": datetime.utcnow().isoformat() + "Z",
                    "configHash": "sha256:abc123",
                    "errors": [],
                },
            },
            "errors": [],
        }

        # Frontend invocation event (API Gateway with Cognito)
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123",
                        "email": "test@example.com",
                        "cognito:username": "testuser",
                        "cognito:groups": "Admins",
                    }
                }
            },
            "httpMethod": "POST",
            "path": f"/protection-groups/{group_id}/apply-launch-configs",
            "pathParameters": {"id": group_id},
            "queryStringParameters": {},
            "body": json.dumps({"force": True}),
        }
        context = get_mock_context()

        result = lambda_handler(event, context)

        # Verify API Gateway response format
        assert "statusCode" in result
        assert "body" in result
        assert "headers" in result

        # Verify success status
        assert result["statusCode"] == 200

        # Verify response body
        body = json.loads(result["body"])
        assert body["groupId"] == group_id
        assert body["status"] == "ready"
        assert body["appliedServers"] == 2
        assert body["failedServers"] == 0


    @mock_aws
    def test_apply_launch_configs_frontend_already_ready(self):
        """
        Test apply-launch-configs when configs already ready (no force).

        Validates:
        - Skip re-apply when status is ready and force=false
        - Return message indicating already applied
        """
        table = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Add protection group with ready status
        table.put_item(Item=create_protection_group_item(group_id, with_status=True))

        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123",
                        "email": "test@example.com",
                        "cognito:username": "testuser",
                    }
                }
            },
            "httpMethod": "POST",
            "path": f"/protection-groups/{group_id}/apply-launch-configs",
            "pathParameters": {"id": group_id},
            "queryStringParameters": {},
            "body": json.dumps({"force": False}),
        }
        context = get_mock_context()

        result = lambda_handler(event, context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "ready"
        assert "message" in body
        assert "already applied" in body["message"].lower()

    @mock_aws
    def test_apply_launch_configs_frontend_group_not_found(self):
        """
        Test apply-launch-configs when protection group not found.

        Validates:
        - 404 response for non-existent group
        - Error message clarity
        """
        setup_dynamodb_tables()
        group_id = str(uuid.uuid4())  # Non-existent group

        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123",
                        "email": "test@example.com",
                        "cognito:username": "testuser",
                    }
                }
            },
            "httpMethod": "POST",
            "path": f"/protection-groups/{group_id}/apply-launch-configs",
            "pathParameters": {"id": group_id},
            "queryStringParameters": {},
            "body": json.dumps({}),
        }
        context = get_mock_context()

        result = lambda_handler(event, context)

        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert "error" in body
        assert "not found" in body.get("message", "").lower()

    @mock_aws
    def test_apply_launch_configs_frontend_no_servers(self):
        """
        Test apply-launch-configs when protection group has no servers.

        Validates:
        - 400 response for group without servers
        - Error message clarity
        """
        table = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Add protection group without servers
        item = create_protection_group_item(group_id)
        item["sourceServerIds"] = []  # No servers
        table.put_item(Item=item)

        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123",
                        "email": "test@example.com",
                        "cognito:username": "testuser",
                    }
                }
            },
            "httpMethod": "POST",
            "path": f"/protection-groups/{group_id}/apply-launch-configs",
            "pathParameters": {"id": group_id},
            "queryStringParameters": {},
            "body": json.dumps({"force": True}),
        }
        context = get_mock_context()

        result = lambda_handler(event, context)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "error" in body
        assert "no servers" in body.get("message", "").lower()


# ============================================================================
# Test: Apply Launch Configs - API Invocation (API Gateway + IAM)
# ============================================================================


class TestApplyLaunchConfigsAPIInvocation:
    """
    Test apply-launch-configs endpoint via API invocation.

    API invocation uses API Gateway with IAM authentication.
    Event structure includes requestContext with identity.

    Validates: Requirements 5.3, 5.6
    """

    @mock_aws
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    def test_apply_launch_configs_api_success(self, mock_apply_configs):
        """
        Test successful apply-launch-configs via API invocation (IAM auth).

        Validates:
        - API Gateway event detection with IAM auth
        - Correct routing to apply_launch_configs function
        - Response format with statusCode
        """
        table = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        table.put_item(Item=create_protection_group_item(group_id))

        mock_apply_configs.return_value = {
            "status": "ready",
            "appliedServers": 2,
            "failedServers": 0,
            "serverConfigs": {},
            "errors": [],
        }

        # API invocation event (API Gateway with IAM auth)
        event = {
            "requestContext": {
                "identity": {
                    "userArn": "arn:aws:iam::123456789012:user/api-user",
                    "accountId": "123456789012",
                }
            },
            "httpMethod": "POST",
            "path": f"/protection-groups/{group_id}/apply-launch-configs",
            "pathParameters": {"id": group_id},
            "queryStringParameters": {},
            "body": json.dumps({"force": True}),
        }
        context = get_mock_context()

        result = lambda_handler(event, context)

        assert "statusCode" in result
        assert result["statusCode"] == 200

        body = json.loads(result["body"])
        assert body["groupId"] == group_id
        assert body["status"] == "ready"

    @mock_aws
    @patch("shared.launch_config_service.apply_launch_configs_to_group")
    def test_apply_launch_configs_api_with_force(self, mock_apply_configs):
        """
        Test apply-launch-configs with force=true via API invocation.

        Validates:
        - Force flag triggers re-apply even when status is ready
        - apply_launch_configs_to_group is called
        """
        table = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Add group with ready status
        table.put_item(Item=create_protection_group_item(group_id, with_status=True))

        mock_apply_configs.return_value = {
            "status": "ready",
            "appliedServers": 2,
            "failedServers": 0,
            "serverConfigs": {},
            "errors": [],
        }

        event = {
            "requestContext": {
                "identity": {
                    "userArn": "arn:aws:iam::123456789012:user/api-user",
                }
            },
            "httpMethod": "POST",
            "path": f"/protection-groups/{group_id}/apply-launch-configs",
            "pathParameters": {"id": group_id},
            "queryStringParameters": {},
            "body": json.dumps({"force": True}),
        }
        context = get_mock_context()

        result = lambda_handler(event, context)

        assert result["statusCode"] == 200
        # Verify apply was called (force=true)
        mock_apply_configs.assert_called_once()


# ============================================================================
# Test: Get Launch Config Status - Frontend Invocation (API Gateway + Cognito)
# ============================================================================


class TestGetLaunchConfigStatusFrontendInvocation:
    """
    Test get-launch-config-status endpoint via Frontend invocation.

    Frontend invocation uses API Gateway with Cognito authentication.

    Validates: Requirements 5.3, 5.6
    """

    @mock_aws
    def test_get_launch_config_status_frontend_success(self):
        """
        Test successful get-launch-config-status via Frontend invocation.

        Validates:
        - API Gateway event detection
        - Cognito user extraction
        - Correct routing to get_launch_config_status function
        - Response format with statusCode
        """
        table = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Add protection group with ready status
        table.put_item(Item=create_protection_group_item(group_id, with_status=True))

        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123",
                        "email": "test@example.com",
                        "cognito:username": "testuser",
                        "cognito:groups": "Admins",
                    }
                }
            },
            "httpMethod": "GET",
            "path": f"/protection-groups/{group_id}/launch-config-status",
            "pathParameters": {"id": group_id},
            "queryStringParameters": {},
            "body": None,
        }
        context = get_mock_context()

        result = lambda_handler(event, context)

        assert "statusCode" in result
        assert "body" in result
        assert "headers" in result
        assert result["statusCode"] == 200

        body = json.loads(result["body"])
        assert body["status"] == "ready"
        assert "serverConfigs" in body
        assert "lastApplied" in body

    @mock_aws
    def test_get_launch_config_status_frontend_not_configured(self):
        """
        Test get-launch-config-status when configs not configured.

        Validates:
        - Returns not_configured status for groups without config
        - Response includes empty serverConfigs
        """
        table = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Add protection group without status
        table.put_item(Item=create_protection_group_item(group_id, with_status=False))

        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123",
                        "email": "test@example.com",
                        "cognito:username": "testuser",
                    }
                }
            },
            "httpMethod": "GET",
            "path": f"/protection-groups/{group_id}/launch-config-status",
            "pathParameters": {"id": group_id},
            "queryStringParameters": {},
            "body": None,
        }
        context = get_mock_context()

        result = lambda_handler(event, context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "not_configured"
        assert body["serverConfigs"] == {}

    @mock_aws
    def test_get_launch_config_status_frontend_group_not_found(self):
        """
        Test get-launch-config-status when protection group not found.

        Validates:
        - 404 response for non-existent group
        - Error message clarity
        """
        setup_dynamodb_tables()
        group_id = str(uuid.uuid4())  # Non-existent group

        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123",
                        "email": "test@example.com",
                        "cognito:username": "testuser",
                    }
                }
            },
            "httpMethod": "GET",
            "path": f"/protection-groups/{group_id}/launch-config-status",
            "pathParameters": {"id": group_id},
            "queryStringParameters": {},
            "body": None,
        }
        context = get_mock_context()

        result = lambda_handler(event, context)

        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert "error" in body
        assert "not found" in body.get("message", "").lower()


# ============================================================================
# Test: Get Launch Config Status - API Invocation (API Gateway + IAM)
# ============================================================================


class TestGetLaunchConfigStatusAPIInvocation:
    """
    Test get-launch-config-status endpoint via API invocation.

    API invocation uses API Gateway with IAM authentication.

    Validates: Requirements 5.3, 5.6
    """

    @mock_aws
    def test_get_launch_config_status_api_success(self):
        """
        Test successful get-launch-config-status via API invocation (IAM).

        Validates:
        - API Gateway event detection with IAM auth
        - Correct routing to get_launch_config_status function
        - Response format with statusCode
        """
        table = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        table.put_item(Item=create_protection_group_item(group_id, with_status=True))

        event = {
            "requestContext": {
                "identity": {
                    "userArn": "arn:aws:iam::123456789012:user/api-user",
                    "accountId": "123456789012",
                }
            },
            "httpMethod": "GET",
            "path": f"/protection-groups/{group_id}/launch-config-status",
            "pathParameters": {"id": group_id},
            "queryStringParameters": {},
            "body": None,
        }
        context = get_mock_context()

        result = lambda_handler(event, context)

        assert "statusCode" in result
        assert result["statusCode"] == 200

        body = json.loads(result["body"])
        assert body["status"] == "ready"
        assert "serverConfigs" in body

    @mock_aws
    def test_get_launch_config_status_api_with_failed_servers(self):
        """
        Test get-launch-config-status with failed server configs.

        Validates:
        - Failed status is returned correctly
        - Per-server errors are included
        """
        table = setup_dynamodb_tables()
        group_id = str(uuid.uuid4())

        # Create item with failed status
        item = create_protection_group_item(group_id)
        item["launchConfigStatus"] = {
            "status": "failed",
            "lastApplied": datetime.utcnow().isoformat() + "Z",
            "appliedBy": "api-user",
            "serverConfigs": {
                "s-1234567890abcdef0": {
                    "status": "ready",
                    "lastApplied": datetime.utcnow().isoformat() + "Z",
                    "configHash": "sha256:abc123",
                    "errors": [],
                },
                "s-abcdef1234567890a": {
                    "status": "failed",
                    "lastApplied": datetime.utcnow().isoformat() + "Z",
                    "configHash": None,
                    "errors": ["DRS API timeout"],
                },
            },
            "errors": ["1 server(s) failed configuration"],
        }
        table.put_item(Item=item)

        event = {
            "requestContext": {
                "identity": {
                    "userArn": "arn:aws:iam::123456789012:user/api-user",
                }
            },
            "httpMethod": "GET",
            "path": f"/protection-groups/{group_id}/launch-config-status",
            "pathParameters": {"id": group_id},
            "queryStringParameters": {},
            "body": None,
        }
        context = get_mock_context()

        result = lambda_handler(event, context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "failed"
        assert len(body["errors"]) > 0
        # Verify per-server status
        server_configs = body["serverConfigs"]
        assert server_configs["s-abcdef1234567890a"]["status"] == "failed"
        assert len(server_configs["s-abcdef1234567890a"]["errors"]) > 0
