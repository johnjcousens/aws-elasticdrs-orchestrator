# Deployment Script Testing Notes

## Overview

The `deploy-main-stack.sh` script is a bash script that orchestrates the deployment pipeline. Unit testing bash scripts requires specialized frameworks and infrastructure.

## Testing Approach

### Manual Testing (Current)

The deployment script is tested through:

1. **Validation Stage Testing**
   - Run `./scripts/deploy-main-stack.sh test --validate-only`
   - Verifies cfn-lint, flake8, black, TypeScript checks work

2. **Security Stage Testing**
   - Run with full pipeline to verify bandit, cfn_nag, detect-secrets, etc.
   - Confirms all security tools execute correctly

3. **Test Stage Testing**
   - Run with `--full-tests` to verify pytest and vitest integration
   - Confirms test execution and failure detection

4. **Deployment Testing**
   - Deploy to test environment: `./scripts/deploy-main-stack.sh test`
   - Verify nested stack templates sync to S3
   - Verify template URL validation works
   - Verify CloudFormation deployment succeeds

5. **Parameter Testing**
   - Test `--use-function-specific-roles` flag
   - Test `--validate-only`, `--full-tests`, `--skip-tests` flags
   - Verify environment variables work correctly

### Automated Testing (Future)

To implement automated bash script testing:

1. **Framework Options**
   - [bats-core](https://github.com/bats-core/bats-core) - Bash Automated Testing System
   - [shunit2](https://github.com/kward/shunit2) - xUnit-based testing framework
   - [shellspec](https://github.com/shellspec/shellspec) - BDD-style testing

2. **Test Coverage Areas**
   ```bash
   # Example test structure with bats-core
   
   @test "script validates nested stack templates exist" {
     # Mock S3 commands
     # Run script with test environment
     # Assert validation passes/fails correctly
   }
   
   @test "script syncs all nested stack directories" {
     # Mock aws s3 sync commands
     # Verify all 12 directories are synced
   }
   
   @test "script creates deployment bucket with account ID" {
     # Mock aws sts get-caller-identity
     # Mock aws s3api create-bucket
     # Verify bucket name includes account ID
   }
   
   @test "script passes UseFunctionSpecificRoles parameter" {
     # Mock CloudFormation deploy
     # Verify parameter is passed correctly
   }
   ```

3. **Implementation Steps**
   - Install bats-core: `npm install -g bats`
   - Create `tests/unit/test_deploy_main_stack.bats`
   - Mock AWS CLI commands using test doubles
   - Run tests in CI/CD pipeline

## Current Status

**Manual testing completed:**
- ✅ Script structure follows deploy.sh pattern
- ✅ All 5 stages implemented (Validation, Security, Tests, Git, Deploy)
- ✅ Nested stack template syncing implemented
- ✅ S3 bucket creation with account ID implemented
- ✅ Template URL validation implemented
- ✅ UseFunctionSpecificRoles parameter support implemented
- ✅ Documentation created

**Automated testing:**
- ⏳ Deferred to future implementation
- Requires bash testing framework setup
- Requires AWS CLI mocking infrastructure

## Verification Checklist

Before deploying to production, verify:

- [ ] Script validates nested stack templates exist
- [ ] Script syncs all 12 nested stack directories to S3
- [ ] Script creates deployment bucket with account ID
- [ ] Script validates S3 URLs are accessible
- [ ] Script passes correct parameters to CloudFormation
- [ ] Script handles errors gracefully
- [ ] Script respects --use-function-specific-roles flag
- [ ] Script works with all command-line options

## Related Documentation

- [Deploy Main Stack Guide](../../docs/DEPLOY_MAIN_STACK_GUIDE.md)
- [Deployment Guide](../../docs/deployment-guide.md)
- [Testing Standards](../../docs/testing-standards.md)
