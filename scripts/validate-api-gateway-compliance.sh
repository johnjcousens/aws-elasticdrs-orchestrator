#!/bin/bash
# API Gateway Architecture Integration for CI/CD
# Integrates validation into GitHub Actions and sync scripts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run API Gateway architecture validation
echo "🔍 Running API Gateway Architecture Validation..."
"$SCRIPT_DIR/validate-api-architecture.sh"

# Run stack size checks
echo "📊 Running Stack Size Analysis..."
"$SCRIPT_DIR/check-stack-sizes.sh"

echo "✅ API Gateway architecture validation completed"