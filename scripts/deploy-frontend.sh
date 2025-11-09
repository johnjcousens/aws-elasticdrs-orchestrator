#!/bin/bash

################################################################################
# AWS DRS Orchestration - Frontend Deployment Script
################################################################################
# This script automates the deployment of the React frontend to S3 and CloudFront
# 
# Usage:
#   ./scripts/deploy-frontend.sh [STACK_NAME] [ENVIRONMENT]
#
# Parameters:
#   STACK_NAME   - CloudFormation stack name (default: DRS-Orchestration)
#   ENVIRONMENT  - Deployment environment: dev, staging, or prod (default: prod)
#
# Examples:
#   ./scripts/deploy-frontend.sh                        # Deploy to DRS-Orchestration stack (prod)
#   ./scripts/deploy-frontend.sh MyStack dev           # Deploy to MyStack (dev mode)
#   ./scripts/deploy-frontend.sh DRS-Orchestration-Test staging
#
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="${1:-DRS-Orchestration}"
ENVIRONMENT="${2:-prod}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BUILD_DIR="$FRONTEND_DIR/dist"

################################################################################
# Helper Functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        log_info "Installation: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi
    
    # Check Node.js and npm
    if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
        log_error "Node.js and npm are required. Please install them first."
        log_info "Installation: https://nodejs.org/"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials are not configured or expired."
        log_info "Please run: aws configure"
        log_info "Or for Amazon employees: ada credentials update --account=YOUR_ACCOUNT --role=YOUR_ROLE"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

get_stack_outputs() {
    log_info "Fetching CloudFormation stack outputs for: $STACK_NAME"
    
    # Check if stack exists
    if ! aws cloudformation describe-stacks --stack-name "$STACK_NAME" &> /dev/null; then
        log_error "CloudFormation stack '$STACK_NAME' not found"
        log_info "Available stacks:"
        aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query 'StackSummaries[].StackName' --output table
        exit 1
    fi
    
    # Get all outputs as JSON
    OUTPUTS=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs' \
        --output json)
    
    if [ -z "$OUTPUTS" ] || [ "$OUTPUTS" = "null" ]; then
        log_error "No outputs found for stack: $STACK_NAME"
        exit 1
    fi
    
    # Extract specific values
    export S3_BUCKET=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="WebsiteBucket") | .OutputValue')
    export CLOUDFRONT_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="CloudFrontDistributionId") | .OutputValue')
    export CLOUDFRONT_URL=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="CloudFrontUrl") | .OutputValue')
    export API_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="ApiEndpoint") | .OutputValue')
    export USER_POOL_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="UserPoolId") | .OutputValue')
    export USER_POOL_CLIENT_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="UserPoolClientId") | .OutputValue')
    export IDENTITY_POOL_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="IdentityPoolId") | .OutputValue')
    export AWS_REGION=$(aws configure get region || echo "us-west-2")
    
    # Validate required outputs
    if [ -z "$S3_BUCKET" ] || [ "$S3_BUCKET" = "null" ]; then
        log_error "WebsiteBucket output not found in stack"
        exit 1
    fi
    
    if [ -z "$CLOUDFRONT_ID" ] || [ "$CLOUDFRONT_ID" = "null" ]; then
        log_error "CloudFrontDistributionId output not found in stack"
        exit 1
    fi
    
    log_success "Retrieved stack outputs:"
    log_info "  S3 Bucket: $S3_BUCKET"
    log_info "  CloudFront ID: $CLOUDFRONT_ID"
    log_info "  CloudFront URL: $CLOUDFRONT_URL"
    log_info "  API Endpoint: $API_ENDPOINT"
    log_info "  User Pool ID: $USER_POOL_ID"
    log_info "  Region: $AWS_REGION"
}

inject_config() {
    log_info "Injecting AWS configuration for environment: $ENVIRONMENT"
    
    # Run Node.js config injection script
    node "$SCRIPT_DIR/inject-config.js" \
        --region "$AWS_REGION" \
        --user-pool-id "$USER_POOL_ID" \
        --user-pool-client-id "$USER_POOL_CLIENT_ID" \
        --identity-pool-id "$IDENTITY_POOL_ID" \
        --api-endpoint "$API_ENDPOINT" \
        --environment "$ENVIRONMENT"
    
    if [ $? -ne 0 ]; then
        log_error "Failed to inject configuration"
        exit 1
    fi
    
    log_success "Configuration injected successfully"
}

