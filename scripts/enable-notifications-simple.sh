#!/bin/bash
# Simple script to enable SNS notifications by updating stack parameter

# Load deployment configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/load-deployment-config.sh"

export AWS_PAGER=""

echo "🔔 Enabling SNS notifications for stack: $STACK_NAME"

# Update just the EnablePipelineNotifications parameter
aws cloudformation update-stack \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --use-previous-template \
  --parameters \
    ParameterKey=ProjectName,UsePreviousValue=true \
    ParameterKey=Environment,UsePreviousValue=true \
    ParameterKey=SourceBucket,UsePreviousValue=true \
    ParameterKey=AdminEmail,UsePreviousValue=true \
    ParameterKey=CognitoDomainPrefix,UsePreviousValue=true \
    ParameterKey=NotificationEmail,UsePreviousValue=true \
    ParameterKey=EnableWAF,UsePreviousValue=true \
    ParameterKey=EnableCloudTrail,UsePreviousValue=true \
    ParameterKey=EnableSecretsManager,UsePreviousValue=true \
    ParameterKey=CrossAccountRoleName,UsePreviousValue=true \
    ParameterKey=EnableTagSync,UsePreviousValue=true \
    ParameterKey=TagSyncIntervalHours,UsePreviousValue=true \
    ParameterKey=EnablePipelineNotifications,ParameterValue=true \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

echo "✅ Stack update initiated"
echo "⏳ Waiting for completion..."

aws cloudformation wait stack-update-complete \
  --stack-name "$STACK_NAME" \
  --region "$REGION"

echo "✅ Stack update completed"
echo "🔍 Checking SNS topic..."

# Check if SNS topic was created
if aws sns list-topics --region "$REGION" | grep -q pipeline-notifications; then
  echo "✅ SNS notifications enabled successfully"
  echo "📧 Check email for subscription confirmation"
else
  echo "❌ SNS topic not found - check CloudFormation events"
fi