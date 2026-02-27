#!/bin/bash
#
# Main Stack Deployment Script (New Architecture)
# Usage: ./scripts/deploy-main-stack.sh [environment] [options]
#
# This script deploys the new main-stack.yaml architecture with nested stacks.
# The existing deploy.sh continues to work with master-template.yaml.
#
# Environment Variables (all optional):
#   PROJECT_NAME              - Project name (default: aws-drs-orchestration)
#   STACK_NAME                - CloudFormation stack name (default: ${PROJECT_NAME}-${ENVIRONMENT})
#   DEPLOYMENT_BUCKET         - S3 bucket for artifacts (default: ${PROJECT_NAME}-${AWS_ACCOUNT_ID}-${ENVIRONMENT})
#   ADMIN_EMAIL               - Admin email for Cognito (default: jocousen@amazon.com)
#   ENABLE_NOTIFICATIONS      - Enable email notifications (default: true)
#   USE_FUNCTION_SPECIFIC_ROLES - Use function-specific IAM roles (default: false)
#
# Examples:
#   ./scripts/deploy-main-stack.sh test                           # Full pipeline
#   ./scripts/deploy-main-stack.sh test --validate-only           # Validation only
#   ./scripts/deploy-main-stack.sh test --use-function-specific-roles  # Enable new IAM roles
#   ./scripts/deploy-main-stack.sh test --lambda-only             # Lambda update only
#   ./scripts/deploy-main-stack.sh test --frontend-only           # Frontend rebuild only
#
# Key Differences from deploy.sh:
#   - Uses main-stack.yaml instead of master-template.yaml
#   - Syncs nested stack templates to S3 before deployment
#   - Validates nested stack template URLs exist in S3
#   - Supports UseFunctionSpecificRoles parameter
#   - Creates deployment bucket with account ID for global uniqueness

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
ENVIRONMENT="${1:-test}"
AWS_REGION="${AWS_REGION:-us-east-2}"
PROJECT_NAME="${PROJECT_NAME:-aws-drs-orchestration}"
STACK_NAME="${STACK_NAME:-${PROJECT_NAME}-${ENVIRONMENT}}"

# Get AWS Account ID for unique bucket naming
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
if [ -n "$AWS_ACCOUNT_ID" ]; then
    DEPLOYMENT_BUCKET="${DEPLOYMENT_BUCKET:-${PROJECT_NAME}-${AWS_ACCOUNT_ID}-${ENVIRONMENT}}"
else
    DEPLOYMENT_BUCKET="${DEPLOYMENT_BUCKET:-${PROJECT_NAME}-${ENVIRONMENT}}"
fi

ADMIN_EMAIL="${ADMIN_EMAIL:-jocousen@amazon.com}"
ENABLE_NOTIFICATIONS="${ENABLE_NOTIFICATIONS:-true}"
USE_FUNCTION_SPECIFIC_ROLES="${USE_FUNCTION_SPECIFIC_ROLES:-false}"

# Parse options
LAMBDA_ONLY=false
FRONTEND_ONLY=false
FORCE=false
DEPLOY_FRONTEND="true"
ORCHESTRATION_ROLE_ARN=""
VALIDATE_ONLY=false
FULL_TESTS=false
SKIP_TESTS=false

shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --lambda-only) LAMBDA_ONLY=true ;;
        --frontend-only) FRONTEND_ONLY=true ;;
        --validate-only) VALIDATE_ONLY=true ;;
        --force) FORCE=true ;;
        --full-tests) FULL_TESTS=true ;;
        --skip-tests) SKIP_TESTS=true ;;
        --no-frontend) DEPLOY_FRONTEND="false" ;;
        --use-function-specific-roles) USE_FUNCTION_SPECIFIC_ROLES="true" ;;
        --orchestration-role)
            ORCHESTRATION_ROLE_ARN="$2"
            shift
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

# ============================================================================
# SCRIPT LOCK - PREVENT CONCURRENT EXECUTIONS
# ============================================================================

