# Orchestration Integration Guide

This guide explains how to integrate AWS DRS Orchestration into larger automation workflows without using the web frontend. The solution provides a complete REST API that can be called from CLI scripts, SSM Automation, Step Functions, EventBridge schedules, or any HTTP client.

## Table of Contents

1. [Authentication](#authentication)
   - [Method 1: User Credentials](#method-1-user-credentials-interactive)
   - [Method 2: Service Account](#method-2-service-account-automation)
   - [Method 3: IAM Role-Based (AWS-Native)](#method-3-iam-role-based-authentication-aws-native)
2. [API Endpoints Reference](#api-endpoints-reference)
3. [CLI Integration](#cli-integration)
4. [SSM Automation Integration](#ssm-automation-integration)
5. [Step Functions Integration](#step-functions-integration)
6. [EventBridge Scheduled Execution](#eventbridge-scheduled-execution)
7. [Python SDK Examples](#python-sdk-examples)
8. [Bash Script Examples](#bash-script-examples)
9. [Error Handling](#error-handling)
10. [Best Practices](#best-practices)

---

## Authentication

All API calls require a valid Cognito JWT token. There are two authentication methods:

### Method 1: User Credentials (Interactive)

```bash
# Get token using username/password
TOKEN=$(aws cognito-idp initiate-auth \
  --client-id ${COGNITO_CLIENT_ID} \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=${USERNAME},PASSWORD=${PASSWORD} \
  --query 'AuthenticationResult.IdToken' \
  --output text)
```

### Method 2: Service Account (Automation)

For automated workflows, create a dedicated service account in Cognito:

```bash
# Create service account (one-time setup)
aws cognito-idp admin-create-user \
  --user-pool-id ${USER_POOL_ID} \
  --username dr-automation@example.com \
  --user-attributes Name=email,Value=dr-automation@example.com \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id ${USER_POOL_ID} \
  --username dr-automation@example.com \
  --password "${SERVICE_ACCOUNT_PASSWORD}" \
  --permanent
```

### Method 3: IAM Role-Based Authentication (AWS-Native)

For AWS-native integrations (Lambda, Step Functions, SSM, EventBridge), you can bypass Cognito entirely by invoking the Lambda function directly using IAM roles. This is the recommended approach for automated AWS workflows.

#### Direct Lambda Invocation

Instead of calling API Gateway (which requires Cognito tokens), invoke the Lambda function directly:

```bash
# Direct Lambda invocation (no Cognito token needed)
AWS_PAGER="" aws lambda invoke \
  --function-name drs-orchestration-api-handler-dev \
  --payload '{"httpMethod":"GET","path":"/recovery-plans"}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/response.json \
  --region us-east-1

cat /tmp/response.json | jq -r '.body' | jq .
```

#### IAM Policy for Direct Lambda Invocation

Create an IAM policy that allows invoking the Lambda function:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": [
        "arn:aws:lambda:us-east-1:*:function:drs-orchestration-api-handler-*",
        "arn:aws:lambda:us-east-1:*:function:drs-orchestration-orchestration-*"
      ]
    }
  ]
}
```

#### Lambda Event Format

When invoking Lambda directly, use this event format (mimics API Gateway):

```json
{
  "httpMethod": "POST",
  "path": "/executions",
  "headers": {},
  "queryStringParameters": null,
  "body": "{\"recoveryPlanId\":\"xxx\",\"executionType\":\"DRILL\",\"initiatedBy\":\"iam-role\"}"
}
```

#### Python Example - Direct Lambda Invocation

```python
import boto3
import json

def invoke_drs_api(method: str, path: str, body: dict = None, query_params: dict = None) -> dict:
    """Invoke DRS Orchestration Lambda directly using IAM credentials"""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    event = {
        'httpMethod': method,
        'path': path,
        'headers': {},
        'queryStringParameters': query_params,
        'body': json.dumps(body) if body else None
    }
    
    response = lambda_client.invoke(
        FunctionName='drs-orchestration-api-handler-dev',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    
    result = json.loads(response['Payload'].read())
    
    # Parse the Lambda response (API Gateway format)
    if 'statusCode' in result:
        if result['statusCode'] >= 400:
            raise Exception(f"API Error {result['statusCode']}: {result.get('body', 'Unknown error')}")
        return json.loads(result.get('body', '{}'))
    
    return result

# Usage examples
# List recovery plans
plans = invoke_drs_api('GET', '/recovery-plans')
print(f"Found {len(plans.get('plans', []))} plans")

# Find plan by name
plans = invoke_drs_api('GET', '/recovery-plans', query_params={'nameExact': '2-Tier Recovery'})

# Start execution
execution = invoke_drs_api('POST', '/executions', body={
    'recoveryPlanId': 'xxx-xxx-xxx',
    'executionType': 'DRILL',
    'initiatedBy': 'iam-automation',
    'invocationSource': 'LAMBDA'
})
print(f"Started execution: {execution.get('ExecutionId')}")

# Check execution status
status = invoke_drs_api('GET', f"/executions/{execution.get('ExecutionId')}")
print(f"Status: {status.get('status')}")
```

#### Bash Example - Direct Lambda Invocation

```bash
#!/bin/bash
# Direct Lambda invocation without Cognito authentication

FUNCTION_NAME="drs-orchestration-api-handler-dev"
REGION="us-east-1"

# Function to invoke Lambda directly
invoke_lambda() {
    local method=$1
    local path=$2
    local body=$3
    
    local payload
    if [ -n "$body" ]; then
        payload=$(jq -n --arg m "$method" --arg p "$path" --arg b "$body" \
            '{httpMethod: $m, path: $p, headers: {}, queryStringParameters: null, body: $b}')
    else
        payload=$(jq -n --arg m "$method" --arg p "$path" \
            '{httpMethod: $m, path: $p, headers: {}, queryStringParameters: null, body: null}')
    fi
    
    AWS_PAGER="" aws lambda invoke \
        --function-name "$FUNCTION_NAME" \
        --payload "$payload" \
        --cli-binary-format raw-in-base64-out \
        --region "$REGION" \
        /tmp/lambda_response.json > /dev/null 2>&1
    
    # Extract body from Lambda response
    jq -r '.body' /tmp/lambda_response.json | jq .
}

# List recovery plans
echo "=== Recovery Plans ==="
invoke_lambda "GET" "/recovery-plans"

# Start a drill execution
echo "=== Starting Drill ==="
PLAN_ID="your-plan-id-here"
invoke_lambda "POST" "/executions" "{\"recoveryPlanId\":\"${PLAN_ID}\",\"executionType\":\"DRILL\",\"initiatedBy\":\"bash-iam\"}"
```

#### Step Functions with Direct Lambda Invocation

```json
{
  "Comment": "DR Orchestration with IAM-based Lambda invocation",
  "StartAt": "ListRecoveryPlans",
  "States": {
    "ListRecoveryPlans": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "drs-orchestration-api-handler-dev",
        "Payload": {
          "httpMethod": "GET",
          "path": "/recovery-plans",
          "queryStringParameters": {
            "nameExact.$": "$.planName"
          }
        }
      },
      "ResultSelector": {
        "plans.$": "States.StringToJson($.Payload.body).plans"
      },
      "ResultPath": "$.planResult",
      "Next": "CheckPlanExists"
    },
    "CheckPlanExists": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.planResult.plans[0]",
          "IsPresent": true,
          "Next": "StartExecution"
        }
      ],
      "Default": "PlanNotFound"
    },
    "StartExecution": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "drs-orchestration-api-handler-dev",
        "Payload": {
          "httpMethod": "POST",
          "path": "/executions",
          "body.$": "States.JsonToString(States.JsonMerge($.executionConfig, States.StringToJson(States.Format('{\"recoveryPlanId\":\"{}\"}', $.planResult.plans[0].id))))"
        }
      },
      "ResultSelector": {
        "executionId.$": "States.StringToJson($.Payload.body).ExecutionId"
      },
      "ResultPath": "$.execution",
      "Next": "WaitAndPoll"
    },
    "WaitAndPoll": {
      "Type": "Wait",
      "Seconds": 30,
      "Next": "CheckStatus"
    },
    "CheckStatus": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "drs-orchestration-api-handler-dev",
        "Payload": {
          "httpMethod": "GET",
          "path.$": "States.Format('/executions/{}', $.execution.executionId)"
        }
      },
      "ResultSelector": {
        "status.$": "States.StringToJson($.Payload.body).status"
      },
      "ResultPath": "$.currentStatus",
      "Next": "EvaluateStatus"
    },
    "EvaluateStatus": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.currentStatus.status",
          "StringEquals": "completed",
          "Next": "Success"
        },
        {
          "Variable": "$.currentStatus.status",
          "StringEquals": "failed",
          "Next": "Failed"
        }
      ],
      "Default": "WaitAndPoll"
    },
    "Success": {
      "Type": "Succeed"
    },
    "Failed": {
      "Type": "Fail",
      "Error": "ExecutionFailed"
    },
    "PlanNotFound": {
      "Type": "Fail",
      "Error": "PlanNotFound"
    }
  }
}
```

#### SSM Automation with Direct Lambda Invocation

```yaml
# ssm-documents/drs-drill-iam-auth.yaml
schemaVersion: '0.3'
description: 'Execute DRS Drill using IAM authentication (no Cognito)'
assumeRole: '{{AutomationAssumeRole}}'
parameters:
  AutomationAssumeRole:
    type: String
    description: IAM role with lambda:InvokeFunction permission
  LambdaFunctionName:
    type: String
    default: drs-orchestration-api-handler-dev
  RecoveryPlanName:
    type: String
    description: Name of recovery plan to execute
  ExecutionType:
    type: String
    default: DRILL
    allowedValues: [DRILL, RECOVERY]

