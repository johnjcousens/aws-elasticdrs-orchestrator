"""
Unit tests for main stack CloudFormation template.

Tests verify:
- Template structure and metadata
- Parameter definitions and defaults
- Nested stack resources and dependencies
- Parameter passing to nested stacks
- Output definitions and exports
- Template URL patterns
- No unused parameters (cfn-lint W2001)
"""

import pytest
from typing import Dict, Any


class TestMainStackStructure:
    """Test main stack template structure and metadata."""

    def test_template_has_required_sections(self, load_cfn_template):
        """Test template contains all required CloudFormation sections."""
        template = load_cfn_template("main-stack.yaml")

        assert "AWSTemplateFormatVersion" in template
        assert template["AWSTemplateFormatVersion"] == "2010-09-09"
        assert "Description" in template
        assert "Parameters" in template
        assert "Conditions" in template
        assert "Resources" in template
        assert "Outputs" in template

    def test_template_description_is_meaningful(self, load_cfn_template):
        """Test template has meaningful description."""
        template = load_cfn_template("main-stack.yaml")

        description = template["Description"]
        assert len(description) > 50
        assert "DR Orchestration Platform" in description
        assert "Main Stack" in description

    def test_template_has_nested_stack_documentation(self, load_cfn_template):
        """Test template description documents nested stacks."""
        template = load_cfn_template("main-stack.yaml")

        description = template["Description"]
        assert "IAM Stack" in description
        assert "Lambda Stack" in description
        assert "API Gateway" in description


class TestMainStackParameters:
    """Test main stack parameter definitions."""

    def test_all_required_parameters_defined(self, load_cfn_template):
        """Test all required parameters are defined."""
        template = load_cfn_template("main-stack.yaml")
        parameters = template["Parameters"]

        required_params = [
            "ProjectName",
            "Environment",
            "DeploymentBucket",
            "AdminEmail",
            "UseFunctionSpecificRoles"
        ]

        for param in required_params:
            assert param in parameters, f"Missing required parameter: {param}"

    def test_project_name_parameter(self, load_cfn_template):
        """Test ProjectName parameter configuration."""
        template = load_cfn_template("main-stack.yaml")
        param = template["Parameters"]["ProjectName"]

        assert param["Type"] == "String"
        assert "Description" in param
        assert param["Default"] == "aws-drs-orchestration"

    def test_environment_parameter(self, load_cfn_template):
        """Test Environment parameter configuration."""
        template = load_cfn_template("main-stack.yaml")
        param = template["Parameters"]["Environment"]

        assert param["Type"] == "String"
        assert "AllowedValues" in param
        assert param["Default"] == "test"

        allowed_values = param["AllowedValues"]
        assert "dev" in allowed_values
        assert "test" in allowed_values
        assert "staging" in allowed_values
        assert "prod" in allowed_values

    def test_deployment_bucket_parameter(self, load_cfn_template):
        """Test DeploymentBucket parameter configuration."""
        template = load_cfn_template("main-stack.yaml")
        param = template["Parameters"]["DeploymentBucket"]

        assert param["Type"] == "String"
        assert "Description" in param
        assert "CloudFormation templates" in param["Description"]

    def test_admin_email_parameter(self, load_cfn_template):
        """Test AdminEmail parameter configuration."""
        template = load_cfn_template("main-stack.yaml")
        param = template["Parameters"]["AdminEmail"]

        assert param["Type"] == "String"
        assert "Description" in param

    def test_use_function_specific_roles_parameter(self, load_cfn_template):
        """Test UseFunctionSpecificRoles parameter configuration."""
        template = load_cfn_template("main-stack.yaml")
        param = template["Parameters"]["UseFunctionSpecificRoles"]

        assert param["Type"] == "String"
        assert "AllowedValues" in param
        assert param["AllowedValues"] == ["true", "false"]
        assert param["Default"] == "false"


