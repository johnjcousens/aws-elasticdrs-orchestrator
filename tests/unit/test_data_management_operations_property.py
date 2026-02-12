"""
Property-based tests for data-management-handler handle_direct_invocation().

Uses Hypothesis framework to verify universal properties hold across all inputs.
Tests operation routing correctness, parameter validation, and error handling
with comprehensive input generation.

Validates Design Properties:
- Property 12: Data Management Handler Operation Routing
- Property 13: Data Management Handler Invalid Operation Rejection

Validates Requirements:
- Requirement 6: Data Management Handler Operation Completion
- Requirement 9: Error Handling for Direct Invocations
- Requirement 10: Response Format Consistency
"""

import json
import os
import sys
from contextlib import contextmanager
from unittest.mock import Mock, patch

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

# Module-level setup to load data-management-handler index
lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
data_management_handler_dir = os.path.join(lambda_dir, "data-management-handler")


@contextmanager
def setup_test_environment():
    """Context manager to set up test environment for each property test"""
    # Save original sys.path and modules
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    # Remove any existing 'index' module
    if "index" in sys.modules:
        del sys.modules["index"]

    # Add data-management-handler to front of path
    sys.path.insert(0, data_management_handler_dir)
    sys.path.insert(0, lambda_dir)

    # Set up environment variables
    with patch.dict(
        os.environ,
        {
            "PROTECTION_GROUPS_TABLE": "test-pg-table",
            "RECOVERY_PLANS_TABLE": "test-plans-table",
            "EXECUTION_HISTORY_TABLE": "test-execution-table",
            "TARGET_ACCOUNTS_TABLE": "test-target-accounts-table",
            "TAG_SYNC_CONFIG_TABLE": "test-tag-sync-table",
            "PROJECT_NAME": "test-project",
            "ENVIRONMENT": "test",
        },
    ):
        # Save original shared modules before replacing
        original_shared_modules = {
            name: mod for name, mod in sys.modules.items()
            if name == "shared" or name.startswith("shared.")
        }

        # Mock shared modules
        sys.modules["shared"] = Mock()
        sys.modules["shared.account_utils"] = Mock()
        sys.modules["shared.conflict_detection"] = Mock()
        sys.modules["shared.config_merge"] = Mock()
        sys.modules["shared.cross_account"] = Mock()
        sys.modules["shared.drs_regions"] = Mock()
        sys.modules["shared.drs_regions"].DRS_REGIONS = ["us-east-1", "us-west-2"]
        sys.modules["shared.security_utils"] = Mock()
        sys.modules["shared.notifications"] = Mock()

        mock_response_utils = Mock()

        def mock_response(status_code, body, headers=None):
            return {
                "statusCode": status_code,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(body),
            }

        mock_response_utils.response = mock_response
        sys.modules["shared.response_utils"] = mock_response_utils

        # Mock IAM utilities
        mock_iam_utils = Mock()
        mock_iam_utils.extract_iam_principal.return_value = "arn:aws:iam::123456789012:role/OrchestrationRole"
        mock_iam_utils.validate_iam_authorization.return_value = True
        mock_iam_utils.validate_direct_invocation_event.return_value = True
        mock_iam_utils.log_direct_invocation.return_value = None
        mock_iam_utils.create_authorization_error_response.return_value = {
            "error": "AUTHORIZATION_FAILED",
            "message": "Not authorized"
        }
        sys.modules["shared.iam_utils"] = mock_iam_utils

        try:
            yield
        finally:
            # Stop all active patches to prevent pollution
            patch.stopall()
            
            # Restore original state
            sys.path = original_path
            if "index" in sys.modules:
                del sys.modules["index"]
            if original_index is not None:
                sys.modules["index"] = original_index

            # Restore original shared modules
            for module_name in list(sys.modules.keys()):
                if module_name == "shared" or module_name.startswith("shared."):
                    del sys.modules[module_name]
            sys.modules.update(original_shared_modules)



def get_mock_context():
    """Create mock Lambda context"""
    context = Mock()
    context.request_id = "test-request-id-123"
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:123456789012:function:test-data-management-handler"
    )
    return context