LOCK_FILE="/tmp/deploy-main-stack-${STACK_NAME}.lock"
LOCK_PID_FILE="/tmp/deploy-main-stack-${STACK_NAME}.pid"

cleanup_lock() {
    if [ -f "$LOCK_FILE" ]; then
        rm -f "$LOCK_FILE"
        rm -f "$LOCK_PID_FILE"
    fi
}

trap cleanup_lock EXIT INT TERM

if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_PID_FILE" 2>/dev/null || echo "")
    
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        echo -e "${RED}❌ Another deployment is already running (PID: $LOCK_PID)${NC}"
        echo -e "${YELLOW}   Lock file: $LOCK_FILE${NC}"
        exit 1
    else
        echo -e "${YELLOW}⚠ Removing stale lock file${NC}"
        rm -f "$LOCK_FILE" "$LOCK_PID_FILE"
    fi
fi

touch "$LOCK_FILE"
echo $$ > "$LOCK_PID_FILE"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Deploy Main Stack: $STACK_NAME${NC}"
echo -e "${BLUE}  Architecture: Nested Stacks (main-stack.yaml)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# ============================================================================
# ACTIVATE VIRTUAL ENVIRONMENTS
# ============================================================================

if [ -d ".venv" ]; then
    echo -e "${BLUE}Activating Python virtual environment...${NC}"
    source .venv/bin/activate
    echo -e "${GREEN}✓ Python venv activated${NC}"
else
    echo -e "${YELLOW}⚠ Python .venv not found - using system Python${NC}"
fi

if command -v rbenv &> /dev/null; then
    eval "$(rbenv init - bash 2>/dev/null || rbenv init - zsh 2>/dev/null || true)"
    if [ -f ".ruby-version" ]; then
        RUBY_VERSION=$(cat .ruby-version)
        echo -e "${BLUE}Using Ruby $RUBY_VERSION via rbenv${NC}"
        echo -e "${GREEN}✓ rbenv initialized${NC}"
    fi
else
    echo -e "${YELLOW}⚠ rbenv not found${NC}"
fi

echo ""

# Set AWS profile if not already set
if [ -z "$AWS_PROFILE" ]; then
    export AWS_PROFILE="AdministratorAccess-438465159935"
    echo -e "${BLUE}Using AWS profile: $AWS_PROFILE${NC}"
fi

# Verify AWS credentials
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>&1 || true)
if [[ "$ACCOUNT_ID" == *"SSO session"* ]] || [[ "$ACCOUNT_ID" == *"expired"* ]]; then
    echo -e "${YELLOW}⚠ SSO session expired - logging in...${NC}"
    aws sso login --profile ${AWS_PROFILE:-AdministratorAccess-438465159935}
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>&1 || true)
fi

if [[ ! "$ACCOUNT_ID" =~ ^[0-9]{12}$ ]]; then
    echo -e "${RED}❌ AWS credentials failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Authenticated to AWS account: $ACCOUNT_ID${NC}"

# Concurrency protection
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "DOES_NOT_EXIST")

if [[ "$STACK_STATUS" == *"IN_PROGRESS"* ]] || [[ "$STACK_STATUS" == *"CLEANUP"* ]]; then
    if [ "$FORCE" = true ]; then
        echo -e "${YELLOW}⚠ Stack status: $STACK_STATUS (forcing deployment)${NC}"
    else
        echo -e "${RED}❌ Stack is currently being updated (status: $STACK_STATUS)${NC}"
        exit 1
    fi
fi

FAILED=false

# ============================================================================
# STAGE 1: VALIDATION
# ============================================================================
echo -e "${BLUE}[1/5] Validation${NC}"

# cfn-lint
if [ -f ".venv/bin/cfn-lint" ]; then
    CFNLINT_CMD=".venv/bin/cfn-lint"
elif command -v cfn-lint &> /dev/null; then
    CFNLINT_CMD="cfn-lint"
else
    CFNLINT_CMD=""
fi