class TestMainStackConditions:
    """Test main stack condition definitions."""

    def test_use_function_specific_roles_condition(self, load_cfn_template):
        """Test UseFunctionSpecificRoles condition is defined."""
        template = load_cfn_template("main-stack.yaml")
        conditions = template["Conditions"]

        assert "UseFunctionSpecificRoles" in conditions
        condition = conditions["UseFunctionSpecificRoles"]
        assert "Fn::Equals" in condition or "Equals" in str(condition)


class TestMainStackNestedStacks:
    """Test nested stack resource definitions."""

    def test_all_nested_stacks_exist(self, load_cfn_template):
        """Test all expected nested stacks are defined."""
        template = load_cfn_template("main-stack.yaml")
        resources = template["Resources"]

        expected_stacks = [
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
            "MonitoringStack",
            "APIGatewayCoreStack",
            "APIGatewayAuthStack",
            "APIGatewayResourcesStack",
            "APIGatewayCoreMethodsStack",
            "APIGatewayInfrastructureMethodsStack",
            "APIGatewayOperationsMethodsStack",
            "APIGatewayDeploymentStack"
        ]

        for stack in expected_stacks:
            assert stack in resources, f"Missing nested stack: {stack}"

    def test_nested_stacks_are_cloudformation_stacks(self, load_cfn_template):
        """Test all nested stacks have correct resource type."""
        template = load_cfn_template("main-stack.yaml")
        resources = template["Resources"]

        nested_stacks = [
            "IAMStack", "DynamoDBStack", "SNSStack", "LambdaStack",
            "StepFunctionsStack", "EventBridgeStack", "S3Stack",
            "WAFStack", "CloudFrontStack", "CognitoStack",
            "MonitoringStack", "APIGatewayCoreStack"
        ]

        for stack in nested_stacks:
            assert resources[stack]["Type"] == "AWS::CloudFormation::Stack"

    def test_nested_stacks_have_template_urls(self, load_cfn_template):
        """Test all nested stacks have TemplateURL property."""
        template = load_cfn_template("main-stack.yaml")
        resources = template["Resources"]

        nested_stacks = [
            "IAMStack", "DynamoDBStack", "SNSStack", "LambdaStack",
            "StepFunctionsStack", "EventBridgeStack", "S3Stack",
            "WAFStack", "CloudFrontStack", "CognitoStack",
            "MonitoringStack", "APIGatewayCoreStack"
        ]

        for stack in nested_stacks:
            properties = resources[stack]["Properties"]
            assert "TemplateURL" in properties


class TestMainStackTemplateURLs:
    """Test nested stack TemplateURL patterns."""

    def test_iam_stack_template_url(self, load_cfn_template):
        """Test IAM stack TemplateURL uses correct path."""
        template = load_cfn_template("main-stack.yaml")
        iam_stack = template["Resources"]["IAMStack"]
        template_url = iam_stack["Properties"]["TemplateURL"]

        assert "Sub" in str(template_url) or "Fn::Sub" in str(template_url)
        assert "DeploymentBucket" in str(template_url)
        assert "cfn/iam/roles-stack.yaml" in str(template_url)

    def test_lambda_stack_template_url(self, load_cfn_template):
        """Test Lambda stack TemplateURL uses correct path."""
        template = load_cfn_template("main-stack.yaml")
        lambda_stack = template["Resources"]["LambdaStack"]
        template_url = lambda_stack["Properties"]["TemplateURL"]

        assert "DeploymentBucket" in str(template_url)
        assert "cfn/lambda/functions-stack.yaml" in str(template_url)

    def test_apigateway_core_stack_template_url(self, load_cfn_template):
        """Test API Gateway core stack TemplateURL uses correct path."""
        template = load_cfn_template("main-stack.yaml")
        api_stack = template["Resources"]["APIGatewayCoreStack"]
        template_url = api_stack["Properties"]["TemplateURL"]

        assert "DeploymentBucket" in str(template_url)
        assert "cfn/apigateway/core-stack.yaml" in str(template_url)


