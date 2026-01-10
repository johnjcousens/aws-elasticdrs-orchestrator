# Updated CI/CD Pipeline Guide

## Overview

The CI/CD pipeline has been fully updated for the restored **aws-elasticdrs-orchestrator-dev** stack. This guide covers the new workflow, safety features, and deployment processes.

## 🚀 Quick Start

### Standard Development Workflow

```bash
# 1. Make your changes locally
# Edit files, test locally where possible

# 2. Stage and commit changes
git add .
git commit -m "feat: your feature description"

# 3. Safe push with workflow checks (RECOMMENDED)
./scripts/safe-push.sh

# 4. Monitor deployment
# GitHub Actions will automatically deploy your changes
```

### Alternative: Manual Workflow Check

```bash
# Check for running workflows before pushing
./scripts/check-workflow.sh && git push
```

## 🔍 Deployment Scope Analysis

Before pushing, analyze what will be deployed:

```bash
# Preview deployment scope and time estimates
./scripts/check-deployment-scope.sh
```

**Output Examples:**
- **Documentation-only**: ~30 seconds (95% time savings)
- **Frontend-only**: ~12 minutes (45% time savings)
- **Full deployment**: ~22 minutes (complete pipeline)

## 🛡️ Safety Features

### Workflow Conflict Prevention

The pipeline now prevents deployment conflicts:

- ✅ **Automatic workflow checks** before pushing
- ✅ **Safe push script** with built-in safety
- ✅ **Deployment scope analysis** with time estimates
- ✅ **Emergency bypass options** for critical fixes

### New Safety Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `check-workflow.sh` | Check if workflows are running | `./scripts/check-workflow.sh && git push` |
| `safe-push.sh` | Safe push with automatic checks | `./scripts/safe-push.sh` |
| `check-deployment-scope.sh` | Analyze deployment scope | `./scripts/check-deployment-scope.sh` |

## 📋 Pipeline Stages

### Intelligent Pipeline Optimization

The pipeline automatically detects changes and optimizes execution:

#### 1. Documentation-Only Changes
- **Time**: ~30 seconds
- **Stages**: Detect Changes → Documentation Summary
- **Skipped**: Validation, Security, Build, Test, Deploy

#### 2. Frontend-Only Changes  
- **Time**: ~12 minutes
- **Stages**: Detect → Validate → Security → Build → Test → Deploy Frontend
- **Skipped**: Deploy Infrastructure

#### 3. Full Deployment
- **Time**: ~22 minutes
- **Stages**: All stages including infrastructure deployment

### Pipeline Stages Detail

1. **Detect Changes** (~10s)
   - Analyzes changed files
   - Determines deployment scope
   - Sets optimization flags

2. **Validate** (~2 min)
   - CloudFormation template validation
   - Python code quality (Flake8, Black, isort)
   - TypeScript type checking
   - ESLint validation
   - CloudScape design system compliance

3. **Security Scan** (~2 min)
   - Python: Bandit, Semgrep, Safety
   - Frontend: NPM audit, ESLint security
   - Infrastructure: CFN-lint, Semgrep YAML
   - Security threshold checking

4. **Build** (~3 min)
   - Lambda package creation
   - Frontend build (React + TypeScript)
   - Artifact upload

5. **Test** (~2 min)
   - Python unit tests (pytest)
   - Frontend tests (if configured)

6. **Deploy Infrastructure** (~10 min)
   - CloudFormation stack deployment
   - Lambda function updates
   - Stack output extraction

7. **Deploy Frontend** (~3 min)
   - S3 sync with optimized caching
   - CloudFront invalidation
   - Configuration generation

## 🔧 Configuration Updates

### Updated Files

#### `.env.deployment.fresh`
```bash
# Current working stack configuration
PROJECT_NAME=aws-elasticdrs-orchestrator
ENVIRONMENT=dev
PARENT_STACK_NAME=aws-elasticdrs-orchestrator-dev
API_ENDPOINT=https://akp69tt2m1.execute-api.us-east-1.amazonaws.com/dev
CLOUDFRONT_URL=https://dly5x2oq5f01g.cloudfront.net
# ... (complete configuration)
```

#### `aws-config.json`
```json
{
  "region": "us-east-1",
  "userPoolId": "us-east-1_ZpRNNnGTK",
  "userPoolClientId": "3b9l2jv7engtoeba2t1h2mo5ds",
  "identityPoolId": "us-east-1:052133fc-f2f7-4e0f-be2c-02fd84287feb",
  "apiEndpoint": "https://akp69tt2m1.execute-api.us-east-1.amazonaws.com/dev"
}
```

#### GitHub Actions Workflow
- **Project Name**: `aws-elasticdrs-orchestrator`
- **Lambda Functions**: Updated naming convention
- **Stack Outputs**: Correct endpoint URLs

### Lambda Function Names (Updated)

| Function | Current Name |
|----------|--------------|
| API Handler | `aws-elasticdrs-orchestrator-api-handler-dev` |
| Orchestration | `aws-elasticdrs-orchestrator-orch-sf-dev` |
| Execution Finder | `aws-elasticdrs-orchestrator-execution-finder-dev` |
| Execution Poller | `aws-elasticdrs-orchestrator-execution-poller-dev` |
| Frontend Builder | `aws-elasticdrs-orchestrator-frontend-builder-dev` |
| Bucket Cleaner | `aws-elasticdrs-orchestrator-bucket-cleaner-dev` |
| Notification Formatter | `aws-elasticdrs-orchestrator-notification-formatter-dev` |

