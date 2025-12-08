#!/bin/bash
# Frontend Build Script with AWS Config Injection
# Builds React app and injects AWS configuration from .env.dev

# Ensure Homebrew's Node.js is used (v25.2.1)
export PATH="/opt/homebrew/bin:$PATH"

set -e  # Exit on error

echo "======================================"
echo "Frontend Build with Config Injection"
echo "======================================"

# Verify Node.js version
NODE_VERSION=$(node --version)
echo "Using Node.js: $NODE_VERSION"
if [[ ! "$NODE_VERSION" =~ ^v(2[0-9]|[3-9][0-9]) ]]; then
    echo "❌ ERROR: Node.js version $NODE_VERSION is too old"
    echo "   Required: v20.19+ or v22.12+"
    exit 1
fi

# Load environment variables from .env.dev
if [ -f "../.env.dev" ]; then
    echo "✅ Loading configuration from .env.dev..."
    export $(grep -v '^#' ../.env.dev | xargs)
else
    echo "❌ ERROR: .env.dev not found in parent directory"
    exit 1
fi

# Validate required environment variables
if [ -z "$COGNITO_USER_POOL_ID" ] || [ -z "$COGNITO_CLIENT_ID" ] || [ -z "$API_ENDPOINT" ] || [ -z "$COGNITO_REGION" ]; then
    echo "❌ ERROR: Missing required environment variables"
    echo "   Required: COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, API_ENDPOINT, COGNITO_REGION"
    exit 1
fi

echo ""
echo "Configuration:"
echo "  Region: $COGNITO_REGION"
echo "  User Pool ID: $COGNITO_USER_POOL_ID"
echo "  Client ID: $COGNITO_CLIENT_ID"
echo "  API Endpoint: $API_ENDPOINT"
echo ""

# Create aws-config.json in public/ directory (will be copied to dist/)
echo "📝 Generating public/aws-config.json..."
cat > public/aws-config.json << EOF
{
  "region": "$COGNITO_REGION",
  "userPoolId": "$COGNITO_USER_POOL_ID",
  "userPoolClientId": "$COGNITO_CLIENT_ID",
  "apiEndpoint": "$API_ENDPOINT"
}
EOF

echo "✅ Generated public/aws-config.json"

# Build the React application
echo ""
echo "🏗️  Building React application..."
npm run build

# Verify aws-config.json was copied to dist/
if [ -f "dist/aws-config.json" ]; then
    echo "✅ aws-config.json successfully copied to dist/"
    echo ""
    echo "Build contents:"
    cat dist/aws-config.json
else
    echo "❌ ERROR: aws-config.json not found in dist/"
    exit 1
fi

echo ""
echo "======================================"
echo "✅ Build Complete!"
echo "======================================"
echo ""
echo "To deploy to S3:"
echo "  aws s3 sync dist/ s3://drs-orchestration-fe-777788889999-dev/ --delete --region us-east-1"
echo ""
echo "To invalidate CloudFront:"
echo "  aws cloudfront create-invalidation --distribution-id <DISTRIBUTION_ID> --paths '/*' --region us-east-1"
echo ""
