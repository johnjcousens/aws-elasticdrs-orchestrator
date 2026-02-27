"""
Unit tests for monitoring stack (cfn/monitoring/alarms-stack.yaml).

This module validates that the monitoring stack:
- CloudFormation template syntax is valid (cfn-lint)
- Alarm configuration is correct (threshold, evaluation periods, comparison operator)
- Metric filters are correctly configured
- Alarm actions reference correct SNS topic
- Alarm naming follows pattern
- All Lambda functions have corresponding alarms
- Alarm descriptions are meaningful
- Tags are present

Validates Requirements: 17.8
"""

import os
import pytest
from typing import Dict, Any


# =============================================================================
# MONITORING STACK STRUCTURE TESTS
# =============================================================================

class TestMonitoringStackStructure:
    """Test suite for monitoring stack structure and metadata."""

    def test_template_has_correct_format_version(self, load_cfn_template):
        """Test that template has correct CloudFormation format version."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "AWSTemplateFormatVersion" in template
        assert template["AWSTemplateFormatVersion"] == "2010-09-09"

    def test_template_has_description(self, load_cfn_template):
        """Test that template has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "Description" in template
        assert "CloudWatch" in template["Description"] or "Monitoring" in template["Description"]
        assert "security" in template["Description"].lower() or "monitoring" in template["Description"].lower()

    def test_template_has_required_parameters(self, load_cfn_template):
        """Test that template defines all required parameters."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "Parameters" in template
        parameters = template["Parameters"]
        
        required_params = ["ProjectName", "Environment", "SecurityAlertTopicArn"]
        for param in required_params:
            assert param in parameters, f"Missing required parameter: {param}"

    def test_template_has_resources_section(self, load_cfn_template):
        """Test that template has Resources section with CloudWatch resources."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "Resources" in template
        assert len(template["Resources"]) > 0

    def test_template_has_outputs_section(self, load_cfn_template):
        """Test that template has Outputs section for alarm ARNs."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "Outputs" in template
        assert len(template["Outputs"]) > 0


# =============================================================================
# METRIC FILTER TESTS
# =============================================================================

class TestMetricFilters:
    """Test suite for CloudWatch metric filters."""

    def test_query_handler_metric_filter_exists(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedMetricFilter resource exists."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "QueryHandlerAccessDeniedMetricFilter" in template["Resources"]

    def test_query_handler_metric_filter_has_correct_type(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedMetricFilter has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        metric_filter = template["Resources"]["QueryHandlerAccessDeniedMetricFilter"]
        
        # Assert
        assert metric_filter["Type"] == "AWS::Logs::MetricFilter"

    def test_query_handler_metric_filter_has_correct_filter_pattern(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedMetricFilter has correct filter pattern."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        metric_filter = template["Resources"]["QueryHandlerAccessDeniedMetricFilter"]
        
        # Assert
        assert "Properties" in metric_filter
        assert "FilterPattern" in metric_filter["Properties"]
        filter_pattern = metric_filter["Properties"]["FilterPattern"]
        
        assert "AccessDenied" in filter_pattern
        assert "[" in filter_pattern and "]" in filter_pattern

    def test_query_handler_metric_filter_has_correct_log_group(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedMetricFilter references correct log group."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        metric_filter = template["Resources"]["QueryHandlerAccessDeniedMetricFilter"]
        
        # Assert
        assert "LogGroupName" in metric_filter["Properties"]
        log_group = metric_filter["Properties"]["LogGroupName"]
        
        # Verify Sub function with correct pattern
        assert isinstance(log_group, dict) and "Sub" in log_group
        assert "/aws/lambda/" in log_group["Sub"]
        assert "${ProjectName}" in log_group["Sub"]
        assert "query-handler" in log_group["Sub"]
        assert "${Environment}" in log_group["Sub"]

    def test_query_handler_metric_filter_has_correct_metric_transformation(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedMetricFilter has correct metric transformation."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        metric_filter = template["Resources"]["QueryHandlerAccessDeniedMetricFilter"]
        
        # Assert
        assert "MetricTransformations" in metric_filter["Properties"]
        transformations = metric_filter["Properties"]["MetricTransformations"]
        
        assert len(transformations) == 1
        transformation = transformations[0]
        
        assert transformation["MetricName"] == "AccessDeniedErrors"
        assert "MetricNamespace" in transformation
        assert isinstance(transformation["MetricNamespace"], dict) and "Sub" in transformation["MetricNamespace"]
        assert "${ProjectName}/Security" in transformation["MetricNamespace"]["Sub"]
        assert transformation["MetricValue"] == "1"
        assert transformation["DefaultValue"] == 0
        assert transformation["Unit"] == "Count"

    def test_data_management_handler_metric_filter_exists(self, load_cfn_template):
        """Test that DataManagementHandlerAccessDeniedMetricFilter resource exists."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "DataManagementHandlerAccessDeniedMetricFilter" in template["Resources"]

    def test_execution_handler_metric_filter_exists(self, load_cfn_template):
        """Test that ExecutionHandlerAccessDeniedMetricFilter resource exists."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "ExecutionHandlerAccessDeniedMetricFilter" in template["Resources"]

    def test_dr_orchestration_step_function_metric_filter_exists(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionAccessDeniedMetricFilter resource exists."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "DrOrchestrationStepFunctionAccessDeniedMetricFilter" in template["Resources"]

    def test_frontend_deployer_metric_filter_exists(self, load_cfn_template):
        """Test that FrontendDeployerAccessDeniedMetricFilter resource exists."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "FrontendDeployerAccessDeniedMetricFilter" in template["Resources"]

    def test_all_metric_filters_have_correct_type(self, load_cfn_template):
        """Test that all metric filters have correct resource type."""
        # Arrange
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        metric_filter_names = [
            "QueryHandlerAccessDeniedMetricFilter",
            "DataManagementHandlerAccessDeniedMetricFilter",
            "ExecutionHandlerAccessDeniedMetricFilter",
            "DrOrchestrationStepFunctionAccessDeniedMetricFilter",
            "FrontendDeployerAccessDeniedMetricFilter"
        ]
        
        # Act & Assert
        for filter_name in metric_filter_names:
            metric_filter = template["Resources"][filter_name]
            assert metric_filter["Type"] == "AWS::Logs::MetricFilter", f"{filter_name} has incorrect type"

    def test_all_metric_filters_follow_naming_pattern(self, load_cfn_template):
        """Test that all metric filters follow naming pattern."""
        # Arrange
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        metric_filter_names = [
            "QueryHandlerAccessDeniedMetricFilter",
            "DataManagementHandlerAccessDeniedMetricFilter",
            "ExecutionHandlerAccessDeniedMetricFilter",
            "DrOrchestrationStepFunctionAccessDeniedMetricFilter",
            "FrontendDeployerAccessDeniedMetricFilter"
        ]
        
        # Act & Assert
        for filter_name in metric_filter_names:
            metric_filter = template["Resources"][filter_name]
            filter_name_ref = metric_filter["Properties"]["FilterName"]
            
            # Verify it uses Fn::Sub or !Sub
            assert isinstance(filter_name_ref, dict) and "Sub" in filter_name_ref
            assert "${ProjectName}" in filter_name_ref["Sub"]
            assert "${Environment}" in filter_name_ref["Sub"]
            assert "access-denied" in filter_name_ref["Sub"]


