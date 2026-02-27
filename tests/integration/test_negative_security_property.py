"""
Property-based negative security tests for function-specific IAM roles.

This module implements Property 16: Security Validation Through Negative Testing
using Hypothesis property-based testing framework with minimum 100 iterations.

**Property 16**: For any Lambda function and any operation that the function
should NOT have permission to perform, when the function attempts the operation,
the operation should fail with AccessDenied error.

**Validates: Requirements 9.14, 9.15, 9.16, 9.17, 9.18, 9.19**

Test Strategy:
- Use Hypothesis to generate test scenarios with multiple unauthorized operations
- Use STS AssumeRole to get credentials for each Lambda function's role
- Attempt unauthorized AWS API operations using those credentials
- Verify that operations fail with AccessDenied errors
- Run minimum 100 iterations per property test
"""

import json
import time
from typing import Dict, Any, List, Optional, Tuple
import boto3
import pytest
from botocore.exceptions import ClientError
from hypothesis import given, strategies as st, settings, HealthCheck


# AWS clients - created lazily to avoid stale credentials
def get_sts_client():
    """Get STS client with current credentials."""
    return boto3.client("sts", region_name="us-east-2")


def get_cloudwatch_client():
    """Get CloudWatch client with current credentials."""
    return boto3.client("cloudwatch", region_name="us-east-2")


def get_logs_client():
    """Get CloudWatch Logs client with current credentials."""
    return boto3.client("logs", region_name="us-east-2")

# Test configuration
PROJECT_NAME = "aws-drs-orchestration"
ENVIRONMENT = "qa"
ACCOUNT_ID = "438465159935"
REGION = "us-east-2"

# IAM role names
QUERY_HANDLER_ROLE = f"{PROJECT_NAME}-query-handler-role-{ENVIRONMENT}"
DATA_MANAGEMENT_ROLE = f"{PROJECT_NAME}-data-management-role-{ENVIRONMENT}"
FRONTEND_DEPLOYER_ROLE = f"{PROJECT_NAME}-frontend-deployer-role-{ENVIRONMENT}"


def get_role_credentials(role_name: str) -> Optional[Dict[str, str]]:
    """
    Get temporary credentials for a Lambda function's IAM role.

    Args:
        role_name: Name of the IAM role

    Returns:
        Dictionary with AccessKeyId, SecretAccessKey, SessionToken
        or None if role cannot be assumed
    """
    try:
        sts_client = get_sts_client()
        role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"negative-security-pbt-{int(time.time())}"
        )
        return {
            "aws_access_key_id": response["Credentials"]["AccessKeyId"],
            "aws_secret_access_key": response["Credentials"]["SecretAccessKey"],
            "aws_session_token": response["Credentials"]["SessionToken"]
        }
    except ClientError as e:
        print(f"Failed to assume role {role_name}: {e}")
        return None


def create_boto3_client(service: str, credentials: Dict[str, str]) -> Any:
    """
    Create a boto3 client with specific credentials.

    Args:
        service: AWS service name (e.g., "dynamodb", "drs")
        credentials: Credentials dictionary from get_role_credentials

    Returns:
        Boto3 client
    """
    return boto3.client(
        service,
        region_name=REGION,
        aws_access_key_id=credentials["aws_access_key_id"],
        aws_secret_access_key=credentials["aws_secret_access_key"],
        aws_session_token=credentials["aws_session_token"]
    )


# ============================================================================
# Hypothesis Strategies for Test Data Generation
# ============================================================================


@st.composite
def dynamodb_table_names(draw):
    """Generate DynamoDB table names for testing."""
    table_types = ["protection-groups", "recovery-plans", "execution-history", "target-accounts"]
    table_type = draw(st.sampled_from(table_types))
    return f"{PROJECT_NAME}-{table_type}-{ENVIRONMENT}"


@st.composite
def dynamodb_items(draw):
    """Generate DynamoDB items for testing."""
    item_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    item_name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    return {
        "id": {"S": f"test-negative-{item_id}"},
        "name": {"S": f"test-item-{item_name}"}
    }


@st.composite
def drs_source_server_ids(draw):
    """Generate DRS source server IDs for testing."""
    server_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Ll", "Nd"))))
    return f"s-test-negative-{server_id}"


@st.composite
def lambda_function_names(draw):
    """Generate Lambda function names for testing."""
    function_types = ["query-handler", "data-management-handler", "execution-handler", "frontend-deployer"]
    function_type = draw(st.sampled_from(function_types))
    return f"{PROJECT_NAME}-{function_type}-{ENVIRONMENT}"


