# CloudFormation Template Quality Fix Plan

**Created**: November 28, 2025  
**Status**: Ready for Implementation  
**Impact**: 38 real issues across 4 deployed templates

---

## Executive Summary

This document provides a complete fix plan for CloudFormation quality issues identified by cfn-lint. The issues fall into two categories:

1. **Hardcoded Partitions** (28 issues): Prevents deployment in AWS GovCloud and China regions
2. **Missing Deletion/Update Policies** (10 issues): Risk of data loss during stack updates/deletion

**security-stack.yaml**: 51 errors are FALSE POSITIVES - it's a reference snippet file, not a deployed template.

---

## ✅ COMPLETION STATUS

### lambda-stack.yaml - COMPLETE (November 28, 2025)
**Status**: ✅ ALL 14 ISSUES FIXED AND VALIDATED
- **Commit**: 445a512 - "fix(cfn): Fix 14 CloudFormation quality issues in lambda-stack.yaml"
- **Date**: November 28, 2025 12:56 PM EST
- **Validation**: cfn-lint returns ZERO errors
- **Changes**: +777 insertions, -17 deletions

**Fixes Applied:**
- ✅ 10 hardcoded partition ARNs → `arn:${AWS::Partition}:*`
- ✅ 4 missing deletion/update policies → `DeletionPolicy: Retain`

**Impact:**
- ✅ Multi-partition support enabled (AWS Standard + GovCloud + China)
- ✅ Data protection policies in place (logs retained)
- ✅ Production-grade CloudFormation best practices

**Deferred (26 issues):**
- api-stack.yaml: 21 issues
- database-stack.yaml: 6 issues  
- frontend-stack.yaml: 1 issue

---

## Part 1: lambda-stack.yaml (14 Issues)

### Issue Type Breakdown
- 10 hardcoded partition ARNs (I3042)
- 4 missing deletion/update policies (I3011)

### 1.1: Hardcoded Partition ARNs (8 fixes)

#### Fix #1: ApiHandlerRole - DynamoDB Policy (Line 75)
**Current (WRONG):**
```yaml
- Effect: Allow
  Action:
    - dynamodb:GetItem
    - dynamodb:PutItem
    - dynamodb:UpdateItem
    - dynamodb:DeleteItem
    - dynamodb:Query
    - dynamodb:Scan
  Resource:
    - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ProtectionGroupsTableName}
```

**Fixed:**
```yaml
- Effect: Allow
  Action:
    - dynamodb:GetItem
    - dynamodb:PutItem
    - dynamodb:UpdateItem
    - dynamodb:DeleteItem
    - dynamodb:Query
    - dynamodb:Scan
  Resource:
    - !Sub 'arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ProtectionGroupsTableName}'
```

#### Fix #2: ApiHandlerRole - DynamoDB Policy (Line 89)
**Current (WRONG):**
```yaml
- arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${RecoveryPlansTableName}
```

**Fixed:**
```yaml
- !Sub 'arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${RecoveryPlansTableName}'
```

#### Fix #3: ApiHandlerRole - DynamoDB Policy (Line 119)
**Current (WRONG):**
```yaml
- arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ExecutionHistoryTableName}
- arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ExecutionHistoryTableName}/index/*
```

**Fixed:**
```yaml
- !Sub 'arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ExecutionHistoryTableName}'
- !Sub 'arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ExecutionHistoryTableName}/index/*'
```

#### Fix #4: OrchestrationRole - DRS Policy (Line 150)
**Current (WRONG):**
```yaml
Resource:
  - arn:aws:drs:${AWS::Region}:${AWS::AccountId}:*
```

**Fixed:**
```yaml
Resource:
  - !Sub 'arn:${AWS::Partition}:drs:${AWS::Region}:${AWS::AccountId}:*'
```

#### Fix #5: CustomResourceRole - S3 Policy (Line 242)
**Current (WRONG):**
```yaml
Resource:
  - arn:aws:s3:::${SourceBucket}/*
```

**Fixed:**
```yaml
Resource:
  - !Sub 'arn:${AWS::Partition}:s3:::${SourceBucket}/*'
```

