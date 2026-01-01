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
  --function-name aws-drs-orchestrator-api-handler-dev \
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
        "arn:aws:lambda:us-east-1:*:function:aws-drs-orchestrator-api-handler-*",
        "arn:aws:lambda:us-east-1:*:function:aws-drs-orchestrator-orchestration-stepfunctions-*"
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
        FunctionName='aws-drs-orchestrator-api-handler-dev',
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

FUNCTION_NAME="aws-drs-orchestrator-api-handler-dev"
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
        "FunctionName": "aws-drs-orchestrator-api-handler-dev",
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
        "FunctionName": "aws-drs-orchestrator-api-handler-dev",
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
        "FunctionName": "aws-drs-orchestrator-api-handler-dev",
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
    default: aws-drs-orchestrator-api-handler-dev
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

| Method                        | Use Case                                                 | Pros                                | Cons                         |
| ----------------------------- | -------------------------------------------------------- | ----------------------------------- | ---------------------------- |
| **Cognito (User)**      | Interactive/manual operations                            | User identity tracking              | Requires password management |
| **Cognito (Service)**   | External integrations, third-party tools                 | Works with any HTTP client          | Token refresh needed         |
| **IAM (Direct Lambda)** | AWS-native automation (Step Functions, SSM, EventBridge) | No token management, uses IAM roles | Only works within AWS        |

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

| Limitation                            | Reason                                         | Workaround                                 |
| ------------------------------------- | ---------------------------------------------- | ------------------------------------------ |
| **Cross-account without setup** | Lambda must allow cross-account invocation     | Add resource-based policy to Lambda        |
| **External/third-party tools**  | Tools outside AWS can't use IAM roles directly | Use Cognito service account instead        |
| **User identity tracking**      | No Cognito user context in Lambda              | Pass `initiatedBy` field in request body |
| **Rate limiting per user**      | No user-level throttling                       | Implement custom throttling in Lambda      |
| **Browser/frontend access**     | Browsers can't assume IAM roles                | Use Cognito for frontend authentication    |

##### Cross-Account Invocation

To allow another AWS account to invoke the Lambda directly:

```bash
# Add resource-based policy to Lambda (run in the account that owns the Lambda)
aws lambda add-permission \
  --function-name aws-drs-orchestrator-api-handler-dev \
  --statement-id AllowCrossAccountInvoke \
  --action lambda:InvokeFunction \
  --principal 111122223333 \
  --region us-east-1
```

The calling account still needs an IAM policy allowing `lambda:InvokeFunction` on the target Lambda ARN.

##### What is NOT Allowed

| Action                                          | Allowed? | Notes                                                |
| ----------------------------------------------- | -------- | ---------------------------------------------------- |
| Direct Lambda invocation from same account      | ✅ Yes   | Requires IAM policy                                  |
| Direct Lambda invocation from different account | ✅ Yes   | Requires resource-based policy on Lambda             |
| Direct Lambda invocation from outside AWS       | ❌ No    | Use API Gateway + Cognito                            |
| Invoking Lambda from browser JavaScript         | ❌ No    | Use API Gateway + Cognito                            |
| Bypassing DRS service limits                    | ❌ No    | Lambda enforces DRS quotas regardless of auth method |
| Executing without valid recovery plan           | ❌ No    | API validates plan exists and has no conflicts       |
| Starting execution with conflicting servers     | ❌ No    | Server conflict check applies to all auth methods    |
| Deleting active executions                      | ❌ No    | Must cancel first, then delete                       |
| Modifying completed executions                  | ❌ No    | Execution history is immutable                       |

##### Edge Cases and Error Handling

| Scenario                   | Behavior                                     | Recommended Action                            |
| -------------------------- | -------------------------------------------- | --------------------------------------------- |
| Lambda cold start          | First invocation may take 1-3 seconds longer | Account for latency in timeouts               |
| Lambda timeout (29 sec)    | Request fails with timeout error             | Break long operations into smaller calls      |
| Concurrent execution limit | Throttling error (429)                       | Implement exponential backoff                 |
| Invalid event format       | 400 Bad Request                              | Validate event structure before invoking      |
| Missing required fields    | 400 Bad Request with field details           | Check API documentation for required fields   |
| Plan has server conflicts  | 409 Conflict                                 | Query plan first, check `hasServerConflict` |
| Execution already running  | 409 Conflict                                 | Wait for completion or cancel existing        |
| DRS quota exceeded         | 400 Bad Request                              | Check `/drs/quotas` before starting         |

##### Lambda Payload Size Limits

| Limit                          | Value          | Impact                                     |
| ------------------------------ | -------------- | ------------------------------------------ |
| Synchronous invocation payload | 6 MB           | Request + response combined                |
| Response payload               | 6 MB           | Large execution histories may be truncated |
| Event payload                  | 256 KB (async) | Use synchronous for larger payloads        |

##### Required Event Fields by Operation

| Operation       | Required Fields                                                           | Optional Fields                                 |
| --------------- | ------------------------------------------------------------------------- | ----------------------------------------------- |
| List resources  | `httpMethod`, `path`                                                  | `queryStringParameters`                       |
| Get by ID       | `httpMethod`, `path` (with ID)                                        | -                                               |
| Create          | `httpMethod`, `path`, `body`                                        | -                                               |
| Update          | `httpMethod`, `path` (with ID), `body`                              | -                                               |
| Delete          | `httpMethod`, `path` (with ID)                                        | -                                               |
| Start execution | `httpMethod`, `path`, `body.recoveryPlanId`, `body.executionType` | `body.initiatedBy`, `body.invocationSource` |

##### Troubleshooting IAM-Based Access

| Error                              | Cause                                        | Solution                                  |
| ---------------------------------- | -------------------------------------------- | ----------------------------------------- |
| `AccessDeniedException`          | Missing `lambda:InvokeFunction` permission | Add IAM policy to calling role            |
| `ResourceNotFoundException`      | Wrong function name or region                | Verify function name and region           |
| `InvalidRequestContentException` | Malformed JSON payload                       | Validate JSON structure                   |
| `ServiceException`               | Lambda internal error                        | Retry with exponential backoff            |
| `TooManyRequestsException`       | Throttled                                    | Implement backoff, request limit increase |
| `KMSAccessDeniedException`       | Lambda uses encrypted env vars               | Grant KMS decrypt to calling role         |

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
    "functionName": "aws-drs-orchestrator-api-handler-dev"
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

The AWS DRS Orchestration platform provides a comprehensive REST API with **42+ endpoints** across **12 categories**. All endpoints require Cognito JWT authentication except for health checks and EventBridge-triggered operations.

