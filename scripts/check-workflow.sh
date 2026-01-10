#!/bin/bash
# Check GitHub Actions workflow status before pushing
# Returns exit code 0 if safe to push, 1 if workflow is running

set -e

# Configuration
REPO_OWNER="jocousen"  # Update with actual GitHub username/org
REPO_NAME="aws-elasticdrs-orchestrator"  # Update with actual repo name

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔍 Checking GitHub Actions workflow status..."

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub CLI not installed${NC}"
    echo "Install with: brew install gh"
    echo "Then authenticate: gh auth login"
    echo ""
    echo -e "${BLUE}ℹ️  Proceeding without workflow check (not recommended)${NC}"
    exit 0
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub CLI not authenticated${NC}"
    echo "Authenticate with: gh auth login"
    echo ""
    echo -e "${BLUE}ℹ️  Proceeding without workflow check (not recommended)${NC}"
    exit 0
fi

# Get current repository info
if git rev-parse --git-dir > /dev/null 2>&1; then
    CURRENT_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "unknown/unknown")
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
else
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

echo "Repository: $CURRENT_REPO"
echo "Branch: $CURRENT_BRANCH"
echo ""

# Check for running workflows
echo "Checking for running workflows..."
RUNNING_WORKFLOWS=$(gh run list --status in_progress --limit 10 --json status,conclusion,workflowName,createdAt,url 2>/dev/null || echo "[]")

if [ "$RUNNING_WORKFLOWS" = "[]" ] || [ -z "$RUNNING_WORKFLOWS" ]; then
    echo -e "${GREEN}✅ No workflows currently running${NC}"
    echo -e "${GREEN}✅ Safe to push${NC}"
    exit 0
else
    echo -e "${RED}⏳ Workflows currently running:${NC}"
    echo ""
    
    # Parse and display running workflows
    echo "$RUNNING_WORKFLOWS" | jq -r '.[] | "  🔄 \(.workflowName) - Started: \(.createdAt) - \(.url)"' 2>/dev/null || {
        echo "  🔄 At least one workflow is running"
        echo "  Check GitHub Actions tab for details"
    }
    
    echo ""
    echo -e "${RED}❌ Cannot push while workflows are running${NC}"
    echo -e "${YELLOW}⚠️  This prevents deployment conflicts and failures${NC}"
    echo ""
    echo "Options:"
    echo "  1. Wait for workflows to complete (recommended)"
    echo "  2. Use emergency force push: ./scripts/safe-push.sh --force"
    echo "  3. Check workflow status: gh run list"
    echo "  4. Monitor in browser: https://github.com/$CURRENT_REPO/actions"
    echo ""
    
    # Estimate wait time
    echo "💡 Most workflows complete within 20-30 minutes"
    echo "   You can monitor progress at: https://github.com/$CURRENT_REPO/actions"
    
    exit 1
fi