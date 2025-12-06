# CI/CD Pipeline Guide

## Overview

This document describes the GitLab CI/CD pipeline for the AWS DRS Orchestration solution. The pipeline automates validation, building, testing, and deployment of both infrastructure and frontend components.

## Pipeline Architecture

```
┌─────────────┐
│  VALIDATE   │  CloudFormation templates, TypeScript types
└──────┬──────┘
       │
┌──────▼──────┐
│    LINT     │  Python (pylint, black, flake8), Frontend (ESLint)
└──────┬──────┘
       │
┌──────▼──────┐
│    BUILD    │  Lambda packages, React frontend
└──────┬──────┘
       │
┌──────▼──────┐
│    TEST     │  Playwright E2E tests (manual trigger)
└──────┬──────┘
       │
┌──────▼──────┐
│ DEPLOY-INFRA│  Upload artifacts, Deploy CloudFormation
└──────┬──────┘
       │
┌──────▼──────┐
│DEPLOY-FRONT │  Inject config, Deploy to S3, Invalidate CloudFront
└─────────────┘
```

## Pipeline Stages

### 1. Validate Stage

**Purpose**: Ensure code quality and correctness before building

#### validate:cloudformation
- **Runs on**: Changes to `cfn/**/*` or `.gitlab-ci.yml`
- **Actions**:
  - Validates CloudFormation templates with `cfn-lint`
  - Validates template syntax with AWS CLI
- **Ignores**: W2001, W3002, W3005, W3037 (common warnings)

#### validate:frontend-types
- **Runs on**: Changes to `frontend/**/*` or `.gitlab-ci.yml`
- **Actions**:
  - Runs TypeScript type checking (`tsc --noEmit`)
  - Ensures no type errors before build
- **Cache**: Frontend node_modules for faster subsequent runs

### 2. Lint Stage

**Purpose**: Enforce code style and best practices

#### lint:python
- **Runs on**: Changes to `lambda/**/*.py` or `.gitlab-ci.yml`
- **Tools**:
  - **pylint**: Code quality checks (disabled: C0114, C0115, C0116, R0903, W0613, C0103)
  - **black**: Code formatting (120 char line length)
  - **flake8**: Style guide enforcement (ignores: E203, W503, E501)
- **Note**: All linters run in non-blocking mode (`|| true`)

#### lint:frontend
- **Runs on**: Changes to `frontend/**/*` or `.gitlab-ci.yml`
- **Actions**:
  - Runs ESLint on TypeScript/React code
- **Cache**: Frontend node_modules

### 3. Build Stage

**Purpose**: Create deployment artifacts

#### build:lambda
- **Runs on**: `main` branch or `dev/*` branches
- **Actions**:
  1. Install Python dependencies to `package/` directory
  2. Create 4 Lambda deployment packages:
     - `api-handler.zip` (main API logic)
     - `orchestration.zip` (DRS recovery orchestration)
     - `execution-finder.zip` (discover PENDING executions)
     - `execution-poller.zip` (poll DRS job status)
  3. Exclude `.pyc` files and `__pycache__` directories
- **Artifacts**: Lambda zip files (1 hour expiration)

#### build:frontend
- **Runs on**: `main` branch or `dev/*` branches
- **Actions**:
  1. Install npm dependencies
  2. Build React frontend with Vite
  3. Output to `frontend/dist/`
- **Artifacts**: Frontend build directory (1 hour expiration)
- **Cache**: Frontend node_modules

### 4. Test Stage

**Purpose**: Run automated tests

#### test:playwright
- **Runs on**: Manual trigger only
- **Image**: `mcr.microsoft.com/playwright:v1.40.0-focal`
- **Actions**:
  - Runs Playwright E2E tests
  - Generates HTML report
- **Artifacts**: Test results and reports (7 days expiration)
- **Note**: Manual trigger to avoid blocking deployments

### 5. Deploy Infrastructure Stage

**Purpose**: Deploy AWS infrastructure

#### deploy:upload-artifacts
- **Runs on**: `main` branch or `dev/*` branches
- **Actions**:
  1. Upload CloudFormation templates to S3
  2. Upload Lambda packages to S3
- **S3 Bucket**: `aws-drs-orchestration`
- **Structure**:
  ```
  s3://aws-drs-orchestration/
  ├── cfn/
  │   ├── master-template.yaml
  │   ├── database-stack.yaml
  │   ├── lambda-stack.yaml
  │   ├── api-stack.yaml
  │   ├── security-stack.yaml
  │   └── frontend-stack.yaml
  └── lambda/
      ├── api-handler.zip
      ├── orchestration.zip
      ├── execution-finder.zip
      └── execution-poller.zip
  ```

#### deploy:cloudformation
- **Runs on**: `main` branch or `dev/*` branches
- **Actions**:
  1. Deploy CloudFormation master template
  2. Wait for stack creation/update to complete
  3. Display stack outputs
- **Parameters**:
  - `ProjectName`: drs-orchestration
  - `Environment`: test (or dev)
  - `SourceBucket`: aws-drs-orchestration
  - `AdminEmail`: From CI/CD variable
- **Capabilities**: CAPABILITY_IAM, CAPABILITY_NAMED_IAM

### 6. Deploy Frontend Stage

**Purpose**: Deploy React frontend to S3/CloudFront

