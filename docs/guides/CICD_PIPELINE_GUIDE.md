# CI/CD Pipeline Guide

> **⚠️ DEPRECATED**: This guide describes the legacy GitLab CI/CD pipeline. The project has migrated to **GitHub Actions** as of January 2026 (v1.3.0).
>
> **For current CI/CD documentation, see:**
> - [CI/CD Setup Guide](deployment/CICD_SETUP_GUIDE.md) - GitHub Actions setup and usage
> - [Activate CI/CD Guide](deployment/ACTIVATE_CICD_GUIDE.md) - Quick start guide
> - [GitHub Actions Setup Guide](deployment/GITHUB_ACTIONS_SETUP_GUIDE.md) - OIDC configuration details

---

## Historical Reference: GitLab CI/CD Pipeline (Deprecated)

This guide describes the GitLab CI/CD pipeline that was previously used for the AWS DRS Orchestration solution. This pipeline was replaced by GitHub Actions to eliminate circular dependency issues and provide better developer experience.

## Prerequisites

Before setting up the pipeline, ensure you have:

1. **GitLab Repository** - Code pushed to GitLab (code.amazon.com or gitlab.com)
2. **AWS Account** - With permissions to deploy CloudFormation, Lambda, S3, CloudFront
3. **S3 Deployment Bucket** - Pre-created bucket for artifacts (default: `aws-elasticdrs-orchestrator`)
4. **IAM Credentials** - Access key with deployment permissions

> **Note**: This pipeline uses Amazon ECR Public images (`public.ecr.aws/docker/library/...`) instead of Docker Hub to avoid rate limiting issues. Docker Hub enforces pull rate limits for unauthenticated requests (100 pulls/6 hours), which can cause CI failures in shared GitLab runners.

## Quick Start

### Step 1: Create S3 Deployment Bucket

```bash
aws s3 mb s3://aws-elasticdrs-orchestrator --region us-east-1
aws s3api put-bucket-versioning \
  --bucket aws-elasticdrs-orchestrator \
  --versioning-configuration Status=Enabled
```

### Step 2: Configure GitLab CI/CD Variables

Navigate to **Settings > CI/CD > Variables** and add:

| Variable | Type | Protected | Masked | Value |
|----------|------|-----------|--------|-------|
| `AWS_ACCESS_KEY_ID` | Variable | Yes | Yes | Your AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Variable | Yes | Yes | Your AWS secret key |
| `ADMIN_EMAIL` | Variable | Yes | No | Admin email for Cognito |

### Step 3: Push Code and Trigger Pipeline

```bash
git push origin main
```

The pipeline will automatically run validation, build, and deployment stages.

## Pipeline Architecture

```mermaid
flowchart TB
    subgraph Validate["VALIDATE Stage"]
        V1[validate:cloudformation]
        V2[validate:frontend-types]
    end
    
    subgraph Lint["LINT Stage"]
        L1[lint:python]
        L2[lint:frontend]
    end
    
    subgraph Build["BUILD Stage"]
        B1[build:lambda]
        B2[build:frontend]
    end
    
    subgraph Deploy["DEPLOY-INFRA Stage"]
        D1[deploy:upload-artifacts]
        D2[deploy:cloudformation]
        D3[deploy:production]
    end
    
    subgraph Frontend["DEPLOY-FRONTEND Stage"]
        F1[deploy:frontend]
    end
    
    Validate --> Lint
    Lint --> Build
    Build --> Deploy
    D2 --> Frontend
```

## Pipeline Stages

### 1. Validate Stage

Ensures code quality before building.

#### validate:cloudformation

Validates CloudFormation templates with cfn-lint and AWS CLI.

- **Image**: `public.ecr.aws/docker/library/python:3.12`
- **Triggers**: Changes to `cfn/**/*`, `.cfnlintrc.yaml`, or `.gitlab-ci.yml`
- **Actions**:
  - Runs `cfn-lint` with project config
  - Validates each template with `aws cloudformation validate-template`

#### validate:frontend-types

Runs TypeScript type checking on the React frontend.

- **Image**: `public.ecr.aws/docker/library/node:22-alpine`
- **Triggers**: Changes to `frontend/**/*` or `.gitlab-ci.yml`
- **Actions**:
  - Installs npm dependencies
  - Runs `tsc --noEmit` for type checking
