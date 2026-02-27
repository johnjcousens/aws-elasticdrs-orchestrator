"""
Unit tests for EventBridge rules stack (cfn/eventbridge/rules-stack.yaml).

This module validates that the EventBridge rules stack:
- Creates all scheduled rules with correct properties
- Rule targets are correctly configured
- No duplicate rules exist across all templates
- Rule naming follows pattern
- Schedule expressions are valid
- IAM role references are correct
- Rule state (ENABLED/DISABLED) is correct
- Tags are present

Validates Requirements: 17.7
"""

import os
import pytest
from typing import Dict, Any


# =============================================================================
# EVENTBRIDGE STACK STRUCTURE TESTS
# =============================================================================

class TestEventBridgeStackStructure:
    """Test suite for EventBridge stack structure and metadata."""

    def test_template_has_correct_format_version(self, load_cfn_template):
        """Test that template has correct CloudFormation format version."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "AWSTemplateFormatVersion" in template
        assert template["AWSTemplateFormatVersion"] == "2010-09-09"

    def test_template_has_description(self, load_cfn_template):
        """Test that template has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "Description" in template
        assert "EventBridge" in template["Description"]
        assert "Scheduled Rules" in template["Description"] or "scheduled" in template["Description"].lower()

    def test_template_has_required_parameters(self, load_cfn_template):
        """Test that template defines all required parameters."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "Parameters" in template
        parameters = template["Parameters"]
        
        required_params = [
            "ProjectName",
            "Environment",
            "ExecutionHandlerFunctionArn",
            "DataManagementHandlerFunctionArn",
            "ApiHandlerFunctionArn"
        ]
        for param in required_params:
            assert param in parameters, f"Missing required parameter: {param}"

    def test_template_has_enable_parameters(self, load_cfn_template):
        """Test that template has enable/disable parameters for each rule."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        parameters = template["Parameters"]
        
        # Assert
        enable_params = [
            "EnableExecutionPolling",
            "EnableTagSync",
            "EnableStagingAccountSync",
            "EnableInventorySync",
            "EnableRecoveryInstanceSync"
        ]
        for param in enable_params:
            assert param in parameters, f"Missing enable parameter: {param}"
            assert parameters[param]["Type"] == "String"
            assert set(parameters[param]["AllowedValues"]) == {"true", "false"}

    def test_template_has_conditions(self, load_cfn_template):
        """Test that template defines conditional logic for rule creation."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "Conditions" in template
        conditions = template["Conditions"]
        
        expected_conditions = [
            "EnableExecutionPollingCondition",
            "EnableTagSyncCondition",
            "EnableStagingAccountSyncCondition",
            "EnableInventorySyncCondition",
            "EnableRecoveryInstanceSyncCondition"
        ]
        for condition in expected_conditions:
            assert condition in conditions, f"Missing condition: {condition}"

    def test_template_has_resources_section(self, load_cfn_template):
        """Test that template has Resources section with EventBridge rules."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "Resources" in template
        assert len(template["Resources"]) > 0

    def test_template_has_outputs_section(self, load_cfn_template):
        """Test that template has Outputs section for rule ARNs."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "Outputs" in template
        assert len(template["Outputs"]) > 0


# =============================================================================
# IAM ROLE TESTS
# =============================================================================

class TestEventBridgeInvokeRole:
    """Test suite for EventBridge invoke IAM role."""

    def test_eventbridge_invoke_role_exists(self, load_cfn_template):
        """Test that EventBridgeInvokeRole resource exists."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "EventBridgeInvokeRole" in template["Resources"]

    def test_eventbridge_invoke_role_has_correct_type(self, load_cfn_template):
        """Test that EventBridgeInvokeRole has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        role = template["Resources"]["EventBridgeInvokeRole"]
        
        # Assert
        assert role["Type"] == "AWS::IAM::Role"

    def test_eventbridge_invoke_role_has_correct_name_pattern(self, load_cfn_template):
        """Test that EventBridgeInvokeRole follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        role = template["Resources"]["EventBridgeInvokeRole"]
        
        # Assert
        assert "Properties" in role
        assert "RoleName" in role["Properties"]
        role_name = role["Properties"]["RoleName"]
        
        # Verify Sub function with correct pattern
        assert isinstance(role_name, dict) and "Sub" in role_name
        assert "${ProjectName}" in role_name["Sub"]
        assert "${Environment}" in role_name["Sub"]
        assert "eventbridge-invoke" in role_name["Sub"]

    def test_eventbridge_invoke_role_has_events_trust_policy(self, load_cfn_template):
        """Test that EventBridgeInvokeRole has correct EventBridge trust policy."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        role = template["Resources"]["EventBridgeInvokeRole"]
        
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
        assert "events.amazonaws.com" in statement["Principal"]["Service"]

    def test_eventbridge_invoke_role_has_lambda_invoke_policy(self, load_cfn_template):
        """Test that EventBridgeInvokeRole has Lambda invoke permissions."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        role = template["Resources"]["EventBridgeInvokeRole"]
        
        # Assert
        assert "Policies" in role["Properties"]
        policies = role["Properties"]["Policies"]
        
        policy_names = [p["PolicyName"] for p in policies]
        assert "InvokeLambda" in policy_names
        
        # Find the InvokeLambda policy
        invoke_policy = next(p for p in policies if p["PolicyName"] == "InvokeLambda")
        policy_doc = invoke_policy["PolicyDocument"]
        
        assert policy_doc["Version"] == "2012-10-17"
        statement = policy_doc["Statement"][0]
        assert statement["Effect"] == "Allow"
        assert "lambda:InvokeFunction" in statement["Action"]
        assert "Resource" in statement


