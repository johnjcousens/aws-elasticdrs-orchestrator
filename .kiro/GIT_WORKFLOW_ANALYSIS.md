# Git Workflow Analysis

**Date**: November 30, 2024
**Purpose**: Document git commit workflow, snapshot automation, and deployment patterns

## Overview

The AWS DRS Orchestration project uses an automated workflow that integrates:
1. Git version control with conventional commits
2. S3 deployment bucket synchronization
3. CloudFormation stack deployments
4. Context preservation via checkpoints
5. Automated documentation updates

## Git Workflow Components

### 1. Makefile Automation

**Location**: `Makefile` (root directory)

**Key Targets**:

```makefile
sync-s3                  # Sync repository to S3 deployment bucket
sync-s3-build            # Build frontend and sync to S3
sync-s3-dry-run          # Preview S3 sync without making changes
enable-auto-sync         # Enable automatic S3 sync after git push
disable-auto-sync        # Disable automatic S3 sync
setup-auto-sync          # Setup automatic S3 sync (creates hook)
```

**Auto-Sync Hook** (`.git/hooks/post-push`):
- Automatically triggers after `git push`
- Runs `./scripts/sync-to-deployment-bucket.sh`
- Syncs all code to S3 deployment bucket
- Can be enabled/disabled via Makefile targets

### 2. Deployment Script

**Location**: `scripts/sync-to-deployment-bucket.sh`

**Purpose**: Comprehensive deployment automation

**Key Features**:
- Syncs code to S3 bucket: `s3://aws-drs-orchestration`
- Tags all S3 objects with git commit hash and sync time
- Supports multiple deployment modes
- Handles CloudFormation stack updates
- Builds and deploys frontend
- Packages and deploys Lambda functions

**Deployment Modes**:

```bash
# Basic sync (no deployment)
./scripts/sync-to-deployment-bucket.sh

# Fast Lambda code updates
./scripts/sync-to-deployment-bucket.sh --update-lambda-code    # ~5 seconds
./scripts/sync-to-deployment-bucket.sh --deploy-lambda         # ~30 seconds

# Frontend deployments
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend

# Full deployments
./scripts/sync-to-deployment-bucket.sh --deploy-cfn            # 5-10 minutes
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-cfn
```

**What Gets Synced**:
- CloudFormation templates (`cfn/`)
- Lambda functions (`lambda/`)
- Frontend source + dist (`frontend/`)
- Automation scripts (`scripts/`)
- SSM documents (`ssm-documents/`)
- Documentation (`docs/`)
- Root files (README.md, .gitignore, Makefile)

**S3 Object Metadata**:
Every synced file is tagged with:
- `git-commit`: Full commit hash
- `git-short`: Short commit hash
- `sync-time`: UTC timestamp

### 3. Snapshot Workflow

**Location**: `.kiro/global-rules/snapshot-workflow.md`

**Trigger**: User types "snapshot"

**Automated Steps**:

#### Step 1: Export Conversation to Checkpoint
```
use_mcp_tool("context-historian-mcp", "create_checkpoint", {
    "description": "Session snapshot",
    "include_full_conversation": true
})
```
- Creates checkpoint summary
- Exports full conversation
- Saves to `history/checkpoints/` and `history/conversations/`

#### Step 2: Update PROJECT_STATUS.md
- Reads current `docs/PROJECT_STATUS.md`
- Adds new session entry with:
  - Session number, date/time
  - Checkpoint path
  - Git commit hash (or "N/A" if not git repo)
  - Summary of accomplishments
  - Created/modified files
  - Technical achievements
  - Lines of code changes
  - Next steps

#### Step 3: Check Git Repository Status
```bash
git rev-parse --is-inside-work-tree 2>/dev/null
```
- Determines if current directory is a git repository
- Conditional execution of git workflow

#### Step 3.5: AWS Deployment (Conditional)
**Only if**: `scripts/sync-to-deployment-bucket.sh` exists

```bash
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-cfn
```

**Deployment Actions**:
1. Build frontend (if applicable)
2. Sync all code to S3 deployment bucket
3. Package Lambda function with dependencies
4. Upload Lambda package to S3
5. Update Lambda CloudFormation stack
6. Update Frontend CloudFormation stack
7. Wait for both stacks to complete

**Captures**:
- Deployment results for git commit message
- Deployment duration
- Stack update status

#### Step 4: Automated Git Workflow (Conditional)
**Only if**: Git repository detected

```bash
# Stage all changes (respects .gitignore)
git add .

# Generate conventional commit message
git commit -m "[conventional commit message]"

# Push to remote
git push origin main

# Get commit hash for documentation
git rev-parse HEAD
```

