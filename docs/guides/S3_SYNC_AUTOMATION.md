# S3 Deployment Repository Automation

This document covers the automated S3 sync workflow for the AWS DRS Orchestration solution.

## Overview

The complete repository is maintained at `s3://aws-drs-orchestration` with automated sync, versioning, and git commit tracking.

## Features

### S3 Versioning Enabled
- Every file version preserved for recovery
- Can restore accidentally deleted files
- Complete version history available

### Git Commit Tagging
- All S3 objects tagged with source git commit hash
- Sync timestamp included in metadata
- Query S3 by commit for audit trail

### Automated Sync Script

```bash
# Sync complete repository to S3
./scripts/sync-to-deployment-bucket.sh

# Build frontend and sync
./scripts/sync-to-deployment-bucket.sh --build-frontend

# Preview changes without executing
./scripts/sync-to-deployment-bucket.sh --dry-run
```

## Auto-Sync on Git Push

**Auto-sync is enabled by default!**

The repository includes a git `post-push` hook that automatically syncs to S3 after every successful `git push`.

### How It Works

1. **You commit and push changes:**
   ```bash
   git add .
   git commit -m "feat: Add new feature"
   git push origin main
   ```

2. **Post-push hook automatically triggers:**
   - Detects current git commit hash
   - Tags all S3 objects with commit metadata
   - Syncs changes to `s3://aws-drs-orchestration`
   - Reports success/failure

3. **S3 is automatically updated:**
   - All files tagged with latest commit
   - Versioning preserves previous versions
   - No manual sync needed!

### Enable/Disable Auto-Sync

```bash
# Disable auto-sync (sync only on demand)
make disable-auto-sync

# Re-enable auto-sync
make enable-auto-sync

# Check current status
make help  # Shows "✅ Auto-sync ENABLED" or "⚠️ Auto-sync DISABLED"
```

## Quick Commands

```bash
# Manual sync
make sync-s3

# Build frontend and sync
make sync-s3-build

# Preview changes (dry-run)
make sync-s3-dry-run

# Direct script usage (all options)
./scripts/sync-to-deployment-bucket.sh [--build-frontend] [--dry-run]
```

## Query S3 by Git Commit

```bash
# Find all files from specific deployment
aws s3api list-objects-v2 \
  --bucket aws-drs-orchestration \
  --query "Contents[?Metadata.'git-commit'=='a93a255'].[Key]" \
  --output text

# View object metadata
aws s3api head-object \
  --bucket aws-drs-orchestration \
  --key cfn/master-template.yaml \
  --query "Metadata"
```

## Recovery from S3

### Primary: Git Checkout + Re-sync

```bash
# Restore to previous commit
git checkout abc1234
./scripts/sync-to-deployment-bucket.sh

# Return to main
git checkout main
```

### Backup: S3 Versioning

```bash
# List all versions of a file
aws s3api list-object-versions \
  --bucket aws-drs-orchestration \
  --prefix cfn/master-template.yaml

# Restore specific version
aws s3api copy-object \
  --copy-source "aws-drs-orchestration/cfn/master-template.yaml?versionId=VERSION_ID" \
  --bucket aws-drs-orchestration \
  --key cfn/master-template.yaml
```

## S3 Repository Structure

```
s3://aws-drs-orchestration/
├── cfn/                          # CloudFormation templates
│   ├── master-template.yaml
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-stack.yaml
│   ├── security-stack.yaml
│   └── frontend-stack.yaml
├── lambda/                       # Lambda packages
│   ├── api-handler.zip
│   ├── orchestration.zip
│   └── frontend-builder.zip
└── frontend/                     # Frontend build artifacts
    └── dist/
```

## Workflow Benefits

- **Zero Manual Effort** - S3 stays in sync automatically
- **Always Audit Trail** - Every S3 object tagged with git commit
- **Version Protection** - S3 versioning enabled for all files
- **Fail-Safe** - Hook fails if sync fails (prevents incomplete updates)
- **Flexible** - Can disable and sync manually when needed
