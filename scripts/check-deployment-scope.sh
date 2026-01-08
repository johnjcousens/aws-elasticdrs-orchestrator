#!/bin/bash

# Check Deployment Scope
# Analyzes git changes to predict what the GitHub Actions pipeline will deploy

set -e

echo "=== AWS DRS Orchestration - Deployment Scope Checker ==="
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Get changed files since last commit
CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || git diff --name-only --cached)

if [ -z "$CHANGED_FILES" ]; then
    echo "ℹ️  No changes detected since last commit"
    echo "   Use 'git add' to stage changes, then run this script again"
    exit 0
fi

echo "📁 Changed files:"
echo "$CHANGED_FILES" | sed 's/^/   /'
echo ""

# Categorize changes
INFRASTRUCTURE_CHANGED=false
LAMBDA_CHANGED=false
FRONTEND_CHANGED=false
DOCS_CHANGED=false

while IFS= read -r file; do
    case "$file" in
        cfn/*|buildspecs/*|scripts/sync-to-deployment-bucket.sh)
            INFRASTRUCTURE_CHANGED=true
            ;;
        lambda/*|tests/python/*)
            LAMBDA_CHANGED=true
            ;;
        frontend/*)
            FRONTEND_CHANGED=true
            ;;
        docs/*|README.md|CHANGELOG.md|*.md)
            DOCS_CHANGED=true
            ;;
        .github/workflows/*)
            # Workflow changes should trigger full pipeline
            INFRASTRUCTURE_CHANGED=true
            ;;
    esac
done <<< "$CHANGED_FILES"

# Determine deployment strategy
DOCS_ONLY=false
FRONTEND_ONLY=false

if [ "$DOCS_CHANGED" = "true" ] && [ "$INFRASTRUCTURE_CHANGED" = "false" ] && [ "$LAMBDA_CHANGED" = "false" ] && [ "$FRONTEND_CHANGED" = "false" ]; then
    DOCS_ONLY=true
elif [ "$FRONTEND_CHANGED" = "true" ] && [ "$INFRASTRUCTURE_CHANGED" = "false" ] && [ "$LAMBDA_CHANGED" = "false" ]; then
    FRONTEND_ONLY=true
fi

echo "🔍 Change Analysis:"
echo "   Infrastructure: $INFRASTRUCTURE_CHANGED"
echo "   Lambda Functions: $LAMBDA_CHANGED"
echo "   Frontend: $FRONTEND_CHANGED"
echo "   Documentation: $DOCS_CHANGED"
echo ""

echo "🚀 GitHub Actions Pipeline Prediction:"

if [ "$DOCS_ONLY" = "true" ]; then
    echo "   ✅ Documentation-only deployment"
    echo "   ⏭️  Will skip: Validate, Security Scan, Build, Test, Deploy Infrastructure, Deploy Frontend"
    echo "   ⏱️  Estimated time: ~30 seconds (vs ~22 minutes for full pipeline)"
    echo "   💰 Cost savings: ~95% reduction in compute time"
elif [ "$FRONTEND_ONLY" = "true" ]; then
    echo "   ✅ Frontend-only deployment"
    echo "   🔄 Will run: Validate, Security Scan, Build, Test"
    echo "   ⏭️  Will skip: Deploy Infrastructure"
    echo "   🎯 Will run: Deploy Frontend"
    echo "   ⏱️  Estimated time: ~12 minutes (vs ~22 minutes for full pipeline)"
    echo "   💰 Cost savings: ~45% reduction in deployment time"
else
    echo "   🔄 Full infrastructure deployment"
    echo "   🎯 Will run: All pipeline stages"
    echo "   ⏱️  Estimated time: ~22 minutes"
    
    if [ "$INFRASTRUCTURE_CHANGED" = "true" ]; then
        echo "   📦 CloudFormation stack will be updated"
    fi
    if [ "$LAMBDA_CHANGED" = "true" ]; then
        echo "   ⚡ Lambda functions will be updated"
    fi
    if [ "$FRONTEND_CHANGED" = "true" ]; then
        echo "   🌐 Frontend will be deployed"
    fi
fi

echo ""
echo "💡 Tips:"
echo "   • Documentation changes (*.md, docs/*) trigger docs-only deployment"
echo "   • Frontend-only changes (frontend/*) skip infrastructure deployment"
echo "   • Infrastructure changes (cfn/*, lambda/*) trigger full deployment"
echo "   • Mixed changes always trigger full deployment for safety"
echo ""
echo "🔗 Monitor deployment: https://github.com/johnjcousens/aws-elasticdrs-orchestrator/actions"