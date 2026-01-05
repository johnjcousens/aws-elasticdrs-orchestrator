# Activate CI/CD Pipeline - Simple Guide

## Overview
This guide helps you use the **already deployed** AWS CodePipeline CI/CD infrastructure for the AWS DRS Orchestration platform. The pipeline is ready and waiting for your code!

## Current CI/CD Infrastructure ✅

Your AWS account already has these components deployed and ready:

| Component | Name | Status |
|-----------|------|--------|
| **Pipeline** | `aws-elasticdrs-orchestrator-pipeline-dev` | ✅ Active |
| **Primary Repository** | `aws-elasticdrs-orchestrator-dev` (CodeCommit) | ✅ Ready |
| **Secondary Repository** | GitHub mirror | ✅ Available |
| **Account** | 438465159935 | ✅ Configured |
| **Deployment Bucket** | `aws-elasticdrs-orchestrator` | ✅ Active |

## What You'll Get
- ✅ **7-Stage Pipeline**: Validate → SecurityScan → Build → Test → Deploy Infrastructure → Deploy Frontend
- ✅ **15-20 minute deployments** with automatic rollback on failures
- ✅ **Security scanning** with Bandit and cfn-lint integration
- ✅ **Real-time monitoring** via AWS Console
- ✅ **Professional development workflow** with AWS-native tools

## Prerequisites
- AWS CLI configured with profile `438465159935_AdministratorAccess`
- Git configured on your computer
- Access to both GitHub and CodeCommit repositories

## Step 1: Configure AWS Profile and Git Credentials

### Set AWS Profile
```bash
# Set the correct AWS profile for the deployed infrastructure
export AWS_PROFILE=438465159935_AdministratorAccess

# Verify you're using the correct account
aws sts get-caller-identity
# Should show Account: 438465159935
```

### Configure Git for CodeCommit
```bash
# Configure Git to use AWS credentials for CodeCommit
git config --global credential.helper '!aws codecommit credential-helper $@'
git config --global credential.UseHttpPath true
```

## Step 2: Connect to the Deployed CI/CD Infrastructure

### Add CodeCommit Remote
```bash
# Navigate to your local repository
cd aws-elasticdrs-orchestrator

# Add the deployed CodeCommit repository as a remote
git remote add aws-pipeline https://git-codecommit.us-east-1.amazonaws.com/v1/repos/aws-elasticdrs-orchestrator-dev

# Verify both remotes are configured
git remote -v
# Should show:
# origin          https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git
# aws-pipeline    https://git-codecommit.us-east-1.amazonaws.com/v1/repos/aws-elasticdrs-orchestrator-dev
```

## Step 3: Trigger Your First Pipeline Execution

### Push to CodeCommit
```bash
# Ensure you're on the main branch
git checkout main

# Make sure all changes are committed
git status

# Push to CodeCommit to trigger the pipeline
export AWS_PROFILE=438465159935_AdministratorAccess
git push aws-pipeline main
```

**🎉 Congratulations!** Your push to CodeCommit automatically triggered the 7-stage pipeline!

## Step 4: Monitor Your Pipeline Execution

