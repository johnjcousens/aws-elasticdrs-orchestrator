"""
Unit tests for data-management-handler recovery instance sync integration.

Tests EventBridge event detection, API Gateway routing for sync endpoints,
direct invocation operations, and cache query functions.

Test Coverage:
- EventBridge event detection in lambda_handler()
- API Gateway routing for /drs/recovery-instance-sync endpoints
- Direct invocation for sync_recovery_instances and get_recovery_instance_sync_status
- Cache query functions in check_existing_recovery_instances()
"""

import json
import os
import sys
from contextlib import contextmanager
from unittest.mock import MagicMock, Mock, patch

import pytest


lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
data_management_handler_dir = os.path.join(lambda_dir, "data-management-handler")


@contextmanager
def setup_dm_test_environment():
    """Context manager to set up test environment for data-management-handler tests."""
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    if "index" in sys.modules:
        del sys.modules["index"]

    sys.path.insert(0, data_management_handler_dir)
    sys.path.insert(0, lambda_dir)

    with patch.dict(
        os.environ,
        {
            "PROTECTION_GROUPS_TABLE": "test-protection-groups",
            "RECOVERY_PLANS_TABLE": "test-recovery-plans",
            "EXECUTION_HISTORY_TABLE": "test-execution-history",
            "TARGET_ACCOUNTS_TABLE": "test-target-accounts",
            "TAG_SYNC_CONFIG_TABLE": "test-tag-sync-config",
            "SOURCE_SERVER_INVENTORY_TABLE": "test-inventory",
            "RECOVERY_INSTANCES_TABLE": "test-recovery-instances",
        },
    ):
        # Mock shared modules before importing index
        sys.modules["shared"] = Mock()
        sys.modules["shared.account_utils"] = Mock()
        sys.modules["shared.security_utils"] = Mock()
        sys.modules["shared.notifications"] = Mock()
        sys.modules["shared.conflict_detection"] = Mock()
        sys.modules["shared.config_merge"] = Mock()
        sys.modules["shared.cross_account"] = Mock()
        sys.modules["shared.drs_regions"] = Mock()
        sys.modules["shared.drs_regions"].DRS_REGIONS = ["us-east-1", "us-east-2"]
        sys.modules["shared.active_region_filter"] = Mock()
        sys.modules["shared.launch_config_service"] = Mock()
        sys.modules["shared.iam_utils"] = Mock()
        sys.modules["shared.recovery_instance_sync"] = Mock()

        mock_response_utils = Mock()

        def mock_response(status_code, body, headers=None):
            return {
                "statusCode": status_code,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(body, default=str),
            }

        def mock_error_response(code, message, details=None):
            result = {"error": code, "message": message}
            if details:
                result["details"] = details
            return result

        mock_response_utils.response = mock_response
        mock_response_utils.error_response = mock_error_response
        mock_response_utils.DecimalEncoder = json.JSONEncoder
        mock_response_utils.ERROR_MISSING_PARAMETER = "MISSING_PARAMETER"
        mock_response_utils.ERROR_INVALID_PARAMETER = "INVALID_PARAMETER"
        mock_response_utils.ERROR_NOT_FOUND = "NOT_FOUND"
        mock_response_utils.ERROR_DYNAMODB_ERROR = "DYNAMODB_ERROR"
        mock_response_utils.ERROR_INTERNAL_ERROR = "INTERNAL_ERROR"
        sys.modules["shared.response_utils"] = mock_response_utils

        try:
            yield
        finally:
            sys.path = original_path
            if "index" in sys.modules:
                del sys.modules["index"]
            if original_index is not None:
                sys.modules["index"] = original_index
            for module_name in list(sys.modules.keys()):
                if module_name.startswith("shared"):
                    del sys.modules[module_name]


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table."""
    return MagicMock()


@pytest.fixture
def dm_handler_module(mock_dynamodb_table):
    """Import data-management-handler with mocked dependencies."""
    with setup_dm_test_environment():
        with patch("boto3.resource") as mock_resource, patch("boto3.client"):
            mock_resource.return_value.Table.return_value = mock_dynamodb_table
            import index

            yield index, mock_dynamodb_table



# ============================================================================
# 12.1 - EventBridge Event Detection Tests
# ============================================================================


class TestEventBridgeSyncDetection:
    """Test EventBridge recovery instance sync event detection in lambda_handler()."""

    def test_eventbridge_sync_event_detected(self, dm_handler_module):
        """EventBridge event with operation=sync_recovery_instances routes to sync handler."""
        index_module, _ = dm_handler_module

        mock_sync_result = {"instancesUpdated": 5, "regionsScanned": 2, "errors": []}

        with patch.object(index_module, "handle_recovery_instance_sync") as mock_sync:
            mock_sync.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(mock_sync_result),
            }

            event = {"operation": "sync_recovery_instances"}
            result = index_module.lambda_handler(event, None)

            mock_sync.assert_called_once()
            assert result["statusCode"] == 200

    def test_eventbridge_sync_event_not_confused_with_direct_invocation(self, dm_handler_module):
        """EventBridge sync event should NOT route to handle_direct_invocation."""
        index_module, _ = dm_handler_module

        with patch.object(index_module, "handle_recovery_instance_sync") as mock_sync, \
             patch.object(index_module, "handle_direct_invocation") as mock_direct:
            mock_sync.return_value = {"statusCode": 200, "body": "{}"}

            event = {"operation": "sync_recovery_instances"}
            index_module.lambda_handler(event, None)

            mock_sync.assert_called_once()
            mock_direct.assert_not_called()

    def test_eventbridge_tag_sync_event_still_works(self, dm_handler_module):
        """Tag sync EventBridge events should still route correctly."""
        index_module, _ = dm_handler_module

        with patch.object(index_module, "handle_drs_tag_sync") as mock_tag_sync:
            mock_tag_sync.return_value = {"statusCode": 200, "body": "{}"}

            event = {"synch_tags": True, "synch_instance_type": True}
            index_module.lambda_handler(event, None)

            mock_tag_sync.assert_called_once_with(event)

    def test_other_operations_route_to_direct_invocation(self, dm_handler_module):
        """Non-sync operations with 'operation' key route to direct invocation."""
        index_module, _ = dm_handler_module

        with patch.object(index_module, "handle_direct_invocation") as mock_direct:
            mock_direct.return_value = {"statusCode": 200, "body": "{}"}

            event = {"operation": "list_protection_groups"}
            index_module.lambda_handler(event, None)

            mock_direct.assert_called_once()

    def test_api_gateway_event_routes_correctly(self, dm_handler_module):
        """API Gateway events with requestContext route to API handler."""
        index_module, _ = dm_handler_module

        with patch.object(index_module, "handle_api_gateway_request") as mock_api:
            mock_api.return_value = {"statusCode": 200, "body": "{}"}

            event = {"requestContext": {"stage": "dev"}, "httpMethod": "GET", "path": "/protection-groups"}
            index_module.lambda_handler(event, None)

            mock_api.assert_called_once()

    def test_invalid_event_returns_400(self, dm_handler_module):
        """Events without recognized keys return 400."""
        index_module, _ = dm_handler_module

        event = {"unknown_key": "value"}
        result = index_module.lambda_handler(event, None)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert body["error"] == "INVALID_INVOCATION"

    def test_eventbridge_sync_error_returns_500(self, dm_handler_module):
        """Errors during EventBridge sync handling return 500."""
        index_module, _ = dm_handler_module

        with patch.object(index_module, "handle_recovery_instance_sync") as mock_sync:
            mock_sync.side_effect = Exception("Sync failed unexpectedly")

            event = {"operation": "sync_recovery_instances"}
            result = index_module.lambda_handler(event, None)

            assert result["statusCode"] == 500



# ============================================================================
# 12.2 - API Gateway Routing Tests
# ============================================================================


class TestApiGatewayRoutingSync:
    """Test API Gateway routing for recovery instance sync endpoints."""

    def test_post_recovery_instance_sync(self, dm_handler_module):
        """POST /drs/recovery-instance-sync routes to handle_recovery_instance_sync."""
        index_module, _ = dm_handler_module

        with patch.object(index_module, "handle_recovery_instance_sync") as mock_sync:
            mock_sync.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"instancesUpdated": 3}),
            }

            event = {
                "requestContext": {"stage": "dev"},
                "httpMethod": "POST",
                "path": "/drs/recovery-instance-sync",
                "body": "{}",
                "pathParameters": {},
                "queryStringParameters": {},
            }
            result = index_module.handle_api_gateway_request(event, None)

            mock_sync.assert_called_once()
            assert result["statusCode"] == 200

    def test_get_recovery_instance_sync_status(self, dm_handler_module):
        """GET /drs/recovery-instance-sync routes to get_recovery_instance_sync_status."""
        index_module, _ = dm_handler_module

        with patch.object(index_module, "get_recovery_instance_sync_status") as mock_status:
            mock_status.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"lastSyncTime": "2025-01-01T00:00:00Z"}),
            }

            event = {
                "requestContext": {"stage": "dev"},
                "httpMethod": "GET",
                "path": "/drs/recovery-instance-sync",
                "body": "{}",
                "pathParameters": {},
                "queryStringParameters": {},
            }
            result = index_module.handle_api_gateway_request(event, None)

            mock_status.assert_called_once()
            assert result["statusCode"] == 200

    def test_unknown_path_returns_404(self, dm_handler_module):
        """Unknown API paths return 404."""
        index_module, _ = dm_handler_module

        event = {
            "requestContext": {"stage": "dev"},
            "httpMethod": "GET",
            "path": "/nonexistent/path",
            "body": "{}",
            "pathParameters": {},
            "queryStringParameters": {},
        }
        result = index_module.handle_api_gateway_request(event, None)

        assert result["statusCode"] == 404


# ============================================================================
# 12.3 - Direct Invocation Tests
# ============================================================================


class TestDirectInvocationSync:
    """Test direct invocation operations for recovery instance sync."""

    def test_sync_recovery_instances_operation(self, dm_handler_module):
        """Direct invocation with operation=sync_recovery_instances calls sync handler."""
        index_module, _ = dm_handler_module

        # Mock IAM utils for direct invocation
        mock_iam = sys.modules["shared.iam_utils"]
        mock_iam.validate_direct_invocation_event.return_value = True
        mock_iam.extract_iam_principal.return_value = "arn:aws:iam::123456789012:role/TestRole"
        mock_iam.validate_iam_authorization.return_value = True

        with patch.object(index_module, "handle_recovery_instance_sync") as mock_sync:
            mock_sync.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"instancesUpdated": 10}),
            }

            event = {"operation": "sync_recovery_instances"}
            mock_context = MagicMock()
            result = index_module.handle_direct_invocation(event, mock_context)

            mock_sync.assert_called_once()
            assert result["instancesUpdated"] == 10

    def test_get_recovery_instance_sync_status_operation(self, dm_handler_module):
        """Direct invocation with operation=get_recovery_instance_sync_status calls status handler."""
        index_module, _ = dm_handler_module

        mock_iam = sys.modules["shared.iam_utils"]
        mock_iam.validate_direct_invocation_event.return_value = True
        mock_iam.extract_iam_principal.return_value = "arn:aws:iam::123456789012:role/TestRole"
        mock_iam.validate_iam_authorization.return_value = True

        with patch.object(index_module, "get_recovery_instance_sync_status") as mock_status:
            mock_status.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"lastSyncTime": "2025-01-01T00:00:00Z", "instancesUpdated": 5}),
            }

            event = {"operation": "get_recovery_instance_sync_status"}
            mock_context = MagicMock()
            result = index_module.handle_direct_invocation(event, mock_context)

            mock_status.assert_called_once()
            assert result["lastSyncTime"] == "2025-01-01T00:00:00Z"

    def test_direct_invocation_unwraps_api_gateway_response(self, dm_handler_module):
        """Direct invocation unwraps statusCode/body format to raw data."""
        index_module, _ = dm_handler_module

        mock_iam = sys.modules["shared.iam_utils"]
        mock_iam.validate_direct_invocation_event.return_value = True
        mock_iam.extract_iam_principal.return_value = "arn:aws:iam::123456789012:role/TestRole"
        mock_iam.validate_iam_authorization.return_value = True

        with patch.object(index_module, "handle_recovery_instance_sync") as mock_sync:
            mock_sync.return_value = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"instancesUpdated": 7, "errors": []}),
            }

            event = {"operation": "sync_recovery_instances"}
            mock_context = MagicMock()
            result = index_module.handle_direct_invocation(event, mock_context)

            # Should be unwrapped - no statusCode wrapper
            assert "statusCode" not in result
            assert result["instancesUpdated"] == 7

    def test_direct_invocation_invalid_operation(self, dm_handler_module):
        """Direct invocation with unknown operation returns error."""
        index_module, _ = dm_handler_module

        mock_iam = sys.modules["shared.iam_utils"]
        mock_iam.validate_direct_invocation_event.return_value = True
        mock_iam.extract_iam_principal.return_value = "arn:aws:iam::123456789012:role/TestRole"
        mock_iam.validate_iam_authorization.return_value = True

        event = {"operation": "nonexistent_operation"}
        mock_context = MagicMock()
        result = index_module.handle_direct_invocation(event, mock_context)

        assert result["error"] == "INVALID_OPERATION"



# ============================================================================
# 12.5 - Cache Query Function Tests
# ============================================================================


class TestCacheQueryFunctions:
    """Test check_existing_recovery_instances() cache query logic."""

    def test_cache_hit_returns_instance_data(self, dm_handler_module):
        """Cache hit returns recovery instance data in expected format."""
        index_module, mock_table = dm_handler_module

        # Mock recovery plans table
        mock_plans_table = MagicMock()
        mock_plans_table.get_item.return_value = {
            "Item": {
                "planId": "plan-123",
                "waves": [{"protectionGroupId": "pg-001", "waveNumber": 1}],
            }
        }

        # Mock protection groups table
        mock_pg_table = MagicMock()
        mock_pg_table.get_item.return_value = {
            "Item": {
                "groupId": "pg-001",
                "region": "us-east-2",
                "sourceServerIds": ["s-abc123"],
            }
        }

        # Mock recovery instances table with cache hit
        mock_ri_table = MagicMock()
        mock_ri_table.get_item.return_value = {
            "Item": {
                "sourceServerId": "s-abc123",
                "recoveryInstanceId": "ri-xyz789",
                "ec2InstanceId": "i-0123456789",
                "ec2InstanceState": "running",
                "sourceServerName": "web-server-01",
                "name": "Recovery of web-server-01",
                "privateIp": "10.0.1.100",
                "publicIp": "54.123.45.67",
                "instanceType": "t3.medium",
                "launchTime": "2025-02-17T10:30:00Z",
                "region": "us-east-2",
                "sourceExecutionId": "exec-abc",
                "sourcePlanName": "Web Recovery",
            }
        }

        with patch.object(index_module, "get_recovery_plans_table", return_value=mock_plans_table), \
             patch.object(index_module, "get_protection_groups_table", return_value=mock_pg_table), \
             patch.object(index_module, "get_recovery_instances_table", return_value=mock_ri_table):

            result = index_module.check_existing_recovery_instances("plan-123")

            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["hasExistingInstances"] is True
            assert body["instanceCount"] == 1
            assert body["existingInstances"][0]["sourceServerId"] == "s-abc123"
            assert body["existingInstances"][0]["ec2InstanceState"] == "running"
            assert body["existingInstances"][0]["privateIp"] == "10.0.1.100"

    def test_cache_miss_returns_empty(self, dm_handler_module):
        """Cache miss returns empty results without error."""
        index_module, mock_table = dm_handler_module

        mock_plans_table = MagicMock()
        mock_plans_table.get_item.return_value = {
            "Item": {
                "planId": "plan-123",
                "waves": [{"protectionGroupId": "pg-001", "waveNumber": 1}],
            }
        }

        mock_pg_table = MagicMock()
        mock_pg_table.get_item.return_value = {
            "Item": {
                "groupId": "pg-001",
                "region": "us-east-2",
                "sourceServerIds": ["s-notfound"],
            }
        }

        # Cache miss - no Item in response
        mock_ri_table = MagicMock()
        mock_ri_table.get_item.return_value = {}

        with patch.object(index_module, "get_recovery_plans_table", return_value=mock_plans_table), \
             patch.object(index_module, "get_protection_groups_table", return_value=mock_pg_table), \
             patch.object(index_module, "get_recovery_instances_table", return_value=mock_ri_table):

            result = index_module.check_existing_recovery_instances("plan-123")

            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["hasExistingInstances"] is False
            assert body["instanceCount"] == 0
            assert body["existingInstances"] == []

    def test_plan_not_found_returns_404(self, dm_handler_module):
        """Non-existent plan returns 404."""
        index_module, mock_table = dm_handler_module

        mock_plans_table = MagicMock()
        mock_plans_table.get_item.return_value = {}

        with patch.object(index_module, "get_recovery_plans_table", return_value=mock_plans_table):
            result = index_module.check_existing_recovery_instances("plan-nonexistent")

            assert result["statusCode"] == 404
            body = json.loads(result["body"])
            assert body["error"] == "RECOVERY_PLAN_NOT_FOUND"

    def test_no_servers_returns_empty(self, dm_handler_module):
        """Plan with no servers returns empty results."""
        index_module, mock_table = dm_handler_module

        mock_plans_table = MagicMock()
        mock_plans_table.get_item.return_value = {
            "Item": {
                "planId": "plan-123",
                "waves": [{"protectionGroupId": "pg-001", "waveNumber": 1}],
            }
        }

        # PG with no servers
        mock_pg_table = MagicMock()
        mock_pg_table.get_item.return_value = {
            "Item": {"groupId": "pg-001", "region": "us-east-2", "sourceServerIds": []}
        }

        with patch.object(index_module, "get_recovery_plans_table", return_value=mock_plans_table), \
             patch.object(index_module, "get_protection_groups_table", return_value=mock_pg_table):

            result = index_module.check_existing_recovery_instances("plan-123")

            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["hasExistingInstances"] is False
            assert body["instanceCount"] == 0

    def test_recovery_instances_table_not_configured(self, dm_handler_module):
        """Missing recovery instances table returns empty results gracefully."""
        index_module, mock_table = dm_handler_module

        mock_plans_table = MagicMock()
        mock_plans_table.get_item.return_value = {
            "Item": {
                "planId": "plan-123",
                "waves": [{"protectionGroupId": "pg-001", "waveNumber": 1}],
            }
        }

        mock_pg_table = MagicMock()
        mock_pg_table.get_item.return_value = {
            "Item": {
                "groupId": "pg-001",
                "region": "us-east-2",
                "sourceServerIds": ["s-abc123"],
            }
        }

        with patch.object(index_module, "get_recovery_plans_table", return_value=mock_plans_table), \
             patch.object(index_module, "get_protection_groups_table", return_value=mock_pg_table), \
             patch.object(index_module, "get_recovery_instances_table", return_value=None):

            result = index_module.check_existing_recovery_instances("plan-123")

            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["hasExistingInstances"] is False

    def test_cache_query_error_continues_gracefully(self, dm_handler_module):
        """DynamoDB error during cache query doesn't crash, returns partial results."""
        index_module, mock_table = dm_handler_module

        mock_plans_table = MagicMock()
        mock_plans_table.get_item.return_value = {
            "Item": {
                "planId": "plan-123",
                "waves": [{"protectionGroupId": "pg-001", "waveNumber": 1}],
            }
        }

        mock_pg_table = MagicMock()
        mock_pg_table.get_item.return_value = {
            "Item": {
                "groupId": "pg-001",
                "region": "us-east-2",
                "sourceServerIds": ["s-abc123", "s-def456"],
            }
        }

        # First call succeeds, second raises error
        mock_ri_table = MagicMock()
        mock_ri_table.get_item.side_effect = [
            {
                "Item": {
                    "sourceServerId": "s-abc123",
                    "recoveryInstanceId": "ri-001",
                    "ec2InstanceId": "i-001",
                    "ec2InstanceState": "running",
                    "sourceServerName": "server-1",
                    "name": "Recovery of server-1",
                    "instanceType": "t3.medium",
                    "launchTime": "2025-01-01T00:00:00Z",
                    "region": "us-east-2",
                }
            },
            Exception("DynamoDB throttled"),
        ]

        with patch.object(index_module, "get_recovery_plans_table", return_value=mock_plans_table), \
             patch.object(index_module, "get_protection_groups_table", return_value=mock_pg_table), \
             patch.object(index_module, "get_recovery_instances_table", return_value=mock_ri_table):

            result = index_module.check_existing_recovery_instances("plan-123")

            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            # Should still return the one successful result
            assert body["instanceCount"] == 1


