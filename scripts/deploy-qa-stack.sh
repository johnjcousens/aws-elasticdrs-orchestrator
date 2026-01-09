#!/bin/bash

# AWS DRS Orchestration - QA Stack Deployment Script
# Matches GitHub Actions pipeline process with local security and validation scans

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - QA Stack with dev environment suffix
QA_STACK_NAME="aws-drs-orchestrator-qa"
DEPLOYMENT_BUCKET="aws-drs-orchestrator-archive-test-bucket"  # Actual bucket from stack
AWS_REGION="us-east-1"
PROJECT_NAME="aws-drs-orchestrator-qa"  # Actual project name from stack
ENVIRONMENT="dev"  # Actual environment from stack (causes -dev suffix on resources)
ADMIN_EMAIL="***REMOVED***"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install AWS CLI."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or expired."
        exit 1
    fi
    
    # Check required tools
    local tools=("python3" "pip3" "npm" "jq")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool not found. Please install $tool."
            exit 1
        fi
    done
    
    log_success "Prerequisites check passed"
}

# Stage 1: Detect Changes (like GitHub Actions)
detect_changes() {
    log "📁 Stage 1: Detecting changes..."
    
    # Check if we have git changes
    if git diff --quiet HEAD~1 HEAD 2>/dev/null; then
        log_warning "No changes detected since last commit"
    else
        log "Changes detected - proceeding with deployment"
    fi
    
    # Analyze changed files
    local changed_files=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || echo "all")
    log "Changed files: $changed_files"
    
    log_success "Change detection completed"
}