- **Cache**: `frontend/node_modules/`

### 2. Lint Stage

Enforces code style (non-blocking).

#### lint:python

Lints Lambda Python code.

- **Image**: `public.ecr.aws/docker/library/python:3.12`
- **Triggers**: Changes to `lambda/**/*.py` or `.gitlab-ci.yml`
- **Tools**:
  - `pylint` - Code quality (disabled: C0114, C0115, C0116, R0903, W0613, C0103)
  - `black` - Formatting (120 char line length)
  - `flake8` - Style guide (ignores: E203, W503, E501)
- **Note**: All linters run with `|| true` (non-blocking)

#### lint:frontend

Lints React/TypeScript code with ESLint.

- **Image**: `public.ecr.aws/docker/library/node:22-alpine`
- **Triggers**: Changes to `frontend/**/*` or `.gitlab-ci.yml`
- **Note**: Non-blocking (`|| true`)

### 3. Build Stage

Creates deployment artifacts.

#### build:lambda

Packages Lambda functions with dependencies.

- **Image**: `public.ecr.aws/docker/library/python:3.12`
- **Triggers**: `main` branch or `dev/*` branches
- **Creates**:
  - `api-handler.zip` - Main API handler (`index.py`)
  - `orchestration.zip` - Legacy DRS orchestration (`drs_orchestrator.py`)
  - `execution-finder.zip` - Execution finder (`poller/execution_finder.py`)
  - `execution-poller.zip` - Execution poller (`poller/execution_poller.py`)
- **Not Built** (manual packaging required):
  - `orchestration-stepfunctions.zip` - Step Functions orchestration (`orchestration_stepfunctions.py`)
  - `frontend-builder.zip` - CloudFormation custom resource (`build_and_deploy.py`)
- **Artifacts**: Expire in 1 week

#### build:frontend

Builds React frontend with Vite.

- **Image**: `public.ecr.aws/docker/library/node:22-alpine`
- **Triggers**: `main` branch or `dev/*` branches
- **Output**: `frontend/dist/`
- **Artifacts**: Expire in 1 week

### 4. Test Stage (Currently Disabled)

Test jobs are disabled because `tests/` directory is gitignored. To enable:

1. Remove `tests/` from `.gitignore`
2. Uncomment test jobs in `.gitlab-ci.yml`
3. Push test files to repository

### 5. Deploy Infrastructure Stage

Deploys AWS resources.

#### deploy:upload-artifacts

Uploads artifacts to S3 deployment bucket.

- **Image**: `public.ecr.aws/aws-cli/aws-cli:latest`
- **Triggers**: `main` branch or `dev/*` branches
- **Uploads**:

```text
s3://aws-drs-orchestration/
├── cfn/                        # CloudFormation templates
│   ├── master-template.yaml
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-stack.yaml
│   ├── security-stack.yaml
│   ├── step-functions-stack.yaml
│   └── frontend-stack.yaml
└── lambda/                     # Lambda packages
    ├── api-handler.zip
    ├── orchestration.zip
    ├── execution-finder.zip
    └── execution-poller.zip
```

> **Note**: The `orchestration-stepfunctions.zip` package is not currently built by CI. If Step Functions orchestration is needed, add it to the `build:lambda` job.

#### deploy:cloudformation

Deploys CloudFormation nested stack.

- **Image**: `public.ecr.aws/aws-cli/aws-cli:latest`
- **Triggers**: `main` branch or `dev/*` branches
- **Stack Name**: `drs-orchestration-{branch-slug}`
- **Parameters**:
  - `ProjectName`: drs-orchestration
  - `Environment`: test
  - `SourceBucket`: aws-drs-orchestration
  - `AdminEmail`: From CI/CD variable
- **Capabilities**: CAPABILITY_IAM, CAPABILITY_NAMED_IAM

#### deploy:production

Manual production deployment.

- **Triggers**: Manual only on `main` branch
- **Stack Name**: `drs-orchestration-prod`
- **Environment**: prod

### 6. Deploy Frontend Stage

#### deploy:frontend

Deploys React app to S3 and invalidates CloudFront.

