"""
Unit tests for EventBridge CloudFormation template validation.

This module validates that the EventBridge stack CloudFormation template
correctly routes staging account sync operations to the data-management-handler
instead of the query-handler.

Validates Requirements:
- 11.6: EventBridge StagingAccountSyncScheduleRule targets ApiHandlerFunctionArn
- 11.7: EventBridge StagingAccountSyncSchedulePermission grants permissions to ApiHandlerFunctionArn
"""

import os
import re
import pytest


def load_eventbridge_template_as_text():
    """Load the EventBridge CloudFormation template as raw text."""
    template_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "cfn",
        "eventbridge-stack.yaml"
    )
    with open(template_path, "r") as f:
        return f.read()


def extract_resource_section(template_text, resource_name):
    """
    Extract a resource section from CloudFormation template text.
    
    Returns the YAML section for the specified resource as a string.
    """
    # Find the resource definition
    pattern = rf"^\s+{re.escape(resource_name)}:\s*$"
    lines = template_text.split("\n")
    
    start_idx = None
    for i, line in enumerate(lines):
        if re.match(pattern, line):
            start_idx = i
            break
    
    if start_idx is None:
        return None
    
    # Find the indentation level of the resource
    resource_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    
    # Extract lines until we hit another resource at the same level or end
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


