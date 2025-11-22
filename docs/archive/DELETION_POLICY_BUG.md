# CRITICAL: DeletionPolicy Bug in Nested Stacks

## Issue Discovery
**Date**: 2025-11-20  
**Session**: Session 5 Part 4  
**Severity**: P1 - Infrastructure Cleanup Blocker

## Problem Summary
`DeletionPolicy: Retain` on nested stack declarations in `cfn/master-template.yaml` prevents proper cascading deletion of child resources when parent stack is deleted or rolled back.

## Root Cause

### Original Code (BROKEN)
```yaml
# cfn/master-template.yaml - Lines 135-137
FrontendStack:
  Type: AWS::CloudFormation::Stack
  DeletionPolicy: Retain  # ❌ BLOCKS cascading delete
  UpdateReplacePolicy: Retain
```

### Impact
1. **Parent DELETE doesn't cascade**: Deleting parent stack leaves nested stacks orphaned
2. **ROLLBACK doesn't cleanup**: Failed deployment rollback leaves nested stacks in CREATE_FAILED state
3. **Orphaned resources**: Resources in nested stacks (S3 buckets, SSM docs, CloudFront OACs) require manual cleanup

## Affected Resources

### Nested Stacks
- `DatabaseStack` - DynamoDB tables
- `LambdaStack` - Lambda functions, IAM roles
- `ApiStack` - Cognito, API Gateway, Step Functions
- `FrontendStack` - S3, CloudFront, SSM documents

### Resources Left Orphaned (Observed)
1. **S3 Bucket**: `drs-orchestration-fe-***REMOVED***-test`
   - Had versioning enabled
   - Required deleting all versions and delete markers
   - Manual cleanup: `aws s3 rb s3://bucket --force`

2. **SSM Documents** (3):
   - `drs-orchestration-app-startup-test`
   - `drs-orchestration-health-check-test`
   - `drs-orchestration-network-validation-test`
   - Manual cleanup: `aws ssm delete-document --name <doc-name>`

3. **CloudFront OAC**:
   - ID: `E2JA5NFK9WZM77`
   - Required ETag for deletion
   - Manual cleanup: `aws cloudfront delete-origin-access-control --id <id> --if-match <etag>`

## Fix Applied

### New Code (FIXED)
```yaml
# All 4 nested stacks now have DeletionPolicy: Delete
DatabaseStack:
  Type: AWS::CloudFormation::Stack
  DeletionPolicy: Delete  # ✅ ENABLES cascading delete
  Properties:
    ...

LambdaStack:
  Type: AWS::CloudFormation::Stack
  DeletionPolicy: Delete
  DependsOn: DatabaseStack
  Properties:
    ...

ApiStack:
  Type: AWS::CloudFormation::Stack
  DeletionPolicy: Delete
  DependsOn:
    - DatabaseStack
    - LambdaStack
  Properties:
    ...

FrontendStack:
  Type: AWS::CloudFormation::Stack
  DeletionPolicy: Delete  # ✅ Removed Retain + UpdateReplacePolicy
  DependsOn:
    - LambdaStack
    - ApiStack
  Properties:
    ...
```

### Resource-Level Protection
Individual resources within nested stacks retain their own DeletionPolicy settings:
- S3 buckets: `DeletionPolicy: Retain` (data protection)
- DynamoDB tables: `DeletionPolicy: Retain` (data protection)
- SSM documents: `DeletionPolicy: Delete` (infrastructure, not data)
- CloudFront OACs: `DeletionPolicy: Delete` (infrastructure)

## Verification Steps

### 1. Deploy Stack
```bash
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name drs-orchestration-test \
  --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND
```

### 2. Verify Nested Stacks Created
```bash
aws cloudformation describe-stacks \
  --query 'Stacks[?contains(StackName, `drs-orchestration-test`)].StackName'
```

### 3. Delete Parent Stack
```bash
aws cloudformation delete-stack --stack-name drs-orchestration-test
```

### 4. Verify Cascade Delete
```bash
# Should show all nested stacks as DELETE_COMPLETE or not found
aws cloudformation describe-stacks --stack-name drs-orchestration-test-DatabaseStack-*
aws cloudformation describe-stacks --stack-name drs-orchestration-test-LambdaStack-*
aws cloudformation describe-stacks --stack-name drs-orchestration-test-ApiStack-*
aws cloudformation describe-stacks --stack-name drs-orchestration-test-FrontendStack-*
```

### 5. Check for Orphaned Resources
```bash
# Run verification script
./scripts/verify-cleanup.sh test

# Should return: "✅ All resources cleaned up for test environment"
```

