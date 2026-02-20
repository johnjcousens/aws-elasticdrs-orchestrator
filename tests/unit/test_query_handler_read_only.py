"""
Unit tests to verify query-handler contains only read-only operations.

This test suite validates that the query-handler Lambda function does not
contain any write operations after the staging account sync refactoring.

Requirements Validated:
- 11.13: Query-handler contains only read-only operations after refactoring
"""

import ast
import os
from typing import List, Set


def get_query_handler_functions() -> Set[str]:
    """
    Parse query-handler/index.py and extract all function names.

    Returns:
        Set of function names defined in query-handler
    """
    query_handler_path = os.path.join(
        os.path.dirname(__file__),
        "../../lambda/query-handler/index.py"
    )

    with open(query_handler_path, "r") as f:
        tree = ast.parse(f.read())

    functions = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.add(node.name)

    return functions


def test_query_handler_has_no_staging_sync_functions():
    """
    Verify query-handler does not contain staging account sync functions.

    These functions should have been moved to data-management-handler:
    - handle_sync_staging_accounts
    - auto_extend_staging_servers
    - extend_source_server
    - get_extended_source_servers
    - get_staging_account_servers

    Validates: Requirement 11.13
    """
    functions = get_query_handler_functions()

    # Functions that should NOT exist in query-handler
    forbidden_functions = {
        "handle_sync_staging_accounts",
        "auto_extend_staging_servers",
        "extend_source_server",
        "get_extended_source_servers",
        "get_staging_account_servers",
    }

    # Check for forbidden functions
    found_forbidden = forbidden_functions.intersection(functions)

    assert not found_forbidden, (
        f"Query-handler contains write operations that should have been "
        f"moved to data-management-handler: {found_forbidden}"
    )


def test_query_handler_has_no_inventory_sync_write():
    """
    Verify query-handler does not contain inventory sync write operations.

    The handle_sync_source_server_inventory function performs write
    operations to DynamoDB and should be moved to data-management-handler.

    Validates: Requirement 11.13
    """
    functions = get_query_handler_functions()

    # This function writes to DynamoDB and should be moved
    assert "handle_sync_source_server_inventory" not in functions, (
        "Query-handler contains handle_sync_source_server_inventory which "
        "performs write operations to DynamoDB"
    )


def test_query_handler_contains_only_read_operations():
    """
    Verify all remaining functions in query-handler are read-only.

    This test checks that function names follow read-only patterns:
    - get_*
    - handle_get_*
    - handle_discover_*
    - handle_validate_*
    - handle_user_*
    - handle_api_gateway_request
    - handle_direct_invocation

    Validates: Requirement 11.13
    """
    functions = get_query_handler_functions()

    # Allowed read-only function name patterns
    read_only_patterns = [
        "get_",
        "handle_get_",
        "handle_discover_",
        "handle_validate_",
        "handle_user_",
        "handle_api_gateway_request",
        "handle_direct_invocation",
        "lambda_handler",
        "response",
        "transform_",
        "map_",
        "is_",
        "check_",
        "query_",
        "list_",
        "describe_",
        "calculate_",
        "format_",
        "parse_",
        "validate_",
        "extract_",
    ]

    # Functions that don't match read-only patterns
    write_functions = []

    for func in functions:
        # Skip private functions (start with _)
        if func.startswith("_"):
            continue

        # Check if function matches any read-only pattern
        is_read_only = any(
            func.startswith(pattern) for pattern in read_only_patterns
        )

        if not is_read_only:
            write_functions.append(func)

    # Known exceptions (functions that don't follow naming pattern but are
    # read-only)
    known_exceptions = {
        "DecimalEncoder",  # JSON encoder class
        "response",  # Response helper
    }

    # Remove known exceptions
    write_functions = [
        f for f in write_functions if f not in known_exceptions
    ]

    assert not write_functions, (
        f"Query-handler contains functions that don't follow read-only "
        f"naming patterns: {write_functions}. These may be write operations "
        f"that should be moved to data-management-handler."
    )


def test_query_handler_has_expected_read_operations():
    """
    Verify query-handler contains expected read-only operations.

    This is a positive test to ensure the handler still has its core
    read-only functionality after refactoring.

    Validates: Requirement 11.13
    """
    functions = get_query_handler_functions()

    # Expected read-only operations
    expected_operations = {
        "handle_get_source_server_inventory",
        "handle_discover_staging_accounts",
        "handle_validate_staging_account",
        "handle_get_combined_capacity",
        "handle_get_all_accounts_capacity",
        "handle_user_permissions",
        "handle_user_profile",
        "handle_user_roles",
    }

    # Check that expected operations exist
    missing_operations = expected_operations - functions

    assert not missing_operations, (
        f"Query-handler is missing expected read-only operations: "
        f"{missing_operations}"
    )