class TestMainStackDependencies:
    """Test nested stack dependency relationships."""

    def test_iam_stack_has_no_dependencies(self, load_cfn_template):
        """Test IAM stack has no dependencies (foundation stack)."""
        template = load_cfn_template("main-stack.yaml")
        iam_stack = template["Resources"]["IAMStack"]

        assert "DependsOn" not in iam_stack

    def test_lambda_stack_depends_on_iam(self, load_cfn_template):
        """Test Lambda stack depends on IAM stack."""
        template = load_cfn_template("main-stack.yaml")
        lambda_stack = template["Resources"]["LambdaStack"]

        assert "DependsOn" in lambda_stack
        depends_on = lambda_stack["DependsOn"]
        assert "IAMStack" in depends_on

    def test_lambda_stack_depends_on_dynamodb(self, load_cfn_template):
        """Test Lambda stack depends on DynamoDB stack."""
        template = load_cfn_template("main-stack.yaml")
        lambda_stack = template["Resources"]["LambdaStack"]

        depends_on = lambda_stack["DependsOn"]
        assert "DynamoDBStack" in depends_on

    def test_lambda_stack_depends_on_sns(self, load_cfn_template):
        """Test Lambda stack depends on SNS stack."""
        template = load_cfn_template("main-stack.yaml")
        lambda_stack = template["Resources"]["LambdaStack"]

        depends_on = lambda_stack["DependsOn"]
        assert "SNSStack" in depends_on

    def test_step_functions_stack_depends_on_lambda(self, load_cfn_template):
        """Test Step Functions stack depends on Lambda stack."""
        template = load_cfn_template("main-stack.yaml")
        sf_stack = template["Resources"]["StepFunctionsStack"]

        assert "DependsOn" in sf_stack
        depends_on = sf_stack["DependsOn"]
        assert "LambdaStack" in depends_on

    def test_eventbridge_stack_depends_on_lambda(self, load_cfn_template):
        """Test EventBridge stack depends on Lambda stack."""
        template = load_cfn_template("main-stack.yaml")
        eb_stack = template["Resources"]["EventBridgeStack"]

        assert "DependsOn" in eb_stack
        depends_on = eb_stack["DependsOn"]
        assert "LambdaStack" in depends_on

    def test_cloudfront_stack_depends_on_s3(self, load_cfn_template):
        """Test CloudFront stack depends on S3 stack."""
        template = load_cfn_template("main-stack.yaml")
        cf_stack = template["Resources"]["CloudFrontStack"]

        assert "DependsOn" in cf_stack
        depends_on = cf_stack["DependsOn"]
        assert "S3Stack" in depends_on

    def test_cloudfront_stack_depends_on_waf(self, load_cfn_template):
        """Test CloudFront stack depends on WAF stack."""
        template = load_cfn_template("main-stack.yaml")
        cf_stack = template["Resources"]["CloudFrontStack"]

        depends_on = cf_stack["DependsOn"]
        assert "WAFStack" in depends_on

    def test_monitoring_stack_depends_on_lambda(self, load_cfn_template):
        """Test Monitoring stack depends on Lambda stack."""
        template = load_cfn_template("main-stack.yaml")
        mon_stack = template["Resources"]["MonitoringStack"]

        assert "DependsOn" in mon_stack
        depends_on = mon_stack["DependsOn"]
        assert "LambdaStack" in depends_on

    def test_monitoring_stack_depends_on_sns(self, load_cfn_template):
        """Test Monitoring stack depends on SNS stack."""
        template = load_cfn_template("main-stack.yaml")
        mon_stack = template["Resources"]["MonitoringStack"]

        depends_on = mon_stack["DependsOn"]
        assert "SNSStack" in depends_on

    def test_apigateway_auth_depends_on_core_and_cognito(self, load_cfn_template):
        """Test API Gateway auth stack depends on core and Cognito stacks."""
        template = load_cfn_template("main-stack.yaml")
        auth_stack = template["Resources"]["APIGatewayAuthStack"]

        assert "DependsOn" in auth_stack
        depends_on = auth_stack["DependsOn"]
        assert "APIGatewayCoreStack" in depends_on
        assert "CognitoStack" in depends_on

    def test_apigateway_deployment_depends_on_methods(self, load_cfn_template):
        """Test API Gateway deployment stack depends on all method stacks."""
        template = load_cfn_template("main-stack.yaml")
        deploy_stack = template["Resources"]["APIGatewayDeploymentStack"]

        assert "DependsOn" in deploy_stack
        depends_on = deploy_stack["DependsOn"]
        assert "APIGatewayCoreMethodsStack" in depends_on
        assert "APIGatewayInfrastructureMethodsStack" in depends_on
        assert "APIGatewayOperationsMethodsStack" in depends_on


