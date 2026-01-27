# Frontend Rebuild Mechanism - Implementation Tasks

## Task 1: Update frontend-stack.yaml

**Objective:** Add FrontendBuildVersion parameter and pass it to Custom::FrontendDeployer

**Changes:**
1. Add `FrontendBuildVersion` parameter with default "v1"
2. Pass parameter as Property to `FrontendDeploymentResource`
3. Add output for version visibility

**Files:**
- `infra/orchestration/drs-orchestration/cfn/frontend-stack.yaml`

**Acceptance Criteria:**
- [ ] Parameter added with correct type and default
- [ ] Property passed to Custom::FrontendDeployer
- [ ] Output added for version tracking
- [ ] cfn-lint passes validation

---

## Task 2: Update master-template.yaml

**Objective:** Add FrontendBuildVersion parameter and pass to nested FrontendStack

**Changes:**
1. Add `FrontendBuildVersion` parameter with default "v1"
2. Pass parameter to FrontendStack nested stack

**Files:**
- `infra/orchestration/drs-orchestration/cfn/master-template.yaml`

**Acceptance Criteria:**
- [ ] Parameter added to master template
- [ ] Parameter passed to FrontendStack
- [ ] cfn-lint passes validation
- [ ] No breaking changes to existing parameters

---

## Task 3: Update deploy.sh

**Objective:** Generate timestamp version and pass to CloudFormation on --frontend-only

**Changes:**
1. Add `generate_frontend_version()` function
2. Update `--frontend-only` block to generate and pass version
3. Add logging for version being deployed

**Files:**
- `infra/orchestration/drs-orchestration/scripts/deploy.sh`

**Acceptance Criteria:**
- [ ] Version generation function uses format YYYYMMDD-HHMM
- [ ] Version passed to CloudFormation on --frontend-only
- [ ] Version logged to console
- [ ] Full deployments still work (use default or omit parameter)
- [ ] Lambda-only deployments unaffected

---

## Task 4: Update frontend-deployer Lambda

**Objective:** Accept and log FrontendBuildVersion property

**Changes:**
1. Extract `FrontendBuildVersion` from properties
2. Log version in deployment start message
3. Include version in security event logging
4. Return version in response data

**Files:**
- `infra/orchestration/drs-orchestration/lambda/frontend-deployer/index.py`

**Acceptance Criteria:**
- [ ] Version extracted from properties with default "v1"
- [ ] Version logged in print statements
- [ ] Version included in log_security_event calls
- [ ] Version returned in response data
- [ ] Input sanitization applied to version string

---

## Task 5: Test Frontend-Only Deployment

**Objective:** Verify --frontend-only triggers rebuild with new version

**Test Steps:**
1. Deploy stack with default version "v1"
2. Make frontend code change (e.g., update Dashboard title)
3. Run `./scripts/deploy.sh dev --frontend-only`
4. Verify CloudFormation shows parameter change
5. Verify Lambda logs show new version
6. Verify frontend change visible in browser

**Acceptance Criteria:**
- [ ] CloudFormation parameter changes from "v1" to timestamp
- [ ] CloudFormation events show UPDATE to FrontendDeploymentResource
- [ ] Lambda logs show "Deploying frontend version YYYYMMDD-HHMM"
- [ ] Frontend changes visible after CloudFront cache invalidation
- [ ] Deployment completes in under 3 minutes

---

## Task 6: Test Backward Compatibility

**Objective:** Verify existing stacks work without changes

**Test Steps:**
1. Deploy code changes to existing stack
2. Verify stack updates successfully
3. Verify frontend still works with version "v1"
4. Run --frontend-only to upgrade to timestamp version
5. Verify subsequent deployments use timestamp

**Acceptance Criteria:**
- [ ] Existing stacks update without errors
- [ ] No stack recreation required
- [ ] Frontend continues working with "v1"
- [ ] First --frontend-only upgrades to timestamp
- [ ] No manual intervention needed

---

## Task 7: Test Full Stack Deployment

**Objective:** Verify full deployments still work correctly

**Test Steps:**
1. Run `./scripts/deploy.sh dev` (full deployment)
2. Verify all stacks deploy successfully
3. Verify frontend deploys with default version
4. Verify no unexpected parameter changes

**Acceptance Criteria:**
- [ ] Full deployment completes successfully
- [ ] Frontend deploys correctly
- [ ] FrontendBuildVersion uses default "v1" (or previous value)
- [ ] No breaking changes to deployment flow

---

## Task 8: Test Lambda-Only Deployment

**Objective:** Verify --lambda-only doesn't trigger frontend rebuild

**Test Steps:**
1. Make Lambda code change
2. Run `./scripts/deploy.sh dev --lambda-only`
3. Verify Lambda updated
4. Verify frontend NOT rebuilt
5. Verify FrontendBuildVersion unchanged

**Acceptance Criteria:**
- [ ] Lambda code updated successfully
- [ ] No CloudFormation deployment triggered
- [ ] Frontend version unchanged
- [ ] Frontend content unchanged

---

## Task 9: Update Documentation

**Objective:** Document the new version mechanism

**Changes:**
1. Update deployment guide with --frontend-only behavior
2. Document version format and purpose
3. Add troubleshooting section for version issues
4. Update CHANGELOG.md

**Files:**
- `infra/orchestration/drs-orchestration/docs/deployment/deployment-guide.md`
- `infra/orchestration/drs-orchestration/CHANGELOG.md`

**Acceptance Criteria:**
- [ ] Deployment guide explains version mechanism
- [ ] Version format documented (YYYYMMDD-HHMM)
- [ ] Troubleshooting steps added
- [ ] CHANGELOG updated with feature description

---

## Task 10: Validation and Cleanup

**Objective:** Final validation and cleanup

**Validation Steps:**
1. Run cfn-lint on all modified templates
2. Run black/flake8 on modified Python code
3. Verify no security issues with bandit
4. Test all deployment modes (full, lambda-only, frontend-only)
5. Verify CloudFormation events show version changes
6. Verify Lambda logs show version information

**Acceptance Criteria:**
- [ ] All linters pass
- [ ] All security scans pass
- [ ] All deployment modes tested successfully
- [ ] CloudFormation events traceable
- [ ] Lambda logs include version information
- [ ] No breaking changes introduced

---

## Deployment Order

1. Deploy Task 1-4 changes together (code + templates)
2. Test with Task 5-8 (all deployment modes)
3. Update documentation (Task 9)
4. Final validation (Task 10)

## Rollback Plan

If issues occur:
1. Revert deploy.sh changes (removes version generation)
2. CloudFormation will use default "v1" for all deployments
3. Frontend deployments continue working with default version
4. No stack recreation needed

## Success Criteria

- ✅ `./scripts/deploy.sh dev --frontend-only` triggers frontend rebuild
- ✅ Version visible in CloudFormation parameters and events
- ✅ Version logged in Lambda execution logs
- ✅ Frontend changes visible in browser after deployment
- ✅ Backward compatible with existing stacks
- ✅ No manual intervention required
- ✅ All deployment modes (full, lambda-only, frontend-only) work correctly