**Base URL**: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}`  
**Authentication**: Cognito JWT Bearer token or direct Lambda invocation  
**RBAC**: 5 roles with granular permissions (see [RBAC System](#rbac-system))

### 1. Protection Groups (6 endpoints)

Manage logical groupings of DRS source servers for coordinated recovery.

| Method | Endpoint                         | Description                                    |
| ------ | -------------------------------- | ---------------------------------------------- |
| GET    | `/protection-groups`           | List all protection groups with filtering      |
| POST   | `/protection-groups`           | Create protection group (explicit or tag-based) |
| GET    | `/protection-groups/{id}`      | Get protection group details                   |
| PUT    | `/protection-groups/{id}`      | Update protection group                        |
| DELETE | `/protection-groups/{id}`      | Delete protection group                        |
| POST   | `/protection-groups/resolve`   | Preview servers from tag-based selection      |

### 2. Recovery Plans (7 endpoints)

Manage multi-wave disaster recovery execution plans.

| Method | Endpoint                                      | Description                                |
| ------ | --------------------------------------------- | ------------------------------------------ |
| GET    | `/recovery-plans`                           | List all recovery plans with filtering     |
| POST   | `/recovery-plans`                           | Create recovery plan                       |
| GET    | `/recovery-plans/{id}`                      | Get recovery plan details                  |
| PUT    | `/recovery-plans/{id}`                      | Update recovery plan                       |
| DELETE | `/recovery-plans/{id}`                      | Delete recovery plan                       |
| POST   | `/recovery-plans/{id}/execute`              | Execute recovery plan (start DR)           |
| GET    | `/recovery-plans/{id}/check-existing-instances` | Check for conflicting recovery instances |

### 3. Executions (11 endpoints)

Monitor and control disaster recovery executions with wave-based orchestration.

| Method | Endpoint                                      | Description                              |
| ------ | --------------------------------------------- | ---------------------------------------- |
| GET    | `/executions`                               | List executions with pagination          |
| POST   | `/executions`                               | Start new execution                      |
| GET    | `/executions/{executionId}`                 | Get detailed execution status            |
| POST   | `/executions/{executionId}/cancel`          | Cancel running execution                 |
| POST   | `/executions/{executionId}/pause`           | Pause execution before next wave         |
| POST   | `/executions/{executionId}/resume`          | Resume paused execution                  |
| POST   | `/executions/{executionId}/terminate-instances` | Terminate recovery instances         |
| GET    | `/executions/{executionId}/job-logs`        | Get DRS job logs for troubleshooting     |
| GET    | `/executions/{executionId}/termination-status` | Check instance termination status     |
| DELETE | `/executions`                               | Bulk delete completed executions         |
| POST   | `/executions/delete`                        | Delete specific executions by IDs        |

### 4. DRS Integration (4 endpoints)

Direct integration with AWS Elastic Disaster Recovery service.

| Method | Endpoint                  | Description                                    |
| ------ | ------------------------- | ---------------------------------------------- |
| GET    | `/drs/source-servers`   | Discover DRS source servers across regions     |
| GET    | `/drs/quotas`           | Get DRS service quotas and current usage       |
| POST   | `/drs/tag-sync`         | Sync EC2 instance tags to DRS source servers   |
| GET    | `/drs/accounts`         | Get available DRS-enabled accounts             |

### 5. Account Management (6 endpoints)

Manage cross-account DRS operations and target accounts.

| Method | Endpoint                           | Description                              |
| ------ | ---------------------------------- | ---------------------------------------- |
| GET    | `/accounts/targets`              | List configured target accounts          |
| POST   | `/accounts/targets`              | Register new target account              |
| PUT    | `/accounts/targets/{id}`         | Update target account configuration      |
| DELETE | `/accounts/targets/{id}`         | Remove target account configuration      |
| POST   | `/accounts/targets/{id}/validate` | Validate cross-account role permissions |
| GET    | `/accounts/current`              | Get current account information          |

### 6. EC2 Resources (4 endpoints)

Retrieve EC2 resources for launch configuration dropdowns.

| Method | Endpoint                    | Description                        |
| ------ | --------------------------- | ---------------------------------- |
| GET    | `/ec2/subnets`            | List available subnets by region   |
| GET    | `/ec2/security-groups`    | List security groups by region     |
| GET    | `/ec2/instance-types`     | List EC2 instance types            |
| GET    | `/ec2/instance-profiles`  | List IAM instance profiles         |

### 7. Configuration (4 endpoints)

Export and import system configuration for backup and migration.

| Method | Endpoint                      | Description                                      |
| ------ | ----------------------------- | ------------------------------------------------ |
| GET    | `/config/export`            | Export all Protection Groups and Recovery Plans  |
| POST   | `/config/import`            | Import configuration (supports dry-run mode)     |
| POST   | `/config/import?dryRun=true`| Validate import without making changes           |
| GET    | `/config/validate`          | Validate current configuration integrity         |

### 8. User Management (1 endpoint)

Manage user permissions and roles.

| Method | Endpoint           | Description                    |
| ------ | ------------------ | ------------------------------ |
| GET    | `/users/current` | Get current user profile/roles |

### 9. Health Check (1 endpoint)

System health and status monitoring.

| Method | Endpoint    | Description                                    |
| ------ | ----------- | ---------------------------------------------- |
| GET    | `/health` | Health check endpoint (returns service status) |

### 10. RBAC System

The API implements a comprehensive Role-Based Access Control (RBAC) system with 5 roles and 11 granular permissions.

#### Roles (5 Total)

1. **DRSOrchestrationAdmin** - Full administrative access to all operations
2. **DRSRecoveryManager** - Execute and manage recovery operations with plan modification
3. **DRSPlanManager** - Create/modify recovery plans and protection groups
4. **DRSOperator** - Execute recovery operations but cannot modify plans
5. **DRSReadOnly** - View-only access for monitoring and reporting

#### Permissions (11 Total)

**Account Management:**
- `register_accounts` - Register new target accounts
- `delete_accounts` - Remove target accounts
- `modify_accounts` - Update account configurations
- `view_accounts` - View account information

**Recovery Operations:**
- `start_recovery` - Start disaster recovery executions
- `stop_recovery` - Cancel/pause recovery executions
- `terminate_instances` - Terminate recovery instances
- `view_executions` - View execution status and history

**Infrastructure Management:**
- `create_protection_groups` - Create protection groups
- `delete_protection_groups` - Delete protection groups
- `modify_protection_groups` - Update protection groups
- `view_protection_groups` - View protection groups
- `create_recovery_plans` - Create recovery plans
- `delete_recovery_plans` - Delete recovery plans
- `modify_recovery_plans` - Update recovery plans
- `view_recovery_plans` - View recovery plans

**Configuration:**
- `export_configuration` - Export system configuration
- `import_configuration` - Import system configuration

#### Role-Permission Matrix

| Role | Account Mgmt | Recovery Ops | Infrastructure | Config |
|------|-------------|-------------|----------------|--------|
| **Admin** | Full | Full | Full | Full |
| **Recovery Manager** | Register/Modify | Full | Full | Full |
| **Plan Manager** | View | Start/Stop | Full | None |
| **Operator** | View | Start/Stop | Modify Only | None |
| **Read Only** | View | View | View | None |

#### Authentication Headers

When using Cognito authentication, include the JWT token in requests:

```bash
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

For direct Lambda invocation, RBAC is bypassed but you should include user context:

```json
{
  "httpMethod": "POST",
  "path": "/executions",
  "body": "{\"recoveryPlanId\":\"xxx\",\"executionType\":\"DRILL\",\"initiatedBy\":\"iam-automation-user\"}"
}
```

---

## API Request/Response Examples

This section provides complete request and response examples for all API operations.

### Protection Groups

#### Create Protection Group (Explicit Server Selection)

```bash
POST /protection-groups
Content-Type: application/json

{
  "GroupName": "Database-Servers",
  "Description": "Primary database servers for HRP application",
  "Region": "us-east-1",
  "SourceServerIds": ["s-1234567890abcdef0", "s-0987654321fedcba0"],
  "LaunchConfig": {
    "SubnetId": "subnet-12345678",
    "SecurityGroupIds": ["sg-12345678", "sg-87654321"],
    "InstanceType": "r5.xlarge",
    "InstanceProfileName": "EC2-DRS-Recovery-Role",
    "CopyPrivateIp": true,
    "CopyTags": true,
    "Licensing": {"osByol": false},
    "TargetInstanceTypeRightSizingMethod": "BASIC",
    "LaunchDisposition": "STARTED"
  }
}
```

**Response (201 Created):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Database-Servers",
  "description": "Primary database servers for HRP application",
  "region": "us-east-1",
  "sourceServerIds": ["s-1234567890abcdef0", "s-0987654321fedcba0"],
  "serverSelectionTags": {},
  "launchConfig": {
    "SubnetId": "subnet-12345678",
    "SecurityGroupIds": ["sg-12345678", "sg-87654321"],
    "InstanceType": "r5.xlarge",
    "InstanceProfileName": "EC2-DRS-Recovery-Role",
    "CopyPrivateIp": true,
    "CopyTags": true,
    "Licensing": {"osByol": false},
    "TargetInstanceTypeRightSizingMethod": "BASIC",
    "LaunchDisposition": "STARTED"
  },
  "launchConfigApplyResults": {
    "applied": 2,
    "skipped": 0,
    "failed": 0,
    "details": [
      {"serverId": "s-1234567890abcdef0", "status": "applied", "templateId": "lt-0123456789abcdef0"},
      {"serverId": "s-0987654321fedcba0", "status": "applied", "templateId": "lt-fedcba9876543210f"}
    ]
  },
  "createdDate": 1702500000,
  "lastModifiedDate": 1702500000,
  "version": 1
}
```

#### Create Protection Group (Tag-Based Selection)

```bash
POST /protection-groups
Content-Type: application/json

