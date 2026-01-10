#!/bin/bash
# Check deployment scope and provide time estimates
# Analyzes git changes to predict GitHub Actions pipeline behavior

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "======================================"
echo "🔍 Deployment Scope Analysis"
echo "======================================"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Get list of changed files
if git diff --cached --quiet; then
    echo -e "${YELLOW}⚠️  No staged changes found${NC}"
    echo ""
    echo "Analyzing unstaged changes instead..."
    CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null || echo "")
else
    echo "Analyzing staged changes..."
    CHANGED_FILES=$(git diff --cached --name-only 2>/dev/null || echo "")
fi

if [ -z "$CHANGED_FILES" ]; then
    echo -e "${YELLOW}⚠️  No changes detected${NC}"
    echo ""
    echo "💡 Make sure to stage your changes:"
    echo "  git add ."
    echo "  $0"
    exit 0
fi

echo ""
echo "Changed files:"
echo "$CHANGED_FILES" | sed 's/^/  /'
echo ""

# Categorize changes
INFRASTRUCTURE_CHANGED=false
LAMBDA_CHANGED=false
FRONTEND_CHANGED=false
DOCS_CHANGED=false

while IFS= read -r file; do
    if [[ "$file" =~ ^cfn/ ]] || [[ "$file" =~ ^scripts/ ]] || [[ "$file" == "Makefile" ]]; then
        INFRASTRUCTURE_CHANGED=true
    elif [[ "$file" =~ ^lambda/ ]]; then
        LAMBDA_CHANGED=true
    elif [[ "$file" =~ ^frontend/ ]]; then
        FRONTEND_CHANGED=true
    elif [[ "$file" =~ ^docs/ ]] || [[ "$file" == "README.md" ]] || [[ "$file" == "CHANGELOG.md" ]]; then
        DOCS_CHANGED=true
    fi
done <<< "$CHANGED_FILES"

# Determine deployment scope
if [[ "$DOCS_CHANGED" == "true" && "$INFRASTRUCTURE_CHANGED" == "false" && "$LAMBDA_CHANGED" == "false" && "$FRONTEND_CHANGED" == "false" ]]; then
    DEPLOYMENT_SCOPE="docs-only"
    ESTIMATED_TIME="30 seconds"
    TIME_SAVINGS="95%"
    PIPELINE_COLOR="$GREEN"
elif [[ "$FRONTEND_CHANGED" == "true" && "$INFRASTRUCTURE_CHANGED" == "false" && "$LAMBDA_CHANGED" == "false" ]]; then
    DEPLOYMENT_SCOPE="frontend-only"
    ESTIMATED_TIME="12 minutes"
    TIME_SAVINGS="45%"
    PIPELINE_COLOR="$BLUE"
else
    DEPLOYMENT_SCOPE="full-deployment"
    ESTIMATED_TIME="22 minutes"
    TIME_SAVINGS="0%"
    PIPELINE_COLOR="$YELLOW"
fi

echo "======================================"
echo -e "${PIPELINE_COLOR}📊 Deployment Analysis${NC}"
echo "======================================"
echo ""
echo "Change Categories:"
echo "  Infrastructure: $INFRASTRUCTURE_CHANGED (CloudFormation, scripts, Makefile)"
echo "  Lambda Code: $LAMBDA_CHANGED (Python functions)"
echo "  Frontend: $FRONTEND_CHANGED (React/TypeScript)"
echo "  Documentation: $DOCS_CHANGED (Markdown, docs)"
echo ""
echo -e "Deployment Scope: ${PIPELINE_COLOR}$DEPLOYMENT_SCOPE${NC}"
echo -e "Estimated Time: ${PIPELINE_COLOR}$ESTIMATED_TIME${NC}"
echo -e "Time Savings: ${PIPELINE_COLOR}$TIME_SAVINGS${NC}"
echo ""

# Show pipeline stages that will run
echo "======================================"
echo "🚀 GitHub Actions Pipeline Stages"
echo "======================================"