# =============================================================================
# EXECUTION POLLING RULE TESTS
# =============================================================================

class TestExecutionPollingScheduleRule:
    """Test suite for Execution Polling Schedule Rule (canonical)."""

    def test_execution_polling_rule_exists(self, load_cfn_template):
        """Test that ExecutionPollingScheduleRule resource exists."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "ExecutionPollingScheduleRule" in template["Resources"]

    def test_execution_polling_rule_has_correct_type(self, load_cfn_template):
        """Test that ExecutionPollingScheduleRule has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["ExecutionPollingScheduleRule"]
        
        # Assert
        assert rule["Type"] == "AWS::Events::Rule"

    def test_execution_polling_rule_has_condition(self, load_cfn_template):
        """Test that ExecutionPollingScheduleRule has EnableExecutionPollingCondition."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["ExecutionPollingScheduleRule"]
        
        # Assert
        assert "Condition" in rule
        assert rule["Condition"] == "EnableExecutionPollingCondition"

    def test_execution_polling_rule_has_correct_name_pattern(self, load_cfn_template):
        """Test that ExecutionPollingScheduleRule follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["ExecutionPollingScheduleRule"]
        
        # Assert
        assert "Properties" in rule
        assert "Name" in rule["Properties"]
        rule_name = rule["Properties"]["Name"]
        
        # Verify Sub function with correct pattern
        assert isinstance(rule_name, dict) and "Sub" in rule_name
        assert "${ProjectName}" in rule_name["Sub"]
        assert "${Environment}" in rule_name["Sub"]
        assert "execution-polling-schedule" in rule_name["Sub"]

    def test_execution_polling_rule_has_description(self, load_cfn_template):
        """Test that ExecutionPollingScheduleRule has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["ExecutionPollingScheduleRule"]
        
        # Assert
        assert "Description" in rule["Properties"]
        description = rule["Properties"]["Description"]
        assert len(description) > 0
        assert "poll" in description.lower() or "execution" in description.lower()

    def test_execution_polling_rule_has_valid_schedule_expression(self, load_cfn_template):
        """Test that ExecutionPollingScheduleRule has valid schedule expression."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["ExecutionPollingScheduleRule"]
        
        # Assert
        assert "ScheduleExpression" in rule["Properties"]
        schedule = rule["Properties"]["ScheduleExpression"]
        
        # Should be rate(1 minute)
        assert schedule == "rate(1 minute)"

    def test_execution_polling_rule_is_enabled(self, load_cfn_template):
        """Test that ExecutionPollingScheduleRule is ENABLED."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["ExecutionPollingScheduleRule"]
        
        # Assert
        assert "State" in rule["Properties"]
        assert rule["Properties"]["State"] == "ENABLED"

    def test_execution_polling_rule_has_correct_target(self, load_cfn_template):
        """Test that ExecutionPollingScheduleRule targets ExecutionHandlerFunction."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["ExecutionPollingScheduleRule"]
        
        # Assert
        assert "Targets" in rule["Properties"]
        targets = rule["Properties"]["Targets"]
        
        assert len(targets) == 1
        target = targets[0]
        
        assert "Id" in target
        assert target["Id"] == "ExecutionPollingTarget"
        
        assert "Arn" in target
        arn = target["Arn"]
        assert isinstance(arn, dict) and "Ref" in arn
        assert arn["Ref"] == "ExecutionHandlerFunctionArn"
        
        assert "RoleArn" in target
        role_arn = target["RoleArn"]
        assert isinstance(role_arn, dict) and "GetAtt" in role_arn

    def test_execution_polling_rule_has_correct_input(self, load_cfn_template):
        """Test that ExecutionPollingScheduleRule has correct input payload."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["ExecutionPollingScheduleRule"]
        
        # Assert
        target = rule["Properties"]["Targets"][0]
        assert "Input" in target
        assert '"operation": "find"' in target["Input"]

    def test_execution_polling_rule_has_lambda_permission(self, load_cfn_template):
        """Test that ExecutionPollingSchedulePermission resource exists."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "ExecutionPollingSchedulePermission" in template["Resources"]
        permission = template["Resources"]["ExecutionPollingSchedulePermission"]
        
        assert permission["Type"] == "AWS::Lambda::Permission"
        assert permission["Properties"]["Action"] == "lambda:InvokeFunction"
        assert permission["Properties"]["Principal"] == "events.amazonaws.com"


