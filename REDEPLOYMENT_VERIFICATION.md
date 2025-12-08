# Redeployment Verification

**Status**: ✅ **READY TO REDEPLOY**

## Current State

Your deployment can be fully reproduced from:
1. **S3 Bucket**: `s3://aws-drs-orchestration`
2. **Git Repository**: Current local code

## What's in S3 (Ready to Deploy)

### CloudFormation Templates (7 files)
```
✅ master-template.yaml
✅ database-stack.yaml
✅ lambda-stack.yaml
✅ api-stack.yaml
✅ step-functions-stack.yaml
✅ frontend-stack.yaml
✅ security-stack.yaml
```

### Lambda Packages (8 files)
```
✅ api-handler.zip (36KB)
✅ orchestration.zip (11KB)
✅ orchestration-stepfunctions.zip (5KB)
✅ execution-finder.zip (3KB)
✅ execution-poller.zip (5KB)
✅ frontend-builder.zip (12MB)
✅ deployment-package.zip (172KB)
✅ lambda-package.zip (98KB)
```

## Redeploy from Scratch

If everything is deleted, run this single command:

```bash
aws cloudformation create-stack \
  --stack-name drs-orchestration-dev \
  --template-url https://s3.amazonaws.com/aws-drs-orchestration/cfn/master-template.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=drs-orchestration \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=SourceBucket,ParameterValue=aws-drs-orchestration \
    ParameterKey=AdminEmail,ParameterValue=admin@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1 \
  --profile ***REMOVED***_AdministratorAccess
```

**Time**: ~20-30 minutes

## What Gets Created

This single command creates:
- ✅ 5 nested CloudFormation stacks
- ✅ 6 Lambda functions
- ✅ 2 Step Functions state machines
- ✅ 3 DynamoDB tables
- ✅ API Gateway + Cognito
- ✅ S3 frontend bucket + CloudFront
- ✅ All IAM roles and permissions

## Verify Before Redeploying

```bash
# 1. Check S3 bucket exists and has content
aws s3 ls s3://aws-drs-orchestration/cfn/ \
  --profile ***REMOVED***_AdministratorAccess --region us-east-1

# 2. Check Lambda packages exist
aws s3 ls s3://aws-drs-orchestration/lambda/ \
  --profile ***REMOVED***_AdministratorAccess --region us-east-1

# 3. Validate master template
aws cloudformation validate-template \
  --template-url https://s3.amazonaws.com/aws-drs-orchestration/cfn/master-template.yaml \
  --profile ***REMOVED***_AdministratorAccess --region us-east-1
```

## Keep S3 Bucket Safe

**CRITICAL**: The `aws-drs-orchestration` S3 bucket contains everything needed to redeploy.

**Protect it**:
```bash
# Enable versioning (if not already)
aws s3api put-bucket-versioning \
  --bucket aws-drs-orchestration \
  --versioning-configuration Status=Enabled \
  --region us-east-1

# Add lifecycle policy to keep old versions
# (Optional but recommended)
```

## Sync Local Changes to S3

Anytime you update code locally:

```bash
# Sync everything to S3
./scripts/sync-to-deployment-bucket.sh

# Or deploy specific components
./scripts/sync-to-deployment-bucket.sh --update-lambda-code
./scripts/sync-to-deployment-bucket.sh --deploy-frontend
```

## Summary

✅ **You CAN redeploy from scratch**
- All templates in S3
- All Lambda packages in S3
- Single command recreates everything
- Takes ~20-30 minutes

✅ **S3 bucket is your source of truth**
- Keep `aws-drs-orchestration` bucket safe
- Sync local changes regularly
- Enable versioning for safety