case $DEPLOYMENT_SCOPE in
    "docs-only")
        echo -e "${GREEN}✅ Documentation Update Only${NC}"
        echo ""
        echo "Pipeline stages:"
        echo "  1. ✅ Detect Changes (~10s)"
        echo "  2. ⏭️  Validate (SKIPPED)"
        echo "  3. ⏭️  Security Scan (SKIPPED)"
        echo "  4. ⏭️  Build (SKIPPED)"
        echo "  5. ⏭️  Test (SKIPPED)"
        echo "  6. ⏭️  Deploy Infrastructure (SKIPPED)"
        echo "  7. ⏭️  Deploy Frontend (SKIPPED)"
        echo "  8. ✅ Documentation Summary (~20s)"
        echo ""
        echo -e "${GREEN}🎉 Ultra-fast deployment! Only documentation updated.${NC}"
        ;;
    "frontend-only")
        echo -e "${BLUE}🌐 Frontend-Only Deployment${NC}"
        echo ""
        echo "Pipeline stages:"
        echo "  1. ✅ Detect Changes (~10s)"
        echo "  2. ✅ Validate (~2 min)"
        echo "  3. ✅ Security Scan (~2 min)"
        echo "  4. ✅ Build (~3 min)"
        echo "  5. ✅ Test (~2 min)"
        echo "  6. ⏭️  Deploy Infrastructure (SKIPPED)"
        echo "  7. ✅ Deploy Frontend (~3 min)"
        echo ""
        echo -e "${BLUE}🚀 Optimized deployment! Infrastructure unchanged.${NC}"
        ;;
    "full-deployment")
        echo -e "${YELLOW}🏗️  Full Deployment${NC}"
        echo ""
        echo "Pipeline stages:"
        echo "  1. ✅ Detect Changes (~10s)"
        echo "  2. ✅ Validate (~2 min)"
        echo "  3. ✅ Security Scan (~2 min)"
        echo "  4. ✅ Build (~3 min)"
        echo "  5. ✅ Test (~2 min)"
        echo "  6. ✅ Deploy Infrastructure (~10 min)"
        echo "  7. ✅ Deploy Frontend (~3 min)"
        echo ""
        echo -e "${YELLOW}⚡ Complete deployment with all quality gates.${NC}"
        ;;
esac

echo ""
echo "======================================"
echo "💡 Deployment Tips"
echo "======================================"
echo ""

case $DEPLOYMENT_SCOPE in
    "docs-only")
        echo "✨ This is a documentation-only change!"
        echo "   • No infrastructure or code changes"
        echo "   • Ultra-fast deployment (30 seconds)"
        echo "   • Safe to push anytime"
        ;;
    "frontend-only")
        echo "🌐 This is a frontend-only change!"
        echo "   • No infrastructure changes required"
        echo "   • Moderate deployment time (12 minutes)"
        echo "   • CloudFront cache will be invalidated"
        ;;
    "full-deployment")
        echo "🏗️  This is a full deployment!"
        echo "   • Infrastructure and/or Lambda changes detected"
        echo "   • Complete pipeline with all quality gates"
        echo "   • Monitor CloudFormation stack progress"
        ;;
esac

echo ""
echo "🔗 Monitoring Links:"
if command -v gh &> /dev/null && gh auth status &> /dev/null; then
    REPO_URL=$(gh repo view --json url -q .url 2>/dev/null || echo "")
    if [ -n "$REPO_URL" ]; then
        echo "   • GitHub Actions: $REPO_URL/actions"
        echo "   • CloudFormation: https://console.aws.amazon.com/cloudformation/home?region=us-east-1"
        echo "   • Application: https://***REMOVED***.cloudfront.net"
    else
        echo "   • Check GitHub Actions tab after pushing"
    fi
else
    echo "   • Check GitHub Actions tab after pushing"
    echo "   • Install GitHub CLI for direct links: brew install gh"
fi

echo ""
echo "🚀 Ready to deploy? Use:"
echo "   ./scripts/safe-push.sh"
echo ""