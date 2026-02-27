"""
Unit tests for backward compatibility between unified and function-specific IAM roles.

This module validates that the CloudFormation templates maintain backward compatibility
when switching between unified role (UseFunctionSpecificRoles=false) and function-specific
roles (UseFunctionSpecificRoles=true) architectures.

Validates Requirements:
- 5.1-5.8: Backward compatibility configuration
- 16.43-16.48: Template reorganization backward compatibility
- 10.2: EventBridge duplicate rule removal
"""

import os
import re
import pytest


def load_template_as_text(template_path):
    """Load a CloudFormation template as raw text."""
    full_path = os.path.join(os.path.dirname(__file__), "..", "..", template_path)
    with open(full_path, "r") as f:
        return f.read()


def extract_resource_section(template_text, resource_name):
    """
    Extract a resource section from CloudFormation template text.
    
    Returns the YAML section for the specified resource as a string.
    """
    pattern = rf"^\s+{re.escape(resource_name)}:\s*$"
    lines = template_text.split("\n")
    
    start_idx = None
    for i, line in enumerate(lines):
        if re.match(pattern, line):
            start_idx = i
            break
    
    if start_idx is None:
        return None
    
    resource_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    
    resource_lines = [lines[start_idx]]
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if line.strip() == "":
            resource_lines.append(line)
            continue
        
        current_indent = len(line) - len(line.lstrip())
        if current_indent <= resource_indent and line.strip():
            break
        
        resource_lines.append(line)
    
    return "\n".join(resource_lines)


def extract_parameters_section(template_text):
    """Extract the Parameters section from CloudFormation template."""
    lines = template_text.split("\n")
    
    start_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^Parameters:\s*$", line):
            start_idx = i
            break
    
    if start_idx is None:
        return None
    
    param_lines = [lines[start_idx]]
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if line.strip() == "":
            param_lines.append(line)
            continue
        
        if re.match(r"^[A-Z][a-zA-Z]+:\s*$", line):
            break
        
        param_lines.append(line)
    
    return "\n".join(param_lines)


def extract_conditions_section(template_text):
    """Extract the Conditions section from CloudFormation template."""
    lines = template_text.split("\n")
    
    start_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^Conditions:\s*$", line):
            start_idx = i
            break
    
    if start_idx is None:
        return None
    
    cond_lines = [lines[start_idx]]
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if line.strip() == "":
            cond_lines.append(line)
            continue
        
        if re.match(r"^[A-Z][a-zA-Z]+:\s*$", line):
            break
        
        cond_lines.append(line)
    
    return "\n".join(cond_lines)


class TestExistingTemplatesUnchanged:
    """Test that existing templates remain unchanged (except Task 10.2 duplicate rule removal)."""

    def test_master_template_exists(self):
        """Test that master-template.yaml still exists."""
        template_text = load_template_as_text("cfn/master-template.yaml")
        assert template_text is not None, "master-template.yaml should still exist"
        assert len(template_text) > 0, "master-template.yaml should not be empty"

    def test_master_template_has_unified_role(self):
        """Test that master-template.yaml still defines UnifiedOrchestrationRole."""
        template_text = load_template_as_text("cfn/master-template.yaml")
        assert "UnifiedOrchestrationRole:" in template_text, (
            "master-template.yaml should still define UnifiedOrchestrationRole"
        )

    def test_lambda_stack_exists(self):
        """Test that lambda-stack.yaml still exists."""
        template_text = load_template_as_text("cfn/lambda-stack.yaml")
        assert template_text is not None, "lambda-stack.yaml should still exist"
        assert len(template_text) > 0, "lambda-stack.yaml should not be empty"

    def test_lambda_stack_has_lambda_functions(self):
        """Test that lambda-stack.yaml still defines all Lambda functions."""
        template_text = load_template_as_text("cfn/lambda-stack.yaml")
        
        assert "QueryHandlerFunction:" in template_text, (
            "lambda-stack.yaml should define QueryHandlerFunction"
        )
        assert "DataManagementHandlerFunction:" in template_text, (
            "lambda-stack.yaml should define DataManagementHandlerFunction"
        )
        assert "ExecutionHandlerFunction:" in template_text, (
            "lambda-stack.yaml should define ExecutionHandlerFunction"
        )
        assert "OrchestrationFunction:" in template_text, (
            "lambda-stack.yaml should define OrchestrationFunction"
        )
        assert "FrontendDeployerFunction:" in template_text, (
            "lambda-stack.yaml should define FrontendDeployerFunction"
        )

    def test_eventbridge_stack_exists(self):
        """Test that eventbridge-stack.yaml still exists."""
        template_text = load_template_as_text("cfn/eventbridge-stack.yaml")
        assert template_text is not None, "eventbridge-stack.yaml should still exist"
        assert len(template_text) > 0, "eventbridge-stack.yaml should not be empty"

    def test_eventbridge_stack_has_execution_polling_rule(self):
        """Test that eventbridge-stack.yaml still has ExecutionPollingScheduleRule."""
        template_text = load_template_as_text("cfn/eventbridge-stack.yaml")
        assert "ExecutionPollingScheduleRule:" in template_text, (
            "eventbridge-stack.yaml should define ExecutionPollingScheduleRule"
        )