mainSteps:
  - name: FindRecoveryPlan
    action: aws:invokeLambdaFunction
    inputs:
      FunctionName: '{{LambdaFunctionName}}'
      Payload: |
        {
          "httpMethod": "GET",
          "path": "/recovery-plans",
          "queryStringParameters": {"nameExact": "{{RecoveryPlanName}}"}
        }
    outputs:
      - Name: PlanId
        Selector: $.Payload.body
        Type: String

  - name: ParsePlanId
    action: aws:executeScript
    inputs:
      Runtime: python3.9
      Handler: parse_plan
      Script: |
        import json
        def parse_plan(events, context):
            body = json.loads(events['PlanResponse'])
            plans = body.get('plans', [])
            if not plans:
                raise Exception('Recovery plan not found')
            return {'planId': plans[0]['id'], 'hasConflict': plans[0].get('hasServerConflict', False)}
      InputPayload:
        PlanResponse: '{{FindRecoveryPlan.PlanId}}'
    outputs:
      - Name: PlanId
        Selector: $.Payload.planId
        Type: String
      - Name: HasConflict
        Selector: $.Payload.hasConflict
        Type: Boolean

  - name: StartExecution
    action: aws:invokeLambdaFunction
    inputs:
      FunctionName: '{{LambdaFunctionName}}'
      Payload: |
        {
          "httpMethod": "POST",
          "path": "/executions",
          "body": "{\"recoveryPlanId\":\"{{ParsePlanId.PlanId}}\",\"executionType\":\"{{ExecutionType}}\",\"initiatedBy\":\"ssm-iam-auth\",\"invocationSource\":\"SSM\"}"
        }
    outputs:
      - Name: ExecutionId
        Selector: $.Payload.body
        Type: String

outputs:
  - ParsePlanId.PlanId
  - StartExecution.ExecutionId
```

#### When to Use Each Authentication Method

| Method | Use Case | Pros | Cons |
|--------|----------|------|------|
| **Cognito (User)** | Interactive/manual operations | User identity tracking | Requires password management |
| **Cognito (Service)** | External integrations, third-party tools | Works with any HTTP client | Token refresh needed |
| **IAM (Direct Lambda)** | AWS-native automation (Step Functions, SSM, EventBridge) | No token management, uses IAM roles | Only works within AWS |

#### Security Considerations for IAM-Based Access

1. **Use least-privilege IAM policies** - Only grant `lambda:InvokeFunction` for specific functions
2. **Use resource-based conditions** - Restrict by source account, VPC, or IP
3. **Enable CloudTrail** - All Lambda invocations are logged
4. **Use IAM roles** - Avoid long-lived credentials; use assumed roles

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:drs-orchestration-*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalAccount": "123456789012"
        }
      }
    }
  ]
}
```

#### Limitations and Restrictions

##### What IAM-Based Access CANNOT Do

| Limitation | Reason | Workaround |
|------------|--------|------------|
| **Cross-account without setup** | Lambda must allow cross-account invocation | Add resource-based policy to Lambda |
| **External/third-party tools** | Tools outside AWS can't use IAM roles directly | Use Cognito service account instead |
| **User identity tracking** | No Cognito user context in Lambda | Pass `initiatedBy` field in request body |
| **Rate limiting per user** | No user-level throttling | Implement custom throttling in Lambda |
| **Browser/frontend access** | Browsers can't assume IAM roles | Use Cognito for frontend authentication |

##### Cross-Account Invocation

To allow another AWS account to invoke the Lambda directly:

```bash
# Add resource-based policy to Lambda (run in the account that owns the Lambda)
aws lambda add-permission \
  --function-name drs-orchestration-api-handler-dev \
  --statement-id AllowCrossAccountInvoke \
  --action lambda:InvokeFunction \
  --principal 111122223333 \
  --region us-east-1
```

The calling account still needs an IAM policy allowing `lambda:InvokeFunction` on the target Lambda ARN.

##### What is NOT Allowed

| Action | Allowed? | Notes |
|--------|----------|-------|
| Direct Lambda invocation from same account | ✅ Yes | Requires IAM policy |
| Direct Lambda invocation from different account | ✅ Yes | Requires resource-based policy on Lambda |
| Direct Lambda invocation from outside AWS | ❌ No | Use API Gateway + Cognito |
| Invoking Lambda from browser JavaScript | ❌ No | Use API Gateway + Cognito |
| Bypassing DRS service limits | ❌ No | Lambda enforces DRS quotas regardless of auth method |
| Executing without valid recovery plan | ❌ No | API validates plan exists and has no conflicts |
| Starting execution with conflicting servers | ❌ No | Server conflict check applies to all auth methods |
| Deleting active executions | ❌ No | Must cancel first, then delete |
| Modifying completed executions | ❌ No | Execution history is immutable |

##### Edge Cases and Error Handling

| Scenario | Behavior | Recommended Action |
|----------|----------|-------------------|
| Lambda cold start | First invocation may take 1-3 seconds longer | Account for latency in timeouts |
| Lambda timeout (29 sec) | Request fails with timeout error | Break long operations into smaller calls |
| Concurrent execution limit | Throttling error (429) | Implement exponential backoff |
| Invalid event format | 400 Bad Request | Validate event structure before invoking |
| Missing required fields | 400 Bad Request with field details | Check API documentation for required fields |
| Plan has server conflicts | 409 Conflict | Query plan first, check `hasServerConflict` |
| Execution already running | 409 Conflict | Wait for completion or cancel existing |
| DRS quota exceeded | 400 Bad Request | Check `/drs/quotas` before starting |

##### Lambda Payload Size Limits

| Limit | Value | Impact |
|-------|-------|--------|
| Synchronous invocation payload | 6 MB | Request + response combined |
| Response payload | 6 MB | Large execution histories may be truncated |
| Event payload | 256 KB (async) | Use synchronous for larger payloads |

##### Required Event Fields by Operation

| Operation | Required Fields | Optional Fields |
|-----------|-----------------|-----------------|
| List resources | `httpMethod`, `path` | `queryStringParameters` |
| Get by ID | `httpMethod`, `path` (with ID) | - |
| Create | `httpMethod`, `path`, `body` | - |
| Update | `httpMethod`, `path` (with ID), `body` | - |
| Delete | `httpMethod`, `path` (with ID) | - |
| Start execution | `httpMethod`, `path`, `body.recoveryPlanId`, `body.executionType` | `body.initiatedBy`, `body.invocationSource` |

##### Troubleshooting IAM-Based Access

| Error | Cause | Solution |
|-------|-------|----------|
| `AccessDeniedException` | Missing `lambda:InvokeFunction` permission | Add IAM policy to calling role |
| `ResourceNotFoundException` | Wrong function name or region | Verify function name and region |
| `InvalidRequestContentException` | Malformed JSON payload | Validate JSON structure |
| `ServiceException` | Lambda internal error | Retry with exponential backoff |
| `TooManyRequestsException` | Throttled | Implement backoff, request limit increase |
| `KMSAccessDeniedException` | Lambda uses encrypted env vars | Grant KMS decrypt to calling role |

##### Audit and Compliance

All direct Lambda invocations are logged in CloudTrail:

```json
{
  "eventSource": "lambda.amazonaws.com",
  "eventName": "Invoke",
  "userIdentity": {
    "type": "AssumedRole",
    "arn": "arn:aws:sts::123456789012:assumed-role/MyRole/session"
  },
  "requestParameters": {
    "functionName": "drs-orchestration-api-handler-dev"
  }
}
```

