#!/bin/bash
#
# Integrated Deployment Script with Full CI/CD Validation
# Combines CI checks, build, and deployment into single workflow
#
# Repository Structure:
#   This script works from the repository root directory.
#   All paths are relative to the repository root.
#
# Usage:
#   ./scripts/deploy-with-validation.sh [environment] [options]
#
# Arguments:
#   environment: dev (default), test, prod
#
# Options:
#   --skip-validation    Skip validation stage (NOT RECOMMENDED)
#   --skip-security      Skip security scans (NOT RECOMMENDED)
#   --skip-tests         Skip unit tests
#   --quick              Skip validation, security, and tests (DANGEROUS)
#   --frontend-only      Deploy frontend only
#   --lambda-only        Deploy Lambda functions only
#   --dry-run            Show what would be deployed without deploying

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root for all operations
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-dev}"
SKIP_VALIDATION=false
SKIP_SECURITY=false
SKIP_TESTS=false
DEPLOYMENT_TYPE="full"
DRY_RUN=false

# Parse options
shift || true
for arg in "$@"; do
    case $arg in
        --skip-validation)
            SKIP_VALIDATION=true
            ;;
        --skip-security)
            SKIP_SECURITY=true
            ;;
        --skip-tests)
            SKIP_TESTS=true
            ;;
        --quick)
            SKIP_VALIDATION=true
            SKIP_SECURITY=true
            SKIP_TESTS=true
            ;;
        --frontend-only)
            DEPLOYMENT_TYPE="frontend-only"
            ;;
        --lambda-only)
            DEPLOYMENT_TYPE="lambda-only"
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|test|prod)$ ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo "Valid environments: dev, test, prod"
    exit 1
fi

# Stack protection
PROJECT_NAME="aws-drs-orchestration"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

if [[ "$STACK_NAME" == *"-test"* ]] || [[ "$STACK_NAME" == "aws-elasticdrs-orchestrator"* ]]; then
    echo -e "${RED}❌ CRITICAL: Cannot deploy to protected stack!${NC}"
    echo "Stack '$STACK_NAME' appears to be a protected production stack."
    echo "Use 'aws-drs-orchestration-dev' for development."
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AWS DRS Orchestration - Validated Deployment             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Environment:${NC}      $ENVIRONMENT"
echo -e "${GREEN}Stack:${NC}            $STACK_NAME"
echo -e "${GREEN}Deployment Type:${NC}  $DEPLOYMENT_TYPE"
echo -e "${GREEN}Dry Run:${NC}          $DRY_RUN"
echo ""

# Warning for skipped checks
if [ "$SKIP_VALIDATION" = true ] || [ "$SKIP_SECURITY" = true ] || [ "$SKIP_TESTS" = true ]; then
    echo -e "${YELLOW}⚠️  WARNING: Quality gates are being skipped!${NC}"
    [ "$SKIP_VALIDATION" = true ] && echo -e "${YELLOW}   - Validation checks skipped${NC}"
    [ "$SKIP_SECURITY" = true ] && echo -e "${YELLOW}   - Security scans skipped${NC}"
    [ "$SKIP_TESTS" = true ] && echo -e "${YELLOW}   - Unit tests skipped${NC}"
    echo ""
    echo -e "${YELLOW}This is NOT recommended for production deployments.${NC}"
    echo ""
    read -p "Continue anyway? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Deployment cancelled."
        exit 1
    fi
    echo ""
fi

# ============================================================================
# STAGE 1: CI/CD QUALITY CHECKS
# ============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  STAGE 1: CI/CD QUALITY CHECKS${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

CI_CHECK_ARGS=""
[ "$SKIP_TESTS" = true ] && CI_CHECK_ARGS="$CI_CHECK_ARGS --skip-tests"
[ "$SKIP_SECURITY" = true ] && CI_CHECK_ARGS="$CI_CHECK_ARGS --skip-security"

if [ "$SKIP_VALIDATION" = false ]; then
    echo "Running CI/CD quality checks..."
    if ./scripts/local-ci-checks.sh $CI_CHECK_ARGS; then
        echo -e "${GREEN}✅ All quality checks passed${NC}"
    else
        echo -e "${RED}❌ Quality checks failed${NC}"
        echo ""
        echo "Fix the issues and try again, or use --skip-validation to bypass (not recommended)."
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Validation skipped${NC}"
fi

echo ""

# ============================================================================
# STAGE 2: BUILD
# ============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  STAGE 2: BUILD${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

if [[ "$DEPLOYMENT_TYPE" != "frontend-only" ]]; then
    echo "Building Lambda packages..."
    python3 package_lambda.py
    echo -e "${GREEN}✓ Lambda packages built${NC}"
    echo ""
    
    # Show package sizes
    echo "Lambda package sizes:"
    ls -lh build/lambda/*.zip | awk '{print "  " $9 ": " $5}'
    echo ""
fi

if [[ "$DEPLOYMENT_TYPE" != "lambda-only" ]]; then
    echo "Preparing frontend source..."
    if [ ! -d "frontend/node_modules" ]; then
        cd frontend
        npm ci --silent
        cd ..
    fi
    echo -e "${GREEN}✓ Frontend source prepared (will be built by FrontendBuilder Lambda)${NC}"
    echo ""
fi

# ============================================================================
# STAGE 3: DEPLOYMENT
# ============================================================================
if [ "$DRY_RUN" = true ]; then
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  DRY RUN - No actual deployment${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Would deploy:"
    echo "  - Stack: $STACK_NAME"
    echo "  - Environment: $ENVIRONMENT"
    echo "  - Type: $DEPLOYMENT_TYPE"
    echo ""
    echo "Deployment cancelled (dry run mode)."
    exit 0
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  STAGE 3: DEPLOYMENT${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Call the deployment script
./scripts/local-deploy.sh "$ENVIRONMENT" "$DEPLOYMENT_TYPE"

# ============================================================================
# STAGE 4: POST-DEPLOYMENT VALIDATION
# ============================================================================
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  STAGE 4: POST-DEPLOYMENT VALIDATION${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

echo "Verifying stack deployment..."
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region us-east-1 \
    --query 'Stacks[0].StackStatus' \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [[ "$STACK_STATUS" == *"COMPLETE"* ]]; then
    echo -e "${GREEN}✓ Stack status: $STACK_STATUS${NC}"
else
    echo -e "${RED}✗ Stack status: $STACK_STATUS${NC}"
    echo ""
    echo "Check CloudFormation console for details:"
    echo "https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks"
    exit 1
fi

# Get stack outputs
echo ""
echo "Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[].{Key:OutputKey,Value:OutputValue}' \
    --output table

# ============================================================================
# DEPLOYMENT SUMMARY
# ============================================================================
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  DEPLOYMENT COMPLETE                                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
    --output text 2>/dev/null || echo "N/A")

API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "N/A")

echo -e "${GREEN}✅ Deployment successful!${NC}"
echo ""
echo "Application URL: $CLOUDFRONT_URL"
echo "API Endpoint: $API_ENDPOINT"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Test the application at the CloudFront URL"
echo "2. Verify API endpoints are responding"
echo "3. Check CloudWatch logs for any errors"
echo "4. Run smoke tests"
echo ""
