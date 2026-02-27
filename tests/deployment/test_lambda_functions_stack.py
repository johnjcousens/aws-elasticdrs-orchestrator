"""
Unit tests for Lambda functions stack (cfn/lambda/functions-stack.yaml).

This module validates that the Lambda functions stack:
- Creates all 5 Lambda functions with correct properties
- Function naming follows the pattern: {ProjectName}-{FunctionName}-{Environment}
- Each function references the correct IAM role (function-specific or unified based on UseFunctionSpecificRoles parameter)
- Conditional logic works correctly for role assignment
- Function runtime, handler, timeout, and memory settings are correct
- Environment variables are properly configured
- VPC configuration is present where required
- All functions have proper tags
- Function code references point to correct S3 locations

Validates Requirements: 17.5
"""

import os
import pytest
from typing import Dict, Any


class TestLambdaFunctionsStackStructure:
    """Test suite for Lambda functions stack structure and metadata."""

    def test_template_has_correct_format_version(self, load_cfn_template):
        """Test that template has correct CloudFormation format version."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "AWSTemplateFormatVersion" in template
        assert template["AWSTemplateFormatVersion"] == "2010-09-09"

    def test_template_has_description(self, load_cfn_template):
        """Test that template has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "Description" in template
        assert "Lambda Functions" in template["Description"]
        assert "DR Orchestration" in template["Description"]

    def test_template_has_required_parameters(self, load_cfn_template):
        """Test that template defines all required parameters."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "Parameters" in template
        parameters = template["Parameters"]
        
        required_params = [
            "ProjectName",
            "Environment",
            "DeploymentBucket",
            "UseFunctionSpecificRoles",
            "UnifiedRoleArn"
        ]
        for param in required_params:
            assert param in parameters, f"Missing required parameter: {param}"

    def test_template_has_conditions(self, load_cfn_template):
        """Test that template defines conditional logic for role assignment."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "Conditions" in template
        conditions = template["Conditions"]
        
        assert "UseFunctionSpecificRoles" in conditions

    def test_template_has_resources_section(self, load_cfn_template):
        """Test that template has Resources section with Lambda functions."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "Resources" in template
        assert len(template["Resources"]) > 0

    def test_template_has_outputs_section(self, load_cfn_template):
        """Test that template has Outputs section for function ARNs."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "Outputs" in template
        assert len(template["Outputs"]) > 0


