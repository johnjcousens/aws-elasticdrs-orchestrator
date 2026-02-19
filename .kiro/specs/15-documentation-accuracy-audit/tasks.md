# Implementation Plan: Documentation Accuracy Audit

## Overview

Documentation-only corrections across 8 files (README + 7 docs). No code changes to `/lambda`, `/cfn`, or `/frontend`. Tasks are ordered so that foundational corrections (architecture, handlers) come before dependent docs (API endpoints, IAM) to maintain consistency.

## Tasks

- [ ] 1. Fix broken README links and create ERROR_CODES stub
  - [ ] 1.1 Update README.md broken links
    - Replace `docs/analysis/LAMBDA_HANDLERS_COMPLETE_ANALYSIS.md` link with `docs/architecture/LAMBDA_HANDLERS_ARCHITECTURE.md`
    - Replace `docs/api-reference/EXECUTION_HANDLER_API.md` link with `docs/reference/API_ENDPOINTS_CURRENT.md` (note execution endpoints are documented there)
    - Keep `docs/troubleshooting/ERROR_CODES.md` link as-is (will create the file next)
    - _Requirements: 1.1, 1.2, 1.4_
  - [ ] 1.2 Create `docs/troubleshooting/ERROR_CODES.md` stub
    - Create minimal file listing the 13 error codes referenced in the README (VALIDATION_ERROR, RESOURCE_NOT_FOUND, CONFLICT_ERROR, DRS_SERVICE_ERROR, EXECUTION_ERROR, AUTHORIZATION_ERROR, etc.)
    - Include brief description and common troubleshooting steps for each
    - _Requirements: 1.3, 1.4_

- [ ] 2. Correct architecture document stack information
  - [ ] 2.1 Fix stack table in `docs/architecture/ARCHITECTURE.md`
    - Add WAFStack row: conditional on `DeployFrontend=true` AND `DeployApiGateway=true` AND region `us-east-1`
    - Move `cross-account-role-stack.yaml` and `github-oidc-stack.yaml` to a new "Standalone Templates" section
    - Update total count to "1 master + 14 nested stacks (some conditional) + 2 standalone templates"
    - _Requirements: 2.1, 2.2, 2.3_
  - [ ] 2.2 Fix parameter name in `docs/architecture/ARCHITECTURE.md`
    - Replace all references to `DeploymentBucket` parameter with `SourceBucket`
    - _Requirements: 2.4_

- [ ] 3. Document missing Lambda handlers in `docs/architecture/LAMBDA_HANDLERS_ARCHITECTURE.md`
  - [ ] 3.1 Add `dr-orchestration-stepfunction` handler section
    - Document wave orchestration responsibilities, Step Functions integration, launch config sync
    - Follow existing doc pattern: purpose, key operations, invocation pattern
    - _Requirements: 3.1, 3.4_
  - [ ] 3.2 Add `frontend-deployer` handler section
    - Document CloudFormation Custom Resource role, S3 sync, CloudFront invalidation
    - _Requirements: 3.2, 3.4_
  - [ ] 3.3 Add `drs-agent-deployer` handler section
    - Document SSM-based agent deployment purpose
    - Note pre-development status: directory exists but not yet deployed via CloudFormation
    - _Requirements: 3.3, 3.4_

- [ ] 4. Document missing shared modules in `docs/architecture/LAMBDA_HANDLERS_ARCHITECTURE.md`
  - [ ] 4.1 Add 9 missing shared module entries to the shared modules table
    - Add: `config_merge.py`, `drs_regions.py`, `drs_utils.py`, `execution_utils.py`, `iam_utils.py`, `launch_config_validation.py`, `notifications.py`, `security_utils.py`, `staging_account_models.py`
    - Read each module's docstrings/code to write accurate purpose descriptions
    - _Requirements: 4.1, 4.2_

