#!/bin/bash
# Fix SNS notifications by redeploying the stack with EnablePipelineNotifications=true
# This script gets current parameters and redeploys with notifications enabled

set -e
export AWS_PAGER=""

STACK_NAME="aws-elasticdrs-orchestrator-dev"
REGION="us-east-1"
BUCKET="aws-elasticdrs-orchestrator"

echo "🔔 Fixing SNS notifications for stack: $STACK_NAME"
echo ""

# First, sync the latest templates to S3
echo "📦 Syncing latest CloudFormation templates to S3..."
aws s3 sync cfn/ s3://$BUCKET/cfn/ --delete --no-cli-pager 2>/dev/null
echo "✅ Templates synced to S3"
echo ""

# Deploy the stack with notifications enabled
echo "🚀 Deploying stack with SNS notifications enabled..."
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=aws-elasticdrs-orchestrator \
    Environment=dev \
    SourceBucket=aws-elasticdrs-orchestrator \
    AdminEmail=jocousen@amazon.com \
    CognitoDomainPrefix=aws-elasticdrs-orchestrator-dev \
    NotificationEmail=jocousen@amazon.com \
    EnablePipelineNotifications=true \
  --no-fail-on-empty-changeset \
  --no-cli-pager 2>/dev/null

echo "✅ Stack deployment completed"
echo ""

# Verify SNS topic was created
echo "🔍 Verifying SNS topic creation..."
sleep 10  # Wait for resources to be fully created

TOPIC_ARN=$(aws sns list-topics --region "$REGION" 2>/dev/null | grep -o "arn:aws:sns:.*pipeline-notifications.*" | head -1 || echo "")

if [ -n "$TOPIC_ARN" ]; then
  echo "✅ SNS topic created: $TOPIC_ARN"
  
  # Check subscription
  echo "📧 Checking email subscription..."
  SUBSCRIPTION=$(aws sns list-subscriptions-by-topic --topic-arn "$TOPIC_ARN" --region "$REGION" 2>/dev/null | grep -o "jocousen@amazon.com" || echo "")
  
  if [ -n "$SUBSCRIPTION" ]; then
    echo "✅ Email subscription found for: jocousen@amazon.com"
  else
    echo "⚠️  Email subscription may be pending confirmation"
  fi
  
  echo ""
  echo "🎉 SNS notifications are now enabled!"
  echo ""
  echo "📋 You should receive email notifications for:"
  echo "  ✉️  CodePipeline failures"
  echo "  ✉️  Security scan failures" 
  echo "  ✉️  Build failures"
  echo ""
  echo "📬 Check your email (jocousen@amazon.com) for:"
  echo "  1. SNS subscription confirmation (if not already confirmed)"
  echo "  2. Test notifications from pipeline events"
  
else
  echo "❌ SNS topic not found"
  echo "Checking CloudFormation events for errors..."
  aws cloudformation describe-stack-events \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`].[Timestamp,ResourceType,ResourceStatus,ResourceStatusReason]' \
    --output table \
    --no-cli-pager 2>/dev/null | head -10
fi

echo ""
echo "🔧 To test notifications, trigger a pipeline failure or check CloudWatch Events"