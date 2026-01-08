#!/bin/bash

# Mark stuck execution as FAILED in DynamoDB
EXECUTION_ID="ac0bc68e-31e1-4530-8f3e-216fe1600dd3"
PLAN_ID="3TierRecoveryPlanCreatedInUIBasedOnTags"
END_TIME=$(date +%s)

echo "🛑 Marking execution $EXECUTION_ID as FAILED in DynamoDB..."

aws dynamodb update-item \
  --table-name execution-history-dev \
  --key "{\"ExecutionId\": {\"S\": \"$EXECUTION_ID\"}, \"PlanId\": {\"S\": \"$PLAN_ID\"}}" \
  --update-expression "SET #status = :status, EndTime = :end" \
  --expression-attribute-names "{\"#status\": \"Status\"}" \
  --expression-attribute-values "{\":status\": {\"S\": \"FAILED\"}, \":end\": {\"N\": \"$END_TIME\"}}" \
  --region us-east-1

echo "✅ Execution marked as FAILED"