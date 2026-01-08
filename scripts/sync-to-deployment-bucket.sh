#!/bin/bash
# Sync repository to S3 for GitHub Actions deployment
# Purpose: Keep s3://aws-elasticdrs-orchestrator in sync with local git repo
# Usage: ./scripts/sync-to-deployment-bucket.sh [options]

set -e  # Exit on error

# Disable AWS CLI pager for all commands
export AWS_PAGER=""

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load configuration from environment files
if [ -f "$PROJECT_ROOT/.env.deployment" ]; then
    echo "📋 Loading configuration from .env.deployment"
    source "$PROJECT_ROOT/.env.deployment"
fi

if [ -f "$PROJECT_ROOT/.env.deployment.local" ]; then
    echo "📋 Loading local overrides from .env.deployment.local"
    source "$PROJECT_ROOT/.env.deployment.local"
fi

# Default configuration
BUCKET="${DEPLOYMENT_BUCKET:-aws-elasticdrs-orchestrator}"
REGION="${DEPLOYMENT_REGION:-us-east-1}"
BUILD_FRONTEND=false
DRY_RUN=false
CLEAN_ORPHANS=false
EMERGENCY_DEPLOY=false
UPDATE_LAMBDA_CODE=false
DEPLOY_FRONTEND=false
AWS_PROFILE="${AWS_PROFILE:-default}"
LIST_PROFILES=false

# CloudFormation stack configuration (aligned with deployed stack)
PROJECT_NAME="${PROJECT_NAME:-aws-drs-orchestrator}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
PARENT_STACK_NAME="${PARENT_STACK_NAME:-${PROJECT_NAME}-${ENVIRONMENT}}"

# Approved directories for sync
APPROVED_DIRS=("cfn" "docs" "frontend" "lambda" "scripts")

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --build-frontend)
            BUILD_FRONTEND=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --clean-orphans)
            CLEAN_ORPHANS=true
            shift
            ;;
        --emergency-deploy)
            EMERGENCY_DEPLOY=true
            echo "⚠️  WARNING: Emergency deployment mode - bypassing GitHub Actions"
            shift
            ;;
        --update-lambda-code)
            UPDATE_LAMBDA_CODE=true
            echo "⚠️  WARNING: --update-lambda-code bypasses GitHub Actions"
            shift
            ;;
        --deploy-frontend)
            DEPLOY_FRONTEND=true
            echo "⚠️  WARNING: --deploy-frontend bypasses GitHub Actions"
            shift
            ;;
        --list-profiles)
            LIST_PROFILES=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "🚀 RECOMMENDED WORKFLOW:"
            echo "  git add . && git commit -m 'changes' && git push  # Triggers GitHub Actions"
            echo "  $0                                                # Basic S3 sync only"
            echo ""
            echo "Options:"
            echo "  --profile PROFILE                  AWS credentials profile (default: ${AWS_PROFILE})"
            echo "  --build-frontend                   Build frontend before syncing"
            echo "  --dry-run                          Show what would be synced without making changes"
            echo "  --clean-orphans                    Remove orphaned directories from S3"
            echo "  --list-profiles                    List available AWS profiles and exit"
            echo "  --help                             Show this help message"
            echo ""
            echo "🚨 EMERGENCY OPTIONS (bypass GitHub Actions):"
            echo "  --emergency-deploy                 Emergency bypass for critical fixes"
            echo "  --update-lambda-code               Update Lambda code directly (legacy)"
            echo "  --deploy-frontend                  Deploy frontend directly (legacy)"
            echo ""
            echo "Examples:"
            echo "  # RECOMMENDED: GitHub Actions deployment"
            echo "  git push                           # Triggers GitHub Actions pipeline"
            echo "  $0                                 # Basic S3 sync (no deployment)"
            echo "  $0 --build-frontend                # Build frontend + sync"
            echo "  $0 --dry-run                       # Preview changes"
            echo ""
            echo "  # Emergency fixes only"
            echo "  $0 --emergency-deploy --update-lambda-code  # Critical production fix"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# List profiles if requested
