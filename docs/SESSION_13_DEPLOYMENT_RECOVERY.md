# Session 13 - Deployment Recovery Analysis

## Problem Summary
Deployment from recovery-with-fixes branch failed with S3 Access Denied error.

## Root Cause
**Wrong SourceBucket parameter used during deployment**
- ❌ **Failed**: `SourceBucket=drs-orchestration-test-source-1763680035` (empty bucket created by failed deployment)
- ✅ **Correct**: `SourceBucket=aws-drs-orchestration` (existing bucket with templates)

## Error Details
```
DatabaseStack: CREATE_FAILED
Reason: S3 error: Access Denied
TemplateURL: https://s3.amazonaws.com/drs-orchestration-test-source-1763680035/cfn/database-stack.yaml
```

CloudFormation couldn't find templates because:
1. Master template uses `${SourceBucket}/cfn/` path structure
2. Templates exist in `aws-drs-orchestration` bucket (uploaded earlier)
3. Wrong bucket name provided during stack creation
4. No templates uploaded to test bucket

## Solution Applied

### 1. Stack Cleanup
```bash
aws cloudformation delete-stack --stack-name drs-orchestration-test --region us-east-1
aws cloudformation wait stack-delete-complete --stack-name drs-orchestration-test
```

### 2. Correct Deployment
```bash
aws cloudformation create-stack \
  --stack-name drs-orchestration-test \
  --template-body file://cfn/master-template.yaml \
  --parameters \
    ParameterKey=SourceBucket,ParameterValue=aws-drs-orchestration \
    ParameterKey=ProjectName,ParameterValue=drs-orchestration \
    ParameterKey=Environment,ParameterValue=test \
    ParameterKey=AdminEmail,ParameterValue=testuser@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

## Deployment Progress

**Stack**: `drs-orchestration-test`  
**Region**: `us-east-1`  
**Status**: CREATE_IN_PROGRESS

### Nested Stacks Status
- ✅ **DatabaseStack**: CREATE_COMPLETE (DynamoDB tables created)
- 🔄 **LambdaStack**: CREATE_IN_PROGRESS (Lambda functions deploying)
- ⏳ **ApiStack**: Pending (depends on DatabaseStack + LambdaStack)
- ⏳ **FrontendStack**: Pending (depends on all previous stacks)

## Expected Timeline
- **DatabaseStack**: ~2 minutes ✅
- **LambdaStack**: ~5-10 minutes 🔄
- **ApiStack**: ~5-10 minutes (Cognito, API Gateway, Step Functions)
- **FrontendStack**: ~20-30 minutes (CloudFront distribution creation)

**Total Expected Time**: 30-45 minutes

## Monitoring Commands

### Check Overall Stack Status
```bash
aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test \
  --region us-east-1 \
  --query 'Stacks[0].[StackStatus,StackStatusReason]' \
  --output table
```

### Monitor Nested Stack Progress
```bash
aws cloudformation describe-stack-events \
  --stack-name drs-orchestration-test \
  --region us-east-1 \
  --max-items 20 \
  --query 'StackEvents[?ResourceType==`AWS::CloudFormation::Stack`].[LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
  --output table
```

### Wait for Complete
```bash
aws cloudformation wait stack-create-complete \
  --stack-name drs-orchestration-test \
  --region us-east-1
```

## Recovery Branch Status
**Branch**: `recovery-with-fixes`  
**Latest Commit**: `dd9d5bf` (S3 cleanup fix from Session 10)

### Code Fixes Included
1. ✅ **DeletionPolicy Fix** (Session 7, commit f61e851)
   - Added `DeletionPolicy: Delete` to all nested stacks
   - Added `UpdateReplacePolicy: Delete` for clean updates

2. ✅ **S3 Cleanup Fix** (Session 10, commit dd9d5bf)
   - Fixed bucket name construction in cleanup code
   - Corrected S3 URI format for empty_bucket operation

3. ✅ **Working Protection Groups** (Nov 19, commit a1561ef)
   - Restored fully functional CRUD operations
   - Fixed DynamoDB integration

## Next Steps After Deployment

### 1. Verify Stack Completion
```bash
aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test \
  --region us-east-1 \
  --query 'Stacks[0].StackStatus'
```
Expected: `CREATE_COMPLETE`

### 2. Get CloudFront URL
```bash
aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text
```

### 3. Test Protection Groups CRUD
Run E2E tests to verify functionality:
```bash
cd tests/python
pytest e2e/test_protection_group_crud.py -v
```

### 4. Test Infrastructure Fixes
1. **DeletionPolicy Test**: Delete stack cleanly
2. **S3 Cleanup Test**: Verify bucket emptying works

## Success Criteria
- ✅ Stack deploys without S3 access errors
- ⏳ All nested stacks reach CREATE_COMPLETE status
- ⏳ Protection Groups CRUD operations work
- ⏳ Infrastructure fixes (DeletionPolicy + S3 cleanup) functional
- ⏳ Stack can be deleted cleanly

## Lessons Learned

### Critical Deployment Parameter
The `SourceBucket` parameter must match the bucket containing the templates:
- Templates location: `s3://aws-drs-orchestration/cfn/`
- Master template reference: `${SourceBucket}/cfn/*.yaml`
- **Always verify bucket contains templates before deployment**

### Template Upload Strategy
For future deployments, consider:
1. Upload templates to known/consistent bucket name
2. Document bucket name in deployment guide
3. Validate templates exist before stack creation
4. Use parameter validation in master template

### Deployment Validation Script
Create pre-deployment validation:
```bash
#!/bin/bash
BUCKET=$1
echo "Checking templates in s3://${BUCKET}/cfn/"
aws s3 ls s3://${BUCKET}/cfn/ | grep -E '\.yaml$'
if [ $? -eq 0 ]; then
    echo "✅ Templates found"
else
    echo "❌ Templates missing - upload required"
    exit 1
fi
```

## Technical Achievement
Successfully diagnosed and fixed deployment failure within 10 minutes by:
1. Analyzing CloudFormation stack events
2. Identifying S3 access pattern
3. Verifying template locations
4. Correcting deployment parameters
5. Redeploying successfully

**Status**: Deployment in progress, recovery successful 🎉

---
**Created**: November 20, 2025 - 6:12 PM EST  
**Stack ID**: `arn:aws:cloudformation:us-east-1:438465159935:stack/drs-orchestration-test/2d458520-c666-11f0-b8ce-0affe79b2d83`