# =============================================================================
# TAG SYNC RULE TESTS
# =============================================================================

class TestTagSyncScheduleRule:
    """Test suite for Tag Sync Schedule Rule."""

    def test_tag_sync_rule_exists(self, load_cfn_template):
        """Test that TagSyncScheduleRule resource exists."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "TagSyncScheduleRule" in template["Resources"]

    def test_tag_sync_rule_has_correct_type(self, load_cfn_template):
        """Test that TagSyncScheduleRule has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["TagSyncScheduleRule"]
        
        # Assert
        assert rule["Type"] == "AWS::Events::Rule"

    def test_tag_sync_rule_has_condition(self, load_cfn_template):
        """Test that TagSyncScheduleRule has EnableTagSyncCondition."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["TagSyncScheduleRule"]
        
        # Assert
        assert "Condition" in rule
        assert rule["Condition"] == "EnableTagSyncCondition"

    def test_tag_sync_rule_has_correct_name_pattern(self, load_cfn_template):
        """Test that TagSyncScheduleRule follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["TagSyncScheduleRule"]
        
        # Assert
        assert "Properties" in rule
        assert "Name" in rule["Properties"]
        rule_name = rule["Properties"]["Name"]
        
        # Verify Sub function with correct pattern
        assert isinstance(rule_name, dict) and "Sub" in rule_name
        assert "${ProjectName}" in rule_name["Sub"]
        assert "${Environment}" in rule_name["Sub"]
        assert "tag-sync-schedule" in rule_name["Sub"]

    def test_tag_sync_rule_has_valid_schedule_expression(self, load_cfn_template):
        """Test that TagSyncScheduleRule has valid schedule expression."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["TagSyncScheduleRule"]
        
        # Assert
        assert "ScheduleExpression" in rule["Properties"]
        schedule = rule["Properties"]["ScheduleExpression"]
        
        # Should be rate(1 hour)
        assert schedule == "rate(1 hour)"

    def test_tag_sync_rule_is_enabled(self, load_cfn_template):
        """Test that TagSyncScheduleRule is ENABLED."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["TagSyncScheduleRule"]
        
        # Assert
        assert "State" in rule["Properties"]
        assert rule["Properties"]["State"] == "ENABLED"

    def test_tag_sync_rule_has_correct_target(self, load_cfn_template):
        """Test that TagSyncScheduleRule targets ApiHandlerFunction."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["TagSyncScheduleRule"]
        
        # Assert
        assert "Targets" in rule["Properties"]
        targets = rule["Properties"]["Targets"]
        
        assert len(targets) == 1
        target = targets[0]
        
        assert target["Id"] == "TagSyncTarget"
        assert isinstance(target["Arn"], dict) and "Ref" in target["Arn"]
        assert target["Arn"]["Ref"] == "ApiHandlerFunctionArn"

    def test_tag_sync_rule_has_lambda_permission(self, load_cfn_template):
        """Test that TagSyncSchedulePermission resource exists."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "TagSyncSchedulePermission" in template["Resources"]
        permission = template["Resources"]["TagSyncSchedulePermission"]
        
        assert permission["Type"] == "AWS::Lambda::Permission"
        assert permission["Properties"]["Action"] == "lambda:InvokeFunction"


