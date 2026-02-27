"""
Integration tests for CloudWatch monitoring infrastructure.

Tests CloudWatch Log Groups, metric filters, and alarms for all Lambda functions
to verify security monitoring is correctly configured.

Test Environment:
- QA stack: aws-drs-orchestration-qa in us-east-2
- Monitoring stack: cfn/monitoring/alarms-stack.yaml
- 5 Lambda functions monitored:
  - Query Handler
  - Data Management Handler
  - Execution Handler
  - DR Orchestration Step Function
  - Frontend Deployer

Requirements Validated:
- 12.1: CloudWatch Logs exist for all Lambda functions
- 12.2: CloudWatch Alarms configured for AccessDenied errors
- 12.3: Metric filters configured with correct pattern
- 12.4: Metric filters publish to correct namespace
- 12.5: Alarms trigger SNS notifications
- 12.6: Alarms use correct threshold and evaluation period
"""

import boto3
import pytest
from botocore.exceptions import ClientError


@pytest.fixture(scope="module")
def qa_environment():
    """QA environment configuration."""
    return {
        "project_name": "aws-drs-orchestration",
        "environment": "qa",
        "region": "us-east-2",
        "lambda_functions": [
            "query-handler",
            "data-management-handler",
            "execution-handler",
            "dr-orch-sf",
            "frontend-deployer",
        ],
        "metric_namespace": "aws-drs-orchestration/Security",
        "metric_name": "AccessDeniedErrors",
        "alarm_threshold": 5,
        "alarm_period": 300,
    }


@pytest.fixture(scope="function")
def logs_client(qa_environment):
    """CloudWatch Logs client for QA region."""
    return boto3.client("logs", region_name=qa_environment["region"])


@pytest.fixture(scope="function")
def cloudwatch_client(qa_environment):
    """CloudWatch client for QA region."""
    return boto3.client("cloudwatch", region_name=qa_environment["region"])


@pytest.fixture(scope="function")
def sns_client(qa_environment):
    """SNS client for QA region."""
    return boto3.client("sns", region_name=qa_environment["region"])


def test_log_groups_exist_for_all_lambda_functions(logs_client, qa_environment):
    """
    Test that CloudWatch Log Groups exist for all Lambda functions.

    Validates: Requirement 12.1 - CloudWatch Logs for all Lambda functions
    """
    project_name = qa_environment["project_name"]
    environment = qa_environment["environment"]
    lambda_functions = qa_environment["lambda_functions"]

    for function_name in lambda_functions:
        log_group_name = f"/aws/lambda/{project_name}-{function_name}-{environment}"

        try:
            response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name, limit=1)

            log_groups = response.get("logGroups", [])
            assert len(log_groups) > 0, (
                f"Log group not found: {log_group_name}. "
                f"Lambda function may not have been invoked yet or log group was not created."
            )

            # Verify exact match (not just prefix)
            actual_log_group_name = log_groups[0]["logGroupName"]
            assert actual_log_group_name == log_group_name, (
                f"Log group name mismatch: expected {log_group_name}, got {actual_log_group_name}"
            )

            print(f"✓ Log group exists: {log_group_name}")

        except ClientError as e:
            pytest.fail(f"Failed to describe log group {log_group_name}: {e}")


def test_metric_filters_configured_correctly(logs_client, qa_environment):
    """
    Test that metric filters are configured with correct pattern and namespace.

    Validates:
    - Requirement 12.3: Metric filters with AccessDenied pattern
    - Requirement 12.4: Metric filters publish to correct namespace
    """
    project_name = qa_environment["project_name"]
    environment = qa_environment["environment"]
    lambda_functions = qa_environment["lambda_functions"]
    expected_namespace = qa_environment["metric_namespace"]
    expected_metric_name = qa_environment["metric_name"]
    expected_filter_pattern = '[..., msg="*AccessDenied*"]'

    for function_name in lambda_functions:
        log_group_name = f"/aws/lambda/{project_name}-{function_name}-{environment}"

        try:
            response = logs_client.describe_metric_filters(logGroupName=log_group_name)

            metric_filters = response.get("metricFilters", [])
            assert len(metric_filters) > 0, (
                f"No metric filters found for log group: {log_group_name}. "
                f"Monitoring stack may not be deployed correctly."
            )

            # Find AccessDenied metric filter
            access_denied_filter = None
            for mf in metric_filters:
                if mf.get("filterPattern") == expected_filter_pattern:
                    access_denied_filter = mf
                    break

            assert access_denied_filter is not None, (
                f"AccessDenied metric filter not found for log group: {log_group_name}. "
                f"Expected filter pattern: {expected_filter_pattern}"
            )

            # Verify metric transformations
            transformations = access_denied_filter.get("metricTransformations", [])
            assert len(transformations) > 0, (
                f"No metric transformations found for AccessDenied filter in log group: {log_group_name}"
            )

            transformation = transformations[0]
            actual_namespace = transformation.get("metricNamespace")
            actual_metric_name = transformation.get("metricName")

            assert actual_namespace == expected_namespace, (
                f"Metric namespace mismatch for {log_group_name}: "
                f"expected {expected_namespace}, got {actual_namespace}"
            )

            assert actual_metric_name == expected_metric_name, (
                f"Metric name mismatch for {log_group_name}: "
                f"expected {expected_metric_name}, got {actual_metric_name}"
            )

            print(f"✓ Metric filter configured correctly for {log_group_name}")
            print(f"  Filter pattern: {expected_filter_pattern}")
            print(f"  Namespace: {actual_namespace}")
            print(f"  Metric name: {actual_metric_name}")

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Log group not found: {log_group_name}. "
                    f"Lambda function may not have been invoked yet."
                )
            else:
                pytest.fail(f"Failed to describe metric filters for {log_group_name}: {e}")


