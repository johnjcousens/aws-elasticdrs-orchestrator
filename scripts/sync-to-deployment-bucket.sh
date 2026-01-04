#!/bin/bash
# Sync repository to S3 and coordinate with CodePipeline for deployment
# Purpose: Keep s3://aws-elasticdrs-orchestrator in sync with local git repo and trigger proper CI/CD
# Usage: ./scripts/sync-to-deployment-bucket.sh [--trigger-pipeline]

set -e  # Exit on error

# Disable AWS CLI pager for all commands (compatible with CLI v1 and v2)
export AWS_PAGER=""

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load configuration from environment files
# Priority: .env.deployment.local > .env.deployment > defaults
if [ -f "$PROJECT_ROOT/.env.deployment" ]; then
    echo "📋 Loading configuration from .env.deployment"
    source "$PROJECT_ROOT/.env.deployment"
fi

if [ -f "$PROJECT_ROOT/.env.deployment.local" ]; then
    echo "📋 Loading local overrides from .env.deployment.local"
    source "$PROJECT_ROOT/.env.deployment.local"
fi

# Default configuration (can be overridden by environment files or command line)
BUCKET="${DEPLOYMENT_BUCKET:-aws-elasticdrs-orchestrator}"
REGION="${DEPLOYMENT_REGION:-us-east-1}"
BUILD_FRONTEND=false
DRY_RUN=false
CLEAN_ORPHANS=false
TRIGGER_PIPELINE=false
PUSH_TO_CODECOMMIT=false
COMMIT_AND_PUSH=false
EMERGENCY_DEPLOY=false  # Emergency bypass for critical fixes only
UPDATE_LAMBDA_CODE=false  # Legacy support - will warn about pipeline
DEPLOY_FRONTEND=false     # Legacy support - will warn about pipeline
# Default AWS profile (override with --profile or in .env files)
AWS_PROFILE="${AWS_PROFILE:-default}"
LIST_PROFILES=false

# CodePipeline configuration
PIPELINE_NAME="${PIPELINE_NAME:-aws-elasticdrs-orchestrator-pipeline-dev}"
CODECOMMIT_REPO="${CODECOMMIT_REPO:-aws-elasticdrs-orchestrator-dev}"
CODECOMMIT_REMOTE="${CODECOMMIT_REMOTE:-aws-pipeline}"

# CloudFormation stack configuration
PROJECT_NAME="${PROJECT_NAME:-aws-elasticdrs-orchestrator}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
PARENT_STACK_NAME="${PARENT_STACK_NAME:-${PROJECT_NAME}-${ENVIRONMENT}}"

# Approved top-level directories (directories synced by this script)
APPROVED_DIRS=("cfn" "docs" "frontend" "lambda" "scripts" "ssm-documents")

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
        --trigger-pipeline)
            TRIGGER_PIPELINE=true
            shift
            ;;
        --push-to-codecommit)
            PUSH_TO_CODECOMMIT=true
            shift
            ;;
        --commit-and-push)
            COMMIT_AND_PUSH=true
            shift
            ;;
        --emergency-deploy)
            EMERGENCY_DEPLOY=true
            echo "⚠️  WARNING: Emergency deployment mode - bypassing CI/CD pipeline"
            echo "   This should only be used for critical production fixes!"
            shift
            ;;
        --update-lambda-code)
            UPDATE_LAMBDA_CODE=true
            echo "⚠️  WARNING: --update-lambda-code bypasses CI/CD pipeline"
            echo "   Consider using --trigger-pipeline for proper deployment"
            shift
            ;;
        --deploy-frontend)
            DEPLOY_FRONTEND=true
            echo "⚠️  WARNING: --deploy-frontend bypasses CI/CD pipeline"
            echo "   Consider using --trigger-pipeline for proper deployment"
            shift
            ;;
        --list-profiles)
            LIST_PROFILES=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "🚀 RECOMMENDED CI/CD WORKFLOW:"
            echo "  $0 --trigger-pipeline              # Sync to S3 + trigger full CI/CD pipeline"
            echo "  $0 --push-to-codecommit           # Push to CodeCommit (triggers pipeline automatically)"
            echo "  $0 --commit-and-push              # Commit changes and push to CodeCommit"
            echo ""
            echo "Options:"
            echo "  --profile PROFILE                  AWS credentials profile (default: ${AWS_PROFILE})"
            echo "  --build-frontend                   Build frontend before syncing"
            echo "  --dry-run                          Show what would be synced without making changes"
            echo "  --clean-orphans                    Remove orphaned directories from S3"
            echo "  --trigger-pipeline                 Trigger CodePipeline after sync (RECOMMENDED)"
            echo "  --push-to-codecommit              Push to CodeCommit repository"
            echo "  --commit-and-push                 Commit changes and push to CodeCommit"
            echo "  --list-profiles                    List available AWS profiles and exit"
            echo "  --help                             Show this help message"
            echo ""
            echo "🚨 EMERGENCY/LEGACY OPTIONS (bypass CI/CD):"
            echo "  --emergency-deploy                 Emergency bypass for critical fixes"
            echo "  --update-lambda-code               Update Lambda code directly (legacy)"
            echo "  --deploy-frontend                  Deploy frontend directly (legacy)"
            echo ""
            echo "Examples:"
            echo "  # RECOMMENDED: Full CI/CD deployment"
            echo "  $0 --trigger-pipeline              # Sync + trigger pipeline (includes security scan)"
            echo "  $0 --push-to-codecommit            # Push to CodeCommit (auto-triggers pipeline)"
            echo "  $0 --commit-and-push               # Commit changes and push to CodeCommit"
            echo ""
            echo "  # Development workflow"
            echo "  $0                                 # Basic sync to S3 (no deployment)"
            echo "  $0 --build-frontend                # Build frontend + sync"
            echo "  $0 --dry-run                       # Preview changes"
            echo ""
            echo "  # Emergency fixes only"
            echo "  $0 --emergency-deploy --update-lambda-code  # Critical production fix"
            echo ""
            echo "Pipeline Stages: Source → Validate → SecurityScan → Build → Test → DeployInfra → DeployFrontend"
            exit 0
            ;;
        # Legacy options - kept for backward compatibility but with warnings
        --deploy-cfn|--deploy-lambda|--update-all-lambda)
            echo "⚠️  WARNING: $1 is deprecated and bypasses CI/CD pipeline"
            echo "   Use --trigger-pipeline for proper deployment through CI/CD"
            echo "   Continuing with legacy behavior..."
            # Set appropriate flags for backward compatibility
            case $1 in
                --deploy-cfn) EMERGENCY_DEPLOY=true ;;
                --deploy-lambda) EMERGENCY_DEPLOY=true ;;
                --update-all-lambda) UPDATE_LAMBDA_CODE=true ;;
            esac
            shift
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
        grep '^\[' ~/.aws/credentials | sed 's/\[//g' | sed 's/\]//g' | while read profile; do
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

