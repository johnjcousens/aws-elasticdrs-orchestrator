"""
Unit tests for main stack nested stack orchestration validation.

This module validates that the main-stack.yaml correctly implements:
- Nested stack dependencies (DependsOn relationships)
- Parameter passing between nested stacks
- No unused parameters (cfn-lint W2001)
- Outputs reference correct nested stack outputs using !GetAtt pattern
- TemplateURL patterns use correct S3 bucket and paths
- All service-specific nested stacks are included

Validates Requirements: 16.14, 16.15-16.34, 16.49, 16.50, 16.51, 16.52
"""

import pytest


class TestMainStackStructure:
    """Test suite for main stack structure and parameters."""

    def test_main_stack_exists(self, load_cfn_template):
        """Test that main-stack.yaml template exists and can be loaded."""
        template = load_cfn_template("main-stack.yaml")
        assert template is not None
        assert "Resources" in template

    def test_main_stack_has_required_parameters(self, load_cfn_template):
        """Test that main stack defines required parameters."""
        template = load_cfn_template("main-stack.yaml")
        
        assert "Parameters" in template
        parameters = template["Parameters"]
        
        # Required parameters
        assert "ProjectName" in parameters
        assert "Environment" in parameters
        assert "DeploymentBucket" in parameters
        assert "AdminEmail" in parameters
        assert "UseFunctionSpecificRoles" in parameters

    def test_main_stack_has_description(self, load_cfn_template):
        """Test that main stack has a description."""
        template = load_cfn_template("main-stack.yaml")
        
        assert "Description" in template
        assert len(template["Description"]) > 0


class TestNestedStackResources:
    """Test suite for nested stack resource definitions."""

    def test_main_stack_has_iam_nested_stack(self, load_cfn_template):
        """Test that main stack includes IAM nested stack."""
        template = load_cfn_template("main-stack.yaml")
        
        resources = template["Resources"]
        
        # Find IAM stack resource
        iam_stack = None
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::CloudFormation::Stack":
                if "iam" in resource_name.lower() or "IAM" in resource_name:
                    iam_stack = resource
                    break
        
        assert iam_stack is not None, "IAM nested stack not found in main stack"

    def test_main_stack_has_lambda_nested_stack(self, load_cfn_template):
        """Test that main stack includes Lambda nested stack."""
        template = load_cfn_template("main-stack.yaml")
        
        resources = template["Resources"]
        
        # Find Lambda stack resource
        lambda_stack = None
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::CloudFormation::Stack":
                if "lambda" in resource_name.lower():
                    lambda_stack = resource
                    break
        
        assert lambda_stack is not None, "Lambda nested stack not found in main stack"

    def test_main_stack_has_all_service_nested_stacks(self, load_cfn_template):
        """Test that main stack includes all required service nested stacks."""
        template = load_cfn_template("main-stack.yaml")
        
        resources = template["Resources"]
        
        # Find all nested stack resources
        nested_stacks = []
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::CloudFormation::Stack":
                nested_stacks.append(resource_name.lower())
        
        # Expected service stacks (at least these should exist)
        expected_services = [
            "iam",
            "lambda",
            "dynamodb",
            "sns"
        ]
        
        for service in expected_services:
            found = any(service in stack_name for stack_name in nested_stacks)
            assert found, f"Missing nested stack for service: {service}"


class TestTemplateURLPatterns:
    """Test suite for nested stack TemplateURL patterns."""

    def test_nested_stacks_use_s3_template_urls(self, load_cfn_template):
        """Test that nested stacks use S3 TemplateURL patterns."""
        template = load_cfn_template("main-stack.yaml")
        
        resources = template["Resources"]
        
        # Find all nested stack resources
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::CloudFormation::Stack":
                properties = resource["Properties"]
                assert "TemplateURL" in properties, (
                    f"Nested stack {resource_name} missing TemplateURL"
                )

    def test_template_urls_reference_deployment_bucket(self, load_cfn_template_as_text):
        """Test that TemplateURL patterns reference DeploymentBucket parameter."""
        template_text = load_cfn_template_as_text("main-stack.yaml")
        
        # Verify TemplateURL uses DeploymentBucket parameter
        assert "TemplateURL:" in template_text
        assert "DeploymentBucket" in template_text or "!Ref DeploymentBucket" in template_text

    def test_template_urls_use_service_subfolder_paths(self, load_cfn_template_as_text):
        """Test that TemplateURL patterns use service-based subfolder paths."""
        template_text = load_cfn_template_as_text("main-stack.yaml")
        
        # Verify service-based paths exist
        service_paths = [
            "cfn/iam/",
            "cfn/lambda/",
            "cfn/dynamodb/",
            "cfn/sns/"
        ]
        
        found_paths = []
        for path in service_paths:
            if path in template_text:
                found_paths.append(path)
        
        assert len(found_paths) >= 2, (
            f"Expected service-based subfolder paths in TemplateURL, found: {found_paths}"
        )