#### Fix #6: CustomResourceRole - CloudFront Policy (Line 253)
**Current (WRONG):**
```yaml
Resource:
  - arn:aws:cloudfront::${AWS::AccountId}:distribution/*
```

**Fixed:**
```yaml
Resource:
  - !Sub 'arn:${AWS::Partition}:cloudfront::${AWS::AccountId}:distribution/*'
```

#### Fix #7: ExecutionFinderRole - DynamoDB Policy (Line 281)
**Current (WRONG):**
```yaml
Resource:
  - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ExecutionHistoryTableName}
  - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ExecutionHistoryTableName}/index/StatusIndex
```

**Fixed:**
```yaml
Resource:
  - !Sub 'arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ExecutionHistoryTableName}'
  - !Sub 'arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ExecutionHistoryTableName}/index/StatusIndex'
```

#### Fix #8: ApiHandlerFunction - State Machine Environment Variable (Line 310)
**Current (WRONG):**
```yaml
Environment:
  Variables:
    STATE_MACHINE_ARN: arn:aws:states:${AWS::Region}:${AWS::AccountId}:stateMachine:${ProjectName}-orchestration
```

**Fixed:**
```yaml
Environment:
  Variables:
    STATE_MACHINE_ARN: !Sub 'arn:${AWS::Partition}:states:${AWS::Region}:${AWS::AccountId}:stateMachine:${ProjectName}-orchestration'
```

### 1.2: Missing Deletion/Update Policies (4 fixes)

#### Fix #9: ApiHandlerLogGroup (Line 395)
**Current (MISSING):**
```yaml
ApiHandlerLogGroup:
  Type: AWS::Logs::LogGroup
  Properties:
    LogGroupName: !Sub '/aws/lambda/${ProjectName}-api-handler'
    RetentionInDays: 30
```

**Fixed:**
```yaml
ApiHandlerLogGroup:
  Type: AWS::Logs::LogGroup
  DeletionPolicy: Retain
  UpdateReplacePolicy: Retain
  Properties:
    LogGroupName: !Sub '/aws/lambda/${ProjectName}-api-handler'
    RetentionInDays: 30
```

#### Fix #10: OrchestrationLogGroup (Line 401)
**Current (MISSING):**
```yaml
OrchestrationLogGroup:
  Type: AWS::Logs::LogGroup
  Properties:
    LogGroupName: !Sub '/aws/lambda/${ProjectName}-orchestration'
    RetentionInDays: 30
```

**Fixed:**
```yaml
OrchestrationLogGroup:
  Type: AWS::Logs::LogGroup
  DeletionPolicy: Retain
  UpdateReplacePolicy: Retain
  Properties:
    LogGroupName: !Sub '/aws/lambda/${ProjectName}-orchestration'
    RetentionInDays: 30
```

#### Fix #11: FrontendBuilderLogGroup (Line 407)
**Current (MISSING):**
```yaml
FrontendBuilderLogGroup:
  Type: AWS::Logs::LogGroup
  Properties:
    LogGroupName: !Sub '/aws/lambda/${ProjectName}-frontend-builder'
    RetentionInDays: 7
```

**Fixed:**
```yaml
FrontendBuilderLogGroup:
  Type: AWS::Logs::LogGroup
  DeletionPolicy: Retain
  UpdateReplacePolicy: Retain
  Properties:
    LogGroupName: !Sub '/aws/lambda/${ProjectName}-frontend-builder'
    RetentionInDays: 7
```

#### Fix #12: ExecutionFinderLogGroup (Line 413)
**Current (MISSING):**
```yaml
ExecutionFinderLogGroup:
  Type: AWS::Logs::LogGroup
  Properties:
    LogGroupName: !Sub '/aws/lambda/${ProjectName}-execution-finder'
    RetentionInDays: 30
```

**Fixed:**
```yaml
ExecutionFinderLogGroup:
  Type: AWS::Logs::LogGroup
  DeletionPolicy: Retain
  UpdateReplacePolicy: Retain
  Properties:
    LogGroupName: !Sub '/aws/lambda/${ProjectName}-execution-finder'
    RetentionInDays: 30
```