if [ "$LIST_PROFILES" = true ]; then
    echo "Available AWS Profiles:"
    echo "======================="
    if [ -f ~/.aws/credentials ]; then
        grep '^\\[' ~/.aws/credentials | sed 's/\\[//g' | sed 's/\\]//g' | while read profile; do
            echo "  - $profile"
        done
    else
        echo "No AWS credentials file found at ~/.aws/credentials"
    fi
    echo ""
    echo "Current default: $AWS_PROFILE"
    exit 0
fi

# Auto-detect git commit for tagging
if git rev-parse --git-dir > /dev/null 2>&1; then
    GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    GIT_SHORT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
else
    GIT_COMMIT="unknown"
    GIT_SHORT="unknown"
fi
SYNC_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Build profile flag if specified
PROFILE_FLAG=""
if [ -n "$AWS_PROFILE" ]; then
    PROFILE_FLAG="--profile $AWS_PROFILE"
fi

# Build sync flags with metadata
SYNC_FLAGS="--region $REGION --metadata git-commit=$GIT_COMMIT,git-short=$GIT_SHORT,sync-time=$SYNC_TIME"
if [ "$DRY_RUN" = true ]; then
    SYNC_FLAGS="$SYNC_FLAGS --dryrun"
    echo "🔍 DRY RUN MODE - No changes will be made"
    echo ""
fi

echo "======================================"
echo "S3 Deployment Repository Sync"
echo "======================================"
echo "Bucket: s3://$BUCKET"
echo "Region: $REGION"
echo "Build Frontend: $BUILD_FRONTEND"
echo "Dry Run: $DRY_RUN"
echo "AWS Profile: $AWS_PROFILE"
echo "Git Commit: $GIT_SHORT ($GIT_COMMIT)"
echo "Sync Time: $SYNC_TIME"
echo ""

# Verify AWS credentials
echo "🔐 Verifying AWS credentials..."
if ! aws sts get-caller-identity $PROFILE_FLAG --region $REGION >/dev/null 2>&1; then
    echo "❌ ERROR: AWS credentials not configured or profile not found"
    echo ""
    echo "Current profile: $AWS_PROFILE"
    echo ""
    echo "Solutions:"
    echo "  1. Check ~/.aws/credentials file exists and contains [$AWS_PROFILE]"
    echo "  2. Use different profile: $0 --profile PROFILE_NAME"
    echo "  3. List available profiles: $0 --list-profiles"
    exit 1
fi

echo "✅ AWS credentials verified"
echo ""

# Build frontend if requested
if [ "$BUILD_FRONTEND" = true ]; then
    echo "🏗️  Building frontend..."
    
    # Update frontend configuration from CloudFormation stack
    echo "📝 Updating frontend configuration from CloudFormation stack..."
    if ./scripts/update-frontend-config.sh "$PARENT_STACK_NAME" "$REGION"; then
        echo "✅ Frontend configuration updated from stack outputs"
    else
        echo "❌ Failed to update frontend configuration from stack"
        echo "   Falling back to .env.dev if available..."
    fi
    
    if [ -f ".env.dev" ]; then
        cd frontend
        npm run build
        cd ..
        echo "✅ Frontend build complete"
    else
        echo "⚠️  WARNING: .env.dev not found in project root"
        echo "   Skipping frontend build..."
    fi
    echo ""
fi

# Sync directories to S3
echo "📦 Syncing repository to S3..."
echo ""

# Sync CloudFormation templates
echo "  📁 Syncing cfn/ templates..."
aws s3 sync cfn/ s3://$BUCKET/cfn/ \
    $PROFILE_FLAG \
    --delete \
    $SYNC_FLAGS \
    --exclude "*.swp" \
    --exclude ".DS_Store"

# Sync Lambda functions
echo "  📁 Syncing lambda/ functions..."
aws s3 sync lambda/ s3://$BUCKET/lambda/ \
    $PROFILE_FLAG \
    --delete \
    $SYNC_FLAGS \
    --exclude "*.pyc" \
    --exclude "__pycache__/*" \
    --exclude "package/*" \
    --exclude ".DS_Store"