if [ -n "$CFNLINT_CMD" ]; then
    set +e
    CFNLINT_OUTPUT=$($CFNLINT_CMD cfn/*.yaml cfn/**/*.yaml 2>&1)
    CFNLINT_RC=$?
    set -e
    
    ERR_COUNT=$(echo "$CFNLINT_OUTPUT" | grep -c "^E[0-9]" || echo "0")
    
    if [ "$CFNLINT_RC" -eq 2 ] || [ "$CFNLINT_RC" -eq 6 ]; then
        echo -e "${RED}  ✗ cfn-lint: $ERR_COUNT errors${NC}"
        echo "$CFNLINT_OUTPUT" | grep "^E[0-9]" | head -5
        FAILED=true
    else
        echo -e "${GREEN}  ✓ cfn-lint${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ cfn-lint not installed${NC}"
fi

# flake8 - ZERO TOLERANCE for warnings
if [ -f ".venv/bin/flake8" ]; then
    FLAKE8_COUNT=$(.venv/bin/flake8 lambda/ --config .flake8 --count -q | tail -1)
    if [ -n "$FLAKE8_COUNT" ] && [ "$FLAKE8_COUNT" -gt 0 ]; then
        echo -e "${RED}  ✗ flake8: $FLAKE8_COUNT warnings (ZERO TOLERANCE)${NC}"
        .venv/bin/flake8 lambda/ --config .flake8 | head -10
        FAILED=true
    else
        echo -e "${GREEN}  ✓ flake8${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ flake8 not installed${NC}"
fi

# black - ZERO TOLERANCE for formatting issues
if [ -f ".venv/bin/black" ]; then
    if ! .venv/bin/black --check --quiet lambda/ 2>/dev/null; then
        echo -e "${RED}  ✗ black: needs formatting (ZERO TOLERANCE)${NC}"
        echo -e "${YELLOW}    Run: black lambda/${NC}"
        FAILED=true
    else
        echo -e "${GREEN}  ✓ black${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ black not installed${NC}"
fi

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

# ============================================================================
# STAGE 2: SECURITY
# ============================================================================
echo -e "${BLUE}[2/5] Security${NC}"

# Bandit - ZERO TOLERANCE for medium/high/critical issues
if [ -f ".venv/bin/bandit" ]; then
    BANDIT_OUTPUT=$(.venv/bin/bandit -r lambda/ -ll -q 2>&1 || true)
    if echo "$BANDIT_OUTPUT" | grep -q "Issue:"; then
        echo -e "${RED}  ✗ bandit: security issues found (ZERO TOLERANCE)${NC}"
        echo "$BANDIT_OUTPUT" | head -20
        FAILED=true
    else
        echo -e "${GREEN}  ✓ bandit${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ bandit not installed${NC}"
fi

# cfn_nag - ZERO TOLERANCE for failures
if command -v cfn_nag_scan &> /dev/null; then
    CFN_NAG_OUTPUT=$(cfn_nag_scan --input-path cfn/ --deny-list-path .cfn_nag_deny_list.yml 2>&1 || true)
    if echo "$CFN_NAG_OUTPUT" | grep -q "Failures count: 0"; then
        echo -e "${GREEN}  ✓ cfn_nag${NC}"
    else
        echo -e "${RED}  ✗ cfn_nag: security issues found (ZERO TOLERANCE)${NC}"
        echo "$CFN_NAG_OUTPUT" | grep -A 5 "Failures count:"
        FAILED=true
    fi
else
    echo -e "${YELLOW}  ⚠ cfn_nag not installed${NC}"
fi

# detect-secrets - ZERO TOLERANCE for new secrets
if [ -f ".venv/bin/detect-secrets" ]; then
    if .venv/bin/detect-secrets scan --baseline .secrets.baseline > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ detect-secrets${NC}"
    else
        echo -e "${RED}  ✗ detect-secrets: potential secrets found (ZERO TOLERANCE)${NC}"
        .venv/bin/detect-secrets scan --baseline .secrets.baseline 2>&1 | head -10
        FAILED=true
    fi
else
    echo -e "${YELLOW}  ⚠ detect-secrets not installed${NC}"
fi