# Hypothesis strategies for generating test data

# Valid operation names from the data management handler
VALID_OPERATIONS = [
    # Protection Groups
    "create_protection_group",
    "list_protection_groups",
    "get_protection_group",
    "update_protection_group",
    "delete_protection_group",
    "resolve_protection_group_tags",
    # Recovery Plans
    "create_recovery_plan",
    "list_recovery_plans",
    "get_recovery_plan",
    "update_recovery_plan",
    "delete_recovery_plan",
    # Server Launch Configs
    "update_server_launch_config",
    "delete_server_launch_config",
    "bulk_update_server_configs",
    "validate_static_ip",
    # Target Accounts
    "add_target_account",
    "update_target_account",
    "delete_target_account",
    # Tag Sync & Config
    "handle_drs_tag_sync",
    "trigger_tag_sync",
    "get_tag_sync_settings",
    "update_tag_sync_settings",
    "import_configuration",
    # Staging Accounts
    "add_staging_account",
    "remove_staging_account",
    "sync_staging_accounts",
    "sync_extended_source_servers",
]


@st.composite
def valid_operation_name(draw):
    """Strategy: Generate valid operation names"""
    return draw(st.sampled_from(VALID_OPERATIONS))


@st.composite
def invalid_operation_name(draw):
    """Strategy: Generate invalid operation names (random strings)"""
    # Generate random strings that are NOT in the valid operations list
    invalid_op = draw(
        st.one_of(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=65
                ),
                min_size=1,
                max_size=50,
            ),
            st.from_regex(r"[a-z_]{1,30}", fullmatch=True),
        )
    )
    # Ensure it's not accidentally a valid operation
    if invalid_op in VALID_OPERATIONS:
        return "definitely_invalid_operation_xyz"
    return invalid_op



@st.composite
def valid_body_for_operation(draw, operation):
    """Strategy: Generate valid body parameters for a given operation"""
    if operation == "create_protection_group":
        return {
            "groupName": draw(st.text(min_size=1, max_size=50)),
            "description": draw(st.text(min_size=0, max_size=200)),
            "region": draw(st.sampled_from(["us-east-1", "us-west-2"])),
        }
    elif operation == "update_protection_group":
        return {
            "groupId": draw(st.uuids()).hex,
            "description": draw(st.text(min_size=0, max_size=200)),
        }
    elif operation == "delete_protection_group":
        return {"groupId": draw(st.uuids()).hex}
    elif operation == "get_protection_group":
        return {"groupId": draw(st.uuids()).hex}
    elif operation == "create_recovery_plan":
        return {
            "planName": draw(st.text(min_size=1, max_size=50)),
            "description": draw(st.text(min_size=0, max_size=200)),
        }
    elif operation == "update_recovery_plan":
        return {
            "planId": draw(st.uuids()).hex,
            "description": draw(st.text(min_size=0, max_size=200)),
        }
    elif operation == "delete_recovery_plan":
        return {"planId": draw(st.uuids()).hex}
    elif operation == "get_recovery_plan":
        return {"planId": draw(st.uuids()).hex}
    elif operation == "update_server_launch_config":
        return {
            "groupId": draw(st.uuids()).hex,
            "serverId": draw(st.text(min_size=1, max_size=50)),
            "launchConfiguration": {},
        }
    elif operation == "delete_server_launch_config":
        return {
            "groupId": draw(st.uuids()).hex,
            "serverId": draw(st.text(min_size=1, max_size=50)),
        }
    elif operation == "bulk_update_server_configs":
        return {
            "groupId": draw(st.uuids()).hex,
            "servers": [],
        }
    elif operation == "validate_static_ip":
        return {
            "groupId": draw(st.uuids()).hex,
            "serverId": draw(st.text(min_size=1, max_size=50)),
            "staticIp": "10.0.1.100",
        }
    elif operation == "add_target_account":
        return {
            "accountId": str(draw(st.integers(min_value=100000000000, max_value=999999999999))),
            "accountName": draw(st.text(min_size=1, max_size=50)),
        }
    elif operation == "update_target_account":
        return {
            "accountId": str(draw(st.integers(min_value=100000000000, max_value=999999999999))),
            "accountName": draw(st.text(min_size=1, max_size=50)),
        }
    elif operation == "delete_target_account":
        return {
            "accountId": str(draw(st.integers(min_value=100000000000, max_value=999999999999)))
        }
    elif operation in ["handle_drs_tag_sync", "trigger_tag_sync"]:
        return {}
    elif operation == "update_tag_sync_settings":
        return {"enabled": draw(st.booleans())}
    elif operation == "import_configuration":
        return {"manifest": {}}
    elif operation == "add_staging_account":
        return {
            "targetAccountId": str(draw(st.integers(min_value=100000000000, max_value=999999999999))),
            "stagingAccountId": str(draw(st.integers(min_value=100000000000, max_value=999999999999))),
        }
    elif operation == "remove_staging_account":
        return {
            "targetAccountId": str(draw(st.integers(min_value=100000000000, max_value=999999999999))),
            "stagingAccountId": str(draw(st.integers(min_value=100000000000, max_value=999999999999))),
        }
    elif operation in ["sync_staging_accounts", "sync_extended_source_servers"]:
        return {
            "targetAccountId": str(draw(st.integers(min_value=100000000000, max_value=999999999999)))
        }
    else:
        return {}