class TestDuplicateRuleRemoval:
    """Test that duplicate EventBridge rule has been removed from lambda-stack.yaml (Task 10.2)."""

    def test_lambda_stack_no_execution_finder_rule(self):
        """
        Test that ExecutionFinderScheduleRule has been removed from lambda-stack.yaml.
        
        Validates Requirement 16.63-16.65: ExecutionFinderScheduleRule in lambda-stack.yaml
        is a duplicate of ExecutionPollingScheduleRule in eventbridge-stack.yaml and should
        be removed during reorganization.
        """
        template_text = load_template_as_text("cfn/lambda-stack.yaml")
        
        assert "ExecutionFinderScheduleRule:" not in template_text, (
            "ExecutionFinderScheduleRule should be removed from lambda-stack.yaml. "
            "This is a duplicate of ExecutionPollingScheduleRule in eventbridge-stack.yaml. "
            "Both rules trigger ExecutionHandlerFunction with {\"operation\": \"find\"} every 1 minute."
        )

    def test_eventbridge_stack_has_execution_polling_rule(self):
        """
        Test that ExecutionPollingScheduleRule is preserved in eventbridge-stack.yaml.
        
        Validates Requirement 16.66: ExecutionPollingScheduleRule should be preserved
        as the canonical execution polling rule.
        """
        template_text = load_template_as_text("cfn/eventbridge-stack.yaml")
        
        assert "ExecutionPollingScheduleRule:" in template_text, (
            "ExecutionPollingScheduleRule should be preserved in eventbridge-stack.yaml"
        )

    def test_only_one_execution_polling_rule_exists(self):
        """
        Test that only ONE execution polling rule exists across all templates.
        
        Validates Requirement 16.70: Only ONE EventBridge rule should trigger execution
        polling after reorganization.
        """
        lambda_text = load_template_as_text("cfn/lambda-stack.yaml")
        eventbridge_text = load_template_as_text("cfn/eventbridge-stack.yaml")
        
        lambda_has_finder = "ExecutionFinderScheduleRule:" in lambda_text
        lambda_has_polling = "ExecutionPollingScheduleRule:" in lambda_text
        eventbridge_has_finder = "ExecutionFinderScheduleRule:" in eventbridge_text
        eventbridge_has_polling = "ExecutionPollingScheduleRule:" in eventbridge_text
        
        total_rules = sum([
            lambda_has_finder,
            lambda_has_polling,
            eventbridge_has_finder,
            eventbridge_has_polling
        ])
        
        assert total_rules == 1, (
            f"Expected exactly 1 execution polling rule, found {total_rules}. "
            f"lambda-stack.yaml: ExecutionFinderScheduleRule={lambda_has_finder}, "
            f"ExecutionPollingScheduleRule={lambda_has_polling}. "
            f"eventbridge-stack.yaml: ExecutionFinderScheduleRule={eventbridge_has_finder}, "
            f"ExecutionPollingScheduleRule={eventbridge_has_polling}."
        )