### Pipeline Console Access
- **Direct Link**: [aws-elasticdrs-orchestrator-pipeline-dev](https://console.aws.amazon.com/codesuite/codepipeline/pipelines/aws-elasticdrs-orchestrator-pipeline-dev/view)
- **Alternative**: AWS Console → CodePipeline → Pipelines → `aws-elasticdrs-orchestrator-pipeline-dev`

### Watch the 7 Pipeline Stages

| Stage | Purpose | Duration | Status Indicator |
|-------|---------|----------|------------------|
| **Source** | Retrieves code from CodeCommit | ~30s | ✅ |
| **Validate** | CloudFormation validation, Python linting | ~2-3min | ✅ |
| **SecurityScan** | Bandit security scan, cfn-lint checks | ~3-4min | ✅ |
| **Build** | Lambda packaging, frontend builds | ~4-5min | ✅ |
| **Test** | Unit tests, integration tests, coverage | ~3-4min | ✅ |
| **DeployInfrastructure** | CloudFormation stack updates | ~8-10min | ✅ |
| **DeployFrontend** | S3 sync, CloudFront invalidation | ~2-3min | ✅ |

### Pipeline Monitoring Commands
```bash
# Check current pipeline status
export AWS_PROFILE=438465159935_AdministratorAccess
aws codepipeline get-pipeline-state \
  --name aws-elasticdrs-orchestrator-pipeline-dev \
  --region us-east-1

# Get recent pipeline executions
aws codepipeline list-pipeline-executions \
  --pipeline-name aws-elasticdrs-orchestrator-pipeline-dev \
  --region us-east-1 \
  --max-items 3
```

**⏱️ Total Duration**: 15-20 minutes for complete deployment

## Step 5: Verify Successful Deployment

### Check Application Status
1. **Frontend**: Visit your CloudFront URL to verify the web interface
2. **API**: Test API endpoints to ensure backend functionality
3. **Infrastructure**: Verify CloudFormation stack shows `UPDATE_COMPLETE`

### Verification Commands
```bash
# Get CloudFront URL
aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text

# Check stack status
aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'Stacks[0].StackStatus' \
  --output text
```

## Daily Development Workflow

### Recommended: GitHub-First Development
```bash
# 1. Work on GitHub repository (for collaboration)
git checkout -b feature/new-feature
# Make your changes
git add .
git commit -m "Add new feature"
git push origin feature/new-feature

# 2. Create Pull Request on GitHub
# 3. After merge to main, sync to CodeCommit
git checkout main
git pull origin main
git push aws-pipeline main  # Triggers automatic deployment
```

### Alternative: Direct CodeCommit Development
```bash
# 1. Work directly on CodeCommit (immediate deployment)
git checkout -b feature/new-feature
# Make your changes
git add .
git commit -m "Add new feature"

# 2. Push to CodeCommit (triggers pipeline immediately)
git push aws-pipeline feature/new-feature

# 3. Merge to main when ready
git checkout main
git merge feature/new-feature
git push aws-pipeline main
```

### Pipeline Triggers

| Action | Result |
|--------|--------|
| `git push aws-pipeline main` | ✅ **Automatic deployment** (15-20 minutes) |
| `git push aws-pipeline feature-branch` | ⚠️ **No automatic trigger** (can be manually started) |
| GitHub Pull Request merge to main | ⚠️ **Manual sync required** to CodeCommit |

## Alternative: Manual Deployment (Without CI/CD)

If you prefer manual deployment for development:

```bash
# Sync all changes to S3 deployment bucket
./scripts/sync-to-deployment-bucket.sh

# Fast Lambda code updates (5 seconds)
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Build and deploy frontend
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend
```

## Troubleshooting

### Common Issues

#### "Permission denied" when pushing to CodeCommit
**Solution**: 
```bash
# Verify AWS profile is set correctly
export AWS_PROFILE=438465159935_AdministratorAccess
aws sts get-caller-identity

# Reconfigure Git credential helper
git config --global credential.helper '!aws codecommit credential-helper $@'
git config --global credential.UseHttpPath true
```

#### Pipeline fails at Validate stage
**Symptoms**: CloudFormation template validation errors
**Solution**: 
```bash
# Validate templates locally before pushing
aws cloudformation validate-template \
  --template-body file://cfn/master-template.yaml \
  --region us-east-1

# Check Python code quality
flake8 lambda/ --config .flake8
black --check lambda/
```

#### Pipeline fails at SecurityScan stage
**Symptoms**: Security vulnerabilities detected by Bandit
**Solution**:
```bash
# Run security scan locally
bandit -r lambda/ -f json

# Run CloudFormation linting
cfn-lint cfn/*.yaml
```

#### Pipeline fails at Build stage
**Symptoms**: Lambda packaging or frontend build issues
**Solution**:
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

#### Pipeline fails at DeployInfrastructure stage
**Symptoms**: CloudFormation deployment errors
**Solution**:
```bash
# Check CloudFormation events for specific errors
aws cloudformation describe-stack-events \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`]'
```

### Getting Help
1. **Pipeline Console**: Click on failed stage to see detailed logs
2. **CloudWatch Logs**: Check `/aws/codebuild/` log groups for build details
3. **CloudFormation Events**: Check stack events for deployment issues
4. **Lambda Logs**: Check function logs in CloudWatch for runtime issues

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

## Benefits of Using the AWS CodePipeline CI/CD

### Technical Benefits
- ✅ **7-Stage Validation**: Comprehensive validation, security scanning, testing, and deployment
- ✅ **AWS-Native Integration**: Seamless integration with CloudFormation, Lambda, S3, and CloudFront
- ✅ **Automatic Rollback**: Failed deployments automatically roll back to previous working state
- ✅ **Security Scanning**: Built-in Bandit security analysis and cfn-lint validation
- ✅ **Real-time Monitoring**: AWS Console integration with detailed logs and metrics

### Development Benefits
- ✅ **Professional Workflow**: Enterprise-grade CI/CD with AWS best practices
- ✅ **Fast Feedback**: Know within 15-20 minutes if your changes work in production
- ✅ **Consistent Deployments**: Same process every time, reducing human error
- ✅ **Audit Trail**: Complete history of all deployments and changes
- ✅ **Team Collaboration**: Multiple developers can work safely with proper branching

### Operational Benefits
- ✅ **Zero Downtime**: Rolling deployments with automatic health checks
- ✅ **Cost Effective**: Pay-per-use pricing, only costs when pipeline runs
- ✅ **Scalable**: Handles any size deployment automatically
- ✅ **Reliable**: AWS-managed infrastructure with 99.9% availability

## Advanced Features

### Branch-Based Development
```bash
# Create feature branch (won't trigger pipeline)
git checkout -b feature/new-dashboard
git push aws-pipeline feature/new-dashboard

