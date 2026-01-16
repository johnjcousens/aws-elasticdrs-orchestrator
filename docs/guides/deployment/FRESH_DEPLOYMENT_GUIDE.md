# AWS DRS Orchestration - Fresh Deployment Guide

This guide provides step-by-step instructions for deploying the AWS DRS Orchestration platform to a fresh AWS environment using GitHub Actions CI/CD (MANDATORY) with emergency manual deployment procedures.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (GitHub Actions - MANDATORY)](#quick-start-github-actions---mandatory)
- [Emergency Manual Deployment (RESTRICTED)](#emergency-manual-deployment-restricted)
- [Configuration Options](#configuration-options)
- [Post-Deployment Setup](#post-deployment-setup)
- [Validation and Testing](#validation-and-testing)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedures](#rollback-procedures)

## Prerequisites

### AWS Account Requirements

- **AWS Account**: Clean AWS account or isolated region for deployment
- **AWS CLI**: Version 2.x installed and configured
- **Permissions**: Administrator access or equivalent permissions for:
  - CloudFormation (full access)
  - S3 (full access)
  - IAM (full access)
  - Lambda (full access)
  - API Gateway (full access)
  - Cognito (full access)
  - DynamoDB (full access)
  - Step Functions (full access)
  - EventBridge (full access)
  - CloudFront (full access)
  - CodeCommit, CodeBuild, CodePipeline (if CI/CD enabled)

### Automated S3 Bucket Cleanup

**✅ IMPLEMENTED**: The deployment includes automated S3 bucket cleanup functionality:

- **Bucket Cleaner Lambda**: Automatically empties S3 buckets during stack deletion
- **Custom Resources**: `EmptyArtifactBucketResource` and `EmptyFrontendBucketResource` handle cleanup
- **DeletionPolicy**: All S3 buckets configured with `DeletionPolicy: Delete`
- **Lifecycle Rules**: Automatic cleanup of old versions and incomplete uploads

**Benefits**:
- No manual S3 bucket cleanup required
- Complete stack deletion without leaving orphaned resources
- Prevents "bucket not empty" errors during CloudFormation deletion
- Tested and verified working in end-to-end deployment scenarios

### Local Environment Requirements

- **Operating System**: macOS, Linux, or Windows with WSL
- **Tools Required**:
  - AWS CLI v2.x
  - jq (JSON processor)
  - curl (for API testing)
  - Git (for repository management)

### Installation Commands

```bash
# macOS (using Homebrew)
brew install awscli jq curl git

# Ubuntu/Debian
sudo apt update
sudo apt install awscli jq curl git

# Amazon Linux 2
sudo yum install awscli jq curl git
```

### AWS Credentials Configuration

```bash
# Configure AWS credentials
aws configure

# Verify credentials
aws sts get-caller-identity

# Set default region (recommended: us-east-1)
export AWS_DEFAULT_REGION=us-east-1
```

## Quick Start (GitHub Actions - MANDATORY)

⚠️ **CRITICAL**: GitHub Actions CI/CD is the **MANDATORY** deployment method. Manual scripts are for emergencies only.

### Standard GitHub Actions Deployment

```bash
# 1. Clone the repository
git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git
cd aws-elasticdrs-orchestrator

# 2. Verify GitHub Actions is configured (one-time setup)
# Check: .github/workflows/deploy.yml exists
# Check: GitHub repository secrets are configured

# 3. MANDATORY: Check for running workflows before pushing
./scripts/check-workflow.sh

# 4. Deploy via GitHub Actions (REQUIRED)
git add .
git commit -m "feat: initial deployment"
./scripts/safe-push.sh  # RECOMMENDED - auto-checks workflows

# 5. Monitor deployment at:
# https://github.com/johnjcousens/aws-elasticdrs-orchestrator/actions
```

### Required GitHub Secrets

Configure these secrets in GitHub repository → Settings → Secrets and variables → Actions:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ROLE_ARN` | `arn:aws:iam::{account-id}:role/aws-elasticdrs-orchestrator-github-actions-dev` | IAM role for GitHub Actions |
| `DEPLOYMENT_BUCKET` | `aws-elasticdrs-orchestrator` | S3 deployment bucket |
| `STACK_NAME` | `aws-elasticdrs-orchestrator-dev` | CloudFormation stack name |
| `ADMIN_EMAIL` | `admin@yourcompany.com` | Admin email for Cognito |

### Pipeline Stages (7 total)

1. **Detect Changes** (~10s) - Analyzes changed files for deployment scope
2. **Validate** (~2 min) - CloudFormation validation, code quality
3. **Security Scan** (~3 min) - Comprehensive security analysis
4. **Build** (~3 min) - Lambda packaging (7 functions), frontend build
5. **Test** (~2 min) - Unit and integration tests
6. **Deploy Infrastructure** (~10 min) - CloudFormation stack deployment
7. **Deploy Frontend** (~2 min) - S3 sync, CloudFront invalidation

**Total Duration**: ~22 minutes for complete deployment

## Emergency Manual Deployment (RESTRICTED)

⚠️ **WARNING**: Manual deployment bypasses all quality gates and should ONLY be used for:
- GitHub Actions service outage (confirmed AWS/GitHub issue)
- Critical production hotfix when pipeline is broken
- Pipeline debugging (with immediate Git follow-up)

### Emergency Procedure

```bash
# EMERGENCY ONLY: Manual fresh deployment
./scripts/fresh-deployment-setup.sh --admin-email admin@yourcompany.com

# IMMEDIATELY follow up with proper Git commit
git add .
git commit -m "emergency: fresh deployment setup"
./scripts/safe-push.sh  # Restores proper CI/CD tracking
```

**Prohibited Practices**:
- ❌ Use manual deployment for regular development
- ❌ Deploy "quick fixes" without Git tracking
- ❌ Bypass pipeline for convenience
- ❌ Skip the pipeline "just this once"

## Detailed Deployment Process

### Step 1: Repository Setup

```bash
# Clone the repository
git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git
cd aws-elasticdrs-orchestrator

# Verify you're in the correct directory
ls -la cfn/master-template.yaml
```

### Step 2: Pre-Deployment Validation

```bash
# Validate AWS credentials and permissions
aws sts get-caller-identity
aws cloudformation list-stacks --region us-east-1 --max-items 1

# Validate CloudFormation templates
make validate

# Optional: Run dry-run to see what will be deployed
./scripts/fresh-deployment-setup.sh --admin-email admin@yourcompany.com --dry-run
```

### Step 3: Execute Fresh Deployment

```bash
# Basic deployment with default settings
./scripts/fresh-deployment-setup.sh --admin-email admin@yourcompany.com

# Custom deployment with specific configuration
./scripts/fresh-deployment-setup.sh \
  --project-name my-drs-orchestrator \
  --environment prod \
  --region us-west-2 \
  --admin-email admin@yourcompany.com \
  --enable-cicd

# Monitor deployment progress
aws cloudformation describe-stack-events \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'StackEvents[0:10].[Timestamp,ResourceStatus,ResourceType,LogicalResourceId]' \
  --output table
```

### Step 4: Monitor Deployment Progress

The deployment process includes these phases:

1. **AWS Credentials Validation** (1 minute)
2. **S3 Deployment Bucket Setup** (2 minutes)
3. **Artifact Upload** (5-10 minutes)
4. **Infrastructure Deployment** (15-25 minutes)
5. **Post-Deployment Configuration** (2-5 minutes)

**Total Expected Time**: 25-45 minutes

### Step 5: Verify Deployment Success

```bash
# Run validation script
./scripts/validate-fresh-deployment.sh

# Check stack status
aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'Stacks[0].StackStatus'

# Get application URLs
aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text
```

## Configuration Options

### Environment Variables

Set these before running the deployment script:

```bash
export PROJECT_NAME="aws-elasticdrs-orchestrator"
export ENVIRONMENT="dev"
export AWS_REGION="us-east-1"
export ADMIN_EMAIL="admin@yourcompany.com"
```

### Command Line Options

```bash
./scripts/fresh-deployment-setup.sh [OPTIONS]

OPTIONS:
  -p, --project-name NAME     Project name (default: aws-elasticdrs-orchestrator)
  -e, --environment ENV       Environment (default: dev)
  -b, --bucket BUCKET         S3 deployment bucket (default: aws-elasticdrs-orchestrator)
  -r, --region REGION         AWS region (default: us-east-1)
  -a, --admin-email EMAIL     Admin email for Cognito (REQUIRED)
  --enable-cicd               Enable CI/CD pipeline (default: true)
  --disable-cicd              Disable CI/CD pipeline
  --dry-run                   Show what would be done without executing
  -v, --verbose               Enable verbose output
  -h, --help                  Show help message
```

### CloudFormation Parameters

The deployment script automatically configures these parameters:

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| ProjectName | aws-elasticdrs-orchestrator | Project name for resource naming |
| Environment | dev | Environment name (dev, test, prod) |
| SourceBucket | aws-elasticdrs-orchestrator | S3 bucket for deployment artifacts |
| AdminEmail | (required) | Email for initial Cognito admin user |
| EnableAutomatedDeployment | true | Enable CI/CD pipeline |
| GitHubRepositoryURL | https://github.com/johnjcousens/aws-elasticdrs-orchestrator | GitHub repository for mirroring |
| EnableWAF | true | Enable AWS WAF protection |
| EnableCloudTrail | true | Enable audit logging |
| EnableSecretsManager | true | Enable secure credential storage |

## Post-Deployment Setup

### Step 1: Access the Application

```bash
# Get the CloudFront URL from stack outputs
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text)

echo "Frontend URL: $CLOUDFRONT_URL"
```

### Step 2: Login with Test User

The deployment script automatically creates a test user:

- **Email**: `***REMOVED***`
- **Password**: `***REMOVED***`
- **Role**: Admin (full access)

### Step 3: Configure Cross-Account Roles

For DRS operations in other AWS accounts:

```bash
# Add target account using the API
curl -X POST "$API_ENDPOINT/target-accounts" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "accountId": "123456789012",
    "roleName": "aws-elasticdrs-orchestrator-cross-account-role",
    "regions": ["us-east-1", "us-west-2"]
  }'
```

### Step 4: Create Your First Protection Group

1. Navigate to **Protection Groups** in the web interface
2. Click **Create Protection Group**
3. Configure:
   - **Name**: `Web-Tier-Servers`
   - **Region**: `us-east-1`
   - **Servers**: Select from discovered DRS source servers
4. Save the protection group

### Step 5: Set Up CI/CD Pipeline (if enabled)

```bash
# Get CodeCommit repository URL
REPO_URL=$(aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`RepositoryCloneUrlHttp`].OutputValue' \
  --output text)

# Clone and configure the repository
git clone $REPO_URL aws-drs-orchestrator-cicd
cd aws-drs-orchestrator-cicd

# Add your code and push to trigger the pipeline
git add .
git commit -m "Initial commit"
git push origin main
```

## Validation and Testing

### Automated Validation

```bash
# Run comprehensive validation
./scripts/validate-fresh-deployment.sh --verbose

# Run integration tests
cd tests/integration/fresh-deployment
pip install -r requirements.txt
python test_fresh_deployment.py
```

### Manual Validation Checklist

- [ ] **Frontend Access**: Can access CloudFront URL
- [ ] **User Authentication**: Can login with test user
- [ ] **API Endpoints**: Health endpoint returns 200
- [ ] **Protection Groups**: Can create and list protection groups
- [ ] **Recovery Plans**: Can create recovery plans
- [ ] **DRS Integration**: Can discover source servers
- [ ] **Cross-Account**: Can configure target accounts
- [ ] **CI/CD Pipeline**: Pipeline executes successfully (if enabled)

### Performance Validation

Expected performance metrics:

- **Deployment Time**: < 45 minutes
- **Frontend Load Time**: < 3 seconds
- **API Response Time**: < 500ms for most endpoints
- **DRS Server Discovery**: < 30 seconds per region

## Troubleshooting

### Common Issues and Solutions

#### 1. Deployment Fails with "Bucket Already Exists"

**Problem**: S3 bucket name conflicts with existing bucket.

**Solution**:
```bash
# Use a unique bucket name
./scripts/fresh-deployment-setup.sh \
  --bucket my-unique-drs-orchestrator-bucket \
  --admin-email admin@yourcompany.com
```

#### 2. CloudFormation Stack Creation Fails

**Problem**: Insufficient permissions or resource limits.

**Solution**:
```bash
# Check stack events for specific error
aws cloudformation describe-stack-events \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'

# Common fixes:
# - Increase service limits (Lambda concurrent executions, API Gateway)
# - Verify IAM permissions
# - Check region availability for all services
```

#### 3. Lambda Functions Fail to Deploy

**Problem**: Lambda package too large or missing dependencies.

**Solution**:
```bash
# Rebuild Lambda packages
cd lambda
for dir in */; do
  cd "$dir"
  pip install -r requirements.txt -t . --upgrade
  cd ..
done

# Re-run deployment
./scripts/fresh-deployment-setup.sh --admin-email admin@yourcompany.com
```

#### 4. Frontend Not Accessible

**Problem**: CloudFront distribution not fully deployed.

**Solution**:
```bash
# Check CloudFront distribution status
aws cloudfront list-distributions \
  --query 'DistributionList.Items[?contains(Comment,`aws-elasticdrs-orchestrator`)].Status'

# Wait for distribution to be "Deployed" (can take 15-20 minutes)
# Then test access again
```

#### 5. API Gateway Returns 403 Errors

**Problem**: WAF blocking requests or CORS configuration.

**Solution**:
```bash
# Check WAF rules
aws wafv2 list-web-acls --scope REGIONAL --region us-east-1

# Test API without WAF (temporarily disable in CloudFormation)
# Or add your IP to WAF allow list
```

#### 6. Cognito User Cannot Login

**Problem**: User not confirmed or password policy issues.

**Solution**:
```bash
# Get User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Confirm test user
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id $USER_POOL_ID \
  --username ***REMOVED*** \
  --region us-east-1

# Reset password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username ***REMOVED*** \
  --password ***REMOVED*** \
  --permanent \
  --region us-east-1
```

### Debug Commands

```bash
# Check all stack resources
aws cloudformation list-stack-resources \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1

# Check Lambda function logs
aws logs tail /aws/lambda/aws-elasticdrs-orchestrator-api-handler-dev \
  --since 1h --region us-east-1

# Check API Gateway logs
aws logs tail /aws/apigateway/aws-elasticdrs-orchestrator-api-dev \
  --since 1h --region us-east-1

# Test API endpoints directly
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

curl -v "$API_ENDPOINT/health"
```

## Rollback Procedures

### Emergency Rollback

If the deployment fails or causes issues:

```bash
# 1. Delete the CloudFormation stack
aws cloudformation delete-stack \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1

# 2. Monitor deletion progress
aws cloudformation describe-stack-events \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'StackEvents[0:10].[Timestamp,ResourceStatus,ResourceType]' \
  --output table

# 3. Clean up S3 bucket (if needed)
aws s3 rm s3://aws-elasticdrs-orchestrator --recursive
aws s3 rb s3://aws-elasticdrs-orchestrator

# 4. Verify cleanup
aws cloudformation list-stacks \
  --stack-status-filter DELETE_COMPLETE \
  --region us-east-1 \
  --query 'StackSummaries[?StackName==`aws-elasticdrs-orchestrator-dev`]'
```

### Partial Rollback

To rollback specific components:

```bash
# Rollback to previous stack version
aws cloudformation cancel-update-stack \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1

# Or continue rollback if stuck
aws cloudformation continue-update-rollback \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1
```

## Next Steps

After successful deployment:

1. **Configure DRS Source Servers**: Set up replication for your source servers
2. **Create Recovery Plans**: Define multi-tier recovery workflows
3. **Set Up Monitoring**: Configure CloudWatch alarms and notifications
4. **Schedule Drills**: Set up automated disaster recovery testing
5. **Team Training**: Train your team on the new platform
6. **Documentation**: Customize documentation for your environment

## Support and Resources

- **Documentation**: `docs/` directory in the repository
- **API Reference**: `docs/guides/API_REFERENCE_GUIDE.md`
- **Troubleshooting**: `docs/guides/TROUBLESHOOTING_GUIDE.md`
- **GitHub Issues**: https://github.com/johnjcousens/aws-elasticdrs-orchestrator/issues

## Security Considerations

- **IAM Roles**: Review and customize IAM permissions for your security requirements
- **Network Security**: Configure VPC, security groups, and NACLs as needed
- **Encryption**: All data is encrypted in transit and at rest by default
- **Audit Logging**: CloudTrail is enabled for all API calls
- **WAF Protection**: Web Application Firewall protects API endpoints

## Cost Optimization

Expected monthly costs for a typical deployment:

- **Lambda**: $10-50 (depending on usage)
- **DynamoDB**: $5-25 (depending on data volume)
- **API Gateway**: $3-15 (depending on requests)
- **CloudFront**: $1-10 (depending on traffic)
- **S3**: $1-5 (for static assets)
- **Other Services**: $10-30 (Cognito, Step Functions, EventBridge)

**Total Estimated Cost**: $30-135/month

To optimize costs:
- Use DynamoDB On-Demand pricing for variable workloads
- Configure CloudFront caching appropriately
- Set up Lambda reserved concurrency if needed
- Monitor and optimize based on actual usage patterns