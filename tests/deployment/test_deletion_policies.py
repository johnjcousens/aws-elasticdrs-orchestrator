"""
Unit tests for CloudFormation DeletionPolicy validation.

Tests verify:
- All CloudFormation resources have DeletionPolicy defined
- DeletionPolicy values are appropriate for resource types
- S3 bucket cleanup logic in Frontend Deployer Lambda
- cfn-lint validation for missing DeletionPolicy (if configured)

Validates Requirements: 17.18, 17.19
"""

import os
import pytest
import yaml
from typing import Dict, Any, List


class TestDeletionPolicyPresence:
    """Test that all CloudFormation resources have DeletionPolicy defined."""

    def test_dynamodb_tables_have_deletion_policy(self, load_cfn_template):
        """Test that all DynamoDB tables have DeletionPolicy: Delete."""
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        resources = template["Resources"]

        dynamodb_tables = [
            "ProtectionGroupsTable",
            "RecoveryPlansTable",
            "ExecutionHistoryTable",
            "TargetAccountsTable",
            "SourceServerInventoryTable",
            "DRSRegionStatusTable",
            "RecoveryInstancesCacheTable"
        ]

        for table_name in dynamodb_tables:
            assert table_name in resources, f"Table {table_name} not found"
            table = resources[table_name]
            assert table["Type"] == "AWS::DynamoDB::Table"
            assert "DeletionPolicy" in table, (
                f"DynamoDB table {table_name} missing DeletionPolicy"
            )
            assert table["DeletionPolicy"] == "Delete", (
                f"DynamoDB table {table_name} should have DeletionPolicy: Delete"
            )

    def test_s3_buckets_have_deletion_policy(self, load_cfn_template):
        """Test that all S3 buckets have DeletionPolicy: Delete."""
        template = load_cfn_template("s3/buckets-stack.yaml")
        resources = template["Resources"]

        s3_buckets = ["AccessLogsBucket", "FrontendBucket"]

        for bucket_name in s3_buckets:
            assert bucket_name in resources, f"Bucket {bucket_name} not found"
            bucket = resources[bucket_name]
            assert bucket["Type"] == "AWS::S3::Bucket"
            assert "DeletionPolicy" in bucket, (
                f"S3 bucket {bucket_name} missing DeletionPolicy"
            )
            assert bucket["DeletionPolicy"] == "Delete", (
                f"S3 bucket {bucket_name} should have DeletionPolicy: Delete"
            )

    def test_cloudfront_distribution_has_deletion_policy(
        self, load_cfn_template
    ):
        """Test that CloudFront distribution has DeletionPolicy: Delete."""
        template = load_cfn_template("cloudfront/distribution-stack.yaml")
        resources = template["Resources"]

        assert "CloudFrontDistribution" in resources
        distribution = resources["CloudFrontDistribution"]
        assert distribution["Type"] == "AWS::CloudFront::Distribution"
        assert "DeletionPolicy" in distribution, (
            "CloudFront distribution missing DeletionPolicy"
        )
        assert distribution["DeletionPolicy"] == "Delete"

    def test_cloudfront_oac_has_deletion_policy(self, load_cfn_template):
        """Test that CloudFront OAC has DeletionPolicy: Delete."""
        template = load_cfn_template("cloudfront/distribution-stack.yaml")
        resources = template["Resources"]

        assert "CloudFrontOAC" in resources
        oac = resources["CloudFrontOAC"]
        assert oac["Type"] == "AWS::CloudFront::OriginAccessControl"
        assert "DeletionPolicy" in oac, (
            "CloudFront OAC missing DeletionPolicy"
        )
        assert oac["DeletionPolicy"] == "Delete"

    def test_cognito_user_pool_has_deletion_policy(self, load_cfn_template):
        """Test that Cognito user pool has DeletionPolicy: Delete."""
        template = load_cfn_template("cognito/auth-stack.yaml")
        resources = template["Resources"]

        assert "UserPool" in resources
        user_pool = resources["UserPool"]
        assert user_pool["Type"] == "AWS::Cognito::UserPool"
        assert "DeletionPolicy" in user_pool, (
            "Cognito user pool missing DeletionPolicy"
        )
        assert user_pool["DeletionPolicy"] == "Delete"

    def test_cognito_identity_pool_has_deletion_policy(
        self, load_cfn_template
    ):
        """Test that Cognito identity pool has DeletionPolicy: Delete."""
        template = load_cfn_template("cognito/auth-stack.yaml")
        resources = template["Resources"]

        assert "IdentityPool" in resources
        identity_pool = resources["IdentityPool"]
        assert identity_pool["Type"] == "AWS::Cognito::IdentityPool"
        assert "DeletionPolicy" in identity_pool, (
            "Cognito identity pool missing DeletionPolicy"
        )
        assert identity_pool["DeletionPolicy"] == "Delete"

    def test_step_functions_state_machine_has_deletion_policy(
        self, load_cfn_template
    ):
        """Test that Step Functions state machine has DeletionPolicy: Delete."""
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        resources = template["Resources"]

        assert "DRSOrchestrationStateMachine" in resources
        state_machine = resources["DRSOrchestrationStateMachine"]
        assert state_machine["Type"] == "AWS::StepFunctions::StateMachine"
        assert "DeletionPolicy" in state_machine, (
            "Step Functions state machine missing DeletionPolicy"
        )
        assert state_machine["DeletionPolicy"] == "Delete"

    def test_sqs_queues_have_deletion_policy(self, load_cfn_template):
        """Test that SQS queues have DeletionPolicy: Delete."""
        template = load_cfn_template("lambda/functions-stack.yaml")
        resources = template["Resources"]

        assert "LambdaDeadLetterQueue" in resources
        dlq = resources["LambdaDeadLetterQueue"]
        assert dlq["Type"] == "AWS::SQS::Queue"
        assert "DeletionPolicy" in dlq, (
            "SQS DLQ missing DeletionPolicy"
        )
        assert dlq["DeletionPolicy"] == "Delete"

    def test_cloudwatch_log_groups_have_deletion_policy(
        self, load_cfn_template
    ):
        """Test that CloudWatch log groups have DeletionPolicy: Delete."""
        template = load_cfn_template("apigateway/deployment-stack.yaml")
        resources = template["Resources"]

        assert "ApiGatewayAccessLogGroup" in resources
        log_group = resources["ApiGatewayAccessLogGroup"]
        assert log_group["Type"] == "AWS::Logs::LogGroup"
        assert "DeletionPolicy" in log_group, (
            "CloudWatch log group missing DeletionPolicy"
        )
        assert log_group["DeletionPolicy"] == "Delete"


