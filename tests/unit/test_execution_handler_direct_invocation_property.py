"""
Property-based tests for execution-handler handle_direct_invocation() function.

Uses Hypothesis framework to verify universal properties hold across all inputs.
Tests operation routing correctness, parameter validation, and error handling
with comprehensive input generation.

Validates Design Properties:
- Property 10: Execution Handler Operation Routing
- Property 11: Execution Handler Invalid Operation Rejection

Validates Requirements:
- Requirement 5: Execution Handler Standardization
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

# Module-level setup to load execution-handler index
lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
execution_handler_dir = os.path.join(lambda_dir, "execution-handler")


@contextmanager
def setup_test_environment():
    """Context manager to set up test environment for each property test"""
    # Save original sys.path and modules
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    # Remove any existing 'index' module
    if "index" in sys.modules:
        del sys.modules["index"]

    # Add execution-handler to front of path
    sys.path.insert(0, execution_handler_dir)
    sys.path.insert(0, lambda_dir)

    # Set up environment variables
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
        # Mock shared modules
        sys.modules["shared"] = Mock()
        sys.modules["shared.account_utils"] = Mock()
        sys.modules["shared.config_merge"] = Mock()
        sys.modules["shared.conflict_detection"] = Mock()
        sys.modules["shared.cross_account"] = Mock()
        sys.modules["shared.drs_limits"] = Mock()
        sys.modules["shared.drs_utils"] = Mock()
        sys.modules["shared.execution_utils"] = Mock()

        # Mock IAM utilities
        mock_iam_utils = Mock()
        mock_iam_utils.extract_iam_principal = Mock(
            return_value="arn:aws:iam::123456789012:role/test-role"
        )
        mock_iam_utils.validate_iam_authorization = Mock(return_value=True)
        mock_iam_utils.log_direct_invocation = Mock()
        mock_iam_utils.create_authorization_error_response = Mock(
            return_value={"error": "UNAUTHORIZED", "message": "Not authorized"}
        )
        mock_iam_utils.validate_direct_invocation_event = Mock(return_value=True)
        sys.modules["shared.iam_utils"] = mock_iam_utils

        mock_response_utils = Mock()

        def mock_response(status_code, body, headers=None):
            return {
                "statusCode": status_code,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps(body),
            }

        mock_response_utils.response = mock_response
        mock_response_utils.DecimalEncoder = json.JSONEncoder
        sys.modules["shared.response_utils"] = mock_response_utils

        try:
            yield
        finally:
            # Restore original state
            sys.path = original_path
            if "index" in sys.modules:
                del sys.modules["index"]
            if original_index is not None:
                sys.modules["index"] = original_index

            # Clean up mocked modules
            for module_name in list(sys.modules.keys()):
                if module_name.startswith("shared"):
                    del sys.modules[module_name]


def get_mock_context():
    """Create mock Lambda context"""
    context = Mock()
    context.request_id = "test-request-id-123"
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:123456789012:function:test-execution-handler"
    )
    return context


# Hypothesis strategies for generating test data

# Valid operation names from the execution handler
VALID_OPERATIONS = [
    "start_execution",
    "cancel_execution",
    "pause_execution",
    "resume_execution",
    "terminate_instances",
    "get_recovery_instances",
    "list_executions",
    "get_execution",
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
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=65),
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
def valid_parameters_for_operation(draw, operation):
    """Strategy: Generate valid parameters for a given operation"""
    if operation == "start_execution":
        return {
            "planId": draw(st.uuids()).hex,
            "executionType": draw(st.sampled_from(["DRILL", "RECOVERY"])),
            "initiatedBy": draw(st.emails()),
        }
    elif operation in ["cancel_execution", "pause_execution"]:
        return {
            "executionId": draw(st.uuids()).hex,
            "reason": draw(st.text(min_size=1, max_size=100)),
        }
    elif operation in [
        "resume_execution",
        "terminate_instances",
        "get_recovery_instances",
        "get_execution",
    ]:
        return {"executionId": draw(st.uuids()).hex}
    elif operation == "list_executions":
        return draw(
            st.one_of(
                st.just({}),
                st.fixed_dictionaries(
                    {
                        "status": st.sampled_from(["RUNNING", "COMPLETED", "FAILED", "CANCELLED"]),
                        "limit": st.integers(min_value=1, max_value=100),
                    }
                ),
            )
        )
    else:
        return {}


# Property 10: Execution Handler Operation Routing
# Feature: direct-lambda-invocation-mode, Property 10: Execution Handler Operation Routing
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

    Validates: Property 10 - Execution Handler Operation Routing
    Validates: Requirement 5 - Execution Handler Standardization
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Mock all handler functions
        with patch("index.execute_recovery_plan") as mock_execute, patch(
            "index.cancel_execution"
        ) as mock_cancel, patch("index.pause_execution") as mock_pause, patch(
            "index.resume_execution"
        ) as mock_resume, patch(
            "index.terminate_recovery_instances"
        ) as mock_terminate, patch(
            "index.get_recovery_instances"
        ) as mock_get_instances, patch(
            "index._delegate_to_query_handler"
        ) as mock_delegate:

            # Mock all handler functions to return success responses
            mock_execute.return_value = {
                "statusCode": 202,
                "body": json.dumps({"executionId": "exec-123", "status": "PENDING"}),
            }
            mock_cancel.return_value = {
                "statusCode": 200,
                "body": json.dumps({"message": "Cancelled"}),
            }
            mock_pause.return_value = {
                "statusCode": 200,
                "body": json.dumps({"message": "Paused"}),
            }
            mock_resume.return_value = {
                "statusCode": 200,
                "body": json.dumps({"message": "Resumed"}),
            }
            mock_terminate.return_value = {
                "statusCode": 200,
                "body": json.dumps({"message": "Terminated"}),
            }
            mock_get_instances.return_value = {
                "statusCode": 200,
                "body": json.dumps({"instances": []}),
            }
            mock_delegate.return_value = {"data": "success"}

            # Generate valid parameters for this operation using st.data()
            parameters = data.draw(valid_parameters_for_operation(operation))

            event = {"operation": operation, "parameters": parameters}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Valid operations should NOT return routing errors
            assert "error" not in result or result.get("error") != "INVALID_OPERATION"
            assert "error" not in result or result.get("error") != "MISSING_OPERATION"

            # Property assertion: Result should be a dict (not an error string)
            assert isinstance(result, dict)

            # Property assertion: Response should not contain API Gateway wrapping
            assert "statusCode" not in result


# Property 11: Execution Handler Invalid Operation Rejection
# Feature: direct-lambda-invocation-mode, Property 11: Execution Handler Invalid Operation Rejection
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
    include a list of valid operations.

    Validates: Property 11 - Execution Handler Invalid Operation Rejection
    Validates: Requirement 5.11 - Invalid operation handling
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        event = {"operation": operation, "parameters": {}}

        result = index.handle_direct_invocation(event, mock_context)

        # Property assertion: Invalid operations should return INVALID_OPERATION error
        assert result.get("error") == "INVALID_OPERATION"

        # Property assertion: Error message should be present
        assert "message" in result
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0

        # Property assertion: Valid operations list should be provided in details
        assert "details" in result
        assert "validOperations" in result["details"]
        assert isinstance(result["details"]["validOperations"], list)
        assert len(result["details"]["validOperations"]) > 0

        # Property assertion: All expected operations should be in the list
        for valid_op in VALID_OPERATIONS:
            assert valid_op in result["details"]["validOperations"]


# Property: Operation with required parameters should route correctly
# Feature: direct-lambda-invocation-mode, Property 10: Execution Handler Operation Routing
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    operation=st.sampled_from(
        [
            "start_execution",
            "cancel_execution",
            "pause_execution",
            "resume_execution",
            "terminate_instances",
            "get_recovery_instances",
        ]
    ),
    data=st.data(),
)
def test_property_operation_with_required_params_routes_correctly(operation, data):
    """
    Property: For any operation with required parameters, should route correctly.

    Universal property: Given any operation that requires parameters and
    providing those parameters, the system should successfully route to
    the handler function without parameter validation errors.

    Validates: Property 10 - Execution Handler Operation Routing
    Validates: Requirement 5 - Execution Handler Standardization
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Mock all handler functions
        with patch("index.execute_recovery_plan") as mock_execute, patch(
            "index.cancel_execution"
        ) as mock_cancel, patch("index.pause_execution") as mock_pause, patch(
            "index.resume_execution"
        ) as mock_resume, patch(
            "index.terminate_recovery_instances"
        ) as mock_terminate, patch(
            "index.get_recovery_instances"
        ) as mock_get_instances:

            # Mock all handler functions to return success
            mock_execute.return_value = {
                "statusCode": 202,
                "body": json.dumps({"executionId": "exec-123"}),
            }
            mock_cancel.return_value = {
                "statusCode": 200,
                "body": json.dumps({"message": "Cancelled"}),
            }
            mock_pause.return_value = {
                "statusCode": 200,
                "body": json.dumps({"message": "Paused"}),
            }
            mock_resume.return_value = {
                "statusCode": 200,
                "body": json.dumps({"message": "Resumed"}),
            }
            mock_terminate.return_value = {
                "statusCode": 200,
                "body": json.dumps({"message": "Terminated"}),
            }
            mock_get_instances.return_value = {
                "statusCode": 200,
                "body": json.dumps({"instances": []}),
            }

            # Generate valid parameters for this operation using st.data()
            parameters = data.draw(valid_parameters_for_operation(operation))

            event = {"operation": operation, "parameters": parameters}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Should not return operation routing errors
            assert result.get("error") != "INVALID_OPERATION"
            assert result.get("error") != "MISSING_OPERATION"

            # Property assertion: Result should be a dict
            assert isinstance(result, dict)

            # Property assertion: Should not contain API Gateway wrapping
            assert "statusCode" not in result