class TestMainStackParameterPassing:
    """Test parameter passing to nested stacks."""

    def test_iam_stack_receives_use_function_specific_roles(self, load_cfn_template):
        """Test IAM stack receives UseFunctionSpecificRoles parameter."""
        template = load_cfn_template("main-stack.yaml")
        iam_stack = template["Resources"]["IAMStack"]
        parameters = iam_stack["Properties"]["Parameters"]

        assert "UseFunctionSpecificRoles" in parameters
        assert "Ref" in str(parameters["UseFunctionSpecificRoles"])

    def test_lambda_stack_receives_all_role_arns(self, load_cfn_template):
        """Test Lambda stack receives all IAM role ARNs."""
        template = load_cfn_template("main-stack.yaml")
        lambda_stack = template["Resources"]["LambdaStack"]
        parameters = lambda_stack["Properties"]["Parameters"]

        required_role_params = [
            "UnifiedRoleArn",
            "QueryHandlerRoleArn",
            "DataManagementRoleArn",
            "ExecutionHandlerRoleArn",
            "OrchestrationRoleArn",
            "FrontendDeployerRoleArn"
        ]

        for param in required_role_params:
            assert param in parameters, f"Missing role parameter: {param}"

    def test_lambda_stack_receives_dynamodb_table_names(self, load_cfn_template):
        """Test Lambda stack receives all DynamoDB table names."""
        template = load_cfn_template("main-stack.yaml")
        lambda_stack = template["Resources"]["LambdaStack"]
        parameters = lambda_stack["Properties"]["Parameters"]

        required_table_params = [
            "ProtectionGroupsTableName",
            "RecoveryPlansTableName",
            "ExecutionHistoryTableName",
            "TargetAccountsTableName",
            "SourceServerInventoryTableName",
            "DRSRegionStatusTableName",
            "RecoveryInstancesCacheTableName"
        ]

        for param in required_table_params:
            assert param in parameters, f"Missing table parameter: {param}"

    def test_lambda_stack_receives_sns_topic_arns(self, load_cfn_template):
        """Test Lambda stack receives SNS topic ARNs."""
        template = load_cfn_template("main-stack.yaml")
        lambda_stack = template["Resources"]["LambdaStack"]
        parameters = lambda_stack["Properties"]["Parameters"]

        required_sns_params = [
            "ExecutionNotificationsTopicArn",
            "DRSAlertsTopicArn",
            "ExecutionPauseTopicArn"
        ]

        for param in required_sns_params:
            assert param in parameters, f"Missing SNS parameter: {param}"

    def test_step_functions_stack_receives_lambda_arns(self, load_cfn_template):
        """Test Step Functions stack receives Lambda function ARNs."""
        template = load_cfn_template("main-stack.yaml")
        sf_stack = template["Resources"]["StepFunctionsStack"]
        parameters = sf_stack["Properties"]["Parameters"]

        assert "OrchestrationFunctionArn" in parameters
        assert "ExecutionHandlerArn" in parameters

    def test_step_functions_stack_receives_correct_role(self, load_cfn_template):
        """Test Step Functions stack receives correct role based on condition."""
        template = load_cfn_template("main-stack.yaml")
        sf_stack = template["Resources"]["StepFunctionsStack"]
        parameters = sf_stack["Properties"]["Parameters"]

        assert "OrchestrationRoleArn" in parameters
        role_param = parameters["OrchestrationRoleArn"]
        assert "Fn::If" in str(role_param) or "If" in str(role_param)

    def test_cloudfront_stack_receives_s3_outputs(self, load_cfn_template):
        """Test CloudFront stack receives S3 bucket outputs."""
        template = load_cfn_template("main-stack.yaml")
        cf_stack = template["Resources"]["CloudFrontStack"]
        parameters = cf_stack["Properties"]["Parameters"]

        assert "FrontendBucketName" in parameters
        assert "FrontendBucketRegionalDomainName" in parameters
        assert "AccessLogsBucketDomainName" in parameters

    def test_cloudfront_stack_receives_waf_arn(self, load_cfn_template):
        """Test CloudFront stack receives WAF WebACL ARN."""
        template = load_cfn_template("main-stack.yaml")
        cf_stack = template["Resources"]["CloudFrontStack"]
        parameters = cf_stack["Properties"]["Parameters"]

        assert "WebACLArn" in parameters

    def test_apigateway_auth_receives_cognito_outputs(self, load_cfn_template):
        """Test API Gateway auth stack receives Cognito outputs."""
        template = load_cfn_template("main-stack.yaml")
        auth_stack = template["Resources"]["APIGatewayAuthStack"]
        parameters = auth_stack["Properties"]["Parameters"]

        assert "UserPoolArn" in parameters


