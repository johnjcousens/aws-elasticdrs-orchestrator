#!/bin/bash
# Complete deployment and sync workflow
# Purpose: Build frontend, deploy to CloudFront, sync to S3 deployment bucket
# Usage: ./scripts/deploy-and-sync-all.sh

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "Complete Deployment & Sync Workflow"
echo "=========================================="
echo "Project: AWS DRS Orchestration"
echo "Root: $PROJECT_ROOT"
echo ""

# Verify AWS credentials
echo "🔐 Verifying AWS credentials..."
if ! aws sts get-caller-identity --region us-east-1 >/dev/null 2>&1; then
    echo "❌ ERROR: AWS credentials not configured"
    echo "Please set:"
    echo "  export AWS_ACCESS_KEY_ID=..."
    echo "  export AWS_SECRET_ACCESS_KEY=..."
    echo "  export AWS_SESSION_TOKEN=..."
    exit 1
fi
echo "✅ AWS credentials verified"
echo ""

# Step 1: Build Frontend
echo "=========================================="
echo "Step 1: Build Frontend"
echo "=========================================="
cd "$PROJECT_ROOT/frontend"

if [ ! -f "../.env.test" ]; then
    echo "❌ ERROR: .env.test not found"
    exit 1
fi

echo "🏗️  Building React application..."
./build.sh

if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then
    echo "❌ ERROR: Build failed - dist/ directory not created"
    exit 1
fi

echo "✅ Frontend build complete"
echo ""
cd "$PROJECT_ROOT"

# Step 2: Deploy Frontend to CloudFront Bucket
echo "=========================================="
echo "Step 2: Deploy Frontend to CloudFront"
echo "=========================================="

FRONTEND_BUCKET="drs-orchestration-fe-***REMOVED***-test"
DISTRIBUTION_ID="E3EHO8EL65JUV4"
REGION="us-east-1"

echo "📦 Syncing frontend to S3..."
aws s3 sync frontend/dist/ s3://$FRONTEND_BUCKET/ \
    --delete \
    --region $REGION \
    --cache-control "public, max-age=31536000" \
    --exclude "index.html" \
    --exclude "aws-config.json"

# Sync index.html and aws-config.json with no-cache
aws s3 cp frontend/dist/index.html s3://$FRONTEND_BUCKET/index.html \
    --region $REGION \
    --cache-control "no-cache, no-store, must-revalidate"

aws s3 cp frontend/dist/aws-config.json s3://$FRONTEND_BUCKET/aws-config.json \
    --region $REGION \
    --cache-control "no-cache, no-store, must-revalidate"

echo "✅ Frontend synced to S3"
echo ""

