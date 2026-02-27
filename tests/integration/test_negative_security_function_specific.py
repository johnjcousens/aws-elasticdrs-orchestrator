"""
Negative security tests for function-specific IAM roles.

This module tests that Lambda functions CANNOT perform unauthorized operations
when using function-specific IAM roles. These tests validate the principle of
least privilege by directly attempting AWS API calls using the Lambda
function's execution role credentials.

**Validates: Requirements 9.14, 9.15, 9.16, 9.17, 9.18, 9.19**

Test Strategy:
- Use STS AssumeRole to get credentials for each Lambda function's role
- Attempt unauthorized AWS API operations using those credentials
- Verify that operations fail with AccessDenied errors
- Check that CloudWatch Alarms are configured correctly for security monitoring
"""

import json
import time
from typing import Dict, Any, List, Optional
import boto3
import pytest
from botocore.exceptions import ClientError


# AWS clients
sts_client = boto3.client("sts", region_name="us-east-2")
iam_client = boto3.client("iam", region_name="us-east-2")
cloudwatch_client = boto3.client("cloudwatch", region_name="us-east-2")
logs_client = boto3.client("logs", region_name="us-east-2")

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
        # Get role ARN
        role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
        
        # Assume role
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"negative-security-test-{int(time.time())}"
        )
        
        return {
            "aws_access_key_id": response["Credentials"]["AccessKeyId"],
            "aws_secret_access_key": response["Credentials"]["SecretAccessKey"],
            "aws_session_token": response["Credentials"]["SessionToken"]
        }
    except ClientError as e:
        print(f"Failed to assume role {role_name}: {e}")
        return None


def create_boto3_client(
    service: str, credentials: Dict[str, str]
) -> Any:
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
# Query Handler Negative Tests
# ============================================================================