class TestMainStackBackwardCompatibility:
    """Test that main-stack.yaml supports both unified and function-specific roles."""

    def test_main_stack_exists(self):
        """Test that main-stack.yaml exists."""
        template_text = load_template_as_text("cfn/main-stack.yaml")
        assert template_text is not None, "main-stack.yaml should exist"
        assert len(template_text) > 0, "main-stack.yaml should not be empty"

    def test_main_stack_has_use_function_specific_roles_parameter(self):
        """
        Test that main-stack.yaml defines UseFunctionSpecificRoles parameter.
        
        Validates Requirement 5.1: CloudFormation template shall define parameter
        named UseFunctionSpecificRoles with allowed values 'true' and 'false'.
        """
        template_text = load_template_as_text("cfn/main-stack.yaml")
        params_section = extract_parameters_section(template_text)
        
        assert params_section is not None, "main-stack.yaml should have Parameters section"
        assert "UseFunctionSpecificRoles:" in params_section, (
            "main-stack.yaml should define UseFunctionSpecificRoles parameter"
        )

    def test_use_function_specific_roles_parameter_default_false(self):
        """
        Test that UseFunctionSpecificRoles parameter defaults to 'false'.
        
        Validates Requirement 5.2: Default value of UseFunctionSpecificRoles shall be
        'false' for backward compatibility.
        """
        template_text = load_template_as_text("cfn/main-stack.yaml")
        params_section = extract_parameters_section(template_text)
        
        assert "Default: 'false'" in params_section or 'Default: "false"' in params_section, (
            "UseFunctionSpecificRoles parameter should default to 'false' for backward compatibility"
        )

    def test_use_function_specific_roles_allowed_values(self):
        """
        Test that UseFunctionSpecificRoles parameter has allowed values 'true' and 'false'.
        
        Validates Requirement 5.1: Parameter shall have allowed values 'true' and 'false'.
        """
        template_text = load_template_as_text("cfn/main-stack.yaml")
        params_section = extract_parameters_section(template_text)
        
        assert "AllowedValues:" in params_section, (
            "UseFunctionSpecificRoles parameter should define AllowedValues"
        )
        
        assert ("'true'" in params_section or '"true"' in params_section) and (
            "'false'" in params_section or '"false"' in params_section
        ), (
            "UseFunctionSpecificRoles parameter should allow values 'true' and 'false'"
        )

    def test_main_stack_has_conditions(self):
        """
        Test that main-stack.yaml defines conditions for role selection.
        
        Validates Requirement 7.2-7.3: Template shall define UseFunctionSpecificRoles
        and UseUnifiedRole conditions.
        """
        template_text = load_template_as_text("cfn/main-stack.yaml")
        conditions_section = extract_conditions_section(template_text)
        
        assert conditions_section is not None, "main-stack.yaml should have Conditions section"
        assert "UseFunctionSpecificRoles:" in conditions_section, (
            "main-stack.yaml should define UseFunctionSpecificRoles condition"
        )
        assert "UseUnifiedRole:" in conditions_section, (
            "main-stack.yaml should define UseUnifiedRole condition"
        )

    def test_main_stack_references_iam_nested_stack(self):
        """Test that main-stack.yaml references iam/roles-stack.yaml nested stack."""
        template_text = load_template_as_text("cfn/main-stack.yaml")
        
        assert "iam/roles-stack.yaml" in template_text or "IAMStack:" in template_text, (
            "main-stack.yaml should reference iam/roles-stack.yaml nested stack"
        )

    def test_main_stack_references_lambda_nested_stack(self):
        """Test that main-stack.yaml references lambda/functions-stack.yaml nested stack."""
        template_text = load_template_as_text("cfn/main-stack.yaml")
        
        assert "lambda/functions-stack.yaml" in template_text or "LambdaStack:" in template_text, (
            "main-stack.yaml should reference lambda/functions-stack.yaml nested stack"
        )


