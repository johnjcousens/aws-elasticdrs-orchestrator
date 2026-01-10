# GitHub Secrets Configuration

## Current Stack Configuration (Updated January 10, 2026)

The following GitHub repository secrets are configured for the **aws-elasticdrs-orchestrator-dev** stack:

### Required Secrets

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ROLE_ARN` | `arn:aws:iam::777788889999:role/GitHubActionsRole` | IAM role for GitHub Actions OIDC |
| `DEPLOYMENT_BUCKET` | `aws-elasticdrs-orchestrator` | S3 bucket for deployment artifacts |
| `STACK_NAME` | `aws-elasticdrs-orchestrator-dev` | CloudFormation stack name |
| `ADMIN_EMAIL` | `jocousen@amazon.com` | Admin email for Cognito user pool |

### Stack Information

- **Stack Name**: `aws-elasticdrs-orchestrator-dev`
- **Stack ARN**: `arn:aws:cloudformation:us-east-1:777788889999:stack/aws-elasticdrs-orchestrator-dev/00c30fb0-eb2b-11f0-9ca6-12010aae964f`
- **Status**: `CREATE_COMPLETE`
- **Region**: `us-east-1`
- **Project Name**: `aws-elasticdrs-orchestrator`
- **Environment**: `dev`

### Stack Outputs

| Output Key | Value | Description |
|------------|-------|-------------|
| `ApiEndpoint` | `https://akp69tt2m1.execute-api.us-east-1.amazonaws.com/dev` | API Gateway endpoint |
| `CloudFrontUrl` | `https://dly5x2oq5f01g.cloudfront.net` | Frontend application URL |
| `UserPoolId` | `us-east-1_ZpRNNnGTK` | Cognito User Pool ID |
| `UserPoolClientId` | `3b9l2jv7engtoeba2t1h2mo5ds` | Cognito User Pool Client ID |
| `IdentityPoolId` | `us-east-1:052133fc-f2f7-4e0f-be2c-02fd84287feb` | Cognito Identity Pool ID |

### Test User Configuration

- **Username**: `testuser@example.com`
- **Password**: `TestPassword123!`
- **Group**: `DRSOrchestrationAdmin` (Full access)

## Setting Up GitHub Secrets

### 1. Navigate to Repository Settings
1. Go to your GitHub repository
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions**

### 2. Add Required Secrets
Click **New repository secret** for each secret:

```bash
# AWS_ROLE_ARN
arn:aws:iam::777788889999:role/GitHubActionsRole

# DEPLOYMENT_BUCKET  
aws-elasticdrs-orchestrator

# STACK_NAME
aws-elasticdrs-orchestrator-dev

# ADMIN_EMAIL
jocousen@amazon.com
```

### 3. Verify Configuration
After adding secrets, verify they appear in the repository secrets list:
- ✅ `AWS_ROLE_ARN`
- ✅ `DEPLOYMENT_BUCKET`
- ✅ `STACK_NAME`
- ✅ `ADMIN_EMAIL`

## GitHub OIDC Setup

The GitHub Actions workflow uses OpenID Connect (OIDC) for secure AWS authentication without storing long-term credentials.

### OIDC Role Configuration
- **Role Name**: `GitHubActionsRole`
- **Trust Policy**: Allows GitHub Actions from your repository
- **Permissions**: CloudFormation, S3, Lambda, API Gateway, Cognito, etc.

### OIDC Stack Deployment
The OIDC role is deployed separately using:
```bash
aws cloudformation deploy \
  --template-file cfn/github-oidc-stack.yaml \
  --stack-name aws-elasticdrs-orchestrator-github-oidc \
  --parameter-overrides \
    ProjectName=aws-elasticdrs-orchestrator \
    Environment=dev \
    GitHubOrg=jocousen \
    GitHubRepo=aws-elasticdrs-orchestrator \
    DeploymentBucket=aws-elasticdrs-orchestrator \
    ApplicationStackName=aws-elasticdrs-orchestrator-dev \
  --capabilities CAPABILITY_NAMED_IAM
```

## Pipeline Workflow

The GitHub Actions workflow (`deploy.yml`) uses these secrets to:

1. **Authenticate** with AWS using OIDC role
2. **Validate** CloudFormation templates
3. **Scan** for security vulnerabilities
4. **Build** Lambda packages and frontend
5. **Test** Python and TypeScript code
6. **Deploy** infrastructure to the specified stack
7. **Deploy** frontend to S3 and CloudFront

## Security Best Practices

### Secret Management
- ✅ Use OIDC instead of long-term AWS keys
- ✅ Rotate secrets regularly
- ✅ Use least-privilege IAM policies
- ✅ Monitor secret usage in GitHub Actions logs

### Access Control
- ✅ Limit repository access to authorized users
- ✅ Use branch protection rules
- ✅ Require pull request reviews
- ✅ Enable security alerts

## Troubleshooting

### Common Issues

#### 1. Authentication Failures
```
Error: Could not assume role with OIDC
```
**Solution**: Verify `AWS_ROLE_ARN` secret matches the actual IAM role ARN

#### 2. Stack Not Found
```
Error: Stack aws-elasticdrs-orchestrator-dev does not exist
```
**Solution**: Verify `STACK_NAME` secret matches the actual CloudFormation stack name

#### 3. S3 Access Denied
```
Error: Access Denied to s3://aws-elasticdrs-orchestrator
```
**Solution**: Verify `DEPLOYMENT_BUCKET` secret and IAM role S3 permissions

#### 4. Invalid Admin Email
```
Error: Invalid email format for AdminEmail parameter
```
**Solution**: Verify `ADMIN_EMAIL` secret contains a valid email address

### Verification Commands

```bash
# Check stack exists
aws cloudformation describe-stacks --stack-name aws-elasticdrs-orchestrator-dev

# Check S3 bucket exists
aws s3 ls s3://aws-elasticdrs-orchestrator/

# Check IAM role exists
aws iam get-role --role-name GitHubActionsRole

# Test API endpoint
curl https://akp69tt2m1.execute-api.us-east-1.amazonaws.com/dev/health
```

## Monitoring

### GitHub Actions
- Monitor workflow runs: `https://github.com/jocousen/aws-elasticdrs-orchestrator/actions`
- Check deployment logs for any authentication or permission issues
- Verify all pipeline stages complete successfully

### AWS Resources
- CloudFormation: Monitor stack events and outputs
- CloudWatch: Check Lambda function logs
- S3: Verify deployment artifacts are uploaded
- API Gateway: Test endpoint functionality

## Updates and Maintenance

### When to Update Secrets
- ✅ Stack name changes
- ✅ S3 bucket changes  
- ✅ IAM role changes
- ✅ Admin email changes
- ✅ Security rotation requirements

### Update Process
1. Update the secret value in GitHub repository settings
2. Test the change with a small commit
3. Monitor the GitHub Actions workflow
4. Verify deployment completes successfully

---

**Last Updated**: January 10, 2026  
**Stack**: aws-elasticdrs-orchestrator-dev  
**Status**: Active and Operational