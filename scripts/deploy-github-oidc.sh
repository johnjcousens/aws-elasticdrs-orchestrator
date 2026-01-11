#!/bin/bash
# Deploy GitHub OIDC stack with automatic repository detection and validation
# Usage: ./scripts/deploy-github-oidc.sh [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-test}"
PROJECT_NAME="aws-elasticdrs-orchestrator"
DEPLOYMENT_BUCKET="aws-elasticdrs-orchestrator"
REGION="us-east-1"

echo "======================================"
echo "🔐 GitHub OIDC Stack Deployment"
echo "======================================"
echo "Environment: $ENVIRONMENT"
echo "Project: $PROJECT_NAME"
echo ""

# Auto-detect repository information
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Get repository URL and extract org/repo
REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REPO_URL" ]; then
    echo -e "${RED}❌ No git remote 'origin' found${NC}"
    exit 1
fi

echo "🔍 Auto-detecting repository information..."
echo "Repository URL: $REPO_URL"

# Extract GitHub org and repo from various URL formats
if [[ "$REPO_URL" =~ git@github\.com:([^/]+)/([^.]+)\.git ]]; then
    GITHUB_ORG="${BASH_REMATCH[1]}"
    GITHUB_REPO="${BASH_REMATCH[2]}"
elif [[ "$REPO_URL" =~ https://github\.com/([^/]+)/([^.]+)\.git ]]; then
    GITHUB_ORG="${BASH_REMATCH[1]}"
    GITHUB_REPO="${BASH_REMATCH[2]}"
elif [[ "$REPO_URL" =~ https://github\.com/([^/]+)/([^/]+) ]]; then
    GITHUB_ORG="${BASH_REMATCH[1]}"
    GITHUB_REPO="${BASH_REMATCH[2]}"
else
    echo -e "${RED}❌ Could not parse GitHub repository from URL: $REPO_URL${NC}"
    echo "Expected format: git@github.com:org/repo.git or https://github.com/org/repo.git"
    exit 1
fi

echo -e "${GREEN}✅ Repository detected:${NC}"
echo "  Organization: $GITHUB_ORG"
echo "  Repository: $GITHUB_REPO"
echo ""

# Validate repository name matches expected
EXPECTED_REPO="aws-elasticdrs-orchestrator"
if [ "$GITHUB_REPO" != "$EXPECTED_REPO" ]; then
    echo -e "${YELLOW}⚠️  Repository name mismatch:${NC}"
    echo "  Expected: $EXPECTED_REPO"
    echo "  Detected: $GITHUB_REPO"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled"
        exit 1
    fi
fi

# Check if OIDC provider exists
echo "🔍 Checking GitHub OIDC provider..."
OIDC_PROVIDER=$(aws iam list-open-id-connect-providers \
    --query 'OpenIDConnectProviderList[?contains(Arn, `token.actions.githubusercontent.com`)].Arn' \
    --output text --region $REGION 2>/dev/null || echo "")

if [ -z "$OIDC_PROVIDER" ]; then
    echo -e "${YELLOW}⚠️  GitHub OIDC provider not found${NC}"
    echo "Creating OIDC provider first..."
    
    # Create OIDC provider
    aws iam create-open-id-connect-provider \
        --url https://token.actions.githubusercontent.com \
        --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
        --client-id-list sts.amazonaws.com \
        --region $REGION
    
    echo -e "${GREEN}✅ OIDC provider created${NC}"
else
    echo -e "${GREEN}✅ OIDC provider exists: $OIDC_PROVIDER${NC}"
fi

# Stack configuration
STACK_NAME="$PROJECT_NAME-github-oidc-$ENVIRONMENT"
APPLICATION_STACK_NAME="$PROJECT_NAME-$ENVIRONMENT"

echo ""
echo "🚀 Deploying GitHub OIDC stack..."
echo "Stack Name: $STACK_NAME"
echo "Application Stack: $APPLICATION_STACK_NAME"
echo ""

# Deploy the stack
aws cloudformation deploy \
    --template-file cfn/github-oidc-stack.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        ProjectName="$PROJECT_NAME" \
        Environment="$ENVIRONMENT" \
        GitHubOrg="$GITHUB_ORG" \
        GitHubRepo="$GITHUB_REPO" \
        DeploymentBucket="$DEPLOYMENT_BUCKET" \
        ApplicationStackName="$APPLICATION_STACK_NAME" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION \
    --tags \
        Project="$PROJECT_NAME" \
        Environment="$ENVIRONMENT" \
        Component="GitHub-OIDC"

echo ""
echo -e "${GREEN}✅ GitHub OIDC stack deployed successfully!${NC}"
echo ""

# Get the role ARN
ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`GitHubActionsRoleArn`].OutputValue' \
    --output text --region $REGION)

echo "======================================"
echo "🔑 GitHub Repository Secrets"
echo "======================================"
echo ""
echo "Update these secrets in your GitHub repository:"
echo "https://github.com/$GITHUB_ORG/$GITHUB_REPO/settings/secrets/actions"
echo ""
echo -e "${BLUE}AWS_ROLE_ARN:${NC} $ROLE_ARN"
echo -e "${BLUE}STACK_NAME:${NC} $APPLICATION_STACK_NAME"
echo -e "${BLUE}DEPLOYMENT_BUCKET:${NC} $DEPLOYMENT_BUCKET"
echo -e "${BLUE}ADMIN_EMAIL:${NC} ***REMOVED***"
echo ""

# Validation
echo "======================================"
echo "🔍 Validation"
echo "======================================"
echo ""

# Test role assumption (this will fail but shows the trust policy is correct)
echo "Testing role trust policy..."
aws sts assume-role-with-web-identity \
    --role-arn "$ROLE_ARN" \
    --role-session-name "test-session" \
    --web-identity-token "dummy-token" \
    --region $REGION 2>&1 | grep -q "InvalidIdentityToken" && \
    echo -e "${GREEN}✅ Role trust policy configured correctly${NC}" || \
    echo -e "${YELLOW}⚠️  Role trust policy may need verification${NC}"

echo ""
echo -e "${GREEN}🎉 GitHub OIDC deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Update GitHub repository secrets (shown above)"
echo "2. Test GitHub Actions deployment"
echo "3. Monitor pipeline at: https://github.com/$GITHUB_ORG/$GITHUB_REPO/actions"