{
  "GroupName": "App-Servers-HRP",
  "Description": "Application servers selected by tags",
  "Region": "us-east-1",
  "ServerSelectionTags": {
    "DR-Application": "HRP",
    "DR-Tier": "Application"
  },
  "LaunchConfig": {
    "SubnetId": "subnet-app12345",
    "SecurityGroupIds": ["sg-app12345"],
    "CopyPrivateIp": true,
    "CopyTags": true,
    "TargetInstanceTypeRightSizingMethod": "IN_AWS",
    "LaunchDisposition": "STARTED"
  }
}
```

**Response (201 Created):**
```json
{
  "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
  "name": "App-Servers-HRP",
  "description": "Application servers selected by tags",
  "region": "us-east-1",
  "sourceServerIds": [],
  "serverSelectionTags": {
    "DR-Application": "HRP",
    "DR-Tier": "Application"
  },
  "launchConfig": {
    "SubnetId": "subnet-app12345",
    "SecurityGroupIds": ["sg-app12345"],
    "CopyPrivateIp": true,
    "CopyTags": true,
    "TargetInstanceTypeRightSizingMethod": "IN_AWS",
    "LaunchDisposition": "STARTED"
  },
  "createdDate": 1702500100,
  "lastModifiedDate": 1702500100,
  "version": 1
}
```

#### LaunchConfig Field Reference

| Field | Type | Description | Values |
|-------|------|-------------|--------|
| `SubnetId` | string | Target VPC subnet for recovery instances | `subnet-xxxxxxxx` |
| `SecurityGroupIds` | string[] | Security groups to attach | `["sg-xxx", "sg-yyy"]` |
| `InstanceType` | string | EC2 instance type | `t3.medium`, `r5.xlarge`, etc. |
| `InstanceProfileName` | string | IAM instance profile name | Profile name (not ARN) |
| `CopyPrivateIp` | boolean | Copy source server's private IP | `true` / `false` |
| `CopyTags` | boolean | Transfer source server tags to recovery instance | `true` / `false` |
| `Licensing` | object | OS licensing configuration | `{"osByol": true}` or `{"osByol": false}` |
| `TargetInstanceTypeRightSizingMethod` | string | Instance type right-sizing | `BASIC`, `IN_AWS`, `NONE` |
| `LaunchDisposition` | string | Start instance upon launch | `STARTED`, `STOPPED` |

**TargetInstanceTypeRightSizingMethod Values:**
- `BASIC` - DRS selects instance type based on source server hardware
- `IN_AWS` - DRS periodically updates based on EC2 instance source server (for in-AWS sources)
- `NONE` - Use instance type from EC2 launch template

**LaunchDisposition Values:**
- `STARTED` - Instance starts automatically upon launch
- `STOPPED` - Instance remains stopped after launch (manual start required)

**Licensing Values:**
- `{"osByol": true}` - Bring Your Own License (BYOL)
- `{"osByol": false}` - Use AWS-provided license

#### Update Protection Group

```bash
PUT /protection-groups/{id}
Content-Type: application/json

{
  "version": 1,
  "GroupName": "Database-Servers-Updated",
  "Description": "Updated description",
  "LaunchConfig": {
    "SubnetId": "subnet-newsubnet",
    "SecurityGroupIds": ["sg-newsecgroup"],
    "InstanceType": "r5.2xlarge",
    "CopyPrivateIp": true,
    "CopyTags": true,
    "Licensing": {"osByol": true},
    "TargetInstanceTypeRightSizingMethod": "NONE",
    "LaunchDisposition": "STOPPED"
  }
}
```

**Response (200 OK):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Database-Servers-Updated",
  "description": "Updated description",
  "region": "us-east-1",
  "sourceServerIds": ["s-1234567890abcdef0", "s-0987654321fedcba0"],
  "launchConfig": {
    "SubnetId": "subnet-newsubnet",
    "SecurityGroupIds": ["sg-newsecgroup"],
    "InstanceType": "r5.2xlarge",
    "CopyPrivateIp": true,
    "CopyTags": true,
    "Licensing": {"osByol": true},
    "TargetInstanceTypeRightSizingMethod": "NONE",
    "LaunchDisposition": "STOPPED"
  },
  "launchConfigApplyResults": {
    "applied": 2,
    "skipped": 0,
    "failed": 0
  },
  "version": 2
}
```

#### List Protection Groups

```bash
GET /protection-groups
```

**Response (200 OK):**
```json
{
  "groups": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Database-Servers",
      "description": "Primary database servers",
      "region": "us-east-1",
      "sourceServerIds": ["s-1234567890abcdef0"],
      "serverSelectionTags": {},
      "launchConfig": {...},
      "version": 1
    }
  ]
}
```

#### Resolve Servers from Tags

```bash
POST /protection-groups/{id}/resolve
```

**Response (200 OK):**
```json
{
  "servers": [
    {
      "sourceServerId": "s-1234567890abcdef0",
      "hostname": "DBSERVER01",
      "nameTag": "HRP-Database-Primary",
      "sourceInstanceId": "i-0123456789abcdef0",
      "sourceIp": "10.0.1.100",
      "sourceRegion": "us-east-1",
      "sourceAccount": "123456789012",
      "state": "READY_FOR_RECOVERY",
      "lagDuration": "PT5M",
      "tags": {
        "DR-Application": "HRP",
        "DR-Tier": "Database",
        "Name": "HRP-Database-Primary"
      }
    }
  ]
}
```

### Recovery Plans

#### Create Recovery Plan

```bash
POST /recovery-plans
Content-Type: application/json

{
  "PlanName": "HRP-Full-Recovery",
  "Description": "Full HRP application recovery - DB then App",
  "Waves": [
    {
      "waveNumber": 1,
      "name": "Database Tier",
      "protectionGroupId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "pauseBeforeWave": false
    },
    {
      "waveNumber": 2,
      "name": "Application Tier",
      "protectionGroupId": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
      "pauseBeforeWave": true,
      "dependsOn": [1]
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": "c3d4e5f6-a7b8-9012-cdef-345678901234",
  "name": "HRP-Full-Recovery",
  "description": "Full HRP application recovery - DB then App",
  "waves": [
    {
      "waveNumber": 1,
      "name": "Database Tier",
      "protectionGroupId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "protectionGroupName": "Database-Servers",
      "pauseBeforeWave": false,
      "dependsOn": []
    },
    {
      "waveNumber": 2,
      "name": "Application Tier",
      "protectionGroupId": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
      "protectionGroupName": "App-Servers-HRP",
      "pauseBeforeWave": true,
      "dependsOn": [1]
    }
  ],
  "createdDate": 1702500200,
  "lastModifiedDate": 1702500200,
  "version": 1
}
```

### Executions

#### Start Execution

```bash
POST /executions
Content-Type: application/json

{
  "recoveryPlanId": "c3d4e5f6-a7b8-9012-cdef-345678901234",
  "executionType": "DRILL",
  "initiatedBy": "api-automation",
  "invocationSource": "CLI"
}
```

**Response (201 Created):**
```json
{
  "ExecutionId": "d4e5f6a7-b8c9-0123-def4-567890123456",
  "recoveryPlanId": "c3d4e5f6-a7b8-9012-cdef-345678901234",
  "recoveryPlanName": "HRP-Full-Recovery",
  "executionType": "DRILL",
  "status": "PENDING",
  "initiatedBy": "api-automation",
  "invocationSource": "CLI",
  "startTime": 1702500300,
  "waves": [
    {"waveNumber": 1, "status": "PENDING"},
    {"waveNumber": 2, "status": "PENDING"}
  ]
}
```

#### Get Execution Status

```bash
GET /executions/{id}
```

**Response (200 OK):**
```json
{
  "ExecutionId": "d4e5f6a7-b8c9-0123-def4-567890123456",
  "recoveryPlanId": "c3d4e5f6-a7b8-9012-cdef-345678901234",
  "recoveryPlanName": "HRP-Full-Recovery",
  "executionType": "DRILL",
  "status": "PAUSED",
  "currentWave": 2,
  "totalWaves": 2,
  "initiatedBy": "api-automation",
  "startTime": 1702500300,
  "waves": [
    {
      "waveNumber": 1,
      "name": "Database Tier",
      "status": "COMPLETED",
      "startTime": 1702500300,
      "endTime": 1702500600,
      "servers": [
        {
          "sourceServerId": "s-1234567890abcdef0",
          "hostname": "DBSERVER01",
          "status": "LAUNCHED",
          "recoveryInstanceId": "i-recovery123456"
        }
      ]
    },
    {
      "waveNumber": 2,
      "name": "Application Tier",
      "status": "PAUSED",
      "pauseBeforeWave": true
    }
  ]
}
```