---

## Part 2: api-stack.yaml (21 Issues)

### Issue Type Breakdown
- 19 hardcoded partition ARNs (I3042)
- 2 missing deletion/update policies (I3011)

### 2.1: Hardcoded Partition ARNs (19 fixes)

All API Gateway method integrations need the same fix pattern. Here's the pattern:

**Current Pattern (WRONG):**
```yaml
Uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ApiHandlerFunctionArn}/invocations'
```

**Fixed Pattern:**
```yaml
Uri: !Sub 'arn:${AWS::Partition}:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ApiHandlerFunctionArn}/invocations'
```

#### Affected Resources (Lines):
1. ProtectionGroupsGetMethod (373)
2. ProtectionGroupsPostMethod (392)
3. ProtectionGroupGetMethod (410)
4. ProtectionGroupPutMethod (429)
5. ProtectionGroupDeleteMethod (447)
6. DRSSourceServersGetMethod (594)
7. RecoveryPlansGetMethod (639)
8. RecoveryPlansPostMethod (658)
9. RecoveryPlanGetMethod (676)
10. RecoveryPlanPutMethod (695)
11. RecoveryPlanDeleteMethod (713)
12. RecoveryPlanExecuteMethod (731)
13. ExecutionsGetMethod (806)
14. ExecutionsPostMethod (825)
15. ExecutionGetMethod (843)
16. ExecutionCancelMethod (861)
17. ExecutionPauseMethod (879)
18. ExecutionResumeMethod (897)

#### Fix #19: ApiGatewayInvokePermission (Line 964)
**Current (WRONG):**
```yaml
SourceArn: !Sub 'arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${RestApi}/*'
```

**Fixed:**
```yaml
SourceArn: !Sub 'arn:${AWS::Partition}:execute-api:${AWS::Region}:${AWS::AccountId}:${RestApi}/*'
```

### 2.2: Missing Deletion/Update Policies (2 fixes)

#### Fix #20: UserPoolLogGroup (Line 64)
**Current (MISSING):**
```yaml
UserPoolLogGroup:
  Type: AWS::Logs::LogGroup
  Properties:
    LogGroupName: !Sub '/aws/cognito/userpools/${ProjectName}-users'
    RetentionInDays: 90
```

**Fixed:**
```yaml
UserPoolLogGroup:
  Type: AWS::Logs::LogGroup
  DeletionPolicy: Retain
  UpdateReplacePolicy: Retain
  Properties:
    LogGroupName: !Sub '/aws/cognito/userpools/${ProjectName}-users'
    RetentionInDays: 90
```

#### Fix #21: StateMachineLogGroup (Line 177)
**Current (MISSING):**
```yaml
StateMachineLogGroup:
  Type: AWS::Logs::LogGroup
  Properties:
    LogGroupName: !Sub '/aws/states/${ProjectName}-orchestration'
    RetentionInDays: 30
```

**Fixed:**
```yaml
StateMachineLogGroup:
  Type: AWS::Logs::LogGroup
  DeletionPolicy: Retain
  UpdateReplacePolicy: Retain
  Properties:
    LogGroupName: !Sub '/aws/states/${ProjectName}-orchestration'
    RetentionInDays: 30
```

---

## Part 3: database-stack.yaml (6 Issues)

### Issue Type Breakdown
- 6 missing deletion/update policies (I3011) on DynamoDB tables

### Critical Note About DynamoDB Tables
Unlike LogGroups (which should ALWAYS use `Retain`), DynamoDB tables are more situational:
- **Production**: Should use `Retain` to prevent accidental data loss
- **Development/Test**: Could use `Delete` for easier cleanup

**Recommendation**: Use `Retain` for all environments to be safe.

#### Fix #22-23: ProtectionGroupsTable (Line 15)
**Current (MISSING):**
```yaml
ProtectionGroupsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub '${ProjectName}-protection-groups'
    # ... rest of properties
```

**Fixed:**
```yaml
ProtectionGroupsTable:
  Type: AWS::DynamoDB::Table
  DeletionPolicy: Retain
  UpdateReplacePolicy: Retain
  Properties:
    TableName: !Sub '${ProjectName}-protection-groups'
    # ... rest of properties
```