# Sync frontend
echo "  📁 Syncing frontend..."
if [ -d "frontend/dist" ]; then
    aws s3 sync frontend/dist/ s3://$BUCKET/frontend/dist/ \
        $PROFILE_FLAG \
        --delete \
        $SYNC_FLAGS \
        --exclude ".DS_Store" \
        --exclude "aws-config.json"
    echo "    ✅ frontend/dist/ synced (excluding aws-config.json)"
else
    echo "    ⚠️  frontend/dist/ not found (run with --build-frontend to create)"
fi

aws s3 sync frontend/src/ s3://$BUCKET/frontend/src/ \
    $PROFILE_FLAG \
    --delete \
    $SYNC_FLAGS \
    --exclude "*.swp" \
    --exclude ".DS_Store"
echo "    ✅ frontend/src/ synced"

# Sync frontend config files
aws s3 cp frontend/package.json s3://$BUCKET/frontend/package.json $PROFILE_FLAG $SYNC_FLAGS
aws s3 cp frontend/package-lock.json s3://$BUCKET/frontend/package-lock.json $PROFILE_FLAG $SYNC_FLAGS
aws s3 cp frontend/tsconfig.json s3://$BUCKET/frontend/tsconfig.json $PROFILE_FLAG $SYNC_FLAGS
aws s3 cp frontend/vite.config.ts s3://$BUCKET/frontend/vite.config.ts $PROFILE_FLAG $SYNC_FLAGS
echo "    ✅ frontend config files synced"

# Sync scripts
echo "  📁 Syncing scripts/..."
aws s3 sync scripts/ s3://$BUCKET/scripts/ \
    $PROFILE_FLAG \
    --delete \
    $SYNC_FLAGS \
    --exclude ".DS_Store"

# Sync documentation
echo "  📁 Syncing docs/..."
aws s3 sync docs/ s3://$BUCKET/docs/ \
    $PROFILE_FLAG \
    --delete \
    $SYNC_FLAGS \
    --exclude ".DS_Store" \
    --exclude "archive/*"

# Sync root files
echo "  📄 Syncing root files..."
aws s3 cp README.md s3://$BUCKET/README.md $PROFILE_FLAG $SYNC_FLAGS
aws s3 cp .gitignore s3://$BUCKET/.gitignore $PROFILE_FLAG $SYNC_FLAGS
aws s3 cp Makefile s3://$BUCKET/Makefile $PROFILE_FLAG $SYNC_FLAGS

echo ""
echo "======================================"
echo "✅ S3 Deployment Repository Synced!"
echo "======================================"
echo ""

# Helper functions for Lambda operations
get_lambda_function_name() {
    local function_name="aws-elasticdrs-orchestrator-api-handler-dev"
    echo "$function_name"
}

