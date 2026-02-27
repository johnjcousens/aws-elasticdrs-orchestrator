"""
Unit tests for service-specific nested stacks.

This module validates that the service-specific nested stacks:
- DynamoDB tables stack (cfn/dynamodb/tables-stack.yaml)
- S3 buckets stack (cfn/s3/buckets-stack.yaml)
- SNS topics stack (cfn/sns/topics-stack.yaml)
- Step Functions state machine stack (cfn/stepfunctions/statemachine-stack.yaml)

Each stack is tested for:
- CloudFormation template structure and format
- Resource existence and properties
- Naming patterns and conventions
- Configuration settings (encryption, versioning, etc.)
- Outputs and exports

Validates Requirements: 17.6
"""

import os
import pytest
from typing import Dict, Any


# =============================================================================
# DYNAMODB TABLES STACK TESTS
# =============================================================================

class TestDynamoDBTablesStackStructure:
    """Test suite for DynamoDB tables stack structure and metadata."""

    def test_template_has_correct_format_version(self, load_cfn_template):
        """Test that template has correct CloudFormation format version."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        
        # Assert
        assert "AWSTemplateFormatVersion" in template
        assert template["AWSTemplateFormatVersion"] == "2010-09-09"

    def test_template_has_description(self, load_cfn_template):
        """Test that template has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        
        # Assert
        assert "Description" in template
        assert "DynamoDB" in template["Description"]

    def test_template_has_required_parameters(self, load_cfn_template):
        """Test that template defines all required parameters."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        
        # Assert
        assert "Parameters" in template
        parameters = template["Parameters"]
        
        required_params = ["ProjectName", "Environment"]
        for param in required_params:
            assert param in parameters, f"Missing required parameter: {param}"

    def test_template_has_resources_section(self, load_cfn_template):
        """Test that template has Resources section with DynamoDB tables."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        
        # Assert
        assert "Resources" in template
        assert len(template["Resources"]) > 0

    def test_template_has_outputs_section(self, load_cfn_template):
        """Test that template has Outputs section for table names and ARNs."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        
        # Assert
        assert "Outputs" in template
        assert len(template["Outputs"]) > 0


class TestProtectionGroupsTable:
    """Test suite for Protection Groups DynamoDB table."""

    def test_protection_groups_table_exists(self, load_cfn_template):
        """Test that ProtectionGroupsTable resource exists."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        
        # Assert
        assert "ProtectionGroupsTable" in template["Resources"]

    def test_protection_groups_table_has_correct_type(self, load_cfn_template):
        """Test that ProtectionGroupsTable has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        table = template["Resources"]["ProtectionGroupsTable"]
        
        # Assert
        assert table["Type"] == "AWS::DynamoDB::Table"

    def test_protection_groups_table_has_correct_name_pattern(self, load_cfn_template):
        """Test that ProtectionGroupsTable follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        table = template["Resources"]["ProtectionGroupsTable"]
        
        # Assert
        assert "Properties" in table
        assert "TableName" in table["Properties"]
        table_name = table["Properties"]["TableName"]
        
        # Verify Sub function with correct pattern
        assert isinstance(table_name, dict) and "Sub" in table_name
        assert "${ProjectName}" in table_name["Sub"]
        assert "${Environment}" in table_name["Sub"]
        assert "protection-groups" in table_name["Sub"]

    def test_protection_groups_table_has_pay_per_request_billing(self, load_cfn_template):
        """Test that ProtectionGroupsTable uses PAY_PER_REQUEST billing mode."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        table = template["Resources"]["ProtectionGroupsTable"]
        
        # Assert
        assert table["Properties"]["BillingMode"] == "PAY_PER_REQUEST"

    def test_protection_groups_table_has_correct_key_schema(self, load_cfn_template):
        """Test that ProtectionGroupsTable has correct partition key."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        table = template["Resources"]["ProtectionGroupsTable"]
        
        # Assert
        key_schema = table["Properties"]["KeySchema"]
        assert len(key_schema) == 1
        assert key_schema[0]["AttributeName"] == "groupId"
        assert key_schema[0]["KeyType"] == "HASH"

    def test_protection_groups_table_has_point_in_time_recovery(self, load_cfn_template):
        """Test that ProtectionGroupsTable has point-in-time recovery enabled."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        table = template["Resources"]["ProtectionGroupsTable"]
        
        # Assert
        assert "PointInTimeRecoverySpecification" in table["Properties"]
        assert table["Properties"]["PointInTimeRecoverySpecification"]["PointInTimeRecoveryEnabled"] is True

    def test_protection_groups_table_has_encryption(self, load_cfn_template):
        """Test that ProtectionGroupsTable has encryption enabled."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        table = template["Resources"]["ProtectionGroupsTable"]
        
        # Assert
        assert "SSESpecification" in table["Properties"]
        assert table["Properties"]["SSESpecification"]["SSEEnabled"] is True

    def test_protection_groups_table_has_tags(self, load_cfn_template):
        """Test that ProtectionGroupsTable has proper tags."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        table = template["Resources"]["ProtectionGroupsTable"]
        
        # Assert
        assert "Tags" in table["Properties"]
        tags = table["Properties"]["Tags"]
        
        tag_keys = [tag["Key"] for tag in tags]
        assert "Project" in tag_keys
        assert "Environment" in tag_keys


class TestDynamoDBTablesOutputs:
    """Test suite for DynamoDB tables stack outputs."""

    def test_protection_groups_table_name_output_exists(self, load_cfn_template):
        """Test that ProtectionGroupsTableName output exists."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        
        # Assert
        assert "ProtectionGroupsTableName" in template["Outputs"]
        output = template["Outputs"]["ProtectionGroupsTableName"]
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_protection_groups_table_arn_output_exists(self, load_cfn_template):
        """Test that ProtectionGroupsTableArn output exists."""
        # Arrange & Act
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        
        # Assert
        assert "ProtectionGroupsTableArn" in template["Outputs"]
        output = template["Outputs"]["ProtectionGroupsTableArn"]
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_all_tables_have_name_and_arn_outputs(self, load_cfn_template):
        """Test that all DynamoDB tables have name and ARN outputs."""
        # Arrange
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        
        expected_tables = [
            "ProtectionGroups",
            "RecoveryPlans",
            "ExecutionHistory",
            "TargetAccounts",
            "SourceServerInventory",
            "DRSRegionStatus",
            "RecoveryInstancesCache"
        ]
        
        # Act & Assert
        for table_name in expected_tables:
            name_output = f"{table_name}TableName"
            arn_output = f"{table_name}TableArn"
            
            assert name_output in template["Outputs"], f"Missing output: {name_output}"
            assert arn_output in template["Outputs"], f"Missing output: {arn_output}"


