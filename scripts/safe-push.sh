#!/bin/bash

# Safe Push Script
# Checks if GitHub Actions workflow is running before pushing to prevent conflicts

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
WORKFLOW_NAME="deploy.yml"
MAX_WAIT_TIME=1800  # 30 minutes max wait
CHECK_INTERVAL=30   # Check every 30 seconds

echo -e "${BLUE}🔍 Safe Push - Checking GitHub Actions status...${NC}"

# Function to check if GitHub CLI is available
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        echo -e "${RED}❌ GitHub CLI (gh) is not installed or not in PATH${NC}"
        echo -e "${YELLOW}💡 Install with: brew install gh${NC}"
        echo -e "${YELLOW}💡 Then authenticate with: gh auth login${NC}"
        exit 1
    fi
    
    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        echo -e "${RED}❌ GitHub CLI is not authenticated${NC}"
        echo -e "${YELLOW}💡 Authenticate with: gh auth login${NC}"
        exit 1
    fi
}

# Function to get running workflows
get_running_workflows() {
    gh run list \
        --repo "${REPO_OWNER}/${REPO_NAME}" \
        --status "in_progress" \
        --limit 10 \
        --json status,conclusion,workflowName,createdAt,url \
        --jq '.[] | select(.workflowName == "Deploy to AWS")'
}

# Function to wait for workflows to complete
wait_for_workflows() {
    local wait_time=0
    
    while [ $wait_time -lt $MAX_WAIT_TIME ]; do
        local running_workflows=$(get_running_workflows)
        
        if [ -z "$running_workflows" ]; then
            echo -e "${GREEN}✅ No workflows currently running${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Workflow still running... (waited ${wait_time}s/${MAX_WAIT_TIME}s)${NC}"
        echo "$running_workflows" | jq -r '"   • " + .workflowName + " (started: " + .createdAt + ")"'
        
        sleep $CHECK_INTERVAL
        wait_time=$((wait_time + CHECK_INTERVAL))
    done
    
    echo -e "${RED}❌ Timeout: Workflow still running after ${MAX_WAIT_TIME} seconds${NC}"
    return 1
}

# Function to push changes
safe_push() {
    local branch=${1:-$(git branch --show-current)}
    
    echo -e "${BLUE}🚀 Pushing to branch: ${branch}${NC}"
    
    # Check if there are changes to push
    if git diff --quiet HEAD origin/"$branch" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  No changes to push${NC}"
        return 0
    fi
    
    # Push the changes
    if git push origin "$branch"; then
        echo -e "${GREEN}✅ Successfully pushed to ${branch}${NC}"
        echo -e "${BLUE}🔗 Monitor deployment: https://github.com/${REPO_OWNER}/${REPO_NAME}/actions${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to push changes${NC}"
        return 1
    fi
}

# Main execution
main() {
    local branch=${1:-$(git branch --show-current)}
    local force_push=${2:-false}
    
    echo -e "${BLUE}📋 Repository: ${REPO_OWNER}/${REPO_NAME}${NC}"
    echo -e "${BLUE}🌿 Branch: ${branch}${NC}"
    
    # Check prerequisites
    check_gh_cli
    
    # Skip workflow check if force flag is provided
    if [ "$force_push" = "--force" ] || [ "$force_push" = "-f" ]; then
        echo -e "${YELLOW}⚠️  Force push requested - skipping workflow check${NC}"
        safe_push "$branch"
        return $?
    fi
    
    # Check for running workflows
    echo -e "${BLUE}🔍 Checking for running workflows...${NC}"
    local running_workflows=$(get_running_workflows)
    
    if [ -n "$running_workflows" ]; then
        echo -e "${YELLOW}⏳ Found running workflow:${NC}"
        echo "$running_workflows" | jq -r '"   • " + .workflowName + " (started: " + .createdAt + ")"'
        echo ""
        
        read -p "$(echo -e ${YELLOW}❓ Wait for workflow to complete? [Y/n]: ${NC})" -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            echo -e "${YELLOW}⚠️  Push cancelled by user${NC}"
            return 1
        fi
        
        echo -e "${BLUE}⏳ Waiting for workflow to complete...${NC}"
        if ! wait_for_workflows; then
            echo -e "${RED}❌ Workflow did not complete in time${NC}"
            echo -e "${YELLOW}💡 You can force push with: $0 --force${NC}"
            return 1
        fi
    fi
    
    # All clear - push the changes
    safe_push "$branch"
}

# Help function
show_help() {
    echo "Safe Push Script - Prevents GitHub Actions conflicts"
    echo ""
    echo "Usage:"
    echo "  $0 [branch] [--force|-f]"
    echo ""
    echo "Options:"
    echo "  branch     Target branch (default: current branch)"
    echo "  --force    Skip workflow check and push immediately"
    echo "  --help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Push current branch after checking workflows"
    echo "  $0 main               # Push to main branch after checking workflows"
    echo "  $0 --force            # Force push without checking workflows"
    echo "  $0 main --force       # Force push to main without checking workflows"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        exit $?
        ;;
esac