# Deployment Guide

**Comprehensive guide for deploying and operating AWS DRS Orchestration.**

---

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Prerequisites](#prerequisites)
3. [Fresh Deployment](#fresh-deployment)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Manual Deployment](#manual-deployment)
6. [Stack Management](#stack-management)
7. [Monitoring and Operations](#monitoring-and-operations)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)

---

## Deployment Overview

AWS DRS Orchestration uses a serverless architecture deployed via CloudFormation Infrastructure as Code (IaC). The system supports multiple deployment methods:

- **GitHub Actions CI/CD** (MANDATORY for regular deployments)
- **Manual deployment scripts** (emergency use only)
- **Fresh deployment** (new environment setup)

### Architecture Components

- **Frontend**: React + CloudScape UI hosted on S3 + CloudFront
- **Backend**: 7 Lambda functions + API Gateway + Step Functions
- **Database**: 4 DynamoDB tables
- **Authentication**: Cognito User Pool + Identity Pool
- **Infrastructure**: 15+ CloudFormation nested stacks

---

## Prerequisites

### AWS Account Requirements

- AWS Account with administrative access
- AWS CLI configured with credentials
- Sufficient service quotas for:
  - Lambda functions (7 required)
  - DynamoDB tables (4 required)
  - CloudFormation stacks (15+ nested stacks)
  - API Gateway resources (400+ resources)

### Required Tools

- **AWS CLI** v2.x or later
- **Node.js** 18.x or later (for frontend build)
- **Python** 3.12 (for Lambda functions)
- **Git** (for repository access)

### S3 Deployment Bucket

Create an S3 bucket for deployment artifacts:

```bash
aws s3 mb s3://{deployment-bucket-name} --region {region}
```

This bucket stores:
- CloudFormation templates
- Lambda deployment packages
- Frontend build artifacts

---

## Fresh Deployment

### Step 1: Clone Repository

```bash
git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git
cd aws-elasticdrs-orchestrator
```

### Step 2: Configure Deployment

Create deployment configuration file:

```bash
cp .env.deployment.template .env.deployment.fresh
```

Edit `.env.deployment.fresh` with your values:

```bash
# AWS Configuration
AWS_REGION={region}
AWS_ACCOUNT_ID={account-id}

# Stack Configuration
PROJECT_NAME=aws-elasticdrs-orchestrator
ENVIRONMENT={environment}
ADMIN_EMAIL={admin-email}

# Deployment Bucket
DEPLOYMENT_BUCKET={deployment-bucket-name}
```

### Step 3: Validate Configuration

```bash
# Load configuration
source .env.deployment.fresh

# Validate deployment configuration
./scripts/validate-deployment-config.sh
```

### Step 4: Sync Artifacts to S3

```bash
# Sync all deployment artifacts to S3
./scripts/sync-to-deployment-bucket.sh

# Verify artifacts uploaded
aws s3 ls s3://${DEPLOYMENT_BUCKET}/cfn/
aws s3 ls s3://${DEPLOYMENT_BUCKET}/lambda/
```

### Step 5: Deploy Master Stack

```bash
# Deploy via CloudFormation
aws cloudformation create-stack \
  --stack-name ${PROJECT_NAME}-${ENVIRONMENT} \
  --template-url https://s3.amazonaws.com/${DEPLOYMENT_BUCKET}/cfn/master-template.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=${PROJECT_NAME} \
    ParameterKey=Environment,ParameterValue=${ENVIRONMENT} \
    ParameterKey=AdminEmail,ParameterValue=${ADMIN_EMAIL} \
    ParameterKey=DeploymentBucket,ParameterValue=${DEPLOYMENT_BUCKET} \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ${AWS_REGION}

# Monitor deployment progress
aws cloudformation wait stack-create-complete \
  --stack-name ${PROJECT_NAME}-${ENVIRONMENT} \
  --region ${AWS_REGION}
```

### Step 6: Retrieve Stack Outputs

```bash
# Get API Gateway URL
aws cloudformation describe-stacks \
  --stack-name ${PROJECT_NAME}-${ENVIRONMENT} \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text

# Get Frontend URL
aws cloudformation describe-stacks \
  --stack-name ${PROJECT_NAME}-${ENVIRONMENT} \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendUrl`].OutputValue' \
  --output text
```

### Step 7: Create Test User

```bash
# Get Cognito User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name ${PROJECT_NAME}-${ENVIRONMENT} \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Create admin user
aws cognito-idp admin-create-user \
  --user-pool-id ${USER_POOL_ID} \
  --username {test-username} \
  --user-attributes Name=email,Value={test-email} \
  --temporary-password {temporary-password} \
  --message-action SUPPRESS

# Add user to admin group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id ${USER_POOL_ID} \
  --username {test-username} \
  --group-name DRSOrchestrationAdmin
```

### Step 8: Verify Deployment

```bash
# Test API endpoint
curl -X GET https://{api-id}.execute-api.{region}.amazonaws.com/{environment}/health

# Access frontend
open https://{distribution-id}.cloudfront.net
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

**MANDATORY**: All regular deployments MUST use GitHub Actions CI/CD pipeline.

#### Workflow Configuration

Location: `.github/workflows/deploy.yml`

**Workflow Stages**:
1. **Detect Changes** (~10s) - Analyzes changed files
2. **Validate** (~2 min) - CloudFormation, Python, TypeScript validation
3. **Security Scan** (~2 min) - Bandit, Safety checks
4. **Build** (~3 min) - Lambda packages, frontend build
5. **Test** (~2 min) - Unit tests
6. **Deploy Infrastructure** (~10 min) - CloudFormation deployment
7. **Deploy Frontend** (~2 min) - S3 sync, CloudFront invalidation

#### Intelligent Optimization

Pipeline automatically skips unnecessary stages:

- **Documentation-only changes**: ~30 seconds (95% time savings)
- **Frontend-only changes**: ~12 minutes (45% time savings)
- **Full deployment**: ~22 minutes (complete pipeline)

#### Concurrency Control

Workflow includes automatic concurrency control:

```yaml
concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: false
```

**Behavior**:
- Creates concurrency group per branch
- Queues new runs instead of canceling
- Workflows run sequentially, never overlapping
- Prevents deployment conflicts automatically

#### Triggering Deployment

```bash
# Standard workflow
git add .
git commit -m "feat: description of changes"
git push

# Safe push with workflow check (recommended)
./scripts/safe-push.sh

# Check deployment scope before pushing
./scripts/check-deployment-scope.sh
```

#### Monitoring Deployment

1. Navigate to GitHub Actions tab
2. Select running workflow
3. Monitor stage progress
4. Review deployment logs
5. Verify stack outputs

---

## Manual Deployment

**WARNING**: Manual deployment scripts are for EMERGENCY USE ONLY. Always use GitHub Actions CI/CD for regular deployments.

### When Manual Deployment is Allowed

- CI/CD service outage (confirmed service issue)
- Critical production hotfix when pipeline is broken
- Pipeline debugging (with immediate revert to Git-based deployment)

### Emergency Deployment Procedure

```bash
# 1. Document the emergency situation
echo "Emergency: [describe situation]" >> emergency-deployment.log

# 2. Deploy critical fix
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# 3. IMMEDIATELY commit changes to Git
git add .
git commit -m "emergency: describe the critical fix"

# 4. Push to restore proper CI/CD tracking
./scripts/safe-push.sh

# 5. Report emergency to team
```

### Sync to Deployment Bucket

```bash
# Full sync (all artifacts)
./scripts/sync-to-deployment-bucket.sh

# Lambda code only (fast update)
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Frontend only
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend

# Dry run (preview changes)
./scripts/sync-to-deployment-bucket.sh --dry-run
```

### Direct Stack Updates

```bash
# Update specific nested stack
aws cloudformation update-stack \
  --stack-name ${PROJECT_NAME}-lambda-${ENVIRONMENT} \
  --template-url https://s3.amazonaws.com/${DEPLOYMENT_BUCKET}/cfn/lambda-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# Update master stack
aws cloudformation update-stack \
  --stack-name ${PROJECT_NAME}-${ENVIRONMENT} \
  --template-url https://s3.amazonaws.com/${DEPLOYMENT_BUCKET}/cfn/master-template.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

---

## Stack Management

### Stack Architecture

**Master Stack**: `{project-name}-{environment}`
- Orchestrates 15+ nested stacks
- Manages stack dependencies
- Provides consolidated outputs

**Nested Stacks**:
- Security Stack (IAM roles, policies)
- Database Stack (4 DynamoDB tables)
- Lambda Stack (7 Lambda functions)
- API Gateway Stacks (5 stacks: core, resources, methods)
- Step Functions Stack (orchestration state machine)
- Frontend Stack (S3, CloudFront)
- EventBridge Stack (scheduled polling)
- Notification Stack (SNS topics)

### Viewing Stack Status

```bash
# List all stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName, `{project-name}`)].{Name:StackName,Status:StackStatus}' \
  --output table

# View specific stack details
aws cloudformation describe-stacks \
  --stack-name {project-name}-{environment}

# View stack events
aws cloudformation describe-stack-events \
  --stack-name {project-name}-{environment} \
  --max-items 20
```

### Stack Outputs

Key outputs from master stack:

- **ApiGatewayUrl**: REST API endpoint
- **FrontendUrl**: CloudFront distribution URL
- **UserPoolId**: Cognito User Pool ID
- **UserPoolClientId**: Cognito Client ID
- **StateMachineArn**: Step Functions ARN
- **ProtectionGroupsTable**: DynamoDB table name
- **RecoveryPlansTable**: DynamoDB table name
- **ExecutionHistoryTable**: DynamoDB table name

### Stack Updates

```bash
# Update via GitHub Actions (RECOMMENDED)
git push

# Manual update (emergency only)
./scripts/sync-to-deployment-bucket.sh
aws cloudformation update-stack \
  --stack-name {project-name}-{environment} \
  --template-url https://s3.amazonaws.com/{deployment-bucket}/cfn/master-template.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

### Stack Deletion

```bash
# Delete master stack (cascades to nested stacks)
aws cloudformation delete-stack \
  --stack-name {project-name}-{environment}

# Monitor deletion
aws cloudformation wait stack-delete-complete \
  --stack-name {project-name}-{environment}

# Clean up S3 buckets (must be done manually)
aws s3 rm s3://{frontend-bucket} --recursive
aws s3 rb s3://{frontend-bucket}
```

---

## Monitoring and Operations

### CloudWatch Logs

**Lambda Function Logs**:

```bash
# View recent logs
aws logs tail /aws/lambda/{project-name}-api-handler-{environment} --since 5m

# Search logs for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/{project-name}-api-handler-{environment} \
  --filter-pattern "ERROR"

# View execution poller logs
aws logs tail /aws/lambda/{project-name}-execution-poller-{environment} --since 10m
```

**Step Functions Logs**:

```bash
# View state machine executions
aws stepfunctions list-executions \
  --state-machine-arn {state-machine-arn} \
  --max-results 10

# View execution details
aws stepfunctions describe-execution \
  --execution-arn {execution-arn}
```

### CloudWatch Metrics

**Key Metrics to Monitor**:

- Lambda invocations, errors, duration
- API Gateway 4xx/5xx errors, latency
- DynamoDB read/write capacity, throttles
- Step Functions execution success/failure rate

```bash
# View Lambda errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value={project-name}-api-handler-{environment} \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### CloudWatch Alarms

**Recommended Alarms**:

```bash
# Lambda error alarm
aws cloudwatch put-metric-alarm \
  --alarm-name {project-name}-lambda-errors-{environment} \
  --alarm-description "Lambda function errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value={project-name}-api-handler-{environment}

# API Gateway 5xx errors
aws cloudwatch put-metric-alarm \
  --alarm-name {project-name}-api-5xx-{environment} \
  --alarm-description "API Gateway 5xx errors" \
  --metric-name 5XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

### DynamoDB Operations

**Table Management**:

```bash
# View table details
aws dynamodb describe-table \
  --table-name {project-name}-protection-groups-{environment}

# Scan table (development only)
aws dynamodb scan \
  --table-name {project-name}-protection-groups-{environment} \
  --max-items 10

# Query by primary key
aws dynamodb get-item \
  --table-name {project-name}-protection-groups-{environment} \
  --key '{"groupId": {"S": "pg-12345"}}'
```

### API Gateway Operations

**Testing Endpoints**:

```bash
# Get JWT token
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id {pool-id} \
  --client-id {client-id} \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME={username},PASSWORD={password} \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Test API endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://{api-id}.execute-api.{region}.amazonaws.com/{environment}/protection-groups
```

**Deployment Management**:

```bash
# Create new deployment
aws apigateway create-deployment \
  --rest-api-id {api-id} \
  --stage-name {environment}

# View deployment history
aws apigateway get-deployments \
  --rest-api-id {api-id}

# View stage configuration
aws apigateway get-stage \
  --rest-api-id {api-id} \
  --stage-name {environment}
```

### Frontend Operations

**CloudFront Management**:

```bash
# Create cache invalidation
aws cloudfront create-invalidation \
  --distribution-id {distribution-id} \
  --paths "/*"

# View invalidation status
aws cloudfront get-invalidation \
  --distribution-id {distribution-id} \
  --id {invalidation-id}

# View distribution configuration
aws cloudfront get-distribution \
  --id {distribution-id}
```

**S3 Bucket Management**:

```bash
# Sync frontend build
aws s3 sync frontend/dist/ s3://{frontend-bucket}/ \
  --delete \
  --cache-control "public, max-age=31536000, immutable"

# View bucket contents
aws s3 ls s3://{frontend-bucket}/ --recursive

# Check bucket size
aws s3 ls s3://{frontend-bucket}/ --recursive --summarize
```

---

## Troubleshooting

### Common Deployment Issues

**Stack Creation Failures**:

```bash
# View failed stack events
aws cloudformation describe-stack-events \
  --stack-name {project-name}-{environment} \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'

# Common causes:
# - Insufficient IAM permissions
# - Resource limits exceeded
# - Invalid parameter values
# - Dependency conflicts
```

**Lambda Function Errors**:

```bash
# Check function configuration
aws lambda get-function \
  --function-name {project-name}-api-handler-{environment}

# View recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/{project-name}-api-handler-{environment} \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000

# Common causes:
# - Missing environment variables
# - IAM permission issues
# - Timeout errors (increase timeout)
# - Memory errors (increase memory)
```

**API Gateway Issues**:

```bash
# Test API Gateway integration
aws apigateway test-invoke-method \
  --rest-api-id {api-id} \
  --resource-id {resource-id} \
  --http-method GET \
  --path-with-query-string "/protection-groups"

# Common causes:
# - CORS configuration errors
# - Lambda integration misconfiguration
# - Cognito authorizer issues
# - Request/response mapping errors
```

**DynamoDB Issues**:

```bash
# Check table status
aws dynamodb describe-table \
  --table-name {project-name}-protection-groups-{environment} \
  --query 'Table.TableStatus'

# View throttled requests
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name UserErrors \
  --dimensions Name=TableName,Value={project-name}-protection-groups-{environment} \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Common causes:
# - Throttling (increase capacity or use on-demand)
# - Invalid key schema
# - Item size exceeds 400KB
```

**Frontend Issues**:

```bash
# Check CloudFront distribution status
aws cloudfront get-distribution \
  --id {distribution-id} \
  --query 'Distribution.Status'

# View CloudFront errors
aws cloudfront get-distribution-config \
  --id {distribution-id} \
  --query 'DistributionConfig.CustomErrorResponses'

# Common causes:
# - S3 bucket permissions
# - CloudFront cache issues (create invalidation)
# - Origin access identity misconfiguration
# - SSL/TLS certificate issues
```

**Authentication Issues**:

```bash
# Verify user exists
aws cognito-idp admin-get-user \
  --user-pool-id {pool-id} \
  --username {username}

# Check user group membership
aws cognito-idp admin-list-groups-for-user \
  --user-pool-id {pool-id} \
  --username {username}

# Reset user password
aws cognito-idp admin-set-user-password \
  --user-pool-id {pool-id} \
  --username {username} \
  --password {new-password} \
  --permanent

# Common causes:
# - User not in correct group
# - Expired JWT token
# - Incorrect client ID configuration
# - CORS issues with Cognito
```

### Rollback Procedures

**Stack Rollback**:

```bash
# CloudFormation automatic rollback on failure
# No action needed - stack rolls back automatically

# Manual rollback to previous version
aws cloudformation update-stack \
  --stack-name {project-name}-{environment} \
  --template-url https://s3.amazonaws.com/{deployment-bucket}/cfn/master-template.yaml \
  --use-previous-template \
  --capabilities CAPABILITY_NAMED_IAM
```

**Lambda Rollback**:

```bash
# List function versions
aws lambda list-versions-by-function \
  --function-name {project-name}-api-handler-{environment}

# Rollback to previous version
aws lambda update-alias \
  --function-name {project-name}-api-handler-{environment} \
  --name live \
  --function-version {previous-version}
```

**Frontend Rollback**:

```bash
# Restore previous S3 version
aws s3api list-object-versions \
  --bucket {frontend-bucket} \
  --prefix index.html

# Copy previous version
aws s3api copy-object \
  --bucket {frontend-bucket} \
  --copy-source {frontend-bucket}/index.html?versionId={version-id} \
  --key index.html

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id {distribution-id} \
  --paths "/*"
```

---

## Maintenance

### Regular Maintenance Tasks

**Weekly**:
- Review CloudWatch logs for errors
- Check Lambda function performance metrics
- Monitor DynamoDB capacity usage
- Review API Gateway request patterns

**Monthly**:
- Update Lambda runtime versions
- Review and optimize Lambda memory allocation
- Analyze CloudWatch costs
- Review IAM permissions for least privilege
- Update dependencies (npm, pip packages)

**Quarterly**:
- Review and update CloudFormation templates
- Conduct security audit
- Review disaster recovery procedures
- Update documentation

### Backup Procedures

**DynamoDB Backups**:

```bash
# Create on-demand backup
aws dynamodb create-backup \
  --table-name {project-name}-protection-groups-{environment} \
  --backup-name {project-name}-protection-groups-backup-$(date +%Y%m%d)

# Enable point-in-time recovery
aws dynamodb update-continuous-backups \
  --table-name {project-name}-protection-groups-{environment} \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# List backups
aws dynamodb list-backups \
  --table-name {project-name}-protection-groups-{environment}
```

**CloudFormation Template Backups**:

```bash
# Export current stack template
aws cloudformation get-template \
  --stack-name {project-name}-{environment} \
  --query 'TemplateBody' \
  > backup-template-$(date +%Y%m%d).yaml

# Store in version control (Git)
git add cfn/
git commit -m "backup: CloudFormation templates $(date +%Y-%m-%d)"
git push
```

**Lambda Function Backups**:

```bash
# Download function code
aws lambda get-function \
  --function-name {project-name}-api-handler-{environment} \
  --query 'Code.Location' \
  --output text | xargs wget -O lambda-backup-$(date +%Y%m%d).zip

# Store in S3
aws s3 cp lambda-backup-$(date +%Y%m%d).zip \
  s3://{deployment-bucket}/backups/
```

### Cost Optimization

**Monitor Costs**:

```bash
# View cost by service
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

**Optimization Strategies**:

- **Lambda**: Right-size memory allocation, reduce cold starts
- **DynamoDB**: Use on-demand billing for variable workloads
- **API Gateway**: Enable caching for frequently accessed endpoints
- **CloudFront**: Optimize cache TTL settings
- **S3**: Use lifecycle policies for old deployment artifacts

### Security Maintenance

**IAM Review**:

```bash
# List IAM roles
aws iam list-roles \
  --query 'Roles[?contains(RoleName, `{project-name}`)].RoleName'

# Review role permissions
aws iam get-role-policy \
  --role-name {project-name}-lambda-execution-role-{environment} \
  --policy-name {policy-name}

# Check for unused roles
aws iam generate-credential-report
aws iam get-credential-report
```

**Security Scanning**:

```bash
# Run security scan (local)
cd /path/to/project
bandit -r lambda/ scripts/ -ll
safety check
semgrep --config=python.lang.security lambda/ scripts/

# Review CloudFormation security
cfn-lint cfn/*.yaml
```

**Certificate Management**:

```bash
# List ACM certificates
aws acm list-certificates \
  --certificate-statuses ISSUED

# Check certificate expiration
aws acm describe-certificate \
  --certificate-arn {certificate-arn} \
  --query 'Certificate.NotAfter'
```

### Performance Tuning

**Lambda Optimization**:

```bash
# Analyze Lambda performance
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value={project-name}-api-handler-{environment} \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average,Maximum
```

**DynamoDB Optimization**:

```bash
# Analyze table metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value={project-name}-protection-groups-{environment} \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average,Maximum

# Consider switching to on-demand if usage is variable
aws dynamodb update-table \
  --table-name {project-name}-protection-groups-{environment} \
  --billing-mode PAY_PER_REQUEST
```

**API Gateway Optimization**:

```bash
# Enable caching
aws apigateway update-stage \
  --rest-api-id {api-id} \
  --stage-name {environment} \
  --patch-operations \
    op=replace,path=/cacheClusterEnabled,value=true \
    op=replace,path=/cacheClusterSize,value=0.5

# Monitor cache performance
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name CacheHitCount \
  --dimensions Name=ApiName,Value={project-name}-api-{environment} \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

---

## Additional Resources

### Documentation
- [API and Integration Guide](API_AND_INTEGRATION_GUIDE.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)
- [Architecture Documentation](../architecture/ARCHITECTURE.md)

### AWS Documentation
- [CloudFormation Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [API Gateway Best Practices](https://docs.aws.amazon.com/apigateway/latest/developerguide/best-practices.html)

### Support
- GitHub Issues: https://github.com/johnjcousens/aws-elasticdrs-orchestrator/issues
- AWS Support: https://console.aws.amazon.com/support/
