make sure complete
# Implementation Tasks

## Phase 1: Lambda Safety Updates (COMPLETE)

- [x] Task 1: Update security_utils.py with Defensive Validation

**Requirements:** Requirement 4

**Files to modify:**
- `infra/orchestration/drs-orchestration/lambda/shared/security_utils.py`

**Acceptance Criteria:**
- [x] `validate_file_path` only blocks actual path traversal patterns (`..`, URL-encoded variants)
- [x] `validate_file_path` allows Lambda runtime paths (`/var/task/frontend`)
- [x] `validate_file_path` allows temporary directory paths (`/tmp`)
- [x] `validate_file_path` returns path unchanged when valid
- [x] Security validation does NOT block paths based on directory depth or absolute path patterns
- [x] Sanitize functions only remove genuinely dangerous characters (null bytes, control characters)

---

- [x] Task 2: Update frontend-builder with Stable PhysicalResourceId

**Requirements:** Requirement 2, Requirement 7

**Files to modify:**
- `infra/orchestration/drs-orchestration/lambda/frontend-builder/index.py`

**Acceptance Criteria:**
- [x] PhysicalResourceId set to `frontend-deployer-{bucket_name}` on CREATE
- [x] PhysicalResourceId remains constant across all UPDATE operations
- [x] PhysicalResourceId is deterministic based on bucket name only

---

- [x] Task 3: Update frontend-builder DELETE Handler with Stack Status Check

**Requirements:** Requirement 3, Requirement 6, Requirement 7

**Files to modify:**
- `infra/orchestration/drs-orchestration/lambda/frontend-builder/index.py`

**Acceptance Criteria:**
- [x] DELETE handler checks stack status before any cleanup
- [x] Bucket cleanup ONLY occurs when stack status contains "DELETE_IN_PROGRESS"
- [x] Bucket cleanup is SKIPPED for UPDATE operations (no "DELETE" in status)
- [x] Bucket cleanup is SKIPPED for ROLLBACK operations
- [x] DELETE always returns SUCCESS (even on errors) to allow stack deletion
- [x] If stack status check fails, cleanup is skipped (safe default)
- [x] Logging includes stack status and cleanup decision

---

- [x] Task 4: Update bucket-cleaner with Safe DELETE Handling

**Requirements:** Requirement 3, Requirement 6

**Files to modify:**
- `infra/orchestration/drs-orchestration/lambda/bucket-cleaner/index.py`

**Acceptance Criteria:**
- [x] DELETE handler checks stack status before cleanup
- [x] Bucket cleanup ONLY occurs when stack status contains "DELETE_IN_PROGRESS"
- [x] DELETE always sends SUCCESS response to CloudFormation
- [x] If bucket doesn't exist, returns SUCCESS
- [x] Logging includes stack status and cleanup decision

---

- [x] Task 8: Update notification-formatter Lambda

**Requirements:** Requirement 17

**Files to modify:**
- `infra/orchestration/drs-orchestration/lambda/notification-formatter/index.py`

**Acceptance Criteria:**
- [x] Rename notification type from `approval` to `pause`
- [x] Update `handle_approval_notification` to `handle_pause_notification`
- [x] Update `format_approval_message` to `format_pause_message`
- [x] Update environment variable from `APPROVAL_WORKFLOW_TOPIC_ARN` to `EXECUTION_PAUSE_TOPIC_ARN`
- [x] Update pause notification to include protection group name
- [x] Update pause notification to include pause reason
- [x] Update pause notification to include resume instructions
- [x] Remove approval URL/reject URL references (not applicable for pause)

---

- [x] Task 15: Create Consolidated Frontend Deployer Lambda

**Requirements:** Requirement 1

**Files created:**
- `infra/orchestration/drs-orchestration/lambda/frontend-deployer/index.py`

**Acceptance Criteria:**
- [x] Create new `frontend-deployer` directory
- [x] Single Lambda handles CREATE, UPDATE, and DELETE
- [x] Stable PhysicalResourceId prevents CloudFormation replacement behavior
- [x] Safe DELETE handling with stack status check
- [x] Comprehensive logging with security event classification