# ============================================================================
# Handler Function Tests
# ============================================================================


class TestHandleRecoveryInstanceSync:
    """Test handle_recovery_instance_sync() function."""

    def test_successful_sync(self, dm_handler_module):
        """Successful sync returns 200 with results."""
        index_module, _ = dm_handler_module

        mock_sync = Mock(return_value={"instancesUpdated": 15, "regionsScanned": 3, "errors": []})

        with patch.dict("sys.modules", {"shared.recovery_instance_sync": Mock(sync_all_recovery_instances=mock_sync)}):
            result = index_module.handle_recovery_instance_sync()

            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["instancesUpdated"] == 15

    def test_sync_failure_returns_500(self, dm_handler_module):
        """Sync failure returns 500 with error details."""
        index_module, _ = dm_handler_module

        mock_sync = Mock(side_effect=Exception("DRS API unavailable"))

        with patch.dict("sys.modules", {"shared.recovery_instance_sync": Mock(sync_all_recovery_instances=mock_sync)}):
            result = index_module.handle_recovery_instance_sync()

            assert result["statusCode"] == 500
            body = json.loads(result["body"])
            assert body["error"] == "SYNC_FAILED"


class TestGetRecoveryInstanceSyncStatus:
    """Test get_recovery_instance_sync_status() function."""

    def test_successful_status_retrieval(self, dm_handler_module):
        """Successful status retrieval returns 200."""
        index_module, _ = dm_handler_module

        mock_status = Mock(return_value={"lastSyncTime": "2025-01-01T00:00:00Z", "instancesUpdated": 10})
        mock_module = Mock()
        mock_module.get_recovery_instance_sync_status = mock_status

        with patch.dict("sys.modules", {"shared.recovery_instance_sync": mock_module}):
            result = index_module.get_recovery_instance_sync_status()

            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["lastSyncTime"] == "2025-01-01T00:00:00Z"

    def test_status_failure_returns_500(self, dm_handler_module):
        """Status retrieval failure returns 500."""
        index_module, _ = dm_handler_module

        mock_status = Mock(side_effect=Exception("Table not found"))
        mock_module = Mock()
        mock_module.get_recovery_instance_sync_status = mock_status

        with patch.dict("sys.modules", {"shared.recovery_instance_sync": mock_module}):
            result = index_module.get_recovery_instance_sync_status()

            assert result["statusCode"] == 500
            body = json.loads(result["body"])
            assert body["error"] == "STATUS_FAILED"
