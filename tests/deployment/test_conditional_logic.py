"""
Unit tests for UseFunctionSpecificRoles conditional logic validation.

This module validates that the UseFunctionSpecificRoles parameter correctly controls:
- Conditional role creation (mutual exclusivity)
- Conditional outputs
- Lambda function role assignment

Validates Requirements: 5.3, 5.4, 5.5, 5.6, 5.7
"""

import pytest


class TestConditionalLogicEvaluation:
    """Test suite for UseFunctionSpecificRoles condition evaluation."""

    def test_iam_stack_has_use_function_specific_roles_condition(self, load_cfn_template):
        """Test that IAM stack defines UseFunctionSpecificRoles condition."""
        template = load_cfn_template("iam/roles-stack.yaml")
        
        assert "Conditions" in template
        conditions = template["Conditions"]
        assert "UseFunctionSpecificRoles" in conditions

    def test_iam_stack_has_use_unified_role_condition(self, load_cfn_template):
        """Test that IAM stack defines UseUnifiedRole condition."""
        template = load_cfn_template("iam/roles-stack.yaml")
        
        assert "Conditions" in template
        conditions = template["Conditions"]
        assert "UseUnifiedRole" in conditions

    def test_lambda_stack_has_use_function_specific_roles_condition(self, load_cfn_template):
        """Test that Lambda stack defines UseFunctionSpecificRoles condition."""
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        assert "Conditions" in template
        conditions = template["Conditions"]
        assert "UseFunctionSpecificRoles" in conditions


class TestMutualExclusivity:
    """Test suite for mutual exclusivity of role creation."""

    def test_unified_role_and_function_roles_have_opposite_conditions(self, load_cfn_template):
        """Test that unified role and function-specific roles have opposite conditions."""
        template = load_cfn_template("iam/roles-stack.yaml")
        
        resources = template["Resources"]
        
        # Get UnifiedOrchestrationRole condition
        unified_role = resources.get("UnifiedOrchestrationRole")
        assert unified_role is not None
        unified_condition = unified_role.get("Condition")
        assert unified_condition == "UseUnifiedRole"
        
        # Get QueryHandlerRole condition
        query_role = resources.get("QueryHandlerRole")
        assert query_role is not None
        query_condition = query_role.get("Condition")
        assert query_condition == "UseFunctionSpecificRoles"
        
        # Conditions should be opposite
        assert unified_condition != query_condition


class TestConditionalOutputs:
    """Test suite for conditional output definitions."""

    def test_unified_role_arn_output_conditional(self, load_cfn_template):
        """Test that UnifiedRoleArn output has UseUnifiedRole condition."""
        template = load_cfn_template("iam/roles-stack.yaml")
        
        outputs = template["Outputs"]
        unified_output = outputs["UnifiedRoleArn"]
        
        assert "Condition" in unified_output
        assert unified_output["Condition"] == "UseUnifiedRole"

    def test_function_role_arn_outputs_conditional(self, load_cfn_template):
        """Test that function-specific role ARN outputs have UseFunctionSpecificRoles condition."""
        template = load_cfn_template("iam/roles-stack.yaml")
        
        outputs = template["Outputs"]
        
        function_outputs = [
            "QueryHandlerRoleArn",
            "DataManagementRoleArn",
            "ExecutionHandlerRoleArn",
            "OrchestrationRoleArn",
            "FrontendDeployerRoleArn"
        ]
        
        for output_name in function_outputs:
            output = outputs[output_name]
            assert "Condition" in output
            assert output["Condition"] == "UseFunctionSpecificRoles"


class TestLambdaFunctionRoleAssignment:
    """Test suite for Lambda function role assignment based on condition."""

    def test_lambda_functions_use_if_for_role_selection(self, load_cfn_template_as_text):
        """Test that Lambda functions use !If to select role based on condition."""
        template_text = load_cfn_template_as_text("lambda/functions-stack.yaml")
        
        # Verify !If is used for role selection
        assert "!If" in template_text
        assert "UseFunctionSpecificRoles" in template_text
        
        # Verify both role types are referenced
        assert "UnifiedRoleArn" in template_text
        assert ("QueryHandlerRoleArn" in template_text or 
                "DataManagementRoleArn" in template_text or
                "ExecutionHandlerRoleArn" in template_text)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
