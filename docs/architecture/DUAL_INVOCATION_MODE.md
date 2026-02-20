# Dual Invocation Mode Architecture

## Overview

The query-handler Lambda function supports two distinct invocation modes, each with different authentication mechanisms, principal extraction patterns, and audit logging requirements. This architecture enables both user-facing API operations (via API Gateway) and service-to-service operations (via Step Functions and EventBridge).

## Invocation Modes

### Mode 1: API Gateway Invocations (Frontend)

**Flow**:
```
User → CloudFront → API Gateway → Cognito JWT Validation → query-handler
                                                              ↓
                                                    RBAC Middleware Check
                                                              ↓
                                                    Audit Log (Cognito User)
```

**Authentication**: Cognito JWT token in Authorization header

**Principal**: Cognito user email from JWT claims

**RBAC**: Role-based permissions from Cognito groups (Admin, Operator, Viewer, Auditor, Planner)

**Audit Trail**: User email, operation, timestamp, parameters (masked)

**Example Event**:
```json
{
  "httpMethod": "GET",
  "path": "/executions",
  "headers": {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "requestContext": {
    "authorizer": {
      "claims": {
        "email": "user@example.com",
        "cognito:groups": ["Operator", "Viewer"]
      }
    }
  },
  "queryStringParameters": {
    "status": "IN_PROGRESS"
  }
}
```

**Principal Extraction**:
```python
# API Gateway invocation detected by presence of requestContext
if "requestContext" in event:
    invocation_mode = "API_GATEWAY"
    user_email = event["requestContext"]["authorizer"]["claims"]["email"]
    user_groups = event["requestContext"]["authorizer"]["claims"].get(
        "cognito:groups", []
    )
    
    principal_info = {
        "principal_type": "CognitoUser",
        "principal_arn": f"cognito:user:{user_email}",
        "session_name": None,
        "account_id": os.environ["AWS_ACCOUNT_ID"],
        "user_groups": user_groups
    }
```

### Mode 2: Direct Lambda Invocations (Step Functions, EventBridge)

**Flow**:
```
Step Functions → Direct Lambda Invoke → query-handler
                                          ↓
                                IAM Principal Extraction
                                          ↓
                                Audit Log (IAM Role/User)
```

**Authentication**: IAM role/user from Lambda context

**Principal**: IAM ARN from context.invoked_function_arn

**RBAC**: Not applicable (service-to-service trust)

**Audit Trail**: IAM ARN, principal type, session name, operation, timestamp

**Example Event (Step Functions)**:
```json
{
  "operation": "poll_wave_status",
  "execution_id": "exec-123456",
  "plan_id": "plan-789",
  "job_id": "drsjob-abc123",
  "current_wave_number": 1,
  "servers": [
    {"sourceServerId": "s-1234567890abcdef0"}
  ]
}
```

**Example Event (EventBridge)**:
```json
{
  "operation": "get_dashboard_data",
  "time_range": "24h"
}
```

**Principal Extraction**:
```python
# Direct Lambda invocation detected by absence of requestContext
if "requestContext" not in event:
    invocation_mode = "DIRECT_LAMBDA"
    
    # Extract IAM principal from Lambda context
    principal_info = extract_principal_from_context(context)
    
    # Returns:
    # {
    #     "principal_type": "AssumedRole",
    #     "principal_arn": "arn:aws:iam::891376951562:role/ExecutionRole",
    #     "session_name": "session-name",
    #     "account_id": "891376951562"
    # }
```

## Implementation Pattern

### Lambda Handler Structure

