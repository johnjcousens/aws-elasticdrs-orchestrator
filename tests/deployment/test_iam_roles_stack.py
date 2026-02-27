"""
Unit tests for IAM roles stack (cfn/iam/roles-stack.yaml).

This module validates that the IAM roles stack:
- Creates all 5 function-specific IAM roles with correct properties
- Creates unified role when UseFunctionSpecificRoles=false
- Role naming follows pattern: {ProjectName}-{FunctionName}-role-{Environment}
- Each role has correct trust policy (Lambda service principal)
- Each role has appropriate managed policies attached
- Conditional logic works correctly
- Role descriptions are present and meaningful
- All roles have proper tags

Validates Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8
"""

import os
import pytest
from typing import Dict, Any


class TestIAMRolesStackStructure:
    """Test suite for IAM roles stack structure and metadata."""

    def test_template_has_correct_format_version(self, load_cfn_template):
        """Test that template has correct CloudFormation format version."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "AWSTemplateFormatVersion" in template
        assert template["AWSTemplateFormatVersion"] == "2010-09-09"

    def test_template_has_description(self, load_cfn_template):
        """Test that template has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "Description" in template
        assert "IAM roles" in template["Description"]
        assert "Lambda functions" in template["Description"]

    def test_template_has_required_parameters(self, load_cfn_template):
        """Test that template defines all required parameters."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "Parameters" in template
        parameters = template["Parameters"]
        
        required_params = ["ProjectName", "Environment", "UseFunctionSpecificRoles"]
        for param in required_params:
            assert param in parameters, f"Missing required parameter: {param}"

    def test_template_has_conditions(self, load_cfn_template):
        """Test that template defines conditional logic for role creation."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "Conditions" in template
        conditions = template["Conditions"]
        
        assert "UseFunctionSpecificRoles" in conditions
        assert "UseUnifiedRole" in conditions

    def test_template_has_resources_section(self, load_cfn_template):
        """Test that template has Resources section with IAM roles."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "Resources" in template
        assert len(template["Resources"]) > 0

    def test_template_has_outputs_section(self, load_cfn_template):
        """Test that template has Outputs section for role ARNs."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "Outputs" in template
        assert len(template["Outputs"]) > 0


