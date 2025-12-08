# Step Functions CloudFormation Fix Analysis

**Issue:** Step Functions still not working after redeployment  
**Root Cause:** CloudFormation is passing the wrong Lambda ARN to Step Functions  

## The Problem

### What CloudFormation Currently Does
```yaml
# cfn/master-template.yaml (Current)
StepFunctionsStack:
  Parameters:
    OrchestrationLambdaArn: !GetAtt LambdaStack.Outputs.OrchestrationStepFunctionsFunctionArn
```

### What Step Functions Expects
```yaml
# cfn/step-functions-stack.yaml
InitiateWavePlan:
  Parameters:
    FunctionName: !Ref OrchestrationLambdaArn  # This gets the ARN from master template
    Payload:
      action: 'begin'  # Expects handler that understands 'begin' action
```

## The Issue: Lambda Function Mismatch

**CloudFormation passes:** `OrchestrationStepFunctionsFunctionArn` (the working Lambda)  
**But Step Functions calls:** Whatever ARN is passed, which should be the working one  

**The real issue:** Your locally deployed Lambda has the working code, but CloudFormation might be calling a different function or the function isn't getting the right parameters.

## Verification Steps

### 1. Check What Lambda Step Functions Is Actually Calling

```bash
# Get the Step Functions state machine definition
aws stepfunctions describe-state-machine \
  --state-machine-arn "arn:aws:states:us-east-1:***REMOVED***:stateMachine:drs-orchestration-state-machine-dev" \
  --region us-east-1 \
  --query 'definition' --output text | jq '.States.InitiateWavePlan.Parameters.FunctionName'
```

### 2. Check What Lambda Functions Exist

```bash
# List all orchestration functions
aws lambda list-functions --region us-east-1 | grep -E "(orchestration|stepfunctions)" | grep FunctionName
```

### 3. Test the Lambda Directly

```bash
# Test the Lambda that Step Functions should call
aws lambda invoke \
  --function-name drs-orchestration-orchestration-stepfunctions-dev \
  --payload '{"action":"begin","execution":"test","plan":{"PlanId":"test"},"isDrill":true}' \
  --region us-east-1 \
  response.json && cat response.json
```

## Likely Issues and Fixes

### Issue 1: Step Functions Calling Wrong Lambda

**Check current state machine:**
```bash
aws stepfunctions describe-state-machine \
  --state-machine-arn $(aws stepfunctions list-state-machines --region us-east-1 --query 'stateMachines[?name==`drs-orchestration-state-machine-dev`].stateMachineArn' --output text) \
  --region us-east-1
```

**If it's calling the wrong function, update CloudFormation:**
```yaml
# Fix in cfn/master-template.yaml - change from:
OrchestrationLambdaArn: !GetAtt LambdaStack.Outputs.OrchestrationStepFunctionsFunctionArn

# To (if needed):
OrchestrationLambdaArn: !GetAtt LambdaStack.Outputs.OrchestrationFunctionArn
```

### Issue 2: Lambda Function Not Deployed to Step Functions Function

**The working code was deployed to:** `drs-orchestration-orchestration-dev`  
**But Step Functions might expect:** `drs-orchestration-orchestration-stepfunctions-dev`

**Fix: Deploy to the correct function:**
```bash
aws lambda update-function-code \
  --function-name drs-orchestration-orchestration-stepfunctions-dev \
  --zip-file fileb://lambda/orchestration.zip \
  --region us-east-1
```

### Issue 3: Handler Function Name Mismatch

**Check the handler configuration:**
```bash
aws lambda get-function-configuration \
  --function-name drs-orchestration-orchestration-stepfunctions-dev \
  --region us-east-1 \
  --query 'Handler'
```

**Should be:** `orchestration_stepfunctions.handler` (for the stepfunctions version)  
**Or:** `drs_orchestrator.lambda_handler` (for the main version)

## Recommended Fix Strategy

### Option 1: Use Main Orchestration Function (Simplest)

**Update CloudFormation to use the main orchestration function:**
```yaml
# cfn/master-template.yaml
StepFunctionsStack:
  Parameters:
    OrchestrationLambdaArn: !GetAtt LambdaStack.Outputs.OrchestrationFunctionArn  # Use main function
```

**Then redeploy CloudFormation:**
```bash
aws cloudformation update-stack \
  --stack-name drs-orchestration-dev \
  --use-previous-template \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Option 2: Deploy to Step Functions Lambda (Current Approach)

**Deploy working code to the Step Functions Lambda:**
```bash
aws lambda update-function-code \
  --function-name drs-orchestration-orchestration-stepfunctions-dev \
  --zip-file fileb://lambda/orchestration.zip \
  --region us-east-1
```

## Testing the Fix

**After applying the fix, test Step Functions:**
```bash
# Start a test execution
aws stepfunctions start-execution \
  --state-machine-arn $(aws stepfunctions list-state-machines --region us-east-1 --query 'stateMachines[?name==`drs-orchestration-state-machine-dev`].stateMachineArn' --output text) \
  --input '{"Plan":{"PlanId":"test","Waves":[]},"IsDrill":true}' \
  --region us-east-1
```

## Summary

The issue is likely that:
1. **Working code deployed to:** `drs-orchestration-orchestration-dev`
2. **Step Functions expects:** `drs-orchestration-orchestration-stepfunctions-dev`
3. **CloudFormation passes:** The stepfunctions ARN but it has old/wrong code

**Quick fix:** Deploy your working Lambda code to the stepfunctions function that CloudFormation is actually referencing.