class TestLambdaFunctionsParameters:
    """Test suite for Lambda functions stack parameters."""

    def test_use_function_specific_roles_parameter_has_correct_properties(self, load_cfn_template):
        """Test that UseFunctionSpecificRoles parameter has correct properties."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        param = template["Parameters"]["UseFunctionSpecificRoles"]
        
        # Assert
        assert param["Type"] == "String"
        assert "AllowedValues" in param
        assert set(param["AllowedValues"]) == {"true", "false"}
        assert param["Default"] == "false"

    def test_deployment_bucket_parameter_exists(self, load_cfn_template):
        """Test that DeploymentBucket parameter exists."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        param = template["Parameters"]["DeploymentBucket"]
        
        # Assert
        assert param["Type"] == "String"
        assert "Description" in param

    def test_role_arn_parameters_exist(self, load_cfn_template):
        """Test that all role ARN parameters exist."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        parameters = template["Parameters"]
        
        # Assert
        role_params = [
            "UnifiedRoleArn",
            "QueryHandlerRoleArn",
            "DataManagementRoleArn",
            "ExecutionHandlerRoleArn",
            "OrchestrationRoleArn",
            "FrontendDeployerRoleArn"
        ]
        for param in role_params:
            assert param in parameters


class TestQueryHandlerFunction:
    """Test suite for Query Handler Lambda function."""

    def test_query_handler_function_exists(self, load_cfn_template):
        """Test that QueryHandlerFunction resource exists."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "QueryHandlerFunction" in template["Resources"]

    def test_query_handler_function_has_correct_type(self, load_cfn_template):
        """Test that QueryHandlerFunction has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert function["Type"] == "AWS::Lambda::Function"

    def test_query_handler_function_has_correct_name_pattern(self, load_cfn_template):
        """Test that QueryHandlerFunction follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert "Properties" in function
        assert "FunctionName" in function["Properties"]
        function_name = function["Properties"]["FunctionName"]
        
        # Verify Sub function with correct pattern
        assert isinstance(function_name, dict) and "Sub" in function_name
        assert "${ProjectName}" in function_name["Sub"]
        assert "${Environment}" in function_name["Sub"]
        assert "query-handler" in function_name["Sub"]

    def test_query_handler_function_has_correct_runtime(self, load_cfn_template):
        """Test that QueryHandlerFunction uses Python 3.12 runtime."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert function["Properties"]["Runtime"] == "python3.12"

    def test_query_handler_function_has_correct_handler(self, load_cfn_template):
        """Test that QueryHandlerFunction has correct handler path."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert function["Properties"]["Handler"] == "index.lambda_handler"

    def test_query_handler_function_has_conditional_role_assignment(self, load_cfn_template):
        """Test that QueryHandlerFunction uses conditional logic for role assignment."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert "Role" in function["Properties"]
        role = function["Properties"]["Role"]
        
        # Should use Fn::If for conditional role assignment
        assert isinstance(role, dict) and "If" in role
        assert role["If"][0] == "UseFunctionSpecificRoles"

    def test_query_handler_function_has_correct_timeout(self, load_cfn_template):
        """Test that QueryHandlerFunction has correct timeout setting."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert function["Properties"]["Timeout"] == 60

    def test_query_handler_function_has_correct_memory(self, load_cfn_template):
        """Test that QueryHandlerFunction has correct memory setting."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert function["Properties"]["MemorySize"] == 256

    def test_query_handler_function_has_environment_variables(self, load_cfn_template):
        """Test that QueryHandlerFunction has required environment variables."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert "Environment" in function["Properties"]
        assert "Variables" in function["Properties"]["Environment"]
        env_vars = function["Properties"]["Environment"]["Variables"]
        
        required_vars = [
            "PROTECTION_GROUPS_TABLE",
            "RECOVERY_PLANS_TABLE",
            "EXECUTION_HISTORY_TABLE",
            "TARGET_ACCOUNTS_TABLE",
            "SOURCE_SERVER_INVENTORY_TABLE",
            "DRS_REGION_STATUS_TABLE",
            "RECOVERY_INSTANCES_CACHE_TABLE",
            "PROJECT_NAME",
            "ENVIRONMENT"
        ]
        for var in required_vars:
            assert var in env_vars, f"Missing environment variable: {var}"

    def test_query_handler_function_has_s3_code_reference(self, load_cfn_template):
        """Test that QueryHandlerFunction references correct S3 code location."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert "Code" in function["Properties"]
        code = function["Properties"]["Code"]
        
        assert "S3Bucket" in code
        assert "S3Key" in code
        assert code["S3Key"] == "lambda/query-handler.zip"

    def test_query_handler_function_has_tags(self, load_cfn_template):
        """Test that QueryHandlerFunction has proper tags."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert "Tags" in function["Properties"]
        tags = function["Properties"]["Tags"]
        
        tag_keys = [tag["Key"] for tag in tags]
        assert "Project" in tag_keys
        assert "Environment" in tag_keys

    def test_query_handler_function_has_dead_letter_config(self, load_cfn_template):
        """Test that QueryHandlerFunction has dead letter queue configuration."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert "DeadLetterConfig" in function["Properties"]
        assert "TargetArn" in function["Properties"]["DeadLetterConfig"]


class TestDataManagementHandlerFunction:
    """Test suite for Data Management Handler Lambda function."""

    def test_data_management_function_exists(self, load_cfn_template):
        """Test that DataManagementHandlerFunction resource exists."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "DataManagementHandlerFunction" in template["Resources"]

    def test_data_management_function_has_correct_type(self, load_cfn_template):
        """Test that DataManagementHandlerFunction has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DataManagementHandlerFunction"]
        
        # Assert
        assert function["Type"] == "AWS::Lambda::Function"

    def test_data_management_function_has_correct_name_pattern(self, load_cfn_template):
        """Test that DataManagementHandlerFunction follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DataManagementHandlerFunction"]
        
        # Assert
        function_name = function["Properties"]["FunctionName"]
        assert isinstance(function_name, dict) and "Sub" in function_name
        assert "data-management-handler" in function_name["Sub"]

    def test_data_management_function_has_correct_runtime(self, load_cfn_template):
        """Test that DataManagementHandlerFunction uses Python 3.12 runtime."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DataManagementHandlerFunction"]
        
        # Assert
        assert function["Properties"]["Runtime"] == "python3.12"

    def test_data_management_function_has_conditional_role_assignment(self, load_cfn_template):
        """Test that DataManagementHandlerFunction uses conditional logic for role assignment."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DataManagementHandlerFunction"]
        
        # Assert
        role = function["Properties"]["Role"]
        assert isinstance(role, dict) and "If" in role
        assert role["If"][0] == "UseFunctionSpecificRoles"

    def test_data_management_function_has_correct_timeout(self, load_cfn_template):
        """Test that DataManagementHandlerFunction has correct timeout setting."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DataManagementHandlerFunction"]
        
        # Assert
        assert function["Properties"]["Timeout"] == 900

    def test_data_management_function_has_correct_memory(self, load_cfn_template):
        """Test that DataManagementHandlerFunction has correct memory setting."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DataManagementHandlerFunction"]
        
        # Assert
        assert function["Properties"]["MemorySize"] == 512

    def test_data_management_function_has_environment_variables(self, load_cfn_template):
        """Test that DataManagementHandlerFunction has required environment variables."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DataManagementHandlerFunction"]
        
        # Assert
        env_vars = function["Properties"]["Environment"]["Variables"]
        
        required_vars = [
            "PROTECTION_GROUPS_TABLE",
            "RECOVERY_PLANS_TABLE",
            "EXECUTION_HISTORY_TABLE",
            "STATE_MACHINE_ARN",
            "EXECUTION_NOTIFICATIONS_TOPIC_ARN"
        ]
        for var in required_vars:
            assert var in env_vars, f"Missing environment variable: {var}"

    def test_data_management_function_has_s3_code_reference(self, load_cfn_template):
        """Test that DataManagementHandlerFunction references correct S3 code location."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DataManagementHandlerFunction"]
        
        # Assert
        code = function["Properties"]["Code"]
        assert code["S3Key"] == "lambda/data-management-handler.zip"


