# Sensitive Data Purge Log

**Date**: January 15, 2026  
**Purpose**: Document all sensitive information in documentation for git history purging  
**Public Repository**: github.com/johnjcousens/aws-elasticdrs-orchestrator/

## ⚠️ CRITICAL: Git History Purge Required

All files listed below contain sensitive information that must be purged from git history before making repository public.

---

## 1. AWS Account ID: `***REMOVED***`

### Files Containing Account ID (12 files):

1. **docs/guides/DEVELOPMENT_WORKFLOW_GUIDE.md** (Line 87)
   - Context: Infrastructure table showing account number

2. **docs/deployment/CI_CD_PLATFORM_SELECTION.md** (Line 31)
   - Context: Account field in configuration

3. **docs/changelog/CHANGELOG_FULL_HISTORY.md** (Line 1761)
   - Context: Frontend bucket name with account ID

4. **docs/deployment/UPDATED_CICD_PIPELINE_GUIDE.md** (Line 174)
   - Context: AWS_ROLE_ARN with account ID

5. **docs/guides/S3_SYNC_AUTOMATION.md** (Line 65)
   - Context: AWS Account field

6. **docs/guides/deployment/FRESH_DEPLOYMENT_GUIDE.md** (Line 119)
   - Context: AWS_ROLE_ARN in secrets table

7. **docs/guides/troubleshooting/CODEBUILD_PERMISSIONS_FIX.md** (Lines 8, 130, 135, 187)
   - Context: IAM role ARNs and S3 bucket names with account ID

8. **docs/guides/troubleshooting/COGNITO_PASSWORD_RESET_FIX.md** (Line 56)
   - Context: AWS_PROFILE environment variable

9. **docs/deployment/GITHUB_SECRETS_CONFIGURATION.md** (Lines 11, 19, 53)
   - Context: AWS_ROLE_ARN and Stack ARN with account ID

10. **docs/deployment/CROSS_ACCOUNT_ROLE_POLICY.md** (Lines 200, 299)
    - Context: Hub account ID examples

### Replacement Pattern:
- Replace: `***REMOVED***`
- With: `{account-id}`

---

## 2. Email Address: `***REMOVED***`

### Files Containing Email (5 files):

1. **docs/guides/GITHUB_OIDC_MANAGEMENT.md** (Line 78)
   - Context: ADMIN_EMAIL in secrets table

2. **docs/deployment/UPDATED_CICD_PIPELINE_GUIDE.md** (Line 177)
   - Context: ADMIN_EMAIL secret value

3. **docs/deployment/STACK_RESTORATION_COMPLETE.md** (Lines 16, 77, 118)
   - Context: Admin Email configuration

4. **docs/deployment/GITHUB_SECRETS_CONFIGURATION.md** (Lines 14, 62)
   - Context: ADMIN_EMAIL secret

### Replacement Pattern:
- Replace: `***REMOVED***`
- With: `{admin-email}`

---

## 3. API Gateway IDs

### Specific API Gateway IDs Found (10+ instances):

#### `***REMOVED***` (Primary Dev Environment)
**Files:**
- docs/guides/DEVELOPMENT_WORKFLOW_GUIDE.md (Line 352)
- docs/changelog/CHANGELOG_FULL_HISTORY.md (Line 514)
- docs/security/RBAC_SECURITY_TESTING_STATUS.md (Line 69)
- docs/deployment/UPDATED_CICD_PIPELINE_GUIDE.md (Lines 135, 147, 229)
- docs/deployment/STACK_RESTORATION_COMPLETE.md (Lines 19, 112)
- docs/deployment/GITHUB_SECRETS_CONFIGURATION.md (Lines 29, 164)

#### `***REMOVED***` (Test Environment)
**Files:**
- docs/deployment/CROSS_ACCOUNT_ROLE_POLICY.md (Line 353)

#### `***REMOVED***` (Dev Environment - RBAC Testing)
**Files:**
- docs/security/RBAC_SECURITY_TESTING_STATUS.md (Line 69)

#### `***REMOVED***` (Dev Environment - Workflow Guide)
**Files:**
- docs/guides/DEVELOPMENT_WORKFLOW_GUIDE.md (Line 352)

#### `***REMOVED***` (Test Environment - Cognito)
**Files:**
- docs/guides/troubleshooting/COGNITO_PASSWORD_RESET_FIX.md (Line 233)

### Replacement Pattern:
- Replace: `[a-z0-9]{10}.execute-api`
- With: `{api-id}.execute-api`

---

## 4. CloudFront Distribution IDs and URLs

### CloudFront Distribution URLs Found (8+ instances):

#### `***REMOVED***.cloudfront.net` (Primary Dev)
**Files:**
- docs/changelog/CHANGELOG_FULL_HISTORY.md (Line 515)
- docs/deployment/UPDATED_CICD_PIPELINE_GUIDE.md (Lines 136, 232, 237)
- docs/deployment/STACK_RESTORATION_COMPLETE.md (Line 20)
- docs/deployment/GITHUB_SECRETS_CONFIGURATION.md (Line 30)