class TestMainStackOutputs:
    """Test main stack output definitions."""

    def test_all_required_outputs_defined(self, load_cfn_template):
        """Test all required outputs are defined."""
        template = load_cfn_template("main-stack.yaml")
        outputs = template["Outputs"]

        required_outputs = [
            "StackStatus",
            "ApiEndpoint",
            "CloudFrontDomain",
            "CloudFrontUrl",
            "UserPoolId",
            "UserPoolClientId",
            "IdentityPoolId"
        ]

        for output in required_outputs:
            assert output in outputs, f"Missing required output: {output}"

    def test_api_endpoint_output_uses_correct_pattern(self, load_cfn_template):
        """Test ApiEndpoint output uses correct URL pattern."""
        template = load_cfn_template("main-stack.yaml")
        output = template["Outputs"]["ApiEndpoint"]

        assert "Value" in output
        value = str(output["Value"])
        assert "execute-api" in value
        assert "amazonaws.com" in value

    def test_cloudfront_outputs_reference_nested_stack(self, load_cfn_template):
        """Test CloudFront outputs reference CloudFront nested stack."""
        template = load_cfn_template("main-stack.yaml")

        cf_domain = template["Outputs"]["CloudFrontDomain"]
        cf_url = template["Outputs"]["CloudFrontUrl"]

        assert "GetAtt" in str(cf_domain["Value"]) or "Fn::GetAtt" in str(cf_domain["Value"])
        assert "CloudFrontStack" in str(cf_domain["Value"])

        assert "GetAtt" in str(cf_url["Value"]) or "Fn::GetAtt" in str(cf_url["Value"])
        assert "CloudFrontStack" in str(cf_url["Value"])

    def test_cognito_outputs_reference_nested_stack(self, load_cfn_template):
        """Test Cognito outputs reference Cognito nested stack."""
        template = load_cfn_template("main-stack.yaml")

        user_pool = template["Outputs"]["UserPoolId"]
        client_id = template["Outputs"]["UserPoolClientId"]
        identity_pool = template["Outputs"]["IdentityPoolId"]

        for output in [user_pool, client_id, identity_pool]:
            assert "GetAtt" in str(output["Value"]) or "Fn::GetAtt" in str(output["Value"])
            assert "CognitoStack" in str(output["Value"])

    def test_all_outputs_have_exports(self, load_cfn_template):
        """Test all outputs have export names."""
        template = load_cfn_template("main-stack.yaml")
        outputs = template["Outputs"]

        for output_name, output_config in outputs.items():
            if output_name != "StackStatus":
                assert "Export" in output_config, f"Output {output_name} missing Export"
                assert "Name" in output_config["Export"]

    def test_conditional_outputs_have_conditions(self, load_cfn_template):
        """Test conditional outputs (function-specific roles) have conditions."""
        template = load_cfn_template("main-stack.yaml")
        outputs = template["Outputs"]

        conditional_outputs = [
            "QueryHandlerRoleArn",
            "DataManagementRoleArn",
            "ExecutionHandlerRoleArn",
            "OrchestrationRoleArn",
            "FrontendDeployerRoleArn"
        ]

        for output_name in conditional_outputs:
            assert output_name in outputs
            output = outputs[output_name]
            assert "Condition" in output
            assert output["Condition"] == "UseFunctionSpecificRoles"


