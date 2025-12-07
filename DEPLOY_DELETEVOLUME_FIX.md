# Deploy DeleteVolume Fix - Quick Guide

**Issue**: DRS drill fails on multi-disk servers with `ec2:DeleteVolume` permission denied  
**Fix**: Remove IAM condition blocking DRS staging volume cleanup  
**Files Changed**: `cfn/lambda-stack.yaml`

---

## Quick Deploy

```bash
# 1. Commit changes
git add cfn/lambda-stack.yaml docs/
git commit -m "Fix: Remove IAM condition blocking DRS DeleteVolume on staging volumes

- Root cause: IAM condition required AWSElasticDisasterRecoveryManaged tag
- DRS staging volumes use drs.amazonaws.com-* tags instead
- Removed condition from OrchestrationRole and ApiHandlerRole
- Fixes multi-disk server drill failures during cleanup phase"

git push origin main

# 2. Deploy CloudFormation
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name drs-orchestration-test \
  --parameter-overrides \
    ProjectName=drs-orchestration \
    Environment=test \
    SourceBucket=aws-drs-orchestration \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1

# 3. Wait for completion (5-10 minutes)
aws cloudformation wait stack-update-complete \
  --stack-name drs-orchestration-test \
  --region us-east-1

echo "✅ Deployment complete!"
```

---

## Verify Fix

```bash
# Check IAM policy has DeleteVolume without condition
aws iam get-role-policy \
  --role-name drs-orchestration-test-LambdaStac-OrchestrationRole-LuY7ANIrFtME \
  --policy-name EC2Access \
  --region us-east-1 \
  --query 'PolicyDocument.Statement[?contains(Action, `ec2:DeleteVolume`)]' \
  --output json

# Should show DeleteVolume with NO Condition block
```

---

## Test DRS Drill

1. Go to https://d1wfyuosowt0hl.cloudfront.net
2. Login: `***REMOVED***` / `IiG2b1o+D$`
3. Navigate to Recovery Plans
4. Execute a plan with both servers
5. **Expected**: Both servers LAUNCH successfully
6. **Expected**: DRS job status = COMPLETED

---

## What Changed

### Before (Broken)
```yaml
- Effect: Allow
  Action:
    - ec2:DeleteVolume
  Resource: '*'
  Condition:
    StringEquals:
      ec2:ResourceTag/AWSElasticDisasterRecoveryManaged: 'true'  # ❌ BLOCKS DRS
```

### After (Fixed)
```yaml
- Effect: Allow
  Action:
    - ec2:DetachVolume
    - ec2:DeleteVolume
  Resource: '*'
  # NO CONDITION - DRS staging volumes use drs.amazonaws.com-* tags
```

---

## Rollback (if needed)

```bash
# Revert to previous version
git revert HEAD
git push origin main

# Redeploy
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name drs-orchestration-test \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

---

## Documentation

- **Root Cause Analysis**: `docs/DRS_DETACHVOLUME_ROOT_CAUSE_ANALYSIS.md`
- **Session Notes**: `docs/SESSION_70_DELETEVOLUME_FIX.md`
- **Step Functions Plan**: `docs/STEP_FUNCTIONS_POLLING_IMPLEMENTATION.md`

---

**Deployment Time**: ~10 minutes  
**Risk**: LOW - Removing overly restrictive condition  
**Testing**: Required before production use