#### `***REMOVED***.cloudfront.net` (Test Environment)
**Files:**
- docs/tasks/POLLING_FIX.md (Line 6)

#### `***REMOVED***.cloudfront.net` (Production)
**Files:**
- docs/changelog/CHANGELOG_FULL_HISTORY.md (Line 1775)

#### `***REMOVED***.cloudfront.net` (Test - Cognito)
**Files:**
- docs/guides/troubleshooting/COGNITO_PASSWORD_RESET_FIX.md (Line 232)

##***REMOVED***:
- `***REMOVED***` (in CHANGELOG_FULL_HISTORY.md, Line 1763)

### Replacement Pattern:
- Replace: `https://[a-z0-9]+.cloudfront.net`
- With: `https://{distribution-id}.cloudfront.net`

---

## 5. Cognito User Pool IDs

### User Pool IDs Found (10+ instances):

#### `***REMOVED***` (Primary Dev)
**Files:**
- docs/deployment/UPDATED_CICD_PIPELINE_GUIDE.md (Line 144)
- docs/deployment/STACK_RESTORATION_COMPLETE.md (Lines 24, 109)
- docs/deployment/GITHUB_SECRETS_CONFIGURATION.md (Line 31)
- docs/changelog/CHANGELOG_FULL_HISTORY.md (Line 516)

#### `***REMOVED***` (Test Environment)
**Files:**
- docs/guides/troubleshooting/COGNITO_PASSWORD_RESET_FIX.md (Lines 60, 69, 78, 120, 140, 174, 182, 229)

#### `***REMOVED***` (Dev - RBAC Testing)
**Files:**
- docs/security/RBAC_SECURITY_TESTING_STATUS.md (Line 71)

#### `***REMOVED***` (Test - Cross Account)
**Files:**
- docs/deployment/CROSS_ACCOUNT_ROLE_POLICY.md (Line 344)

### Replacement Pattern:
- Replace: `us-east-1_[A-Za-z0-9]{9}`
- With: `{region}_{pool-id}`

---

## 6. Cognito Client IDs

### Client IDs Found (5+ instances):

#### `***REMOVED***` (Primary Dev)
**Files:**
- docs/deployment/UPDATED_CICD_PIPELINE_GUIDE.md (Line 146)
- docs/deployment/STACK_RESTORATION_COMPLETE.md (Lines 26, 111)
- docs/deployment/GITHUB_SECRETS_CONFIGURATION.md (Line 33)

#### `***REMOVED***` (Dev - RBAC Testing)
**Files:**
- docs/security/RBAC_SECURITY_TESTING_STATUS.md (Line 73)

#### `***REMOVED***` (Test - Cross Account)
**Files:**
- docs/deployment/CROSS_ACCOUNT_ROLE_POLICY.md (Line 346)

### Replacement Pattern:
- Replace: `[a-z0-9]{26}` (26-character client IDs)
- With: `{client-id}`

---

## 7. Cognito Identity Pool IDs

### Identity Pool IDs Found (3+ instances):

#### `***REMOVED***` (Primary Dev)
**Files:**
- docs/deployment/UPDATED_CICD_PIPELINE_GUIDE.md (Line 147)
- docs/deployment/STACK_RESTORATION_COMPLETE.md (Lines 27, 112)
- docs/deployment/GITHUB_SECRETS_CONFIGURATION.md (Line 34)

### Replacement Pattern:
- Replace: `us-east-1:[a-f0-9-]{36}`
- With: `{region}:{identity-pool-id}`

---

## 8. S3 Bucket Names with Account IDs

### Bucket Names Found:

#### `aws-elasticdrs-orchestrator-cicd-artifacts-***REMOVED***-dev`
**Files:**
- docs/guides/troubleshooting/CODEBUILD_PERMISSIONS_FIX.md (Lines 130, 135, 187)

#### `drsorchv4-fe-***REMOVED***-test`
**Files:**
- docs/changelog/CHANGELOG_FULL_HISTORY.md (Line 1761)

### Replacement Pattern:
- Replace: Bucket names containing account ID
- With: `{project-name}-{resource}-{account-id}-{environment}`

---

## 9. Stack ARNs

### Stack ARNs Found:

#### `arn:aws:cloudformation:us-east-1:***REMOVED***:stack/aws-elasticdrs-orchestrator-dev/00c30fb0-eb2b-11f0-9ca6-12010aae964f`
**Files:**
- docs/deployment/GITHUB_SECRETS_CONFIGURATION.md (Line 19)

### Replacement Pattern:
- Replace: Full ARNs with account ID
- With: `arn:aws:cloudformation:{region}:{account-id}:stack/{stack-name}/{stack-id}`

---

## 10. IAM Role ARNs

### Role ARNs Found (Multiple instances):

#### `arn:aws:iam::***REMOVED***:role/GitHubActionsRole`
**Files:**
- docs/deployment/UPDATED_CICD_PIPELINE_GUIDE.md (Line 174)
- docs/deployment/GITHUB_SECRETS_CONFIGURATION.md (Lines 11, 53)