- [ ] 5. Checkpoint - Review architecture and handler docs
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Correct IAM documentation
  - [ ] 6.1 Fix trust policy and add missing policies in `docs/iam/ORCHESTRATION_ROLE_POLICY.md`
    - Update trust policy to list: `lambda.amazonaws.com`, `states.amazonaws.com`, `apigateway.amazonaws.com`
    - Add 6 missing policy sections: CloudWatchLogsAccess, LicenseManagerAccess, ResourceGroupsAccess, ELBAccess, SQSAccess, ApiGatewayDeploymentAccess
    - Include exact actions and resource scoping from master-template.yaml
    - _Requirements: 5.1, 5.3_
  - [ ] 6.2 Fix SNS and CloudWatch policy details in `docs/iam/ORCHESTRATION_ROLE_POLICY.md`
    - Update SNS section with all 8 actions: Publish, Subscribe, Unsubscribe, ListSubscriptionsByTopic, GetSubscriptionAttributes, SetSubscriptionAttributes, GetTopicAttributes, ListTopics
    - Update CloudWatch section with all 3 actions: PutMetricData, GetMetricStatistics, GetMetricData
    - _Requirements: 5.4, 5.5_
  - [ ] 6.3 Fix cross-account role name in `docs/reference/ORCHESTRATION_ROLE_SPECIFICATION.md`
    - Replace old role naming pattern with `DRSOrchestrationRole`
    - _Requirements: 5.2_

- [ ] 7. Correct API endpoint documentation in `docs/reference/API_ENDPOINTS_CURRENT.md`
  - [ ] 7.1 Add missing implemented endpoint sections
    - Add server launch configuration endpoints (5 endpoints)
    - Add staging account management endpoints (6 endpoints)
    - Add capacity query endpoints (2 endpoints)
    - Add config validation endpoint (1 endpoint)
    - Add GET method for `/drs/tag-sync`
    - Read handler source code to determine exact paths and methods
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [ ] 7.2 Add "Defined but Not Implemented" section and fix endpoint count
    - Add section listing ~20 DRS infrastructure endpoints defined in CFN but not implemented
    - Correct total endpoint count from 44 to ~35 implemented
    - _Requirements: 6.6, 6.7_

- [ ] 8. Fix deployment script references
  - [ ] 8.1 Replace `local-deploy.sh` with `deploy.sh` in `docs/deployment/QUICK_START_GUIDE.md`
    - Replace all occurrences of `./scripts/local-deploy.sh` with `./scripts/deploy.sh`
    - Update command arguments if the deploy.sh syntax differs
    - _Requirements: 7.1_
  - [ ] 8.2 Replace `local-deploy.sh` with `deploy.sh` in `docs/guides/DEVELOPER_GUIDE.md`
    - Replace all occurrences of `./scripts/local-deploy.sh` with `./scripts/deploy.sh`
    - Update command arguments if the deploy.sh syntax differs
    - _Requirements: 7.2_

- [ ] 9. Checkpoint - Verify all documentation corrections
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 10. Write documentation accuracy verification tests
  - [ ]* 10.1 Write property test: All README links resolve
    - **Property 1: All README relative links resolve to existing files**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
  - [ ]* 10.2 Write property test: All Lambda handlers documented
    - **Property 2: All Lambda handler directories are documented**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
  - [ ]* 10.3 Write property test: All shared modules documented
    - **Property 3: All production shared modules are documented**
    - **Validates: Requirements 4.1, 4.2**
  - [ ]* 10.4 Write property test: Stack count matches master template
    - **Property 4: Architecture doc stack count matches master template**
    - **Validates: Requirements 2.3**
  - [ ]* 10.5 Write unit tests for specific content corrections
    - Verify WAFStack mentioned in architecture doc
    - Verify SourceBucket (not DeploymentBucket) in architecture doc
    - Verify DRSOrchestrationRole in role spec doc
    - Verify no `local-deploy.sh` references in Quick Start or Developer Guide
    - Verify trust policy principals in IAM doc
    - _Requirements: 2.1, 2.4, 5.1, 5.2, 7.1, 7.2_

- [ ] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster completion
- No code in `/lambda`, `/cfn`, or `/frontend` should be modified
- All corrections are verified against the actual deployed codebase (stack `hrp-drs-tech-adapter-dev`)
- Property tests are implemented as parameterized pytest tests (not hypothesis-based, since inputs are deterministic)
- Test file location: `tests/unit/test_documentation_accuracy.py`