# shellcheck - ZERO TOLERANCE for warnings
if command -v shellcheck &> /dev/null; then
    if [ -d "lambda" ] && find lambda/ -name "*.sh" 2>/dev/null | grep -q .; then
        SHELLCHECK_OUTPUT=$(find lambda/ -name "*.sh" -exec shellcheck -S warning {} + 2>&1 || true)
        if [ -n "$SHELLCHECK_OUTPUT" ]; then
            echo -e "${RED}  ✗ shellcheck: issues found (ZERO TOLERANCE)${NC}"
            echo "$SHELLCHECK_OUTPUT" | head -20
            FAILED=true
        else
            echo -e "${GREEN}  ✓ shellcheck${NC}"
        fi
    else
        echo -e "${GREEN}  ✓ shellcheck (no scripts)${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ shellcheck not installed${NC}"
fi

# npm audit - ZERO TOLERANCE for critical/high vulnerabilities
if [ -d "frontend" ]; then
    cd frontend
    AUDIT_JSON=$(npm audit --json 2>/dev/null || echo '{}')
    CRITICAL_COUNT=$(echo "$AUDIT_JSON" | jq -r '.metadata.vulnerabilities.critical // 0' 2>/dev/null || echo "0")
    HIGH_COUNT=$(echo "$AUDIT_JSON" | jq -r '.metadata.vulnerabilities.high // 0' 2>/dev/null || echo "0")
    
    if [ "$CRITICAL_COUNT" = "0" ] && [ "$HIGH_COUNT" = "0" ]; then
        echo -e "${GREEN}  ✓ npm audit${NC}"
    else
        echo -e "${RED}  ✗ npm audit: $CRITICAL_COUNT critical, $HIGH_COUNT high (ZERO TOLERANCE)${NC}"
        echo -e "${YELLOW}    Run: cd frontend && npm audit fix${NC}"
        npm audit --audit-level=high 2>&1 | head -30
        FAILED=true
    fi
    cd ..
else
    echo -e "${YELLOW}  ⚠ frontend directory not found${NC}"
fi

echo ""

# ============================================================================
# STAGE 3: TESTS
# ============================================================================
echo -e "${BLUE}[3/5] Tests${NC}"

if [ "$SKIP_TESTS" = true ]; then
    echo -e "${YELLOW}  ⚠ Tests skipped${NC}"
else
    if [ -f ".venv/bin/pytest" ]; then
        if [ "$VALIDATE_ONLY" = true ] || [ "$FULL_TESTS" = true ]; then
            echo "  Running full test suite..."
            set +e
            .venv/bin/pytest tests/unit/ -v --forked --hypothesis-show-statistics 2>&1 | tee /tmp/pytest_output.txt
            PYTEST_EXIT_CODE=$?
            set -e
            
            if [ $PYTEST_EXIT_CODE -ne 0 ]; then
                echo -e "${RED}  ✗ Unit tests failed${NC}"
                FAILED=true
            else
                echo -e "${GREEN}  ✓ Unit tests passed${NC}"
            fi
        else
            echo "  Running fast unit tests..."
            set +e
            .venv/bin/pytest tests/unit/ -m "not property" -v --tb=short 2>&1 | tee /tmp/pytest_output.txt
            PYTEST_EXIT_CODE=$?
            set -e
            
            if [ $PYTEST_EXIT_CODE -ne 0 ]; then
                echo -e "${RED}  ✗ Unit tests failed${NC}"
                FAILED=true
            else
                echo -e "${GREEN}  ✓ Unit tests passed${NC}"
            fi
        fi
    fi
    
    if [ -d "frontend" ]; then
        cd frontend
        if npm test -- --run --silent; then
            echo -e "${GREEN}  ✓ vitest${NC}"
        else
            echo -e "${RED}  ✗ vitest: tests failed${NC}"
            FAILED=true
        fi
        cd ..
    fi
fi

echo ""

if [ "$FAILED" = true ]; then
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ❌ VALIDATION FAILED - ZERO TOLERANCE POLICY${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}This is production code in a public repository.${NC}"
    echo -e "${YELLOW}All code must be solid without critical issues or warnings.${NC}"
    echo ""
    echo -e "${YELLOW}Fix the issues above and run again.${NC}"
    echo ""
    exit 1