## Conventional Commit Format

### Structure
```
<type>: Session [N] snapshot + deployment - [brief description]

- Session achievements: [key accomplishments]
- Files created: [count] ([highlighted files])
- Files modified: [count] ([key modifications])
- Technical progress: [improvements and fixes]
- AWS Deployment: [if applicable]
  - Lambda: [stack-name] (UPDATE_COMPLETE/No changes)
  - Frontend: [stack-name] (UPDATE_COMPLETE/No changes)
  - Duration: [seconds]s
- Lines of code: [insertions/deletions]

Checkpoint: history/conversations/conversation_export_[timestamp].md
Co-authored-by: context-historian-mcp
```

### Commit Types
- `feat`: New functionality
- `fix`: Bug fixes
- `docs`: Documentation only
- `refactor`: Code improvements
- `chore`: Build/tooling changes
- `test`: Test additions/modifications

### Example Commit
```
feat: Session 64 snapshot + deployment - Global rules integration

- Session achievements: Integrated global Cline rules and MCPs
- Files created: 7 (.kiro/global-rules/*, .kiro/MCP_CONFIGURATION.md)
- Files modified: 3 (.kiro/settings/mcp.json, Makefile, README.md)
- Technical progress: Enabled all MCPs, created symbolic links
- AWS Deployment:
  - Lambda: drs-orchestration-test-lambda (No changes)
  - Frontend: drs-orchestration-test-frontend (No changes)
  - Duration: 45s
- Lines of code: +1,234 insertions, -56 deletions

Checkpoint: history/conversations/conversation_export_20241130_215700.md
Co-authored-by: context-historian-mcp
```

## Git Workflow Patterns

### Pattern 1: Development Session with Snapshot

```bash
# 1. Work on features (Kiro makes changes)
# ... code changes ...

# 2. User types "snapshot"
# Kiro automatically:
#   - Creates checkpoint
#   - Updates PROJECT_STATUS.md
#   - Checks git status
#   - Deploys to AWS (if applicable)
#   - Commits all changes
#   - Pushes to remote

# 3. Post-push hook triggers (if enabled)
#   - Syncs to S3 deployment bucket
#   - Tags objects with git commit hash
```

### Pattern 2: Manual Deployment

```bash
# Sync to S3 without deployment
make sync-s3

# Build frontend and sync
make sync-s3-build

# Preview changes (dry-run)
make sync-s3-dry-run

# Fast Lambda update
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Full deployment
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-cfn
```

### Pattern 3: Auto-Sync Setup

```bash
# Setup auto-sync (creates post-push hook)
make setup-auto-sync

# Enable auto-sync
make enable-auto-sync

# Now every git push automatically syncs to S3
git push origin main
# ... auto-sync runs ...

# Disable auto-sync
make disable-auto-sync
```

## Git Repository Integrity Rules

**From**: `.kiro/global-rules/amazon-builder-context.md`

### Absolute Rules (NEVER VIOLATE)

1. **Never delete Git files or directories**
   - `.git` directory is sacrosanct
   - Never run commands that corrupt history
   - No `git filter-branch`, `git reset --hard`, etc.

2. **Never rewrite Git history**
   - No force push (`git push --force`)
   - No amending commits (even local)
   - No rebasing branches
   - No interactive rebase
   - Treat local history with same reverence as remote

3. **Never push changes off host** (Amazon-specific)
   - All Git operations remain on local system
   - No configuring remote repositories
   - No pushing to external services

### Rationale
- Maintain complete project evolution history
- Enable reversion to previous states
- Provide safety net for errors

### Emergency Recovery
If rules violated:
1. Do not attempt further Git operations
2. Document what happened and what was lost
3. Consider creating new branch from last known good state
4. Preserve working directory before attempting recovery

## Commit Best Practices

**From**: `.kiro/global-rules/amazon-builder-context.md`

### Conventional Commits Specification

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]

<SIM URL>
```

### Best Practices
- Use imperative mood ("add" not "added" or "adds")
- Don't end subject line with period
- Limit subject line to 50 characters
- Capitalize subject line
- Separate subject from body with blank line
- Use body to explain what and why vs. how
- Wrap body at 72 characters

### Git Command Patterns

**Always use `-P` flag for paginated output**:
```bash
# Viewing commit history
git -P log -n 100
git -P log --oneline -n 100
git -P log --graph --oneline -n 100

# Viewing differences
git -P diff
git -P diff --cached
git -P diff HEAD~1

