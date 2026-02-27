"""
Unit tests for CloudFormation DeletionPolicy attributes.

Tests verify that all CloudFormation resources have explicit DeletionPolicy
attributes to prevent orphaned resources during stack deletion.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

import pytest


def load_template_resources(template_path: str) -> Dict[str, Dict]:
    """
    Load CloudFormation template and extract resources with DeletionPolicy.

    Args:
        template_path: Path to CloudFormation template file

    Returns:
        Dictionary mapping resource logical IDs to resource metadata
    """
    resources = {}

    with open(template_path, "r") as f:
        content = f.read()

    # Find Resources section
    resources_match = re.search(r"^Resources:\s*$", content, re.MULTILINE)
    if not resources_match:
        return {}

    # Extract resource definitions
    lines = content[resources_match.end() :].split("\n")
    current_resource = None
    current_type = None
    current_deletion_policy = None

    for line in lines:
        # Stop at next top-level section
        if line and not line[0].isspace() and line.strip().endswith(":"):
            break

        # Resource name (2 spaces indent)
        resource_match = re.match(r"^  (\w+):\s*$", line)
        if resource_match:
            # Save previous resource
            if current_resource:
                resources[current_resource] = {
                    "Type": current_type or "Unknown",
                    "DeletionPolicy": current_deletion_policy or "MISSING",
                }

            current_resource = resource_match.group(1)
            current_type = None
            current_deletion_policy = None
            continue

        # Type property
        type_match = re.match(r"^\s+Type:\s*(.+)$", line)
        if type_match and current_resource:
            current_type = type_match.group(1).strip()
            continue

        # DeletionPolicy property
        deletion_match = re.match(r"^\s+DeletionPolicy:\s*(.+)$", line)
        if deletion_match and current_resource:
            current_deletion_policy = deletion_match.group(1).strip()
            continue

    # Save last resource
    if current_resource:
        resources[current_resource] = {
            "Type": current_type or "Unknown",
            "DeletionPolicy": current_deletion_policy or "MISSING",
        }

    return resources


def find_all_templates(base_dir: str = "cfn") -> List[str]:
    """Find all CloudFormation template files."""
    templates = []

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith((".yaml", ".yml")):
                templates.append(os.path.join(root, file))

    return sorted(templates)


class TestDeletionPolicies:
    """Test suite for CloudFormation DeletionPolicy attributes."""

    def test_all_templates_have_resources_with_deletion_policy(self):
        """Test that all CloudFormation templates have DeletionPolicy on all resources."""
        templates = find_all_templates()

        assert len(templates) > 0, "No CloudFormation templates found"

        missing_policies = []

        for template_path in templates:
            resources = load_template_resources(template_path)

            for logical_id, resource_data in resources.items():
                if resource_data["DeletionPolicy"] == "MISSING":
                    missing_policies.append(
                        (template_path, logical_id, resource_data["Type"])
                    )

        if missing_policies:
            error_msg = "Resources missing DeletionPolicy:\n"
            for template, logical_id, resource_type in missing_policies:
                error_msg += f"  - {template}: {logical_id} ({resource_type})\n"
            pytest.fail(error_msg)

    def test_iam_roles_stack_has_deletion_policy(self):
        """Test that IAM roles stack has DeletionPolicy on all roles."""
        template_path = "cfn/iam/roles-stack.yaml"

        if not os.path.exists(template_path):
            pytest.skip(f"Template not found: {template_path}")

        resources = load_template_resources(template_path)

        # Check specific IAM roles
        expected_roles = [
            "UnifiedOrchestrationRole",
            "QueryHandlerRole",
            "DataManagementRole",
            "ExecutionHandlerRole",
            "OrchestrationRole",
            "FrontendDeployerRole",
        ]

        for role_name in expected_roles:
            if role_name in resources:
                assert (
                    resources[role_name]["DeletionPolicy"] != "MISSING"
                ), f"IAM role {role_name} missing DeletionPolicy"

    def test_lambda_functions_stack_has_deletion_policy(self):
        """Test that Lambda functions stack has DeletionPolicy on all functions."""
        template_path = "cfn/lambda/functions-stack.yaml"

        if not os.path.exists(template_path):
            pytest.skip(f"Template not found: {template_path}")

        resources = load_template_resources(template_path)

        # Check specific Lambda functions
        expected_functions = [
            "QueryHandlerFunction",
            "DataManagementHandlerFunction",
            "ExecutionHandlerFunction",
            "DrOrchestrationStepFunctionFunction",
            "FrontendDeployerFunction",
        ]

        for function_name in expected_functions:
            if function_name in resources:
                assert (
                    resources[function_name]["DeletionPolicy"] != "MISSING"
                ), f"Lambda function {function_name} missing DeletionPolicy"

    def test_dynamodb_tables_stack_has_deletion_policy(self):
        """Test that DynamoDB tables stack has DeletionPolicy on all tables."""
        template_path = "cfn/dynamodb/tables-stack.yaml"

        if not os.path.exists(template_path):
            pytest.skip(f"Template not found: {template_path}")

        resources = load_template_resources(template_path)

        # Check for DynamoDB tables
        for logical_id, resource_data in resources.items():
            if "DynamoDB::Table" in resource_data["Type"]:
                assert (
                    resource_data["DeletionPolicy"] != "MISSING"
                ), f"DynamoDB table {logical_id} missing DeletionPolicy"

    def test_s3_buckets_stack_has_deletion_policy(self):
        """Test that S3 buckets stack has DeletionPolicy on all buckets."""
        template_path = "cfn/s3/buckets-stack.yaml"

        if not os.path.exists(template_path):
            pytest.skip(f"Template not found: {template_path}")

        resources = load_template_resources(template_path)

        # Check for S3 buckets
        for logical_id, resource_data in resources.items():
            if "S3::Bucket" in resource_data["Type"]:
                assert (
                    resource_data["DeletionPolicy"] != "MISSING"
                ), f"S3 bucket {logical_id} missing DeletionPolicy"

    def test_cloudfront_distribution_has_deletion_policy(self):
        """Test that CloudFront distribution has DeletionPolicy."""
        template_path = "cfn/cloudfront/distribution-stack.yaml"

        if not os.path.exists(template_path):
            pytest.skip(f"Template not found: {template_path}")

        resources = load_template_resources(template_path)

        # Check for CloudFront distributions
        for logical_id, resource_data in resources.items():
            if "CloudFront::Distribution" in resource_data["Type"]:
                assert (
                    resource_data["DeletionPolicy"] != "MISSING"
                ), f"CloudFront distribution {logical_id} missing DeletionPolicy"

    def test_cognito_resources_have_deletion_policy(self):
        """Test that Cognito resources have DeletionPolicy."""
        template_path = "cfn/cognito/auth-stack.yaml"

        if not os.path.exists(template_path):
            pytest.skip(f"Template not found: {template_path}")

        resources = load_template_resources(template_path)

        # Check for Cognito resources
        cognito_types = [
            "Cognito::UserPool",
            "Cognito::IdentityPool",
            "Cognito::UserPoolClient",
        ]

        for logical_id, resource_data in resources.items():
            if any(
                cognito_type in resource_data["Type"] for cognito_type in cognito_types
            ):
                assert (
                    resource_data["DeletionPolicy"] != "MISSING"
                ), f"Cognito resource {logical_id} missing DeletionPolicy"

    def test_api_gateway_resources_have_deletion_policy(self):
        """Test that API Gateway resources have DeletionPolicy."""
        api_templates = [
            "cfn/apigateway/auth-stack.yaml",
            "cfn/apigateway/core-stack.yaml",
            "cfn/apigateway/resources-stack.yaml",
            "cfn/apigateway/core-methods-stack.yaml",
            "cfn/apigateway/infrastructure-methods-stack.yaml",
            "cfn/apigateway/operations-methods-stack.yaml",
            "cfn/apigateway/deployment-stack.yaml",
        ]

        for template_path in api_templates:
            if not os.path.exists(template_path):
                continue

            resources = load_template_resources(template_path)

            for logical_id, resource_data in resources.items():
                if "ApiGateway::" in resource_data["Type"]:
                    assert (
                        resource_data["DeletionPolicy"] != "MISSING"
                    ), f"API Gateway resource {logical_id} in {template_path} missing DeletionPolicy"

    def test_deletion_policy_values_are_valid(self):
        """Test that DeletionPolicy values are valid (Delete, Retain, or Snapshot)."""
        templates = find_all_templates()
        valid_policies = ["Delete", "Retain", "Snapshot"]

        invalid_policies = []

        for template_path in templates:
            resources = load_template_resources(template_path)

            for logical_id, resource_data in resources.items():
                deletion_policy = resource_data["DeletionPolicy"]
                if (
                    deletion_policy != "MISSING"
                    and deletion_policy not in valid_policies
                ):
                    invalid_policies.append(
                        (template_path, logical_id, deletion_policy)
                    )

        if invalid_policies:
            error_msg = "Resources with invalid DeletionPolicy values:\n"
            for template, logical_id, policy in invalid_policies:
                error_msg += f"  - {template}: {logical_id} has '{policy}' (must be Delete, Retain, or Snapshot)\n"
            pytest.fail(error_msg)

    def test_cfn_lint_config_enforces_deletion_policy(self):
        """Test that cfn-lint configuration enforces DeletionPolicy."""
        config_path = ".cfnlintrc.yaml"

        assert os.path.exists(config_path), "cfn-lint config not found"

        with open(config_path, "r") as f:
            config_content = f.read()

        # Check that W3011 rule is configured
        assert (
            "W3011" in config_content
        ), "W3011 rule not found in cfn-lint config"

        # Check that strict mode is enabled for W3011
        assert (
            "strict: true" in config_content
        ), "W3011 strict mode not enabled in cfn-lint config"
