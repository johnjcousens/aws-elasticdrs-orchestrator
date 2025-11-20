# CloudFormation Stack Cleanup Procedure

## Critical Cleanup Requirements for drs-orchestration Stacks

### Overview
The drs-orchestration CloudFormation stacks require **special manual cleanup steps** before deletion due to stateful resources that CloudFormation cannot automatically delete.

---

## 🚨 CRITICAL: Proper Cleanup Order

### ❌ NEVER Do This
**DO NOT manually delete the S3 bucket before deleting the CloudFormation stack!**

**Why:** The FrontendStack has a custom resource (FrontendBuildResource Lambda) that handles bucket cleanup. If you delete the bucket manually first, the custom resource will timeout trying to delete a non-existent bucket, causing the stack to fail with DELETE_FAILED.

### ✅ Correct Cleanup Order

**Option 1: Let CloudFormation Handle Everything (Recommended)**
```bash
# Just delete the stack - it will handle S3 bucket cleanup
aws cloudformation delete-stack --stack-name drs-orchestration-qa-FrontendStack-XXXXX
aws cloudformation wait stack-delete-complete --stack-name drs-orchestration-qa-FrontendStack-XXXXX
```

The custom resource Lambda will:
1. Empty the S3 bucket
2. Delete the S3 bucket
3. Delete CloudFront distribution
4. Delete Origin Access Control
5. Delete all other resources

**Option 2: Manual Cleanup (Only if Stack Already Failed)**
If the stack is already in DELETE_FAILED state:
```bash
# 1. Retry stack deletion (it will skip failed resources)
aws cloudformation delete-stack --stack-name drs-orchestration-qa-FrontendStack-XXXXX

# 2. If it still fails, delete remaining resources manually
# (But this should rarely be needed)
```

### Step 1: Disable CloudFront Distributions (Optional - Only for Faster Cleanup)

**Why:** CloudFront distributions must be disabled before deletion (takes ~5 minutes to propagate).

```bash
# List distributions
aws cloudfront list-distributions --query 'DistributionList.Items[].{Id:Id,Status:Status,Comment:Comment}' --output table

# For each drs-orchestration distribution:
DIST_ID="EDYN92FL7I8WH"

# Get config and disable
aws cloudfront get-distribution-config --id ${DIST_ID} | \
  jq -r '.DistributionConfig | .Enabled = false' > /tmp/cf-config.json

# Update distribution
ETAG=$(aws cloudfront get-distribution-config --id ${DIST_ID} --query 'ETag' --output text)
aws cloudfront update-distribution --id ${DIST_ID} \
  --distribution-config file:///tmp/cf-config.json \
  --if-match ${ETAG}

# Wait for deployment (~5 minutes)
aws cloudfront wait distribution-deployed --id ${DIST_ID}
```

### Step 2: Delete Orphaned CloudFront Resources (Only After Stack Deletion)

**Why:** Failed stack deletions leave orphaned CloudFront resources that block future deployments.

```bash
# After distribution is deployed and disabled, delete it
ETAG=$(aws cloudfront get-distribution --id ${DIST_ID} --query 'ETag' --output text)
aws cloudfront delete-distribution --id ${DIST_ID} --if-match ${ETAG}

# Delete Origin Access Control
OAC_ID=$(aws cloudfront list-origin-access-controls \
  --query 'OriginAccessControlList.Items[?Name==`drs-orchestration-oac`].Id' \
  --output text)

ETAG=$(aws cloudfront get-origin-access-control --id ${OAC_ID} --query 'ETag' --output text)
aws cloudfront delete-origin-access-control --id ${OAC_ID} --if-match ${ETAG}
```

---

## Complete Cleanup Workflow