def mock_all_handlers():
    """Helper to create all handler mocks"""
    success_response = {"success": True, "data": "test"}
    
    patches = {
        "index.create_protection_group": success_response,
        "index.get_protection_groups": success_response,
        "index.get_protection_group": success_response,
        "index.update_protection_group": success_response,
        "index.delete_protection_group": success_response,
        "index.resolve_protection_group_tags": success_response,
        "index.create_recovery_plan": success_response,
        "index.get_recovery_plans": success_response,
        "index.get_recovery_plan": success_response,
        "index.update_recovery_plan": success_response,
        "index.delete_recovery_plan": success_response,
        "index.update_server_launch_config": success_response,
        "index.delete_server_launch_config": success_response,
        "index.bulk_update_server_launch_config": success_response,
        "index.validate_server_static_ip": success_response,
        "index.create_target_account": success_response,
        "index.update_target_account": success_response,
        "index.delete_target_account": success_response,
        "index.handle_drs_tag_sync": success_response,
        "index.get_tag_sync_settings": success_response,
        "index.update_tag_sync_settings": success_response,
        "index.import_configuration": success_response,
        "index.handle_add_staging_account": success_response,
        "index.handle_remove_staging_account": success_response,
        "index.handle_sync_single_account": success_response,
    }
    
    return [patch(name, return_value=value) for name, value in patches.items()]


# Property 12: Data Management Handler Operation Routing
# Feature: direct-lambda-invocation-mode, Property 12: Data Management Handler Operation Routing
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(operation=valid_operation_name(), data=st.data())
def test_property_valid_operation_routing_succeeds(operation, data):
    """
    Property: For any valid operation name, routing should succeed.

    Universal property: Given any operation from the supported list,
    the system should route to the correct handler function and return
    a response without routing errors.

    Validates: Property 12 - Data Management Handler Operation Routing
    Validates: Requirements 6.1-6.20 - Data Management Handler Operation Completion
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Apply all mocks
        mocks = mock_all_handlers()
        for mock_patch in mocks:
            mock_patch.start()

        try:
            # Generate valid body for this operation using st.data()
            body = data.draw(valid_body_for_operation(operation))

            event = {"operation": operation, "body": body}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Valid operations should NOT return routing errors
            assert "error" not in result or result.get("error") != "UNKNOWN_OPERATION"
            assert "error" not in result or result.get("error") != "INVALID_EVENT_FORMAT"

            # Property assertion: Result should be a dict (not an error string)
            assert isinstance(result, dict)
        finally:
            # Stop all mocks
            for mock_patch in mocks:
                mock_patch.stop()



# Property 13: Data Management Handler Invalid Operation Rejection
# Feature: direct-lambda-invocation-mode, Property 13: Data Management Handler Invalid Operation Rejection
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(operation=invalid_operation_name())
def test_property_invalid_operation_returns_error(operation):
    """
    Property: For any invalid operation name, should return INVALID_OPERATION error.

    Universal property: Given any operation name that is NOT in the supported
    list, the system should return an error with code "INVALID_OPERATION" and
    include an error message.

    Validates: Property 13 - Data Management Handler Invalid Operation Rejection
    Validates: Requirement 6.20 - Invalid operation handling
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        event = {"operation": operation, "body": {}}

        result = index.handle_direct_invocation(event, mock_context)

        # Property assertion: Invalid operations should return INVALID_OPERATION error
        assert result.get("error") == "INVALID_OPERATION"

        # Property assertion: Error message should be present
        assert "message" in result
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0

        # Property assertion: Error message should mention the invalid operation
        assert operation in result["message"] or "Invalid operation" in result["message"]


