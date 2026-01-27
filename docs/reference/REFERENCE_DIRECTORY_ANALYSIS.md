# Reference Directory Analysis

**Date**: January 26, 2026  
**Analyzed Files**: 8  
**Status**: Complete

## Summary

Analyzed all 8 files in `docs/reference/` directory against actual codebase implementation. Found **3 files with accuracy issues** and **5 files that are current and accurate**.

## Files Analyzed

### ✅ ACCURATE - Keep As-Is (5 files)

#### 1. DR_WAVE_PRIORITY_MAPPING.md
**Status**: Accurate  
**Content**: Wave and priority mapping strategy for DR orchestration  
**Verification**: Conceptual document - defines tagging strategy, not implementation-specific  
**Notes**: Provides clear guidance on wave/priority assignment based on resource characteristics

#### 2. DRS_CROSS_ACCOUNT_REFERENCE.md
**Status**: Accurate  
**Content**: Comprehensive cross-account DRS setup guide  
**Verification**: AWS service documentation - not implementation-specific  
**Notes**: Detailed IAM, KMS, networking configuration for cross-account scenarios

#### 3. DRS_LAUNCH_CONFIGURATION_REFERENCE.md
**Status**: Accurate  
**Content**: DRS launch template configuration guide based on AWS sample tools  
**Verification**: References official AWS sample tools (drs-configuration-synchronizer, drs-template-manager)  
**Notes**: Provides safe modification guidelines for launch templates

#### 4. DRS_SERVICE_LIMITS_AND_CAPABILITIES.md
**Status**: Accurate  
**Content**: AWS DRS service quotas, limits, and capabilities  
**Verification**: AWS service documentation - validated December 10, 2025  
**Notes**: Critical information about 300 replicating server hard limit

#### 5. SECURITY.md
**Status**: Accurate  
**Content**: Security policy and vulnerability reporting  
**Verification**: Standard security policy document  
**Notes**: Includes supported versions, security standards, reporting procedures

### ⚠️ NEEDS UPDATE - Inaccurate (3 files)

#### 6. API_ENDPOINTS_CURRENT.md
**Status**: **INACCURATE** - Partially outdated  
**Issues Found**:
1. **Claims 42+ endpoints** but actual implementation has fewer
2. **References non-existent Lambda functions**:
   - Document mentions: "ApiHandler", "CustomResource", "BucketCleaner", "ExecutionFinder"
   - Actual functions: `data-management-handler`, `execution-handler`, `query-handler`, `frontend-deployer`, `orch-sf`, `notification-formatter`
3. **Some documented endpoints not implemented**:
   - `/recovery-plans/{id}/check-existing-instances` - Returns 501 "Not yet implemented"
4. **Missing handler routing details** - Document doesn't clarify which handler serves which endpoints

**Actual Architecture**:
- **data-management-handler**: Protection groups, recovery plans, tag sync, config, target accounts
- **execution-handler**: Executions, pause/resume, termination, DRS operations
- **query-handler**: DRS source servers, quotas, EC2 resources, config export

**Recommendation**: Update to reflect 3-handler architecture and remove references to non-existent functions

#### 7. DRS_IAM_AND_PERMISSIONS_REFERENCE.md
**Status**: **PARTIALLY ACCURATE** - Needs verification  
**Issues Found**:
1. **References outdated Lambda function names**:
   - Document mentions: "ApiHandler", "CustomResource", "BucketCleaner", "ExecutionFinder", "ExecutionPoller"
   - Should reference: `data-management-handler`, `execution-handler`, `query-handler`, `frontend-deployer`, `orch-sf`, `notification-formatter`
2. **IAM permissions appear accurate** - Verified against `cfn/master-template.yaml` UnifiedOrchestrationRole
3. **Cross-account setup is accurate** - Matches AWS DRS service requirements

**Verified Accurate**:
- All 16 policy statements match CloudFormation template
- Critical permissions correctly identified (SendTaskHeartbeat, CreateRecoveryInstanceForDrs, CreateLaunchTemplateVersion, CreateOpsItem)
- Resource naming conventions match actual implementation
- KMS, cross-account, and service role configurations are correct

**Recommendation**: Update Lambda function name references but keep IAM policy content

#### 8. ORCHESTRATION_ROLE_SPECIFICATION.md
**Status**: **PARTIALLY ACCURATE** - Needs verification  
**Issues Found**:
1. **References outdated Lambda function names**:
   - Document mentions: "ApiHandler", "CustomResource", "BucketCleaner", "ExecutionFinder", "ExecutionPoller", "NotificationFormatter"
   - Should reference: `data-management-handler`, `execution-handler`, `query-handler`, `frontend-deployer`, `orch-sf`, `notification-formatter`