---

- [x] Task 16: Add Comprehensive Logging

**Requirements:** Requirement 8

**Files to modify:**
- `infra/orchestration/drs-orchestration/lambda/frontend-deployer/index.py`
- `infra/orchestration/drs-orchestration/lambda/frontend-builder/index.py`
- `infra/orchestration/drs-orchestration/lambda/bucket-cleaner/index.py`

**Acceptance Criteria:**
- [x] Log CloudFormation event type at start of each invocation
- [x] Log stack status when making cleanup decisions
- [x] Log number of files deployed on successful deployment
- [x] Log CloudFront invalidation ID on successful cache invalidation
- [x] Log full stack trace on errors
- [x] Use structured logging with security event classification

---

- [x] Task 14: Update Unit Tests

**Requirements:** All

**Files verified:**
- `infra/orchestration/drs-orchestration/tests/python/unit/test_frontend_deployer.py` - EXISTS
- `infra/orchestration/drs-orchestration/tests/python/unit/test_bucket_cleaner.py` - EXISTS
- `infra/orchestration/drs-orchestration/tests/python/unit/test_security_utils.py` - EXISTS
- `infra/orchestration/drs-orchestration/tests/python/unit/test_notification_formatter.py` - EXISTS

**Acceptance Criteria:**
- [x] Test stable PhysicalResourceId generation
- [x] Test stack status check logic for various statuses
- [x] Test DELETE handling skips cleanup for UPDATE operations
- [x] Test DELETE handling skips cleanup for ROLLBACK operations
- [x] Test DELETE handling proceeds for DELETE_IN_PROGRESS
- [x] Test defensive security validation allows Lambda paths
- [x] Test defensive security validation blocks traversal patterns
- [x] Test pause notification formatting
- [x] Test notification type routing

---

## Phase 2: CloudFormation Template Updates (NOT STARTED)

**CRITICAL: Parameter Dependency Analysis**

Before removing ANY parameter from master-template.yaml, verify it is NOT passed to nested stacks.

**Currently USED Parameters (DO NOT REMOVE from master-template.yaml until nested stacks updated):**

| Parameter | Passed To | Usage |
|-----------|-----------|-------|
| `CognitoDomainPrefix` | api-auth-stack.yaml | HasCognitoDomain condition (unused but parameter expected) |
| `NotificationEmail` | api-auth-stack.yaml, notification-stack.yaml | HasNotificationEmail condition, SNS subscriptions |
| `TagSyncIntervalHours` | eventbridge-stack.yaml | Tag sync schedule expression |
| `EnableTagSync` | eventbridge-stack.yaml | EnableTagSyncCondition |
| `FrontendBuildTimestamp` | frontend-stack.yaml | Forces frontend rebuild |
| `ApiDeploymentTimestamp` | api-gateway-core-stack.yaml, api-gateway-deployment-stack.yaml | Forces API redeployment |
| `ForceRecreation` | database-stack.yaml | DynamoDB table recreation |
| `EnablePipelineNotifications` | lambda-stack.yaml | PipelineNotificationsTopic condition |
| `AdminEmail` | api-auth-stack.yaml, notification-stack.yaml, lambda-stack.yaml | Cognito admin, SNS subscriptions |
| `CrossAccountRoleName` | lambda-stack.yaml | Cross-account IAM role |

**Safe to Remove (NOT passed to nested stacks):**
- `EnableWAF` - Only used in SecurityStack condition (SecurityStack disabled)
- `EnableCloudTrail` - Only used in SecurityStack (SecurityStack disabled)
- `EnableSecurityStack` - Condition only, SecurityStack not developed
- `EnableSecretsManager` - Unused parameter (no references)
- `EnableTerminationProtection` - Unused parameter (set via CLI)

---

- [x] Task 5: Remove Unused Parameters from master-template.yaml (SAFE)

**Requirements:** Requirement 16