class TestMainStackTags:
    """Test nested stack tagging."""

    def test_all_nested_stacks_have_tags(self, load_cfn_template):
        """Test all nested stacks have required tags."""
        template = load_cfn_template("main-stack.yaml")
        resources = template["Resources"]

        nested_stacks = [
            "IAMStack", "DynamoDBStack", "SNSStack", "LambdaStack",
            "StepFunctionsStack", "EventBridgeStack", "S3Stack",
            "WAFStack", "CloudFrontStack", "CognitoStack",
            "MonitoringStack", "APIGatewayCoreStack"
        ]

        for stack in nested_stacks:
            properties = resources[stack]["Properties"]
            assert "Tags" in properties, f"Stack {stack} missing Tags"

    def test_nested_stacks_have_required_tag_keys(self, load_cfn_template):
        """Test nested stacks have Project, Environment, and StackType tags."""
        template = load_cfn_template("main-stack.yaml")
        resources = template["Resources"]

        nested_stacks = ["IAMStack", "LambdaStack", "APIGatewayCoreStack"]

        for stack in nested_stacks:
            tags = resources[stack]["Properties"]["Tags"]
            tag_keys = [tag["Key"] for tag in tags]

            assert "Project" in tag_keys
            assert "Environment" in tag_keys
            assert "StackType" in tag_keys


class TestMainStackNoUnusedParameters:
    """Test that all parameters are used (no cfn-lint W2001 warnings)."""

    def test_project_name_parameter_is_used(self, load_cfn_template):
        """Test ProjectName parameter is used in resources and outputs."""
        template = load_cfn_template("main-stack.yaml")
        template_str = str(template)

        assert "ProjectName" in template_str
        assert template_str.count("ProjectName") > 5

    def test_environment_parameter_is_used(self, load_cfn_template):
        """Test Environment parameter is used in resources and outputs."""
        template = load_cfn_template("main-stack.yaml")
        template_str = str(template)

        assert "Environment" in template_str
        assert template_str.count("Environment") > 5

    def test_deployment_bucket_parameter_is_used(self, load_cfn_template):
        """Test DeploymentBucket parameter is used in TemplateURLs."""
        template = load_cfn_template("main-stack.yaml")
        template_str = str(template)

        assert "DeploymentBucket" in template_str
        assert template_str.count("DeploymentBucket") > 10

    def test_admin_email_parameter_is_used(self, load_cfn_template):
        """Test AdminEmail parameter is passed to nested stacks."""
        template = load_cfn_template("main-stack.yaml")
        template_str = str(template)

        assert "AdminEmail" in template_str
        assert template_str.count("AdminEmail") >= 3

    def test_use_function_specific_roles_parameter_is_used(self, load_cfn_template):
        """Test UseFunctionSpecificRoles parameter is used in conditions and stacks."""
        template = load_cfn_template("main-stack.yaml")
        template_str = str(template)

        assert "UseFunctionSpecificRoles" in template_str
        assert template_str.count("UseFunctionSpecificRoles") >= 4

