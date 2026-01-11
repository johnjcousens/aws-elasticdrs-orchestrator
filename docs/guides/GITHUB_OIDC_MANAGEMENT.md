# GitHub OIDC Management Guide

This guide covers the management of GitHub Actions OIDC integration for AWS DRS Orchestration deployments.

## Overview

GitHub Actions uses OpenID Connect (OIDC) to securely authenticate with AWS without storing long-lived credentials. This integration requires:

1. **GitHub OIDC Provider** in AWS IAM
2. **IAM Role** with trust policy for the specific repository
3. **GitHub Repository Secrets** with the role ARN

## Quick Start

### 1. Deploy OIDC Stack (Automated)

```bash
# Deploy for test environment (recommended)
./scripts/deploy-github-oidc.sh test

# Deploy for production environment
./scripts/deploy-github-oidc.sh prod
```

This script will:
- ✅ Auto-detect your repository information
- ✅ Validate repository name matches expected format
- ✅ Create OIDC provider if it doesn't exist
- ✅ Deploy CloudFormation stack with correct parameters
- ✅ Display GitHub secrets to update

### 2. Validate OIDC Configuration

```bash
# Validate test environment
./scripts/validate-github-oidc.sh test

# Validate production environment
./scripts/validate-github-oidc.sh prod
```

This script will:
- ✅ Check if OIDC role exists
- ✅ Validate repository configuration in trust policy
- ✅ Verify OIDC provider exists
- ✅ Display role ARN for GitHub secrets

## Manual Deployment (Advanced)

If you need to deploy manually or customize parameters:

```bash
aws cloudformation deploy \
  --template-file cfn/github-oidc-stack.yaml \
  --stack-name aws-elasticdrs-orchestrator-github-oidc-test \
  --parameter-overrides \
    ProjectName=aws-elasticdrs-orchestrator \
    Environment=test \
    GitHubOrg=johnjcousens \
    GitHubRepo=aws-elasticdrs-orchestrator \
    DeploymentBucket=aws-elasticdrs-orchestrator \
    ApplicationStackName=aws-elasticdrs-orchestrator-test \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

## GitHub Repository Secrets

After deploying the OIDC stack, update these secrets in your GitHub repository:

**Repository Settings → Secrets and variables → Actions**

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ROLE_ARN` | `arn:aws:iam::ACCOUNT:role/aws-elasticdrs-orchestrator-github-actions-ENV` | IAM role for GitHub Actions |
| `STACK_NAME` | `aws-elasticdrs-orchestrator-ENV` | CloudFormation stack name |
| `DEPLOYMENT_BUCKET` | `aws-elasticdrs-orchestrator` | S3 bucket for artifacts |
| `ADMIN_EMAIL` | `jocousen@amazon.com` | Admin email for Cognito |

## Troubleshooting

### Common Issues

#### 1. "Not authorized to perform sts:AssumeRoleWithWebIdentity"

**Cause**: Repository name mismatch in OIDC role trust policy

**Solution**:
```bash
# Validate configuration
./scripts/validate-github-oidc.sh test

# If validation fails, redeploy with correct parameters
./scripts/deploy-github-oidc.sh test
```

#### 2. "OIDC provider not found"

**Cause**: GitHub OIDC provider doesn't exist in AWS account

**Solution**:
```bash
# Create OIDC provider manually
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --client-id-list sts.amazonaws.com

# Or use the deployment script which creates it automatically
./scripts/deploy-github-oidc.sh test
```

#### 3. "Role already exists" during deployment

**Cause**: OIDC role exists but with wrong configuration

**Solution**:
```bash
# Delete existing role and redeploy
aws iam delete-role --role-name aws-elasticdrs-orchestrator-github-actions-test
./scripts/deploy-github-oidc.sh test
```

### Validation Commands

```bash
# Check if role exists
aws iam get-role --role-name aws-elasticdrs-orchestrator-github-actions-test

# Check role trust policy
aws iam get-role --role-name aws-elasticdrs-orchestrator-github-actions-test \
  --query 'Role.AssumeRolePolicyDocument'

# Check OIDC provider
aws iam list-open-id-connect-providers \
  --query 'OpenIDConnectProviderList[?contains(Arn, `token.actions.githubusercontent.com`)]'

# Test GitHub Actions workflow
gh workflow run deploy.yml
```

## Security Best Practices

### 1. Least Privilege Access

The OIDC role includes comprehensive permissions for CloudFormation deployment but follows AWS best practices:

- ✅ Scoped to specific repository
- ✅ Limited to main branch and environments
- ✅ Includes resource-level restrictions where possible
- ✅ Uses condition keys for additional security

### 2. Repository Restrictions

The trust policy restricts access to:
- ✅ Specific repository: `johnjcousens/aws-elasticdrs-orchestrator`
- ✅ Main branch: `refs/heads/main`
- ✅ Pull requests from the repository
- ✅ Specific environments: `test`, `prod`

### 3. Regular Validation

```bash
# Run validation monthly or after any OIDC issues
./scripts/validate-github-oidc.sh test
./scripts/validate-github-oidc.sh prod
```

## Multiple Environments

### Environment-Specific Roles

Each environment has its own OIDC role:

- **Test**: `aws-elasticdrs-orchestrator-github-actions-test`
- **Production**: `aws-elasticdrs-orchestrator-github-actions-prod`

### Deployment Commands

```bash
# Deploy test environment OIDC
./scripts/deploy-github-oidc.sh test

# Deploy production environment OIDC
./scripts/deploy-github-oidc.sh prod

# Validate both environments
./scripts/validate-github-oidc.sh test
./scripts/validate-github-oidc.sh prod
```

## Integration with CI/CD

### GitHub Actions Workflow

The OIDC integration is used in `.github/workflows/deploy.yml`:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: ${{ env.AWS_REGION }}
```

### Environment Selection

The workflow supports multiple environments:

```yaml
workflow_dispatch:
  inputs:
    environment:
      description: 'Deployment environment'
      required: true
      default: 'test'
      type: choice
      options:
        - test
        - prod
```

## Maintenance

### Regular Tasks

1. **Monthly Validation**:
   ```bash
   ./scripts/validate-github-oidc.sh test
   ```

2. **After Repository Changes**:
   - Repository rename → Redeploy OIDC stack
   - Organization transfer → Update GitHubOrg parameter

3. **Security Reviews**:
   - Review role permissions quarterly
   - Validate trust policy restrictions
   - Check for unused roles

### Updates and Migrations

When updating the OIDC configuration:

1. **Test first**: Always test changes in test environment
2. **Validate**: Run validation script after changes
3. **Monitor**: Check GitHub Actions logs for authentication issues
4. **Rollback plan**: Keep previous role ARN for quick rollback

## Reference

### Files

- **CloudFormation Template**: `cfn/github-oidc-stack.yaml`
- **Deployment Script**: `scripts/deploy-github-oidc.sh`
- **Validation Script**: `scripts/validate-github-oidc.sh`
- **GitHub Workflow**: `.github/workflows/deploy.yml`

### AWS Resources

- **OIDC Provider**: `arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com`
- **IAM Roles**: `aws-elasticdrs-orchestrator-github-actions-{ENV}`
- **CloudFormation Stacks**: `aws-elasticdrs-orchestrator-github-oidc-{ENV}`

### External Links

- [GitHub OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [AWS IAM OIDC Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)
- [GitHub Actions AWS Integration](https://github.com/aws-actions/configure-aws-credentials)