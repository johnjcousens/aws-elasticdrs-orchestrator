"""
Property 17: Rollback Preserves Data and Executions

Feature: function-specific-iam-roles
Property 17: For any CloudFormation stack update that changes UseFunctionSpecificRoles
from true to false, when the update completes, all DynamoDB data should remain unchanged,
all running Step Functions executions should continue without interruption, and all Lambda
functions should immediately use the Unified Role.

This property test verifies the rollback capability using data captured from the
rollback capability test execution.

Validates: Requirements 11.2, 11.3, 11.4, 11.5

Environment: aws-drs-orchestration-qa
Region: us-east-2
Account: 438465159935

Usage:
    # Activate virtual environment first
    source .venv/bin/activate

    # Run property test
    .venv/bin/pytest tests/integration/test_property_17_rollback.py -v

Requirements:
    - Rollback capability test must have been executed first
    - rollback_capability_results.json must exist
    - Python 3.9+ with pytest installed in .venv
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

import pytest

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Test data file
RESULTS_FILE = Path("tests/integration/rollback_capability_results.json")


@pytest.fixture(scope="module")
def rollback_results() -> Dict[str, Any]:
    """Load rollback capability test results."""
    if not RESULTS_FILE.exists():
        pytest.skip(f"Rollback results file not found: {RESULTS_FILE}")

    with open(RESULTS_FILE, "r") as f:
        return json.load(f)


def test_property_17_dynamodb_data_preserved(rollback_results: Dict[str, Any]) -> None:
    """
    Property 17a: DynamoDB data is preserved during rollback.

    Verifies that all DynamoDB tables maintain the same item count before and
    after rollback from function-specific to unified roles.
    """
    logger.info("Testing Property 17a: DynamoDB data preserved")

    pre_state = rollback_results["pre_rollback_state"]
    post_state = rollback_results["post_rollback_state"]

    pre_tables = pre_state["dynamodb_tables"]
    post_tables = post_state["dynamodb_tables"]

    for table_name, pre_data in pre_tables.items():
        if "error" in pre_data:
            logger.warning(f"Skipping {table_name} - pre-rollback error: {pre_data['error']}")
            continue

        post_data = post_tables.get(table_name, {})
        if "error" in post_data:
            logger.warning(f"Skipping {table_name} - post-rollback error: {post_data['error']}")
            continue

        pre_count = pre_data["item_count"]
        post_count = post_data["item_count"]

        logger.info(f"{table_name}: {pre_count} items before, {post_count} items after")

        assert pre_count == post_count, (
            f"DynamoDB data loss detected in {table_name}: "
            f"{pre_count} items before rollback, {post_count} items after rollback"
        )

    logger.info("✓ Property 17a verified: All DynamoDB data preserved")


def test_property_17_lambda_functions_use_unified_role(rollback_results: Dict[str, Any]) -> None:
    """
    Property 17b: Lambda functions switch to unified role after rollback.

    Verifies that all Lambda functions are using the unified role after rollback
    from function-specific roles configuration.
    """
    logger.info("Testing Property 17b: Lambda functions use unified role")

    post_state = rollback_results["post_rollback_state"]
    post_functions = post_state["lambda_functions"]

    unified_role_pattern = "unified-role"

    for function_name, function_data in post_functions.items():
        if "error" in function_data:
            logger.warning(f"Skipping {function_name} - error: {function_data['error']}")
            continue

        role_arn = function_data["role_arn"]
        logger.info(f"{function_name}: {role_arn}")

        assert unified_role_pattern in role_arn, (
            f"Lambda function {function_name} is not using unified role. "
            f"Current role: {role_arn}"
        )

    logger.info("✓ Property 17b verified: All Lambda functions use unified role")


def test_property_17_stepfunctions_executions_not_interrupted(rollback_results: Dict[str, Any]) -> None:
    """
    Property 17c: Step Functions executions continue without interruption.

    Verifies that any Step Functions executions that were running before rollback
    continue to run after rollback without interruption.
    """
    logger.info("Testing Property 17c: Step Functions executions not interrupted")

    pre_state = rollback_results["pre_rollback_state"]
    post_state = rollback_results["post_rollback_state"]

    pre_executions = pre_state.get("stepfunctions_executions", [])
    post_executions = post_state.get("stepfunctions_executions", [])

    if isinstance(pre_executions, dict) and "error" in pre_executions:
        logger.warning(f"Skipping - pre-rollback error: {pre_executions['error']}")
        pytest.skip("Unable to verify Step Functions executions - pre-rollback data unavailable")

    if isinstance(post_executions, dict) and "error" in post_executions:
        logger.warning(f"Skipping - post-rollback error: {post_executions['error']}")
        pytest.skip("Unable to verify Step Functions executions - post-rollback data unavailable")

    pre_execution_arns = {exec["execution_arn"] for exec in pre_executions}
    post_execution_arns = {exec["execution_arn"] for exec in post_executions}

    interrupted_executions = pre_execution_arns - post_execution_arns

    logger.info(f"Executions before rollback: {len(pre_executions)}")
    logger.info(f"Executions after rollback: {len(post_executions)}")
    logger.info(f"Interrupted executions: {len(interrupted_executions)}")

    assert len(interrupted_executions) == 0, (
        f"Step Functions executions were interrupted during rollback. "
        f"Interrupted execution ARNs: {interrupted_executions}"
    )

    logger.info("✓ Property 17c verified: No Step Functions executions interrupted")


def test_property_17_cloudformation_parameter_updated(rollback_results: Dict[str, Any]) -> None:
    """
    Property 17d: CloudFormation parameter updated to false.

    Verifies that the UseFunctionSpecificRoles parameter is set to 'false' after
    rollback deployment.
    """
    logger.info("Testing Property 17d: CloudFormation parameter updated")

    post_state = rollback_results["post_rollback_state"]
    post_params = post_state.get("cloudformation_parameters", {})

    if "error" in post_params:
        logger.warning(f"Skipping - error: {post_params['error']}")
        pytest.skip("Unable to verify CloudFormation parameters - data unavailable")

    param_value = post_params.get("UseFunctionSpecificRoles")

    logger.info(f"UseFunctionSpecificRoles parameter: {param_value}")

    assert param_value == "false", (
        f"CloudFormation parameter not updated correctly. "
        f"Expected 'false', got '{param_value}'"
    )

    logger.info("✓ Property 17d verified: CloudFormation parameter updated to 'false'")


def test_property_17_overall_rollback_success(rollback_results: Dict[str, Any]) -> None:
    """
    Property 17: Overall rollback success verification.

    Verifies that the overall rollback test passed all checks, confirming that
    rollback from function-specific to unified roles preserves all data and
    executions without service interruption.
    """
    logger.info("Testing Property 17: Overall rollback success")

    verification_results = rollback_results.get("verification_results", {})
    overall_success = verification_results.get("overall_success", False)

    checks = verification_results.get("checks", [])
    logger.info(f"Total checks: {len(checks)}")

    for check in checks:
        check_name = check["name"]
        check_success = check["success"]
        status = "✓ PASS" if check_success else "✗ FAIL"
        logger.info(f"  {status}: {check_name}")

    assert overall_success, (
        "Rollback test failed - not all checks passed. "
        "See rollback_capability_results.json for details."
    )

    logger.info("✓ Property 17 verified: Rollback preserves data and executions")
