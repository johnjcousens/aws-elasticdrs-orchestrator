# AWS DRS Orchestration - CI/CD Setup Guide

This guide provides detailed instructions for using and configuring the AWS CodePipeline CI/CD infrastructure for the AWS DRS Orchestration platform.

## Table of Contents

1. [Overview](#overview)
2. [Current Infrastructure](#current-infrastructure)
3. [Quick Start](#quick-start)
4. [Pipeline Architecture](#pipeline-architecture)
5. [Development Workflow](#development-workflow)
6. [Pipeline Monitoring](#pipeline-monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

---

## Overview

The AWS DRS Orchestration platform uses **AWS CodePipeline** for automated CI/CD with the following capabilities:

- **Automated Validation**: CloudFormation template validation, Python/TypeScript linting, security scanning
- **Automated Building**: Lambda packaging, React frontend builds
- **Automated Testing**: Unit tests, integration tests, coverage reports
- **Automated Deployment**: Infrastructure and application deployment
- **Dual Repository Support**: Primary CodeCommit with GitHub mirror

### Pipeline Benefits

- ✅ **7-Stage Pipeline**: Complete validation, build, test, and deployment automation
- ✅ **Security Scanning**: Integrated Bandit and cfn-lint security checks
- ✅ **Fast Deployments**: 15-20 minute full deployments
- ✅ **Rollback Safety**: Automatic rollback on deployment failures
- ✅ **Real-time Monitoring**: AWS Console integration with detailed logs

## Current Infrastructure

### Deployed CI/CD Components

| Component | Name | Purpose |
|-----------|------|---------|
| **Pipeline** | `aws-elasticdrs-orchestrator-pipeline-dev` | Main CI/CD orchestration |
| **Primary Repository** | `aws-elasticdrs-orchestrator-dev` | CodeCommit source repository |
| **Secondary Repository** | GitHub mirror | Development and collaboration |
| **Account** | ***REMOVED*** | AWS account for all resources |
| **Deployment Bucket** | `aws-elasticdrs-orchestrator` | Artifact storage |

### Pipeline Stages

| Stage | Purpose | Duration | Key Actions |
|-------|---------|----------|-------------|
| **Source** | Code retrieval from CodeCommit | ~30s | Repository polling, artifact creation |
| **Validate** | Template and code validation | ~2-3min | CloudFormation validation, Python linting |
| **SecurityScan** | Security analysis | ~3-4min | Bandit security scan, cfn-lint checks |
| **Build** | Package creation | ~4-5min | Lambda packaging, frontend build |
| **Test** | Automated testing | ~3-4min | Unit tests, integration tests, coverage |
| **DeployInfrastructure** | AWS resource deployment | ~8-10min | CloudFormation stack updates |
| **DeployFrontend** | Frontend deployment | ~2-3min | S3 sync, CloudFront invalidation |

## Quick Start

### Prerequisites

- AWS CLI configured with profile `***REMOVED***_AdministratorAccess`
- Git configured on your local machine
- Access to both GitHub and CodeCommit repositories

### Step 1: Configure Git for CodeCommit

```bash
# Set up AWS credential helper for CodeCommit
git config --global credential.helper '!aws codecommit credential-helper $@'
git config --global credential.UseHttpPath true

# Verify AWS profile
export AWS_PROFILE=***REMOVED***_AdministratorAccess
aws sts get-caller-identity
```

### Step 2: Clone and Configure Repository

```bash
# Clone from GitHub (if starting fresh)
git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git
cd aws-elasticdrs-orchestrator

# Add CodeCommit remote
git remote add aws-pipeline https://git-codecommit.us-east-1.amazonaws.com/v1/repos/aws-elasticdrs-orchestrator-dev

# Verify remotes
git remote -v
```

### Step 3: Trigger Your First Pipeline

```bash
# Ensure you're on main branch
git checkout main

# Push to CodeCommit to trigger pipeline
export AWS_PROFILE=***REMOVED***_AdministratorAccess
git push aws-pipeline main
```

### Step 4: Monitor Pipeline Execution

- **Pipeline Console**: [aws-elasticdrs-orchestrator-pipeline-dev](https://console.aws.amazon.com/codesuite/codepipeline/pipelines/aws-elasticdrs-orchestrator-pipeline-dev/view)
- **Expected Duration**: 15-20 minutes for complete deployment
- **Success Indicators**: All 7 stages show green checkmarks

## Pipeline Architecture

```mermaid
flowchart TB
    subgraph GitHub
        GH[GitHub Repository<br/>johnjcousens/aws-elasticdrs-orchestrator]
    end
    
    subgraph AWS["AWS Account: ***REMOVED***"]
        subgraph CodeCommit
            CC[CodeCommit Repository<br/>aws-elasticdrs-orchestrator-dev]
        end
        
        subgraph CodePipeline
            CP[Pipeline<br/>aws-elasticdrs-orchestrator-pipeline-dev]
        end
        
        subgraph CodeBuild["CodeBuild Projects"]
            CB1[Validate Project<br/>Template validation, linting]
            CB2[SecurityScan Project<br/>Bandit, cfn-lint]
            CB3[Build Project<br/>Lambda packaging, frontend build]
            CB4[Test Project<br/>Unit tests, integration tests]
            CB5[Deploy Infra Project<br/>CloudFormation deployment]
            CB6[Deploy Frontend Project<br/>S3 sync, CloudFront invalidation]
        end
        
        subgraph S3
            S3A[Artifact Bucket<br/>Pipeline artifacts]
            S3D[Deployment Bucket<br/>aws-elasticdrs-orchestrator]
        end
        
        subgraph Target["Deployment Targets"]
            CF[CloudFormation Stack<br/>aws-elasticdrs-orchestrator-dev]
            S3F[Frontend Bucket]
            CDN[CloudFront Distribution]
        end
    end
    
    GH -.->|Manual Mirror| CC
    CC -->|Trigger| CP
    CP -->|Stage 1| CB1
    CP -->|Stage 2| CB2
    CP -->|Stage 3| CB3
    CP -->|Stage 4| CB4
    CP -->|Stage 5| CB5
    CP -->|Stage 6| CB6
    CB1 -->|Artifacts| S3A
    CB3 -->|Artifacts| S3A
    CB5 -->|Deploy| CF
    CB5 -->|Upload| S3D
    CB6 -->|Deploy| S3F
    CB6 -->|Invalidate| CDN
```

## Development Workflow

### Daily Development Process

#### Option A: GitHub-First Development (Recommended)
```bash
# 1. Work on GitHub repository
git checkout -b feature/new-feature
# Make changes
git add .
git commit -m "Add new feature"
git push origin feature/new-feature

# 2. Create Pull Request on GitHub
# 3. After merge to main, sync to CodeCommit
git checkout main
git pull origin main
git push aws-pipeline main  # Triggers pipeline
```

#### Option B: Direct CodeCommit Development
```bash
# 1. Work directly on CodeCommit
git checkout -b feature/new-feature
# Make changes
git add .
git commit -m "Add new feature"

# 2. Push to CodeCommit (triggers pipeline immediately)
git push aws-pipeline feature/new-feature

# 3. Merge to main when ready
git checkout main
git merge feature/new-feature
git push aws-pipeline main
```

### Branch Strategy

- **main**: Production-ready code, triggers full deployment
- **feature/***: Feature development branches
- **hotfix/***: Critical fixes, can be fast-tracked
- **develop**: Integration branch (optional)

### Pipeline Triggers

| Action | Trigger | Result |
|--------|---------|--------|
| Push to `main` | Automatic | Full 7-stage pipeline execution |
| Push to feature branch | Manual trigger only | Pipeline can be manually started |
| Pull Request merge | Automatic (if merged to main) | Full deployment |

## Pipeline Monitoring

### Real-Time Monitoring

```bash
# Check pipeline status
export AWS_PROFILE=***REMOVED***_AdministratorAccess
aws codepipeline get-pipeline-state \
  --name aws-elasticdrs-orchestrator-pipeline-dev \
  --region us-east-1

# Get recent pipeline executions
aws codepipeline list-pipeline-executions \
  --pipeline-name aws-elasticdrs-orchestrator-pipeline-dev \
  --region us-east-1 \
  --max-items 5
```

### Stage-Specific Monitoring

```bash
# Monitor specific CodeBuild project
aws codebuild list-builds-for-project \
  --project-name aws-elasticdrs-orchestrator-validate-dev \
  --region us-east-1

# Get build logs
aws logs tail /aws/codebuild/aws-elasticdrs-orchestrator-validate-dev \
  --since 1h --region us-east-1
```

### Pipeline Notifications

Set up SNS notifications for pipeline events:

```bash
# Create SNS topic for notifications
aws sns create-topic \
  --name aws-elasticdrs-orchestrator-pipeline-notifications \
  --region us-east-1

# Subscribe to notifications
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:***REMOVED***:aws-elasticdrs-orchestrator-pipeline-notifications \
  --protocol email \
  --notification-endpoint your-email@company.com \
  --region us-east-1
```

## Troubleshooting

### Common Pipeline Failures

#### 1. Source Stage Failure
**Symptoms**: Pipeline fails to retrieve source code
**Solutions**:
```bash
# Check CodeCommit repository status
aws codecommit get-repository \
  --repository-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1

# Verify Git credentials
git config --get credential.helper
```

#### 2. Validate Stage Failure
**Symptoms**: CloudFormation template validation errors
**Solutions**:
```bash
# Validate templates locally
aws cloudformation validate-template \
  --template-body file://cfn/master-template.yaml \
  --region us-east-1

# Check Python code quality
flake8 lambda/ --config .flake8
black --check lambda/
```

#### 3. SecurityScan Stage Failure
**Symptoms**: Security vulnerabilities detected
**Solutions**:
```bash
# Run Bandit locally
bandit -r lambda/ -f json

# Run cfn-lint locally
cfn-lint cfn/*.yaml
```

#### 4. Build Stage Failure
**Symptoms**: Lambda packaging or frontend build issues
**Solutions**:
```bash
# Test Lambda packaging locally
cd lambda/api-handler
pip install -r requirements.txt -t .
zip -r api-handler.zip .

# Test frontend build locally
cd frontend
npm install
npm run build
```

#### 5. DeployInfrastructure Stage Failure
**Symptoms**: CloudFormation deployment errors
**Solutions**:
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`]'

# Check IAM permissions
aws iam get-role \
  --role-name aws-elasticdrs-orchestrator-dev-cfn-deployment-role
```

### Debug Commands

```bash
# Get detailed pipeline execution information
EXECUTION_ID=$(aws codepipeline list-pipeline-executions \
  --pipeline-name aws-elasticdrs-orchestrator-pipeline-dev \
  --region us-east-1 \
  --query 'pipelineExecutionSummaries[0].pipelineExecutionId' \
  --output text)

aws codepipeline get-pipeline-execution \
  --pipeline-name aws-elasticdrs-orchestrator-pipeline-dev \
  --pipeline-execution-id $EXECUTION_ID \
  --region us-east-1

# Get build project details
aws codebuild batch-get-projects \
  --names aws-elasticdrs-orchestrator-validate-dev \
  --region us-east-1
```

### Pipeline Recovery

```bash
# Retry failed pipeline execution
aws codepipeline retry-stage-execution \
  --pipeline-name aws-elasticdrs-orchestrator-pipeline-dev \
  --stage-name DeployInfrastructure \
  --retry-mode FAILED_ACTIONS \
  --region us-east-1

# Start new pipeline execution
aws codepipeline start-pipeline-execution \
  --name aws-elasticdrs-orchestrator-pipeline-dev \
  --region us-east-1
```

## Advanced Configuration

### Custom BuildSpec Modifications

The pipeline uses these BuildSpec files in the `buildspecs/` directory:

- `validate-buildspec.yml` - Template validation and linting
- `security-scan-buildspec.yml` - Security scanning with Bandit
- `build-buildspec.yml` - Lambda packaging and frontend builds
- `test-buildspec.yml` - Unit and integration testing
- `deploy-infra-buildspec.yml` - CloudFormation deployment
- `deploy-frontend-buildspec.yml` - Frontend deployment

### Environment Variables

Key environment variables used in the pipeline:

```yaml
# Common variables across all stages
PROJECT_NAME: aws-elasticdrs-orchestrator
ENVIRONMENT: dev
DEPLOYMENT_BUCKET: aws-elasticdrs-orchestrator
AWS_REGION: us-east-1
STACK_NAME: aws-elasticdrs-orchestrator-dev
```

### IAM Roles and Permissions

The pipeline uses these service roles:

1. **CodePipeline Service Role**: `aws-elasticdrs-orchestrator-dev-pipeline-service-role`
2. **CodeBuild Service Roles**: Individual roles for each build project
3. **CloudFormation Deployment Role**: `aws-elasticdrs-orchestrator-dev-cfn-deployment-role`

### Multi-Environment Support

To extend the pipeline for multiple environments:

```bash
# Create additional stacks for different environments
aws cloudformation deploy \
  --template-file cfn/codepipeline-stack.yaml \
  --stack-name aws-elasticdrs-orchestrator-test \
  --parameter-overrides Environment=test \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Integration with External Tools

```yaml
# Example: Slack notifications in BuildSpec
post_build:
  commands:
    - |
      if [ "$CODEBUILD_BUILD_SUCCEEDING" = "1" ]; then
        curl -X POST -H 'Content-type: application/json' \
          --data '{"text":"✅ Pipeline succeeded for aws-elasticdrs-orchestrator"}' \
          $SLACK_WEBHOOK_URL
      else
        curl -X POST -H 'Content-type: application/json' \
          --data '{"text":"❌ Pipeline failed for aws-elasticdrs-orchestrator"}' \
          $SLACK_WEBHOOK_URL
      fi
```

## Best Practices

### Security
- ✅ Use least-privilege IAM roles for all pipeline components
- ✅ Store sensitive data in AWS Secrets Manager
- ✅ Enable encryption for all S3 buckets and artifacts
- ✅ Regular security scanning with Bandit and cfn-lint

### Performance
- ✅ Use CodeBuild caching for dependencies
- ✅ Optimize Docker images for build projects
- ✅ Parallel execution where possible
- ✅ Efficient artifact management

### Reliability
- ✅ Comprehensive error handling in BuildSpecs
- ✅ Automatic rollback on deployment failures
- ✅ Health checks and monitoring
- ✅ Backup and recovery procedures

### Cost Optimization
- ✅ Right-sized CodeBuild instances
- ✅ S3 lifecycle policies for artifacts
- ✅ Scheduled builds during off-peak hours
- ✅ Resource cleanup after deployments

This comprehensive CI/CD setup provides enterprise-grade automation for the AWS DRS Orchestration platform with AWS-native services.

## <a name="prerequisites"></a>Prerequisites

### AWS Services Required

- AWS CodeCommit
- AWS CodeBuild
- AWS CodePipeline
- AWS S3 (for artifacts)
- AWS IAM (for service roles)
- AWS Secrets Manager (for GitHub integration)

### Permissions Required

The deployment user/role needs permissions for:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "codecommit:*",
        "codebuild:*",
        "codepipeline:*",
        "s3:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PassRole",
        "secretsmanager:CreateSecret",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "*"
    }
  ]
}
```

### GitHub Requirements (Optional)

- GitHub repository: https://github.com/johnjcousens/aws-elasticdrs-orchestrator
- GitHub Personal Access Token with `repo` permissions
- Webhook configuration for automatic mirroring

## <a name="cicd-architecture"></a>CI/CD Architecture

```mermaid
flowchart TB
    subgraph GitHub
        GH[GitHub Repository]
    end
    
    subgraph AWS
        subgraph CodeCommit
            CC[CodeCommit Repository]
        end
        
        subgraph CodePipeline
            CP[Pipeline]
        end
        
        subgraph CodeBuild
            CB1[Validate Project]
            CB2[Build Project]
            CB3[Test Project]
            CB4[Deploy Infra Project]
            CB5[Deploy Frontend Project]
        end
        
        subgraph S3
            S3A[Artifact Bucket]
            S3D[Deployment Bucket]
        end
        
        subgraph CloudFormation
            CF[Infrastructure Stack]
        end
        
        subgraph Frontend
            S3F[Frontend Bucket]
            CDN[CloudFront]
        end
    end
    
    GH -->|Mirror| CC
    CC -->|Trigger| CP
    CP -->|Execute| CB1
    CP -->|Execute| CB2
    CP -->|Execute| CB3
    CP -->|Execute| CB4
    CP -->|Execute| CB5
    CB1 -->|Artifacts| S3A
    CB2 -->|Artifacts| S3A
    CB3 -->|Artifacts| S3A
    CB4 -->|Deploy| CF
    CB4 -->|Upload| S3D
    CB5 -->|Deploy| S3F
    CB5 -->|Invalidate| CDN
```

## <a name="setup-process"></a>Setup Process

### Step 1: Enable CI/CD During Fresh Deployment

```bash
# Deploy with CI/CD enabled (default)
./scripts/fresh-deployment-setup.sh \
  --admin-email admin@yourcompany.com \
  --enable-cicd

# Or explicitly enable CI/CD
./scripts/fresh-deployment-setup.sh \
  --admin-email admin@yourcompany.com \
  --enable-cicd
```

### Step 2: Configure GitHub Integration (Optional)

If you want automatic mirroring from GitHub:

```bash
# Store GitHub Personal Access Token in Secrets Manager
aws secretsmanager create-secret \
  --name "aws-elasticdrs-orchestrator/dev/github-token" \
  --description "GitHub Personal Access Token for repository mirroring" \
  --secret-string "ghp_your_github_token_here" \
  --region us-east-1

# Update the secret if it already exists
aws secretsmanager update-secret \
  --secret-id "aws-elasticdrs-orchestrator/dev/github-token" \
  --secret-string "ghp_your_github_token_here" \
  --region us-east-1
```

### Step 3: Get Repository Information

```bash
# Get CodeCommit repository URL
REPO_URL=$(aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`RepositoryCloneUrlHttp`].OutputValue' \
  --output text)

echo "CodeCommit Repository: $REPO_URL"

# Get pipeline URL
PIPELINE_URL=$(aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`PipelineUrl`].OutputValue' \
  --output text)

echo "Pipeline Console: $PIPELINE_URL"
```

### Step 4: Clone and Configure Repository

```bash
# Clone the CodeCommit repository
git clone $REPO_URL aws-drs-orchestrator-cicd
cd aws-drs-orchestrator-cicd

# Configure Git credentials (if using HTTPS)
git config credential.helper '!aws codecommit credential-helper $@'
git config credential.UseHttpPath true

# Add the original repository as upstream (optional)
git remote add upstream https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git
```

## <a name="pipeline-configuration"></a>Pipeline Configuration

### Pipeline Parameters

The pipeline is configured with these environment variables:

| Variable | Value | Description |
|----------|-------|-------------|
| PROJECT_NAME | aws-elasticdrs-orchestrator | Project name for resource naming |
| ENVIRONMENT | dev | Environment name |
| DEPLOYMENT_BUCKET | aws-elasticdrs-orchestrator | S3 bucket for deployment artifacts |
| AWS_REGION | us-east-1 | AWS region for deployment |

### Service Roles

The pipeline creates these IAM roles:

1. **CodePipeline Service Role**: `aws-elasticdrs-orchestrator-dev-pipeline-service-role`
2. **CodeBuild Service Roles**: One for each build project
3. **CloudFormation Deployment Role**: `aws-elasticdrs-orchestrator-dev-cfn-deployment-role`

### Artifact Management

- **Source Artifacts**: Stored in CodeCommit
- **Build Artifacts**: Stored in S3 artifact bucket
- **Deployment Artifacts**: Stored in S3 deployment bucket

## <a name="buildspec-customization"></a>BuildSpec Customization

### Validate BuildSpec (`buildspecs/validate-buildspec.yml`)

Customization options:

```yaml
# Add custom validation tools
install:
  runtime-versions:
    python: 3.12
    nodejs: 22
  commands:
    - pip install custom-validator==1.0.0
    - npm install -g custom-linter

# Add custom validation commands
build:
  commands:
    - custom-validator cfn/
    - custom-linter frontend/src/
```

### Build BuildSpec (`buildspecs/build-buildspec.yml`)

Customization options:

```yaml
# Customize Lambda packaging
build:
  commands:
    # Add custom dependencies
    - pip install custom-library==2.0.0 -t lambda/api-handler/
    
    # Custom build steps
    - python scripts/custom-build-step.py
    
    # Custom frontend build
    - cd frontend && npm run build:custom
```

### Test BuildSpec (`buildspecs/test-buildspec.yml`)

Customization options:

```yaml
# Add custom test frameworks
install:
  commands:
    - pip install custom-test-framework==1.0.0

# Custom test execution
build:
  commands:
    # Run custom tests
    - python -m custom_test_framework tests/
    
    # Generate custom reports
    - custom-reporter --output reports/custom-report.xml
```

### Deploy Infrastructure BuildSpec (`buildspecs/deploy-infra-buildspec.yml`)

Customization options:

```yaml
# Custom deployment parameters
build:
  commands:
    # Deploy with custom parameters
    - aws cloudformation deploy \
        --template-file cfn/master-template.yaml \
        --stack-name $PROJECT_NAME-$ENVIRONMENT \
        --parameter-overrides \
          ProjectName=$PROJECT_NAME \
          Environment=$ENVIRONMENT \
          CustomParameter=CustomValue \
        --capabilities CAPABILITY_NAMED_IAM
```

### Deploy Frontend BuildSpec (`buildspecs/deploy-frontend-buildspec.yml`)

Customization options:

```yaml
# Custom frontend deployment
build:
  commands:
    # Custom configuration generation
    - python scripts/generate-custom-config.py
    
    # Custom S3 sync options
    - aws s3 sync frontend/dist/ s3://$FRONTEND_BUCKET/ \
        --delete \
        --cache-control "public, max-age=86400" \
        --exclude "*.html" \
        --exclude "config.js"
```

## <a name="github-integration"></a>GitHub Integration

### Automatic Mirroring Setup

The CI/CD stack automatically sets up GitHub mirroring if a GitHub token is provided:

```bash
# 1. Create GitHub Personal Access Token
# Go to GitHub Settings > Developer settings > Personal access tokens
# Create token with 'repo' permissions

# 2. Store token in AWS Secrets Manager
aws secretsmanager create-secret \
  --name "aws-elasticdrs-orchestrator/dev/github-token" \
  --secret-string "ghp_your_token_here" \
  --region us-east-1

# 3. The CodeCommit stack will automatically configure mirroring
```

### Manual GitHub Integration

If automatic mirroring is not working:

```bash
# 1. Clone both repositories
git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git github-repo
git clone $CODECOMMIT_URL codecommit-repo

# 2. Set up manual sync
cd github-repo
git remote add codecommit $CODECOMMIT_URL

# 3. Push changes to both repositories
git push origin main
git push codecommit main
```

### Webhook Configuration

For real-time mirroring, configure GitHub webhooks:

```bash
# Get webhook URL from CodeCommit stack outputs
WEBHOOK_URL=$(aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`GitHubWebhookUrl`].OutputValue' \
  --output text)

echo "Configure GitHub webhook: $WEBHOOK_URL"
```

## <a name="pipeline-monitoring"></a>Pipeline Monitoring

### Pipeline Status

```bash
# Check pipeline status
aws codepipeline get-pipeline-state \
  --name aws-elasticdrs-orchestrator-dev-pipeline \
  --region us-east-1

# Get pipeline execution history
aws codepipeline list-pipeline-executions \
  --pipeline-name aws-elasticdrs-orchestrator-dev-pipeline \
  --region us-east-1 \
  --max-items 10
```

### Build Project Status

```bash
# List all build projects
aws codebuild list-projects \
  --region us-east-1 \
  --query 'projects[?contains(@, `aws-elasticdrs-orchestrator-dev`)]'

# Get build history for a specific project
aws codebuild list-builds-for-project \
  --project-name aws-elasticdrs-orchestrator-dev-validate \
  --region us-east-1 \
  --max-items 10
```

### CloudWatch Logs

```bash
# View pipeline logs
aws logs tail /aws/codepipeline/aws-elasticdrs-orchestrator-dev-pipeline \
  --since 1h --region us-east-1

# View build logs
aws logs tail /aws/codebuild/aws-elasticdrs-orchestrator-dev-validate \
  --since 1h --region us-east-1
```

### Notifications

Set up SNS notifications for pipeline events:

```bash
# Create SNS topic
aws sns create-topic \
  --name aws-elasticdrs-orchestrator-dev-pipeline-notifications \
  --region us-east-1

# Subscribe to notifications
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:aws-elasticdrs-orchestrator-dev-pipeline-notifications \
  --protocol email \
  --notification-endpoint admin@yourcompany.com \
  --region us-east-1
```

## <a name="troubleshooting"></a>Troubleshooting

### Common Issues

#### 1. Pipeline Fails at Source Stage

**Problem**: CodeCommit repository is empty or inaccessible.

**Solution**:
```bash
# Check repository status
aws codecommit get-repository \
  --repository-name aws-elasticdrs-orchestrator-dev-repo \
  --region us-east-1

# Push initial code
git clone $CODECOMMIT_URL
cd aws-elasticdrs-orchestrator-dev-repo
# Add your code
git add .
git commit -m "Initial commit"
git push origin main
```

#### 2. Validate Stage Fails

**Problem**: CloudFormation templates have syntax errors.

**Solution**:
```bash
# Validate templates locally
aws cloudformation validate-template \
  --template-body file://cfn/master-template.yaml \
  --region us-east-1

# Check build logs
aws codebuild batch-get-builds \
  --ids $(aws codebuild list-builds-for-project \
    --project-name aws-elasticdrs-orchestrator-dev-validate \
    --region us-east-1 \
    --query 'ids[0]' --output text) \
  --region us-east-1 \
  --query 'builds[0].logs.cloudWatchLogs.groupName'
```

#### 3. Build Stage Fails

**Problem**: Lambda packaging or frontend build issues.

**Solution**:
```bash
# Check build project configuration
aws codebuild batch-get-projects \
  --names aws-elasticdrs-orchestrator-dev-build \
  --region us-east-1

# Test build locally
cd lambda/api-handler
pip install -r requirements.txt -t .
zip -r api-handler.zip .
```

#### 4. Deploy Infrastructure Fails

**Problem**: CloudFormation deployment errors.

**Solution**:
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'

# Check deployment role permissions
aws iam get-role \
  --role-name aws-elasticdrs-orchestrator-dev-cfn-deployment-role
```

#### 5. Deploy Frontend Fails

**Problem**: S3 sync or CloudFront invalidation issues.

**Solution**:
```bash
# Check S3 bucket permissions
aws s3api get-bucket-policy \
  --bucket $(aws cloudformation describe-stacks \
    --stack-name aws-elasticdrs-orchestrator-dev \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
    --output text)

# Check CloudFront distribution
aws cloudfront list-distributions \
  --query 'DistributionList.Items[?contains(Comment,`aws-elasticdrs-orchestrator`)].Status'
```

### Debug Commands

```bash
# Get detailed pipeline execution
EXECUTION_ID=$(aws codepipeline list-pipeline-executions \
  --pipeline-name aws-elasticdrs-orchestrator-dev-pipeline \
  --region us-east-1 \
  --query 'pipelineExecutionSummaries[0].pipelineExecutionId' \
  --output text)

aws codepipeline get-pipeline-execution \
  --pipeline-name aws-elasticdrs-orchestrator-dev-pipeline \
  --pipeline-execution-id $EXECUTION_ID \
  --region us-east-1

# Get build details
BUILD_ID=$(aws codebuild list-builds-for-project \
  --project-name aws-elasticdrs-orchestrator-dev-validate \
  --region us-east-1 \
  --query 'ids[0]' --output text)

aws codebuild batch-get-builds \
  --ids $BUILD_ID \
  --region us-east-1
```

## <a name="best-practices"></a>Best Practices

### Security

1. **Least Privilege**: Use minimal IAM permissions for service roles
2. **Secrets Management**: Store sensitive data in AWS Secrets Manager
3. **Encryption**: Enable encryption for all S3 buckets and artifacts
4. **Access Logging**: Enable CloudTrail for all CI/CD activities

### Performance

1. **Caching**: Use CodeBuild caching for dependencies
2. **Parallel Execution**: Run independent stages in parallel
3. **Artifact Optimization**: Minimize artifact sizes
4. **Resource Sizing**: Use appropriate compute resources for build projects

### Reliability

1. **Error Handling**: Implement proper error handling in BuildSpecs
2. **Rollback**: Configure automatic rollback for failed deployments
3. **Monitoring**: Set up comprehensive monitoring and alerting
4. **Testing**: Include comprehensive testing in the pipeline

### Cost Optimization

1. **Build Scheduling**: Schedule builds during off-peak hours
2. **Resource Management**: Use appropriate instance types for builds
3. **Artifact Lifecycle**: Configure S3 lifecycle policies for artifacts
4. **Monitoring**: Monitor and optimize build times and resource usage

### Maintenance

1. **Regular Updates**: Keep BuildSpec files and dependencies updated
2. **Security Patches**: Regularly update base images and tools
3. **Performance Review**: Regularly review and optimize pipeline performance
4. **Documentation**: Keep pipeline documentation up to date

## <a name="advanced-configuration"></a>Advanced Configuration

### Custom Build Images

```yaml
# Use custom Docker image for builds
version: 0.2
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
  build:
    commands:
      - echo Build started on `date`
      - docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker image...
      - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
```

### Multi-Environment Deployment

```yaml
# Deploy to multiple environments
version: 0.2
phases:
  build:
    commands:
      # Deploy to dev
      - aws cloudformation deploy --stack-name $PROJECT_NAME-dev --parameter-overrides Environment=dev
      
      # Deploy to test (after dev succeeds)
      - aws cloudformation deploy --stack-name $PROJECT_NAME-test --parameter-overrides Environment=test
      
      # Deploy to prod (with approval)
      - aws codepipeline put-approval-result --pipeline-name $PIPELINE_NAME --stage-name ApprovalStage --action-name ManualApproval --result summary="Ready for production",status=Approved
```

### Integration with External Tools

```yaml
# Integrate with external tools
version: 0.2
phases:
  pre_build:
    commands:
      # Slack notification
      - curl -X POST -H 'Content-type: application/json' --data '{"text":"Build started"}' $SLACK_WEBHOOK_URL
      
      # JIRA integration
      - python scripts/update-jira-ticket.py --status "In Progress"
  
  post_build:
    commands:
      # Update monitoring dashboard
      - python scripts/update-dashboard.py --build-status $CODEBUILD_BUILD_SUCCEEDING
      
      # Send metrics to external system
      - curl -X POST $METRICS_ENDPOINT -d '{"build_time": "'$BUILD_TIME'", "status": "success"}'
```

This comprehensive CI/CD setup guide provides everything needed to configure, customize, and maintain the AWS DRS Orchestration CI/CD pipeline.