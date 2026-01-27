#!/bin/bash
#
# Unified CI/CD Deploy Script
# Usage: ./scripts/deploy.sh [environment] [options]
#
# Environment Variables (all optional):
#   PROJECT_NAME              - Project name (default: aws-drs-orchestration)
#   STACK_NAME                - CloudFormation stack name (default: ${PROJECT_NAME}-${ENVIRONMENT})
#   DEPLOYMENT_BUCKET         - S3 bucket for artifacts (default: ${PROJECT_NAME}-${ENVIRONMENT})
#   ADMIN_EMAIL               - Admin email for Cognito (default: jocousen@amazon.com)
#   CROSS_ACCOUNT_ROLE_NAME   - Pre-existing cross-account role name (default: empty, creates new role)
#   ENABLE_NOTIFICATIONS      - Enable email notifications (default: true)
#
# Repository Structure:
#   This script works from the repository root directory.
#   All paths are relative to the repository root.
#
# Examples:
#   ./scripts/deploy.sh dev                                    # Full pipeline: validate, test, push, deploy
#   ./scripts/deploy.sh dev --quick                            # Skip security scans and tests
#   ./scripts/deploy.sh dev --lambda-only                      # Just update Lambda code
#   ./scripts/deploy.sh dev --frontend-only                    # Just rebuild frontend
#   ./scripts/deploy.sh dev --validate-only                    # Run validation/tests only (no deployment)
#   ./scripts/deploy.sh dev --skip-push                        # Skip git push (but still deploy)
#   ./scripts/deploy.sh dev --no-frontend                      # API-only deployment (no S3/CloudFront)
#   ./scripts/deploy.sh dev --orchestration-role arn:aws:iam::123456789012:role/MyRole  # Use external role
#
# Deployment Modes (via --no-frontend and --orchestration-role):
#   1. Default (standalone with frontend):
#      ./scripts/deploy.sh dev
#      - Creates unified orchestration role
#      - Deploys full frontend (S3, CloudFront)
#
#   2. API-only standalone:
#      ./scripts/deploy.sh dev --no-frontend
#      - Creates unified orchestration role
#      - Skips frontend deployment
#
#   3. HRP integration with frontend:
#      ./scripts/deploy.sh dev --orchestration-role arn:aws:iam::123456789012:role/HRPRole
#      - Uses external HRP orchestration role
#      - Deploys full frontend
#
#   4. Full HRP integration (API-only):
#      ./scripts/deploy.sh dev --no-frontend --orchestration-role arn:aws:iam::123456789012:role/HRPRole
#      - Uses external HRP orchestration role
#      - Skips frontend deployment

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
NC='\033[0m'

# ============================================================================
# CONFIGURATION
# ============================================================================

# Required Parameters
ENVIRONMENT="${1:-dev}"
AWS_REGION="us-east-1"
PROJECT_NAME="${PROJECT_NAME:-aws-drs-orchestration}"
STACK_NAME="${STACK_NAME:-${PROJECT_NAME}-${ENVIRONMENT}}"
DEPLOYMENT_BUCKET="${DEPLOYMENT_BUCKET:-${PROJECT_NAME}-${ENVIRONMENT}}"
ADMIN_EMAIL="${ADMIN_EMAIL:-jocousen@amazon.com}"

# Deployment Flexibility Parameters (from deployment-flexibility spec)
ORCHESTRATION_ROLE_ARN="${ORCHESTRATION_ROLE_ARN:-}"  # Empty = create unified role
DEPLOY_FRONTEND="${DEPLOY_FRONTEND:-true}"            # true = deploy frontend

# Cross-Account Configuration (optional)
CROSS_ACCOUNT_ROLE_NAME="${CROSS_ACCOUNT_ROLE_NAME:-}"  # Empty = no cross-account

# Notification Configuration (optional)
ENABLE_NOTIFICATIONS="${ENABLE_NOTIFICATIONS:-true}"  # true = enable email notifications