To query CloudTrail for Lambda invocations:

```bash
AWS_PAGER="" aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=Invoke \
  --start-time $(date -u -v-1d +%Y-%m-%dT%H:%M:%SZ) \
  --query 'Events[?contains(CloudTrailEvent, `drs-orchestration`)].CloudTrailEvent' \
  --region us-east-1 | head -50
```

---

## API Endpoints Reference

Base URL: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}`

### Protection Groups

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/protection-groups` | List all protection groups |
| GET | `/protection-groups/{id}` | Get protection group by ID |
| POST | `/protection-groups` | Create protection group |
| PUT | `/protection-groups/{id}` | Update protection group |
| DELETE | `/protection-groups/{id}` | Delete protection group |
| POST | `/protection-groups/{id}/resolve` | Resolve servers from tags |

### Recovery Plans

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/recovery-plans` | List all recovery plans |
| GET | `/recovery-plans?name={partial}` | Filter by name (partial match) |
| GET | `/recovery-plans?nameExact={name}` | Filter by exact name |
| GET | `/recovery-plans?tag={key}={value}` | Filter by protection group tag |
| GET | `/recovery-plans?hasConflict=false` | Filter by conflict status |
| GET | `/recovery-plans?status={status}` | Filter by last execution status |
| GET | `/recovery-plans/{id}` | Get recovery plan by ID |
| POST | `/recovery-plans` | Create recovery plan |
| PUT | `/recovery-plans/{id}` | Update recovery plan |
| DELETE | `/recovery-plans/{id}` | Delete recovery plan |

### Executions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/executions` | List all executions |
| GET | `/executions/{id}` | Get execution details |
| POST | `/executions` | Start new execution |
| POST | `/executions/{id}/cancel` | Cancel execution |
| POST | `/executions/{id}/pause` | Pause execution |
| POST | `/executions/{id}/resume` | Resume paused execution |
| DELETE | `/executions/{id}` | Delete execution record |

### DRS Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/drs/source-servers?region={region}` | List DRS source servers |
| GET | `/drs/quotas?region={region}` | Get DRS service quotas |

---

## CLI Integration

### Environment Setup

```bash
# Set environment variables
export API_ENDPOINT="https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod"
export COGNITO_CLIENT_ID="xxxxxxxxxxxxxxxxxxxxxxxxxx"
export COGNITO_USER_POOL_ID="us-east-1_xxxxxxxxx"
export DR_USERNAME="dr-automation@example.com"
export DR_PASSWORD="YourSecurePassword123!"

# Function to get auth token
get_token() {
  aws cognito-idp initiate-auth \
    --client-id ${COGNITO_CLIENT_ID} \
    --auth-flow USER_PASSWORD_AUTH \
    --auth-parameters USERNAME=${DR_USERNAME},PASSWORD=${DR_PASSWORD} \
    --query 'AuthenticationResult.IdToken' \
    --output text
}

# Function to make authenticated API calls
api_call() {
  local method=$1
  local endpoint=$2
  local data=$3
  local token=$(get_token)
  
  if [ -n "$data" ]; then
    curl -s -X ${method} \
      -H "Authorization: Bearer ${token}" \
      -H "Content-Type: application/json" \
      -d "${data}" \
      "${API_ENDPOINT}${endpoint}"
  else
    curl -s -X ${method} \
      -H "Authorization: Bearer ${token}" \
      "${API_ENDPOINT}${endpoint}"
  fi
}
```

### Common CLI Operations

#### List Recovery Plans

```bash
# List all plans
api_call GET "/recovery-plans" | jq '.plans[] | {id, name, waveCount}'

# Find plan by name
api_call GET "/recovery-plans?nameExact=2-Tier%20Recovery" | jq '.plans[0]'

# Find plans with specific tag
api_call GET "/recovery-plans?tag=Purpose=DatabaseServers" | jq '.plans'

# Find plans ready to execute (no conflicts)
api_call GET "/recovery-plans?hasConflict=false" | jq '.plans[] | {id, name}'
```

#### Get Plan Details

```bash
# Get full plan details including waves
PLAN_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
api_call GET "/recovery-plans/${PLAN_ID}" | jq '.'
```

#### Start Execution

```bash
# Start a drill execution
PLAN_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
api_call POST "/executions" '{
  "recoveryPlanId": "'${PLAN_ID}'",
  "executionType": "DRILL",
  "initiatedBy": "cli-automation"
}'

# Start actual recovery
api_call POST "/executions" '{
  "recoveryPlanId": "'${PLAN_ID}'",
  "executionType": "RECOVERY",
  "initiatedBy": "cli-automation"
}'
```

#### Monitor Execution

```bash
# Get execution status
EXECUTION_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
api_call GET "/executions/${EXECUTION_ID}" | jq '{status, currentWave, totalWaves}'

# Poll until complete
while true; do
  STATUS=$(api_call GET "/executions/${EXECUTION_ID}" | jq -r '.status')
  echo "Status: ${STATUS}"
  
  case ${STATUS} in
    completed|failed|cancelled)
      echo "Execution finished with status: ${STATUS}"
      break
      ;;
    paused)
      echo "Execution paused - manual intervention required"
      break
      ;;
  esac
  
  sleep 30
done
```

#### Resume Paused Execution

```bash
# Resume execution that was paused before a wave
EXECUTION_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
api_call POST "/executions/${EXECUTION_ID}/resume" '{}'
```

#### Cancel Execution

```bash
# Cancel running execution
EXECUTION_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
api_call POST "/executions/${EXECUTION_ID}/cancel" '{}'
```

---

## SSM Automation Integration

### SSM Document for DR Drill

Create an SSM Automation document that executes DR drills:

```yaml
# ssm-documents/drs-drill-automation.yaml
schemaVersion: '0.3'
description: 'Execute DRS Orchestration Drill'
assumeRole: '{{AutomationAssumeRole}}'
parameters:
  AutomationAssumeRole:
    type: String
    description: IAM role for SSM Automation
  ApiEndpoint:
    type: String
    description: DRS Orchestration API endpoint
  CognitoClientId:
    type: String
    description: Cognito client ID
  Username:
    type: String
    description: Service account username
  PasswordParameter:
    type: String
    description: SSM Parameter name containing password
  RecoveryPlanName:
    type: String
    description: Name of recovery plan to execute
  ExecutionType:
    type: String
    default: DRILL
    allowedValues:
      - DRILL
      - RECOVERY

mainSteps:
  - name: GetAuthToken
    action: aws:executeScript
    inputs:
      Runtime: python3.9
      Handler: get_token
      Script: |
        import boto3
        import json
        
        def get_token(events, context):
            ssm = boto3.client('ssm')
            cognito = boto3.client('cognito-idp')
            
            # Get password from Parameter Store
            password = ssm.get_parameter(
                Name=events['PasswordParameter'],
                WithDecryption=True
            )['Parameter']['Value']
            
            # Authenticate
            response = cognito.initiate_auth(
                ClientId=events['CognitoClientId'],
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': events['Username'],
                    'PASSWORD': password
                }
            )
            
            return {'token': response['AuthenticationResult']['IdToken']}
      InputPayload:
        CognitoClientId: '{{CognitoClientId}}'
        Username: '{{Username}}'
        PasswordParameter: '{{PasswordParameter}}'
    outputs:
      - Name: Token
        Selector: $.Payload.token
        Type: String

  - name: FindRecoveryPlan
    action: aws:executeScript
    inputs:
      Runtime: python3.9
      Handler: find_plan
      Script: |
        import urllib.request
        import urllib.parse
        import json
        
        def find_plan(events, context):
            api = events['ApiEndpoint']
            token = events['Token']
            plan_name = urllib.parse.quote(events['RecoveryPlanName'])
            
            url = f"{api}/recovery-plans?nameExact={plan_name}"
            req = urllib.request.Request(url, headers={
                'Authorization': f'Bearer {token}'
            })
            
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
                
            if not data.get('plans'):
                raise Exception(f"Recovery plan '{events['RecoveryPlanName']}' not found")
            
            plan = data['plans'][0]
            return {
                'planId': plan['id'],
                'planName': plan['name'],
                'hasConflict': plan.get('hasServerConflict', False)
            }
      InputPayload:
        ApiEndpoint: '{{ApiEndpoint}}'
        Token: '{{GetAuthToken.Token}}'
        RecoveryPlanName: '{{RecoveryPlanName}}'
    outputs:
      - Name: PlanId
        Selector: $.Payload.planId
        Type: String
      - Name: HasConflict
        Selector: $.Payload.hasConflict
        Type: Boolean

  - name: CheckConflicts
    action: aws:branch
    inputs:
      Choices:
        - NextStep: FailOnConflict
          Variable: '{{FindRecoveryPlan.HasConflict}}'
          BooleanEquals: true
      Default: StartExecution

  - name: FailOnConflict
    action: aws:executeScript
    isEnd: true
    inputs:
      Runtime: python3.9
      Handler: fail
      Script: |
        def fail(events, context):
            raise Exception("Recovery plan has server conflicts with active execution")
      InputPayload: {}

  - name: StartExecution
    action: aws:executeScript
    inputs:
      Runtime: python3.9
      Handler: start_execution
      Script: |
        import urllib.request
        import json
        
        def start_execution(events, context):
            api = events['ApiEndpoint']
            token = events['Token']
            
            url = f"{api}/executions"
            data = json.dumps({
                'recoveryPlanId': events['PlanId'],
                'executionType': events['ExecutionType'],
                'initiatedBy': 'ssm-automation',
                'invocationSource': 'SSM',
                'invocationDetails': {
                    'ssmDocumentName': 'drs-drill-automation'
                }
            }).encode()
            
            req = urllib.request.Request(url, data=data, headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            })
            
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
            
            return {'executionId': result.get('ExecutionId') or result.get('executionId')}
      InputPayload:
        ApiEndpoint: '{{ApiEndpoint}}'
        Token: '{{GetAuthToken.Token}}'
        PlanId: '{{FindRecoveryPlan.PlanId}}'
        ExecutionType: '{{ExecutionType}}'
    outputs:
      - Name: ExecutionId
        Selector: $.Payload.executionId
        Type: String

  - name: WaitForCompletion
    action: aws:waitForAwsResourceProperty
    timeoutSeconds: 7200
    inputs:
      Service: lambda
      Api: Invoke
      FunctionName: drs-orchestration-api-handler-prod
      Payload: '{"httpMethod":"GET","path":"/executions/{{StartExecution.ExecutionId}}"}'
      PropertySelector: $.Payload.status
      DesiredValues:
        - completed
        - failed
        - cancelled

outputs:
  - ExecutionId
  - StartExecution.ExecutionId
```