# =============================================================================
# STAGING ACCOUNT SYNC RULE TESTS
# =============================================================================

class TestStagingAccountSyncScheduleRule:
    """Test suite for Staging Account Sync Schedule Rule."""

    def test_staging_account_sync_rule_exists(self, load_cfn_template):
        """Test that StagingAccountSyncScheduleRule resource exists."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "StagingAccountSyncScheduleRule" in template["Resources"]

    def test_staging_account_sync_rule_has_correct_type(self, load_cfn_template):
        """Test that StagingAccountSyncScheduleRule has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["StagingAccountSyncScheduleRule"]
        
        # Assert
        assert rule["Type"] == "AWS::Events::Rule"

    def test_staging_account_sync_rule_has_valid_schedule_expression(self, load_cfn_template):
        """Test that StagingAccountSyncScheduleRule has valid schedule expression."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["StagingAccountSyncScheduleRule"]
        
        # Assert
        assert "ScheduleExpression" in rule["Properties"]
        schedule = rule["Properties"]["ScheduleExpression"]
        
        # Should be rate(5 minutes)
        assert schedule == "rate(5 minutes)"

    def test_staging_account_sync_rule_has_correct_target(self, load_cfn_template):
        """Test that StagingAccountSyncScheduleRule targets DataManagementHandlerFunction."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["StagingAccountSyncScheduleRule"]
        
        # Assert
        targets = rule["Properties"]["Targets"]
        assert len(targets) == 1
        target = targets[0]
        
        assert target["Id"] == "StagingAccountSyncTarget"
        assert target["Arn"]["Ref"] == "DataManagementHandlerFunctionArn"


# =============================================================================
# INVENTORY SYNC RULE TESTS
# =============================================================================

class TestInventorySyncScheduleRule:
    """Test suite for Inventory Sync Schedule Rule."""

    def test_inventory_sync_rule_exists(self, load_cfn_template):
        """Test that InventorySyncScheduleRule resource exists."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "InventorySyncScheduleRule" in template["Resources"]

    def test_inventory_sync_rule_has_correct_type(self, load_cfn_template):
        """Test that InventorySyncScheduleRule has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["InventorySyncScheduleRule"]
        
        # Assert
        assert rule["Type"] == "AWS::Events::Rule"

    def test_inventory_sync_rule_has_valid_schedule_expression(self, load_cfn_template):
        """Test that InventorySyncScheduleRule has valid schedule expression."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["InventorySyncScheduleRule"]
        
        # Assert
        assert "ScheduleExpression" in rule["Properties"]
        schedule = rule["Properties"]["ScheduleExpression"]
        
        # Should be rate(15 minutes)
        assert schedule == "rate(15 minutes)"

    def test_inventory_sync_rule_has_correct_target(self, load_cfn_template):
        """Test that InventorySyncScheduleRule targets DataManagementHandlerFunction."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["InventorySyncScheduleRule"]
        
        # Assert
        targets = rule["Properties"]["Targets"]
        assert len(targets) == 1
        target = targets[0]
        
        assert target["Id"] == "InventorySyncTarget"
        assert target["Arn"]["Ref"] == "DataManagementHandlerFunctionArn"


# =============================================================================
# RECOVERY INSTANCE SYNC RULE TESTS
# =============================================================================

class TestRecoveryInstanceSyncScheduleRule:
    """Test suite for Recovery Instance Sync Schedule Rule."""

    def test_recovery_instance_sync_rule_exists(self, load_cfn_template):
        """Test that RecoveryInstanceSyncScheduleRule resource exists."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "RecoveryInstanceSyncScheduleRule" in template["Resources"]

    def test_recovery_instance_sync_rule_has_correct_type(self, load_cfn_template):
        """Test that RecoveryInstanceSyncScheduleRule has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["RecoveryInstanceSyncScheduleRule"]
        
        # Assert
        assert rule["Type"] == "AWS::Events::Rule"

    def test_recovery_instance_sync_rule_has_valid_schedule_expression(self, load_cfn_template):
        """Test that RecoveryInstanceSyncScheduleRule has valid schedule expression."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["RecoveryInstanceSyncScheduleRule"]
        
        # Assert
        assert "ScheduleExpression" in rule["Properties"]
        schedule = rule["Properties"]["ScheduleExpression"]
        
        # Should be rate(5 minutes)
        assert schedule == "rate(5 minutes)"

    def test_recovery_instance_sync_rule_has_correct_target(self, load_cfn_template):
        """Test that RecoveryInstanceSyncScheduleRule targets DataManagementHandlerFunction."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        rule = template["Resources"]["RecoveryInstanceSyncScheduleRule"]
        
        # Assert
        targets = rule["Properties"]["Targets"]
        assert len(targets) == 1
        target = targets[0]
        
        assert target["Id"] == "RecoveryInstanceSyncTarget"
        assert target["Arn"]["Ref"] == "DataManagementHandlerFunctionArn"