# Property: Response format consistency - no API Gateway wrapping
# Feature: direct-lambda-invocation-mode, Property 10: Execution Handler Operation Routing
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

    Validates: Property 10 - Execution Handler Operation Routing
    Validates: Requirement 10.4 - Direct invocation response format
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Mock all handler functions
        with patch("index.execute_recovery_plan") as mock_execute, patch(
            "index.cancel_execution"
        ) as mock_cancel, patch("index.pause_execution") as mock_pause, patch(
            "index.resume_execution"
        ) as mock_resume, patch(
            "index.terminate_recovery_instances"
        ) as mock_terminate, patch(
            "index.get_recovery_instances"
        ) as mock_get_instances, patch(
            "index._delegate_to_query_handler"
        ) as mock_delegate:

            # Mock all handler functions to return API Gateway format
            api_gateway_response = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"data": "success"}),
            }

            mock_execute.return_value = api_gateway_response
            mock_cancel.return_value = api_gateway_response
            mock_pause.return_value = api_gateway_response
            mock_resume.return_value = api_gateway_response
            mock_terminate.return_value = api_gateway_response
            mock_get_instances.return_value = api_gateway_response
            mock_delegate.return_value = {"data": "success"}

            # Generate valid parameters using st.data()
            parameters = data.draw(valid_parameters_for_operation(operation))

            event = {"operation": operation, "parameters": parameters}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Response should NOT contain API Gateway fields
            assert "statusCode" not in result
            assert "headers" not in result

            # Property assertion: Response should be a dict
            assert isinstance(result, dict)

            # Property assertion: If there's data, it should be directly accessible
            if "data" in result:
                assert result["data"] == "success"