### Execute SSM Document

```bash
# Start SSM Automation
aws ssm start-automation-execution \
  --document-name "drs-drill-automation" \
  --parameters '{
    "AutomationAssumeRole": ["arn:aws:iam::123456789012:role/SSMAutomationRole"],
    "ApiEndpoint": ["https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod"],
    "CognitoClientId": ["xxxxxxxxxxxxxxxxxxxxxxxxxx"],
    "Username": ["dr-automation@example.com"],
    "PasswordParameter": ["/drs-orchestration/service-account-password"],
    "RecoveryPlanName": ["2-Tier Recovery"],
    "ExecutionType": ["DRILL"]
  }'
```

---

## Step Functions Integration

### Step Functions State Machine

Create a Step Functions state machine that orchestrates DR drills as part of a larger workflow:

```json
{
  "Comment": "DR Orchestration Integration",
  "StartAt": "GetAuthToken",
  "States": {
    "GetAuthToken": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:get-cognito-token",
      "ResultPath": "$.auth",
      "Next": "FindRecoveryPlan"
    },
    "FindRecoveryPlan": {
      "Type": "Task",
      "Resource": "arn:aws:states:::http:invoke",
      "Parameters": {
        "ApiEndpoint.$": "$.config.apiEndpoint",
        "Method": "GET",
        "Path.$": "States.Format('/recovery-plans?nameExact={}', $.planName)",
        "Headers": {
          "Authorization.$": "States.Format('Bearer {}', $.auth.token)"
        }
      },
      "ResultPath": "$.planResult",
      "Next": "CheckPlanFound"
    },
    "CheckPlanFound": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.planResult.plans[0]",
          "IsPresent": true,
          "Next": "CheckConflicts"
        }
      ],
      "Default": "PlanNotFound"
    },
    "CheckConflicts": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.planResult.plans[0].hasServerConflict",
          "BooleanEquals": true,
          "Next": "ConflictDetected"
        }
      ],
      "Default": "StartDRExecution"
    },
    "StartDRExecution": {
      "Type": "Task",
      "Resource": "arn:aws:states:::http:invoke",
      "Parameters": {
        "ApiEndpoint.$": "$.config.apiEndpoint",
        "Method": "POST",
        "Path": "/executions",
        "Headers": {
          "Authorization.$": "States.Format('Bearer {}', $.auth.token)",
          "Content-Type": "application/json"
        },
        "RequestBody": {
          "recoveryPlanId.$": "$.planResult.plans[0].id",
          "executionType.$": "$.executionType",
          "initiatedBy": "step-functions",
          "invocationSource": "STEPFUNCTIONS"
        }
      },
      "ResultPath": "$.execution",
      "Next": "WaitForExecution"
    },
    "WaitForExecution": {
      "Type": "Wait",
      "Seconds": 30,
      "Next": "CheckExecutionStatus"
    },
    "CheckExecutionStatus": {
      "Type": "Task",
      "Resource": "arn:aws:states:::http:invoke",
      "Parameters": {
        "ApiEndpoint.$": "$.config.apiEndpoint",
        "Method": "GET",
        "Path.$": "States.Format('/executions/{}', $.execution.executionId)",
        "Headers": {
          "Authorization.$": "States.Format('Bearer {}', $.auth.token)"
        }
      },
      "ResultPath": "$.status",
      "Next": "EvaluateStatus"
    },
    "EvaluateStatus": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.status.status",
          "StringEquals": "completed",
          "Next": "ExecutionSucceeded"
        },
        {
          "Variable": "$.status.status",
          "StringEquals": "failed",
          "Next": "ExecutionFailed"
        },
        {
          "Variable": "$.status.status",
          "StringEquals": "cancelled",
          "Next": "ExecutionCancelled"
        },
        {
          "Variable": "$.status.status",
          "StringEquals": "paused",
          "Next": "ExecutionPaused"
        }
      ],
      "Default": "WaitForExecution"
    },
    "ExecutionSucceeded": {
      "Type": "Succeed"
    },
    "ExecutionFailed": {
      "Type": "Fail",
      "Error": "DRExecutionFailed",
      "Cause": "DR execution failed"
    },
    "ExecutionCancelled": {
      "Type": "Fail",
      "Error": "DRExecutionCancelled",
      "Cause": "DR execution was cancelled"
    },
    "ExecutionPaused": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish.waitForTaskToken",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:dr-approval-topic",
        "Message.$": "States.Format('DR execution {} is paused. Approve to continue.', $.execution.executionId)"
      },
      "Next": "ResumeExecution"
    },
    "ResumeExecution": {
      "Type": "Task",
      "Resource": "arn:aws:states:::http:invoke",
      "Parameters": {
        "ApiEndpoint.$": "$.config.apiEndpoint",
        "Method": "POST",
        "Path.$": "States.Format('/executions/{}/resume', $.execution.executionId)",
        "Headers": {
          "Authorization.$": "States.Format('Bearer {}', $.auth.token)"
        }
      },
      "Next": "WaitForExecution"
    },
    "PlanNotFound": {
      "Type": "Fail",
      "Error": "PlanNotFound",
      "Cause": "Recovery plan not found"
    },
    "ConflictDetected": {
      "Type": "Fail",
      "Error": "ConflictDetected",
      "Cause": "Recovery plan has server conflicts"
    }
  }
}
```

### Start Step Functions Execution

```bash
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:dr-orchestration \
  --input '{
    "config": {
      "apiEndpoint": "https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod"
    },
    "planName": "2-Tier Recovery",
    "executionType": "DRILL"
  }'
```

---

## EventBridge Scheduled Execution

### Create Scheduled Rule for Monthly DR Drills

```bash
# Create EventBridge rule for monthly DR drill
aws events put-rule \
  --name "monthly-dr-drill" \
  --schedule-expression "cron(0 6 1 * ? *)" \
  --description "Monthly DR drill on 1st of each month at 6 AM UTC"

# Create target (Lambda or Step Functions)
aws events put-targets \
  --rule "monthly-dr-drill" \
  --targets '[{
    "Id": "dr-drill-target",
    "Arn": "arn:aws:states:us-east-1:123456789012:stateMachine:dr-orchestration",
    "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeStepFunctionsRole",
    "Input": "{\"config\":{\"apiEndpoint\":\"https://xxx.execute-api.us-east-1.amazonaws.com/prod\"},\"planName\":\"2-Tier Recovery\",\"executionType\":\"DRILL\"}"
  }]'
```

