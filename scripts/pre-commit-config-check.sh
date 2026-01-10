#!/bin/bash

# Pre-commit Configuration Check
# Prevents commits with hardcoded configuration values

set -e

echo "🔍 Checking for hardcoded configuration values..."

# Define patterns to search for
HARDCODED_PATTERNS=(
  "us-east-1_[a-zA-Z0-9]+"  # User Pool IDs
  "[0-9a-z]{26}"            # Client IDs (26 character alphanumeric)
  "https://[a-z0-9]+\.execute-api\.[a-z0-9-]+\.amazonaws\.com"  # API Gateway URLs
)

VIOLATIONS_FOUND=false

for pattern in "${HARDCODED_PATTERNS[@]}"; do
  echo "  Checking pattern: $pattern"
  
  # Search in frontend source files, excluding node_modules and dist
  MATCHES=$(find frontend/src -name "*.ts" -o -name "*.tsx" | xargs grep -l "$pattern" 2>/dev/null || true)
  
  if [ -n "$MATCHES" ]; then
    echo "❌ Hardcoded configuration found in:"
    echo "$MATCHES" | sed 's/^/    /'
    
    # Show the actual matches
    echo "  Matches:"
    find frontend/src -name "*.ts" -o -name "*.tsx" | xargs grep -n "$pattern" 2>/dev/null | sed 's/^/    /' || true
    
    VIOLATIONS_FOUND=true
  fi
done

if [ "$VIOLATIONS_FOUND" = true ]; then
  echo ""
  echo "💥 COMMIT BLOCKED: Hardcoded configuration values detected"
  echo ""
  echo "🔧 To fix this:"
  echo "1. Remove hardcoded User Pool IDs, Client IDs, and API endpoints"
  echo "2. Use window.AWS_CONFIG for runtime configuration"
  echo "3. Ensure configuration is loaded from aws-config.json"
  echo ""
  echo "ℹ️ Configuration should be generated dynamically by GitHub Actions"
  echo "   from CloudFormation stack outputs during deployment."
  exit 1
else
  echo "✅ No hardcoded configuration values found"
fi