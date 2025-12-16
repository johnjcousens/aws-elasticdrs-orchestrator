#!/bin/bash
# Sync complete deployment-ready repository to S3
# Purpose: Keep s3://aws-drs-orchestration in sync with local git repo
# Usage: ./scripts/sync-to-deployment-bucket.sh [--build-frontend]

set -e  # Exit on error

# Disable AWS CLI pager for all commands (compatible with CLI v1 and v2)
export AWS_PAGER=""

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BUCKET="aws-drs-orchestration"
REGION="us-east-1"
BUILD_FRONTEND=false
DRY_RUN=false
CLEAN_ORPHANS=false
DEPLOY_CFN=false
DEPLOY_LAMBDA=false
UPDATE_LAMBDA_CODE=false
DEPLOY_FRONTEND=false
UPDATE_ALL_LAMBDA=false
# Default to standard AWS credentials profile
AWS_PROFILE="777788889999_AdministratorAccess"
LIST_PROFILES=false

# CloudFormation stack configuration
PROJECT_NAME="drsorchv4"
ENVIRONMENT="test"
PARENT_STACK_NAME="drs-orch-v4"

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
        --deploy-cfn)
            DEPLOY_CFN=true
            shift
            ;;
        --deploy-lambda)
            DEPLOY_LAMBDA=true
            shift
            ;;
        --update-lambda-code)
            UPDATE_LAMBDA_CODE=true
            shift
            ;;
        --update-all-lambda)
            UPDATE_ALL_LAMBDA=true
            shift
            ;;
        --deploy-frontend)
            DEPLOY_FRONTEND=true
            shift
            ;;
        --list-profiles)
            LIST_PROFILES=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --profile PROFILE        AWS credentials profile (default: 777788889999_AdministratorAccess)"
            echo "  --build-frontend         Build frontend before syncing"
            echo "  --dry-run                Show what would be synced without making changes"
            echo "  --clean-orphans          Remove orphaned directories from S3"
            echo "  --list-profiles          List available AWS profiles and exit"
            echo "  --help                   Show this help message"
            echo ""
            echo "Deployment Options:"
            echo "  --deploy-cfn             Deploy ALL stacks via parent CloudFormation (5-10 min)"
            echo "  --update-lambda-code     Update api-handler Lambda code ONLY (~5 sec)"
            echo "  --update-all-lambda      Update ALL Lambda functions code (~15 sec)"
            echo "  --deploy-lambda          Deploy Lambda stack via CloudFormation (~30 sec)"
            echo "  --deploy-frontend        Sync frontend/dist to S3 + CloudFront invalidation (~10 sec)"
            echo ""
            echo "Examples:"
            echo "  # Basic sync (no deployment)"
            echo "  $0                                    # Sync all files to S3"
            echo ""
            echo "  # Fast Lambda code updates"
            echo "  $0 --update-lambda-code               # Fastest: Direct Lambda update (~5s)"
            echo "  $0 --deploy-lambda                    # Fast: Lambda stack only (~30s)"
            echo ""
            echo "  # Frontend deployments"
            echo "  $0 --build-frontend --deploy-frontend # Build + deploy frontend"
            echo ""
            echo "  # Full deployments"
            echo "  $0 --deploy-cfn                       # All stacks via parent (5-10 min)"
            echo "  $0 --build-frontend --deploy-cfn      # Build + deploy everything"
            echo ""
            echo "  # Utilities"
            echo "  $0 --profile MyProfile                # Use specific AWS profile"
            echo "  $0 --dry-run --clean-orphans          # Preview cleanup"
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
        ./build.sh
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
    local function_name="drsorchv4-api-handler-test"
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
        
        # Lambda function mappings: local file -> actual function name
        declare -A LAMBDA_FUNCTIONS=(
            ["index.py"]="drsorchv4-api-handler-test"
            ["orchestration_stepfunctions.py"]="drsorchv4-orchestration-stepfunctions-test"
            ["build_and_deploy.py"]="drsorchv4-frontend-builder-test"
            ["poller/execution_finder.py"]="drsorchv4-execution-finder-test"
            ["poller/execution_poller.py"]="drsorchv4-execution-poller-test"
        )
        
        for local_file in "${!LAMBDA_FUNCTIONS[@]}"; do
            func_name="${LAMBDA_FUNCTIONS[$local_file]}"
            
            if [ -f "$local_file" ]; then
                echo "📦 Packaging $func_suffix..."
                rm -f /tmp/lambda-${func_suffix}.zip
                
                # First, add dependencies from package/ directory (at root level of zip)
                if [ -d "package" ] && [ "$(ls -A package 2>/dev/null)" ]; then
                    cd package
                    zip -qr /tmp/lambda-${func_suffix}.zip .
                    cd ..
                fi
                
                # Create zip based on file location
                if [[ "$local_file" == poller/* ]]; then
                    # For poller functions, include the poller directory structure
                    zip -qg /tmp/lambda-${func_suffix}.zip "$local_file" 2>/dev/null || zip -q /tmp/lambda-${func_suffix}.zip "$local_file"
                else
                    zip -qg /tmp/lambda-${func_suffix}.zip "$local_file" 2>/dev/null || zip -q /tmp/lambda-${func_suffix}.zip "$local_file"
                fi
                
                echo "⚡ Updating $func_name..."
                aws lambda update-function-code \
                    --function-name "$func_name" \
                    --zip-file fileb:///tmp/lambda-${func_suffix}.zip \
                    $PROFILE_FLAG \
                    --region $REGION \
                    --query 'LastModified' \
                    --output text \
                    2>/dev/null && echo "  ✅ $func_suffix updated" || echo "  ⚠️  $func_suffix not found (may not be deployed)"
                
                rm -f /tmp/lambda-${func_suffix}.zip
            else
                echo "  ⚠️  $local_file not found, skipping $func_suffix"
            fi
        done
        
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
        
        # Add Lambda code to zip
        zip -g "$PACKAGE_FILE" index.py > /dev/null
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
if [ "$DEPLOY_CFN" = true ] && [ "$DRY_RUN" = false ]; then
    echo "Deployed Stacks:"
    if [ "$STACK_UPDATED" = true ]; then
        echo "  ✅ $PARENT_STACK_NAME (parent)"
        echo "     └─ All nested stacks updated"
    else
        echo "  ℹ️  $PARENT_STACK_NAME (no changes)"
        echo "     └─ All nested stacks up-to-date"
    fi
    echo ""
fi
