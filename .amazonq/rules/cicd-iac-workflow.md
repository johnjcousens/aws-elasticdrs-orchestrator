# CI/CD and Infrastructure as Code Workflow

## CRITICAL: Always Update IaC with Code Changes

**NEVER deploy code changes without updating CloudFormation templates and S3 artifacts.**

## Development Workflow

### Local Development Process

#### 1. Make Code Changes
- Update Lambda functions in `lambda/` (5 active functions)
- Update frontend in `frontend/`
- Update CloudFormation templates in `cfn/` (6 nested stacks)

#### 2. Sync to S3 Deployment Bucket (REQUIRED)
```bash
./scripts/sync-to-deployment-bucket.sh
```

**This syncs:**
- CloudFormation templates → `s3://aws-drs-orchestration/cfn/`
- Lambda source code → `s3://aws-drs-orchestration/lambda/`
- Frontend source → `s3://aws-drs-orchestration/frontend/`

#### 3. Deploy Changes (REQUIRED)

**Fast Lambda updates (~5 seconds):**
```bash
./scripts/sync-to-deployment-bucket.sh --update-lambda-code
```

**Full CloudFormation deployment (5-10 minutes):**
```bash
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

**Frontend build and deploy:**
```bash
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend
```

#### 4. Verify Deployment
```bash
# Check stack status
aws cloudformation describe-stacks --stack-name drs-orchestration-dev --region us-east-1

# Verify S3 has latest
aws s3 ls s3://aws-drs-orchestration/lambda/ --region us-east-1
```

### GitLab CI/CD Pipeline

**6-Stage Pipeline:**
```
validate → lint → build → test → deploy-infra → deploy-frontend
```

**Key Features:**
- ECR Public images (avoids Docker Hub rate limits)
- Builds 5 Lambda packages individually
- Automated deployment for main/dev branches
- Manual production deployment
- Complete artifact upload to S3 deployment bucket

## Rules for Kiro

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
| Full deployment | `./scripts/sync-to-deployment-bucket.sh --deploy-cfn` | 5-10min |
| Frontend build + deploy | `./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend` | ~2min |
| Preview changes | `./scripts/sync-to-deployment-bucket.sh --dry-run` | ~10s |

## Architecture Overview

**5 Lambda Functions:**
- `api-handler` (index.py) - REST API endpoints
- `orchestration-stepfunctions` - Step Functions orchestration
- `execution-finder` - EventBridge scheduled poller
- `execution-poller` - DRS job status updates
- `frontend-builder` - CloudFormation custom resource

**6 Nested CloudFormation Stacks:**
- database-stack.yaml (DynamoDB tables)
- lambda-stack.yaml (Lambda functions + IAM)
- api-stack.yaml (API Gateway + Cognito)
- step-functions-stack.yaml (orchestration)
- security-stack.yaml (optional WAF + CloudTrail)
- frontend-stack.yaml (S3 + CloudFront)

## Before Completing ANY Task

**Checklist:**
- [ ] Code changes made
- [ ] Synced to S3: `./scripts/sync-to-deployment-bucket.sh`
- [ ] Deployed via script (fast update or full deployment)
- [ ] Verified S3 has latest artifacts
- [ ] Tested deployment works

## S3 Bucket is Source of Truth

**Remember**: `s3://aws-drs-orchestration` must always have the latest:
- CloudFormation templates (7 files: master + 6 nested)
- Lambda source code (NOT zip packages during sync)
- Frontend source and built assets

This bucket enables redeployment from scratch at any time.