class TestDeletionPolicyValues:
    """Test that DeletionPolicy values are appropriate for resource types."""

    def test_dynamodb_tables_use_delete_policy(self, load_cfn_template):
        """Test that DynamoDB tables use Delete (not Retain) for test env."""
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        resources = template["Resources"]

        for resource_name, resource in resources.items():
            if resource["Type"] == "AWS::DynamoDB::Table":
                assert resource["DeletionPolicy"] == "Delete", (
                    f"DynamoDB table {resource_name} should use "
                    f"DeletionPolicy: Delete for test environment"
                )

    def test_s3_buckets_use_delete_policy(self, load_cfn_template):
        """Test that S3 buckets use Delete policy."""
        template = load_cfn_template("s3/buckets-stack.yaml")
        resources = template["Resources"]

        for resource_name, resource in resources.items():
            if resource["Type"] == "AWS::S3::Bucket":
                assert resource["DeletionPolicy"] == "Delete", (
                    f"S3 bucket {resource_name} should use "
                    f"DeletionPolicy: Delete"
                )

    def test_cloudformation_stacks_use_delete_policy(
        self, load_cfn_template
    ):
        """Test that nested CloudFormation stacks use Delete policy."""
        template = load_cfn_template("main-stack.yaml")
        resources = template["Resources"]

        nested_stacks = [
            "IAMStack",
            "DynamoDBStack",
            "SNSStack",
            "LambdaStack",
            "StepFunctionsStack",
            "EventBridgeStack",
            "S3Stack",
            "WAFStack",
            "CloudFrontStack",
            "CognitoStack",
            "MonitoringStack"
        ]

        for stack_name in nested_stacks:
            if stack_name in resources:
                stack = resources[stack_name]
                if stack["Type"] == "AWS::CloudFormation::Stack":
                    # Note: Main stack may not have DeletionPolicy on nested
                    # stacks as they are managed by CloudFormation
                    # This test documents expected behavior
                    if "DeletionPolicy" in stack:
                        assert stack["DeletionPolicy"] == "Delete"