# =============================================================================
# RULE NAMING CONVENTIONS TESTS
# =============================================================================

class TestEventBridgeRuleNamingConventions:
    """Test suite for EventBridge rule naming conventions."""

    def test_all_rules_follow_naming_pattern(self, load_cfn_template):
        """Test that all EventBridge rules follow naming pattern."""
        # Arrange
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        rule_names = [
            "ExecutionPollingScheduleRule",
            "TagSyncScheduleRule",
            "StagingAccountSyncScheduleRule",
            "InventorySyncScheduleRule",
            "RecoveryInstanceSyncScheduleRule"
        ]
        
        # Act & Assert
        for rule_name in rule_names:
            rule = template["Resources"][rule_name]
            rule_name_ref = rule["Properties"]["Name"]
            
            # Verify it uses Fn::Sub or !Sub
            assert isinstance(rule_name_ref, dict) and "Sub" in rule_name_ref
            assert "${ProjectName}" in rule_name_ref["Sub"]
            assert "${Environment}" in rule_name_ref["Sub"]


# =============================================================================
# SCHEDULE EXPRESSION VALIDATION TESTS
# =============================================================================

class TestScheduleExpressionValidation:
    """Test suite for schedule expression validation."""

    def test_all_schedule_expressions_are_valid(self, load_cfn_template):
        """Test that all schedule expressions use valid rate or cron syntax."""
        # Arrange
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        rules_and_schedules = {
            "ExecutionPollingScheduleRule": "rate(1 minute)",
            "TagSyncScheduleRule": "rate(1 hour)",
            "StagingAccountSyncScheduleRule": "rate(5 minutes)",
            "InventorySyncScheduleRule": "rate(15 minutes)",
            "RecoveryInstanceSyncScheduleRule": "rate(5 minutes)"
        }
        
        # Act & Assert
        for rule_name, expected_schedule in rules_and_schedules.items():
            rule = template["Resources"][rule_name]
            actual_schedule = rule["Properties"]["ScheduleExpression"]
            
            assert actual_schedule == expected_schedule, f"{rule_name} has incorrect schedule: {actual_schedule}"

    def test_schedule_expressions_use_rate_syntax(self, load_cfn_template):
        """Test that all schedule expressions use rate() syntax."""
        # Arrange
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        rule_names = [
            "ExecutionPollingScheduleRule",
            "TagSyncScheduleRule",
            "StagingAccountSyncScheduleRule",
            "InventorySyncScheduleRule",
            "RecoveryInstanceSyncScheduleRule"
        ]
        
        # Act & Assert
        for rule_name in rule_names:
            rule = template["Resources"][rule_name]
            schedule = rule["Properties"]["ScheduleExpression"]
            
            assert schedule.startswith("rate("), f"{rule_name} does not use rate() syntax"
            assert schedule.endswith(")"), f"{rule_name} has malformed rate() syntax"



# =============================================================================
# RULE STATE TESTS
# =============================================================================

class TestEventBridgeRuleState:
    """Test suite for EventBridge rule state (ENABLED/DISABLED)."""

    def test_all_rules_are_enabled(self, load_cfn_template):
        """Test that all EventBridge rules are ENABLED by default."""
        # Arrange
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        rule_names = [
            "ExecutionPollingScheduleRule",
            "TagSyncScheduleRule",
            "StagingAccountSyncScheduleRule",
            "InventorySyncScheduleRule",
            "RecoveryInstanceSyncScheduleRule"
        ]
        
        # Act & Assert
        for rule_name in rule_names:
            rule = template["Resources"][rule_name]
            assert "State" in rule["Properties"], f"{rule_name} missing State property"
            assert rule["Properties"]["State"] == "ENABLED", f"{rule_name} is not ENABLED"


# =============================================================================
# RULE TARGETS TESTS
# =============================================================================

