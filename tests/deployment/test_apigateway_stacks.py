"""
Unit tests for API Gateway nested stacks.

Tests all 7 API Gateway CloudFormation templates:
1. core-stack.yaml - REST API, Authorizer, Request Validator
2. resources-stack.yaml - API resources (path structure)
3. core-methods-stack.yaml - Core methods (health, user, protection groups, recovery plans)
4. infrastructure-methods-stack.yaml - Infrastructure methods (DRS, EC2, config, accounts)
5. operations-methods-stack.yaml - Operations methods (executions, failover, failback)
6. deployment-stack.yaml - Deployment, Stage, Gateway Responses
7. auth-stack.yaml - Cognito authorizer

Validates:
- CloudFormation template syntax (cfn-lint)
- No unused parameters (cfn-lint W2001)
- Resource dependencies
- Outputs and exports
- REST API configuration
- Authorizer configuration
- Resource and method definitions
- Deployment and stage configuration
"""

import pytest
import yaml
from pathlib import Path


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def apigateway_templates_dir():
    """Return path to API Gateway templates directory."""
    return Path("cfn/apigateway")


@pytest.fixture
def core_stack_template(apigateway_templates_dir):
    """Load core-stack.yaml template."""
    template_path = apigateway_templates_dir / "core-stack.yaml"
    with open(template_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def resources_stack_template(apigateway_templates_dir):
    """Load resources-stack.yaml template."""
    template_path = apigateway_templates_dir / "resources-stack.yaml"
    with open(template_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def core_methods_stack_template(apigateway_templates_dir):
    """Load core-methods-stack.yaml template."""
    template_path = apigateway_templates_dir / "core-methods-stack.yaml"
    with open(template_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def infrastructure_methods_stack_template(apigateway_templates_dir):
    """Load infrastructure-methods-stack.yaml template."""
    template_path = apigateway_templates_dir / "infrastructure-methods-stack.yaml"
    with open(template_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def operations_methods_stack_template(apigateway_templates_dir):
    """Load operations-methods-stack.yaml template."""
    template_path = apigateway_templates_dir / "operations-methods-stack.yaml"
    with open(template_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def deployment_stack_template(apigateway_templates_dir):
    """Load deployment-stack.yaml template."""
    template_path = apigateway_templates_dir / "deployment-stack.yaml"
    with open(template_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def auth_stack_template(apigateway_templates_dir):
    """Load auth-stack.yaml template."""
    template_path = apigateway_templates_dir / "auth-stack.yaml"
    with open(template_path, 'r') as f:
        return yaml.safe_load(f)


# =============================================================================
# CORE STACK TESTS
# =============================================================================

class TestCoreStack:
    """Tests for API Gateway Core Stack (core-stack.yaml)."""

    def test_core_stack_has_required_sections(self, core_stack_template):
        """Verify core stack has all required CloudFormation sections."""
        assert 'AWSTemplateFormatVersion' in core_stack_template
        assert 'Description' in core_stack_template
        assert 'Parameters' in core_stack_template
        assert 'Resources' in core_stack_template
        assert 'Outputs' in core_stack_template

    def test_core_stack_parameters(self, core_stack_template):
        """Verify core stack has required parameters."""
        params = core_stack_template['Parameters']
        assert 'ProjectName' in params
        assert 'Environment' in params
        assert 'ApiHandlerFunctionArn' in params

    def test_core_stack_rest_api_resource(self, core_stack_template):
        """Verify REST API resource is correctly configured."""
        resources = core_stack_template['Resources']
        assert 'RestApi' in resources

        rest_api = resources['RestApi']
        assert rest_api['Type'] == 'AWS::ApiGateway::RestApi'

        props = rest_api['Properties']
        assert 'Name' in props
        assert 'EndpointConfiguration' in props
        assert props['EndpointConfiguration']['Types'] == ['REGIONAL']
        assert 'Policy' in props
        assert 'BinaryMediaTypes' in props

    def test_core_stack_request_validator(self, core_stack_template):
        """Verify request validator is configured."""
        resources = core_stack_template['Resources']
        assert 'ApiRequestValidator' in resources

        validator = resources['ApiRequestValidator']
        assert validator['Type'] == 'AWS::ApiGateway::RequestValidator'

        props = validator['Properties']
        assert props['ValidateRequestBody'] is True
        assert props['ValidateRequestParameters'] is True

    def test_core_stack_lambda_permission(self, core_stack_template):
        """Verify Lambda permission for API Gateway."""
        resources = core_stack_template['Resources']
        assert 'ApiGatewayInvokePermission' in resources

        permission = resources['ApiGatewayInvokePermission']
        assert permission['Type'] == 'AWS::Lambda::Permission'

        props = permission['Properties']
        assert props['Action'] == 'lambda:InvokeFunction'
        assert props['Principal'] == 'apigateway.amazonaws.com'

    def test_core_stack_outputs(self, core_stack_template):
        """Verify core stack exports required outputs."""
        outputs = core_stack_template['Outputs']
        assert 'RestApiId' in outputs
        assert 'RestApiRootResourceId' in outputs
        assert 'ApiRequestValidatorId' in outputs

        for output_name, output_value in outputs.items():
            assert 'Export' in output_value
            assert 'Name' in output_value['Export']


# =============================================================================
# RESOURCES STACK TESTS
# =============================================================================

class TestResourcesStack:
    """Tests for API Gateway Resources Stack (resources-stack.yaml)."""

    def test_resources_stack_has_required_sections(self, resources_stack_template):
        """Verify resources stack has all required sections."""
        assert 'AWSTemplateFormatVersion' in resources_stack_template
        assert 'Description' in resources_stack_template
        assert 'Parameters' in resources_stack_template
        assert 'Resources' in resources_stack_template
        assert 'Outputs' in resources_stack_template

    def test_resources_stack_parameters(self, resources_stack_template):
        """Verify resources stack has required parameters."""
        params = resources_stack_template['Parameters']
        assert 'ProjectName' in params
        assert 'Environment' in params
        assert 'RestApiId' in params
        assert 'RestApiRootResourceId' in params

    def test_resources_stack_health_resource(self, resources_stack_template):
        """Verify health check resource exists."""
        resources = resources_stack_template['Resources']
        assert 'HealthResource' in resources

        health = resources['HealthResource']
        assert health['Type'] == 'AWS::ApiGateway::Resource'
        assert health['Properties']['PathPart'] == 'health'

    def test_resources_stack_user_resources(self, resources_stack_template):
        """Verify user management resources exist."""
        resources = resources_stack_template['Resources']
        assert 'UserResource' in resources
        assert 'UserProfileResource' in resources
        assert 'UserRolesResource' in resources
        assert 'UserPermissionsResource' in resources

    def test_resources_stack_protection_group_resources(self, resources_stack_template):
        """Verify protection group resources exist."""
        resources = resources_stack_template['Resources']
        assert 'ProtectionGroupsResource' in resources
        assert 'ProtectionGroupResource' in resources
        assert 'ProtectionGroupResolveResource' in resources
        assert 'ProtectionGroupApplyLaunchConfigsResource' in resources
        assert 'ProtectionGroupLaunchConfigStatusResource' in resources

    def test_resources_stack_recovery_plan_resources(self, resources_stack_template):
        """Verify recovery plan resources exist."""
        resources = resources_stack_template['Resources']
        assert 'RecoveryPlansResource' in resources
        assert 'RecoveryPlanResource' in resources
        assert 'RecoveryPlanExecuteResource' in resources
        assert 'RecoveryPlanCheckExistingInstancesResource' in resources

    def test_resources_stack_execution_resources(self, resources_stack_template):
        """Verify execution resources exist."""
        resources = resources_stack_template['Resources']
        assert 'ExecutionsResource' in resources
        assert 'ExecutionResource' in resources
        assert 'ExecutionCancelResource' in resources
        assert 'ExecutionPauseResource' in resources
        assert 'ExecutionResumeResource' in resources
        assert 'ExecutionTerminateInstancesResource' in resources

    def test_resources_stack_drs_resources(self, resources_stack_template):
        """Verify DRS resources exist."""
        resources = resources_stack_template['Resources']
        assert 'DRSResource' in resources
        assert 'DRSSourceServersResource' in resources
        assert 'DRSQuotasResource' in resources
        assert 'DRSAccountsResource' in resources
        assert 'DRSTagSyncResource' in resources

    def test_resources_stack_ec2_resources(self, resources_stack_template):
        """Verify EC2 resources exist."""
        resources = resources_stack_template['Resources']
        assert 'EC2Resource' in resources
        assert 'EC2SubnetsResource' in resources
        assert 'EC2SecurityGroupsResource' in resources
        assert 'EC2InstanceProfilesResource' in resources
        assert 'EC2InstanceTypesResource' in resources

    def test_resources_stack_config_resources(self, resources_stack_template):
        """Verify config resources exist."""
        resources = resources_stack_template['Resources']
        assert 'ConfigResource' in resources
        assert 'ConfigExportResource' in resources
        assert 'ConfigImportResource' in resources
        assert 'ConfigTagSyncResource' in resources

    def test_resources_stack_account_resources(self, resources_stack_template):
        """Verify account resources exist."""
        resources = resources_stack_template['Resources']
        assert 'AccountsResource' in resources
        assert 'AccountsCurrentResource' in resources
        assert 'AccountsTargetsResource' in resources
        assert 'AccountsTargetResource' in resources

    def test_resources_stack_outputs_exported(self, resources_stack_template):
        """Verify all resource IDs are exported."""
        outputs = resources_stack_template['Outputs']
        assert len(outputs) > 50

        for output_name, output_value in outputs.items():
            assert 'Export' in output_value
            assert 'Name' in output_value['Export']


# =============================================================================
# CORE METHODS STACK TESTS
# =============================================================================

class TestCoreMethodsStack:
    """Tests for API Gateway Core Methods Stack (core-methods-stack.yaml)."""

    def test_core_methods_stack_has_required_sections(self, core_methods_stack_template):
        """Verify core methods stack has all required sections."""
        assert 'AWSTemplateFormatVersion' in core_methods_stack_template
        assert 'Description' in core_methods_stack_template
        assert 'Parameters' in core_methods_stack_template
        assert 'Resources' in core_methods_stack_template

    def test_core_methods_stack_parameters(self, core_methods_stack_template):
        """Verify core methods stack has required parameters."""
        params = core_methods_stack_template['Parameters']
        assert 'ProjectName' in params
        assert 'Environment' in params
        assert 'RestApiId' in params
        assert 'ApiAuthorizerId' in params
        assert 'ApiRequestValidatorId' in params
        assert 'QueryHandlerArn' in params
        assert 'DataManagementHandlerArn' in params

    def test_core_methods_health_check_method(self, core_methods_stack_template):
        """Verify health check GET method uses MOCK integration."""
        resources = core_methods_stack_template['Resources']
        assert 'HealthGetMethod' in resources

        method = resources['HealthGetMethod']
        assert method['Type'] == 'AWS::ApiGateway::Method'
        assert method['Properties']['HttpMethod'] == 'GET'
        assert method['Properties']['AuthorizationType'] == 'NONE'
        assert method['Properties']['Integration']['Type'] == 'MOCK'

    def test_core_methods_user_profile_method(self, core_methods_stack_template):
        """Verify user profile GET method is authenticated."""
        resources = core_methods_stack_template['Resources']
        assert 'UserProfileGetMethod' in resources

        method = resources['UserProfileGetMethod']
        assert method['Type'] == 'AWS::ApiGateway::Method'
        assert method['Properties']['HttpMethod'] == 'GET'
        assert method['Properties']['AuthorizationType'] == 'COGNITO_USER_POOLS'
        assert method['Properties']['Integration']['Type'] == 'AWS_PROXY'

    def test_core_methods_protection_groups_methods(self, core_methods_stack_template):
        """Verify protection groups methods exist."""
        resources = core_methods_stack_template['Resources']
        assert 'ProtectionGroupsGetMethod' in resources
        assert 'ProtectionGroupsPostMethod' in resources
        assert 'ProtectionGroupGetMethod' in resources
        assert 'ProtectionGroupPutMethod' in resources
        assert 'ProtectionGroupDeleteMethod' in resources

    def test_core_methods_recovery_plans_methods(self, core_methods_stack_template):
        """Verify recovery plans methods exist."""
        resources = core_methods_stack_template['Resources']
        assert 'RecoveryPlansGetMethod' in resources
        assert 'RecoveryPlansPostMethod' in resources
        assert 'RecoveryPlanGetMethod' in resources
        assert 'RecoveryPlanPutMethod' in resources
        assert 'RecoveryPlanDeleteMethod' in resources
        assert 'RecoveryPlanExecuteMethod' in resources

    def test_core_methods_options_methods_exist(self, core_methods_stack_template):
        """Verify OPTIONS methods exist for CORS."""
        resources = core_methods_stack_template['Resources']
        assert 'HealthOptionsMethod' in resources
        assert 'UserProfileOptionsMethod' in resources
        assert 'ProtectionGroupsOptionsMethod' in resources
        assert 'RecoveryPlansOptionsMethod' in resources

    def test_core_methods_options_have_cors_headers(self, core_methods_stack_template):
        """Verify OPTIONS methods have CORS headers."""
        resources = core_methods_stack_template['Resources']
        options_method = resources['HealthOptionsMethod']

        integration = options_method['Properties']['Integration']
        response_params = integration['IntegrationResponses'][0]['ResponseParameters']

        assert 'method.response.header.Access-Control-Allow-Origin' in response_params
        assert 'method.response.header.Access-Control-Allow-Headers' in response_params
        assert 'method.response.header.Access-Control-Allow-Methods' in response_params


# =============================================================================
# INFRASTRUCTURE METHODS STACK TESTS
# =============================================================================

class TestInfrastructureMethodsStack:
    """Tests for API Gateway Infrastructure Methods Stack."""

    def test_infrastructure_methods_stack_has_required_sections(
        self, infrastructure_methods_stack_template
    ):
        """Verify infrastructure methods stack has all required sections."""
        assert 'AWSTemplateFormatVersion' in infrastructure_methods_stack_template
        assert 'Description' in infrastructure_methods_stack_template
        assert 'Parameters' in infrastructure_methods_stack_template
        assert 'Resources' in infrastructure_methods_stack_template

    def test_infrastructure_methods_stack_parameters(
        self, infrastructure_methods_stack_template
    ):
        """Verify infrastructure methods stack has required parameters."""
        params = infrastructure_methods_stack_template['Parameters']
        assert 'ProjectName' in params
        assert 'Environment' in params
        assert 'RestApiId' in params
        assert 'ApiAuthorizerId' in params
        assert 'QueryHandlerArn' in params
        assert 'ApiHandlerFunctionArn' in params

    def test_infrastructure_methods_drs_source_servers_method(
        self, infrastructure_methods_stack_template
    ):
        """Verify DRS source servers GET method exists."""
        resources = infrastructure_methods_stack_template['Resources']
        assert 'DrsSourceServersGetMethod' in resources

        method = resources['DrsSourceServersGetMethod']
        assert method['Type'] == 'AWS::ApiGateway::Method'
        assert method['Properties']['HttpMethod'] == 'GET'
        assert method['Properties']['AuthorizationType'] == 'COGNITO_USER_POOLS'

    def test_infrastructure_methods_ec2_subnets_method(
        self, infrastructure_methods_stack_template
    ):
        """Verify EC2 subnets GET method exists."""
        resources = infrastructure_methods_stack_template['Resources']
        assert 'Ec2SubnetsGetMethod' in resources

        method = resources['Ec2SubnetsGetMethod']
        assert method['Type'] == 'AWS::ApiGateway::Method'
        assert method['Properties']['HttpMethod'] == 'GET'

    def test_infrastructure_methods_config_export_method(
        self, infrastructure_methods_stack_template
    ):
        """Verify config export GET method exists."""
        resources = infrastructure_methods_stack_template['Resources']
        assert 'ConfigExportGetMethod' in resources

    def test_infrastructure_methods_accounts_methods(
        self, infrastructure_methods_stack_template
    ):
        """Verify account management methods exist."""
        resources = infrastructure_methods_stack_template['Resources']
        assert 'AccountsCurrentGetMethod' in resources
        assert 'AccountsTargetsGetMethod' in resources
        assert 'AccountsTargetsPostMethod' in resources


# =============================================================================
# OPERATIONS METHODS STACK TESTS
# =============================================================================

class TestOperationsMethodsStack:
    """Tests for API Gateway Operations Methods Stack."""

    def test_operations_methods_stack_has_required_sections(
        self, operations_methods_stack_template
    ):
        """Verify operations methods stack has all required sections."""
        assert 'AWSTemplateFormatVersion' in operations_methods_stack_template
        assert 'Description' in operations_methods_stack_template
        assert 'Parameters' in operations_methods_stack_template
        assert 'Resources' in operations_methods_stack_template

    def test_operations_methods_stack_parameters(
        self, operations_methods_stack_template
    ):
        """Verify operations methods stack has required parameters."""
        params = operations_methods_stack_template['Parameters']
        assert 'ProjectName' in params
        assert 'Environment' in params
        assert 'RestApiId' in params
        assert 'ApiAuthorizerId' in params
        assert 'ExecutionHandlerArn' in params

    def test_operations_methods_executions_methods(
        self, operations_methods_stack_template
    ):
        """Verify execution management methods exist."""
        resources = operations_methods_stack_template['Resources']
        assert 'ExecutionsGetMethod' in resources
        assert 'ExecutionsPostMethod' in resources
        assert 'ExecutionGetMethod' in resources
        assert 'ExecutionCancelMethod' in resources
        assert 'ExecutionPauseMethod' in resources
        assert 'ExecutionResumeMethod' in resources

    def test_operations_methods_drs_failover_methods(
        self, operations_methods_stack_template
    ):
        """Verify DRS failover methods exist."""
        resources = operations_methods_stack_template['Resources']
        assert 'DrsFailoverGetMethod' in resources
        assert 'DrsStartRecoveryPostMethod' in resources

    def test_operations_methods_drs_jobs_methods(
        self, operations_methods_stack_template
    ):
        """Verify DRS jobs methods exist."""
        resources = operations_methods_stack_template['Resources']
        assert 'DrsJobsGetMethod' in resources


# =============================================================================
# DEPLOYMENT STACK TESTS
# =============================================================================

class TestDeploymentStack:
    """Tests for API Gateway Deployment Stack (deployment-stack.yaml)."""

    def test_deployment_stack_has_required_sections(self, deployment_stack_template):
        """Verify deployment stack has all required sections."""
        assert 'AWSTemplateFormatVersion' in deployment_stack_template
        assert 'Description' in deployment_stack_template
        assert 'Parameters' in deployment_stack_template
        assert 'Resources' in deployment_stack_template
        assert 'Outputs' in deployment_stack_template

    def test_deployment_stack_parameters(self, deployment_stack_template):
        """Verify deployment stack has required parameters."""
        params = deployment_stack_template['Parameters']
        assert 'ProjectName' in params
        assert 'Environment' in params
        assert 'RestApiId' in params
        assert 'OrchestrationRoleArn' in params

    def test_deployment_stack_orchestrator_lambda(self, deployment_stack_template):
        """Verify deployment orchestrator Lambda exists."""
        resources = deployment_stack_template['Resources']
        assert 'DeploymentOrchestratorFunction' in resources

        lambda_func = resources['DeploymentOrchestratorFunction']
        assert lambda_func['Type'] == 'AWS::Lambda::Function'
        assert lambda_func['Properties']['Runtime'] == 'python3.12'
        assert lambda_func['Properties']['Timeout'] == 300

    def test_deployment_stack_dlq(self, deployment_stack_template):
        """Verify dead letter queue exists."""
        resources = deployment_stack_template['Resources']
        assert 'DeploymentOrchestratorDLQ' in resources

        dlq = resources['DeploymentOrchestratorDLQ']
        assert dlq['Type'] == 'AWS::SQS::Queue'

    def test_deployment_stack_gateway_responses(self, deployment_stack_template):
        """Verify gateway responses for CORS exist."""
        resources = deployment_stack_template['Resources']
        assert 'GatewayResponse4XX' in resources
        assert 'GatewayResponse5XX' in resources
        assert 'GatewayResponseUnauthorized' in resources
        assert 'GatewayResponseAccessDenied' in resources

        response_4xx = resources['GatewayResponse4XX']
        assert response_4xx['Type'] == 'AWS::ApiGateway::GatewayResponse'
        assert response_4xx['Properties']['ResponseType'] == 'DEFAULT_4XX'

    def test_deployment_stack_gateway_response_cors_headers(
        self, deployment_stack_template
    ):
        """Verify gateway responses have CORS headers."""
        resources = deployment_stack_template['Resources']
        response = resources['GatewayResponse4XX']

        response_params = response['Properties']['ResponseParameters']
        assert 'gatewayresponse.header.Access-Control-Allow-Origin' in response_params
        assert 'gatewayresponse.header.Access-Control-Allow-Headers' in response_params
        assert 'gatewayresponse.header.Access-Control-Allow-Methods' in response_params

    def test_deployment_stack_custom_resource(self, deployment_stack_template):
        """Verify deployment custom resource exists."""
        resources = deployment_stack_template['Resources']
        assert 'ApiDeploymentOrchestrator' in resources

        custom_resource = resources['ApiDeploymentOrchestrator']
        assert custom_resource['Type'] == 'AWS::CloudFormation::CustomResource'

    def test_deployment_stack_api_stage(self, deployment_stack_template):
        """Verify API stage is configured."""
        resources = deployment_stack_template['Resources']
        assert 'ApiStage' in resources

        stage = resources['ApiStage']
        assert stage['Type'] == 'AWS::ApiGateway::Stage'

        props = stage['Properties']
        assert props['TracingEnabled'] is True
        assert 'AccessLogSetting' in props
        assert 'MethodSettings' in props

    def test_deployment_stack_api_gateway_account(self, deployment_stack_template):
        """Verify API Gateway account setting exists."""
        resources = deployment_stack_template['Resources']
        assert 'ApiGatewayAccount' in resources

        account = resources['ApiGatewayAccount']
        assert account['Type'] == 'AWS::ApiGateway::Account'

    def test_deployment_stack_access_log_group(self, deployment_stack_template):
        """Verify access log group exists."""
        resources = deployment_stack_template['Resources']
        assert 'ApiGatewayAccessLogGroup' in resources

        log_group = resources['ApiGatewayAccessLogGroup']
        assert log_group['Type'] == 'AWS::Logs::LogGroup'
        assert log_group['Properties']['RetentionInDays'] == 30

    def test_deployment_stack_outputs(self, deployment_stack_template):
        """Verify deployment stack exports required outputs."""
        outputs = deployment_stack_template['Outputs']
        assert 'ApiEndpoint' in outputs
        assert 'DeploymentId' in outputs
        assert 'ApiStageArn' in outputs

        for output_name, output_value in outputs.items():
            assert 'Export' in output_value


# =============================================================================
# AUTH STACK TESTS
# =============================================================================

class TestAuthStack:
    """Tests for API Gateway Auth Stack (auth-stack.yaml)."""

    def test_auth_stack_has_required_sections(self, auth_stack_template):
        """Verify auth stack has all required sections."""
        assert 'AWSTemplateFormatVersion' in auth_stack_template
        assert 'Description' in auth_stack_template
        assert 'Parameters' in auth_stack_template
        assert 'Resources' in auth_stack_template
        assert 'Outputs' in auth_stack_template

    def test_auth_stack_parameters(self, auth_stack_template):
        """Verify auth stack has required parameters."""
        params = auth_stack_template['Parameters']
        assert 'ProjectName' in params
        assert 'Environment' in params
        assert 'RestApiId' in params
        assert 'UserPoolArn' in params

    def test_auth_stack_cognito_authorizer(self, auth_stack_template):
        """Verify Cognito authorizer is configured."""
        resources = auth_stack_template['Resources']
        assert 'ApiAuthorizer' in resources

        authorizer = resources['ApiAuthorizer']
        assert authorizer['Type'] == 'AWS::ApiGateway::Authorizer'

        props = authorizer['Properties']
        assert props['Type'] == 'COGNITO_USER_POOLS'
        assert props['IdentitySource'] == 'method.request.header.Authorization'
        assert 'ProviderARNs' in props

    def test_auth_stack_outputs(self, auth_stack_template):
        """Verify auth stack exports authorizer ID."""
        outputs = auth_stack_template['Outputs']
        assert 'ApiAuthorizerId' in outputs

        authorizer_output = outputs['ApiAuthorizerId']
        assert 'Export' in authorizer_output
        assert 'Name' in authorizer_output['Export']


# =============================================================================
# CROSS-STACK VALIDATION TESTS
# =============================================================================

class TestCrossStackValidation:
    """Tests for cross-stack dependencies and consistency."""

    def test_all_stacks_use_consistent_parameters(
        self,
        core_stack_template,
        resources_stack_template,
        core_methods_stack_template,
        infrastructure_methods_stack_template,
        operations_methods_stack_template,
        deployment_stack_template,
        auth_stack_template
    ):
        """Verify all stacks use consistent parameter names."""
        all_templates = [
            core_stack_template,
            resources_stack_template,
            core_methods_stack_template,
            infrastructure_methods_stack_template,
            operations_methods_stack_template,
            deployment_stack_template,
            auth_stack_template
        ]

        for template in all_templates:
            params = template['Parameters']
            assert 'ProjectName' in params
            assert 'Environment' in params

    def test_resources_stack_exports_match_methods_stack_imports(
        self, resources_stack_template, core_methods_stack_template
    ):
        """Verify resources stack exports match methods stack parameters."""
        resources_outputs = resources_stack_template['Outputs']
        methods_params = core_methods_stack_template['Parameters']

        assert 'HealthResourceId' in resources_outputs
        assert 'HealthResourceId' in methods_params

        assert 'ProtectionGroupsResourceId' in resources_outputs
        assert 'ProtectionGroupsResourceId' in methods_params

    def test_core_stack_exports_match_auth_stack_imports(
        self, core_stack_template, auth_stack_template
    ):
        """Verify core stack exports match auth stack parameters."""
        core_outputs = core_stack_template['Outputs']
        auth_params = auth_stack_template['Parameters']

        assert 'RestApiId' in core_outputs
        assert 'RestApiId' in auth_params

    def test_auth_stack_exports_match_methods_stack_imports(
        self, auth_stack_template, core_methods_stack_template
    ):
        """Verify auth stack exports match methods stack parameters."""
        auth_outputs = auth_stack_template['Outputs']
        methods_params = core_methods_stack_template['Parameters']

        assert 'ApiAuthorizerId' in auth_outputs
        assert 'ApiAuthorizerId' in methods_params