#### Fix #24-25: RecoveryPlansTable (Line 37)
**Current (MISSING):**
```yaml
RecoveryPlansTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub '${ProjectName}-recovery-plans'
    # ... rest of properties
```

**Fixed:**
```yaml
RecoveryPlansTable:
  Type: AWS::DynamoDB::Table
  DeletionPolicy: Retain
  UpdateReplacePolicy: Retain
  Properties:
    TableName: !Sub '${ProjectName}-recovery-plans'
    # ... rest of properties
```

#### Fix #26-27: ExecutionHistoryTable (Line 59)
**Current (MISSING):**
```yaml
ExecutionHistoryTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub '${ProjectName}-execution-history'
    # ... rest of properties
```

**Fixed:**
```yaml
ExecutionHistoryTable:
  Type: AWS::DynamoDB::Table
  DeletionPolicy: Retain
  UpdateReplacePolicy: Retain
  Properties:
    TableName: !Sub '${ProjectName}-execution-history'
    # ... rest of properties
```

---

## Part 4: frontend-stack.yaml (1 Issue)

### Issue Type Breakdown
- 1 hardcoded partition ARN (I3042)

#### Fix #28: FrontendBucketPolicy (Line 139)
**Current (WRONG):**
```yaml
Statement:
  - Sid: AllowCloudFrontOAI
    Effect: Allow
    Principal:
      CanonicalUser: !GetAtt CloudFrontOAI.S3CanonicalUserId
    Action: s3:GetObject
    Resource: !Sub 'arn:aws:s3:::${FrontendBucket}/*'
```

**Fixed:**
```yaml
Statement:
  - Sid: AllowCloudFrontOAI
    Effect: Allow
    Principal:
      CanonicalUser: !GetAtt CloudFrontOAI.S3CanonicalUserId
    Action: s3:GetObject
    Resource: !Sub 'arn:${AWS::Partition}:s3:::${FrontendBucket}/*'
```

---

## Part 5: security-stack.yaml Clarification

### Why No Fixes Are Needed

**File Purpose**: Reference snippet for future Phase 2 security enhancements  
**Status**: NOT deployed, NOT causing problems  
**cfn-lint Errors**: 51 errors are **FALSE POSITIVES**

#### What security-stack.yaml Actually Is:
1. A **documentation file** containing security resource snippets
2. Designed to be **manually integrated** into master-template.yaml later
3. NOT a standalone CloudFormation template
4. Header explicitly states: "This file contains security resources to be integrated into master-template.yaml"

#### Why cfn-lint Reports Errors:
- cfn-lint validates it as a **standalone template**
- It references resources from other stacks (RestApi, DynamoDB tables, etc.)
- These references are **intentionally incomplete** - they're placeholders
- When integrated into master-template.yaml, these would be properly parameterized

#### What To Do:
- **Ignore the 51 cfn-lint errors** - they're expected for a snippet file
- **Keep the file as-is** - it's useful reference documentation
- **Don't validate it with cfn-lint** - it's not meant to be validated in isolation
- **IF implementing Phase 2 security**: Use it as a guide, not as a deployable template

---

## Part 6: Implementation Strategies

### Strategy A: Fix Everything Now (SAFEST)
**Best for**: Production environments, pre-deployment preparation

**Steps:**
1. Create feature branch: `git checkout -b fix/cloudformation-quality-issues`
2. Fix lambda-stack.yaml (12 issues)
3. Validate: `cfn-lint cfn/lambda-stack.yaml`
4. Commit: `git commit -m "fix(cfn): lambda-stack partition ARNs and deletion policies"`
5. Fix api-stack.yaml (21 issues)
6. Validate: `cfn-lint cfn/api-stack.yaml`
7. Commit: `git commit -m "fix(cfn): api-stack partition ARNs and deletion policies"`
8. Fix database-stack.yaml (6 issues)
9. Validate: `cfn-lint cfn/database-stack.yaml`
10. Commit: `git commit -m "fix(cfn): database-stack deletion policies"`
11. Fix frontend-stack.yaml (1 issue)
12. Validate: `cfn-lint cfn/frontend-stack.yaml`
13. Commit: `git commit -m "fix(cfn): frontend-stack partition ARN"`
14. Final validation: `cfn-lint cfn/*.yaml`
15. Merge to main: `git checkout main && git merge fix/cloudformation-quality-issues`
16. Push: `git push origin main`