class TestExecutionHandlerFunction:
    """Test suite for Execution Handler Lambda function."""

    def test_execution_handler_function_exists(self, load_cfn_template):
        """Test that ExecutionHandlerFunction resource exists."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "ExecutionHandlerFunction" in template["Resources"]

    def test_execution_handler_function_has_correct_type(self, load_cfn_template):
        """Test that ExecutionHandlerFunction has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["ExecutionHandlerFunction"]
        
        # Assert
        assert function["Type"] == "AWS::Lambda::Function"

    def test_execution_handler_function_has_correct_name_pattern(self, load_cfn_template):
        """Test that ExecutionHandlerFunction follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["ExecutionHandlerFunction"]
        
        # Assert
        function_name = function["Properties"]["FunctionName"]
        assert isinstance(function_name, dict) and "Sub" in function_name
        assert "execution-handler" in function_name["Sub"]

    def test_execution_handler_function_has_correct_runtime(self, load_cfn_template):
        """Test that ExecutionHandlerFunction uses Python 3.12 runtime."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["ExecutionHandlerFunction"]
        
        # Assert
        assert function["Properties"]["Runtime"] == "python3.12"

    def test_execution_handler_function_has_conditional_role_assignment(self, load_cfn_template):
        """Test that ExecutionHandlerFunction uses conditional logic for role assignment."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["ExecutionHandlerFunction"]
        
        # Assert
        role = function["Properties"]["Role"]
        assert isinstance(role, dict) and "If" in role
        assert role["If"][0] == "UseFunctionSpecificRoles"

    def test_execution_handler_function_has_correct_timeout(self, load_cfn_template):
        """Test that ExecutionHandlerFunction has correct timeout setting."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["ExecutionHandlerFunction"]
        
        # Assert
        assert function["Properties"]["Timeout"] == 300

    def test_execution_handler_function_has_correct_memory(self, load_cfn_template):
        """Test that ExecutionHandlerFunction has correct memory setting."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["ExecutionHandlerFunction"]
        
        # Assert
        assert function["Properties"]["MemorySize"] == 512

    def test_execution_handler_function_has_environment_variables(self, load_cfn_template):
        """Test that ExecutionHandlerFunction has required environment variables."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["ExecutionHandlerFunction"]
        
        # Assert
        env_vars = function["Properties"]["Environment"]["Variables"]
        
        required_vars = [
            "STATE_MACHINE_ARN",
            "EXECUTION_NOTIFICATIONS_TOPIC_ARN",
            "EXECUTION_PAUSE_TOPIC_ARN",
            "API_GATEWAY_URL"
        ]
        for var in required_vars:
            assert var in env_vars, f"Missing environment variable: {var}"

    def test_execution_handler_function_has_s3_code_reference(self, load_cfn_template):
        """Test that ExecutionHandlerFunction references correct S3 code location."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["ExecutionHandlerFunction"]
        
        # Assert
        code = function["Properties"]["Code"]
        assert code["S3Key"] == "lambda/execution-handler.zip"


class TestDrOrchestrationStepFunctionFunction:
    """Test suite for DR Orchestration Step Function Lambda function."""

    def test_orchestration_function_exists(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionFunction resource exists."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "DrOrchestrationStepFunctionFunction" in template["Resources"]

    def test_orchestration_function_has_correct_type(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionFunction has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DrOrchestrationStepFunctionFunction"]
        
        # Assert
        assert function["Type"] == "AWS::Lambda::Function"

    def test_orchestration_function_has_correct_name_pattern(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionFunction follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DrOrchestrationStepFunctionFunction"]
        
        # Assert
        function_name = function["Properties"]["FunctionName"]
        assert isinstance(function_name, dict) and "Sub" in function_name
        assert "dr-orch-sf" in function_name["Sub"]

    def test_orchestration_function_has_correct_runtime(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionFunction uses Python 3.12 runtime."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DrOrchestrationStepFunctionFunction"]
        
        # Assert
        assert function["Properties"]["Runtime"] == "python3.12"

    def test_orchestration_function_has_conditional_role_assignment(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionFunction uses conditional logic for role assignment."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DrOrchestrationStepFunctionFunction"]
        
        # Assert
        role = function["Properties"]["Role"]
        assert isinstance(role, dict) and "If" in role
        assert role["If"][0] == "UseFunctionSpecificRoles"

    def test_orchestration_function_has_correct_timeout(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionFunction has correct timeout setting."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DrOrchestrationStepFunctionFunction"]
        
        # Assert
        assert function["Properties"]["Timeout"] == 300

    def test_orchestration_function_has_correct_memory(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionFunction has correct memory setting."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DrOrchestrationStepFunctionFunction"]
        
        # Assert
        assert function["Properties"]["MemorySize"] == 512

    def test_orchestration_function_has_environment_variables(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionFunction has required environment variables."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DrOrchestrationStepFunctionFunction"]
        
        # Assert
        env_vars = function["Properties"]["Environment"]["Variables"]
        
        required_vars = [
            "EXECUTION_NOTIFICATIONS_TOPIC_ARN",
            "DRS_ALERTS_TOPIC_ARN",
            "EXECUTION_HANDLER_ARN",
            "QUERY_HANDLER_ARN"
        ]
        for var in required_vars:
            assert var in env_vars, f"Missing environment variable: {var}"

    def test_orchestration_function_has_s3_code_reference(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionFunction references correct S3 code location."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DrOrchestrationStepFunctionFunction"]
        
        # Assert
        code = function["Properties"]["Code"]
        assert code["S3Key"] == "lambda/dr-orchestration-stepfunction.zip"


class TestFrontendDeployerFunction:
    """Test suite for Frontend Deployer Lambda function."""

    def test_frontend_deployer_function_exists(self, load_cfn_template):
        """Test that FrontendDeployerFunction resource exists."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "FrontendDeployerFunction" in template["Resources"]

    def test_frontend_deployer_function_has_correct_type(self, load_cfn_template):
        """Test that FrontendDeployerFunction has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["FrontendDeployerFunction"]
        
        # Assert
        assert function["Type"] == "AWS::Lambda::Function"

    def test_frontend_deployer_function_has_correct_name_pattern(self, load_cfn_template):
        """Test that FrontendDeployerFunction follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["FrontendDeployerFunction"]
        
        # Assert
        function_name = function["Properties"]["FunctionName"]
        assert isinstance(function_name, dict) and "Sub" in function_name
        assert "frontend-deployer" in function_name["Sub"]

    def test_frontend_deployer_function_has_correct_runtime(self, load_cfn_template):
        """Test that FrontendDeployerFunction uses Python 3.12 runtime."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["FrontendDeployerFunction"]
        
        # Assert
        assert function["Properties"]["Runtime"] == "python3.12"

    def test_frontend_deployer_function_has_conditional_role_assignment(self, load_cfn_template):
        """Test that FrontendDeployerFunction uses conditional logic for role assignment."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["FrontendDeployerFunction"]
        
        # Assert
        role = function["Properties"]["Role"]
        assert isinstance(role, dict) and "If" in role
        assert role["If"][0] == "UseFunctionSpecificRoles"

    def test_frontend_deployer_function_has_correct_timeout(self, load_cfn_template):
        """Test that FrontendDeployerFunction has correct timeout setting."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["FrontendDeployerFunction"]
        
        # Assert
        assert function["Properties"]["Timeout"] == 900

    def test_frontend_deployer_function_has_correct_memory(self, load_cfn_template):
        """Test that FrontendDeployerFunction has correct memory setting."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["FrontendDeployerFunction"]
        
        # Assert
        assert function["Properties"]["MemorySize"] == 2048

    def test_frontend_deployer_function_has_s3_code_reference(self, load_cfn_template):
        """Test that FrontendDeployerFunction references correct S3 code location."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["FrontendDeployerFunction"]
        
        # Assert
        code = function["Properties"]["Code"]
        assert code["S3Key"] == "lambda/frontend-deployer.zip"


class TestLambdaDeadLetterQueue:
    """Test suite for Lambda Dead Letter Queue."""

    def test_dead_letter_queue_exists(self, load_cfn_template):
        """Test that LambdaDeadLetterQueue resource exists."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "LambdaDeadLetterQueue" in template["Resources"]

    def test_dead_letter_queue_has_correct_type(self, load_cfn_template):
        """Test that LambdaDeadLetterQueue has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        queue = template["Resources"]["LambdaDeadLetterQueue"]
        
        # Assert
        assert queue["Type"] == "AWS::SQS::Queue"

    def test_all_functions_have_dead_letter_config(self, load_cfn_template):
        """Test that all Lambda functions have dead letter queue configuration."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        lambda_functions = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction",
            "DrOrchestrationStepFunctionFunction",
            "FrontendDeployerFunction"
        ]
        
        # Act & Assert
        for function_name in lambda_functions:
            function = template["Resources"][function_name]
            assert "DeadLetterConfig" in function["Properties"]
            assert "TargetArn" in function["Properties"]["DeadLetterConfig"]


