"""
Property-based tests for CloudFormation DeletionPolicy completeness.

**Property 22: Deletion Policy Completeness**

For any CloudFormation resource in any template, the resource MUST have an
explicit DeletionPolicy attribute (Delete, Retain, or Snapshot).

This property validates Requirements 17.1-17.13 by ensuring no resources
are missing DeletionPolicy attributes, which would cause orphaned resources
during stack deletion.

**Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.8,
17.9, 17.10, 17.11, 17.12, 17.13**
"""

import os
import re
from typing import Dict, List

import pytest
from hypothesis import given, settings, strategies as st


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


# Strategy: Generate random template paths from actual templates
@st.composite
def template_path_strategy(draw):
    """Generate a random CloudFormation template path."""
    templates = find_all_templates()
    if not templates:
        pytest.skip("No CloudFormation templates found")
    return draw(st.sampled_from(templates))


# Strategy: Generate random resource types
@st.composite
def resource_type_strategy(draw):
    """Generate a random CloudFormation resource type."""
    resource_types = [
        "AWS::IAM::Role",
        "AWS::Lambda::Function",
        "AWS::DynamoDB::Table",
        "AWS::S3::Bucket",
        "AWS::CloudFront::Distribution",
        "AWS::Cognito::UserPool",
        "AWS::Cognito::IdentityPool",
        "AWS::ApiGateway::RestApi",
        "AWS::ApiGateway::Resource",
        "AWS::ApiGateway::Method",
        "AWS::SNS::Topic",
        "AWS::StepFunctions::StateMachine",
        "AWS::Events::Rule",
        "AWS::CloudWatch::Alarm",
        "AWS::Logs::LogGroup",
        "AWS::WAFv2::WebACL",
    ]
    return draw(st.sampled_from(resource_types))


class TestDeletionPolicyCompleteness:
    """
    Property-based tests for DeletionPolicy completeness.

    **Property 22: Deletion Policy Completeness**

    For any CloudFormation resource in any template, the resource MUST have
    an explicit DeletionPolicy attribute.
    """

    @given(template_path=template_path_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_all_resources_have_deletion_policy(self, template_path):
        """
        **Property 22: Deletion Policy Completeness**

        For any CloudFormation template, ALL resources MUST have an explicit
        DeletionPolicy attribute (Delete, Retain, or Snapshot).

        This property ensures no resources are missing DeletionPolicy, which
        would cause orphaned resources during stack deletion.

        **Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7,
        17.8, 17.9, 17.10, 17.11, 17.12, 17.13**
        """
        resources = load_template_resources(template_path)

        # Property: Every resource must have DeletionPolicy
        for logical_id, resource_data in resources.items():
            deletion_policy = resource_data["DeletionPolicy"]

            assert deletion_policy != "MISSING", (
                f"Resource {logical_id} in {template_path} is missing "
                f"DeletionPolicy attribute. Type: {resource_data['Type']}"
            )

    @given(
        template_path=template_path_strategy(),
        resource_type=resource_type_strategy(),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_specific_resource_types_have_deletion_policy(
        self, template_path, resource_type
    ):
        """
        **Property 22: Deletion Policy Completeness (Resource Type Specific)**

        For any CloudFormation template and any resource type, if a resource
        of that type exists in the template, it MUST have an explicit
        DeletionPolicy attribute.

        This property validates that specific resource types (IAM roles,
        Lambda functions, DynamoDB tables, S3 buckets, etc.) all have
        DeletionPolicy attributes.

        **Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7,
        17.8, 17.9, 17.10, 17.11, 17.12, 17.13**
        """
        resources = load_template_resources(template_path)

        # Property: If resource type exists, it must have DeletionPolicy
        for logical_id, resource_data in resources.items():
            if resource_type in resource_data["Type"]:
                deletion_policy = resource_data["DeletionPolicy"]

                assert deletion_policy != "MISSING", (
                    f"Resource {logical_id} of type {resource_type} in "
                    f"{template_path} is missing DeletionPolicy attribute"
                )

    @given(template_path=template_path_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_deletion_policy_values_are_valid(self, template_path):
        """
        **Property 22: Deletion Policy Value Validity**

        For any CloudFormation resource with a DeletionPolicy attribute, the
        value MUST be one of: Delete, Retain, or Snapshot.

        This property ensures that DeletionPolicy values are valid
        CloudFormation values.

        **Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7,
        17.8, 17.9, 17.10, 17.11, 17.12, 17.13**
        """
        resources = load_template_resources(template_path)
        valid_policies = ["Delete", "Retain", "Snapshot"]

        # Property: DeletionPolicy value must be valid
        for logical_id, resource_data in resources.items():
            deletion_policy = resource_data["DeletionPolicy"]

            if deletion_policy != "MISSING":
                assert deletion_policy in valid_policies, (
                    f"Resource {logical_id} in {template_path} has invalid "
                    f"DeletionPolicy value: {deletion_policy}. Must be one "
                    f"of: {', '.join(valid_policies)}"
                )

    @given(template_path=template_path_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_no_template_has_missing_deletion_policies(
        self, template_path
    ):
        """
        **Property 22: Template-Level Completeness**

        For any CloudFormation template, the count of resources missing
        DeletionPolicy MUST be zero.

        This property validates that entire templates are complete with
        respect to DeletionPolicy attributes.

        **Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7,
        17.8, 17.9, 17.10, 17.11, 17.12, 17.13**
        """
        resources = load_template_resources(template_path)

        # Property: Count of missing DeletionPolicy must be zero
        missing_count = sum(
            1
            for resource_data in resources.values()
            if resource_data["DeletionPolicy"] == "MISSING"
        )

        assert missing_count == 0, (
            f"Template {template_path} has {missing_count} resources "
            f"missing DeletionPolicy attributes"
        )

    def test_property_all_templates_collectively_complete(self):
        """
        **Property 22: Collective Completeness**

        For all CloudFormation templates in the project, the total count of
        resources missing DeletionPolicy MUST be zero.

        This property validates that the entire project is complete with
        respect to DeletionPolicy attributes.

        **Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7,
        17.8, 17.9, 17.10, 17.11, 17.12, 17.13**
        """
        templates = find_all_templates()
        total_missing = 0
        missing_details = []

        for template_path in templates:
            resources = load_template_resources(template_path)

            for logical_id, resource_data in resources.items():
                if resource_data["DeletionPolicy"] == "MISSING":
                    total_missing += 1
                    missing_details.append(
                        (template_path, logical_id, resource_data["Type"])
                    )

        if total_missing > 0:
            error_msg = (
                f"Found {total_missing} resources missing DeletionPolicy "
                f"across all templates:\n"
            )
            for template, logical_id, resource_type in missing_details[:10]:
                error_msg += f"  - {template}: {logical_id} ({resource_type})\n"
            if len(missing_details) > 10:
                error_msg += f"  ... and {len(missing_details) - 10} more\n"
            pytest.fail(error_msg)

        # Property: Total missing count must be zero
        assert total_missing == 0, (
            f"Project has {total_missing} resources missing DeletionPolicy"
        )