# Hardcoded Internal Values (per frontend-deployment-hardening spec)
# The following parameters were removed from master-template.yaml and are now:
# - TagSyncIntervalHours: Hardcoded to 1 hour in eventbridge-stack.yaml
# - EnableTagSync: Hardcoded to always enabled in eventbridge-stack.yaml
# - ApiDeploymentTimestamp: Generated internally by API Gateway deployment
# - FrontendBuildTimestamp: Generated internally by frontend deployer
# - NotificationEmail: Consolidated into AdminEmail
# - CognitoDomainPrefix: Removed (unused)
# - ForceRecreation: Removed (dangerous migration hack)

# Parse options
SKIP_SECURITY=false
SKIP_TESTS=false
LAMBDA_ONLY=false
FRONTEND_ONLY=false
SKIP_PUSH=false
FORCE=false
DEPLOY_FRONTEND="true"
ORCHESTRATION_ROLE_ARN=""
VALIDATE_ONLY=false

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

generate_frontend_version() {
    # Generate timestamp-based version: YYYYMMDD-HHMM
    date +"%Y%m%d-%H%M"
}

# ============================================================================
# PARSE OPTIONS
# ============================================================================

shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick) SKIP_SECURITY=true; SKIP_TESTS=true ;;
        --lambda-only) LAMBDA_ONLY=true ;;
        --frontend-only) FRONTEND_ONLY=true ;;
        --skip-push) SKIP_PUSH=true ;;
        --validate-only) VALIDATE_ONLY=true; SKIP_PUSH=true ;;
        --force) FORCE=true ;;
        --no-frontend) DEPLOY_FRONTEND="false" ;;
        --orchestration-role)
            ORCHESTRATION_ROLE_ARN="$2"
            shift
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

# Stack protection
if [[ "$STACK_NAME" == *"elasticdrs-orchestrator-test"* ]] || [[ "$STACK_NAME" == *"-test" ]]; then
    echo -e "${RED}❌ CRITICAL: Cannot deploy to protected stack!${NC}"
    exit 1
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Deploy: $STACK_NAME${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Verify AWS credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
fi

# Concurrency protection - check if stack is already being updated
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "DOES_NOT_EXIST")

if [[ "$STACK_STATUS" == *"IN_PROGRESS"* ]]; then
    if [ "$FORCE" = true ]; then
        echo -e "${YELLOW}⚠ Stack status: $STACK_STATUS (forcing deployment)${NC}"
    else
        echo -e "${RED}❌ Stack is currently being updated (status: $STACK_STATUS)${NC}"
        echo -e "${YELLOW}   Wait for the current deployment to complete before starting another.${NC}"
        echo -e "${YELLOW}   Or use --force to bypass this check.${NC}"
        echo ""
        echo "   To check status: aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].StackStatus'"
        exit 1
    fi
fi

# Handle UPDATE_ROLLBACK_FAILED state - attempt recovery
if [[ "$STACK_STATUS" == "UPDATE_ROLLBACK_FAILED" ]]; then
    echo -e "${YELLOW}⚠ Stack is in UPDATE_ROLLBACK_FAILED state - attempting recovery...${NC}"
    
    # Find nested stacks that are also in failed state
    NESTED_STACKS=$(aws cloudformation list-stack-resources --stack-name "$STACK_NAME" \
        --query 'StackResourceSummaries[?ResourceType==`AWS::CloudFormation::Stack` && ResourceStatus==`UPDATE_FAILED`].LogicalResourceId' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$NESTED_STACKS" ]; then
        echo -e "${YELLOW}  Found failed nested stacks: $NESTED_STACKS${NC}"
        echo -e "${YELLOW}  Attempting continue-update-rollback with skip...${NC}"
        
        # Build skip list
        SKIP_RESOURCES=""
        for stack in $NESTED_STACKS; do
            SKIP_RESOURCES="$SKIP_RESOURCES $stack"
        done
        
        if aws cloudformation continue-update-rollback --stack-name "$STACK_NAME" \
            --resources-to-skip $SKIP_RESOURCES 2>/dev/null; then
            echo -e "${GREEN}  ✓ Rollback recovery initiated${NC}"
            
            # Wait for rollback to complete
            echo "  Waiting for rollback to complete..."
            aws cloudformation wait stack-rollback-complete --stack-name "$STACK_NAME" 2>/dev/null || true
            
            # Check new status
            STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
                --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "UNKNOWN")
            echo -e "${GREEN}  ✓ Stack status: $STACK_STATUS${NC}"
        else
            echo -e "${RED}  ✗ Rollback recovery failed${NC}"
            echo -e "${YELLOW}  Manual intervention may be required.${NC}"
            exit 1
        fi
    else
        # No nested stacks failed, try simple continue
        if aws cloudformation continue-update-rollback --stack-name "$STACK_NAME" 2>/dev/null; then
            echo -e "${GREEN}  ✓ Rollback recovery initiated${NC}"
            aws cloudformation wait stack-rollback-complete --stack-name "$STACK_NAME" 2>/dev/null || true
            STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
                --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "UNKNOWN")
            echo -e "${GREEN}  ✓ Stack status: $STACK_STATUS${NC}"
        else
            echo -e "${RED}  ✗ Rollback recovery failed${NC}"
            exit 1
        fi
    fi
    echo ""
