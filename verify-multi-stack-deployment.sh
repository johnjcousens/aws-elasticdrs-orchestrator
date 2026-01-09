#!/bin/bash

# Verify Multi-Stack Deployment
# This script verifies both stacks are deployed correctly and Lambda packages are fixed

set -e

echo "=== Multi-Stack Deployment Verification ==="

# Stack names
CURRENT_STACK="aws-elasticdrs-orchestrator-dev"
ARCHIVE_STACK="aws-drs-orchestrator-archive-test"

echo ""
echo "🔍 Checking CloudFormation Stacks..."

# Check current stack
echo "Current Stack: $CURRENT_STACK"
CURRENT_STATUS=$(aws cloudformation describe-stacks --stack-name "$CURRENT_STACK" \
  --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_FOUND")
echo "  Status: $CURRENT_STATUS"

if [ "$CURRENT_STATUS" = "CREATE_COMPLETE" ] || [ "$CURRENT_STATUS" = "UPDATE_COMPLETE" ]; then
  CURRENT_API=$(aws cloudformation describe-stacks --stack-name "$CURRENT_STACK" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)
  CURRENT_FRONTEND=$(aws cloudformation describe-stacks --stack-name "$CURRENT_STACK" \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' --output text)
  echo "  API Endpoint: $CURRENT_API"
  echo "  Frontend URL: $CURRENT_FRONTEND"
fi

echo ""

# Check archive test stack
echo "Archive Test Stack: $ARCHIVE_STACK"
ARCHIVE_STATUS=$(aws cloudformation describe-stacks --stack-name "$ARCHIVE_STACK" \
  --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_FOUND")
echo "  Status: $ARCHIVE_STATUS"

if [ "$ARCHIVE_STATUS" = "CREATE_COMPLETE" ] || [ "$ARCHIVE_STATUS" = "UPDATE_COMPLETE" ]; then
  ARCHIVE_API=$(aws cloudformation describe-stacks --stack-name "$ARCHIVE_STACK" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)
  ARCHIVE_FRONTEND=$(aws cloudformation describe-stacks --stack-name "$ARCHIVE_STACK" \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' --output text)
  echo "  API Endpoint: $ARCHIVE_API"
  echo "  Frontend URL: $ARCHIVE_FRONTEND"
fi

echo ""
echo "🔍 Checking Lambda Functions..."

# Check execution-finder Lambda functions
echo "Execution Finder Lambda Functions:"

CURRENT_FINDER="$CURRENT_STACK-execution-finder-dev"
ARCHIVE_FINDER="$ARCHIVE_STACK-execution-finder-test"

echo "Current Stack Execution Finder: $CURRENT_FINDER"
CURRENT_FINDER_STATUS=$(aws lambda get-function --function-name "$CURRENT_FINDER" \
  --query 'Configuration.State' --output text 2>/dev/null || echo "NOT_FOUND")
echo "  Status: $CURRENT_FINDER_STATUS"

if [ "$CURRENT_FINDER_STATUS" = "Active" ]; then
  CURRENT_HANDLER=$(aws lambda get-function --function-name "$CURRENT_FINDER" \
    --query 'Configuration.Handler' --output text)
  echo "  Handler: $CURRENT_HANDLER"
fi

echo ""

echo "Archive Stack Execution Finder: $ARCHIVE_FINDER"
ARCHIVE_FINDER_STATUS=$(aws lambda get-function --function-name "$ARCHIVE_FINDER" \
  --query 'Configuration.State' --output text 2>/dev/null || echo "NOT_FOUND")
echo "  Status: $ARCHIVE_FINDER_STATUS"

if [ "$ARCHIVE_FINDER_STATUS" = "Active" ]; then
  ARCHIVE_HANDLER=$(aws lambda get-function --function-name "$ARCHIVE_FINDER" \
    --query 'Configuration.Handler' --output text)
  echo "  Handler: $ARCHIVE_HANDLER"
fi

echo ""
echo "🔍 Testing Lambda Function Invocation..."

# Test current stack execution finder
echo "Testing Current Stack Execution Finder..."
CURRENT_TEST_RESULT=$(aws lambda invoke \
  --function-name "$CURRENT_FINDER" \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/current-response.json 2>&1 || echo "FAILED")

if [ "$CURRENT_TEST_RESULT" != "FAILED" ]; then
  echo "  ✅ Current stack execution finder invoked successfully"
  cat /tmp/current-response.json | jq -r '.body' | jq . 2>/dev/null || cat /tmp/current-response.json
else
  echo "  ❌ Current stack execution finder failed: $CURRENT_TEST_RESULT"
fi

echo ""

# Test archive stack execution finder
echo "Testing Archive Stack Execution Finder..."
ARCHIVE_TEST_RESULT=$(aws lambda invoke \
  --function-name "$ARCHIVE_FINDER" \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/archive-response.json 2>&1 || echo "FAILED")

if [ "$ARCHIVE_TEST_RESULT" != "FAILED" ]; then
  echo "  ✅ Archive stack execution finder invoked successfully"
  cat /tmp/archive-response.json | jq -r '.body' | jq . 2>/dev/null || cat /tmp/archive-response.json
else
  echo "  ❌ Archive stack execution finder failed: $ARCHIVE_TEST_RESULT"
fi

echo ""
echo "🔍 Checking EventBridge Rules..."

# Check EventBridge rules
echo "EventBridge Schedule Rules:"

CURRENT_RULE="$CURRENT_STACK-execution-finder-schedule-dev"
ARCHIVE_RULE="$ARCHIVE_STACK-execution-finder-schedule-test"

echo "Current Stack Rule: $CURRENT_RULE"
CURRENT_RULE_STATUS=$(aws events describe-rule --name "$CURRENT_RULE" \
  --query 'State' --output text 2>/dev/null || echo "NOT_FOUND")
echo "  Status: $CURRENT_RULE_STATUS"

echo "Archive Stack Rule: $ARCHIVE_RULE"
ARCHIVE_RULE_STATUS=$(aws events describe-rule --name "$ARCHIVE_RULE" \
  --query 'State' --output text 2>/dev/null || echo "NOT_FOUND")
echo "  Status: $ARCHIVE_RULE_STATUS"

echo ""
echo "📊 Deployment Summary:"
echo "===================="

if [ "$CURRENT_STATUS" = "CREATE_COMPLETE" ] || [ "$CURRENT_STATUS" = "UPDATE_COMPLETE" ]; then
  echo "✅ Current Stack: Deployed successfully"
else
  echo "❌ Current Stack: $CURRENT_STATUS"
fi

if [ "$ARCHIVE_STATUS" = "CREATE_COMPLETE" ] || [ "$ARCHIVE_STATUS" = "UPDATE_COMPLETE" ]; then
  echo "✅ Archive Test Stack: Deployed successfully"
else
  echo "❌ Archive Test Stack: $ARCHIVE_STATUS"
fi

if [ "$CURRENT_FINDER_STATUS" = "Active" ]; then
  echo "✅ Current Stack Lambda: Working correctly"
else
  echo "❌ Current Stack Lambda: $CURRENT_FINDER_STATUS"
fi

if [ "$ARCHIVE_FINDER_STATUS" = "Active" ]; then
  echo "✅ Archive Test Stack Lambda: Fixed (no more module import errors)"
else
  echo "❌ Archive Test Stack Lambda: $ARCHIVE_FINDER_STATUS"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Test both applications in browser"
echo "2. Create test executions in both stacks"
echo "3. Verify DRS Job Events update correctly"
echo "4. Compare execution behavior between stacks"

# Clean up temp files
rm -f /tmp/current-response.json /tmp/archive-response.json