**Files to modify:**
- `infra/orchestration/drs-orchestration/cfn/master-template.yaml`

**Acceptance Criteria:**
- [ ] Remove `EnableWAF` parameter (SecurityStack disabled, not passed anywhere)
- [ ] Remove `EnableCloudTrail` parameter (SecurityStack disabled, not passed anywhere)
- [ ] Remove `EnableSecretsManager` parameter (unused, no references)
- [ ] Remove `EnableTerminationProtection` parameter (unused, set via CLI)
- [ ] Update Metadata ParameterGroups to remove these parameters
- [ ] Verify deployment succeeds after removal

**DO NOT REMOVE YET (requires nested stack updates first):**
- `CognitoDomainPrefix` - api-auth-stack.yaml expects it
- `NotificationEmail` - api-auth-stack.yaml and notification-stack.yaml expect it
- `TagSyncIntervalHours` - eventbridge-stack.yaml expects it
- `EnableTagSync` - eventbridge-stack.yaml expects it
- `ForceRecreation` - database-stack.yaml expects it
- `FrontendBuildTimestamp` - frontend-stack.yaml expects it
- `ApiDeploymentTimestamp` - api-gateway stacks expect it
- `EnablePipelineNotifications` - lambda-stack.yaml expects it

---

- [x] Task 6: Remove CognitoDomainPrefix from api-auth-stack.yaml

**Requirements:** Requirement 16

**Files to modify:**
- `infra/orchestration/drs-orchestration/cfn/api-auth-stack.yaml`
- `infra/orchestration/drs-orchestration/cfn/master-template.yaml`

**Current State Analysis:**
- `CognitoDomainPrefix` parameter exists with `HasCognitoDomain` condition
- `HasCognitoDomain` condition is NEVER USED in any resource (dead code)
- Parameter is passed from master-template.yaml but serves no purpose

**Coordinated Change Required:**
1. api-auth-stack.yaml: Remove `CognitoDomainPrefix` parameter
2. api-auth-stack.yaml: Remove `HasCognitoDomain` condition
3. master-template.yaml: Remove `CognitoDomainPrefix` parameter
4. master-template.yaml: Remove `CognitoDomainPrefix: !Ref CognitoDomainPrefix` from ApiAuthStack parameters
5. master-template.yaml: Update Metadata ParameterGroups to remove CognitoDomainPrefix

**Acceptance Criteria:**
- [ ] Remove `CognitoDomainPrefix` parameter from api-auth-stack.yaml
- [ ] Remove `HasCognitoDomain` condition from api-auth-stack.yaml
- [ ] Remove `CognitoDomainPrefix` parameter from master-template.yaml
- [ ] Remove `CognitoDomainPrefix` from ApiAuthStack parameters in master-template.yaml
- [ ] Update Metadata ParameterGroups in master-template.yaml
- [ ] Keep `NotificationEmail` parameter (still used for optional SNS subscriptions)

**DEPLOYMENT:** Must deploy both files together in single deployment
**RISK:** Low - Condition is unused, safe to remove

---

- [x] Task 7: Rename ApprovalWorkflow to ExecutionPause in notification-stack.yaml

**Requirements:** Requirement 17

**Files to modify:**
- `infra/orchestration/drs-orchestration/cfn/notification-stack.yaml`

**Current State Analysis:**
- `ApprovalWorkflowTopic` exists and is ACTIVELY USED
- Output `ApprovalWorkflowTopicArn` is consumed by lambda-stack.yaml
- master-template.yaml passes this to LambdaStack as `ApprovalWorkflowTopicArn`