### Lambda-Based Scheduled Execution

```python
# lambda/scheduled_drill.py
import boto3
import json
import os
import urllib.request

def handler(event, context):
    """EventBridge scheduled DR drill execution"""
    
    # Get configuration from environment or event
    api_endpoint = os.environ.get('API_ENDPOINT') or event.get('apiEndpoint')
    plan_name = event.get('planName', os.environ.get('DEFAULT_PLAN_NAME'))
    execution_type = event.get('executionType', 'DRILL')
    
    # Get auth token
    token = get_auth_token()
    
    # Find recovery plan
    plan = find_plan_by_name(api_endpoint, token, plan_name)
    if not plan:
        raise Exception(f"Recovery plan '{plan_name}' not found")
    
    if plan.get('hasServerConflict'):
        raise Exception(f"Recovery plan has server conflicts")
    
    # Start execution
    execution = start_execution(
        api_endpoint, token, plan['id'], execution_type,
        invocation_source='EVENTBRIDGE',
        invocation_details={
            'scheduleRuleName': event.get('ruleName', 'scheduled-drill'),
            'scheduleExpression': event.get('scheduleExpression', 'manual')
        }
    )
    
    return {
        'statusCode': 200,
        'executionId': execution['executionId'],
        'planName': plan_name
    }

def get_auth_token():
    """Get Cognito auth token from SSM Parameter Store credentials"""
    ssm = boto3.client('ssm')
    cognito = boto3.client('cognito-idp')
    
    client_id = ssm.get_parameter(Name='/drs-orchestration/cognito-client-id')['Parameter']['Value']
    username = ssm.get_parameter(Name='/drs-orchestration/service-username')['Parameter']['Value']
    password = ssm.get_parameter(Name='/drs-orchestration/service-password', WithDecryption=True)['Parameter']['Value']
    
    response = cognito.initiate_auth(
        ClientId=client_id,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={'USERNAME': username, 'PASSWORD': password}
    )
    
    return response['AuthenticationResult']['IdToken']

def find_plan_by_name(api_endpoint, token, plan_name):
    """Find recovery plan by exact name"""
    import urllib.parse
    url = f"{api_endpoint}/recovery-plans?nameExact={urllib.parse.quote(plan_name)}"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    
    return data['plans'][0] if data.get('plans') else None

def start_execution(api_endpoint, token, plan_id, execution_type, invocation_source, invocation_details):
    """Start DR execution"""
    url = f"{api_endpoint}/executions"
    data = json.dumps({
        'recoveryPlanId': plan_id,
        'executionType': execution_type,
        'initiatedBy': 'eventbridge-scheduler',
        'invocationSource': invocation_source,
        'invocationDetails': invocation_details
    }).encode()
    
    req = urllib.request.Request(url, data=data, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    })
    
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
```

---

## Python SDK Examples

### Complete Python Client

```python
# drs_orchestration_client.py
"""
DRS Orchestration Python Client

Usage:
    from drs_orchestration_client import DRSOrchestrationClient
    
    client = DRSOrchestrationClient(
        api_endpoint='https://xxx.execute-api.us-east-1.amazonaws.com/prod',
        cognito_client_id='xxxxxxxxxx',
        username='dr-automation@example.com',
        password='YourPassword123!'
    )
    
    # List plans
    plans = client.list_recovery_plans()
    
    # Start drill
    execution = client.start_execution(plan_id='xxx', execution_type='DRILL')
    
    # Wait for completion
    result = client.wait_for_completion(execution['executionId'], timeout=3600)
"""

import boto3
import json
import time
import urllib.request
import urllib.parse
from typing import Dict, List, Optional

class DRSOrchestrationClient:
    def __init__(self, api_endpoint: str, cognito_client_id: str, 
                 username: str, password: str, region: str = 'us-east-1'):
        self.api_endpoint = api_endpoint.rstrip('/')
        self.cognito_client_id = cognito_client_id
        self.username = username
        self.password = password
        self.region = region
        self._token = None
        self._token_expiry = 0
    
    def _get_token(self) -> str:
        """Get or refresh Cognito auth token"""
        if self._token and time.time() < self._token_expiry - 300:
            return self._token
        
        cognito = boto3.client('cognito-idp', region_name=self.region)
        response = cognito.initiate_auth(
            ClientId=self.cognito_client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': self.username,
                'PASSWORD': self.password
            }
        )
        
        self._token = response['AuthenticationResult']['IdToken']
        self._token_expiry = time.time() + response['AuthenticationResult']['ExpiresIn']
        return self._token
    
    def _request(self, method: str, path: str, data: Dict = None) -> Dict:
        """Make authenticated API request"""
        url = f"{self.api_endpoint}{path}"
        headers = {
            'Authorization': f'Bearer {self._get_token()}',
            'Content-Type': 'application/json'
        }
        
        if data:
            req = urllib.request.Request(url, json.dumps(data).encode(), headers, method=method)
        else:
            req = urllib.request.Request(url, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise Exception(f"API Error {e.code}: {error_body}")

    # Protection Groups
    def list_protection_groups(self) -> List[Dict]:
        """List all protection groups"""
        return self._request('GET', '/protection-groups').get('groups', [])
    
    def get_protection_group(self, group_id: str) -> Dict:
        """Get protection group by ID"""
        return self._request('GET', f'/protection-groups/{group_id}')
    
    def resolve_protection_group(self, group_id: str) -> Dict:
        """Resolve servers from protection group tags"""
        return self._request('POST', f'/protection-groups/{group_id}/resolve')
    
    # Recovery Plans
    def list_recovery_plans(self, name: str = None, name_exact: str = None,
                           tag: str = None, has_conflict: bool = None,
                           status: str = None) -> List[Dict]:
        """List recovery plans with optional filters"""
        params = []
        if name:
            params.append(f'name={urllib.parse.quote(name)}')
        if name_exact:
            params.append(f'nameExact={urllib.parse.quote(name_exact)}')
        if tag:
            params.append(f'tag={urllib.parse.quote(tag)}')
        if has_conflict is not None:
            params.append(f'hasConflict={str(has_conflict).lower()}')
        if status:
            params.append(f'status={urllib.parse.quote(status)}')
        
        query = '?' + '&'.join(params) if params else ''
        return self._request('GET', f'/recovery-plans{query}').get('plans', [])
    
    def get_recovery_plan(self, plan_id: str) -> Dict:
        """Get recovery plan by ID"""
        return self._request('GET', f'/recovery-plans/{plan_id}')
    
    def find_plan_by_name(self, name: str) -> Optional[Dict]:
        """Find recovery plan by exact name"""
        plans = self.list_recovery_plans(name_exact=name)
        return plans[0] if plans else None
    
    # Executions
    def list_executions(self, limit: int = 50) -> List[Dict]:
        """List executions"""
        return self._request('GET', f'/executions?limit={limit}').get('items', [])
    
    def get_execution(self, execution_id: str) -> Dict:
        """Get execution details"""
        return self._request('GET', f'/executions/{execution_id}')
    
    def start_execution(self, plan_id: str, execution_type: str = 'DRILL',
                       initiated_by: str = 'api-client',
                       invocation_source: str = 'API') -> Dict:
        """Start new execution"""
        return self._request('POST', '/executions', {
            'recoveryPlanId': plan_id,
            'executionType': execution_type,
            'initiatedBy': initiated_by,
            'invocationSource': invocation_source
        })
    
    def cancel_execution(self, execution_id: str) -> Dict:
        """Cancel running execution"""
        return self._request('POST', f'/executions/{execution_id}/cancel')
    
    def pause_execution(self, execution_id: str) -> Dict:
        """Pause execution"""
        return self._request('POST', f'/executions/{execution_id}/pause')
    
    def resume_execution(self, execution_id: str) -> Dict:
        """Resume paused execution"""
        return self._request('POST', f'/executions/{execution_id}/resume')
    
    def wait_for_completion(self, execution_id: str, timeout: int = 3600,
                           poll_interval: int = 30) -> Dict:
        """Wait for execution to complete"""
        start_time = time.time()
        terminal_states = {'completed', 'failed', 'cancelled'}
        
        while time.time() - start_time < timeout:
            execution = self.get_execution(execution_id)
            status = execution.get('status', '').lower()
            
            if status in terminal_states:
                return execution
            
            if status == 'paused':
                raise Exception(f"Execution {execution_id} is paused - manual intervention required")
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Execution {execution_id} did not complete within {timeout} seconds")
    
    # DRS Operations
    def list_drs_source_servers(self, region: str) -> List[Dict]:
        """List DRS source servers in region"""
        return self._request('GET', f'/drs/source-servers?region={region}').get('servers', [])
    
    def get_drs_quotas(self, region: str) -> Dict:
        """Get DRS service quotas for region"""
        return self._request('GET', f'/drs/quotas?region={region}')


# Example usage
if __name__ == '__main__':
    import os
    
    client = DRSOrchestrationClient(
        api_endpoint=os.environ['API_ENDPOINT'],
        cognito_client_id=os.environ['COGNITO_CLIENT_ID'],
        username=os.environ['DR_USERNAME'],
        password=os.environ['DR_PASSWORD']
    )
    
    # Find and execute plan
    plan = client.find_plan_by_name('2-Tier Recovery')
    if plan and not plan.get('hasServerConflict'):
        execution = client.start_execution(plan['id'], 'DRILL')
        print(f"Started execution: {execution['executionId']}")
        
        result = client.wait_for_completion(execution['executionId'])
        print(f"Execution completed with status: {result['status']}")
```

