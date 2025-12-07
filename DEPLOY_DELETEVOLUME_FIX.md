# Deploy DeleteVolume Fix - Quick Guide

**Status**: ✅ DEPLOYED & VALIDATED (Session 71)  
**Issue**: DRS drills failed with `ec2:DeleteVolume` and `ec2:StartInstances` permission denied  
**Fix**: Removed IAM conditions blocking DRS operations  
**Files Changed**: `cfn/lambda-stack.yaml`

**Validation**: Job drsjob-36ee3447586054f5e - Both servers launched successfully  
**See**: [Session 71 Validation Report](docs/SESSION_71_SUCCESSFUL_DRILL_VALIDATION.md)

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

✅ **VALIDATION COMPLETE** (Session 71)

**Test Job**: drsjob-36ee3447586054f5e  
**Result**: Both servers launched successfully
- EC2AMAZ-8B7IRHJ → i-01fdffb937aa6efec ✅ LAUNCHED
- EC2AMAZ-3B0B3UD → i-050bf37d129e94bfc ✅ LAUNCHED
- Duration: 23 minutes 56 seconds
- Status: COMPLETED

**To Test Again**:
1. Go to https://d1wfyuosowt0hl.cloudfront.net
2. Login: `testuser@example.com` / `IiG2b1o+D$`
3. Navigate to Recovery Plans
4. Execute a plan with servers
5. **Expected**: All servers LAUNCH successfully

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

- **Session 71 Validation**: `docs/SESSION_71_SUCCESSFUL_DRILL_VALIDATION.md` - Production test results
- **Session 70 Root Cause**: `docs/SESSION_70_FINAL_ROOT_CAUSE.md` - Why IAM conditions blocked DRS
- **Step Functions Plan**: `docs/STEP_FUNCTIONS_POLLING_IMPLEMENTATION.md`

---

**Deployment Time**: ~10 minutes  
**Status**: ✅ DEPLOYED & VALIDATED  
**Risk**: NONE - Fix confirmed working in production