class TestEventBridgeRuleTargets:
    """Test suite for EventBridge rule targets."""

    def test_all_rules_have_exactly_one_target(self, load_cfn_template):
        """Test that all EventBridge rules have exactly one target."""
        # Arrange
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        rule_names = [
            "ExecutionPollingScheduleRule",
            "TagSyncScheduleRule",
            "StagingAccountSyncScheduleRule",
            "InventorySyncScheduleRule",
            "RecoveryInstanceSyncScheduleRule"
        ]
        
        # Act & Assert
        for rule_name in rule_names:
            rule = template["Resources"][rule_name]
            assert "Targets" in rule["Properties"], f"{rule_name} missing Targets"
            targets = rule["Properties"]["Targets"]
            assert len(targets) == 1, f"{rule_name} should have exactly 1 target, has {len(targets)}"

    def test_all_targets_have_required_properties(self, load_cfn_template):
        """Test that all rule targets have Id, Arn, and RoleArn properties."""
        # Arrange
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        rule_names = [
            "ExecutionPollingScheduleRule",
            "TagSyncScheduleRule",
            "StagingAccountSyncScheduleRule",
            "InventorySyncScheduleRule",
            "RecoveryInstanceSyncScheduleRule"
        ]
        
        # Act & Assert
        for rule_name in rule_names:
            rule = template["Resources"][rule_name]
            target = rule["Properties"]["Targets"][0]
            
            assert "Id" in target, f"{rule_name} target missing Id"
            assert "Arn" in target, f"{rule_name} target missing Arn"
            assert "RoleArn" in target, f"{rule_name} target missing RoleArn"

    def test_all_targets_reference_eventbridge_invoke_role(self, load_cfn_template):
        """Test that all rule targets reference EventBridgeInvokeRole."""
        # Arrange
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        rule_names = [
            "ExecutionPollingScheduleRule",
            "TagSyncScheduleRule",
            "StagingAccountSyncScheduleRule",
            "InventorySyncScheduleRule",
            "RecoveryInstanceSyncScheduleRule"
        ]
        
        # Act & Assert
        for rule_name in rule_names:
            rule = template["Resources"][rule_name]
            target = rule["Properties"]["Targets"][0]
            role_arn = target["RoleArn"]
            
            # Should use GetAtt to reference EventBridgeInvokeRole.Arn
            assert isinstance(role_arn, dict), f"{rule_name} RoleArn is not a dict"
            assert "GetAtt" in role_arn or "Fn::GetAtt" in role_arn, f"{rule_name} RoleArn does not use GetAtt"



# =============================================================================
# LAMBDA PERMISSIONS TESTS
# =============================================================================

class TestLambdaPermissions:
    """Test suite for Lambda permissions for EventBridge rules."""

    def test_all_rules_have_corresponding_lambda_permissions(self, load_cfn_template):
        """Test that all EventBridge rules have corresponding Lambda permissions."""
        # Arrange
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        rules_and_permissions = {
            "ExecutionPollingScheduleRule": "ExecutionPollingSchedulePermission",
            "TagSyncScheduleRule": "TagSyncSchedulePermission",
            "StagingAccountSyncScheduleRule": "StagingAccountSyncSchedulePermission",
            "InventorySyncScheduleRule": "InventorySyncSchedulePermission",
            "RecoveryInstanceSyncScheduleRule": "RecoveryInstanceSyncSchedulePermission"
        }
        
        # Act & Assert
        for rule_name, permission_name in rules_and_permissions.items():
            assert permission_name in template["Resources"], f"Missing permission: {permission_name}"
            permission = template["Resources"][permission_name]
            
            assert permission["Type"] == "AWS::Lambda::Permission"
            assert permission["Properties"]["Action"] == "lambda:InvokeFunction"
            assert permission["Properties"]["Principal"] == "events.amazonaws.com"

    def test_lambda_permissions_have_correct_conditions(self, load_cfn_template):
        """Test that Lambda permissions have same conditions as their rules."""
        # Arrange
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        rules_and_permissions = {
            "ExecutionPollingScheduleRule": "ExecutionPollingSchedulePermission",
            "TagSyncScheduleRule": "TagSyncSchedulePermission",
            "StagingAccountSyncScheduleRule": "StagingAccountSyncSchedulePermission",
            "InventorySyncScheduleRule": "InventorySyncSchedulePermission",
            "RecoveryInstanceSyncScheduleRule": "RecoveryInstanceSyncSchedulePermission"
        }
        
        # Act & Assert
        for rule_name, permission_name in rules_and_permissions.items():
            rule = template["Resources"][rule_name]
            permission = template["Resources"][permission_name]
            
            # Both should have the same condition
            assert "Condition" in rule, f"{rule_name} missing Condition"
            assert "Condition" in permission, f"{permission_name} missing Condition"
            assert rule["Condition"] == permission["Condition"], f"Condition mismatch for {rule_name}"


