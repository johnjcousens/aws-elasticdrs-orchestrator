# GitHub Repository Security Setup Guide

> **Complete guide for securing the AWS DRS Orchestration repository with branch protection, access controls, and security features**

## Prerequisites

- Repository admin access
- GitHub account with 2FA enabled
- Basic understanding of Git workflows

## Quick Setup Checklist

- [ ] Configure main branch protection
- [ ] Set up development branch protection
- [ ] Configure repository access controls
- [ ] Enable security features
- [ ] Set up required status checks
- [ ] Create CODEOWNERS file
- [ ] Test protection rules

---

## 1. Branch Protection Rules

### Step 1: Access Branch Protection Settings

1. **Navigate to your repository** on GitHub
2. Click **Settings** tab (requires admin access)
3. In the left sidebar, click **Branches**
4. Click **Add rule** button

> 💡 **Tip**: If you don't see the Settings tab, you don't have admin access to the repository.

### Step 2: Configure Main Branch Protection

**Branch name pattern**: `main`

#### Required Pull Request Settings
✅ **Require a pull request before merging**
- **Require approvals**: `1` (minimum for small teams, `2+` for larger teams)
- ✅ **Dismiss stale PR approvals when new commits are pushed**
  - *Why*: Ensures reviewers see the latest changes
- ✅ **Require review from code owners**
  - *Why*: Ensures domain experts review relevant changes

#### Status Check Requirements
✅ **Require status checks to pass before merging**
- ✅ **Require branches to be up to date before merging**
  - *Why*: Prevents integration issues from outdated branches

**Required status checks** (add these if available):
- `validate` - CloudFormation template validation
- `security-scan` - Security vulnerability scanning
- `test` - Unit and integration tests
- `build` - Build verification

> ⚠️ **Note**: Status checks only appear after they've run at least once. You may need to create a PR first to see them.

#### Additional Protection Settings
✅ **Require conversation resolution before merging**
- *Why*: Ensures all review comments are addressed

✅ **Restrict pushes that create files larger than 100MB**
- *Why*: Prevents accidental large file commits

✅ **Do not allow bypassing the above settings**
- *Why*: Removes admin override capability for consistency

#### Advanced Settings (Optional)
- ✅ **Require linear history** - Forces rebase/squash merging
- ✅ **Require deployments to succeed** - If using GitHub deployments

### Step 3: Configure Development Branch Protection

**Branch name pattern**: `develop`

**Settings**: Apply the same settings as main branch

> 💡 **Best Practice**: Protect all long-lived branches with the same rigor

### Step 4: Save and Verify

1. Click **Create** to save the rule
2. Verify the rule appears in the branch protection list
3. Test by attempting to push directly to main (should be blocked)

---

## 2. Repository Access Control

### Step 1: Review Current Access

1. Go to **Settings → Manage access**
2. Review all current collaborators
3. Remove any unnecessary access

### Step 2: Set Appropriate Permission Levels

| Role | Permission Level | Use Case |
|------|------------------|----------|
| **Admin** | Admin | Repository owner only |
| **Maintainer** | Maintain | Trusted maintainers, release managers |
| **Developer** | Write | Core contributors, regular developers |
| **Reviewer** | Triage | Code reviewers, issue managers |
| **Observer** | Read | External contributors, stakeholders |

### Step 3: Organization Settings (if applicable)

**For organization repositories**:
1. Go to **Organization Settings → Member privileges**
2. ✅ **Require two-factor authentication**
3. Set **Base permissions** to "No permission"
4. Configure **Repository creation** permissions

---

## 3. Security Features

### Step 1: Enable Core Security Features

**Navigate to**: Settings → Security & analysis

✅ **Dependency graph**
- *Purpose*: Visualizes project dependencies
- *Action*: Enable automatically

✅ **Dependabot alerts**
- *Purpose*: Alerts for vulnerable dependencies
- *Action*: Enable and configure notification preferences

✅ **Dependabot security updates**
- *Purpose*: Automatic PRs for security fixes
- *Action*: Enable for automatic patching

✅ **Secret scanning**
- *Purpose*: Detects committed secrets
- *Action*: Enable for all repositories

✅ **Push protection**
- *Purpose*: Prevents secret commits in real-time
- *Action*: Enable to block pushes with secrets

### Step 2: Configure Code Scanning

**Navigate to**: Security → Code scanning

1. Click **Set up code scanning**
2. Choose **CodeQL Analysis**
3. **Configure languages**:
   - ✅ Python (Lambda functions)
   - ✅ JavaScript/TypeScript (Frontend)
   - ✅ CloudFormation (if supported)

**CodeQL Configuration**:
```yaml
# .github/workflows/codeql-analysis.yml
name: "CodeQL"
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1'  # Weekly Monday 2 AM
```

---

## 4. Required Status Checks Setup

### Understanding Status Checks

Status checks are automated tests that must pass before merging. They integrate with:
- **GitHub Actions** workflows
- **AWS CodeBuild** projects
- **External CI/CD** systems

