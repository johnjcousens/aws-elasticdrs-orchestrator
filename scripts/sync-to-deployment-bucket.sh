#!/bin/bash
# Sync complete deployment-ready repository to S3
# Purpose: Keep s3://aws-drs-orchestration in sync with local git repo
# Usage: ./scripts/sync-to-deployment-bucket.sh [--build-frontend]

set -e  # Exit on error

# Auto-load AWS credentials if helper script exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/set-aws-credentials.sh" ]; then
    source "$SCRIPT_DIR/set-aws-credentials.sh" > /dev/null 2>&1
fi

# Configuration
BUCKET="aws-drs-orchestration"
REGION="us-east-1"
BUILD_FRONTEND=false
DRY_RUN=false
CLEAN_ORPHANS=false

# Approved top-level directories (directories synced by this script)
APPROVED_DIRS=("cfn" "docs" "frontend" "lambda" "scripts" "ssm-documents")

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
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
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--build-frontend] [--dry-run] [--clean-orphans]"
            exit 1
            ;;
    esac
done

# Auto-detect git commit for tagging
if git rev-parse --git-dir > /dev/null 2>&1; then
    GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    GIT_SHORT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
else
    GIT_COMMIT="unknown"
    GIT_SHORT="unknown"
fi
SYNC_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)

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
echo "Git Commit: $GIT_SHORT ($GIT_COMMIT)"
echo "Sync Time: $SYNC_TIME"
echo ""

# Verify AWS credentials
if ! aws sts get-caller-identity --region $REGION >/dev/null 2>&1; then
    echo "❌ ERROR: AWS credentials not configured"
    echo "Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN"
    exit 1
fi

echo "✅ AWS credentials verified"
echo ""

# Clean orphaned directories if requested
if [ "$CLEAN_ORPHANS" = true ]; then
    echo "🧹 Checking for orphaned directories in S3..."
    echo ""
    
    # Get all top-level directories from S3
    S3_DIRS=$(aws s3 ls s3://$BUCKET/ --region $REGION | grep PRE | awk '{print $2}' | sed 's/\///')
    
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
    S3_FILES=$(aws s3 ls s3://$BUCKET/ --region $REGION | grep -v PRE | awk '{print $4}')
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
                    aws s3 rm s3://$BUCKET/$dir/ --recursive --region $REGION
                done
                
                # Delete orphaned files
                for file in "${ORPHANED_FILES[@]}"; do
                    echo "  🗑️  Deleting $file..."
                    aws s3 rm s3://$BUCKET/$file --region $REGION
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
    --delete \
    $SYNC_FLAGS \
    --exclude "*.swp" \
    --exclude ".DS_Store"

# Sync Lambda functions
echo "  📁 Syncing lambda/ functions..."
aws s3 sync lambda/ s3://$BUCKET/lambda/ \
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
        --delete \
        $SYNC_FLAGS \
        --exclude ".DS_Store"
    echo "    ✅ frontend/dist/ synced"
else
    echo "    ⚠️  frontend/dist/ not found (run with --build-frontend to create)"
fi

aws s3 sync frontend/src/ s3://$BUCKET/frontend/src/ \
    --delete \
    $SYNC_FLAGS \
    --exclude "*.swp" \
    --exclude ".DS_Store"
echo "    ✅ frontend/src/ synced"

# Sync frontend config files
aws s3 cp frontend/package.json s3://$BUCKET/frontend/package.json $SYNC_FLAGS
aws s3 cp frontend/package-lock.json s3://$BUCKET/frontend/package-lock.json $SYNC_FLAGS
aws s3 cp frontend/tsconfig.json s3://$BUCKET/frontend/tsconfig.json $SYNC_FLAGS
aws s3 cp frontend/vite.config.ts s3://$BUCKET/frontend/vite.config.ts $SYNC_FLAGS
echo "    ✅ frontend config files synced"

# Sync scripts
echo "  📁 Syncing scripts/..."
aws s3 sync scripts/ s3://$BUCKET/scripts/ \
    --delete \
    $SYNC_FLAGS \
    --exclude ".DS_Store"

# Sync SSM documents
echo "  📁 Syncing ssm-documents/..."
aws s3 sync ssm-documents/ s3://$BUCKET/ssm-documents/ \
    --delete \
    $SYNC_FLAGS \
    --exclude ".DS_Store"

# Sync documentation
echo "  📁 Syncing docs/..."
aws s3 sync docs/ s3://$BUCKET/docs/ \
    --delete \
    $SYNC_FLAGS \
    --exclude ".DS_Store" \
    --exclude "archive/*"

# Sync root files
echo "  📄 Syncing root files..."
aws s3 cp README.md s3://$BUCKET/README.md $SYNC_FLAGS
aws s3 cp .gitignore s3://$BUCKET/.gitignore $SYNC_FLAGS
aws s3 cp Makefile s3://$BUCKET/Makefile $SYNC_FLAGS

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