fi

FAILED=false

# Stage 1: Validation
echo -e "${BLUE}[1/5] Validation${NC}"

# cfn-lint
if command -v cfn-lint &> /dev/null; then
    if cfn-lint cfn/*.yaml 2>&1 | grep -v "^W" | grep -q "^E"; then
        echo -e "${RED}  ✗ cfn-lint: errors found${NC}"
        FAILED=true
    else
        echo -e "${GREEN}  ✓ cfn-lint${NC}"
    fi
fi

# flake8
if [ -f ".venv/bin/flake8" ]; then
    FLAKE8_CMD=".venv/bin/flake8"
elif command -v flake8 &> /dev/null; then
    FLAKE8_CMD="flake8"
else
    FLAKE8_CMD=""
fi

if [ -n "$FLAKE8_CMD" ]; then
    if $FLAKE8_CMD lambda/ --config .flake8 --count -q 2>&1 | grep -q "^[0-9]"; then
        echo -e "${YELLOW}  ⚠ flake8: warnings (non-blocking)${NC}"
    else
        echo -e "${GREEN}  ✓ flake8${NC}"
    fi
fi

# black
if [ -f ".venv/bin/black" ]; then
    BLACK_CMD=".venv/bin/black"
elif command -v black &> /dev/null; then
    BLACK_CMD="black"
else
    BLACK_CMD=""
fi

if [ -n "$BLACK_CMD" ]; then
    if ! $BLACK_CMD --check --quiet --line-length 79 lambda/ 2>/dev/null; then
        echo -e "${RED}  ✗ black: needs formatting${NC}"
        echo "    Run: black --line-length 79 lambda/"
        FAILED=true
    else
        echo -e "${GREEN}  ✓ black${NC}"
    fi
fi

# TypeScript
if [ -d "frontend" ]; then
    cd frontend
    if npm run type-check --silent 2>/dev/null; then
        echo -e "${GREEN}  ✓ TypeScript${NC}"
    else
        echo -e "${RED}  ✗ TypeScript: errors${NC}"
        FAILED=true
    fi
    cd ..
fi

echo ""

# Stage 2: Security (unless skipped)
if [ "$SKIP_SECURITY" = false ]; then
    echo -e "${BLUE}[2/5] Security${NC}"
    
    # Python SAST - Bandit
    if [ -f ".venv/bin/bandit" ]; then
        BANDIT_CMD=".venv/bin/bandit"
    elif command -v bandit &> /dev/null; then
        BANDIT_CMD="bandit"
    else
        BANDIT_CMD=""
    fi

    if [ -n "$BANDIT_CMD" ]; then
        if $BANDIT_CMD -r lambda/ -ll -q 2>/dev/null; then
            echo -e "${GREEN}  ✓ bandit (Python SAST)${NC}"
        else
            echo -e "${YELLOW}  ⚠ bandit: issues found (non-blocking)${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠ bandit not installed (pip install bandit)${NC}"
    fi
    
    # CloudFormation Security - cfn_nag
    # Use Ruby 3.3 for cfn_nag (Ruby 4.0 has compatibility issues)
    export PATH="/opt/homebrew/opt/ruby@3.3/bin:/opt/homebrew/lib/ruby/gems/3.3.0/bin:$PATH"
    if command -v cfn_nag_scan &> /dev/null; then
        if cfn_nag_scan --input-path cfn/ --deny-list-path .cfn_nag_deny_list.yml 2>/dev/null | grep -q "Failures count: 0"; then
            echo -e "${GREEN}  ✓ cfn_nag (IaC security)${NC}"
        else
            echo -e "${YELLOW}  ⚠ cfn_nag: issues found (non-blocking)${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠ cfn_nag not installed (gem install cfn-nag)${NC}"
    fi
    
    # Secrets Detection - detect-secrets
    if [ -f ".venv/bin/detect-secrets" ]; then
        # Use virtual environment version
        if .venv/bin/detect-secrets scan --baseline .secrets.baseline > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓ detect-secrets${NC}"
        else
            echo -e "${YELLOW}  ⚠ detect-secrets: potential secrets found (non-blocking)${NC}"
        fi
    elif command -v detect-secrets &> /dev/null; then
        # Fallback to system version
        if detect-secrets scan --baseline .secrets.baseline > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓ detect-secrets${NC}"
        else
            echo -e "${YELLOW}  ⚠ detect-secrets: potential secrets found (non-blocking)${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠ detect-secrets not installed (pip install detect-secrets)${NC}"
    fi
    
    # Shell Script Security - shellcheck (only production code, not utility scripts)
    if command -v shellcheck &> /dev/null; then
        # Only check shell scripts embedded in Lambda layers or CFN templates
        # Skip utility scripts in /scripts directory
        if [ -d "lambda" ] && find lambda/ -name "*.sh" 2>/dev/null | grep -q .; then
            if find lambda/ -name "*.sh" -exec shellcheck -S warning {} + 2>/dev/null; then
                echo -e "${GREEN}  ✓ shellcheck (Lambda scripts)${NC}"
            else
                echo -e "${YELLOW}  ⚠ shellcheck: issues in Lambda scripts (non-blocking)${NC}"
            fi
        else
            echo -e "${GREEN}  ✓ shellcheck (no Lambda scripts found)${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠ shellcheck not installed (brew install shellcheck)${NC}"
    fi
    
    # Frontend Dependencies - npm audit
    if [ -d "frontend" ]; then
        cd frontend
        if npm audit --audit-level=critical 2>/dev/null | grep -q "found 0 vulnerabilities"; then
            echo -e "${GREEN}  ✓ npm audit (dependencies)${NC}"
        else
            echo -e "${YELLOW}  ⚠ npm audit: vulnerabilities (non-blocking)${NC}"
        fi
        cd ..
    fi
    echo ""
else
    echo -e "${YELLOW}[2/5] Security: SKIPPED${NC}"
    echo ""
fi

# Stage 3: Tests (unless skipped)
if [ "$SKIP_TESTS" = false ]; then
    echo -e "${BLUE}[3/5] Tests${NC}"
    
    # Python tests
    if [ -d "tests" ]; then
        # Use pytest from virtual environment
        if [ -f ".venv/bin/pytest" ]; then
            PYTEST_CMD=".venv/bin/pytest"
        elif command -v pytest &> /dev/null; then
            PYTEST_CMD="pytest"
        else
            PYTEST_CMD="python3 -m pytest"
        fi
        
        # Run test directories separately to avoid namespace conflicts
        TEST_FAILED=false
        
        if ! $PYTEST_CMD tests/python/unit/ -q --tb=no 2>/dev/null; then
            TEST_FAILED=true
        fi
        
        if ! $PYTEST_CMD tests/unit/ -q --tb=no 2>/dev/null; then
            TEST_FAILED=true
        fi
        
        if ! $PYTEST_CMD tests/integration/ -q --tb=no 2>/dev/null; then
            TEST_FAILED=true
        fi
        
        if [ "$TEST_FAILED" = true ]; then
            echo -e "${RED}  ✗ pytest: failures${NC}"
            FAILED=true
        else
            echo -e "${GREEN}  ✓ pytest${NC}"
        fi
    fi
    
    # Frontend tests
    if [ -d "frontend" ]; then
        cd frontend
        if npm run test --silent -- --run 2>/dev/null; then
            echo -e "${GREEN}  ✓ vitest${NC}"
        else
            echo -e "${RED}  ✗ vitest: failures${NC}"
            FAILED=true
        fi
        cd ..
    fi
    echo ""
else
    echo -e "${YELLOW}[3/5] Tests: SKIPPED${NC}"
    echo ""
fi

# Check for failures
if [ "$FAILED" = true ]; then
    echo -e "${RED}❌ Validation failed - fix issues before deploying${NC}"
    exit 1
fi

# Exit early if validate-only mode
if [ "$VALIDATE_ONLY" = true ]; then
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✓ Validation Complete (No Deployment)${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "All validation checks passed!"
    echo "To deploy, run without --validate-only flag"
    exit 0
fi

# Stage 4: Git push (unless skipped)
if [ "$SKIP_PUSH" = false ]; then
    echo -e "${BLUE}[4/5] Git Push${NC}"
    
    if git diff --quiet && git diff --cached --quiet; then
        echo -e "${YELLOW}  ⚠ No changes to commit${NC}"
    else
        echo -e "${YELLOW}  ⚠ Uncommitted changes - commit first${NC}"
    fi
    
    if git push origin HEAD --quiet 2>/dev/null; then
        echo -e "${GREEN}  ✓ Pushed to remote${NC}"
    else
        echo -e "${YELLOW}  ⚠ Push failed or nothing to push${NC}"
    fi
    echo ""
else
    echo -e "${YELLOW}[4/5] Git Push: SKIPPED${NC}"
    echo ""
fi

# Stage 5: Deploy
echo -e "${BLUE}[5/5] Deploy${NC}"

# Build Lambda packages
if [ "$FRONTEND_ONLY" = false ]; then
    echo "  Building Lambda packages..."
    python3 package_lambda.py > /dev/null 2>&1
    echo -e "${GREEN}  ✓ Lambda packages built${NC}"
    
    # Sync to S3
    aws s3 sync cfn/ "s3://${DEPLOYMENT_BUCKET}/cfn/" --delete --quiet
    aws s3 sync build/lambda/ "s3://${DEPLOYMENT_BUCKET}/lambda/" --delete --quiet
    echo -e "${GREEN}  ✓ Artifacts synced to S3${NC}"
fi

# Deploy based on type
if [ "$LAMBDA_ONLY" = true ]; then
    echo "  Updating Lambda functions..."
    # Active Lambda functions:
    # - data-management-handler: Protection Groups & Recovery Plans CRUD
    # - execution-handler: DR execution lifecycle
    # - query-handler: Read-only infrastructure queries
    # - frontend-deployer: Frontend deployment automation
    # - orch-sf: Step Functions orchestration (S3 key: orchestration-stepfunctions)
    # - notification-formatter: SNS notification formatting
    # Note: deployment-orchestrator uses inline ZipFile code, not S3
    FUNCTIONS="data-management-handler execution-handler query-handler frontend-deployer orch-sf:orchestration-stepfunctions notification-formatter"
    for entry in $FUNCTIONS; do
        if [[ "$entry" == *":"* ]]; then
            func="${entry%%:*}"
            s3key="${entry##*:}"
        else
            func="$entry"
            s3key="$entry"
        fi
        FUNCTION_NAME="${PROJECT_NAME}-${func}-${ENVIRONMENT}"
        if aws lambda get-function --function-name "$FUNCTION_NAME" > /dev/null 2>&1; then
            aws lambda update-function-code \
                --function-name "$FUNCTION_NAME" \
                --s3-bucket "$DEPLOYMENT_BUCKET" \
                --s3-key "lambda/${s3key}.zip" \
                --output json > /dev/null
            echo -e "${GREEN}    ✓ Updated: $FUNCTION_NAME${NC}"
        fi
    done
    echo -e "${GREEN}  ✓ Lambda functions updated${NC}"

elif [ "$FRONTEND_ONLY" = true ]; then
    # Build frontend
    echo "  Building frontend..."
    (cd frontend && npm run build > /dev/null 2>&1)
    echo -e "${GREEN}  ✓ Frontend built${NC}"
    
    # Package frontend-deployer Lambda with new dist
    echo "  Packaging frontend-deployer Lambda..."
    python3 package_lambda.py > /dev/null 2>&1
    echo -e "${GREEN}  ✓ Lambda packaged${NC}"
    
    # Sync artifacts to S3
    echo "  Syncing artifacts to S3..."
    aws s3 sync cfn/ "s3://${DEPLOYMENT_BUCKET}/cfn/" --delete --quiet
    aws s3 cp build/lambda/frontend-deployer.zip "s3://${DEPLOYMENT_BUCKET}/lambda/frontend-deployer.zip" --quiet
    echo -e "${GREEN}  ✓ Artifacts synced${NC}"
    
    # Update Lambda function code
    echo "  Updating frontend-deployer Lambda..."
    aws lambda update-function-code \
        --function-name "${PROJECT_NAME}-frontend-deployer-${ENVIRONMENT}" \
        --s3-bucket "$DEPLOYMENT_BUCKET" \
        --s3-key "lambda/frontend-deployer.zip" \
        --output json > /dev/null
    echo -e "${GREEN}  ✓ Lambda updated${NC}"
    
    # Generate new frontend version to trigger rebuild
    FRONTEND_VERSION=$(generate_frontend_version)
    echo "  Triggering frontend rebuild (version: $FRONTEND_VERSION)..."
    
    # Force CloudFormation update to trigger frontend-deployer Lambda
    # Note: Removed --no-fail-on-empty-changeset to ensure FrontendBuildVersion change triggers deployment
    aws cloudformation deploy \
        --template-file cfn/master-template.yaml \
        --stack-name "$STACK_NAME" \
        --parameter-overrides \
            ProjectName="$PROJECT_NAME" \
            Environment="$ENVIRONMENT" \
            SourceBucket="$DEPLOYMENT_BUCKET" \
            AdminEmail="$ADMIN_EMAIL" \
            CrossAccountRoleName="$CROSS_ACCOUNT_ROLE_NAME" \
            EnableNotifications="$ENABLE_NOTIFICATIONS" \
            DeployFrontend="$DEPLOY_FRONTEND" \
            OrchestrationRoleArn="$ORCHESTRATION_ROLE_ARN" \
            FrontendBuildVersion="$FRONTEND_VERSION" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$AWS_REGION" > /dev/null 2>&1
    echo -e "${GREEN}  ✓ Frontend rebuild triggered (version: $FRONTEND_VERSION)${NC}"

else
    echo "  Deploying CloudFormation stack..."
    # Parameters cleaned up per frontend-deployment-hardening spec
    # Removed: NotificationEmail, CognitoDomainPrefix, EnableTagSync, TagSyncIntervalHours,
    #          ApiDeploymentTimestamp, FrontendBuildTimestamp, ForceRecreation
    # These are either hardcoded internally or generated by deploy.sh
    aws cloudformation deploy \
        --template-file cfn/master-template.yaml \
        --stack-name "$STACK_NAME" \
        --parameter-overrides \
            ProjectName="$PROJECT_NAME" \
            Environment="$ENVIRONMENT" \
            SourceBucket="$DEPLOYMENT_BUCKET" \
            AdminEmail="$ADMIN_EMAIL" \
            CrossAccountRoleName="$CROSS_ACCOUNT_ROLE_NAME" \
            EnableNotifications="$ENABLE_NOTIFICATIONS" \
            DeployFrontend="$DEPLOY_FRONTEND" \
            OrchestrationRoleArn="$ORCHESTRATION_ROLE_ARN" \
        --capabilities CAPABILITY_NAMED_IAM \
        --no-fail-on-empty-changeset \
        --region "$AWS_REGION"
    echo -e "${GREEN}  ✓ Stack deployed${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Deployment complete${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"

# Show URLs
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
    --output text 2>/dev/null || echo "N/A")
echo ""
echo "Application: $CLOUDFRONT_URL"