# Build sync/cp flags with metadata
SYNC_FLAGS="--region $REGION --metadata git-commit=$GIT_COMMIT,git-short=$GIT_SHORT,sync-time=$SYNC_TIME"
if [ "$DRY_RUN" = true ]; then
    SYNC_FLAGS="$SYNC_FLAGS --dryrun"
    echo "🔍 DRY RUN MODE - No changes will be made"
    echo ""
fi

echo "======================================"
echo "S3 Deployment Repository Sync + CI/CD"
echo "======================================"
echo "Bucket: s3://$BUCKET"
echo "Region: $REGION"
echo "Build Frontend: $BUILD_FRONTEND"
echo "Dry Run: $DRY_RUN"
echo "AWS Profile: $AWS_PROFILE"
echo "Git Commit: $GIT_SHORT ($GIT_COMMIT)"
echo "Sync Time: $SYNC_TIME"
echo ""
if [ "$TRIGGER_PIPELINE" = true ]; then
    echo "🚀 CI/CD Mode: Will trigger CodePipeline after sync"
    echo "   Pipeline: $PIPELINE_NAME"
fi
if [ "$PUSH_TO_CODECOMMIT" = true ]; then
    echo "📤 CodeCommit Mode: Will push to CodeCommit repository"
    echo "   Repository: $CODECOMMIT_REPO"
fi
if [ "$COMMIT_AND_PUSH" = true ]; then
    echo "📝 Commit and Push Mode: Will commit changes and push to CodeCommit"
    echo "   Repository: $CODECOMMIT_REPO"
fi
if [ "$UPDATE_LAMBDA_CODE" = true ] || [ "$DEPLOY_FRONTEND" = true ] || [ "$EMERGENCY_DEPLOY" = true ]; then
    echo "⚠️  Legacy Mode: Bypassing CI/CD pipeline (not recommended)"
fi
echo ""

# Verify AWS credentials
echo "🔐 Verifying AWS credentials..."
if ! AWS_PAGER="" aws sts get-caller-identity $PROFILE_FLAG --region $REGION >/dev/null 2>&1; then
    echo "❌ ERROR: AWS credentials not configured or profile not found"
    echo ""
    echo "Current profile: $AWS_PROFILE"
    echo ""
    echo "Solutions:"
    echo "  1. Check ~/.aws/credentials file exists and contains [$AWS_PROFILE]"
    echo "  2. Use different profile: $0 --profile PROFILE_NAME"
    echo "  3. List available profiles: $0 --list-profiles"
    echo ""
    echo "Expected credentials file format:"
    echo "  ~/.aws/credentials should contain:"
    echo "  [$AWS_PROFILE]"
    echo "  aws_access_key_id = YOUR_KEY"
    echo "  aws_secret_access_key = YOUR_SECRET"
    echo "  aws_session_token = YOUR_TOKEN (if using temporary credentials)"
    exit 1
fi

echo "✅ AWS credentials verified"
echo ""