# =============================================================================
# S3 BUCKETS STACK TESTS
# =============================================================================

class TestS3BucketsStackStructure:
    """Test suite for S3 buckets stack structure and metadata."""

    def test_template_has_correct_format_version(self, load_cfn_template):
        """Test that template has correct CloudFormation format version."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        
        # Assert
        assert "AWSTemplateFormatVersion" in template
        assert template["AWSTemplateFormatVersion"] == "2010-09-09"

    def test_template_has_description(self, load_cfn_template):
        """Test that template has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        
        # Assert
        assert "Description" in template
        assert "S3" in template["Description"]

    def test_template_has_required_parameters(self, load_cfn_template):
        """Test that template defines all required parameters."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        
        # Assert
        assert "Parameters" in template
        parameters = template["Parameters"]
        
        required_params = ["ProjectName", "Environment"]
        for param in required_params:
            assert param in parameters, f"Missing required parameter: {param}"

    def test_template_has_resources_section(self, load_cfn_template):
        """Test that template has Resources section with S3 buckets."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        
        # Assert
        assert "Resources" in template
        assert len(template["Resources"]) > 0

    def test_template_has_outputs_section(self, load_cfn_template):
        """Test that template has Outputs section for bucket names and ARNs."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        
        # Assert
        assert "Outputs" in template
        assert len(template["Outputs"]) > 0


class TestFrontendBucket:
    """Test suite for Frontend S3 bucket."""

    def test_frontend_bucket_exists(self, load_cfn_template):
        """Test that FrontendBucket resource exists."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        
        # Assert
        assert "FrontendBucket" in template["Resources"]

    def test_frontend_bucket_has_correct_type(self, load_cfn_template):
        """Test that FrontendBucket has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        bucket = template["Resources"]["FrontendBucket"]
        
        # Assert
        assert bucket["Type"] == "AWS::S3::Bucket"

    def test_frontend_bucket_has_correct_name_pattern(self, load_cfn_template):
        """Test that FrontendBucket follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        bucket = template["Resources"]["FrontendBucket"]
        
        # Assert
        assert "Properties" in bucket
        assert "BucketName" in bucket["Properties"]
        bucket_name = bucket["Properties"]["BucketName"]
        
        # Verify Sub function with correct pattern
        assert isinstance(bucket_name, dict) and "Sub" in bucket_name
        assert "${ProjectName}" in bucket_name["Sub"]
        assert "${Environment}" in bucket_name["Sub"]
        assert "fe" in bucket_name["Sub"]

    def test_frontend_bucket_has_versioning_enabled(self, load_cfn_template):
        """Test that FrontendBucket has versioning enabled."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        bucket = template["Resources"]["FrontendBucket"]
        
        # Assert
        assert "VersioningConfiguration" in bucket["Properties"]
        assert bucket["Properties"]["VersioningConfiguration"]["Status"] == "Enabled"

    def test_frontend_bucket_has_encryption(self, load_cfn_template):
        """Test that FrontendBucket has encryption enabled."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        bucket = template["Resources"]["FrontendBucket"]
        
        # Assert
        assert "BucketEncryption" in bucket["Properties"]
        encryption_config = bucket["Properties"]["BucketEncryption"]
        assert "ServerSideEncryptionConfiguration" in encryption_config
        assert len(encryption_config["ServerSideEncryptionConfiguration"]) > 0
        assert encryption_config["ServerSideEncryptionConfiguration"][0]["ServerSideEncryptionByDefault"]["SSEAlgorithm"] == "AES256"

    def test_frontend_bucket_has_public_access_block(self, load_cfn_template):
        """Test that FrontendBucket has public access blocked."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        bucket = template["Resources"]["FrontendBucket"]
        
        # Assert
        assert "PublicAccessBlockConfiguration" in bucket["Properties"]
        public_access = bucket["Properties"]["PublicAccessBlockConfiguration"]
        
        assert public_access["BlockPublicAcls"] is True
        assert public_access["BlockPublicPolicy"] is True
        assert public_access["IgnorePublicAcls"] is True
        assert public_access["RestrictPublicBuckets"] is True

    def test_frontend_bucket_has_lifecycle_policies(self, load_cfn_template):
        """Test that FrontendBucket has lifecycle policies configured."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        bucket = template["Resources"]["FrontendBucket"]
        
        # Assert
        assert "LifecycleConfiguration" in bucket["Properties"]
        lifecycle = bucket["Properties"]["LifecycleConfiguration"]
        assert "Rules" in lifecycle
        assert len(lifecycle["Rules"]) > 0

    def test_frontend_bucket_has_tags(self, load_cfn_template):
        """Test that FrontendBucket has proper tags."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        bucket = template["Resources"]["FrontendBucket"]
        
        # Assert
        assert "Tags" in bucket["Properties"]
        tags = bucket["Properties"]["Tags"]
        
        tag_keys = [tag["Key"] for tag in tags]
        assert "Project" in tag_keys
        assert "Environment" in tag_keys


class TestS3BucketsOutputs:
    """Test suite for S3 buckets stack outputs."""

    def test_frontend_bucket_name_output_exists(self, load_cfn_template):
        """Test that FrontendBucketName output exists."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        
        # Assert
        assert "FrontendBucketName" in template["Outputs"]
        output = template["Outputs"]["FrontendBucketName"]
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_frontend_bucket_arn_output_exists(self, load_cfn_template):
        """Test that FrontendBucketArn output exists."""
        # Arrange & Act
        template = load_cfn_template("s3/buckets-stack.yaml")
        
        # Assert
        assert "FrontendBucketArn" in template["Outputs"]
        output = template["Outputs"]["FrontendBucketArn"]
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output