---

## Bash Script Examples

### Complete DR Drill Script

```bash
#!/bin/bash
# scripts/execute_dr_drill.sh
# Complete DR drill execution script with error handling

set -euo pipefail

# Configuration
API_ENDPOINT="${API_ENDPOINT:-https://xxx.execute-api.us-east-1.amazonaws.com/prod}"
COGNITO_CLIENT_ID="${COGNITO_CLIENT_ID:-}"
DR_USERNAME="${DR_USERNAME:-}"
DR_PASSWORD="${DR_PASSWORD:-}"
PLAN_NAME="${1:-}"
EXECUTION_TYPE="${2:-DRILL}"
POLL_INTERVAL="${POLL_INTERVAL:-30}"
TIMEOUT="${TIMEOUT:-3600}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Validate inputs
if [ -z "$PLAN_NAME" ]; then
    log_error "Usage: $0 <plan-name> [DRILL|RECOVERY]"
    exit 1
fi

if [ -z "$COGNITO_CLIENT_ID" ] || [ -z "$DR_USERNAME" ] || [ -z "$DR_PASSWORD" ]; then
    log_error "Missing required environment variables: COGNITO_CLIENT_ID, DR_USERNAME, DR_PASSWORD"
    exit 1
fi

# Get auth token
log_info "Authenticating..."
TOKEN=$(aws cognito-idp initiate-auth \
    --client-id "${COGNITO_CLIENT_ID}" \
    --auth-flow USER_PASSWORD_AUTH \
    --auth-parameters USERNAME="${DR_USERNAME}",PASSWORD="${DR_PASSWORD}" \
    --query 'AuthenticationResult.IdToken' \
    --output text 2>/dev/null)

if [ -z "$TOKEN" ]; then
    log_error "Failed to authenticate"
    exit 1
fi

# Find recovery plan
log_info "Finding recovery plan: ${PLAN_NAME}"
ENCODED_NAME=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${PLAN_NAME}'))")
PLAN_RESPONSE=$(curl -s -H "Authorization: Bearer ${TOKEN}" \
    "${API_ENDPOINT}/recovery-plans?nameExact=${ENCODED_NAME}")

PLAN_ID=$(echo "$PLAN_RESPONSE" | jq -r '.plans[0].id // empty')
HAS_CONFLICT=$(echo "$PLAN_RESPONSE" | jq -r '.plans[0].hasServerConflict // false')

if [ -z "$PLAN_ID" ]; then
    log_error "Recovery plan '${PLAN_NAME}' not found"
    exit 1
fi

log_info "Found plan: ${PLAN_ID}"

# Check for conflicts
if [ "$HAS_CONFLICT" = "true" ]; then
    log_error "Recovery plan has server conflicts with active execution"
    exit 1
fi

# Start execution
log_info "Starting ${EXECUTION_TYPE} execution..."
EXEC_RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"recoveryPlanId\":\"${PLAN_ID}\",\"executionType\":\"${EXECUTION_TYPE}\",\"initiatedBy\":\"bash-script\",\"invocationSource\":\"CLI\"}" \
    "${API_ENDPOINT}/executions")

EXECUTION_ID=$(echo "$EXEC_RESPONSE" | jq -r '.ExecutionId // .executionId // empty')

if [ -z "$EXECUTION_ID" ]; then
    log_error "Failed to start execution: $(echo "$EXEC_RESPONSE" | jq -r '.error // .message // "Unknown error"')"
    exit 1
fi

log_info "Execution started: ${EXECUTION_ID}"

# Poll for completion
log_info "Waiting for completion (timeout: ${TIMEOUT}s)..."
START_TIME=$(date +%s)

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [ $ELAPSED -ge $TIMEOUT ]; then
        log_error "Timeout waiting for execution to complete"
        exit 1
    fi
    
    STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer ${TOKEN}" \
        "${API_ENDPOINT}/executions/${EXECUTION_ID}")
    
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
    CURRENT_WAVE=$(echo "$STATUS_RESPONSE" | jq -r '.currentWave // 0')
    TOTAL_WAVES=$(echo "$STATUS_RESPONSE" | jq -r '.totalWaves // 0')
    
    log_info "Status: ${STATUS} (Wave ${CURRENT_WAVE}/${TOTAL_WAVES}) - Elapsed: ${ELAPSED}s"
    
    case "$STATUS" in
        completed)
            log_info "Execution completed successfully!"
            exit 0
            ;;
        failed)
            ERROR_MSG=$(echo "$STATUS_RESPONSE" | jq -r '.errorMessage // "Unknown error"')
            log_error "Execution failed: ${ERROR_MSG}"
            exit 1
            ;;
        cancelled)
            log_warn "Execution was cancelled"
            exit 1
            ;;
        paused)
            log_warn "Execution is paused - manual intervention required"
            log_info "Resume with: curl -X POST -H 'Authorization: Bearer \$TOKEN' ${API_ENDPOINT}/executions/${EXECUTION_ID}/resume"
            exit 2
            ;;
    esac
    
    sleep $POLL_INTERVAL
done
```

### Usage Examples

```bash
# Execute drill
./scripts/execute_dr_drill.sh "2-Tier Recovery" DRILL

# Execute actual recovery
./scripts/execute_dr_drill.sh "Production Recovery" RECOVERY

# With custom timeout
TIMEOUT=7200 ./scripts/execute_dr_drill.sh "Large Recovery Plan" DRILL
```

---

## Error Handling

### Common HTTP Status Codes

| HTTP Code | Category | Description | Resolution |
|-----------|----------|-------------|------------|
| 400 | Bad Request | Invalid request body, missing fields, or validation failure | Check request format and required fields |
| 401 | Unauthorized | Invalid or expired Cognito token | Refresh auth token or use IAM-based access |
| 403 | Forbidden | Insufficient IAM or Cognito permissions | Check IAM policy or Cognito group membership |
| 404 | Not Found | Resource (PG, Plan, Execution) not found | Verify resource ID exists |
| 405 | Method Not Allowed | HTTP method not supported for endpoint | Check API documentation for allowed methods |
| 409 | Conflict | Resource conflict (duplicate name, active execution, etc.) | Resolve conflict before retrying |
| 429 | Too Many Requests | DRS service limit exceeded | Wait and retry, or request limit increase |
| 500 | Internal Server Error | Unexpected server-side error | Check CloudWatch logs, retry with backoff |

### API Error Codes Reference

#### Protection Group Errors

| Error Code | HTTP | Message | Cause | Resolution |
|------------|------|---------|-------|------------|
| `PG_NAME_EXISTS` | 409 | "A Protection Group named X already exists" | Duplicate name (case-insensitive) | Use a unique name |
| `TAG_CONFLICT` | 409 | "Another Protection Group already uses these exact tags" | Identical tag set exists | Use different tags or modify existing PG |
| `SERVER_CONFLICT` | 409 | "One or more servers are already assigned to another Protection Group" | Server already in another PG | Remove server from other PG first |
| `PG_IN_ACTIVE_EXECUTION` | 409 | "Cannot modify Protection Group while it is part of an active execution" | PG is in running execution | Wait for execution to complete or cancel |
| `PG_IN_USE` | 409 | "Cannot delete Protection Group - it is used in N Recovery Plan(s)" | PG referenced by plans | Remove PG from all plans first |
| `PROTECTION_GROUP_NOT_FOUND` | 404 | "Protection Group X not found" | Invalid PG ID | Verify PG ID exists |
| `INVALID_TAGS` | 400 | "ServerSelectionTags must be a non-empty object" | Empty or invalid tags | Provide valid tag key-value pairs |
| `INVALID_SERVERS` | 400 | "SourceServerIds must be a non-empty array" | Empty or invalid server list | Provide valid server IDs |