build_frontend() {
    log_info "Building React frontend for $ENVIRONMENT environment..."
    
    cd "$FRONTEND_DIR"
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        log_info "Installing npm dependencies..."
        npm install
    fi
    
    # Run TypeScript compilation check
    log_info "Running TypeScript compilation check..."
    npx tsc --noEmit
    
    if [ $? -ne 0 ]; then
        log_error "TypeScript compilation failed. Please fix errors before deploying."
        exit 1
    fi
    
    # Build for production
    log_info "Building production bundle..."
    npm run build
    
    if [ $? -ne 0 ]; then
        log_error "Build failed"
        exit 1
    fi
    
    # Check if build directory exists
    if [ ! -d "$BUILD_DIR" ]; then
        log_error "Build directory not found: $BUILD_DIR"
        exit 1
    fi
    
    # Display build size
    BUILD_SIZE=$(du -sh "$BUILD_DIR" | cut -f1)
    log_success "Build completed successfully (Size: $BUILD_SIZE)"
    
    cd "$PROJECT_ROOT"
}

sync_to_s3() {
    log_info "Syncing build files to S3: s3://$S3_BUCKET"
    
    # Sync with appropriate cache headers and content types
    aws s3 sync "$BUILD_DIR" "s3://$S3_BUCKET" \
        --delete \
        --cache-control "public, max-age=31536000, immutable" \
        --exclude "index.html" \
        --exclude "*.map"
    
    # Upload index.html with no-cache to ensure users get latest version
    aws s3 cp "$BUILD_DIR/index.html" "s3://$S3_BUCKET/index.html" \
        --cache-control "no-cache, no-store, must-revalidate" \
        --content-type "text/html"
    
    # Upload source maps separately if they exist (for debugging)
    if ls "$BUILD_DIR"/*.map 1> /dev/null 2>&1; then
        log_info "Uploading source maps..."
        aws s3 sync "$BUILD_DIR" "s3://$S3_BUCKET" \
            --exclude "*" \
            --include "*.map" \
            --cache-control "private, max-age=0"
    fi
    
    if [ $? -ne 0 ]; then
        log_error "Failed to sync files to S3"
        exit 1
    fi
    
    log_success "Files synced to S3 successfully"
}

invalidate_cloudfront() {
    log_info "Creating CloudFront invalidation..."
    
    # Create invalidation for all files
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_ID" \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text)
    
    if [ $? -ne 0 ]; then
        log_error "Failed to create CloudFront invalidation"
        exit 1
    fi
    
    log_success "CloudFront invalidation created: $INVALIDATION_ID"
    log_info "Invalidation typically takes 30-60 seconds to complete"
    log_info "You can check status with: aws cloudfront get-invalidation --distribution-id $CLOUDFRONT_ID --id $INVALIDATION_ID"
}

display_summary() {
    echo ""
    echo "======================================================================="
    log_success "🚀 Deployment Complete!"
    echo "======================================================================="
    echo ""
    log_info "Environment: $ENVIRONMENT"
    log_info "Stack: $STACK_NAME"
    echo ""
    log_info "Frontend URL: $CLOUDFRONT_URL"
    log_info "API Endpoint: $API_ENDPOINT"
    echo ""
    log_info "CloudFront Distribution: $CLOUDFRONT_ID"
    log_info "S3 Bucket: $S3_BUCKET"
    echo ""
    log_warning "Note: CloudFront cache invalidation may take 30-60 seconds"
    log_info "Test your deployment at: $CLOUDFRONT_URL"
    echo ""
    echo "======================================================================="
}

################################################################################
# Main Execution
################################################################################

main() {
    echo ""
    echo "======================================================================="
    echo "  AWS DRS Orchestration - Frontend Deployment"
    echo "======================================================================="
    echo ""
    
    log_info "Starting deployment..."
    log_info "Stack: $STACK_NAME"
    log_info "Environment: $ENVIRONMENT"
    echo ""
    
    # Execute deployment steps
    check_prerequisites
    get_stack_outputs
    inject_config
    build_frontend
    sync_to_s3
    invalidate_cloudfront
    display_summary
    
    log_success "Deployment completed successfully!"
    exit 0
}

# Run main function
main
