# Amazon Q Development Workflow

## CRITICAL: Always Update IaC with Code Changes

**NEVER deploy code changes without updating CloudFormation templates and S3 artifacts.**

## Development Workflow

### Local Development Process

#### 1. Make Code Changes
- Update Lambda functions in `lambda/` (5 active functions)
- Update frontend in `frontend/`
- Update CloudFormation templates in `cfn/` (7 total: 1 master + 6 nested stacks)

#### 2. Sync to S3 Deployment Bucket (REQUIRED)
```bash
./scripts/sync-to-deployment-bucket.sh
```

**This syncs:**
- CloudFormation templates → `s3://hrp-drs-tech-adapter/cfn/`
- Lambda source code → `s3://hrp-drs-tech-adapter/lambda/`
- Frontend source + built dist → `s3://hrp-drs-tech-adapter/frontend/`
- Scripts and SSM documents → `s3://hrp-drs-tech-adapter/scripts/` and `ssm-documents/`
- Documentation → `s3://hrp-drs-tech-adapter/docs/`

#### 3. Deploy Changes (REQUIRED)

**Fast Lambda updates (~5 seconds):**
```bash
./scripts/sync-to-deployment-bucket.sh --update-lambda-code
```

**Update ALL Lambda functions (~15 seconds):**
```bash
./scripts/sync-to-deployment-bucket.sh --update-all-lambda
```

**Full CloudFormation deployment (5-10 minutes):**
```bash
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

**Frontend build and deploy:**
```bash
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend
```

**Individual Lambda stack deployment (~30 seconds):**
```bash
./scripts/sync-to-deployment-bucket.sh --deploy-lambda
```

#### 4. Verify Deployment
```bash
# Check stack status
aws cloudformation describe-stacks --stack-name hrp-drs-tech-adapter-dev --region us-east-2

# Verify S3 has latest
aws s3 ls s3://hrp-drs-tech-adapter/lambda/ --region us-east-2
```

### GitLab CI/CD Pipeline

**6-Stage Pipeline:**
```
validate → lint → build → test → deploy-infra → deploy-frontend
```

**Pipeline Jobs:**
- **validate**: CloudFormation templates (cfn-lint + AWS CLI), Frontend TypeScript type checking
- **lint**: Python (pylint, black, flake8), Frontend (ESLint)
- **build**: 5 Lambda packages individually, Frontend (React + Vite)
- **test**: Python unit/integration tests, Playwright E2E tests (currently disabled - tests/ not in git)
- **deploy-infra**: Upload artifacts to S3, Deploy CloudFormation stack
- **deploy-frontend**: Generate aws-config.js, Deploy to S3 + CloudFront invalidation

**Key Features:**
- ECR Public images (avoids Docker Hub rate limits)
- Builds 5 Lambda packages individually with dependencies
- Automated deployment for main/dev branches
- Manual production deployment
- Complete artifact upload to S3 deployment bucket
- Project name: "hrp-drs-tech-adapter" (matches sync script)

## Rules for Amazon Q

### ALWAYS Do This:
1. ✅ Sync to S3 before any deployment: `./scripts/sync-to-deployment-bucket.sh`
2. ✅ Use fast Lambda updates for code changes: `--update-lambda-code`
3. ✅ Use full deployment for infrastructure changes: `--deploy-cfn`
4. ✅ Verify S3 artifacts are current after changes
5. ✅ Let GitLab CI/CD handle production deployments

### NEVER Do This:
1. ❌ Deploy Lambda code without syncing to S3 first
2. ❌ Make infrastructure changes without updating CloudFormation
3. ❌ Skip the sync step - S3 is source of truth
4. ❌ Assume local code matches deployed code
5. ❌ Deploy directly to production (use GitLab pipeline)

## Why This Matters

**Problem**: If you only update deployed resources (Lambda, etc.) without updating S3:
- CloudFormation templates become stale
- S3 artifacts don't match deployed code
- Cannot redeploy from scratch
- Lose all progress if stack is deleted

**Solution**: Always sync to S3 and deploy via CloudFormation

## Quick Reference

| Action | Command | Time |
|--------|---------|------|
| Sync everything | `./scripts/sync-to-deployment-bucket.sh` | ~30s |
| Fast Lambda update | `./scripts/sync-to-deployment-bucket.sh --update-lambda-code` | ~5s |
| Update all Lambda | `./scripts/sync-to-deployment-bucket.sh --update-all-lambda` | ~15s |
| Lambda stack only | `./scripts/sync-to-deployment-bucket.sh --deploy-lambda` | ~30s |
| Full deployment | `./scripts/sync-to-deployment-bucket.sh --deploy-cfn` | 5-10min |
| Frontend build + deploy | `./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend` | ~2min |
| Preview changes | `./scripts/sync-to-deployment-bucket.sh --dry-run` | ~10s |
| Clean orphans | `./scripts/sync-to-deployment-bucket.sh --clean-orphans` | varies |
| List AWS profiles | `./scripts/sync-to-deployment-bucket.sh --list-profiles` | instant |

## Architecture Overview

**5 Lambda Functions:**
- `api-handler` (index.py + rbac_middleware.py) - REST API endpoints with RBAC support
- `orchestration-stepfunctions` (orchestration_stepfunctions.py) - Step Functions orchestration
- `execution-finder` (poller/execution_finder.py) - EventBridge scheduled poller
- `execution-poller` (poller/execution_poller.py) - DRS job status updates
- `frontend-builder` (build_and_deploy.py) - CloudFormation custom resource

**7 CloudFormation Templates (1 master + 6 nested stacks):**
- master-template.yaml (parent orchestrator)
- database-stack.yaml (3 DynamoDB tables)
- lambda-stack.yaml (5 Lambda functions + IAM)
- api-stack-rbac.yaml (API Gateway + Cognito + RBAC)
- step-functions-stack.yaml (orchestration state machine)
- security-stack.yaml (optional WAF + CloudTrail)
- frontend-stack.yaml (S3 + CloudFront)

## Deployment Verification

### After Every Code Change Session

Before marking work complete, ALWAYS verify:

#### 1. S3 Bucket Has Latest Code
```bash
# Check timestamps - should be recent
aws s3 ls s3://hrp-drs-tech-adapter/lambda/ --region us-east-2
aws s3 ls s3://hrp-drs-tech-adapter/cfn/ --region us-east-2
aws s3 ls s3://hrp-drs-tech-adapter/frontend/ --region us-east-2
```

#### 2. CloudFormation Templates Are Current
```bash
# Verify master template is valid
aws cloudformation validate-template \
  --template-url https://s3.amazonaws.com/hrp-drs-tech-adapter/cfn/master-template.yaml \
  --region us-east-2