### AWS DRS Orchestration Status Checks

For this project, configure these status checks:

| Check Name | Purpose | Source |
|------------|---------|--------|
| `validate` | CloudFormation template validation | AWS CodeBuild |
| `security-scan` | Bandit, Semgrep security scanning | AWS CodeBuild |
| `test` | Python unit/integration tests | AWS CodeBuild |
| `build` | Lambda packaging, frontend build | AWS CodeBuild |

### Adding Status Checks to Branch Protection

1. **Edit branch protection rule** for `main`
2. In **Require status checks**, search for check names
3. **Select required checks** from the list
4. ✅ **Require branches to be up to date**

> ⚠️ **Important**: Status checks only appear after running at least once. Create a test PR to populate the list.

---

## 5. CODEOWNERS Configuration

### Step 1: Create CODEOWNERS File

Create `.github/CODEOWNERS` in your repository:

```bash
# Global ownership - requires review from repository maintainers
* @johnjcousens

# CloudFormation templates - requires infrastructure review
/cfn/ @johnjcousens @infrastructure-team

# Lambda functions - requires backend review
/lambda/ @johnjcousens @backend-team

# Frontend application - requires frontend review
/frontend/ @johnjcousens @frontend-team

# CI/CD and deployment - requires DevOps review
/buildspecs/ @johnjcousens @devops-team
/.github/ @johnjcousens @devops-team
/scripts/ @johnjcousens @devops-team

# Documentation - requires technical writing review
/docs/ @johnjcousens @docs-team

# Security and compliance
/.github/workflows/ @johnjcousens @security-team
/cfn/security-stack.yaml @johnjcousens @security-team
```

### Step 2: CODEOWNERS Syntax

```bash
# Comments start with #

# Global rule (applies to all files)
* @username

# Directory rules
/path/to/directory/ @team-name

# File extension rules
*.py @python-team
*.js @javascript-team

# Specific file rules
/important-file.txt @specific-reviewer

# Multiple reviewers
/critical/ @reviewer1 @reviewer2 @team-name
```

### Step 3: Test CODEOWNERS

1. **Create a test PR** modifying files in different directories
2. **Verify correct reviewers** are automatically requested
3. **Adjust CODEOWNERS** as needed

---

## 6. Testing Your Protection Rules

### Test 1: Direct Push Protection

```bash
# This should be blocked
git checkout main
echo "test" >> README.md
git add README.md
git commit -m "Test direct push"
git push origin main
# Expected: Error message about branch protection
```

### Test 2: Pull Request Workflow

```bash
# This should work
git checkout -b test-branch
echo "test" >> README.md
git add README.md
git commit -m "Test PR workflow"
git push origin test-branch
# Create PR via GitHub UI
```

### Test 3: Status Check Requirements

1. **Create PR** with changes
2. **Verify status checks** run automatically
3. **Confirm merge is blocked** until checks pass
4. **Test merge** after all checks pass

---

## 7. Troubleshooting

### Common Issues

#### "Settings tab not visible"
**Problem**: No admin access to repository
**Solution**: Contact repository owner for admin permissions

#### "Status checks not appearing"
**Problem**: Checks haven't run yet
**Solution**: Create a test PR to trigger status checks, then add them to branch protection

#### "CODEOWNERS not working"
**Problem**: File syntax or location incorrect
**Solution**: 
- Ensure file is at `.github/CODEOWNERS`
- Check syntax with GitHub's CODEOWNERS validator
- Verify usernames/team names are correct

#### "Can't merge despite passing checks"
**Problem**: Branch not up to date
**Solution**: 
```bash
git checkout feature-branch
git pull origin main
git push origin feature-branch
```

### Getting Help

- **GitHub Docs**: [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
- **CODEOWNERS**: [About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- **Status Checks**: [About status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)

---

## 8. Maintenance

### Regular Reviews

- **Monthly**: Review collaborator access
- **Quarterly**: Update CODEOWNERS as team changes
- **After incidents**: Adjust protection rules based on lessons learned

### Security Updates

- **Monitor Dependabot alerts** and apply updates promptly
- **Review security advisories** for your technology stack
- **Update status checks** as CI/CD pipeline evolves

### Documentation

- **Keep this guide updated** as GitHub features change
- **Document exceptions** and their justifications
- **Train new team members** on the protection workflow

---

## Summary

With these settings configured, your repository will have:

✅ **Protected main branch** requiring PR reviews
✅ **Automated security scanning** for vulnerabilities
✅ **Code owner reviews** for domain expertise
✅ **Status check requirements** ensuring code quality
✅ **Access controls** limiting repository permissions
✅ **Secret scanning** preventing credential leaks

**Next Steps**:
1. Test the complete workflow with a sample PR
2. Train team members on the new process
3. Monitor and adjust rules based on team feedback

> 🎉 **Congratulations!** Your repository is now secured with enterprise-grade protection rules.