# =============================================================================
# SNS TOPICS STACK TESTS
# =============================================================================

class TestSNSTopicsStackStructure:
    """Test suite for SNS topics stack structure and metadata."""

    def test_template_has_correct_format_version(self, load_cfn_template):
        """Test that template has correct CloudFormation format version."""
        # Arrange & Act
        template = load_cfn_template("sns/topics-stack.yaml")
        
        # Assert
        assert "AWSTemplateFormatVersion" in template
        assert template["AWSTemplateFormatVersion"] == "2010-09-09"

    def test_template_has_description(self, load_cfn_template):
        """Test that template has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("sns/topics-stack.yaml")
        
        # Assert
        assert "Description" in template
        assert "SNS" in template["Description"]

    def test_template_has_required_parameters(self, load_cfn_template):
        """Test that template defines all required parameters."""
        # Arrange & Act
        template = load_cfn_template("sns/topics-stack.yaml")
        
        # Assert
        assert "Parameters" in template
        parameters = template["Parameters"]
        
        required_params = ["ProjectName", "Environment", "AdminEmail"]
        for param in required_params:
            assert param in parameters, f"Missing required parameter: {param}"

    def test_template_has_resources_section(self, load_cfn_template):
        """Test that template has Resources section with SNS topics."""
        # Arrange & Act
        template = load_cfn_template("sns/topics-stack.yaml")
        
        # Assert
        assert "Resources" in template
        assert len(template["Resources"]) > 0

    def test_template_has_outputs_section(self, load_cfn_template):
        """Test that template has Outputs section for topic ARNs."""
        # Arrange & Act
        template = load_cfn_template("sns/topics-stack.yaml")
        
        # Assert
        assert "Outputs" in template
        assert len(template["Outputs"]) > 0


class TestExecutionNotificationsTopic:
    """Test suite for Execution Notifications SNS topic."""

    def test_execution_notifications_topic_exists(self, load_cfn_template):
        """Test that ExecutionNotificationsTopic resource exists."""
        # Arrange & Act
        template = load_cfn_template("sns/topics-stack.yaml")
        
        # Assert
        assert "ExecutionNotificationsTopic" in template["Resources"]

    def test_execution_notifications_topic_has_correct_type(self, load_cfn_template):
        """Test that ExecutionNotificationsTopic has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("sns/topics-stack.yaml")
        topic = template["Resources"]["ExecutionNotificationsTopic"]
        
        # Assert
        assert topic["Type"] == "AWS::SNS::Topic"

    def test_execution_notifications_topic_has_correct_name_pattern(self, load_cfn_template):
        """Test that ExecutionNotificationsTopic follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("sns/topics-stack.yaml")
        topic = template["Resources"]["ExecutionNotificationsTopic"]
        
        # Assert
        assert "Properties" in topic
        assert "TopicName" in topic["Properties"]
        topic_name = topic["Properties"]["TopicName"]
        
        # Verify Sub function with correct pattern
        assert isinstance(topic_name, dict) and "Sub" in topic_name
        assert "${ProjectName}" in topic_name["Sub"]
        assert "${Environment}" in topic_name["Sub"]
        assert "execution-notifications" in topic_name["Sub"]

    def test_execution_notifications_topic_has_display_name(self, load_cfn_template):
        """Test that ExecutionNotificationsTopic has display name."""
        # Arrange & Act
        template = load_cfn_template("sns/topics-stack.yaml")
        topic = template["Resources"]["ExecutionNotificationsTopic"]
        
        # Assert
        assert "DisplayName" in topic["Properties"]
        assert len(topic["Properties"]["DisplayName"]) > 0

    def test_execution_notifications_topic_has_encryption(self, load_cfn_template):
        """Test that ExecutionNotificationsTopic has encryption enabled."""
        # Arrange & Act
        template = load_cfn_template("sns/topics-stack.yaml")
        topic = template["Resources"]["ExecutionNotificationsTopic"]
        
        # Assert
        assert "KmsMasterKeyId" in topic["Properties"]
        assert topic["Properties"]["KmsMasterKeyId"] == "alias/aws/sns"

    def test_execution_notifications_topic_has_subscription(self, load_cfn_template):
        """Test that ExecutionNotificationsTopic has email subscription."""
        # Arrange & Act
        template = load_cfn_template("sns/topics-stack.yaml")
        
        # Assert
        assert "ExecutionNotificationsSubscription" in template["Resources"]
        subscription = template["Resources"]["ExecutionNotificationsSubscription"]
        
        assert subscription["Type"] == "AWS::SNS::Subscription"
        assert subscription["Properties"]["Protocol"] == "email"


class TestSNSTopicsOutputs:
    """Test suite for SNS topics stack outputs."""

    def test_execution_notifications_topic_arn_output_exists(self, load_cfn_template):
        """Test that ExecutionNotificationsTopicArn output exists."""
        # Arrange & Act
        template = load_cfn_template("sns/topics-stack.yaml")
        
        # Assert
        assert "ExecutionNotificationsTopicArn" in template["Outputs"]
        output = template["Outputs"]["ExecutionNotificationsTopicArn"]
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_all_topics_have_arn_outputs(self, load_cfn_template):
        """Test that all SNS topics have ARN outputs."""
        # Arrange
        template = load_cfn_template("sns/topics-stack.yaml")
        
        expected_topics = [
            "ExecutionNotifications",
            "DRSOperationalAlerts",
            "ExecutionPause"
        ]
        
        # Act & Assert
        for topic_name in expected_topics:
            arn_output = f"{topic_name}TopicArn"
            assert arn_output in template["Outputs"], f"Missing output: {arn_output}"


# =============================================================================
# STEP FUNCTIONS STACK TESTS
# =============================================================================

class TestStepFunctionsStackStructure:
    """Test suite for Step Functions stack structure and metadata."""

    def test_template_has_correct_format_version(self, load_cfn_template):
        """Test that template has correct CloudFormation format version."""
        # Arrange & Act
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        
        # Assert
        assert "AWSTemplateFormatVersion" in template
        assert template["AWSTemplateFormatVersion"] == "2010-09-09"

    def test_template_has_description(self, load_cfn_template):
        """Test that template has meaningful description."""
        # Arrange & Act
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        
        # Assert
        assert "Description" in template
        assert "State Machine" in template["Description"] or "Step Functions" in template["Description"]

    def test_template_has_required_parameters(self, load_cfn_template):
        """Test that template defines all required parameters."""
        # Arrange & Act
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        
        # Assert
        assert "Parameters" in template
        parameters = template["Parameters"]
        
        required_params = ["ProjectName", "Environment", "OrchestrationFunctionArn", "ExecutionHandlerArn", "OrchestrationRoleArn"]
        for param in required_params:
            assert param in parameters, f"Missing required parameter: {param}"

    def test_template_has_resources_section(self, load_cfn_template):
        """Test that template has Resources section with state machine."""
        # Arrange & Act
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        
        # Assert
        assert "Resources" in template
        assert len(template["Resources"]) > 0

    def test_template_has_outputs_section(self, load_cfn_template):
        """Test that template has Outputs section for state machine ARN."""
        # Arrange & Act
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        
        # Assert
        assert "Outputs" in template
        assert len(template["Outputs"]) > 0


class TestDRSOrchestrationStateMachine:
    """Test suite for DRS Orchestration State Machine."""

    def test_state_machine_exists(self, load_cfn_template):
        """Test that DRSOrchestrationStateMachine resource exists."""
        # Arrange & Act
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        
        # Assert
        assert "DRSOrchestrationStateMachine" in template["Resources"]

    def test_state_machine_has_correct_type(self, load_cfn_template):
        """Test that DRSOrchestrationStateMachine has correct resource type."""
        # Arrange & Act
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        state_machine = template["Resources"]["DRSOrchestrationStateMachine"]
        
        # Assert
        assert state_machine["Type"] == "AWS::StepFunctions::StateMachine"

    def test_state_machine_has_correct_name_pattern(self, load_cfn_template):
        """Test that DRSOrchestrationStateMachine follows naming pattern."""
        # Arrange & Act
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        state_machine = template["Resources"]["DRSOrchestrationStateMachine"]
        
        # Assert
        assert "Properties" in state_machine
        assert "StateMachineName" in state_machine["Properties"]
        state_machine_name = state_machine["Properties"]["StateMachineName"]
        
        # Verify Sub function with correct pattern
        assert isinstance(state_machine_name, dict) and "Sub" in state_machine_name
        assert "${ProjectName}" in state_machine_name["Sub"]
        assert "${Environment}" in state_machine_name["Sub"]
        assert "orchestration" in state_machine_name["Sub"]

    def test_state_machine_has_role_arn(self, load_cfn_template):
        """Test that DRSOrchestrationStateMachine has IAM role ARN."""
        # Arrange & Act
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        state_machine = template["Resources"]["DRSOrchestrationStateMachine"]
        
        # Assert
        assert "RoleArn" in state_machine["Properties"]
        role_arn = state_machine["Properties"]["RoleArn"]
        
        # Should reference OrchestrationRoleArn parameter
        assert isinstance(role_arn, dict) and "Ref" in role_arn
        assert role_arn["Ref"] == "OrchestrationRoleArn"

    def test_state_machine_has_definition(self, load_cfn_template):
        """Test that DRSOrchestrationStateMachine has state machine definition."""
        # Arrange & Act
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        state_machine = template["Resources"]["DRSOrchestrationStateMachine"]
        
        # Assert
        assert "Definition" in state_machine["Properties"]
        definition = state_machine["Properties"]["Definition"]
        
        # Verify it's a valid state machine definition
        assert "StartAt" in definition
        assert "States" in definition
        assert len(definition["States"]) > 0

    def test_state_machine_has_tags(self, load_cfn_template):
        """Test that DRSOrchestrationStateMachine has proper tags."""
        # Arrange & Act
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        state_machine = template["Resources"]["DRSOrchestrationStateMachine"]
        
        # Assert
        assert "Tags" in state_machine["Properties"]
        tags = state_machine["Properties"]["Tags"]
        
        tag_keys = [tag["Key"] for tag in tags]
        assert "Project" in tag_keys
        assert "Environment" in tag_keys


class TestStepFunctionsOutputs:
    """Test suite for Step Functions stack outputs."""

    def test_state_machine_arn_output_exists(self, load_cfn_template):
        """Test that StateMachineArn output exists."""
        # Arrange & Act
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        
        # Assert
        assert "StateMachineArn" in template["Outputs"]
        output = template["Outputs"]["StateMachineArn"]
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output

    def test_state_machine_name_output_exists(self, load_cfn_template):
        """Test that StateMachineName output exists."""
        # Arrange & Act
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        
        # Assert
        assert "StateMachineName" in template["Outputs"]
        output = template["Outputs"]["StateMachineName"]
        assert "Description" in output
        assert "Value" in output
        assert "Export" in output