fi

if [ "$VALIDATE_ONLY" = true ]; then
    echo -e "${GREEN}✓ Validation Complete${NC}"
    exit 0
fi

# ============================================================================
# STAGE 4: GIT PUSH
# ============================================================================
echo -e "${BLUE}[4/5] Git Push${NC}"

if git diff --quiet && git diff --cached --quiet; then
    echo -e "${YELLOW}  ⚠ No changes to commit${NC}"
else
    echo -e "${YELLOW}  ⚠ Uncommitted changes - commit first${NC}"
fi

if git push origin HEAD --quiet 2>/dev/null; then
    echo -e "${GREEN}  ✓ Pushed to origin${NC}"
else
    echo -e "${YELLOW}  ⚠ Push failed or nothing to push${NC}"
fi

echo ""

# ============================================================================
# STAGE 5: DEPLOY
# ============================================================================
echo -e "${BLUE}[5/5] Deploy${NC}"

# Build Lambda packages
if [ "$FRONTEND_ONLY" = false ]; then
    echo "  Building Lambda packages..."
    python3 package_lambda.py > /dev/null 2>&1
    echo -e "${GREEN}  ✓ Lambda packages built${NC}"
    
    # Create deployment bucket if it doesn't exist (with account ID for uniqueness)
    if ! aws s3api head-bucket --bucket "${DEPLOYMENT_BUCKET}" --region "$AWS_REGION" > /dev/null 2>&1; then
        echo "  Creating deployment bucket: ${DEPLOYMENT_BUCKET} in ${AWS_REGION}"
        
        RETRY_COUNT=0
        MAX_RETRIES=3
        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            if [ "$AWS_REGION" = "us-east-1" ]; then
                if aws s3api create-bucket --bucket "${DEPLOYMENT_BUCKET}" --region "$AWS_REGION" 2>/dev/null; then
                    break
                fi
            else
                if aws s3api create-bucket \
                    --bucket "${DEPLOYMENT_BUCKET}" \
                    --region "$AWS_REGION" \
                    --create-bucket-configuration LocationConstraint="$AWS_REGION" 2>/dev/null; then
                    break
                fi
            fi
            
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                echo "  Bucket creation conflict, retrying... (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
                sleep 5
            else
                echo -e "${RED}  ✗ Failed to create deployment bucket${NC}"
                exit 1
            fi
        done
        
        aws s3api wait bucket-exists --bucket "${DEPLOYMENT_BUCKET}" --region "$AWS_REGION"
        
        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket "${DEPLOYMENT_BUCKET}" \
            --versioning-configuration Status=Enabled \
            --region "$AWS_REGION"
        
        echo -e "${GREEN}  ✓ Deployment bucket created${NC}"
    fi

    
    # Sync nested stack templates to S3 (CRITICAL for nested stack architecture)
    echo "  Syncing nested stack templates to S3..."
    
    # Sync all service-specific nested stack directories
    aws s3 sync cfn/iam/ "s3://${DEPLOYMENT_BUCKET}/cfn/iam/" --delete --quiet --region "$AWS_REGION"
    aws s3 sync cfn/lambda/ "s3://${DEPLOYMENT_BUCKET}/cfn/lambda/" --delete --quiet --region "$AWS_REGION"
    aws s3 sync cfn/dynamodb/ "s3://${DEPLOYMENT_BUCKET}/cfn/dynamodb/" --delete --quiet --region "$AWS_REGION"
    aws s3 sync cfn/stepfunctions/ "s3://${DEPLOYMENT_BUCKET}/cfn/stepfunctions/" --delete --quiet --region "$AWS_REGION"
    aws s3 sync cfn/sns/ "s3://${DEPLOYMENT_BUCKET}/cfn/sns/" --delete --quiet --region "$AWS_REGION"
    aws s3 sync cfn/eventbridge/ "s3://${DEPLOYMENT_BUCKET}/cfn/eventbridge/" --delete --quiet --region "$AWS_REGION"
    aws s3 sync cfn/s3/ "s3://${DEPLOYMENT_BUCKET}/cfn/s3/" --delete --quiet --region "$AWS_REGION"
    aws s3 sync cfn/cloudfront/ "s3://${DEPLOYMENT_BUCKET}/cfn/cloudfront/" --delete --quiet --region "$AWS_REGION"
    aws s3 sync cfn/apigateway/ "s3://${DEPLOYMENT_BUCKET}/cfn/apigateway/" --delete --quiet --region "$AWS_REGION"
    aws s3 sync cfn/cognito/ "s3://${DEPLOYMENT_BUCKET}/cfn/cognito/" --delete --quiet --region "$AWS_REGION"
    aws s3 sync cfn/monitoring/ "s3://${DEPLOYMENT_BUCKET}/cfn/monitoring/" --delete --quiet --region "$AWS_REGION"
    aws s3 sync cfn/waf/ "s3://${DEPLOYMENT_BUCKET}/cfn/waf/" --delete --quiet --region "$AWS_REGION"
    
    # Sync main-stack.yaml to S3
    aws s3 cp cfn/main-stack.yaml "s3://${DEPLOYMENT_BUCKET}/cfn/main-stack.yaml" --quiet --region "$AWS_REGION"
    
    echo -e "${GREEN}  ✓ Nested stack templates synced${NC}"
    
    # Sync Lambda packages to S3
    echo "  Syncing Lambda packages to S3..."
    aws s3 sync build/lambda/ "s3://${DEPLOYMENT_BUCKET}/lambda/" --delete --quiet --region "$AWS_REGION"
    echo -e "${GREEN}  ✓ Lambda packages synced${NC}"
