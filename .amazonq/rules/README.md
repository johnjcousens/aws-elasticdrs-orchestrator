# Amazon Q Project Rules

These rules ensure proper CI/CD practices and prevent loss of deployment progress.

## Active Rules

### 1. cicd-iac-workflow.md
**Purpose**: Enforce proper Infrastructure as Code workflow  
**Key Requirement**: Always sync code to S3 and deploy via CloudFormation

### 2. deployment-verification.md
**Purpose**: Verify deployment can be reproduced  
**Key Requirement**: Check S3 bucket has latest artifacts before completing work

## How These Rules Help

**Problem We're Preventing:**
- Code deployed manually without updating CloudFormation
- S3 artifacts becoming stale
- Inability to redeploy from scratch
- Loss of progress when stack is deleted

**Solution:**
- Always sync to S3: `./scripts/sync-to-deployment-bucket.sh`
- Always deploy via CloudFormation
- Always verify S3 has latest before completing work

## Quick Commands

```bash
# Sync everything to S3
./scripts/sync-to-deployment-bucket.sh

# Deploy changes
./scripts/sync-to-deployment-bucket.sh --deploy-cfn

# Verify S3 is current
aws s3 ls s3://aws-drs-orchestration/lambda/ --region us-east-1
```

## For Kiro

These rules are automatically applied to all interactions. Follow the workflow in `cicd-iac-workflow.md` for every code change.