```python
import os
from datetime import datetime
from lambda.shared.iam_utils import extract_principal_from_context
from lambda.shared.rbac_middleware import check_permission
from lambda.shared.security_utils import mask_sensitive_parameters


def lambda_handler(event, context):
    """
    Query handler with dual invocation mode support.
    
    Supports both API Gateway (Cognito) and Direct Lambda (IAM) invocations
    with appropriate authentication, authorization, and audit logging.
    """
    
    # Determine invocation mode
    if "requestContext" in event:
        # API Gateway invocation - use Cognito JWT
        invocation_mode = "API_GATEWAY"
        user_email = event["requestContext"]["authorizer"]["claims"]["email"]
        user_groups = event["requestContext"]["authorizer"]["claims"].get(
            "cognito:groups", []
        )
        
        principal_info = {
            "principal_type": "CognitoUser",
            "principal_arn": f"cognito:user:{user_email}",
            "session_name": None,
            "account_id": os.environ["AWS_ACCOUNT_ID"],
            "user_groups": user_groups
        }
        
        # Extract operation from path and method
        operation = extract_operation_from_api_gateway(event)
        
        # Check RBAC permissions
        if not check_permission(user_groups, operation):
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Insufficient permissions"})
            }
    else:
        # Direct Lambda invocation - extract IAM principal
        invocation_mode = "DIRECT_LAMBDA"
        principal_info = extract_principal_from_context(context)
        
        # Extract operation from event
        operation = event.get("operation")
        
        # No RBAC check for service-to-service invocations
        # Trust is established via IAM policies
    
    # Log audit trail with principal information
    audit_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "operation": operation,
        "invocation_mode": invocation_mode,
        "principal_type": principal_info["principal_type"],
        "principal_arn": principal_info["principal_arn"],
        "session_name": principal_info.get("session_name"),
        "account_id": principal_info["account_id"],
        "parameters": mask_sensitive_parameters(event),
        "source_ip": event.get("requestContext", {}).get("identity", {}).get("sourceIp"),
        "user_agent": event.get("requestContext", {}).get("identity", {}).get("userAgent")
    }
    
    # Write audit log to DynamoDB (with retry and CloudWatch fallback)
    write_audit_log(audit_log)
    
    # Process request
    try:
        result = process_query(event, principal_info)
        
        # Return appropriate response format
        if invocation_mode == "API_GATEWAY":
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps(result)
            }
        else:
            # Direct Lambda invocation - return result directly
            return result
            
    except Exception as e:
        logger.exception(f"Failed to process {operation}")
        
        # Update audit log with error
        audit_log["error"] = str(e)
        audit_log["status"] = "FAILED"
        write_audit_log(audit_log)
        
        if invocation_mode == "API_GATEWAY":
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Internal server error"})
            }
        else:
            raise
```

## IAM Principal Types

### 1. AssumedRole (Step Functions, Lambda)

**Context ARN**:
```
arn:aws:sts::891376951562:assumed-role/ExecutionRole/session-name
```

**Extracted Principal**:
```python
{
    "principal_type": "AssumedRole",
    "principal_arn": "arn:aws:iam::891376951562:role/ExecutionRole",
    "session_name": "session-name",
    "account_id": "891376951562"
}
```

**Use Cases**:
- Step Functions invoking query-handler for wave polling
- Lambda-to-Lambda invocations (if needed)

### 2. IAM User (Direct Invocation)

**Context ARN**:
```
arn:aws:iam::891376951562:user/admin-user
```

**Extracted Principal**:
```python
{
    "principal_type": "User",
    "principal_arn": "arn:aws:iam::891376951562:user/admin-user",
    "session_name": None,
    "account_id": "891376951562"
}
```

**Use Cases**:
- Manual Lambda invocations for testing
- CLI-based operations

### 3. AWS Service (EventBridge)

**Context ARN**:
```
arn:aws:events::891376951562:rule/inventory-sync
```

**Extracted Principal**:
```python
{
    "principal_type": "Service",
    "principal_arn": "arn:aws:events::891376951562:rule/inventory-sync",
    "session_name": None,
    "account_id": "891376951562"
}
```

**Use Cases**:
- EventBridge scheduled rules
- CloudWatch Events triggers

## RBAC Integration

### API Gateway Invocations Only

RBAC permissions are enforced ONLY for API Gateway invocations (Cognito users). Direct Lambda invocations bypass RBAC checks and rely on IAM policies for authorization.

**Permission Check**:
```python
from lambda.shared.rbac_middleware import check_permission

# API Gateway invocation
if invocation_mode == "API_GATEWAY":
    user_groups = principal_info["user_groups"]
    operation = extract_operation_from_api_gateway(event)
    
    if not check_permission(user_groups, operation):
        return {
            "statusCode": 403,
            "body": json.dumps({"error": "Insufficient permissions"})
        }
```

**Role Permissions**:
- **Admin**: All operations
- **Operator**: Operational data (executions, servers, plans)
- **Viewer**: Read-only operational data
- **Auditor**: Audit logs + operational data
- **Planner**: Recovery plans + protection groups

See [RBAC_PERMISSIONS.md](../security/RBAC_PERMISSIONS.md) for complete permission mapping.

## Audit Logging

### Audit Log Schema

Both invocation modes write to the same `AuditLogs` DynamoDB table with mode-specific fields:

**Common Fields**:
```python
{
    "timestamp": "2026-02-20T10:30:00.000Z",
    "operation": "list_executions",
    "invocation_mode": "API_GATEWAY" | "DIRECT_LAMBDA",
    "account_id": "891376951562",
    "parameters": {"status": "IN_PROGRESS"},  # Masked
    "status": "SUCCESS" | "FAILED",
    "error": "Error message if failed"
}
```