#### deploy:frontend
- **Runs on**: `main` branch or `dev/*` branches
- **Actions**:
  1. Retrieve CloudFormation outputs (API endpoint, Cognito details, etc.)
  2. Generate `aws-config.js` with runtime configuration
  3. Upload frontend to S3 with cache headers:
     - Static assets: `max-age=31536000, immutable`
     - HTML/config: `no-cache, no-store, must-revalidate`
  4. Create CloudFront invalidation for `/*`
  5. Display application URL

## CI/CD Variables

Configure these in GitLab CI/CD settings:

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key for deployment | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for deployment | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `ADMIN_EMAIL` | Email for Cognito admin user | `admin@example.com` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_DEFAULT_REGION` | AWS region for deployment | `us-east-1` |
| `DEPLOYMENT_BUCKET` | S3 bucket for artifacts | `aws-drs-orchestration` |
| `ENVIRONMENT` | Deployment environment | `test` |

## Branch Strategy

### Main Branch (`main`)
- **Triggers**: All stages automatically
- **Deploys to**: TEST environment
- **Manual**: Production deployment

### Development Branches (`dev/*`)
- **Triggers**: All stages automatically
- **Deploys to**: DEV environment (dynamic stack name)
- **Cleanup**: Manual stack deletion required

### Feature Branches
- **Triggers**: Validate and Lint stages only
- **No deployment**: Build artifacts not created

## Manual Deployments

### Production Deployment

Production deployments require manual approval:

```yaml
deploy:production:
  when: manual
  environment: production
```

**Steps**:
1. Merge to `main` branch
2. Pipeline runs automatically for TEST
3. Navigate to GitLab pipeline
4. Click "Play" button on `deploy:production` job
5. Confirm deployment

### Rollback Procedure

To rollback a deployment:

```bash
# Option 1: Redeploy previous version
git checkout <previous-commit>
git push origin main --force

# Option 2: CloudFormation rollback
aws cloudformation cancel-update-stack --stack-name drs-orchestration-test

# Option 3: Manual rollback via AWS Console
# Navigate to CloudFormation → Select stack → Actions → Roll back
```

## Troubleshooting

### Pipeline Failures

#### CloudFormation Validation Fails
```
Error: Template format error: YAML not well-formed
```
**Solution**: Check YAML syntax in CloudFormation templates

#### Lambda Build Fails
```
Error: Could not install packages due to an EnvironmentError
```
**Solution**: Check `lambda/requirements.txt` for incompatible versions

#### Frontend Build Fails
```
Error: Cannot find module '@cloudscape-design/components'
```
**Solution**: Run `npm install` locally and commit `package-lock.json`

#### CloudFormation Deployment Fails
```
Error: Stack is in UPDATE_ROLLBACK_COMPLETE state
```
**Solution**: Delete stack and redeploy, or fix the issue and update again

#### Frontend Deployment Fails
```
Error: An error occurred (NoSuchBucket) when calling the PutObject operation
```
**Solution**: Ensure CloudFormation stack deployed successfully first

### Common Issues

#### Cache Issues
Clear GitLab CI cache:
```bash
# In GitLab UI: CI/CD → Pipelines → Clear runner caches
```

#### Artifact Expiration
Artifacts expire after 1 hour. If deployment fails, rebuild:
```bash
# Retry the build:lambda or build:frontend job
```

#### CloudFront Invalidation Slow
CloudFront invalidations take 5-15 minutes. Check status:
```bash
aws cloudfront get-invalidation \
  --distribution-id E46O075T9AHF3 \
  --id <invalidation-id>
```

## Performance Optimization

### Cache Strategy
- **Frontend node_modules**: Cached per branch
- **Lambda dependencies**: Rebuilt only when `requirements.txt` changes

### Parallel Execution
- Validation jobs run in parallel
- Lint jobs run in parallel
- Build jobs run in parallel

### Artifact Management
- Lambda packages: 1 hour expiration
- Frontend build: 1 hour expiration
- Test results: 7 days expiration

## Security Best Practices

### Secrets Management
- Store AWS credentials in GitLab CI/CD variables (masked)
- Never commit credentials to repository
- Use IAM roles with least privilege

### Access Control
- Limit who can trigger manual deployments
- Require approval for production deployments
- Use protected branches for `main`

### Audit Trail
- All deployments logged in GitLab
- CloudFormation change sets provide audit trail
- CloudTrail logs all AWS API calls

## Monitoring

### Pipeline Metrics
- **Success Rate**: Track in GitLab Analytics
- **Duration**: Monitor average pipeline duration
- **Failure Patterns**: Identify common failure points

### Deployment Monitoring
- **CloudFormation Events**: Monitor stack events during deployment
- **Lambda Logs**: Check CloudWatch Logs for errors
- **Frontend Errors**: Monitor CloudFront access logs

## Next Steps

1. **Setup GitLab Repository**: Push code to GitLab
2. **Configure CI/CD Variables**: Add AWS credentials and admin email
3. **Test Pipeline**: Trigger first pipeline run
4. **Monitor Deployment**: Verify all stages complete successfully
5. **Access Application**: Navigate to CloudFront URL

## References

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [AWS CloudFormation Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)
- [CloudScape Design System](https://cloudscape.design/)
- [Project README](../README.md)