#### Recovery Plan Errors

| Error Code | HTTP | Message | Cause | Resolution |
|------------|------|---------|-------|------------|
| `RP_NAME_EXISTS` | 409 | "A Recovery Plan named X already exists" | Duplicate name (case-insensitive) | Use a unique name |
| `PLAN_HAS_ACTIVE_EXECUTION` | 409 | "Cannot modify/delete Recovery Plan while execution is in progress" | Plan has running execution | Wait for execution to complete or cancel |
| `INVALID_WAVE_DATA` | 400 | "Wave N has invalid ServerIds format" | Wave data malformed | Ensure ServerIds is an array |

#### Execution Errors

| Error Code | HTTP | Message | Cause | Resolution |
|------------|------|---------|-------|------------|
| `PLAN_ALREADY_EXECUTING` | 409 | "This Recovery Plan already has an execution in progress" | Plan already running | Wait for current execution to complete |
| `SERVER_CONFLICT` | 409 | "N server(s) are already in active executions" | Servers in other running executions | Wait for other executions to complete |
| `WAVE_SIZE_LIMIT_EXCEEDED` | 400 | "N wave(s) exceed the DRS limit of 100 servers per job" | Wave has >100 servers | Split wave into smaller groups |
| `CONCURRENT_JOBS_LIMIT_EXCEEDED` | 429 | "DRS concurrent jobs limit exceeded" | >20 concurrent DRS jobs | Wait for jobs to complete |
| `SERVERS_IN_JOBS_LIMIT_EXCEEDED` | 429 | "DRS servers in jobs limit exceeded" | >500 servers across all jobs | Wait for jobs to complete |
| `UNHEALTHY_SERVER_REPLICATION` | 400 | "Server replication not healthy" | Server not ready for recovery | Check DRS console for replication status |
| `EXECUTION_NOT_FOUND` | 404 | "Execution with ID X not found" | Invalid execution ID | Verify execution ID exists |
| `EXECUTION_NOT_CANCELLABLE` | 400 | "Execution cannot be cancelled - status is X" | Execution already completed/failed | Only running/paused executions can be cancelled |
| `EXECUTION_NOT_PAUSABLE` | 400 | "Execution cannot be paused - status is X" | Execution not running | Only running executions can be paused |
| `EXECUTION_NO_WAVES` | 400 | "No waves found in execution" | Execution has no wave data | Internal error - check execution state |
| `SINGLE_WAVE_NOT_PAUSABLE` | 400 | "Cannot pause single-wave execution" | Plan has only one wave | Pause only works for multi-wave plans |
| `NO_PENDING_WAVES` | 400 | "Cannot pause - no pending waves remaining" | All waves completed | Nothing left to pause |

#### DRS Service Errors

| Error Code | HTTP | Message | Cause | Resolution |
|------------|------|---------|-------|------------|
| `DRS_NOT_INITIALIZED` | 400 | "DRS is not initialized in region" | DRS not set up in region | Complete DRS initialization wizard in AWS Console |

#### Validation Errors

| Error Code | HTTP | Message | Cause | Resolution |
|------------|------|---------|-------|------------|
| `MISSING_FIELD` | 400 | "X is required" | Required field not provided | Include the required field in request |
| `INVALID_NAME` | 400 | "Name cannot be empty" or "Name must be 256 characters or fewer" | Empty or too long name | Provide valid name (1-256 chars) |
| `INVALID_EXECUTION_TYPE` | 400 | "ExecutionType must be DRILL or RECOVERY" | Invalid execution type | Use DRILL or RECOVERY |
| `PLAN_HAS_NO_WAVES` | 400 | "Recovery Plan has no waves configured" | Plan has no waves | Add at least one wave to the plan |
| `RECOVERY_PLAN_NOT_FOUND` | 404 | "Recovery Plan with ID X not found" | Invalid plan ID | Verify plan ID exists |

#### General Errors

| Error Code | HTTP | Message | Cause | Resolution |
|------------|------|---------|-------|------------|
| `INTERNAL_ERROR` | 500 | "Failed to X: error details" | Unexpected error | Check CloudWatch logs, retry |
| `DELETE_FAILED` | 500 | "Failed to delete X" | Delete operation failed | Check CloudWatch logs, retry |

### Error Response Format

All errors return a consistent JSON structure:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message explaining what went wrong",
  "conflicts": [...],           // Optional: Details about conflicting resources
  "activeExecutions": [...],    // Optional: IDs of blocking executions
  "plans": [...],               // Optional: Plans referencing the resource
  "region": "us-east-1",        // Optional: Region context
  "existingName": "..."         // Optional: Name that already exists
}
```

### Example Error Responses

#### Duplicate Protection Group Name
```json
{
  "error": "PG_NAME_EXISTS",
  "message": "A Protection Group named \"Database Servers\" already exists",
  "existingName": "Database Servers"
}
```

#### Tag Conflict
```json
{
  "error": "TAG_CONFLICT",
  "message": "Another Protection Group already uses these exact tags",
  "conflicts": [
    {
      "protectionGroupId": "pg-abc123",
      "protectionGroupName": "Existing PG",
      "conflictingTags": {"Environment": "Production", "Tier": "Database"},
      "conflictType": "exact_match"
    }
  ]
}
```

#### Server Already Assigned
```json
{
  "error": "SERVER_CONFLICT",
  "message": "One or more servers are already assigned to another Protection Group",
  "conflicts": [
    {
      "serverId": "s-abc123",
      "hostname": "db-server-01",
      "assignedToGroupId": "pg-xyz789",
      "assignedToGroupName": "Other PG"
    }
  ]
}
```

#### Execution Server Conflict
```json
{
  "error": "SERVER_CONFLICT",
  "message": "3 server(s) are already in active executions",
  "conflicts": [
    {
      "serverId": "s-abc123",
      "hostname": "web-server-01",
      "conflictingExecutionId": "exec-xyz789",
      "conflictingPlanName": "Other Recovery Plan"
    }
  ],
  "conflictingExecutions": [
    {
      "executionId": "exec-xyz789",
      "planName": "Other Recovery Plan",
      "status": "IN_PROGRESS",
      "serverCount": 3
    }
  ]
}
```

#### DRS Limit Exceeded
```json
{
  "error": "CONCURRENT_JOBS_LIMIT_EXCEEDED",
  "message": "Cannot start execution: 20 concurrent DRS jobs already running (limit: 20)",
  "currentJobs": 20,
  "limit": 20
}
```

#### DRS Not Initialized
```json
{
  "error": "DRS_NOT_INITIALIZED",
  "message": "AWS Elastic Disaster Recovery (DRS) is not initialized in us-west-2. Go to the DRS Console in us-west-2 and complete the initialization wizard before creating Protection Groups.",
  "region": "us-west-2",
  "consoleUrl": "https://us-west-2.console.aws.amazon.com/drs/home?region=us-west-2#/welcome"
}
```

#### Execution Not Pausable
```json
{
  "error": "EXECUTION_NOT_PAUSABLE",
  "message": "Execution cannot be paused - status is COMPLETED",
  "executionId": "exec-abc123",
  "currentStatus": "COMPLETED",
  "pausableStatuses": ["RUNNING", "IN_PROGRESS", "POLLING"],
  "reason": "Execution must be running to pause"
}
```

#### Single Wave Not Pausable
```json
{
  "error": "SINGLE_WAVE_NOT_PAUSABLE",
  "message": "Cannot pause single-wave execution - pause is only available for multi-wave recovery plans",
  "executionId": "exec-abc123",
  "waveCount": 1,
  "reason": "Pause is only available for multi-wave recovery plans"
}
```

#### Execution Not Cancellable
```json
{
  "error": "EXECUTION_NOT_CANCELLABLE",
  "message": "Execution cannot be cancelled - status is COMPLETED",
  "executionId": "exec-abc123",
  "currentStatus": "COMPLETED",
  "cancellableStatuses": ["RUNNING", "PAUSED", "PAUSE_PENDING", "IN_PROGRESS", "POLLING", "INITIATED", "PENDING"],
  "reason": "Execution must be running, paused, or pending to cancel"
}
```

### Handling Errors in Code

#### Python Example

```python
def handle_api_error(response_body: dict) -> None:
    """Handle API errors with user-friendly messages"""
    error_code = response_body.get('error', 'UNKNOWN')
    message = response_body.get('message', 'An unknown error occurred')
    
    # Map error codes to user actions
    error_actions = {
        # Protection Group errors
        'PG_NAME_EXISTS': 'Choose a different Protection Group name',
        'TAG_CONFLICT': 'Use different tags or modify the existing Protection Group',
        'SERVER_CONFLICT': 'Remove servers from other Protection Groups first',
        'PG_IN_ACTIVE_EXECUTION': 'Wait for the execution to complete or cancel it',
        'PG_IN_USE': 'Remove this Protection Group from all Recovery Plans first',
        'INVALID_TAGS': 'Provide valid tag key-value pairs',
        'INVALID_SERVERS': 'Provide a non-empty array of valid server IDs',
        # Recovery Plan errors
        'RP_NAME_EXISTS': 'Choose a different Recovery Plan name',
        'PLAN_HAS_ACTIVE_EXECUTION': 'Wait for the execution to complete or cancel it',
        'INVALID_WAVE_DATA': 'Ensure wave ServerIds is a valid array',
        # Execution errors
        'PLAN_ALREADY_EXECUTING': 'Wait for the current execution to complete',
        'WAVE_SIZE_LIMIT_EXCEEDED': 'Split large waves into groups of 100 servers or fewer',
        'CONCURRENT_JOBS_LIMIT_EXCEEDED': 'Wait for some DRS jobs to complete',
        'SERVERS_IN_JOBS_LIMIT_EXCEEDED': 'Wait for some DRS jobs to complete',
        'UNHEALTHY_SERVER_REPLICATION': 'Check DRS console for server replication status',
        'EXECUTION_NOT_FOUND': 'Verify the execution ID exists',
        'EXECUTION_NOT_CANCELLABLE': 'Only running/paused executions can be cancelled',
        'EXECUTION_NOT_PAUSABLE': 'Only running executions can be paused',
        'SINGLE_WAVE_NOT_PAUSABLE': 'Pause is only available for multi-wave plans',
        'NO_PENDING_WAVES': 'All waves have completed - nothing to pause',
        # Validation errors
        'MISSING_FIELD': 'Include all required fields in the request',
        'INVALID_NAME': 'Provide a valid name (1-256 characters, not empty)',
        'INVALID_EXECUTION_TYPE': 'Use DRILL or RECOVERY as execution type',
        'PLAN_HAS_NO_WAVES': 'Add at least one wave to the Recovery Plan',
        'RECOVERY_PLAN_NOT_FOUND': 'Verify the Recovery Plan ID exists',
        # DRS errors
        'DRS_NOT_INITIALIZED': 'Initialize DRS in the AWS Console for this region',
    }
    
    action = error_actions.get(error_code, 'Check the error details and try again')
    
    print(f"Error: {message}")
    print(f"Action: {action}")
    
    # Log additional context if available
    if 'conflicts' in response_body:
        print(f"Conflicts: {len(response_body['conflicts'])} resource(s)")
    if 'activeExecutions' in response_body:
        print(f"Active executions: {response_body['activeExecutions']}")
