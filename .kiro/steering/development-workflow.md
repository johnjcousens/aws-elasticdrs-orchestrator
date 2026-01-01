# Development Workflow

## Terminal Rules (CRITICAL)

### Output Suppression - Avoid Token Exhaustion
```bash
# ALWAYS suppress output to avoid crashing terminal
command > /dev/null 2>&1
command | head -5
command | tail -5
```

### Git Commands - ALWAYS use --no-pager
```bash
git --no-pager status -s
git --no-pager log --oneline -5
git --no-pager diff --stat
git --no-pager push -q
git --no-pager pull -q
```

### AWS CLI - ALWAYS use AWS_PAGER=""
```bash
AWS_PAGER="" aws drs describe-jobs --region us-east-1
AWS_PAGER="" aws cloudformation describe-stacks --stack-name stack-name
```

### Long Commit Messages
```bash
# NEVER use: git commit -m "long message..."
# ALWAYS use temp file:
# 1. fsWrite to .git_commit_msg.txt
# 2. git --no-pager commit -F .git_commit_msg.txt
# 3. rm .git_commit_msg.txt
```

## File Writing Rules

- **Just write files** using fsWrite/strReplace tools
- **Do NOT open files in editor** after writing (causes autocomplete issues)
- **Batch multiple edits** when possible
- **Report completion, not progress**

## CI/CD and Deployment

### S3 Deployment Bucket (Source of Truth)
```
s3://aws-drs-orchestration/
├── cfn/                     # CloudFormation templates (7 total)
├── lambda/                  # Lambda deployment packages (5 functions)
└── frontend/                # Frontend build artifacts
```

### Primary Deployment Script
```bash
# Sync everything to S3 deployment bucket
./scripts/sync-to-deployment-bucket.sh

# Fast Lambda code update (no CloudFormation)
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Build and deploy frontend
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend

# Dry run (preview changes)
./scripts/sync-to-deployment-bucket.sh --dry-run
```

### Development Commands

#### Frontend Development
```bash
cd frontend
npm install                    # Install dependencies
npm run dev                    # Start dev server (http://localhost:5173)
npm run build                  # Production build
npm run type-check             # TypeScript validation
npm run lint                   # ESLint code quality
```

#### Lambda Testing
```bash
cd tests/python
pip install -r requirements.txt
pytest unit/ -v               # Unit tests
pytest integration/ -v        # Integration tests
pytest --cov=lambda           # Coverage report
```

#### CloudFormation Validation
```bash
make validate                  # AWS native validation
make lint                      # cfn-lint validation
```

### Deployment Checklist
- [ ] Code changes made and tested locally
- [ ] CloudFormation templates updated (if infrastructure changed)
- [ ] Synced to S3: `./scripts/sync-to-deployment-bucket.sh`
- [ ] Deployed via script (not manual)
- [ ] Verified S3 has latest artifacts
- [ ] Tested deployment works
- [ ] Committed changes to git

## Debugging Rules

### DRS Integration Debugging
```bash
# Check DRS job status
AWS_PAGER="" aws drs describe-jobs \
  --filters jobIDs=drsjob-xxx \
  --region us-east-1

# Check job logs for errors
AWS_PAGER="" aws drs describe-job-log-items \
  --job-id drsjob-xxx \
  --region us-east-1

# Check Lambda logs
AWS_PAGER="" aws logs tail /aws/lambda/function-name \
  --since 5m --region us-east-1
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

## Update Requirements Workflow

When updating requirements documents:

1. **Identify the change type**:
   - New feature → Add to appropriate requirements doc
   - UI change → Update UX/UI specifications
   - API change → Update Software Requirements Specification

2. **Update the source document**:
   - Make changes in `docs/requirements/` files
   - These are the authoritative source

3. **Update steering summaries if needed**:
   - Only update if the change affects daily development
   - Keep steering files focused on essential rules

4. **Validate consistency**:
   - Ensure no conflicts between requirements and steering
   - Requirements documents take precedence over steering

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