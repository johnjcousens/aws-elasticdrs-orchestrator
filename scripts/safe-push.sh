#!/bin/bash
# Safe push script that checks for running GitHub Actions workflows
# Usage: ./scripts/safe-push.sh [branch] [--force]

set -e

# Configuration
DEFAULT_BRANCH="main"
FORCE_PUSH=false
TARGET_BRANCH=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_PUSH=true
            echo -e "${YELLOW}🚨 FORCE MODE: Skipping workflow checks${NC}"
            shift
            ;;
        --help)
            echo "Usage: $0 [branch] [--force]"
            echo ""
            echo "Safe push script that prevents GitHub Actions conflicts"
            echo ""
            echo "Arguments:"
            echo "  branch    Target branch (default: current branch or main)"
            echo "  --force   Skip workflow checks (emergency use only)"
            echo ""
            echo "Examples:"
            echo "  $0                    # Push to current branch"
            echo "  $0 main               # Push to main branch"
            echo "  $0 --force            # Emergency push (skip checks)"
            echo "  $0 main --force       # Emergency push to main"
            echo ""
            echo "🚀 RECOMMENDED WORKFLOW:"
            echo "  git add ."
            echo "  git commit -m 'description'"
            echo "  $0                    # Safe push with workflow checks"
            exit 0
            ;;
        *)
            if [ -z "$TARGET_BRANCH" ]; then
                TARGET_BRANCH="$1"
            else
                echo "Unknown option: $1"
                echo "Run '$0 --help' for usage information"
                exit 1
            fi
            shift
            ;;
    esac
done

# Determine target branch
if [ -z "$TARGET_BRANCH" ]; then
    if git rev-parse --git-dir > /dev/null 2>&1; then
        TARGET_BRANCH=$(git branch --show-current 2>/dev/null || echo "$DEFAULT_BRANCH")
    else
        TARGET_BRANCH="$DEFAULT_BRANCH"
    fi
fi

echo "======================================"
echo "🚀 Safe Push to GitHub"
echo "======================================"
echo "Target Branch: $TARGET_BRANCH"
echo "Force Mode: $FORCE_PUSH"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes${NC}"
    echo ""
    echo "Uncommitted files:"
    git status --porcelain
    echo ""
    echo "Please commit your changes first:"
    echo "  git add ."
    echo "  git commit -m 'your commit message'"
    echo "  $0"
    exit 1
fi

# Check workflow status (unless force mode)
if [ "$FORCE_PUSH" = false ]; then
    echo "🔍 Checking GitHub Actions workflow status..."
    
    if ./scripts/check-workflow.sh; then
        echo -e "${GREEN}✅ Workflow check passed${NC}"
    else
        echo ""
        echo -e "${RED}❌ Workflow check failed${NC}"
        echo ""
        echo "Options:"
        echo "  1. Wait for workflows to complete (recommended)"
        echo "  2. Force push (emergency only): $0 $TARGET_BRANCH --force"
        echo "  3. Check workflow status: gh run list"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  SKIPPING workflow checks (force mode)${NC}"
fi

echo ""
echo "🚀 Pushing to $TARGET_BRANCH..."

# Perform the git push
if git push origin "$TARGET_BRANCH"; then
    echo ""
    echo -e "${GREEN}✅ Successfully pushed to $TARGET_BRANCH${NC}"
    echo ""
    
    # Get repository info for monitoring links
    if command -v gh &> /dev/null && gh auth status &> /dev/null; then
        REPO_URL=$(gh repo view --json url -q .url 2>/dev/null || echo "")
        if [ -n "$REPO_URL" ]; then
            echo "📊 Monitor deployment:"
            echo "  GitHub Actions: $REPO_URL/actions"
            echo "  Latest workflow: $REPO_URL/actions/runs"
        fi
    fi
    
    echo ""
    echo "💡 Next steps:"
    echo "  1. Monitor GitHub Actions for deployment progress"
    echo "  2. Verify deployment completes successfully"
    echo "  3. Test application functionality"
    echo "  4. Wait for deployment completion before making more changes"
    
else
    echo ""
    echo -e "${RED}❌ Push failed${NC}"
    echo ""
    echo "Common solutions:"
    echo "  1. Pull latest changes: git pull origin $TARGET_BRANCH"
    echo "  2. Resolve any merge conflicts"
    echo "  3. Try pushing again: $0 $TARGET_BRANCH"
    exit 1
fi

echo ""
echo "======================================"
echo -e "${GREEN}🎉 Safe Push Complete${NC}"
echo "======================================"