echo "🔄 Creating CloudFront invalidation..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $DISTRIBUTION_ID \
    --paths "/*" \
    --region $REGION \
    --query 'Invalidation.Id' \
    --output text)

echo "✅ CloudFront invalidation created: $INVALIDATION_ID"
echo "   Status: https://console.aws.amazon.com/cloudfront/home?region=$REGION#distribution-settings:$DISTRIBUTION_ID"
echo ""

# Step 3: Sync to Deployment Repository
echo "=========================================="
echo "Step 3: Sync to S3 Deployment Repository"
echo "=========================================="

DEPLOYMENT_BUCKET="aws-drs-orchestration"

echo "📦 Syncing complete repository to S3..."
echo ""

# Sync CloudFormation templates
echo "  📁 Syncing cfn/..."
aws s3 sync cfn/ s3://$DEPLOYMENT_BUCKET/cfn/ \
    --delete \
    --region $REGION \
    --exclude ".DS_Store"

# Sync Lambda functions
echo "  📁 Syncing lambda/..."
aws s3 sync lambda/ s3://$DEPLOYMENT_BUCKET/lambda/ \
    --delete \
    --region $REGION \
    --exclude "*.pyc" \
    --exclude "__pycache__/*" \
    --exclude "package/*" \
    --exclude ".DS_Store"

# Sync frontend
echo "  📁 Syncing frontend/dist/..."
aws s3 sync frontend/dist/ s3://$DEPLOYMENT_BUCKET/frontend/dist/ \
    --delete \
    --region $REGION \
    --exclude ".DS_Store"

echo "  📁 Syncing frontend/src/..."
aws s3 sync frontend/src/ s3://$DEPLOYMENT_BUCKET/frontend/src/ \
    --delete \
    --region $REGION \
    --exclude ".DS_Store"

# Sync frontend config
echo "  📄 Syncing frontend config files..."
aws s3 cp frontend/package.json s3://$DEPLOYMENT_BUCKET/frontend/package.json --region $REGION
aws s3 cp frontend/package-lock.json s3://$DEPLOYMENT_BUCKET/frontend/package-lock.json --region $REGION
aws s3 cp frontend/tsconfig.json s3://$DEPLOYMENT_BUCKET/frontend/tsconfig.json --region $REGION
aws s3 cp frontend/vite.config.ts s3://$DEPLOYMENT_BUCKET/frontend/vite.config.ts --region $REGION

# Sync scripts
echo "  📁 Syncing scripts/..."
aws s3 sync scripts/ s3://$DEPLOYMENT_BUCKET/scripts/ \
    --delete \
    --region $REGION \
    --exclude ".DS_Store"

# Sync SSM documents
echo "  📁 Syncing ssm-documents/..."
aws s3 sync ssm-documents/ s3://$DEPLOYMENT_BUCKET/ssm-documents/ \
    --delete \
    --region $REGION \
    --exclude ".DS_Store"

# Sync documentation
echo "  📁 Syncing docs/..."
aws s3 sync docs/ s3://$DEPLOYMENT_BUCKET/docs/ \
    --delete \
    --region $REGION \
    --exclude ".DS_Store" \
    --exclude "archive/*"

# Sync root files
echo "  📄 Syncing root files..."
aws s3 cp README.md s3://$DEPLOYMENT_BUCKET/README.md --region $REGION
aws s3 cp .gitignore s3://$DEPLOYMENT_BUCKET/.gitignore --region $REGION
aws s3 cp Makefile s3://$DEPLOYMENT_BUCKET/Makefile --region $REGION

echo ""
echo "✅ Deployment repository synced"
echo ""

# Step 4: Verification
echo "=========================================="
echo "Step 4: Verification"
echo "=========================================="

echo "🔍 Verifying deployments..."
echo ""

# Verify frontend bucket
echo "Frontend Bucket Check:"
if aws s3 ls s3://$FRONTEND_BUCKET/index.html --region $REGION > /dev/null 2>&1; then
    echo "  ✅ index.html exists in CloudFront bucket"
else
    echo "  ❌ index.html NOT found in CloudFront bucket"
fi

# Verify deployment bucket
echo "Deployment Bucket Check:"
if aws s3 ls s3://$DEPLOYMENT_BUCKET/frontend/dist/index.html --region $REGION > /dev/null 2>&1; then
    echo "  ✅ frontend/dist/index.html exists in deployment bucket"
else
    echo "  ❌ frontend/dist/index.html NOT found in deployment bucket"
fi

echo ""

# Step 5: Summary
echo "=========================================="
echo "✅ Deployment & Sync Complete!"
echo "=========================================="
echo ""
echo "Frontend Deployment:"
echo "  🌐 CloudFront URL: https://d2bxv9p27f38od.cloudfront.net"
echo "  📦 S3 Bucket: s3://$FRONTEND_BUCKET"
echo "  🔄 Invalidation: $INVALIDATION_ID"
echo ""
echo "Deployment Repository:"
echo "  📦 S3 Bucket: s3://$DEPLOYMENT_BUCKET"
echo "  🌐 Console: https://s3.console.aws.amazon.com/s3/buckets/$DEPLOYMENT_BUCKET"
echo ""
echo "Repository Contents (Deployment Ready):"
echo "  ✅ CloudFormation templates (cfn/)"
echo "  ✅ Lambda functions (lambda/)"
echo "  ✅ Frontend build (frontend/dist/)"
echo "  ✅ Frontend source (frontend/src/)"
echo "  ✅ Automation scripts (scripts/)"
echo "  ✅ SSM documents (ssm-documents/)"
echo "  ✅ Documentation (docs/)"
echo ""
echo "Next Steps:"
echo "  1. Test frontend: https://d2bxv9p27f38od.cloudfront.net"
echo "  2. Verify CloudFront cache clear (5-10 minutes)"
echo "  3. Deployment from S3: aws s3 sync s3://$DEPLOYMENT_BUCKET/ ./deploy/"
echo ""