# =============================================================================
# NO DUPLICATE RULES TESTS (CRITICAL)
# =============================================================================

class TestNoDuplicateRules:
    """Test suite to ensure no duplicate EventBridge rules exist across templates."""

    def test_execution_polling_rule_not_in_lambda_stack(self, load_cfn_template):
        """Test that ExecutionPollingScheduleRule does NOT exist in lambda-stack.yaml."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert - ExecutionPollingScheduleRule should NOT exist in Lambda stack
        assert "ExecutionPollingScheduleRule" not in template.get("Resources", {}), \
            "DUPLICATE FOUND: ExecutionPollingScheduleRule exists in lambda-stack.yaml (should only be in eventbridge/rules-stack.yaml)"

    def test_execution_finder_rule_not_in_lambda_stack(self, load_cfn_template):
        """Test that ExecutionFinderScheduleRule does NOT exist in lambda-stack.yaml."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        
        # Assert - ExecutionFinderScheduleRule should NOT exist (deprecated)
        assert "ExecutionFinderScheduleRule" not in template.get("Resources", {}), \
            "DEPRECATED RULE FOUND: ExecutionFinderScheduleRule exists in lambda-stack.yaml (replaced by ExecutionPollingScheduleRule)"

    def test_no_eventbridge_rules_in_lambda_stack(self, load_cfn_template):
        """Test that lambda-stack.yaml contains NO EventBridge rules."""
        # Arrange & Act
        template = load_cfn_template("lambda/functions-stack.yaml")
        resources = template.get("Resources", {})
        
        # Assert - Find any AWS::Events::Rule resources
        eventbridge_rules = [
            name for name, resource in resources.items()
            if resource.get("Type") == "AWS::Events::Rule"
        ]
        
        assert len(eventbridge_rules) == 0, \
            f"EventBridge rules found in lambda-stack.yaml: {eventbridge_rules}. All rules should be in eventbridge/rules-stack.yaml"

    def test_all_eventbridge_rules_consolidated_in_rules_stack(self, load_cfn_template):
        """Test that all EventBridge rules are consolidated in rules-stack.yaml."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        resources = template.get("Resources", {})
        
        # Assert - Count EventBridge rules
        eventbridge_rules = [
            name for name, resource in resources.items()
            if resource.get("Type") == "AWS::Events::Rule"
        ]
        
        # Should have exactly 5 rules
        assert len(eventbridge_rules) == 5, \
            f"Expected 5 EventBridge rules in rules-stack.yaml, found {len(eventbridge_rules)}: {eventbridge_rules}"
        
        expected_rules = [
            "ExecutionPollingScheduleRule",
            "TagSyncScheduleRule",
            "StagingAccountSyncScheduleRule",
            "InventorySyncScheduleRule",
            "RecoveryInstanceSyncScheduleRule"
        ]
        
        for expected_rule in expected_rules:
            assert expected_rule in eventbridge_rules, f"Missing expected rule: {expected_rule}"


# =============================================================================
# OUTPUTS TESTS
# =============================================================================

class TestEventBridgeStackOutputs:
    """Test suite for EventBridge stack outputs."""

    def test_eventbridge_invoke_role_arn_output_exists(self, load_cfn_template):
        """Test that EventBridgeInvokeRoleArn output exists."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "EventBridgeInvokeRoleArn" in template["Outputs"]
        output = template["Outputs"]["EventBridgeInvokeRoleArn"]
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_execution_polling_rule_arn_output_exists(self, load_cfn_template):
        """Test that ExecutionPollingScheduleRuleArn output exists."""
        # Arrange & Act
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "ExecutionPollingScheduleRuleArn" in template["Outputs"]
        output = template["Outputs"]["ExecutionPollingScheduleRuleArn"]
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output
        assert "Condition" in output
        assert output["Condition"] == "EnableExecutionPollingCondition"

    def test_all_rules_have_arn_outputs(self, load_cfn_template):
        """Test that all EventBridge rules have ARN outputs."""
        # Arrange
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        expected_outputs = [
            "ExecutionPollingScheduleRuleArn",
            "TagSyncScheduleRuleArn",
            "StagingAccountSyncScheduleRuleArn",
            "InventorySyncScheduleRuleArn",
            "RecoveryInstanceSyncScheduleRuleArn"
        ]
        
        # Act & Assert
        for output_name in expected_outputs:
            assert output_name in template["Outputs"], f"Missing output: {output_name}"
            output = template["Outputs"][output_name]
            
            assert "Description" in output
            assert "Value" in output
            assert "Export" in output
            assert "Condition" in output

    def test_outputs_have_correct_export_names(self, load_cfn_template):
        """Test that outputs have correct export name patterns."""
        # Arrange
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        outputs_and_exports = {
            "EventBridgeInvokeRoleArn": "eventbridge-role",
            "ExecutionPollingScheduleRuleArn": "execution-polling-rule",
            "TagSyncScheduleRuleArn": "tag-sync-rule",
            "StagingAccountSyncScheduleRuleArn": "staging-account-sync-rule",
            "InventorySyncScheduleRuleArn": "inventory-sync-rule",
            "RecoveryInstanceSyncScheduleRuleArn": "recovery-instance-sync-rule"
        }
        
        # Act & Assert
        for output_name, export_suffix in outputs_and_exports.items():
            output = template["Outputs"][output_name]
            export_name = output["Export"]["Name"]
            
            # Verify Sub function with correct pattern
            assert isinstance(export_name, dict) and "Sub" in export_name
            assert "${ProjectName}" in export_name["Sub"]
            assert "${Environment}" in export_name["Sub"]
            assert export_suffix in export_name["Sub"]