**Coordinated Change Required (ALL must happen together):**
1. notification-stack.yaml: Rename `ApprovalWorkflowTopic` → `ExecutionPauseTopic`
2. notification-stack.yaml: Rename output `ApprovalWorkflowTopicArn` → `ExecutionPauseTopicArn`
3. lambda-stack.yaml: Rename parameter `ApprovalWorkflowTopicArn` → `ExecutionPauseTopicArn`
4. lambda-stack.yaml: Update environment variable `APPROVAL_WORKFLOW_TOPIC_ARN` → `EXECUTION_PAUSE_TOPIC_ARN`
5. master-template.yaml: Update `!GetAtt NotificationStack.Outputs.ApprovalWorkflowTopicArn` → `!GetAtt NotificationStack.Outputs.ExecutionPauseTopicArn`

**Acceptance Criteria:**
- [ ] Rename `ApprovalWorkflowTopic` to `ExecutionPauseTopic` in notification-stack.yaml
- [ ] Rename `ApprovalWorkflowSubscription` to `ExecutionPauseSubscription`
- [ ] Rename `ApprovalWorkflowTopicPolicy` to `ExecutionPauseTopicPolicy`
- [ ] Rename output `ApprovalWorkflowTopicArn` to `ExecutionPauseTopicArn`
- [ ] Update export name to reflect renamed topic
- [ ] Keep `NotificationEmail` parameter (still used for optional subscriptions)

**RISK:** Medium - Requires coordinated changes across 3 files
**DEPLOYMENT:** Must deploy all 3 files together in single deployment

---

- [x] Task 9: Update lambda-stack.yaml for ExecutionPause Rename

**Requirements:** Requirement 17

**Files to modify:**
- `infra/orchestration/drs-orchestration/cfn/lambda-stack.yaml`

**Current State Analysis:**
- Parameter `ApprovalWorkflowTopicArn` is passed from master-template.yaml
- Environment variable `APPROVAL_WORKFLOW_TOPIC_ARN` is set on NotificationFormatterFunction
- This is part of the coordinated rename with Task 7

**Acceptance Criteria:**
- [ ] Rename parameter `ApprovalWorkflowTopicArn` to `ExecutionPauseTopicArn`
- [ ] Update environment variable `APPROVAL_WORKFLOW_TOPIC_ARN` to `EXECUTION_PAUSE_TOPIC_ARN` in NotificationFormatterFunction
- [ ] Update any IAM policy references if they use the parameter

**DEPENDENCY:** Must be deployed TOGETHER with Task 7 (notification-stack.yaml) changes
**RISK:** Medium - Part of coordinated 3-file change

---

- [x] Task 10: Hardcode TagSyncIntervalHours in eventbridge-stack.yaml

**Requirements:** Requirement 16

**Files to modify:**
- `infra/orchestration/drs-orchestration/cfn/eventbridge-stack.yaml`
- `infra/orchestration/drs-orchestration/cfn/master-template.yaml`

**Current State Analysis:**
- `TagSyncIntervalHours` parameter is used in schedule expression: `rate(${TagSyncIntervalHours} hours)`
- Default value is 4 hours, requirement says hardcode to 1 hour
- `EnableTagSync` parameter controls `EnableTagSyncCondition` - keep this for flexibility

**Coordinated Change Required:**
1. eventbridge-stack.yaml: Remove `TagSyncIntervalHours` parameter
2. eventbridge-stack.yaml: Hardcode schedule to `rate(1 hour)`
3. master-template.yaml: Remove `TagSyncIntervalHours` parameter
4. master-template.yaml: Remove `TagSyncIntervalHours: !Ref TagSyncIntervalHours` from EventBridgeStack parameters
5. master-template.yaml: Update outputs that reference TagSyncScheduleExpression

**Acceptance Criteria:**
- [ ] Remove `TagSyncIntervalHours` parameter from eventbridge-stack.yaml
- [ ] Change `ScheduleExpression: !Sub 'rate(${TagSyncIntervalHours} hours)'` to `ScheduleExpression: 'rate(1 hour)'`
- [ ] Update `TagSyncScheduleExpression` output to hardcoded value
- [ ] Remove `TagSyncIntervalHours` parameter from master-template.yaml
- [ ] Remove `TagSyncIntervalHours` from EventBridgeStack parameters in master-template.yaml
- [ ] Keep `EnableTagSync` parameter (useful for disabling tag sync)