fi


# Validate nested stack templates exist in S3 before deployment
if [ "$FRONTEND_ONLY" = false ]; then
    echo "  Validating nested stack templates in S3..."
    
    NESTED_TEMPLATES=(
        "cfn/iam/roles-stack.yaml"
        "cfn/lambda/functions-stack.yaml"
        "cfn/dynamodb/tables-stack.yaml"
        "cfn/stepfunctions/statemachine-stack.yaml"
        "cfn/sns/topics-stack.yaml"
        "cfn/eventbridge/rules-stack.yaml"
        "cfn/s3/buckets-stack.yaml"
        "cfn/cloudfront/distribution-stack.yaml"
        "cfn/cognito/auth-stack.yaml"
        "cfn/monitoring/alarms-stack.yaml"
        "cfn/waf/webacl-stack.yaml"
    )
    
    VALIDATION_FAILED=false
    for template in "${NESTED_TEMPLATES[@]}"; do
        if ! aws s3api head-object --bucket "${DEPLOYMENT_BUCKET}" --key "$template" --region "$AWS_REGION" > /dev/null 2>&1; then
            echo -e "${RED}  ✗ Missing template: $template${NC}"
            VALIDATION_FAILED=true
        fi
    done
    
    if [ "$VALIDATION_FAILED" = true ]; then
        echo -e "${RED}❌ Nested stack template validation failed${NC}"
        echo -e "${YELLOW}   Ensure all nested stack templates are synced to S3${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}  ✓ All nested stack templates validated${NC}"
fi


# Deploy CloudFormation stack
if [ "$LAMBDA_ONLY" = true ]; then
    echo "  Lambda-only deployment not yet implemented for main-stack architecture"
    echo "  Use full deployment instead"
    exit 1