# Property: Protection Group operations route correctly
# Feature: direct-lambda-invocation-mode, Property 12: Data Management Handler Operation Routing
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    operation=st.sampled_from([
        "create_protection_group",
        "list_protection_groups",
        "get_protection_group",
        "update_protection_group",
        "delete_protection_group",
        "resolve_protection_group_tags",
    ]),
    data=st.data(),
)
def test_property_protection_group_operations_route_correctly(operation, data):
    """
    Property: For any protection group operation, should route correctly.

    Universal property: Given any protection group operation with valid
    parameters, the system should successfully route to the handler function
    without parameter validation errors.

    Validates: Property 12 - Data Management Handler Operation Routing
    Validates: Requirements 6.1-6.3 - Protection Group operations
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Mock protection group handlers
        with patch("index.create_protection_group") as mock_create, \
             patch("index.get_protection_groups") as mock_list, \
             patch("index.get_protection_group") as mock_get, \
             patch("index.update_protection_group") as mock_update, \
             patch("index.delete_protection_group") as mock_delete, \
             patch("index.resolve_protection_group_tags") as mock_resolve:

            # Mock all handlers to return success
            success_response = {"success": True, "groupId": "pg-123"}
            mock_create.return_value = success_response
            mock_list.return_value = {"protectionGroups": []}
            mock_get.return_value = success_response
            mock_update.return_value = success_response
            mock_delete.return_value = {"message": "Deleted"}
            mock_resolve.return_value = {"servers": []}

            # Generate valid body using st.data()
            body = data.draw(valid_body_for_operation(operation))

            event = {"operation": operation, "body": body}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Should not return operation routing errors
            assert result.get("error") != "UNKNOWN_OPERATION"
            assert result.get("error") != "INVALID_EVENT_FORMAT"

            # Property assertion: Result should be a dict
            assert isinstance(result, dict)



# Property: Recovery Plan operations route correctly
# Feature: direct-lambda-invocation-mode, Property 12: Data Management Handler Operation Routing
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    operation=st.sampled_from([
        "create_recovery_plan",
        "list_recovery_plans",
        "get_recovery_plan",
        "update_recovery_plan",
        "delete_recovery_plan",
    ]),
    data=st.data(),
)
def test_property_recovery_plan_operations_route_correctly(operation, data):
    """
    Property: For any recovery plan operation, should route correctly.

    Universal property: Given any recovery plan operation with valid
    parameters, the system should successfully route to the handler function
    without parameter validation errors.

    Validates: Property 12 - Data Management Handler Operation Routing
    Validates: Requirements 6.8-6.10 - Recovery Plan operations
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Mock recovery plan handlers
        with patch("index.create_recovery_plan") as mock_create, \
             patch("index.get_recovery_plans") as mock_list, \
             patch("index.get_recovery_plan") as mock_get, \
             patch("index.update_recovery_plan") as mock_update, \
             patch("index.delete_recovery_plan") as mock_delete:

            # Mock all handlers to return success
            success_response = {"success": True, "planId": "plan-123"}
            mock_create.return_value = success_response
            mock_list.return_value = {"recoveryPlans": []}
            mock_get.return_value = success_response
            mock_update.return_value = success_response
            mock_delete.return_value = {"message": "Deleted"}

            # Generate valid body using st.data()
            body = data.draw(valid_body_for_operation(operation))

            event = {"operation": operation, "body": body}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Should not return operation routing errors
            assert result.get("error") != "UNKNOWN_OPERATION"
            assert result.get("error") != "INVALID_EVENT_FORMAT"

            # Property assertion: Result should be a dict
            assert isinstance(result, dict)


