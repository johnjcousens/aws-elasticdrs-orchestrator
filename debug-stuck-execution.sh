#!/bin/bash

# Debug script for stuck DRS execution
# Usage: ./debug-stuck-execution.sh [execution-id]

set -e

EXECUTION_ID=${1:-""}
REGION="us-east-1"

if [ -z "$EXECUTION_ID" ]; then
    echo "❌ Please provide execution ID as argument"
    echo "Usage: ./debug-stuck-execution.sh <execution-id>"
    exit 1
fi

echo "🔍 Debugging stuck execution: $EXECUTION_ID"
echo "=================================="

# 1. Check execution status in DynamoDB
echo "📊 Checking execution status in DynamoDB..."
AWS_PAGER="" aws dynamodb query \
    --table-name drsorchv4-execution-history-test \
    --key-condition-expression "ExecutionId = :eid" \
    --expression-attribute-values '{":eid": {"S": "'$EXECUTION_ID'"}}' \
    --query 'Items[0].{Status:Status.S,CurrentWave:CurrentWave.N,TaskToken:TaskToken.S}' \
    --region $REGION

# 2. Check Step Functions execution
echo ""
echo "🔄 Checking Step Functions execution..."
SF_ARN=$(aws cloudformation describe-stacks \
    --stack-name drs-orch-v4 \
    --query 'Stacks[0].Outputs[?OutputKey==`StepFunctionArn`].OutputValue' \
    --output text --region $REGION)

if [ ! -z "$SF_ARN" ]; then
    EXEC_ARN="${SF_ARN}:${EXECUTION_ID}"
    AWS_PAGER="" aws stepfunctions describe-execution \
        --execution-arn "$EXEC_ARN" \
        --query '{Status:status,StartDate:startDate,Input:input}' \
        --region $REGION
else
    echo "❌ Could not find Step Functions ARN"
fi

# 3. Check recent Lambda logs
echo ""
echo "📝 Checking recent orchestration Lambda logs..."
AWS_PAGER="" aws logs filter-log-events \
    --log-group-name "/aws/lambda/drsorchv4-orchestration-stepfunctions-test" \
    --start-time $(date -d '10 minutes ago' +%s)000 \
    --filter-pattern "$EXECUTION_ID" \
    --query 'events[0:5].message' \
    --region $REGION

# 4. Check for DRS jobs in us-west-2
echo ""
echo "🏥 Checking DRS jobs in us-west-2..."
AWS_PAGER="" aws drs describe-jobs \
    --filters jobIDs= \
    --max-results 5 \
    --query 'items[0:3].{JobID:jobID,Status:status,Type:type,CreationDateTime:creationDateTime}' \
    --region us-west-2

echo ""
echo "✅ Debug complete. Check the output above for issues."