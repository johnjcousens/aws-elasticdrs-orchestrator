# Lambda Deployment Guide

## Overview

This guide explains how to deploy Lambda functions for the AWS DRS Orchestration solution. The solution includes a new automated deployment script that supports multiple deployment strategies.

## Lambda Functions

The solution includes three Lambda functions:

1. **API Handler** (`drs-orchestration-api-handler-{env}`)
   - Main API Gateway backend
   - File: `lambda/index.py`
   - Package: `lambda/api-handler.zip`

2. **Orchestration** (`drs-orchestration-orchestration-{env}`)
   - Step Functions orchestrator for DRS recovery execution
   - File: `lambda/drs_orchestrator.py` (future)
   - Package: `lambda/orchestration.zip`

3. **Frontend Builder** (`drs-orchestration-frontend-builder-{env}`)
   - Custom resource for frontend deployment
   - File: `lambda/build_and_deploy.py`
   - Package: `lambda/frontend-builder.zip`

## Deployment Script

### Location
```bash
lambda/deploy_lambda.py
```

### Deployment Modes

#### 1. Direct Deployment (Fastest - Development)
Updates Lambda function directly, bypassing CloudFormation.

```bash
cd lambda
python3 deploy_lambda.py --direct \
  --function-name drs-orchestration-api-handler-test \
  --region us-east-1
```

**Use when:**
- Testing code changes quickly
- Debugging in development environment
- Need immediate deployment

**Pros:** Instant deployment (~10 seconds)
**Cons:** Not tracked by CloudFormation

#### 2. S3 Upload Only (CloudFormation Preparation)
Uploads Lambda package to S3 for CloudFormation deployment.

```bash
cd lambda
python3 deploy_lambda.py --s3-only \
  --bucket aws-drs-orchestration \
  --region us-east-1
```

**Use when:**
- Preparing for CloudFormation deployment
- Want to version Lambda code in S3
- CI/CD pipeline integration

**Pros:** Makes code available for CloudFormation
**Cons:** Doesn't actually deploy to Lambda

#### 3. CloudFormation Update (Production Standard)
Triggers CloudFormation stack update to deploy Lambda from S3.

```bash
cd lambda
python3 deploy_lambda.py --cfn \
  --bucket aws-drs-orchestration \
  --stack-name drs-orchestration-test \
  --region us-east-1
```

**Use when:**
- Production deployments
- Need CloudFormation change tracking
- Want rollback capability

**Pros:** Fully tracked, rollback support
**Cons:** Slower (~2-5 minutes)

#### 4. Full Deployment (S3 + Direct)
Uploads to S3 AND updates Lambda directly.

```bash
cd lambda
python3 deploy_lambda.py --full \
  --bucket aws-drs-orchestration \
  --function-name drs-orchestration-api-handler-test \
  --region us-east-1
```

**Use when:**
- Want both S3 backup and immediate deployment
- Preparing for eventual CloudFormation sync
- Development with S3 versioning

**Pros:** Best of both worlds
**Cons:** Takes slightly longer

## Environment-Specific Deployments

### Test Environment
```bash
cd lambda
python3 deploy_lambda.py --full \
  --bucket aws-drs-orchestration \
  --function-name drs-orchestration-api-handler-test \
  --region us-east-1
```

### Production Environment
```bash
cd lambda
python3 deploy_lambda.py --cfn \
  --bucket aws-drs-orchestration \
  --stack-name drs-orchestration-prod \
  --region us-east-1
```

## Package Structure

### What Gets Packaged

The deployment script creates a zip file containing:

1. **Handler file**: `index.py` (renamed from source)
2. **Dependencies**: All files from `lambda/package/` directory
3. **Exclusions**: `__pycache__`, `*.pyc` files automatically excluded

### Dependencies

Python dependencies are pre-installed in `lambda/package/`:
- boto3 (included in Lambda runtime)
- Additional packages as needed

To add dependencies:
```bash
cd lambda
pip install -t package/ <package-name>
```

## CloudFormation Integration

### Stack Configuration

The Lambda stack (`cfn/lambda-stack.yaml`) is configured to:

1. **Expect Lambda packages in S3**:
   ```yaml
   Code:
     S3Bucket: !Ref SourceBucket
     S3Key: 'lambda/api-handler.zip'
   ```

2. **Environment variables** properly configured:
   ```yaml
   Environment:
     Variables:
       PROTECTION_GROUPS_TABLE: !Ref ProtectionGroupsTableName
       RECOVERY_PLANS_TABLE: !Ref RecoveryPlansTableName
       EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTableName
   ```

