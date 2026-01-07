#!/bin/bash

# Quick Workflow Status Check
# Simple script to check if GitHub Actions is currently running

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_OWNER="johnjcousens"
REPO_NAME="aws-elasticdrs-orchestrator"

echo -e "${BLUE}🔍 Checking GitHub Actions status...${NC}"

# Check if GitHub CLI is available
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) is not installed${NC}"
    echo -e "${YELLOW}💡 Install with: brew install gh${NC}"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI is not authenticated${NC}"
    echo -e "${YELLOW}💡 Authenticate with: gh auth login${NC}"
    exit 1
fi

# Get running workflows
running_workflows=$(gh run list \
    --repo "${REPO_OWNER}/${REPO_NAME}" \
    --status "in_progress" \
    --limit 5 \
    --json status,conclusion,workflowName,createdAt,url,headBranch \
    --jq '.[] | select(.workflowName == "Deploy to AWS")')

if [ -n "$running_workflows" ]; then
    echo -e "${YELLOW}⏳ GitHub Actions workflow is currently running:${NC}"
    echo "$running_workflows" | jq -r '"   • " + .workflowName + " on " + .headBranch + " (started: " + (.createdAt | fromdateiso8601 | strftime("%H:%M:%S")) + ")"'
    echo ""
    echo -e "${YELLOW}⚠️  Wait for completion before pushing to avoid conflicts${NC}"
    echo -e "${BLUE}🔗 Monitor: https://github.com/${REPO_OWNER}/${REPO_NAME}/actions${NC}"
    exit 1
else
    echo -e "${GREEN}✅ No workflows currently running - safe to push${NC}"
    exit 0
fi