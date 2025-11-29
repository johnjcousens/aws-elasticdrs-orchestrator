#!/bin/bash
# Sync complete deployment-ready repository to S3
# Purpose: Keep s3://aws-drs-orchestration in sync with local git repo
# Usage: ./scripts/sync-to-deployment-bucket.sh [--build-frontend]

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BUCKET="aws-drs-orchestration"
REGION="us-east-1"
BUILD_FRONTEND=false
DRY_RUN=false
CLEAN_ORPHANS=false
# Default to standard AWS credentials profile
AWS_PROFILE="***REMOVED***_AdministratorAccess"
LIST_PROFILES=false

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
        --list-profiles)
            LIST_PROFILES=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --profile PROFILE        AWS credentials profile (default: ***REMOVED***_AdministratorAccess)"
            echo "  --build-frontend         Build frontend before syncing"
            echo "  --dry-run                Show what would be synced without making changes"
            echo "  --clean-orphans          Remove orphaned directories from S3"
            echo "  --list-profiles          List available AWS profiles and exit"
            echo "  --help                   Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Use default profile"
            echo "  $0 --build-frontend                   # Build frontend and sync"
            echo "  $0 --profile MyProfile                # Use specific profile"
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
if ! aws sts get-caller-identity $PROFILE_FLAG --region $REGION >/dev/null 2>&1; then
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
    if [ -f "../.env.test" ]; then
        cd frontend
        ../frontend/build.sh
        cd ..
        echo "✅ Frontend build complete"
    else
        echo "⚠️  WARNING: .env.test not found, skipping frontend build"
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

# Sync frontend (built dist/ and source)
echo "  📁 Syncing frontend..."
if [ -d "frontend/dist" ]; then
    aws s3 sync frontend/dist/ s3://$BUCKET/frontend/dist/ \
        $PROFILE_FLAG \
        --delete \
        $SYNC_FLAGS \
        --exclude ".DS_Store"
    echo "    ✅ frontend/dist/ synced"
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

# Sync SSM documents
echo "  📁 Syncing ssm-documents/..."
aws s3 sync ssm-documents/ s3://$BUCKET/ssm-documents/ \
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
echo "S3 Bucket: s3://$BUCKET"
echo "Region: $REGION"
echo ""
echo "Deployment-ready repository now contains:"
echo "  ✅ CloudFormation templates (cfn/)"
echo "  ✅ Lambda functions (lambda/)"
echo "  ✅ Frontend source + dist (frontend/)"
echo "  ✅ Automation scripts (scripts/)"
echo "  ✅ SSM documents (ssm-documents/)"
echo "  ✅ Documentation (docs/)"
echo ""
echo "To deploy from S3:"
echo "  1. Download: aws s3 sync s3://$BUCKET/ ./deploy-temp/"
echo "  2. Deploy CloudFormation stacks from cfn/"
echo "  3. Deploy frontend from frontend/dist/"
echo ""