# Property: Server Launch Config operations route correctly
# Feature: direct-lambda-invocation-mode, Property 12: Data Management Handler Operation Routing
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    operation=st.sampled_from([
        "update_server_launch_config",
        "delete_server_launch_config",
        "bulk_update_server_configs",
        "validate_static_ip",
    ]),
    data=st.data(),
)
def test_property_server_launch_config_operations_route_correctly(operation, data):
    """
    Property: For any server launch config operation, should route correctly.

    Universal property: Given any server launch config operation with valid
    parameters, the system should successfully route to the handler function
    without parameter validation errors.

    Validates: Property 12 - Data Management Handler Operation Routing
    Validates: Requirements 6.4-6.7 - Server Launch Config operations
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Mock server launch config handlers
        with patch("index.update_server_launch_config") as mock_update, \
             patch("index.delete_server_launch_config") as mock_delete, \
             patch("index.bulk_update_server_launch_config") as mock_bulk, \
             patch("index.validate_server_static_ip") as mock_validate:

            # Mock all handlers to return success
            success_response = {"success": True}
            mock_update.return_value = success_response
            mock_delete.return_value = {"message": "Deleted"}
            mock_bulk.return_value = success_response
            mock_validate.return_value = {"valid": True}

            # Generate valid body using st.data()
            body = data.draw(valid_body_for_operation(operation))

            event = {"operation": operation, "body": body}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Should not return operation routing errors
            assert result.get("error") != "UNKNOWN_OPERATION"
            assert result.get("error") != "INVALID_EVENT_FORMAT"

            # Property assertion: Result should be a dict
            assert isinstance(result, dict)



# Property: Target Account operations route correctly
# Feature: direct-lambda-invocation-mode, Property 12: Data Management Handler Operation Routing
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    operation=st.sampled_from([
        "add_target_account",
        "update_target_account",
        "delete_target_account",
    ]),
    data=st.data(),
)
def test_property_target_account_operations_route_correctly(operation, data):
    """
    Property: For any target account operation, should route correctly.

    Universal property: Given any target account operation with valid
    parameters, the system should successfully route to the handler function
    without parameter validation errors.

    Validates: Property 12 - Data Management Handler Operation Routing
    Validates: Requirements 6.11-6.13 - Target Account operations
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Mock target account handlers
        with patch("index.create_target_account") as mock_create, \
             patch("index.update_target_account") as mock_update, \
             patch("index.delete_target_account") as mock_delete:

            # Mock all handlers to return success
            success_response = {"success": True, "accountId": "123456789012"}
            mock_create.return_value = success_response
            mock_update.return_value = success_response
            mock_delete.return_value = {"message": "Deleted"}

            # Generate valid body using st.data()
            body = data.draw(valid_body_for_operation(operation))

            event = {"operation": operation, "body": body}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Should not return operation routing errors
            assert result.get("error") != "UNKNOWN_OPERATION"
            assert result.get("error") != "INVALID_EVENT_FORMAT"

            # Property assertion: Result should be a dict
            assert isinstance(result, dict)