### Phase 1: Pre-Cleanup (Optional - Only for Faster Cleanup)
```bash
# 1. Disable CloudFront distribution (optional - speeds up deletion by ~5 min)
DIST_ID=$(aws cloudfront list-distributions \
  --query 'DistributionList.Items[?Comment==`drs-orchestration Frontend Distribution`].Id' \
  --output text)

if [ ! -z "$DIST_ID" ]; then
  aws cloudfront get-distribution-config --id ${DIST_ID} | \
    jq -r '.DistributionConfig | .Enabled = false' > /tmp/cf-config.json
  
  ETAG=$(aws cloudfront get-distribution-config --id ${DIST_ID} --query 'ETag' --output text)
  aws cloudfront update-distribution --id ${DIST_ID} \
    --distribution-config file:///tmp/cf-config.json \
    --if-match ${ETAG}
  
  echo "⏳ Waiting for distribution to deploy (5 min)..."
  aws cloudfront wait distribution-deployed --id ${DIST_ID}
fi
```

### Phase 2: Delete Main Stack (Handles S3 Automatically)
```bash
# Delete the main stack - it will handle S3 bucket cleanup via custom resource
STACK_NAME="drs-orchestration-qa"
aws cloudformation delete-stack --stack-name ${STACK_NAME}

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}

# If deletion fails with DELETE_FAILED (e.g., custom resource timeout):
# 1. Check if S3 bucket still exists - if not, retry deletion:
aws cloudformation delete-stack --stack-name ${STACK_NAME}
aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}
```

### Phase 3: Post-Cleanup (After Stack Deletion)
```bash
# 1. Delete CloudFront distribution
if [ ! -z "$DIST_ID" ]; then
  ETAG=$(aws cloudfront get-distribution --id ${DIST_ID} --query 'ETag' --output text)
  aws cloudfront delete-distribution --id ${DIST_ID} --if-match ${ETAG}
fi

# 2. Delete Origin Access Control
OAC_ID=$(aws cloudfront list-origin-access-controls \
  --query 'OriginAccessControlList.Items[?Name==`drs-orchestration-oac`].Id' \
  --output text)

if [ ! -z "$OAC_ID" ]; then
  ETAG=$(aws cloudfront get-origin-access-control --id ${OAC_ID} --query 'ETag' --output text)
  aws cloudfront delete-origin-access-control --id ${OAC_ID} --if-match ${ETAG}
fi

# 3. Verify all nested stacks are gone
aws cloudformation list-stacks \
  --query 'StackSummaries[?contains(StackName, `drs-orchestration-qa`)].[StackName,StackStatus]' \
  --output table
```

---

## Common Issues & Solutions

### Issue 1: FrontendStack DELETE_FAILED
**Cause:** S3 bucket was manually deleted before stack deletion, causing custom resource timeout

**Symptoms:**
```
FrontendBuildResource: CloudFormation did not receive a response from your Custom Resource
Stack Status: DELETE_FAILED
```

**Solution:**
```bash
# Simply retry deletion - bucket is already gone, custom resource will skip it
aws cloudformation delete-stack --stack-name ${STACK_NAME}
aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}
```

**Prevention:** Never manually delete the S3 bucket first! Let CloudFormation handle it.

### Issue 2: "OriginAccessControlInUse" Error
**Cause:** CloudFront distribution still using the OAC

**Solution:** Must delete distribution first (requires distribution to be disabled and deployed)

### Issue 3: "AlreadyExists" on Redeployment
**Cause:** Orphaned CloudFront OAC from previous failed deployment

**Solution:** Delete the orphaned OAC (see Phase 3 cleanup)

### Issue 2: FrontendStack DELETE_IN_PROGRESS Stuck
**Cause:** Waiting for CloudFront distribution to finish deploying (if you disabled it first)

**Solution:** Wait for distribution Status to change from "InProgress" to "Deployed" (~5 minutes)

### Issue 3: "Bucket not empty" Error (Rare)
**Cause:** Custom resource Lambda failed and didn't empty bucket

**Solution:**
```bash
# Manually empty bucket
BUCKET=$(aws s3 ls | grep drs-orchestration-fe | awk '{print $3}')
aws s3 rm s3://${BUCKET} --recursive

# Retry stack deletion
aws cloudformation delete-stack --stack-name ${STACK_NAME}
```

---

## Verification Checklist