# Property: Error response structure consistency
# Feature: direct-lambda-invocation-mode, Property 11: Execution Handler Invalid Operation Rejection
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

    Validates: Property 11 - Execution Handler Invalid Operation Rejection
    Validates: Requirement 9.7 - Consistent error response structure
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        event = {"operation": operation, "parameters": {}}

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
# Feature: direct-lambda-invocation-mode, Property 11: Execution Handler Invalid Operation Rejection
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(parameters=st.dictionaries(st.text(), st.text()))
def test_property_missing_operation_returns_error(parameters):
    """
    Property: For any event missing operation field, should return MISSING_OPERATION error.

    Universal property: Given any event structure that does NOT contain
    an "operation" field, the system should return an error with code
    "MISSING_OPERATION".

    Validates: Property 11 - Execution Handler Invalid Operation Rejection
    Validates: Requirement 9.1 - Missing required parameters
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Event without operation field
        event = {"parameters": parameters}

        result = index.handle_direct_invocation(event, mock_context)

        # Property assertion: Should return MISSING_OPERATION error
        assert result.get("error") == "MISSING_OPERATION"

        # Property assertion: Error message should be present
        assert "message" in result
        assert "operation" in result["message"].lower()


# Property: All valid operations return dict responses
# Feature: direct-lambda-invocation-mode, Property 10: Execution Handler Operation Routing
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

    Validates: Property 10 - Execution Handler Operation Routing
    Validates: Requirement 10.4 - Response format consistency
    """
    with setup_test_environment():
        import index

        mock_context = get_mock_context()

        # Mock all handlers
        with patch("index.execute_recovery_plan") as mock_execute, patch(
            "index.cancel_execution"
        ) as mock_cancel, patch("index.pause_execution") as mock_pause, patch(
            "index.resume_execution"
        ) as mock_resume, patch(
            "index.terminate_recovery_instances"
        ) as mock_terminate, patch(
            "index.get_recovery_instances"
        ) as mock_get_instances, patch(
            "index._delegate_to_query_handler"
        ) as mock_delegate:

            # Mock all handlers to return various response formats
            mock_execute.return_value = {
                "statusCode": 202,
                "body": json.dumps({"executionId": "exec-123"}),
            }
            mock_cancel.return_value = {
                "statusCode": 200,
                "body": json.dumps({"message": "Cancelled"}),
            }
            mock_pause.return_value = {
                "statusCode": 200,
                "body": json.dumps({"message": "Paused"}),
            }
            mock_resume.return_value = {
                "statusCode": 200,
                "body": json.dumps({"message": "Resumed"}),
            }
            mock_terminate.return_value = {
                "statusCode": 200,
                "body": json.dumps({"message": "Terminated"}),
            }
            mock_get_instances.return_value = {
                "statusCode": 200,
                "body": json.dumps({"instances": []}),
            }
            mock_delegate.return_value = {"data": "success"}

            # Generate valid parameters using st.data()
            parameters = data.draw(valid_parameters_for_operation(operation))

            event = {"operation": operation, "parameters": parameters}

            result = index.handle_direct_invocation(event, mock_context)

            # Property assertion: Result must be a dict
            assert isinstance(result, dict)

            # Property assertion: Result must NOT be a string
            assert not isinstance(result, str)

            # Property assertion: Result must NOT be bytes
            assert not isinstance(result, bytes)