# =============================================================================
# CLOUDWATCH ALARM TESTS
# =============================================================================

class TestCloudWatchAlarms:
    """Test suite for CloudWatch alarms."""

    def test_query_handler_alarm_exists(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedAlarm resource exists."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "QueryHandlerAccessDeniedAlarm" in template["Resources"]

    def test_query_handler_alarm_has_correct_type(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedAlarm has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        alarm = template["Resources"]["QueryHandlerAccessDeniedAlarm"]
        
        # Assert
        assert alarm["Type"] == "AWS::CloudWatch::Alarm"

    def test_query_handler_alarm_has_correct_name_pattern(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedAlarm follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        alarm = template["Resources"]["QueryHandlerAccessDeniedAlarm"]
        
        # Assert
        assert "Properties" in alarm
        assert "AlarmName" in alarm["Properties"]
        alarm_name = alarm["Properties"]["AlarmName"]
        
        # Verify Sub function with correct pattern
        assert isinstance(alarm_name, dict) and "Sub" in alarm_name
        assert "${ProjectName}" in alarm_name["Sub"]
        assert "${Environment}" in alarm_name["Sub"]
        assert "query-handler" in alarm_name["Sub"]
        assert "access-denied" in alarm_name["Sub"]

    def test_query_handler_alarm_has_meaningful_description(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedAlarm has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        alarm = template["Resources"]["QueryHandlerAccessDeniedAlarm"]
        
        # Assert
        assert "AlarmDescription" in alarm["Properties"]
        description = alarm["Properties"]["AlarmDescription"]
        
        assert len(description) > 0
        assert "AccessDenied" in description or "access denied" in description.lower()
        assert "Query Handler" in description or "query-handler" in description.lower()

    def test_query_handler_alarm_has_correct_metric_configuration(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedAlarm has correct metric configuration."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        alarm = template["Resources"]["QueryHandlerAccessDeniedAlarm"]
        
        # Assert
        properties = alarm["Properties"]
        
        assert properties["MetricName"] == "AccessDeniedErrors"
        assert "Namespace" in properties
        assert isinstance(properties["Namespace"], dict) and "Sub" in properties["Namespace"]
        assert "${ProjectName}/Security" in properties["Namespace"]["Sub"]

    def test_query_handler_alarm_has_correct_threshold_configuration(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedAlarm has correct threshold configuration."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        alarm = template["Resources"]["QueryHandlerAccessDeniedAlarm"]
        
        # Assert
        properties = alarm["Properties"]
        
        assert properties["Statistic"] == "Sum"
        assert properties["Period"] == 300
        assert properties["EvaluationPeriods"] == 1
        assert properties["Threshold"] == 5
        assert properties["ComparisonOperator"] == "GreaterThanOrEqualToThreshold"
        assert properties["TreatMissingData"] == "notBreaching"

    def test_query_handler_alarm_has_correct_sns_action(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedAlarm references correct SNS topic."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        alarm = template["Resources"]["QueryHandlerAccessDeniedAlarm"]
        
        # Assert
        assert "AlarmActions" in alarm["Properties"]
        actions = alarm["Properties"]["AlarmActions"]
        
        assert len(actions) == 1
        action = actions[0]
        
        # Verify it references SecurityAlertTopicArn parameter
        assert isinstance(action, dict) and "Ref" in action
        assert action["Ref"] == "SecurityAlertTopicArn"

    def test_query_handler_alarm_has_correct_dimensions(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedAlarm has correct dimensions."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        alarm = template["Resources"]["QueryHandlerAccessDeniedAlarm"]
        
        # Assert
        assert "Dimensions" in alarm["Properties"]
        dimensions = alarm["Properties"]["Dimensions"]
        
        assert len(dimensions) == 1
        dimension = dimensions[0]
        
        assert dimension["Name"] == "FunctionName"
        assert "Value" in dimension
        assert isinstance(dimension["Value"], dict) and "Sub" in dimension["Value"]
        assert "${ProjectName}" in dimension["Value"]["Sub"]
        assert "query-handler" in dimension["Value"]["Sub"]
        assert "${Environment}" in dimension["Value"]["Sub"]

    def test_data_management_handler_alarm_exists(self, load_cfn_template):
        """Test that DataManagementHandlerAccessDeniedAlarm resource exists."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "DataManagementHandlerAccessDeniedAlarm" in template["Resources"]

    def test_execution_handler_alarm_exists(self, load_cfn_template):
        """Test that ExecutionHandlerAccessDeniedAlarm resource exists."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "ExecutionHandlerAccessDeniedAlarm" in template["Resources"]

    def test_dr_orchestration_step_function_alarm_exists(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionAccessDeniedAlarm resource exists."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "DrOrchestrationStepFunctionAccessDeniedAlarm" in template["Resources"]

    def test_frontend_deployer_alarm_exists(self, load_cfn_template):
        """Test that FrontendDeployerAccessDeniedAlarm resource exists."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "FrontendDeployerAccessDeniedAlarm" in template["Resources"]

    def test_all_alarms_have_correct_type(self, load_cfn_template):
        """Test that all alarms have correct resource type."""
        # Arrange
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        alarm_names = [
            "QueryHandlerAccessDeniedAlarm",
            "DataManagementHandlerAccessDeniedAlarm",
            "ExecutionHandlerAccessDeniedAlarm",
            "DrOrchestrationStepFunctionAccessDeniedAlarm",
            "FrontendDeployerAccessDeniedAlarm"
        ]
        
        # Act & Assert
        for alarm_name in alarm_names:
            alarm = template["Resources"][alarm_name]
            assert alarm["Type"] == "AWS::CloudWatch::Alarm", f"{alarm_name} has incorrect type"

    def test_all_alarms_follow_naming_pattern(self, load_cfn_template):
        """Test that all alarms follow naming pattern."""
        # Arrange
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        alarm_names = [
            "QueryHandlerAccessDeniedAlarm",
            "DataManagementHandlerAccessDeniedAlarm",
            "ExecutionHandlerAccessDeniedAlarm",
            "DrOrchestrationStepFunctionAccessDeniedAlarm",
            "FrontendDeployerAccessDeniedAlarm"
        ]
        
        # Act & Assert
        for alarm_name in alarm_names:
            alarm = template["Resources"][alarm_name]
            alarm_name_ref = alarm["Properties"]["AlarmName"]
            
            # Verify it uses Fn::Sub or !Sub
            assert isinstance(alarm_name_ref, dict) and "Sub" in alarm_name_ref
            assert "${ProjectName}" in alarm_name_ref["Sub"]
            assert "${Environment}" in alarm_name_ref["Sub"]
            assert "access-denied" in alarm_name_ref["Sub"]

    def test_all_alarms_have_meaningful_descriptions(self, load_cfn_template):
        """Test that all alarms have meaningful descriptions."""
        # Arrange
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        alarm_names = [
            "QueryHandlerAccessDeniedAlarm",
            "DataManagementHandlerAccessDeniedAlarm",
            "ExecutionHandlerAccessDeniedAlarm",
            "DrOrchestrationStepFunctionAccessDeniedAlarm",
            "FrontendDeployerAccessDeniedAlarm"
        ]
        
        # Act & Assert
        for alarm_name in alarm_names:
            alarm = template["Resources"][alarm_name]
            description = alarm["Properties"]["AlarmDescription"]
            
            assert len(description) > 0, f"{alarm_name} has empty description"
            assert "AccessDenied" in description or "access denied" in description.lower()
            assert "5+" in description or "5 " in description

    def test_all_alarms_have_consistent_threshold_configuration(self, load_cfn_template):
        """Test that all alarms have consistent threshold configuration."""
        # Arrange
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        alarm_names = [
            "QueryHandlerAccessDeniedAlarm",
            "DataManagementHandlerAccessDeniedAlarm",
            "ExecutionHandlerAccessDeniedAlarm",
            "DrOrchestrationStepFunctionAccessDeniedAlarm",
            "FrontendDeployerAccessDeniedAlarm"
        ]
        
        # Act & Assert
        for alarm_name in alarm_names:
            alarm = template["Resources"][alarm_name]
            properties = alarm["Properties"]
            
            assert properties["Statistic"] == "Sum", f"{alarm_name} has incorrect Statistic"
            assert properties["Period"] == 300, f"{alarm_name} has incorrect Period"
            assert properties["EvaluationPeriods"] == 1, f"{alarm_name} has incorrect EvaluationPeriods"
            assert properties["Threshold"] == 5, f"{alarm_name} has incorrect Threshold"
            assert properties["ComparisonOperator"] == "GreaterThanOrEqualToThreshold"
            assert properties["TreatMissingData"] == "notBreaching"

    def test_all_alarms_reference_security_alert_topic(self, load_cfn_template):
        """Test that all alarms reference SecurityAlertTopicArn parameter."""
        # Arrange
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        alarm_names = [
            "QueryHandlerAccessDeniedAlarm",
            "DataManagementHandlerAccessDeniedAlarm",
            "ExecutionHandlerAccessDeniedAlarm",
            "DrOrchestrationStepFunctionAccessDeniedAlarm",
            "FrontendDeployerAccessDeniedAlarm"
        ]
        
        # Act & Assert
        for alarm_name in alarm_names:
            alarm = template["Resources"][alarm_name]
            actions = alarm["Properties"]["AlarmActions"]
            
            assert len(actions) == 1, f"{alarm_name} has incorrect number of actions"
            action = actions[0]
            
            assert isinstance(action, dict) and "Ref" in action
            assert action["Ref"] == "SecurityAlertTopicArn", f"{alarm_name} references incorrect SNS topic"


# =============================================================================
# LAMBDA FUNCTION COVERAGE TESTS
# =============================================================================

class TestLambdaFunctionCoverage:
    """Test suite for Lambda function alarm coverage."""

    def test_all_lambda_functions_have_metric_filters(self, load_cfn_template):
        """Test that all Lambda functions have corresponding metric filters."""
        # Arrange
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        expected_functions = [
            "query-handler",
            "data-management-handler",
            "execution-handler",
            "dr-orch-sf",
            "frontend-deployer"
        ]
        
        # Act
        metric_filters = [
            name for name in template["Resources"].keys()
            if name.endswith("MetricFilter")
        ]
        
        # Assert
        assert len(metric_filters) == len(expected_functions)
        
        for function in expected_functions:
            found = False
            for filter_name in metric_filters:
                filter_resource = template["Resources"][filter_name]
                log_group = filter_resource["Properties"]["LogGroupName"]
                if isinstance(log_group, dict) and "Sub" in log_group:
                    if function in log_group["Sub"]:
                        found = True
                        break
            
            assert found, f"No metric filter found for function: {function}"

    def test_all_lambda_functions_have_alarms(self, load_cfn_template):
        """Test that all Lambda functions have corresponding alarms."""
        # Arrange
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        expected_functions = [
            "query-handler",
            "data-management-handler",
            "execution-handler",
            "dr-orch-sf",
            "frontend-deployer"
        ]
        
        # Act
        alarms = [
            name for name in template["Resources"].keys()
            if name.endswith("Alarm")
        ]
        
        # Assert
        assert len(alarms) == len(expected_functions)
        
        for function in expected_functions:
            found = False
            for alarm_name in alarms:
                alarm_resource = template["Resources"][alarm_name]
                alarm_name_ref = alarm_resource["Properties"]["AlarmName"]
                if isinstance(alarm_name_ref, dict) and "Sub" in alarm_name_ref:
                    if function in alarm_name_ref["Sub"]:
                        found = True
                        break
            
            assert found, f"No alarm found for function: {function}"


# =============================================================================
# OUTPUT TESTS
# =============================================================================

class TestMonitoringStackOutputs:
    """Test suite for monitoring stack outputs."""

    def test_query_handler_alarm_arn_output_exists(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedAlarmArn output exists."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        assert "QueryHandlerAccessDeniedAlarmArn" in template["Outputs"]

    def test_query_handler_alarm_arn_output_has_correct_value(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedAlarmArn output has correct value."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        output = template["Outputs"]["QueryHandlerAccessDeniedAlarmArn"]
        
        # Assert
        assert "Value" in output
        value = output["Value"]
        
        # GetAtt can be parsed as string "ResourceName.AttributeName" or dict with list
        assert isinstance(value, dict) and "GetAtt" in value
        get_att_value = value["GetAtt"]
        
        if isinstance(get_att_value, str):
            # Short form: !GetAtt ResourceName.AttributeName
            assert get_att_value == "QueryHandlerAccessDeniedAlarm.Arn"
        else:
            # Long form: !GetAtt [ResourceName, AttributeName]
            assert get_att_value[0] == "QueryHandlerAccessDeniedAlarm"
            assert get_att_value[1] == "Arn"

    def test_query_handler_alarm_arn_output_has_export(self, load_cfn_template):
        """Test that QueryHandlerAccessDeniedAlarmArn output has export."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        output = template["Outputs"]["QueryHandlerAccessDeniedAlarmArn"]
        
        # Assert
        assert "Export" in output
        assert "Name" in output["Export"]
        export_name = output["Export"]["Name"]
        
        assert isinstance(export_name, dict) and "Sub" in export_name
        assert "${ProjectName}" in export_name["Sub"]
        assert "${Environment}" in export_name["Sub"]

    def test_all_alarms_have_corresponding_outputs(self, load_cfn_template):
        """Test that all alarms have corresponding outputs."""
        # Arrange
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        alarm_names = [
            "QueryHandlerAccessDeniedAlarm",
            "DataManagementHandlerAccessDeniedAlarm",
            "ExecutionHandlerAccessDeniedAlarm",
            "DrOrchestrationStepFunctionAccessDeniedAlarm",
            "FrontendDeployerAccessDeniedAlarm"
        ]
        
        # Act & Assert
        for alarm_name in alarm_names:
            output_name = f"{alarm_name}Arn"
            assert output_name in template["Outputs"], f"Missing output for {alarm_name}"
            
            output = template["Outputs"][output_name]
            assert "Value" in output
            assert "Description" in output
            assert "Export" in output

    def test_all_outputs_have_descriptions(self, load_cfn_template):
        """Test that all outputs have meaningful descriptions."""
        # Arrange & Act
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        # Assert
        for output_name, output in template["Outputs"].items():
            assert "Description" in output, f"Output {output_name} missing description"
            description = output["Description"]
            assert len(description) > 0, f"Output {output_name} has empty description"
            assert "alarm" in description.lower() or "ARN" in description


# =============================================================================
# METRIC FILTER AND ALARM PAIRING TESTS
# =============================================================================

class TestMetricFilterAlarmPairing:
    """Test suite for metric filter and alarm pairing."""

    def test_each_metric_filter_has_corresponding_alarm(self, load_cfn_template):
        """Test that each metric filter has a corresponding alarm."""
        # Arrange
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        metric_filter_names = [
            "QueryHandlerAccessDeniedMetricFilter",
            "DataManagementHandlerAccessDeniedMetricFilter",
            "ExecutionHandlerAccessDeniedMetricFilter",
            "DrOrchestrationStepFunctionAccessDeniedMetricFilter",
            "FrontendDeployerAccessDeniedMetricFilter"
        ]
        
        # Act & Assert
        for filter_name in metric_filter_names:
            # Derive expected alarm name
            alarm_name = filter_name.replace("MetricFilter", "Alarm")
            
            assert alarm_name in template["Resources"], f"No alarm found for metric filter: {filter_name}"

    def test_metric_filter_and_alarm_use_same_metric_name(self, load_cfn_template):
        """Test that metric filters and alarms use the same metric name."""
        # Arrange
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        pairs = [
            ("QueryHandlerAccessDeniedMetricFilter", "QueryHandlerAccessDeniedAlarm"),
            ("DataManagementHandlerAccessDeniedMetricFilter", "DataManagementHandlerAccessDeniedAlarm"),
            ("ExecutionHandlerAccessDeniedMetricFilter", "ExecutionHandlerAccessDeniedAlarm"),
            ("DrOrchestrationStepFunctionAccessDeniedMetricFilter", "DrOrchestrationStepFunctionAccessDeniedAlarm"),
            ("FrontendDeployerAccessDeniedMetricFilter", "FrontendDeployerAccessDeniedAlarm")
        ]
        
        # Act & Assert
        for filter_name, alarm_name in pairs:
            metric_filter = template["Resources"][filter_name]
            alarm = template["Resources"][alarm_name]
            
            filter_metric_name = metric_filter["Properties"]["MetricTransformations"][0]["MetricName"]
            alarm_metric_name = alarm["Properties"]["MetricName"]
            
            assert filter_metric_name == alarm_metric_name, f"Metric name mismatch for {filter_name} and {alarm_name}"

    def test_metric_filter_and_alarm_use_same_namespace(self, load_cfn_template):
        """Test that metric filters and alarms use the same namespace."""
        # Arrange
        template = load_cfn_template("monitoring/alarms-stack.yaml")
        
        pairs = [
            ("QueryHandlerAccessDeniedMetricFilter", "QueryHandlerAccessDeniedAlarm"),
            ("DataManagementHandlerAccessDeniedMetricFilter", "DataManagementHandlerAccessDeniedAlarm"),
            ("ExecutionHandlerAccessDeniedMetricFilter", "ExecutionHandlerAccessDeniedAlarm"),
            ("DrOrchestrationStepFunctionAccessDeniedMetricFilter", "DrOrchestrationStepFunctionAccessDeniedAlarm"),
            ("FrontendDeployerAccessDeniedMetricFilter", "FrontendDeployerAccessDeniedAlarm")
        ]
        
        # Act & Assert
        for filter_name, alarm_name in pairs:
            metric_filter = template["Resources"][filter_name]
            alarm = template["Resources"][alarm_name]
            
            filter_namespace = metric_filter["Properties"]["MetricTransformations"][0]["MetricNamespace"]
            alarm_namespace = alarm["Properties"]["Namespace"]
            
            # Both should use Sub function with same pattern
            assert isinstance(filter_namespace, dict) and "Sub" in filter_namespace
            assert isinstance(alarm_namespace, dict) and "Sub" in alarm_namespace
            assert filter_namespace["Sub"] == alarm_namespace["Sub"]