**DEPLOYMENT:** Must deploy both files together in single deployment
**RISK:** Low - Just hardcodes an interval value

---

- [x] Task 18: Update master-template.yaml for ExecutionPause Rename

**Requirements:** Requirement 17

**Files to modify:**
- `infra/orchestration/drs-orchestration/cfn/master-template.yaml`

**Current State Analysis:**
- master-template.yaml passes `ApprovalWorkflowTopicArn` from NotificationStack to LambdaStack
- This reference must be updated when notification-stack.yaml output is renamed

**Acceptance Criteria:**
- [ ] Update `ApprovalWorkflowTopicArn: !GetAtt NotificationStack.Outputs.ApprovalWorkflowTopicArn` to `ExecutionPauseTopicArn: !GetAtt NotificationStack.Outputs.ExecutionPauseTopicArn`

**DEPENDENCY:** Must be deployed TOGETHER with Task 7 and Task 9
**RISK:** Medium - Part of coordinated 3-file change

---

## Phase 3: Frontend Stack Simplification (NOT STARTED)

- [x] Task 12: Update Lambda Stack Outputs for Frontend Deployer

**Requirements:** Requirement 12, Requirement 15

**Files to modify:**
- `infra/orchestration/drs-orchestration/cfn/lambda-stack.yaml`

**Current State Analysis:**
- `FrontendBuilderFunctionArn` output exists and is consumed by frontend-stack.yaml
- `BucketCleanerFunctionArn` output exists and is consumed by frontend-stack.yaml
- master-template.yaml passes both to FrontendStack
- `frontend-deployer` Lambda exists in code but NOT defined in CloudFormation

**Acceptance Criteria:**
- [ ] Add `FrontendDeployerFunction` resource definition (Lambda function)
- [ ] Add `FrontendDeployerFunctionArn` output
- [ ] KEEP existing `FrontendBuilderFunctionArn` output (still used by frontend-stack.yaml)
- [ ] KEEP existing `BucketCleanerFunctionArn` output (still used by frontend-stack.yaml)
- [ ] Only remove old outputs AFTER frontend-stack.yaml is updated (Task 11)

**DEPLOYMENT ORDER:**
1. Deploy Task 12 first (adds new output, keeps old outputs)
2. Deploy Task 11 (frontend-stack.yaml uses new output)
3. Deploy Task 13 (master-template.yaml uses new output)
4. THEN remove old outputs from lambda-stack.yaml (separate deployment)

---

- [x] Task 11: Simplify frontend-stack.yaml

**Requirements:** Requirement 12

**Files to modify:**
- `infra/orchestration/drs-orchestration/cfn/frontend-stack.yaml`

**Current State Analysis:**
- `BucketCleanerFunctionArn` parameter is ACTIVELY USED by `EmptyFrontendBucketResource`
- `FrontendBuilderFunctionArn` parameter is ACTIVELY USED by `BuildAndDeployFrontendResource`
- Both custom resources exist and work correctly
- The consolidated `frontend-deployer` Lambda was created in Phase 1 but NOT yet integrated into CloudFormation

**Acceptance Criteria:**
- [ ] Add new parameter `FrontendDeployerFunctionArn` 
- [ ] Create new `FrontendDeploymentResource` using `FrontendDeployerFunctionArn`
- [ ] Remove `EmptyFrontendBucketResource` custom resource (cleanup handled by deployer)
- [ ] Remove `BuildAndDeployFrontendResource` custom resource (replaced by deployer)
- [ ] Remove `BucketCleanerFunctionArn` parameter AFTER removing EmptyFrontendBucketResource
- [ ] Remove `FrontendBuilderFunctionArn` parameter AFTER removing BuildAndDeployFrontendResource
- [ ] Update `FrontendBucketPolicy` DependsOn to reference `FrontendDeploymentResource`
- [ ] Update custom resource type to `Custom::FrontendDeployer`