#### Resume Paused Execution

```bash
POST /executions/{id}/resume
Content-Type: application/json

{}
```

**Response (200 OK):**
```json
{
  "ExecutionId": "d4e5f6a7-b8c9-0123-def4-567890123456",
  "status": "IN_PROGRESS",
  "message": "Execution resumed"
}
```

#### Terminate Recovery Instances

```bash
POST /executions/{id}/terminate-instances
Content-Type: application/json

{}
```

**Response (200 OK):**
```json
{
  "ExecutionId": "d4e5f6a7-b8c9-0123-def4-567890123456",
  "terminatedInstances": [
    {"instanceId": "i-recovery123456", "status": "terminated"},
    {"instanceId": "i-recovery789012", "status": "terminated"}
  ]
}
```

### DRS Operations

#### List Source Servers

```bash
GET /drs/source-servers?region=us-east-1
```

**Response (200 OK):**
```json
{
  "servers": [
    {
      "sourceServerId": "s-1234567890abcdef0",
      "hostname": "DBSERVER01",
      "nameTag": "HRP-Database-Primary",
      "sourceInstanceId": "i-0123456789abcdef0",
      "sourceIp": "10.0.1.100",
      "sourceRegion": "us-east-1",
      "sourceAccount": "123456789012",
      "state": "READY_FOR_RECOVERY",
      "lagDuration": "PT5M",
      "assignedProtectionGroupId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "assignedProtectionGroupName": "Database-Servers",
      "tags": {
        "DR-Application": "HRP",
        "DR-Tier": "Database"
      }
    }
  ]
}
```

#### Query Servers by Tags

```bash
POST /drs/source-servers/query-by-tags?region=us-east-1
Content-Type: application/json

{
  "tags": {
    "DR-Application": "HRP",
    "DR-Tier": "Database"
  }
}
```

**Response (200 OK):**
```json
{
  "servers": [
    {
      "sourceServerId": "s-1234567890abcdef0",
      "hostname": "DBSERVER01",
      "nameTag": "HRP-Database-Primary",
      "sourceInstanceId": "i-0123456789abcdef0",
      "sourceIp": "10.0.1.100",
      "state": "READY_FOR_RECOVERY",
      "tags": {...}
    }
  ],
  "matchedTags": {
    "DR-Application": "HRP",
    "DR-Tier": "Database"
  }
}
```

#### Get DRS Quotas

```bash
GET /drs/quotas?region=us-east-1
```

**Response (200 OK):**
```json
{
  "region": "us-east-1",
  "quotas": {
    "maxReplicatingServers": 300,
    "currentReplicatingServers": 45,
    "maxConcurrentJobs": 20,
    "currentActiveJobs": 2,
    "maxServersPerJob": 100,
    "maxTotalServersInActiveJobs": 500
  }
}
```

### EC2 Resources (for Launch Config)

#### List Subnets

```bash
GET /ec2/subnets?region=us-east-1
```

**Response (200 OK):**
```json
{
  "subnets": [
    {
      "subnetId": "subnet-12345678",
      "vpcId": "vpc-abcdef01",
      "availabilityZone": "us-east-1a",
      "cidrBlock": "10.0.1.0/24",
      "name": "Private-Subnet-1a"
    }
  ]
}
```

#### List Security Groups

```bash
GET /ec2/security-groups?region=us-east-1
```

**Response (200 OK):**
```json
{
  "securityGroups": [
    {
      "groupId": "sg-12345678",
      "groupName": "DRS-Recovery-SG",
      "vpcId": "vpc-abcdef01",
      "description": "Security group for DRS recovery instances"
    }
  ]
}
```

#### List Instance Profiles

```bash
GET /ec2/instance-profiles?region=us-east-1
```

**Response (200 OK):**
```json
{
  "instanceProfiles": [
    {
      "instanceProfileName": "EC2-DRS-Recovery-Role",
      "instanceProfileId": "AIPA1234567890EXAMPLE",
      "arn": "arn:aws:iam::123456789012:instance-profile/EC2-DRS-Recovery-Role",
      "roles": ["EC2-DRS-Recovery-Role"]
    }
  ]
}
```

#### List Instance Types

```bash
GET /ec2/instance-types?region=us-east-1
```

**Response (200 OK):**
```json
{
  "instanceTypes": [
    {"instanceType": "t3.micro", "vCpus": 2, "memoryGiB": 1},
    {"instanceType": "t3.small", "vCpus": 2, "memoryGiB": 2},
    {"instanceType": "t3.medium", "vCpus": 2, "memoryGiB": 4},
    {"instanceType": "r5.large", "vCpus": 2, "memoryGiB": 16},
    {"instanceType": "r5.xlarge", "vCpus": 4, "memoryGiB": 32}
  ]
}
```

### Configuration Export/Import

#### Export Configuration

Export all Protection Groups and Recovery Plans to JSON for backup or migration.

```bash
GET /config/export
```

**Response (200 OK):**
```json
{
  "metadata": {
    "schemaVersion": "1.0",
    "exportedAt": "2025-12-14T10:30:00.000Z",
    "sourceRegion": "us-east-1",
    "protectionGroupCount": 3,
    "recoveryPlanCount": 2
  },
  "protectionGroups": [
    {
      "name": "Database-Servers",
      "description": "Primary database servers",
      "region": "us-east-1",
      "sourceServerIds": ["s-1234567890abcdef0"],
      "serverSelectionTags": {},
      "launchConfig": {
        "SubnetId": "subnet-12345678",
        "SecurityGroupIds": ["sg-12345678"],
        "InstanceType": "r5.xlarge",
        "CopyPrivateIp": true,
        "CopyTags": true,
        "Licensing": {"osByol": false},
        "TargetInstanceTypeRightSizingMethod": "BASIC",
        "LaunchDisposition": "STARTED"
      }
    },
    {
      "name": "App-Servers-HRP",
      "description": "Application servers by tags",
      "region": "us-east-1",
      "sourceServerIds": [],
      "serverSelectionTags": {
        "DR-Application": "HRP",
        "DR-Tier": "Application"
      },
      "launchConfig": {
        "SubnetId": "subnet-app12345",
        "SecurityGroupIds": ["sg-app12345"],
        "CopyPrivateIp": true,
        "CopyTags": true
      }
    }
  ],
  "recoveryPlans": [
    {
      "name": "HRP-Full-Recovery",
      "description": "Full HRP application recovery",
      "waves": [
        {
          "waveNumber": 1,
          "protectionGroupName": "Database-Servers",
          "pauseBeforeWave": false
        },
        {
          "waveNumber": 2,
          "protectionGroupName": "App-Servers-HRP",
          "pauseBeforeWave": true
        }
      ]
    }
  ]
}
```

**CLI Example - Export to File:**
```bash
# Export configuration to file
curl -s -H "Authorization: Bearer ${TOKEN}" \
  "${API_ENDPOINT}/config/export" | jq . > drs-config-backup.json

# Direct Lambda invocation (no Cognito token needed)
AWS_PAGER="" aws lambda invoke \
  --function-name aws-drs-orchestrator-api-handler-dev \
  --payload '{"httpMethod":"GET","path":"/config/export"}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/response.json \
  --region us-east-1

jq -r '.body' /tmp/response.json | jq . > drs-config-backup.json
```

#### Import Configuration (Dry Run)

Validate import without making changes. Use this to preview what will be created or skipped.

```bash
POST /config/import?dryRun=true
Content-Type: application/json

{
  "metadata": { ... },
  "protectionGroups": [ ... ],
  "recoveryPlans": [ ... ]
}
```

**Response (200 OK):**
```json
{
  "dryRun": true,
  "summary": {
    "protectionGroups": {
      "total": 3,
      "created": 2,
      "skipped": 1,
      "failed": 0
    },
    "recoveryPlans": {
      "total": 2,
      "created": 1,
      "skipped": 1,
      "failed": 0
    }
  },
  "protectionGroups": [
    {"name": "Database-Servers", "status": "would_create"},
    {"name": "App-Servers-HRP", "status": "would_create"},
    {"name": "Web-Servers", "status": "skipped", "reason": "Name already exists"}
  ],
  "recoveryPlans": [
    {"name": "HRP-Full-Recovery", "status": "would_create"},
    {"name": "Existing-Plan", "status": "skipped", "reason": "Name already exists"}
  ]
}
```

