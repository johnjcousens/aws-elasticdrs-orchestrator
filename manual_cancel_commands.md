# Manual Commands to Cancel Stuck Execution

## Option 1: Via API (Recommended)

```bash
# Get JWT token
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id ***REMOVED*** \
  --client-id ***REMOVED*** \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=***REMOVED***,PASSWORD=***REMOVED*** \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Cancel the execution
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "https://***REMOVED***.execute-api.us-east-1.amazonaws.com/dev/executions/ac0bc68e-31e1-4530-8f3e-216fe1600dd3/cancel"
```

## Option 2: Direct DynamoDB Update

```bash
# Update execution status to CANCELLED in DynamoDB
aws dynamodb update-item \
  --table-name execution-history-dev \
  --key '{"ExecutionId": {"S": "ac0bc68e-31e1-4530-8f3e-216fe1600dd3"}, "PlanId": {"S": "3TierRecoveryPlanCreatedInUIBasedOnTags"}}' \
  --update-expression "SET #status = :status, EndTime = :end" \
  --expression-attribute-names '{"#status": "Status"}' \
  --expression-attribute-values '{":status": {"S": "CANCELLED"}, ":end": {"N": "1736374800"}}' \
  --region us-east-1
```

## Option 3: Stop Step Functions Execution

```bash
# Find the Step Functions execution ARN
aws stepfunctions list-executions \
  --state-machine-arn "arn:aws:states:us-east-1:***REMOVED***:stateMachine:aws-elasticdrs-orchestrator-orchestration-dev" \
  --status-filter RUNNING \
  --region us-east-1

# Stop the execution (replace EXECUTION_ARN with actual ARN from above)
aws stepfunctions stop-execution \
  --execution-arn "EXECUTION_ARN" \
  --region us-east-1
```

## Option 4: Frontend Cancel Button

If the frontend is accessible:
1. Go to the Executions page
2. Find execution `ac0bc68e-31e1-4530-8f3e-216fe1600dd3`
3. Click the "Cancel" button

The execution should be terminated and marked as CANCELLED.