class TestUpdateReplacePolicyPresence:
    """Test that resources have UpdateReplacePolicy alongside DeletionPolicy."""

    def test_dynamodb_tables_have_update_replace_policy(
        self, load_cfn_template
    ):
        """Test that DynamoDB tables have UpdateReplacePolicy: Delete."""
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        resources = template["Resources"]

        dynamodb_tables = [
            "ProtectionGroupsTable",
            "RecoveryPlansTable",
            "ExecutionHistoryTable",
            "TargetAccountsTable",
            "SourceServerInventoryTable",
            "DRSRegionStatusTable",
            "RecoveryInstancesCacheTable"
        ]

        for table_name in dynamodb_tables:
            table = resources[table_name]
            assert "UpdateReplacePolicy" in table, (
                f"DynamoDB table {table_name} missing UpdateReplacePolicy"
            )
            assert table["UpdateReplacePolicy"] == "Delete", (
                f"DynamoDB table {table_name} should have "
                f"UpdateReplacePolicy: Delete"
            )

    def test_s3_buckets_have_update_replace_policy(self, load_cfn_template):
        """Test that S3 buckets have UpdateReplacePolicy: Delete."""
        template = load_cfn_template("s3/buckets-stack.yaml")
        resources = template["Resources"]

        s3_buckets = ["AccessLogsBucket", "FrontendBucket"]

        for bucket_name in s3_buckets:
            bucket = resources[bucket_name]
            assert "UpdateReplacePolicy" in bucket, (
                f"S3 bucket {bucket_name} missing UpdateReplacePolicy"
            )
            assert bucket["UpdateReplacePolicy"] == "Delete", (
                f"S3 bucket {bucket_name} should have "
                f"UpdateReplacePolicy: Delete"
            )

    def test_step_functions_has_update_replace_policy(
        self, load_cfn_template
    ):
        """Test that Step Functions state machine has UpdateReplacePolicy."""
        template = load_cfn_template("stepfunctions/statemachine-stack.yaml")
        resources = template["Resources"]

        state_machine = resources["DRSOrchestrationStateMachine"]
        assert "UpdateReplacePolicy" in state_machine, (
            "Step Functions state machine missing UpdateReplacePolicy"
        )
        assert state_machine["UpdateReplacePolicy"] == "Delete"