## Manual Cleanup Procedure (If Needed)

### For Orphaned Nested Stacks
```bash
# Get nested stack names
aws cloudformation list-stacks \
  --stack-status-filter CREATE_FAILED DELETE_FAILED \
  --query 'StackSummaries[?contains(StackName, `drs-orchestration-test`)].StackName'

# Delete each nested stack
aws cloudformation delete-stack --stack-name <nested-stack-name>
```

### For Orphaned S3 Buckets
```bash
# Delete all versions and markers
aws s3api delete-objects --bucket <bucket> \
  --delete "$(aws s3api list-object-versions --bucket <bucket> \
    --query='{Objects: Versions[].{Key:Key,VersionId:VersionId}}' --output json)"

aws s3api delete-objects --bucket <bucket> \
  --delete "$(aws s3api list-object-versions --bucket <bucket> \
    --query='{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' --output json)"

# Remove bucket
aws s3 rb s3://<bucket>
```

### For Orphaned SSM Documents
```bash
aws ssm delete-document --name <document-name>
```

### For Orphaned CloudFront OACs
```bash
# Get ETag
ETAG=$(aws cloudfront get-origin-access-control --id <oac-id> --query 'ETag' --output text)

# Delete with ETag
aws cloudfront delete-origin-access-control --id <oac-id> --if-match "$ETAG"
```

## Prevention

### Template Guidelines
1. **NEVER** use `DeletionPolicy: Retain` on nested stack declarations
2. **ALWAYS** use `DeletionPolicy: Delete` on nested stacks for proper cascade
3. **ONLY** use `DeletionPolicy: Retain` on individual resources that contain data:
   - S3 buckets with user content
   - DynamoDB tables with application data
   - RDS databases
   - EFS file systems

### Review Checklist
- [ ] Master template has no `DeletionPolicy: Retain` on nested stacks
- [ ] Individual resources have appropriate DeletionPolicy for their type
- [ ] Cleanup verification script passes
- [ ] Delete test succeeds with no orphaned resources

## References
- **AWS Docs**: [DeletionPolicy Attribute](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-attribute-deletionpolicy.html)
- **Best Practice**: Use `Delete` for infrastructure, `Retain` for data
- **Cleanup Script**: `scripts/verify-cleanup.sh`

## Validation Results

### Test 1: Session 10/11 Validation (2025-11-20 14:18 EST)
**Objective**: Validate both Session 7 DeletionPolicy fix and Session 10 S3 cleanup fix

**Deployment**:
- Stack: `drs-orchestration-test`
- Region: `us-east-1`
- Deployment time: ~9 minutes
- All 4 nested stacks: CREATE_COMPLETE ✅

**Deletion Test**:
- Deletion initiated: 19:18:15 UTC
- Master stack DELETE_COMPLETE: 19:18:15
- FrontendStack DELETE_COMPLETE: 19:18:26 (11 seconds) ✅
- ApiStack DELETE_COMPLETE: 19:24:20 (6 min 5 sec)
- LambdaStack DELETE_COMPLETE: 19:25:08 (6 min 53 sec)
- DatabaseStack DELETE_COMPLETE: 19:25:42 (7 min 27 sec)
- **Total deletion time**: ~7.5 minutes

**Session 10 Fix Validation (S3 Cleanup)**:
- Lambda log: "Successfully emptied bucket drs-test-fe-***REMOVED***-test" ✅
- Lambda execution: 121 seconds
- CloudFormation response: SUCCESS
- S3 bucket deleted cleanly (no manual intervention needed)

**Session 7 Fix Validation (DeletionPolicy)**:
- ✅ All 4 nested stacks CASCADE DELETED
- ✅ NO RETAINED nested stacks found
- ✅ NO orphaned resources remaining
- ✅ NO manual cleanup required

**Verification Query**:
```bash
aws cloudformation list-stacks --region us-east-1 \
  --query "StackSummaries[?contains(StackName, 'drs-orchestration-test')].[StackName,StackStatus]"
```

**Result**: All 5 stacks (master + 4 nested) show `DELETE_COMPLETE` status.

## Status
- **Fix**: ✅ Applied to master-template.yaml (Session 7 - Commit 4324411)
- **S3 Cleanup Fix**: ✅ Applied to lambda/index.py (Session 10 - Commit c8a5fbe)
- **Deployed**: ✅ Verified 2025-11-20 14:18 EST
- **Validated**: ✅ BOTH FIXES CONFIRMED WORKING
  - Session 7: Nested stacks cascade delete (no orphaned resources)
  - Session 10: Lambda empties S3 bucket before deletion