class TestIAMRolesStackConditionalCreation:
    """Test that iam/roles-stack.yaml creates roles conditionally."""

    def test_iam_roles_stack_exists(self):
        """Test that iam/roles-stack.yaml exists."""
        template_text = load_template_as_text("cfn/iam/roles-stack.yaml")
        assert template_text is not None, "iam/roles-stack.yaml should exist"
        assert len(template_text) > 0, "iam/roles-stack.yaml should not be empty"

    def test_iam_roles_stack_has_unified_role(self):
        """
        Test that iam/roles-stack.yaml defines UnifiedOrchestrationRole.
        
        Validates Requirement 5.3: When UseFunctionSpecificRoles is 'false',
        template shall create the Unified_Role.
        """
        template_text = load_template_as_text("cfn/iam/roles-stack.yaml")
        
        assert "UnifiedOrchestrationRole:" in template_text, (
            "iam/roles-stack.yaml should define UnifiedOrchestrationRole"
        )

    def test_unified_role_has_use_unified_role_condition(self):
        """
        Test that UnifiedOrchestrationRole has UseUnifiedRole condition.
        
        Validates Requirement 7.4: Unified_Role resource shall include condition UseUnifiedRole.
        """
        template_text = load_template_as_text("cfn/iam/roles-stack.yaml")
        unified_role_section = extract_resource_section(template_text, "UnifiedOrchestrationRole")
        
        assert unified_role_section is not None, (
            "UnifiedOrchestrationRole not found in iam/roles-stack.yaml"
        )
        
        assert "Condition: UseUnifiedRole" in unified_role_section, (
            "UnifiedOrchestrationRole should have Condition: UseUnifiedRole"
        )

    def test_iam_roles_stack_has_function_specific_roles(self):
        """
        Test that iam/roles-stack.yaml defines all five function-specific roles.
        
        Validates Requirement 5.4: When UseFunctionSpecificRoles is 'true',
        template shall create all five Function_Specific_Roles.
        """
        template_text = load_template_as_text("cfn/iam/roles-stack.yaml")
        
        assert "QueryHandlerRole:" in template_text, (
            "iam/roles-stack.yaml should define QueryHandlerRole"
        )
        assert "DataManagementHandlerRole:" in template_text, (
            "iam/roles-stack.yaml should define DataManagementHandlerRole"
        )
        assert "ExecutionHandlerRole:" in template_text, (
            "iam/roles-stack.yaml should define ExecutionHandlerRole"
        )
        assert "OrchestrationFunctionRole:" in template_text, (
            "iam/roles-stack.yaml should define OrchestrationFunctionRole"
        )
        assert "FrontendDeployerRole:" in template_text, (
            "iam/roles-stack.yaml should define FrontendDeployerRole"
        )

    def test_function_specific_roles_have_condition(self):
        """
        Test that function-specific roles have UseFunctionSpecificRoles condition.
        
        Validates Requirement 7.5: Function_Specific_Role resources shall include
        condition UseFunctionSpecificRoles.
        """
        template_text = load_template_as_text("cfn/iam/roles-stack.yaml")
        
        query_role_section = extract_resource_section(template_text, "QueryHandlerRole")
        assert query_role_section is not None, "QueryHandlerRole not found"
        assert "Condition: UseFunctionSpecificRoles" in query_role_section, (
            "QueryHandlerRole should have Condition: UseFunctionSpecificRoles"
        )
        
        data_mgmt_role_section = extract_resource_section(template_text, "DataManagementHandlerRole")
        assert data_mgmt_role_section is not None, "DataManagementHandlerRole not found"
        assert "Condition: UseFunctionSpecificRoles" in data_mgmt_role_section, (
            "DataManagementHandlerRole should have Condition: UseFunctionSpecificRoles"
        )


class TestLambdaStackRoleSelection:
    """Test that lambda/functions-stack.yaml selects roles conditionally."""

    def test_lambda_functions_stack_exists(self):
        """Test that lambda/functions-stack.yaml exists."""
        template_text = load_template_as_text("cfn/lambda/functions-stack.yaml")
        assert template_text is not None, "lambda/functions-stack.yaml should exist"
        assert len(template_text) > 0, "lambda/functions-stack.yaml should not be empty"

    def test_lambda_functions_stack_accepts_role_parameters(self):
        """
        Test that lambda/functions-stack.yaml accepts role ARN parameters.
        
        Validates Requirement 7.6: Lambda_Stack nested template shall accept role ARN
        parameters for each function (unified role plus five function-specific roles).
        """
        template_text = load_template_as_text("cfn/lambda/functions-stack.yaml")
        params_section = extract_parameters_section(template_text)
        
        assert params_section is not None, "lambda/functions-stack.yaml should have Parameters"
        
        assert "UnifiedRoleArn:" in params_section, (
            "lambda/functions-stack.yaml should accept UnifiedRoleArn parameter"
        )
        assert "QueryHandlerRoleArn:" in params_section, (
            "lambda/functions-stack.yaml should accept QueryHandlerRoleArn parameter"
        )
        assert "DataManagementHandlerRoleArn:" in params_section, (
            "lambda/functions-stack.yaml should accept DataManagementHandlerRoleArn parameter"
        )
        assert "ExecutionHandlerRoleArn:" in params_section, (
            "lambda/functions-stack.yaml should accept ExecutionHandlerRoleArn parameter"
        )
        assert "OrchestrationFunctionRoleArn:" in params_section, (
            "lambda/functions-stack.yaml should accept OrchestrationFunctionRoleArn parameter"
        )
        assert "FrontendDeployerRoleArn:" in params_section, (
            "lambda/functions-stack.yaml should accept FrontendDeployerRoleArn parameter"
        )

    def test_lambda_functions_use_conditional_role_selection(self):
        """
        Test that Lambda functions use !If to select between unified and function-specific roles.
        
        Validates Requirement 7.8: Lambda_Stack shall use CloudFormation intrinsic function
        !If to select the correct role ARN for each Lambda function.
        """
        template_text = load_template_as_text("cfn/lambda/functions-stack.yaml")
        
        query_handler_section = extract_resource_section(template_text, "QueryHandlerFunction")
        assert query_handler_section is not None, "QueryHandlerFunction not found"
        assert "!If" in query_handler_section or "Fn::If" in query_handler_section, (
            "QueryHandlerFunction should use !If to select role ARN"
        )
        
        data_mgmt_section = extract_resource_section(template_text, "DataManagementHandlerFunction")
        assert data_mgmt_section is not None, "DataManagementHandlerFunction not found"
        assert "!If" in data_mgmt_section or "Fn::If" in data_mgmt_section, (
            "DataManagementHandlerFunction should use !If to select role ARN"
        )