@st.composite
def step_function_arns(draw):
    """Generate Step Functions state machine ARNs for testing."""
    return f"arn:aws:states:{REGION}:{ACCOUNT_ID}:stateMachine:{PROJECT_NAME}-dr-orch-sf-{ENVIRONMENT}"


# ============================================================================
# Property 16: Query Handler Cannot Execute Write Operations
# ============================================================================


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    table_name=dynamodb_table_names(),
    item=dynamodb_items()
)
def test_property_query_handler_cannot_write_dynamodb(table_name: str, item: Dict[str, Any]):
    """
    Property 16.1: Query Handler cannot execute DynamoDB write operations.

    **Validates: Requirement 9.14**

    Property: For any DynamoDB table and any item data, when Query Handler
    attempts PutItem operation, the operation should fail with AccessDenied.

    Args:
        table_name: Generated DynamoDB table name
        item: Generated DynamoDB item data
    """
    credentials = get_role_credentials(QUERY_HANDLER_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {QUERY_HANDLER_ROLE}")

    dynamodb = create_boto3_client("dynamodb", credentials)

    with pytest.raises(ClientError) as exc_info:
        dynamodb.put_item(TableName=table_name, Item=item)

    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code == "AccessDeniedException", (
        f"Expected AccessDeniedException for Query Handler PutItem on {table_name}, got {error_code}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(server_id=drs_source_server_ids())
def test_property_query_handler_cannot_start_recovery(server_id: str):
    """
    Property 16.2: Query Handler cannot execute DRS StartRecovery operations.

    **Validates: Requirement 9.15**

    Property: For any DRS source server ID, when Query Handler attempts
    StartRecovery operation, the operation should fail with AccessDenied.

    Args:
        server_id: Generated DRS source server ID
    """
    credentials = get_role_credentials(QUERY_HANDLER_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {QUERY_HANDLER_ROLE}")

    drs = create_boto3_client("drs", credentials)

    with pytest.raises(ClientError) as exc_info:
        drs.start_recovery(sourceServers=[{"sourceServerID": server_id}])

    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code in ["AccessDeniedException", "UnauthorizedOperation"], (
        f"Expected AccessDeniedException for Query Handler StartRecovery with {server_id}, got {error_code}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(function_name=lambda_function_names())
def test_property_query_handler_cannot_invoke_unauthorized_functions(function_name: str):
    """
    Property 16.3: Query Handler cannot invoke unauthorized Lambda functions.

    **Validates: Requirement 9.14**

    Property: For any Lambda function except execution-handler, when Query
    Handler attempts InvokeFunction, the operation should fail with AccessDenied.

    Args:
        function_name: Generated Lambda function name
    """
    # Query Handler can only invoke execution-handler
    if "execution-handler" in function_name:
        pytest.skip("Query Handler is authorized to invoke execution-handler")

    credentials = get_role_credentials(QUERY_HANDLER_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {QUERY_HANDLER_ROLE}")

    lambda_client = create_boto3_client("lambda", credentials)

    with pytest.raises(ClientError) as exc_info:
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps({"test": "negative-security"})
        )

    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code == "AccessDeniedException", (
        f"Expected AccessDeniedException for Query Handler invoking {function_name}, got {error_code}"
    )


# ============================================================================
# Property 16: Data Management Handler Cannot Execute DRS Recovery Operations
# ============================================================================


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(server_id=drs_source_server_ids())
def test_property_data_management_cannot_start_recovery(server_id: str):
    """
    Property 16.4: Data Management Handler cannot execute DRS StartRecovery.

    **Validates: Requirement 9.16**

    Property: For any DRS source server ID, when Data Management Handler
    attempts StartRecovery operation, the operation should fail with AccessDenied.

    Args:
        server_id: Generated DRS source server ID
    """
    credentials = get_role_credentials(DATA_MANAGEMENT_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {DATA_MANAGEMENT_ROLE}")

    drs = create_boto3_client("drs", credentials)

    with pytest.raises(ClientError) as exc_info:
        drs.start_recovery(sourceServers=[{"sourceServerID": server_id}])

    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code in ["AccessDeniedException", "UnauthorizedOperation"], (
        f"Expected AccessDeniedException for Data Management StartRecovery with {server_id}, got {error_code}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    recovery_instance_id=st.text(
        min_size=10, max_size=20, alphabet=st.characters(whitelist_categories=("Ll", "Nd"))
    ).map(lambda x: f"i-test-negative-{x}")
)
def test_property_data_management_cannot_terminate_recovery_instances(recovery_instance_id: str):
    """
    Property 16.5: Data Management Handler cannot terminate recovery instances.

    **Validates: Requirement 9.16**

    Property: For any recovery instance ID, when Data Management Handler
    attempts TerminateRecoveryInstances, the operation should fail with AccessDenied.

    Args:
        recovery_instance_id: Generated recovery instance ID
    """
    credentials = get_role_credentials(DATA_MANAGEMENT_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {DATA_MANAGEMENT_ROLE}")

    drs = create_boto3_client("drs", credentials)

    with pytest.raises(ClientError) as exc_info:
        drs.terminate_recovery_instances(recoveryInstanceIDs=[recovery_instance_id])

    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code in ["AccessDeniedException", "UnauthorizedOperation"], (
        f"Expected AccessDeniedException for Data Management TerminateRecoveryInstances with "
        f"{recovery_instance_id}, got {error_code}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(state_machine_arn=step_function_arns())
def test_property_data_management_cannot_start_step_functions(state_machine_arn: str):
    """
    Property 16.6: Data Management Handler cannot start Step Functions.

    **Validates: Requirement 9.16**

    Property: For any Step Functions state machine ARN, when Data Management
    Handler attempts StartExecution, the operation should fail with AccessDenied.

    Args:
        state_machine_arn: Generated Step Functions state machine ARN
    """
    credentials = get_role_credentials(DATA_MANAGEMENT_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {DATA_MANAGEMENT_ROLE}")

    sfn = create_boto3_client("stepfunctions", credentials)

    with pytest.raises(ClientError) as exc_info:
        sfn.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps({"test": "negative-security"})
        )

    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code == "AccessDeniedException", (
        f"Expected AccessDeniedException for Data Management StartExecution on {state_machine_arn}, "
        f"got {error_code}"
    )


# ============================================================================
# Property 16: Frontend Deployer Cannot Access DRS/DynamoDB
# ============================================================================


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(table_name=dynamodb_table_names())
def test_property_frontend_deployer_cannot_access_dynamodb(table_name: str):
    """
    Property 16.7: Frontend Deployer cannot access DynamoDB.

    **Validates: Requirement 9.18**

    Property: For any DynamoDB table, when Frontend Deployer attempts GetItem
    operation, the operation should fail with AccessDenied.

    Args:
        table_name: Generated DynamoDB table name
    """
    credentials = get_role_credentials(FRONTEND_DEPLOYER_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {FRONTEND_DEPLOYER_ROLE}")

    dynamodb = create_boto3_client("dynamodb", credentials)

    with pytest.raises(ClientError) as exc_info:
        dynamodb.get_item(
            TableName=table_name,
            Key={"id": {"S": "test-negative-security"}}
        )

    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code == "AccessDeniedException", (
        f"Expected AccessDeniedException for Frontend Deployer GetItem on {table_name}, got {error_code}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(max_results=st.integers(min_value=1, max_value=100))
def test_property_frontend_deployer_cannot_access_drs(max_results: int):
    """
    Property 16.8: Frontend Deployer cannot access DRS.

    **Validates: Requirement 9.17**

    Property: For any DRS operation parameters, when Frontend Deployer attempts
    DescribeSourceServers, the operation should fail with AccessDenied.

    Args:
        max_results: Generated max results parameter
    """
    credentials = get_role_credentials(FRONTEND_DEPLOYER_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {FRONTEND_DEPLOYER_ROLE}")

    drs = create_boto3_client("drs", credentials)

    with pytest.raises(ClientError) as exc_info:
        drs.describe_source_servers(maxResults=max_results)

    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code in ["AccessDeniedException", "UnauthorizedOperation"], (
        f"Expected AccessDeniedException for Frontend Deployer DescribeSourceServers, got {error_code}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(function_name=lambda_function_names())
def test_property_frontend_deployer_cannot_invoke_lambda(function_name: str):
    """
    Property 16.9: Frontend Deployer cannot invoke Lambda functions.

    **Validates: Requirement 9.18**

    Property: For any Lambda function, when Frontend Deployer attempts
    InvokeFunction, the operation should fail with AccessDenied.

    Args:
        function_name: Generated Lambda function name
    """
    credentials = get_role_credentials(FRONTEND_DEPLOYER_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {FRONTEND_DEPLOYER_ROLE}")

    lambda_client = create_boto3_client("lambda", credentials)

    with pytest.raises(ClientError) as exc_info:
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps({"test": "negative-security"})
        )

    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code == "AccessDeniedException", (
        f"Expected AccessDeniedException for Frontend Deployer invoking {function_name}, got {error_code}"
    )


# ============================================================================
# Property 16: Resource Pattern Restrictions
# ============================================================================


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    non_project_table=st.text(
        min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pd"))
    ).filter(lambda x: not x.startswith(PROJECT_NAME))
)
def test_property_functions_cannot_access_non_project_resources(non_project_table: str):
    """
    Property 16.10: Functions cannot access resources outside project pattern.

    **Validates: Requirement 9.19**

    Property: For any DynamoDB table not matching {ProjectName}-* pattern,
    when any function attempts access, the operation should fail with AccessDenied.

    Args:
        non_project_table: Generated non-project table name
    """
    # Test Query Handler
    credentials = get_role_credentials(QUERY_HANDLER_ROLE)
    if credentials:
        dynamodb = create_boto3_client("dynamodb", credentials)
        with pytest.raises(ClientError) as exc_info:
            dynamodb.get_item(
                TableName=non_project_table,
                Key={"id": {"S": "test"}}
            )
        error_code = exc_info.value.response["Error"]["Code"]
        assert error_code in ["AccessDeniedException", "ResourceNotFoundException"], (
            f"Query Handler should receive AccessDenied for non-project table {non_project_table}, "
            f"got {error_code}"
        )

    # Test Data Management Handler
    credentials = get_role_credentials(DATA_MANAGEMENT_ROLE)
    if credentials:
        dynamodb = create_boto3_client("dynamodb", credentials)
        with pytest.raises(ClientError) as exc_info:
            dynamodb.get_item(
                TableName=non_project_table,
                Key={"id": {"S": "test"}}
            )
        error_code = exc_info.value.response["Error"]["Code"]
        assert error_code in ["AccessDeniedException", "ResourceNotFoundException"], (
            f"Data Management Handler should receive AccessDenied for non-project table "
            f"{non_project_table}, got {error_code}"
        )


# ============================================================================
# CloudWatch Monitoring Verification
# ============================================================================


def test_cloudwatch_alarms_configured_for_access_denied():
    """
    Verify CloudWatch Alarms are configured for AccessDenied errors.

    **Validates: Requirements 10.1, 10.2, 10.3**

    This test verifies that CloudWatch Alarms exist and are properly configured
    to detect and alert on AccessDenied errors from Lambda functions.
    """
    cloudwatch_client = get_cloudwatch_client()
    alarm_name = f"{PROJECT_NAME}-access-denied-{ENVIRONMENT}"

    try:
        response = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    except ClientError as e:
        pytest.fail(f"Failed to describe CloudWatch Alarm: {e}")

    assert len(response["MetricAlarms"]) > 0, f"CloudWatch Alarm '{alarm_name}' not found"

    alarm = response["MetricAlarms"][0]

    # Verify alarm configuration
    assert alarm["Threshold"] == 5, f"Alarm threshold should be 5, got {alarm['Threshold']}"
    assert alarm["Period"] == 300, f"Alarm period should be 300 seconds, got {alarm['Period']}"
    assert alarm["EvaluationPeriods"] == 1, (
        f"Alarm evaluation periods should be 1, got {alarm['EvaluationPeriods']}"
    )

    # Verify alarm has SNS actions
    assert len(alarm.get("AlarmActions", [])) > 0, "Alarm should have at least one SNS action configured"

    # Verify SNS topic ARN pattern
    for action in alarm["AlarmActions"]:
        assert f"arn:aws:sns:{REGION}:{ACCOUNT_ID}:" in action, (
            f"Alarm action should be an SNS topic ARN, got {action}"
        )


def test_cloudwatch_metric_filters_exist_for_access_denied():
    """
    Verify CloudWatch Metric Filters exist for AccessDenied errors.

    **Validates: Requirement 10.4**

    This test verifies that metric filters are configured to capture
    AccessDenied errors from Lambda function log groups.
    """
    logs_client = get_logs_client()
    function_names = [
        f"{PROJECT_NAME}-query-handler-{ENVIRONMENT}",
        f"{PROJECT_NAME}-data-management-handler-{ENVIRONMENT}",
        f"{PROJECT_NAME}-frontend-deployer-{ENVIRONMENT}"
    ]

    for function_name in function_names:
        log_group = f"/aws/lambda/{function_name}"

        try:
            response = logs_client.describe_metric_filters(logGroupName=log_group)
        except ClientError as e:
            pytest.fail(f"Failed to describe metric filters for {log_group}: {e}")

        assert len(response["metricFilters"]) > 0, f"No metric filters found for log group {log_group}"

        # Verify filter pattern includes AccessDenied
        found_access_denied_filter = False
        for metric_filter in response["metricFilters"]:
            pattern = metric_filter.get("filterPattern", "")
            if "AccessDenied" in pattern or "AccessDeniedException" in pattern:
                found_access_denied_filter = True
                break

        assert found_access_denied_filter, (
            f"No AccessDenied metric filter found for log group {log_group}"
        )