elif [ "$FRONTEND_ONLY" = true ]; then
    # Build frontend locally, package into deployer Lambda, upload, then trigger CFN
    echo "  Building frontend..."
    (cd frontend && npm run build > /dev/null 2>&1)
    echo -e "${GREEN}  ✓ Frontend built${NC}"

    # Package frontend-deployer Lambda with new dist
    echo "  Packaging frontend-deployer Lambda..."
    python3 package_lambda.py > /dev/null 2>&1
    echo -e "${GREEN}  ✓ Lambda packaged${NC}"

    # Sync artifacts to S3
    echo "  Syncing artifacts to S3..."
    aws s3 sync cfn/ "s3://${DEPLOYMENT_BUCKET}/cfn/" --delete --quiet --region "$AWS_REGION"
    aws s3 cp build/lambda/frontend-deployer.zip "s3://${DEPLOYMENT_BUCKET}/lambda/frontend-deployer.zip" --quiet --region "$AWS_REGION"
    echo -e "${GREEN}  ✓ Artifacts synced${NC}"

    # Update Lambda function code
    echo "  Updating frontend-deployer Lambda..."
    aws lambda update-function-code \
        --function-name "${PROJECT_NAME}-frontend-deployer-${ENVIRONMENT}" \
        --s3-bucket "$DEPLOYMENT_BUCKET" \
        --s3-key "lambda/frontend-deployer.zip" \
        --region "$AWS_REGION" \
        --output json > /dev/null
    echo -e "${GREEN}  ✓ Lambda updated${NC}"

    # Trigger frontend rebuild via CloudFormation parameter update
    FRONTEND_VERSION=$(date +"%Y%m%d-%H%M")
    echo "  Triggering frontend rebuild (version: $FRONTEND_VERSION)..."

    # Get current parameters from main stack to preserve them
    CURRENT_PARAMS=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Parameters' \
        --output json)
    
    # Extract current parameter values
    CURRENT_USE_FUNC_ROLES=$(echo "$CURRENT_PARAMS" | jq -r '.[] | select(.ParameterKey=="UseFunctionSpecificRoles") | .ParameterValue // "false"')
    
    # Update main stack with new FrontendBuildVersion parameter
    # Keep all other parameters the same to avoid unnecessary updates
    aws cloudformation deploy \
        --template-file cfn/main-stack.yaml \
        --stack-name "$STACK_NAME" \
        --s3-bucket "$DEPLOYMENT_BUCKET" \
        --s3-prefix cfn \
        --parameter-overrides \
            ProjectName="$PROJECT_NAME" \
            Environment="$ENVIRONMENT" \
            DeploymentBucket="$DEPLOYMENT_BUCKET" \
            AdminEmail="$ADMIN_EMAIL" \
            UseFunctionSpecificRoles="$CURRENT_USE_FUNC_ROLES" \
            FrontendBuildVersion="$FRONTEND_VERSION" \
        --capabilities CAPABILITY_NAMED_IAM \
        --no-fail-on-empty-changeset \
        --region "$AWS_REGION"
    
    echo -e "${GREEN}  ✓ Frontend rebuild triggered (version: $FRONTEND_VERSION)${NC}"
else
    echo "  Deploying CloudFormation stack (main-stack.yaml)..."
    
    # Generate versions
    FRONTEND_VERSION=$(date +"%Y%m%d-%H%M")
    
    # Deploy main stack with nested stacks
    aws cloudformation deploy \
        --template-file cfn/main-stack.yaml \
        --stack-name "$STACK_NAME" \
        --s3-bucket "$DEPLOYMENT_BUCKET" \
        --s3-prefix cfn \
        --parameter-overrides \
            ProjectName="$PROJECT_NAME" \
            Environment="$ENVIRONMENT" \
            DeploymentBucket="$DEPLOYMENT_BUCKET" \
            AdminEmail="$ADMIN_EMAIL" \
            UseFunctionSpecificRoles="$USE_FUNCTION_SPECIFIC_ROLES" \
            FrontendBuildVersion="$FRONTEND_VERSION" \
        --capabilities CAPABILITY_NAMED_IAM \
        --no-fail-on-empty-changeset \
        --region "$AWS_REGION"
    
    echo -e "${GREEN}  ✓ Stack deployed${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Deployment complete${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"

# Show stack outputs
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
    --output text 2>/dev/null || echo "N/A")
echo ""
echo "Application: $CLOUDFRONT_URL"
echo "Stack: $STACK_NAME"
echo "Region: $AWS_REGION"
echo "Function-Specific Roles: $USE_FUNCTION_SPECIFIC_ROLES"