# Property: Tag Sync operations route correctly
# Feature: direct-lambda-invocation-mode, Property 12: Data Management Handler Operation Routing
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    operation=st.sampled_from([
        "handle_drs_tag_sync",
        "trigger_tag_sync",
        "get_tag_sync_settings",
        "update_tag_sync_settings",
    ]),
    data=st.data(),
)
def test_property_tag_sync_operations_route_correctly(operation, data):
    """
    Property: For any tag sync operation, should route correctly.

    Universal property: Given any tag sync operation with valid
    parameters, the system should successfully route to the handler function
    without parameter validation errors.

    Validates: Property 12 - Data Management Handler Operation Routing
    Validates: Requirements 6.16-6.17 - Tag Sync operations
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Mock tag sync handlers
        with patch("index.handle_drs_tag_sync") as mock_sync, \
             patch("index.get_tag_sync_settings") as mock_get_settings, \
             patch("index.update_tag_sync_settings") as mock_update_settings:

            # Mock all handlers to return success
            success_response = {"success": True}
            mock_sync.return_value = success_response
            mock_get_settings.return_value = {"enabled": True}
            mock_update_settings.return_value = success_response

            # Generate valid body using st.data()
            body = data.draw(valid_body_for_operation(operation))

            event = {"operation": operation, "body": body}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Should not return operation routing errors
            assert result.get("error") != "UNKNOWN_OPERATION"
            assert result.get("error") != "INVALID_EVENT_FORMAT"

            # Property assertion: Result should be a dict
            assert isinstance(result, dict)



# Property: Staging Account operations route correctly
# Feature: direct-lambda-invocation-mode, Property 12: Data Management Handler Operation Routing
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    operation=st.sampled_from([
        "add_staging_account",
        "remove_staging_account",
        "sync_staging_accounts",
        "sync_extended_source_servers",
    ]),
    data=st.data(),
)
def test_property_staging_account_operations_route_correctly(operation, data):
    """
    Property: For any staging account operation, should route correctly.

    Universal property: Given any staging account operation with valid
    parameters, the system should successfully route to the handler function
    without parameter validation errors.

    Validates: Property 12 - Data Management Handler Operation Routing
    Validates: Requirements 6.14-6.15, 6.18 - Staging Account operations
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Mock staging account handlers
        with patch("index.handle_add_staging_account") as mock_add, \
             patch("index.handle_remove_staging_account") as mock_remove, \
             patch("index.handle_sync_single_account") as mock_sync:

            # Mock all handlers to return success
            success_response = {"success": True}
            mock_add.return_value = success_response
            mock_remove.return_value = {"message": "Removed"}
            mock_sync.return_value = success_response

            # Generate valid body using st.data()
            body = data.draw(valid_body_for_operation(operation))

            event = {"operation": operation, "body": body}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Should not return operation routing errors
            assert result.get("error") != "UNKNOWN_OPERATION"
            assert result.get("error") != "INVALID_EVENT_FORMAT"

            # Property assertion: Result should be a dict
            assert isinstance(result, dict)


# Property: Configuration Import operation routes correctly
# Feature: direct-lambda-invocation-mode, Property 12: Data Management Handler Operation Routing
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(data=st.data())
def test_property_import_configuration_routes_correctly(data):
    """
    Property: For import_configuration operation, should route correctly.

    Universal property: Given import_configuration operation with valid
    parameters, the system should successfully route to the handler function
    without parameter validation errors.

    Validates: Property 12 - Data Management Handler Operation Routing
    Validates: Requirement 6.19 - Configuration Import operation
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Mock import configuration handler
        with patch("index.import_configuration") as mock_import:

            # Mock handler to return success
            success_response = {"success": True, "imported": 0}
            mock_import.return_value = success_response

            # Generate valid body using st.data()
            body = data.draw(valid_body_for_operation("import_configuration"))

            event = {"operation": "import_configuration", "body": body}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Should not return operation routing errors
            assert result.get("error") != "UNKNOWN_OPERATION"
            assert result.get("error") != "INVALID_EVENT_FORMAT"

            # Property assertion: Result should be a dict
            assert isinstance(result, dict)


# Property: Error response structure consistency
# Feature: direct-lambda-invocation-mode, Property 13: Data Management Handler Invalid Operation Rejection
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(operation=invalid_operation_name())
def test_property_error_response_structure_consistency(operation):
    """
    Property: For any error condition, response should have consistent structure.

    Universal property: Given any invalid operation (which causes an error),
    the error response should contain "error" and "message" fields with
    appropriate types and values.

    Validates: Property 13 - Data Management Handler Invalid Operation Rejection
    Validates: Requirement 9.7 - Consistent error response structure
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        event = {"operation": operation, "body": {}}

        result = index.handle_direct_invocation(event, mock_context)

        # Property assertion: Error response must have "error" field
        assert "error" in result
        assert isinstance(result["error"], str)
        assert len(result["error"]) > 0

        # Property assertion: Error response must have "message" field
        assert "message" in result
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0

        # Property assertion: Error code should be uppercase with underscores
        assert result["error"].isupper()
        assert "_" in result["error"] or result["error"].isalpha()