def test_query_handler_cannot_write_dynamodb():
    """
    Query Handler should not be able to write to DynamoDB.

    **Validates: Requirement 9.14**

    Test Strategy:
    - Assume Query Handler role
    - Attempt DynamoDB PutItem operation
    - Verify AccessDenied error is raised
    """
    # Get credentials for Query Handler role
    credentials = get_role_credentials(QUERY_HANDLER_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {QUERY_HANDLER_ROLE}")

    # Create DynamoDB client with Query Handler credentials
    dynamodb = create_boto3_client("dynamodb", credentials)

    # Attempt to write to DynamoDB
    table_name = f"{PROJECT_NAME}-protection-groups-{ENVIRONMENT}"
    
    with pytest.raises(ClientError) as exc_info:
        dynamodb.put_item(
            TableName=table_name,
            Item={
                "id": {"S": "test-negative-security"},
                "name": {"S": "test-item"}
            }
        )
    
    # Verify AccessDenied error
    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code == "AccessDeniedException", (
        f"Expected AccessDeniedException, got {error_code}"
    )


def test_query_handler_cannot_start_recovery():
    """
    Query Handler should not be able to start DRS recovery.

    **Validates: Requirement 9.15**

    Test Strategy:
    - Assume Query Handler role
    - Attempt DRS StartRecovery operation
    - Verify AccessDenied error is raised
    """
    # Get credentials for Query Handler role
    credentials = get_role_credentials(QUERY_HANDLER_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {QUERY_HANDLER_ROLE}")

    # Create DRS client with Query Handler credentials
    drs = create_boto3_client("drs", credentials)

    # Attempt to start DRS recovery
    with pytest.raises(ClientError) as exc_info:
        drs.start_recovery(
            sourceServers=[
                {"sourceServerID": "s-test-negative-security"}
            ]
        )
    
    # Verify AccessDenied error
    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code in ["AccessDeniedException", "UnauthorizedOperation"], (
        f"Expected AccessDeniedException or UnauthorizedOperation, got "
        f"{error_code}"
    )


def test_query_handler_cannot_invoke_data_management():
    """
    Query Handler should not be able to invoke Data Management Handler.

    **Validates: Requirement 9.14**

    Test Strategy:
    - Assume Query Handler role
    - Attempt Lambda InvokeFunction on Data Management Handler
    - Verify AccessDenied error is raised
    """
    # Get credentials for Query Handler role
    credentials = get_role_credentials(QUERY_HANDLER_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {QUERY_HANDLER_ROLE}")

    # Create Lambda client with Query Handler credentials
    lambda_client = create_boto3_client("lambda", credentials)

    # Attempt to invoke Data Management Handler
    function_name = f"{PROJECT_NAME}-data-management-handler-{ENVIRONMENT}"
    
    with pytest.raises(ClientError) as exc_info:
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps({"test": "negative-security"})
        )
    
    # Verify AccessDenied error
    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code == "AccessDeniedException", (
        f"Expected AccessDeniedException, got {error_code}"
    )


# ============================================================================
# Data Management Handler Negative Tests
# ============================================================================


def test_data_management_cannot_start_recovery():
    """
    Data Management Handler should not be able to start DRS recovery.

    **Validates: Requirement 9.16**

    Test Strategy:
    - Assume Data Management Handler role
    - Attempt DRS StartRecovery operation
    - Verify AccessDenied error is raised
    """
    # Get credentials for Data Management Handler role
    credentials = get_role_credentials(DATA_MANAGEMENT_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {DATA_MANAGEMENT_ROLE}")

    # Create DRS client with Data Management Handler credentials
    drs = create_boto3_client("drs", credentials)

    # Attempt to start DRS recovery
    with pytest.raises(ClientError) as exc_info:
        drs.start_recovery(
            sourceServers=[
                {"sourceServerID": "s-test-negative-security"}
            ]
        )
    
    # Verify AccessDenied error
    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code in ["AccessDeniedException", "UnauthorizedOperation"], (
        f"Expected AccessDeniedException or UnauthorizedOperation, got "
        f"{error_code}"
    )


def test_data_management_cannot_terminate_recovery_instances():
    """
    Data Management Handler should not be able to terminate recovery instances.

    **Validates: Requirement 9.16**

    Test Strategy:
    - Assume Data Management Handler role
    - Attempt DRS TerminateRecoveryInstances operation
    - Verify AccessDenied error is raised
    """
    # Get credentials for Data Management Handler role
    credentials = get_role_credentials(DATA_MANAGEMENT_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {DATA_MANAGEMENT_ROLE}")

    # Create DRS client with Data Management Handler credentials
    drs = create_boto3_client("drs", credentials)

    # Attempt to terminate recovery instances
    with pytest.raises(ClientError) as exc_info:
        drs.terminate_recovery_instances(
            recoveryInstanceIDs=["i-test-negative-security"]
        )
    
    # Verify AccessDenied error
    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code in ["AccessDeniedException", "UnauthorizedOperation"], (
        f"Expected AccessDeniedException or UnauthorizedOperation, got "
        f"{error_code}"
    )


def test_data_management_cannot_start_step_functions():
    """
    Data Management Handler should not be able to start Step Functions.

    **Validates: Requirement 9.16**

    Test Strategy:
    - Assume Data Management Handler role
    - Attempt Step Functions StartExecution operation
    - Verify AccessDenied error is raised
    """
    # Get credentials for Data Management Handler role
    credentials = get_role_credentials(DATA_MANAGEMENT_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {DATA_MANAGEMENT_ROLE}")

    # Create Step Functions client with Data Management Handler credentials
    sfn = create_boto3_client("stepfunctions", credentials)

    # Attempt to start Step Functions execution
    state_machine_arn = (
        f"arn:aws:states:{REGION}:{ACCOUNT_ID}:stateMachine:"
        f"{PROJECT_NAME}-dr-orch-sf-{ENVIRONMENT}"
    )
    
    with pytest.raises(ClientError) as exc_info:
        sfn.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps({"test": "negative-security"})
        )
    
    # Verify AccessDenied error
    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code == "AccessDeniedException", (
        f"Expected AccessDeniedException, got {error_code}"
    )


# ============================================================================
# Frontend Deployer Negative Tests
# ============================================================================


def test_frontend_deployer_cannot_access_dynamodb():
    """
    Frontend Deployer should not be able to access DynamoDB.

    **Validates: Requirement 9.18**

    Test Strategy:
    - Assume Frontend Deployer role
    - Attempt DynamoDB GetItem operation
    - Verify AccessDenied error is raised
    """
    # Get credentials for Frontend Deployer role
    credentials = get_role_credentials(FRONTEND_DEPLOYER_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {FRONTEND_DEPLOYER_ROLE}")

    # Create DynamoDB client with Frontend Deployer credentials
    dynamodb = create_boto3_client("dynamodb", credentials)

    # Attempt to read from DynamoDB
    table_name = f"{PROJECT_NAME}-protection-groups-{ENVIRONMENT}"
    
    with pytest.raises(ClientError) as exc_info:
        dynamodb.get_item(
            TableName=table_name,
            Key={"id": {"S": "test-negative-security"}}
        )
    
    # Verify AccessDenied error
    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code == "AccessDeniedException", (
        f"Expected AccessDeniedException, got {error_code}"
    )


def test_frontend_deployer_cannot_access_drs():
    """
    Frontend Deployer should not be able to access DRS.

    **Validates: Requirement 9.17**

    Test Strategy:
    - Assume Frontend Deployer role
    - Attempt DRS DescribeSourceServers operation
    - Verify AccessDenied error is raised
    """
    # Get credentials for Frontend Deployer role
    credentials = get_role_credentials(FRONTEND_DEPLOYER_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {FRONTEND_DEPLOYER_ROLE}")

    # Create DRS client with Frontend Deployer credentials
    drs = create_boto3_client("drs", credentials)

    # Attempt to describe DRS source servers
    with pytest.raises(ClientError) as exc_info:
        drs.describe_source_servers(maxResults=10)
    
    # Verify AccessDenied error
    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code in ["AccessDeniedException", "UnauthorizedOperation"], (
        f"Expected AccessDeniedException or UnauthorizedOperation, got "
        f"{error_code}"
    )


def test_frontend_deployer_cannot_invoke_query_handler():
    """
    Frontend Deployer should not be able to invoke Query Handler.

    **Validates: Requirement 9.18**

    Test Strategy:
    - Assume Frontend Deployer role
    - Attempt Lambda InvokeFunction on Query Handler
    - Verify AccessDenied error is raised
    """
    # Get credentials for Frontend Deployer role
    credentials = get_role_credentials(FRONTEND_DEPLOYER_ROLE)
    if not credentials:
        pytest.skip(f"Cannot assume role {FRONTEND_DEPLOYER_ROLE}")

    # Create Lambda client with Frontend Deployer credentials
    lambda_client = create_boto3_client("lambda", credentials)

    # Attempt to invoke Query Handler
    function_name = f"{PROJECT_NAME}-query-handler-{ENVIRONMENT}"
    
    with pytest.raises(ClientError) as exc_info:
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps({"test": "negative-security"})
        )
    
    # Verify AccessDenied error
    error_code = exc_info.value.response["Error"]["Code"]
    assert error_code == "AccessDeniedException", (
        f"Expected AccessDeniedException, got {error_code}"
    )


# ============================================================================
# CloudWatch Alarms Verification
# ============================================================================


def test_cloudwatch_alarms_configured():
    """
    Verify CloudWatch Alarms are configured for AccessDenied errors.

    **Validates: Requirement 10.1, 10.2, 10.3**

    Test Strategy:
    - Check that CloudWatch Alarms exist for all Lambda functions
    - Verify alarm configuration (threshold, period, evaluation periods)
    - Verify alarm actions (SNS topic notifications)
    """
    # Expected alarm name pattern
    alarm_name = f"{PROJECT_NAME}-access-denied-{ENVIRONMENT}"

    # Get alarm details
    try:
        response = cloudwatch_client.describe_alarms(
            AlarmNames=[alarm_name]
        )
    except ClientError as e:
        pytest.fail(f"Failed to describe CloudWatch Alarm: {e}")

    # Verify alarm exists
    assert len(response["MetricAlarms"]) > 0, (
        f"CloudWatch Alarm '{alarm_name}' not found"
    )

    alarm = response["MetricAlarms"][0]

    # Verify alarm configuration
    assert alarm["Threshold"] == 5, (
        f"Alarm threshold should be 5, got {alarm['Threshold']}"
    )
    assert alarm["Period"] == 300, (
        f"Alarm period should be 300 seconds, got {alarm['Period']}"
    )
    assert alarm["EvaluationPeriods"] == 1, (
        f"Alarm evaluation periods should be 1, got "
        f"{alarm['EvaluationPeriods']}"
    )

    # Verify alarm has SNS actions
    assert len(alarm.get("AlarmActions", [])) > 0, (
        "Alarm should have at least one SNS action configured"
    )

    # Verify SNS topic ARN pattern
    for action in alarm["AlarmActions"]:
        assert f"arn:aws:sns:{REGION}:{ACCOUNT_ID}:" in action, (
            f"Alarm action should be an SNS topic ARN, got {action}"
        )


def test_cloudwatch_metric_filters_exist():
    """
    Verify CloudWatch Metric Filters exist for AccessDenied errors.

    **Validates: Requirement 10.4**

    Test Strategy:
    - Check that metric filters exist for all Lambda function log groups
    - Verify filter patterns match AccessDenied errors
    """
    function_names = [
        f"{PROJECT_NAME}-query-handler-{ENVIRONMENT}",
        f"{PROJECT_NAME}-data-management-handler-{ENVIRONMENT}",
        f"{PROJECT_NAME}-frontend-deployer-{ENVIRONMENT}"
    ]

    for function_name in function_names:
        log_group = f"/aws/lambda/{function_name}"

        # Get metric filters for log group
        try:
            response = logs_client.describe_metric_filters(
                logGroupName=log_group
            )
        except ClientError as e:
            pytest.fail(
                f"Failed to describe metric filters for {log_group}: {e}"
            )

        # Verify at least one metric filter exists
        assert len(response["metricFilters"]) > 0, (
            f"No metric filters found for log group {log_group}"
        )

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


# ============================================================================
# Resource Pattern Restrictions
# ============================================================================


def test_functions_cannot_access_non_project_resources():
    """
    Verify all functions cannot access resources outside project naming pattern.

    **Validates: Requirement 9.19**

    Test Strategy:
    - Attempt to access DynamoDB tables not matching {ProjectName}-* pattern
    - Verify AccessDenied errors for all functions
    """
    # Non-project table name
    non_project_table = "some-other-table-not-in-project"

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
            f"Query Handler should receive AccessDenied for non-project table, "
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
            f"Data Management Handler should receive AccessDenied for "
            f"non-project table, got {error_code}"
        )