```

#### 3. Can Redeploy from Scratch
**Test command** (don't actually run, just verify it would work):
```bash
aws cloudformation create-stack \
  --stack-name hrp-drs-tech-adapter-dev-TEST \
  --template-url https://s3.amazonaws.com/hrp-drs-tech-adapter/cfn/master-template.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=hrp-drs-tech-adapter \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=SourceBucket,ParameterValue=hrp-drs-tech-adapter \
    ParameterKey=AdminEmail,ParameterValue=admin@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

### Red Flags

**Stop and fix if:**
- ❌ S3 timestamps are old (not from today)
- ❌ Local code differs from S3 artifacts
- ❌ CloudFormation template validation fails
- ❌ Deployed Lambda code doesn't match local

### Recovery Check

**Can you answer YES to:**
- [ ] If stack is deleted, can I redeploy from S3?
- [ ] Are all 7 CloudFormation templates in S3? (master + 6 nested)
- [ ] Are all 5 Lambda source files in S3?
- [ ] Is frontend source code in S3?
- [ ] Is S3 bucket synced with latest code?

**Architecture Verification:**
- [ ] 5 Lambda functions: api-handler, orchestration-stepfunctions, execution-finder, execution-poller, frontend-builder
- [ ] 6 nested stacks: database, lambda, api, step-functions, security, frontend
- [ ] S3 contains source code (NOT zip packages during sync)

If any answer is NO, run:
```bash
./scripts/sync-to-deployment-bucket.sh
```

## Update Requirements Workflow

When updating requirements documents:

### 1. Identify the change type:
- New feature → Add to appropriate requirements doc
- UI change → Update UX/UI specifications
- API change → Update Software Requirements Specification

### 2. Update the source document:
- Make changes in `docs/requirements/` files
- These are the authoritative source

### 3. Update steering summaries if needed:
- Only update if the change affects daily development
- Keep steering files focused on essential rules

### 4. Validate consistency:
- Ensure no conflicts between requirements and steering
- Requirements documents take precedence over steering

## Development Commands

### Frontend Development
```bash
cd frontend
npm install                    # Install dependencies
npm run dev                    # Start dev server (http://localhost:5173)
npm run build                  # Production build
npm run type-check             # TypeScript validation
npm run lint                   # ESLint code quality
```

### Lambda Testing
```bash
cd tests/python
pip install -r requirements.txt
pytest unit/ -v               # Unit tests
pytest integration/ -v        # Integration tests
pytest --cov=lambda           # Coverage report
```

### CloudFormation Validation
```bash
make validate                  # AWS native validation
make lint                      # cfn-lint validation
```

## Debugging Rules

### DRS Integration Debugging
```bash
# Check DRS job status
AWS_PAGER="" aws drs describe-jobs \
  --filters jobIDs=drsjob-xxx \
  --region us-east-2

# Check job logs for errors
AWS_PAGER="" aws drs describe-job-log-items \
  --job-id drsjob-xxx \
  --region us-east-2

# Check Lambda logs
AWS_PAGER="" aws logs tail /aws/lambda/function-name \
  --since 5m --region us-east-2
```

### Common DRS Errors
- **UnauthorizedOperation on CreateLaunchTemplateVersion**: Add EC2 launch template permissions
- **AccessDeniedException on CreateRecoveryInstanceForDrs**: Add `drs:CreateRecoveryInstanceForDrs`
- **LAUNCH_FAILED with No Recovery Instances**: Check CloudTrail for EC2 API failures