# Viewing file content
git -P show
git -P blame <file>
```

**Standard commands** (no `-P` needed):
```bash
git status
git add
git commit
git checkout
```

## Deployment Architecture

### CloudFormation Stacks

**Parent Stack**: `drs-orchestration-test`
- Orchestrates all nested stacks
- Propagates parameters to children
- Aggregates outputs

**Nested Stacks**:
1. `drs-orchestration-test-database` - DynamoDB tables
2. `drs-orchestration-test-lambda` - Lambda functions + IAM
3. `drs-orchestration-test-api` - Cognito + API Gateway + Step Functions
4. `drs-orchestration-test-security` - WAF + CloudTrail (optional)
5. `drs-orchestration-test-frontend` - S3 + CloudFront

### Deployment Timing

| Operation | Duration | Method |
|-----------|----------|--------|
| S3 Sync Only | ~10s | `make sync-s3` |
| Lambda Code Update | ~5s | `--update-lambda-code` |
| Lambda Stack | ~30s | `--deploy-lambda` |
| Frontend Stack | ~2min | `--deploy-frontend` |
| Full Deployment | 5-10min | `--deploy-cfn` |

### S3 Bucket Structure

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
│   └── deployment-package.zip
├── frontend/                     # Frontend build
│   ├── dist/
│   └── src/
├── scripts/                      # Automation scripts
├── ssm-documents/                # SSM automation
└── docs/                         # Documentation
```

## Integration with Snapshot Workflow

### Complete Snapshot Flow

```
User types "snapshot"
    ↓
1. Context Historian MCP creates checkpoint
    ↓
2. Update PROJECT_STATUS.md with session details
    ↓
3. Check if git repository
    ↓
4. Deploy to AWS (if deployment script exists)
    ├─ Build frontend
    ├─ Sync to S3
    ├─ Package Lambda
    ├─ Update CloudFormation stacks
    └─ Capture deployment results
    ↓
5. Git workflow (if git repo)
    ├─ git add .
    ├─ git commit -m "[conventional commit]"
    └─ git push origin main
    ↓
6. Post-push hook (if enabled)
    └─ Sync to S3 deployment bucket
    ↓
7. Create new task with preserved context
```

### Conditional Execution

**Git Workflow Runs If**:
- `git rev-parse --is-inside-work-tree` succeeds
- Current directory is a git repository

**AWS Deployment Runs If**:
- `scripts/sync-to-deployment-bucket.sh` exists
- Project has AWS infrastructure

**Post-Push Hook Runs If**:
- `.git/hooks/post-push` exists and is executable
- Auto-sync is enabled via `make enable-auto-sync`

## Environment Configuration

### AWS Credentials
**Location**: `~/.aws/credentials`

**Profiles**:
- `[default]` - Default AWS profile
- `[438465159935_AdministratorAccess]` - Admin access for TEST environment

**Current Configuration**:
- Account: 438465159935
- Region: us-east-1
- Role: AdministratorAccess
- User: jocousen@amazon.com

### Deployment Configuration
**Location**: `scripts/sync-to-deployment-bucket.sh`

```bash
BUCKET="aws-drs-orchestration"
REGION="us-east-1"
AWS_PROFILE="438465159935_AdministratorAccess"
PROJECT_NAME="drs-orchestration"
ENVIRONMENT="test"
PARENT_STACK_NAME="drs-orchestration-test"
```

## Summary

The git workflow is highly automated and integrated:

1. **Development**: Kiro makes code changes
2. **Snapshot**: User types "snapshot" to trigger automation
3. **Checkpoint**: Context Historian preserves session state
4. **Documentation**: PROJECT_STATUS.md updated automatically
5. **Deployment**: AWS infrastructure updated via CloudFormation
6. **Git Commit**: Conventional commit with deployment details
7. **Git Push**: Changes pushed to remote repository
8. **S3 Sync**: Post-push hook syncs to deployment bucket
9. **Context Preservation**: New task created with full context

**Key Benefits**:
- Zero manual git operations required
- Automatic deployment on snapshot
- Complete audit trail via commits
- Context preservation across sessions
- S3 deployment bucket always in sync
- CloudFormation stacks always up-to-date

**Key Files**:
- `Makefile` - Automation targets
- `scripts/sync-to-deployment-bucket.sh` - Deployment automation
- `.kiro/global-rules/snapshot-workflow.md` - Snapshot automation
- `.kiro/global-rules/amazon-builder-context.md` - Git best practices
- `.git/hooks/post-push` - Auto-sync hook (optional)

---

**Status**: ✅ Workflow Documented and Understood
**Last Updated**: November 30, 2024
