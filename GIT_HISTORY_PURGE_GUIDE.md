# Git History Purge Guide

**CRITICAL**: Complete guide for removing sensitive data from entire git history before making repository public.

**Repository**: github.com/johnjcousens/aws-elasticdrs-orchestrator/  
**Date**: January 15, 2026

---

## ⚠️ WARNING: DESTRUCTIVE OPERATION

This process **permanently rewrites git history**. All commit SHAs will change. This is a **one-way operation** that cannot be undone.

### Before You Begin

1. ✅ **Backup everything** - Clone repository to safe location
2. ✅ **Notify all collaborators** - They must re-clone after purge
3. ✅ **Close all pull requests** - They will become invalid
4. ✅ **Document current state** - Save commit SHAs for reference
5. ✅ **Test on backup first** - Never run on production repository first

---

## Method 1: git-filter-repo (RECOMMENDED)

**Why git-filter-repo?**
- Fastest and most reliable tool
- Officially recommended by GitHub
- Handles large repositories efficiently
- Better than BFG Repo-Cleaner for complex replacements

### Step 1: Install git-filter-repo

```bash
# macOS
brew install git-filter-repo

# Linux (Ubuntu/Debian)
sudo apt-get install git-filter-repo

# Python pip (all platforms)
pip3 install git-filter-repo

# Verify installation
git-filter-repo --version
```

### Step 2: Create Backup

```bash
# Clone fresh copy for backup
git clone --mirror https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git backup-repo-$(date +%Y%m%d)

# Create working copy
git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git purge-working-copy
cd purge-working-copy
```

### Step 3: Create Replacement File

Create `replacements.txt` with all sensitive data patterns:

```text
***REMOVED***
***REMOVED***==>***REMOVED***

***REMOVED***
***REMOVED***==>***REMOVED***

***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***

***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***

***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***

***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***

***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***

***REMOVED***
aws-elasticdrs-orchestrator-cicd-artifacts-***REMOVED***-dev==>***REMOVED***
drsorchv4-fe-***REMOVED***-test==>***REMOVED***
aws-elasticdrs-orchestrator-fe-***REMOVED***-test==>***REMOVED***

***REMOVED*** (if any exist in history)
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
```

### Step 4: Run git-filter-repo

```bash
# CRITICAL: Remove remote to prevent accidental push
git remote remove origin

# Run replacement on entire history
git filter-repo --replace-text replacements.txt --force

# Verify replacements worked
git log --all --oneline | head -20
git log --all -p | grep -i "***REMOVED***" || echo "Account ID successfully removed"
git log --all -p | grep -i "***REMOVED***" || echo "Email successfully removed"
```

### Step 5: Verify Purge Success

```bash
# Search for sensitive data in entire history
echo "Searching for AWS Account ID..."
git log --all -p | grep "***REMOVED***" && echo "❌ FOUND" || echo "✅ CLEAN"

echo "Searching for Email..."
git log --all -p | grep "***REMOVED***" && echo "❌ FOUND" || echo "✅ CLEAN"

echo "Searching for API Gateway IDs..."
git log --all -p | grep -E "(***REMOVED***|***REMOVED***|***REMOVED***)" && echo "❌ FOUND" || echo "✅ CLEAN"

echo "Searching for CloudFront IDs..."
git log --all -p | grep -E "(***REMOVED***|***REMOVED***)" && echo "❌ FOUND" || echo "✅ CLEAN"

echo "Searching for Cognito Pool IDs..."
git log --all -p | grep -E "us-east-1_[A-Za-z0-9]{9}" && echo "❌ FOUND" || echo "✅ CLEAN"
```

### Step 6: Force Push to GitHub

```bash
# Add remote back
git remote add origin https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git

# Force push (DESTRUCTIVE - rewrites history)
git push origin --force --all
git push origin --force --tags

# Verify on GitHub
# All commit SHAs will be different
```

---

## Method 2: BFG Repo-Cleaner (ALTERNATIVE)

**Use if git-filter-repo doesn't work for your case.**

### Step 1: Install BFG

```bash
# macOS
brew install bfg

# Manual download (all platforms)
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar
alias bfg='java -jar bfg-1.14.0.jar'
```

### Step 2: Create Replacement File

Create `replacements.txt`:

```text
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
# ... (same as git-filter-repo)
```

### Step 3: Run BFG

```bash
# Clone mirror
git clone --mirror https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git

# Run BFG
bfg --replace-text replacements.txt aws-elasticdrs-orchestrator.git

# Clean up
cd aws-elasticdrs-orchestrator.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push --force
```

---

## Method 3: GitHub Secret Scanning (DETECTION ONLY)

GitHub automatically scans for secrets. Check if any were detected:

```bash
# Enable secret scanning (if not already enabled)
# Go to: Settings → Security → Code security and analysis
# Enable: Secret scanning
# Enable: Push protection

# View detected secrets
# Go to: Security → Secret scanning alerts
```

**Note**: This only detects, doesn't remove from history.

---

## Post-Purge Actions

### 1. Verify Repository is Clean

```bash
# Clone fresh copy
git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git verify-clean
cd verify-clean

# Search entire history
git log --all -p | grep -i "***REMOVED***" && echo "❌ STILL FOUND" || echo "✅ CLEAN"
git log --all -p | grep -i "jocousen" && echo "❌ STILL FOUND" || echo "✅ CLEAN"

# Check all branches
git branch -r | while read branch; do
  echo "Checking $branch..."
  git log $branch -p | grep -i "***REMOVED***" && echo "❌ FOUND IN $branch"
done
```

### 2. Notify All Collaborators

Send this message to all team members:

```
URGENT: Git History Rewrite Complete

The aws-elasticdrs-orchestrator repository history has been rewritten to remove sensitive data.

ACTION REQUIRED:
1. Delete your local clone: rm -rf aws-elasticdrs-orchestrator
2. Re-clone from GitHub: git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git
3. Do NOT try to merge old branches - they are incompatible

All commit SHAs have changed. Old branches and pull requests are invalid.

If you have unpushed work:
1. Save your changes: git diff > my-changes.patch
2. Re-clone repository
3. Apply changes: git apply my-changes.patch
```

### 3. Update GitHub Settings

```bash
# Enable branch protection
# Go to: Settings → Branches → Add rule
# Branch name pattern: main
# ✅ Require pull request reviews
# ✅ Require status checks to pass
# ✅ Include administrators

# Enable secret scanning
# Go to: Settings → Security → Code security and analysis
# ✅ Secret scanning
# ✅ Push protection
```

### 4. Install git-secrets Locally

Prevent future commits with sensitive data:

```bash
# Install git-secrets
brew install git-secrets  # macOS
# OR
pip install git-secrets   # All platforms

# Initialize in repository
cd aws-elasticdrs-orchestrator
git secrets --install
git secrets --register-aws

# Add custom patterns
git secrets --add '***REMOVED***'
git secrets --add 'jocousen@amazon\.com'
git secrets --add '[a-z0-9]{10}\.execute-api'
git secrets --add 'us-east-1_[A-Za-z0-9]{9}'
git secrets --add '[a-z0-9]{26}'  # Cognito client IDs

# Test it works
echo "***REMOVED***" > test.txt
git add test.txt
git commit -m "test"  # Should be blocked
rm test.txt
```

### 5. Add Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Run git-secrets check
git secrets --pre_commit_hook -- "$@"

# Additional custom checks
if git diff --cached | grep -i "***REMOVED***"; then
  echo "❌ ERROR: AWS Account ID detected in commit"
  exit 1
fi

if git diff --cached | grep -i "***REMOVED***"; then
  echo "❌ ERROR: Email address detected in commit"
  exit 1
fi

echo "✅ Pre-commit checks passed"
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

---

## Verification Checklist

Before making repository public, verify:

- [ ] ✅ Backed up original repository
- [ ] ✅ Created replacements.txt with all sensitive patterns
- [ ] ✅ Ran git-filter-repo successfully
- [ ] ✅ Verified no sensitive data in history (searched all commits)
- [ ] ✅ Force pushed to GitHub
- [ ] ✅ All commit SHAs changed
- [ ] ✅ Notified all collaborators
- [ ] ✅ Collaborators re-cloned repository
- [ ] ✅ Enabled GitHub secret scanning
- [ ] ✅ Enabled push protection
- [ ] ✅ Installed git-secrets locally
- [ ] ✅ Added pre-commit hooks
- [ ] ✅ Tested secret detection works
- [ ] ✅ Updated documentation with generic placeholders
- [ ] ✅ No AWS Account ID in any commit
- [ ] ✅ No email addresses in any commit
- [ ] ✅ No API Gateway IDs in any commit
- [ ] ✅ No CloudFront IDs in any commit
- [ ] ✅ No Cognito resource IDs in any commit

---

## Troubleshooting

### Issue: "fatal: not a git repository"

```bash
# Ensure you're in repository root
cd aws-elasticdrs-orchestrator
git status
```

### Issue: "remote: Permission denied"

```bash
# Ensure you have admin access to repository
# Or use personal access token
git remote set-url origin https://YOUR_TOKEN@github.com/johnjcousens/aws-elasticdrs-orchestrator.git
```

### Issue: "Still finding sensitive data after purge"

```bash
# Check if data is in tags
git tag -l | xargs -n1 git show | grep "***REMOVED***"

# Delete and recreate tags
git tag -d $(git tag -l)
git push origin --delete $(git tag -l)

# Re-run git-filter-repo
git filter-repo --replace-text replacements.txt --force --refs refs/heads/*
```

### Issue: "Collaborator can't push after purge"

```bash
# Collaborator must:
1. Delete local repository
2. Re-clone from GitHub
3. Do NOT try to merge old branches

# If they have unpushed work:
git diff > my-changes.patch  # Save changes
# Re-clone repository
git apply my-changes.patch   # Apply changes
```

---

## Alternative: Start Fresh Repository

If purging is too complex, consider starting fresh:

```bash
# 1. Create new repository on GitHub
# 2. Clone current repository
git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git fresh-start

# 3. Remove git history
cd fresh-start
rm -rf .git

# 4. Initialize new repository
git init
git add .
git commit -m "Initial commit with sanitized data"

# 5. Push to new repository
git remote add origin https://github.com/johnjcousens/aws-elasticdrs-orchestrator-public.git
git push -u origin main
```

**Pros**: Clean history, no risk of missed sensitive data  
**Cons**: Lose all commit history, contributors, issues, PRs

---

## Resources

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [git-filter-repo documentation](https://github.com/newren/git-filter-repo)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [git-secrets](https://github.com/awslabs/git-secrets)

---

## Summary

**Recommended Approach**: Use git-filter-repo (Method 1)

**Timeline**:
- Backup: 5 minutes
- Create replacements.txt: 10 minutes
- Run git-filter-repo: 2-5 minutes
- Verify: 10 minutes
- Force push: 2 minutes
- **Total: ~30 minutes**

**Risk Level**: HIGH (destructive, irreversible)

**Success Criteria**: Zero sensitive data in entire git history

---

**CRITICAL**: Do not make repository public until purge is complete and verified.