After cleanup, verify:
- [ ] All S3 buckets deleted: `aws s3 ls | grep drs-orchestration`
- [ ] All CloudFront distributions deleted: `aws cloudfront list-distributions`
- [ ] All OACs deleted: `aws cloudfront list-origin-access-controls`
- [ ] All stacks deleted: `aws cloudformation list-stacks | grep drs-orchestration`

---

## Timeline Expectations

| Step | Expected Duration |
|------|------------------|
| Empty S3 bucket | 1-2 minutes |
| Disable CloudFront | Immediate |
| CloudFront deployment | **5-7 minutes** |
| Stack deletion | 3-5 minutes |
| Delete CloudFront | 1-2 minutes |
| Delete OAC | Immediate |
| **Total** | **10-17 minutes** |

---

## Automation Script

Complete cleanup script:

```bash
#!/bin/bash
# cleanup-drs-orchestration.sh

STACK_NAME="drs-orchestration-qa"

echo "🧹 Starting cleanup for ${STACK_NAME}..."

# Phase 1: Pre-cleanup
echo "📦 Phase 1: Cleaning up S3 and CloudFront..."

# Find and empty S3 bucket
BUCKET=$(aws s3 ls | grep drs-orchestration-fe-.*-${STACK_NAME#drs-orchestration-} | awk '{print $3}')
if [ ! -z "$BUCKET" ]; then
  echo "  Emptying bucket: ${BUCKET}"
  aws s3 rm s3://${BUCKET} --recursive
  aws s3api delete-bucket --bucket ${BUCKET}
  echo "  ✅ Bucket deleted"
fi

# Find and disable CloudFront
DIST_ID=$(aws cloudfront list-distributions \
  --query 'DistributionList.Items[?Comment==`drs-orchestration Frontend Distribution`].Id' \
  --output text)

if [ ! -z "$DIST_ID" ]; then
  echo "  Disabling CloudFront distribution: ${DIST_ID}"
  aws cloudfront get-distribution-config --id ${DIST_ID} | \
    jq -r '.DistributionConfig | .Enabled = false' > /tmp/cf-config.json
  
  ETAG=$(aws cloudfront get-distribution-config --id ${DIST_ID} --query 'ETag' --output text)
  aws cloudfront update-distribution --id ${DIST_ID} \
    --distribution-config file:///tmp/cf-config.json \
    --if-match ${ETAG}
  
  echo "  ⏳ Waiting for CloudFront deployment (5 min)..."
  aws cloudfront wait distribution-deployed --id ${DIST_ID}
  echo "  ✅ CloudFront disabled"
fi

# Phase 2: Delete stack
echo "🗑️  Phase 2: Deleting CloudFormation stack..."
aws cloudformation delete-stack --stack-name ${STACK_NAME}
echo "  ⏳ Waiting for stack deletion..."
aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}
echo "  ✅ Stack deleted"

# Phase 3: Post-cleanup
echo "🧹 Phase 3: Cleaning up CloudFront resources..."

if [ ! -z "$DIST_ID" ]; then
  echo "  Deleting CloudFront distribution: ${DIST_ID}"
  ETAG=$(aws cloudfront get-distribution --id ${DIST_ID} --query 'ETag' --output text)
  aws cloudfront delete-distribution --id ${DIST_ID} --if-match ${ETAG}
  echo "  ✅ Distribution deleted"
fi

OAC_ID=$(aws cloudfront list-origin-access-controls \
  --query 'OriginAccessControlList.Items[?Name==`drs-orchestration-oac`].Id' \
  --output text)

if [ ! -z "$OAC_ID" ]; then
  echo "  Deleting Origin Access Control: ${OAC_ID}"
  ETAG=$(aws cloudfront get-origin-access-control --id ${OAC_ID} --query 'ETag' --output text)
  aws cloudfront delete-origin-access-control --id ${OAC_ID} --if-match ${ETAG}
  echo "  ✅ OAC deleted"
fi

echo "✅ Cleanup complete!"
```

Save as `scripts/cleanup-drs-orchestration.sh` and run:
```bash
chmod +x scripts/cleanup-drs-orchestration.sh
./scripts/cleanup-drs-orchestration.sh
```

---

**Last Updated:** November 20, 2025
**Tested With:** drs-orchestration-qa stack cleanup