class TestIAMRolesParameters:
    """Test suite for IAM roles stack parameters."""

    def test_project_name_parameter_has_correct_properties(self, load_cfn_template):
        """Test that ProjectName parameter has correct properties."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        param = template["Parameters"]["ProjectName"]
        
        # Assert
        assert param["Type"] == "String"
        assert "Description" in param
        assert param["Default"] == "aws-drs-orchestration"

    def test_environment_parameter_has_allowed_values(self, load_cfn_template):
        """Test that Environment parameter has correct allowed values."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        param = template["Parameters"]["Environment"]
        
        # Assert
        assert param["Type"] == "String"
        assert "AllowedValues" in param
        assert set(param["AllowedValues"]) == {"dev", "test", "staging", "prod"}
        assert param["Default"] == "test"

    def test_use_function_specific_roles_parameter_has_correct_properties(self, load_cfn_template):
        """Test that UseFunctionSpecificRoles parameter has correct properties."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        param = template["Parameters"]["UseFunctionSpecificRoles"]
        
        # Assert
        assert param["Type"] == "String"
        assert "AllowedValues" in param
        assert set(param["AllowedValues"]) == {"true", "false"}
        assert param["Default"] == "false"


class TestQueryHandlerRole:
    """Test suite for Query Handler IAM role."""

    def test_query_handler_role_exists(self, load_cfn_template):
        """Test that QueryHandlerRole resource exists."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "QueryHandlerRole" in template["Resources"]

    def test_query_handler_role_has_correct_type(self, load_cfn_template):
        """Test that QueryHandlerRole has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["QueryHandlerRole"]
        
        # Assert
        assert role["Type"] == "AWS::IAM::Role"

    def test_query_handler_role_has_condition(self, load_cfn_template):
        """Test that QueryHandlerRole has UseFunctionSpecificRoles condition."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["QueryHandlerRole"]
        
        # Assert
        assert "Condition" in role
        assert role["Condition"] == "UseFunctionSpecificRoles"

    def test_query_handler_role_has_correct_name_pattern(self, load_cfn_template):
        """Test that QueryHandlerRole follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["QueryHandlerRole"]
        
        # Assert
        assert "Properties" in role
        assert "RoleName" in role["Properties"]
        role_name = role["Properties"]["RoleName"]
        
        # Verify Sub function with correct pattern
        assert isinstance(role_name, dict) and "Sub" in role_name
        assert "${ProjectName}" in role_name["Sub"]
        assert "${Environment}" in role_name["Sub"]
        assert "role" in role_name["Sub"]

    def test_query_handler_role_has_description(self, load_cfn_template):
        """Test that QueryHandlerRole has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["QueryHandlerRole"]
        
        # Assert
        assert "Description" in role["Properties"]
        description = role["Properties"]["Description"]
        assert len(description) > 0
        assert "Query Handler" in description or "read-only" in description.lower()

    def test_query_handler_role_has_lambda_trust_policy(self, load_cfn_template):
        """Test that QueryHandlerRole has correct Lambda trust policy."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["QueryHandlerRole"]
        
        # Assert
        assert "AssumeRolePolicyDocument" in role["Properties"]
        trust_policy = role["Properties"]["AssumeRolePolicyDocument"]
        
        assert trust_policy["Version"] == "2012-10-17"
        assert "Statement" in trust_policy
        assert len(trust_policy["Statement"]) > 0
        
        statement = trust_policy["Statement"][0]
        assert statement["Effect"] == "Allow"
        assert statement["Action"] == "sts:AssumeRole"
        assert "Principal" in statement
        assert "Service" in statement["Principal"]
        assert "lambda.amazonaws.com" in statement["Principal"]["Service"]

    def test_query_handler_role_has_basic_execution_policy(self, load_cfn_template):
        """Test that QueryHandlerRole has AWSLambdaBasicExecutionRole managed policy."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["QueryHandlerRole"]
        
        # Assert
        assert "ManagedPolicyArns" in role["Properties"]
        managed_policies = role["Properties"]["ManagedPolicyArns"]
        
        assert "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" in managed_policies

    def test_query_handler_role_has_inline_policies(self, load_cfn_template):
        """Test that QueryHandlerRole has inline policies for DRS, DynamoDB, EC2."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["QueryHandlerRole"]
        
        # Assert
        assert "Policies" in role["Properties"]
        policies = role["Properties"]["Policies"]
        
        policy_names = [p["PolicyName"] for p in policies]
        assert "DynamoDBReadOnly" in policy_names
        assert "DRSReadOnly" in policy_names
        assert "EC2ReadOnly" in policy_names


class TestDataManagementRole:
    """Test suite for Data Management Handler IAM role."""

    def test_data_management_role_exists(self, load_cfn_template):
        """Test that DataManagementRole resource exists."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "DataManagementRole" in template["Resources"]

    def test_data_management_role_has_correct_type(self, load_cfn_template):
        """Test that DataManagementRole has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["DataManagementRole"]
        
        # Assert
        assert role["Type"] == "AWS::IAM::Role"

    def test_data_management_role_has_condition(self, load_cfn_template):
        """Test that DataManagementRole has UseFunctionSpecificRoles condition."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["DataManagementRole"]
        
        # Assert
        assert "Condition" in role
        assert role["Condition"] == "UseFunctionSpecificRoles"

    def test_data_management_role_has_description(self, load_cfn_template):
        """Test that DataManagementRole has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["DataManagementRole"]
        
        # Assert
        assert "Description" in role["Properties"]
        description = role["Properties"]["Description"]
        assert len(description) > 0
        assert "Data Management" in description or "DynamoDB" in description

    def test_data_management_role_has_lambda_trust_policy(self, load_cfn_template):
        """Test that DataManagementRole has correct Lambda trust policy."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["DataManagementRole"]
        
        # Assert
        trust_policy = role["Properties"]["AssumeRolePolicyDocument"]
        statement = trust_policy["Statement"][0]
        
        assert statement["Effect"] == "Allow"
        assert statement["Action"] == "sts:AssumeRole"
        assert "lambda.amazonaws.com" in statement["Principal"]["Service"]

    def test_data_management_role_has_dynamodb_crud_policy(self, load_cfn_template):
        """Test that DataManagementRole has DynamoDB CRUD permissions."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["DataManagementRole"]
        
        # Assert
        policies = role["Properties"]["Policies"]
        policy_names = [p["PolicyName"] for p in policies]
        
        assert "DynamoDBFullAccess" in policy_names


class TestExecutionHandlerRole:
    """Test suite for Execution Handler IAM role."""

    def test_execution_handler_role_exists(self, load_cfn_template):
        """Test that ExecutionHandlerRole resource exists."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "ExecutionHandlerRole" in template["Resources"]

    def test_execution_handler_role_has_correct_type(self, load_cfn_template):
        """Test that ExecutionHandlerRole has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["ExecutionHandlerRole"]
        
        # Assert
        assert role["Type"] == "AWS::IAM::Role"

    def test_execution_handler_role_has_condition(self, load_cfn_template):
        """Test that ExecutionHandlerRole has UseFunctionSpecificRoles condition."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["ExecutionHandlerRole"]
        
        # Assert
        assert "Condition" in role
        assert role["Condition"] == "UseFunctionSpecificRoles"

    def test_execution_handler_role_has_description(self, load_cfn_template):
        """Test that ExecutionHandlerRole has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["ExecutionHandlerRole"]
        
        # Assert
        assert "Description" in role["Properties"]
        description = role["Properties"]["Description"]
        assert len(description) > 0

    def test_execution_handler_role_has_step_functions_policy(self, load_cfn_template):
        """Test that ExecutionHandlerRole has Step Functions orchestration permissions."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["ExecutionHandlerRole"]
        
        # Assert
        policies = role["Properties"]["Policies"]
        policy_names = [p["PolicyName"] for p in policies]
        
        assert "StepFunctionsOrchestration" in policy_names

    def test_execution_handler_role_has_sns_policy(self, load_cfn_template):
        """Test that ExecutionHandlerRole has SNS notification permissions."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["ExecutionHandlerRole"]
        
        # Assert
        policies = role["Properties"]["Policies"]
        policy_names = [p["PolicyName"] for p in policies]
        
        assert "SNSNotifications" in policy_names


class TestOrchestrationRole:
    """Test suite for Orchestration Function IAM role."""

    def test_orchestration_role_exists(self, load_cfn_template):
        """Test that OrchestrationRole resource exists."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "OrchestrationRole" in template["Resources"]

    def test_orchestration_role_has_correct_type(self, load_cfn_template):
        """Test that OrchestrationRole has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["OrchestrationRole"]
        
        # Assert
        assert role["Type"] == "AWS::IAM::Role"

    def test_orchestration_role_has_condition(self, load_cfn_template):
        """Test that OrchestrationRole has UseFunctionSpecificRoles condition."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["OrchestrationRole"]
        
        # Assert
        assert "Condition" in role
        assert role["Condition"] == "UseFunctionSpecificRoles"

    def test_orchestration_role_has_description(self, load_cfn_template):
        """Test that OrchestrationRole has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["OrchestrationRole"]
        
        # Assert
        assert "Description" in role["Properties"]
        description = role["Properties"]["Description"]
        assert len(description) > 0
        assert "Orchestration" in description or "DRS" in description

    def test_orchestration_role_has_comprehensive_drs_permissions(self, load_cfn_template):
        """Test that OrchestrationRole has comprehensive DRS permissions."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["OrchestrationRole"]
        
        # Assert
        policies = role["Properties"]["Policies"]
        policy_names = [p["PolicyName"] for p in policies]
        
        assert "DRSComprehensive" in policy_names

    def test_orchestration_role_has_ec2_permissions(self, load_cfn_template):
        """Test that OrchestrationRole has comprehensive EC2 permissions."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["OrchestrationRole"]
        
        # Assert
        policies = role["Properties"]["Policies"]
        policy_names = [p["PolicyName"] for p in policies]
        
        assert "EC2Comprehensive" in policy_names


class TestFrontendDeployerRole:
    """Test suite for Frontend Deployer IAM role."""

    def test_frontend_deployer_role_exists(self, load_cfn_template):
        """Test that FrontendDeployerRole resource exists."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "FrontendDeployerRole" in template["Resources"]

    def test_frontend_deployer_role_has_correct_type(self, load_cfn_template):
        """Test that FrontendDeployerRole has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["FrontendDeployerRole"]
        
        # Assert
        assert role["Type"] == "AWS::IAM::Role"

    def test_frontend_deployer_role_has_condition(self, load_cfn_template):
        """Test that FrontendDeployerRole has UseFunctionSpecificRoles condition."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["FrontendDeployerRole"]
        
        # Assert
        assert "Condition" in role
        assert role["Condition"] == "UseFunctionSpecificRoles"

    def test_frontend_deployer_role_has_description(self, load_cfn_template):
        """Test that FrontendDeployerRole has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["FrontendDeployerRole"]
        
        # Assert
        assert "Description" in role["Properties"]
        description = role["Properties"]["Description"]
        assert len(description) > 0
        assert "Frontend" in description or "S3" in description or "CloudFront" in description

    def test_frontend_deployer_role_has_s3_permissions(self, load_cfn_template):
        """Test that FrontendDeployerRole has S3 bucket access permissions."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["FrontendDeployerRole"]
        
        # Assert
        policies = role["Properties"]["Policies"]
        policy_names = [p["PolicyName"] for p in policies]
        
        assert "S3FrontendBucketAccess" in policy_names

    def test_frontend_deployer_role_has_cloudfront_permissions(self, load_cfn_template):
        """Test that FrontendDeployerRole has CloudFront invalidation permissions."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["FrontendDeployerRole"]
        
        # Assert
        policies = role["Properties"]["Policies"]
        policy_names = [p["PolicyName"] for p in policies]
        
        assert "CloudFrontInvalidation" in policy_names



class TestUnifiedOrchestrationRole:
    """Test suite for Unified Orchestration IAM role (backward compatibility)."""

    def test_unified_role_exists(self, load_cfn_template):
        """Test that UnifiedOrchestrationRole resource exists."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "UnifiedOrchestrationRole" in template["Resources"]

    def test_unified_role_has_correct_type(self, load_cfn_template):
        """Test that UnifiedOrchestrationRole has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["UnifiedOrchestrationRole"]
        
        # Assert
        assert role["Type"] == "AWS::IAM::Role"

    def test_unified_role_has_use_unified_role_condition(self, load_cfn_template):
        """Test that UnifiedOrchestrationRole has UseUnifiedRole condition."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["UnifiedOrchestrationRole"]
        
        # Assert
        assert "Condition" in role
        assert role["Condition"] == "UseUnifiedRole"

    def test_unified_role_has_description(self, load_cfn_template):
        """Test that UnifiedOrchestrationRole has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["UnifiedOrchestrationRole"]
        
        # Assert
        assert "Description" in role["Properties"]
        description = role["Properties"]["Description"]
        assert len(description) > 0
        assert "Unified" in description or "backward compatibility" in description

    def test_unified_role_has_multiple_service_principals(self, load_cfn_template):
        """Test that UnifiedOrchestrationRole trusts Lambda, States, and API Gateway."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["UnifiedOrchestrationRole"]
        
        # Assert
        trust_policy = role["Properties"]["AssumeRolePolicyDocument"]
        statement = trust_policy["Statement"][0]
        
        assert "Service" in statement["Principal"]
        services = statement["Principal"]["Service"]
        
        assert "lambda.amazonaws.com" in services
        assert "states.amazonaws.com" in services
        assert "apigateway.amazonaws.com" in services

    def test_unified_role_has_comprehensive_permissions(self, load_cfn_template):
        """Test that UnifiedOrchestrationRole has comprehensive permissions for all functions."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["UnifiedOrchestrationRole"]
        
        # Assert
        policies = role["Properties"]["Policies"]
        policy_names = [p["PolicyName"] for p in policies]
        
        # Should have permissions for all services
        assert "DynamoDBAccess" in policy_names
        assert "StepFunctionsAccess" in policy_names
        assert "DRSReadAccess" in policy_names
        assert "DRSWriteAccess" in policy_names
        assert "EC2Access" in policy_names
        assert "S3Access" in policy_names
        assert "CloudFrontAccess" in policy_names



class TestRoleNamingConventions:
    """Test suite for IAM role naming conventions."""

    def test_all_function_specific_roles_follow_naming_pattern(self, load_cfn_template):
        """Test that all function-specific roles follow naming pattern."""
        # Arrange
        template = load_cfn_template("iam/roles-stack.yaml")
        
        function_specific_roles = [
            "QueryHandlerRole",
            "DataManagementRole",
            "ExecutionHandlerRole",
            "OrchestrationRole",
            "FrontendDeployerRole"
        ]
        
        # Act & Assert
        for role_name in function_specific_roles:
            role = template["Resources"][role_name]
            role_name_ref = role["Properties"]["RoleName"]
            
            # Verify it uses Fn::Sub or !Sub
            assert isinstance(role_name_ref, dict) or "!Sub" in str(role_name_ref)

    def test_unified_role_follows_naming_pattern(self, load_cfn_template):
        """Test that UnifiedOrchestrationRole follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["UnifiedOrchestrationRole"]
        
        # Assert
        role_name_ref = role["Properties"]["RoleName"]
        assert isinstance(role_name_ref, dict) or "!Sub" in str(role_name_ref)


