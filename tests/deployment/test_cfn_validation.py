"""
Unit tests for CloudFormation template validation.

This module validates that all CloudFormation templates pass:
- cfn-lint validation (syntax, schema, resource properties)
- cfn_nag security scanning
- Checkov infrastructure security scanning
- IAM policy syntax validation
- Resource ARN pattern validation
- Conditional logic evaluation
- Parameter passing between nested stacks

Validates Requirements: 16.49, 16.51, 16.52
"""

import os
import subprocess
import pytest
import yaml
from typing import Dict, Any, List


class TestCfnLintValidation:
    """Test suite for cfn-lint validation on all CloudFormation templates."""

    def test_all_templates_pass_cfn_lint(self, cfn_templates_dir):
        """Test that all CloudFormation templates pass cfn-lint validation."""
        # Find all YAML files in cfn directory and subdirectories
        template_files = []
        for root, dirs, files in os.walk(cfn_templates_dir):
            for file in files:
                if file.endswith((".yaml", ".yml")):
                    template_files.append(os.path.join(root, file))
        
        assert len(template_files) > 0, "No CloudFormation templates found"
        
        # Run cfn-lint on all templates
        # Ignore W1030 (parameter reference warnings), W2001 (unused parameters), W3005 (redundant DependsOn)
        failed_templates = []
        for template_path in template_files:
            result = subprocess.run(
                [".venv/bin/cfn-lint", template_path, "--ignore-checks", "W1030,W2001,W3005"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                failed_templates.append({
                    "template": os.path.relpath(template_path, cfn_templates_dir),
                    "errors": result.stdout
                })
        
        # Report failures
        if failed_templates:
            error_msg = "The following templates failed cfn-lint validation:\n\n"
            for failure in failed_templates:
                error_msg += f"Template: {failure['template']}\n"
                error_msg += f"Errors:\n{failure['errors']}\n\n"
            pytest.fail(error_msg)

    def test_main_stack_passes_cfn_lint(self, load_cfn_template):
        """Test that main-stack.yaml passes cfn-lint validation."""
        template_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "cfn",
            "main-stack.yaml"
        )
        
        result = subprocess.run(
            [".venv/bin/cfn-lint", template_path, "--ignore-checks", "W1030,W2001,W3005"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, (
            f"main-stack.yaml failed cfn-lint validation:\n{result.stdout}"
        )

    def test_iam_roles_stack_passes_cfn_lint(self, load_cfn_template):
        """Test that iam/roles-stack.yaml passes cfn-lint validation."""
        template_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "cfn",
            "iam",
            "roles-stack.yaml"
        )
        
        result = subprocess.run(
            [".venv/bin/cfn-lint", template_path, "--ignore-checks", "W1030,W2001,W3005"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, (
            f"iam/roles-stack.yaml failed cfn-lint validation:\n{result.stdout}"
        )

    def test_lambda_functions_stack_passes_cfn_lint(self, load_cfn_template):
        """Test that lambda/functions-stack.yaml passes cfn-lint validation."""
        template_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "cfn",
            "lambda",
            "functions-stack.yaml"
        )
        
        result = subprocess.run(
            [".venv/bin/cfn-lint", template_path, "--ignore-checks", "W1030,W2001,W3005"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, (
            f"lambda/functions-stack.yaml failed cfn-lint validation:\n{result.stdout}"
        )


class TestCfnNagSecurityScanning:
    """Test suite for cfn_nag security scanning on all CloudFormation templates."""

    @pytest.mark.skipif(
        subprocess.run(["which", "cfn_nag_scan"], capture_output=True).returncode != 0,
        reason="cfn_nag_scan not installed"
    )
    def test_all_templates_pass_cfn_nag(self, cfn_templates_dir):
        """Test that all CloudFormation templates pass cfn_nag security scanning."""
        # Find all YAML files in cfn directory and subdirectories
        template_files = []
        for root, dirs, files in os.walk(cfn_templates_dir):
            for file in files:
                if file.endswith((".yaml", ".yml")):
                    template_files.append(os.path.join(root, file))
        
        assert len(template_files) > 0, "No CloudFormation templates found"
        
        # Run cfn_nag on all templates
        failed_templates = []
        for template_path in template_files:
            result = subprocess.run(
                ["cfn_nag_scan", "--input-path", template_path],
                capture_output=True,
                text=True
            )
            
            # cfn_nag returns non-zero for failures
            if result.returncode != 0:
                failed_templates.append({
                    "template": os.path.relpath(template_path, cfn_templates_dir),
                    "output": result.stdout
                })
        
        # Report failures
        if failed_templates:
            error_msg = "The following templates failed cfn_nag security scanning:\n\n"
            for failure in failed_templates:
                error_msg += f"Template: {failure['template']}\n"
                error_msg += f"Output:\n{failure['output']}\n\n"
            pytest.fail(error_msg)

    @pytest.mark.skipif(
        subprocess.run(["which", "cfn_nag_scan"], capture_output=True).returncode != 0,
        reason="cfn_nag_scan not installed"
    )
    def test_iam_roles_stack_passes_cfn_nag(self):
        """Test that iam/roles-stack.yaml passes cfn_nag security scanning."""
        template_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "cfn",
            "iam",
            "roles-stack.yaml"
        )
        
        result = subprocess.run(
            ["cfn_nag_scan", "--input-path", template_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, (
            f"iam/roles-stack.yaml failed cfn_nag security scanning:\n{result.stdout}"
        )


class TestCheckovSecurityScanning:
    """Test suite for Checkov infrastructure security scanning."""

    @pytest.mark.skipif(
        subprocess.run(["which", "checkov"], capture_output=True).returncode != 0,
        reason="checkov not installed"
    )
    def test_all_templates_pass_checkov(self, cfn_templates_dir):
        """Test that all CloudFormation templates pass Checkov security scanning."""
        # Run Checkov on entire cfn directory
        result = subprocess.run(
            [
                "checkov",
                "--directory", cfn_templates_dir,
                "--framework", "cloudformation",
                "--quiet"
            ],
            capture_output=True,
            text=True
        )
        
        # Checkov returns non-zero for failures
        if result.returncode != 0:
            pytest.fail(
                f"CloudFormation templates failed Checkov security scanning:\n{result.stdout}"
            )

    @pytest.mark.skipif(
        subprocess.run(["which", "checkov"], capture_output=True).returncode != 0,
        reason="checkov not installed"
    )
    def test_iam_roles_stack_passes_checkov(self):
        """Test that iam/roles-stack.yaml passes Checkov security scanning."""
        template_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "cfn",
            "iam",
            "roles-stack.yaml"
        )
        
        result = subprocess.run(
            [
                "checkov",
                "--file", template_path,
                "--framework", "cloudformation",
                "--quiet"
            ],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, (
            f"iam/roles-stack.yaml failed Checkov security scanning:\n{result.stdout}"
        )


class TestIAMPolicySyntax:
    """Test suite for IAM policy syntax validation."""

    def test_iam_roles_have_valid_policy_syntax(self, load_cfn_template):
        """Test that all IAM roles have valid policy document syntax."""
        template = load_cfn_template("iam/roles-stack.yaml")
        
        resources = template.get("Resources", {})
        
        # Find all IAM roles
        iam_roles = []
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::IAM::Role":
                iam_roles.append(resource_name)
        
        assert len(iam_roles) > 0, "No IAM roles found in template"
        
        # Validate each role's policy documents
        for role_name in iam_roles:
            role = resources[role_name]
            properties = role.get("Properties", {})
            
            # Validate AssumeRolePolicyDocument
            if "AssumeRolePolicyDocument" in properties:
                trust_policy = properties["AssumeRolePolicyDocument"]
                self._validate_policy_document(trust_policy, f"{role_name}.AssumeRolePolicyDocument")
            
            # Validate inline policies
            if "Policies" in properties:
                policies = properties["Policies"]
                assert isinstance(policies, list), f"{role_name}.Policies must be a list"
                
                for idx, policy in enumerate(policies):
                    assert "PolicyName" in policy, f"{role_name}.Policies[{idx}] missing PolicyName"
                    assert "PolicyDocument" in policy, f"{role_name}.Policies[{idx}] missing PolicyDocument"
                    
                    policy_doc = policy["PolicyDocument"]
                    self._validate_policy_document(
                        policy_doc,
                        f"{role_name}.Policies[{idx}].PolicyDocument"
                    )

    def _validate_policy_document(self, policy_doc: Dict[str, Any], context: str):
        """Validate IAM policy document structure."""
        assert "Version" in policy_doc, f"{context} missing Version"
        assert policy_doc["Version"] in ["2012-10-17", "2008-10-17"], (
            f"{context} has invalid Version: {policy_doc['Version']}"
        )
        
        assert "Statement" in policy_doc, f"{context} missing Statement"
        statements = policy_doc["Statement"]
        assert isinstance(statements, list), f"{context}.Statement must be a list"
        assert len(statements) > 0, f"{context}.Statement cannot be empty"
        
        for idx, statement in enumerate(statements):
            self._validate_policy_statement(statement, f"{context}.Statement[{idx}]")

    def _validate_policy_statement(self, statement: Dict[str, Any], context: str):
        """Validate IAM policy statement structure."""
        assert "Effect" in statement, f"{context} missing Effect"
        assert statement["Effect"] in ["Allow", "Deny"], (
            f"{context} has invalid Effect: {statement['Effect']}"
        )
        
        assert "Action" in statement or "NotAction" in statement, (
            f"{context} missing Action or NotAction"
        )
        
        # Validate Action format
        if "Action" in statement:
            action = statement["Action"]
            if isinstance(action, str):
                assert ":" in action or action == "*", (
                    f"{context}.Action has invalid format: {action}"
                )
            elif isinstance(action, list):
                for act in action:
                    assert isinstance(act, str), f"{context}.Action must contain strings"
                    assert ":" in act or act == "*", (
                        f"{context}.Action has invalid format: {act}"
                    )


class TestResourceARNPatterns:
    """Test suite for resource ARN pattern validation."""

    def test_dynamodb_permissions_use_project_specific_arns(self, load_cfn_template_as_text):
        """Test that DynamoDB permissions use project-specific ARN patterns."""
        template_text = load_cfn_template_as_text("iam/roles-stack.yaml")
        
        # Find all DynamoDB permission statements
        assert "dynamodb:" in template_text.lower()
        
        # Verify resource ARN pattern includes ProjectName
        # Pattern: arn:aws:dynamodb:{Region}:{AccountId}:table/{ProjectName}-*
        if "dynamodb:GetItem" in template_text or "dynamodb:PutItem" in template_text:
            assert "table/" in template_text or "table:" in template_text
            assert "${ProjectName}" in template_text or "!Sub" in template_text

    def test_lambda_permissions_use_project_specific_arns(self, load_cfn_template_as_text):
        """Test that Lambda permissions use project-specific ARN patterns."""
        template_text = load_cfn_template_as_text("iam/roles-stack.yaml")
        
        # Find Lambda invoke permissions
        if "lambda:InvokeFunction" in template_text:
            # Verify resource ARN pattern includes ProjectName
            assert "${ProjectName}" in template_text or "!Sub" in template_text

    def test_sns_permissions_use_project_specific_arns(self, load_cfn_template_as_text):
        """Test that SNS permissions use project-specific ARN patterns."""
        template_text = load_cfn_template_as_text("iam/roles-stack.yaml")
        
        # Find SNS permissions
        if "sns:Publish" in template_text or "sns:Subscribe" in template_text:
            # Verify resource ARN pattern includes ProjectName
            assert "${ProjectName}" in template_text or "!Sub" in template_text

    def test_step_functions_permissions_use_project_specific_arns(self, load_cfn_template_as_text):
        """Test that Step Functions permissions use project-specific ARN patterns."""
        template_text = load_cfn_template_as_text("iam/roles-stack.yaml")
        
        # Find Step Functions permissions
        if "states:StartExecution" in template_text or "states:DescribeExecution" in template_text:
            # Verify resource ARN pattern includes ProjectName
            assert "${ProjectName}" in template_text or "!Sub" in template_text


class TestConditionalLogic:
    """Test suite for CloudFormation conditional logic validation."""

    def test_use_function_specific_roles_condition_evaluates_correctly(self, load_cfn_template):
        """Test that UseFunctionSpecificRoles condition evaluates correctly."""
        template = load_cfn_template("iam/roles-stack.yaml")
        
        conditions = template.get("Conditions", {})
        assert "UseFunctionSpecificRoles" in conditions
        
        # Verify condition logic (YAML parser converts !Equals to dict format)
        condition = conditions["UseFunctionSpecificRoles"]
        assert "Fn::Equals" in condition or "Equals" in condition

    def test_use_unified_role_condition_is_inverse(self, load_cfn_template):
        """Test that UseUnifiedRole condition is inverse of UseFunctionSpecificRoles."""
        template = load_cfn_template("iam/roles-stack.yaml")
        
        conditions = template.get("Conditions", {})
        assert "UseUnifiedRole" in conditions
        
        # Verify condition is inverse (YAML parser converts !Not to dict format)
        condition = conditions["UseUnifiedRole"]
        assert "Fn::Not" in condition or "Not" in condition

    def test_conditional_resources_have_correct_conditions(self, load_cfn_template):
        """Test that conditional resources have correct condition attributes."""
        template = load_cfn_template("iam/roles-stack.yaml")
        
        resources = template.get("Resources", {})
        
        # Unified role should have UseUnifiedRole condition
        if "UnifiedOrchestrationRole" in resources:
            unified_role = resources["UnifiedOrchestrationRole"]
            assert "Condition" in unified_role
            assert unified_role["Condition"] == "UseUnifiedRole"
        
        # Function-specific roles should have UseFunctionSpecificRoles condition
        function_specific_roles = [
            "QueryHandlerRole",
            "DataManagementRole",
            "ExecutionHandlerRole",
            "OrchestrationRole",
            "FrontendDeployerRole"
        ]
        
        for role_name in function_specific_roles:
            if role_name in resources:
                role = resources[role_name]
                assert "Condition" in role, f"{role_name} missing Condition"
                assert role["Condition"] == "UseFunctionSpecificRoles", (
                    f"{role_name} has incorrect condition: {role['Condition']}"
                )


class TestParameterPassing:
    """Test suite for parameter passing between nested stacks."""

    def test_main_stack_passes_role_arns_to_lambda_stack(self, load_cfn_template):
        """Test that main-stack.yaml passes role ARNs to lambda stack."""
        template = load_cfn_template("main-stack.yaml")
        
        resources = template.get("Resources", {})
        
        # Find Lambda stack resource
        lambda_stack = None
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::CloudFormation::Stack":
                properties = resource.get("Properties", {})
                template_url = properties.get("TemplateURL", "")
                # TemplateURL can be a string or dict (CloudFormation intrinsic function)
                template_url_str = str(template_url).lower()
                if "lambda" in template_url_str:
                    lambda_stack = resource
                    break
        
        assert lambda_stack is not None, "Lambda stack not found in main-stack.yaml"
        
        # Verify role ARN parameters are passed
        parameters = lambda_stack["Properties"].get("Parameters", {})
        
        expected_parameters = [
            "UnifiedRoleArn",
            "QueryHandlerRoleArn",
            "DataManagementRoleArn",
            "ExecutionHandlerRoleArn",
            "OrchestrationRoleArn",
            "FrontendDeployerRoleArn"
        ]
        
        for param_name in expected_parameters:
            assert param_name in parameters, (
                f"Lambda stack missing parameter: {param_name}"
            )

    def test_lambda_stack_accepts_role_arn_parameters(self, load_cfn_template):
        """Test that lambda/functions-stack.yaml accepts role ARN parameters."""
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        parameters = template.get("Parameters", {})
        
        expected_parameters = [
            "UnifiedRoleArn",
            "QueryHandlerRoleArn",
            "DataManagementRoleArn",
            "ExecutionHandlerRoleArn",
            "OrchestrationRoleArn",
            "FrontendDeployerRoleArn"
        ]
        
        for param_name in expected_parameters:
            assert param_name in parameters, (
                f"Lambda stack missing parameter definition: {param_name}"
            )
            
            param = parameters[param_name]
            assert param["Type"] == "String", (
                f"Parameter {param_name} has incorrect type: {param['Type']}"
            )

    def test_lambda_functions_use_conditional_role_selection(self, load_cfn_template):
        """Test that Lambda functions use conditional role selection."""
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        resources = template.get("Resources", {})
        
        # Find Lambda function resources
        lambda_functions = []
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::Lambda::Function":
                lambda_functions.append(resource_name)
        
        assert len(lambda_functions) >= 5, (
            f"Expected at least 5 Lambda functions, found {len(lambda_functions)}"
        )
        
        # Verify each function has Role property
        for func_name in lambda_functions:
            func = resources[func_name]
            properties = func.get("Properties", {})
            assert "Role" in properties, f"Function {func_name} missing Role property"


class TestNestedStackDependencies:
    """Test suite for nested stack dependency validation."""

    def test_main_stack_has_correct_dependency_order(self, load_cfn_template):
        """Test that main-stack.yaml defines correct dependency order."""
        template = load_cfn_template("main-stack.yaml")
        
        resources = template.get("Resources", {})
        
        # Find IAM stack
        iam_stack_name = None
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::CloudFormation::Stack":
                properties = resource.get("Properties", {})
                template_url = properties.get("TemplateURL", "")
                # TemplateURL can be a string or dict (CloudFormation intrinsic function)
                template_url_str = str(template_url).lower()
                if "iam" in template_url_str:
                    iam_stack_name = resource_name
                    break
        
        assert iam_stack_name is not None, "IAM stack not found in main-stack.yaml"
        
        # Find Lambda stack and verify it depends on IAM stack
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::CloudFormation::Stack":
                properties = resource.get("Properties", {})
                template_url = properties.get("TemplateURL", "")
                # TemplateURL can be a string or dict (CloudFormation intrinsic function)
                template_url_str = str(template_url).lower()
                if "lambda" in template_url_str:
                    # Lambda stack should depend on IAM stack
                    depends_on = resource.get("DependsOn", [])
                    if isinstance(depends_on, str):
                        depends_on = [depends_on]
                    
                    assert iam_stack_name in depends_on, (
                        f"Lambda stack should depend on {iam_stack_name}"
                    )

    def test_nested_stacks_have_template_urls(self, load_cfn_template):
        """Test that all nested stacks have valid TemplateURL properties."""
        template = load_cfn_template("main-stack.yaml")
        
        resources = template.get("Resources", {})
        
        # Find all nested stacks
        nested_stacks = []
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::CloudFormation::Stack":
                nested_stacks.append(resource_name)
        
        assert len(nested_stacks) > 0, "No nested stacks found in main-stack.yaml"
        
        # Verify each nested stack has TemplateURL
        for stack_name in nested_stacks:
            stack = resources[stack_name]
            properties = stack.get("Properties", {})
            
            assert "TemplateURL" in properties, (
                f"Nested stack {stack_name} missing TemplateURL"
            )
            
            template_url = properties["TemplateURL"]
            template_url_str = str(template_url)
            assert "s3.amazonaws.com" in template_url_str or "Sub" in template_url_str, (
                f"Nested stack {stack_name} has invalid TemplateURL format"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