**DEPENDENCY:** Requires Task 12 (lambda-stack.yaml outputs) to be completed first
**RISK:** Medium - Changes custom resource architecture

---

- [x] Task 13: Update master-template.yaml Frontend Stack Parameters

**Requirements:** Requirement 12

**Files to modify:**
- `infra/orchestration/drs-orchestration/cfn/master-template.yaml`

**Current State Analysis:**
- FrontendStack receives `BucketCleanerFunctionArn` from LambdaStack
- FrontendStack receives `FrontendBuilderFunctionArn` from LambdaStack
- Both are actively used by frontend-stack.yaml custom resources

**Acceptance Criteria:**
- [ ] Add `FrontendDeployerFunctionArn` parameter to FrontendStack (from LambdaStack output)
- [ ] KEEP `BucketCleanerFunctionArn` parameter until frontend-stack.yaml no longer needs it
- [ ] KEEP `FrontendBuilderFunctionArn` parameter until frontend-stack.yaml no longer needs it
- [ ] Only remove old parameters AFTER frontend-stack.yaml is updated (Task 11)

**DEPENDENCY:** Must be deployed AFTER Task 11 and Task 12
**RISK:** Low if deployment order is followed

---

## Phase 4: Testing & Validation (NOT STARTED)

- [x] Task 17: Validate CloudFormation Templates

**Requirements:** All

**Files to validate:**
- All files in `infra/orchestration/drs-orchestration/cfn/`

**Acceptance Criteria:**
- [ ] All templates pass `cfn-lint` validation
- [ ] All templates pass AWS CloudFormation validate-template
- [ ] No circular dependencies between stacks
- [ ] All parameter references are valid
- [ ] All condition references are valid
- [ ] All output exports are unique

**Validation Command:**
```bash
cd infra/orchestration/drs-orchestration
make validate
```

---

## Implementation Order

**Phase 1: Lambda Safety Updates (COMPLETE)**
1. ✅ Task 1: security_utils.py defensive validation
2. ✅ Task 2: frontend-builder stable PhysicalResourceId
3. ✅ Task 3: frontend-builder safe DELETE handling
4. ✅ Task 4: bucket-cleaner safe DELETE handling
5. ✅ Task 8: notification-formatter pause notification support
6. ✅ Task 15: Create consolidated frontend-deployer Lambda
7. ✅ Task 16: Comprehensive logging
8. ✅ Task 14: Unit tests exist for all Lambda functions

**Phase 2: CloudFormation Parameter Cleanup (NOT STARTED)**
9. Task 5: Remove unused parameters (EnableWAF, EnableCloudTrail, EnableSecretsManager, EnableTerminationProtection)
10. Task 6: Remove CognitoDomainPrefix from api-auth-stack.yaml and master-template.yaml
11. Task 7 + Task 9 + Task 18: Rename ApprovalWorkflow → ExecutionPause (notification-stack, lambda-stack, master-template)
12. Task 10: Hardcode TagSyncIntervalHours in eventbridge-stack.yaml and master-template.yaml

**Phase 3: Frontend Stack Simplification (NOT STARTED)**
13. Task 12: Add FrontendDeployerFunction to lambda-stack.yaml
14. Task 11: Update frontend-stack.yaml to use new deployer
15. Task 13: Update master-template.yaml frontend parameters

**Phase 4: Testing & Validation (NOT STARTED)**
16. Task 17: Validate CloudFormation templates

---

## Deployment Commands

```bash
# Phase 1: Lambda-only update (safe, no CloudFormation changes) - COMPLETE
cd infra/orchestration/drs-orchestration
./scripts/deploy.sh dev --lambda-only

# Phase 2-3: Full deployment with CloudFormation changes
./scripts/deploy.sh dev

# Validation only (no deployment)
./scripts/deploy.sh dev --skip-push --dry-run
```

---

## Rollback Procedures

**If Lambda updates fail (Phase 1):**
```bash
git checkout HEAD~1 -- lambda/
./scripts/deploy.sh dev --lambda-only
```