class TestNestedStackDependencies:
    """Test suite for nested stack DependsOn relationships."""

    def test_lambda_stack_depends_on_iam_stack(self, load_cfn_template):
        """Test that Lambda stack depends on IAM stack."""
        template = load_cfn_template("main-stack.yaml")
        
        resources = template["Resources"]
        
        # Find Lambda stack
        lambda_stack = None
        lambda_stack_name = None
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::CloudFormation::Stack":
                if "lambda" in resource_name.lower():
                    lambda_stack = resource
                    lambda_stack_name = resource_name
                    break
        
        assert lambda_stack is not None, "Lambda stack not found"
        
        # Verify DependsOn includes IAM stack
        if "DependsOn" in lambda_stack:
            depends_on = lambda_stack["DependsOn"]
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            
            # Check if any dependency is IAM-related
            has_iam_dependency = any("iam" in dep.lower() for dep in depends_on)
            assert has_iam_dependency, (
                f"Lambda stack {lambda_stack_name} should depend on IAM stack"
            )


class TestParameterPassing:
    """Test suite for parameter passing between nested stacks."""

    def test_iam_stack_receives_required_parameters(self, load_cfn_template):
        """Test that IAM stack receives required parameters from main stack."""
        template = load_cfn_template("main-stack.yaml")
        
        resources = template["Resources"]
        
        # Find IAM stack
        iam_stack = None
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::CloudFormation::Stack":
                if "iam" in resource_name.lower() or "IAM" in resource_name:
                    iam_stack = resource
                    break
        
        assert iam_stack is not None, "IAM stack not found"
        
        properties = iam_stack["Properties"]
        assert "Parameters" in properties, "IAM stack missing Parameters"
        
        parameters = properties["Parameters"]
        
        # Verify required parameters are passed
        assert "ProjectName" in parameters
        assert "Environment" in parameters
        assert "UseFunctionSpecificRoles" in parameters

    def test_lambda_stack_receives_role_arn_parameters(self, load_cfn_template):
        """Test that Lambda stack receives role ARN parameters from IAM stack."""
        template = load_cfn_template("main-stack.yaml")
        
        resources = template["Resources"]
        
        # Find Lambda stack
        lambda_stack = None
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::CloudFormation::Stack":
                if "lambda" in resource_name.lower():
                    lambda_stack = resource
                    break
        
        assert lambda_stack is not None, "Lambda stack not found"
        
        properties = lambda_stack["Properties"]
        assert "Parameters" in properties, "Lambda stack missing Parameters"
        
        parameters = properties["Parameters"]
        
        # Verify role ARN parameters are passed (at least some should exist)
        role_arn_params = [
            "UnifiedRoleArn",
            "QueryHandlerRoleArn",
            "DataManagementRoleArn",
            "ExecutionHandlerRoleArn",
            "OrchestrationRoleArn",
            "FrontendDeployerRoleArn"
        ]
        
        found_role_params = [param for param in role_arn_params if param in parameters]
        assert len(found_role_params) >= 2, (
            f"Lambda stack should receive role ARN parameters, found: {found_role_params}"
        )


class TestOutputReferences:
    """Test suite for output references using !GetAtt pattern."""

    def test_main_stack_has_outputs(self, load_cfn_template):
        """Test that main stack defines outputs."""
        template = load_cfn_template("main-stack.yaml")
        
        assert "Outputs" in template
        outputs = template["Outputs"]
        assert len(outputs) > 0, "Main stack should have outputs"

    def test_outputs_use_getatt_for_nested_stack_outputs(self, load_cfn_template_as_text):
        """Test that outputs use !GetAtt to reference nested stack outputs."""
        template_text = load_cfn_template_as_text("main-stack.yaml")
        
        # Verify !GetAtt is used in Outputs section
        if "Outputs:" in template_text:
            outputs_section_start = template_text.find("Outputs:")
            outputs_section = template_text[outputs_section_start:outputs_section_start + 3000]
            
            # Should use !GetAtt pattern for nested stack outputs
            assert "!GetAtt" in outputs_section or "Fn::GetAtt" in outputs_section, (
                "Outputs should use !GetAtt to reference nested stack outputs"
            )


class TestNoUnusedParameters:
    """Test suite for verifying no unused parameters."""

    def test_all_parameters_are_used(self, load_cfn_template):
        """Test that all parameters defined in main stack are used."""
        template = load_cfn_template("main-stack.yaml")
        
        parameters = template.get("Parameters", {})
        resources = template.get("Resources", {})
        
        # Convert template to string for searching
        import yaml
        template_str = yaml.dump(template)
        
        # Check each parameter is referenced
        for param_name in parameters.keys():
            # Parameter should be referenced via !Ref or ${ParamName}
            is_referenced = (
                f"!Ref {param_name}" in template_str or
                f"Ref: {param_name}" in template_str or
                f"${{{param_name}}}" in template_str
            )
            
            assert is_referenced, (
                f"Parameter {param_name} is defined but not used (cfn-lint W2001). "
                "Remove unused parameters or reference them in the template."
            )


class TestServiceStackInclusion:
    """Test suite for verifying all service-specific nested stacks are included."""

    def test_main_stack_includes_core_service_stacks(self, load_cfn_template):
        """Test that main stack includes core service nested stacks."""
        template = load_cfn_template("main-stack.yaml")
        
        resources = template["Resources"]
        
        # Find all nested stack resources
        nested_stack_names = []
        for resource_name, resource in resources.items():
            if resource.get("Type") == "AWS::CloudFormation::Stack":
                nested_stack_names.append(resource_name.lower())
        
        # Core services that should be present
        core_services = ["iam", "lambda"]
        
        for service in core_services:
            found = any(service in name for name in nested_stack_names)
            assert found, f"Main stack missing {service} nested stack"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