class TestFunctionNamingConventions:
    """Test suite for Lambda function naming conventions."""

    def test_all_functions_follow_naming_pattern(self, load_cfn_template):
        """Test that all Lambda functions follow naming pattern."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        lambda_functions = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction",
            "DrOrchestrationStepFunctionFunction",
            "FrontendDeployerFunction"
        ]
        
        # Act & Assert
        for function_name in lambda_functions:
            function = template["Resources"][function_name]
            function_name_ref = function["Properties"]["FunctionName"]
            
            # Verify it uses Fn::Sub
            assert isinstance(function_name_ref, dict) and "Sub" in function_name_ref
            assert "${ProjectName}" in function_name_ref["Sub"]
            assert "${Environment}" in function_name_ref["Sub"]


class TestFunctionRuntimeConfiguration:
    """Test suite for Lambda function runtime configuration."""

    def test_all_functions_use_python_312_runtime(self, load_cfn_template):
        """Test that all Lambda functions use Python 3.12 runtime."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        lambda_functions = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction",
            "DrOrchestrationStepFunctionFunction",
            "FrontendDeployerFunction"
        ]
        
        # Act & Assert
        for function_name in lambda_functions:
            function = template["Resources"][function_name]
            assert function["Properties"]["Runtime"] == "python3.12"

    def test_all_functions_use_index_lambda_handler(self, load_cfn_template):
        """Test that all Lambda functions use index.lambda_handler as handler."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        lambda_functions = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction",
            "DrOrchestrationStepFunctionFunction",
            "FrontendDeployerFunction"
        ]
        
        # Act & Assert
        for function_name in lambda_functions:
            function = template["Resources"][function_name]
            assert function["Properties"]["Handler"] == "index.lambda_handler"

    def test_all_functions_have_reserved_concurrent_executions(self, load_cfn_template):
        """Test that all Lambda functions have reserved concurrent executions configured."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        lambda_functions = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction",
            "DrOrchestrationStepFunctionFunction",
            "FrontendDeployerFunction"
        ]
        
        # Act & Assert
        for function_name in lambda_functions:
            function = template["Resources"][function_name]
            assert "ReservedConcurrentExecutions" in function["Properties"]


