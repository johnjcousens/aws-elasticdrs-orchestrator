"""
Unit tests for deploy-main-stack.sh deployment script validation.

This module validates the deploy-main-stack.sh script behavior including:
- Script argument parsing and validation
- Environment variable handling
- AWS credential verification
- CloudFormation template validation
- Deployment bucket operations
- Stack deployment with different parameters
- Error handling and rollback scenarios

Uses mocking to avoid actual AWS deployments.

Validates Requirements:
- 17.18: Deployment script validation
"""

import os
import subprocess
import pytest
from unittest.mock import Mock, patch, MagicMock, call


# Test fixtures
@pytest.fixture
def mock_aws_credentials():
    """Mock AWS credentials and account ID."""
    with patch("subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "438465159935"
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def script_path():
    """Return path to deploy-main-stack.sh script."""
    return os.path.join(
        os.path.dirname(__file__), "..", "..", "scripts", "deploy-main-stack.sh"
    )


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    env = {
        "AWS_REGION": "us-east-2",
        "PROJECT_NAME": "aws-drs-orchestration",
        "AWS_PROFILE": "AdministratorAccess-438465159935",
    }
    return env



class TestScriptArgumentParsing:
    """Test suite for script argument parsing and validation."""

    def test_script_exists(self, script_path):
        """Test that deploy-main-stack.sh script exists."""
        assert os.path.exists(script_path), "deploy-main-stack.sh should exist"
        assert os.path.isfile(script_path), "deploy-main-stack.sh should be a file"

    def test_script_is_executable(self, script_path):
        """Test that deploy-main-stack.sh has execute permissions."""
        assert os.access(script_path, os.X_OK), "deploy-main-stack.sh should be executable"

    @patch("subprocess.run")
    def test_default_environment_parameter(self, mock_run, script_path):
        """Test that script defaults to 'test' environment when no argument provided."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="")
        
        # Script should use 'test' as default environment
        # We can't easily test this without running the script, so we verify the script content
        with open(script_path, "r") as f:
            content = f.read()
            assert 'ENVIRONMENT="${1:-test}"' in content, (
                "Script should default to 'test' environment"
            )

    def test_script_accepts_environment_argument(self, script_path):
        """Test that script accepts environment as first argument."""
        with open(script_path, "r") as f:
            content = f.read()
            # Verify script reads first argument as environment
            assert 'ENVIRONMENT="${1' in content, (
                "Script should accept environment as first argument"
            )

    def test_script_supports_lambda_only_flag(self, script_path):
        """Test that script supports --lambda-only flag."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "--lambda-only" in content, "Script should support --lambda-only flag"
            assert "LAMBDA_ONLY=true" in content, "Script should set LAMBDA_ONLY variable"

    def test_script_supports_frontend_only_flag(self, script_path):
        """Test that script supports --frontend-only flag."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "--frontend-only" in content, "Script should support --frontend-only flag"
            assert "FRONTEND_ONLY=true" in content, "Script should set FRONTEND_ONLY variable"

    def test_script_supports_validate_only_flag(self, script_path):
        """Test that script supports --validate-only flag."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "--validate-only" in content, "Script should support --validate-only flag"
            assert "VALIDATE_ONLY=true" in content, "Script should set VALIDATE_ONLY variable"

    def test_script_supports_use_function_specific_roles_flag(self, script_path):
        """Test that script supports --use-function-specific-roles flag."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "--use-function-specific-roles" in content, (
                "Script should support --use-function-specific-roles flag"
            )
            assert 'USE_FUNCTION_SPECIFIC_ROLES="true"' in content, (
                "Script should set USE_FUNCTION_SPECIFIC_ROLES to true"
            )

    def test_script_supports_force_flag(self, script_path):
        """Test that script supports --force flag."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "--force" in content, "Script should support --force flag"
            assert "FORCE=true" in content, "Script should set FORCE variable"

    def test_script_supports_orchestration_role_parameter(self, script_path):
        """Test that script supports --orchestration-role parameter."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "--orchestration-role" in content, (
                "Script should support --orchestration-role parameter"
            )
            assert "ORCHESTRATION_ROLE_ARN=" in content, (
                "Script should set ORCHESTRATION_ROLE_ARN variable"
            )



class TestEnvironmentVariableHandling:
    """Test suite for environment variable handling and defaults."""

    def test_script_uses_aws_region_environment_variable(self, script_path):
        """Test that script uses AWS_REGION environment variable."""
        with open(script_path, "r") as f:
            content = f.read()
            assert 'AWS_REGION="${AWS_REGION:-us-east-2}"' in content, (
                "Script should use AWS_REGION environment variable with default"
            )

    def test_script_uses_project_name_environment_variable(self, script_path):
        """Test that script uses PROJECT_NAME environment variable."""
        with open(script_path, "r") as f:
            content = f.read()
            assert 'PROJECT_NAME="${PROJECT_NAME:-aws-drs-orchestration}"' in content, (
                "Script should use PROJECT_NAME environment variable with default"
            )

    def test_script_uses_admin_email_environment_variable(self, script_path):
        """Test that script uses ADMIN_EMAIL environment variable."""
        with open(script_path, "r") as f:
            content = f.read()
            assert 'ADMIN_EMAIL="${ADMIN_EMAIL' in content, (
                "Script should use ADMIN_EMAIL environment variable"
            )

    def test_script_uses_enable_notifications_environment_variable(self, script_path):
        """Test that script uses ENABLE_NOTIFICATIONS environment variable."""
        with open(script_path, "r") as f:
            content = f.read()
            assert 'ENABLE_NOTIFICATIONS="${ENABLE_NOTIFICATIONS:-true}"' in content, (
                "Script should use ENABLE_NOTIFICATIONS with default true"
            )

    def test_script_uses_use_function_specific_roles_environment_variable(self, script_path):
        """Test that script uses USE_FUNCTION_SPECIFIC_ROLES environment variable."""
        with open(script_path, "r") as f:
            content = f.read()
            assert 'USE_FUNCTION_SPECIFIC_ROLES="${USE_FUNCTION_SPECIFIC_ROLES:-false}"' in content, (
                "Script should use USE_FUNCTION_SPECIFIC_ROLES with default false"
            )

    def test_script_constructs_deployment_bucket_with_account_id(self, script_path):
        """Test that script constructs deployment bucket name with AWS account ID."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "AWS_ACCOUNT_ID=$(aws sts get-caller-identity" in content, (
                "Script should get AWS account ID"
            )
            assert "${PROJECT_NAME}-${AWS_ACCOUNT_ID}-${ENVIRONMENT}" in content, (
                "Script should construct deployment bucket with account ID"
            )

    def test_script_constructs_stack_name_from_project_and_environment(self, script_path):
        """Test that script constructs stack name from project name and environment."""
        with open(script_path, "r") as f:
            content = f.read()
            assert 'STACK_NAME="${STACK_NAME:-${PROJECT_NAME}-${ENVIRONMENT}}"' in content, (
                "Script should construct stack name from project and environment"
            )



class TestAWSCredentialVerification:
    """Test suite for AWS credential verification."""

    def test_script_verifies_aws_credentials(self, script_path):
        """Test that script verifies AWS credentials before proceeding."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "aws sts get-caller-identity" in content, (
                "Script should verify AWS credentials using STS"
            )

    def test_script_handles_expired_sso_session(self, script_path):
        """Test that script handles expired SSO session."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "SSO session" in content or "expired" in content, (
                "Script should check for expired SSO session"
            )
            assert "aws sso login" in content, (
                "Script should attempt SSO login when session expired"
            )

    def test_script_validates_account_id_format(self, script_path):
        """Test that script validates AWS account ID format (12 digits)."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "[0-9]{12}" in content, (
                "Script should validate account ID is 12 digits"
            )

    def test_script_exits_on_credential_failure(self, script_path):
        """Test that script exits when AWS credentials fail."""
        with open(script_path, "r") as f:
            content = f.read()
            # Find the credential check section
            assert "AWS credentials failed" in content, (
                "Script should report credential failure"
            )
            # Verify exit after credential failure
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "AWS credentials failed" in line:
                    # Check next few lines for exit
                    next_lines = "\n".join(lines[i:i+5])
                    assert "exit 1" in next_lines, (
                        "Script should exit after credential failure"
                    )
                    break

    def test_script_sets_aws_profile_if_not_set(self, script_path):
        """Test that script sets AWS_PROFILE if not already set."""
        with open(script_path, "r") as f:
            content = f.read()
            assert 'if [ -z "$AWS_PROFILE" ]' in content, (
                "Script should check if AWS_PROFILE is set"
            )
            assert 'export AWS_PROFILE=' in content, (
                "Script should set AWS_PROFILE if not set"
            )



class TestCloudFormationTemplateValidation:
    """Test suite for CloudFormation template validation."""

    def test_script_runs_cfn_lint_validation(self, script_path):
        """Test that script runs cfn-lint validation on templates."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "cfn-lint" in content, "Script should run cfn-lint"
            assert "cfn/*.yaml" in content or "cfn/**/*.yaml" in content, (
                "Script should validate CloudFormation templates"
            )

    def test_script_checks_for_cfn_lint_in_venv(self, script_path):
        """Test that script checks for cfn-lint in virtual environment."""
        with open(script_path, "r") as f:
            content = f.read()
            assert ".venv/bin/cfn-lint" in content, (
                "Script should check for cfn-lint in .venv"
            )

    def test_script_counts_cfn_lint_errors(self, script_path):
        """Test that script counts cfn-lint errors."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "ERR_COUNT" in content or "grep -c" in content, (
                "Script should count cfn-lint errors"
            )

    def test_script_fails_on_cfn_lint_errors(self, script_path):
        """Test that script fails when cfn-lint reports errors."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "FAILED=true" in content, (
                "Script should set FAILED flag on validation errors"
            )

    def test_script_runs_flake8_on_python_code(self, script_path):
        """Test that script runs flake8 on Python code."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "flake8" in content, "Script should run flake8"
            assert "lambda/" in content, "Script should check lambda directory"

    def test_script_runs_black_formatting_check(self, script_path):
        """Test that script runs black formatting check."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "black" in content, "Script should run black"
            assert "--check" in content, "Script should run black in check mode"

    def test_script_runs_typescript_type_checking(self, script_path):
        """Test that script runs TypeScript type checking."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "type-check" in content or "tsc" in content, (
                "Script should run TypeScript type checking"
            )

    def test_script_validates_nested_stack_templates_exist(self, script_path):
        """Test that script validates nested stack templates exist in S3."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "Validating nested stack templates" in content, (
                "Script should validate nested stack templates"
            )
            assert "aws s3api head-object" in content, (
                "Script should check if templates exist in S3"
            )
            assert "roles-stack.yaml" in content, (
                "Script should check for IAM roles stack"
            )
            assert "functions-stack.yaml" in content, (
                "Script should check for Lambda functions stack"
            )



