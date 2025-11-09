# AWS DRS Orchestration - Deployment Guide

Complete deployment guide for the AWS DRS Orchestration solution using modular nested CloudFormation stacks with S3-hosted deployment.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Deployment Methods](#deployment-methods)
5. [S3-Hosted Deployment (Recommended)](#s3-hosted-deployment-recommended)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Monitoring and Validation](#monitoring-and-validation)
8. [Troubleshooting](#troubleshooting)
9. [Updating the Stack](#updating-the-stack)
10. [Cleanup](#cleanup)

---

## Overview

The AWS DRS Orchestration solution uses a **modular nested stack architecture** deployed from S3 for professional, scalable infrastructure management.

### Deployment Architecture

```
S3 Bucket (Deployment Artifacts)
├── master-template.yaml           # Root orchestrator
├── nested-stacks/                 # Nested CloudFormation templates
│   ├── database-stack.yaml        # DynamoDB tables
│   ├── lambda-stack.yaml          # Lambda functions
│   ├── api-stack.yaml             # Cognito + API Gateway
│   ├── security-stack.yaml        # WAF + CloudTrail (optional)
│   └── frontend-stack.yaml        # S3 + CloudFront
├── lambda/                        # Lambda deployment packages
│   ├── api-handler.zip
│   ├── orchestration.zip
│   ├── s3-cleanup.zip
│   └── frontend-builder.zip
└── frontend/
    └── frontend-source.zip        # React application source
```

### Stack Deployment Order

1. **DatabaseStack** (2-3 min) → DynamoDB tables
2. **LambdaStack** (3-5 min) → Lambda functions + IAM roles
3. **ApiStack** (5-7 min) → Cognito + API Gateway + Step Functions
4. **SecurityStack** (5-7 min) → WAF + CloudTrail (if enabled)
5. **FrontendStack** (5-8 min) → S3 + CloudFront + Custom Resources

**Total Time**: 20-30 minutes

---

## Architecture

### Modular Template Structure

| Template | Lines | Purpose |
|----------|-------|---------|
| **master-template.yaml** | 336 | Root orchestrator with nested stack references |
| **database-stack.yaml** | 130 | DynamoDB tables (3) with encryption & PITR |
| **lambda-stack.yaml** | 408 | Lambda functions (4) + IAM roles + CloudWatch Log Groups |
| **api-stack.yaml** | 696 | Cognito User Pool, API Gateway REST API, Step Functions |
| **security-stack.yaml** | 648 | WAF, CloudTrail, Secrets Manager (optional) |
| **frontend-stack.yaml** | 361 | S3 bucket, CloudFront distribution, Custom Resources |

### Key Benefits

✅ **All templates under 750 lines** - Better maintainability  
✅ **Single-command deployment** - Simple user experience  
✅ **Modular updates** - Update individual stacks independently  
✅ **Professional patterns** - AWS nested stack best practices  
✅ **S3-hosted** - Scalable, shareable deployment artifacts  

---

## Prerequisites

### AWS Requirements

1. **AWS Account** with appropriate permissions
2. **AWS CLI v2.x** installed and configured
3. **S3 Bucket** for deployment artifacts (or ability to create one)
4. **IAM Permissions**:
   - `cloudformation:*`
   - `lambda:*`
   - `s3:*`
   - `cloudfront:*`
   - `cognito-idp:*`
   - `apigateway:*`
   - `dynamodb:*`
   - `iam:*` (for role creation)
   - `waf:*` (if using WAF)
   - `cloudtrail:*` (if using CloudTrail)

### Local Development Tools

For packaging only (not required if using pre-built artifacts):
- **Python 3.12+** with pip
- **Node.js 18+** and npm
- **Bash shell** (macOS/Linux) or Git Bash (Windows)

### AWS Service Limits

Verify these limits in your account:
- CloudFormation stacks: 2000 per region
- Lambda functions: 1000 per region
- API Gateway REST APIs: 300 per region
- DynamoDB tables: 2500 per region

---

## Deployment Methods

### Quick Comparison

| Method | Use Case | Complexity | Time |
|--------|----------|------------|------|
| **S3-Hosted** | Production, teams, repeatable deploys | Medium | 20-30 min |
| **Local** | Development, testing, quick iterations | Low | 15-20 min |

**Recommendation**: Use **S3-Hosted Deployment** for production and team environments.

---

## S3-Hosted Deployment (Recommended)

### Step 1: Package Deployment Artifacts

```bash
cd AWS-DRS-Orchestration

# Run packaging script
./scripts/package-deployment.sh

# Output: deployment-package/ directory created
```

**What This Does**:
- Packages all 4 Lambda functions with dependencies
- Copies all 6 CloudFormation templates
- Creates frontend source archive
- Generates deployment README
- Total package size: ~15-20 MB

**Verify Package**:
```bash
ls -lh deployment-package/
# Should see:
# - master-template.yaml
# - nested-stacks/ (5 templates)
# - lambda/ (4 zip files)
# - frontend/ (frontend-source.zip)
```

### Step 2: Create S3 Bucket (If Needed)

```bash
# Create bucket with versioning enabled
aws s3 mb s3://my-drs-solution-bucket --region us-west-2

# Enable versioning (optional but recommended)
aws s3api put-bucket-versioning \
  --bucket my-drs-solution-bucket \
  --versioning-configuration Status=Enabled \
  --region us-west-2

# Block public access (security best practice)
aws s3api put-public-access-block \
  --bucket my-drs-solution-bucket \
  --public-access-block-configuration \
    BlockPublicAcls=true,\
    IgnorePublicAcls=true,\
    BlockPublicPolicy=true,\
    RestrictPublicBuckets=true \
  --region us-west-2
```

### Step 3: Upload Deployment Package

```bash
# Upload all artifacts to S3
aws s3 sync deployment-package/ s3://my-drs-solution-bucket/ \
  --exclude "README.md" \
  --region us-west-2

# Verify upload
aws s3 ls s3://my-drs-solution-bucket/ --recursive --human-readable

# Expected output:
# master-template.yaml
# nested-stacks/database-stack.yaml
# nested-stacks/lambda-stack.yaml
# nested-stacks/api-stack.yaml
# nested-stacks/security-stack.yaml
# nested-stacks/frontend-stack.yaml
# lambda/api-handler.zip
# lambda/orchestration.zip
# lambda/s3-cleanup.zip
# lambda/frontend-builder.zip
# frontend/frontend-source.zip
```

### Step 4: Deploy CloudFormation Stack

```bash
# Deploy with required parameters
aws cloudformation create-stack \
  --stack-name drs-orchestration \
  --template-url https://my-drs-solution-bucket.s3.amazonaws.com/master-template.yaml \
  --parameters \
    ParameterKey=SourceBucket,ParameterValue=my-drs-solution-bucket \
    ParameterKey=AdminEmail,ParameterValue=admin@example.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2 \
  --tags \
    Key=Environment,Value=Production \
    Key=Project,Value=DRS-Orchestration
```

**Parameter Reference**:

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `SourceBucket` | ✅ Yes | - | S3 bucket containing deployment artifacts |
| `AdminEmail` | ✅ Yes | - | Email for Cognito admin user (receives temp password) |
| `ProjectName` | No | drs-orchestration | Project identifier for resource naming |
| `Environment` | No | prod | Environment name (dev/test/prod) |
| `CognitoDomainPrefix` | No | drs-orch-{random} | Cognito domain prefix (must be globally unique) |
| `NotificationEmail` | No | - | Email for execution notifications (optional) |
| `EnableWAF` | No | false | Enable WAF for API protection |
| `EnableCloudTrail` | No | false | Enable CloudTrail for audit logging |
| `EnableSecretsManager` | No | false | Enable Secrets Manager for sensitive data |

**Example with All Optional Parameters**:
```bash
aws cloudformation create-stack \
  --stack-name drs-orchestration \
  --template-url https://my-drs-solution-bucket.s3.amazonaws.com/master-template.yaml \
  --parameters \
    ParameterKey=SourceBucket,ParameterValue=my-drs-solution-bucket \
    ParameterKey=AdminEmail,ParameterValue=admin@example.com \
    ParameterKey=ProjectName,ParameterValue=drs-orch-prod \
    ParameterKey=Environment,ParameterValue=prod \
    ParameterKey=NotificationEmail,ParameterValue=ops-team@example.com \
    ParameterKey=EnableWAF,ParameterValue=true \
    ParameterKey=EnableCloudTrail,ParameterValue=true \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2
```

### Step 5: Monitor Deployment

```bash
# Wait for stack creation (20-30 minutes)
aws cloudformation wait stack-create-complete \
  --stack-name drs-orchestration \
  --region us-west-2

# Monitor progress with events
aws cloudformation describe-stack-events \
  --stack-name drs-orchestration \
  --region us-west-2 \
  --max-items 20 \
  --output table
```

**Watch for These Milestones**:
1. ✅ DatabaseStack: CREATE_COMPLETE (~3 min)
2. ✅ LambdaStack: CREATE_COMPLETE (~5 min)
3. ✅ ApiStack: CREATE_COMPLETE (~7 min)
4. ✅ SecurityStack: CREATE_COMPLETE (~7 min, if enabled)
5. ✅ FrontendStack: CREATE_COMPLETE (~8 min)
6. ✅ Master Stack: CREATE_COMPLETE

### Step 6: Get Stack Outputs

```bash
# Get all stack outputs
aws cloudformation describe-stacks \
  --stack-name drs-orchestration \
  --region us-west-2 \
  --query 'Stacks[0].Outputs' \
  --output table

# Get specific outputs
# CloudFront URL
aws cloudformation describe-stacks \
  --stack-name drs-orchestration \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text

# API Endpoint
aws cloudformation describe-stacks \
  --stack-name drs-orchestration \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text

# Cognito User Pool ID
aws cloudformation describe-stacks \
  --stack-name drs-orchestration \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text
```

### Step 7: Access the Application

1. **Get CloudFront URL** from stack outputs
2. **Check your email** for Cognito temporary password
3. **Open CloudFront URL** in browser
4. **Login** with:
   - Username: your email address
   - Password: temporary password from email
5. **Change password** when prompted
6. **Start using the application**

---

## Post-Deployment Configuration

### Initial User Setup

The stack creates an initial admin user with the email you provided. To add more users:

```bash
# Add user via AWS CLI
aws cognito-idp admin-create-user \
  --user-pool-id <USER_POOL_ID> \
  --username newuser@example.com \
  --user-attributes \
    Name=email,Value=newuser@example.com \
    Name=email_verified,Value=true \
  --temporary-password TempPass123! \
  --message-action SUPPRESS \
  --region us-west-2
```

### Cross-Account DRS Access

To execute recovery in different AWS accounts:

1. **Create IAM role in target account**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<SOURCE_ACCOUNT>:role/drs-orchestration-orchestration-role"
      },
      "Action": "sts:AssumeRole",
      "Condition": {}
    }
  ]
}
```

2. **Attach DRS permissions policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "drs:*",
        "ec2:Describe*",
        "ec2:CreateTags"
      ],
      "Resource": "*"
    }
  ]
}
```

3. **Use role ARN in Protection Group configuration**

### CloudWatch Alarms (Optional)

Set up monitoring alarms:

```bash
# Lambda errors alarm
aws cloudwatch put-metric-alarm \
  --alarm-name drs-orch-lambda-errors \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --period 300 \
  --statistic Sum \
  --threshold 5 \
  --alarm-actions <SNS_TOPIC_ARN> \
  --dimensions Name=FunctionName,Value=drs-orchestration-api-handler

# API Gateway 5xx errors
aws cloudwatch put-metric-alarm \
  --alarm-name drs-orch-api-5xx \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --metric-name 5XXError \
  --namespace AWS/ApiGateway \
  --period 300 \
  --statistic Sum \
  --threshold 10 \
  --alarm-actions <SNS_TOPIC_ARN>
```

---

## Monitoring and Validation

### Verify Stack Health

```bash
# Check all nested stacks status
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName, `drs-orchestration`)].{Name:StackName,Status:StackStatus}' \
  --output table

# Expected: 6 stacks (master + 5 nested) all CREATE_COMPLETE
```

### Validate Components

**1. DynamoDB Tables**:
```bash
aws dynamodb list-tables \
  --query 'TableNames[?contains(@, `drs-orchestration`)]' \
  --output table

# Expected: 3 tables
# - drs-orchestration-protection-groups
# - drs-orchestration-recovery-plans  
# - drs-orchestration-execution-history
```

**2. Lambda Functions**:
```bash
aws lambda list-functions \
  --query 'Functions[?contains(FunctionName, `drs-orchestration`)].FunctionName' \
  --output table

# Expected: 4 functions
# - drs-orchestration-api-handler
# - drs-orchestration-orchestration
# - drs-orchestration-s3-cleanup
# - drs-orchestration-frontend-builder
```

**3. API Gateway**:
```bash
aws apigateway get-rest-apis \
  --query 'items[?contains(name, `drs-orchestration`)].{Name:name,ID:id}' \
  --output table
```

**4. CloudFront Distribution**:
```bash
aws cloudfront list-distributions \
  --query 'DistributionList.Items[?contains(Comment, `drs-orchestration`)].{ID:Id,DomainName:DomainName,Status:Status}' \
  --output table
```

### Test API Endpoint

```bash
# Get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name drs-orchestration \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# Test health check (no auth required)
curl $API_ENDPOINT/health

# Expected: {"status": "healthy", "timestamp": "..."}
```

### View Lambda Logs

```bash
# API Handler logs
aws logs tail /aws/lambda/drs-orchestration-api-handler --follow

# Orchestration logs
aws logs tail /aws/lambda/drs-orchestration-orchestration --follow

# Frontend Builder logs (deployment time)
aws logs tail /aws/lambda/drs-orchestration-frontend-builder --since 30m
```

---

## Troubleshooting

### Issue 1: Stack Creation Fails

**Symptom**: CloudFormation stack fails with `CREATE_FAILED` status.

**Common Causes**:
1. Insufficient IAM permissions
2. Service quotas exceeded
3. Invalid parameter values
4. S3 bucket permissions

**Solution**:
```bash
# Check stack events for error details
aws cloudformation describe-stack-events \
  --stack-name drs-orchestration \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].{Resource:LogicalResourceId,Reason:ResourceStatusReason}' \
  --output table

# Check which nested stack failed
aws cloudformation list-stacks \
  --stack-status-filter CREATE_FAILED \
  --query 'StackSummaries[?contains(StackName, `drs-orchestration`)].{Name:StackName,Status:StackStatus,Reason:StackStatusReason}' \
  --output table
```

### Issue 2: Frontend Shows Placeholder Page

**Symptom**: CloudFront URL shows "React App Not Yet Deployed" message.

**Solution**:
```bash
# Check frontend builder Lambda logs
aws logs tail /aws/lambda/drs-orchestration-frontend-builder --since 1h

# Verify frontend source in S3
aws s3 ls s3://my-drs-solution-bucket/frontend/

# Manual frontend rebuild (if needed)
aws lambda invoke \
  --function-name drs-orchestration-frontend-builder \
  --payload '{"RequestType": "Update"}' \
  response.json
```

### Issue 3: Nested Stack TemplateURL Not Found

**Symptom**: Nested stack creation fails with "TemplateURL not found" error.

**Solution**:
```bash
# Verify all nested stack templates in S3
aws s3 ls s3://my-drs-solution-bucket/nested-stacks/

# Should see all 5 templates:
# - database-stack.yaml
# - lambda-stack.yaml
# - api-stack.yaml
# - security-stack.yaml
# - frontend-stack.yaml

# Re-upload if missing
aws s3 sync deployment-package/nested-stacks/ \
  s3://my-drs-solution-bucket/nested-stacks/
```

### Issue 4: Lambda Function Fails to Start

**Symptom**: Lambda function invocation errors in CloudWatch logs.

**Solution**:
```bash
# Check Lambda configuration
aws lambda get-function-configuration \
  --function-name drs-orchestration-api-handler

# Verify Lambda code exists in S3
aws s3 ls s3://my-drs-solution-bucket/lambda/

# Check Lambda execution role permissions
aws iam get-role-policy \
  --role-name drs-orchestration-api-handler-role \
  --policy-name inline-policy
```

### Issue 5: Cognito User Pool Login Fails

**Symptom**: Cannot login with temporary password.

**Solution**:
```bash
# Verify user exists
aws cognito-idp admin-get-user \
  --user-pool-id <USER_POOL_ID> \
  --username admin@example.com

# Reset password if needed
aws cognito-idp admin-set-user-password \
  --user-pool-id <USER_POOL_ID> \
  --username admin@example.com \
  --password NewTempPass123! \
  --permanent false
```

---

## Updating the Stack

### Update Process

1. **Make changes** to templates or code
2. **Package updated artifacts**
3. **Upload to S3**
4. **Update CloudFormation stack**

### Example: Update Lambda Function Code

```bash
# 1. Make code changes to lambda/api-handler/

# 2. Re-package
cd AWS-DRS-Orchestration
./scripts/package-deployment.sh

# 3. Upload updated Lambda package
aws s3 cp deployment-package/lambda/api-handler.zip \
  s3://my-drs-solution-bucket/lambda/api-handler.zip

# 4. Update stack (triggers Lambda update)
aws cloudformation update-stack \
  --stack-name drs-orchestration \
  --use-previous-template \
  --parameters \
    ParameterKey=SourceBucket,UsePreviousValue=true \
    ParameterKey=AdminEmail,UsePreviousValue=true \
  --capabilities CAPABILITY_NAMED_IAM

# 5. Wait for completion
aws cloudformation wait stack-update-complete \
  --stack-name drs-orchestration
```

### Example: Update Frontend

```bash
# 1. Make changes to frontend/src/

# 2. Re-package
./scripts/package-deployment.sh

# 3. Upload updated frontend source
aws s3 cp deployment-package/frontend/frontend-source.zip \
  s3://my-drs-solution-bucket/frontend/frontend-source.zip

# 4. Update stack (triggers frontend rebuild)
aws cloudformation update-stack \
  --stack-name drs-orchestration \
  --use-previous-template \
  --parameters \
    ParameterKey=SourceBucket,UsePreviousValue=true \
    ParameterKey=AdminEmail,UsePreviousValue=true \
  --capabilities CAPABILITY_NAMED_IAM
```

### Example: Add Optional Security Stack

```bash
# Update stack with security features enabled
aws cloudformation update-stack \
  --stack-name drs-orchestration \
  --use-previous-template \
  --parameters \
    ParameterKey=SourceBucket,UsePreviousValue=true \
    ParameterKey=AdminEmail,UsePreviousValue=true \
    ParameterKey=EnableWAF,ParameterValue=true \
    ParameterKey=EnableCloudTrail,ParameterValue=true \
  --capabilities CAPABILITY_NAMED_IAM
```

---

## Cleanup

### Delete Stack

```bash
# Delete CloudFormation stack
aws cloudformation delete-stack \
  --stack-name drs-orchestration \
  --region us-west-2

# Monitor deletion
aws cloudformation wait stack-delete-complete \
  --stack-name drs-orchestration \
  --region us-west-2
```

**Note**: The S3 cleanup Custom Resource automatically empties the frontend S3 bucket before deletion.

### Clean Up S3 Deployment Bucket

```bash
# Delete deployment artifacts (optional)
aws s3 rm s3://my-drs-solution-bucket/ --recursive

# Delete bucket
aws s3 rb s3://my-drs-solution-bucket
```

### Manual Cleanup (If Needed)

If stack deletion fails:

```bash
# Empty frontend S3 bucket manually
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name drs-orchestration \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
  --output text)

aws s3 rm s3://$BUCKET/ --recursive

# Retry deletion
aws cloudformation delete-stack \
  --stack-name drs-orchestration
```

---

## Summary

### Deployment Checklist

- [ ] Prerequisites verified (AWS CLI, S3 bucket, IAM permissions)
- [ ] Deployment package created with `package-deployment.sh`
- [ ] Artifacts uploaded to S3 bucket
- [ ] CloudFormation stack created with required parameters
- [ ] Stack creation completed successfully (20-30 minutes)
- [ ] Stack outputs retrieved (CloudFront URL, API endpoint)
- [ ] Application accessed via CloudFront URL
- [ ] Initial login completed with Cognito temporary password
- [ ] Password changed from temporary to permanent

### Quick Reference Commands

```bash
# Package
./scripts/package-deployment.sh

# Upload
aws s3 sync deployment-package/ s3://BUCKET/ --exclude "README.md"

# Deploy
aws cloudformation create-stack \
  --stack-name drs-orchestration \
  --template-url https://BUCKET.s3.amazonaws.com/master-template.yaml \
  --parameters \
    ParameterKey=SourceBucket,ParameterValue=BUCKET \
    ParameterKey=AdminEmail,ParameterValue=EMAIL \
  --capabilities CAPABILITY_NAMED_IAM

# Monitor
aws cloudformation wait stack-create-complete --stack-name drs-orchestration

# Get URL
aws cloudformation describe-stacks --stack-name drs-orchestration \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text
```

---

**Last Updated**: November 8, 2025  
**Version**: 3.0.0 (Modular Nested Stack Architecture)

For architecture details, see [MODULAR_ARCHITECTURE_COMPLETED.md](MODULAR_ARCHITECTURE_COMPLETED.md)
