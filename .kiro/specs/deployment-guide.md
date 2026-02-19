---
inclusion: always
---

# Deployment & CI/CD Guide

Essential deployment workflows and verification procedures.

## Critical Rules

### NEVER Execute These Commands Directly
```bash
❌ aws lambda update-function-code
❌ aws cloudformation deploy
❌ aws s3 sync (for deployments)
❌ aws cloudfront create-invalidation
```

### ALWAYS Use Deployment Scripts
```bash
✅ ./scripts/deploy.sh dev
✅ ./scripts/sync-to-deployment-bucket.sh
```

## Deployment Architecture

**S3 Bucket = Source of Truth**

```
Local Code → S3 Deployment Bucket → CloudFormation → AWS Resources
```

### S3 Bucket Structure
```
s3://deployment-bucket/
├── cfn/          # CloudFormation templates
├── lambda/       # Lambda packages (.zip)
└── frontend/     # Frontend build artifacts
```

## Standard Workflow

### 1. Make Changes
```bash
# Edit code
vim lambda/index.py
vim frontend/src/App.tsx
vim cfn/template.yaml
```

### 2. Sync to S3 (REQUIRED)
```bash
./scripts/sync-to-deployment-bucket.sh
```

### 3. Deploy
```bash
# Full deployment
./scripts/deploy.sh dev

# Quick (skip tests/security)
./scripts/deploy.sh dev --quick

# Lambda only
./scripts/deploy.sh dev --lambda-only

# Frontend only
./scripts/deploy.sh dev --frontend-only
```

### 4. Verify
```bash
# Check S3 timestamps
AWS_PAGER="" aws s3 ls s3://deployment-bucket/lambda/

# Check Lambda update
AWS_PAGER="" aws lambda get-function \
  --function-name my-function \
  --query 'Configuration.LastModified'
```

## Deployment Verification Checklist

After EVERY code change session:

- [ ] S3 has latest code (check timestamps)
- [ ] Local code matches S3 artifacts
- [ ] CloudFormation templates validated
- [ ] Can redeploy from scratch using S3
- [ ] Changes committed to git

### Verification Commands
```bash
# S3 timestamps (should be recent)
AWS_PAGER="" aws s3 ls s3://deployment-bucket/cfn/
AWS_PAGER="" aws s3 ls s3://deployment-bucket/lambda/

# Validate CloudFormation
aws cloudformation validate-template \
  --template-url https://s3.amazonaws.com/deployment-bucket/cfn/template.yaml

# Test redeployment (don't actually run)
aws cloudformation create-stack \
  --stack-name test-stack \
  --template-url https://s3.amazonaws.com/deployment-bucket/cfn/template.yaml \
  --capabilities CAPABILITY_IAM
```

## Terminal Rules (CRITICAL)

### Always Disable Pagers
```bash
# Git - ALWAYS use --no-pager
git --no-pager status
git --no-pager log -10
git --no-pager diff

# AWS CLI - ALWAYS use AWS_PAGER=""
AWS_PAGER="" aws drs describe-jobs
AWS_PAGER="" aws cloudformation describe-stacks

# Limit output
command | head -50
command | tail -100
command > output.txt
```

### Long Commit Messages
```bash
# NEVER: git commit -m "very long message..."
# ALWAYS: Use temp file
echo "message" > .git_commit_msg.txt
git --no-pager commit -F .git_commit_msg.txt
rm .git_commit_msg.txt
```

## File Writing Rules

- **Just write files** using tools (fsWrite/strReplace)
- **Do NOT open files** in editor after writing
- **Batch multiple edits** when possible
- **Report completion, not progress**

## Deployment Scripts

### Sync Script
```bash
#!/bin/bash
# scripts/sync-to-deployment-bucket.sh

BUCKET="${DEPLOYMENT_BUCKET:-my-bucket}"
REGION="${AWS_REGION:-us-east-2}"

# Sync CloudFormation
aws s3 sync cfn/ s3://$BUCKET/cfn/ --delete

# Package Lambda
cd lambda
zip -r function.zip index.py package/
aws s3 cp function.zip s3://$BUCKET/lambda/

# Build and sync frontend
cd frontend
npm run build
aws s3 sync dist/ s3://$BUCKET/frontend/dist/
```

### Deploy Script
```bash
#!/bin/bash
# scripts/deploy.sh

ENV=$1
QUICK=false
LAMBDA_ONLY=false

# Parse options
while [[ $# -gt 0 ]]; do
  case $1 in
    --quick) QUICK=true ;;
    --lambda-only) LAMBDA_ONLY=true ;;
    *) shift ;;
  esac
  shift
done

# 1. Validation
if [ "$QUICK" = false ]; then
  cfn-lint cfn/*.yaml
  flake8 lambda/
  npm run lint
fi

# 2. Tests
if [ "$QUICK" = false ]; then
  pytest
  npm test
fi

# 3. Sync to S3
./scripts/sync-to-deployment-bucket.sh

# 4. Deploy
if [ "$LAMBDA_ONLY" = true ]; then
  aws lambda update-function-code \
    --function-name my-function-$ENV \
    --s3-bucket $BUCKET \
    --s3-key lambda/function.zip
else
  aws cloudformation deploy \
    --template-url https://$BUCKET.s3.$REGION.amazonaws.com/cfn/template.yaml \
    --stack-name my-stack-$ENV \
    --capabilities CAPABILITY_IAM
fi
```

## Makefile
```makefile
.PHONY: sync deploy deploy-lambda

sync:
	./scripts/sync-to-deployment-bucket.sh

deploy:
	./scripts/deploy.sh dev

deploy-lambda:
	./scripts/deploy.sh dev --lambda-only

deploy-quick:
	./scripts/deploy.sh dev --quick
```

## Rollback

```bash
# List S3 versions
AWS_PAGER="" aws s3api list-object-versions \
  --bucket deployment-bucket \
  --prefix lambda/function.zip

# Restore previous version
aws lambda update-function-code \
  --function-name my-function \
  --s3-bucket deployment-bucket \
  --s3-key lambda/function.zip \
  --s3-object-version {version-id}

# Or rollback CloudFormation
aws cloudformation rollback-stack --stack-name my-stack
```

## Best Practices

1. **Always sync before deploy** - Never deploy from local files
2. **Use S3 versioning** - Enables rollback
3. **Validate before deploy** - Run linters and tests
4. **Test in dev first** - Deploy to dev before production
5. **Monitor deployments** - Watch CloudFormation events
6. **Keep artifacts in sync** - Local, S3, and deployed should match
7. **Commit before deploy** - Git tracks all changes

## Red Flags

Stop and fix if:
- ❌ S3 timestamps are old (not from today)
- ❌ Local code differs from S3
- ❌ CloudFormation validation fails
- ❌ Deployed code doesn't match local

## Recovery Questions

Can you answer YES to all?
- [ ] If stack is deleted, can I redeploy from S3?
- [ ] Are all templates in S3?
- [ ] Are all Lambda packages in S3?
- [ ] Is S3 synced with latest code?

If NO to any, run: `./scripts/sync-to-deployment-bucket.sh`