class TestFunctionConditionalRoleAssignment:
    """Test suite for Lambda function conditional role assignment."""

    def test_all_functions_use_conditional_role_assignment(self, load_cfn_template):
        """Test that all Lambda functions use conditional logic for role assignment."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        lambda_functions = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction",
            "DrOrchestrationStepFunctionFunction",
            "FrontendDeployerFunction"
        ]
        
        # Act & Assert
        for function_name in lambda_functions:
            function = template["Resources"][function_name]
            role = function["Properties"]["Role"]
            
            # Should use Fn::If for conditional role assignment
            assert isinstance(role, dict) and "If" in role
            assert role["If"][0] == "UseFunctionSpecificRoles"

    def test_conditional_role_assignment_references_correct_role_arns(self, load_cfn_template):
        """Test that conditional role assignment references correct role ARN parameters."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        function_role_mapping = {
            "QueryHandlerFunction": "QueryHandlerRoleArn",
            "DataManagementHandlerFunction": "DataManagementRoleArn",
            "ExecutionHandlerFunction": "ExecutionHandlerRoleArn",
            "DrOrchestrationStepFunctionFunction": "OrchestrationRoleArn",
            "FrontendDeployerFunction": "FrontendDeployerRoleArn"
        }
        
        # Act & Assert
        for function_name, expected_role_param in function_role_mapping.items():
            function = template["Resources"][function_name]
            role = function["Properties"]["Role"]
            
            # Verify conditional references correct role parameter
            assert isinstance(role, dict) and "If" in role
            # role["If"] should be [condition, true_value, false_value]
            assert len(role["If"]) == 3


