#!/bin/bash
# Enable SNS notifications for the AWS DRS Orchestration stack
# This updates the existing stack to enable pipeline notifications

set -e
export AWS_PAGER=""

STACK_NAME="aws-elasticdrs-orchestrator-dev"
REGION="us-east-1"

echo "🔔 Enabling SNS notifications for stack: $STACK_NAME"
echo "📧 Admin email: jocousen@amazon.com"
echo ""

# Update the stack with EnablePipelineNotifications=true
echo "Updating CloudFormation stack to enable notifications..."
aws cloudformation update-stack \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --use-previous-template \
  --parameters \
    ParameterKey=EnablePipelineNotifications,ParameterValue=true \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --no-cli-pager 2>/dev/null || {
    echo "❌ Stack update failed or no changes needed"
    echo "Checking if notifications are already enabled..."
    
    # Check if SNS topic exists
    if aws sns list-topics --region "$REGION" 2>/dev/null | grep -q "pipeline-notifications"; then
      echo "✅ SNS notifications are already enabled"
    else
      echo "❌ SNS notifications are not enabled"
      echo "The stack may need to be deployed with the EnablePipelineNotifications parameter"
    fi
    exit 1
  }

echo "✅ Stack update initiated successfully"
echo ""
echo "Waiting for stack update to complete..."
aws cloudformation wait stack-update-complete \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --no-cli-pager

echo "✅ Stack update completed successfully"
echo ""

# Verify SNS topic was created
echo "Verifying SNS topic creation..."
TOPIC_ARN=$(aws sns list-topics --region "$REGION" 2>/dev/null | grep -o "arn:aws:sns:.*pipeline-notifications.*" | head -1)

if [ -n "$TOPIC_ARN" ]; then
  echo "✅ SNS topic created: $TOPIC_ARN"
  
  # Check subscription
  SUBSCRIPTION=$(aws sns list-subscriptions-by-topic --topic-arn "$TOPIC_ARN" --region "$REGION" 2>/dev/null | grep -o "jocousen@amazon.com" || echo "")
  
  if [ -n "$SUBSCRIPTION" ]; then
    echo "✅ Email subscription confirmed for: jocousen@amazon.com"
    echo ""
    echo "🎉 SNS notifications are now enabled!"
    echo "You should receive email notifications for:"
    echo "  - CodePipeline failures"
    echo "  - Security scan failures"
    echo "  - Build failures"
  else
    echo "⚠️  Email subscription pending confirmation"
    echo "Check your email (jocousen@amazon.com) for a confirmation message"
  fi
else
  echo "❌ SNS topic not found - there may have been an issue with the deployment"
fi

echo ""
echo "📋 Next steps:"
echo "1. Check your email for SNS subscription confirmation"
echo "2. Trigger a pipeline failure to test notifications"
echo "3. Monitor CloudWatch Events for notification delivery"