# Clean orphaned directories if requested
if [ "$CLEAN_ORPHANS" = true ]; then
    echo "🧹 Checking for orphaned directories in S3..."
    echo ""
    
    # Get all top-level directories from S3
    S3_DIRS=$(aws s3 ls s3://$BUCKET/ $PROFILE_FLAG --region $REGION | grep PRE | awk '{print $2}' | sed 's/\///')
    
    # Find orphaned directories
    ORPHANED_DIRS=()
    ORPHANED_FILES=()
    
    for dir in $S3_DIRS; do
        # Check if directory is in approved list
        is_approved=false
        for approved in "${APPROVED_DIRS[@]}"; do
            if [ "$dir" = "$approved" ]; then
                is_approved=true
                break
            fi
        done
        if [ "$is_approved" = false ]; then
            ORPHANED_DIRS+=("$dir")
        fi
    done
    
    # Check for orphaned files at root level (excluding approved files)
    S3_FILES=$(aws s3 ls s3://$BUCKET/ $PROFILE_FLAG --region $REGION | grep -v PRE | awk '{print $4}')
    APPROVED_FILES=("README.md" ".gitignore" "Makefile")
    
    for file in $S3_FILES; do
        is_approved=false
        for approved in "${APPROVED_FILES[@]}"; do
            if [ "$file" = "$approved" ]; then
                is_approved=true
                break
            fi
        done
        if [ "$is_approved" = false ]; then
            ORPHANED_FILES+=("$file")
        fi
    done
    
    # Report findings
    if [ ${#ORPHANED_DIRS[@]} -eq 0 ] && [ ${#ORPHANED_FILES[@]} -eq 0 ]; then
        echo "✅ No orphaned directories or files found!"
        echo ""
    else
        echo "⚠️  Found orphaned items:"
        echo ""
        
        if [ ${#ORPHANED_DIRS[@]} -gt 0 ]; then
            echo "  Orphaned directories:"
            for dir in "${ORPHANED_DIRS[@]}"; do
                echo "    - $dir/"
            done
            echo ""
        fi
        
        if [ ${#ORPHANED_FILES[@]} -gt 0 ]; then
            echo "  Orphaned files:"
            for file in "${ORPHANED_FILES[@]}"; do
                echo "    - $file"
            done
            echo ""
        fi
        
        # Confirm deletion (skip in dry-run mode)
        if [ "$DRY_RUN" = true ]; then
            echo "  (DRY RUN: Would prompt for deletion confirmation)"
            echo ""
        else
            read -p "Delete these orphaned items? (y/n): " -n 1 -r
            echo ""
            
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                # Delete orphaned directories
                for dir in "${ORPHANED_DIRS[@]}"; do
                    echo "  🗑️  Deleting $dir/..."
                    aws s3 rm s3://$BUCKET/$dir/ $PROFILE_FLAG --recursive --region $REGION
                done
                
                # Delete orphaned files
                for file in "${ORPHANED_FILES[@]}"; do
                    echo "  🗑️  Deleting $file..."
                    aws s3 rm s3://$BUCKET/$file $PROFILE_FLAG --region $REGION
                done
                
                echo ""
                echo "✅ Orphaned items deleted!"
                echo ""
            else
                echo ""
                echo "ℹ️  Orphaned items kept (not deleted)"
                echo ""
            fi
        fi
    fi
fi

# Build frontend if requested
if [ "$BUILD_FRONTEND" = true ]; then
    echo "🏗️  Building frontend..."
    
    # Always update frontend configuration from CloudFormation stack
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
        echo "   .env.dev is required for frontend build - it contains:"
        echo "   - Cognito User Pool ID and Client ID"
        echo "   - API Gateway Endpoint URL"
        echo "   - AWS Region"
        echo "   Create .env.dev from .env.test.template and populate with your values"
        echo ""
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
    --exclude ".DS_Store" \
   

# Sync Lambda functions
echo "  📁 Syncing lambda/ functions..."
aws s3 sync lambda/ s3://$BUCKET/lambda/ \
    $PROFILE_FLAG \
    --delete \
    $SYNC_FLAGS \
    --exclude "*.pyc" \
    --exclude "__pycache__/*" \
    --exclude "package/*" \
    --exclude ".DS_Store" \
   

# Sync frontend (built dist/ and source)
echo "  📁 Syncing frontend..."
if [ -d "frontend/dist" ]; then
    aws s3 sync frontend/dist/ s3://$BUCKET/frontend/dist/ \
        $PROFILE_FLAG \
        --delete \
        $SYNC_FLAGS \
        --exclude ".DS_Store" \
       
    echo "    ✅ frontend/dist/ synced"
else
    echo "    ⚠️  frontend/dist/ not found (run with --build-frontend to create)"
fi

aws s3 sync frontend/src/ s3://$BUCKET/frontend/src/ \
    $PROFILE_FLAG \
    --delete \
    $SYNC_FLAGS \
    --exclude "*.swp" \
    --exclude ".DS_Store" \
   
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
    --exclude ".DS_Store" \
   

# Sync SSM documents
echo "  📁 Syncing ssm-documents/..."
aws s3 sync ssm-documents/ s3://$BUCKET/ssm-documents/ \
    $PROFILE_FLAG \
    --delete \
    $SYNC_FLAGS \
    --exclude ".DS_Store" \
   

# Sync documentation
echo "  📁 Syncing docs/..."
aws s3 sync docs/ s3://$BUCKET/docs/ \
    $PROFILE_FLAG \
    --delete \
    $SYNC_FLAGS \
    --exclude ".DS_Store" \
    --exclude "archive/*" \
   

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

# Helper function to get Lambda function name
get_lambda_function_name() {
    local function_name="aws-elasticdrs-orchestrator-api-handler-dev"
    echo "$function_name"
}

# Helper function to package Lambda
package_lambda() {
    echo "📦 Packaging Lambda function..." >&2
    cd "$PROJECT_ROOT/lambda"
    
    # Create deployment package
    local package_file="deployment-package.zip"
    rm -f "$package_file"
    
    # Install dependencies if requirements.txt exists
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt -t package/ --quiet
    fi
    
    # Create zip with dependencies
    if [ -d "package" ]; then
        cd package
        zip -r ../"$package_file" . > /dev/null
        cd ..
    else
        mkdir -p package
        cd package
        zip -r ../"$package_file" . > /dev/null
        cd ..
    fi
    
    # Add Lambda code to zip
    zip -g "$package_file" index.py > /dev/null
    if [ -f "rbac_middleware.py" ]; then
        zip -g "$package_file" rbac_middleware.py > /dev/null
    fi
    # Add security_utils dependency (required by index.py)
    if [ -f "security_utils.py" ]; then
        zip -g "$package_file" security_utils.py > /dev/null
    fi
    if [ -d "poller" ]; then
        zip -rg "$package_file" poller/ > /dev/null
    fi
    
    cd "$PROJECT_ROOT"
    echo "$package_file"
}

# Individual stack deployment: Update Lambda code directly (fastest)
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
        
        LAMBDA_FUNCTION=$(get_lambda_function_name)
        
        # Create proper Lambda package with dependencies
        echo "📦 Creating Lambda package with dependencies..."
        cd "$PROJECT_ROOT/lambda"
        rm -f /tmp/lambda-quick.zip
        
        # First, add dependencies from package/ directory (at root level of zip)
        if [ -d "package" ] && [ "$(ls -A package 2>/dev/null)" ]; then
            echo "  Adding dependencies from package/..."
            cd package
            zip -qr /tmp/lambda-quick.zip .
            cd ..
        else
            # Initialize empty zip
            echo "  No package/ dependencies found, creating minimal package..."
            touch /tmp/empty_placeholder
            zip -q /tmp/lambda-quick.zip /tmp/empty_placeholder
            zip -qd /tmp/lambda-quick.zip empty_placeholder 2>/dev/null || true
            rm -f /tmp/empty_placeholder
        fi
        
        # Add Lambda code files at root level
        echo "  Adding Lambda code files..."
        zip -qg /tmp/lambda-quick.zip index.py
        if [ -f "requirements.txt" ]; then
            zip -qg /tmp/lambda-quick.zip requirements.txt
        fi
        # Add rbac_middleware dependency (required by index.py)
        if [ -f "rbac_middleware.py" ]; then
            zip -qg /tmp/lambda-quick.zip rbac_middleware.py
        fi
        # Add security_utils dependency (required by index.py)
        if [ -f "security_utils.py" ]; then
            zip -qg /tmp/lambda-quick.zip security_utils.py
        fi
        if [ -d "poller" ]; then
            zip -qrg /tmp/lambda-quick.zip poller/
        fi
        if [ -f "orchestration_stepfunctions.py" ]; then
            zip -qg /tmp/lambda-quick.zip orchestration_stepfunctions.py
        fi
        if [ -f "build_and_deploy.py" ]; then
            zip -qg /tmp/lambda-quick.zip build_and_deploy.py
        fi
        
        cd "$PROJECT_ROOT"
        
        echo "⚡ Updating Lambda function code..."
        aws lambda update-function-code \
            --function-name "$LAMBDA_FUNCTION" \
            --zip-file fileb:///tmp/lambda-quick.zip \
            $PROFILE_FLAG \
            --region $REGION \
            --query '[FunctionName,LastModified,CodeSize]' \
            --output table \
           
        
        rm -f /tmp/lambda-quick.zip
        
        DEPLOY_END=$(date +%s)
        DEPLOY_DURATION=$((DEPLOY_END - DEPLOY_START))
        
        echo ""
        echo "======================================"
        echo "✅ Lambda Code Updated!"
        echo "======================================"
        echo "Deployment Duration: ${DEPLOY_DURATION}s"
        echo "Function: $LAMBDA_FUNCTION"
        echo ""
    fi
fi

# Update ALL Lambda functions
if [ "$UPDATE_ALL_LAMBDA" = true ]; then
    if [ "$DRY_RUN" = true ]; then
        echo "ℹ️  DRY RUN: Would update all Lambda functions"
        echo ""
    else
        echo "======================================"
        echo "⚡ Updating ALL Lambda Functions"
        echo "======================================"
        echo ""
        
        DEPLOY_START=$(date +%s)
        
        cd "$PROJECT_ROOT/lambda"
        
        # Update each Lambda function individually with proper dependencies
        echo "📦 Packaging index (API Handler)..."
        rm -f "/tmp/lambda-index.zip"
        
        # Add dependencies if they exist
        if [ -d "package" ] && [ "$(ls -A package 2>/dev/null)" ]; then
            cd package
            zip -qr "/tmp/lambda-index.zip" .
            cd ..
        fi
        
        # Add the main handler and its dependencies (files must be at root level in zip)
        zip -qj "/tmp/lambda-index.zip" "index.py" 2>/dev/null || zip -qj "/tmp/lambda-index.zip" "index.py"
        # Add rbac_middleware dependency (required by index.py)
        if [ -f "rbac_middleware.py" ]; then
            zip -qj "/tmp/lambda-index.zip" "rbac_middleware.py"
        fi
        # Add security_utils dependency (required by index.py)
        if [ -f "security_utils.py" ]; then
            zip -qj "/tmp/lambda-index.zip" "security_utils.py"
        fi
        
        echo "⚡ Updating aws-elasticdrs-orchestrator-api-handler-dev..."
        aws lambda update-function-code \
            --function-name "aws-elasticdrs-orchestrator-api-handler-dev" \
            --zip-file "fileb:///tmp/lambda-index.zip" \
            $PROFILE_FLAG \
            --region $REGION \
            --query 'LastModified' \
            --output text > /dev/null 2>&1 && echo "  ✅ API Handler updated" || echo "  ⚠️  API Handler update failed"
        
        rm -f "/tmp/lambda-index.zip"
        
        # Update orchestration stepfunctions
        echo "📦 Packaging orchestration_stepfunctions..."
        rm -f "/tmp/lambda-orchestration.zip"
        
        if [ -d "package" ] && [ "$(ls -A package 2>/dev/null)" ]; then
            cd package
            zip -qr "/tmp/lambda-orchestration.zip" .
            cd ..
        fi
        
        zip -qj "/tmp/lambda-orchestration.zip" "orchestration_stepfunctions.py" 2>/dev/null || zip -qj "/tmp/lambda-orchestration.zip" "orchestration_stepfunctions.py"
        # Add security_utils dependency
        if [ -f "security_utils.py" ]; then
            zip -qj "/tmp/lambda-orchestration.zip" "security_utils.py"
        fi
        
        echo "⚡ Updating aws-elasticdrs-orchestrator-orchestration-stepfunctions-dev..."
        aws lambda update-function-code \
            --function-name "aws-elasticdrs-orchestrator-orchestration-stepfunctions-dev" \
            --zip-file "fileb:///tmp/lambda-orchestration.zip" \
            $PROFILE_FLAG \
            --region $REGION \
            --query 'LastModified' \
            --output text > /dev/null 2>&1 && echo "  ✅ Orchestration StepFunctions updated" || echo "  ⚠️  Orchestration StepFunctions update failed"
        
        rm -f "/tmp/lambda-orchestration.zip"
        
        # Update frontend builder
        echo "📦 Packaging build_and_deploy..."
        rm -f "/tmp/lambda-builder.zip"
        
        if [ -d "package" ] && [ "$(ls -A package 2>/dev/null)" ]; then
            cd package
            zip -qr "/tmp/lambda-builder.zip" .
            cd ..
        fi
        
        zip -qj "/tmp/lambda-builder.zip" "build_and_deploy.py" 2>/dev/null || zip -qj "/tmp/lambda-builder.zip" "build_and_deploy.py"
        # Add security_utils dependency
        if [ -f "security_utils.py" ]; then
            zip -qj "/tmp/lambda-builder.zip" "security_utils.py"
        fi
        
        echo "⚡ Updating aws-elasticdrs-orchestrator-frontend-builder-dev..."
        aws lambda update-function-code \
            --function-name "aws-elasticdrs-orchestrator-frontend-builder-dev" \
            --zip-file "fileb:///tmp/lambda-builder.zip" \
            $PROFILE_FLAG \
            --region $REGION \
            --query 'LastModified' \
            --output text > /dev/null 2>&1 && echo "  ✅ Frontend Builder updated" || echo "  ⚠️  Frontend Builder update failed"
        
        rm -f "/tmp/lambda-builder.zip"
        
        # Update execution finder
        echo "📦 Packaging execution_finder..."
        rm -f "/tmp/lambda-finder.zip"
        
        if [ -d "package" ] && [ "$(ls -A package 2>/dev/null)" ]; then
            cd package
            zip -qr "/tmp/lambda-finder.zip" .
            cd ..
        fi
        
        zip -qj "/tmp/lambda-finder.zip" "poller/execution_finder.py" 2>/dev/null || zip -qj "/tmp/lambda-finder.zip" "poller/execution_finder.py"
        # Add security_utils dependency
        if [ -f "security_utils.py" ]; then
            zip -qj "/tmp/lambda-finder.zip" "security_utils.py"
        fi
        
        echo "⚡ Updating aws-elasticdrs-orchestrator-execution-finder-dev..."
        aws lambda update-function-code \
            --function-name "aws-elasticdrs-orchestrator-execution-finder-dev" \
            --zip-file "fileb:///tmp/lambda-finder.zip" \
            $PROFILE_FLAG \
            --region $REGION \
            --query 'LastModified' \
            --output text > /dev/null 2>&1 && echo "  ✅ Execution Finder updated" || echo "  ⚠️  Execution Finder update failed"
        
        rm -f "/tmp/lambda-finder.zip"
        
        # Update execution poller
        echo "📦 Packaging execution_poller..."
        rm -f "/tmp/lambda-poller.zip"
        
        if [ -d "package" ] && [ "$(ls -A package 2>/dev/null)" ]; then
            cd package
            zip -qr "/tmp/lambda-poller.zip" .
            cd ..
        fi
        
        zip -qj "/tmp/lambda-poller.zip" "poller/execution_poller.py" 2>/dev/null || zip -qj "/tmp/lambda-poller.zip" "poller/execution_poller.py"
        # Add security_utils dependency
        if [ -f "security_utils.py" ]; then
            zip -qj "/tmp/lambda-poller.zip" "security_utils.py"
        fi
        
        echo "⚡ Updating aws-elasticdrs-orchestrator-execution-poller-dev..."
        aws lambda update-function-code \
            --function-name "aws-elasticdrs-orchestrator-execution-poller-dev" \
            --zip-file "fileb:///tmp/lambda-poller.zip" \
            $PROFILE_FLAG \
            --region $REGION \
            --query 'LastModified' \
            --output text > /dev/null 2>&1 && echo "  ✅ Execution Poller updated" || echo "  ⚠️  Execution Poller update failed"
        
        rm -f "/tmp/lambda-poller.zip"
        
        cd "$PROJECT_ROOT"
        
        DEPLOY_END=$(date +%s)
        DEPLOY_DURATION=$((DEPLOY_END - DEPLOY_START))
        
        echo ""
        echo "======================================"
        echo "✅ All Lambda Functions Updated!"
        echo "======================================"
        echo "Deployment Duration: ${DEPLOY_DURATION}s"
        echo ""
    fi
fi

# Individual stack deployment: Deploy Lambda stack via CloudFormation
if [ "$DEPLOY_LAMBDA" = true ]; then
    if [ "$DRY_RUN" = true ]; then
        echo "ℹ️  DRY RUN: Would deploy Lambda stack"
        echo ""
    else
        echo "======================================"
        echo "🚀 Deploying Lambda Stack"
        echo "======================================"
        echo ""
        
        DEPLOY_START=$(date +%s)
        
        # Package and upload Lambda code
        PACKAGE_FILE=$(package_lambda)
        
        echo "☁️  Uploading Lambda package to S3..."
        aws s3 cp "lambda/$PACKAGE_FILE" "s3://$BUCKET/lambda/$PACKAGE_FILE" \
            $PROFILE_FLAG \
            --region $REGION \
            --metadata "git-commit=$GIT_COMMIT,sync-time=$SYNC_TIME" \
           
        echo "  ✅ Package uploaded"
        echo ""
        
        # Get Lambda stack name from parent stack
        LAMBDA_STACK_ID=$(aws cloudformation describe-stack-resources \
            --stack-name "$PARENT_STACK_NAME" \
            --logical-resource-id "LambdaStack" \
            --query "StackResources[0].PhysicalResourceId" \
            --output text \
            $PROFILE_FLAG \
            --region $REGION \
            2>/dev/null) || LAMBDA_STACK_ID="${PROJECT_NAME}-${ENVIRONMENT}-lambda"
        
        echo "🔄 Updating Lambda stack ($LAMBDA_STACK_ID)..."
        
        # Get parameters from parent stack
        PROT_TABLE=$(aws cloudformation describe-stacks \
            --stack-name "$PARENT_STACK_NAME" \
            --query "Stacks[0].Outputs[?OutputKey=='ProtectionGroupsTableName'].OutputValue" \
            --output text $PROFILE_FLAG --region $REGION)
        PLANS_TABLE=$(aws cloudformation describe-stacks \
            --stack-name "$PARENT_STACK_NAME" \
            --query "Stacks[0].Outputs[?OutputKey=='RecoveryPlansTableName'].OutputValue" \
            --output text $PROFILE_FLAG --region $REGION)
        EXEC_TABLE=$(aws cloudformation describe-stacks \
            --stack-name "$PARENT_STACK_NAME" \
            --query "Stacks[0].Outputs[?OutputKey=='ExecutionHistoryTableName'].OutputValue" \
            --output text $PROFILE_FLAG --region $REGION)
        
        STACK_UPDATE_OUTPUT=$(aws cloudformation update-stack \
            --stack-name "$LAMBDA_STACK_ID" \
            --template-url "https://s3.amazonaws.com/$BUCKET/cfn/lambda-stack.yaml" \
            --parameters \
                ParameterKey=ProjectName,ParameterValue="$PROJECT_NAME" \
                ParameterKey=Environment,ParameterValue="$ENVIRONMENT" \
                ParameterKey=SourceBucket,ParameterValue="$BUCKET" \
                ParameterKey=ProtectionGroupsTableName,ParameterValue="$PROT_TABLE" \
                ParameterKey=RecoveryPlansTableName,ParameterValue="$PLANS_TABLE" \
                ParameterKey=ExecutionHistoryTableName,ParameterValue="$EXEC_TABLE" \
                ParameterKey=NotificationTopicArn,ParameterValue="" \
            --capabilities CAPABILITY_NAMED_IAM \
            $PROFILE_FLAG \
            --region $REGION \
            \
            2>&1) || STACK_UPDATE_FAILED=true
        
        if [ "$STACK_UPDATE_FAILED" = true ]; then
            if echo "$STACK_UPDATE_OUTPUT" | grep -q "No updates are to be performed"; then
                echo "  ℹ️  Lambda stack already up-to-date"
            else
                echo "  ❌ Stack update failed:"
                echo "$STACK_UPDATE_OUTPUT"
                exit 1
            fi
        else
            echo "  ⏳ Waiting for Lambda stack update..."
            aws cloudformation wait stack-update-complete \
                --stack-name "$LAMBDA_STACK_ID" \
                $PROFILE_FLAG \
                --region $REGION \
               
            echo "  ✅ Lambda stack updated"
        fi
        
        DEPLOY_END=$(date +%s)
        DEPLOY_DURATION=$((DEPLOY_END - DEPLOY_START))
        
        echo ""
        echo "======================================"
        echo "✅ Lambda Stack Deployed!"
        echo "======================================"
        echo "Deployment Duration: ${DEPLOY_DURATION}s"
        echo ""
    fi
fi

# Individual stack deployment: Deploy Frontend stack
if [ "$DEPLOY_FRONTEND" = true ]; then
    if [ "$DRY_RUN" = true ]; then
        echo "ℹ️  DRY RUN: Would deploy Frontend stack"
        echo ""
    else
        echo "======================================"
        echo "🚀 Deploying Frontend"
        echo "======================================"
        echo ""
        
        # Always update frontend configuration from CloudFormation stack before deployment
        echo "📝 Updating frontend configuration from CloudFormation stack..."
        if ./scripts/update-frontend-config.sh "$PARENT_STACK_NAME" "$REGION"; then
            echo "✅ Frontend configuration updated from stack outputs"
        else
            echo "❌ Failed to update frontend configuration from stack"
            exit 1
        fi
        
        DEPLOY_START=$(date +%s)
        
        # Get Frontend bucket name from parent stack
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
        
        # Sync frontend dist to the actual frontend bucket (not deployment bucket)
        if [ -d "frontend/dist" ]; then
            aws s3 sync frontend/dist/ s3://$FRONTEND_BUCKET/ \
                $PROFILE_FLAG \
                --delete \
                --region $REGION \
               
            echo "  ✅ Frontend files synced to $FRONTEND_BUCKET"
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
                --output text \
               
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

# Deploy to CloudFormation if requested
if [ "$DEPLOY_CFN" = true ]; then
    if [ "$DRY_RUN" = true ]; then
        echo "ℹ️  DRY RUN: Would deploy to CloudFormation"
        echo ""
    else
        echo "======================================"
        echo "🚀 Deploying to AWS via CloudFormation"
        echo "======================================"
        echo ""
        
        DEPLOY_START=$(date +%s)
        
        # Package Lambda function
        echo "📦 Packaging Lambda function..."
        cd "$PROJECT_ROOT/lambda"
        
        # Create deployment package
        PACKAGE_FILE="deployment-package.zip"
        rm -f "$PACKAGE_FILE"
        
        # Install dependencies to package directory
        if [ -f requirements.txt ]; then
            pip install -r requirements.txt -t package/ --quiet
        fi
        
        # Create zip with dependencies
        cd package
        zip -r ../"$PACKAGE_FILE" . > /dev/null
        cd ..
        
        # Add Lambda code to zip with dependencies
        zip -g "$PACKAGE_FILE" index.py > /dev/null
        # Add rbac_middleware dependency (required by index.py)
        if [ -f "rbac_middleware.py" ]; then
            zip -g "$PACKAGE_FILE" rbac_middleware.py > /dev/null
        fi
        # Add security_utils dependency (required by index.py)
        if [ -f "security_utils.py" ]; then
            zip -g "$PACKAGE_FILE" security_utils.py > /dev/null
        fi
        if [ -d "poller" ]; then
            zip -rg "$PACKAGE_FILE" poller/ > /dev/null
        fi
        
        # Upload Lambda package to S3
        echo "  ☁️  Uploading Lambda package to S3..."
        aws s3 cp "$PACKAGE_FILE" "s3://$BUCKET/lambda/$PACKAGE_FILE" \
            $PROFILE_FLAG \
            --region $REGION \
            --metadata "git-commit=$GIT_COMMIT,sync-time=$SYNC_TIME" \
           
        
        cd "$PROJECT_ROOT"
        echo "  ✅ Lambda package uploaded"
        echo ""
        
        # Update parent stack (will automatically propagate to nested stacks)
        echo "🔄 Updating parent stack ($PARENT_STACK_NAME)..."
        echo "   This will update all nested stacks (Database, Lambda, API, Frontend)"
        echo ""
        
        STACK_UPDATE_OUTPUT=$(aws cloudformation update-stack \
            --stack-name "$PARENT_STACK_NAME" \
            --template-url "https://s3.amazonaws.com/$BUCKET/cfn/master-template.yaml" \
            --parameters \
                ParameterKey=ProjectName,UsePreviousValue=true \
                ParameterKey=Environment,UsePreviousValue=true \
                ParameterKey=SourceBucket,ParameterValue="$BUCKET" \
                ParameterKey=AdminEmail,UsePreviousValue=true \
                ParameterKey=CognitoDomainPrefix,UsePreviousValue=true \
                ParameterKey=NotificationEmail,UsePreviousValue=true \
                ParameterKey=EnableWAF,UsePreviousValue=true \
                ParameterKey=EnableCloudTrail,UsePreviousValue=true \
                ParameterKey=EnableSecretsManager,UsePreviousValue=true \
            --capabilities CAPABILITY_NAMED_IAM \
            $PROFILE_FLAG \
            --region $REGION \
            \
            2>&1) || STACK_UPDATE_FAILED=true
        
        if [ "$STACK_UPDATE_FAILED" = true ]; then
            if echo "$STACK_UPDATE_OUTPUT" | grep -q "No updates are to be performed"; then
                echo "  ℹ️  Stack already up-to-date (no changes needed)"
                STACK_UPDATED=false
            else
                echo "  ❌ Stack update failed:"
                echo ""
                echo "$STACK_UPDATE_OUTPUT"
                echo ""
                exit 1
            fi
        else
            echo "  ⏳ Waiting for stack update to complete..."
            echo "     (This may take 5-10 minutes as nested stacks update)"
            aws cloudformation wait stack-update-complete \
                --stack-name "$PARENT_STACK_NAME" \
                $PROFILE_FLAG \
                --region $REGION \
               
            echo "  ✅ Parent stack updated successfully"
            echo "     All nested stacks (Database, Lambda, API, Frontend) are now up-to-date"
            STACK_UPDATED=true
        fi
        echo ""
        
        DEPLOY_END=$(date +%s)
        DEPLOY_DURATION=$((DEPLOY_END - DEPLOY_START))
        
        echo "======================================"
        echo "✅ CloudFormation Deployment Complete!"
        echo "======================================"
        echo ""
        echo "Deployment Duration: ${DEPLOY_DURATION}s"
        echo ""
        if [ "$STACK_UPDATED" = true ]; then
            echo "  ✅ Parent stack: UPDATE_COMPLETE"
            echo "     └─ All nested stacks updated (Database, Lambda, API, Frontend)"
        else
            echo "  ℹ️  Parent stack: No changes needed"
            echo "     └─ All nested stacks already up-to-date"
        fi
        echo ""
    fi
fi

# Pipeline coordination functions
push_to_codecommit() {
    echo "======================================"
    echo "🚀 Pushing to CodeCommit Repository"
    echo "======================================"
    echo "Repository: $CODECOMMIT_REPO"
    echo "Remote: $CODECOMMIT_REMOTE"
    echo ""
    
    # Check if CodeCommit remote exists
    if ! git remote get-url "$CODECOMMIT_REMOTE" >/dev/null 2>&1; then
        echo "❌ ERROR: CodeCommit remote '$CODECOMMIT_REMOTE' not configured"
        echo ""
        echo "To configure CodeCommit remote:"
        echo "  git remote add $CODECOMMIT_REMOTE https://git-codecommit.$REGION.amazonaws.com/v1/repos/$CODECOMMIT_REPO"
        echo ""
        exit 1
    fi
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        echo "⚠️  WARNING: You have uncommitted changes"
        echo "   Commit your changes before pushing to CodeCommit"
        echo ""
        git --no-pager status -s
        echo ""
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted by user"
            exit 1
        fi
    fi
    
    # Push to CodeCommit
    echo "📤 Pushing to CodeCommit..."
    if git --no-pager push "$CODECOMMIT_REMOTE" main -q; then
        echo "✅ Successfully pushed to CodeCommit"
        echo ""
        echo "🔄 CodePipeline will automatically trigger from CodeCommit push"
        echo "   Monitor pipeline: https://console.aws.amazon.com/codesuite/codepipeline/pipelines/$PIPELINE_NAME/view"
        echo ""
    else
        echo "❌ Failed to push to CodeCommit"
        exit 1
    fi
}

trigger_pipeline() {
    echo "======================================"
    echo "🚀 Triggering CodePipeline"
    echo "======================================"
    echo "Pipeline: $PIPELINE_NAME"
    echo ""
    
    # Check if pipeline exists
    if ! AWS_PAGER="" aws codepipeline get-pipeline --name "$PIPELINE_NAME" $PROFILE_FLAG --region "$REGION" >/dev/null 2>&1; then
        echo "❌ ERROR: Pipeline '$PIPELINE_NAME' not found"
        echo ""
        echo "Available pipelines:"
        AWS_PAGER="" aws codepipeline list-pipelines $PROFILE_FLAG --region "$REGION" --query 'pipelines[].name' --output table
        exit 1
    fi
    
    # Start pipeline execution
    echo "🚀 Starting pipeline execution..."
    EXECUTION_ID=$(AWS_PAGER="" aws codepipeline start-pipeline-execution \
        --name "$PIPELINE_NAME" \
        $PROFILE_FLAG \
        --region "$REGION" \
        --query 'pipelineExecutionId' \
        --output text)
    
    if [ $? -eq 0 ]; then
        echo "✅ Pipeline execution started"
        echo "   Execution ID: $EXECUTION_ID"
        echo ""
        echo "🔍 Pipeline Stages:"
        echo "   1. Source          - Pull from CodeCommit"
        echo "   2. Validate        - CloudFormation validation"
        echo "   3. SecurityScan    - Security scanning (Bandit, Semgrep, Safety)"
        echo "   4. Build           - Lambda packaging & frontend build"
        echo "   5. Test            - Unit & integration tests"
        echo "   6. DeployInfra     - CloudFormation deployment"
        echo "   7. DeployFrontend  - Frontend deployment to S3/CloudFront"
        echo ""
        echo "📊 Monitor pipeline:"
        echo "   Console: https://console.aws.amazon.com/codesuite/codepipeline/pipelines/$PIPELINE_NAME/view"
        echo "   CLI: aws codepipeline get-pipeline-execution --pipeline-name $PIPELINE_NAME --pipeline-execution-id $EXECUTION_ID"
        echo ""
        
        # Wait a moment and show initial status
        echo "⏳ Checking initial pipeline status..."
        sleep 5
        PIPELINE_STATUS=$(AWS_PAGER="" aws codepipeline get-pipeline-execution \
            --pipeline-name "$PIPELINE_NAME" \
            --pipeline-execution-id "$EXECUTION_ID" \
            $PROFILE_FLAG \
            --region "$REGION" \
            --query 'pipelineExecution.status' \
            --output text 2>/dev/null || echo "Unknown")
        
        echo "   Current Status: $PIPELINE_STATUS"
        echo ""
        
        if [ "$PIPELINE_STATUS" = "InProgress" ]; then
            echo "🎯 Pipeline is running successfully!"
            echo "   You will receive email notifications for any failures"
            echo "   Estimated completion time: 10-15 minutes"
        fi
    else
        echo "❌ Failed to start pipeline execution"
        exit 1
    fi
}

commit_and_push() {
    echo "======================================"
    echo "📝 Committing and Pushing to CodeCommit"
    echo "======================================"
    echo "Repository: $CODECOMMIT_REPO"
    echo ""
    
    # Check if we're in a git repository
    if ! git --no-pager rev-parse --git-dir > /dev/null 2>&1; then
        echo "❌ ERROR: Not in a git repository"
        exit 1
    fi
    
    # Check if CodeCommit remote exists
    if ! git --no-pager remote get-url aws-pipeline > /dev/null 2>&1; then
        echo "❌ ERROR: CodeCommit remote 'aws-pipeline' not configured"
        echo ""
        echo "Configure with:"
        echo "  git remote add aws-pipeline https://git-codecommit.us-east-1.amazonaws.com/v1/repos/$CODECOMMIT_REPO"
        exit 1
    fi
    
    # Check for changes to commit
    if git --no-pager diff --quiet && git --no-pager diff --cached --quiet; then
        echo "ℹ️  No changes to commit"
        echo ""
        echo "🚀 Pushing existing commits to CodeCommit..."
        if git --no-pager push -q aws-pipeline HEAD:main; then
            echo "✅ Successfully pushed to CodeCommit"
            echo "   Repository: $CODECOMMIT_REPO"
            echo "   Branch: main"
            echo ""
            echo "🔄 CodePipeline will auto-trigger from this push"
            echo ""
        else
            echo "❌ Failed to push to CodeCommit"
            exit 1
        fi
        return
    fi
    
    # Stage all changes
    echo "📋 Staging changes..."
    git add . > /dev/null 2>&1
    
    # Get current git info
    GIT_COMMIT=$(git --no-pager rev-parse HEAD 2>/dev/null || echo "unknown")
    GIT_SHORT=$(echo "$GIT_COMMIT" | cut -c1-8)
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Create commit message
    COMMIT_MSG="Security and CI/CD improvements - $TIMESTAMP

- Applied Black code formatting (PEP 8 compliance)
- Fixed isort import sorting violations
- Resolved flake8 code quality issues
- Updated Lambda functions with security integration
- Enhanced CI/CD pipeline coordination

Deployment: $GIT_SHORT
Timestamp: $TIMESTAMP
Pipeline: Will auto-trigger on push"
    
    # Write commit message to temp file
    echo "$COMMIT_MSG" > .git_commit_msg.txt
    
    # Commit changes
    echo "💾 Committing changes..."
    if git --no-pager commit -F .git_commit_msg.txt > /dev/null 2>&1; then
        echo "✅ Changes committed successfully"
        
        # Clean up temp file
        rm -f .git_commit_msg.txt
        
        # Push to CodeCommit
        echo "🚀 Pushing to CodeCommit..."
        if git --no-pager push -q aws-pipeline HEAD:main; then
            echo "✅ Successfully pushed to CodeCommit"
            echo "   Repository: $CODECOMMIT_REPO"
            echo "   Branch: main"
            echo "   Commit: $GIT_SHORT"
            echo ""
            echo "🔄 CodePipeline will auto-trigger from this push"
            echo "   Pipeline: $PIPELINE_NAME"
            echo "   Stages: Source → Validate → SecurityScan → Build → Deploy"
            echo ""
        else
            echo "❌ Failed to push to CodeCommit"
            rm -f .git_commit_msg.txt
            exit 1
        fi
    else
        echo "❌ Failed to commit changes"
        rm -f .git_commit_msg.txt
        exit 1
    fi
}

# Execute pipeline coordination based on flags
if [ "$COMMIT_AND_PUSH" = true ]; then
    if [ "$DRY_RUN" = true ]; then
        echo "ℹ️  DRY RUN: Would commit changes and push to CodeCommit"
        echo ""
    else
        commit_and_push
    fi
fi

if [ "$PUSH_TO_CODECOMMIT" = true ]; then
    if [ "$DRY_RUN" = true ]; then
        echo "ℹ️  DRY RUN: Would push to CodeCommit repository"
        echo ""
    else
        push_to_codecommit
    fi
fi

if [ "$TRIGGER_PIPELINE" = true ]; then
    if [ "$DRY_RUN" = true ]; then
        echo "ℹ️  DRY RUN: Would trigger CodePipeline execution"
        echo ""
    else
        trigger_pipeline
    fi
fi

# Show warnings for legacy deployment methods
if [ "$UPDATE_LAMBDA_CODE" = true ] || [ "$DEPLOY_FRONTEND" = true ] || [ "$EMERGENCY_DEPLOY" = true ]; then
    echo "======================================"
    echo "⚠️  CI/CD Pipeline Bypass Warning"
    echo "======================================"
    echo ""
    echo "You are using legacy deployment methods that bypass the CI/CD pipeline:"
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
    echo "  • Potential security vulnerabilities"
    echo ""
    echo "🚀 RECOMMENDED: Use proper CI/CD pipeline instead:"
    echo "  $0 --trigger-pipeline              # Full CI/CD with security scanning"
    echo "  $0 --push-to-codecommit           # Push to CodeCommit (auto-triggers pipeline)"
    echo ""
    
    if [ "$EMERGENCY_DEPLOY" = false ]; then
        read -p "Continue with legacy deployment? (y/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Deployment cancelled. Use --trigger-pipeline for proper CI/CD."
            exit 1
        fi
        echo ""
    fi
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
echo "  ✅ SSM documents (ssm-documents/)"
echo "  ✅ Documentation (docs/)"
echo ""

# Show pipeline status if triggered
if [ "$TRIGGER_PIPELINE" = true ] && [ "$DRY_RUN" = false ]; then
    echo "Pipeline Execution:"
    echo "  🚀 $PIPELINE_NAME"
    echo "     └─ Execution ID: $EXECUTION_ID"
    echo "     └─ Status: $PIPELINE_STATUS"
    echo ""
fi

# Show CodeCommit commit and push status
if [ "$COMMIT_AND_PUSH" = true ] && [ "$DRY_RUN" = false ]; then
    echo "CodeCommit Commit & Push:"
    echo "  ✅ Committed and pushed to $CODECOMMIT_REPO"
    echo "     └─ Pipeline will auto-trigger from push"
    echo ""
fi

# Show CodeCommit push status
if [ "$PUSH_TO_CODECOMMIT" = true ] && [ "$DRY_RUN" = false ]; then
    echo "CodeCommit Push:"
    echo "  ✅ Pushed to $CODECOMMIT_REPO"
    echo "     └─ Pipeline will auto-trigger from push"
    echo ""
fi

# Show legacy deployment status
if [ "$EMERGENCY_DEPLOY" = true ] && [ "$DRY_RUN" = false ]; then
    echo "Emergency Deployment:"
    echo "  ⚠️  Bypassed CI/CD pipeline"
    echo "     └─ Direct deployment completed"
    echo ""
fi
