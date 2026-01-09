# GitHub Secrets Setup for Multi-Stack Deployment

## Overview

The GitHub Actions pipeline now supports deploying to both stacks simultaneously using a matrix strategy with sequential execution. This requires additional GitHub repository secrets for the archive test stack.

## Required GitHub Repository Secrets

### Current Stack Secrets (Already Configured)
- `AWS_ROLE_ARN` - IAM role ARN for current stack deployment
- `DEPLOYMENT_BUCKET` - S3 bucket for current stack artifacts
- `STACK_NAME` - CloudFormation stack name: `aws-elasticdrs-orchestrator-dev`
- `ADMIN_EMAIL` - Admin email for Cognito user pool

### Archive Test Stack Secrets (NEED TO ADD)
- `ARCHIVE_AWS_ROLE_ARN` - IAM role ARN for archive test stack deployment
- `ARCHIVE_DEPLOYMENT_BUCKET` - S3 bucket for archive test stack artifacts
- `ARCHIVE_STACK_NAME` - CloudFormation stack name: `aws-drs-orchestrator-archive-test`
- `ARCHIVE_ADMIN_EMAIL` - Admin email for archive test stack: `jocousen@amazon.com`

## How to Add GitHub Secrets

1. **Navigate to Repository Settings**
   - Go to: https://github.com/YOUR_ORG/aws-elasticdrs-orchestrator/settings/secrets/actions

2. **Add New Repository Secrets**
   - Click "New repository secret"
   - Add each secret with the exact name and value

## Archive Test Stack Values

Based on the existing archive test stack deployment:

```bash
# Archive Test Stack Configuration
ARCHIVE_AWS_ROLE_ARN="arn:aws:iam::777788889999:role/GitHubActionsRole"  # Same as current
ARCHIVE_DEPLOYMENT_BUCKET="aws-drs-orchestrator-archive-test-bucket"     # Needs creation
ARCHIVE_STACK_NAME="aws-drs-orchestrator-archive-test"                   # Existing stack
ARCHIVE_ADMIN_EMAIL="jocousen@amazon.com"                                # As specified
```

## S3 Bucket Creation for Archive Test Stack

The archive test stack needs its own S3 deployment bucket:

```bash
# Create S3 bucket for archive test stack artifacts
aws s3 mb s3://aws-drs-orchestrator-archive-test-bucket --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket aws-drs-orchestrator-archive-test-bucket \
  --versioning-configuration Status=Enabled

# Set lifecycle policy to clean up old versions
aws s3api put-bucket-lifecycle-configuration \
  --bucket aws-drs-orchestrator-archive-test-bucket \
  --lifecycle-configuration file://bucket-lifecycle.json
```

## IAM Role Configuration

The archive test stack can use the same IAM role as the current stack, or create a dedicated role:

### Option 1: Use Same Role (Recommended)
```bash
ARCHIVE_AWS_ROLE_ARN="arn:aws:iam::777788889999:role/GitHubActionsRole"
```

### Option 2: Create Dedicated Role
Deploy a separate GitHub OIDC stack for the archive test stack with its own role.

## Matrix Strategy Benefits

### Sequential Execution
- `max-parallel: 1` ensures no S3 conflicts
- Both stacks deploy the same artifacts
- Consistent deployment process

### Deployment Flow
1. **Build Stage**: Creates Lambda packages and frontend build
2. **Deploy Infrastructure**: 
   - First: Current Stack (`aws-elasticdrs-orchestrator-dev`)
   - Then: Archive Test Stack (`aws-drs-orchestrator-archive-test`)
3. **Deploy Frontend**:
   - First: Current Stack frontend
   - Then: Archive Test Stack frontend

### Safety Features
- Same validation and security scanning for both stacks
- Isolated AWS resources (different stack names)
- Separate S3 buckets prevent artifact conflicts
- Git-based audit trail for both deployments

## Verification Steps

After adding the secrets and deploying:

1. **Check Both Stacks Deploy Successfully**
   ```bash
   # Current stack
   aws cloudformation describe-stacks --stack-name aws-elasticdrs-orchestrator-dev
   
   # Archive test stack
   aws cloudformation describe-stacks --stack-name aws-drs-orchestrator-archive-test
   ```

2. **Verify Lambda Packages Are Correct**
   ```bash
   # Check Lambda function code
   aws lambda get-function --function-name aws-elasticdrs-orchestrator-execution-finder-dev
   aws lambda get-function --function-name aws-drs-orchestrator-execution-finder-test
   ```

3. **Test Both Applications**
   - Current Stack: https://d2d8elt2tpmz1z.cloudfront.net
   - Archive Test Stack: [URL from CloudFormation outputs]

## Troubleshooting

### Common Issues
- **Missing secrets**: Pipeline will fail with clear error messages
- **S3 bucket conflicts**: Use separate buckets for each stack
- **IAM permissions**: Ensure role has access to both stack resources

### Rollback Plan
If issues occur:
1. Remove archive test stack from matrix temporarily
2. Deploy current stack only
3. Fix issues and re-add archive test stack

## Next Steps

1. **Add GitHub secrets** as documented above
2. **Create S3 bucket** for archive test stack
3. **Test deployment** with both stacks
4. **Monitor GitHub Actions** for successful deployment
5. **Verify both applications** are working correctly

This multi-stack approach will fix the Lambda package corruption in the archive test stack and provide consistent deployment for both environments.