#!/bin/bash
#
# Lambda Packaging Script
# Packages all Lambda functions and uploads to S3 deployment bucket
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_BUCKET=$1
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate arguments
if [ -z "$DEPLOYMENT_BUCKET" ]; then
    print_error "Usage: $0 <deployment-bucket>"
    print_info "Example: $0 my-lambda-deployment-bucket"
    exit 1
fi

# Verify AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Verify S3 bucket exists
if ! aws s3 ls "s3://${DEPLOYMENT_BUCKET}" &> /dev/null; then
    print_error "S3 bucket '${DEPLOYMENT_BUCKET}' does not exist or is not accessible"
    exit 1
fi

print_info "Starting Lambda packaging process..."
print_info "Project Root: ${PROJECT_ROOT}"
print_info "Deployment Bucket: ${DEPLOYMENT_BUCKET}"

# Create build directory
print_info "Creating build directory..."
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

# Package API Handler
print_info "Packaging API Handler Lambda..."
cd "${PROJECT_ROOT}/lambda/api-handler"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -t . --upgrade
fi
zip -r "${BUILD_DIR}/api-handler.zip" . -x "*.pyc" -x "*__pycache__*" -x "*.git*" -x "*.DS_Store"
print_info "API Handler packaged: $(du -h ${BUILD_DIR}/api-handler.zip | cut -f1)"

# Package Orchestration Lambda
print_info "Packaging Orchestration Lambda..."
cd "${PROJECT_ROOT}/lambda/orchestration"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -t . --upgrade
fi
zip -r "${BUILD_DIR}/orchestration.zip" . -x "*.pyc" -x "*__pycache__*" -x "*.git*" -x "*.DS_Store"
print_info "Orchestration packaged: $(du -h ${BUILD_DIR}/orchestration.zip | cut -f1)"

# Package S3 Cleanup Custom Resource
print_info "Packaging S3 Cleanup Lambda..."
cd "${PROJECT_ROOT}/lambda/custom-resources"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -t . --upgrade
fi
zip -r "${BUILD_DIR}/s3-cleanup.zip" . -x "*.pyc" -x "*__pycache__*" -x "*.git*" -x "*.DS_Store"
print_info "S3 Cleanup packaged: $(du -h ${BUILD_DIR}/s3-cleanup.zip | cut -f1)"

# Package Frontend Builder Custom Resource
print_info "Packaging Frontend Builder Lambda..."
cd "${PROJECT_ROOT}/lambda/frontend-builder"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -t . --upgrade
fi
zip -r "${BUILD_DIR}/frontend-builder.zip" . -x "*.pyc" -x "*__pycache__*" -x "*.git*" -x "*.DS_Store"
print_info "Frontend Builder packaged: $(du -h ${BUILD_DIR}/frontend-builder.zip | cut -f1)"

# Upload to S3
print_info "Uploading Lambda packages to S3..."
cd "${BUILD_DIR}"

aws s3 cp api-handler.zip "s3://${DEPLOYMENT_BUCKET}/lambda/api-handler.zip" --no-progress
print_info "✓ Uploaded api-handler.zip"

aws s3 cp orchestration.zip "s3://${DEPLOYMENT_BUCKET}/lambda/orchestration.zip" --no-progress
print_info "✓ Uploaded orchestration.zip"

aws s3 cp s3-cleanup.zip "s3://${DEPLOYMENT_BUCKET}/lambda/s3-cleanup.zip" --no-progress
print_info "✓ Uploaded s3-cleanup.zip"

aws s3 cp frontend-builder.zip "s3://${DEPLOYMENT_BUCKET}/lambda/frontend-builder.zip" --no-progress
print_info "✓ Uploaded frontend-builder.zip"

# Generate manifest file
print_info "Generating deployment manifest..."
cat > "${BUILD_DIR}/manifest.json" <<EOF
{
  "generatedAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "bucket": "${DEPLOYMENT_BUCKET}",
  "packages": [
    {
      "name": "api-handler",
      "key": "lambda/api-handler.zip",
      "size": "$(stat -f%z api-handler.zip 2>/dev/null || stat -c%s api-handler.zip 2>/dev/null)"
    },
    {
      "name": "orchestration",
      "key": "lambda/orchestration.zip",
      "size": "$(stat -f%z orchestration.zip 2>/dev/null || stat -c%s orchestration.zip 2>/dev/null)"
    },
    {
      "name": "s3-cleanup",
      "key": "lambda/s3-cleanup.zip",
      "size": "$(stat -f%z s3-cleanup.zip 2>/dev/null || stat -c%s s3-cleanup.zip 2>/dev/null)"
    },
    {
      "name": "frontend-builder",
      "key": "lambda/frontend-builder.zip",
      "size": "$(stat -f%z frontend-builder.zip 2>/dev/null || stat -c%s frontend-builder.zip 2>/dev/null)"
    }
  ]
}
EOF

aws s3 cp manifest.json "s3://${DEPLOYMENT_BUCKET}/lambda/manifest.json" --no-progress
print_info "✓ Uploaded manifest.json"

# Cleanup
print_info "Cleaning up build directory..."
cd "${PROJECT_ROOT}"
# Keep the build directory for local reference but remove installed packages
find lambda -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find lambda -name "*.pyc" -delete 2>/dev/null || true

print_info ""
print_info "================================"
print_info "Lambda packaging complete!"
print_info "================================"
print_info ""
print_info "Deployment bucket: s3://${DEPLOYMENT_BUCKET}/lambda/"
print_info "Build artifacts: ${BUILD_DIR}"
print_info ""
print_info "Next steps:"
print_info "1. Update CloudFormation parameters to use this S3 bucket"
print_info "2. Deploy CloudFormation stacks"
print_info ""
print_info "CloudFormation parameter:"
print_info "  LambdaCodeBucket=${DEPLOYMENT_BUCKET}"
