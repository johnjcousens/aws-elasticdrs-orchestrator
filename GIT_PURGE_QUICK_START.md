# Git History Purge - Quick Start

**⚠️ CRITICAL: Read full guide (GIT_HISTORY_PURGE_GUIDE.md) before proceeding**

---

## 30-Minute Purge Process

### Prerequisites
- [ ] Admin access to GitHub repository
- [ ] All collaborators notified
- [ ] Backup created
- [ ] git-filter-repo installed

---

## Step 1: Backup (5 min)

```bash
# Create backup
git clone --mirror https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git backup-$(date +%Y%m%d)

# Create working copy
git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git purge-working
cd purge-working
```

---

## Step 2: Install git-filter-repo (2 min)

```bash
# macOS
brew install git-filter-repo

# Verify
git-filter-repo --version
```

---

## Step 3: Create Replacements File (5 min)

```bash
cat > replacements.txt << 'EOF'
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
***REMOVED***==>***REMOVED***
EOF
```

---

## Step 4: Run Purge (3 min)

```bash
# Remove remote (safety)
git remote remove origin

# Run purge
git filter-repo --replace-text replacements.txt --force

# Verify
git log --all -p | grep "***REMOVED***" && echo "❌ FAILED" || echo "✅ SUCCESS"
```

---

## Step 5: Verify Clean (5 min)

```bash
# Check for sensitive data
echo "Checking AWS Account ID..."
git log --all -p | grep "***REMOVED***" && echo "❌ FOUND" || echo "✅ CLEAN"

echo "Checking Email..."
git log --all -p | grep "***REMOVED***" && echo "❌ FOUND" || echo "✅ CLEAN"

echo "Checking API Gateway IDs..."
git log --all -p | grep -E "(***REMOVED***|***REMOVED***)" && echo "❌ FOUND" || echo "✅ CLEAN"

echo "Checking Cognito IDs..."
git log --all -p | grep -E "us-east-1_[A-Za-z0-9]{9}" && echo "❌ FOUND" || echo "✅ CLEAN"
```

**If ANY checks show ❌ FOUND, DO NOT PROCEED. Review GIT_HISTORY_PURGE_GUIDE.md**

---

## Step 6: Force Push (2 min)

```bash
# Add remote back
git remote add origin https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git

# Force push (DESTRUCTIVE)
git push origin --force --all
git push origin --force --tags
```

---

## Step 7: Post-Purge Actions (10 min)

### Enable GitHub Protections

1. Go to: Settings → Security → Code security and analysis
2. Enable: Secret scanning
3. Enable: Push protection

### Notify Collaborators

Send this message:

```
URGENT: Repository history rewritten

ACTION REQUIRED:
1. Delete local clone: rm -rf aws-elasticdrs-orchestrator
2. Re-clone: git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git

All commit SHAs have changed. Do NOT merge old branches.
```

### Install git-secrets

```bash
# Install
brew install git-secrets

# Setup in repository
cd aws-elasticdrs-orchestrator
git secrets --install
git secrets --register-aws
git secrets --add '***REMOVED***'
git secrets --add 'jocousen@amazon\.com'
```

---

## Verification Checklist

- [ ] ✅ Backup created
- [ ] ✅ git-filter-repo installed
- [ ] ✅ Replacements file created
- [ ] ✅ Purge completed successfully
- [ ] ✅ All verification checks passed (no ❌ FOUND)
- [ ] ✅ Force pushed to GitHub
- [ ] ✅ GitHub secret scanning enabled
- [ ] ✅ Collaborators notified
- [ ] ✅ git-secrets installed
- [ ] ✅ Repository safe for public access

---

## If Something Goes Wrong

### Restore from Backup

```bash
# Use backup mirror
cd backup-$(date +%Y%m%d)
git push origin --mirror --force
```

### Get Help

1. Review full guide: GIT_HISTORY_PURGE_GUIDE.md
2. Check troubleshooting section
3. Test on backup repository first

---

## Success Criteria

✅ Zero sensitive data in entire git history  
✅ All commit SHAs changed  
✅ Collaborators re-cloned successfully  
✅ Secret scanning enabled  
✅ Repository ready for public access

---

**CRITICAL**: Do not skip verification steps. One missed sensitive value compromises entire purge.

**See**: GIT_HISTORY_PURGE_GUIDE.md for complete details and troubleshooting.
