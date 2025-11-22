#!/bin/bash
# Automated incremental commit workflow
# Usage: ./scripts/incremental-commit.sh <file> <validation-cmd> <commit-message>

set -e

FILE=$1
VALIDATION_CMD=$2
COMMIT_MSG=$3

if [ -z "$FILE" ] || [ -z "$VALIDATION_CMD" ] || [ -z "$COMMIT_MSG" ]; then
    echo "❌ Error: Missing required arguments"
    echo ""
    echo "Usage: $0 <file> <validation-cmd> <commit-message>"
    echo ""
    echo "Examples:"
    echo "  # TypeScript file"
    echo "  $0 frontend/src/App.tsx 'cd frontend && npm run type-check' 'fix: add new route'"
    echo ""
    echo "  # CloudFormation template"
    echo "  $0 cfn/api-stack.yaml 'aws cloudformation validate-template --template-body file://cfn/api-stack.yaml' 'fix: add API method'"
    echo ""
    echo "  # Python file"
    echo "  $0 lambda/index.py 'cd lambda && python -m pytest tests/unit/' 'feat: add handler'"
    exit 1
fi

echo "🚀 Incremental Commit Workflow"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 File: $FILE"
echo "✅ Validation: $VALIDATION_CMD"
echo "💬 Message: $COMMIT_MSG"
echo ""

# Step 1: Validate
echo "Step 1/3: Validating changes..."
echo "Running: $VALIDATION_CMD"
echo ""
if eval "$VALIDATION_CMD"; then
    echo "✅ Validation passed"
else
    echo "❌ Validation failed - NOT committing"
    echo "Fix errors above and try again"
    exit 1
fi

# Step 2: Commit
echo ""
echo "Step 2/3: Committing changes..."
git add "$FILE"
git commit -m "$COMMIT_MSG"
COMMIT_HASH=$(git rev-parse --short HEAD)
echo "✅ Committed: $COMMIT_HASH"

# Step 3: Push
echo ""
echo "Step 3/3: Pushing to remote..."
git push origin main
echo "✅ Pushed to remote"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Incremental commit complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "File: $FILE"
echo "Commit: $COMMIT_HASH"
echo "✅ Safe point established - ready for next change"