- **Image**: `public.ecr.aws/aws-cli/aws-cli:latest`
- **Triggers**: `main` branch or `dev/*` branches
- **Actions**:
  1. Retrieves CloudFormation outputs (API endpoint, Cognito IDs, etc.)
  2. Generates `aws-config.js` with runtime configuration
  3. Uploads to S3 with cache headers:
     - Static assets: `max-age=31536000, immutable`
     - HTML/config: `no-cache, no-store, must-revalidate`
  4. Creates CloudFront invalidation

**Generated aws-config.js Structure**:

The pipeline generates `aws-config.js` that must match the structure expected by `frontend/src/aws-config.ts`:

```javascript
window.AWS_CONFIG = {
  Auth: {
    Cognito: {
      region: 'us-east-1',
      userPoolId: 'us-east-1_XXXXXXX',
      userPoolClientId: 'XXXXXXXXXXXXXXXXXXXXXXXXXX',
      loginWith: {
        email: true
      }
    }
  },
  API: {
    REST: {
      DRSOrchestration: {
        endpoint: 'https://xxx.execute-api.us-east-1.amazonaws.com/prod',
        region: 'us-east-1'
      }
    }
  }
};
```

> **Important**: The structure must match exactly. Using incorrect property names (e.g., `cognito` instead of `Auth.Cognito`, or `clientId` instead of `userPoolClientId`) will cause authentication failures.

## CI/CD Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `wJalrXUtnFEMI/...` |
| `ADMIN_EMAIL` | Cognito admin email | `admin@example.com` |

### Built-in Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS deployment region |
| `DEPLOYMENT_BUCKET` | `aws-drs-orchestration` | S3 bucket for artifacts |
| `ENVIRONMENT` | `test` | Deployment environment |
| `STACK_NAME` | `drs-orchestration-{branch}` | CloudFormation stack name |

## Branch Strategy

| Branch | Validation | Build | Deploy | Environment |
|--------|------------|-------|--------|-------------|
| `main` | Auto | Auto | Auto | test |
| `dev/*` | Auto | Auto | Auto | dev |
| Feature | Auto | No | No | - |
| Production | - | - | Manual | prod |

## Troubleshooting

### CloudFormation Validation Fails

```text
Error: Template format error: YAML not well-formed
```

**Solution**: Check YAML syntax. Run locally:

```bash
cfn-lint cfn/*.yaml
aws cloudformation validate-template --template-body file://cfn/template.yaml
```

### Lambda Build Fails

```text
Error: Could not install packages
```

**Solution**: Check `lambda/requirements.txt` for version conflicts.

### Frontend Build Fails

```text
Error: Cannot find module '@cloudscape-design/components'
```

**Solution**: Ensure `package-lock.json` is committed:

```bash
cd frontend
npm install
git add package-lock.json
git commit -m "Update package-lock.json"
```

### CloudFormation Deployment Fails

```text
Error: Stack is in UPDATE_ROLLBACK_COMPLETE state
```

**Solution**: Delete the stack and redeploy:

```bash
aws cloudformation delete-stack --stack-name drs-orchestration-test
aws cloudformation wait stack-delete-complete --stack-name drs-orchestration-test
# Then re-run pipeline
```

### Frontend Deployment Fails

```text
Error: NoSuchBucket when calling PutObject
```

**Solution**: Ensure CloudFormation stack deployed successfully first. The frontend bucket is created by CloudFormation.

### Frontend Authentication Fails After Deployment

```text
Error: User pool does not exist / Invalid UserPoolId
```

**Solution**: The `aws-config.js` structure may be incorrect. Verify the generated config:

```bash
# Check the deployed config
curl -s https://YOUR_CLOUDFRONT_URL/aws-config.js
```

The structure must use `Auth.Cognito.userPoolClientId` (not `cognito.clientId`). See the "Generated aws-config.js Structure" section above.

## Manual Operations

### Trigger Pipeline Manually

Via GitLab UI: **CI/CD > Pipelines > Run pipeline**

### Rollback Deployment