**Pros:**
- ✅ All issues fixed before any new deployments
- ✅ Clean commit history with logical grouping
- ✅ Easy to revert if needed

**Cons:**
- ⏱️ Takes more time before continuing Phase 2
- ⏸️ Blocks Phase 2 progress temporarily

### Strategy B: Fix Incrementally (PRAGMATIC)
**Best for**: Active development with periodic deployments

**Approach**: Fix one template at a time as you work with it

**Example Workflow:**
1. Working on lambda-stack.yaml for Phase 2? → Fix its 12 issues first
2. Deploy and test
3. Later, when touching api-stack.yaml → Fix its 21 issues
4. Continue pattern for remaining templates

**Pros:**
- ✅ Doesn't block Phase 2 work
- ✅ Fixes are tested alongside feature changes
- ✅ Spread out work over time

**Cons:**
- ⚠️ Some templates remain with issues longer
- ⚠️ Need to remember to fix each template
- ⚠️ More complex commit history

### Strategy C: Document and Defer (FASTEST)
**Best for**: Pre-production prototyping, rapid iteration

**Steps:**
1. Add `.cfnlintrc.yaml` rules to suppress non-critical warnings
2. Document all issues in this file
3. Continue Phase 2 work
4. Schedule dedicated "CloudFormation cleanup" session later

**Pros:**
- ✅ Continue Phase 2 immediately
- ✅ No context switching
- ✅ Batch all fixes together later

**Cons:**
- ❌ Issues remain in production templates
- ❌ Risk of forgetting to fix later
- ❌ Deployment to GovCloud/China won't work

### **Recommended Strategy**

For your situation (Phase 2 active development with deployed Phase 1):

**Hybrid Approach:**
1. **Fix lambda-stack.yaml NOW** (12 issues) - You're actively modifying it for Phase 2
2. **Document the rest** - Add to technical debt backlog
3. **Fix before production deployment** - Make it a pre-deployment checklist item

This balances progress with quality without blocking Phase 2 work.

---

## Part 7: Validation Procedures

### Pre-Fix Validation
```bash
# Baseline - capture current state
cfn-lint cfn/*.yaml --format parseable > cfn-lint-before.txt
```

### During Fix Validation
```bash
# After fixing each template
cfn-lint cfn/lambda-stack.yaml    # Should show 0 errors in fixed sections
cfn-lint cfn/api-stack.yaml
cfn-lint cfn/database-stack.yaml
cfn-lint cfn/frontend-stack.yaml
```

### Post-Fix Validation
```bash
# All templates should pass
cfn-lint cfn/*.yaml --format parseable > cfn-lint-after.txt

# Compare before/after
diff cfn-lint-before.txt cfn-lint-after.txt
```

### AWS CloudFormation Validation
```bash
# Validate syntax with AWS (requires AWS CLI)
aws cloudformation validate-template --template-body file://cfn/lambda-stack.yaml
aws cloudformation validate-template --template-body file://cfn/api-stack.yaml
aws cloudformation validate-template --template-body file://cfn/database-stack.yaml
aws cloudformation validate-template --template-body file://cfn/frontend-stack.yaml
```

### Deployment Test (Safest Approach)
```bash
# Create change set to see what would change
aws cloudformation create-change-set \
  --stack-name drs-orchestration-test \
  --template-body file://cfn/master-template.yaml \
  --parameters file://params-test.json \
  --change-set-name quality-fixes \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

# Review change set
aws cloudformation describe-change-set \
  --stack-name drs-orchestration-test \
  --change-set-name quality-fixes

# If changes look good, execute
aws cloudformation execute-change-set \
  --stack-name drs-orchestration-test \
  --change-set-name quality-fixes
```

---

## Part 8: Rollback Procedures

