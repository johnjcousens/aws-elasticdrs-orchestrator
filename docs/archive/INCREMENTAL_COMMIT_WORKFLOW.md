# Incremental Commit & Push Workflow

## Purpose
Automate the pattern learned in Session 45 & 47: **Commit immediately after each successful change** to protect good fixes from being lost during later reverts.

## Core Principle
**One logical change → Validate → Commit → Push**

This ensures that if a later step fails and requires `git checkout`, previously committed fixes remain safe.

## Workflow Pattern

### Step 1: Make Single Logical Change
```bash
# Example: Fix parameter rename
sed -i '' 's/_event/event/g' file.tsx
```

### Step 2: Validate Immediately
```bash
# For TypeScript/React
cd frontend && npm run type-check

# For Python
cd lambda && python -m pytest tests/

# For CloudFormation
aws cloudformation validate-template --template-body file://cfn/stack.yaml
```

### Step 3: Commit Immediately on Success
```bash
git add <changed-file>
git commit -m "fix: specific change description"
```

### Step 4: Push to Remote
```bash
git push origin main
```

### Step 5: Proceed to Next Change
Now safe to attempt next change. If it fails and needs `git checkout`, previous commits are protected.

## Why This Matters

### Without Incremental Commits (❌ Bad)
```bash
# Change 1: Parameter fix (sed)
sed -i '' 's/_event/event/g' file.tsx
# Change 2: Add debug logging (replace_in_file)
# ... FAILS with 140+ errors
git checkout file.tsx  # ❌ LOSES BOTH CHANGES
```

### With Incremental Commits (✅ Good)
```bash
# Change 1: Parameter fix
sed -i '' 's/_event/event/g' file.tsx
npm run type-check  # ✅ Passes
git add file.tsx
git commit -m "fix: remove underscore from event parameter"
git push origin main  # ✅ SAFE ON REMOTE

# Change 2: Add debug logging
# ... FAILS with errors
git checkout file.tsx  # ✅ Only reverts Change 2
# Change 1 still safe in git history!
```

## Automation Script

### scripts/incremental-commit.sh
```bash
#!/bin/bash
# Automated incremental commit workflow

set -e

FILE=$1
VALIDATION_CMD=$2
COMMIT_MSG=$3

if [ -z "$FILE" ] || [ -z "$VALIDATION_CMD" ] || [ -z "$COMMIT_MSG" ]; then
    echo "Usage: $0 <file> <validation-cmd> <commit-message>"
    echo "Example: $0 frontend/src/App.tsx 'cd frontend && npm run type-check' 'fix: add new route'"
    exit 1
fi

echo "📝 File: $FILE"
echo "✅ Validation: $VALIDATION_CMD"
echo "💬 Message: $COMMIT_MSG"
echo ""

# Step 1: Validate
echo "Step 1: Validating changes..."
if eval "$VALIDATION_CMD"; then
    echo "✅ Validation passed"
else
    echo "❌ Validation failed - NOT committing"
    exit 1
fi

# Step 2: Commit
echo ""
echo "Step 2: Committing changes..."
git add "$FILE"
git commit -m "$COMMIT_MSG"
COMMIT_HASH=$(git rev-parse --short HEAD)
echo "✅ Committed: $COMMIT_HASH"

# Step 3: Push
echo ""
echo "Step 3: Pushing to remote..."
git push origin main
echo "✅ Pushed to remote"

echo ""
echo "🎉 Incremental commit complete!"
echo "File: $FILE"
echo "Commit: $COMMIT_HASH"
echo "Safe point established ✅"
```

## Usage Examples

### Example 1: TypeScript File Edit
```bash
# Make change
sed -i '' 's/oldValue/newValue/' frontend/src/App.tsx

# Incremental commit
./scripts/incremental-commit.sh \
  "frontend/src/App.tsx" \
  "cd frontend && npm run type-check" \
  "fix: update configuration value"
```

### Example 2: CloudFormation Template
```bash
# Make change to template
# ... edit cfn/api-stack.yaml

# Incremental commit
./scripts/incremental-commit.sh \
  "cfn/api-stack.yaml" \
  "aws cloudformation validate-template --template-body file://cfn/api-stack.yaml" \
  "fix: add missing API Gateway method"
```

### Example 3: Lambda Function
```bash
# Make change
# ... edit lambda/index.py

# Incremental commit
./scripts/incremental-commit.sh \
  "lambda/index.py" \
  "cd lambda && python -m pytest tests/unit/" \
  "feat: add new execution endpoint handler"
```

## Multi-File Changes

For changes spanning multiple files, commit each file separately:

```bash
# File 1: API Gateway configuration
./scripts/incremental-commit.sh \
  "cfn/api-stack.yaml" \
  "aws cloudformation validate-template --template-body file://cfn/api-stack.yaml" \
  "fix(api): add POST /executions endpoint"

# File 2: Lambda handler
./scripts/incremental-commit.sh \
  "lambda/index.py" \
  "cd lambda && python -m pytest tests/unit/" \
  "feat(lambda): implement POST /executions handler"

# File 3: Frontend API client
./scripts/incremental-commit.sh \
  "frontend/src/services/api.ts" \
  "cd frontend && npm run type-check" \
  "feat(frontend): add createExecution API method"
```

## Integration with Safe Editing Rules

This workflow implements **Rule 9: Multi-Step Edits** from safe-file-editing.md:

```
Rule 9: Multi-Step Edits (CRITICAL - Prevents Loss of Good Fixes)

For changes requiring multiple steps:
1. Break into atomic changes
2. Validate after each step
3. **COMMIT after each success** (MANDATORY)
4. If later step fails, previous commits are protected
```

## Benefits

### ✅ Rollback Safety
- Each commit is a safe rollback point
- `git checkout` only reverts uncommitted work
- Committed fixes never lost

### ✅ Clear History
- Each commit represents one logical change
- Easy to understand what changed when
- Bisect-friendly for debugging

### ✅ Deploy Partial Fixes
- Can deploy after any successful commit
- Don't need to wait for complete feature
- Incremental progress visible

### ✅ Collaboration Safety
- Teammates can pull partial progress
- Work doesn't block other changes
- Conflicts less likely

## When to Use

### Always Use For:
- ✅ Multi-step file edits
- ✅ Changes with validation steps
- ✅ Risky operations (replace_in_file, etc.)
- ✅ CloudFormation deployments
- ✅ Any change you might need to revert

### Can Skip For:
- Documentation-only changes (low risk)
- Typo fixes in comments
- Changes you're 100% confident about

## Emergency Recovery

If you forget to commit and need to revert:

```bash
# Save current changes to stash first!
git stash save "emergency-backup-$(date +%Y%m%d-%H%M%S)"

# Now safe to checkout
git checkout <file>

# Can recover from stash later if needed
git stash list
git stash pop stash@{0}
```

## Success Metrics

You're using this workflow correctly when:
- ✅ Every file edit has a corresponding commit
- ✅ `git log --oneline` shows incremental progress
- ✅ Each commit message is descriptive and focused
- ✅ You can rollback to any commit safely
- ✅ `git revert` works for individual changes

## References
- safe-file-editing.md - Rule 9: Multi-Step Edits
- Session 45 incident: Lost parameter fix during revert
- Session 47: Applied incremental commits for API fixes