```bash
# Option 1: Revert commit and push
git revert HEAD
git push origin main

# Option 2: CloudFormation rollback
aws cloudformation cancel-update-stack --stack-name drs-orchestration-test

# Option 3: Restore previous Lambda version from S3
aws s3api list-object-versions --bucket aws-drs-orchestration --prefix lambda/api-handler.zip
aws lambda update-function-code \
  --function-name aws-drs-orchestrator-api-handler-test \
  --s3-bucket aws-drs-orchestration \
  --s3-key lambda/api-handler.zip \
  --s3-object-version <previous-version-id>
```

### Clear GitLab CI Cache

Navigate to **CI/CD > Pipelines > Clear runner caches**

## IAM Permissions Required

The CI/CD IAM user needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3DeploymentBucket",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket", "s3:GetBucketLocation"],
      "Resource": ["arn:aws:s3:::aws-drs-orchestration", "arn:aws:s3:::aws-drs-orchestration/*"]
    },
    {
      "Sid": "S3FrontendBucket",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket", "s3:CreateBucket", "s3:PutBucketPolicy", "s3:GetBucketPolicy", "s3:PutBucketWebsite", "s3:PutBucketPublicAccessBlock"],
      "Resource": ["arn:aws:s3:::drs-orchestration-*", "arn:aws:s3:::drs-orchestration-*/*"]
    },
    {
      "Sid": "CloudFormation",
      "Effect": "Allow",
      "Action": ["cloudformation:*"],
      "Resource": "arn:aws:cloudformation:*:*:stack/drs-orchestration-*/*"
    },
    {
      "Sid": "CloudFormationValidate",
      "Effect": "Allow",
      "Action": ["cloudformation:ValidateTemplate", "cloudformation:DescribeStacks", "cloudformation:ListStacks"],
      "Resource": "*"
    },
    {
      "Sid": "IAMRoles",
      "Effect": "Allow",
      "Action": ["iam:CreateRole", "iam:DeleteRole", "iam:AttachRolePolicy", "iam:DetachRolePolicy", "iam:PutRolePolicy", "iam:DeleteRolePolicy", "iam:GetRole", "iam:PassRole", "iam:TagRole", "iam:CreatePolicy", "iam:DeletePolicy", "iam:GetPolicy", "iam:GetPolicyVersion"],
      "Resource": ["arn:aws:iam::*:role/drs-orchestration-*", "arn:aws:iam::*:policy/drs-orchestration-*"]
    },
    {
      "Sid": "Lambda",
      "Effect": "Allow",
      "Action": ["lambda:*"],
      "Resource": "arn:aws:lambda:*:*:function:drs-orchestration-*"
    },
    {
      "Sid": "DynamoDB",
      "Effect": "Allow",
      "Action": ["dynamodb:*"],
      "Resource": "arn:aws:dynamodb:*:*:table/drs-orchestration-*"
    },
    {
      "Sid": "Cognito",
      "Effect": "Allow",
      "Action": ["cognito-idp:*", "cognito-identity:*"],
      "Resource": "*"
    },
    {
      "Sid": "APIGateway",
      "Effect": "Allow",
      "Action": ["apigateway:*"],
      "Resource": "*"
    },
    {
      "Sid": "CloudFront",
      "Effect": "Allow",
      "Action": ["cloudfront:*"],
      "Resource": "*"
    },
    {
      "Sid": "StepFunctions",
      "Effect": "Allow",
      "Action": ["states:*"],
      "Resource": "arn:aws:states:*:*:stateMachine:drs-orchestration-*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:DeleteLogGroup", "logs:PutRetentionPolicy", "logs:DescribeLogGroups"],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/drs-orchestration-*"
    },
    {
      "Sid": "EventBridge",
      "Effect": "Allow",
      "Action": ["events:*"],
      "Resource": "arn:aws:events:*:*:rule/drs-orchestration-*"
    }
  ]
}
```

## Pipeline Outputs

After successful deployment, the pipeline outputs:

| Output | Description |
|--------|-------------|
| `CloudFrontUrl` | Frontend application URL |
| `ApiEndpoint` | API Gateway endpoint |
| `UserPoolId` | Cognito User Pool ID |
| `UserPoolClientId` | Cognito App Client ID |

Access in GitLab: **CI/CD > Jobs > deploy:cloudformation > Artifacts > stack-outputs.json**

## References

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [AWS CloudFormation Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)
- [Project README](../../README.md)
