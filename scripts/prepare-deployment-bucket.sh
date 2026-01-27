#!/bin/bash
# Prepare S3 deployment bucket with Lambda packages and frontend source
# Run this ONCE before deploying CloudFormation
#
# Repository Structure:
#   This script works from the repository root directory.
#   All paths are relative to the repository root.
#
# Usage: ./scripts/prepare-deployment-bucket.sh <bucket-name>

set -e

BUCKET="${1:-aws-drs-orchestration-dev}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root for all operations
cd "$PROJECT_ROOT"

echo "======================================"
echo "Preparing Deployment Bucket: $BUCKET"
echo "======================================"
echo ""

# Create build directory
mkdir -p "build/lambda"

# Package Lambda functions
echo "📦 Packaging Lambda functions..."
cd "lambda"

for func_dir in query-handler data-management-handler execution-handler frontend-deployer notification-formatter orchestration-stepfunctions; do
    echo "  Building $func_dir.zip..."
    cd "$func_dir"
    zip -q "$PROJECT_ROOT/build/lambda/$func_dir.zip" index.py
    if [ -d "../shared" ]; then
        cd ..
        zip -qgr "$PROJECT_ROOT/build/lambda/$func_dir.zip" shared/
        cd "$func_dir"
    fi
    cd ..
done

echo "✅ Lambda packages built"
echo ""

# Upload to S3
echo "📤 Uploading to S3..."
AWS_PAGER="" aws s3 sync "build/lambda/" "s3://$BUCKET/lambda/" --exclude "*" --include "*.zip"
AWS_PAGER="" aws s3 sync "cfn/" "s3://$BUCKET/cfn/"
AWS_PAGER="" aws s3 sync "lambda/" "s3://$BUCKET/lambda/" --exclude "*.zip" --exclude "__pycache__/*" --exclude "*.pyc"
AWS_PAGER="" aws s3 sync "frontend/" "s3://$BUCKET/frontend/" --exclude "node_modules/*" --exclude "dist/*"

echo "✅ Deployment bucket ready"
echo ""
echo "Now deploy CloudFormation:"
echo "  aws cloudformation deploy \\"
echo "    --template-file cfn/master-template.yaml \\"
echo "    --stack-name your-stack-name \\"
echo "    --parameter-overrides \\"
echo "      ProjectName=your-project \\"
echo "      Environment=prod \\"
echo "      SourceBucket=$BUCKET \\"
echo "      AdminEmail=admin@example.com \\"
echo "    --capabilities CAPABILITY_NAMED_IAM"