# =============================================================================
# EDGE CASES AND VALIDATION TESTS
# =============================================================================

class TestEventBridgeStackEdgeCases:
    """Test suite for edge cases and validation."""

    def test_all_rules_have_descriptions(self, load_cfn_template):
        """Test that all EventBridge rules have meaningful descriptions."""
        # Arrange
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        rule_names = [
            "ExecutionPollingScheduleRule",
            "TagSyncScheduleRule",
            "StagingAccountSyncScheduleRule",
            "InventorySyncScheduleRule",
            "RecoveryInstanceSyncScheduleRule"
        ]
        
        # Act & Assert
        for rule_name in rule_names:
            rule = template["Resources"][rule_name]
            assert "Description" in rule["Properties"], f"{rule_name} missing Description"
            description = rule["Properties"]["Description"]
            assert len(description) > 10, f"{rule_name} has too short description: {description}"

    def test_rule_target_ids_are_unique(self, load_cfn_template):
        """Test that all rule target IDs are unique."""
        # Arrange
        template = load_cfn_template("eventbridge/rules-stack.yaml")
        
        rule_names = [
            "ExecutionPollingScheduleRule",
            "TagSyncScheduleRule",
            "StagingAccountSyncScheduleRule",
            "InventorySyncScheduleRule",
            "RecoveryInstanceSyncScheduleRule"
        ]
        
        # Act
        target_ids = []
        for rule_name in rule_names:
            rule = template["Resources"][rule_name]
            target = rule["Properties"]["Targets"][0]
            target_ids.append(target["Id"])
        
        # Assert - All target IDs should be unique
        assert len(target_ids) == len(set(target_ids)), f"Duplicate target IDs found: {target_ids}"

    def test_execution_polling_rule_has_canonical_comment(self, load_cfn_template_as_text):
        """Test that ExecutionPollingScheduleRule has comment indicating it's canonical."""
        # Arrange & Act
        template_text = load_cfn_template_as_text("eventbridge/rules-stack.yaml")
        
        # Assert - Should have comment indicating this is the canonical rule
        assert "canonical" in template_text.lower(), \
            "ExecutionPollingScheduleRule should have comment indicating it's the canonical rule"
        assert "duplicate" in template_text.lower() or "replaces" in template_text.lower(), \
            "Template should mention that this replaces duplicate rules"

    def test_template_mentions_consolidation(self, load_cfn_template_as_text):
        """Test that template description mentions consolidation of EventBridge rules."""
        # Arrange & Act
        template_text = load_cfn_template_as_text("eventbridge/rules-stack.yaml")
        
        # Assert
        assert "consolidat" in template_text.lower(), \
            "Template should mention consolidation of EventBridge rules"