## 🔐 GitHub Repository Secrets

### Required Secrets

| Secret | Value | Description |
|--------|-------|-------------|
| `AWS_ROLE_ARN` | `arn:aws:iam::777788889999:role/GitHubActionsRole` | OIDC role for AWS access |
| `DEPLOYMENT_BUCKET` | `aws-elasticdrs-orchestrator` | S3 deployment bucket |
| `STACK_NAME` | `aws-elasticdrs-orchestrator-dev` | CloudFormation stack name |
| `ADMIN_EMAIL` | `jocousen@amazon.com` | Admin email for Cognito |

### Setting Up Secrets

1. Go to GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** for each required secret
3. Verify all secrets are configured correctly

## 🚨 Emergency Procedures

### When Manual Deployment is Allowed

- **GitHub Actions service outage** (confirmed AWS/GitHub issue)
- **Critical production hotfix** when pipeline is broken
- **Pipeline debugging** (with immediate revert to Git-based deployment)

### Emergency Commands

```bash
# ONLY in genuine emergencies
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# IMMEDIATELY follow up with proper Git commit
git add .
git commit -m "emergency: describe the critical fix"
./scripts/safe-push.sh
```

### Emergency Options

| Flag | Purpose | Risk Level |
|------|---------|------------|
| `--update-lambda-code` | Fast Lambda updates | Medium |
| `--deploy-frontend` | Direct frontend deployment | Medium |
| `--deploy-cfn` | CloudFormation deployment | High |
| `--emergency-deploy` | Full emergency bypass | Very High |

## 📊 Monitoring and Verification

### GitHub Actions Monitoring

- **Workflow URL**: `https://github.com/jocousen/aws-elasticdrs-orchestrator/actions`
- **Latest Run**: Check for successful completion
- **Logs**: Review each stage for errors

### AWS Resource Verification

```bash
# Check stack status
aws cloudformation describe-stacks --stack-name aws-elasticdrs-orchestrator-dev

# Test API endpoint
curl https://akp69tt2m1.execute-api.us-east-1.amazonaws.com/dev/health

# Check frontend
curl -I https://dly5x2oq5f01g.cloudfront.net
```

### Application Testing

- **Frontend**: `https://dly5x2oq5f01g.cloudfront.net`
- **Login**: `testuser@example.com` / `TestPassword123!`
- **API**: Test protection groups, recovery plans, executions

## 🔄 Migration from Old Workflow

### What Changed

1. **Project Name**: `aws-drs-orchestrator-fresh` → `aws-elasticdrs-orchestrator`
2. **Stack Name**: `aws-drs-orchestrator-fresh` → `aws-elasticdrs-orchestrator-dev`
3. **Lambda Names**: Updated to match new stack
4. **Safety Scripts**: Added workflow conflict prevention
5. **Deployment Scope**: Added intelligent optimization

### Migration Steps

1. ✅ **Update local configuration** (completed)
2. ✅ **Update GitHub secrets** (required)
3. ✅ **Test new workflow** (recommended)
4. ✅ **Train team on new scripts** (ongoing)

## 🎯 Best Practices

### Development Workflow

1. **Always use safe-push**: `./scripts/safe-push.sh`
2. **Check deployment scope**: `./scripts/check-deployment-scope.sh`
3. **Monitor pipeline progress**: Watch GitHub Actions
4. **Wait for completion**: Don't push during deployments
5. **Test after deployment**: Verify functionality

### Git Practices

- ✅ Use conventional commit messages: `feat:`, `fix:`, `docs:`
- ✅ Keep commits focused and atomic
- ✅ Write descriptive commit messages
- ✅ Stage changes before checking deployment scope

### Quality Gates

- ✅ Run `make validate` before committing
- ✅ Fix linting errors locally
- ✅ Write tests for new functionality
- ✅ Follow coding standards (Python PEP 8, TypeScript)

## 🆘 Troubleshooting

### Common Issues

#### 1. Workflow Check Fails
```bash
# Install GitHub CLI
brew install gh
gh auth login

# Retry workflow check
./scripts/check-workflow.sh
```

#### 2. Pipeline Fails
1. Check GitHub Actions logs
2. Fix the issue locally
3. Commit and push the fix
4. Let the pipeline retry

#### 3. Authentication Issues
- Verify GitHub repository secrets
- Check AWS IAM role permissions
- Confirm OIDC trust policy

#### 4. Stack Deployment Fails
- Check CloudFormation events
- Verify template syntax
- Review parameter values

### Getting Help

1. **Check logs**: GitHub Actions → Latest workflow run
2. **Review documentation**: This guide and related docs
3. **Test locally**: Use validation scripts
4. **Emergency contact**: Use manual deployment only for critical issues

---

**Last Updated**: January 10, 2026  
**Stack**: aws-elasticdrs-orchestrator-dev  
**Pipeline Status**: Fully Operational  
**Safety Features**: Active