class TestEventBridgeStackValidation:
    """Test suite for EventBridge CloudFormation template validation."""

    def test_staging_account_sync_rule_exists(self):
        """Test that StagingAccountSyncScheduleRule exists in template."""
        template_text = load_eventbridge_template_as_text()
        
        assert "StagingAccountSyncScheduleRule:" in template_text, (
            "StagingAccountSyncScheduleRule not found in EventBridge template"
        )

    def test_staging_account_sync_rule_targets_data_management_handler(self):
        """
        Test that StagingAccountSyncScheduleRule targets DataManagementHandlerFunctionArn.
        
        Validates Requirement 11.6: EventBridge StagingAccountSyncScheduleRule
        should invoke ApiHandlerFunctionArn (data-management-handler) instead
        of QueryHandlerFunctionArn.
        """
        template_text = load_eventbridge_template_as_text()
        resource_section = extract_resource_section(template_text, "StagingAccountSyncScheduleRule")
        
        assert resource_section is not None, (
            "StagingAccountSyncScheduleRule not found in template"
        )
        
        # Verify it references DataManagementHandlerFunctionArn
        assert "DataManagementHandlerFunctionArn" in resource_section, (
            f"StagingAccountSyncScheduleRule does not target DataManagementHandlerFunctionArn. "
            "This rule should invoke data-management-handler for write operations.\n"
            f"Resource section:\n{resource_section}"
        )
        
        # Verify it does NOT reference QueryHandlerFunctionArn
        assert "QueryHandlerFunctionArn" not in resource_section, (
            "StagingAccountSyncScheduleRule incorrectly targets QueryHandlerFunctionArn. "
            "Query handler should be read-only. Staging account sync performs write "
            "operations and should target DataManagementHandlerFunctionArn.\n"
            f"Resource section:\n{resource_section}"
        )

    def test_staging_account_sync_permission_grants_to_data_management_handler(self):
        """
        Test that StagingAccountSyncSchedulePermission grants permissions to DataManagementHandlerFunctionArn.
        
        Validates Requirement 11.7: EventBridge StagingAccountSyncSchedulePermission
        should grant lambda:InvokeFunction permission to ApiHandlerFunctionArn
        (data-management-handler).
        """
        template_text = load_eventbridge_template_as_text()
        resource_section = extract_resource_section(template_text, "StagingAccountSyncSchedulePermission")
        
        assert resource_section is not None, (
            "StagingAccountSyncSchedulePermission not found in template"
        )
        
        # Verify it references DataManagementHandlerFunctionArn
        assert "DataManagementHandlerFunctionArn" in resource_section, (
            f"StagingAccountSyncSchedulePermission does not grant permission to DataManagementHandlerFunctionArn. "
            "This permission should allow EventBridge to invoke data-management-handler.\n"
            f"Resource section:\n{resource_section}"
        )
        
        # Verify it does NOT reference QueryHandlerFunctionArn
        assert "QueryHandlerFunctionArn" not in resource_section, (
            "StagingAccountSyncSchedulePermission incorrectly grants permission to QueryHandlerFunctionArn. "
            "Query handler should be read-only. Staging account sync performs write "
            "operations and should grant permission to DataManagementHandlerFunctionArn.\n"
            f"Resource section:\n{resource_section}"
        )

    def test_staging_account_sync_rule_has_correct_input(self):
        """Test that StagingAccountSyncScheduleRule passes correct input payload."""
        template_text = load_eventbridge_template_as_text()
        resource_section = extract_resource_section(template_text, "StagingAccountSyncScheduleRule")
        
        assert resource_section is not None, (
            "StagingAccountSyncScheduleRule not found in template"
        )
        
        # Verify input contains operation: sync_staging_accounts
        assert "sync_staging_accounts" in resource_section, (
            f"StagingAccountSyncScheduleRule input does not contain 'sync_staging_accounts'.\n"
            f"Resource section:\n{resource_section}"
        )

    def test_staging_account_sync_rule_schedule_expression(self):
        """Test that StagingAccountSyncScheduleRule has correct schedule (every 5 minutes)."""
        template_text = load_eventbridge_template_as_text()
        resource_section = extract_resource_section(template_text, "StagingAccountSyncScheduleRule")
        
        assert resource_section is not None, (
            "StagingAccountSyncScheduleRule not found in template"
        )
        
        # Verify schedule is every 5 minutes
        assert "rate(5 minutes)" in resource_section, (
            f"StagingAccountSyncScheduleRule has incorrect schedule, expected 'rate(5 minutes)'.\n"
            f"Resource section:\n{resource_section}"
        )

    def test_staging_account_sync_rule_is_enabled(self):
        """Test that StagingAccountSyncScheduleRule is enabled by default."""
        template_text = load_eventbridge_template_as_text()
        resource_section = extract_resource_section(template_text, "StagingAccountSyncScheduleRule")
        
        assert resource_section is not None, (
            "StagingAccountSyncScheduleRule not found in template"
        )
        
        # Verify rule is enabled
        assert "State: ENABLED" in resource_section, (
            f"StagingAccountSyncScheduleRule state is not ENABLED.\n"
            f"Resource section:\n{resource_section}"
        )

    def test_staging_account_sync_rule_has_condition(self):
        """Test that StagingAccountSyncScheduleRule has EnableStagingAccountSyncCondition."""
        template_text = load_eventbridge_template_as_text()
        resource_section = extract_resource_section(template_text, "StagingAccountSyncScheduleRule")
        
        assert resource_section is not None, (
            "StagingAccountSyncScheduleRule not found in template"
        )
        
        # Verify condition exists
        assert "Condition: EnableStagingAccountSyncCondition" in resource_section, (
            f"StagingAccountSyncScheduleRule does not have EnableStagingAccountSyncCondition.\n"
            f"Resource section:\n{resource_section}"
        )

    def test_eventbridge_role_has_data_management_handler_permission(self):
        """Test that EventBridgeInvokeRole has permission to invoke DataManagementHandlerFunctionArn."""
        template_text = load_eventbridge_template_as_text()
        resource_section = extract_resource_section(template_text, "EventBridgeInvokeRole")
        
        assert resource_section is not None, (
            "EventBridgeInvokeRole not found in template"
        )
        
        # Verify DataManagementHandlerFunctionArn is in the role's resources
        assert "DataManagementHandlerFunctionArn" in resource_section, (
            f"EventBridgeInvokeRole does not have permission to invoke DataManagementHandlerFunctionArn.\n"
            f"Resource section:\n{resource_section}"
        )


class TestEventBridgeStackComments:
    """Test suite for EventBridge CloudFormation template comments and documentation."""

    def test_staging_account_sync_rule_has_routing_comment(self):
        """Test that StagingAccountSyncScheduleRule has comment explaining handler routing."""
        template_text = load_eventbridge_template_as_text()
        
        # Find the StagingAccountSyncScheduleRule section
        rule_section_start = template_text.find("StagingAccountSyncScheduleRule:")
        assert rule_section_start != -1, "StagingAccountSyncScheduleRule not found in template"
        
        # Get 500 characters before the rule definition (should include comments)
        section_start = max(0, rule_section_start - 500)
        section = template_text[section_start:rule_section_start + 500]
        
        # Verify comment mentions data-management-handler or write operations
        assert (
            "data-management" in section.lower() or
            "data management" in section.lower() or
            "write operation" in section.lower()
        ), (
            "StagingAccountSyncScheduleRule section should have comment explaining "
            "that it routes to data-management-handler for write operations"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