#### Import Configuration (Execute)

Import configuration and create resources. Existing resources with matching names are skipped (non-destructive).

```bash
POST /config/import
Content-Type: application/json

{
  "metadata": {
    "schemaVersion": "1.0",
    "exportedAt": "2025-12-14T10:30:00.000Z",
    "sourceRegion": "us-east-1"
  },
  "protectionGroups": [
    {
      "name": "Database-Servers",
      "description": "Primary database servers",
      "region": "us-east-1",
      "sourceServerIds": ["s-1234567890abcdef0"],
      "launchConfig": {
        "SubnetId": "subnet-12345678",
        "SecurityGroupIds": ["sg-12345678"],
        "InstanceType": "r5.xlarge",
        "CopyPrivateIp": true,
        "CopyTags": true,
        "Licensing": {"osByol": false},
        "TargetInstanceTypeRightSizingMethod": "BASIC",
        "LaunchDisposition": "STARTED"
      }
    }
  ],
  "recoveryPlans": [
    {
      "name": "HRP-Full-Recovery",
      "description": "Full HRP application recovery",
      "waves": [
        {
          "waveNumber": 1,
          "protectionGroupName": "Database-Servers",
          "pauseBeforeWave": false
        }
      ]
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "dryRun": false,
  "summary": {
    "protectionGroups": {
      "total": 1,
      "created": 1,
      "skipped": 0,
      "failed": 0
    },
    "recoveryPlans": {
      "total": 1,
      "created": 1,
      "skipped": 0,
      "failed": 0
    }
  },
  "protectionGroups": [
    {
      "name": "Database-Servers",
      "status": "created",
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "launchConfigApplied": true
    }
  ],
  "recoveryPlans": [
    {
      "name": "HRP-Full-Recovery",
      "status": "created",
      "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012"
    }
  ]
}
```

**CLI Example - Import from File:**
```bash
# Import with dry-run validation first
curl -X POST -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d @drs-config-backup.json \
  "${API_ENDPOINT}/config/import?dryRun=true" | jq .

# Execute import after validation
curl -X POST -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d @drs-config-backup.json \
  "${API_ENDPOINT}/config/import" | jq .

# Direct Lambda invocation (no Cognito token needed)
CONFIG_JSON=$(cat drs-config-backup.json | jq -c .)
AWS_PAGER="" aws lambda invoke \
  --function-name aws-drs-orchestrator-api-handler-dev \
  --payload "{\"httpMethod\":\"POST\",\"path\":\"/config/import\",\"queryStringParameters\":{\"dryRun\":\"true\"},\"body\":$(echo $CONFIG_JSON | jq -Rs .)}" \
  --cli-binary-format raw-in-base64-out \
  /tmp/response.json \
  --region us-east-1

jq -r '.body' /tmp/response.json | jq .
```

#### Import Validation Rules

The import process validates:

| Validation | Behavior |
|------------|----------|
| **Existing names** | Resources with matching names are skipped (non-destructive) |
| **Server IDs** | Validates DRS source servers exist in the target region |
| **Tag-based groups** | Validates tags resolve to at least one server |
| **Recovery Plan references** | Validates referenced Protection Groups exist or will be created |
| **LaunchConfig** | Applies LaunchConfig to DRS source servers on successful import |

#### Import Error Handling

If a Protection Group fails to import, any Recovery Plans that reference it will also fail with a cascade error:

```json
{
  "protectionGroups": [
    {
      "name": "Database-Servers",
      "status": "failed",
      "reason": "Server s-invalid123 not found in DRS"
    }
  ],
  "recoveryPlans": [
    {
      "name": "HRP-Full-Recovery",
      "status": "failed",
      "reason": "Referenced Protection Group 'Database-Servers' failed to import"
    }
  ]
}
```

#### Minimum Import Example

This is the minimum JSON required to create a 3-tier tag-based recovery setup from scratch:

```json
{
  "metadata": {
    "schemaVersion": "1.0"
  },
  "protectionGroups": [
    {
      "GroupName": "ADServersBasedOnTags",
      "Region": "us-east-1",
      "ServerSelectionTags": {"Service": "Active Directory"},
      "LaunchConfig": {
        "SubnetId": "subnet-0c458dee42bb55fde",
        "SecurityGroupIds": ["sg-06f217dba4afdd97f"],
        "InstanceType": "t3a.xlarge",
        "InstanceProfileName": "AWSElasticDisasterRecoveryReplicationServerRole"
      }
    },
    {
      "GroupName": "DNSServersBasedOnTags",
      "Region": "us-east-1",
      "ServerSelectionTags": {"Service": "DNS"},
      "LaunchConfig": {
        "SubnetId": "subnet-06b0b2cb42c4cf99c",
        "SecurityGroupIds": ["sg-06f217dba4afdd97f"],
        "InstanceType": "t3a.large",
        "InstanceProfileName": "demo-ec2-profile",
        "LaunchDisposition": "STARTED"
      }
    },
    {
      "GroupName": "AppServersBasedOnTags",
      "Region": "us-east-1",
      "ServerSelectionTags": {"Application": "PatientPortal"},
      "LaunchConfig": {
        "SubnetId": "subnet-055e7f7e2db65bd5e",
        "SecurityGroupIds": ["sg-06f217dba4afdd97f"],
        "InstanceType": "t3a.large",
        "InstanceProfileName": "demo-ec2-profile",
        "LaunchDisposition": "STOPPED"
      }
    }
  ],
  "recoveryPlans": [
    {
      "PlanName": "HRPRecoveryPlan",
      "Waves": [
        {
          "WaveName": "InfrastructureWave",
          "ProtectionGroupName": "ADServersBasedOnTags"
        },
        {
          "WaveName": "DNSWave",
          "ProtectionGroupName": "DNSServersBasedOnTags",
          "PauseBeforeWave": true,
          "Dependencies": [{"DependsOnWaveId": "wave-1"}]
        },
        {
          "WaveName": "ApplicationWave",
          "ProtectionGroupName": "AppServersBasedOnTags",
          "PauseBeforeWave": true,
          "Dependencies": [{"DependsOnWaveId": "wave-2"}]
        }
      ]
    }
  ]
}
```

**Required Fields:**

| Section | Required Fields |
|---------|-----------------|
| `metadata` | `schemaVersion` ("1.0") |
| `protectionGroups[]` | `GroupName`, `Region` |
| `protectionGroups[].LaunchConfig` | `SubnetId`, `SecurityGroupIds` (minimum for DRS) |
| `recoveryPlans[]` | `PlanName`, `Waves[]` |
| `Waves[]` | `WaveName`, `ProtectionGroupName` |

**Optional Fields (auto-defaulted):**

- `Description`, `AccountId`, `Owner` - empty strings
- `WaveId` - auto-generated (wave-1, wave-2, etc.)
- `ExecutionOrder` - calculated from array position
- `PauseBeforeWave` - defaults to false
- `Dependencies` - empty array
- `LaunchDisposition` - defaults to DRS default
- `InstanceType` - uses DRS right-sizing if not specified

**Tag-Based Server Selection:**

The `ServerSelectionTags` field enables dynamic server discovery. Servers are matched by EC2 tags:

```json
"ServerSelectionTags": {"Service": "Active Directory"}
```

This finds all DRS source servers where the EC2 instance has tag `Service=Active Directory`. Use existing organizational tags like `Service`, `Application`, or `Customer` for server selection rather than creating custom tier tags.

### Error Responses

All error responses follow this format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "field": "fieldName",
  "details": {}
}
```

**Common Error Codes:**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `MISSING_FIELD` | 400 | Required field not provided |
| `INVALID_NAME` | 400 | Name validation failed |
| `INVALID_SERVER_IDS` | 400 | Server IDs not found in DRS |
| `INVALID_LAUNCH_CONFIG` | 400 | LaunchConfig validation failed |
| `PG_NAME_EXISTS` | 409 | Protection group name already exists |
| `SERVER_CONFLICT` | 409 | Server already assigned to another group |
| `TAG_CONFLICT` | 409 | Tags already used by another group |
| `VERSION_CONFLICT` | 409 | Optimistic locking conflict |
| `PG_IN_ACTIVE_EXECUTION` | 409 | Cannot modify group during active execution |
| `PLAN_IN_ACTIVE_EXECUTION` | 409 | Cannot modify plan during active execution |
| `CIRCULAR_DEPENDENCY` | 400 | Wave dependencies form a loop |
| `DRS_QUOTA_EXCEEDED` | 400 | DRS service limit would be exceeded |

---

## Advanced Features

### Cross-Account Operations

The API supports cross-account DRS operations, allowing you to manage disaster recovery across multiple AWS accounts.

#### Register Target Account

```bash
POST /accounts/targets
Content-Type: application/json