**API Gateway Specific**:
```python
{
    "principal_type": "CognitoUser",
    "principal_arn": "cognito:user:user@example.com",
    "user_groups": ["Operator", "Viewer"],
    "source_ip": "203.0.113.42",
    "user_agent": "Mozilla/5.0..."
}
```

**Direct Lambda Specific**:
```python
{
    "principal_type": "AssumedRole" | "User" | "Service",
    "principal_arn": "arn:aws:iam::891376951562:role/ExecutionRole",
    "session_name": "session-name"  # For AssumedRole only
}
```

See [AUDIT_LOG_SCHEMA.md](../security/AUDIT_LOG_SCHEMA.md) for complete schema.

## Security Considerations

### API Gateway Invocations

**Authentication**: Cognito JWT token validation by API Gateway

**Authorization**: RBAC middleware checks user groups against operation permissions

**Audit**: User email, groups, source IP, user agent logged

**Parameter Masking**: Sensitive parameters (password, api_key, secret, token) masked before logging

### Direct Lambda Invocations

**Authentication**: IAM role/user from Lambda context

**Authorization**: IAM policies control which roles can invoke Lambda

**Audit**: IAM ARN, principal type, session name logged

**Parameter Masking**: Same masking rules apply

**Authorized Role Validation** (Optional):
```python
from lambda.shared.iam_utils import validate_authorized_role

# Define authorized role patterns
AUTHORIZED_ROLE_PATTERNS = [
    r"^arn:aws:iam::\d{12}:role/ExecutionRole$",
    r"^arn:aws:iam::\d{12}:role/StepFunctionsRole$",
    r"^arn:aws:iam::\d{12}:role/EventBridgeRole$"
]

# Validate role (for AssumedRole principals only)
if principal_info["principal_type"] == "AssumedRole":
    if not validate_authorized_role(
        principal_info["principal_arn"],
        AUTHORIZED_ROLE_PATTERNS
    ):
        return error_response(403, "Unauthorized IAM role")
```

## Testing Strategies

### API Gateway Invocation Tests

```python
def test_api_gateway_invocation_with_cognito_jwt():
    """Test API Gateway invocation with Cognito JWT token."""
    event = {
        "httpMethod": "GET",
        "path": "/executions",
        "headers": {
            "Authorization": "Bearer mock-jwt-token"
        },
        "requestContext": {
            "authorizer": {
                "claims": {
                    "email": "test@example.com",
                    "cognito:groups": ["Operator"]
                }
            }
        }
    }
    
    context = MockLambdaContext()
    response = lambda_handler(event, context)
    
    assert response["statusCode"] == 200
    assert "invocation_mode" in audit_log
    assert audit_log["invocation_mode"] == "API_GATEWAY"
    assert audit_log["principal_type"] == "CognitoUser"
```

### Direct Lambda Invocation Tests

```python
def test_direct_lambda_invocation_with_iam_role():
    """Test direct Lambda invocation with IAM role."""
    event = {
        "operation": "poll_wave_status",
        "execution_id": "exec-123",
        "job_id": "drsjob-abc"
    }
    
    context = MockLambdaContext(
        invoked_function_arn="arn:aws:sts::891376951562:assumed-role/ExecutionRole/session"
    )
    
    response = lambda_handler(event, context)
    
    assert "job_status" in response
    assert "invocation_mode" in audit_log
    assert audit_log["invocation_mode"] == "DIRECT_LAMBDA"
    assert audit_log["principal_type"] == "AssumedRole"
```

## Troubleshooting

### Issue: API Gateway returns 401 Unauthorized

**Cause**: Invalid or expired Cognito JWT token

**Solution**:
1. Verify token is not expired
2. Check Cognito User Pool configuration
3. Ensure API Gateway authorizer is configured correctly

### Issue: Direct Lambda invocation fails with AccessDenied

**Cause**: IAM role lacks permission to invoke Lambda

**Solution**:
1. Add `lambda:InvokeFunction` permission to IAM role
2. Verify Lambda resource-based policy allows invocation
3. Check IAM role trust relationship

### Issue: Audit logs missing principal information

**Cause**: IAM principal extraction failed

**Solution**:
1. Verify Lambda context contains `invoked_function_arn`
2. Check `iam_utils.extract_principal_from_context()` implementation
3. Review CloudWatch Logs for extraction errors

## Related Documentation

- [Handler Responsibilities](HANDLER_RESPONSIBILITIES.md)
- [IAM Principal Extraction](../security/IAM_PRINCIPAL_EXTRACTION.md)
- [RBAC Permissions](../security/RBAC_PERMISSIONS.md)
- [Audit Log Schema](../security/AUDIT_LOG_SCHEMA.md)
- [Parameter Masking](../security/PARAMETER_MASKING.md)