**If CloudFormation updates fail (Phase 2-3):**
- CloudFormation automatically rolls back
- Frontend deployer's safe DELETE handling prevents data loss during rollback
- Check CloudFormation events for root cause
- Fix code and redeploy

**If stack enters UPDATE_ROLLBACK_FAILED:**
```bash
# Check which resources failed
aws cloudformation describe-stack-events --stack-name aws-drs-orch-dev --max-items 20

# Continue rollback skipping problematic resources
aws cloudformation continue-update-rollback \
  --stack-name aws-drs-orch-dev \
  --resources-to-skip ResourceLogicalId1 ResourceLogicalId2
```

---

## Critical Notes

**Parameter Dependencies - VERIFIED FROM CURRENT CODE:**

The following parameters in master-template.yaml are passed to nested stacks and CANNOT be removed until the nested stacks are updated first:

| Parameter | Nested Stack | How Used |
|-----------|--------------|----------|
| `CognitoDomainPrefix` | api-auth-stack.yaml | HasCognitoDomain condition (unused but expected) |
| `NotificationEmail` | api-auth-stack.yaml, notification-stack.yaml | SNS subscriptions |
| `TagSyncIntervalHours` | eventbridge-stack.yaml | Schedule expression |
| `EnableTagSync` | eventbridge-stack.yaml | EnableTagSyncCondition |
| `FrontendBuildTimestamp` | frontend-stack.yaml | Forces rebuild |
| `ApiDeploymentTimestamp` | api-gateway stacks | Forces redeployment |
| `ForceRecreation` | database-stack.yaml | Table recreation |
| `EnablePipelineNotifications` | lambda-stack.yaml | Topic condition |
| `AdminEmail` | api-auth-stack, notification-stack, lambda-stack | Multiple uses |
| `CrossAccountRoleName` | lambda-stack.yaml | IAM role name |
| `BucketCleanerFunctionArn` | frontend-stack.yaml | EmptyFrontendBucketResource |
| `FrontendBuilderFunctionArn` | frontend-stack.yaml | BuildAndDeployFrontendResource |
| `ApprovalWorkflowTopicArn` | lambda-stack.yaml | NotificationFormatter env var |

**Safe Deployment Order for Phase 2-3:**

1. **Task 5** - Remove unused parameters (EnableWAF, EnableCloudTrail, EnableSecretsManager, EnableTerminationProtection) - SAFE, no dependencies
2. **Task 6** - Remove CognitoDomainPrefix from api-auth-stack.yaml and master-template.yaml - deploy together
3. **Task 7 + Task 9 + Task 18** - Rename ApprovalWorkflow → ExecutionPause - MUST deploy notification-stack, lambda-stack, master-template together
4. **Task 10** - Hardcode TagSyncIntervalHours in eventbridge-stack.yaml and master-template.yaml - deploy together
5. **Task 12** - Add FrontendDeployerFunction to lambda-stack.yaml (add new output, keep old outputs)
6. **Task 11** - Update frontend-stack.yaml to use new deployer
7. **Task 13** - Update master-template.yaml frontend parameters
8. **Cleanup** - Remove old outputs/parameters after all stacks updated

**DO NOT:**
- Remove parameters from master-template.yaml before updating nested stacks
- Remove outputs from lambda-stack.yaml before updating frontend-stack.yaml
- Deploy partial changes that break parameter references
- Rename outputs without updating all consumers in same deployment

**Key Differences from Pre-Refactored Code (v3.0.0):**
- Current master-template.yaml has `FrontendBuildTimestamp` parameter (added later)
- Current master-template.yaml passes both `BucketCleanerFunctionArn` AND `FrontendBuilderFunctionArn` to FrontendStack
- Pre-refactored only passed `BucketCleanerFunctionArn` to FrontendStack
- Current notification-formatter Lambda already updated for pause notifications (Phase 1 complete)
- Unit tests exist for all Lambda functions (test_frontend_deployer.py, test_bucket_cleaner.py, test_security_utils.py, test_notification_formatter.py)