### Full Stack Deployment

For complete reproducibility from S3:

```bash
# 1. Upload Lambda packages to S3
cd lambda
python3 deploy_lambda.py --s3-only --bucket aws-drs-orchestration

# 2. Upload CloudFormation templates to S3
./scripts/sync-to-deployment-bucket.sh

# 3. Deploy/Update CloudFormation stack
aws cloudformation update-stack \
  --stack-name drs-orchestration-test \
  --template-url https://s3.amazonaws.com/aws-drs-orchestration/cfn/master-template.yaml \
  --parameters file://deployment-params.json \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

## Troubleshooting

### Issue: "Code hasn't changed"
**Symptom:** CloudFormation says no updates needed
**Solution:** Use `--direct` mode or manually update Lambda code SHA

### Issue: "Package too large"
**Symptom:** Zip file exceeds Lambda limits (50MB compressed, 250MB uncompressed)
**Solution:** 
- Use Lambda layers for large dependencies
- Optimize package size by removing unnecessary files

### Issue: "Environment variables not set"
**Symptom:** Lambda throws KeyError for DynamoDB table names
**Solution:** Ensure CloudFormation parameters are passed correctly:
```bash
aws lambda update-function-configuration \
  --function-name drs-orchestration-api-handler-test \
  --environment "Variables={
    RECOVERY_PLANS_TABLE=drs-orchestration-recovery-plans-test,
    PROTECTION_GROUPS_TABLE=drs-orchestration-protection-groups-test,
    EXECUTION_HISTORY_TABLE=drs-orchestration-execution-history-test
  }"
```

### Issue: "Import errors in Lambda"
**Symptom:** Lambda fails with ImportError
**Solution:**
1. Verify dependencies in `lambda/package/`
2. Check Python version compatibility (Lambda uses Python 3.12)
3. Ensure package structure is correct (no nested package/ directories)

## Best Practices

### Development Workflow
1. **Make code changes** to `lambda/index.py`
2. **Test locally** if possible
3. **Deploy directly** for quick testing:
   ```bash
   python3 deploy_lambda.py --direct --function-name drs-orchestration-api-handler-test
   ```
4. **Verify** with API calls or Lambda console test
5. **Upload to S3** when ready for production:
   ```bash
   python3 deploy_lambda.py --s3-only --bucket aws-drs-orchestration
   ```
6. **Commit changes** to git
7. **Update CloudFormation** for production deployment

### Production Workflow
1. **All changes via CloudFormation**
2. **Lambda packages in S3** before stack updates
3. **Test in non-prod** environment first
4. **Use CloudFormation change sets** for review
5. **Monitor CloudWatch logs** after deployment

### CI/CD Integration
```bash
# Example CI/CD pipeline step
cd lambda

# Package and upload to S3
python3 deploy_lambda.py --s3-only \
  --bucket aws-drs-orchestration \
  --region us-east-1

# Trigger CloudFormation stack update
aws cloudformation update-stack \
  --stack-name drs-orchestration-${ENVIRONMENT} \
  --template-url https://s3.amazonaws.com/aws-drs-orchestration/cfn/master-template.yaml \
  --parameters file://deployment-params-${ENVIRONMENT}.json \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

## Verification

### After Deployment

1. **Check Lambda version**:
   ```bash
   aws lambda get-function-configuration \
     --function-name drs-orchestration-api-handler-test \
     --query '{LastModified:LastModified,CodeSize:CodeSize,Runtime:Runtime}' \
     --region us-east-1
   ```

2. **Verify environment variables**:
   ```bash
   aws lambda get-function-configuration \
     --function-name drs-orchestration-api-handler-test \
     --query 'Environment.Variables' \
     --region us-east-1
   ```

3. **Test API endpoint**:
   ```bash
   curl -X GET \
     "https://<api-id>.execute-api.us-east-1.amazonaws.com/test/recovery-plans" \
     -H "Authorization: Bearer <token>"
   ```

4. **Check CloudWatch logs**:
   ```bash
   aws logs tail /aws/lambda/drs-orchestration-api-handler-test \
     --since 5m \
     --region us-east-1
   ```

## Related Documentation

- [Deployment and Operations Guide](./guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md)
- [CloudFormation Templates](../cfn/)
- [Testing Guide](./guides/TESTING_AND_QUALITY_ASSURANCE.md)