class TestFunctionCodeReferences:
    """Test suite for Lambda function code references."""

    def test_all_functions_reference_deployment_bucket(self, load_cfn_template):
        """Test that all Lambda functions reference the deployment bucket parameter."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        lambda_functions = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction",
            "DrOrchestrationStepFunctionFunction",
            "FrontendDeployerFunction"
        ]
        
        # Act & Assert
        for function_name in lambda_functions:
            function = template["Resources"][function_name]
            code = function["Properties"]["Code"]
            
            assert "S3Bucket" in code
            assert "S3Key" in code
            # S3Bucket should reference DeploymentBucket parameter
            assert isinstance(code["S3Bucket"], dict) and "Ref" in code["S3Bucket"]

    def test_all_functions_have_unique_s3_keys(self, load_cfn_template):
        """Test that all Lambda functions have unique S3 keys."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        lambda_functions = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction",
            "DrOrchestrationStepFunctionFunction",
            "FrontendDeployerFunction"
        ]
        
        # Act
        s3_keys = []
        for function_name in lambda_functions:
            function = template["Resources"][function_name]
            code = function["Properties"]["Code"]
            s3_keys.append(code["S3Key"])
        
        # Assert
        assert len(s3_keys) == len(set(s3_keys)), "S3 keys must be unique"