class TestDeploymentBucketOperations:
    """Test suite for deployment bucket operations."""

    def test_script_creates_deployment_bucket_if_not_exists(self, script_path):
        """Test that script creates deployment bucket if it doesn't exist."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "aws s3api head-bucket" in content, (
                "Script should check if bucket exists"
            )
            assert "aws s3api create-bucket" in content, (
                "Script should create bucket if not exists"
            )

    def test_script_handles_bucket_creation_retry(self, script_path):
        """Test that script retries bucket creation on conflict."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "RETRY_COUNT" in content, (
                "Script should implement retry logic"
            )
            assert "MAX_RETRIES" in content, (
                "Script should have maximum retry limit"
            )

    def test_script_enables_bucket_versioning(self, script_path):
        """Test that script enables versioning on deployment bucket."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "put-bucket-versioning" in content, (
                "Script should enable bucket versioning"
            )
            assert "Status=Enabled" in content, (
                "Script should set versioning status to Enabled"
            )

    def test_script_syncs_nested_stack_templates_to_s3(self, script_path):
        """Test that script syncs nested stack templates to S3."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "Syncing nested stack templates" in content, (
                "Script should sync nested stack templates"
            )
            assert "aws s3 sync cfn/iam/" in content, (
                "Script should sync IAM templates"
            )
            assert "aws s3 sync cfn/lambda/" in content, (
                "Script should sync Lambda templates"
            )
            assert "aws s3 sync cfn/dynamodb/" in content, (
                "Script should sync DynamoDB templates"
            )

    def test_script_syncs_main_stack_template_to_s3(self, script_path):
        """Test that script syncs main-stack.yaml to S3."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "aws s3 cp cfn/main-stack.yaml" in content, (
                "Script should copy main-stack.yaml to S3"
            )

    def test_script_syncs_lambda_packages_to_s3(self, script_path):
        """Test that script syncs Lambda packages to S3."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "aws s3 sync build/lambda/" in content, (
                "Script should sync Lambda packages"
            )
            assert "--delete" in content, (
                "Script should use --delete flag to remove old packages"
            )

    def test_script_uses_correct_region_for_bucket_creation(self, script_path):
        """Test that script uses correct region for bucket creation."""
        with open(script_path, "r") as f:
            content = f.read()
            # Check for region-specific bucket creation logic
            assert "us-east-1" in content, (
                "Script should handle us-east-1 special case"
            )
            assert "LocationConstraint" in content, (
                "Script should set LocationConstraint for non-us-east-1 regions"
            )