#### `arn:aws:iam::***REMOVED***:role/aws-elasticdrs-orchestrator-github-actions-dev`
**Files:**
- docs/guides/deployment/FRESH_DEPLOYMENT_GUIDE.md (Line 119)

#### `arn:aws:sts::***REMOVED***:assumed-role/aws-elasticdrs-orchestrator-codebuild-service-role-dev/...`
**Files:**
- docs/guides/troubleshooting/CODEBUILD_PERMISSIONS_FIX.md (Line 8)

### Replacement Pattern:
- Replace: IAM role ARNs with account ID
- With: `arn:aws:iam::{account-id}:role/{role-name}`

---

## Git History Purge Strategy

### Tools Required:
1. **git-filter-repo** (recommended) or **BFG Repo-Cleaner**
2. **git-secrets** (for future prevention)

### Purge Process:

#### Step 1: Create Replacement File
```bash
# Create replacements.txt with all patterns
***REMOVED*** ==> {account-id}
***REMOVED*** ==> {admin-email}
***REMOVED*** ==> {api-id}
***REMOVED*** ==> {api-id}
***REMOVED*** ==> {api-id}
***REMOVED*** ==> {api-id}
***REMOVED*** ==> {api-id}
***REMOVED*** ==> {distribution-id}
***REMOVED*** ==> {distribution-id}
***REMOVED*** ==> {distribution-id}
***REMOVED*** ==> {distribution-id}
***REMOVED*** ==> {cloudfront-id}
***REMOVED*** ==> {region}_{pool-id}
***REMOVED*** ==> {region}_{pool-id}
***REMOVED*** ==> {region}_{pool-id}
***REMOVED*** ==> {region}_{pool-id}
***REMOVED*** ==> {client-id}
***REMOVED*** ==> {client-id}
***REMOVED*** ==> {client-id}
***REMOVED*** ==> {region}:{identity-pool-id}
```

#### Step 2: Backup Repository
```bash
# Create backup before purging
git clone --mirror git@github.com:johnjcousens/aws-elasticdrs-orchestrator.git backup-repo
```

#### Step 3: Run git-filter-repo
```bash
# Install git-filter-repo
pip install git-filter-repo

# Run replacement on all history
git filter-repo --replace-text replacements.txt --force
```

#### Step 4: Force Push (DESTRUCTIVE)
```bash
# Force push to rewrite history (requires admin access)
git push origin --force --all
git push origin --force --tags
```

#### Step 5: Notify Collaborators
All collaborators must re-clone the repository after history rewrite.

---

## Files Requiring Manual Review

### High Priority (Contains Multiple Sensitive Values):
1. docs/deployment/GITHUB_SECRETS_CONFIGURATION.md
2. docs/deployment/STACK_RESTORATION_COMPLETE.md
3. docs/deployment/UPDATED_CICD_PIPELINE_GUIDE.md
4. docs/guides/troubleshooting/COGNITO_PASSWORD_RESET_FIX.md
5. docs/guides/troubleshooting/CODEBUILD_PERMISSIONS_FIX.md
6. docs/changelog/CHANGELOG_FULL_HISTORY.md

### Medium Priority (Contains Some Sensitive Values):
7. docs/guides/DEVELOPMENT_WORKFLOW_GUIDE.md
8. docs/guides/deployment/FRESH_DEPLOYMENT_GUIDE.md
9. docs/deployment/CROSS_ACCOUNT_ROLE_POLICY.md
10. docs/security/RBAC_SECURITY_TESTING_STATUS.md

---

## Summary Statistics

- **Total Files with Sensitive Data**: 15+ documentation files
- **AWS Account ID Instances**: 12+ files
- **Email Address Instances**: 5 files
- **API Gateway IDs**: 5 unique IDs across 10+ files
- **CloudFront URLs**: 4 unique distributions across 8+ files
- **Cognito Pool IDs**: 4 unique pools across 10+ files
- **Cognito Client IDs**: 3 unique clients across 5+ files
- **Identity Pool IDs**: 1 pool across 4 files

---

## Post-Purge Verification

After git history purge, verify:
1. ✅ No account IDs in any commit
2. ✅ No email addresses in any commit
3. ✅ No API Gateway IDs in any commit
4. ✅ No CloudFront distribution IDs in any commit
5. ✅ No Cognito resource IDs in any commit
6. ✅ All documentation uses generic placeholders
7. ✅ Repository safe for public access

---

## Prevention Strategy

### Install git-secrets
```bash
# Install git-secrets
brew install git-secrets

# Initialize in repository
git secrets --install
git secrets --register-aws

# Add custom patterns
git secrets --add '***REMOVED***'
git secrets --add 'jocousen@amazon\.com'
git secrets --add '[a-z0-9]{10}\.execute-api'
git secrets --add 'us-east-1_[A-Za-z0-9]{9}'
```

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
git secrets --pre_commit_hook -- "$@"
```

---

**CRITICAL**: This purge must be completed before making repository public.
**Repository**: github.com/johnjcousens/aws-elasticdrs-orchestrator/
**Date Created**: January 15, 2026