package_lambda_function() {
    local function_dir="$1"
    local output_zip="$2"
    
    echo "📦 Packaging $function_dir..." >&2
    cd "$PROJECT_ROOT/lambda"
    
    rm -f "$output_zip"
    
    # Initialize zip
    if [ -d "package" ] && [ "$(ls -A package 2>/dev/null)" ]; then
        cd package
        zip -qr "$output_zip" .
        cd ..
    else
        touch /tmp/empty_placeholder
        zip -q "$output_zip" /tmp/empty_placeholder
        zip -qd "$output_zip" empty_placeholder 2>/dev/null || true
        rm -f /tmp/empty_placeholder
    fi
    
    # Add the function's index.py
    if [ -f "$function_dir/index.py" ]; then
        zip -qj "$output_zip" "$function_dir/index.py"
    fi
    
    # Add shared modules
    if [ -d "shared" ]; then
        for shared_file in shared/*.py; do
            if [ -f "$shared_file" ]; then
                zip -qj "$output_zip" "$shared_file"
            fi
        done
    fi
    
    cd "$PROJECT_ROOT"
    echo "$output_zip"
}

# Update Lambda code directly (emergency use only)
if [ "$UPDATE_LAMBDA_CODE" = true ]; then
    if [ "$DRY_RUN" = true ]; then
        echo "ℹ️  DRY RUN: Would update Lambda function code"
        echo ""
    else
        echo "======================================"
        echo "⚡ Fast Lambda Code Update"
        echo "======================================"
        echo ""
        
        DEPLOY_START=$(date +%s)
        
        # Lambda functions to update (aligned with deployed stack)
        LAMBDA_FUNCTIONS=(
            "api-handler:aws-elasticdrs-orchestrator-api-handler-dev"
            "orchestration-stepfunctions:aws-elasticdrs-orchestrator-orch-sf-dev"
            "frontend-builder:aws-elasticdrs-orchestrator-frontend-build-dev"
            "execution-finder:aws-elasticdrs-orchestrator-execution-finder-dev"
            "execution-poller:aws-elasticdrs-orchestrator-execution-poller-dev"
            "bucket-cleaner:aws-elasticdrs-orchestrator-bucket-cleaner-dev"
            "notification-formatter:aws-elasticdrs-orchestrator-notif-fmt-dev"
        )
        
        cd "$PROJECT_ROOT/lambda"
        
        for func_entry in "${LAMBDA_FUNCTIONS[@]}"; do
            func_dir="${func_entry%%:*}"
            func_name="${func_entry##*:}"
            
            if [ ! -d "$func_dir" ]; then
                echo "⚠️  Directory $func_dir not found, skipping..."
                continue
            fi
            
            package_lambda_function "$func_dir" "/tmp/lambda-${func_dir}.zip"
            
            echo "⚡ Updating $func_name..."
            aws lambda update-function-code \
                --function-name "$func_name" \
                --zip-file "fileb:///tmp/lambda-${func_dir}.zip" \
                $PROFILE_FLAG \
                --region $REGION \
                --query 'LastModified' \
                --output text > /dev/null 2>&1 && echo "  ✅ $func_dir updated" || echo "  ⚠️  $func_dir update failed"
            
            rm -f "/tmp/lambda-${func_dir}.zip"
        done
        
        cd "$PROJECT_ROOT"
        
        DEPLOY_END=$(date +%s)
        DEPLOY_DURATION=$((DEPLOY_END - DEPLOY_START))
        
        echo ""
        echo "======================================"
        echo "✅ Lambda Functions Updated!"
        echo "======================================"
        echo "Deployment Duration: ${DEPLOY_DURATION}s"
        echo ""
    fi
fi

# Deploy frontend directly (emergency use only)
if [ "$DEPLOY_FRONTEND" = true ]; then
    if [ "$DRY_RUN" = true ]; then
        echo "ℹ️  DRY RUN: Would deploy Frontend"
        echo ""
    else
        echo "======================================"
        echo "🚀 Deploying Frontend"
        echo "======================================"
        echo ""
        
        DEPLOY_START=$(date +%s)
        
        # Get Frontend bucket name from stack
        FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
            --stack-name "$PARENT_STACK_NAME" \
            --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
            --output text $PROFILE_FLAG --region $REGION)
        
        # Get CloudFront distribution ID
        CLOUDFRONT_DIST=$(aws cloudformation describe-stacks \
            --stack-name "$PARENT_STACK_NAME" \
            --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
            --output text $PROFILE_FLAG --region $REGION)
        
        if [ -z "$FRONTEND_BUCKET" ] || [ "$FRONTEND_BUCKET" = "None" ]; then
            echo "  ❌ Could not find Frontend bucket from stack outputs"
            exit 1
        fi
        
        echo "📦 Syncing frontend/dist/ to s3://$FRONTEND_BUCKET/..."
        
        if [ -d "frontend/dist" ]; then
            aws s3 sync frontend/dist/ s3://$FRONTEND_BUCKET/ \
                $PROFILE_FLAG \
                --delete \
                --region $REGION \
                --exclude "aws-config.json"
            
            echo "  ✅ Frontend files synced to $FRONTEND_BUCKET"
            
            # Generate aws-config.json from stack outputs
            echo "  📝 Generating aws-config.json from CloudFormation outputs..."
            API_ENDPOINT=$(aws cloudformation describe-stacks \
                --stack-name "$PARENT_STACK_NAME" \
                --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
                --output text $PROFILE_FLAG --region $REGION)
            USER_POOL_ID=$(aws cloudformation describe-stacks \
                --stack-name "$PARENT_STACK_NAME" \
                --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" \
                --output text $PROFILE_FLAG --region $REGION)
            USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks \
                --stack-name "$PARENT_STACK_NAME" \
                --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" \
                --output text $PROFILE_FLAG --region $REGION)
            
            cat > /tmp/aws-config.json << EOF
{
  "region": "$REGION",
  "userPoolId": "$USER_POOL_ID",
  "userPoolClientId": "$USER_POOL_CLIENT_ID",
  "apiEndpoint": "$API_ENDPOINT"
}
EOF
            aws s3 cp /tmp/aws-config.json s3://$FRONTEND_BUCKET/aws-config.json \
                $PROFILE_FLAG \
                --region $REGION \
                --cache-control "no-cache, no-store, must-revalidate"
            rm -f /tmp/aws-config.json
            echo "  ✅ aws-config.json generated and uploaded"
        else
            echo "  ❌ frontend/dist/ not found - run with --build-frontend first"
            exit 1
        fi
        
        # Invalidate CloudFront cache
        if [ -n "$CLOUDFRONT_DIST" ] && [ "$CLOUDFRONT_DIST" != "None" ]; then
            echo ""
            echo "🔄 Invalidating CloudFront cache ($CLOUDFRONT_DIST)..."
            aws cloudfront create-invalidation \
                --distribution-id "$CLOUDFRONT_DIST" \
                --paths "/*" \
                $PROFILE_FLAG \
                --region $REGION \
                --query 'Invalidation.Id' \
                --output text
            echo "  ✅ CloudFront invalidation started"
        fi
        
        DEPLOY_END=$(date +%s)
        DEPLOY_DURATION=$((DEPLOY_END - DEPLOY_START))
        
        echo ""
        echo "======================================"
        echo "✅ Frontend Deployed!"
        echo "======================================"
        echo "Deployment Duration: ${DEPLOY_DURATION}s"
        echo "Frontend Bucket: $FRONTEND_BUCKET"
        echo "CloudFront: $CLOUDFRONT_DIST"
        echo ""
    fi
fi

# Show warnings for emergency deployment methods
if [ "$UPDATE_LAMBDA_CODE" = true ] || [ "$DEPLOY_FRONTEND" = true ] || [ "$EMERGENCY_DEPLOY" = true ]; then
    echo "======================================"
    echo "⚠️  GitHub Actions Bypass Warning"
    echo "======================================"
    echo ""
    echo "You are using emergency deployment methods that bypass GitHub Actions:"
    echo ""
    if [ "$UPDATE_LAMBDA_CODE" = true ]; then
        echo "  • --update-lambda-code: Direct Lambda deployment"
    fi
    if [ "$DEPLOY_FRONTEND" = true ]; then
        echo "  • --deploy-frontend: Direct frontend deployment"
    fi
    if [ "$EMERGENCY_DEPLOY" = true ]; then
        echo "  • --emergency-deploy: Emergency bypass mode"
    fi
    echo ""
    echo "⚠️  RISKS:"
    echo "  • No security scanning (Bandit, Semgrep, Safety)"
    echo "  • No CloudFormation validation"
    echo "  • No automated testing"
    echo "  • No deployment audit trail"
    echo ""
    echo "🚀 RECOMMENDED: Use GitHub Actions instead:"
    echo "  git add . && git commit -m 'changes' && git push"
    echo ""
fi

echo "======================================"
echo "📊 Summary"
echo "======================================"
echo "S3 Bucket: s3://$BUCKET"
echo "Region: $REGION"
echo "Git Commit: $GIT_SHORT"
echo ""
echo "Synced Components:"
echo "  ✅ CloudFormation templates (cfn/)"
echo "  ✅ Lambda functions (lambda/)"
echo "  ✅ Frontend source + dist (frontend/)"
echo "  ✅ Automation scripts (scripts/)"
echo "  ✅ Documentation (docs/)"
echo ""
echo "🚀 Next Steps:"
echo "  • For deployment: git push (triggers GitHub Actions)"
echo "  • For emergency fixes: Use --emergency-deploy flags"
echo ""