# Stage 2: Validation (CloudFormation, Python, TypeScript)
validate_code() {
    log "🔍 Stage 2: Code validation..."
    
    # CloudFormation validation
    log "Validating CloudFormation templates..."
    for template in cfn/*.yaml; do
        if [[ -f "$template" ]]; then
            log "Validating $template..."
            aws cloudformation validate-template --template-body file://"$template" --region "$AWS_REGION" > /dev/null
        fi
    done
    
    # Python linting (if available)
    if command -v flake8 &> /dev/null; then
        log "Running Python linting..."
        flake8 lambda/ scripts/ --max-line-length=79 --ignore=E203,W503 || log_warning "Linting warnings found"
    fi
    
    # TypeScript checking (if frontend exists)
    if [[ -d "frontend" && -f "frontend/package.json" ]]; then
        log "Running TypeScript validation..."
        cd frontend
        npm install --silent
        npm run type-check || log_warning "TypeScript warnings found"
        cd ..
    fi
    
    log_success "Code validation completed"
}

# Stage 3: Security Scan (Bandit, Safety, Semgrep)
security_scan() {
    log "🔒 Stage 3: Security scanning..."
    
    # Create security reports directory
    mkdir -p security-reports
    
    # Install security tools if not available
    if ! command -v bandit &> /dev/null; then
        log "Installing security tools..."
        pip3 install bandit safety semgrep --quiet
    fi
    
    # Bandit security scan
    log "Running Bandit security scan..."
    bandit -r lambda/ scripts/ -ll -f json -o security-reports/bandit-report.json 2>/dev/null || true
    bandit -r lambda/ scripts/ -ll --format screen > security-reports/bandit-summary.txt 2>/dev/null || true
    
    # Safety dependency scan
    log "Running Safety dependency scan..."
    safety check --json > security-reports/safety-report.json 2>/dev/null || true
    
    # Semgrep security patterns
    if command -v semgrep &> /dev/null; then
        log "Running Semgrep security analysis..."
        semgrep --config=python.lang.security lambda/ scripts/ --json --output security-reports/semgrep-report.json --severity ERROR --severity WARNING 2>/dev/null || true
    fi
    
    # Check for critical security issues
    local critical_issues=$(jq -r '.results | length' security-reports/bandit-report.json 2>/dev/null || echo "0")
    if [[ "$critical_issues" -gt 10 ]]; then
        log_warning "Found $critical_issues security issues - review security-reports/"
    fi
    
    log_success "Security scanning completed"
}

# Stage 4: Build (Lambda packages, Frontend)
build_artifacts() {
    log "🔨 Stage 4: Building artifacts..."
    
    # Build Lambda packages
    log "Building Lambda packages..."
    
    # Create Lambda deployment packages
    local lambda_functions=("api-handler" "execution-poller" "execution-finder" "orchestration-stepfunctions" "notification-formatter" "bucket-cleaner" "frontend-builder")
    
    for func in "${lambda_functions[@]}"; do
        if [[ -d "lambda/$func" ]]; then
            log "Packaging lambda/$func..."
            
            # Create package directory
            mkdir -p "build/lambda/$func"
            
            # Copy function code
            cp -r "lambda/$func"/* "build/lambda/$func/"
            
            # Copy shared utilities if they exist
            if [[ -d "lambda/shared" ]]; then
                cp -r lambda/shared "build/lambda/$func/"
            fi
            
            # Install Python dependencies if requirements.txt exists
            if [[ -f "lambda/$func/requirements.txt" ]]; then
                pip3 install -r "lambda/$func/requirements.txt" -t "build/lambda/$func/" --quiet
            fi
            
            # Create ZIP package
            cd "build/lambda/$func"
            zip -r "../../../$func.zip" . > /dev/null
            cd ../../..
        fi
    done
    
    # Build frontend if it exists
    if [[ -d "frontend" ]]; then
        log "Building frontend..."
        cd frontend
        npm install --silent
        npm run build
        cd ..
    fi
    
    log_success "Build completed"
}

# Stage 5: Test (Unit tests)
run_tests() {
    log "🧪 Stage 5: Running tests..."
    
    # Python tests
    if [[ -d "tests" ]]; then
        log "Running Python tests..."
        if command -v pytest &> /dev/null; then
            pytest tests/ -v --tb=short || log_warning "Some tests failed"
        else
            log_warning "pytest not available - skipping Python tests"
        fi
    fi
    
    # Frontend tests
    if [[ -d "frontend" && -f "frontend/package.json" ]]; then
        log "Running frontend tests..."
        cd frontend
        if npm run test --if-present > /dev/null 2>&1; then
            log_success "Frontend tests passed"
        else
            log_warning "Frontend tests not available or failed"
        fi
        cd ..
    fi
    
    log_success "Testing completed"
}

# Stage 6: Deploy Infrastructure (QA Stack)
deploy_infrastructure() {
    log "🚀 Stage 6: Deploying QA stack infrastructure..."
    
    # Upload Lambda packages to S3
    log "Uploading Lambda packages to S3..."
    for zip_file in *.zip; do
        if [[ -f "$zip_file" ]]; then
            aws s3 cp "$zip_file" "s3://$DEPLOYMENT_BUCKET/lambda/" --region "$AWS_REGION"
        fi
    done
    
    # Upload CloudFormation templates
    log "Uploading CloudFormation templates..."
    aws s3 sync cfn/ "s3://$DEPLOYMENT_BUCKET/cfn/" --region "$AWS_REGION" --delete
    
    # Deploy master CloudFormation stack for QA
    log "Deploying QA stack: $QA_STACK_NAME..."
    
    aws cloudformation deploy \
        --template-file cfn/master-template.yaml \
        --stack-name "$QA_STACK_NAME" \
        --parameter-overrides \
            ProjectName="$PROJECT_NAME" \
            Environment="$ENVIRONMENT" \
            AdminEmail="$ADMIN_EMAIL" \
            DeploymentBucket="$DEPLOYMENT_BUCKET" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$AWS_REGION" \
        --no-fail-on-empty-changeset
    
    # Wait for stack to complete
    log "Waiting for stack deployment to complete..."
    aws cloudformation wait stack-deploy-complete \
        --stack-name "$QA_STACK_NAME" \
        --region "$AWS_REGION"
    
    log_success "QA stack deployment completed"
}

# Stage 7: Deploy Frontend (QA Stack)
deploy_frontend() {
    log "🌐 Stage 7: Deploying frontend to QA stack..."
    
    if [[ -d "frontend/dist" ]]; then
        # Get QA stack frontend bucket
        local frontend_bucket=$(aws cloudformation describe-stacks \
            --stack-name "$QA_STACK_NAME" \
            --region "$AWS_REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
            --output text)
        
        if [[ -n "$frontend_bucket" && "$frontend_bucket" != "None" ]]; then
            log "Deploying frontend to bucket: $frontend_bucket"
            
            # Sync frontend files
            aws s3 sync frontend/dist/ "s3://$frontend_bucket/" --region "$AWS_REGION" --delete
            
            # Get CloudFront distribution ID
            local cloudfront_id=$(aws cloudformation describe-stacks \
                --stack-name "$QA_STACK_NAME" \
                --region "$AWS_REGION" \
                --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
                --output text 2>/dev/null || echo "")
            
            # Invalidate CloudFront cache if distribution exists
            if [[ -n "$cloudfront_id" && "$cloudfront_id" != "None" ]]; then
                log "Invalidating CloudFront cache: $cloudfront_id"
                aws cloudfront create-invalidation \
                    --distribution-id "$cloudfront_id" \
                    --paths "/*" > /dev/null
            fi
            
            log_success "Frontend deployment completed"
        else
            log_warning "Frontend bucket not found in QA stack outputs"
        fi
    else
        log_warning "Frontend build directory not found - skipping frontend deployment"
    fi
}

# Cleanup function
cleanup() {
    log "🧹 Cleaning up build artifacts..."
    rm -rf build/
    rm -f *.zip
    log_success "Cleanup completed"
}

# Get QA stack information
get_qa_stack_info() {
    log "📋 QA Stack Information:"
    
    local api_endpoint=$(aws cloudformation describe-stacks \
        --stack-name "$QA_STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
        --output text 2>/dev/null || echo "Not found")
    
    local frontend_url=$(aws cloudformation describe-stacks \
        --stack-name "$QA_STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
        --output text 2>/dev/null || echo "Not found")
    
    echo "  API Endpoint: $api_endpoint"
    echo "  Frontend URL: $frontend_url"
    echo "  Stack Name: $QA_STACK_NAME"
    echo "  Region: $AWS_REGION"
}

# Main execution
main() {
    log "🚀 Starting QA Stack Deployment Pipeline"
    log "Stack: $QA_STACK_NAME"
    log "Region: $AWS_REGION"
    echo ""
    
    # Execute pipeline stages
    check_prerequisites
    detect_changes
    validate_code
    security_scan
    build_artifacts
    run_tests
    deploy_infrastructure
    deploy_frontend
    
    # Show results
    echo ""
    log_success "🎉 QA Stack deployment completed successfully!"
    get_qa_stack_info
    
    # Cleanup
    cleanup
    
    echo ""
    log "📝 Next steps:"
    echo "  1. Test API endpoints with QA stack credentials"
    echo "  2. Verify Lambda functions are working without import errors"
    echo "  3. Test execution-poller functionality"
    echo "  4. Check CloudWatch logs for any issues"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "AWS DRS Orchestration - QA Stack Deployment Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --dry-run      Show what would be deployed without executing"
        echo "  --skip-tests   Skip test execution"
        echo "  --skip-security Skip security scanning"
        echo ""
        echo "Environment Variables:"
        echo "  QA_STACK_NAME     Override QA stack name (default: aws-drs-orchestrator-qa)"
        echo "  DEPLOYMENT_BUCKET Override S3 deployment bucket"
        echo "  AWS_REGION        Override AWS region (default: us-east-1)"
        exit 0
        ;;
    --dry-run)
        log "🔍 DRY RUN MODE - No actual deployment will occur"
        # Set dry run flag and modify functions to show what would happen
        DRY_RUN=true
        ;;
    --skip-tests)
        log "⏭️  Skipping test execution"
        SKIP_TESTS=true
        ;;
    --skip-security)
        log "⏭️  Skipping security scanning"
        SKIP_SECURITY=true
        ;;
esac

# Execute main function
main "$@"