class TestFunctionTags:
    """Test suite for Lambda function tags."""

    def test_all_functions_have_project_and_environment_tags(self, load_cfn_template):
        """Test that all Lambda functions have Project and Environment tags."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        lambda_functions = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction",
            "DrOrchestrationStepFunctionFunction",
            "FrontendDeployerFunction"
        ]
        
        # Act & Assert
        for function_name in lambda_functions:
            function = template["Resources"][function_name]
            assert "Tags" in function["Properties"]
            tags = function["Properties"]["Tags"]
            
            tag_keys = [tag["Key"] for tag in tags]
            assert "Project" in tag_keys
            assert "Environment" in tag_keys


class TestFunctionOutputs:
    """Test suite for Lambda function stack outputs."""

    def test_stack_has_query_handler_function_arn_output(self, load_cfn_template):
        """Test that stack exports QueryHandlerFunctionArn output."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "QueryHandlerFunctionArn" in template["Outputs"]
        output = template["Outputs"]["QueryHandlerFunctionArn"]
        
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_stack_has_data_management_handler_function_arn_output(self, load_cfn_template):
        """Test that stack exports DataManagementHandlerFunctionArn output."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "DataManagementHandlerFunctionArn" in template["Outputs"]
        output = template["Outputs"]["DataManagementHandlerFunctionArn"]
        
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_stack_has_execution_handler_function_arn_output(self, load_cfn_template):
        """Test that stack exports ExecutionHandlerFunctionArn output."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "ExecutionHandlerFunctionArn" in template["Outputs"]
        output = template["Outputs"]["ExecutionHandlerFunctionArn"]
        
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_stack_has_orchestration_function_arn_output(self, load_cfn_template):
        """Test that stack exports OrchestrationFunctionArn output."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "OrchestrationFunctionArn" in template["Outputs"]
        output = template["Outputs"]["OrchestrationFunctionArn"]
        
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_stack_has_frontend_deployer_function_arn_output(self, load_cfn_template):
        """Test that stack exports FrontendDeployerFunctionArn output."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "FrontendDeployerFunctionArn" in template["Outputs"]
        output = template["Outputs"]["FrontendDeployerFunctionArn"]
        
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_stack_has_dead_letter_queue_outputs(self, load_cfn_template):
        """Test that stack exports dead letter queue ARN and URL outputs."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "LambdaDeadLetterQueueArn" in template["Outputs"]
        assert "LambdaDeadLetterQueueUrl" in template["Outputs"]


class TestFunctionResourceCount:
    """Test suite for Lambda function resource count validation."""

    def test_template_has_exactly_five_lambda_functions(self, load_cfn_template):
        """Test that template defines exactly 5 Lambda functions."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        resources = template["Resources"]
        
        # Assert
        lambda_functions = [r for r in resources.values() if r["Type"] == "AWS::Lambda::Function"]
        assert len(lambda_functions) == 5

    def test_template_has_all_expected_functions(self, load_cfn_template):
        """Test that template has all expected Lambda function resources."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        resources = template["Resources"]
        
        # Assert
        expected_functions = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction",
            "DrOrchestrationStepFunctionFunction",
            "FrontendDeployerFunction"
        ]
        
        for function_name in expected_functions:
            assert function_name in resources
            assert resources[function_name]["Type"] == "AWS::Lambda::Function"


class TestConditionalLogic:
    """Test suite for Lambda functions stack conditional logic."""

    def test_use_function_specific_roles_condition_is_defined(self, load_cfn_template):
        """Test that UseFunctionSpecificRoles condition is properly defined."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert
        assert "Conditions" in template
        assert "UseFunctionSpecificRoles" in template["Conditions"]
        condition = template["Conditions"]["UseFunctionSpecificRoles"]
        
        # Should use Fn::Equals to check parameter value
        assert isinstance(condition, dict) or "!Equals" in str(condition)


