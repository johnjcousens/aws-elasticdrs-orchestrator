# GitHub Actions CI/CD Guide

⚠️ **CRITICAL**: GitHub Actions CI/CD is the **MANDATORY** deployment method. Manual deployment scripts are for emergencies only.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Pipeline Architecture](#pipeline-architecture)
4. [Development Workflow](#development-workflow)
5. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
6. [Advanced Configuration](#advanced-configuration)

---

## Overview

### GitHub Actions First Policy

**ALL deployments MUST use GitHub Actions CI/CD pipeline:**
- ✅ **Audit Trail**: All changes tracked in Git history
- ✅ **Quality Gates**: Automated validation, testing, comprehensive security scanning
- ✅ **Team Visibility**: All deployments visible to team members
- ✅ **Enterprise Compliance**: Meets deployment standards and governance
- ✅ **Rollback Capability**: Git-based rollback and deployment history
- ✅ **OIDC Security**: Secure AWS access without storing credentials

### Current Infrastructure

| Component | Value | Purpose |
|-----------|-------|---------|
| **Workflow** | `.github/workflows/deploy.yml` | Main CI/CD orchestration |
| **Repository** | `johnjcousens/aws-elasticdrs-orchestrator` | GitHub source repository |
| **Authentication** | OIDC (OpenID Connect) | Secure AWS access |
| **OIDC Stack** | `cfn/github-oidc-stack.yaml` | IAM role for GitHub Actions |
| **Account** | 777788889999 | AWS account for all resources |
| **Deployment Bucket** | `aws-elasticdrs-orchestrator` | Artifact storage |

---

## Quick Start

### For Existing Setup (Most Common)

If the infrastructure is already deployed, simply push to trigger deployment:

```bash
# Standard development workflow
git add .
git commit -m "feat: your changes"
git push origin main  # Triggers GitHub Actions deployment

# Monitor at: https://github.com/johnjcousens/aws-elasticdrs-orchestrator/actions
```

### For New Setup (First Time)

#### Step 1: Deploy GitHub OIDC Stack

```bash
# Set your parameters
export PROJECT_NAME="aws-elasticdrs-orchestrator"
export ENVIRONMENT="dev"
export GITHUB_ORG="your-github-username"
export GITHUB_REPO="your-repo-name"
export DEPLOYMENT_BUCKET="your-deployment-bucket"

# Deploy the OIDC stack (one-time)
aws cloudformation deploy \
  --template-file cfn/github-oidc-stack.yaml \
  --stack-name "${PROJECT_NAME}-github-oidc" \
  --parameter-overrides \
    ProjectName="${PROJECT_NAME}" \
    Environment="${ENVIRONMENT}" \
    GitHubOrg="${GITHUB_ORG}" \
    GitHubRepo="${GITHUB_REPO}" \
    DeploymentBucket="${DEPLOYMENT_BUCKET}" \
    ApplicationStackName="${PROJECT_NAME}-${ENVIRONMENT}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

#### Step 2: Configure GitHub Secrets

Go to GitHub repository → Settings → Secrets and variables → Actions → New repository secret

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ROLE_ARN` | `arn:aws:iam::ACCOUNT_ID:role/PROJECT-github-actions-ENV` | IAM role ARN from Step 1 |
| `DEPLOYMENT_BUCKET` | `your-deployment-bucket` | S3 bucket for artifacts |
| `STACK_NAME` | `aws-elasticdrs-orchestrator-dev` | CloudFormation stack name |
| `ADMIN_EMAIL` | `admin@example.com` | Admin email for Cognito |

#### Step 3: Initial Application Deployment

```bash
# Sync artifacts to S3 first
./scripts/sync-to-deployment-bucket.sh

# Deploy the application stack
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
  --parameter-overrides \
    ProjectName="${PROJECT_NAME}" \
    Environment="${ENVIRONMENT}" \
    SourceBucket="${DEPLOYMENT_BUCKET}" \
    AdminEmail="your-email@example.com" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

#### Step 4: Activate CI/CD

```bash
git add .
git commit -m "feat: activate GitHub Actions CI/CD"
git push origin main
```

---

## Pipeline Architecture

### 6-Stage Pipeline

| Stage | Purpose | Duration | Key Actions |
|-------|---------|----------|-------------|
| **Validate** | Template and code validation | ~2 min | CloudFormation validation, Python linting, TypeScript checking |
| **Security Scan** | **Enhanced comprehensive security analysis** | ~3 min | **Bandit, Safety, Semgrep, CFN-Lint, ESLint, NPM Audit with thresholds** |
| **Build** | Package creation | ~3 min | Lambda packaging, frontend build |
| **Test** | Automated testing | ~2 min | Unit tests, integration tests |
| **Deploy Infrastructure** | AWS resource deployment | ~10 min | CloudFormation stack updates |
| **Deploy Frontend** | Frontend deployment | ~2 min | S3 sync, CloudFront invalidation |

**Total Duration**: ~22 minutes for complete deployment

### Enhanced Security Scanning

The security scanning stage includes **enterprise-grade security validation** with automated thresholds:

#### Security Tools & Versions
- **Bandit v1.9.2** - Python security analysis with medium+ severity detection
- **Safety v2.3.4** - Python dependency vulnerability scanning  
- **Semgrep v1.146.0** - Advanced security pattern matching for Python and YAML
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

---

## Development Workflow

### Standard Workflow (REQUIRED)

```bash
# 1. Make changes locally
# Edit code, test locally where possible

# 2. Validate before committing
make validate  # CloudFormation validation

# 3. Commit and push (triggers CI/CD)
git add .
git commit -m "feat: describe your changes"
git push origin main

# 4. Monitor pipeline
# Visit: https://github.com/johnjcousens/aws-elasticdrs-orchestrator/actions
```

### Manual Deployment (EMERGENCY ONLY)

⚠️ **RESTRICTED**: Manual deployment scripts are for emergencies only.

**Emergency Use Cases:**
- GitHub Actions service outage (confirmed AWS/GitHub issue)
- Critical production hotfix when pipeline is broken
- Pipeline debugging (with immediate Git follow-up)

```bash
# EMERGENCY ONLY: Fast Lambda code update
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# IMMEDIATELY follow up with proper Git commit
git add .
git commit -m "emergency: describe the critical fix"
git push  # Restores proper CI/CD tracking
```

### Prohibited Practices

❌ **NEVER bypass GitHub Actions for regular development**  
❌ **NEVER use manual sync scripts for convenience**  
❌ **NEVER deploy "quick fixes" without Git tracking**  
❌ **NEVER skip the pipeline "just this once"**

---

## Monitoring & Troubleshooting

### Pipeline Monitoring

- **GitHub Actions Console**: https://github.com/johnjcousens/aws-elasticdrs-orchestrator/actions
- **Real-time Status**: Watch each stage progress in the Actions tab
- **Deployment Outputs**: Stack outputs displayed in pipeline summary
- **Artifact Downloads**: Security reports available for 30 days

### Common Issues & Solutions

#### 1. OIDC Authentication Fails

**Symptoms**: `Error: Could not assume role with OIDC`
**Solutions**:
- Verify GitHub repository matches OIDC trust policy
- Ensure workflow runs from correct branch (main)
- Check `id-token: write` permission in workflow

#### 2. CloudFormation Deployment Fails

**Symptoms**: Stack deployment errors
**Solutions**:
- Verify IAM role has sufficient permissions
- Check S3 bucket exists and contains templates
- Ensure stack isn't in failed state (ROLLBACK_COMPLETE)

#### 3. Security Scan Stage Failure

**Symptoms**: Security vulnerabilities detected, build fails due to threshold violations
**Solutions**:
```bash
# Run enhanced security scans locally
bandit -r lambda/ scripts/ -ll --severity-level medium --confidence-level medium
safety check
semgrep --config=python.lang.security lambda/ scripts/ --severity ERROR --severity WARNING
cfn-lint cfn/*.yaml

# Frontend security scanning
cd frontend/
npm audit --audit-level moderate
npx eslint src/ --ext .ts,.tsx

# Generate security summary (requires reports directory)
mkdir -p reports/security/raw reports/security/formatted
python scripts/generate-security-summary.py
python scripts/check-security-thresholds.py
```

**Security Thresholds**:
- **Critical Issues**: 0 allowed (fails build immediately)
- **High Issues**: 10 maximum (warning, continues deployment)  
- **Total Issues**: 50 maximum (informational tracking)

**Common Security Issues**:
- **Bandit B101**: Use of assert statements (replace with proper error handling)
- **Bandit B108**: Hardcoded temporary file paths (use tempfile module)
- **Safety**: Outdated dependencies with known vulnerabilities (update packages)
- **CFN-Lint**: CloudFormation security misconfigurations (follow AWS best practices)
- **NPM Audit**: Frontend dependency vulnerabilities (run `npm audit fix`)

#### 4. Build Stage Failure

**Symptoms**: Lambda packaging or frontend build issues
**Solutions**:
```bash
# Test Lambda packaging locally
cd lambda/api-handler
pip install -r requirements.txt -t .
zip -r api-handler.zip .

# Test frontend build locally
cd frontend/
npm ci
npm run build
```

#### 5. Test Stage Failure

**Symptoms**: Unit test failures
**Solutions**:
```bash
# Run tests locally
cd tests/python
pip install -r requirements.txt
pytest unit/ -v
pytest integration/ -v
```

#### 6. Frontend Deployment Fails

**Symptoms**: S3 sync or CloudFront invalidation errors
**Solutions**:
- Verify stack outputs exist (FrontendBucketName, CloudFrontDistributionId)
- Check S3 bucket permissions allow IAM role to write
- Ensure CloudFront distribution is in deployed state

---

## Advanced Configuration

### Manual Workflow Trigger

You can trigger deployments manually:

1. Go to Actions tab in GitHub
2. Select "Deploy AWS DRS Orchestration"
3. Click "Run workflow"
4. Select environment (dev/test/prod)
5. Click "Run workflow"

### Branch Strategy

- **main**: Production deployments (automatic)
- **feature/***: Development branches (no automatic deployment)
- **Pull Requests**: Run validation and security scans only

### Cost Comparison

| Platform | Monthly Cost |
|----------|--------------|
| AWS Native (CodePipeline + CodeBuild) | $7-19 |
| GitHub Actions (private repo) | $0-50 |
| GitHub Actions (public repo) | Free |

### Security Best Practices

- ✅ Use OIDC instead of long-lived credentials
- ✅ Store sensitive data in GitHub Secrets
- ✅ Enable branch protection for main branch
- ✅ Regular security scanning with comprehensive tool coverage
- ✅ Monitor pipeline execution logs
- ✅ Review security reports regularly

---

## Related Documentation

- [Fresh Deployment Guide](FRESH_DEPLOYMENT_GUIDE.md) - Complete fresh environment setup
- [Development Workflow Guide](../DEVELOPMENT_WORKFLOW_GUIDE.md) - Development best practices
- [Troubleshooting Guide](../TROUBLESHOOTING_GUIDE.md) - General troubleshooting

---

**Built for enterprise disaster recovery on AWS**