### Git Rollback
```bash
# If issues discovered after commit
git revert <commit-hash>
git push origin main

# Or rollback multiple commits
git reset --hard <commit-before-fixes>
git push origin main --force  # Use with caution
```

### CloudFormation Rollback
```bash
# CloudFormation automatic rollback on failure
# (Enabled by default during stack update)

# Manual rollback to previous version
aws cloudformation update-stack \
  --stack-name drs-orchestration-prod \
  --template-url s3://deployment-bucket/cfn/master-template.yaml.backup \
  --parameters file://params-prod.json \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

### Emergency Rollback
If stack update fails and causes service disruption:

1. **Check stack events**:
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name drs-orchestration-prod \
     --max-items 50
   ```

2. **Identify failed resource**

3. **Manual fix if needed**:
   - Fix via AWS Console
   - Then update CloudFormation to match

4. **Prevent future drift**:
   ```bash
   aws cloudformation detect-stack-drift \
     --stack-name drs-orchestration-prod
   ```

---

## Impact Analysis

### Current State (With Issues)
- ❌ **Cannot deploy to AWS GovCloud** (uses aws-us-gov partition)
- ❌ **Cannot deploy to AWS China** (uses aws-cn partition)
- ❌ **Risk of data loss** on stack updates (10 resources)
- ⚠️ **Compliance concerns** (no retention guarantees for logs/data)

### After Fixes
- ✅ **Multi-partition support** (standard + GovCloud + China)
- ✅ **Data protection** (logs and tables retained)
- ✅ **Compliance ready** (explicit retention policies)
- ✅ **Production-grade** (follows AWS best practices)

### Benefits
1. **Portability**: Deploy anywhere in AWS ecosystem
2. **Safety**: No accidental data loss
3. **Compliance**: Meets audit requirements
4. **Maintainability**: Easier to understand resource lifecycle
5. **Best Practices**: Aligns with AWS Well-Architected Framework

---

## Appendix A: Quick Reference

### Issue Count by Template
| Template | Partition ARNs | Deletion Policies | Total | Status |
|----------|----------------|-------------------|-------|--------|
| lambda-stack.yaml | 10 | 4 | 14 | ✅ COMPLETE |
| api-stack.yaml | 19 | 2 | 21 | ⏳ Deferred |
| database-stack.yaml | 0 | 6 | 6 | ⏳ Deferred |
| frontend-stack.yaml | 1 | 0 | 1 | ⏳ Deferred |
| **TOTAL** | **28** | **10** | **38** | **14/38 (37%)** |

### Fix Pattern Quick Reference

**Hardcoded Partition Fix:**
```yaml
# Before: arn:aws:service:region:account:resource
# After:  !Sub 'arn:${AWS::Partition}:service:region:account:resource'
```

**Deletion Policy Fix:**
```yaml
# Add to resource:
DeletionPolicy: Retain
UpdateReplacePolicy: Retain
```

### Validation Commands
```bash
# Quick validation
cfn-lint cfn/*.yaml

# Detailed validation
cfn-lint cfn/*.yaml --format parseable

# AWS validation
aws cloudformation validate-template --template-body file://cfn/template.yaml
```

---

## Appendix B: Related Documentation

- [AWS CloudFormation Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)
- [AWS Partitions](https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html#genref-aws-service-namespaces)
- [DeletionPolicy Attribute](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-attribute-deletionpolicy.html)
- [cfn-lint Rules Reference](https://github.com/aws-cloudformation/cfn-lint/blob/main/docs/rules.md)

---

## Summary

**Total Issues**: 38 real issues + 51 false positives  
**Priority**: Medium (blocks GovCloud/China, data loss risk)  
**Effort**: 2-4 hours for all fixes  
**Risk**: Low (purely additive changes, no logic changes)  

**Next Steps**:
1. Choose implementation strategy
2. Fix templates systematically
3. Validate thoroughly
4. Test deployment
5. Continue Phase 2 work

---

**Document Status**: Partially Complete - lambda-stack.yaml fixed (14/38 issues), 26 deferred  
**Last Updated**: November 28, 2025 1:01 PM EST