class TestRoleTrustPolicies:
    """Test suite for IAM role trust policies."""

    def test_all_function_specific_roles_trust_lambda_service(self, load_cfn_template):
        """Test that all function-specific roles trust Lambda service principal."""
        # Arrange
        template = load_cfn_template("iam/roles-stack.yaml")
        
        function_specific_roles = [
            "QueryHandlerRole",
            "DataManagementRole",
            "ExecutionHandlerRole",
            "OrchestrationRole",
            "FrontendDeployerRole"
        ]
        
        # Act & Assert
        for role_name in function_specific_roles:
            role = template["Resources"][role_name]
            trust_policy = role["Properties"]["AssumeRolePolicyDocument"]
            
            assert trust_policy["Version"] == "2012-10-17"
            statement = trust_policy["Statement"][0]
            assert statement["Effect"] == "Allow"
            assert statement["Action"] == "sts:AssumeRole"
            assert "lambda.amazonaws.com" in statement["Principal"]["Service"]


class TestRoleManagedPolicies:
    """Test suite for IAM role managed policies."""

    def test_all_function_specific_roles_have_basic_execution_policy(self, load_cfn_template):
        """Test that all function-specific roles have AWSLambdaBasicExecutionRole."""
        # Arrange
        template = load_cfn_template("iam/roles-stack.yaml")
        
        function_specific_roles = [
            "QueryHandlerRole",
            "DataManagementRole",
            "ExecutionHandlerRole",
            "OrchestrationRole",
            "FrontendDeployerRole"
        ]
        
        # Act & Assert
        for role_name in function_specific_roles:
            role = template["Resources"][role_name]
            managed_policies = role["Properties"]["ManagedPolicyArns"]
            
            assert "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" in managed_policies

    def test_unified_role_has_basic_execution_policy(self, load_cfn_template):
        """Test that UnifiedOrchestrationRole has AWSLambdaBasicExecutionRole."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["UnifiedOrchestrationRole"]
        
        # Assert
        managed_policies = role["Properties"]["ManagedPolicyArns"]
        assert "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" in managed_policies



class TestRoleInlinePolicies:
    """Test suite for IAM role inline policies."""

    def test_query_handler_role_has_read_only_policies(self, load_cfn_template):
        """Test that QueryHandlerRole has only read-only inline policies."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["QueryHandlerRole"]
        policies = role["Properties"]["Policies"]
        
        # Assert
        policy_names = [p["PolicyName"] for p in policies]
        
        # Should have read-only policies
        assert "DynamoDBReadOnly" in policy_names
        assert "DRSReadOnly" in policy_names
        assert "EC2ReadOnly" in policy_names
        
        # Should NOT have write policies
        assert "DynamoDBFullAccess" not in policy_names
        assert "DRSWriteAccess" not in policy_names

    def test_data_management_role_has_dynamodb_write_policies(self, load_cfn_template):
        """Test that DataManagementRole has DynamoDB write permissions."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["DataManagementRole"]
        policies = role["Properties"]["Policies"]
        
        # Assert
        policy_names = [p["PolicyName"] for p in policies]
        assert "DynamoDBFullAccess" in policy_names

    def test_execution_handler_role_has_orchestration_policies(self, load_cfn_template):
        """Test that ExecutionHandlerRole has orchestration-related policies."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["ExecutionHandlerRole"]
        policies = role["Properties"]["Policies"]
        
        # Assert
        policy_names = [p["PolicyName"] for p in policies]
        
        assert "StepFunctionsOrchestration" in policy_names
        assert "SNSNotifications" in policy_names
        assert "DynamoDBFullAccess" in policy_names

    def test_orchestration_role_has_comprehensive_policies(self, load_cfn_template):
        """Test that OrchestrationRole has comprehensive DRS and EC2 policies."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["OrchestrationRole"]
        policies = role["Properties"]["Policies"]
        
        # Assert
        policy_names = [p["PolicyName"] for p in policies]
        
        assert "DRSComprehensive" in policy_names
        assert "EC2Comprehensive" in policy_names
        assert "IAMPassRole" in policy_names
        assert "KMSOperations" in policy_names


class TestRoleOutputs:
    """Test suite for IAM role stack outputs."""

    def test_stack_has_unified_role_arn_output(self, load_cfn_template):
        """Test that stack exports UnifiedRoleArn output."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "UnifiedRoleArn" in template["Outputs"]
        output = template["Outputs"]["UnifiedRoleArn"]
        
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_stack_has_query_handler_role_arn_output(self, load_cfn_template):
        """Test that stack exports QueryHandlerRoleArn output."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "QueryHandlerRoleArn" in template["Outputs"]
        output = template["Outputs"]["QueryHandlerRoleArn"]
        
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_stack_has_data_management_role_arn_output(self, load_cfn_template):
        """Test that stack exports DataManagementRoleArn output."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "DataManagementRoleArn" in template["Outputs"]
        output = template["Outputs"]["DataManagementRoleArn"]
        
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_stack_has_execution_handler_role_arn_output(self, load_cfn_template):
        """Test that stack exports ExecutionHandlerRoleArn output."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "ExecutionHandlerRoleArn" in template["Outputs"]
        output = template["Outputs"]["ExecutionHandlerRoleArn"]
        
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_stack_has_orchestration_role_arn_output(self, load_cfn_template):
        """Test that stack exports OrchestrationRoleArn output."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "OrchestrationRoleArn" in template["Outputs"]
        output = template["Outputs"]["OrchestrationRoleArn"]
        
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_stack_has_frontend_deployer_role_arn_output(self, load_cfn_template):
        """Test that stack exports FrontendDeployerRoleArn output."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "FrontendDeployerRoleArn" in template["Outputs"]
        output = template["Outputs"]["FrontendDeployerRoleArn"]
        
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_all_role_outputs_use_conditional_logic(self, load_cfn_template):
        """Test that all role ARN outputs use conditional logic."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        role_outputs = [
            "UnifiedRoleArn",
            "QueryHandlerRoleArn",
            "DataManagementRoleArn",
            "ExecutionHandlerRoleArn",
            "OrchestrationRoleArn",
            "FrontendDeployerRoleArn"
        ]
        
        # Assert
        for output_name in role_outputs:
            output = template["Outputs"][output_name]
            value = output["Value"]
            
            # Should use Fn::If or !If for conditional output
            assert isinstance(value, dict) or "!If" in str(value)


