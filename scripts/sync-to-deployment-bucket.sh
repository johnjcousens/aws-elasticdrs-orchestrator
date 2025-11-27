#!/bin/bash
# Sync complete deployment-ready repository to S3
# Purpose: Keep s3://aws-drs-orchestration in sync with local git repo
# Usage: ./scripts/sync-to-deployment-bucket.sh [--build-frontend]

set -e  # Exit on error

# Configuration
BUCKET="aws-drs-orchestration"
REGION="us-east-1"
BUILD_FRONTEND=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --build-frontend)
            BUILD_FRONTEND=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--build-frontend]"
            exit 1
            ;;
    esac
done

echo "======================================"
echo "S3 Deployment Repository Sync"
echo "======================================"
echo "Bucket: s3://$BUCKET"
echo "Region: $REGION"
echo "Build Frontend: $BUILD_FRONTEND"
echo ""

# Verify AWS credentials
if ! aws sts get-caller-identity --region $REGION >/dev/null 2>&1; then
    echo "❌ ERROR: AWS credentials not configured"
    echo "Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN"
    exit 1
fi

echo "✅ AWS credentials verified"
echo ""

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
    --region $REGION \
    --exclude "*.swp" \
    --exclude ".DS_Store"

# Sync Lambda functions
echo "  📁 Syncing lambda/ functions..."
aws s3 sync lambda/ s3://$BUCKET/lambda/ \
    --delete \
    --region $REGION \
    --exclude "*.pyc" \
    --exclude "__pycache__/*" \
    --exclude "package/*" \
    --exclude ".DS_Store"

# Sync frontend (built dist/ and source)
echo "  📁 Syncing frontend..."
if [ -d "frontend/dist" ]; then
    aws s3 sync frontend/dist/ s3://$BUCKET/frontend/dist/ \
        --delete \
        --region $REGION \
        --exclude ".DS_Store"
    echo "    ✅ frontend/dist/ synced"
else
    echo "    ⚠️  frontend/dist/ not found (run with --build-frontend to create)"
fi

aws s3 sync frontend/src/ s3://$BUCKET/frontend/src/ \
    --delete \
    --region $REGION \
    --exclude "*.swp" \
    --exclude ".DS_Store"
echo "    ✅ frontend/src/ synced"

# Sync frontend config files
aws s3 cp frontend/package.json s3://$BUCKET/frontend/package.json --region $REGION
aws s3 cp frontend/package-lock.json s3://$BUCKET/frontend/package-lock.json --region $REGION
aws s3 cp frontend/tsconfig.json s3://$BUCKET/frontend/tsconfig.json --region $REGION
aws s3 cp frontend/vite.config.ts s3://$BUCKET/frontend/vite.config.ts --region $REGION
echo "    ✅ frontend config files synced"

# Sync scripts
echo "  📁 Syncing scripts/..."
aws s3 sync scripts/ s3://$BUCKET/scripts/ \
    --delete \
    --region $REGION \
    --exclude ".DS_Store"

# Sync SSM documents
echo "  📁 Syncing ssm-documents/..."
aws s3 sync ssm-documents/ s3://$BUCKET/ssm-documents/ \
    --delete \
    --region $REGION \
    --exclude ".DS_Store"

# Sync documentation
echo "  📁 Syncing docs/..."
aws s3 sync docs/ s3://$BUCKET/docs/ \
    --delete \
    --region $REGION \
    --exclude ".DS_Store" \
    --exclude "archive/*"

# Sync root files
echo "  📄 Syncing root files..."
aws s3 cp README.md s3://$BUCKET/README.md --region $REGION
aws s3 cp .gitignore s3://$BUCKET/.gitignore --region $REGION
aws s3 cp Makefile s3://$BUCKET/Makefile --region $REGION

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