def test_cloudwatch_alarms_configured_correctly(cloudwatch_client, qa_environment):
    """
    Test that CloudWatch Alarms are configured with correct threshold and period.

    Validates:
    - Requirement 12.2: CloudWatch Alarms for AccessDenied errors
    - Requirement 12.6: Alarms use correct threshold and evaluation period
    """
    project_name = qa_environment["project_name"]
    environment = qa_environment["environment"]
    lambda_functions = qa_environment["lambda_functions"]
    expected_threshold = qa_environment["alarm_threshold"]
    expected_period = qa_environment["alarm_period"]
    expected_namespace = qa_environment["metric_namespace"]
    expected_metric_name = qa_environment["metric_name"]

    for function_name in lambda_functions:
        alarm_name = f"{project_name}-{function_name}-access-denied-{environment}"

        try:
            response = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])

            alarms = response.get("MetricAlarms", [])
            assert len(alarms) > 0, (
                f"Alarm not found: {alarm_name}. " f"Monitoring stack may not be deployed correctly."
            )

            alarm = alarms[0]

            # Verify alarm configuration
            actual_namespace = alarm.get("Namespace")
            actual_metric_name = alarm.get("MetricName")
            actual_threshold = alarm.get("Threshold")
            actual_period = alarm.get("Period")
            actual_statistic = alarm.get("Statistic")
            actual_comparison = alarm.get("ComparisonOperator")
            actual_evaluation_periods = alarm.get("EvaluationPeriods")
            actual_treat_missing_data = alarm.get("TreatMissingData")

            assert actual_namespace == expected_namespace, (
                f"Alarm namespace mismatch for {alarm_name}: "
                f"expected {expected_namespace}, got {actual_namespace}"
            )

            assert actual_metric_name == expected_metric_name, (
                f"Alarm metric name mismatch for {alarm_name}: "
                f"expected {expected_metric_name}, got {actual_metric_name}"
            )

            assert actual_threshold == expected_threshold, (
                f"Alarm threshold mismatch for {alarm_name}: "
                f"expected {expected_threshold}, got {actual_threshold}"
            )

            assert actual_period == expected_period, (
                f"Alarm period mismatch for {alarm_name}: "
                f"expected {expected_period}, got {actual_period}"
            )

            assert actual_statistic == "Sum", (
                f"Alarm statistic mismatch for {alarm_name}: " f"expected Sum, got {actual_statistic}"
            )

            assert actual_comparison == "GreaterThanOrEqualToThreshold", (
                f"Alarm comparison operator mismatch for {alarm_name}: "
                f"expected GreaterThanOrEqualToThreshold, got {actual_comparison}"
            )

            assert actual_evaluation_periods == 1, (
                f"Alarm evaluation periods mismatch for {alarm_name}: "
                f"expected 1, got {actual_evaluation_periods}"
            )

            assert actual_treat_missing_data == "notBreaching", (
                f"Alarm treat missing data mismatch for {alarm_name}: "
                f"expected notBreaching, got {actual_treat_missing_data}"
            )

            print(f"✓ Alarm configured correctly: {alarm_name}")
            print(f"  Threshold: {actual_threshold} errors")
            print(f"  Period: {actual_period} seconds")
            print(f"  Statistic: {actual_statistic}")
            print(f"  Comparison: {actual_comparison}")

        except ClientError as e:
            pytest.fail(f"Failed to describe alarm {alarm_name}: {e}")


def test_alarms_have_sns_notification_actions(cloudwatch_client, sns_client, qa_environment):
    """
    Test that CloudWatch Alarms have SNS notification actions configured.

    Validates: Requirement 12.5 - Alarms trigger SNS notifications
    """
    project_name = qa_environment["project_name"]
    environment = qa_environment["environment"]
    lambda_functions = qa_environment["lambda_functions"]

    for function_name in lambda_functions:
        alarm_name = f"{project_name}-{function_name}-access-denied-{environment}"

        try:
            response = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])

            alarms = response.get("MetricAlarms", [])
            assert len(alarms) > 0, f"Alarm not found: {alarm_name}"

            alarm = alarms[0]

            # Verify alarm actions exist
            alarm_actions = alarm.get("AlarmActions", [])
            assert len(alarm_actions) > 0, (
                f"No alarm actions configured for {alarm_name}. " f"SNS notifications will not be sent."
            )

            # Verify alarm actions are SNS topics
            for action_arn in alarm_actions:
                assert action_arn.startswith("arn:aws:sns:"), (
                    f"Alarm action is not an SNS topic ARN: {action_arn}. "
                    f"Expected format: arn:aws:sns:region:account:topic-name"
                )

                # Verify SNS topic exists
                try:
                    sns_client.get_topic_attributes(TopicArn=action_arn)
                    print(f"✓ Alarm {alarm_name} has valid SNS action: {action_arn}")
                except ClientError as e:
                    if e.response["Error"]["Code"] == "NotFound":
                        pytest.fail(
                            f"SNS topic not found: {action_arn}. " f"Alarm notifications will fail to send."
                        )
                    else:
                        raise

        except ClientError as e:
            pytest.fail(f"Failed to describe alarm {alarm_name}: {e}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
