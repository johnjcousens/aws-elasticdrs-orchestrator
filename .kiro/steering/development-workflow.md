# Development Workflow

## CRITICAL: GitHub Actions First Policy + Conflict Prevention

**ALL deployments MUST use GitHub Actions CI/CD pipeline. Manual deployment scripts are for emergencies only.**

**MANDATORY: Always check for running workflows before pushing to prevent deployment conflicts and failures.**

## Standard Development Workflow

### 1. Local Development
```bash
# Make your changes locally
# Test locally where possible
# Validate CloudFormation templates
make validate

# MANDATORY: Check deployment scope before committing
./scripts/check-deployment-scope.sh
```

### 2. Commit and Push (Required)
```bash
# Stage changes
git add .

# MANDATORY: Preview deployment scope and time estimates
./scripts/check-deployment-scope.sh

# Commit with descriptive message
git commit -m "feat: add new feature description"

# MANDATORY: Check for running workflows before pushing
./scripts/check-workflow.sh && git push

# OR use the safe push script (recommended)
./scripts/safe-push.sh
```

### 3. Monitor Pipeline
- Watch GitHub Actions workflow progress
- Verify all stages pass: Validate → Security Scan → Build → Test → Deploy
- Check deployment outputs and stack status
- Validate application functionality

## Emergency Manual Deployment (RESTRICTED)

### When Manual Sync is Allowed
- **GitHub Actions service outage** (confirmed AWS/GitHub issue)
- **Critical production hotfix** when pipeline is broken
- **Pipeline debugging** (with immediate revert to Git-based deployment)

### Emergency Procedure
```bash
# ONLY in genuine emergencies
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# IMMEDIATELY follow up with proper Git commit
git add .
git commit -m "emergency: describe the critical fix"
git push
```

## Prohibited Practices

### NEVER Do These Things
- ❌ Use sync script for regular development
- ❌ Deploy "quick fixes" without Git tracking
- ❌ Bypass pipeline for convenience
- ❌ Make production changes without code review
- ❌ Deploy untested changes manually
- ❌ Skip the pipeline "just this once"
- ❌ **Push while GitHub Actions workflow is running** (causes conflicts)
- ❌ **Use `git push` directly without checking workflow status**

### Why These Are Prohibited
- **No audit trail**: Changes not tracked in Git
- **No quality gates**: Skip validation, testing, security scans
- **Inconsistent deployments**: Different process than production
- **Team blindness**: Other developers unaware of changes
- **Rollback impossible**: No Git history to revert to
- **Compliance violation**: Breaks enterprise deployment standards
- **Deployment conflicts**: Overlapping workflows cause failures and resource conflicts

## Workflow Conflict Prevention (MANDATORY)

### Safe Push Scripts

Two scripts are available to prevent GitHub Actions conflicts:

#### Quick Check: `./scripts/check-workflow.sh`
```bash
# Quick status check before manual push
./scripts/check-workflow.sh && git push

# Returns exit code 0 if safe to push, 1 if workflow running
```

#### Safe Push: `./scripts/safe-push.sh` (RECOMMENDED)
```bash
# Automatically checks workflows and pushes when safe
./scripts/safe-push.sh

# Push to specific branch
./scripts/safe-push.sh main

# Emergency force push (skip workflow check)
./scripts/safe-push.sh --force
```

### Prerequisites (One-time Setup)
```bash
# Install GitHub CLI
brew install gh

# Authenticate with GitHub
gh auth login
```

### MANDATORY Workflow Check Rules

1. **ALWAYS check deployment scope** before committing: `./scripts/check-deployment-scope.sh`
2. **ALWAYS check for running workflows** before pushing
3. **NEVER push while a deployment is in progress** - this causes conflicts and failures
4. **WAIT for completion** if a workflow is running (max 30 minutes)
5. **Use safe-push.sh script** instead of manual `git push` to automate checks
6. **Monitor deployment** until completion before making additional changes

### Workflow Status Indicators

- ✅ **Safe to push**: No workflows running
- ⏳ **Wait required**: Deployment in progress (wait for completion)
- ❌ **Conflict risk**: Multiple workflows would overlap
- 🚨 **Emergency only**: Use `--force` flag only for critical hotfixes

## Pipeline Troubleshooting

### If GitHub Actions Fails
1. **Check the logs** in GitHub Actions tab
2. **Fix the issue** in your local code
3. **Commit and push** the fix
4. **Let the pipeline retry** - don't bypass it

### Common Pipeline Issues
- **CloudFormation validation errors**: Fix template syntax
- **Security scan failures**: Address Bandit/Safety findings
- **Test failures**: Fix failing unit tests
- **Build errors**: Fix TypeScript/Python syntax errors

## Development Best Practices

### Code Quality
- Run `make validate` before committing
- Fix linting errors locally
- Write tests for new functionality
- Follow Python and TypeScript coding standards

### Git Practices
- Use conventional commit messages: `feat:`, `fix:`, `docs:`, etc.
- Keep commits focused and atomic
- Write descriptive commit messages
- **ALWAYS use `./scripts/safe-push.sh` instead of `git push`**
- **Check workflow status before pushing**: `./scripts/check-workflow.sh`
- **Wait for deployment completion** before making additional changes

### Deployment Verification
- Check CloudFormation stack status after deployment
- Verify API endpoints are working
- Test frontend functionality
- Monitor CloudWatch logs for errors

## Enterprise Compliance

This workflow ensures:
- **Audit compliance**: All changes tracked in Git
- **Quality assurance**: Automated validation and testing
- **Security compliance**: Automated security scanning
- **Deployment consistency**: Same process for all environments
- **Team collaboration**: Visible deployment history
- **Rollback capability**: Git-based rollback procedures

## Emergency Contact

If you encounter a genuine emergency requiring manual deployment:
1. Document the emergency situation
2. Use manual sync script only for immediate fix
3. IMMEDIATELY commit changes to Git
4. Push to restore proper CI/CD tracking
5. Report the emergency to the team