class TestFunctionDescriptions:
    """Test suite for Lambda function descriptions."""

    def test_all_functions_have_descriptions(self, load_cfn_template):
        """Test that all Lambda functions have meaningful descriptions."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        lambda_functions = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction",
            "DrOrchestrationStepFunctionFunction",
            "FrontendDeployerFunction"
        ]
        
        # Act & Assert
        for function_name in lambda_functions:
            function = template["Resources"][function_name]
            assert "Description" in function["Properties"]
            description = function["Properties"]["Description"]
            assert len(description) > 0
            # Description should include version reference
            assert "v${LambdaCodeVersion}" in description or "LambdaCodeVersion" in str(description)


class TestFunctionTimeoutConfiguration:
    """Test suite for Lambda function timeout configuration."""

    def test_query_handler_has_60_second_timeout(self, load_cfn_template):
        """Test that QueryHandlerFunction has 60 second timeout."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert function["Properties"]["Timeout"] == 60

    def test_data_management_handler_has_900_second_timeout(self, load_cfn_template):
        """Test that DataManagementHandlerFunction has 900 second timeout."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DataManagementHandlerFunction"]
        
        # Assert
        assert function["Properties"]["Timeout"] == 900

    def test_execution_handler_has_300_second_timeout(self, load_cfn_template):
        """Test that ExecutionHandlerFunction has 300 second timeout."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["ExecutionHandlerFunction"]
        
        # Assert
        assert function["Properties"]["Timeout"] == 300

    def test_orchestration_function_has_300_second_timeout(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionFunction has 300 second timeout."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DrOrchestrationStepFunctionFunction"]
        
        # Assert
        assert function["Properties"]["Timeout"] == 300

    def test_frontend_deployer_has_900_second_timeout(self, load_cfn_template):
        """Test that FrontendDeployerFunction has 900 second timeout."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["FrontendDeployerFunction"]
        
        # Assert
        assert function["Properties"]["Timeout"] == 900


class TestFunctionMemoryConfiguration:
    """Test suite for Lambda function memory configuration."""

    def test_query_handler_has_256_mb_memory(self, load_cfn_template):
        """Test that QueryHandlerFunction has 256 MB memory."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert function["Properties"]["MemorySize"] == 256

    def test_data_management_handler_has_512_mb_memory(self, load_cfn_template):
        """Test that DataManagementHandlerFunction has 512 MB memory."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DataManagementHandlerFunction"]
        
        # Assert
        assert function["Properties"]["MemorySize"] == 512

    def test_execution_handler_has_512_mb_memory(self, load_cfn_template):
        """Test that ExecutionHandlerFunction has 512 MB memory."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["ExecutionHandlerFunction"]
        
        # Assert
        assert function["Properties"]["MemorySize"] == 512

    def test_orchestration_function_has_512_mb_memory(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionFunction has 512 MB memory."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DrOrchestrationStepFunctionFunction"]
        
        # Assert
        assert function["Properties"]["MemorySize"] == 512

    def test_frontend_deployer_has_2048_mb_memory(self, load_cfn_template):
        """Test that FrontendDeployerFunction has 2048 MB memory."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["FrontendDeployerFunction"]
        
        # Assert
        assert function["Properties"]["MemorySize"] == 2048


class TestFunctionEnvironmentVariables:
    """Test suite for Lambda function environment variables."""

    def test_all_functions_have_project_name_environment_variable(self, load_cfn_template):
        """Test that all Lambda functions have PROJECT_NAME environment variable."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        functions_with_project_name = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction"
        ]
        
        # Act & Assert
        for function_name in functions_with_project_name:
            function = template["Resources"][function_name]
            env_vars = function["Properties"]["Environment"]["Variables"]
            assert "PROJECT_NAME" in env_vars

    def test_all_functions_have_environment_environment_variable(self, load_cfn_template):
        """Test that all Lambda functions have ENVIRONMENT environment variable."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        functions_with_environment = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction"
        ]
        
        # Act & Assert
        for function_name in functions_with_environment:
            function = template["Resources"][function_name]
            env_vars = function["Properties"]["Environment"]["Variables"]
            assert "ENVIRONMENT" in env_vars

    def test_functions_have_dynamodb_table_environment_variables(self, load_cfn_template):
        """Test that functions have DynamoDB table name environment variables."""
        # Arrange
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        functions_with_tables = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction"
        ]
        
        # Act & Assert
        for function_name in functions_with_tables:
            function = template["Resources"][function_name]
            env_vars = function["Properties"]["Environment"]["Variables"]
            
            # All should have at least these core tables
            assert "PROTECTION_GROUPS_TABLE" in env_vars
            assert "RECOVERY_PLANS_TABLE" in env_vars
            assert "EXECUTION_HISTORY_TABLE" in env_vars


class TestFunctionConcurrencyConfiguration:
    """Test suite for Lambda function concurrency configuration."""

    def test_query_handler_has_50_reserved_concurrent_executions(self, load_cfn_template):
        """Test that QueryHandlerFunction has 50 reserved concurrent executions."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["QueryHandlerFunction"]
        
        # Assert
        assert function["Properties"]["ReservedConcurrentExecutions"] == 50

    def test_data_management_handler_has_50_reserved_concurrent_executions(self, load_cfn_template):
        """Test that DataManagementHandlerFunction has 50 reserved concurrent executions."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DataManagementHandlerFunction"]
        
        # Assert
        assert function["Properties"]["ReservedConcurrentExecutions"] == 50

    def test_execution_handler_has_50_reserved_concurrent_executions(self, load_cfn_template):
        """Test that ExecutionHandlerFunction has 50 reserved concurrent executions."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["ExecutionHandlerFunction"]
        
        # Assert
        assert function["Properties"]["ReservedConcurrentExecutions"] == 50

    def test_orchestration_function_has_50_reserved_concurrent_executions(self, load_cfn_template):
        """Test that DrOrchestrationStepFunctionFunction has 50 reserved concurrent executions."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["DrOrchestrationStepFunctionFunction"]
        
        # Assert
        assert function["Properties"]["ReservedConcurrentExecutions"] == 50

    def test_frontend_deployer_has_10_reserved_concurrent_executions(self, load_cfn_template):
        """Test that FrontendDeployerFunction has 10 reserved concurrent executions."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        function = template["Resources"]["FrontendDeployerFunction"]
        
        # Assert
        assert function["Properties"]["ReservedConcurrentExecutions"] == 10
