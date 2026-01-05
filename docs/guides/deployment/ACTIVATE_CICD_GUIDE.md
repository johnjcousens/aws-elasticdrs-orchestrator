# Activate CI/CD Pipeline - Simple Guide

## Overview
This guide helps you activate the automated CI/CD pipeline so that any code changes automatically deploy to your AWS DRS Orchestration platform. No DevOps experience required!

## What You'll Get
- ✅ Automatic deployments when you make changes
- ✅ Built-in testing and validation
- ✅ No more manual deployment scripts
- ✅ Professional development workflow

## Prerequisites
- AWS DRS Orchestration platform already deployed
- Git configured on your computer
- AWS CLI configured with your credentials

## Step 1: Set Up Git Credentials for CodeCommit

### Option A: Using Git Credential Helper (Recommended)
```bash
# Configure Git to use AWS credentials
git config --global credential.helper '!aws codecommit credential-helper $@'
git config --global credential.UseHttpPath true
```

### Option B: Using HTTPS Git Credentials (Alternative)
1. Go to AWS IAM Console → Users → Your User → Security Credentials
2. Scroll to "HTTPS Git credentials for AWS CodeCommit"
3. Click "Generate credentials" and save the username/password
4. Use these when Git prompts for credentials

## Step 2: Connect Your Local Code to AWS CodeCommit

```bash
# Add the AWS CodeCommit repository as a remote
git remote add aws-pipeline https://git-codecommit.us-east-1.amazonaws.com/v1/repos/aws-elasticdrs-orchestrator-dev

# Verify the remote was added
git remote -v
```

## Step 3: Push Your Code to Activate the Pipeline

```bash
# Make sure all your changes are committed
git add .
git commit -m "Activate CI/CD pipeline with latest code"

# Push to AWS CodeCommit (this will trigger the pipeline!)
git push aws-pipeline main
```

## Step 4: Monitor Your First Pipeline Run

1. **Open the Pipeline Console**:
   - Go to: https://console.aws.amazon.com/codesuite/codepipeline/pipelines/aws-elasticdrs-orchestrator-pipeline-dev/view
   - Or search "CodePipeline" in AWS Console

2. **Watch the Pipeline Stages**:
   - **Source**: Gets your code from CodeCommit ✅
   - **Validate**: Checks CloudFormation templates ✅
   - **Build**: Builds Lambda functions and frontend ✅
   - **Test**: Runs automated tests ✅
   - **DeployInfrastructure**: Updates AWS resources ✅
   - **DeployFrontend**: Updates the web interface ✅

3. **Pipeline Duration**: First run takes ~15-20 minutes

## Step 5: Verify Everything Works

1. **Check the Web Interface**: Visit your CloudFront URL
2. **Test a Feature**: Try creating a protection group
3. **Check Logs**: Look for any errors in the pipeline

## Daily Workflow (After Activation)

### Making Changes
```bash
# 1. Make your code changes
# 2. Test locally if needed
# 3. Commit your changes
git add .
git commit -m "Description of your changes"

# 4. Push to trigger automatic deployment
git push aws-pipeline main
```

### Monitoring Deployments
- **Pipeline Console**: Monitor progress in real-time
- **Notifications**: Get email alerts for failures (if configured)
- **Rollback**: Pipeline automatically rolls back on failures

## Troubleshooting

### Common Issues

**"Permission denied" when pushing to CodeCommit**
- Solution: Check your AWS credentials and Git credential helper setup

**Pipeline fails at Validate stage**
- Solution: CloudFormation template has syntax errors - check the logs

**Pipeline fails at Test stage**
- Solution: Code has bugs - check test results and fix issues

**Pipeline fails at Deploy stage**
- Solution: AWS resource limits or permissions - check CloudFormation events

### Getting Help
1. **Pipeline Logs**: Click on failed stage to see detailed logs
2. **CloudFormation Events**: Check stack events for deployment issues
3. **Lambda Logs**: Check function logs in CloudWatch

## Benefits of Using CI/CD

### For You
- ✅ No more manual deployment scripts
- ✅ Automatic testing catches bugs early
- ✅ Consistent deployments every time
- ✅ Easy rollback if something goes wrong

### For Your Team
- ✅ Multiple developers can work safely
- ✅ All changes are tracked and auditable
- ✅ Professional development workflow
- ✅ Reduced human error

## Advanced Features (Optional)

### Branch-Based Development
```bash
# Create feature branch
git checkout -b new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push feature branch (won't trigger pipeline)
git push aws-pipeline new-feature

# Merge to main when ready (triggers pipeline)
git checkout main
git merge new-feature
git push aws-pipeline main
```

### Environment Promotion
- **Dev Environment**: Automatic deployment from main branch
- **Prod Environment**: Manual promotion after testing

## Next Steps

1. **Activate the pipeline** following steps 1-4 above
2. **Make a small test change** to verify it works
3. **Train your team** on the new workflow
4. **Set up notifications** for pipeline status
5. **Consider branch protection** for production environments

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review pipeline logs in AWS Console
3. Ensure all prerequisites are met
4. Contact your AWS support team if needed

---

**Remember**: The first pipeline run takes longer because it's building everything from scratch. Subsequent runs are much faster!