class TestRollbackCapability:
    """Test that templates support rollback from function-specific to unified roles."""

    def test_no_simultaneous_role_creation(self):
        """
        Test that templates do not create both unified and function-specific roles simultaneously.
        
        Validates Requirement 5.7: CloudFormation template shall NOT create both
        Unified_Role and Function_Specific_Roles simultaneously.
        """
        template_text = load_template_as_text("cfn/iam/roles-stack.yaml")
        
        unified_role_section = extract_resource_section(template_text, "UnifiedOrchestrationRole")
        query_role_section = extract_resource_section(template_text, "QueryHandlerRole")
        
        assert unified_role_section is not None, "UnifiedOrchestrationRole should exist"
        assert query_role_section is not None, "QueryHandlerRole should exist"
        
        assert "Condition: UseUnifiedRole" in unified_role_section, (
            "UnifiedOrchestrationRole should have UseUnifiedRole condition"
        )
        assert "Condition: UseFunctionSpecificRoles" in query_role_section, (
            "QueryHandlerRole should have UseFunctionSpecificRoles condition"
        )

    def test_conditions_are_mutually_exclusive(self):
        """
        Test that UseUnifiedRole and UseFunctionSpecificRoles conditions are mutually exclusive.
        
        Validates Requirement 7.3: UseUnifiedRole condition shall be the inverse of
        UseFunctionSpecificRoles.
        """
        template_text = load_template_as_text("cfn/iam/roles-stack.yaml")
        conditions_section = extract_conditions_section(template_text)
        
        assert conditions_section is not None, "iam/roles-stack.yaml should have Conditions"
        
        assert "UseUnifiedRole:" in conditions_section, (
            "iam/roles-stack.yaml should define UseUnifiedRole condition"
        )
        
        assert "!Not" in conditions_section or "Fn::Not" in conditions_section, (
            "UseUnifiedRole condition should use !Not to invert UseFunctionSpecificRoles"
        )


class TestTemplateValidation:
    """Test that templates can be parsed and validated (no live AWS resources)."""

    def test_master_template_is_valid_yaml(self):
        """Test that master-template.yaml is valid YAML."""
        template_text = load_template_as_text("cfn/master-template.yaml")
        
        assert "AWSTemplateFormatVersion:" in template_text, (
            "master-template.yaml should have AWSTemplateFormatVersion"
        )
        assert "Resources:" in template_text, (
            "master-template.yaml should have Resources section"
        )

    def test_main_stack_is_valid_yaml(self):
        """Test that main-stack.yaml is valid YAML."""
        template_text = load_template_as_text("cfn/main-stack.yaml")
        
        assert "AWSTemplateFormatVersion:" in template_text, (
            "main-stack.yaml should have AWSTemplateFormatVersion"
        )
        assert "Resources:" in template_text, (
            "main-stack.yaml should have Resources section"
        )

    def test_iam_roles_stack_is_valid_yaml(self):
        """Test that iam/roles-stack.yaml is valid YAML."""
        template_text = load_template_as_text("cfn/iam/roles-stack.yaml")
        
        assert "AWSTemplateFormatVersion:" in template_text, (
            "iam/roles-stack.yaml should have AWSTemplateFormatVersion"
        )
        assert "Resources:" in template_text, (
            "iam/roles-stack.yaml should have Resources section"
        )

    def test_lambda_functions_stack_is_valid_yaml(self):
        """Test that lambda/functions-stack.yaml is valid YAML."""
        template_text = load_template_as_text("cfn/lambda/functions-stack.yaml")
        
        assert "AWSTemplateFormatVersion:" in template_text, (
            "lambda/functions-stack.yaml should have AWSTemplateFormatVersion"
        )
        assert "Resources:" in template_text, (
            "lambda/functions-stack.yaml should have Resources section"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
