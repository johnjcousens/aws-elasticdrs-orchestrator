# Activate CI/CD Pipeline - Simple Guide

## Overview
This guide helps you use the **GitHub Actions** CI/CD infrastructure for the AWS DRS Orchestration platform. The pipeline is ready and waiting for your code!

## Current CI/CD Infrastructure ✅

Your GitHub repository has these components deployed and ready:

| Component | Name | Status |
|-----------|------|--------|
| **Workflow** | `.github/workflows/deploy.yml` | ✅ Active |
| **Repository** | `johnjcousens/aws-elasticdrs-orchestrator` | ✅ Ready |
| **Authentication** | OIDC (OpenID Connect) | ✅ Configured |
| **OIDC Stack** | `cfn/github-oidc-stack.yaml` | ✅ Deployed |
| **Account** | 777788889999 | ✅ Configured |
| **Deployment Bucket** | `aws-elasticdrs-orchestrator` | ✅ Active |

## What You'll Get
- ✅ **6-Stage Pipeline**: Validate → Security Scan → Build → Test → Deploy Infrastructure → Deploy Frontend
- ✅ **~20 minute deployments** with automatic rollback on failures
- ✅ **Security scanning** with Bandit and Safety integration
- ✅ **Real-time monitoring** via GitHub Actions UI
- ✅ **OIDC authentication** - no long-lived AWS credentials needed

## Prerequisites
- GitHub repository access with push permissions
- AWS CLI configured (for manual deployments only)
- Git configured on your computer

## Step 1: Verify GitHub Secrets Are Configured

Go to your GitHub repository → Settings → Secrets and variables → Actions

Verify these secrets exist:

| Secret Name | Description |
|-------------|-------------|
| `AWS_ROLE_ARN` | IAM role ARN for GitHub Actions OIDC |
| `DEPLOYMENT_BUCKET` | S3 bucket for artifacts |
| `STACK_NAME` | CloudFormation stack name |
| `ADMIN_EMAIL` | Admin email for Cognito |

## Step 2: Trigger Your First Pipeline Execution

### Push to GitHub
```bash
# Ensure you're on the main branch
git checkout main

# Make sure all changes are committed
git status

# Push to GitHub to trigger the pipeline
git push origin main
```

**🎉 Congratulations!** Your push to GitHub automatically triggered the 6-stage pipeline!

## Step 3: Monitor Your Pipeline Execution

### GitHub Actions Console Access
- **Direct Link**: https://github.com/johnjcousens/aws-elasticdrs-orchestrator/actions
- **Alternative**: GitHub Repository → Actions tab

### Watch the 6 Pipeline Stages

| Stage | Purpose | Duration | Status Indicator |
|-------|---------|----------|------------------|
| **Validate** | CloudFormation validation, Python linting, TypeScript checking | ~2 min | ✅ |
| **Security Scan** | Bandit security scan, Safety dependency check | ~2 min | ✅ |
| **Build** | Lambda packaging, frontend builds | ~3 min | ✅ |
| **Test** | Unit tests, integration tests | ~2 min | ✅ |
| **Deploy Infrastructure** | CloudFormation stack updates | ~10 min | ✅ |
| **Deploy Frontend** | S3 sync, CloudFront invalidation | ~2 min | ✅ |

**⏱️ Total Duration**: ~20 minutes for complete deployment

## Step 4: Verify Successful Deployment

### Check Application Status
1. **Frontend**: Visit your CloudFront URL to verify the web interface
2. **API**: Test API endpoints to ensure backend functionality
3. **Infrastructure**: Verify CloudFormation stack shows `UPDATE_COMPLETE`

### Verification Commands
```bash
# Get CloudFront URL
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text

# Check stack status
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'Stacks[0].StackStatus' \
  --output text
```

## Daily Development Workflow

### Recommended: GitHub CI/CD (Production Releases)
```bash
# 1. Work on feature branch
git checkout -b feature/new-feature
# Make your changes
git add .
git commit -m "Add new feature"
git push origin feature/new-feature

# 2. Create Pull Request on GitHub
# 3. After merge to main, pipeline triggers automatically
```

### Alternative: Manual Deployment (Development)
```bash
# Fast Lambda code updates (~5 seconds)
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Full CloudFormation deployment (~5-10 minutes)
./scripts/sync-to-deployment-bucket.sh --deploy-cfn

# Build and deploy frontend
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend
```

### When to Use Each Approach

| Scenario | Recommended Approach | Duration |
|----------|---------------------|----------|
| **Daily Development** | Manual deployment with `--update-lambda-code` | ~5 seconds |
| **Infrastructure Changes** | Manual deployment with `--deploy-cfn` | ~5-10 minutes |
| **Production Releases** | GitHub Actions CI/CD | ~20 minutes |
| **Team Collaboration** | GitHub Actions CI/CD | ~20 minutes |
| **Security Validation** | GitHub Actions CI/CD (includes security scanning) | ~20 minutes |

