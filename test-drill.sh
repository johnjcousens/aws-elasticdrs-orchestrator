#!/bin/bash
# Test drill execution through Step Functions

PLAN_ID="$1"

if [ -z "$PLAN_ID" ]; then
    echo "Usage: $0 <plan-id>"
    echo ""
    echo "Available plans:"
    aws dynamodb scan --table-name recovery-plans-dev --region us-east-1 \
        --query 'Items[*].[PlanId.S,PlanName.S]' --output text
    exit 1
fi

STATE_MACHINE_ARN=$(aws stepfunctions list-state-machines --region us-east-1 \
    --query 'stateMachines[?name==`drs-orchestration-orchestration-dev`].stateMachineArn' \
    --output text)

echo "Starting drill execution for plan: $PLAN_ID"
echo "State machine: $STATE_MACHINE_ARN"

EXECUTION_NAME="test-drill-$(date +%s)"

aws stepfunctions start-execution \
    --state-machine-arn "$STATE_MACHINE_ARN" \
    --name "$EXECUTION_NAME" \
    --input "{\"planId\":\"$PLAN_ID\",\"isDrill\":true}" \
    --region us-east-1

echo ""
echo "Execution started: $EXECUTION_NAME"
echo ""
echo "Monitor with:"
echo "  aws stepfunctions describe-execution --execution-arn ${STATE_MACHINE_ARN/:stateMachine:/:execution:}:${EXECUTION_NAME} --region us-east-1"
echo ""
echo "View logs:"
echo "  aws logs tail /aws/lambda/drs-orchestration-orchestration-dev --region us-east-1 --follow"
