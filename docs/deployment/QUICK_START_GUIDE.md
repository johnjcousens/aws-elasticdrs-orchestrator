# Quick Start Guide - AWS DRS Orchestration

**Stack**: aws-drs-orchestration-dev  
**Environment**: dev  
**Region**: us-east-1

---

## Prerequisites

- AWS CLI v2 configured with credentials
- Access to AWS account
- Node.js 18+ and npm (for frontend development)
- Python 3.12+ (for Lambda development and local CI/CD)

---

## Step 1: Environment Setup

```bash
# Navigate to project directory
cd infra/orchestration/drs-orchestration

# Copy environment template
cp .env.dev.template .env.dev

# Edit with your configuration
vim .env.dev

# Source environment variables
source .env.dev
```

**Required configuration in `.env.dev`:**
- `AWS_ACCOUNT_ID` - Your AWS account ID
- `ADMIN_EMAIL` - Email for Cognito admin user
- Other values can use defaults for dev environment

---

## Step 2: Deploy Infrastructure

### Option A: Full Local CI/CD Deployment (Recommended)

```bash
# Run full CI/CD pipeline: Validate → Security → Build → Test → Deploy
./scripts/local-deploy.sh dev full

# Or quick deployment (skip validation)
./scripts/local-deploy.sh dev full --quick
```

### Option B: Direct CloudFormation Deployment

```bash
# Sync artifacts to S3
./scripts/sync-to-deployment-bucket.sh

# Deploy CloudFormation stack
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

---

## Step 3: Get Stack Outputs

After deployment completes, get the stack outputs:

```bash
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-dev \
  --query 'Stacks[0].Outputs' \
  --output table \
  --region us-east-1
```

Key outputs:
- **CloudFrontURL** - Frontend application URL
- **ApiEndpoint** - REST API endpoint
- **UserPoolId** - Cognito User Pool ID
- **UserPoolClientId** - Cognito App Client ID

---

## Step 4: Create Admin User

```bash
# Get User Pool ID from stack outputs
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text --region us-east-1)

# Create Cognito user
AWS_PAGER="" aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com Name=email_verified,Value=true \
  --temporary-password 'TempPassword123!' \
  --message-action SUPPRESS \
  --region us-east-1

# Set permanent password
AWS_PAGER="" aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --password 'YourSecurePassword123!' \
  --permanent \
  --region us-east-1
```

---

## Step 5: Access the Application

1. Get CloudFront URL from stack outputs
2. Open browser to the CloudFront URL
3. Login with admin credentials created above
4. Verify dashboard loads successfully

---

## Step 6: Test API Endpoints

```bash
# Health check
curl https://0enyngna6c.execute-api.us-east-1.amazonaws.com/dev/health

# List protection groups (requires auth token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://0enyngna6c.execute-api.us-east-1.amazonaws.com/dev/api/v1/protection-groups
```

---

## Step 7: Test Step Functions

```bash
# Start test execution
AWS_PAGER="" aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:777788889999:stateMachine:DRSOrchestrationStateMachine-RMk7viQfO24W \
  --input '{"recoveryPlanId":"test-plan","executionType":"DRILL"}' \
  --region us-east-1

# Check execution status
AWS_PAGER="" aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:777788889999:stateMachine:DRSOrchestrationStateMachine-RMk7viQfO24W \
  --max-results 5 \
  --region us-east-1
```

---

## Common Tasks

### View Lambda Logs
```bash
# API Handler
AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestration-data-management-handler-dev --follow --region us-east-1

# Orchestration
AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestration-orchestration-stepfunctions-dev --follow --region us-east-1
```

### Query DynamoDB Tables
```bash
# Protection Groups
AWS_PAGER="" aws dynamodb scan \
  --table-name aws-drs-orchestration-protection-groups-dev \
  --region us-east-1

# Recovery Plans
AWS_PAGER="" aws dynamodb scan \
  --table-name aws-drs-orchestration-recovery-plans-dev \
  --region us-east-1
```

### Update Lambda Code
```bash
# Build Lambda packages
make build-lambda

# Sync to S3
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Update Lambda functions
AWS_PAGER="" aws lambda update-function-code \
  --function-name aws-drs-orchestration-data-management-handler-dev \
  --s3-bucket aws-drs-orchestration-dev \
  --s3-key lambda/data-management-handler.zip \
  --region us-east-1
```

---

## Troubleshooting

### Frontend Not Loading
1. Check CloudFront distribution status from stack outputs
2. Verify S3 bucket has files from stack outputs
3. Check browser console for errors

### API Errors
1. Check Lambda logs for errors
2. Verify API Gateway deployment: `aws apigateway get-rest-api --rest-api-id 0enyngna6c`
3. Test with curl to isolate frontend vs backend issues

### Authentication Issues
1. Verify Cognito user exists: `aws cognito-idp admin-get-user --user-pool-id us-east-1_4FChZ5iDB --username admin@example.com`
2. Check user pool configuration: `aws cognito-idp describe-user-pool --user-pool-id us-east-1_4FChZ5iDB`
3. Verify frontend config.ts has correct IDs

---

## Next Steps

1. ✅ Stack deployed successfully
2. ✅ Admin user created
3. ⏳ Frontend configured and deployed
4. ⏳ Sample data populated
5. ⏳ API endpoints tested
6. ⏳ Step Functions execution tested
7. ⏳ Create protection groups
8. ⏳ Create recovery plans
9. ⏳ Execute first DR drill

---

## Additional Resources

- [Deployment Outputs](DEPLOYMENT_OUTPUTS.md) - Complete stack outputs and resource ARNs
- [Project Migration](../../PROJECT_NAME_MIGRATION.md) - ProjectName change documentation
- [Architecture Diagram](../architecture/AWS-DRS-Orchestration-Architecture.png) - System architecture
- [API Documentation](../reference/API_REFERENCE.md) - Complete API reference

---

**Last Updated**: January 17, 2026  
**Maintained By**: AWS DRS Orchestration Team
