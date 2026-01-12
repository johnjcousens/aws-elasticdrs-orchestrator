#!/bin/bash
# Shared deployment configuration loader
# Usage: source scripts/load-deployment-config.sh

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load configuration from environment files in priority order
if [ -f "$PROJECT_ROOT/.env.deployment.fresh" ]; then
    echo "📋 Loading fresh stack configuration from .env.deployment.fresh"
    source "$PROJECT_ROOT/.env.deployment.fresh"
elif [ -f "$PROJECT_ROOT/.env.deployment" ]; then
    echo "📋 Loading configuration from .env.deployment"
    source "$PROJECT_ROOT/.env.deployment"
fi

if [ -f "$PROJECT_ROOT/.env.deployment.local" ]; then
    echo "📋 Loading local overrides from .env.deployment.local"
    source "$PROJECT_ROOT/.env.deployment.local"
fi

# Set default values if not provided in config files
export DEPLOYMENT_BUCKET="${DEPLOYMENT_BUCKET:-aws-elasticdrs-orchestrator}"
export DEPLOYMENT_REGION="${DEPLOYMENT_REGION:-us-east-1}"
export PROJECT_NAME="${PROJECT_NAME:-aws-elasticdrs-orchestrator}"
export ENVIRONMENT="${ENVIRONMENT:-test}"
export PARENT_STACK_NAME="${PARENT_STACK_NAME:-aws-elasticdrs-orchestrator-test}"

# Only set AWS_PROFILE if not in CI environment (GitHub Actions uses OIDC, not profiles)
if [ -z "$GITHUB_ACTIONS" ]; then
    export AWS_PROFILE="${AWS_PROFILE:-default}"
fi

# Derived values for convenience
export STACK_NAME="$PARENT_STACK_NAME"
export REGION="$DEPLOYMENT_REGION"

# API endpoints (from .env.deployment if available)
export API_ENDPOINT="${API_ENDPOINT:-}"
export CLOUDFRONT_URL="${CLOUDFRONT_URL:-}"
export USER_POOL_ID="${USER_POOL_ID:-}"
export USER_POOL_CLIENT_ID="${USER_POOL_CLIENT_ID:-}"

echo "🔧 Configuration loaded:"
echo "   Stack: $STACK_NAME"
echo "   Environment: $ENVIRONMENT"
echo "   Region: $REGION"
echo "   Project: $PROJECT_NAME"