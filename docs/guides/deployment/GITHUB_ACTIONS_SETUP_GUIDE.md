# GitHub Actions CI/CD Setup Guide

This guide covers migrating from AWS CodePipeline to GitHub Actions for CI/CD deployment.

## Overview

GitHub Actions provides a simpler CI/CD approach that avoids the circular dependency issues with AWS native tools (where the pipeline tries to update the stack containing itself).

**Benefits:**
- No circular dependency - GitHub Actions runs outside AWS
- Simpler architecture - One workflow file vs 3 CloudFormation stacks
- Better debugging - GitHub's UI is more intuitive
- Native Git integration - No CodeCommit mirroring needed

## Prerequisites

- AWS Account with appropriate permissions
- GitHub repository with admin access
- AWS CLI configured locally
- S3 deployment bucket already exists

## Step 1: Deploy the GitHub OIDC Stack

This stack creates the IAM role that GitHub Actions will assume using OIDC (no long-lived credentials needed).

```bash
# Set your parameters
export PROJECT_NAME="aws-elasticdrs-orchestrator"
export ENVIRONMENT="dev"
export GITHUB_ORG="your-github-username"
export GITHUB_REPO="your-repo-name"
export DEPLOYMENT_BUCKET="your-deployment-bucket"
export APP_STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

# Deploy the OIDC stack
aws cloudformation deploy \
  --template-file cfn/github-oidc-stack.yaml \
  --stack-name "${PROJECT_NAME}-github-oidc" \
  --parameter-overrides \
    ProjectName="${PROJECT_NAME}" \
    Environment="${ENVIRONMENT}" \
    GitHubOrg="${GITHUB_ORG}" \
    GitHubRepo="${GITHUB_REPO}" \
    DeploymentBucket="${DEPLOYMENT_BUCKET}" \
    ApplicationStackName="${APP_STACK_NAME}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Get the role ARN for GitHub secrets
aws cloudformation describe-stacks \
  --stack-name "${PROJECT_NAME}-github-oidc" \
  --query 'Stacks[0].Outputs[?OutputKey==`GitHubActionsRoleArn`].OutputValue' \
  --output text
```

## Step 2: Configure GitHub Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ROLE_ARN` | `arn:aws:iam::ACCOUNT_ID:role/PROJECT-github-actions-ENV` | IAM role ARN from Step 1 |
| `DEPLOYMENT_BUCKET` | `your-deployment-bucket` | S3 bucket for artifacts |
| `STACK_NAME` | `aws-elasticdrs-orchestrator-dev` | CloudFormation stack name |
| `ADMIN_EMAIL` | `admin@example.com` | Admin email for Cognito |

## Step 3: Deploy Application Stack (First Time)

For the initial deployment, deploy the application stack with CI/CD disabled:

```bash
# Sync artifacts to S3 first
./scripts/sync-to-deployment-bucket.sh

# Deploy the application stack without AWS native CI/CD
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name "${APP_STACK_NAME}" \
  --parameter-overrides \
    ProjectName="${PROJECT_NAME}" \
    Environment="${ENVIRONMENT}" \
    SourceBucket="${DEPLOYMENT_BUCKET}" \
    AdminEmail="your-email@example.com" \
    EnableAutomatedDeployment=false \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

## Step 4: Push to GitHub

The workflow will automatically trigger on push to main:

```bash
git add .
git commit -m "feat: migrate to GitHub Actions CI/CD"
git push origin main
```

## Workflow Stages

The GitHub Actions workflow (`.github/workflows/deploy.yml`) runs these stages:

| Stage | Duration | Description |
|-------|----------|-------------|
| **Validate** | ~2 min | CloudFormation validation, Python linting, TypeScript checking |
| **Security Scan** | ~2 min | Bandit security scan, Safety dependency check |
| **Build** | ~3 min | Lambda packaging, frontend build |
| **Test** | ~2 min | Unit tests |
| **Deploy Infrastructure** | ~10 min | CloudFormation stack deployment |
| **Deploy Frontend** | ~2 min | S3 sync, CloudFront invalidation |

**Total: ~20 minutes** (similar to CodePipeline)

## Manual Deployment

You can also trigger deployments manually:

1. Go to Actions tab in GitHub
2. Select "Deploy AWS DRS Orchestration"
3. Click "Run workflow"
4. Select environment (dev/test/prod)
5. Click "Run workflow"

## Cleanup AWS Native CI/CD Resources

After confirming GitHub Actions works, clean up the old AWS CI/CD resources:

```bash
# Delete the old CI/CD nested stacks (if they exist)
# These should already be skipped with EnableAutomatedDeployment=false

# Optional: Delete orphaned CodePipeline
aws codepipeline delete-pipeline --name "${PROJECT_NAME}-pipeline-${ENVIRONMENT}"

# Optional: Delete orphaned CodeBuild projects
aws codebuild delete-project --name "${PROJECT_NAME}-validate-${ENVIRONMENT}"
aws codebuild delete-project --name "${PROJECT_NAME}-security-scan-${ENVIRONMENT}"
aws codebuild delete-project --name "${PROJECT_NAME}-build-${ENVIRONMENT}"
aws codebuild delete-project --name "${PROJECT_NAME}-test-${ENVIRONMENT}"
aws codebuild delete-project --name "${PROJECT_NAME}-deploy-infra-${ENVIRONMENT}"
aws codebuild delete-project --name "${PROJECT_NAME}-deploy-frontend-${ENVIRONMENT}"

# Optional: Delete CodeCommit repository (if not needed)
aws codecommit delete-repository --repository-name "${PROJECT_NAME}-${ENVIRONMENT}"
```

## Troubleshooting

### OIDC Authentication Fails

Check that:
1. The GitHub repository matches the OIDC trust policy
2. The workflow is running from the correct branch (main)
3. The `id-token: write` permission is set in the workflow

### CloudFormation Deployment Fails

Check:
1. IAM role has sufficient permissions
2. S3 bucket exists and contains templates
3. Stack isn't in a failed state (ROLLBACK_COMPLETE)

### Frontend Deployment Fails

Verify:
1. Stack outputs exist (FrontendBucketName, CloudFrontDistributionId)
2. S3 bucket permissions allow the IAM role to write

## Architecture Comparison

### Before (AWS Native)
```
CodeCommit → CodePipeline → CodeBuild → CloudFormation
     ↑                            ↓
     └────── Circular Dependency ─┘
```

### After (GitHub Actions)
```
GitHub → GitHub Actions → AWS (S3, CloudFormation)
              ↓
         No circular dependency
```

## Cost Comparison

| Platform | Monthly Cost |
|----------|--------------|
| AWS Native (CodePipeline + CodeBuild) | $7-19 |
| GitHub Actions (private repo) | $0-50 |
| GitHub Actions (public repo) | Free |

## Related Documentation

- [Fresh Deployment Guide](FRESH_DEPLOYMENT_GUIDE.md)
- [CI/CD Platform Selection Analysis](../../CI_CD_PLATFORM_SELECTION.md)
- [Development Workflow Guide](../DEVELOPMENT_WORKFLOW_GUIDE.md)