{
  "accountId": "123456789012",
  "accountName": "Production Account",
  "crossAccountRoleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
}
```

#### Cross-Account Protection Group

```bash
POST /protection-groups
Content-Type: application/json

{
  "GroupName": "Cross-Account-Servers",
  "Description": "Servers in production account",
  "Region": "us-east-1",
  "AccountId": "123456789012",
  "SourceServerIds": ["s-1234567890abcdef0"],
  "LaunchConfig": {
    "SubnetId": "subnet-12345678",
    "SecurityGroupIds": ["sg-12345678"],
    "InstanceType": "r5.xlarge"
  }
}
```

#### Required Cross-Account IAM Role

The target account must have a role with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "drs:DescribeSourceServers",
        "drs:StartRecovery",
        "drs:DescribeJobs",
        "drs:CreateRecoveryInstanceForDrs",
        "ec2:DescribeInstances",
        "ec2:DescribeLaunchTemplates",
        "ec2:CreateLaunchTemplateVersion"
      ],
      "Resource": "*"
    }
  ]
}
```

Trust relationship:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::SOURCE-ACCOUNT:role/DRSOrchestrationLambdaRole"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Tag-Based Server Selection

Protection Groups can automatically select servers based on EC2 tags instead of explicit server IDs.

#### Create Tag-Based Protection Group

```bash
POST /protection-groups
Content-Type: application/json

{
  "GroupName": "Production-Web-Servers",
  "Description": "All production web servers",
  "Region": "us-east-1",
  "ServerSelectionTags": {
    "Environment": "Production",
    "Tier": "Web",
    "DR-Enabled": "true"
  }
}
```

#### Preview Tag Selection

Before creating a Protection Group, preview which servers would be selected:

```bash
POST /protection-groups/resolve
Content-Type: application/json

{
  "region": "us-east-1",
  "serverSelectionTags": {
    "Environment": "Production",
    "Tier": "Web"
  }
}
```

**Response:**
```json
{
  "servers": [
    {
      "sourceServerId": "s-1234567890abcdef0",
      "hostname": "WEB01",
      "nameTag": "Production-Web-01",
      "sourceInstanceId": "i-0123456789abcdef0",
      "tags": {
        "Environment": "Production",
        "Tier": "Web",
        "Name": "Production-Web-01"
      }
    }
  ],
  "matchedTags": {
    "Environment": "Production",
    "Tier": "Web"
  }
}
```

#### Tag Sync Automation

Enable automatic synchronization of EC2 tags to DRS source servers:

```bash
POST /drs/tag-sync
Content-Type: application/json

{
  "regions": ["us-east-1", "us-west-2"],
  "dryRun": false
}
```

### Wave-Based Execution with Pause/Resume

Recovery Plans support wave-based execution with pause points for manual validation.

#### Create Plan with Pause Points

```bash
POST /recovery-plans
Content-Type: application/json

{
  "PlanName": "Staged-Recovery",
  "Description": "Recovery with manual validation points",
  "Waves": [
    {
      "waveNumber": 1,
      "name": "Database Tier",
      "protectionGroupId": "pg-database",
      "pauseBeforeWave": false
    },
    {
      "waveNumber": 2,
      "name": "Application Tier",
      "protectionGroupId": "pg-application",
      "pauseBeforeWave": true,
      "dependsOn": [1]
    },
    {
      "waveNumber": 3,
      "name": "Web Tier",
      "protectionGroupId": "pg-web",
      "pauseBeforeWave": true,
      "dependsOn": [2]
    }
  ]
}
```

#### Execution Flow with Pauses

1. **Start Execution** - Wave 1 begins immediately
2. **Wave 1 Completes** - Execution pauses before Wave 2
3. **Manual Validation** - Verify database tier is healthy
4. **Resume Execution** - Wave 2 begins
5. **Wave 2 Completes** - Execution pauses before Wave 3
6. **Manual Validation** - Verify application tier is healthy
7. **Resume Execution** - Wave 3 begins and completes

#### Resume Paused Execution

```bash
POST /executions/{executionId}/resume
```

### Conflict Detection

The API automatically detects server conflicts and prevents overlapping assignments.

#### Server Conflict Example

```bash
POST /protection-groups
Content-Type: application/json

{
  "GroupName": "Duplicate-Servers",
  "SourceServerIds": ["s-1234567890abcdef0"]  // Already assigned to another group
}
```

**Response (409 Conflict):**
```json
{
  "error": "SERVER_CONFLICT",
  "message": "Server s-1234567890abcdef0 is already assigned to protection group 'Database-Servers'",
  "details": {
    "conflictingServers": [
      {
        "serverId": "s-1234567890abcdef0",
        "existingGroupId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "existingGroupName": "Database-Servers"
      }
    ]
  }
}
```

#### Recovery Plan Conflict Check

Before executing a recovery plan, check for existing recovery instances:

```bash
GET /recovery-plans/{id}/check-existing-instances
```

**Response:**
```json
{
  "hasConflicts": true,
  "existingInstances": [
    {
      "sourceServerId": "s-1234567890abcdef0",
      "recoveryInstanceId": "i-recovery123456",
      "state": "running",
      "launchedAt": "2025-01-01T10:00:00Z"
    }
  ]
}
```

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
api_call GET "/recovery-plans?tag=Service=Active%20Directory" | jq '.plans'

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

### Configuration Backup and Restore (Complete Walkthrough)

This walkthrough demonstrates a complete export/delete/reimport cycle using direct Lambda invocation (no Cognito token required).

#### Step 1: Set Up Environment

```bash
# Set Lambda function name and region
export LAMBDA_FUNCTION="aws-drs-orchestrator-api-handler-dev"
export AWS_REGION="us-east-1"

# Helper function for Lambda invocation
invoke_api() {
  local method=$1
  local path=$2
  local body=$3
  local query=$4
  
  local payload="{\"httpMethod\":\"$method\",\"path\":\"$path\""
  
  # Add pathParameters if path contains an ID
  if [[ "$path" =~ /([a-f0-9-]{36})$ ]]; then
    local id="${BASH_REMATCH[1]}"
    payload="$payload,\"pathParameters\":{\"id\":\"$id\"}"
  fi
  
  # Add queryStringParameters if provided
  if [ -n "$query" ]; then
    payload="$payload,\"queryStringParameters\":$query"
  fi
  
  # Add body if provided
  if [ -n "$body" ]; then
    payload="$payload,\"body\":$(echo "$body" | jq -Rs .)"
  fi
  
  payload="$payload}"
  
  AWS_PAGER="" aws lambda invoke \
    --function-name "$LAMBDA_FUNCTION" \
    --payload "$payload" \
    --cli-binary-format raw-in-base64-out \
    /tmp/lambda_response.json \
    --region "$AWS_REGION" > /dev/null 2>&1
  
  jq -r '.body' /tmp/lambda_response.json
}
```

#### Step 2: Export Current Configuration

```bash
# Export all Protection Groups and Recovery Plans
echo "=== Exporting Configuration ==="
invoke_api "GET" "/config/export" | jq . > drs-config-backup.json

# Verify export contents
echo "Export metadata:"
jq '.metadata' drs-config-backup.json

echo "Protection Groups: $(jq '.protectionGroups | length' drs-config-backup.json)"
echo "Recovery Plans: $(jq '.recoveryPlans | length' drs-config-backup.json)"

# List exported resources
echo "Protection Groups:"
jq -r '.protectionGroups[].GroupName' drs-config-backup.json

echo "Recovery Plans:"
jq -r '.recoveryPlans[].PlanName' drs-config-backup.json
```

#### Step 3: Delete All Resources (Simulating Disaster)