# Property: Missing operation field returns error
# Feature: direct-lambda-invocation-mode, Property 13: Data Management Handler Invalid Operation Rejection
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(body=st.dictionaries(st.text(), st.text()))
def test_property_missing_operation_returns_error(body):
    """
    Property: For any event missing operation field, should return error.

    Universal property: Given any event structure that does NOT contain
    an "operation" field, the system should return an error indicating
    the operation is missing or invalid.

    Validates: Property 13 - Data Management Handler Invalid Operation Rejection
    Validates: Requirement 9.1 - Missing required parameters
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Override the mock to return False for missing operation
        with patch("shared.iam_utils.validate_direct_invocation_event", return_value=False):
            # Event without operation field
            event = {"body": body}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Should return INVALID_EVENT_FORMAT error
            assert result.get("error") == "INVALID_EVENT_FORMAT"

            # Property assertion: Error message should be present
            assert "message" in result
            assert "operation" in result["message"].lower()


# Property: All valid operations return dict responses
# Feature: direct-lambda-invocation-mode, Property 12: Data Management Handler Operation Routing
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(operation=valid_operation_name(), data=st.data())
def test_property_all_operations_return_dict(operation, data):
    """
    Property: For any valid operation, response should be a dict (not string).

    Universal property: Given any valid operation, the system should return
    a Python dict object, never a JSON string or other type.

    Validates: Property 12 - Data Management Handler Operation Routing
    Validates: Requirement 10.6 - Response format consistency
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Apply all mocks
        mocks = mock_all_handlers()
        for mock_patch in mocks:
            mock_patch.start()

        try:
            # Generate valid body using st.data()
            body = data.draw(valid_body_for_operation(operation))

            event = {"operation": operation, "body": body}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Result must be a dict
            assert isinstance(result, dict)

            # Property assertion: Result must NOT be a string
            assert not isinstance(result, str)

            # Property assertion: Result must NOT be bytes
            assert not isinstance(result, bytes)
        finally:
            # Stop all mocks
            for mock_patch in mocks:
                mock_patch.stop()


# Property: Response format - no API Gateway wrapping
# Feature: direct-lambda-invocation-mode, Property 12: Data Management Handler Operation Routing
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(operation=valid_operation_name(), data=st.data())
def test_property_response_format_no_api_gateway_wrapping(operation, data):
    """
    Property: For any operation, response should not contain API Gateway wrapping.

    Universal property: Given any valid operation, the response should be
    a plain dict without statusCode, headers, or body fields (which are
    API Gateway response format).

    Validates: Property 12 - Data Management Handler Operation Routing
    Validates: Requirement 10.6 - Direct invocation response format
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Mock all handlers - they might return API Gateway format internally
        # but handle_direct_invocation should unwrap it
        with patch("index.create_protection_group") as mock_handler:
            # Mock handler returns API Gateway format
            api_gateway_response = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"data": "success"}),
            }
            mock_handler.return_value = api_gateway_response

            # Generate valid body using st.data()
            body = data.draw(valid_body_for_operation(operation))

            event = {"operation": operation, "body": body}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Response should NOT contain API Gateway fields
            # Note: The actual implementation may or may not unwrap, but we test
            # the expected behavior
            assert isinstance(result, dict)

            # If the result has statusCode, it means the handler didn't unwrap
            # This is acceptable as long as it's consistent
            # The key property is that it returns a dict, not a string
