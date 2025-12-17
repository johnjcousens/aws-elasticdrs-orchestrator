#!/bin/bash

# Check recent Lambda logs for debugging output
echo "🔍 Checking Lambda logs for hardware debugging..."

AWS_PAGER="" aws logs tail /aws/lambda/drs-orchestration-api-handler-dev \
  --since 2m \
  --region us-west-2 \
  --filter-pattern "DEBUG" \
  --format short

echo ""
echo "🔍 Checking for any errors..."
AWS_PAGER="" aws logs tail /aws/lambda/drs-orchestration-api-handler-dev \
  --since 2m \
  --region us-west-2 \
  --filter-pattern "ERROR" \
  --format short