```bash
echo "=== Deleting All Resources ==="

# Get Recovery Plan IDs and delete them first (they reference Protection Groups)
PLAN_IDS=$(invoke_api "GET" "/recovery-plans" | jq -r '.plans[].id')
for id in $PLAN_IDS; do
  echo "Deleting Recovery Plan: $id"
  invoke_api "DELETE" "/recovery-plans/$id"
done

# Get Protection Group IDs and delete them
GROUP_IDS=$(invoke_api "GET" "/protection-groups" | jq -r '.groups[].id')
for id in $GROUP_IDS; do
  echo "Deleting Protection Group: $id"
  invoke_api "DELETE" "/protection-groups/$id"
done

# Verify deletion
echo "Remaining Protection Groups: $(invoke_api "GET" "/protection-groups" | jq '.groups | length')"
echo "Remaining Recovery Plans: $(invoke_api "GET" "/recovery-plans" | jq '.plans | length')"
```

#### Step 4: Validate Import with Dry Run

```bash
echo "=== Dry Run Import ==="
CONFIG_JSON=$(cat drs-config-backup.json | jq -c .)

# Dry run to validate without making changes
invoke_api "POST" "/config/import" "$CONFIG_JSON" '{"dryRun":"true"}' | jq '.summary'
```

Expected output:
```json
{
  "protectionGroups": { "created": 3, "skipped": 0, "failed": 0 },
  "recoveryPlans": { "created": 1, "skipped": 0, "failed": 0 }
}
```

#### Step 5: Execute Import

```bash
echo "=== Executing Import ==="
CONFIG_JSON=$(cat drs-config-backup.json | jq -c .)

# Execute actual import
RESULT=$(invoke_api "POST" "/config/import" "$CONFIG_JSON")
echo "$RESULT" | jq '.summary'

# Show created resources
echo "Created Protection Groups:"
echo "$RESULT" | jq -r '.created[] | select(.type=="ProtectionGroup") | "  - \(.name) (ID: \(.id))"'

echo "Created Recovery Plans:"
echo "$RESULT" | jq -r '.created[] | select(.type=="RecoveryPlan") | "  - \(.name) (ID: \(.id))"'
```

#### Step 6: Verify Restoration

```bash
echo "=== Verifying Restoration ==="

# List restored Protection Groups
echo "Protection Groups:"
invoke_api "GET" "/protection-groups" | jq '.groups[] | {name, region, serverCount: (.sourceServerIds | length)}'

# List restored Recovery Plans
echo "Recovery Plans:"
invoke_api "GET" "/recovery-plans" | jq '.plans[] | {name, waveCount: (.waves | length)}'

# Verify LaunchConfig was preserved (check first Protection Group)
FIRST_PG_ID=$(invoke_api "GET" "/protection-groups" | jq -r '.groups[0].id')
echo "LaunchConfig for first Protection Group:"
invoke_api "GET" "/protection-groups/$FIRST_PG_ID" | jq '.launchConfig'
```

#### Complete Script

Save this as `scripts/config-backup-restore.sh`:

```bash
#!/bin/bash
# Configuration Backup and Restore Script
# Usage: ./config-backup-restore.sh [export|import|restore-test]

set -e

LAMBDA_FUNCTION="${LAMBDA_FUNCTION:-aws-drs-orchestrator-api-handler-dev}"
AWS_REGION="${AWS_REGION:-us-east-1}"
BACKUP_FILE="${BACKUP_FILE:-drs-config-backup.json}"

invoke_api() {
  local method=$1
  local path=$2
  local body=$3
  local query=$4
  
  local payload="{\"httpMethod\":\"$method\",\"path\":\"$path\""
  
  if [[ "$path" =~ /([a-f0-9-]{36})$ ]]; then
    local id="${BASH_REMATCH[1]}"
    payload="$payload,\"pathParameters\":{\"id\":\"$id\"}"
  fi
  
  if [ -n "$query" ]; then
    payload="$payload,\"queryStringParameters\":$query"
  fi
  
  if [ -n "$body" ]; then
    payload="$payload,\"body\":$(echo "$body" | jq -Rs .)"
  fi
  
  payload="$payload}"
  
  AWS_PAGER="" aws lambda invoke \
    --function-name "$LAMBDA_FUNCTION" \
    --payload "$payload" \
    --cli-binary-format raw-in-base64-out \
    /tmp/lambda_response.json \
    --region "$AWS_REGION" > /dev/null 2>&1
  
  jq -r '.body' /tmp/lambda_response.json
}

case "$1" in
  export)
    echo "Exporting configuration to $BACKUP_FILE..."
    invoke_api "GET" "/config/export" | jq . > "$BACKUP_FILE"
    echo "Exported:"
    echo "  - Protection Groups: $(jq '.protectionGroups | length' "$BACKUP_FILE")"
    echo "  - Recovery Plans: $(jq '.recoveryPlans | length' "$BACKUP_FILE")"
    ;;
    
  import)
    if [ ! -f "$BACKUP_FILE" ]; then
      echo "Error: Backup file $BACKUP_FILE not found"
      exit 1
    fi
    echo "Importing configuration from $BACKUP_FILE..."
    CONFIG_JSON=$(cat "$BACKUP_FILE" | jq -c .)
    RESULT=$(invoke_api "POST" "/config/import" "$CONFIG_JSON")
    echo "$RESULT" | jq '.summary'
    ;;
    
  dry-run)
    if [ ! -f "$BACKUP_FILE" ]; then
      echo "Error: Backup file $BACKUP_FILE not found"
      exit 1
    fi
    echo "Dry-run import from $BACKUP_FILE..."
    CONFIG_JSON=$(cat "$BACKUP_FILE" | jq -c .)
    invoke_api "POST" "/config/import" "$CONFIG_JSON" '{"dryRun":"true"}' | jq '.summary'
    ;;
    
  *)
    echo "Usage: $0 [export|import|dry-run]"
    echo "  export   - Export current configuration to $BACKUP_FILE"
    echo "  import   - Import configuration from $BACKUP_FILE"
    echo "  dry-run  - Validate import without making changes"
    exit 1
    ;;
esac
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
      FunctionName: aws-drs-orchestrator-api-handler-prod
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

| HTTP Code | Category              | Description                                                 | Resolution                                   |
| --------- | --------------------- | ----------------------------------------------------------- | -------------------------------------------- |
| 400       | Bad Request           | Invalid request body, missing fields, or validation failure | Check request format and required fields     |
| 401       | Unauthorized          | Invalid or expired Cognito token                            | Refresh auth token or use IAM-based access   |
| 403       | Forbidden             | Insufficient IAM or Cognito permissions                     | Check IAM policy or Cognito group membership |
| 404       | Not Found             | Resource (PG, Plan, Execution) not found                    | Verify resource ID exists                    |
| 405       | Method Not Allowed    | HTTP method not supported for endpoint                      | Check API documentation for allowed methods  |
| 409       | Conflict              | Resource conflict (duplicate name, active execution, etc.)  | Resolve conflict before retrying             |
| 429       | Too Many Requests     | DRS service limit exceeded                                  | Wait and retry, or request limit increase    |
| 500       | Internal Server Error | Unexpected server-side error                                | Check CloudWatch logs, retry with backoff    |

### API Error Codes Reference

#### Protection Group Errors

| Error Code                     | HTTP | Message                                                                  | Cause                             | Resolution                               |
| ------------------------------ | ---- | ------------------------------------------------------------------------ | --------------------------------- | ---------------------------------------- |
| `PG_NAME_EXISTS`             | 409  | "A Protection Group named X already exists"                              | Duplicate name (case-insensitive) | Use a unique name                        |
| `TAG_CONFLICT`               | 409  | "Another Protection Group already uses these exact tags"                 | Identical tag set exists          | Use different tags or modify existing PG |
| `SERVER_CONFLICT`            | 409  | "One or more servers are already assigned to another Protection Group"   | Server already in another PG      | Remove server from other PG first        |
| `PG_IN_ACTIVE_EXECUTION`     | 409  | "Cannot modify Protection Group while it is part of an active execution" | PG is in running execution        | Wait for execution to complete or cancel |
| `PG_IN_USE`                  | 409  | "Cannot delete Protection Group - it is used in N Recovery Plan(s)"      | PG referenced by plans            | Remove PG from all plans first           |
| `PROTECTION_GROUP_NOT_FOUND` | 404  | "Protection Group X not found"                                           | Invalid PG ID                     | Verify PG ID exists                      |
| `INVALID_TAGS`               | 400  | "ServerSelectionTags must be a non-empty object"                         | Empty or invalid tags             | Provide valid tag key-value pairs        |
| `INVALID_SERVERS`            | 400  | "SourceServerIds must be a non-empty array"                              | Empty or invalid server list      | Provide valid server IDs                 |

#### Recovery Plan Errors

| Error Code                    | HTTP | Message                                                             | Cause                             | Resolution                               |
| ----------------------------- | ---- | ------------------------------------------------------------------- | --------------------------------- | ---------------------------------------- |
| `RP_NAME_EXISTS`            | 409  | "A Recovery Plan named X already exists"                            | Duplicate name (case-insensitive) | Use a unique name                        |
| `PLAN_HAS_ACTIVE_EXECUTION` | 409  | "Cannot modify/delete Recovery Plan while execution is in progress" | Plan has running execution        | Wait for execution to complete or cancel |
| `INVALID_WAVE_DATA`         | 400  | "Wave N has invalid ServerIds format"                               | Wave data malformed               | Ensure ServerIds is an array             |

#### Execution Errors

| Error Code                         | HTTP | Message                                                   | Cause                               | Resolution                                      |
| ---------------------------------- | ---- | --------------------------------------------------------- | ----------------------------------- | ----------------------------------------------- |
| `PLAN_ALREADY_EXECUTING`         | 409  | "This Recovery Plan already has an execution in progress" | Plan already running                | Wait for current execution to complete          |
| `SERVER_CONFLICT`                | 409  | "N server(s) are already in active executions"            | Servers in other running executions | Wait for other executions to complete           |
| `WAVE_SIZE_LIMIT_EXCEEDED`       | 400  | "N wave(s) exceed the DRS limit of 100 servers per job"   | Wave has >100 servers               | Split wave into smaller groups                  |
| `CONCURRENT_JOBS_LIMIT_EXCEEDED` | 429  | "DRS concurrent jobs limit exceeded"                      | >20 concurrent DRS jobs             | Wait for jobs to complete                       |
| `SERVERS_IN_JOBS_LIMIT_EXCEEDED` | 429  | "DRS servers in jobs limit exceeded"                      | >500 servers across all jobs        | Wait for jobs to complete                       |
| `UNHEALTHY_SERVER_REPLICATION`   | 400  | "Server replication not healthy"                          | Server not ready for recovery       | Check DRS console for replication status        |
| `EXECUTION_NOT_FOUND`            | 404  | "Execution with ID X not found"                           | Invalid execution ID                | Verify execution ID exists                      |
| `EXECUTION_NOT_CANCELLABLE`      | 400  | "Execution cannot be cancelled - status is X"             | Execution already completed/failed  | Only running/paused executions can be cancelled |
| `EXECUTION_NOT_PAUSABLE`         | 400  | "Execution cannot be paused - status is X"                | Execution not running               | Only running executions can be paused           |
| `EXECUTION_NO_WAVES`             | 400  | "No waves found in execution"                             | Execution has no wave data          | Internal error - check execution state          |
| `SINGLE_WAVE_NOT_PAUSABLE`       | 400  | "Cannot pause single-wave execution"                      | Plan has only one wave              | Pause only works for multi-wave plans           |
| `NO_PENDING_WAVES`               | 400  | "Cannot pause - no pending waves remaining"               | All waves completed                 | Nothing left to pause                           |

#### DRS Service Errors

| Error Code              | HTTP | Message                            | Cause                    | Resolution                                        |
| ----------------------- | ---- | ---------------------------------- | ------------------------ | ------------------------------------------------- |
| `DRS_NOT_INITIALIZED` | 400  | "DRS is not initialized in region" | DRS not set up in region | Complete DRS initialization wizard in AWS Console |

#### Validation Errors

| Error Code                  | HTTP | Message                                                         | Cause                                  | Resolution                               |
| --------------------------- | ---- | --------------------------------------------------------------- | -------------------------------------- | ---------------------------------------- |
| `MISSING_FIELD`           | 400  | "X is required"                                                 | Required field not provided            | Include the required field in request    |
| `MISSING_REGION`          | 400  | "region query parameter is required"                            | Region not provided for DRS operations | Include `?region=us-east-1` in request |
| `INVALID_NAME`            | 400  | "Name cannot be empty" or "Name must be 64 characters or fewer" | Empty or too long name                 | Provide valid name (1-64 chars)          |
| `INVALID_EXECUTION_TYPE`  | 400  | "ExecutionType must be DRILL or RECOVERY"                       | Invalid execution type                 | Use DRILL or RECOVERY                    |
| `PLAN_HAS_NO_WAVES`       | 400  | "Recovery Plan has no waves configured"                         | Plan has no waves                      | Add at least one wave to the plan        |
| `RECOVERY_PLAN_NOT_FOUND` | 404  | "Recovery Plan with ID X not found"                             | Invalid plan ID                        | Verify plan ID exists                    |

#### Concurrency Errors

| Error Code           | HTTP | Message                                 | Cause                       | Resolution                                  |
| -------------------- | ---- | --------------------------------------- | --------------------------- | ------------------------------------------- |
| `VERSION_CONFLICT` | 409  | "Resource was modified by another user" | Optimistic locking conflict | Refresh data and retry with current version |

#### General Errors

| Error Code         | HTTP | Message                      | Cause                   | Resolution                   |
| ------------------ | ---- | ---------------------------- | ----------------------- | ---------------------------- |
| `INTERNAL_ERROR` | 500  | "Failed to X: error details" | Unexpected error        | Check CloudWatch logs, retry |
| `DELETE_FAILED`  | 500  | "Failed to delete X"         | Delete operation failed | Check CloudWatch logs, retry |

### Optimistic Locking (Version Field)

All Protection Groups and Recovery Plans include a `version` field for optimistic locking. When updating a resource, you must include the current version number. If another user modified the resource since you fetched it, you'll receive a `VERSION_CONFLICT` error.

#### Create Response (version starts at 1)

```json
{
  "id": "pg-abc123",
  "name": "Database Servers",
  "version": 1,
  ...
}
```

#### Update Request (must include current version)

```json
{
  "name": "Updated Name",
  "version": 1
}
```

#### Version Conflict Response

```json
{
  "error": "VERSION_CONFLICT",
  "message": "Resource was modified by another user. Please refresh and try again."
}
```

#### Handling Version Conflicts

```python
def update_with_retry(client, resource_id, updates, max_retries=3):
    """Update resource with automatic conflict resolution"""
    for attempt in range(max_retries):
        # Get current resource state
        resource = client.get_protection_group(resource_id)
      
        # Apply updates with current version
        updates['version'] = resource['version']
      
        try:
            return client.update_protection_group(resource_id, updates)
        except Exception as e:
            if 'VERSION_CONFLICT' in str(e) and attempt < max_retries - 1:
                print(f"Version conflict, retrying ({attempt + 1}/{max_retries})...")
                continue
            raise
```

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
        'MISSING_REGION': 'Include region query parameter (e.g., ?region=us-east-1)',
        'INVALID_NAME': 'Provide a valid name (1-64 characters, not empty)',
        'INVALID_EXECUTION_TYPE': 'Use DRILL or RECOVERY as execution type',
        'PLAN_HAS_NO_WAVES': 'Add at least one wave to the Recovery Plan',
        'RECOVERY_PLAN_NOT_FOUND': 'Verify the Recovery Plan ID exists',
        # Concurrency errors
        'VERSION_CONFLICT': 'Refresh the resource and retry with current version',
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
        VERSION_CONFLICT)
            echo "→ Resource was modified - refresh and retry with current version"
            ;;
        MISSING_REGION)
            echo "→ Include region parameter: ?region=us-east-1"
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
│                    Integration Patterns                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │EventBridge│───▶│  Lambda  │───▶│   API    │───▶│   DRS    │  │
│  │ Schedule  │    │ Trigger  │    │ Gateway  │    │ Service  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘   │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │   SSM    │───▶│Automation│───▶│   API    │───▶│   DRS    │   │
│  │ Document │    │  Steps   │    │ Gateway  │    │ Service  │   │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘   │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │  Step    │───▶│  HTTP    │───▶│   API    │───▶│   DRS    │   │
│  │Functions │    │  Task    │    │ Gateway  │    │ Service  │   │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘   │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │  Bash/   │───▶│  curl/   │───▶│   API    │───▶│   DRS    │   │
│  │ Python   │    │ requests │    │ Gateway  │    │ Service  │   │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘   │
│                                                                 │
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