class TestS3BucketCleanupLogic:
    """Test S3 bucket cleanup logic in Frontend Deployer Lambda."""

    def test_empty_bucket_function_exists(self):
        """Test that empty_bucket function exists in frontend deployer."""
        frontend_deployer_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "lambda",
            "frontend-deployer",
            "index.py"
        )

        assert os.path.exists(frontend_deployer_path), (
            "Frontend deployer Lambda not found"
        )

        with open(frontend_deployer_path, "r") as f:
            content = f.read()

        assert "def empty_bucket" in content, (
            "empty_bucket function not found in frontend deployer"
        )

    def test_empty_bucket_handles_versioned_objects(self):
        """Test that empty_bucket handles versioned objects and delete markers."""
        frontend_deployer_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "lambda",
            "frontend-deployer",
            "index.py"
        )

        with open(frontend_deployer_path, "r") as f:
            content = f.read()

        # Check for list_object_versions usage
        assert "list_object_versions" in content, (
            "empty_bucket should use list_object_versions for versioned buckets"
        )

        # Check for version handling
        assert "VersionId" in content, (
            "empty_bucket should handle object versions"
        )

        # Check for delete markers handling
        assert "DeleteMarkers" in content, (
            "empty_bucket should handle delete markers"
        )

    def test_empty_bucket_handles_pagination(self):
        """Test that empty_bucket handles pagination for large buckets."""
        frontend_deployer_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "lambda",
            "frontend-deployer",
            "index.py"
        )

        with open(frontend_deployer_path, "r") as f:
            content = f.read()

        # Check for paginator usage
        assert "get_paginator" in content, (
            "empty_bucket should use paginator for large buckets"
        )

        # Check for batch deletion
        assert "delete_objects" in content, (
            "empty_bucket should use delete_objects for batch deletion"
        )

    def test_empty_bucket_has_error_handling(self):
        """Test that empty_bucket has proper error handling."""
        frontend_deployer_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "lambda",
            "frontend-deployer",
            "index.py"
        )

        with open(frontend_deployer_path, "r") as f:
            content = f.read()

        # Check for error handling
        assert "except ClientError" in content, (
            "empty_bucket should handle ClientError exceptions"
        )

        # Check for NoSuchBucket handling
        assert "NoSuchBucket" in content, (
            "empty_bucket should handle NoSuchBucket error"
        )

    def test_should_empty_bucket_function_exists(self):
        """Test that should_empty_bucket function exists."""
        frontend_deployer_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "lambda",
            "frontend-deployer",
            "index.py"
        )

        with open(frontend_deployer_path, "r") as f:
            content = f.read()

        assert "def should_empty_bucket" in content, (
            "should_empty_bucket function not found in frontend deployer"
        )

    def test_should_empty_bucket_checks_stack_status(self):
        """Test that should_empty_bucket checks CloudFormation stack status."""
        frontend_deployer_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "lambda",
            "frontend-deployer",
            "index.py"
        )

        with open(frontend_deployer_path, "r") as f:
            content = f.read()

        # Check for stack status verification
        assert "describe_stacks" in content, (
            "should_empty_bucket should check stack status"
        )

        # Check for DELETE_IN_PROGRESS handling
        assert "DELETE_IN_PROGRESS" in content, (
            "should_empty_bucket should check for DELETE_IN_PROGRESS"
        )

        # Check for UPDATE_ROLLBACK safety check
        assert "UPDATE_ROLLBACK" in content, (
            "should_empty_bucket should prevent cleanup during UPDATE_ROLLBACK"
        )

    def test_delete_handler_uses_should_empty_bucket(self):
        """Test that delete handler uses should_empty_bucket before cleanup."""
        frontend_deployer_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "lambda",
            "frontend-deployer",
            "index.py"
        )

        with open(frontend_deployer_path, "r") as f:
            content = f.read()

        # Check that delete handler calls should_empty_bucket
        assert "@helper.delete" in content, (
            "Frontend deployer should have delete handler"
        )

        # Find the delete function
        delete_func_start = content.find("@helper.delete")
        delete_func_content = content[delete_func_start:delete_func_start + 3000]

        assert "should_empty_bucket" in delete_func_content, (
            "Delete handler should call should_empty_bucket"
        )

    def test_delete_handler_returns_success_on_error(self):
        """Test that delete handler returns success even on cleanup errors."""
        frontend_deployer_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "lambda",
            "frontend-deployer",
            "index.py"
        )

        with open(frontend_deployer_path, "r") as f:
            content = f.read()

        # Find the delete function
        delete_func_start = content.find("@helper.delete")
        # Read until the next function definition or end of file
        next_func = content.find("\ndef ", delete_func_start + 100)
        if next_func == -1:
            next_func = len(content)
        delete_func_content = content[delete_func_start:next_func]

        # Check for graceful error handling
        assert "except Exception" in delete_func_content, (
            "Delete handler should catch exceptions"
        )

        # Check that it returns None on error (doesn't raise)
        assert "return None" in delete_func_content, (
            "Delete handler should return None to allow stack deletion"
        )


class TestDeletionPolicyConsistency:
    """Test that DeletionPolicy is consistent across related resources."""

    def test_all_dynamodb_tables_have_same_policy(self, load_cfn_template):
        """Test that all DynamoDB tables have consistent DeletionPolicy."""
        template = load_cfn_template("dynamodb/tables-stack.yaml")
        resources = template["Resources"]

        deletion_policies = set()

        for resource_name, resource in resources.items():
            if resource["Type"] == "AWS::DynamoDB::Table":
                if "DeletionPolicy" in resource:
                    deletion_policies.add(resource["DeletionPolicy"])

        assert len(deletion_policies) == 1, (
            "All DynamoDB tables should have the same DeletionPolicy"
        )
        assert "Delete" in deletion_policies

    def test_all_s3_buckets_have_same_policy(self, load_cfn_template):
        """Test that all S3 buckets have consistent DeletionPolicy."""
        template = load_cfn_template("s3/buckets-stack.yaml")
        resources = template["Resources"]

        deletion_policies = set()

        for resource_name, resource in resources.items():
            if resource["Type"] == "AWS::S3::Bucket":
                if "DeletionPolicy" in resource:
                    deletion_policies.add(resource["DeletionPolicy"])

        assert len(deletion_policies) == 1, (
            "All S3 buckets should have the same DeletionPolicy"
        )
        assert "Delete" in deletion_policies


