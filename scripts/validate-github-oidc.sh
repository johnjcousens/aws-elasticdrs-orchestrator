#!/bin/bash
# Validate GitHub OIDC role matches the actual repository
# Usage: ./scripts/validate-github-oidc.sh [environment]

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
REGION="us-east-1"

echo "======================================"
echo "🔍 GitHub OIDC Validation"
echo "======================================"
echo "Environment: $ENVIRONMENT"
echo ""

# Auto-detect repository information
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REPO_URL" ]; then
    echo -e "${RED}❌ No git remote 'origin' found${NC}"
    exit 1
fi

# Extract GitHub org and repo
if [[ "$REPO_URL" =~ git@github\.com:([^/]+)/([^.]+)\.git ]]; then
    ACTUAL_ORG="${BASH_REMATCH[1]}"
    ACTUAL_REPO="${BASH_REMATCH[2]}"
elif [[ "$REPO_URL" =~ https://github\.com/([^/]+)/([^.]+)\.git ]]; then
    ACTUAL_ORG="${BASH_REMATCH[1]}"
    ACTUAL_REPO="${BASH_REMATCH[2]}"
elif [[ "$REPO_URL" =~ https://github\.com/([^/]+)/([^/]+) ]]; then
    ACTUAL_ORG="${BASH_REMATCH[1]}"
    ACTUAL_REPO="${BASH_REMATCH[2]}"
else
    echo -e "${RED}❌ Could not parse GitHub repository from URL: $REPO_URL${NC}"
    exit 1
fi

echo "🔍 Detected repository: $ACTUAL_ORG/$ACTUAL_REPO"
echo ""

# Check if OIDC role exists
ROLE_NAME="$PROJECT_NAME-github-actions-$ENVIRONMENT"
echo "🔍 Checking OIDC role: $ROLE_NAME"

if ! aws iam get-role --role-name "$ROLE_NAME" --region $REGION >/dev/null 2>&1; then
    echo -e "${RED}❌ OIDC role not found: $ROLE_NAME${NC}"
    echo ""
    echo "Create the role with:"
    echo "  ./scripts/deploy-github-oidc.sh $ENVIRONMENT"
    exit 1
fi

# Get role trust policy
TRUST_POLICY=$(aws iam get-role --role-name "$ROLE_NAME" \
    --query 'Role.AssumeRolePolicyDocument' --output json --region $REGION)

echo -e "${GREEN}✅ OIDC role found${NC}"
echo ""

# Extract repository from trust policy
CONFIGURED_REPOS=$(echo "$TRUST_POLICY" | jq -r '.Statement[0].Condition.StringLike["token.actions.githubusercontent.com:sub"][]' | grep "repo:" | sed 's/repo:\([^:]*\):.*/\1/')

echo "🔍 Validating repository configuration..."
echo ""

VALIDATION_PASSED=true
EXPECTED_REPO="$ACTUAL_ORG/$ACTUAL_REPO"

echo "Expected repository: $EXPECTED_REPO"
echo "Configured repositories in trust policy:"

while IFS= read -r configured_repo; do
    echo "  - $configured_repo"
    if [ "$configured_repo" = "$EXPECTED_REPO" ]; then
        echo -e "    ${GREEN}✅ Match found${NC}"
    fi
done <<< "$CONFIGURED_REPOS"

# Check if expected repo is in configured repos
if echo "$CONFIGURED_REPOS" | grep -q "^$EXPECTED_REPO$"; then
    echo ""
    echo -e "${GREEN}✅ Repository validation passed${NC}"
    echo "The OIDC role is correctly configured for: $EXPECTED_REPO"
else
    echo ""
    echo -e "${RED}❌ Repository validation failed${NC}"
    echo "The OIDC role is NOT configured for: $EXPECTED_REPO"
    echo ""
    echo "Configured repositories:"
    echo "$CONFIGURED_REPOS" | sed 's/^/  - /'
    echo ""
    echo "Fix this by running:"
    echo "  ./scripts/deploy-github-oidc.sh $ENVIRONMENT"
    VALIDATION_PASSED=false
fi

# Additional validations
echo ""
echo "🔍 Additional validations..."

# Check OIDC provider
OIDC_PROVIDER=$(aws iam list-open-id-connect-providers \
    --query 'OpenIDConnectProviderList[?contains(Arn, `token.actions.githubusercontent.com`)].Arn' \
    --output text --region $REGION 2>/dev/null || echo "")

if [ -n "$OIDC_PROVIDER" ]; then
    echo -e "${GREEN}✅ GitHub OIDC provider exists${NC}"
else
    echo -e "${RED}❌ GitHub OIDC provider missing${NC}"
    VALIDATION_PASSED=false
fi

# Check if role ARN matches GitHub secrets format
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" \
    --query 'Role.Arn' --output text --region $REGION)

echo -e "${BLUE}ℹ️  Role ARN:${NC} $ROLE_ARN"

# Summary
echo ""
echo "======================================"
if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}✅ All validations passed${NC}"
    echo "======================================"
    echo ""
    echo "GitHub Actions should be able to assume this role successfully."
    echo ""
    echo "GitHub repository secrets should be:"
    echo "  AWS_ROLE_ARN: $ROLE_ARN"
    echo "  STACK_NAME: $PROJECT_NAME-$ENVIRONMENT"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Validation failed${NC}"
    echo "======================================"
    echo ""
    echo "Fix the issues above before using GitHub Actions."
    echo ""
    exit 1
fi