class TestStackDeploymentParameters:
    """Test suite for stack deployment with different parameters."""

    def test_script_deploys_with_main_stack_template(self, script_path):
        """Test that script deploys using main-stack.yaml template."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "aws cloudformation deploy" in content, (
                "Script should use CloudFormation deploy command"
            )
            assert "cfn/main-stack.yaml" in content, (
                "Script should deploy main-stack.yaml"
            )

    def test_script_passes_project_name_parameter(self, script_path):
        """Test that script passes ProjectName parameter to CloudFormation."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "ProjectName=" in content, (
                "Script should pass ProjectName parameter"
            )
            assert "$PROJECT_NAME" in content, (
                "Script should use PROJECT_NAME variable"
            )

    def test_script_passes_environment_parameter(self, script_path):
        """Test that script passes Environment parameter to CloudFormation."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "Environment=" in content, (
                "Script should pass Environment parameter"
            )
            assert "$ENVIRONMENT" in content, (
                "Script should use ENVIRONMENT variable"
            )

    def test_script_passes_deployment_bucket_parameter(self, script_path):
        """Test that script passes DeploymentBucket parameter to CloudFormation."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "DeploymentBucket=" in content, (
                "Script should pass DeploymentBucket parameter"
            )
            assert "$DEPLOYMENT_BUCKET" in content, (
                "Script should use DEPLOYMENT_BUCKET variable"
            )

    def test_script_passes_use_function_specific_roles_parameter(self, script_path):
        """Test that script passes UseFunctionSpecificRoles parameter to CloudFormation."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "UseFunctionSpecificRoles=" in content, (
                "Script should pass UseFunctionSpecificRoles parameter"
            )
            assert "$USE_FUNCTION_SPECIFIC_ROLES" in content, (
                "Script should use USE_FUNCTION_SPECIFIC_ROLES variable"
            )

    def test_script_passes_admin_email_parameter(self, script_path):
        """Test that script passes AdminEmail parameter to CloudFormation."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "AdminEmail=" in content, (
                "Script should pass AdminEmail parameter"
            )

    def test_script_passes_enable_notifications_parameter(self, script_path):
        """Test that script passes EnableNotifications parameter to CloudFormation."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "EnableNotifications=" in content, (
                "Script should pass EnableNotifications parameter"
            )

    def test_script_generates_lambda_code_version(self, script_path):
        """Test that script generates LambdaCodeVersion parameter."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "LAMBDA_CODE_VERSION=" in content, (
                "Script should generate Lambda code version"
            )
            assert "LambdaCodeVersion=" in content, (
                "Script should pass LambdaCodeVersion parameter"
            )

    def test_script_generates_frontend_version(self, script_path):
        """Test that script generates FrontendBuildVersion parameter."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "FRONTEND_VERSION=" in content, (
                "Script should generate frontend version"
            )
            assert "FrontendBuildVersion=" in content, (
                "Script should pass FrontendBuildVersion parameter"
            )

    def test_script_uses_capability_named_iam(self, script_path):
        """Test that script uses CAPABILITY_NAMED_IAM for IAM resource creation."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "CAPABILITY_NAMED_IAM" in content, (
                "Script should use CAPABILITY_NAMED_IAM capability"
            )

    def test_script_uses_no_fail_on_empty_changeset(self, script_path):
        """Test that script uses --no-fail-on-empty-changeset flag."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "--no-fail-on-empty-changeset" in content, (
                "Script should use --no-fail-on-empty-changeset flag"
            )



class TestErrorHandlingAndRollback:
    """Test suite for error handling and rollback scenarios."""

    def test_script_checks_stack_status_before_deployment(self, script_path):
        """Test that script checks stack status before deployment."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "aws cloudformation describe-stacks" in content, (
                "Script should check stack status"
            )
            assert "STACK_STATUS=" in content, (
                "Script should capture stack status"
            )

    def test_script_prevents_concurrent_deployments(self, script_path):
        """Test that script prevents concurrent deployments to same stack."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "IN_PROGRESS" in content, (
                "Script should check for IN_PROGRESS status"
            )
            assert "currently being updated" in content or "CLEANUP" in content, (
                "Script should prevent concurrent updates"
            )

    def test_script_uses_lock_file_for_concurrency_protection(self, script_path):
        """Test that script uses lock file to prevent concurrent executions."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "LOCK_FILE=" in content, (
                "Script should define lock file"
            )
            assert "LOCK_PID_FILE=" in content, (
                "Script should define PID file"
            )
            assert "Another deployment is already running" in content, (
                "Script should detect concurrent execution"
            )

    def test_script_cleans_up_lock_file_on_exit(self, script_path):
        """Test that script cleans up lock file on exit."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "cleanup_lock" in content, (
                "Script should define cleanup function"
            )
            assert "trap cleanup_lock EXIT" in content, (
                "Script should trap EXIT signal"
            )

    def test_script_exits_on_validation_failure(self, script_path):
        """Test that script exits when validation fails."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "FAILED=true" in content, (
                "Script should set FAILED flag"
            )
            assert "Validation failed" in content, (
                "Script should report validation failure"
            )
            # Verify exit after validation failure
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "Validation failed" in line:
                    next_lines = "\n".join(lines[i:i+5])
                    assert "exit 1" in next_lines, (
                        "Script should exit after validation failure"
                    )
                    break

    def test_script_exits_early_on_validate_only_mode(self, script_path):
        """Test that script exits after validation when --validate-only is used."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "VALIDATE_ONLY=true" in content, (
                "Script should support validate-only mode"
            )
            assert "Validation Complete" in content, (
                "Script should report validation completion"
            )
            # Verify exit after validation in validate-only mode
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "VALIDATE_ONLY" in line and "true" in line:
                    # Find the exit statement
                    for j in range(i, min(i+50, len(lines))):
                        if "Validation Complete" in lines[j]:
                            next_lines = "\n".join(lines[j:j+5])
                            assert "exit 0" in next_lines, (
                                "Script should exit successfully after validation"
                            )
                            break

    def test_script_handles_missing_nested_stack_templates(self, script_path):
        """Test that script handles missing nested stack templates."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "VALIDATION_FAILED=false" in content or "VALIDATION_FAILED=true" in content, (
                "Script should track validation failures"
            )
            assert "Missing template" in content, (
                "Script should report missing templates"
            )

    def test_script_activates_python_virtual_environment(self, script_path):
        """Test that script activates Python virtual environment if available."""
        with open(script_path, "r") as f:
            content = f.read()
            assert 'if [ -d ".venv" ]' in content, (
                "Script should check for .venv directory"
            )
            assert "source .venv/bin/activate" in content, (
                "Script should activate virtual environment"
            )

    def test_script_handles_missing_virtual_environment(self, script_path):
        """Test that script handles missing virtual environment gracefully."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "Python .venv not found" in content or "using system Python" in content, (
                "Script should warn about missing virtual environment"
            )

    def test_script_runs_security_scans(self, script_path):
        """Test that script runs security scans (bandit, npm audit, etc.)."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "bandit" in content, (
                "Script should run bandit security scan"
            )
            assert "npm audit" in content, (
                "Script should run npm audit"
            )
            assert "detect-secrets" in content, (
                "Script should run detect-secrets"
            )