# Manually trigger pipeline for feature branch testing
aws codepipeline start-pipeline-execution \
  --name aws-elasticdrs-orchestrator-pipeline-dev \
  --region us-east-1

# Merge to main when ready (triggers automatic deployment)
git checkout main
git merge feature/new-dashboard
git push aws-pipeline main
```

### Pipeline Notifications
```bash
# Set up SNS notifications for pipeline events
aws sns create-topic \
  --name aws-elasticdrs-orchestrator-pipeline-notifications \
  --region us-east-1

# Subscribe to get email notifications
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:438465159935:aws-elasticdrs-orchestrator-pipeline-notifications \
  --protocol email \
  --notification-endpoint your-email@company.com \
  --region us-east-1
```

### Multi-Environment Promotion
- **Development**: Automatic deployment from main branch
- **Testing**: Manual promotion after development validation
- **Production**: Controlled promotion with approval gates

## Next Steps

1. **✅ Complete Setup**: Follow steps 1-5 above to activate your pipeline
2. **🧪 Test the Workflow**: Make a small change and push to verify everything works
3. **👥 Train Your Team**: Share this guide with other developers
4. **📧 Set Up Notifications**: Configure email alerts for pipeline status
5. **🔒 Consider Branch Protection**: Set up branch protection rules for production

## Pipeline Resources

### Quick Links
- **Pipeline Console**: [aws-elasticdrs-orchestrator-pipeline-dev](https://console.aws.amazon.com/codesuite/codepipeline/pipelines/aws-elasticdrs-orchestrator-pipeline-dev/view)
- **CodeCommit Repository**: [aws-elasticdrs-orchestrator-dev](https://console.aws.amazon.com/codesuite/codecommit/repositories/aws-elasticdrs-orchestrator-dev/browse)
- **CloudFormation Stack**: [aws-elasticdrs-orchestrator-dev](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?stackId=aws-elasticdrs-orchestrator-dev)
- **S3 Deployment Bucket**: [aws-elasticdrs-orchestrator](https://s3.console.aws.amazon.com/s3/buckets/aws-elasticdrs-orchestrator)

### Documentation
- **[CI/CD Setup Guide](CICD_SETUP_GUIDE.md)**: Detailed technical documentation
- **[Development Workflow Guide](../DEVELOPMENT_WORKFLOW_GUIDE.md)**: Complete development procedures
- **[Troubleshooting Guide](../TROUBLESHOOTING_GUIDE.md)**: Common issues and solutions

## Support

If you encounter issues:
1. ✅ **Check this troubleshooting section** for common solutions
2. ✅ **Review pipeline logs** in the AWS Console for specific error details
3. ✅ **Verify prerequisites** are met (AWS profile, Git configuration)
4. ✅ **Test locally** before pushing to identify issues early
5. ✅ **Contact your AWS support team** for infrastructure-related issues

---

**🎉 Success!** You now have enterprise-grade CI/CD automation for your AWS DRS Orchestration platform. Every code change automatically goes through validation, security scanning, testing, and deployment - just like the big tech companies!