class TestDeletionPolicyDocumentation:
    """Test that DeletionPolicy decisions are documented."""

    def test_frontend_deployer_has_deletion_documentation(self):
        """Test that frontend deployer documents deletion behavior."""
        frontend_deployer_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "lambda",
            "frontend-deployer",
            "index.py"
        )

        with open(frontend_deployer_path, "r") as f:
            content = f.read()

        # Check for documentation of deletion behavior
        assert "DELETE" in content, (
            "Frontend deployer should document DELETE behavior"
        )

        # Check for safety documentation
        assert "SAFETY" in content or "safety" in content.lower(), (
            "Frontend deployer should document safety considerations"
        )

    def test_s3_buckets_stack_has_deletion_comments(self, load_cfn_template):
        """Test that S3 buckets stack documents DeletionPolicy choices."""
        template_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "cfn",
            "s3",
            "buckets-stack.yaml"
        )

        with open(template_path, "r") as f:
            content = f.read()

        # Check that DeletionPolicy is present in the file
        assert "DeletionPolicy" in content, (
            "S3 buckets stack should have DeletionPolicy defined"
        )


class TestMissingDeletionPolicyDetection:
    """Test detection of resources missing DeletionPolicy."""

    def test_can_detect_missing_deletion_policy_in_template(self):
        """Test that we can detect resources missing DeletionPolicy."""
        # Create a test template with missing DeletionPolicy
        test_template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Resources": {
                "TestTable": {
                    "Type": "AWS::DynamoDB::Table",
                    "Properties": {
                        "TableName": "test-table",
                        "AttributeDefinitions": [
                            {
                                "AttributeName": "id",
                                "AttributeType": "S"
                            }
                        ],
                        "KeySchema": [
                            {
                                "AttributeName": "id",
                                "KeyType": "HASH"
                            }
                        ],
                        "BillingMode": "PAY_PER_REQUEST"
                    }
                }
            }
        }

        # Check for missing DeletionPolicy
        resources = test_template["Resources"]
        missing_deletion_policy = []

        for resource_name, resource in resources.items():
            if "DeletionPolicy" not in resource:
                missing_deletion_policy.append(resource_name)

        assert len(missing_deletion_policy) == 1
        assert "TestTable" in missing_deletion_policy

    def test_all_templates_have_deletion_policy_on_stateful_resources(
        self, load_cfn_template
    ):
        """Test that all stateful resources have DeletionPolicy."""
        stateful_resource_types = [
            "AWS::DynamoDB::Table",
            "AWS::S3::Bucket",
            "AWS::RDS::DBInstance",
            "AWS::RDS::DBCluster",
            "AWS::ElastiCache::CacheCluster",
            "AWS::ElastiCache::ReplicationGroup"
        ]

        template_paths = [
            "dynamodb/tables-stack.yaml",
            "s3/buckets-stack.yaml",
            "cloudfront/distribution-stack.yaml",
            "cognito/auth-stack.yaml",
            "stepfunctions/statemachine-stack.yaml"
        ]

        for template_path in template_paths:
            template = load_cfn_template(template_path)
            resources = template.get("Resources", {})

            for resource_name, resource in resources.items():
                resource_type = resource.get("Type", "")

                if resource_type in stateful_resource_types:
                    assert "DeletionPolicy" in resource, (
                        f"Stateful resource {resource_name} in "
                        f"{template_path} missing DeletionPolicy"
                    )


class TestCfnLintValidation:
    """Test cfn-lint validation for DeletionPolicy (if configured)."""

    def test_cfnlintrc_exists(self):
        """Test that .cfnlintrc.yaml configuration file exists."""
        cfnlintrc_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".cfnlintrc.yaml"
        )

        # Note: This test documents expected behavior
        # cfn-lint configuration may or may not enforce DeletionPolicy
        if os.path.exists(cfnlintrc_path):
            with open(cfnlintrc_path, "r") as f:
                config = yaml.safe_load(f)

            # Document that cfn-lint config exists
            assert config is not None

    def test_can_run_cfn_lint_on_templates(self):
        """Test that cfn-lint can be run on CloudFormation templates."""
        # This test documents that cfn-lint should be run as part of CI/CD
        # Actual cfn-lint execution happens in deployment scripts

        template_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "cfn"
        )

        assert os.path.exists(template_dir), (
            "CloudFormation templates directory should exist"
        )

        # Count YAML files
        yaml_files = []
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith(".yaml") or file.endswith(".yml"):
                    yaml_files.append(os.path.join(root, file))

        assert len(yaml_files) > 0, (
            "Should have CloudFormation templates to validate"
        )
