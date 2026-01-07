# GitHub Actions CI/CD Setup Guide

⚠️ **CRITICAL**: This guide sets up the **MANDATORY** GitHub Actions CI/CD pipeline. Manual deployment scripts are for emergencies only.

This guide covers setting up GitHub Actions for CI/CD deployment of the AWS DRS Orchestration platform.

## Overview

**GitHub Actions First Policy**: ALL deployments MUST use GitHub Actions CI/CD pipeline.

GitHub Actions provides a streamlined CI/CD approach with OIDC-based AWS authentication (no long-lived credentials required).

**Benefits:**
- ✅ **Audit Trail**: All changes tracked in Git history
- ✅ **Quality Gates**: Automated validation, testing, security scanning
- ✅ **No Circular Dependencies**: GitHub Actions runs outside AWS
- ✅ **Enterprise Compliance**: Meets deployment standards and governance
- ✅ **Team Visibility**: All deployments visible to team members
- ✅ **OIDC Security**: Secure AWS access without storing credentials

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
| **Security Scan** | ~3 min | **Enhanced comprehensive security scanning** |
| **Build** | ~3 min | Lambda packaging, frontend build |
| **Test** | ~2 min | Unit tests |
| **Deploy Infrastructure** | ~10 min | CloudFormation stack deployment |
| **Deploy Frontend** | ~2 min | S3 sync, CloudFront invalidation |

**Total: ~22 minutes** (enhanced security scanning adds ~1 minute)

### Enhanced Security Scanning Stage

The security scanning stage includes **enterprise-grade security validation** with automated thresholds:

#### Security Tools & Versions
- **Bandit v1.7.5** - Python security analysis with medium+ severity detection
- **Safety v2.3.4** - Python dependency vulnerability scanning  
- **Semgrep v1.45.0** - Advanced security pattern matching for Python and YAML
- **CFN-Lint v0.83.8** - CloudFormation security linting and best practices
- **ESLint** - Frontend TypeScript/React security rule scanning
- **NPM Audit** - Frontend dependency vulnerability detection

#### Security Thresholds & Quality Gates
```bash
# Environment variables controlling security thresholds
SECURITY_THRESHOLD_CRITICAL: "0"    # No critical issues allowed (fails build)
SECURITY_THRESHOLD_HIGH: "10"       # Max 10 high-severity issues (warning)
SECURITY_THRESHOLD_TOTAL: "50"      # Max 50 total issues (informational)
```

#### Comprehensive Scanning Scope
- **Python Security**: `lambda/` and `scripts/` directories
- **Frontend Security**: TypeScript/React patterns and NPM dependencies
- **Infrastructure Security**: CloudFormation templates and YAML configurations
- **Dependency Scanning**: Both Python (pip) and NPM vulnerability detection

#### Security Reports & Artifacts
- **Raw Reports**: JSON format for automated processing (`reports/security/raw/`)
- **Formatted Reports**: Human-readable text format (`reports/security/formatted/`)
- **Security Summary**: Consolidated findings with remediation guidance
- **Threshold Validation**: Automated pass/fail decisions based on severity
- **Artifact Retention**: 30-day GitHub Actions artifact storage

#### Security Report Structure
```text
reports/security/
├── raw/                    # JSON reports for automation
│   ├── bandit-report.json
│   ├── safety-report.json
│   ├── semgrep-python.json
│   ├── semgrep-cfn.json
│   ├── npm-audit.json
│   ├── eslint-security.json
│   └── cfn-lint.json
├── formatted/              # Human-readable reports
│   ├── bandit-report.txt
│   ├── safety-report.txt
│   ├── semgrep-python.txt
│   ├── semgrep-cfn.txt
│   ├── npm-audit.txt
│   ├── eslint-security.txt
│   └── cfn-lint.txt
└── security-summary.json   # Consolidated summary with thresholds
```

This enhanced security scanning restores the comprehensive capabilities from the original CodePipeline setup, ensuring enterprise-grade security validation for all deployments.

## Manual Deployment

You can also trigger deployments manually:

1. Go to Actions tab in GitHub
2. Select "Deploy AWS DRS Orchestration"
3. Click "Run workflow"
4. Select environment (dev/test/prod)
5. Click "Run workflow"

## Historical: Cleanup Legacy AWS CI/CD Resources

> **Note**: This section is for historical reference only. If you previously used AWS CodePipeline/CodeBuild/CodeCommit and need to clean up those resources, use the commands below.

```bash
# Optional: Delete orphaned CodePipeline (if it exists)
aws codepipeline delete-pipeline --name "${PROJECT_NAME}-pipeline-${ENVIRONMENT}" 2>/dev/null || true

# Optional: Delete orphaned CodeBuild projects (if they exist)
aws codebuild delete-project --name "${PROJECT_NAME}-validate-${ENVIRONMENT}" 2>/dev/null || true
aws codebuild delete-project --name "${PROJECT_NAME}-security-scan-${ENVIRONMENT}" 2>/dev/null || true
aws codebuild delete-project --name "${PROJECT_NAME}-build-${ENVIRONMENT}" 2>/dev/null || true
aws codebuild delete-project --name "${PROJECT_NAME}-test-${ENVIRONMENT}" 2>/dev/null || true
aws codebuild delete-project --name "${PROJECT_NAME}-deploy-infra-${ENVIRONMENT}" 2>/dev/null || true
aws codebuild delete-project --name "${PROJECT_NAME}-deploy-frontend-${ENVIRONMENT}" 2>/dev/null || true

# Optional: Delete CodeCommit repository (if not needed)
aws codecommit delete-repository --repository-name "${PROJECT_NAME}-${ENVIRONMENT}" 2>/dev/null || true
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