### Pipeline Triggers

| Action | Result |
|--------|--------|
| `git push origin main` | ✅ **Automatic deployment** (~20 minutes) |
| Pull Request to main | ✅ **Validation and testing** (no deployment) |
| Manual workflow dispatch | ✅ **Full deployment** with environment selection |

## Manual Workflow Trigger

You can also trigger deployments manually:

1. Go to GitHub repository → Actions tab
2. Select "Deploy AWS DRS Orchestration"
3. Click "Run workflow"
4. Select environment (dev/test/prod)
5. Click "Run workflow"

## Troubleshooting

### Common Issues

#### OIDC Authentication Fails
**Symptoms**: Pipeline fails with "Could not assume role" error
**Solution**: 
```bash
# Verify OIDC stack is deployed
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-github-oidc \
  --region us-east-1

# Check GitHub repository matches trust policy
# Ensure workflow has id-token: write permission
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

#### Pipeline fails at Security Scan stage
**Symptoms**: Security vulnerabilities detected
**Solution**:
```bash
# Run security scan locally
bandit -r lambda/ -f json

# Run Safety dependency check
safety check -r lambda/requirements.txt
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

#### Pipeline fails at Deploy Infrastructure stage
**Symptoms**: CloudFormation deployment errors
**Solution**:
```bash
# Check CloudFormation events for specific errors
AWS_PAGER="" aws cloudformation describe-stack-events \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --region us-east-1 \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`]' | head -50
```

### Getting Help
1. **GitHub Actions Logs**: Click on failed job to see detailed logs
2. **CloudFormation Events**: Check stack events for deployment issues
3. **Lambda Logs**: Check function logs in CloudWatch for runtime issues

## Benefits of Using GitHub Actions CI/CD

### Technical Benefits
- ✅ **6-Stage Validation**: Comprehensive validation, security scanning, testing, and deployment
- ✅ **OIDC Authentication**: Secure AWS access without long-lived credentials
- ✅ **No Circular Dependencies**: GitHub Actions runs outside AWS
- ✅ **Security Scanning**: Built-in Bandit and Safety security analysis
- ✅ **Real-time Monitoring**: GitHub Actions UI with detailed logs

### Development Benefits
- ✅ **Native Git Integration**: No CodeCommit mirroring required
- ✅ **Fast Feedback**: Know within ~20 minutes if your changes work
- ✅ **Consistent Deployments**: Same process every time, reducing human error
- ✅ **Audit Trail**: Complete history of all deployments and changes
- ✅ **Team Collaboration**: Pull request workflow with automatic validation

### Operational Benefits
- ✅ **Zero Downtime**: Rolling deployments with automatic health checks
- ✅ **Cost Effective**: Free for public repos, pay-per-use for private
- ✅ **Scalable**: Handles any size deployment automatically
- ✅ **Reliable**: GitHub-managed infrastructure with high availability

## Next Steps

1. **✅ Complete Setup**: Follow steps 1-4 above to activate your pipeline
2. **🧪 Test the Workflow**: Make a small change and push to verify everything works
3. **👥 Train Your Team**: Share this guide with other developers
4. **🔒 Consider Branch Protection**: Set up branch protection rules for main branch

## Pipeline Resources

### Quick Links
- **GitHub Actions**: https://github.com/johnjcousens/aws-elasticdrs-orchestrator/actions
- **CloudFormation Stack**: [aws-elasticdrs-orchestrator-dev](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?stackId=aws-elasticdrs-orchestrator-dev)
- **S3 Deployment Bucket**: [aws-elasticdrs-orchestrator](https://s3.console.aws.amazon.com/s3/buckets/aws-elasticdrs-orchestrator)

### Documentation
- **[CI/CD Setup Guide](CICD_SETUP_GUIDE.md)**: Detailed technical documentation
- **[GitHub Actions Setup Guide](GITHUB_ACTIONS_SETUP_GUIDE.md)**: OIDC setup details
- **[Development Workflow Guide](../DEVELOPMENT_WORKFLOW_GUIDE.md)**: Complete development procedures
- **[Troubleshooting Guide](../TROUBLESHOOTING_GUIDE.md)**: Common issues and solutions

## Support

If you encounter issues:
1. ✅ **Check this troubleshooting section** for common solutions
2. ✅ **Review GitHub Actions logs** for specific error details
3. ✅ **Verify prerequisites** are met (GitHub secrets configured)
4. ✅ **Test locally** before pushing to identify issues early

---

**🎉 Success!** You now have enterprise-grade CI/CD automation for your AWS DRS Orchestration platform. Every code change automatically goes through validation, security scanning, testing, and deployment!