### Required IAM Permissions for Lambda
```yaml
# DRS Permissions
- drs:DescribeSourceServers
- drs:StartRecovery
- drs:DescribeJobs
- drs:CreateRecoveryInstanceForDrs  # CRITICAL - often missing

# EC2 Permissions (required by DRS during recovery)
- ec2:RunInstances
- ec2:CreateLaunchTemplate
- ec2:CreateLaunchTemplateVersion
- ec2:CreateVolume
- ec2:CreateTags
```

## Best Practices

### Development
- Always sync to S3 before deploying
- Use ECR Public images (avoids Docker Hub rate limits)
- Test in dev environment before production
- Monitor CloudFormation events during deployment

### Debugging
- Disable pagers for all commands (`--no-pager`, `AWS_PAGER=""`)
- Limit output with `head`/`tail` to avoid token exhaustion
- Use CloudTrail for cross-service API failure investigation
- Check IAM permissions when DRS operations fail

### File Management
- Use fsWrite/strReplace instead of opening files in editor
- Batch related file operations
- Report completion, not progress
- Minimize chat window responses to avoid token consumption

## S3 Bucket is Source of Truth

**Remember**: `s3://hrp-drs-tech-adapter` must always have the latest:
- CloudFormation templates (7 files: master-template.yaml + 6 nested stacks)
- Lambda source code (NOT zip packages during sync)
- Frontend source and built assets
- Scripts and SSM documents
- Documentation

This bucket enables redeployment from scratch at any time.

## Before Completing ANY Task

**Checklist:**
- [ ] Code changes made
- [ ] Synced to S3: `./scripts/sync-to-deployment-bucket.sh`
- [ ] Deployed via script (fast update or full deployment)
- [ ] Verified S3 has latest artifacts
- [ ] Tested deployment works
## CI/CD Best Practices (MANDATORY)

### GitHub Actions First Policy

**ALL deployments MUST use CI/CD pipeline. Manual deployment scripts are for emergencies only.**

**MANDATORY: Always check for running workflows before pushing to prevent deployment conflicts and failures.**

### Standard Development Workflow

#### 1. Local Development
- Make changes locally
- Test locally where possible
- Validate templates/code
- Run linting and type checking

#### 2. Commit and Push (Required)
```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new feature description"

# Check for running workflows before pushing
# Use project-specific safe-push script if available
git push
```

#### 3. Monitor Pipeline
- Watch CI/CD workflow progress
- Verify all stages pass: Validate → Security Scan → Build → Test → Deploy
- Check deployment outputs and status
- Validate application functionality

### Prohibited Practices (NEVER DO THESE)

#### NEVER Do These Things
- ❌ Use manual deployment scripts for regular development
- ❌ Deploy "quick fixes" without Git tracking
- ❌ Bypass pipeline for convenience
- ❌ Make production changes without code review
- ❌ Deploy untested changes manually
- ❌ Skip the pipeline "just this once"
- ❌ Push while CI/CD workflow is running (causes conflicts)
- ❌ Use `git push` directly without checking workflow status

#### Why These Are Prohibited
- **No audit trail**: Changes not tracked in Git
- **No quality gates**: Skip validation, testing, security scans
- **Inconsistent deployments**: Different process than production
- **Team blindness**: Other developers unaware of changes
- **Rollback impossible**: No Git history to revert to
- **Compliance violation**: Breaks enterprise deployment standards
- **Deployment conflicts**: Overlapping workflows cause failures and resource conflicts

### Workflow Conflict Prevention

#### Best Practices
1. **ALWAYS check for running workflows** before pushing
2. **NEVER push while a deployment is in progress** - causes conflicts and failures
3. **WAIT for completion** if a workflow is running
4. **Use safe-push scripts** if available in project to automate checks
5. **Monitor deployment** until completion before making additional changes

#### Workflow Status Indicators
- ✅ **Safe to push**: No workflows running
- ⏳ **Wait required**: Deployment in progress (wait for completion)
- ❌ **Conflict risk**: Multiple workflows would overlap
- 🚨 **Emergency only**: Force push only for critical hotfixes

### Enterprise Compliance

This workflow ensures:
- **Audit compliance**: All changes tracked in Git
- **Quality assurance**: Automated validation and testing
- **Security compliance**: Automated security scanning
- **Deployment consistency**: Same process for all environments
- **Team collaboration**: Visible deployment history
- **Rollback capability**: Git-based rollback procedures

### Emergency Manual Deployment (RESTRICTED)

#### When Manual Deployment is Allowed
- **CI/CD service outage** (confirmed service issue)
- **Critical production hotfix** when pipeline is broken
- **Pipeline debugging** (with immediate revert to Git-based deployment)

#### Emergency Procedure
1. Document the emergency situation
2. Use manual deployment only for immediate fix
3. IMMEDIATELY commit changes to Git
4. Push to restore proper CI/CD tracking
5. Report the emergency to the team