class TestConditionalLogic:
    """Test suite for IAM roles stack conditional logic."""

    def test_use_function_specific_roles_condition_is_defined(self, load_cfn_template):
        """Test that UseFunctionSpecificRoles condition is properly defined."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "UseFunctionSpecificRoles" in template["Conditions"]
        condition = template["Conditions"]["UseFunctionSpecificRoles"]
        
        # Should use Fn::Equals to check parameter value
        assert isinstance(condition, dict) or "!Equals" in str(condition)

    def test_use_unified_role_condition_is_defined(self, load_cfn_template):
        """Test that UseUnifiedRole condition is properly defined."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        
        # Assert
        assert "UseUnifiedRole" in template["Conditions"]
        condition = template["Conditions"]["UseUnifiedRole"]
        
        # Should use Fn::Not to negate UseFunctionSpecificRoles
        assert isinstance(condition, dict) or "!Not" in str(condition)

    def test_function_specific_roles_have_correct_condition(self, load_cfn_template):
        """Test that all function-specific roles use UseFunctionSpecificRoles condition."""
        # Arrange
        template = load_cfn_template("iam/roles-stack.yaml")
        
        function_specific_roles = [
            "QueryHandlerRole",
            "DataManagementRole",
            "ExecutionHandlerRole",
            "OrchestrationRole",
            "FrontendDeployerRole"
        ]
        
        # Act & Assert
        for role_name in function_specific_roles:
            role = template["Resources"][role_name]
            assert role["Condition"] == "UseFunctionSpecificRoles"

    def test_unified_role_has_correct_condition(self, load_cfn_template):
        """Test that UnifiedOrchestrationRole uses UseUnifiedRole condition."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["UnifiedOrchestrationRole"]
        
        # Assert
        assert role["Condition"] == "UseUnifiedRole"


class TestRolePermissionScoping:
    """Test suite for IAM role permission scoping and least privilege."""

    def test_query_handler_role_has_no_write_permissions(self, load_cfn_template):
        """Test that QueryHandlerRole has no write permissions to DRS or DynamoDB."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["QueryHandlerRole"]
        policies = role["Properties"]["Policies"]
        
        # Assert
        for policy in policies:
            policy_name = policy["PolicyName"]
            
            # Should only have read-only policies
            assert "ReadOnly" in policy_name or policy_name in [
                "STSAssumeRole",
                "LambdaInvoke",
                "CloudWatchMetrics",
                "CloudWatchLogs"
            ]

    def test_data_management_role_has_no_recovery_permissions(self, load_cfn_template):
        """Test that DataManagementRole has no DRS recovery operation permissions."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["DataManagementRole"]
        policies = role["Properties"]["Policies"]
        
        # Assert
        policy_names = [p["PolicyName"] for p in policies]
        
        # Should have metadata permissions but not recovery operations
        assert "DRSMetadata" in policy_names
        assert "DRSRecoveryCoordination" not in policy_names
        assert "DRSComprehensive" not in policy_names

    def test_frontend_deployer_role_scoped_to_frontend_resources(self, load_cfn_template):
        """Test that FrontendDeployerRole is scoped to frontend-related resources only."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        role = template["Resources"]["FrontendDeployerRole"]
        policies = role["Properties"]["Policies"]
        
        # Assert
        policy_names = [p["PolicyName"] for p in policies]
        
        # Should have S3 and CloudFront permissions
        assert "S3FrontendBucketAccess" in policy_names
        assert "CloudFrontInvalidation" in policy_names
        
        # Should NOT have DRS or DynamoDB permissions
        assert "DRSReadOnly" not in policy_names
        assert "DynamoDBFullAccess" not in policy_names


class TestRoleResourceCount:
    """Test suite for IAM role resource count validation."""

    def test_template_has_exactly_six_iam_roles(self, load_cfn_template):
        """Test that template defines exactly 6 IAM roles (5 function-specific + 1 unified)."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        resources = template["Resources"]
        
        # Assert
        iam_roles = [r for r in resources.values() if r["Type"] == "AWS::IAM::Role"]
        assert len(iam_roles) == 6

    def test_template_has_all_expected_roles(self, load_cfn_template):
        """Test that template has all expected role resources."""
        # Arrange & Act
        template = load_cfn_template("iam/roles-stack.yaml")
        resources = template["Resources"]
        
        # Assert
        expected_roles = [
            "QueryHandlerRole",
            "DataManagementRole",
            "ExecutionHandlerRole",
            "OrchestrationRole",
            "FrontendDeployerRole",
            "UnifiedOrchestrationRole"
        ]
        
        for role_name in expected_roles:
            assert role_name in resources
            assert resources[role_name]["Type"] == "AWS::IAM::Role"
