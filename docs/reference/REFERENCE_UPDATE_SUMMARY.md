# Reference Directory Update Summary

**Date**: January 26, 2026  
**Updated Files**: 3  
**Status**: Complete

## Updates Completed

### 1. API_ENDPOINTS_CURRENT.md
**Changes Made**:
- Added Lambda Handler Architecture section explaining 3-handler split
- Added handler annotations to all endpoint categories
- Marked unimplemented endpoint (`/recovery-plans/{id}/check-existing-instances`) with 501 status
- Updated overview to explain handler responsibilities

**Key Additions**:
```markdown
## Lambda Handler Architecture

### 1. Data Management Handler
**Function**: `data-management-handler`
**Endpoints**: Protection Groups, Recovery Plans, Target Accounts, Tag Sync

### 2. Execution Handler
**Function**: `execution-handler`
**Endpoints**: Executions, pause/resume, termination, DRS operations

### 3. Query Handler
**Function**: `query-handler`
**Endpoints**: DRS Integration, EC2 Resources, Configuration Export
```

### 2. DRS_IAM_AND_PERMISSIONS_REFERENCE.md
**Changes Made**:
- Added Lambda Handler Architecture section at the beginning
- Updated all Lambda function name references from old names to current names
- Kept all IAM policy content (verified accurate against CloudFormation)

**Function Name Updates**:
- ~~ApiHandler~~ → `data-management-handler`, `execution-handler`, `query-handler`
- ~~CustomResource~~ → `frontend-deployer`
- ~~BucketCleaner~~ → `frontend-deployer`
- ~~ExecutionFinder~~ → `execution-handler`
- ~~ExecutionPoller~~ → `execution-handler`, `orch-sf`
- ~~NotificationFormatter~~ → `notification-formatter`
- ~~Orchestration~~ → `orch-sf`

### 3. ORCHESTRATION_ROLE_SPECIFICATION.md
**Changes Made**:
- Added Lambda Handler Architecture section explaining 6 functions
- Updated all 16 "Used by" annotations with correct handler names
- Kept all IAM policy specifications (verified accurate against CloudFormation)

**Updated "Used by" Annotations** (16 policies):
1. DynamoDB Access: `data-management-handler`, `execution-handler`, `query-handler`, `orch-sf`
2. Step Functions Access: `execution-handler`
3. DRS Read Access: `query-handler`, `execution-handler`, `orch-sf`
4. DRS Write Access: `execution-handler`, `orch-sf`
5. EC2 Access: `execution-handler`, `query-handler`, `orch-sf`
6. IAM Access: `execution-handler`, `orch-sf`
7. STS Access: `execution-handler`, `query-handler`, `orch-sf`
8. KMS Access: `execution-handler`, `orch-sf`
9. CloudFormation Access: `frontend-deployer`
10. S3 Access: `frontend-deployer`
11. CloudFront Access: `frontend-deployer`
12. Lambda Invoke Access: `execution-handler`, `data-management-handler`
13. EventBridge Access: `data-management-handler`
14. SSM Access: `orch-sf`
15. SNS Access: `orch-sf`, `notification-formatter`
16. CloudWatch Access: `execution-handler`, `orch-sf`

## Verification Status

### IAM Policies - ✅ VERIFIED ACCURATE
All 16 IAM policy statements in both reference documents match the actual CloudFormation template (`cfn/master-template.yaml` lines 125-500) exactly:
- Policy names match
- Permissions match
- Resource ARNs match
- Conditions match
- Critical permissions correctly identified

### API Endpoints - ✅ VERIFIED ACCURATE
API endpoint routing verified against actual Lambda handler code:
- `data-management-handler/index.py` - Protection groups, recovery plans, accounts, config
- `execution-handler/index.py` - Executions, pause/resume, termination
- `query-handler/index.py` - DRS queries, EC2 resources, user permissions

### Lambda Functions - ✅ VERIFIED ACCURATE
All 6 Lambda functions verified against actual directory structure:
- `lambda/data-management-handler/`
- `lambda/execution-handler/`
- `lambda/query-handler/`
- `lambda/frontend-deployer/`
- `lambda/orchestration-stepfunctions/` (deployed as `orch-sf`)
- `lambda/notification-formatter/`

## Files NOT Updated (Accurate As-Is)

The following 5 files were verified accurate and require no changes:
1. `DR_WAVE_PRIORITY_MAPPING.md` - Conceptual tagging strategy
2. `DRS_CROSS_ACCOUNT_REFERENCE.md` - AWS service documentation
3. `DRS_LAUNCH_CONFIGURATION_REFERENCE.md` - AWS sample tools reference
4. `DRS_SERVICE_LIMITS_AND_CAPABILITIES.md` - AWS service quotas
5. `SECURITY.md` - Security policy

## Impact Assessment

### Documentation Accuracy
- **Before**: References to 7+ non-existent Lambda functions
- **After**: Accurate references to 6 actual Lambda functions
- **Technical Content**: No changes - all IAM policies and API endpoints remain accurate

### User Impact
- Developers can now correctly identify which handler serves which endpoints
- IAM policy documentation correctly attributes permissions to actual functions
- Architecture documentation reflects current implementation

### Maintenance
- Future updates will be easier with accurate function names
- Reduced confusion when debugging or extending functionality
- Clear separation of concerns documented

## Related Documents

- `REFERENCE_DIRECTORY_ANALYSIS.md` - Initial analysis findings
- `cfn/master-template.yaml` - Source of truth for IAM policies
- `lambda/*/index.py` - Source of truth for API routing

---

**Updated By**: Kiro AI Assistant  
**Verification Method**: Direct codebase comparison  
**Next Review**: When Lambda architecture changes