class TestTestExecution:
    """Test suite for test execution behavior."""

    def test_script_runs_pytest_unit_tests(self, script_path):
        """Test that script runs pytest unit tests."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "pytest" in content, (
                "Script should run pytest"
            )
            assert "tests/unit/" in content, (
                "Script should run unit tests"
            )

    def test_script_supports_skip_tests_flag(self, script_path):
        """Test that script supports --skip-tests flag."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "--skip-tests" in content, (
                "Script should support --skip-tests flag"
            )
            assert "SKIP_TESTS=true" in content, (
                "Script should set SKIP_TESTS variable"
            )
            assert "Tests skipped" in content, (
                "Script should report when tests are skipped"
            )

    def test_script_supports_full_tests_flag(self, script_path):
        """Test that script supports --full-tests flag."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "--full-tests" in content, (
                "Script should support --full-tests flag"
            )
            assert "FULL_TESTS=true" in content, (
                "Script should set FULL_TESTS variable"
            )

    def test_script_runs_property_based_tests_in_full_mode(self, script_path):
        """Test that script runs property-based tests in full test mode."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "--hypothesis-show-statistics" in content, (
                "Script should show hypothesis statistics"
            )
            assert "--forked" in content, (
                "Script should use forked execution for isolation"
            )

    def test_script_runs_fast_tests_by_default(self, script_path):
        """Test that script runs fast tests by default (skips property tests)."""
        with open(script_path, "r") as f:
            content = f.read()
            assert '-m "not property"' in content, (
                "Script should skip property tests in fast mode"
            )

    def test_script_runs_vitest_frontend_tests(self, script_path):
        """Test that script runs vitest frontend tests."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "npm test" in content or "vitest" in content, (
                "Script should run frontend tests"
            )
            assert "--run" in content, (
                "Script should use --run flag for single execution"
            )


class TestGitOperations:
    """Test suite for git operations."""

    def test_script_checks_for_uncommitted_changes(self, script_path):
        """Test that script checks for uncommitted changes."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "git diff --quiet" in content, (
                "Script should check for uncommitted changes"
            )
            assert "git diff --cached --quiet" in content, (
                "Script should check for staged changes"
            )

    def test_script_pushes_to_origin(self, script_path):
        """Test that script pushes changes to origin."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "git push origin HEAD" in content, (
                "Script should push to origin"
            )

    def test_script_handles_push_failure_gracefully(self, script_path):
        """Test that script handles push failure gracefully."""
        with open(script_path, "r") as f:
            content = f.read()
            # Script should not fail on push error
            assert "Push failed or nothing to push" in content, (
                "Script should handle push failure"
            )


class TestLambdaPackaging:
    """Test suite for Lambda packaging operations."""

    def test_script_builds_lambda_packages(self, script_path):
        """Test that script builds Lambda packages."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "python3 package_lambda.py" in content or "Building Lambda packages" in content, (
                "Script should build Lambda packages"
            )

    def test_script_skips_lambda_build_in_frontend_only_mode(self, script_path):
        """Test that script skips Lambda build in frontend-only mode."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "FRONTEND_ONLY=false" in content or 'if [ "$FRONTEND_ONLY" = false ]' in content, (
                "Script should check FRONTEND_ONLY flag"
            )



class TestStackOutputs:
    """Test suite for stack outputs and reporting."""

    def test_script_displays_cloudfront_url(self, script_path):
        """Test that script displays CloudFront URL after deployment."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "CloudFrontURL" in content, (
                "Script should retrieve CloudFront URL from stack outputs"
            )
            assert "Application:" in content, (
                "Script should display application URL"
            )

    def test_script_displays_stack_name(self, script_path):
        """Test that script displays stack name after deployment."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "Stack:" in content, (
                "Script should display stack name"
            )

    def test_script_displays_region(self, script_path):
        """Test that script displays region after deployment."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "Region:" in content, (
                "Script should display region"
            )

    def test_script_displays_function_specific_roles_status(self, script_path):
        """Test that script displays function-specific roles status."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "Function-Specific Roles:" in content, (
                "Script should display function-specific roles status"
            )


class TestDeploymentModes:
    """Test suite for different deployment modes."""

    def test_script_reports_lambda_only_not_implemented(self, script_path):
        """Test that script reports lambda-only mode not yet implemented."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "Lambda-only deployment not yet implemented" in content, (
                "Script should report lambda-only not implemented for main-stack"
            )

    def test_script_reports_frontend_only_not_implemented(self, script_path):
        """Test that script reports frontend-only mode not yet implemented."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "Frontend-only deployment not yet implemented" in content, (
                "Script should report frontend-only not implemented for main-stack"
            )

    def test_script_uses_main_stack_architecture(self, script_path):
        """Test that script identifies itself as using main-stack architecture."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "main-stack.yaml" in content, (
                "Script should reference main-stack.yaml"
            )
            assert "Nested Stacks" in content or "nested stacks" in content, (
                "Script should mention nested stacks architecture"
            )


class TestScriptStages:
    """Test suite for deployment script stages."""

    def test_script_has_five_stages(self, script_path):
        """Test that script has five deployment stages."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "[1/5] Validation" in content, (
                "Script should have stage 1: Validation"
            )
            assert "[2/5] Security" in content, (
                "Script should have stage 2: Security"
            )
            assert "[3/5] Tests" in content, (
                "Script should have stage 3: Tests"
            )
            assert "[4/5] Git Push" in content, (
                "Script should have stage 4: Git Push"
            )
            assert "[5/5] Deploy" in content, (
                "Script should have stage 5: Deploy"
            )

    def test_script_reports_deployment_complete(self, script_path):
        """Test that script reports deployment complete."""
        with open(script_path, "r") as f:
            content = f.read()
            assert "Deployment complete" in content, (
                "Script should report deployment completion"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
