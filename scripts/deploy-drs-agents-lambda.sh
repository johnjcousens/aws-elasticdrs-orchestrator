#!/bin/bash

# Deploy DRS Agents via Lambda Function
#
# This script invokes the DRS Agent Deployer Lambda function to install
# DRS agents on EC2 instances in target AWS accounts.
#
# Usage:
#   ./deploy-drs-agents-lambda.sh [account_id] [source_region] [target_region]
#
# Examples:
#   ./deploy-drs-agents-lambda.sh 111122223333
#   ./deploy-drs-agents-lambda.sh 111122223333 us-east-1 us-west-2
#   ./deploy-drs-agents-lambda.sh 444455556666 us-east-1 eu-west-1

set -e

# Parse parameters
ACCOUNT_ID="${1}"
SOURCE_REGION="${2:-us-east-1}"
TARGET_REGION="${3:-us-west-2}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
PROJECT_NAME="${PROJECT_NAME:-hrp-drs-tech-adapter}"

# Show help if no account ID provided
if [ -z "$ACCOUNT_ID" ]; then
  echo "Usage: $0 <account_id> [source_region] [target_region]"
  echo ""
  echo "Examples:"
  echo "  $0 111122223333"
  echo "  $0 111122223333 us-east-1 us-west-2"
  echo "  $0 444455556666 us-east-1 eu-west-1"
  echo ""
  echo "Environment variables:"
  echo "  ENVIRONMENT - Environment name (default: dev)"
  echo "  PROJECT_NAME - Project name (default: hrp-drs-tech-adapter)"
  exit 1
fi

FUNCTION_NAME="${PROJECT_NAME}-drs-agent-deployer-${ENVIRONMENT}"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT_NAME}-cross-account-role"

echo "=========================================="
echo "DRS Agent Deployment via Lambda"
echo "=========================================="
echo "Account ID: $ACCOUNT_ID"
echo "Source Region: $SOURCE_REGION"
echo "Target Region: $TARGET_REGION"
echo "Lambda Function: $FUNCTION_NAME"
echo "Cross-Account Role: $ROLE_ARN"
echo ""

# Create event payload
EVENT_FILE=$(mktemp)
cat > "$EVENT_FILE" << EOF
{
  "account_id": "$ACCOUNT_ID",
  "source_region": "$SOURCE_REGION",
  "target_region": "$TARGET_REGION",
  "role_arn": "$ROLE_ARN",
  "external_id": "DRSOrchestration2024",
  "wait_for_completion": true,
  "timeout_seconds": 600
}
EOF

echo "Event payload:"
cat "$EVENT_FILE" | jq .
echo ""

# Invoke Lambda function
echo "Invoking Lambda function..."
RESPONSE_FILE=$(mktemp)

AWS_PAGER="" aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --payload file://"$EVENT_FILE" \
  "$RESPONSE_FILE" \
  --log-type Tail \
  --query 'LogResult' \
  --output text | base64 -d

echo ""
echo "=========================================="
echo "Deployment Results"
echo "=========================================="
echo ""

# Parse and display results
cat "$RESPONSE_FILE" | jq .

# Check status
STATUS=$(cat "$RESPONSE_FILE" | jq -r '.body' | jq -r '.status' 2>/dev/null || echo "unknown")

if [ "$STATUS" == "success" ]; then
  echo ""
  echo "✅ Deployment successful!"
  
  # Extract key metrics
  INSTANCES_DEPLOYED=$(cat "$RESPONSE_FILE" | jq -r '.body' | jq -r '.instances_deployed' 2>/dev/null || echo "0")
  SOURCE_SERVERS=$(cat "$RESPONSE_FILE" | jq -r '.body' | jq -r '.source_servers | length' 2>/dev/null || echo "0")
  DURATION=$(cat "$RESPONSE_FILE" | jq -r '.body' | jq -r '.duration_seconds' 2>/dev/null || echo "0")
  
  echo ""
  echo "Summary:"
  echo "  Instances Deployed: $INSTANCES_DEPLOYED"
  echo "  Source Servers Registered: $SOURCE_SERVERS"
  echo "  Duration: ${DURATION}s"
  echo ""
  echo "Next steps:"
  echo "  1. Monitor DRS console: https://$TARGET_REGION.console.aws.amazon.com/drs/home?region=$TARGET_REGION#/sourceServers"
  echo "  2. Wait for INITIAL_SYNC to complete"
  echo "  3. Configure launch settings"
  echo "  4. Test recovery when ready"
else
  echo ""
  echo "❌ Deployment failed or incomplete"
  echo "Status: $STATUS"
  echo ""
  echo "Check Lambda logs:"
  echo "  aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
fi

# Cleanup
rm -f "$EVENT_FILE" "$RESPONSE_FILE"

echo ""