```

#### Bash Example

```bash
handle_error() {
    local response="$1"
    local error_code=$(echo "$response" | jq -r '.error // "UNKNOWN"')
    local message=$(echo "$response" | jq -r '.message // "Unknown error"')
    
    echo "ERROR [$error_code]: $message"
    
    case "$error_code" in
        PG_NAME_EXISTS|RP_NAME_EXISTS)
            echo "→ Choose a different name"
            ;;
        TAG_CONFLICT)
            echo "→ Use different tags or modify existing Protection Group"
            ;;
        SERVER_CONFLICT)
            echo "→ Servers are in use - wait for executions to complete"
            ;;
        PG_IN_ACTIVE_EXECUTION|PLAN_ALREADY_EXECUTING)
            echo "→ Wait for execution to complete or cancel it"
            ;;
        DRS_NOT_INITIALIZED)
            local region=$(echo "$response" | jq -r '.region')
            echo "→ Initialize DRS at: https://${region}.console.aws.amazon.com/drs/"
            ;;
        *)
            echo "→ Check CloudWatch logs for details"
            ;;
    esac
    
    return 1
}

# Usage
response=$(invoke_lambda "POST" "/protection-groups" "$body")
status=$(echo "$response" | jq -r '.statusCode // 200')

if [ "$status" -ge 400 ]; then
    handle_error "$(echo "$response" | jq -r '.body')"
fi
```

### Retry Logic Example

```python
import time
import random

def api_call_with_retry(func, max_retries=3, base_delay=1):
    """Execute API call with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            # Check if retryable
            error_str = str(e)
            if '429' in error_str or '500' in error_str or '503' in error_str:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {e}")
                time.sleep(delay)
            else:
                raise
```

---

## Best Practices

### 1. Authentication

- **Use IAM roles with direct Lambda invocation** for AWS-native integrations (Step Functions, SSM, EventBridge, Lambda)
- **Use service accounts** for external integrations that require HTTP/REST access
- **Store Cognito credentials in SSM Parameter Store** with encryption when needed
- **Rotate credentials** regularly (every 90 days)
- **Prefer IAM-based access** over Cognito tokens for automated workflows within AWS

### 2. Execution Management

- **Always check for conflicts** before starting execution
- **Implement proper timeout handling** for long-running operations
- **Use idempotent operations** where possible
- **Log execution IDs** for audit trails

### 3. Error Handling

- **Implement retry logic** with exponential backoff
- **Handle paused executions** gracefully
- **Monitor execution status** rather than assuming success
- **Set up CloudWatch alarms** for failed executions

### 4. Integration Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                    Integration Patterns                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ EventBridge│───▶│  Lambda  │───▶│   API    │───▶│   DRS    │  │
│  │ Schedule  │    │ Trigger  │    │ Gateway  │    │ Service  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │   SSM    │───▶│Automation│───▶│   API    │───▶│   DRS    │  │
│  │ Document │    │  Steps   │    │ Gateway  │    │ Service  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Step    │───▶│  HTTP    │───▶│   API    │───▶│   DRS    │  │
│  │Functions │    │  Task    │    │ Gateway  │    │ Service  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Bash/   │───▶│  curl/   │───▶│   API    │───▶│   DRS    │  │
│  │ Python   │    │ requests │    │ Gateway  │    │ Service  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5. Monitoring and Alerting

```bash
# Create CloudWatch alarm for failed executions
aws cloudwatch put-metric-alarm \
  --alarm-name "DRS-Orchestration-Failed-Executions" \
  --alarm-description "Alert when DR executions fail" \
  --metric-name "ExecutionsFailed" \
  --namespace "DRS-Orchestration" \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions "arn:aws:sns:us-east-1:123456789012:dr-alerts"
```

### 6. Security Considerations

- **Use HTTPS** for all API calls
- **Validate SSL certificates** in production
- **Implement IP allowlisting** via WAF if needed
- **Enable CloudTrail** for API audit logging
- **Use least-privilege IAM policies**

---

## Quick Reference

### Environment Variables

```bash
export API_ENDPOINT="https://xxx.execute-api.us-east-1.amazonaws.com/prod"
export COGNITO_CLIENT_ID="xxxxxxxxxxxxxxxxxxxxxxxxxx"
export COGNITO_USER_POOL_ID="us-east-1_xxxxxxxxx"
export DR_USERNAME="dr-automation@example.com"
export DR_PASSWORD="YourSecurePassword123!"
export AWS_REGION="us-east-1"
```

### Common Commands

```bash
# List plans
curl -H "Authorization: Bearer $TOKEN" "$API_ENDPOINT/recovery-plans"

# Find plan by name
curl -H "Authorization: Bearer $TOKEN" "$API_ENDPOINT/recovery-plans?nameExact=MyPlan"

# Start drill
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"recoveryPlanId":"xxx","executionType":"DRILL"}' "$API_ENDPOINT/executions"

# Check status
curl -H "Authorization: Bearer $TOKEN" "$API_ENDPOINT/executions/{id}"

# Resume paused
curl -X POST -H "Authorization: Bearer $TOKEN" "$API_ENDPOINT/executions/{id}/resume"

# Cancel
curl -X POST -H "Authorization: Bearer $TOKEN" "$API_ENDPOINT/executions/{id}/cancel"
```

---

## Related Documentation

- [Deployment and Operations Guide](DEPLOYMENT_AND_OPERATIONS_GUIDE.md)
- [AWS DRS API Reference](AWS_DRS_API_REFERENCE.md)
- [Debugging Guide](../troubleshooting/DRS_DRILL_FAILURE_ANALYSIS.md)