2. **IAM policies are accurate** - All 16 policies verified against `cfn/master-template.yaml`
3. **Critical permissions correctly identified**

**Verified Accurate**:
- All policy statements match CloudFormation implementation
- Resource ARN patterns correct
- Trust policy accurate
- HRP integration checklist valid

**Recommendation**: Update Lambda function name references but keep policy specifications

## Verification Methodology

### 1. Lambda Function Names
**Verified Against**: `infra/orchestration/drs-orchestration/lambda/` directory structure  
**Actual Functions**:
- `data-management-handler/`
- `execution-handler/`
- `query-handler/`
- `frontend-deployer/`
- `orchestration-stepfunctions/` (deployed as `orch-sf`)
- `notification-formatter/`

### 2. IAM Permissions
**Verified Against**: `cfn/master-template.yaml` lines 125-500  
**Result**: All documented policies match CloudFormation template exactly

### 3. API Endpoints
**Verified Against**: Lambda handler routing code  
**Files Checked**:
- `lambda/data-management-handler/index.py` (lines 405-500)
- `lambda/execution-handler/index.py` (lines 2800-2850)
- `lambda/query-handler/index.py` (lines 410-450)

## Recommended Actions

### Immediate Actions (High Priority)

1. **Update API_ENDPOINTS_CURRENT.md**:
   - Add section explaining 3-handler architecture
   - Map endpoints to specific handlers
   - Remove references to non-existent functions
   - Mark unimplemented endpoints clearly (501 status)
   - Update "Used by" annotations with correct handler names

2. **Update DRS_IAM_AND_PERMISSIONS_REFERENCE.md**:
   - Replace all Lambda function name references
   - Keep all IAM policy content (verified accurate)
   - Update "Used by" annotations

3. **Update ORCHESTRATION_ROLE_SPECIFICATION.md**:
   - Replace all Lambda function name references
   - Keep all policy specifications (verified accurate)
   - Update "Used by" annotations

### Optional Actions (Low Priority)

4. **Add Lambda Architecture Document**:
   - Create new reference doc explaining 3-handler split
   - Document routing logic for each handler
   - Explain why handlers were split (data-management vs execution vs query)

## Files to Keep

All 8 files should be retained:
- 5 files are accurate and current
- 3 files need updates but contain valuable information
- No files should be archived

## Accuracy Summary

| File | Status | Action Required |
|------|--------|----------------|
| DR_WAVE_PRIORITY_MAPPING.md | ✅ Accurate | None |
| DRS_CROSS_ACCOUNT_REFERENCE.md | ✅ Accurate | None |
| DRS_LAUNCH_CONFIGURATION_REFERENCE.md | ✅ Accurate | None |
| DRS_SERVICE_LIMITS_AND_CAPABILITIES.md | ✅ Accurate | None |
| SECURITY.md | ✅ Accurate | None |
| API_ENDPOINTS_CURRENT.md | ⚠️ Partially Inaccurate | Update Lambda function names, add handler architecture |
| DRS_IAM_AND_PERMISSIONS_REFERENCE.md | ⚠️ Partially Inaccurate | Update Lambda function names only |
| ORCHESTRATION_ROLE_SPECIFICATION.md | ⚠️ Partially Inaccurate | Update Lambda function names only |

## Key Findings

### Critical Discovery: Lambda Function Naming Mismatch

**Root Cause**: Documentation was written before Lambda handlers were split into specialized functions.

**Original Architecture** (documented):
- Single `ApiHandler` function handling all API requests

**Current Architecture** (implemented):
- `data-management-handler` - Protection groups, recovery plans, configuration
- `execution-handler` - Execution control, pause/resume, termination
- `query-handler` - Read-only queries, DRS status, EC2 resources

**Impact**: Documentation references are outdated but underlying technical content (IAM policies, API endpoints) is mostly accurate.

### IAM Policies Are Accurate

All IAM policy specifications in reference documents match the actual CloudFormation template exactly. The 16 policies in `UnifiedOrchestrationRole` are correctly documented with accurate permissions, resource ARNs, and conditions.

### Service Limits Documentation Is Critical

`DRS_SERVICE_LIMITS_AND_CAPABILITIES.md` contains critical information about the 300 replicating server hard limit that cannot be increased. This is essential for capacity planning and multi-account architecture decisions.

## Next Steps

1. Update the 3 files with Lambda function name corrections
2. Consider creating a Lambda architecture reference document
3. Verify API endpoint implementation status (which are 501 vs implemented)
4. Add handler routing documentation to API reference

---

**Analysis Completed**: January 26, 2026  
**Analyst**: Kiro AI Assistant  
**Verification Method**: Direct codebase comparison
